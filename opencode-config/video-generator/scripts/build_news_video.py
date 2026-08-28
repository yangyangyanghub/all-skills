"""
每日新闻简报 → 3:4 竖版新闻视频构建器
流程:
  1. 解析 daily-brief.md → 提取新闻条目（标题/摘要/分类/来源）
  2. 生成每个新闻的 HTML 卡片（1080×1440 竖版）
  3. 启动本地 HTTP 服务器
  4. Playwright 截图每个卡片
  5. edge-tts 为每条新闻生成配音
  6. 按 TTS 时长计算精确时间线
  7. 生成 HyperFrames 项目（片头 -> 新闻卡片 -> 片尾）
  8. hyperframes render -> 合成音轨 -> final.mp4
"""
import asyncio
import json
import os
import re
import subprocess
import sys
import time
import html as html_mod
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import tempfile

PROJECT_DIR = Path(__file__).parent.resolve()
SLIDES_DIR = PROJECT_DIR / "slides"
CAPTURES_DIR = PROJECT_DIR / "captures"
AUDIO_DIR = PROJECT_DIR / "audio"
COMPOSITIONS_DIR = PROJECT_DIR / "compositions"

VIEWPORT = {"width": 1080, "height": 1440}

BRAND = {
    "title": "每日AI新闻简报",
    "subtitle": "",
    "accentColor": "#6366f1",
    "bgColor": "#0c0a1d",
    "tagline": "AI · 遥感 · 技术工具",
}

TIMING = {
    "introDuration": 4,
    "outroDuration": 5,
    "minSlideDuration": 4,
    "slidePadding": 1,
}


class NewsItem:
    def __init__(self, title, summary, category, source, url, priority="normal",
                 media_type=None, media_path=None):
        self.title = title
        self.summary = summary
        self.category = category
        self.source = source
        self.url = url
        self.priority = priority
        self.media_type = media_type  # "image", "video", or None
        self.media_path = media_path  # relative path to media file

    def tts_text(self):
        text = self.title
        if self.summary:
            # 过滤掉 Markdown 链接 [text](url)，只保留文本
            summary_clean = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", self.summary)
            # 过滤掉纯 URL
            summary_clean = re.sub(r"https?://[^\s]+", "", summary_clean)
            # 过滤 --- 分隔符和多余标点
            summary_clean = re.sub(r"\s*-{3,}\s*", "", summary_clean)
            summary_clean = re.sub(r"\s+[。，！？；：,.!?;:]", "", summary_clean)
            # 清理末尾多余的标点
            summary_clean = summary_clean.rstrip("。，！？；：,.!?;: ")
            text += "。" + summary_clean
        return text

    def __repr__(self):
        return f"[{self.category}] {self.title[:40]}"


def parse_markdown(md_path):
    with open(md_path, "r", encoding="utf-8") as f:
        text = f.read()

    items = []
    sections = re.split(r"\n## ", text)

    for sec in sections:
        if not sec.strip():
            continue
        lines = sec.strip().split("\n")
        section_title = lines[0].strip().lstrip("#").strip()

        skip_keywords = ["数据统计", "来源分布", "招聘信息", "政策与会议"]
        if any(sk in section_title for sk in skip_keywords):
            continue

        current_sub = ""
        sub_items_text = []

        for line in lines[1:]:
            m = re.match(r"### (.+)", line)
            if m:
                if sub_items_text and current_sub:
                    parsed = parse_sub_section(current_sub, sub_items_text)
                    items.extend(parsed)
                current_sub = m.group(1).strip()
                sub_items_text = []
            else:
                sub_items_text.append(line)

        if sub_items_text and current_sub:
            parsed = parse_sub_section(current_sub, sub_items_text)
            items.extend(parsed)

    return items


def parse_sub_section(category, lines):
    items = []
    buffer = []
    in_bullet = False

    for line in lines:
        bullet_match = re.match(r"\*\*(\d+\.\s*)?(.+?)\*\*", line)
        if bullet_match:
            if in_bullet and buffer:
                parsed = parse_single_news(buffer, category)
                if parsed:
                    items.append(parsed)
            buffer = [line]
            in_bullet = True
        elif line.strip().startswith("- ") and in_bullet:
            tool_text = line.strip()[2:]
            items.append(NewsItem(
                title=tool_text, summary="",
                category=category, source="", url="",
                priority="tool",
            ))
        elif in_bullet:
            buffer.append(line)

    if in_bullet and buffer:
        parsed = parse_single_news(buffer, category)
        if parsed:
            items.append(parsed)

    return items


def parse_single_news(lines, category):
    combined = " ".join(lines)

    title_m = re.match(r"\*\*(\d+\.\s*)?(.+?)\*\*", combined)
    if not title_m:
        return None
    title = title_m.group(2).strip()

    # 提取所有 blockquote 内容（在 join 之前）
    raw_text = "\n".join(lines)
    summary_m = re.findall(r"^>\s*(.+)$", raw_text, re.MULTILINE)
    summary = " ".join(s.strip() for s in summary_m) if summary_m else ""

    # 提取来源链接（从摘要中移除）
    source_url = ""
    source_name = ""
    url_m = re.search(r"\[([^\]]+)\]\(([^)]+)\)", summary)
    if url_m:
        source_name = url_m.group(1)
        source_url = url_m.group(2)
        # 从摘要中移除 Markdown 链接
        summary = re.sub(r"\[[^\]]+\]\([^)]+\)", "", summary).strip()

    # 检测媒体文件 ![](path)
    media_type = None
    media_path = None
    media_m = re.search(r"!\[([^\]]*)\]\(([^)]+\.(?:mp4|webm|mov|png|jpg|jpeg|gif))\)", summary)
    if media_m:
        media_path = media_m.group(2)
        ext = media_path.lower().split(".")[-1]
        if ext in ("mp4", "webm", "mov"):
            media_type = "video"
        elif ext in ("png", "jpg", "jpeg", "gif"):
            media_type = "image"
        # 从摘要中移除媒体语法
        summary = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", summary).strip()

    priority = "hot" if "🔥" in combined else "normal"

    return NewsItem(
        title=title, summary=summary,
        category=category, source=source_name,
        url=source_url, priority=priority,
        media_type=media_type, media_path=media_path,
    )


def generate_slide_html(item, idx, total):
    accent = BRAND["accentColor"]
    bg = BRAND["bgColor"]
    subtitle = BRAND["subtitle"]  # 日期

    title_esc = html_mod.escape(item.title)
    summary_esc = html_mod.escape(item.summary) if item.summary else ""
    source_esc = html_mod.escape(item.source) if item.source else ""
    category_esc = html_mod.escape(item.category)

    cat_colors = {
        "AI": "#818cf8", "遥感": "#34d399",
        "测绘地理信息": "#f59e0b", "技术工具": "#38bdf8",
    }
    cat_color = "#818cf8"
    for k, v in cat_colors.items():
        if k in item.category:
            cat_color = v
            break

    dots = ""
    for i in range(total):
        if i == idx:
            dots += f"<span style=\"display:inline-block;width:10px;height:10px;border-radius:50%;background:{accent};margin:0 4px\"></span>"
        else:
            dots += f"<span style=\"display:inline-block;width:8px;height:8px;border-radius:50%;background:rgba(255,255,255,0.2);margin:0 4px\"></span>"

    hot_badge = ""
    if item.priority == "hot":
        hot_badge = "<span style=\"display:inline-block;background:#ef4444;color:#fff;font-size:14px;font-weight:700;padding:3px 10px;border-radius:4px;margin-left:10px\">热门</span>"

    summary_html = ""
    if summary_esc:
        summary_html = f"<div class=\"summary\">{summary_esc}</div>"

    # 媒体区域（图片/视频）
    media_html = ""
    if item.media_type and item.media_path:
        media_esc = html_mod.escape(item.media_path)
        if item.media_type == "video":
            media_html = f"""<div class="media-area">
<video class="media-video" src="{media_esc}" muted playsinline preload="auto" loop></video>
</div>"""
        else:
            media_html = f"""<div class="media-area">
<img class="media-img" src="{media_esc}" alt="media" />
</div>"""

    # 三段式布局
    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1440px;overflow:hidden;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;background:{bg};color:#fff}}
.slide{{width:1080px;height:1440px;position:relative;display:flex;flex-direction:column;background:linear-gradient(180deg,{bg} 0%,#14102e 100%)}}
.deco{{position:absolute;top:-200px;right:-200px;width:500px;height:500px;border-radius:50%;background:radial-gradient(circle,{accent}15 0%,transparent 70%);pointer-events:none}}

/* 上区：日期 + 分类 */
.top-area{{height:280px;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:40px 64px;gap:20px}}
.date{{font-size:28px;font-weight:400;color:rgba(255,255,255,0.5);letter-spacing:0.1em}}
.cat-row{{display:flex;align-items:center;gap:16px}}
.badge{{display:inline-block;background:{cat_color}22;color:{cat_color};font-size:15px;font-weight:600;padding:8px 20px;border-radius:20px;border:1px solid {cat_color}44;letter-spacing:0.05em}}
.div{{width:60px;height:3px;background:{accent};border-radius:2px}}

/* 中区：内容展示 */
.middle-area{{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:40px 64px;gap:30px}}
.title{{font-size:44px;font-weight:800;line-height:1.3;letter-spacing:0.02em;color:#fff;text-align:center;max-width:950px}}
.summary{{font-size:24px;line-height:1.6;color:rgba(255,255,255,0.75);text-align:center;max-width:900px}}
.media-area{{width:100%;max-height:520px;display:flex;align-items:center;justify-content:center;border-radius:16px;overflow:hidden;background:rgba(0,0,0,0.3)}}
.media-img{{max-width:95%;max-height:500px;object-fit:contain;border-radius:12px}}
.media-video{{max-width:95%;max-height:500px;object-fit:contain;border-radius:12px}}

/* 下区：字幕 + 来源 + 进度 */
.bottom-area{{height:320px;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;padding:0 64px 40px;gap:20px}}
.subtitle-box{{width:100%;max-width:950px;min-height:80px;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,0.6);border-radius:12px;padding:20px 30px}}
.subtitle-text{{font-size:26px;font-weight:500;color:#fff;text-align:center;line-height:1.5}}
.source-row{{width:100%;display:flex;justify-content:space-between;align-items:center;padding-top:20px;border-top:1px solid rgba(255,255,255,0.08)}}
.source{{font-size:15px;color:rgba(255,255,255,0.4)}}
.cnt{{font-size:14px;color:rgba(255,255,255,0.3)}}
.prog{{display:flex;justify-content:center;align-items:center;gap:0}}
</style></head><body>
<div class="slide"><div class="deco"></div>

<!-- 上区 -->
<div class="top-area">
<div class="date">{subtitle}</div>
<div class="cat-row"><span class="badge">{category_esc}</span>{hot_badge}</div>
<div class="div"></div>
</div>

<!-- 中区 -->
<div class="middle-area">
<div class="title">{title_esc}</div>
{summary_html}
{media_html}
</div>

<!-- 下区 -->
<div class="bottom-area">
<div class="subtitle-box"><div class="subtitle-text" id="subtitle-text"></div></div>
<div class="source-row">
<span class="source">来源：{source_esc if source_esc else "AI自动整理"}</span>
<span class="cnt">{idx+1} / {total}</span>
</div>
<div class="prog">{dots}</div>
</div>

</div></body></html>"""
    return html


def generate_intro_html():
    accent = BRAND["accentColor"]
    bg = BRAND["bgColor"]
    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1440px;overflow:hidden;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;background:{bg};color:#fff}}
.intro{{width:1080px;height:1440px;display:flex;flex-direction:column;justify-content:center;align-items:center;position:relative;overflow:hidden}}
.glow{{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:700px;height:700px;border-radius:50%;background:radial-gradient(circle,{accent}20 0%,transparent 60%);pointer-events:none}}
.grid{{position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,0.03) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.03) 1px,transparent 1px);background-size:40px 40px;pointer-events:none}}
.ring{{width:80px;height:80px;border:2px solid {accent}66;border-radius:50%;display:flex;align-items:center;justify-content:center;margin-bottom:36px;z-index:1}}
.ring svg{{width:36px;height:36px;stroke:{accent};fill:none}}
.h1{{font-size:52px;font-weight:800;letter-spacing:0.04em;margin-bottom:14px;text-align:center;z-index:1}}
.h2{{font-size:22px;font-weight:400;color:rgba(255,255,255,0.5);letter-spacing:0.15em;margin-bottom:40px;z-index:1}}
.div2{{width:80px;height:2px;background:{accent};border-radius:2px;margin-bottom:30px;z-index:1}}
.tag{{font-size:15px;color:rgba(255,255,255,0.3);letter-spacing:0.08em;z-index:1}}
</style></head><body>
<div class="intro"><div class="glow"></div><div class="grid"></div>
<div class="ring"><svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a2 2 0 0 1-2 2Zm0 0a2 2 0 0 1-2-2v-9c0-1.1.9-2 2-2h2"/><path d="M18 14h-8"/><path d="M15 18h-5"/><path d="M10 6h8v4h-8V6Z"/></svg></div>
<div class="h1">{BRAND["title"]}</div>
<div class="h2">{BRAND["subtitle"]}</div>
<div class="div2"></div>
<div class="tag">{BRAND["tagline"]}</div>
</div></body></html>"""


def generate_outro_html():
    accent = BRAND["accentColor"]
    bg = BRAND["bgColor"]
    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1440px;overflow:hidden;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;background:{bg};color:#fff}}
.outro{{width:1080px;height:1440px;display:flex;flex-direction:column;justify-content:center;align-items:center;position:relative;overflow:hidden}}
.glow{{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:700px;height:700px;border-radius:50%;background:radial-gradient(circle,{accent}15 0%,transparent 60%);pointer-events:none}}
.chk{{width:72px;height:72px;border:3px solid {accent};border-radius:50%;display:flex;align-items:center;justify-content:center;margin-bottom:32px;z-index:1}}
.chk svg{{width:36px;height:36px;stroke:{accent};fill:none}}
.h1o{{font-size:42px;font-weight:700;letter-spacing:0.04em;margin-bottom:12px;text-align:center;z-index:1}}
.h2o{{font-size:18px;color:rgba(255,255,255,0.4);letter-spacing:0.1em;z-index:1}}
.div3{{width:60px;height:2px;background:{accent};border-radius:2px;margin-bottom:20px;z-index:1}}
.dt{{font-size:14px;color:rgba(255,255,255,0.2);margin-top:40px;z-index:1}}
</style></head><body>
<div class="outro"><div class="glow"></div>
<div class="chk"><svg viewBox="0 0 24 24" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg></div>
<div class="h1o">感谢观看</div>
<div class="h2o">{BRAND["title"]}</div>
<div class="div3"></div>
<div class="dt">{BRAND["subtitle"]}</div>
</div></body></html>"""


def get_audio_duration(path):
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True
        )
        return float(r.stdout.strip())
    except:
        return 5.0


def get_video_duration(path):
    """获取视频文件时长（秒）"""
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True
        )
        return float(r.stdout.strip())
    except:
        return 10.0


def prepare_media(items):
    """预处理媒体文件：复制视频到 captures 目录，获取视频时长"""
    for idx, item in enumerate(items):
        if item.media_type == "video" and item.media_path:
            seg_dir = CAPTURES_DIR / f"seg_{idx:03d}"
            seg_dir.mkdir(parents=True, exist_ok=True)
            # 复制视频到 captures 目录
            src = Path(item.media_path)
            if not src.is_absolute():
                src = PROJECT_DIR / item.media_path
            if src.exists():
                dst = seg_dir / src.name
                if not dst.exists():
                    import shutil
                    shutil.copy2(str(src), str(dst))
                item._media_captured = str(dst.relative_to(PROJECT_DIR))
                item._video_duration = get_video_duration(str(dst))
                print(f"  [{idx+1}] 视频: {src.name} ({item._video_duration:.1f}s)")
            else:
                print(f"  [{idx+1}] [warn] 视频文件不存在: {src}")
                item._media_captured = ""
                item._video_duration = 10.0
        elif item.media_type == "image" and item.media_path:
            item._media_captured = item.media_path
            item._video_duration = None
        else:
            item._media_captured = None
            item._video_duration = None


def generate_all_slides(items):
    SLIDES_DIR.mkdir(parents=True, exist_ok=True)

    # intro
    intro_html = generate_intro_html()
    intro_path = COMPOSITIONS_DIR / "intro.html"
    COMPOSITIONS_DIR.mkdir(parents=True, exist_ok=True)
    intro_path.write_text(intro_html, encoding="utf-8")
    print(f"  -> intro.html")

    # news slides
    total = len(items)
    for idx, item in enumerate(items):
        html = generate_slide_html(item, idx, total)
        slide_path = SLIDES_DIR / f"slide_{idx:03d}.html"
        slide_path.write_text(html, encoding="utf-8")
        print(f"  -> slides/slide_{idx:03d}.html [{item.category}] {item.title[:40]}")

    # outro
    outro_html = generate_outro_html()
    outro_path = COMPOSITIONS_DIR / "outro.html"
    outro_path.write_text(outro_html, encoding="utf-8")
    print(f"  -> outro.html")


# ════════════════════════════════════════════════════
# HTTP Server (for serving local slide HTMLs)
# ════════════════════════════════════════════════════

class SlidesHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PROJECT_DIR), **kwargs)

    def log_message(self, format, *args):
        pass  # quiet


def start_http_server(port=18909):
    server = HTTPServer(("127.0.0.1", port), SlidesHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    print(f"  HTTP server: http://127.0.0.1:{port}")
    return server, port


# ════════════════════════════════════════════════════
# Playwright Screenshot
# ════════════════════════════════════════════════════

async def capture_slides(items, base_url):
    from playwright.async_api import async_playwright

    CAPTURES_DIR.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport=VIEWPORT)
        page = await context.new_page()

        results = []
        for idx, item in enumerate(items):
            seg_dir = CAPTURES_DIR / f"seg_{idx:03d}"
            seg_dir.mkdir(parents=True, exist_ok=True)
            shot_path = seg_dir / "screenshot.png"

            # 视频不需要截图
            if item.media_type == "video":
                results.append("")  # 视频用 _media_captured
                continue

            if shot_path.exists():
                print(f"  [{idx+1}/{len(items)}] skip (已存在): {item.title[:40]}")
                results.append(str(shot_path.relative_to(PROJECT_DIR)))
                continue

            url = f"{base_url}/slides/slide_{idx:03d}.html"
            print(f"  [{idx+1}/{len(items)}] 截图: {item.title[:40]}")
            try:
                await page.goto(url, wait_until="networkidle", timeout=15000)
                await page.wait_for_timeout(500)
                await page.screenshot(path=str(shot_path), full_page=False)
                results.append(str(shot_path.relative_to(PROJECT_DIR)))
            except Exception as e:
                print(f"    [error] {e}")
                results.append("")

        await context.close()
        await browser.close()

    return results


# ════════════════════════════════════════════════════
# TTS Generation
# ════════════════════════════════════════════════════

async def generate_tts(items, voice="zh-CN-YunxiNeural", rate="+0%"):
    import edge_tts

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    durations = []

    for idx, item in enumerate(items):
        text = item.tts_text()
        if not text:
            durations.append(3.0)
            continue

        seg_path = AUDIO_DIR / f"seg_{idx:03d}.mp3"
        if seg_path.exists():
            dur = get_audio_duration(str(seg_path))
            durations.append(dur)
            print(f"  [{idx+1}/{len(items)}] skip TTS: {dur:.1f}s")
            continue

        print(f"  [{idx+1}/{len(items)}] TTS ({len(text)}字): {text[:50]}...")
        for attempt in range(3):
            try:
                c = edge_tts.Communicate(text, voice, rate=rate)
                await c.save(str(seg_path))
                dur = get_audio_duration(str(seg_path))
                durations.append(dur)
                print(f"    OK: {dur:.1f}s")
                break
            except Exception as e:
                if attempt < 2:
                    await asyncio.sleep(2)
                else:
                    print(f"    [error] TTS失败: {e}")
                    durations.append(5.0)

    return durations



compositions_dir = PROJECT_DIR / "compositions"

def build_subtitles_html(timeline_items):
    lines = []
    lines.append('<!DOCTYPE html>')
    lines.append('<html style="background:transparent">')
    lines.append('<head><meta charset="UTF-8"><style>')
    lines.append('*{margin:0;padding:0;box-sizing:border-box}')
    lines.append('[data-composition-id="subtitles"]{width:1080px;height:1440px;overflow:hidden;position:relative;pointer-events:none;font-family:Arial,"PingFang SC","Microsoft YaHei",sans-serif}')
    lines.append('[data-composition-id="subtitles"] .sub{position:absolute;bottom:200px;left:0;right:0;text-align:center;padding:0 60px;opacity:0}')
    lines.append('[data-composition-id="subtitles"] .sub-text{display:inline-block;background:rgba(0,0,0,.75);color:#fff;font-size:26px;font-weight:500;padding:16px 32px;border-radius:12px;letter-spacing:.04em;line-height:1.5;max-width:950px}')
    lines.append('</style></head><body style="background:transparent">')
    lines.append('<div data-composition-id="subtitles">')
    for item in timeline_items:
        if item['type'] == 'slide':
            text = item.get('ttsText', '')
            if text:
                escaped = text.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('"','&quot;')
                lines.append(f'<div class="sub clip" data-start="{item["start"]}" data-duration="{item["duration"]}"><span class="sub-text">{escaped}</span></div>')
    lines.append('</div>')
    lines.append('<script src="https://cdn.jsdelivr.net/npm/gsap@3/dist/gsap.min.js"></script>')
    lines.append('<script>')
    lines.append('var p="[data-composition-id=\\"subtitles\\"] ";')
    lines.append('var tl=gsap.timeline({paused:true});')
    lines.append('document.querySelectorAll(p+".sub.clip").forEach(function(el){')
    lines.append('  var s=parseFloat(el.dataset.start);')
    lines.append('  var d=parseFloat(el.dataset.duration);')
    lines.append('  tl.to(el,{opacity:1,duration:.3},s);')
    lines.append('  tl.to(el,{opacity:0,duration:.3},s+d-.3);')
    lines.append('});')
    lines.append('window.__timelines=window.__timelines||{};')
    lines.append('window.__timelines["subtitles"]=tl;')
    lines.append('</script>')
    lines.append('</body></html>')
    path = compositions_dir / "subtitles.html"
    path.write_text("\n".join(lines), encoding="utf-8")
    print("  -> compositions/subtitles.html")


def build_index_html(timeline_items, total_dur):
    import json as _json
    accent = BRAND["accentColor"]
    bg = BRAND["bgColor"]
    lines = []
    lines.append('<!DOCTYPE html>')
    lines.append('<html>')
    lines.append('<head><meta charset="UTF-8"><style>')
    lines.append('*{margin:0;padding:0;box-sizing:border-box}')
    lines.append('[data-composition-id="root"]{width:1080px;height:1440px;overflow:hidden;position:relative;background:' + bg + ';font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif}')
    lines.append('</style></head><body>')
    lines.append('<div id="root" data-composition-id="root" data-width="1080" data-height="1440" data-start="0" data-duration="' + str(total_dur) + '">')
    for i, item in enumerate(timeline_items):
        sid = item['start']
        sdir = item['duration']
        if item['type'] == 'intro':
            lines.append('  <div id="intro" data-composition-id="intro" data-composition-src="compositions/intro.html" data-start="' + str(sid) + '" data-duration="' + str(sdir) + '"></div>')
        elif item['type'] == 'slide':
            shot_path = item.get('screenshot', '')
            media_path = item.get('mediaPath', '')
            media_type = item.get('mediaType', '')

            if media_type == 'video' and media_path:
                # 视频元素：需要 muted playsinline preload="auto"
                lines.append('  <video id="slide-' + str(i) + '" class="clip" src="' + media_path + '" muted playsinline preload="auto" data-start="' + str(sid) + '" data-duration="' + str(sdir) + '" style="position:absolute;top:0;left:0;width:1080px;height:1440px;object-fit:contain;z-index:1;opacity:0"></video>')
            elif shot_path:
                lines.append('  <img id="slide-' + str(i) + '" class="clip" src="' + shot_path + '" data-start="' + str(sid) + '" data-duration="' + str(sdir) + '" style="position:absolute;top:0;left:0;width:1080px;height:1440px;object-fit:cover;z-index:1;opacity:0">')
        elif item['type'] == 'outro':
            lines.append('  <div id="outro" class="clip" data-start="' + str(sid) + '" data-duration="' + str(sdir) + '" style="position:absolute;top:0;left:0;width:1080px;height:1440px;overflow:hidden;z-index:100;opacity:0;display:block">')
            lines.append('    <div data-composition-id="outro-inner" data-composition-src="compositions/outro.html" data-start="0" data-duration="' + str(sdir) + '"></div>')
            lines.append('  </div>')
    lines.append('  <div data-composition-id="subtitles" data-composition-src="compositions/subtitles.html" data-start="0" data-duration="' + str(total_dur) + '"></div>')
    lines.append('</div>')
    shot_data = []
    for i, item in enumerate(timeline_items):
        if item['type'] in ('slide', 'outro'):
            sid_name = 'slide-' + str(i) if item['type'] == 'slide' else 'outro'
            shot_data.append({"id": sid_name, "start": item['start'], "duration": item['duration']})
    lines.append('<script src="https://cdn.jsdelivr.net/npm/gsap@3/dist/gsap.min.js"></script>')
    lines.append('<script>')
    lines.append('window.__timelines=window.__timelines||{};')
    lines.append('window.__timelines["root"]=gsap.timeline({paused:true});')
    lines.append('var HF_SHOTS=' + _json.dumps(shot_data) + ';')
    lines.append('var HF_ROOT=window.__timelines["root"];')
    lines.append('var _played={};')
    lines.append('HF_ROOT.eventCallback("onUpdate",function(){')
    lines.append('  var t=HF_ROOT.time();')
    lines.append('  for(var i=0;i<HF_SHOTS.length;i++){')
    lines.append('    var s=HF_SHOTS[i];')
    lines.append('    var el=document.getElementById(s.id);')
    lines.append('    if(!el)continue;')
    lines.append('    var st=s.start, ed=s.start+s.duration;')
    lines.append('    if(t>=st&&t<=ed){')
    lines.append('      el.style.opacity="1";el.style.display="block";')
    lines.append('      if(el.tagName==="VIDEO"&&!_played[s.id]){el.play();_played[s.id]=1;}')
    lines.append('    }else{')
    lines.append('      el.style.opacity="0";el.style.display="none";')
    lines.append('      if(el.tagName==="VIDEO"){el.pause();el.currentTime=0;delete _played[s.id];}')
    lines.append('    }')
    lines.append('  }')
    lines.append('});')
    lines.append('</script>')
    lines.append('</body></html>')
    path = PROJECT_DIR / "index.html"
    path.write_text("\n".join(lines), encoding="utf-8")
    print("  -> index.html")


def build_narration(timeline_items, total_dur):
    blank_path = AUDIO_DIR / "blank.wav"
    if not blank_path.exists():
        subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
             "-t", str(total_dur), blank_path],
            capture_output=True, text=True)
    inputs = [str(blank_path)]
    filter_parts = []
    next_idx = 1
    delayed_labels = []
    for item in timeline_items:
        if item['type'] == 'slide':
            audio_path = item.get('audioPath', '')
            if not audio_path or not os.path.exists(audio_path):
                continue
            delay_ms = int(item['start'] * 1000)
            inputs.append(audio_path)
            label = 's' + str(next_idx)
            filter_parts.append('[' + str(next_idx) + ':a]adelay=' + str(delay_ms) + '|' + str(delay_ms) + '[' + label + ']')
            delayed_labels.append('[' + label + ']')
            next_idx += 1
    if next_idx == 1:
        print('  [warn] 无TTS音频')
        return ''
    mix_inputs = '[0:a] ' + ' '.join(delayed_labels)
    filter_parts.append(mix_inputs + 'amix=inputs=' + str(next_idx) + ':duration=first:dropout_transition=0[out]')
    filter_str = ';'.join(filter_parts)
    output_path = str(AUDIO_DIR / 'narration.wav')
    cmd = ['ffmpeg', '-y'] + sum([['-i', inp] for inp in inputs], []) + [
        '-filter_complex', filter_str,
        '-map', '[out]', '-c:a', 'pcm_s16le',
        '-t', str(total_dur), output_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print('  [error] 音频合成失败: ' + result.stderr[-300:])
        return ''
    mp3_path = str(AUDIO_DIR / 'narration.mp3')
    subprocess.run(
        ['ffmpeg', '-y', '-i', output_path, '-c:a', 'libmp3lame', '-q:a', '2', mp3_path],
        capture_output=True)
    return mp3_path


async def main():
    import argparse
    parser = argparse.ArgumentParser(description='新闻简报 -> 3:4竖版视频')
    parser.add_argument('--md', default='daily-brief.md', help='Markdown新闻简报文件')
    parser.add_argument('--voice', default='zh-CN-YunxiNeural', help='TTS语音')
    parser.add_argument('--rate', default='+30%', help='TTS语速')
    parser.add_argument('--output', default='final.mp4', help='输出MP4路径')
    parser.add_argument('--port', type=int, default=18909, help='本地HTTP端口')
    parser.add_argument('--skip-capture', action='store_true', help='跳过截图')
    parser.add_argument('--skip-tts', action='store_true', help='跳过TTS')
    parser.add_argument('--skip-subs', action='store_true', help='跳过字幕')
    parser.add_argument('--bgm', help='背景音乐文件路径')
    parser.add_argument('--skip-render', action='store_true', help='只生成HTML')
    args = parser.parse_args()

    md_path = Path(args.md)
    if not md_path.is_absolute():
        md_path = PROJECT_DIR / args.md

    # 自动从文件名提取日期（如 2026-06-08/daily-brief.md）
    date_str = md_path.parent.name
    import re as _re
    date_match = _re.match(r'(\d{4})-(\d{2})-(\d{2})', date_str)
    if date_match:
        BRAND["subtitle"] = '%s年%s月%s日' % (date_match.group(1), int(date_match.group(2)), int(date_match.group(3)))
    else:
        # 从 markdown 内容中提取日期
        try:
            with open(str(md_path), 'r', encoding='utf-8') as _f:
                _content = _f.read()
            _dm = _re.search(r'(\d{4})-(\d{2})-(\d{2})', _content)
            if _dm:
                BRAND["subtitle"] = '%s年%s月%s日' % (_dm.group(1), int(_dm.group(2)), int(_dm.group(3)))
        except:
            pass

    print('源文件: ' + str(md_path))
    print('工作目录: ' + str(PROJECT_DIR))
    print('日期: ' + BRAND["subtitle"])

    print('\n── [0/6] 解析Markdown ──')
    items = parse_markdown(str(md_path))
    print('  解析到 ' + str(len(items)) + ' 条新闻:')
    for item in items:
        media_info = ''
        if item.media_type:
            media_info = ' [%s: %s]' % (item.media_type, item.media_path or '')
        print('  [' + item.category + '] ' + item.title[:50] + media_info)

    # 预处理媒体文件（复制视频、获取时长）
    print('\n── [0.5/6] 预处理媒体 ──')
    prepare_media(items)

    print('\n── [1/6] 生成HTML卡片 ──')
    generate_all_slides(items)

    print('\n── [2/6] 启动本地HTTP服务器 ──')
    start_http_server(args.port)
    base_url = 'http://127.0.0.1:' + str(args.port)
    time.sleep(0.5)

    if not args.skip_capture:
        print('\n── [3/6] Playwright截图 ──')
        screenshots = await capture_slides(items, base_url)
    else:
        print('\n  跳过截图')
        screenshots = []
        for idx in range(len(items)):
            p = CAPTURES_DIR / ('seg_%03d' % idx) / 'screenshot.png'
            screenshots.append(str(p.relative_to(PROJECT_DIR)) if p.exists() else '')

    if not args.skip_tts:
        print('\n── [4/6] TTS配音 ──')
        durations = await generate_tts(items, args.voice, args.rate)
    else:
        print('\n  跳过TTS')
        durations = [TIMING['minSlideDuration']] * len(items)

    print('\n── [5/6] 时间线计算 + HTML生成 ──')
    timeline_items = []
    current = 0.0
    intro_dur = TIMING['introDuration']
    timeline_items.append({'type': 'intro', 'start': current, 'duration': intro_dur})
    current += intro_dur
    for idx, item in enumerate(items):
        audio_dur = durations[idx] if idx < len(durations) else TIMING['minSlideDuration']

        # 视频用实际时长，图片/纯文本用 TTS 时长
        if item.media_type == 'video' and hasattr(item, '_video_duration') and item._video_duration:
            slide_dur = max(item._video_duration, audio_dur + TIMING['slidePadding'])
        else:
            slide_dur = max(audio_dur + TIMING['slidePadding'], TIMING['minSlideDuration'])

        # 媒体路径
        media_path = ''
        if item.media_type == 'video' and hasattr(item, '_media_captured') and item._media_captured:
            media_path = item._media_captured
        elif item.media_type == 'image' and item.media_path:
            media_path = item.media_path

        timeline_items.append({
            'type': 'slide', 'start': current, 'duration': slide_dur,
            'screenshot': screenshots[idx] if idx < len(screenshots) else '',
            'mediaPath': media_path,
            'mediaType': item.media_type or '',
            'ttsText': item.tts_text(),
            'title': item.title,
            'audioPath': str(AUDIO_DIR / ('seg_%03d.mp3' % idx)),
        })
        current += slide_dur
    outro_dur = TIMING['outroDuration'] + 3
    timeline_items.append({'type': 'outro', 'start': current, 'duration': outro_dur})
    current += outro_dur
    total_dur = current
    for item in timeline_items:
        dur = item['duration']
        if item['type'] == 'slide':
            t = item.get('title', '')[:40]
            print('  %6.1fs - %6.1fs [slide] %s' % (item['start'], item['start']+dur, t))
        else:
            print('  %6.1fs - %6.1fs [%s]' % (item['start'], item['start']+dur, item['type']))
    print('\n  总时长: %.1fs' % total_dur)
    if not args.skip_subs:
        build_subtitles_html(timeline_items)
    else:
        print('\n  ⏭ 跳过字幕 (--skip-subs)')
    build_index_html(timeline_items, total_dur)
    narration_path = build_narration(timeline_items, total_dur)
    if not args.skip_render:
        print('\n── [6/6] HyperFrames渲染 ──')
        output_path = str((PROJECT_DIR / args.output).resolve())
        cmd = 'npx hyperframes render -o "' + output_path + '" --quality standard --fps 30 --workers 2 --page-side-compositing=no "' + str(PROJECT_DIR) + '"'
        print('  运行: ' + cmd)
        result = subprocess.run(cmd, capture_output=False, text=True, shell=True)
        if result.returncode != 0:
            print('  [error] render失败 (exit=%d)' % result.returncode)
            return
        if os.path.exists(output_path):
            size_mb = os.path.getsize(output_path) / (1024*1024)
            print('  ✅ 完成: %s (%.1f MB)' % (output_path, size_mb))
            if narration_path and os.path.exists(narration_path):
                merged_path = output_path.replace('.mp4', '-with-audio.mp4')
                print('\n── 合并音轨 ──')

                # 如果有 BGM，混合 narration + bgm
                if args.bgm and os.path.exists(args.bgm):
                    print('  BGM: ' + args.bgm)
                    bgm_mixed = str(AUDIO_DIR / 'narration_with_bgm.mp3')
                    # 将 BGM 循环到视频长度，然后与 narration 混合
                    bgm_cmd = [
                        'ffmpeg', '-y',
                        '-i', narration_path,
                        '-stream_loop', '-1', '-i', args.bgm,
                        '-filter_complex',
                        '[1:a]volume=0.15[bgm];[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=0[out]',
                        '-map', '[out]', '-c:a', 'libmp3lame', '-q:a', '2',
                        '-t', str(total_dur), bgm_mixed,
                    ]
                    result = subprocess.run(bgm_cmd, capture_output=True, text=True)
                    if result.returncode != 0:
                        print('  [error] BGM 混合失败: %s' % result.stderr[-300:])
                        audio_input = narration_path
                    else:
                        print('  ✅ BGM 混合完成')
                        audio_input = bgm_mixed
                else:
                    audio_input = narration_path

                merge_cmd = [
                    'ffmpeg', '-y',
                    '-i', output_path,
                    '-i', audio_input,
                    '-c:v', 'copy',
                    '-c:a', 'aac', '-b:a', '192k',
                    '-map', '0:v:0', '-map', '1:a:0',
                    '-shortest', merged_path,
                ]
                result = subprocess.run(merge_cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    print('  [error] 合并失败: %s' % result.stderr[-300:])
                elif os.path.exists(merged_path):
                    merged_mb = os.path.getsize(merged_path) / (1024*1024)
                    print('  ✅ 音轨合并: %s (%.1f MB)' % (merged_path, merged_mb))
                    verify = subprocess.run(
                        ['ffprobe', '-v', 'quiet', '-show_entries', 'stream=codec_type,codec_name',
                         '-of', 'csv=p=0', merged_path],
                        capture_output=True, text=True)
                    streams = [s.strip() for s in verify.stdout.strip().split('\n') if s.strip()]
                    print('  流: %s' % streams)
                else:
                    print('  [error] 合并输出不存在')
        else:
            print('  [error] 输出文件不存在: ' + output_path)
    else:
        print('\n  ⏭ 跳过渲染 (--skip-render)')


if __name__ == '__main__':
    asyncio.run(main())
