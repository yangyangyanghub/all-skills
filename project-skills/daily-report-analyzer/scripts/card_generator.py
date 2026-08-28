#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OpenClaw卡片生成器
生成适合钉钉AI卡片的日报分析结果
"""

import json
from typing import Dict, List, Any
from datetime import datetime


def generate_ai_card_content(analysis: Dict) -> Dict[str, Any]:
    """
    生成AI卡片内容
    
    Args:
        analysis: 分析结果数据
        
    Returns:
        卡片内容结构
    """
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    # 构建卡片内容
    card = {
        "title": f"📊 日报分析报告 - {date_str}",
        "summary": {
            "total": analysis["total_count"],
            "avg_score": analysis["avg_score"],
            "distribution": analysis["score_distribution"]
        },
        "departments": [],
        "valuable_info": {
            "outputs": [],
            "resources": [],
            "risks": []
        }
    }
    
    # 部门分析
    for dept, stats in analysis.get("dept_stats", {}).items():
        card["departments"].append({
            "name": dept,
            "count": stats["count"],
            "avg_score": stats["avg_score"],
            "rating": _get_rating(stats["avg_score"])
        })
    
    # 有价值信息
    valuable = analysis.get("valuable_info", {})
    
    for item in valuable.get("project_outputs", [])[:5]:
        card["valuable_info"]["outputs"].append({
            "content": item.get("content", "")[:50],
            "creator": item.get("creator", "-")
        })
    
    for item in valuable.get("data_resources", [])[:3]:
        card["valuable_info"]["resources"].append({
            "content": item.get("content", "")[:50],
            "creator": item.get("creator", "-")
        })
    
    for item in valuable.get("risk_warnings", [])[:3]:
        card["valuable_info"]["risks"].append({
            "content": item.get("content", "")[:50],
            "creator": item.get("creator", "-"),
            "dept": item.get("dept", "-")
        })
    
    return card


def generate_card_markdown(analysis: Dict) -> str:
    """
    生成Markdown格式的卡片内容（适合流式输出）
    
    Args:
        analysis: 分析结果数据
        
    Returns:
        Markdown文本
    """
    date_str = datetime.now().strftime("%Y-%m-%d")
    lines = []
    
    # 标题
    lines.append(f"## 📊 日报分析报告")
    lines.append(f"**日期**: {date_str}")
    lines.append("")
    
    # 整体概况
    lines.append("### 📈 整体概况")
    lines.append("")
    lines.append(f"| 指标 | 数值 |")
    lines.append(f"|------|------|")
    lines.append(f"| 提交人数 | {analysis['total_count']}人 |")
    lines.append(f"| 平均得分 | {analysis['avg_score']}分 |")
    lines.append("")
    
    # 分数分布
    dist = analysis.get("score_distribution", {})
    lines.append("### 📊 分数分布")
    lines.append("")
    lines.append(f"- 🌟 优秀(4.5+): {dist.get('excellent', 0)}人")
    lines.append(f"- ⭐ 良好(3.5-4.4): {dist.get('good', 0)}人")
    lines.append(f"- 📝 一般(2.5-3.4): {dist.get('average', 0)}人")
    lines.append(f"- ⚠️ 较差(1.5-2.4): {dist.get('poor', 0)}人")
    lines.append(f"- ❌ 差(0-1.4): {dist.get('bad', 0)}人")
    lines.append("")
    
    # 部门TOP3
    dept_stats = analysis.get("dept_stats", {})
    if dept_stats:
        lines.append("### 🏆 部门排名 TOP3")
        lines.append("")
        sorted_depts = sorted(dept_stats.items(), key=lambda x: x[1]["avg_score"], reverse=True)[:3]
        for i, (dept, stats) in enumerate(sorted_depts, 1):
            rating = _get_rating(stats["avg_score"])
            lines.append(f"{i}. **{dept}**: {stats['avg_score']}分 {rating} ({stats['count']}人)")
        lines.append("")
    
    # 有价值信息
    valuable = analysis.get("valuable_info", {})
    
    # 风险预警（优先展示）
    risks = valuable.get("risk_warnings", [])
    if risks:
        lines.append("### ⚠️ 风险预警")
        lines.append("")
        for risk in risks[:3]:
            content = risk.get("content", "")[:60]
            creator = risk.get("creator", "-")
            lines.append(f"- {content}... _@{creator}_")
        lines.append("")
    
    # 项目产出
    outputs = valuable.get("project_outputs", [])
    if outputs:
        lines.append("### ✅ 项目产出")
        lines.append("")
        for output in outputs[:5]:
            content = output.get("content", "")[:50]
            creator = output.get("creator", "-")
            lines.append(f"- {content}... _@{creator}_")
        lines.append("")
    
    # 数据资源
    resources = valuable.get("data_resources", [])
    if resources:
        lines.append("### 📦 数据资源")
        lines.append("")
        for res in resources[:3]:
            content = res.get("content", "")[:50]
            creator = res.get("creator", "-")
            lines.append(f"- {content}... _@{creator}_")
        lines.append("")
    
    # 底部说明
    lines.append("---")
    lines.append("*由AI自动分析生成，如有疑问请人工复核*")
    
    return "\n".join(lines)


def generate_brief_text(analysis: Dict) -> str:
    """
    生成简短文本（适合快速预览）
    
    Args:
        analysis: 分析结果数据
        
    Returns:
        简短文本
    """
    date_str = datetime.now().strftime("%Y-%m-%d")
    total = analysis["total_count"]
    avg = analysis["avg_score"]
    dist = analysis.get("score_distribution", {})
    
    excellent = dist.get("excellent", 0)
    good = dist.get("good", 0)
    
    risks = len(analysis.get("valuable_info", {}).get("risk_warnings", []))
    
    brief = (
        f"📊 **{date_str} 日报分析**\n"
        f"提交{total}人，平均{avg}分\n"
        f"优秀/良好: {excellent}/{good}人\n"
    )
    
    if risks > 0:
        brief += f"⚠️ 发现{risks}条风险预警\n"
    
    brief += "\n回复「详情」查看完整报告"
    
    return brief


def _get_rating(score: float) -> str:
    """根据分数获取评级"""
    if score >= 4.5:
        return "🌟🌟🌟🌟🌟"
    elif score >= 4.0:
        return "🌟🌟🌟🌟"
    elif score >= 3.5:
        return "🌟🌟🌟"
    elif score >= 3.0:
        return "🌟🌟"
    else:
        return "🌟"


# OpenClaw 插件入口
def handle_message(message: str, context: Dict) -> str:
    """
    处理用户消息（OpenClaw插件入口）
    
    Args:
        message: 用户消息
        context: 上下文信息
        
    Returns:
        回复内容
    """
    import os
    import sys
    from pathlib import Path
    
    # 获取脚本目录
    script_dir = Path(__file__).parent
    
    # 解析日期
    date_str = "today"
    if "昨天" in message or "昨日" in message:
        date_str = "yesterday"
    elif "前天" in message:
        date_str = "yesterday"  # 简化处理
    
    # 解析部门
    dept_filter = None
    # TODO: 从消息中提取部门名称
    
    try:
        # 执行分析
        from analyze_reports import ReportAnalyzer
        
        # 读取日报数据
        if date_str == "today":
            from datetime import datetime, timedelta
            date_path = datetime.now().strftime("%Y-%m-%d")
        else:
            from datetime import datetime, timedelta
            date_path = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        reports_file = Path("reports") / date_path / "raw_reports.json"
        
        if not reports_file.exists():
            return f"❌ 未找到 {date_path} 的日报数据，请先获取日报。"
        
        with open(reports_file, "r", encoding="utf-8") as f:
            reports = json.load(f)
        
        # 分析
        analyzer = ReportAnalyzer()
        results = analyzer.analyze_all(reports)
        
        # 生成回复
        if "详情" in message:
            return generate_card_markdown(results)
        else:
            return generate_brief_text(results)
            
    except Exception as e:
        return f"❌ 分析失败: {str(e)}"


if __name__ == "__main__":
    # 测试
    test_analysis = {
        "total_count": 50,
        "avg_score": 3.85,
        "score_distribution": {
            "excellent": 8,
            "good": 22,
            "average": 15,
            "poor": 4,
            "bad": 1
        },
        "dept_stats": {
            "研发部": {"count": 20, "avg_score": 4.2},
            "产品部": {"count": 10, "avg_score": 3.8},
            "运营部": {"count": 15, "avg_score": 3.5}
        },
        "valuable_info": {
            "project_outputs": [
                {"content": "完成用户模块开发", "creator": "张三"},
                {"content": "上线API v2.0", "creator": "李四"}
            ],
            "risk_warnings": [
                {"content": "接口联调延期风险", "creator": "王五", "dept": "研发部"}
            ]
        }
    }
    
    print("=== Markdown 卡片 ===")
    print(generate_card_markdown(test_analysis))
    print("\n=== 简短文本 ===")
    print(generate_brief_text(test_analysis))