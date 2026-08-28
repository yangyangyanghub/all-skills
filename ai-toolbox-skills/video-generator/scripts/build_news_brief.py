"""
新闻简报模式 —— 同类新闻合屏展示，无配音，BGM，15 秒以内
流程:
  1. 解析 daily-brief.md → 按分类分组，每屏最多 5 条
  2. 生成 compositions/brief.html（所有分组 + GSAP 过渡动画）
  3. 生成 index.html（引用 brief composition）
  4. hyperframes render → 添加 BGM → final.mp4
"""
import json, os, re, subprocess, sys, html as html_mod
from pathlib import Path
from collections import OrderedDict
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent.resolve()
COMPOSITIONS_DIR = SCRIPT_DIR / "compositions"

THEME = {
    "bgGradient": "linear-gradient(180deg, #0a0e27 0%, #111638 50%, #0d1230 100%)",
    "accent": "#818cf8",
    "keywordCyan": "#22d3ee",
    "keywordGreen": "#4ade80",
    "textSecondary": "rgba(255,255,255,0.6)",
}

CATEGORY_STYLES = OrderedDict([
    ("AI 与智能化",       {"badge_bg": "#818cf822", "badge_border": "#818cf844", "badge_text": "#818cf8"}),
    ("遥感、产品与行业动态", {"badge_bg": "#34d39922", "badge_border": "#34d39944", "badge_text": "#34d399"}),
    ("今日重点",           {"badge_bg": "#f59e0b22", "badge_border": "#f59e0b44", "badge_text": "#f59e0b"}),
])

sys.path.insert(0, str(SCRIPT_DIR))
from build_news_video import parse_markdown, NewsItem


def extract_date(md_path):
    date_str = Path(md_path).parent.name
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", date_str)
    if m:
        return "%s年%s月%s日" % (m.group(1), int(m.group(2)), int(m.group(3)))
    try:
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()
        dm = re.search(r"(\d{4})-(\d{2})-(\d{2})", content)
        if dm:
            return "%s年%s月%s日" % (dm.group(1), int(dm.group(2)), int(dm.group(3)))
    except:
        pass
    return datetime.now().strftime("%Y年%m月%d日")


def group_items(items, max_per_screen=5):
    groups = []
    seen = set()
    for item in items:
        if item.priority == "tool":
            continue
        if item.title in seen:
            continue
        seen.add(item.title)
        found = None
        for g in groups:
            if g["category"] == item.category and len(g["items"]) < max_per_screen:
                found = g
                break
        if found is None:
            found = {"category": item.category, "items": []}
            groups.append(found)
        found["items"].append(item)
    return groups


def escape_and_highlight(text):
    """HTML 转义 + 关键词高亮"""
    escaped = html_mod.escape(text)
    # 数字高亮
    escaped = re.sub(
        r"(\d+[\.\d]*)\s*(亿|万|千|%)",
        r'<span class="kw-num">\1\2</span>',
        escaped,
    )
    companies = [
        "Nex-AGI", "SpaceX", "xAI", "OpenAI", "Anthropic", "Google", "Apple",
        "Kimi", "阿里", "腾讯", "百度", "字节", "华为", "高德", "文远知行",
        "NASA", "MDPI", "Qwen", "GPT", "Claude", "Gemini", "Cursor",
        "RTPurboV2", "MANGO", "ABot-Earth", "WRD", "ATLAS", "Colossus",
        "MCP", "Agent Swarm", "AI4S",
    ]
    for c in companies:
        escaped = re.sub(
            r"(?<![a-zA-Z])" + re.escape(c) + r"(?![a-zA-Z])",
            r'<span class="kw">\g<0></span>',
            escaped,
        )
    return escaped


def generate_brief_composition(groups, date_str, per_slide=3.5):
    total_groups = len(groups)
    if total_groups == 0:
        print("  [error] 没有新闻条目")
        return None, 0

    fade_duration = 0.4
    total_duration = total_groups * per_slide

    slides_html = []
    for gi, group in enumerate(groups):
        category = group["category"]
        cat_style = CATEGORY_STYLES.get(
            category,
            {"badge_bg": "#6366f122", "badge_border": "#6366f144", "badge_text": "#6366f1"},
        )
        items = group["items"]

        # 列表项
        list_html = ""
        for idx, item in enumerate(items):
            title_hl = escape_and_highlight(item.title)
            summary_hl = escape_and_highlight(item.summary) if item.summary else ""
            delay = 0.08 * idx
            list_html += (
                '<div class="list-item" style="animation-delay:%.2fs">'
                '  <div class="item-num" style="color:%s">%02d</div>'
                '  <div class="item-body">'
                '    <div class="item-title">%s</div>'
                '    <div class="item-summary">%s</div>'
                "  </div>"
                "</div>"
            ) % (delay, cat_style["badge_text"], idx + 1, title_hl, summary_hl)

        # 底部圆点
        dots = ""
        for i in range(total_groups):
            if i == gi:
                dots += '<span class="dot active" style="background:%s"></span>' % cat_style["badge_text"]
            else:
                dots += '<span class="dot"></span>'

        slide_html = (
            '<div class="slide" id="slide-%d">'
            '  <div class="grid-bg"></div>'
            '  <div class="glow" style="background:radial-gradient(circle,%s08 0%%,transparent 60%%)"></div>'
            '  <div class="top-area">'
            '    <div class="date-line">%s</div>'
            '    <div class="cat-row">'
            '      <span class="badge" style="background:%s;border-color:%s;color:%s">%s</span>'
            "    </div>"
            '    <div class="divider"></div>'
            "  </div>"
            '  <div class="list-area">%s</div>'
            '  <div class="bottom-area">'
            '    <div class="page-dots">%s</div>'
            "  </div>"
            "</div>"
        ) % (
            gi,
            cat_style["badge_text"],
            date_str,
            cat_style["badge_bg"],
            cat_style["badge_border"],
            cat_style["badge_text"],
            html_mod.escape(category),
            list_html,
            dots,
        )
        slides_html.append(slide_html)

    all_slides = "\n".join(slides_html)

    # CSS + JS
    html = """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1440px;overflow:hidden;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;background:#0a0e27;color:#fff}
.slide{width:1080px;height:1440px;position:absolute;top:0;left:0;display:flex;flex-direction:column;background:%s;opacity:0;transition:opacity %.1fs ease-in-out}
.slide.active{opacity:1;z-index:10}
.grid-bg{position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,0.02) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.02) 1px,transparent 1px);background-size:60px 60px;pointer-events:none}
.glow{position:absolute;top:-100px;right:-100px;width:500px;height:500px;border-radius:50%%;pointer-events:none}
.top-area{height:220px;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:28px 60px 16px;gap:12px;position:relative;z-index:2}
.date-line{font-size:22px;font-weight:400;color:rgba(255,255,255,0.4);letter-spacing:0.08em}
.cat-row{display:flex;align-items:center;gap:12px}
.badge{display:inline-block;font-size:13px;font-weight:600;padding:5px 16px;border-radius:14px;border:1px solid;letter-spacing:0.04em}
.divider{width:40px;height:2px;background:%s;border-radius:2px;opacity:0.5}
.list-area{flex:1;display:flex;flex-direction:column;justify-content:center;padding:8px 60px 10px;position:relative;z-index:2}
.list-item{display:flex;align-items:flex-start;gap:14px;padding:12px 18px;margin-bottom:5px;border-radius:10px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.05);animation:fadeInUp 0.45s ease-out both;opacity:0}
@keyframes fadeInUp{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:translateY(0)}}
.item-num{font-size:18px;font-weight:800;min-width:32px;text-align:center;padding-top:2px;flex-shrink:0}
.item-body{flex:1;min-width:0}
.item-title{font-size:22px;font-weight:700;line-height:1.3;color:#fff;margin-bottom:3px}
.item-summary{font-size:15px;line-height:1.4;color:%s}
.kw{color:%s;font-weight:600}
.kw-num{color:%s;font-weight:700}
.bottom-area{height:80px;display:flex;align-items:center;justify-content:center;position:relative;z-index:2;padding-bottom:20px}
.page-dots{display:flex;gap:8px}
.dot{width:7px;height:7px;border-radius:50%%;background:rgba(255,255,255,0.15);transition:background 0.3s}
.dot.active{box-shadow:0 0 6px currentColor}
</style></head><body>
<div id="brief-root" data-composition-id="brief" data-width="1080" data-height="1440">
%s
</div>
<script src="https://cdn.jsdelivr.net/npm/gsap@3/dist/gsap.min.js"></script>
<script>
(function(){
var totalSlides = %d;
var slideDur = %.1f;
var fadeDur = %.1f;

function showSlide(idx){
  for(var i=0;i<totalSlides;i++){
    var el = document.getElementById("slide-"+i);
    if(!el) continue;
    if(i===idx) el.classList.add("active");
    else el.classList.remove("active");
  }
}

var tl = gsap.timeline({paused:true});
for(var i=0;i<totalSlides;i++){
  (function(idx){
    if(idx===0){
      tl.call(function(){showSlide(0);}, [], ">", 0);
    } else {
      tl.call(function(){showSlide(idx);}, [], ">", 0);
      tl.to({}, {duration: fadeDur}, ">");
    }
    if(idx < totalSlides - 1){
      tl.to({}, {duration: slideDur - fadeDur}, ">");
    }
  })(i);
}
tl.to({}, {duration: slideDur}, ">");

window.__timelines = window.__timelines || {};
window.__timelines["brief"] = tl;
})();
</script>
</body></html>""" % (
        THEME["bgGradient"],
        fade_duration,
        THEME["accent"],
        THEME["textSecondary"],
        THEME["keywordCyan"],
        THEME["keywordGreen"],
        all_slides,
        total_groups,
        per_slide,
        fade_duration,
    )

    comp_path = COMPOSITIONS_DIR / "brief.html"
    comp_path.parent.mkdir(parents=True, exist_ok=True)
    comp_path.write_text(html, encoding="utf-8")
    print("  -> compositions/brief.html")
    return comp_path, total_duration


def generate_index_html(total_duration):
    html = """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
[data-composition-id="root"]{width:1080px;height:1440px;overflow:hidden;position:relative;background:#0a0e27}
</style></head><body>
<div id="root" data-composition-id="root" data-width="1080" data-height="1440" data-start="0" data-duration="%.1f">
  <div data-composition-id="brief" data-composition-src="compositions/brief.html" data-start="0" data-duration="%.1f"></div>
</div>
<script src="https://cdn.jsdelivr.net/npm/gsap@3/dist/gsap.min.js"></script>
<script>
(function(){
var tl = gsap.timeline({paused:true});
tl.to({}, {duration: %.1f});
window.__timelines = window.__timelines || {};
window.__timelines["root"] = tl;
})();
</script>
</body></html>""" % (total_duration, total_duration, total_duration)
    path = SCRIPT_DIR / "index.html"
    path.write_text(html, encoding="utf-8")
    print("  -> index.html")


def add_bgm(video_path, bgm_path, output_path):
    """给无声视频添加 BGM（循环 + 音量控制）"""
    print("\n── 添加 BGM ──")
    if not bgm_path or not os.path.exists(bgm_path):
        print("  [warn] BGM 文件不存在: %s" % bgm_path)
        return False
    print("  BGM: " + bgm_path)
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-stream_loop", "-1", "-i", bgm_path,
        "-filter_complex", "[1:a]volume=0.12[a]",
        "-map", "0:v:0", "-map", "[a]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-shortest", output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("  [error] BGM 添加失败: %s" % result.stderr[-300:])
        return False
    if os.path.exists(output_path):
        mb = os.path.getsize(output_path) / (1024 * 1024)
        print("  ✅ BGM 合成: %s (%.1f MB)" % (output_path, mb))
        return True
    return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description="新闻简报模式 —— 同类新闻合屏")
    parser.add_argument("--md", required=True, help="Markdown 文件路径")
    parser.add_argument("--output", default="brief-final.mp4", help="输出 MP4 路径")
    parser.add_argument("--bgm", default=None, help="BGM 文件路径")
    parser.add_argument("--per-slide", type=float, default=3.5, help="每屏时长(秒)")
    parser.add_argument("--skip-render", action="store_true", help="只生成 HTML")
    args = parser.parse_args()

    md_path = Path(args.md)
    if not md_path.is_absolute():
        md_path = SCRIPT_DIR / args.md

    print("源文件: " + str(md_path))
    date_str = extract_date(str(md_path))
    print("日期: " + date_str)

    print("\n── [1/4] 解析 Markdown ──")
    items = parse_markdown(str(md_path))
    print("  解析到 %d 条新闻" % len(items))

    print("\n── [2/4] 按分类分组 ──")
    groups = group_items(items, max_per_screen=5)
    print("  分组: " + ", ".join("%s(%d条)" % (g["category"], len(g["items"])) for g in groups))

    print("\n── [3/4] 生成 HTML ──")
    # 清理旧文件
    old_brief = COMPOSITIONS_DIR / "brief.html"
    if old_brief.exists():
        old_brief.unlink()
    generate_brief_composition(groups, date_str, per_slide=args.per_slide)
    total_dur = len(groups) * args.per_slide
    generate_index_html(total_dur)
    print("  总时长: %.1fs (%d屏 x %.1fs)" % (total_dur, len(groups), args.per_slide))

    if not args.skip_render:
        print("\n── [4/4] HyperFrames 渲染 ──")
        output_path = str((SCRIPT_DIR / args.output).resolve())
        cmd = (
            'npx hyperframes render -o "' + output_path + '" '
            '--quality standard --fps 30 --workers 2 --page-side-compositing=no "'
            + str(SCRIPT_DIR) + '"'
        )
        print("  运行: " + cmd)
        result = subprocess.run(cmd, capture_output=False, text=True, shell=True)
        if result.returncode != 0:
            print("  [error] render 失败 (exit=%d)" % result.returncode)
            return
        if os.path.exists(output_path):
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            print("  ✅ 完成: %s (%.1f MB)" % (output_path, size_mb))

            # BGM 合成
            if args.bgm and os.path.exists(args.bgm):
                merged_path = output_path.replace(".mp4", "-with-bgm.mp4")
                add_bgm(output_path, args.bgm, merged_path)
        else:
            print("  [error] 输出文件不存在: " + output_path)


if __name__ == "__main__":
    main()