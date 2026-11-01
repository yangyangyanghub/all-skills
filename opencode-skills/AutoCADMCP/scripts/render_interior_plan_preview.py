from __future__ import annotations

"""从语义 plan.json 渲染室内平面预览图（Pillow）。

把 plan.json 里的墙体、门窗、家具、洁具、文字与标注按比例缩放到一张 PNG，
供落图前人工审图。仅支持室内平面图（interior_plan），不用于其他图种。
"""

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from general_entities import INTERIOR_TYPES, drawing_type, draw_entity, validate_entities


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="从语义 plan.json 渲染室内平面预览图（仅限室内平面）")
    parser.add_argument("plan", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--width", type=int, default=1800)
    parser.add_argument("--height", type=int, default=1280)
    return parser.parse_args()


def pick_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    """按需选一个可显示中文的本地字体，找不到就用 PIL 默认字体。"""
    candidates = [
        Path("C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/simhei.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def render_preview(plan_path, output_path, width: int = 1800, height: int = 1280):
    """从语义 plan.json 渲染室内平面预览图，返回结果 dict。

    供 CLI 与模块调用共用；文件缺失或 JSON 非法时抛异常，由调用方决定处理。
    """
    plan_path = Path(plan_path)
    output_path = Path(output_path)
    with plan_path.open("r", encoding="utf-8-sig") as handle:
        plan = json.load(handle)
    if drawing_type(plan) not in INTERIOR_TYPES:
        raise ValueError("非室内计划请使用 render_general_plan_preview.py")
    errors = validate_entities(plan.get("entities", []))
    if errors:
        raise ValueError("; ".join(errors))
    plan_w, plan_h = map(float, plan["meta"]["plan_size"])
    if plan_w <= 0 or plan_h <= 0:
        raise ValueError("meta.plan_size 必须为正数")

    image_w, image_h = max(width, 640), max(height, 480)
    margins = (120, 110, 100, 170)
    left, right, top, bottom = margins
    scale = min((image_w - left - right) / plan_w, (image_h - top - bottom) / plan_h)
    image = Image.new("RGB", (image_w, image_h), "#ffffff")
    draw = ImageDraw.Draw(image)
    font_room = pick_font(max(15, image_w // 100), bold=True)
    font_area = pick_font(max(12, image_w // 140))
    font_small = pick_font(max(11, image_w // 155))
    font_title = pick_font(max(16, image_w // 95), bold=True)

    def xy(point: list[float] | tuple[float, float]) -> tuple[float, float]:
        return left + float(point[0]) * scale, top + (plan_h - float(point[1])) * scale

    def box(rect: list[float]) -> list[tuple[float, float]]:
        return [xy((rect[0], rect[3])), xy((rect[2], rect[1]))]

    for room in plan.get("rooms", []):
        rect = room.get("rect")
        if isinstance(rect, list) and len(rect) == 4:
            draw.rectangle(box(rect), fill="#f4f5f2")

    for wall in plan.get("walls", []):
        rect = wall.get("rect")
        if isinstance(rect, list) and len(rect) == 4:
            color = "#24292e" if wall.get("layer") == "A-WALL-EXIST" else "#495057"
            draw.rectangle(box(rect), fill=color, outline="#111111")

    for opening in plan.get("openings", []):
        if "p0" in opening and "p1" in opening:
            draw.line([xy(opening["p0"]), xy(opening["p1"])], fill="#c7ccd1", width=2)

    for window in plan.get("windows", []):
        p0, p1 = window.get("p0"), window.get("p1")
        if not isinstance(p0, list) or not isinstance(p1, list):
            continue
        offset_value = float(window.get("frame_offset", 35))
        orientation = str(window.get("orientation", "H")).upper()
        for offset in (-offset_value, 0, offset_value):
            if orientation == "H":
                a, b = (p0[0], p0[1] + offset), (p1[0], p1[1] + offset)
            else:
                a, b = (p0[0] + offset, p0[1]), (p1[0] + offset, p1[1])
            draw.line([xy(a), xy(b)], fill="#0877b9", width=3)
        if orientation == "H":
            for x in (p0[0], p1[0]):
                draw.line([xy((x, p0[1] - offset_value)), xy((x, p0[1] + offset_value))], fill="#0877b9", width=2)
        else:
            for y in (p0[1], p1[1]):
                draw.line([xy((p0[0] - offset_value, y)), xy((p0[0] + offset_value, y))], fill="#0877b9", width=2)

    for door in plan.get("doors", []):
        hinge, leaf_end = door.get("hinge"), door.get("leaf_end")
        if not isinstance(hinge, list) or not isinstance(leaf_end, list):
            continue
        draw.line([xy(hinge), xy(leaf_end)], fill="#ad5d25", width=4)
        radius = float(door.get("width", 0)) * scale
        cx, cy = xy(hinge)
        start = 360 - float(door.get("angle1", 90))
        end = 360 - float(door.get("angle0", 0))
        draw.arc([cx - radius, cy - radius, cx + radius, cy + radius], start=start, end=end, fill="#ad5d25", width=2)

    def render_furniture(item: dict[str, Any], color: str) -> None:
        rect = item.get("rect")
        if not isinstance(rect, list) or len(rect) != 4:
            return
        draw.rectangle(box(rect), outline=color, width=2)
        x0, y0, x1, y1 = map(float, rect)
        kind = str(item.get("kind", "")).upper()
        if kind.startswith("BED_"):
            if kind == "BED_W":
                draw.line([xy((x0 + 90, y0)), xy((x0 + 90, y1))], fill=color, width=3)
            elif kind == "BED_E":
                draw.line([xy((x1 - 90, y0)), xy((x1 - 90, y1))], fill=color, width=3)
            elif kind == "BED_S":
                draw.line([xy((x0, y0 + 90)), xy((x1, y0 + 90))], fill=color, width=3)
            else:
                draw.line([xy((x0, y1 - 90)), xy((x1, y1 - 90))], fill=color, width=3)
        elif kind in {"WARDROBE", "TV"}:
            draw.line([xy(((x0 + x1) / 2, y0)), xy(((x0 + x1) / 2, y1))], fill=color, width=1)
        elif kind in {"COFFEE", "DINING"}:
            draw.rounded_rectangle(box(rect), radius=7, outline=color, width=2)

    for item in plan.get("fixed_furniture", []):
        render_furniture(item, "#68737d")
    for item in plan.get("movable_furniture", []):
        render_furniture(item, "#93663b")

    for fixture in plan.get("fixtures", []):
        kind = str(fixture.get("kind", "")).upper()
        color = "#087f73"
        if kind in {"SHOWER", "WASHER"} and isinstance(fixture.get("rect"), list):
            rect = fixture["rect"]
            draw.rectangle(box(rect), outline=color, width=2)
            if kind == "SHOWER":
                draw.line([xy((rect[0], rect[1])), xy((rect[2], rect[3]))], fill=color, width=1)
                draw.line([xy((rect[0], rect[3])), xy((rect[2], rect[1]))], fill=color, width=1)
        elif kind == "TOILET" and isinstance(fixture.get("anchor"), list):
            x, y = map(float, fixture["anchor"][:2])
            direction = str(fixture.get("orientation", "N")).upper()
            bounds = {
                "N": ([x - 260, y - 380, x + 260, y], [x - 300, y - 1050, x + 300, y - 350]),
                "S": ([x - 260, y, x + 260, y + 380], [x - 300, y + 350, x + 300, y + 1050]),
                "E": ([x - 380, y - 260, x, y + 260], [x - 1050, y - 300, x - 350, y + 300]),
                "W": ([x, y - 260, x + 380, y + 260], [x + 350, y - 300, x + 1050, y + 300]),
            }.get(direction)
            if bounds:
                draw.rectangle(box(bounds[0]), outline=color, width=2)
                draw.ellipse(box(bounds[1]), outline=color, width=2)

    for room in plan.get("rooms", []):
        label = room.get("label")
        if not isinstance(label, list):
            continue
        px, py = xy(label)
        draw.text((px, py - 10), str(room.get("name", "")), font=font_room, fill="#1d252c", anchor="mm")
        draw.text((px, py + 16), str(room.get("area", "")), font=font_area, fill="#4d5963", anchor="mm")

    for dim in plan.get("dims", []):
        if not isinstance(dim.get("p0"), list) or not isinstance(dim.get("p1"), list):
            continue
        a, b = xy(dim["p0"]), xy(dim["p1"])
        draw.line([a, b], fill="#76519c", width=1)
        position = dim.get("text_position")
        if isinstance(position, list):
            text_xy = xy(position)
        else:
            text_xy = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 - 10)
        draw.text(text_xy, str(dim.get("value", "")), font=font_small, fill="#68458a", anchor="mm")

    for entity in plan.get("entities", []):
        draw_entity(draw, entity, xy, scale, pick_font)

    title = str(plan.get("meta", {}).get("title", "CAD 预览"))
    draw.text((left, image_h - 55), f"{title} | 单位: mm", font=font_title, fill="#20262b", anchor="lm")
    inferred = sum(1 for category in ("walls", "openings", "windows", "doors", "rooms", "fixed_furniture", "movable_furniture", "fixtures", "dims", "notes", "entities") for item in plan.get(category, []) if item.get("confidence") == "inferred")
    unresolved = sum(1 for category in ("walls", "openings", "windows", "doors", "rooms", "fixed_furniture", "movable_furniture", "fixtures", "dims", "notes", "entities") for item in plan.get(category, []) if item.get("confidence") == "unresolved")
    draw.text((image_w - right, image_h - 55), f"推断: {inferred} | 未决: {unresolved}", font=font_small, fill="#59636b", anchor="rm")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, optimize=True)
    manifest_path = Path(str(output_path) + ".manifest.json")
    manifest = {
        "drawing_type": "interior_plan",
        "plan": str(plan_path.resolve()),
        "plan_sha256": sha256_file(plan_path),
        "preview": str(output_path.resolve()),
        "preview_sha256": sha256_file(output_path),
        "renderer": "render_interior_plan_preview.py"
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "preview": str(output_path.resolve()),
        "manifest": str(manifest_path.resolve()),
        "size_px": [image_w, image_h],
        "plan_size_mm": [plan_w, plan_h],
        "inferred": inferred,
        "unresolved": unresolved,
    }


def main() -> int:
    args = parse_args()
    try:
        result = render_preview(args.plan, args.output, args.width, args.height)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"预览失败: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
