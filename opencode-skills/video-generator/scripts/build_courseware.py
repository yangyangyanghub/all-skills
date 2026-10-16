"""
交互课件 → 16:9 技术讲解视频构建器

输入: interactive-courseware-builder 产出的单文件 HTML 课件（Step 3 静态产物）
流程:
  1. Playwright 打开课件，读 PAGE_IDS/PAGE_LABELS 页面清单
  2. 逐页 showPage(i) → 展开 reveal → 截图 1920×1080
  3. 按页面类型（cover/teach/quiz/sim/summary）提取 TTS 文案
  4. edge-tts 逐页配音
  5. 时间线（封面=片头、总结=片尾，无独立 intro/outro）→ HyperFrames 渲染 → 合成音轨
"""
import asyncio
import os
import re
import subprocess
import sys
from pathlib import Path

# 复用技术分享模式的共享设施（目录、时长探测、浏览器启动）
from build_tech_share import (
    PROJECT_DIR, get_audio_duration, _launch_browser,
)

VIEWPORT = {"width": 1920, "height": 1080}

BRAND = {
    "title": "技术讲解",
    "bgColor": "#0c0a1d",
}

TIMING = {
    "minSlideDuration": 4,
    "slidePadding": 1.0,
}

CW_CAPTURES_DIR = PROJECT_DIR / "captures" / "courseware"
CW_AUDIO_DIR = PROJECT_DIR / "audio" / "courseware"


# ════════════════════════════════════════════════════
# TTS 文案清洗
# ════════════════════════════════════════════════════

def clean_tts_text(text, max_chars=320):
    text = re.sub(r"https?://[^\s]+", "", text)
    text = re.sub(r"[\U0001F300-\U0001FAFF\u2700-\u27BF\u2600-\u26FF]", "", text)
    text = re.sub(r"[|｜/·•●◆■▶▶️]+", "，", text)
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[，]{2,}", "，", text).strip("，。 ")
    if len(text) > max_chars:
        text = text[:max_chars].rstrip("，;；:") + "。"
    return text


def build_tts_text(page_type, title, body, n_quiz=0):
    title = clean_tts_text(title, 60)
    body = clean_tts_text(body)
    if page_type == "cover":
        return (title + "。" + body) if body else (title + "。我们开始今天的学习。")
    if page_type == "quiz":
        head = title + "。" if title else ""
        return head + "这里有几道题，请暂停视频想一想。" + (body[:120] if body else "")
    if page_type == "sim":
        head = title + "。" if title else ""
        return head + (body if body else "请仔细观察这个仿真演示。")
    if page_type == "summary":
        return (title + "。我们来总结一下。" + body) if body else (title + "。以上就是本节课的全部内容。感谢观看。")
    # teach
    return (title + "。" + body) if body else title


# ════════════════════════════════════════════════════
# 页面探测 + 截图 + 文案提取（一次遍历完成）
# ════════════════════════════════════════════════════

PAGE_INSPECT_JS = """
() => {
  const sec = document.querySelector('.page.active');
  if (!sec) return null;
  let type = 'teach';
  if (sec.querySelector('.cover-page')) type = 'cover';
  else if (sec.querySelector('.quiz-page')) type = 'quiz';
  else if (sec.querySelector('.sim-page')) type = 'sim';
  else if (sec.querySelector('[class*="summary"]')) type = 'summary';
  const titleEl = sec.querySelector('.teach-title, .quiz-title, .sim-title, .cover-page h1, .cover-page h2, h1');
  const title = titleEl ? titleEl.innerText.trim() : '';
  let body = '';
  if (type === 'quiz') {
    body = Array.from(sec.querySelectorAll('.q-stem')).map(e => e.innerText.trim()).join('；');
  } else if (type === 'cover') {
    body = Array.from(sec.querySelectorAll('.cover-page .sub, .cover-page p'))
      .map(e => e.innerText.trim())
      .filter(t => t && !t.includes('点击右下角') && !t.includes('点击顶部'))
      .join('。');
  } else {
    body = Array.from(sec.querySelectorAll('.teach-text, .sim-desc, .key-box, .card, [class*="summary"] p, [class*="summary"] li'))
      .map(e => e.innerText.trim())
      .filter(Boolean)
      .join('。');
  }
  return { type, title, body };
}
"""

EXPAND_REVEAL_JS = """
() => {
  document.querySelectorAll('.reveal-hidden').forEach(el => {
    el.classList.remove('reveal-hidden');
    el.classList.add('reveal-done');
  });
  const hint = document.getElementById('revealHint');
  if (hint) hint.style.setProperty('display', 'none', 'important');
  const nav = document.getElementById('navBtns');
  if (nav) nav.style.setProperty('display', 'none', 'important');
  const lb = document.getElementById('imgLightbox');
  if (lb) lb.style.setProperty('display', 'none', 'important');
}
"""


async def capture_courseware(html_path):
    """打开课件 → 读页面清单 → 逐页截图+文案。返回 pages 列表。"""
    from playwright.async_api import async_playwright

    file_url = Path(html_path).resolve().as_uri()
    print("  课件: " + file_url)

    pages = []
    async with async_playwright() as p:
        browser = await _launch_browser(p)
        context = await browser.new_context(viewport=VIEWPORT)
        page = await context.new_page()
        await page.goto(file_url, wait_until="load", timeout=60000)
        await page.wait_for_timeout(2000)

        page_ids = await page.evaluate("() => window.PAGE_IDS || []")
        page_labels = await page.evaluate("() => window.PAGE_LABELS || []")
        if not page_ids:
            raise RuntimeError("未读到 PAGE_IDS——确认输入是 interactive-courseware-builder 课件（含翻页系统）")
        total = len(page_ids)
        print("  页面清单: %d 页 %s" % (total, page_labels))

        CW_CAPTURES_DIR.mkdir(parents=True, exist_ok=True)

        for i in range(total):
            seg_dir = CW_CAPTURES_DIR / ("seg_%03d" % i)
            seg_dir.mkdir(parents=True, exist_ok=True)
            shot_path = seg_dir / "screenshot.png"

            info = None
            await page.evaluate("(i) => showPage(i)", i)
            await page.wait_for_timeout(1200)
            await page.evaluate(EXPAND_REVEAL_JS)
            await page.wait_for_timeout(600)
            info = await page.evaluate(PAGE_INSPECT_JS)
            if info is None:
                info = {"type": "teach", "title": page_labels[i] if i < len(page_labels) else "", "body": ""}
            await page.screenshot(path=str(shot_path), full_page=False)

            n_quiz = await page.evaluate(
                "() => document.querySelectorAll('.page.active .quiz-q').length"
            )
            pages.append({
                "idx": i,
                "id": page_ids[i],
                "label": page_labels[i] if i < len(page_labels) else ("第%d页" % (i + 1)),
                "type": info["type"],
                "title": info["title"] or (page_labels[i] if i < len(page_labels) else ""),
                "body": info["body"],
                "n_quiz": n_quiz,
                "screenshot": str(shot_path.relative_to(PROJECT_DIR)),
            })
            print("  [%d/%d] %s [%s] %s" % (
                i + 1, total, pages[-1]["label"], info["type"], info["title"][:40]))

        await browser.close()
    return pages


# ════════════════════════════════════════════════════
# TTS
# ════════════════════════════════════════════════════

async def generate_tts(pages, voice, rate, skip_pages=()):
    import edge_tts
    CW_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    durations = []
    for pg in pages:
        idx = pg["idx"]
        seg_path = CW_AUDIO_DIR / ("seg_%03d.mp3" % idx)
        if pg["type"] in skip_pages:
            durations.append(3.0)
            continue
        text = build_tts_text(pg["type"], pg["title"], pg["body"], pg["n_quiz"])
        pg["tts_text"] = text
        if seg_path.exists():
            dur = get_audio_duration(str(seg_path))
            durations.append(dur)
            print("  [%d/%d] skip TTS: %.1fs" % (idx + 1, len(pages), dur))
            continue
        print("  [%d/%d] TTS (%d字): %s..." % (idx + 1, len(pages), len(text), text[:50]))
        ok = False
        for attempt in range(3):
            try:
                c = edge_tts.Communicate(text, voice, rate=rate)
                await c.save(str(seg_path))
                dur = get_audio_duration(str(seg_path))
                if dur <= 0.1:
                    raise RuntimeError("空音频 (dur=%.2fs)" % dur)
                durations.append(dur)
                print("    OK: %.1fs" % dur)
                ok = True
                break
            except Exception as e:
                if seg_path.exists():
                    seg_path.unlink(missing_ok=True)
                if attempt < 2:
                    await asyncio.sleep(2)
                else:
                    print("    [error] TTS failed: %s" % e)
        if not ok:
            durations.append(4.0)
    return durations


# ════════════════════════════════════════════════════
# 时间线 + index.html（16:9，无独立 intro/outro）
# ════════════════════════════════════════════════════

def build_timeline(pages, durations, skip_pages=()):
    timeline = []
    current = 0.0
    for pg in pages:
        if pg["type"] in skip_pages:
            continue
        dur = max(durations[pg["idx"]] + TIMING["slidePadding"], TIMING["minSlideDuration"])
        timeline.append({
            "type": pg["type"],
            "start": current,
            "duration": dur,
            "idx": pg["idx"],
            "label": pg["label"],
            "screenshot": pg["screenshot"],
            "audioPath": str(CW_AUDIO_DIR / ("seg_%03d.mp3" % pg["idx"])) if pg["type"] not in skip_pages else "",
        })
        current += dur
    total_dur = current
    for item in timeline:
        print("  %6.1fs - %6.1fs [%s] %s" % (
            item["start"], item["start"] + item["duration"], item["type"], item["label"][:40]))
    print("\n  总时长: %.1fs" % total_dur)
    return timeline, total_dur


def build_index_html(timeline, total_dur):
    """按 HyperFrames 官方 slideshow 规范：每个 <img> 只带 data-start/data-duration，
    由框架自动挂载/卸载（禁写内联 opacity/display，框架会强制 opacity:1 覆盖）。
    时间线仅注册一个 sentinel，把 root 时长撑到整片时长。"""
    lines = []
    lines.append('<!DOCTYPE html>')
    lines.append('<html>')
    lines.append('<head><meta charset="UTF-8"><style>')
    lines.append('*{margin:0;padding:0;box-sizing:border-box}')
    lines.append('[data-composition-id="root"]{width:1920px;height:1080px;overflow:hidden;position:relative;background:%s}' % BRAND["bgColor"])
    lines.append('</style></head><body>')
    lines.append('<div id="root" data-composition-id="root" data-width="1920" data-height="1080" data-start="0" data-duration="%s">' % str(total_dur))
    for item in timeline:
        lines.append('  <img id="slide-%d" data-start="%s" data-duration="%s" data-track-index="1" src="%s" style="position:absolute;top:0;left:0;width:1920px;height:1080px;object-fit:cover;z-index:1">' % (
            item["idx"], str(item["start"]), str(item["duration"]), item["screenshot"]))
    lines.append('</div>')
    lines.append('<script src="https://cdn.jsdelivr.net/npm/gsap@3/dist/gsap.min.js"></script>')
    lines.append('<script>')
    lines.append('window.__timelines=window.__timelines||{};')
    lines.append('var _tl=gsap.timeline({paused:true});')
    lines.append('_tl.set({},{},%s);' % str(total_dur))
    lines.append('window.__timelines["root"]=_tl;')
    lines.append('</script>')
    lines.append('</body></html>')
    path = PROJECT_DIR / "index.html"
    path.write_text("\n".join(lines), encoding="utf-8")
    print("  -> index.html")


def build_narration(timeline, total_dur):
    """拼逐页 TTS → 整轨旁白（与 build_tech_share 同思路，跳过空音频页）"""
    blank_path = CW_AUDIO_DIR / "blank.wav"
    if not blank_path.exists():
        CW_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
             "-t", str(total_dur), str(blank_path)],
            capture_output=True, text=True)
    inputs = [str(blank_path)]
    filter_parts = []
    next_idx = 1
    delayed_labels = []
    for item in timeline:
        audio_path = item.get("audioPath", "")
        if not audio_path or not os.path.exists(audio_path) or os.path.getsize(audio_path) < 1024:
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
    filter_parts.append(
        "[0:a] " + " ".join(delayed_labels) +
        "amix=inputs=%d:duration=first:dropout_transition=0[out]" % next_idx)
    output_path = str(CW_AUDIO_DIR / "narration.wav")
    cmd = (["ffmpeg", "-y"] +
           sum([["-i", inp] for inp in inputs], []) +
           ["-filter_complex", ";".join(filter_parts),
            "-map", "[out]", "-c:a", "pcm_s16le",
            "-t", str(total_dur), output_path])
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("  [error] 音频合成失败: " + result.stderr[-300:])
        return ""
    mp3_path = str(CW_AUDIO_DIR / "narration.mp3")
    subprocess.run(
        ["ffmpeg", "-y", "-i", output_path, "-c:a", "libmp3lame", "-q:a", "2", mp3_path],
        capture_output=True)
    return mp3_path


# ════════════════════════════════════════════════════
# Main
# ════════════════════════════════════════════════════

async def main():
    import argparse
    parser = argparse.ArgumentParser(description="交互课件 → 16:9 技术讲解视频")
    parser.add_argument("--html", required=True, help="课件 HTML 文件（Step 3 静态产物）")
    parser.add_argument("--voice", default="zh-CN-YunxiNeural", help="TTS语音")
    parser.add_argument("--rate", default="+30%", help="TTS语速")
    parser.add_argument("--output", default="courseware-final.mp4", help="输出MP4路径")
    parser.add_argument("--title", help="视频标题（仅日志显示）")
    parser.add_argument("--skip-tts", action="store_true", help="跳过TTS")
    parser.add_argument("--skip-render", action="store_true", help="只生成截图+index.html")
    parser.add_argument("--skip-quiz", action="store_true", help="测验页不进视频")
    parser.add_argument("--skip-sim", action="store_true", help="仿真页不进视频")
    parser.add_argument("--bgm", help="背景音乐文件路径")
    args = parser.parse_args()

    html_path = Path(args.html)
    if not html_path.is_absolute():
        html_path = PROJECT_DIR / args.html
    if not html_path.exists():
        print("[error] 课件文件不存在: " + str(html_path))
        sys.exit(1)

    skip_pages = set()
    if args.skip_quiz:
        skip_pages.add("quiz")
    if args.skip_sim:
        skip_pages.add("sim")

    print("源课件: " + str(html_path))
    print("工作目录: " + str(PROJECT_DIR))

    print("\n── [1/5] 打开课件 · 逐页截图+文案提取 ──")
    pages = await capture_courseware(html_path)
    print("  共 %d 页进入时间线" % sum(1 for pg in pages if pg["type"] not in skip_pages))

    if not args.skip_tts:
        print("\n── [2/5] TTS配音 ──")
        durations = await generate_tts(pages, args.voice, args.rate, skip_pages)
    else:
        print("\n  跳过TTS")
        durations = [TIMING["minSlideDuration"]] * len(pages)

    print("\n── [3/5] 时间线计算 ──")
    timeline, total_dur = build_timeline(pages, durations, skip_pages)
    build_index_html(timeline, total_dur)

    print("\n── [4/5] 音频合成 ──")
    narration_path = build_narration(timeline, total_dur)

    if args.skip_render:
        print("\n  ⏭ 跳过渲染 (--skip-render)，可直接检查 index.html / captures/courseware/")
        return

    print("\n── [5/5] HyperFrames渲染 ──")
    output_path = str((PROJECT_DIR / args.output).resolve())
    cmd = 'npx hyperframes render -o "%s" --quality standard --fps 30 --workers 2 --page-side-compositing=no "%s"' % (
        output_path, str(PROJECT_DIR))
    print("  运行: " + cmd)
    result = subprocess.run(cmd, capture_output=False, text=True, shell=True)
    if result.returncode != 0:
        print("  [error] render失败 (exit=%d)" % result.returncode)
        return
    if not os.path.exists(output_path):
        print("  [error] 输出文件不存在: " + output_path)
        return

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print("  ✅ 无声视频: %s (%.1f MB)" % (output_path, size_mb))

    if narration_path and os.path.exists(narration_path):
        print("\n── 合并音轨 ──")
        audio_input = narration_path
        if args.bgm and os.path.exists(args.bgm):
            print("  BGM: " + args.bgm)
            bgm_mixed = str(CW_AUDIO_DIR / "narration_with_bgm.mp3")
            bgm_cmd = [
                "ffmpeg", "-y",
                "-i", narration_path,
                "-stream_loop", "-1", "-i", args.bgm,
                "-filter_complex",
                "[1:a]volume=0.15[bgm];[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=0[out]",
                "-map", "[out]", "-c:a", "libmp3lame", "-q:a", "2",
                "-t", str(total_dur), bgm_mixed,
            ]
            r = subprocess.run(bgm_cmd, capture_output=True, text=True)
            if r.returncode == 0:
                audio_input = bgm_mixed
        merged_path = output_path.replace(".mp4", "-with-audio.mp4")
        merge_cmd = [
            "ffmpeg", "-y",
            "-i", output_path,
            "-i", audio_input,
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-map", "0:v:0", "-map", "1:a:0",
            "-shortest", merged_path,
        ]
        r = subprocess.run(merge_cmd, capture_output=True, text=True)
        if r.returncode == 0 and os.path.exists(merged_path):
            merged_mb = os.path.getsize(merged_path) / (1024 * 1024)
            print("  ✅ 最终成片: %s (%.1f MB)" % (merged_path, merged_mb))
        else:
            print("  [error] 合并失败: " + r.stderr[-200:])


if __name__ == "__main__":
    asyncio.run(main())
