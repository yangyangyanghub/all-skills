"""
HyperFrames 视频构建器 v1
从步骤配置 + 截图 + TTS 生成完整 HyperFrames 项目并渲染

流程:
  1. 读取 edu-steps-hf.json（含章节分组、品牌配置、TTS 文本）
  2. 对每个 step URL，用 Playwright 截图（复用已有登录态）
  3. 用 edge-tts 生成每步配音，测量时长
  4. 按实际 TTS 时长计算精确时间线
  5. 生成 index.html + subtitles composition
  6. hyperframes render → final.mp4
"""
import asyncio
import json
import os
import subprocess
import sys
import time
from pathlib import Path

VIEWPORT = {"width": 1920, "height": 1080}

# ── 配置 ──────────────────────────────────────────

PROJECT_DIR = Path(__file__).parent.resolve()
COMPOSITIONS_DIR = PROJECT_DIR / "compositions"
CAPTURES_DIR = PROJECT_DIR / "captures"
AUDIO_DIR = PROJECT_DIR / "audio"
ASSETS_DIR = PROJECT_DIR / "assets"

DEFAULT_BRAND = {
  "title": "系统演示",
  "subtitle": "",
  "accentColor": "#3b82f6",
  "bgColor": "#0f172a",
  "logoPath": "",
}

DEFAULT_TIMING = {
  "introDuration": 4,
  "chapterDuration": 2,
  "outroDuration": 5,
  "minStepDuration": 5,   # 每步最少时长
  "stepPadding": 1,        # 步间间隔
}


# ════════════════════════════════════════════════════
# 1. 截图模块（Playwright）
# ════════════════════════════════════════════════════

async def capture_screenshots(steps, base_url, storage_state=None):
  """对每个 step 的 URL 截全页图，存到 CAPTURES_DIR"""
  from playwright.async_api import async_playwright

  CAPTURES_DIR.mkdir(parents=True, exist_ok=True)

  async with async_playwright() as p:
    browser = await p.chromium.launch(headless=True)

    context_kwargs = {"viewport": VIEWPORT}
    if storage_state and os.path.exists(storage_state):
      context_kwargs["storage_state"] = storage_state

    context = await browser.new_context(**context_kwargs)
    page = await context.new_page()

    for i, step in enumerate(steps):
      url = step["url"]
      if not url.startswith("http"):
        url = base_url.rstrip("/") + "/" + url.lstrip("/")

      step_id = f"seg_{i:03d}"
      step["id"] = step_id
      step_dir = CAPTURES_DIR / step_id
      step_dir.mkdir(parents=True, exist_ok=True)

      screenshot_path = step_dir / "screenshot.png"
      if screenshot_path.exists():
        print(f"  [{i+1}/{len(steps)}] skip (已存在): {os.path.basename(screenshot_path)}")
        step["screenshot"] = str(screenshot_path.relative_to(PROJECT_DIR))
        continue

      print(f"  [{i+1}/{len(steps)}] 截图: {url}")

      try:
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        # 等待渲染
        await page.wait_for_timeout(2000)
        # 尝试 networkidle
        try:
          await page.wait_for_load_state("networkidle", timeout=10000)
        except:
          pass
        await page.wait_for_timeout(1000)

        await page.screenshot(path=str(screenshot_path), full_page=False)
        step["screenshot"] = str(screenshot_path.relative_to(PROJECT_DIR))
      except Exception as e:
        print(f"    [error] {e}")
        step["screenshot"] = ""

    await context.close()
    await browser.close()

  return steps


# ════════════════════════════════════════════════════
# 2. TTS 配音模块
# ════════════════════════════════════════════════════

async def generate_tts_segments(steps, voice="zh-CN-YunxiNeural", rate="+0%"):
  """为每步生成 TTS 音频，返回带时长的 steps"""
  import edge_tts

  AUDIO_DIR.mkdir(parents=True, exist_ok=True)

  for i, step in enumerate(steps):
    text = step.get("ttsText", step.get("description", ""))
    seg_path = AUDIO_DIR / f"seg_{i:03d}.mp3"

    if not text:
      step["audioDuration"] = 3.0
      step["audioPath"] = ""
      continue

    if seg_path.exists():
      dur = get_audio_duration(str(seg_path))
      step["audioDuration"] = dur
      step["audioPath"] = str(seg_path.relative_to(PROJECT_DIR))
      print(f"  [{i+1}/{len(steps)}] skip TTS (已存在): {dur:.1f}s")
      continue

    print(f"  [{i+1}/{len(steps)}] TTS: {text[:50]}...")
    for attempt in range(3):
      try:
        c = edge_tts.Communicate(text, voice, rate=rate)
        await c.save(str(seg_path))
        dur = get_audio_duration(str(seg_path))
        step["audioDuration"] = dur
        step["audioPath"] = str(seg_path.relative_to(PROJECT_DIR))
        print(f"    OK: {dur:.1f}s")
        break
      except Exception as e:
        if attempt < 2:
          await asyncio.sleep(2)
        else:
          print(f"    [error] TTS 失败: {e}")
          step["audioDuration"] = 5.0
          step["audioPath"] = ""

  return steps


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


# ════════════════════════════════════════════════════
# 3. 时间线计算
# ════════════════════════════════════════════════════

def calculate_timeline(steps, brand, timing):
  """
  计算精确时间线。
  结构:
    [intro] → [ch1][seg1][seg2] → [ch2][seg3] → ...[outro]

  返回:
    timeline: [
      {"type":"intro", "start":0, "duration":4, ...},
      {"type":"chapter", "start":4, "duration":2, "number":"01", "title":"平台概览"},
      {"type":"step", "start":6, "duration":7.5, "step":{...}},
      ...
    ]
    totalDuration: float
  """
  timeline = []
  current = 0.0
  t = timing

  # Intro
  intro_dur = t["introDuration"]
  timeline.append({"type": "intro", "start": current, "duration": intro_dur, **brand})
  current += intro_dur

  # 按章节分组
  chapters = group_by_chapter(steps)

  for ch_idx, chapter in enumerate(chapters):
    ch_steps = chapter["steps"]
    ch_num = chapter.get("id", f"{ch_idx+1:02d}")
    ch_title = chapter.get("title", "")

    # Chapter 页
    ch_dur = t["chapterDuration"]
    timeline.append({
      "type": "chapter",
      "start": current,
      "duration": ch_dur,
      "number": ch_num,
      "title": ch_title,
      "accentColor": brand.get("accentColor", "#3b82f6"),
    })
    current += ch_dur

    # 步骤
    for step in ch_steps:
      audio_dur = step.get("audioDuration", t["minStepDuration"])
      step_dur = max(audio_dur + t["stepPadding"], t["minStepDuration"])

      timeline.append({
        "type": "step",
        "start": current,
        "duration": step_dur,
        "step": step,
      })
      current += step_dur

  # Outro
  outro_dur = t["outroDuration"] + 3  # 额外3秒黑帧缓冲，避免clip机制末尾边界问题
  timeline.append({
    "type": "outro",
    "start": current,
    "duration": outro_dur,
    "message": "感谢观看",
    "contact": "",
    "accentColor": brand.get("accentColor", "#3b82f6"),
  })
  current += outro_dur

  return timeline, current


def group_by_chapter(steps):
  """按 chapterId 字段分组。若无则所有步骤归为一个章节"""
  chapters = []
  current_chapter = None

  for step in steps:
    ch_id = step.get("chapterId", "")
    ch_title = step.get("chapterTitle", "")

    if not current_chapter or (ch_id and ch_id != current_chapter.get("id")):
      if current_chapter:
        chapters.append(current_chapter)
      current_chapter = {"id": ch_id or "01", "title": ch_title or "系统演示", "steps": []}

    current_chapter["steps"].append(step)

  if current_chapter:
    chapters.append(current_chapter)

  return chapters


# ════════════════════════════════════════════════════
# 4. 生成 HyperFrames HTML
# ════════════════════════════════════════════════════

def build_subtitles_html(timeline):
  """生成字幕叠加层 HTML（HyperFrames 规范）"""
  lines = []
  lines.append('<!DOCTYPE html>')
  lines.append('<html style="background:transparent">')
  lines.append('<head><meta charset="UTF-8"><style>')
  lines.append('*{margin:0;padding:0;box-sizing:border-box}')
  lines.append('[data-composition-id="subtitles"]{width:1920px;height:1080px;overflow:hidden;position:relative;pointer-events:none;font-family:Arial,Inter,sans-serif}')
  lines.append('[data-composition-id="subtitles"] .sub{position:absolute;bottom:120px;left:0;right:0;text-align:center;padding:0 200px;opacity:0}')
  lines.append('[data-composition-id="subtitles"] .sub-text{display:inline-block;background:rgba(0,0,0,.75);color:#fff;font-size:30px;font-weight:500;padding:14px 32px;border-radius:8px;letter-spacing:.04em;line-height:1.5;max-width:1400px;text-shadow:0 2px 4px rgba(0,0,0,.5)}')
  lines.append('</style></head>')
  lines.append('<body style="background:transparent">')

  for i, item in enumerate(timeline):
    if item["type"] == "step":
      step = item["step"]
      text = step.get("ttsText", step.get("description", ""))
      if text:
        escaped = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
        lines.append(f'<div id="sub-{i}" class="sub clip" data-start="{item["start"]}" data-duration="{item["duration"]}">')
        lines.append(f'  <span class="sub-text">{escaped}</span>')
        lines.append(f'</div>')

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

  path = COMPOSITIONS_DIR / "subtitles.html"
  path.write_text("\n".join(lines), encoding="utf-8")
  print(f"  → {path}")


def build_index_html(timeline, brand, timing):
  """生成主 index.html（HyperFrames 规范）"""
  total_dur = timeline[-1]["start"] + timeline[-1]["duration"] if timeline else 0

  # 字幕数据给 composition 使用
  subtitle_data = []
  for item in timeline:
    if item["type"] == "step":
      text = item["step"].get("ttsText", item["step"].get("description", ""))
      subtitle_data.append({"start": item["start"], "duration": item["duration"], "text": text})

  vars_json = json.dumps([
    {"id": "title", "type": "string", "label": "标题", "default": brand.get("title", "")},
    {"id": "subtitle", "type": "string", "label": "副标题", "default": brand.get("subtitle", "")},
    {"id": "bgColor", "type": "color", "label": "背景色", "default": brand.get("bgColor", "#0f172a")},
    {"id": "accentColor", "type": "color", "label": "强调色", "default": brand.get("accentColor", "#3b82f6")},
    {"id": "logoPath", "type": "string", "label": "Logo", "default": brand.get("logoPath", "")},
  ])

  def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

  lines = []
  lines.append('<!DOCTYPE html>')
  lines.append(f'<html data-composition-variables=\'{vars_json}\'>')
  lines.append('<head><meta charset="UTF-8"><style>')
  lines.append('*{margin:0;padding:0;box-sizing:border-box}')
  lines.append('[data-composition-id="root"]{width:1920px;height:1080px;overflow:hidden;position:relative;background:#0f172a;font-family:Arial,Inter,sans-serif}')
  lines.append('[data-composition-id="root"] .bg{position:absolute;inset:0;background:#0f172a;z-index:0}')
  lines.append('</style></head>')
  lines.append('<body>')
  lines.append(f'<div id="root" data-composition-id="root" data-width="1920" data-height="1080" data-start="0" data-duration="{total_dur}">')
  lines.append('  <div class="bg"></div>')

  for i, item in enumerate(timeline):
    t = item["type"]
    sid = item.get("start", 0)
    sdir = item.get("duration", 1)

    if t == "intro":
      # 使用子 composition（必须，否则 HyperFrames clip 全局失效）
      cid = "intro"
      lines.append(f'  <div id="intro-{i}" data-composition-id="{cid}" data-composition-src="compositions/intro.html" data-start="{sid}" data-duration="{sdir}"'
                   f' data-variable-values=\'{{"title":"{esc(item.get("title",""))}","subtitle":"{esc(item.get("subtitle",""))}","bgColor":"{item.get("bgColor","#0f172a")}","accentColor":"{item.get("accentColor","#3b82f6")}","logoPath":"{item.get("logoPath","")}","duration":{sdir}}}\'></div>')

    elif t == "chapter":
      # 内联章节页（通过 HF_SHOTS onUpdate 控制显隐）
      num = item.get("number", "")
      chap_title = esc(item.get("title", ""))
      accent = item.get("accentColor", "#3b82f6")
      lines.append(f'  <div id="chapter-{i}" class="clip chapter-page" data-start="{sid}" data-duration="{sdir}"'
                   f' style="position:absolute;top:0;left:0;width:1920px;height:1080px;overflow:hidden;background:#0f172a;z-index:2;opacity:0">')
      lines.append(f'    <div style="position:absolute;inset:0;background:radial-gradient(ellipse at 50% 40%,{accent}22 0%,transparent 65%)"></div>')
      # 四个角标 - 不设 opacity:0，由父 div 统一控制
      for corner_pos, tx, ty in [("tl",80,80),("tr","auto",80),("bl",80,"auto"),("br","auto","auto")]:
        l = f'{tx}px' if tx != "auto" else "auto"
        r = '80px' if corner_pos in ("tr","br") else "auto"
        t = f'{ty}px' if ty != "auto" else "auto"
        b = '80px' if corner_pos in ("bl","br") else "auto"
        lines.append(f'    <div style="position:absolute;top:{t};bottom:{b};left:{l};right:{r};width:40px;height:40px;'
                     f'border-{"top" if corner_pos in ("tl","tr") else "bottom"}:2px solid {accent};'
                     f'border-{"left" if corner_pos in ("tl","bl") else "right"}:2px solid {accent}"></div>')
      # 内容中心 - 不设 opacity:0，由父 div inline style 统一控制
      lines.append(f'    <div style="position:absolute;inset:0;display:flex;flex-direction:column;justify-content:center;align-items:center">')
      lines.append(f'      <div style="font-size:140px;font-weight:800;line-height:1;color:{accent}">{num}</div>')
      lines.append(f'      <div style="font-size:48px;font-weight:600;color:#fff;letter-spacing:0.1em;margin-top:24px">{chap_title}</div>')
      lines.append(f'      <div style="height:2px;width:200px;margin-top:32px;background:linear-gradient(90deg,transparent,{accent},transparent)"></div>')
      lines.append(f'    </div>')
      lines.append(f'  </div>')

    elif t == "step":
      step = item["step"]
      screenshot = step.get("screenshot", "")
      if screenshot:
        lines.append(f'  <img id="step-{i}" class="clip screenshot" src="{screenshot}" data-start="{sid}" data-duration="{sdir}"'
                     f' style="position:absolute;top:0;left:0;width:1920px;height:1080px;object-fit:contain;background:#0f172a;z-index:1;opacity:0">')

    elif t == "outro":
      # 片尾：使用 class="clip" 让 HyperFrames clip 系统管理显隐
      msg = esc(item.get("message", "感谢观看"))
      accent = item.get("accentColor", "#3b82f6")
      lines.append(f'  <div id="outro-{i}" class="clip" data-start="{sid}" data-duration="{sdir}"'
                   f' style="position:absolute;top:0;left:0;width:1920px;height:1080px;overflow:hidden;background:#0f172a;z-index:100;opacity:0;display:block">')
      lines.append(f'    <div style="position:absolute;inset:0;background:radial-gradient(ellipse at 50% 40%,{accent}22 0%,transparent 65%)"></div>')
      lines.append(f'    <div style="position:absolute;inset:0;display:flex;flex-direction:column;justify-content:center;align-items:center">')
      lines.append(f'      <div style="width:72px;height:72px;border:3px solid {accent};border-radius:50%;display:flex;align-items:center;justify-content:center"><svg viewBox="0 0 24 24" fill="none" stroke="{accent}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" width="36" height="36"><polyline points="20 6 9 17 4 12"/></svg></div>')
      lines.append(f'      <div style="font-size:56px;font-weight:700;color:#fff;letter-spacing:.05em;margin-top:40px">{msg}</div>')
      lines.append(f'      <div style="font-size:24px;font-weight:400;color:#64748b;margin-top:16px">教育资源动态监测平台</div>')
      lines.append(f'      <div style="height:3px;width:80px;background:{accent};border-radius:2px;margin-top:30px"></div>')
      lines.append(f'      <div style="position:absolute;bottom:30px;font-size:12px;color:#1e293b">Made with HyperFrames</div>')
      lines.append(f'    </div>')
      lines.append(f'  </div>')

  # 字幕叠加层 - 使用 subtitles 的 timeline ID 注册
  lines.append('  <!-- 字幕叠加层 -->')
  lines.append('  <div data-composition-id="subtitles" data-composition-src="compositions/subtitles.html"'
               ' data-start="0" data-duration="' + str(total_dur) + '"'
               ' data-variable-values=\'{"segments":' + json.dumps(subtitle_data, ensure_ascii=False) + '}\'></div>')

  lines.append('</div>')  # root
  # 截图时间线数据（JSON）
  shot_data = []
  for i, item in enumerate(timeline):
    if item["type"] in ("step", "chapter", "outro"):
      sid = item["start"]
      sdir = item["duration"]
      shot_data.append({"id": f"{item['type']}-{i}", "start": sid, "duration": sdir})

  # Root timeline 注册 - HyperFrames 需要
  lines.append('<script src="https://cdn.jsdelivr.net/npm/gsap@3/dist/gsap.min.js"></script>')
  lines.append('<script>')
  lines.append('window.__timelines=window.__timelines||{};')
  lines.append('window.__timelines["root"]=gsap.timeline({paused:true});')
  lines.append('var HF_SHOTS=' + json.dumps(shot_data) + ';')
  lines.append('var HF_ROOT=window.__timelines["root"];')
  lines.append('HF_ROOT.eventCallback("onUpdate",function(){')
  lines.append('  var t=HF_ROOT.time();')
  lines.append('  for(var i=0;i<HF_SHOTS.length;i++){')
  lines.append('    var s=HF_SHOTS[i];')
  lines.append('    var el=document.getElementById(s.id);')
  lines.append('    if(!el)continue;')
  lines.append('    var st=s.start, ed=s.start+s.duration;')
  lines.append('    if(t>=st&&t<=ed){el.style.opacity="1";el.style.display="block"}')
  lines.append('    else{el.style.opacity="0";el.style.display="none"}')
  lines.append('  }')
  lines.append('});')
  # onUpdate 已处理所有 clip 的显隐控制（包括片尾）
  lines.append('</script>')
  lines.append('</body></html>')

  path = PROJECT_DIR / "index.html"
  path.write_text("\n".join(lines), encoding="utf-8")
  print(f"  → {path}")


# ════════════════════════════════════════════════════
# 5. 拼接配音
# ════════════════════════════════════════════════════

def build_narration(timeline, total_dur):
  """将所有 TTS 片段按时间线中的精确 start 时间叠加到完整音轨"""
  # 生成一个空白底音轨（等同于视频总时长）
  blank_path = AUDIO_DIR / "blank.wav"
  if not blank_path.exists():
    subprocess.run(
      ["ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo",
       "-t", str(total_dur), "-c:a", "pcm_s16le", str(blank_path)],
      capture_output=True, text=True
    )

  # 收集所有步骤的 TTS 片段及其延迟毫秒数
  inputs = [str(blank_path)]
  filter_parts = []
  next_idx = 1
  delayed_labels = []

  for item in timeline:
    if item["type"] == "step":
      step = item["step"]
      audio_path = step.get("audioPath", "")
      if not audio_path:
        continue
      abs_path = (PROJECT_DIR / audio_path).resolve()
      if not abs_path.exists():
        continue
      delay_ms = int(item["start"] * 1000)
      inputs.append(str(abs_path))
      label = f"s{next_idx}"
      filter_parts.append(f"[{next_idx}:a]adelay={delay_ms}|{delay_ms}[{label}]")
      delayed_labels.append(f"[{label}]")
      next_idx += 1

  if next_idx == 1:
    print("  [warn] 无 TTS 音频")
    return ""

  # amix: 空白底音轨 + 所有延迟配音混合
  mix_inputs = "[0:a] " + " ".join(delayed_labels)
  filter_parts.append(f"{mix_inputs}amix=inputs={next_idx}:duration=first:dropout_transition=0[out]")

  filter_str = ";".join(filter_parts)

  output_path = str(AUDIO_DIR / "narration.wav")

  cmd = ["ffmpeg", "-y"] + sum([["-i", inp] for inp in inputs], []) + [
    "-filter_complex", filter_str,
    "-map", "[out]",
    "-c:a", "pcm_s16le",
    "-t", str(total_dur),
    output_path,
  ]

  result = subprocess.run(cmd, capture_output=True, text=True)
  if result.returncode != 0:
    print(f"  [error] 音频合成失败: {result.stderr[-300:]}")
    return ""

  # 转为 MP3
  mp3_path = str(AUDIO_DIR / "narration.mp3")
  subprocess.run(
    ["ffmpeg", "-y", "-i", output_path,
     "-c:a", "libmp3lame", "-q:a", "2", mp3_path],
    capture_output=True
  )

  return mp3_path


# ════════════════════════════════════════════════════
# 主流程
# ════════════════════════════════════════════════════

async def main():
  import argparse
  parser = argparse.ArgumentParser(description="HyperFrames 视频构建器")
  parser.add_argument("--config", required=True, help="步骤配置文件 JSON")
  parser.add_argument("--base-url", default="http://localhost:5173", help="系统基础 URL")
  parser.add_argument("--storage-state", help="Playwright storage state JSON (免登录)")
  parser.add_argument("--voice", default="zh-CN-YunxiNeural", help="TTS 语音")
  parser.add_argument("--rate", default="+0%", help="TTS 语速")
  parser.add_argument("--output", default="final.mp4", help="输出 MP4 路径")
  parser.add_argument("--skip-capture", action="store_true", help="跳过截图（用已有）")
  parser.add_argument("--skip-tts", action="store_true", help="跳过 TTS（用已有）")
  parser.add_argument("--skip-render", action="store_true", help="只生成 HTML，不渲染")
  args = parser.parse_args()

  with open(args.config, "r", encoding="utf-8") as f:
    config = json.load(f)

  steps = config["steps"]
  brand = {**DEFAULT_BRAND, **config.get("brand", {})}
  timing = {**DEFAULT_TIMING, **config.get("timing", {})}

  print(f"配置: {len(steps)} 步, 品牌={brand['title']}")

  # Step 1: 截图
  if not args.skip_capture:
    print("\n── [1/5] 截图 ──")
    steps = await capture_screenshots(steps, args.base_url, args.storage_state)

  # Step 2: TTS
  if not args.skip_tts:
    print("\n── [2/5] TTS 配音 ──")
    steps = await generate_tts_segments(steps, args.voice, args.rate)

  # Step 3: 时间线
  print("\n── [3/5] 时间线计算 ──")
  timeline, total_dur = calculate_timeline(steps, brand, timing)

  for item in timeline:
    dur = item["duration"]
    if item["type"] == "step":
      desc = item["step"].get("description", "")[:40]
      print(f"  {item['start']:6.1f}s - {item['start']+dur:6.1f}s [{item['type']}] {desc}")
    else:
      label = item.get("title", item.get("message", item["type"]))
      print(f"  {item['start']:6.1f}s - {item['start']+dur:6.1f}s [{item['type']}] {label}")

  print(f"\n  总时长: {total_dur:.1f}s")

  # Step 4: 生成 HTML
  print("\n── [4/5] 生成 HyperFrames 项目 ──")
  build_subtitles_html(timeline)
  build_index_html(timeline, brand, timing)
  narration_path = build_narration(timeline, total_dur)

  # Step 5: 渲染
  if not args.skip_render:
    print("\n── [5/5] HyperFrames 渲染 ──")
    # 先 copy 截图到 captures 目录下的路径
    # render 命令
    output_path = str((PROJECT_DIR / args.output).resolve())
    cmd = "npx hyperframes render -o " + output_path + " --quality standard --fps 30 --workers 2 --page-side-compositing=no " + str(PROJECT_DIR)
    print(f"  运行: {cmd}")
    result = subprocess.run(cmd, capture_output=False, text=True, shell=True)
    if result.returncode != 0:
      print(f"  [error] render 失败 (exit={result.returncode})")
      return

    if os.path.exists(output_path):
      size_mb = os.path.getsize(output_path) / (1024 * 1024)
      print(f"  ✅ 完成: {output_path} ({size_mb:.1f} MB)")

      # 6. 合并音轨
      if narration_path and os.path.exists(narration_path):
        merged_path = output_path.replace(".mp4", "-with-audio.mp4")
        print(f"\n── [6/6] 合并音轨 ──")
        merge_cmd = [
          "ffmpeg", "-y",
          "-i", output_path,
          "-i", narration_path,
          "-c:v", "copy",
          "-c:a", "aac", "-b:a", "192k",
          "-map", "0:v:0",
          "-map", "1:a:0",
          "-shortest",
          merged_path,
        ]
        result = subprocess.run(merge_cmd, capture_output=True, text=True)
        if result.returncode != 0:
          print(f"  [error] 音轨合并失败: {result.stderr[-300:]}")
        elif os.path.exists(merged_path):
          merged_mb = os.path.getsize(merged_path) / (1024 * 1024)
          print(f"  ✅ 音轨合并: {merged_path} ({merged_mb:.1f} MB)")
          # 验证
          verify = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "stream=codec_type,codec_name",
             "-of", "csv=p=0", merged_path],
            capture_output=True, text=True
          )
          streams = [s.strip() for s in verify.stdout.strip().split("\n") if s.strip()]
          print(f"  流: {streams}")
        else:
          print(f"  [error] 合并输出不存在")
      else:
        print(f"\n  [warn] 无配音文件，跳过音轨合并")
    else:
      print(f"  [error] 输出文件不存在: {output_path}")
  else:
    print("\n  ⏭ 跳过渲染（--skip-render）")
    print(f"  手动运行:")
    print(f"    npx hyperframes preview")
    print(f"    npx hyperframes render -o {args.output}")


if __name__ == "__main__":
  asyncio.run(main())
