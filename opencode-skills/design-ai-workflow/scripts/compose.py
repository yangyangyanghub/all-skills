#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成后合成：mask 白色区域取 edit，黑色区域保留 base。

用法:
    python compose.py --base 原图.png --edit 重绘.png --mask mask.png --out 交付.png

约定:
    base 与 edit 必须同尺寸（不自动缩放，缩放会破坏结构保真）。
    mask 为白(255)=用 edit，黑(0)=用 base，灰度按灰度线性混合。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image, ImageFilter
except ImportError:
    sys.exit("需要 Pillow：python -m pip install pillow")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="按 mask 合成重绘图的局部区域")
    p.add_argument("--base", required=True, help="原始底图")
    p.add_argument("--edit", required=True, help="AI 重绘结果")
    p.add_argument("--mask", required=True, help="mask：白=用 edit，黑=保留 base")
    p.add_argument("--out", required=True, help="输出路径")
    p.add_argument("--feather", type=int, default=2, help="mask 边缘羽化像素，默认 2")
    p.add_argument("--dump-mask", action="store_true", help="另存处理后的 mask 供复查")
    return p.parse_args()


def load(path: str) -> Image.Image:
    if not Path(path).is_file():
        sys.exit(f"文件不存在：{path}")
    return Image.open(path)


def main() -> None:
    a = parse_args()

    base = load(a.base).convert("RGB")
    edit = load(a.edit).convert("RGB")
    mask = load(a.mask)

    if base.size != edit.size:
        sys.exit(
            f"尺寸不一致：base={base.size} edit={edit.size}。"
            "不自动缩放——请用与 base 同尺寸的底图重出图。"
        )

    if mask.size != base.size:
        mask = mask.resize(base.size, Image.LANCZOS)

    mask_l = mask.convert("L")
    if a.feather > 0:
        mask_l = mask_l.filter(ImageFilter.GaussianBlur(radius=a.feather))

    out = Image.composite(edit, base, mask_l)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    out.save(a.out)

    hist = mask_l.histogram()
    replaced = sum(hist[128:]) / (mask_l.width * mask_l.height)
    print(f"已合成: {a.out}")
    print(f"替换区域占比: {replaced:.1%}  羽化: {a.feather}px")

    if a.dump_mask:
        mp = Path(a.out).with_name(Path(a.out).stem + "-mask.png")
        mask_l.save(mp)
        print(f"mask 已另存: {mp}")

    if replaced <= 0.0:
        print("警告: 替换占比为 0，检查 mask 是否为全黑。", file=sys.stderr)
    if replaced >= 1.0:
        print("警告: 替换占比 100%，等于没做合成，检查 mask 是否为全白。", file=sys.stderr)


if __name__ == "__main__":
    main()
