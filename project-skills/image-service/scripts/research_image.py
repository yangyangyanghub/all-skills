#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调研配图生成器 - deep-research 技能的配图适配层

按图解类型套用手绘信息图模板，把结构化参数（类型/标题/内容）转换成
完整绘图 prompt，内部调用 image-service 的 text_to_image.py 完成实际生图。

用法：
  python research_image.py -t arch -n "标题" -c "画面内容描述" -o "输出.png"

图解类型（-t）：
  arch     架构图    科技蓝 #4A90D9   分层/模块化
  flow     流程图    蓝+绿+橙         从上到下
  compare  对比图    蓝 vs 橙         左右分栏
  concept  概念图    蓝紫渐变         中心发散
"""
import argparse
import subprocess
import sys
from pathlib import Path

# 同技能内的 text_to_image.py（实际执行生图）
TEXT_TO_IMAGE = Path(__file__).resolve().parent.parent / "core" / "text_to_image.py"

# 各类型通用的手绘风格收尾
_STYLE_TAIL = "整体风格简洁像工程师手绘笔记，白色背景，信息图排版清晰，文字使用简体中文"

# 四类模板：{title} 填标题，{content} 填内容描述
TEMPLATES = {
    "arch": (
        "手绘风格技术架构信息图，科技蓝（#4A90D9）主色调，分层模块化布局，"
        "标题为：{title}。画面内容：{content}。方框与箭头布局清晰，" + _STYLE_TAIL
    ),
    "flow": (
        "手绘风格流程信息图，蓝色和绿色为主色调，从上到下的步骤式布局，"
        "标题为：{title}。按顺序排布：{content}。步骤之间用手绘箭头串联，" + _STYLE_TAIL
    ),
    "compare": (
        "手绘风格对比信息图，对比双方分别用蓝色和橙色区分，左右分栏布局，"
        "标题为：{title}。对比要点：{content}。" + _STYLE_TAIL
    ),
    "concept": (
        "手绘风格概念信息图，蓝紫渐变配色，中心发散式布局，"
        "标题为：{title}。中心为核心主题，周围发散展示各要素：{content}。" + _STYLE_TAIL
    ),
}

# 各类型默认宽高比
RATIO_DEFAULT = {
    "arch": "3:2",
    "flow": "3:2",
    "compare": "3:2",
    "concept": "1:1",
}


def build_prompt(kind: str, title: str, content: str) -> str:
    """按类型套模板，拼出完整绘图 prompt"""
    return TEMPLATES[kind].format(title=title, content=content)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="调研配图生成器：按类型套用手绘信息图模板，调 text_to_image.py 生图"
    )
    parser.add_argument("-t", "--type", required=True, choices=sorted(TEMPLATES),
                        help="图解类型：arch/flow/compare/concept")
    parser.add_argument("-n", "--name", required=True, help="图的标题")
    parser.add_argument("-c", "--content", required=True, help="画面内容描述")
    parser.add_argument("-o", "--output", required=True, help="输出 png 路径")
    parser.add_argument("-r", "--ratio", default=None,
                        help="宽高比（默认按类型自动：arch/flow/compare 3:2，concept 1:1）")
    args = parser.parse_args()

    prompt = build_prompt(args.type, args.name, args.content)
    ratio = args.ratio or RATIO_DEFAULT[args.type]

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    if not TEXT_TO_IMAGE.exists():
        print(f"[research_image] 找不到执行脚本: {TEXT_TO_IMAGE}")
        return 1

    cmd = [sys.executable, str(TEXT_TO_IMAGE), prompt, "-o", str(output), "-r", ratio]

    print(f"[research_image] 类型={args.type} 输出={output}")
    print("[research_image] 调用 text_to_image.py 生图（约 1-2 分钟）...")
    result = subprocess.run(cmd)

    if result.returncode != 0:
        print(f"[research_image] 生图失败，退出码 {result.returncode}")
        return result.returncode
    if not output.exists():
        print("[research_image] 生图进程正常退出，但输出文件不存在")
        return 1

    size_kb = output.stat().st_size // 1024
    print(f"[research_image] 完成: {output} ({size_kb}KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
