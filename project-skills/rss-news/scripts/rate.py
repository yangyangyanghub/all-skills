#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import io

# 设置控制台编码为 UTF-8 (Windows)
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass
"""
RSS 新闻评分脚本
功能：
1. 读取收集的新闻
2. 规则评分（1-5分）
3. 智能分类
4. 输出 Markdown 文件
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# 配置
SKILL_DIR = Path(__file__).parent.parent
CATEGORIES_JSON = SKILL_DIR / "references" / "categories.json"
OUTPUT_DIR = Path("E:/code/my-ai-workspace/dailynews")


def load_categories() -> dict:
    """加载分类规则"""
    with open(CATEGORIES_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def classify_news(news: dict, categories: dict) -> str:
    """根据关键词分类新闻"""
    content = (news.get("title", "") + " " + 
               news.get("ai_summary", "") + " " + 
               news.get("summary", "")).lower()
    
    priority_order = categories.get("priorityOrder", [])
    default_category = categories.get("defaultCategory", "其他")
    
    # 按优先级顺序匹配
    for category in priority_order:
        if category in categories.get("categories", {}):
            keywords = categories["categories"][category].get("keywords", [])
            for kw in keywords:
                if kw.lower() in content:
                    return category
    
    return default_category


def calculate_score(news: dict, categories: dict) -> int:
    """
    规则评分（1-5分）
    评分维度：
    - 来源权威性
    - 内容完整性
    - 关键词匹配
    - 日期时效性
    """
    score = 3  # 基础分
    
    # 1. 来源权威性加分
    high_quality_sources = [
        "自然资源部", "国家发展改革委", "中国测绘学会", "中国计算机学会",
        "国家数据局", "中国城市规划", "遥感学报", "测绘学报"
    ]
    source = news.get("source", "")
    for hqs in high_quality_sources:
        if hqs in source:
            score += 1
            break
    
    # 2. 内容完整性加分
    content = news.get("content", "") or ""
    summary = news.get("ai_summary", "") or ""
    
    if len(content) > 1000:
        score += 1
    if len(summary) > 20:
        score += 1
    
    # 3. 关键词匹配加分
    important_keywords = [
        "政策", "发布", "标准", "规范", "自然资源", "测绘", "遥感",
        "AI", "大模型", "发布", "试点", "管理办法"
    ]
    
    title = news.get("title", "")
    full_text = title + " " + summary + " " + content[:500]
    
    keyword_count = sum(1 for kw in important_keywords if kw in full_text)
    if keyword_count >= 3:
        score += 1
    
    # 4. 要点数量加分
    points = news.get("ai_points", [])
    if len(points) >= 3:
        score += 1
    
    # 5. 扣分项
    if not summary and not content:
        score -= 1
    if len(title) < 10:
        score -= 1
    
    # 限制在 1-5 分
    return max(1, min(5, score))


def format_news_item(news: dict, index: int) -> str:
    """格式化单条新闻为 Markdown"""
    score = news.get("score", 3)
    score_icon = "⭐" * score
    
    # 标题和分数
    lines = [
        f"### {index}. {news['title']}",
        f"> **来源**: {news.get('source', '未知')} | **日期**: {news.get('pub_date', '')} | **评分**: {score_icon}",
        ""
    ]
    
    # AI 摘要
    if news.get("ai_summary"):
        lines.append(f"**一句话总结**: {news['ai_summary']}")
        lines.append("")
    
    # 要点列表
    if news.get("ai_points"):
        lines.append("**要点**:")
        for point in news["ai_points"]:
            lines.append(f"- {point}")
        lines.append("")
    
    # 详情链接
    if news.get("link"):
        lines.append(f"**原文链接**: [查看原文]({news['link']})")
        lines.append("")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="RSS 新闻评分脚本")
    parser.add_argument("--date", type=str, default="today", help="目标日期 YYYY-MM-DD")
    parser.add_argument("--min-score", type=int, default=1, help="最低分数过滤")
    args = parser.parse_args()
    
    # 处理日期参数
    if args.date == "today":
        target_date = datetime.now().strftime("%Y-%m-%d")
    else:
        target_date = args.date
    
    print(f"📅 评分目标日期: {target_date}")
    
    # 加载分类规则
    print("📂 加载分类规则...")
    categories = load_categories()
    
    # 读取原始新闻
    raw_file = OUTPUT_DIR / target_date / "raw_news.json"
    if not raw_file.exists():
        print(f"❌ 错误: 找不到原始数据文件 {raw_file}")
        print(f"   请先运行: python scripts/collect.py --date={target_date}")
        sys.exit(1)
    
    with open(raw_file, "r", encoding="utf-8") as f:
        news_list = json.load(f)
    
    print(f"📊 共 {len(news_list)} 条新闻待评分")
    
    # 评分和分类
    print("✍️  正在评分和分类...")
    scored_news = []
    
    for i, news in enumerate(news_list):
        score = calculate_score(news, categories)
        category = classify_news(news, categories)
        
        news["score"] = score
        news["category"] = category
        scored_news.append(news)
        
        print(f"  [{i+1}/{len(news_list)}] {score}分 - {category}")
    
    # 按分数排序
    scored_news.sort(key=lambda x: x["score"], reverse=True)
    
    # 按分类分组
    grouped = defaultdict(list)
    for news in scored_news:
        if news["score"] >= args.min_score:
            grouped[news["category"]].append(news)
    
    # 生成 Markdown
    print("\n📝 生成 Markdown 报告...")
    
    lines = [
        f"# 每日新闻汇总 - {target_date}",
        "",
        f"**收集时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**新闻总数**: {len(news_list)}",
        f"**评分过滤**: ≥{args.min_score}分",
        "",
        "---",
        "",
    ]
    
    # 按优先级顺序输出
    priority_order = categories.get("priorityOrder", [])
    
    # 确保所有分类都输出
    all_categories = set(grouped.keys())
    output_order = []
    for cat in priority_order:
        if cat in all_categories:
            output_order.append(cat)
    for cat in all_categories:
        if cat not in output_order:
            output_order.append(cat)
    
    for category in output_order:
        cat_news = grouped[category]
        if not cat_news:
            continue
        
        lines.append(f"## {category} ({len(cat_news)}条)")
        lines.append("")
        
        for i, news in enumerate(cat_news, 1):
            lines.append(format_news_item(news, i))
        
        lines.append("")
        lines.append("---")
        lines.append("")
    
    # 分数统计
    lines.append("## 评分统计")
    lines.append("")
    
    score_dist = defaultdict(int)
    for news in scored_news:
        score_dist[news["score"]] += 1
    
    lines.append("| 分数 | 数量 |")
    lines.append("|------|------|")
    for score in range(5, 0, -1):
        count = score_dist[score]
        bar = "█" * count
        lines.append(f"| {score}分 | {count} {bar} |")
    
    lines.append("")
    
    # 保存
    output_file = OUTPUT_DIR / target_date / "news.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    print(f"\n✅ 完成!")
    print(f"   输出文件: {output_file}")
    print(f"   有效新闻: {sum(len(v) for v in grouped.values())}条")


if __name__ == "__main__":
    main()