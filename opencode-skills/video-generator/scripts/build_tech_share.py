"""
技术/调研分享 → 3:4 竖版口播视频构建器

流程:
  1. 解析调研 Markdown → 按章节提取内容
  2. 生成各类型幻灯片（概述/要点/表格/代码/截图）
  3. 混合截图：本地 HTML 卡片 + 远程 URL
  4. edge-tts 为每条配音
  5. 时间线计算 → HyperFrames 渲染 → 合成音轨
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
from dataclasses import dataclass, field

_h = html_mod  # shorthand for html.escape

PROJECT_DIR = Path(__file__).parent.resolve()
SLIDES_DIR = PROJECT_DIR / "slides"
CAPTURES_DIR = PROJECT_DIR / "captures"
AUDIO_DIR = PROJECT_DIR / "audio"
COMPOSITIONS_DIR = PROJECT_DIR / "compositions"

VIEWPORT = {"width": 1080, "height": 1440}
URL_VIEWPORT = {"width": 1280, "height": 800}

BRAND = {
    "title": "技术调研分享",
    "subtitle": "",
    "accentColor": "#6366f1",
    "bgColor": "#0c0a1d",
    "tagline": "",
}

TIMING = {
    "introDuration": 5,
    "outroDuration": 6,
    "minSlideDuration": 5,
    "slidePadding": 1.5,
}


@dataclass
class TechSlide:
    type: str = ""
    title: str = ""
    tts_text: str = ""
    items: list = field(default_factory=list)
    headers: list = field(default_factory=list)
    rows: list = field(default_factory=list)
    code: str = ""
    language: str = ""
    url: str = ""
    url_label: str = ""
    content_raw: str = ""


# ════════════════════════════════════════════════════
# Text Helpers
# ════════════════════════════════════════════════════

def clean_text_for_tts(text):
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"https?://[^\s]+", "", text)
    text = re.sub(r"[*_`#]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def summarize_text(text, max_chars=200):
    cleaned = clean_text_for_tts(text)
    if len(cleaned) > max_chars:
        cleaned = cleaned[:max_chars] + "。"
    return cleaned


# ════════════════════════════════════════════════════
# Brand Helpers
# ════════════════════════════════════════════════════

def update_brand_from_md(md_path, h1_title=""):
    if h1_title:
        BRAND["title"] = h1_title
    try:
        content = Path(md_path).read_text("utf-8")
        dm = re.search(r"(?:调研日期|Date)[：:]\s*(\S+)", content)
        if dm:
            BRAND["subtitle"] = dm.group(1)
        pm = re.search(r"(?:项目地址|Project address|GitHub)[：:]\s*(https?://[^\s\)]+)", content)
        if pm:
            BRAND["tagline"] = pm.group(1)
    except:
        pass


def extract_h1_title(text):
    m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    return m.group(1).strip() if m else "技术调研分享"


def extract_project_url(text):
    m = re.search(r"(?:项目地址|Project address)[：:]\s*(https?://[^\s\)\n]+)", text)
    return m.group(1).strip() if m else ""


def extract_all_urls(text):
    return re.findall(r"https?://[^\s\)\]\n]+", text)


# ════════════════════════════════════════════════════
# Markdown Parsing
# ════════════════════════════════════════════════════

def parse_tech_markdown(md_path):
    """Parse research markdown → list[TechSlide]"""
    text = Path(md_path).read_text("utf-8")
    h1_title = extract_h1_title(text)
    project_url = extract_project_url(text)
    slides = []

    # Intro
    slides.append(TechSlide(type="intro", title=h1_title))

    # Project URL screenshot (if found)
    all_urls = extract_all_urls(text)
    if project_url:
        slides.append(TechSlide(
            type="screenshot", title="项目主页",
            url=project_url, url_label="GitHub",
            tts_text=f"先来看看项目主页。{project_url}",
        ))
    elif all_urls:
        slides.append(TechSlide(
            type="screenshot", title="相关链接",
            url=all_urls[0], url_label="网页",
            tts_text=f"先看看相关页面。{all_urls[0]}",
        ))

    # Split by ## sections
    sections = re.split(r"\n## ", text)
    skip_sections = ["目录", "Table of Contents", "更新日志", "Changelog"]

    for sec in sections:
        if not sec.strip():
            continue
        lines = sec.strip().split("\n")
        section_title = lines[0].strip().lstrip("#").strip()
        if any(sk in section_title for sk in skip_sections):
            continue
        if section_title == h1_title:
            continue
        sec_text = "\n".join(lines[1:]).strip()
        if not sec_text:
            continue
        parsed = parse_section(section_title, sec_text)
        slides.extend(parsed)

    # Mark conclusion
    if len(slides) > 1 and slides[-1].type in ("overview", "bullet"):
        tl = slides[-1].title.lower()
        if any(kw in tl for kw in ["总结", "结论", "小结", "conclusion", "summary"]):
            slides[-1].type = "conclusion"

    # Ensure conclusion
    has_conclusion = any(s.type == "conclusion" for s in slides)
    if not has_conclusion:
        slides.append(TechSlide(
            type="conclusion", title="总结",
            tts_text="以上是本次调研的分享。感谢观看。",
        ))

    return slides, h1_title


def parse_section(title, text):
    """Parse a ## section → list of TechSlide"""
    slides = []

    table_matches = re.findall(
        r"(\|[^\n]+\|\s*\n\|[^\n]+\|\s*\n(?:\|[^\n]+\|\s*\n)*)", text
    )
    code_matches = re.findall(r"```(\w*)\n(.*?)```", text, re.DOTALL)
    sub_sections = re.split(r"\n### ", text)

    if table_matches and len(table_matches) <= 4:
        for tm in table_matches:
            ts = _parse_table(tm, title)
            if ts:
                slides.append(ts)
        for cm in code_matches:
            cs = _parse_code(cm, title)
            if cs:
                slides.append(cs)
    elif code_matches and len(text) < 800:
        for cm in code_matches[:3]:
            cs = _parse_code(cm, title)
            if cs:
                slides.append(cs)
    elif len(sub_sections) > 1:
        for i, sub in enumerate(sub_sections):
            sub_lines = sub.strip().split("\n")
            sub_title = sub_lines[0].strip().lstrip("#").strip() if i > 0 else title
            sub_text = "\n".join(sub_lines[1:]).strip() if i > 0 else sub.strip()
            if not sub_text:
                continue
            sub_slides = _parse_subsection(sub_title, sub_text)
            slides.extend(sub_slides)
    else:
        slides.extend(_parse_subsection(title, text))

    if not slides:
        tts = title + "。" + summarize_text(text)
        slides.append(TechSlide(type="overview", title=title, tts_text=tts, content_raw=text))

    return slides


def _parse_subsection(title, text):
    slides = []
    # Tables
    table_m = re.findall(
        r"(\|[^\n]+\|\s*\n\|[^\n]+\|\s*\n(?:\|[^\n]+\|\s*\n)*)", text
    )
    if table_m:
        for tm in table_m:
            ts = _parse_table(tm, title)
            if ts:
                slides.append(ts)
        return slides
    # Code
    code_m = re.findall(r"```(\w*)\n(.*?)```", text, re.DOTALL)
    if code_m:
        for cm in code_m[:2]:
            cs = _parse_code(cm, title)
            if cs:
                slides.append(cs)
        return slides
    # Bullet lists
    bullet_items = re.findall(
        r"(?:^\s*(?:\d+[.、．)\s]|[-*+]\s)\s*(.+)$)", text, re.MULTILINE
    )
    if bullet_items:
        tts_items = [clean_text_for_tts(b) for b in bullet_items[:8]]
        tts = title + "。" + "，".join(tts_items)
        slides.append(TechSlide(
            type="bullet", title=title, items=bullet_items[:8],
            tts_text=tts,
        ))
        return slides
    # Fallback
    tts = title + "。" + summarize_text(text)
    slides.append(TechSlide(type="overview", title=title, tts_text=tts, content_raw=text))
    return slides


def _parse_table(table_text, section_title):
    lines = [l.strip() for l in table_text.strip().split("\n") if l.strip()]
    if len(lines) < 2:
        return None
    headers = [h.strip().lstrip("|").rstrip("|").strip() for h in lines[0].split("|")]
    headers = [h for h in headers if h]
    rows = []
    for line in lines[2:]:
        cells = [c.strip() for c in line.split("|")]
        cells = [c for c in cells if c]
        if cells:
            rows.append(cells)
    if not headers or not rows:
        return None
    tts_parts = []
    for row in rows[:3]:
        for i, cell in enumerate(row):
            if i < len(headers):
                tts_parts.append(f"{headers[i]}: {cell}")
    tts = section_title + "。" + "，".join(tts_parts)
    return TechSlide(
        type="table", title=section_title,
        headers=headers, rows=rows[:15], tts_text=tts,
    )


def _parse_code(code_match, section_title):
    lang = code_match[0] if code_match[0] else "text"
    code_text = code_match[1].strip()
    if not code_text or len(code_text) < 10:
        return None
    if len(code_text) > 1000:
        code_text = code_text[:1000] + "\n  # ..."
    first_line = code_text.split("\n")[0]
    desc = ""
    if first_line.startswith("#") or first_line.startswith("//"):
        desc = first_line.lstrip("#/ ").strip()
    tts = section_title
    tts += "。" + (desc if desc else ("代码示例：" + code_text[:60]))
    return TechSlide(
        type="code", title=section_title,
        code=code_text, language=lang, tts_text=tts,
    )


# ======== Slide HTML Generation ========

def generate_slide_html(slide, idx, total):
    if slide.type == "intro":
        return _html_intro()
    elif slide.type == "conclusion":
        return _html_conclusion()
    elif slide.type == "bullet":
        return _html_bullet(slide, idx, total)
    elif slide.type == "table":
        return _html_table(slide, idx, total)
    elif slide.type == "code":
        return _html_code(slide, idx, total)
    elif slide.type == "screenshot":
        return None
    else:
        return _html_overview(slide, idx, total)


def _dot(idx, total, a):
    d = ""
    for i in range(total):
        s = f"background:{a};width:10px;height:10px" if i == idx else "background:rgba(255,255,255,0.2)"
        d += f'<span class="pg" style="{s}"></span>'
    return d


def _html_bullet(slide, idx, total):
    a = BRAND["accentColor"]; b = BRAND["bgColor"]
    title_esc = _h.escape(slide.title)
    dots = _dot(idx, total, a)
    items_html = ""
    for i, item in enumerate(slide.items[:8]):
        item_esc = _h.escape(item)
        num = f"{i+1:02d}"
        items_html += f'<div class="bi"><span class="bn">{num}</span><span class="bt">{item_esc}</span></div>'
    css_lines = [
        '*{margin:0;padding:0;box-sizing:border-box}',
        'body{width:1080px;height:1440px;overflow:hidden;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;background:%s;color:#fff}' % b,
        '.slide{width:1080px;height:1440px;position:relative;display:flex;flex-direction:column;background:linear-gradient(180deg,%s 0%%,#14102e 100%%)}' % b,
        '.deco{position:absolute;top:-200px;right:-200px;width:500px;height:500px;border-radius:50%%;background:radial-gradient(circle,%s15 0%%,transparent 70%%);pointer-events:none}' % a,
        '.tp{height:200px;display:flex;align-items:center;justify-content:center;padding:30px 60px 10px}',
        '.tp h2{font-size:34px;font-weight:700;text-align:center}',
        '.lst{flex:1;display:flex;flex-direction:column;justify-content:center;gap:16px;padding:0 80px 20px;overflow:hidden}',
        '.bi{display:flex;align-items:flex-start;gap:14px}',
        '.bn{font-size:20px;font-weight:800;color:%s;min-width:34px;text-align:right;line-height:1.5}' % a,
        '.bt{font-size:24px;line-height:1.5;color:rgba(255,255,255,0.87)}',
        '.btm{height:140px;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;padding:0 60px 24px;gap:8px}',
        '.pg{display:inline-block;border-radius:50%%;margin:0 4px}',
    ]
    css = "\n".join(css_lines)
    body = '<div class="slide"><div class="deco"></div>\n'
    body += '<div class="tp"><h2>%s</h2></div>\n' % title_esc
    body += '<div class="lst">%s</div>\n' % items_html
    body += '<div class="btm"><div>%s</div><span class="cnt" style="font-size:13px;color:rgba(255,255,255,0.3)">%d/%d</span></div>\n' % (dots, idx+1, total)
    body += '</div>'
    return '<!DOCTYPE html>\n<html><head><meta charset="UTF-8"><style>\n%s\n</style></head><body>\n%s\n</body></html>' % (css, body)



def _html_table(slide, idx, total):
    a = BRAND["accentColor"]; b = BRAND["bgColor"]
    title_esc = _h.escape(slide.title)
    dots = _dot(idx, total, a)
    thead = "".join("<th>%s</th>" % _h.escape(h) for h in slide.headers[:6])
    trows = ""
    for row in slide.rows[:12]:
        cells = ""
        for ci, cell in enumerate(row[:6]):
            esc = _h.escape(cell)
            if __import__("re").search(r"(快|高|强|首|支持|优势|本地|推荐|首选)", cell):
                cells += '<td class="hl">%s</td>' % esc
            else:
                cells += "<td>%s</td>" % esc
        trows += "<tr>%s</tr>" % cells
    css_lines = [
        '*{margin:0;padding:0;box-sizing:border-box}',
        'body{width:1080px;height:1440px;overflow:hidden;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;background:%s;color:#fff}' % b,
        '.slide{width:1080px;height:1440px;position:relative;display:flex;flex-direction:column;background:linear-gradient(180deg,%s 0%%,#14102e 100%%)}' % b,
        '.deco{position:absolute;top:-200px;right:-200px;width:500px;height:500px;border-radius:50%%;background:radial-gradient(circle,%s15 0%%,transparent 70%%);pointer-events:none}' % a,
        '.tp{height:150px;display:flex;align-items:center;justify-content:center;padding:20px 50px}',
        '.tp h2{font-size:30px;font-weight:700;text-align:center}',
        '.tw{flex:1;display:flex;align-items:flex-start;justify-content:center;padding:10px 40px 10px;overflow:hidden}',
        'table{border-collapse:collapse;width:100%%;font-size:17px}',
        'th{background:%s33;color:%s;font-weight:600;padding:8px 10px;text-align:left;border-bottom:2px solid %s66;white-space:nowrap}' % (a, a, a),
        'td{padding:7px 10px;border-bottom:1px solid rgba(255,255,255,0.06);color:rgba(255,255,255,0.82)}',
        '.hl{color:%s;font-weight:600}' % a,
        '.btm{height:120px;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;padding:0 60px 20px;gap:6px}',
        '.pg{display:inline-block;border-radius:50%%;margin:0 4px}',
    ]
    css = "\n".join(css_lines)
    body = '<div class="slide"><div class="deco"></div>\n'
    body += '<div class="tp"><h2>%s</h2></div>\n' % title_esc
    body += '<div class="tw"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>\n' % (thead, trows)
    body += '<div class="btm"><div>%s</div><span class="cnt" style="font-size:13px;color:rgba(255,255,255,0.3)">%d/%d</span></div>\n' % (dots, idx+1, total)
    body += '</div>'
    return '<!DOCTYPE html>\n<html><head><meta charset="UTF-8"><style>\n%s\n</style></head><body>\n%s\n</body></html>' % (css, body)



def _html_code(slide, idx, total):
    a = BRAND["accentColor"]; b = BRAND["bgColor"]
    title_esc = _h.escape(slide.title)
    dots = _dot(idx, total, a)
    lang_esc = _h.escape(slide.language or "code")
    raw = _h.escape(slide.code)
    # simple syntax highlight via re substitution
    re = __import__("re")
    raw = re.sub(r'\b(import|from|def|class|return|if|elif|else|for|while|try|except|with|async|await|print|True|False|None)\b',
                 r'<span style="color:#c084fc">\1</span>', raw)
    raw = re.sub(r'("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')',
                 r'<span style="color:#34d399">\1</span>', raw)
    raw = re.sub(r'(#.+?)(?:\n|$)',
                 r'<span style="color:#64748b">\1</span>', raw)
    css_lines = [
        '*{margin:0;padding:0;box-sizing:border-box}',
        'body{width:1080px;height:1440px;overflow:hidden;font-family:"JetBrains Mono","Fira Code","Cascadia Code",monospace,sans-serif;background:%s;color:#fff}' % b,
        '.slide{width:1080px;height:1440px;position:relative;display:flex;flex-direction:column;background:#0d1117}',
        '.deco{position:absolute;top:-200px;right:-200px;width:500px;height:500px;border-radius:50%%;background:radial-gradient(circle,%s10 0%%,transparent 70%%);pointer-events:none}' % a,
        '.tp{height:130px;display:flex;align-items:center;justify-content:center;padding:20px 50px}',
        '.tp h2{font-size:28px;font-weight:700;text-align:center}',
        '.lb{display:inline-block;background:%s22;color:%s;font-size:12px;padding:3px 12px;border-radius:10px;margin-left:12px;border:1px solid %s44}' % (a, a, a),
        '.cw{flex:1;display:flex;padding:10px 40px 10px;overflow:hidden}',
        '.cb{width:100%%;background:rgba(0,0,0,0.5);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:20px 24px;overflow-y:auto;font-size:16px;line-height:1.6;color:#e2e8f0;white-space:pre-wrap;word-break:break-word}',
        '.btm{height:110px;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;padding:0 60px 18px;gap:6px}',
        '.pg{display:inline-block;border-radius:50%%;margin:0 4px}',
    ]
    css = "\n".join(css_lines)
    body = '<div class="slide"><div class="deco"></div>\n'
    body += '<div class="tp"><h2>%s<span class="lb">%s</span></h2></div>\n' % (title_esc, lang_esc)
    body += '<div class="cw"><div class="cb">%s</div></div>\n' % raw
    body += '<div class="btm"><div>%s</div><span class="cnt" style="font-size:13px;color:rgba(255,255,255,0.3)">%d/%d</span></div>\n' % (dots, idx+1, total)
    body += '</div>'
    return '<!DOCTYPE html>\n<html><head><meta charset="UTF-8"><style>\n%s\n</style></head><body>\n%s\n</body></html>' % (css, body)


def _html_overview(slide, idx, total):
    a = BRAND["accentColor"]; b = BRAND["bgColor"]
    title_esc = _h.escape(slide.title)
    dots = _dot(idx, total, a)
    text_esc = _h.escape(clean_text_for_tts(slide.content_raw[:500]))
    css_lines = [
        '*{margin:0;padding:0;box-sizing:border-box}',
        'body{width:1080px;height:1440px;overflow:hidden;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;background:%s;color:#fff}' % b,
        '.slide{width:1080px;height:1440px;position:relative;display:flex;flex-direction:column;background:linear-gradient(180deg,%s 0%%,#14102e 100%%)}' % b,
        '.deco{position:absolute;top:-200px;right:-200px;width:500px;height:500px;border-radius:50%%;background:radial-gradient(circle,%s15 0%%,transparent 70%%);pointer-events:none}' % a,
        '.tp{height:180px;display:flex;align-items:center;justify-content:center;padding:30px 60px}',
        '.tp h2{font-size:34px;font-weight:700;text-align:center}',
        '.mid{flex:1;display:flex;align-items:center;justify-content:center;padding:20px 70px 10px}',
        '.mid .tx{font-size:26px;line-height:1.7;color:rgba(255,255,255,0.8);text-align:left}',
        '.btm{height:130px;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;padding:0 60px 20px;gap:6px}',
        '.pg{display:inline-block;border-radius:50%%;margin:0 4px}',
    ]
    css = "\n".join(css_lines)
    body = '<div class="slide"><div class="deco"></div>\n'
    body += '<div class="tp"><h2>%s</h2></div>\n' % title_esc
    body += '<div class="mid"><div class="tx">%s</div></div>\n' % text_esc
    body += '<div class="btm"><div>%s</div><span class="cnt" style="font-size:13px;color:rgba(255,255,255,0.3)">%d/%d</span></div>\n' % (dots, idx+1, total)
    body += '</div>'
    return '<!DOCTYPE html>\n<html><head><meta charset="UTF-8"><style>\n%s\n</style></head><body>\n%s\n</body></html>' % (css, body)


# ======== HTTP Server ========

class _SlidesHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PROJECT_DIR), **kwargs)
    def log_message(self, fmt, *args):
        pass


def start_http_server(port=18910):
    server = HTTPServer(("127.0.0.1", port), _SlidesHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    print("  HTTP server: http://127.0.0.1:%d" % port)
    return server, port


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


# ======== Mixed Screenshot Capture ========

async def capture_tech_slides(slides, base_url):
    from playwright.async_api import async_playwright

    CAPTURES_DIR.mkdir(parents=True, exist_ok=True)
    results = [""] * len(slides)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        for idx, slide in enumerate(slides):
            seg_dir = CAPTURES_DIR / ("seg_%03d" % idx)
            seg_dir.mkdir(parents=True, exist_ok=True)
            shot_path = seg_dir / "screenshot.png"
            if shot_path.exists():
                print("  [%d/%d] skip (exists): %s" % (idx+1, len(slides), slide.title[:50]))
                results[idx] = str(shot_path.relative_to(PROJECT_DIR))
                continue

            if slide.type == "screenshot" and slide.url:
                # URL screenshot: navigate directly
                context = await browser.new_context(viewport=URL_VIEWPORT)
                page = await context.new_page()
                print("  [%d/%d] URL截图: %s" % (idx+1, len(slides), slide.url[:70]))
                try:
                    await page.goto(slide.url, wait_until="networkidle", timeout=20000)
                    await page.wait_for_timeout(1000)
                    await page.screenshot(path=str(shot_path), full_page=False)
                    results[idx] = str(shot_path.relative_to(PROJECT_DIR))
                except Exception as e:
                    print("    [error] %s" % e)
                    results[idx] = ""
                await context.close()
            else:
                # Content slide: screenshot local HTML
                context = await browser.new_context(viewport=VIEWPORT)
                page = await context.new_page()
                url = "%s/slides/slide_%03d.html" % (base_url, idx)
                print("  [%d/%d] 截图: %s" % (idx+1, len(slides), slide.title[:50]))
                try:
                    await page.goto(url, wait_until="networkidle", timeout=15000)
                    await page.wait_for_timeout(500)
                    await page.screenshot(path=str(shot_path), full_page=False)
                    results[idx] = str(shot_path.relative_to(PROJECT_DIR))
                except Exception as e:
                    print("    [error] %s" % e)
                    results[idx] = ""
                await context.close()

        await browser.close()
    return results


# ======== TTS Generation ========

async def generate_tts(slides, voice="zh-CN-YunxiNeural", rate="+30%"):
    import edge_tts
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    durations = []
    for idx, slide in enumerate(slides):
        text = slide.tts_text
        if not text:
            durations.append(3.0)
            continue
        seg_path = AUDIO_DIR / ("seg_%03d.mp3" % idx)
        if seg_path.exists():
            dur = get_audio_duration(str(seg_path))
            durations.append(dur)
            print("  [%d/%d] skip TTS: %.1fs" % (idx+1, len(slides), dur))
            continue
        print("  [%d/%d] TTS (%d字): %s..." % (idx+1, len(slides), len(text), text[:60]))
        for attempt in range(3):
            try:
                c = edge_tts.Communicate(text, voice, rate=rate)
                await c.save(str(seg_path))
                dur = get_audio_duration(str(seg_path))
                durations.append(dur)
                print("    OK: %.1fs" % dur)
                break
            except Exception as e:
                if attempt < 2:
                    await __import__("asyncio").sleep(2)
                else:
                    print("    [error] TTS failed: %s" % e)
                    durations.append(5.0)
    return durations


# ======== Slide Generation ========

def generate_all_slides(slides):
    SLIDES_DIR.mkdir(parents=True, exist_ok=True)
    total = len(slides)
    for idx, slide in enumerate(slides):
        html = generate_slide_html(slide, idx, total)
        if html:  # screenshot slides return None
            path = SLIDES_DIR / ("slide_%03d.html" % idx)
            path.write_text(html, encoding="utf-8")
            print("  -> slides/slide_%03d.html [%s] %s" % (idx, slide.type, slide.title[:50]))
        else:
            print("  -> slides/slide_%03d.html [%s] (URL截图: %s)" % (idx, slide.type, slide.url[:60]))


# ======== Timeline + Index + Narration ========

def build_timeline(slides, screenshots, durations):
    timeline = []
    current = 0.0
    # intro
    intro_dur = TIMING["introDuration"]
    timeline.append({"type": "intro", "start": current, "duration": intro_dur, "idx": 0})
    current += intro_dur
    # content slides
    for idx, slide in enumerate(slides):
        if slide.type == "intro":
            continue
        dur = max(durations[idx] + TIMING["slidePadding"], TIMING["minSlideDuration"])
        timeline.append({
            "type": slide.type,
            "start": current,
            "duration": dur,
            "idx": idx,
            "title": slide.title,
            "screenshot": screenshots[idx] if idx < len(screenshots) else "",
            "audioPath": str(AUDIO_DIR / ("seg_%03d.mp3" % idx)),
        })
        current += dur
    # outro
    outro_dur = TIMING["outroDuration"] + 3
    timeline.append({"type": "outro", "start": current, "duration": outro_dur, "idx": len(slides)})
    current += outro_dur
    total_dur = current
    # print summary
    for item in timeline:
        t = item.get("title", item["type"])[:50]
        print("  %6.1fs - %6.1fs [%s] %s" % (item["start"], item["start"]+item["duration"], item["type"], t))
    print("\n  总时长: %.1fs" % total_dur)
    return timeline, total_dur


def build_index_html(timeline, total_dur, slides):
    import json as _json
    lines = []
    lines.append('<!DOCTYPE html>')
    lines.append('<html>')
    lines.append('<head><meta charset="UTF-8"><style>')
    lines.append('*{margin:0;padding:0;box-sizing:border-box}')
    lines.append('[data-composition-id="root"]{width:1080px;height:1440px;overflow:hidden;position:relative;background:%s;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif}' % BRAND["bgColor"])
    lines.append('</style></head><body>')
    lines.append('<div id="root" data-composition-id="root" data-width="1080" data-height="1440" data-start="0" data-duration="%s">' % str(total_dur))
    for item in timeline:
        sid = item["start"]
        sdir = item["duration"]
        if item["type"] == "intro":
            lines.append('  <div id="intro" data-composition-id="intro" data-composition-src="compositions/intro.html" data-start="%s" data-duration="%s"></div>' % (str(sid), str(sdir)))
        elif item["type"] == "outro":
            lines.append('  <div id="outro" class="clip" data-start="%s" data-duration="%s" style="position:absolute;top:0;left:0;width:1080px;height:1440px;overflow:hidden;z-index:100;opacity:0;display:block">' % (str(sid), str(sdir)))
            lines.append('    <div data-composition-id="outro-inner" data-composition-src="compositions/outro.html" data-start="0" data-duration="%s"></div>' % str(sdir))
            lines.append('  </div>')
        else:
            shot = item.get("screenshot", "")
            if shot:
                lines.append('  <img id="slide-%d" class="clip" src="%s" data-start="%s" data-duration="%s" style="position:absolute;top:0;left:0;width:1080px;height:1440px;object-fit:cover;z-index:1;opacity:0">' % (item["idx"], shot, str(sid), str(sdir)))
    lines.append('</div>')
    # Build shot data for visibility control
    shot_data = []
    for item in timeline:
        if item["type"] not in ("intro", "outro"):
            shot_data.append({"id": "slide-%d" % item["idx"], "start": item["start"], "duration": item["duration"]})
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
    lines.append('    var s=HF_SHOTS[i];var el=document.getElementById(s.id);')
    lines.append('    if(!el)continue;')
    lines.append('    var st=s.start,ed=s.start+s.duration;')
    lines.append('    if(t>=st&&t<=ed){el.style.opacity="1";el.style.display="block";')
    lines.append('    }else{el.style.opacity="0";el.style.display="none";}')
    lines.append('  }')
    lines.append('});')
    lines.append('</script>')
    lines.append('</body></html>')
    path = PROJECT_DIR / "index.html"
    path.write_text("\n".join(lines), encoding="utf-8")
    print("  -> index.html")


def build_narration(timeline, total_dur):
    blank_path = AUDIO_DIR / "blank.wav"
    if not blank_path.exists():
        subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
             "-t", str(total_dur), str(blank_path)],
            capture_output=True, text=True)
    inputs = [str(blank_path)]
    filter_parts = []
    next_idx = 1
    delayed_labels = []
    for item in timeline:
        if item["type"] in ("intro", "outro", "screenshot"):
            continue
        audio_path = item.get("audioPath", "")
        if not audio_path or not os.path.exists(audio_path):
            continue
        delay_ms = int(item["start"] * 1000)
        inputs.append(audio_path)
        label = "s%d" % next_idx
        filter_parts.append("[%d:a]adelay=%d|%d[%s]" % (next_idx, delay_ms, delay_ms, label))
        delayed_labels.append("[%s]" % label)
        next_idx += 1
    if next_idx == 1:
        print("  [warn] 无TTS音频")
        return ""
    mix_inputs = "[0:a] " + " ".join(delayed_labels)
    filter_parts.append("%samix=inputs=%d:duration=first:dropout_transition=0[out]" % (mix_inputs, next_idx))
    filter_str = ";".join(filter_parts)
    output_path = str(AUDIO_DIR / "narration.wav")
    cmd = (["ffmpeg", "-y"] +
           sum([["-i", inp] for inp in inputs], []) +
           ["-filter_complex", filter_str,
            "-map", "[out]", "-c:a", "pcm_s16le",
            "-t", str(total_dur), output_path])
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("  [error] 音频合成失败: " + result.stderr[-300:])
        return ""
    mp3_path = str(AUDIO_DIR / "narration.mp3")
    subprocess.run(
        ["ffmpeg", "-y", "-i", output_path, "-c:a", "libmp3lame", "-q:a", "2", mp3_path],
        capture_output=True)
    return mp3_path


# ======== Main ========

async def main():
    import argparse
    parser = argparse.ArgumentParser(description="技术/调研分享 → 3:4竖版视频")
    parser.add_argument("--md", default="research.md", help="调研Markdown文件")
    parser.add_argument("--voice", default="zh-CN-YunxiNeural", help="TTS语音")
    parser.add_argument("--rate", default="+30%", help="TTS语速")
    parser.add_argument("--output", default="tech-share-final.mp4", help="输出MP4路径")
    parser.add_argument("--port", type=int, default=18910, help="本地HTTP端口")
    parser.add_argument("--skip-capture", action="store_true", help="跳过截图")
    parser.add_argument("--skip-tts", action="store_true", help="跳过TTS")
    parser.add_argument("--skip-subs", action="store_true", help="跳过字幕")
    parser.add_argument("--bgm", help="背景音乐文件路径")
    parser.add_argument("--skip-render", action="store_true", help="只生成HTML")
    parser.add_argument("--brand-title", help="自定义标题")
    parser.add_argument("--brand-accent", help="自定义强调色 (如 #6366f1)")
    args = parser.parse_args()

    md_path = Path(args.md)
    if not md_path.is_absolute():
        md_path = PROJECT_DIR / args.md

    if args.brand_title:
        BRAND["title"] = args.brand_title
    if args.brand_accent:
        BRAND["accentColor"] = args.brand_accent

    print("源文件: " + str(md_path))
    print("工作目录: " + str(PROJECT_DIR))

    print("\n── [0/7] 解析Markdown ──")
    slides, h1_title = parse_tech_markdown(str(md_path))
    update_brand_from_md(md_path, h1_title)
    print("  解析到 %d 个章节: " % len(slides))
    for i, s in enumerate(slides):
        print("  [%d] %s: %s" % (i+1, s.type, s.title[:60]))

    print("\n── [1/7] 生成HTML卡片 ──")
    generate_all_slides(slides)

    print("\n── [2/7] 启动HTTP服务器 ──")
    server, port = start_http_server(args.port)
    base_url = "http://127.0.0.1:%d" % port
    await __import__("asyncio").sleep(0.5)

    if not args.skip_capture:
        print("\n── [3/7] 截图捕获（混合: HTML卡片 + URL远程） ──")
        screenshots = await capture_tech_slides(slides, base_url)
    else:
        print("\n  跳过截图")
        screenshots = [""] * len(slides)

    if not args.skip_tts:
        print("\n── [4/7] TTS配音 ──")
        durations = await generate_tts(slides, args.voice, args.rate)
    else:
        print("\n  跳过TTS")
        durations = [TIMING["minSlideDuration"]] * len(slides)

    print("\n── [5/7] 时间线计算 ──")
    timeline, total_dur = build_timeline(slides, screenshots, durations)
    build_index_html(timeline, total_dur, slides)

    print("\n── [6/7] 音频合成 ──")
    narration_path = build_narration(timeline, total_dur)

    if not args.skip_render:
        print("\n── [7/7] HyperFrames渲染 ──")
        output_path = str((PROJECT_DIR / args.output).resolve())
        cmd = 'npx hyperframes render -o "%s" --quality standard --fps 30 --workers 2 --page-side-compositing=no "%s"' % (output_path, str(PROJECT_DIR))
        print("  运行: " + cmd)
        result = subprocess.run(cmd, capture_output=False, text=True, shell=True)
        if result.returncode != 0:
            print("  [error] render失败 (exit=%d)" % result.returncode)
            return
        if os.path.exists(output_path):
            size_mb = os.path.getsize(output_path) / (1024*1024)
            print("  ✅ 完成: %s (%.1f MB)" % (output_path, size_mb))
            if narration_path and os.path.exists(narration_path):
                merged_path = output_path.replace(".mp4", "-with-audio.mp4")
                print("\n── 合并音轨 ──")
                if args.bgm and os.path.exists(args.bgm):
                    print("  BGM: " + args.bgm)
                    bgm_mixed = str(AUDIO_DIR / "narration_with_bgm.mp3")
                    bgm_cmd = [
                        "ffmpeg", "-y",
                        "-i", narration_path,
                        "-stream_loop", "-1", "-i", args.bgm,
                        "-filter_complex",
                        "[1:a]volume=0.15[bgm];[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=0[out]",
                        "-map", "[out]", "-c:a", "libmp3lame", "-q:a", "2",
                        "-t", str(total_dur), bgm_mixed,
                    ]
                    result = subprocess.run(bgm_cmd, capture_output=True, text=True)
                    audio_input = bgm_mixed if result.returncode == 0 else narration_path
                else:
                    audio_input = narration_path
                merge_cmd = [
                    "ffmpeg", "-y",
                    "-i", output_path,
                    "-i", audio_input,
                    "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k",
                    "-map", "0:v:0", "-map", "1:a:0",
                    "-shortest", merged_path,
                ]
                result = subprocess.run(merge_cmd, capture_output=True, text=True)
                if result.returncode == 0 and os.path.exists(merged_path):
                    merged_mb = os.path.getsize(merged_path) / (1024*1024)
                    print("  ✅ 音轨合并: %s (%.1f MB)" % (merged_path, merged_mb))
                else:
                    print("  [error] 合并失败")
        else:
            print("  [error] 输出文件不存在: " + output_path)
    else:
        print("\n  ⏭ 跳过渲染 (--skip-render)")



def _html_intro():
    a = BRAND["accentColor"]; b = BRAND["bgColor"]
    t = _h.escape(BRAND["title"]); s = _h.escape(BRAND["subtitle"]); g = _h.escape(BRAND["tagline"])
    css = (
        '*{margin:0;padding:0;box-sizing:border-box}' + "\n"
        'body{width:1080px;height:1440px;overflow:hidden;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;background:%s;color:#fff}' % b + "\n"
        '.intro{width:1080px;height:1440px;display:flex;flex-direction:column;justify-content:center;align-items:center;position:relative;overflow:hidden}' + "\n"
        '.glow{position:absolute;top:50%%;left:50%%;transform:translate(-50%%,-50%%);width:700px;height:700px;border-radius:50%%;background:radial-gradient(circle,%s20 0%%,transparent 60%%);pointer-events:none}' % a + "\n"
        '.grid{position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,0.03) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.03) 1px,transparent 1px);background-size:40px 40px;pointer-events:none}' + "\n"
        '.ib{width:80px;height:80px;border:2px solid %s66;border-radius:50%%;display:flex;align-items:center;justify-content:center;margin-bottom:32px;z-index:1}' % a + "\n"
        '.ib svg{width:36px;height:36px;stroke:%s;fill:none}' % a + "\n"
        '.h1{font-size:46px;font-weight:800;letter-spacing:0.04em;margin-bottom:12px;text-align:center;z-index:1;padding:0 40px}' + "\n"
        '.h2{font-size:20px;font-weight:400;color:rgba(255,255,255,0.5);letter-spacing:0.12em;margin-bottom:30px;z-index:1}' + "\n"
        '.dv{width:80px;height:2px;background:%s;border-radius:2px;margin-bottom:24px;z-index:1}' % a + "\n"
        '.tg{font-size:14px;color:rgba(255,255,255,0.3);letter-spacing:0.06em;z-index:1;text-align:center;padding:0 60px;word-break:break-all}'
    )
    body = '<div class="intro"><div class="glow"></div><div class="grid"></div>' + "\n"
    body += '<div class="ib"><svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg></div>' + "\n"
    body += '<div class="h1">%s</div>' % t + "\n"
    body += '<div class="h2">%s</div>' % s + "\n"
    body += '<div class="dv"></div>' + "\n"
    body += '<div class="tg">%s</div>' % g + "\n"
    body += '</div>'
    return '<!DOCTYPE html>\n<html><head><meta charset="UTF-8"><style>\n%s\n</style></head><body>\n%s\n</body></html>' % (css, body)


def _html_conclusion():
    a = BRAND["accentColor"]; b = BRAND["bgColor"]
    t = _h.escape(BRAND["title"]); s = _h.escape(BRAND["subtitle"])
    css = (
        '*{margin:0;padding:0;box-sizing:border-box}' + "\n"
        'body{width:1080px;height:1440px;overflow:hidden;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;background:%s;color:#fff}' % b + "\n"
        '.outro{width:1080px;height:1440px;display:flex;flex-direction:column;justify-content:center;align-items:center;position:relative;overflow:hidden}' + "\n"
        '.glow{position:absolute;top:50%%;left:50%%;transform:translate(-50%%,-50%%);width:700px;height:700px;border-radius:50%%;background:radial-gradient(circle,%s15 0%%,transparent 60%%);pointer-events:none}' % a + "\n"
        '.chk{width:72px;height:72px;border:3px solid %s;border-radius:50%%;display:flex;align-items:center;justify-content:center;margin-bottom:28px;z-index:1}' % a + "\n"
        '.chk svg{width:36px;height:36px;stroke:%s;fill:none}' % a + "\n"
        '.h1o{font-size:40px;font-weight:700;letter-spacing:0.04em;margin-bottom:10px;text-align:center;z-index:1;padding:0 40px}' + "\n"
        '.h2o{font-size:18px;color:rgba(255,255,255,0.4);letter-spacing:0.1em;z-index:1;padding:0 60px;text-align:center}' + "\n"
        '.dt{font-size:13px;color:rgba(255,255,255,0.2);margin-top:30px;z-index:1}'
    )
    body = '<div class="outro"><div class="glow"></div>' + "\n"
    body += '<div class="chk"><svg viewBox="0 0 24 24" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg></div>' + "\n"
    body += '<div class="h1o">%s</div>' % _h.escape("感谢观看") + "\n"
    body += '<div class="h2o">%s</div>' % t + "\n"
    body += '<div class="dt">%s</div>' % s + "\n"
    body += '</div>'
    return '<!DOCTYPE html>\n<html><head><meta charset="UTF-8"><style>\n%s\n</style></head><body>\n%s\n</body></html>' % (css, body)


if __name__ == "__main__":
    asyncio.run(main())
