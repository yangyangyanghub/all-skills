#!/usr/bin/env python3
"""
把字幕文件或浏览器快照转成"带时间戳的纯文本"。

支持输入：
    .vtt / .srt      YouTube 自动字幕、人工字幕
    .json3           YouTube json3 字幕
    快照文本          chrome-devtools take_snapshot 存下来的页面快照（--from-snapshot）

用法：
    python subtitle_to_text.py out/video.en.vtt -o transcript.txt
    python subtitle_to_text.py snap.txt --from-snapshot -o transcript.txt
    python subtitle_to_text.py snap.txt --from-snapshot --no-timestamps
"""

import argparse
import json
import re
import sys
from pathlib import Path

# 快照里的两种时间写法：中文界面 "1分钟29秒钟"，英文界面 "1:29" / "1:02:03"
SNAPSHOT_CUE = re.compile(
    r'button "((?:\d+分钟)?\d+秒钟|\d{1,2}:\d{2}(?::\d{2})?)\s+([^"]+)"'
)
CN_TIME = re.compile(r"^(?:(\d+)分钟)?(?:(\d+)秒钟)?$")
CUE_TIMING = re.compile(
    r"(\d{1,2}:\d{2}:\d{2})[.,](\d{1,3})\s*-->\s*(\d{1,2}:\d{2}:\d{2})"
)


def cn_to_seconds(text: str):
    """'1分钟29秒钟' / '43秒钟' -> 秒数。"""
    match = CN_TIME.match(text.strip())
    if not match:
        return None
    return int(match.group(1) or 0) * 60 + int(match.group(2) or 0)


def clock_to_seconds(text: str):
    """'1:29' / '1:02:03' -> 秒数。"""
    parts = [int(p) for p in text.split(":")]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return None


def fmt_seconds(total: int) -> str:
    hours, rem = divmod(max(total, 0), 3600)
    minutes, seconds = divmod(rem, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def parse_snapshot(text: str):
    """从 a11y 快照里抽 'button "<时间> <正文>"'，章节标题因不以时间开头会被自动排除。"""
    cues = []
    for line in text.splitlines():
        match = SNAPSHOT_CUE.search(line)
        if not match:
            continue
        raw_time, body = match.group(1), match.group(2).strip()
        seconds = (
            cn_to_seconds(raw_time) if "秒" in raw_time else clock_to_seconds(raw_time)
        )
        if seconds is None:
            continue
        cues.append((seconds, body))
    return cues


def parse_json3(text: str):
    """YouTube json3：按 tStartMs 把 segs 拼回一句。"""
    data = json.loads(text)
    cues = []
    for event in data.get("events", []):
        segs = event.get("segs") or []
        body = "".join(seg.get("utf8", "") for seg in segs).strip()
        if not body or body == "\n":
            continue
        start_ms = event.get("tStartMs", 0)
        cues.append((start_ms // 1000, body.replace("\n", " ")))
    return cues


def parse_cue_file(text: str):
    """VTT / SRT：取每条 cue 的时间与正文，跳过序号行、样式行。"""
    cues = []
    lines = text.splitlines()
    current_start = None
    buffer = []

    def flush():
        if current_start is not None and buffer:
            body = " ".join(x.strip() for x in buffer if x.strip())
            body = re.sub(r"<[^>]+>", "", body).strip()
            if body:
                cues.append((current_start, body))

    for line in lines:
        timing = CUE_TIMING.search(line)
        if timing:
            flush()
            buffer = []
            current_start = clock_to_seconds(timing.group(1))
        elif line.strip().upper().startswith(("WEBVTT", "NOTE", "STYLE", "REGION")):
            continue
        elif line.strip().isdigit():
            continue
        else:
            buffer.append(line)
    flush()
    return cues


def dedupe(cues):
    """自动字幕常有滚动重复，相邻同文只保留第一条。"""
    result = []
    last = None
    for seconds, body in cues:
        if body == last:
            continue
        result.append((seconds, body))
        last = body
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="字幕/快照 -> 带时间戳纯文本")
    parser.add_argument("input", help="字幕文件或快照文本")
    parser.add_argument("-o", "--output", help="输出文件；省略则打印到标准输出")
    parser.add_argument(
        "--from-snapshot",
        action="store_true",
        help="输入是 chrome-devtools take_snapshot 保存的页面快照",
    )
    parser.add_argument(
        "--no-timestamps", action="store_true", help="只输出正文，不带 [mm:ss]"
    )
    parser.add_argument(
        "--no-dedupe", action="store_true", help="关闭相邻重复行去重"
    )
    args = parser.parse_args()

    path = Path(args.input)
    if not path.exists():
        print(f"文件不存在：{path}", file=sys.stderr)
        return 2
    text = path.read_text(encoding="utf-8", errors="replace")

    if args.from_snapshot:
        cues = parse_snapshot(text)
    elif path.suffix.lower() == ".json3":
        cues = parse_json3(text)
    else:
        cues = parse_cue_file(text)

    if not cues:
        print("没有解析出任何字幕段，请检查输入格式。", file=sys.stderr)
        return 1

    if not args.no_dedupe:
        cues = dedupe(cues)

    if args.no_timestamps:
        output = "\n".join(body for _, body in cues)
    else:
        output = "\n".join(f"[{fmt_seconds(s)}] {body}" for s, body in cues)

    span = fmt_seconds(cues[-1][0])
    summary = (
        f"段落数：{len(cues)}\n"
        f"字符数：{len(output)}\n"
        f"时间范围：{fmt_seconds(cues[0][0])} ~ {span}"
    )

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"已写入 {args.output}\n{summary}", file=sys.stderr)
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(output)
        print("\n" + summary, file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
