import argparse
import os

from PIL import Image

import specs
from crop_and_resize import crop_to_ratio, resize_to_spec
from cutout import cutout_auto
from layout_sheet import SHEETS, make_sheet

BG_COLORS = {"white": (255, 255, 255), "blue": (67, 142, 219), "red": (215, 0, 15), "light_grey": (240, 240, 240), "light_blue": (200, 220, 240)}


def make_idphoto(src, spec_id, out_dir, bg=None, sheets=("5inch", "6inch")):
    spec = specs.get_spec(spec_id)
    os.makedirs(out_dir, exist_ok=True)

    if not os.path.isfile(src):
        raise FileNotFoundError(f"源图不存在: {src}")
    img = Image.open(src).convert("RGB")
    if bg is not None:
        img = cutout_auto(img, BG_COLORS[bg])
    # 用 px 比例裁切（px 为最终输出尺寸；避免个别规格 mm 与 px 比例不一致时被拉伸）
    img = crop_to_ratio(img, tuple(spec["px"]))
    img = resize_to_spec(img, tuple(spec["px"]))

    base = os.path.splitext(os.path.basename(src))[0]
    result = {}

    single = os.path.join(out_dir, f"{base}_{spec['id']}.png")
    img.save(single, dpi=(spec["dpi"], spec["dpi"]))
    result["single"] = single

    for sheet_key in sheets:
        sheet = make_sheet(img, sheet_key)
        path = os.path.join(out_dir, f"{base}_{spec['id']}_{sheet_key}.png")
        sheet.save(path, dpi=(300, 300))
        result[f"sheet_{sheet_key}"] = path

    return result


def main():
    parser = argparse.ArgumentParser(description="证件照生成器")
    parser.add_argument("--src", required=True, help="源图路径")
    parser.add_argument("--spec", required=True, help="规格 id 或别名，如 xiaotwo / 小二寸")
    default_out = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "assets", "generated"))
    parser.add_argument("--out", default=default_out)
    parser.add_argument("--bg", choices=list(BG_COLORS), default=None)
    parser.add_argument("--sheets", default="5inch,6inch")
    args = parser.parse_args()

    sheets = tuple(s for s in args.sheets.split(",") if s in SHEETS)
    result = make_idphoto(args.src, args.spec, args.out, bg=args.bg, sheets=sheets)
    for k, v in result.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
