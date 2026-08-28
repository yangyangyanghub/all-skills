#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
报告生成脚本（增强版）
生成Markdown分析报告和Excel数据清单
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

# 默认目录（工作空间根目录）
DEFAULT_REPORTS_DIR = str(Path(__file__).parent.parent.parent.parent / "daily-reports")


def _clean_table_cell(text: str) -> str:
    """清理表格单元格内容，移除换行符"""
    if not text:
        return "-"
    # 替换换行符为空格
    text = text.replace('\n', ' ').replace('\r', ' ')
    # 移除多余空格
    text = ' '.join(text.split())
    return text


def generate_markdown_report(analysis: Dict, scores: Dict, date_str: str) -> str:
    """生成Markdown格式的分析报告"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 计算提交率
    total_should = analysis.get('total_should_submit', analysis['total_count'])
    total_submitted = analysis['total_count']
    submit_rate = round(total_submitted / max(total_should, 1) * 100, 1)
    
    # 审批效率数据
    approval_stats = analysis.get("approval_stats")
    
    lines = [
        f"# 日报分析报告 - {date_str}",
        "",
        f"> 分析时间：{now} | 应提交：{total_should}人 | 已提交：{total_submitted}人 | 平均分：{analysis['avg_score']}",
        "",
        "---",
        "",
        "## 一、整体概况",
        "",
        "| 指标 | 数值 | 说明 |",
        "|------|------|------|",
        f"| 应提交人数 | {total_should}人 | 部门总人数 |",
        f"| 已提交人数 | {total_submitted}人 | 当日提交日报人数 |",
        f"| 提交率 | {submit_rate}% | 已提交/应提交 |",
        f"| 平均得分 | {analysis['avg_score']}分 | 六维度综合评分 |",
        f"| 🤖 AI使用率 | {analysis.get('ai_usage_rate', 0)}% | 使用AI人数/应提交人数 |",
        f"| ⚠️ 流水账率 | {analysis.get('lazy_report_rate', 0)}% | 流水账人数/应提交人数 |",
        f"| 📋 计划率 | {analysis.get('plan_rate', 0)}% | 有计划人数/应提交人数 |",
        f"| 🔄 复盘率 | {analysis.get('review_rate', 0)}% | 有复盘人数/应提交人数 |",
    ]
    
    # 审批效率指标并入核心指标
    if approval_stats:
        lines.extend([
            f"| ⚡ 审批完成率 | {approval_stats.get('completion_rate', 0)}% | 审批已通过/已提交 |",
            f"| ⏱️ 平均审批耗时 | {approval_stats.get('avg_total_duration_hours', 0)}小时 | 从提交到审批完成 |",
            f"| ⏰ 平均首审延迟 | {approval_stats.get('avg_first_approve_delay_hours', 0)}小时 | 部门主管审批等待时间 |",
        ])
    
    # 分数分布
    dist = analysis.get("score_distribution", {})
    total = analysis["total_count"]
    
    lines.extend([
        "",
        "### 📈 分数分布",
        "",
        "| 等级 | 人数 | 占比 |",
        "|------|------|------|",
    ])
    
    level_names = {
        "excellent": ("优秀(4.5+)", "🌟"),
        "good": ("良好(3.5-4.4)", "👍"),
        "average": ("一般(2.5-3.4)", "👌"),
        "poor": ("较差(1.5-2.4)", "⚠️"),
        "bad": ("差(0-1.4)", "❌")
    }
    
    for key, (name, emoji) in level_names.items():
        count = dist.get(key, 0)
        rate = count / total * 100 if total else 0
        lines.append(f"| {emoji} {name} | {count}人 | {rate:.1f}% |")
    
    # 二、部门综合分析
    dept_stats = analysis.get("dept_stats", {})
    completion_stats = analysis.get("completion_stats", {})
    
    # 构建完整的部门列表（包含未提交日报的部门）
    all_depts = {}
    
    # 先添加completion_stats中的所有部门（确保包含未提交的部门，院部除外）
    if completion_stats:
        for dept, stats in completion_stats.items():
            if dept == "总览" or dept == "院部":
                continue
            all_depts[dept] = {
                "dept_total": stats.get("should_submit", 0),
                "submitted": stats.get("submitted", 0),
                "submission_rate": stats.get("rate", 0),
                "avg_score": "-",
                "ai_usage_rate": "-",
                "lazy_report_rate": "-",
                "plan_rate": "-",
                "review_rate": "-"
            }
    
    # 用dept_stats的数据覆盖（已提交的部门有详细数据）
    if dept_stats:
        for dept, stats in dept_stats.items():
            all_depts[dept] = {
                "dept_total": stats.get("dept_total", stats.get("count", 0)),
                "submitted": stats.get("count", 0),
                "submission_rate": stats.get("submission_rate", 0),
                "avg_score": stats.get("avg_score", "-"),
                "max_score": stats.get("max_score", "-"),
                "min_score": stats.get("min_score", "-"),
                "ai_usage_rate": stats.get("ai_usage_rate", "-"),
                "lazy_report_rate": stats.get("lazy_report_rate", "-"),
                "plan_rate": stats.get("plan_rate", "-"),
                "review_rate": stats.get("review_rate", "-"),
                "approval_rate": stats.get("approval_rate", "-")
            }
    
    if all_depts:
        lines.extend([
            "",
            "---",
            "",
            "## 二、部门综合分析",
            "",
            "### 汇总表",
            "",
            "| 部门 | 已提交/总人数 | 提交率 | 平均分 | AI使用率 | 流水账率 | 计划率 | 复盘率 | 审批率 |",
            "|------|---------------|--------|--------|----------|----------|--------|--------|--------|"
        ])
        
        # 按提交率排序
        sorted_depts = sorted(all_depts.items(), key=lambda x: x[1].get("submission_rate", 0), reverse=True)
        
        for dept, stats in sorted_depts:
            submitted = stats.get('submitted', 0)
            total_dept = stats.get('dept_total', 0)
            submission_rate = stats.get('submission_rate', 0)
            avg = stats.get("avg_score", "-")
            ai_rate = stats.get("ai_usage_rate", "-")
            lazy_rate = stats.get("lazy_report_rate", "-")
            plan_rate = stats.get("plan_rate", "-")
            review_rate = stats.get("review_rate", "-")
            approval_rate = stats.get("approval_rate", "-")
            
            # 评级
            submit_emoji = "✅" if submission_rate >= 90 else "⚠️" if submission_rate >= 70 else "❌"
            score_emoji = "🌟" if avg != "-" and avg >= 4 else "👍" if avg != "-" and avg >= 3 else "👌" if avg != "-" and avg >= 2.5 else "⚠️" if avg != "-" else "-"
            lazy_emoji = "❌" if lazy_rate != "-" and lazy_rate >= 50 else "⚠️" if lazy_rate != "-" and lazy_rate >= 30 else "✅" if lazy_rate != "-" else "-"
            approval_emoji = "✅" if approval_rate != "-" and approval_rate >= 80 else "⚠️" if approval_rate != "-" and approval_rate >= 50 else "❌" if approval_rate != "-" else "-"
            
            # 处理 "-" 的情况
            avg_str = f"{score_emoji} {avg}" if avg != "-" else "-"
            ai_str = f"{ai_rate}%" if ai_rate != "-" else "-"
            lazy_str = f"{lazy_emoji} {lazy_rate}%" if lazy_rate != "-" else "-"
            plan_str = f"{plan_rate}%" if plan_rate != "-" else "-"
            review_str = f"{review_rate}%" if review_rate != "-" else "-"
            approval_str = f"{approval_emoji} {approval_rate}%" if approval_rate != "-" else "-"
            
            lines.append(
                f"| {dept} | {submitted}/{total_dept} | {submit_emoji} {submission_rate}% | {avg_str} | "
                f"{ai_str} | {lazy_str} | {plan_str} | {review_str} | {approval_str} |"
            )
        
        # 各部门详情
        lines.extend([
            "",
            "### 部门详情",
            ""
        ])
        
        for dept, stats in sorted_depts:
            submitted = stats.get('submitted', 0)
            total_dept = stats.get('dept_total', 0)
            submission_rate = stats.get('submission_rate', 0)
            avg = stats.get("avg_score", "-")
            max_score = stats.get("max_score", "-")
            min_score = stats.get("min_score", "-")
            ai_rate = stats.get("ai_usage_rate", "-")
            lazy_rate = stats.get("lazy_report_rate", "-")
            plan_rate = stats.get("plan_rate", "-")
            review_rate = stats.get("review_rate", "-")
            
            # 如果没有提交日报，跳过详情
            if submitted == 0:
                continue
            
            # 简短评语
            if avg != "-" and avg >= 3:
                comment = "整体表现良好"
            elif avg != "-" and avg >= 2.5:
                comment = "表现一般，有改进空间"
            else:
                comment = "需要重点关注"
            
            if lazy_rate != "-" and lazy_rate >= 50:
                comment += "，流水账问题严重"
            
            # 处理评级显示
            avg_rating = "👍" if avg != "-" and avg >= 3 else "⚠️" if avg != "-" else "-"
            ai_rating = "👍" if ai_rate != "-" and ai_rate >= 30 else "⚠️" if ai_rate != "-" else "-"
            lazy_rating = "✅" if lazy_rate != "-" and lazy_rate <= 30 else "❌" if lazy_rate != "-" else "-"
            plan_rating = "👍" if plan_rate != "-" and plan_rate >= 50 else "⚠️" if plan_rate != "-" else "-"
            review_rating = "👍" if review_rate != "-" and review_rate >= 50 else "⚠️" if review_rate != "-" else "-"
            
            lines.extend([
                f"#### {dept}",
                "",
                f"> {comment}",
                "",
                "| 指标 | 数值 | 评级 |",
                "|------|------|------|",
                f"| 提交人数 | {submitted}/{total_dept} | {'✅' if submission_rate >= 90 else '⚠️'} |",
                f"| 平均得分 | {avg}分 | {avg_rating} |",
                f"| 最高分 | {max_score if max_score != '-' else '-'}分 | - |",
                f"| 最低分 | {min_score if min_score != '-' else '-'}分 | - |",
                f"| AI使用率 | {ai_rate if ai_rate != '-' else '-'}% | {ai_rating} |",
                f"| 流水账率 | {lazy_rate if lazy_rate != '-' else '-'}% | {lazy_rating} |",
                f"| 计划率 | {plan_rate if plan_rate != '-' else '-'}% | {plan_rating} |",
                f"| 复盘率 | {review_rate if review_rate != '-' else '-'}% | {review_rating} |",
                ""
            ])
    
    # 三、审批效率详情
    if approval_stats:
        dept_approval = approval_stats.get("dept_approval_stats", {})
        if dept_approval:
            lines.extend([
                "---",
                "",
                "## 三、审批效率详情",
                "",
                "| 排名 | 部门 | 提交 | 完成 | 完成率 | 平均耗时 |",
                "|------|------|------|------|--------|----------|"
            ])
            
            sorted_approval = sorted(
                dept_approval.items(),
                key=lambda x: x[1].get("completion_rate", 0),
                reverse=True
            )
            
            for i, (dept, stats) in enumerate(sorted_approval, 1):
                lines.append(
                    f"| {i} | {dept} | {stats.get('total', 0)} | {stats.get('completed', 0)} | "
                    f"{stats.get('completion_rate', 0)}% | {stats.get('avg_duration_hours', 0)}小时 |"
                )
            lines.append("")
    
    # 四、AI工具应用案例
    valuable = analysis.get("valuable_info", {})
    ai_apps = valuable.get("ai_applications", [])
    
    if ai_apps:
        lines.extend([
            "---",
            "",
            "## 四、🤖 AI工具应用案例",
            "",
            "| 使用者 | 部门 | AI应用情况 |",
            "|--------|------|------------|"
        ])
        
        for item in ai_apps[:15]:
            creator = _clean_table_cell(item.get("creator", "-"))
            dept = _clean_table_cell(item.get("dept", "-"))
            content = _clean_table_cell(item.get("content", ""))[:60]
            lines.append(f"| {creator} | {dept} | {content} |")
        
        lines.append("")
    
    # 五、流水账问题
    lazy_reports = scores.get("lazy_reports", [])
    
    if lazy_reports:
        lines.extend([
            "---",
            "",
            "## 五、⚠️ 流水账问题日报",
            "",
            "> 以下日报存在内容敷衍问题，建议关注",
            "",
            "| 提交人 | 部门 | 问题原因 |",
            "|--------|------|----------|"
        ])
        
        for item in lazy_reports[:10]:
            creator = _clean_table_cell(item.get("creator_name", "-"))
            dept = _clean_table_cell(item.get("dept_name", "-"))
            reason = _clean_table_cell(item.get("lazy_reason", "内容敷衍"))
            lines.append(f"| {creator} | {dept} | {reason} |")
        
        lines.append("")
    
    # 六、改进建议
    lines.extend([
        "---",
        "",
        "## 六、📝 改进建议",
        ""
    ])
    
    suggestions = []
    
    if analysis.get('ai_usage_rate', 0) < 30:
        suggestions.append("1. **AI工具应用**: 使用率较低，建议推广AI工具在日常工作中的应用")
    
    if analysis.get('lazy_report_rate', 0) > 20:
        suggestions.append("2. **日报质量**: 流水账率较高，建议引导员工详细描述工作内容")
    
    if analysis.get('plan_rate', 0) < 50:
        suggestions.append("3. **工作计划**: 计划填写率偏低，建议督促员工养成工作规划习惯")
    
    if analysis.get('review_rate', 0) < 50:
        suggestions.append("4. **工作复盘**: 复盘填写率偏低，建议鼓励员工每日总结反思")
    
    if submit_rate < 80:
        suggestions.append("5. **提交率**: 提交率偏低，建议督促未提交人员及时填写")
    
    if suggestions:
        lines.extend(suggestions)
    else:
        lines.append("✅ 各项指标表现良好，继续保持！")
    
    lines.append("")
    
    # 底部说明
    lines.extend([
        "---",
        "",
        "*本报告由AI自动分析生成，如有疑问请人工复核。*"
    ])
    
    return "\n".join(lines)


def generate_excel_data(analysis: Dict, scores: Dict, output_dir: Path) -> None:
    """生成Excel数据清单"""
    if not HAS_PANDAS:
        print("[WARN] 未安装pandas，跳过Excel生成。请运行: pip install pandas openpyxl")
        return
    
    details = scores.get("details", [])
    valuable = analysis.get("valuable_info", {})
    lazy_reports = scores.get("lazy_reports", [])
    
    output_path = output_dir / "data-list.xlsx"
    
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        # Sheet1: 员工评分明细
        if details:
            df_scores = pd.DataFrame([{
                "姓名": d.get("creator_name"),
                "部门": d.get("dept_name"),
                "综合分": d.get("scores", {}).get("total"),
                "完整度": d.get("scores", {}).get("completeness"),
                "内容质量": d.get("scores", {}).get("content_quality"),
                "AI应用": d.get("scores", {}).get("ai_application"),
                "及时性": d.get("scores", {}).get("timeliness"),
                "工作量": d.get("scores", {}).get("workload"),
                "计划性": d.get("scores", {}).get("planning"),
                "是否流水账": "是" if d.get("is_lazy_report") else "否",
                "AI应用情况": d.get("ai_usage") or "未使用",
                "字数": d.get("word_count", 0),
                "有复盘": "是" if d.get("has_review") else "否",
                "有计划": "是" if d.get("has_plan") else "否"
            } for d in details])
            df_scores.to_excel(writer, sheet_name="员工评分明细", index=False)
        
        # Sheet2: AI应用案例
        ai_apps = valuable.get("ai_applications", [])
        if ai_apps:
            df_ai = pd.DataFrame([{
                "使用者": a.get("creator"),
                "部门": a.get("dept"),
                "AI应用情况": a.get("content", "")[:100]
            } for a in ai_apps])
            df_ai.to_excel(writer, sheet_name="AI应用案例", index=False)
        
        # Sheet3: 流水账问题清单
        if lazy_reports:
            df_lazy = pd.DataFrame([{
                "提交人": r.get("creator_name"),
                "部门": r.get("dept_name"),
                "问题原因": r.get("lazy_reason"),
                "工作内容长度": r.get("work_done_length", 0)
            } for r in lazy_reports])
            df_lazy.to_excel(writer, sheet_name="流水账问题清单", index=False)
        
        # Sheet4: 部门统计
        dept_stats = analysis.get("dept_stats", {})
        if dept_stats:
            df_dept = pd.DataFrame([{
                "部门": dept,
                "总人数": stats.get("dept_total", stats.get("count")),
                "已提交": stats.get("count"),
                "提交率": f"{stats.get('submission_rate', 100)}%",
                "平均分": stats.get("avg_score"),
                "AI使用率": f"{stats.get('ai_usage_rate', 0)}%",
                "流水账率": f"{stats.get('lazy_report_rate', 0)}%",
                "计划率": f"{stats.get('plan_rate', 0)}%",
                "复盘率": f"{stats.get('review_rate', 0)}%"
            } for dept, stats in dept_stats.items()])
            df_dept.to_excel(writer, sheet_name="部门统计", index=False)
    
    print(f"[INFO] Excel数据清单已保存到: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="报告生成工具")
    parser.add_argument(
        "--date",
        default="today",
        help="目标日期"
    )
    parser.add_argument(
        "--input",
        default=DEFAULT_REPORTS_DIR,
        help=f"输入目录 (默认: {DEFAULT_REPORTS_DIR})"
    )
    
    args = parser.parse_args()
    
    try:
        # 解析日期
        if args.date == "today":
            date_str = datetime.now().strftime("%Y-%m-%d")
        elif args.date == "yesterday":
            date_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            date_str = args.date
        
        # 读取分析结果
        input_dir = Path(args.input)
        analysis_file = input_dir / date_str / "analysis.json"
        scores_file = input_dir / date_str / "scores.json"
        
        if not analysis_file.exists():
            print(f"[ERROR] 未找到分析结果文件: {analysis_file}")
            sys.exit(1)
        
        with open(analysis_file, "r", encoding="utf-8") as f:
            analysis = json.load(f)
        
        scores = {}
        if scores_file.exists():
            with open(scores_file, "r", encoding="utf-8") as f:
                scores = json.load(f)
        
        output_dir = input_dir / date_str
        
        # 生成Markdown报告
        md_content = generate_markdown_report(analysis, scores, date_str)
        md_file = output_dir / "daily-report.md"
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f"[INFO] Markdown报告已保存到: {md_file}")
        
        # 生成Excel清单
        generate_excel_data(analysis, scores, output_dir)
        
        print("\n[SUCCESS] 报告生成完成！")
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()