#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HTML可视化报告生成脚本
使用模板文件生成美观的HTML格式日报分析报告
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

# 默认目录
DEFAULT_REPORTS_DIR = str(Path(__file__).parent.parent.parent.parent.parent / "daily-reports")
TEMPLATE_FILE = Path(__file__).parent.parent / "references" / "html_template.html"


def generate_html_report(analysis: Dict, scores: Dict, date_str: str) -> str:
    """使用模板生成HTML可视化报告"""
    
    # 读取模板文件
    if not TEMPLATE_FILE.exists():
        raise FileNotFoundError(f"模板文件不存在: {TEMPLATE_FILE}")
    
    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        template = f.read()
    
    # 准备基础数据 - 兼容不同的key名称
    should_submit = analysis.get("should_submit_count") or analysis.get("total_should_submit") or analysis.get("total_count", 0)
    submitted = analysis.get("total_count", 0)
    submit_rate = round(submitted / should_submit * 100, 1) if should_submit > 0 else 0
    avg_score = round(analysis.get("avg_score", 0), 1)
    ai_rate = round(analysis.get("ai_usage_rate", 0), 1)
    lazy_rate = round(analysis.get("lazy_report_rate", 0), 1)
    plan_rate = round(analysis.get("plan_rate", 0), 1)
    review_rate = round(analysis.get("review_rate", 0), 1)
    
    # 计算样式类
    submit_rate_class = "trend-good" if submit_rate >= 80 else "trend-warning" if submit_rate >= 50 else "trend-danger"
    avg_score_class = "trend-good" if avg_score >= 3 else "trend-warning" if avg_score >= 2 else "trend-danger"
    ai_rate_class = "trend-good" if ai_rate >= 30 else "trend-warning" if ai_rate >= 15 else "trend-danger"
    lazy_rate_class = "trend-good" if lazy_rate <= 20 else "trend-warning" if lazy_rate <= 40 else "trend-danger"
    plan_rate_class = "trend-good" if plan_rate >= 50 else "trend-warning" if plan_rate >= 30 else "trend-danger"
    review_rate_class = "trend-good" if review_rate >= 50 else "trend-warning" if review_rate >= 30 else "trend-danger"
    
    # 提示文字
    avg_score_tip = "表现良好" if avg_score >= 3 else "需提升" if avg_score >= 2 else "较差"
    ai_rate_tip = "活跃" if ai_rate >= 30 else "待推广"
    lazy_rate_tip = "正常" if lazy_rate <= 20 else "需改进"
    plan_rate_tip = "良好" if plan_rate >= 50 else "待提高"
    review_rate_tip = "良好" if review_rate >= 50 else "待提高"
    
    # 准备图表数据 - 兼容不同key名称
    dept_stats = analysis.get("dept_stats", {})
    dept_names = list(dept_stats.keys())
    dept_scores = [round(dept_stats[d].get("avg_score", 0), 1) for d in dept_names]
    dept_ai_rates = [round(dept_stats[d].get("ai_usage_rate", 0), 1) for d in dept_names]
    dept_submit_rates = []
    for d in dept_names:
        d_submitted = dept_stats[d].get("count", 0)
        # 兼容不同的key名称
        d_total = dept_stats[d].get("should_submit_count") or dept_stats[d].get("dept_total") or d_submitted
        rate = round(d_submitted / d_total * 100, 1) if d_total > 0 else 0
        dept_submit_rates.append(rate)
    
    # 分数分布数据
    dist = analysis.get("score_distribution", {})
    score_dist_labels = json.dumps(["优秀", "良好", "一般", "较差", "差"])
    score_dist_data = json.dumps([
        dist.get("excellent", 0),
        dist.get("good", 0),
        dist.get("average", 0),
        dist.get("poor", 0),
        dist.get("bad", 0)
    ])
    score_dist_colors = json.dumps(["#4ade80", "#22d3ee", "#fbbf24", "#fb923c", "#f87171"])
    
    # 部门分数图表 - 取TOP10
    top_depts = sorted(zip(dept_names, dept_scores), key=lambda x: x[1], reverse=True)[:10]
    dept_score_labels = json.dumps([d[0] for d in top_depts])
    dept_score_data = json.dumps([d[1] for d in top_depts])
    # 为不同部门生成不同颜色
    dept_score_colors = json.dumps([
        "#fbbf24" if i == 0 else "#94a3b8" if i == 1 else "#fb923c" if i == 2 else "#a78bfa" 
        for i in range(len(top_depts))
    ])
    
    # 替换所有占位符
    replacements = {
        "{{DATE}}": date_str,
        "{{SUBMITTED}}": str(submitted),
        "{{SHOULD_SUBMIT}}": str(should_submit),
        "{{AVG_SCORE}}": str(avg_score),
        "{{AI_RATE}}": str(ai_rate),
        "{{LAZY_RATE}}": str(lazy_rate),
        "{{PLAN_RATE}}": str(plan_rate),
        "{{REVIEW_RATE}}": str(review_rate),
        "{{SUBMIT_RATE}}": str(submit_rate),
        "{{SUBMIT_RATE_CLASS}}": submit_rate_class,
        "{{AVG_SCORE_CLASS}}": avg_score_class,
        "{{AVG_SCORE_TIP}}": avg_score_tip,
        "{{AI_RATE_CLASS}}": ai_rate_class,
        "{{AI_RATE_TIP}}": ai_rate_tip,
        "{{LAZY_RATE_CLASS}}": lazy_rate_class,
        "{{LAZY_RATE_TIP}}": lazy_rate_tip,
        "{{PLAN_RATE_CLASS}}": plan_rate_class,
        "{{PLAN_RATE_TIP}}": plan_rate_tip,
        "{{REVIEW_RATE_CLASS}}": review_rate_class,
        "{{REVIEW_RATE_TIP}}": review_rate_tip,
        "{{GENERATE_TIME}}": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "{{DEPT_TABLE_ROWS}}": _generate_dept_table(analysis),
        "{{AI_ITEMS}}": _generate_ai_list(analysis),
        "{{SUGGESTIONS}}": _generate_suggestions(analysis),
        "{{SCORE_DIST_LABELS}}": score_dist_labels,
        "{{SCORE_DIST_DATA}}": score_dist_data,
        "{{SCORE_DIST_COLORS}}": score_dist_colors,
        "{{DEPT_SCORE_LABELS}}": dept_score_labels,
        "{{DEPT_SCORE_DATA}}": dept_score_data,
        "{{DEPT_SCORE_COLORS}}": dept_score_colors,
    }
    
    result = template
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, value)
    
    return result


def _generate_dept_table(analysis: Dict) -> str:
    """生成部门排名表格"""
    dept_stats = analysis.get("dept_stats", {})
    
    # 按提交率降序排序，0提交的部门排最后
    def get_submit_rate(item):
        stats = item[1]
        submitted = stats.get('count', 0)
        should_submit = stats.get('should_submit_count') or stats.get('dept_total') or submitted
        if should_submit == 0:
            return -1  # 无数据的排最后
        rate = submitted / should_submit * 100
        return rate
    
    sorted_depts = sorted(
        dept_stats.items(), 
        key=get_submit_rate,
        reverse=True
    )
    
    rows = []
    for i, (dept, stats) in enumerate(sorted_depts, 1):
        submitted = stats.get('count', 0)
        # 兼容不同key名称
        should_submit = stats.get('should_submit_count') or stats.get('dept_total') or submitted
        submit_rate = round(submitted / should_submit * 100, 1) if should_submit > 0 else 0
        avg_score = round(stats.get("avg_score", 0), 1)
        ai_rate = round(stats.get("ai_usage_rate", 0), 1)
        lazy_rate = round(stats.get("lazy_report_rate", 0), 1)
        approval_rate = round(stats.get("approval_rate", 0), 1)
        
        # 判断是否为0提交部门
        is_zero = submitted == 0
        
        # 排名徽章
        if is_zero:
            rank_class = "rank-zero"
        elif i == 1:
            rank_class = "rank-1"
        elif i == 2:
            rank_class = "rank-2"
        elif i == 3:
            rank_class = "rank-3"
        else:
            rank_class = "rank-other"
        
        # 评分标签
        score_badge = "badge-success" if avg_score >= 3 else "badge-warning" if avg_score >= 2 else "badge-danger"
        if is_zero:
            score_badge = "badge-muted"
        
        # AI率标签
        ai_badge = "badge-success" if ai_rate >= 50 else "badge-warning" if ai_rate >= 20 else "badge-danger"
        if is_zero:
            ai_badge = "badge-muted"
        
        # 流水账标签
        lazy_badge = "badge-success" if lazy_rate <= 20 else "badge-warning" if lazy_rate <= 40 else "badge-danger"
        if is_zero:
            lazy_badge = "badge-muted"
        
        # 审批率标签
        approval_badge = "badge-success" if approval_rate >= 80 else "badge-warning" if approval_rate >= 50 else "badge-danger"
        if is_zero:
            approval_badge = "badge-muted"
        
        row_class = "zero-submit" if is_zero else ""
        
        rows.append(f'''
                        <tr class="{row_class}">
                            <td><span class="rank-badge {rank_class}">{i if not is_zero else '-'}</span></td>
                            <td>{dept}</td>
                            <td>{submitted}/{should_submit}</td>
                            <td><span class="badge {score_badge}">{submit_rate}%</span></td>
                            <td><span class="badge {ai_badge}">{avg_score}</span></td>
                            <td><span class="badge {lazy_badge}">{ai_rate}%</span></td>
                            <td><span class="badge {lazy_badge}">{lazy_rate}%</span></td>
                            <td><span class="badge {approval_badge}">{approval_rate}%</span></td>
                        </tr>
        ''')
    
    return "\n".join(rows)


def _generate_ai_list(analysis: Dict) -> str:
    """生成AI应用列表"""
    ai_apps = analysis.get("valuable_info", {}).get("ai_applications", [])
    
    # 过滤掉未使用的
    used_apps = [a for a in ai_apps if a.get("content") and 
                 a.get("content") not in ["无", "暂无", "null", "今日未使用", "未使用AI工具", "今日无应用", "未使用", "今日工作无ai相关内容"]]
    
    if not used_apps:
        return "<p style='color: #666; text-align: center; padding: 20px;'>暂无AI应用案例</p>"
    
    items = []
    for app in used_apps[:8]:
        content = app.get('content', '')[:100] if app.get('content') else ''
        items.append(f'''
                <div class="ai-item">
                    <div class="ai-user">{app.get('creator', '-')}</div>
                    <div class="ai-dept">{app.get('dept', '-')}</div>
                    <div class="ai-content">{content}</div>
                </div>
        ''')
    
    return "\n".join(items)


def _generate_lazy_table(scores: Dict) -> str:
    """生成流水账问题表格"""
    lazy_reports = scores.get("lazy_reports", [])
    
    if not lazy_reports:
        return "<tr><td colspan='3' style='text-align: center; color: #28a745;'>✅ 无流水账问题</td></tr>"
    
    rows = []
    for report in lazy_reports[:15]:
        rows.append(f'''
            <tr>
                <td>{report.get('creator_name', '-')}</td>
                <td>{report.get('dept_name', '-')}</td>
                <td><span class="badge badge-warning">{report.get('lazy_reason', '内容敷衍')}</span></td>
            </tr>
        ''')
    
    return "\n".join(rows)


def _generate_suggestions(analysis: Dict) -> str:
    """生成改进建议"""
    suggestions = []
    
    if analysis.get('ai_usage_rate', 0) < 30:
        suggestions.append({
            "icon": "🤖",
            "text": "AI工具应用率较低，建议推广AI工具在日常工作中的应用，如豆包、DeepSeek等可辅助查找规范、生成文案"
        })
    
    if analysis.get('lazy_report_rate', 0) > 20:
        suggestions.append({
            "icon": "⚠️",
            "text": f"流水账占比高达{analysis.get('lazy_report_rate', 0)}%，建议引导员工详细描述工作内容，避免只写项目名"
        })
    
    if analysis.get('plan_rate', 0) < 50:
        suggestions.append({
            "icon": "📋",
            "text": "明日计划填写率偏低，建议督促员工养成工作规划习惯，提前安排第二天工作"
        })
    
    if analysis.get('review_rate', 0) < 50:
        suggestions.append({
            "icon": "🔄",
            "text": "工作复盘填写率偏低，建议鼓励员工每日总结反思，记录亮点、问题和改进点"
        })
    
    if analysis.get('avg_score', 0) < 3:
        suggestions.append({
            "icon": "⭐",
            "text": "整体平均分偏低，建议加强日报填写培训，明确优秀日报标准"
        })
    
    if not suggestions:
        suggestions.append({
            "icon": "✅",
            "text": "各项指标表现良好，继续保持！"
        })
    
    return "\n".join([f'''
                <div class="suggestion-item">
                    <span class="suggestion-icon">{s["icon"]}</span>
                    <span>{s["text"]}</span>
                </div>
    ''' for s in suggestions])


def main():
    parser = argparse.ArgumentParser(description="HTML报告生成工具")
    parser.add_argument("--date", default="today", help="目标日期")
    parser.add_argument("--input", default=DEFAULT_REPORTS_DIR, help="输入目录")
    
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
        
        # 生成HTML报告
        html_content = generate_html_report(analysis, scores, date_str)
        output_file = input_dir / date_str / "report.html"
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        print(f"[INFO] HTML报告已生成: {output_file}")
        print(f"[SUCCESS] 可在浏览器中打开查看可视化报告")
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()