"""从通用 entities 计划生成等比例二维预览与哈希证据清单。"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

from general_entities import INTERIOR_TYPES, drawing_type, draw_entity
from render_interior_plan_preview import pick_font
from validate_plan import sha256_file, validate_plan_file


def render_preview(plan_path, output_path, width=1800, height=1280):
    plan_path, output_path = Path(plan_path), Path(output_path)
    report = validate_plan_file(plan_path)
    if report["status"] != "ok":
        raise ValueError("; ".join(report["errors"]))
    plan = json.loads(plan_path.read_text(encoding="utf-8-sig"))
    if drawing_type(plan) in INTERIOR_TYPES:
        raise ValueError("室内语义计划需使用室内预览器")
    width, height = max(640, width), max(480, height)
    entities = plan["entities"]
    bounds = []
    for entity in entities:
        kind = entity["kind"]
        if kind == "line":
            bounds.extend([entity["p0"][:2], entity["p1"][:2]])
        elif kind == "polyline":
            bounds.extend(p[:2] for p in entity["points"])
        elif kind == "rect":
            r = entity["rect"]
            bounds.extend([r[:2], r[2:]])
        elif kind in {"circle", "arc"}:
            x, y = entity["center"][:2]
            r = entity["radius"]
            bounds.extend([[x-r, y-r], [x+r, y+r]])
        elif kind == "text":
            x, y = entity["point"][:2]
            h = entity["height"]
            box = pick_font(100).getbbox(entity["text"], anchor="ls")
            bounds.extend([[x+box[0]*h/100, y-box[3]*h/100], [x+box[2]*h/100, y-box[1]*h/100]])
    x0, y0 = (min(p[i] for p in bounds) for i in (0, 1))
    x1, y1 = (max(p[i] for p in bounds) for i in (0, 1))
    scale = min((width-160)/max(x1-x0, 1), (height-180)/max(y1-y0, 1))
    left = (width-(x1-x0)*scale)/2
    top = (height-80-(y1-y0)*scale)/2

    def xy(p):
        return left+(p[0]-x0)*scale, top+(y1-p[1])*scale

    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    for entity in entities:
        draw_entity(draw, entity, xy, scale, pick_font)
    draw.text((40, height-48), f"{drawing_type(plan)} | mm | 通用几何预览，专业规范需复核",
              font=pick_font(18), fill="#555555")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, optimize=True)
    manifest_path = Path(str(output_path)+".manifest.json")
    manifest = {
        "drawing_type": drawing_type(plan), "plan": str(plan_path.resolve()),
        "plan_sha256": sha256_file(plan_path), "preview": str(output_path.resolve()),
        "preview_sha256": sha256_file(output_path), "renderer": "render_general_plan_preview.py",
        "validation_scope": report["validation_scope"], "warnings": report["warnings"],
        "entity_count": len(entities), "bounds_mm": [x0, y0, x1, y1],
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"preview": str(output_path.resolve()), "manifest": str(manifest_path.resolve()), "size_px": [width, height]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan")
    parser.add_argument("--output", required=True)
    parser.add_argument("--width", type=int, default=1800)
    parser.add_argument("--height", type=int, default=1280)
    args = parser.parse_args()
    try:
        print(json.dumps(render_preview(args.plan, args.output, args.width, args.height), ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f"预览失败: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
