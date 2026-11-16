#!/usr/bin/env python3
"""
从 HTML 页面中提取内嵌的 transcript 字段，并还原成纯文本。

适用场景：页面由服务端渲染或注入了完整 props，逐字稿藏在 HTML 里的 JSON 字符串中
（典型如 YC Library 的演讲页）。直接对这类页面做正文抽取往往只能拿到标题和摘要。

用法：
    python extract_embedded.py page.html -o transcript.txt
    python extract_embedded.py page.html --field transcript --field transcript_text
"""

import argparse
import html
import json
import re
import sys
from pathlib import Path

DEFAULT_FIELDS = [
    "transcript",
    "transcription",
    "transcript_text",
    "full_transcript",
    "caption_text",
    "full_text",
]


def read_page(path: Path) -> str:
    """读页面并把 HTML 实体还原，这样后续可以按普通 JSON 处理。"""
    return html.unescape(path.read_text(encoding="utf-8", errors="replace"))


def decode_json_string(raw: str) -> str:
    """字段值本身是 JSON 字符串字面量，优先用 json 解转义，失败再手工替换。"""
    try:
        return json.loads('"%s"' % raw)
    except json.JSONDecodeError:
        return (
            raw.replace("\\n", "\n")
            .replace("\\t", "\t")
            .replace('\\"', '"')
            .replace("\\\\", "\\")
        )


def find_longest(text: str, fields: list[str]) -> tuple[str, str]:
    """多个字段、多个出现位置里取最长的那段，通常就是正文而不是摘要或空值。"""
    best_value, best_field = "", ""
    for field in fields:
        pattern = re.compile(r'"%s"\s*:\s*"((?:[^"\\]|\\.)*)"' % re.escape(field))
        for match in pattern.finditer(text):
            value = decode_json_string(match.group(1))
            if len(value) > len(best_value):
                best_value, best_field = value, field
    return best_value, best_field


def main() -> int:
    parser = argparse.ArgumentParser(
        description="提取 HTML 内嵌 transcript 字段并转为纯文本"
    )
    parser.add_argument("input", help="HTML 文件路径")
    parser.add_argument("-o", "--output", help="输出文件；省略则打印到标准输出")
    parser.add_argument(
        "--field",
        action="append",
        dest="fields",
        help="自定义字段名，可重复；默认尝试常见 transcript 字段",
    )
    parser.add_argument(
        "--min-length",
        type=int,
        default=200,
        help="低于该长度时提示可能不是正文（默认 200）",
    )
    args = parser.parse_args()

    path = Path(args.input)
    if not path.exists():
        print(f"文件不存在：{path}", file=sys.stderr)
        return 2

    page = read_page(path)
    fields = args.fields or DEFAULT_FIELDS
    value, field = find_longest(page, fields)

    if not value:
        print(
            "未找到内嵌 transcript 字段。该页可能把正文放在异步接口里，"
            "建议改用 yt-dlp 字幕或浏览器转写面板路径。",
            file=sys.stderr,
        )
        return 1

    if len(value) < args.min_length:
        print(
            f"命中了字段 {field}，但只有 {len(value)} 字符，可能不是完整正文。",
            file=sys.stderr,
        )

    if args.output:
        Path(args.output).write_text(value, encoding="utf-8")
        print(
            f"已写入 {args.output}\n字段：{field}\n字符数：{len(value)}",
            file=sys.stderr,
        )
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(value)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
