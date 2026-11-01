from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成原图与 CAD 预览的并排审查图和待填写报告")
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--preview", type=Path, required=True)
    parser.add_argument("--comparison", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--drawing-type", required=True)
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fit(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    contained = ImageOps.contain(image.convert("RGB"), size)
    canvas = Image.new("RGB", size, "white")
    canvas.paste(contained, ((size[0] - contained.width) // 2, (size[1] - contained.height) // 2))
    return canvas


def main() -> int:
    args = parse_args()
    for label, path in (("plan", args.plan), ("source", args.source), ("preview", args.preview)):
        if not path.is_file():
            print(f"{label} 不存在: {path}", file=sys.stderr)
            return 1
    try:
        source = Image.open(args.source)
        preview = Image.open(args.preview)
    except OSError as exc:
        print(f"无法读取图片: {exc}", file=sys.stderr)
        return 1

    panel_size = (1100, 900)
    header = 70
    output = Image.new("RGB", (panel_size[0] * 2, panel_size[1] + header), "white")
    output.paste(fit(source, panel_size), (0, header))
    output.paste(fit(preview, panel_size), (panel_size[0], header))
    draw = ImageDraw.Draw(output)
    font = ImageFont.load_default(size=28)
    draw.text((panel_size[0] // 2, 32), "SOURCE", fill="#111111", font=font, anchor="mm")
    draw.text((panel_size[0] + panel_size[0] // 2, 32), "CAD PREVIEW", fill="#111111", font=font, anchor="mm")
    draw.line((panel_size[0], 0, panel_size[0], output.height), fill="#333333", width=3)
    args.comparison.parent.mkdir(parents=True, exist_ok=True)
    output.save(args.comparison, optimize=True)

    report = {
        "status": "pending",
        "drawing_type": args.drawing_type,
        "sha256": {
            "plan": sha256(args.plan),
            "source": sha256(args.source),
            "preview": sha256(args.preview),
        },
        "comparison_image": str(args.comparison.resolve()),
        "review_method": "agent_visual_side_by_side",
        "checks": [
            {"name": "overall_outline_and_proportion", "status": "pending", "notes": ""},
            {"name": "anchors_and_alignment", "status": "pending", "notes": ""},
            {"name": "major_geometry_and_openings", "status": "pending", "notes": ""},
            {"name": "details_text_and_dimensions", "status": "pending", "notes": ""}
        ],
        "blocking_issues": ["必须查看 comparison_image，完成全部检查后才能改为 passed"],
        "residual_differences": []
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"comparison": str(args.comparison.resolve()), "report": str(args.report.resolve()), "status": "pending"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
