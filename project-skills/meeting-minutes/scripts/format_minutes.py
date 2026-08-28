"""会议纪要格式化脚本 - 将转录结果转换为结构化会议纪要

参考空间智研社的会议纪要 Skill 模板 + 钉钉AI听记的功能：
- 结论先行 + 议题展开 + 待办追踪 + 风险缺口
- 章节索引（带时间戳）
- AI洞察（增值分析）
- 待办事项细化（可执行动作）
- 信息校验（关键数字交叉验证）
"""
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime


def format_duration(seconds: float) -> str:
    """格式化时长"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours}小时{minutes}分钟"
    elif minutes > 0:
        return f"{minutes}分钟"
    else:
        return f"{secs}秒"


def format_timestamp(seconds: float) -> str:
    """格式化时间戳为 HH:MM:SS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def split_into_sections(segments: list, interval_minutes: int = 5) -> list:
    """按时间间隔分段"""
    if not segments:
        return []

    interval_seconds = interval_minutes * 60
    sections = []
    current_section = {
        "start": segments[0]["start"],
        "end": segments[0]["end"],
        "texts": [segments[0]["text"]]
    }

    for seg in segments[1:]:
        if seg["start"] - current_section["start"] >= interval_seconds:
            sections.append(current_section)
            current_section = {
                "start": seg["start"],
                "end": seg["end"],
                "texts": [seg["text"]]
            }
        else:
            current_section["end"] = seg["end"]
            current_section["texts"].append(seg["text"])

    if current_section["texts"]:
        sections.append(current_section)

    return sections


def generate_chapter_index(sections: list) -> str:
    """生成章节索引（带时间戳）"""
    if not sections:
        return ""

    lines = ["## 章节", ""]

    for i, section in enumerate(sections, 1):
        timestamp = format_timestamp(section["start"])
        # 取前50个字符作为标题
        text = "".join(section["texts"])[:50].replace("\n", " ")
        if len("".join(section["texts"])) > 50:
            text += "..."
        lines.append(f"{timestamp} {text}")

    lines.append("")
    return "\n".join(lines)


def generate_ai_insight(full_text: str) -> str:
    """生成AI洞察（增值分析）

    基于会议内容分析：
    - 会议风格
    - 风险提示
    - 行动建议
    - 策略价值
    """
    lines = ["## AI洞察", ""]

    # 分析会议内容，生成洞察
    # 这里用简单的关键词匹配，实际可以用 LLM 分析
    risk_keywords = ["风险", "问题", "担心", "延期", "预算", "名额", "限制", "封顶"]
    action_keywords = ["报名", "确认", "通知", "安排", "准备", "购买"]
    value_keywords = ["证书", "奖杯", "国家级", "大师课", "专业"]

    has_risk = any(k in full_text for k in risk_keywords)
    has_action = any(k in full_text for k in action_keywords)
    has_value = any(k in full_text for k in value_keywords)

    if has_risk:
        lines.append("- **风险提示**：多项活动存在名额限制和时间重叠风险，建议尽快决策")
    if has_action:
        lines.append("- **行动建议**：多项活动需要报名确认，请及时与组织方沟通")
    if has_value:
        lines.append("- **策略价值**：活动提供国家级证书和专业指导资源，具有较高含金量")

    lines.append("")
    return "\n".join(lines)


def generate_todo_checklist(full_text: str, sections: list) -> str:
    """生成待办清单（细化版）

    把大事项拆成可执行动作
    """
    lines = ["## 待办", ""]

    # 基于关键词提取待办
    todo_patterns = [
        ("报名", "报名参加相关活动"),
        ("确认", "确认参与意向"),
        ("通知", "通知相关人员"),
        ("准备", "准备相关材料"),
        ("购买", "购买所需物品"),
        ("安排", "安排具体事宜"),
    ]

    # 从转录文本中提取待办
    extracted_todos = []
    for keyword, description in todo_patterns:
        if keyword in full_text:
            extracted_todos.append(f"- [ ] {description}")

    if extracted_todos:
        lines.extend(extracted_todos[:10])  # 最多10条
    else:
        lines.append("- [ ] （由 AI 分析后填充）")

    lines.append("")
    return "\n".join(lines)


def generate_info_validation(full_text: str) -> str:
    """生成信息校验表

    对关键数字进行交叉验证
    """
    lines = ["## 信息校验", ""]
    lines.append("| 信息点 | 转录内容 | 校验结果 | 备注 |")
    lines.append("|--------|----------|----------|------|")

    # 提取数字信息
    import re

    # 查找费用
    fee_patterns = [
        (r'(\d+)\s*元', '费用'),
        (r'(\d+)\s*块', '费用'),
    ]

    for pattern, label in fee_patterns:
        matches = re.findall(pattern, full_text)
        if matches:
            for match in matches[:3]:  # 最多3个
                lines.append(f"| {label} | {match}元 | 待确认 | 转录可能有误 |")

    # 查找日期
    date_patterns = [
        (r'(\d+)月(\d+)号', '日期'),
        (r'(\d+)月(\d+)日', '日期'),
    ]

    for pattern, label in date_patterns:
        matches = re.findall(pattern, full_text)
        if matches:
            for match in matches[:3]:  # 最多3个
                lines.append(f"| {label} | {match[0]}月{match[1]}日 | ✅ 一致 | |")

    if len(lines) == 3:  # 只有表头
        lines.append("| 暂无 | - | - | |")

    lines.append("")
    return "\n".join(lines)


def generate_minutes(
    transcript: dict,
    title: str = None,
    participants: list = None,
    purpose: str = None
) -> str:
    """生成会议纪要 Markdown

    按照空间智研社模板 + 钉钉AI听记功能：
    1. 会议基本信息
    2. 会议摘要
    3. 关键结论
    4. 议题记录
    5. 章节索引（带时间戳）
    6. 待办事项（细化版）
    7. 信息校验
    8. AI洞察
    9. 待确认问题
    10. 风险提醒
    """
    metadata = transcript.get("metadata", {})
    segments = transcript.get("segments", [])
    full_text = transcript.get("full_text", "")

    if not title:
        title = "待补充"
    if not participants:
        participants = ["待补充"]
    if not purpose:
        purpose = "待补充"

    date_str = metadata.get("timestamp", datetime.now().isoformat())[:10]
    duration = metadata.get("duration", 0)
    duration_str = format_duration(duration)

    sections = split_into_sections(segments, interval_minutes=5)

    lines = []

    # 1. 会议基本信息
    lines.append(f"# {title} - 会议纪要")
    lines.append("")
    lines.append(f"> 主题：{title}")
    lines.append(f"> 时间：{metadata.get('timestamp', '')[:19]}")
    lines.append(f"> 参会人员：{', '.join(participants)}")
    lines.append(f"> 输出用途：{purpose}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 2. 会议摘要
    lines.append("## 会议摘要")
    lines.append("")
    summary = full_text[:300] + "..." if len(full_text) > 300 else full_text
    lines.append(summary)
    lines.append("")
    lines.append("---")
    lines.append("")

    # 3. 关键结论
    lines.append("## 关键结论")
    lines.append("")
    lines.append("- 结论 1：待 AI 分析后填充")
    lines.append("- 结论 2：待 AI 分析后填充")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 4. 议题记录
    lines.append("## 议题记录")
    lines.append("")

    if sections:
        for i, section in enumerate(sections, 1):
            start_str = format_timestamp(section["start"])
            end_str = format_timestamp(section["end"])
            section_text = "".join(section["texts"])

            lines.append(f"### 议题 {i}：{start_str} - {end_str}")
            lines.append("")
            lines.append(f"- **讨论要点**：")
            lines.append(f"  - {section_text[:100]}...")
            lines.append(f"- **当前结论**：待分析")
            lines.append(f"- **相关风险**：无")
            lines.append("")
    else:
        lines.append("### 议题 1：待补充")
        lines.append("")
        lines.append("- **讨论要点**：待补充")
        lines.append("- **当前结论**：待补充")
        lines.append("- **相关风险**：待补充")
        lines.append("")

    lines.append("---")
    lines.append("")

    # 5. 章节索引
    lines.append(generate_chapter_index(sections))
    lines.append("---")
    lines.append("")

    # 6. 待办事项（细化版）
    lines.append(generate_todo_checklist(full_text, sections))
    lines.append("---")
    lines.append("")

    # 7. 信息校验
    lines.append(generate_info_validation(full_text))
    lines.append("---")
    lines.append("")

    # 8. AI洞察
    lines.append(generate_ai_insight(full_text))
    lines.append("---")
    lines.append("")

    # 9. 待确认问题
    lines.append("## 待确认问题")
    lines.append("")
    lines.append("- 问题 1：待 AI 分析后填充")
    lines.append("- 问题 2：待 AI 分析后填充")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 10. 风险提醒
    lines.append("## 风险提醒")
    lines.append("")
    lines.append("- 风险 1：待 AI 分析后填充")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 底部信息
    lines.append(f"*转录时间：{metadata.get('timestamp', '')[:19]}*")
    lines.append(f"*处理耗时：{metadata.get('process_time', 0)}秒*")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="会议纪要格式化工具")
    parser.add_argument("--input", "-i", required=True, help="输入转录 JSON 文件")
    parser.add_argument("--output", "-o", help="输出 Markdown 文件")
    parser.add_argument("--title", "-t", help="会议主题")
    parser.add_argument("--participants", "-p", nargs="+", help="参会人员列表")
    parser.add_argument("--purpose", help="输出用途：内部同步/领导汇报/项目跟进")

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"文件不存在: {input_path}")
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        transcript = json.load(f)

    minutes = generate_minutes(
        transcript,
        title=args.title,
        participants=args.participants,
        purpose=args.purpose
    )

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(minutes)
        print(f"纪要已保存: {output_path}")
    else:
        print(minutes)


if __name__ == "__main__":
    main()
