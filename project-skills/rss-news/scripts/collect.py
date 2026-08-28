#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RSS 新闻收集脚本（多线程版）
功能：
1. 从 OPML 读取 RSS 源列表
2. 多线程并行抓取新闻，按日期过滤
3. 智能合并重复新闻
4. 规则自动摘要
"""

import sys
import io

# 设置控制台编码为 UTF-8 (Windows)
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

import argparse
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from threading import Lock

try:
    import feedparser
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("请安装依赖: pip install feedparser requests beautifulsoup4")
    sys.exit(1)

# 配置
SKILL_DIR = Path(__file__).parent.parent
FEEDS_OPML = SKILL_DIR / "references" / "feeds.opml"
CATEGORIES_JSON = SKILL_DIR / "references" / "categories.json"
OUTPUT_DIR = Path("E:/code/my-ai-workspace/dailynews")

# 并发配置
DEFAULT_WORKERS = 10
DEFAULT_TIMEOUT = 8


def parse_opml(opml_path: Path) -> list[dict]:
    """解析 OPML 文件获取 RSS 源列表"""
    import xml.etree.ElementTree as ET
    
    sources = []
    try:
        tree = ET.parse(opml_path)
        root = tree.getroot()
        
        for outline in root.findall(".//outline"):
            xml_url = outline.get("xmlUrl")
            if xml_url:
                sources.append({
                    "title": outline.get("title", ""),
                    "xmlUrl": xml_url,
                    "htmlUrl": outline.get("htmlUrl", xml_url)
                })
    except Exception as e:
        print(f"解析 OPML 失败: {e}")
    
    return sources


def fetch_feed(source: dict, target_date: str, timeout: int = DEFAULT_TIMEOUT) -> list[dict]:
    """抓取单个 RSS 源，返回目标日期的新闻"""
    news_list = []
    try:
        response = requests.get(
            source["xmlUrl"], 
            timeout=timeout, 
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
            allow_redirects=True
        )
        feed = feedparser.parse(response.content)
        
        for entry in feed.entries[:20]:
            # 解析发布日期
            pub_date = None
            if hasattr(entry, "published"):
                try:
                    pub_date = datetime(*entry.published_parsed[:6])
                except:
                    pass
            elif hasattr(entry, "updated"):
                try:
                    pub_date = datetime(*entry.updated_parsed[:6])
                except:
                    pass
            
            # 检查日期是否匹配
            if pub_date:
                if pub_date.strftime("%Y-%m-%d") != target_date:
                    continue
            else:
                # 没有日期信息，标题中查找日期
                title = entry.title if hasattr(entry, "title") else ""
                title_date_match = re.search(r"(\d{4}-\d{2}-\d{2})", title)
                if title_date_match:
                    if title_date_match.group(1) != target_date:
                        continue
            
            # 获取链接
            link = ""
            if hasattr(entry, "link"):
                link = entry.link
            elif hasattr(entry, "links") and entry.links:
                link = entry.links[0].href
            
            news_list.append({
                "title": entry.title.strip() if hasattr(entry, "title") else "",
                "link": link,
                "source": source["title"],
                "pub_date": pub_date.strftime("%Y-%m-%d") if pub_date else target_date,
                "summary": entry.summary if hasattr(entry, "summary") else "",
                "content": getattr(entry, "content", [{"value": ""}])[0].value if hasattr(entry, "content") else "",
            })
            
    except Exception as e:
        raise RuntimeError(str(e))
    
    return news_list


def fetch_detail(url: str, timeout: int = DEFAULT_TIMEOUT) -> str:
    """抓取详情页内容"""
    try:
        response = requests.get(
            url, 
            timeout=timeout, 
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        soup = BeautifulSoup(response.content, "html.parser")
        
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        
        article = soup.find("article") or soup.find("main") or soup.find("body")
        if article:
            text = article.get_text(separator="\n", strip=True)
            text = re.sub(r"\n{3,}", "\n\n", text)
            return text[:5000]
    except:
        pass
    return ""


def extract_summary(content: str, max_points: int = 5) -> tuple[str, list[str]]:
    """规则摘要：从内容中提取一句话总结和要点"""
    if not content:
        return "", []
    
    lines = [l.strip() for l in content.split("\n") if l.strip()]
    
    # 一句话总结
    summary = ""
    for line in lines[:5]:
        if len(line) > 20:
            summary = line
            break
    
    # 提取要点
    keywords = ["发布", "推出", "表示", "认为", "显示", "提供", "支持", 
                "实现", "完成", "通过", "进行", "开展", "召开", "启动"]
    
    points = []
    for line in lines[1:20]:
        if any(kw in line for kw in keywords) and len(line) > 15:
            points.append(line)
            if len(points) >= max_points:
                break
    
    return summary, points[:max_points]


def similarity(s1: str, s2: str) -> float:
    """计算两个标题的相似度"""
    s1 = re.sub(r"[^\w\u4e00-\u9fff]", "", s1.lower())
    s2 = re.sub(r"[^\w\u4e00-\u9fff]", "", s2.lower())
    
    if not s1 or not s2:
        return 0
    
    set1, set2 = set(s1), set(s2)
    return len(set1 & set2) / len(set1 | set2) if set1 | set2 else 0


def merge_news(news_list: list[dict]) -> list[dict]:
    """智能合并重复新闻"""
    if not news_list:
        return []
    
    merged = []
    used = set()
    
    for i, news in enumerate(news_list):
        if i in used:
            continue
        
        group = [news]
        used.add(i)
        
        for j, other in enumerate(news_list[i+1:], i+1):
            if j in used:
                continue
            if similarity(news["title"], other["title"]) > 0.6:
                group.append(other)
                used.add(j)
        
        best = max(group, key=lambda x: len(x.get("content", "") or x.get("summary", "")))
        merged.append(best)
    
    return merged


def main():
    parser = argparse.ArgumentParser(description="RSS 新闻收集脚本（多线程版）")
    parser.add_argument("--date", type=str, default="today", help="目标日期 YYYY-MM-DD")
    parser.add_argument("--force", action="store_true", default=False, help="强制重新抓取所有源")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS, help=f"并发数（默认{DEFAULT_WORKERS}）")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help=f"请求超时秒数（默认{DEFAULT_TIMEOUT}）")
    args = parser.parse_args()
    
    # 处理日期参数
    if args.date == "today":
        target_date = datetime.now().strftime("%Y-%m-%d")
    else:
        target_date = args.date
    
    print(f"📅 收集目标日期: {target_date}")
    print(f"⚙️  并发数: {args.workers}, 超时: {args.timeout}秒")
    
    # 创建输出目录
    output_dir = OUTPUT_DIR / target_date
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 进度状态文件
    progress_file = output_dir / "progress.json"
    
    # 加载已有进度
    if args.force:
        progress = {}
        print("🔄 强制模式：清除所有进度，重新开始")
    else:
        if progress_file.exists():
            with open(progress_file, "r", encoding="utf-8") as f:
                progress = json.load(f)
            print(f"📂 找到进度文件，继续上次任务")
        else:
            progress = {}
    
    # 加载已抓取的新闻
    raw_file = output_dir / "raw_news.json"
    all_news = []
    if raw_file.exists():
        with open(raw_file, "r", encoding="utf-8") as f:
            all_news = json.load(f)
        print(f"📂 已有 {len(all_news)} 条新闻缓存")
    
    # 解析 RSS 源
    print("📡 解析 RSS 源...")
    sources = parse_opml(FEEDS_OPML)
    print(f"   找到 {len(sources)} 个 RSS 源")
    
    # 统计进度
    done_count = sum(1 for s in sources if progress.get(s["xmlUrl"], {}).get("status") == "done")
    print(f"   已完成: {done_count}/{len(sources)}")
    
    # 准备待抓取列表
    pending_sources = []
    for source in sources:
        xml_url = source["xmlUrl"]
        if args.force or progress.get(xml_url, {}).get("status") != "done":
            pending_sources.append(source)
    
    if not pending_sources:
        print("✅ 所有源已完成，跳过抓取")
    else:
        print(f"🔄 开始并行抓取 {len(pending_sources)} 个源...")
        
        lock = Lock()
        new_news_count = 0
        
        def fetch_one(source: dict) -> tuple[dict, list, bool, str]:
            xml_url = source["xmlUrl"]
            try:
                news = fetch_feed(source, target_date, args.timeout)
                return (source, news, True, "")
            except Exception as e:
                return (source, [], False, str(e))
        
        # 并行抓取
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {executor.submit(fetch_one, s): s for s in pending_sources}
            
            completed = 0
            total = len(pending_sources)
            
            for future in as_completed(futures):
                completed += 1
                source, news, success, error = future.result()
                xml_url = source["xmlUrl"]
                
                with lock:
                    if success:
                        all_news.extend(news)
                        new_news_count += len(news)
                        progress[xml_url] = {
                            "title": source["title"],
                            "status": "done",
                            "count": len(news),
                            "end_time": datetime.now().isoformat()
                        }
                        print(f"  [{completed}/{total}] {source['title']} -> ✓ {len(news)}条")
                    else:
                        progress[xml_url] = {
                            "title": source["title"],
                            "status": "failed",
                            "error": error,
                            "end_time": datetime.now().isoformat()
                        }
                        print(f"  [{completed}/{total}] {source['title']} -> ✗ {error[:30]}")
                    
                    # 实时保存（每5个源保存一次）
                    if completed % 5 == 0 or completed == total:
                        with open(progress_file, "w", encoding="utf-8") as f:
                            json.dump(progress, f, ensure_ascii=False, indent=2)
                        with open(raw_file, "w", encoding="utf-8") as f:
                            json.dump(all_news, f, ensure_ascii=False, indent=2)
        
        print(f"\n📊 本次新增 {new_news_count} 条新闻，共 {len(all_news)} 条")
    
    # 合并重复
    print("🔗 智能合并重复新闻...")
    all_news = merge_news(all_news)
    print(f"   合并后 {len(all_news)} 条")
    
    # 抓取详情并摘要
    print("📝 抓取详情页并生成摘要...")
    for i, news in enumerate(all_news):
        if news.get("ai_summary"):
            print(f"  [{i+1}/{len(all_news)}] {news['title'][:30]}... -> ⏭️")
            continue
            
        print(f"  [{i+1}/{len(all_news)}] {news['title'][:30]}...", end=" ", flush=True)
        
        content = news.get("content") or news.get("summary", "")
        if not content and news.get("link"):
            try:
                content = fetch_detail(news["link"], args.timeout)
                print("✓", end=" ", flush=True)
            except:
                print("✗", end=" ", flush=True)
        
        news["content"] = content
        
        if content:
            summary, points = extract_summary(content)
            news["ai_summary"] = summary
            news["ai_points"] = points
            print(f"摘要: {len(points)}条要点")
        else:
            print("无内容")
        
        if (i + 1) % 10 == 0:
            with open(raw_file, "w", encoding="utf-8") as f:
                json.dump(all_news, f, ensure_ascii=False, indent=2)
    
    with open(raw_file, "w", encoding="utf-8") as f:
        json.dump(all_news, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 已保存原始数据到: {raw_file}")
    print(f"   进度文件: {progress_file}")
    
    # 打印失败列表
    failed = [v for v in progress.values() if v.get("status") == "failed"]
    if failed:
        print(f"\n⚠️  失败源: {len(failed)}个")
        for f in failed[:5]:
            print(f"   - {f.get('title')}: {f.get('error', '未知错误')}")
        if len(failed) > 5:
            print(f"   ... 还有 {len(failed)-5} 个")
    
    print(f"\n📌 下一步: python scripts/rate.py --date={target_date}")


if __name__ == "__main__":
    main()