#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把纯色涂鸦图转成二值 mask（涂鸦色 = 白/要替换，其余 = 黑/保留）。

用法:
    python mask_from_zoning.py --zoning 涂鸦.png --out mask.png
    python mask_from_zoning.py --zoning 涂鸦.png --out mask.png --color red --grow 3

默认认品红 #FF00FF，因为建筑/景观照片里几乎不会出现高饱和品红；
用纯红容易误伤红砖墙、红铺装、晚霞。要改区域也可以显式 --color red。
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
    p = argparse.ArgumentParser(description="涂鸦图转 mask")
    p.add_argument("--zoning", required=True, help="涂鸦图（要改的区域涂单色）")
    p.add_argument("--out", required=True, help="输出 mask 路径")
    p.add_argument("--color", choices=["magenta", "red", "green", "blue"], default="magenta",
                   help="涂鸦颜色，默认 magenta(#FF00FF)")
    p.add_argument("--grow", type=int, default=0, help="mask 膨胀像素，给模型留过渡空间")
    p.add_argument("--threshold", type=int, default=150, help="主通道门限，默认 150")
    p.add_argument("--separation", type=int, default=60, help="主通道需高出其它通道的差值，默认 60")
    return p.parse_args()


PRIMARY = {"magenta": 0, "red": 0, "green": 1, "blue": 2}
# magenta 用 R 与 B 同时高、G 低来判定
MAGENTA = True


def is_hit(r: int, g: int, b: int, color: str, thr: int, sep: int) -> bool:
    if color == "magenta":
        return r >= thr and b >= thr and min(r, b) - g >= sep
    p = PRIMARY[color]
    ch = (r, g, b)
    main = ch[p]
    others = [ch[i] for i in range(3) if i != p]
    return main >= thr and main - max(others) >= sep


def main() -> None:
    a = parse_args()
    if not Path(a.zoning).is_file():
        sys.exit(f"文件不存在：{a.zoning}")

    img = Image.open(a.zoning).convert("RGB")
    w, h = img.size
    px = img.load()

    mask = Image.new("L", (w, h), 0)
    mp = mask.load()
    hit = 0
    for y in range(h):
        for x in range(w):
            if is_hit(*px[x, y], a.color, a.threshold, a.separation):
                mp[x, y] = 255
                hit += 1

    if a.grow > 0:
        mask = mask.filter(ImageFilter.MaxFilter(size=2 * a.grow + 1))

    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    mask.save(a.out)

    total = w * h
    print(f"mask 已生成: {a.out}  ({w}x{h})")
    print(f"命中像素: {hit} ({hit / total:.2%})  颜色: {a.color}  膨胀: {a.grow}px")

    if hit == 0:
        print(f"警告: 没检测到 {a.color} 涂鸦；检查涂鸦颜色或调 --threshold。", file=sys.stderr)
    elif hit / total > 0.9:
        print("警告: 命中超过 90%，可能涂满了或底图本身含大量该颜色。", file=sys.stderr)


if __name__ == "__main__":
    main()
