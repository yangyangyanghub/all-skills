# id-photo 证件照工厂 · 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 交付 `id-photo` skill——输入一张端正人像 + 证件类型，输出合规规格的电子版与 5寸/6寸相纸排版。

**Architecture:** 纯 Python 脚本集（`scripts/`）+ Pillow/numpy，单一职责分文件：规格库加载 → 构图裁切 → 换底色 → 缩放 → 相纸排版 → CLI 编排。无 Web/服务依赖。

**Tech Stack:** Python 3.10、Pillow 12.2、numpy 1.26、pytest 9.1；可选 rembg + onnxruntime（AI 抠图）。

## Global Constraints

- Python 3.10+；依赖 Pillow、numpy、pytest（均已装）
- 代码缩进 4 空格、命名 snake_case（**已提请洋哥确认，AGENTS.md「2 空格 + camelCase」与此冲突**）
- 函数名动词开头；禁止静默吞异常；禁止 `Any` 类型注解
- 脚本必须可被 import 且无导入副作用（主逻辑放 `if __name__ == "__main__":`）
- 输出 PNG 必须写入 dpi 元数据，值 = 该规格的 `dpi` 字段
- 输出目录：`E:\code\my-ai-workspace\assets\generated\`
- 所有规格数据以 `specs/photo-specs.json` 为唯一权威来源

---

## File Structure

```
.opencode/skills/id-photo/
├── SKILL.md                     # 入口：触发词、用法、路由
├── DESIGN.md                    # 设计文档（已完成）
├── PLAN.md                      # 本计划
├── specs/
│   └── photo-specs.json         # 规格库（Task 1）
├── scripts/
│   ├── specs.py                 # 规格加载/查询（Task 1）
│   ├── crop_and_resize.py       # 构图+裁切+缩放（Task 2）
│   ├── cutout.py                # 换底色：色差法 + rembg 升级（Task 3/4）
│   ├── layout_sheet.py          # 相纸排版（Task 5）
│   └── make_idphoto.py          # 主 CLI 编排（Task 6）
└── tests/
    ├── test_specs.py
    ├── test_crop_and_resize.py
    ├── test_cutout.py
    ├── test_layout_sheet.py
    └── test_end_to_end.py
```

---

## Task 1: 规格库与查询

**Files:**
- Create: `.opencode/skills/id-photo/specs/photo-specs.json`
- Create: `.opencode/skills/id-photo/scripts/specs.py`
- Test: `.opencode/skills/id-photo/tests/test_specs.py`

**Interfaces:**
- Consumes: 无
- Produces: `load_specs() -> list[dict]`；`get_spec(key: str) -> dict`；`list_specs() -> list[dict]`

- [ ] **Step 1: 写失败测试**

`tests/test_specs.py`：
```python
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import specs


def test_load_specs_returns_list():
    items = specs.load_specs()
    assert isinstance(items, list)
    assert len(items) >= 20


def test_get_spec_by_id():
    s = specs.get_spec("xiaotwo")
    assert s["mm"] == [35, 45]
    assert s["px"] == [413, 531]
    assert s["dpi"] == 300


def test_get_spec_by_alias():
    assert specs.get_spec("小二寸")["id"] == "xiaotwo"


def test_idcard_is_350dpi():
    s = specs.get_spec("shenfenzheng")
    assert s["dpi"] == 350
    assert s["px"] == [358, 441]


def test_unknown_spec_raises():
    import pytest
    with pytest.raises(KeyError):
        specs.get_spec("__nope__")
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python -m pytest .opencode/skills/id-photo/tests/test_specs.py -v` (workdir = workspace 根)
Expected: FAIL — `ModuleNotFoundError: No module named 'specs'`

- [ ] **Step 3: 写 `scripts/specs.py`**

```python
import json
import os

_SPECS_PATH = os.path.join(os.path.dirname(__file__), "..", "specs", "photo-specs.json")


def load_specs():
    with open(_SPECS_PATH, encoding="utf-8") as f:
        return json.load(f)["specs"]


def get_spec(key):
    for spec in load_specs():
        if spec["id"] == key or key in spec.get("aliases", []):
            return spec
    raise KeyError(f"unknown spec: {key}")


def list_specs():
    return load_specs()


if __name__ == "__main__":
    for spec in load_specs():
        print(f"{spec['id']:16s} {spec['name']:12s} {spec['mm'][0]}x{spec['mm'][1]}mm  {spec['px'][0]}x{spec['px'][1]}px @{spec['dpi']}dpi")
```

- [ ] **Step 4: 写 `specs/photo-specs.json`**（数据来源见 DESIGN.md 第 5 节）

```json
{
  "specs": [
    {"id": "shenfenzheng", "name": "居民身份证", "mm": [26, 32], "px": [358, 441], "pxMax": null, "dpi": 350, "aliases": ["身份证"], "usage": "身份证制证", "bg": ["white"], "headPercent": null, "fileKB": [null, null], "variable": false, "source": "GA/T 461-2019", "note": ""},
    {"id": "huzhao", "name": "护照/出入境", "mm": [33, 48], "px": [390, 567], "pxMax": null, "dpi": 300, "aliases": ["护照", "出入境"], "usage": "护照、出入境证件", "bg": ["white"], "headPercent": null, "fileKB": [null, null], "variable": false, "source": "国家移民管理局《出入境证件相片照相指引》", "note": "头部宽15-22mm/高28-33mm"},
    {"id": "jiache", "name": "驾驶证", "mm": [22, 32], "px": [260, 378], "pxMax": null, "dpi": 300, "aliases": ["驾照"], "usage": "机动车驾驶证", "bg": ["white"], "headPercent": null, "fileKB": [null, null], "variable": false, "source": "GA482-2012", "note": ""},
    {"id": "shebaoka_blue", "name": "社保卡（蓝底）", "mm": [26, 32], "px": [358, 441], "pxMax": null, "dpi": 350, "aliases": ["社保卡蓝底"], "usage": "社会保障卡", "bg": ["blue"], "headPercent": null, "fileKB": [null, null], "variable": false, "source": "人社部《社会保障卡数字相片技术要求》", "note": ""},
    {"id": "shebaoka_white", "name": "社保卡（白底）", "mm": [33, 48], "px": [390, 567], "pxMax": null, "dpi": 300, "aliases": ["社保卡白底"], "usage": "社会保障卡", "bg": ["white"], "headPercent": null, "fileKB": [null, null], "variable": false, "source": "人社部《社会保障卡数字相片技术要求》", "note": ""},
    {"id": "yicun", "name": "一寸", "mm": [25, 35], "px": [295, 413], "pxMax": null, "dpi": 300, "aliases": ["1寸", "一寸照"], "usage": "通用", "bg": ["white", "blue", "red"], "headPercent": null, "fileKB": [null, null], "variable": false, "source": "行业惯例", "note": ""},
    {"id": "xiaoyicun", "name": "小一寸", "mm": [22, 32], "px": [260, 378], "pxMax": null, "dpi": 300, "aliases": ["小1寸"], "usage": "通用", "bg": ["white", "blue", "red"], "headPercent": null, "fileKB": [null, null], "variable": false, "source": "行业惯例", "note": ""},
    {"id": "dayicun", "name": "大一寸", "mm": [33, 48], "px": [390, 567], "pxMax": null, "dpi": 300, "aliases": ["大1寸"], "usage": "通用", "bg": ["white", "blue", "red"], "headPercent": null, "fileKB": [null, null], "variable": false, "source": "行业惯例", "note": ""},
    {"id": "ercun", "name": "二寸", "mm": [35, 49], "px": [413, 579], "pxMax": null, "dpi": 300, "aliases": ["2寸", "标准二寸"], "usage": "通用", "bg": ["white", "blue", "red"], "headPercent": null, "fileKB": [null, null], "variable": false, "source": "行业惯例", "note": ""},
    {"id": "xiaotwo", "name": "小二寸", "mm": [35, 45], "px": [413, 531], "pxMax": null, "dpi": 300, "aliases": ["小二寸照", "小二寸"], "usage": "学位、职称、简历", "bg": ["white", "blue", "red"], "headPercent": null, "fileKB": [null, null], "variable": false, "source": "行业惯例", "note": ""},
    {"id": "daercun", "name": "大二寸", "mm": [35, 53], "px": [413, 626], "pxMax": null, "dpi": 300, "aliases": ["大2寸"], "usage": "通用", "bg": ["white", "blue", "red"], "headPercent": null, "fileKB": [null, null], "variable": false, "source": "行业惯例", "note": ""},
    {"id": "meiqian", "name": "美国签证", "mm": [51, 51], "px": [600, 600], "pxMax": [1200, 1200], "dpi": 300, "aliases": ["美签"], "usage": "美国签证", "bg": ["white"], "headPercent": null, "fileKB": [null, 240], "variable": false, "source": "travel.state.gov", "note": "JPEG；2×2英寸"},
    {"id": "shengen", "name": "申根签证", "mm": [35, 45], "px": [413, 531], "pxMax": null, "dpi": 400, "aliases": ["申根"], "usage": "申根签证", "bg": ["white", "light_grey"], "headPercent": "70-80%", "fileKB": [null, null], "variable": false, "source": "EU Visa Code / ICAO Doc 9303", "note": "建议400dpi"},
    {"id": "riqian", "name": "日本签证", "mm": [45, 45], "px": [600, 600], "pxMax": null, "dpi": 300, "aliases": ["日签"], "usage": "日本签证", "bg": ["white"], "headPercent": null, "fileKB": [null, 120], "variable": true, "source": "日本外务省", "note": "部分领馆接受35×45或2×2英寸"},
    {"id": "yingqian", "name": "英国签证", "mm": [35, 45], "px": [600, 750], "pxMax": null, "dpi": 300, "aliases": ["英签"], "usage": "英国签证", "bg": ["white", "light_grey"], "headPercent": null, "fileKB": [50, 10240], "variable": false, "source": "gov.uk", "note": ""},
    {"id": "jiaqian", "name": "加拿大签证", "mm": [35, 45], "px": [420, 540], "pxMax": [2000, 2800], "dpi": 300, "aliases": ["加签"], "usage": "加拿大临时居民签证", "bg": ["white"], "headPercent": null, "fileKB": [null, 4096], "variable": true, "source": "canada.ca", "note": "PR卡为50×70mm"},
    {"id": "aoqian", "name": "澳大利亚签证", "mm": [35, 45], "px": [900, 1200], "pxMax": [1200, 1600], "dpi": 300, "aliases": ["澳签"], "usage": "澳大利亚签证", "bg": ["white"], "headPercent": null, "fileKB": [70, 3584], "variable": false, "source": "homeaffairs.gov.au", "note": "头部32-36mm"},
    {"id": "hanqian", "name": "韩国签证", "mm": [35, 45], "px": [413, 531], "pxMax": null, "dpi": 300, "aliases": ["韩签"], "usage": "韩国签证", "bg": ["white"], "headPercent": null, "fileKB": [null, 500], "variable": false, "source": "韩国外交部", "note": "头部25-35mm"},
    {"id": "xinxilan", "name": "新西兰签证", "mm": [35, 45], "px": [900, 1200], "pxMax": [2250, 3000], "dpi": 300, "aliases": ["新西兰"], "usage": "新西兰签证", "bg": ["white"], "headPercent": "70-80%", "fileKB": [512, 3215], "variable": true, "source": "immigration.govt.nz", "note": "在线申请仅要求3:4比例"},
    {"id": "gongwuyuan", "name": "公务员报名", "mm": [25, 35], "px": [295, 413], "pxMax": null, "dpi": 300, "aliases": ["公务员"], "usage": "公务员考试报名", "bg": ["blue", "white"], "headPercent": null, "fileKB": [null, 100], "variable": false, "source": "国家公务员局", "note": ""},
    {"id": "jiaozi", "name": "教师资格证报名", "mm": [25, 35], "px": [295, 413], "pxMax": [400, 600], "dpi": 300, "aliases": ["教资"], "usage": "教师资格证报名", "bg": ["white"], "headPercent": null, "fileKB": [null, 200], "variable": true, "source": "中小学教师资格考试网", "note": "广东为400×600，其余省份不同"},
    {"id": "kaoyan", "name": "考研报名", "mm": [25, 35], "px": [295, 413], "pxMax": [480, 640], "dpi": 300, "aliases": ["考研"], "usage": "研究生考试报名", "bg": ["white", "blue"], "headPercent": null, "fileKB": [null, 10240], "variable": true, "source": "研招网", "note": "各省份不同，山西要求480×640"},
    {"id": "xuewei", "name": "学位照", "mm": [33, 48], "px": [390, 567], "pxMax": [480, 640], "dpi": 300, "aliases": ["学位"], "usage": "学历学位图像采集", "bg": ["light_blue", "white", "light_grey"], "headPercent": null, "fileKB": [20, 40], "variable": false, "source": "教育部学历证书电子注册图像采集规范", "note": ""}
  ]
}
```

- [ ] **Step 5: 运行测试，确认通过**

Run: `python -m pytest .opencode/skills/id-photo/tests/test_specs.py -v`
Expected: 5 passed

- [ ] **Step 6: 提交**

```bash
git add .opencode/skills/id-photo/specs/photo-specs.json .opencode/skills/id-photo/scripts/specs.py .opencode/skills/id-photo/tests/test_specs.py
git commit -m "feat(id-photo): add photo spec library and loader"
```

---

## Task 2: 构图、裁切、缩放

**Files:**
- Create: `.opencode/skills/id-photo/scripts/crop_and_resize.py`
- Test: `.opencode/skills/id-photo/tests/test_crop_and_resize.py`

**Interfaces:**
- Consumes: 无
- Produces: `find_subject_bbox(img, thresh=240) -> tuple[int,int,int,int]`；`crop_to_ratio(img, ratio, head_margin=0.08) -> Image`；`resize_to_spec(img, px) -> Image`

- [ ] **Step 1: 写失败测试**

`tests/test_crop_and_resize.py`：
```python
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import crop_and_resize as cr


def make_img():
    im = Image.new("RGB", (300, 400), "white")
    for x in range(100, 200):
        for y in range(50, 300):
            im.putpixel((x, y), (200, 0, 0))
    return im


def test_find_subject_bbox():
    assert cr.find_subject_bbox(make_img()) == (100, 50, 199, 299)


def test_crop_to_ratio_has_target_ratio():
    out = cr.crop_to_ratio(make_img(), (35, 45))
    w, h = out.size
    assert abs(w / h - 35 / 45) < 0.01


def test_resize_to_spec_exact():
    out = cr.resize_to_spec(make_img(), (413, 531))
    assert out.size == (413, 531)
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python -m pytest .opencode/skills/id-photo/tests/test_crop_and_resize.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'crop_and_resize'`

- [ ] **Step 3: 写 `scripts/crop_and_resize.py`**

```python
import numpy as np
from PIL import Image


def find_subject_bbox(img, thresh=240):
    arr = np.asarray(img.convert("RGB")).mean(axis=2)
    mask = arr < thresh
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return (0, 0, img.width - 1, img.height - 1)
    return (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))


def crop_to_ratio(img, ratio, head_margin=0.08):
    rw, rh = ratio
    W, H = img.size
    x0, y0, x1, _y1 = find_subject_bbox(img)
    cx = (x0 + x1) / 2
    target = rw / rh

    crop_w = W
    crop_h = crop_w / target
    if crop_h > H:
        crop_h = H
        crop_w = crop_h * target

    top = y0 - head_margin * crop_h
    top = max(0, min(top, H - crop_h))
    left = cx - crop_w / 2
    left = max(0, min(left, W - crop_w))

    return img.crop((round(left), round(top), round(left + crop_w), round(top + crop_h)))


def resize_to_spec(img, px):
    return img.resize((int(px[0]), int(px[1])), Image.LANCZOS)
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `python -m pytest .opencode/skills/id-photo/tests/test_crop_and_resize.py -v`
Expected: 3 passed

- [ ] **Step 5: 提交**

```bash
git add .opencode/skills/id-photo/scripts/crop_and_resize.py .opencode/skills/id-photo/tests/test_crop_and_resize.py
git commit -m "feat(id-photo): add subject bbox detection and ratio crop"
```

---

## Task 3: 抠图引擎（色差法）

**Files:**
- Create: `.opencode/skills/id-photo/scripts/cutout.py`
- Test: `.opencode/skills/id-photo/tests/test_cutout.py`

**Interfaces:**
- Consumes: 无
- Produces: `detect_bg_color(img, corner=10) -> tuple[int,int,int]`；`is_bg_uniform(img, thresh=12) -> bool`；`cutout_alpha(img, bg_color, tol=40, feather=1) -> Image(RGBA)`；`replace_bg(img, color) -> Image(RGB)`

- [ ] **Step 1: 写失败测试**

`tests/test_cutout.py`：
```python
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import cutout


def make_img():
    im = Image.new("RGB", (100, 100), "white")
    for x in range(30, 70):
        for y in range(30, 70):
            im.putpixel((x, y), (200, 0, 0))
    return im


def test_detect_bg_is_white():
    bg = cutout.detect_bg_color(make_img())
    assert all(c > 240 for c in bg)


def test_bg_is_uniform():
    assert cutout.is_bg_uniform(make_img()) is True


def test_replace_bg_blue():
    out = cutout.replace_bg(make_img(), (67, 142, 219))
    assert out.getpixel((0, 0)) == (67, 142, 219)
    assert out.getpixel((50, 50)) == (200, 0, 0)
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python -m pytest .opencode/skills/id-photo/tests/test_cutout.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cutout'`

- [ ] **Step 3: 写 `scripts/cutout.py`**

```python
import numpy as np
from PIL import Image, ImageFilter


def detect_bg_color(img, corner=10):
    arr = np.asarray(img.convert("RGB"))
    patches = [arr[:corner, :corner], arr[:corner, -corner:], arr[-corner:, :corner], arr[-corner:, -corner:]]
    px = np.concatenate([p.reshape(-1, 3) for p in patches], axis=0)
    return tuple(int(v) for v in px.mean(axis=0))


def is_bg_uniform(img, thresh=12):
    arr = np.asarray(img.convert("RGB"))
    c = 10
    patches = [arr[:c, :c], arr[:c, -c:], arr[-c:, :c], arr[-c:, -c:]]
    px = np.concatenate([p.reshape(-1, 3) for p in patches], axis=0)
    return float(px.std(axis=0).mean()) < thresh


def cutout_alpha(img, bg_color, tol=40, feather=1):
    arr = np.asarray(img.convert("RGB")).astype(np.int32)
    bg = np.array(bg_color, dtype=np.int32)
    dist = np.sqrt(((arr - bg) ** 2).sum(axis=2))
    alpha = np.clip((dist - tol) / max(1, tol) * 255, 0, 255).astype(np.uint8)
    alpha_img = Image.fromarray(alpha, "L")
    if feather:
        alpha_img = alpha_img.filter(ImageFilter.GaussianBlur(feather))
    rgba = img.convert("RGBA")
    rgba.putalpha(alpha_img)
    return rgba


def replace_bg(img, color):
    bg = detect_bg_color(img)
    rgba = cutout_alpha(img, bg)
    base = Image.new("RGB", img.size, tuple(color))
    base.paste(rgba, (0, 0), rgba)
    return base
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `python -m pytest .opencode/skills/id-photo/tests/test_cutout.py -v`
Expected: 3 passed

- [ ] **Step 5: 提交**

```bash
git add .opencode/skills/id-photo/scripts/cutout.py .opencode/skills/id-photo/tests/test_cutout.py
git commit -m "feat(id-photo): add color-distance background replacement"
```

---

## Task 4: rembg AI 抠图升级（可选）

**Files:**
- Modify: `.opencode/skills/id-photo/scripts/cutout.py`
- Test: `.opencode/skills/id-photo/tests/test_cutout.py`（追加）

**Interfaces:**
- Consumes: `replace_bg`（Task 3）
- Produces: `has_rembg() -> bool`；`cutout_auto(img, target_color) -> Image(RGB)`

- [ ] **Step 1: 安装依赖（洋哥已同意）**

Run: `pip install rembg onnxruntime`
Expected: 安装成功（首次运行 rembg 会自动下载 ~170MB 模型）

- [ ] **Step 2: 追加测试**

`tests/test_cutout.py` 追加：
```python
def test_cutout_auto_returns_rgb():
    out = cutout.cutout_auto(make_img(), (67, 142, 219))
    assert out.mode == "RGB"
    assert out.size == (100, 100)


def test_has_rembg_is_bool():
    assert isinstance(cutout.has_rembg(), bool)
```

- [ ] **Step 3: 运行测试，确认失败**

Run: `python -m pytest .opencode/skills/id-photo/tests/test_cutout.py -v -k auto`
Expected: FAIL — `AttributeError: module 'cutout' has no attribute 'cutout_auto'`

- [ ] **Step 4: 在 `scripts/cutout.py` 末尾追加**

```python
def has_rembg():
    try:
        import rembg  # noqa: F401
        return True
    except ImportError:
        return False


def cutout_auto(img, target_color):
    if has_rembg():
        from rembg import remove
        rgba = remove(img.convert("RGB")).convert("RGBA")
        base = Image.new("RGB", img.size, tuple(target_color))
        base.paste(rgba, (0, 0), rgba)
        return base
    return replace_bg(img, target_color)
```

- [ ] **Step 5: 运行全部 cutout 测试**

Run: `python -m pytest .opencode/skills/id-photo/tests/test_cutout.py -v`
Expected: 5 passed

- [ ] **Step 6: 提交**

```bash
git add .opencode/skills/id-photo/scripts/cutout.py .opencode/skills/id-photo/tests/test_cutout.py
git commit -m "feat(id-photo): add rembg auto-upgrade for background replacement"
```

---

## Task 5: 相纸排版

**Files:**
- Create: `.opencode/skills/id-photo/scripts/layout_sheet.py`
- Test: `.opencode/skills/id-photo/tests/test_layout_sheet.py`

**Interfaces:**
- Consumes: 无
- Produces: `SHEETS: dict[str, tuple[int,int]]`；`plan_grid(sheet_size, photo_size, gap=20) -> tuple[int,int]`；`make_sheet(photo, sheet_key, gap=20) -> Image`

- [ ] **Step 1: 写失败测试**

`tests/test_layout_sheet.py`：
```python
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import layout_sheet


def test_plan_grid_5inch_xiaotwo():
    assert layout_sheet.plan_grid((1050, 1500), (413, 531)) == (2, 2)


def test_make_sheet_5inch_size():
    photo = Image.new("RGB", (413, 531), "white")
    assert layout_sheet.make_sheet(photo, "5inch").size == (1050, 1500)


def test_make_sheet_6inch_size():
    photo = Image.new("RGB", (413, 531), "white")
    assert layout_sheet.make_sheet(photo, "6inch").size == (1500, 1800)
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python -m pytest .opencode/skills/id-photo/tests/test_layout_sheet.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'layout_sheet'`

- [ ] **Step 3: 写 `scripts/layout_sheet.py`**

```python
from PIL import Image, ImageDraw

SHEETS = {"5inch": (1050, 1500), "6inch": (1500, 1800)}


def plan_grid(sheet_size, photo_size, gap=20):
    sw, sh = sheet_size
    pw, ph = photo_size
    cols = (sw + gap) // (pw + gap)
    rows = (sh + gap) // (ph + gap)
    return max(1, cols), max(1, rows)


def make_sheet(photo, sheet_key, gap=20):
    SW, SH = SHEETS[sheet_key]
    sheet = Image.new("RGB", (SW, SH), "white")
    cols, rows = plan_grid((SW, SH), photo.size, gap)

    grid_w = cols * photo.width + (cols - 1) * gap
    grid_h = rows * photo.height + (rows - 1) * gap
    mx = (SW - grid_w) // 2
    my = (SH - grid_h) // 2

    draw = ImageDraw.Draw(sheet)
    for r in range(rows):
        for c in range(cols):
            x = mx + c * (photo.width + gap)
            y = my + r * (photo.height + gap)
            sheet.paste(photo, (x, y))
            draw.rectangle([x - 1, y - 1, x + photo.width, y + photo.height], outline=(190, 190, 190), width=1)
    return sheet
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `python -m pytest .opencode/skills/id-photo/tests/test_layout_sheet.py -v`
Expected: 3 passed

- [ ] **Step 5: 提交**

```bash
git add .opencode/skills/id-photo/scripts/layout_sheet.py .opencode/skills/id-photo/tests/test_layout_sheet.py
git commit -m "feat(id-photo): add photo sheet layout"
```

---

## Task 6: 主 CLI 编排

**Files:**
- Create: `.opencode/skills/id-photo/scripts/make_idphoto.py`
- Test: `.opencode/skills/id-photo/tests/test_end_to_end.py`

**Interfaces:**
- Consumes: `specs.get_spec`、`crop_and_resize.*`、`cutout.cutout_auto`、`layout_sheet.make_sheet`
- Produces: `make_idphoto(src, spec_id, out_dir, bg=None, sheets=("5inch","6inch")) -> dict`（返回生成的文件路径字典）

- [ ] **Step 1: 写失败测试**

`tests/test_end_to_end.py`：
```python
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import make_idphoto


def make_src(path):
    im = Image.new("RGB", (295, 413), "white")
    for x in range(100, 195):
        for y in range(50, 360):
            im.putpixel((x, y), (180, 60, 60))
    im.save(path)


def test_make_idphoto_outputs(tmp_path):
    src = str(tmp_path / "src.jpg")
    make_src(src)
    out_dir = str(tmp_path / "out")
    result = make_idphoto.make_idphoto(src, "xiaotwo", out_dir, sheets=("5inch", "6inch"))

    assert os.path.exists(result["single"])
    assert Image.open(result["single"]).size == (413, 531)
    assert Image.open(result["sheet_5inch"]).size == (1050, 1500)
    assert Image.open(result["sheet_6inch"]).size == (1500, 1800)
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python -m pytest .opencode/skills/id-photo/tests/test_end_to_end.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'make_idphoto'`

- [ ] **Step 3: 写 `scripts/make_idphoto.py`**

```python
import argparse
import os

from PIL import Image

import specs
from crop_and_resize import crop_to_ratio, resize_to_spec
from cutout import cutout_auto
from layout_sheet import SHEETS, make_sheet

BG_COLORS = {"white": (255, 255, 255), "blue": (67, 142, 219), "red": (215, 0, 15)}


def make_idphoto(src, spec_id, out_dir, bg=None, sheets=("5inch", "6inch")):
    spec = specs.get_spec(spec_id)
    os.makedirs(out_dir, exist_ok=True)

    img = Image.open(src).convert("RGB")
    if bg is not None:
        img = cutout_auto(img, BG_COLORS[bg])
    img = crop_to_ratio(img, tuple(spec["mm"]))
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
    parser.add_argument("--out", default=r"E:\code\my-ai-workspace\assets\generated")
    parser.add_argument("--bg", choices=list(BG_COLORS), default=None)
    parser.add_argument("--sheets", default="5inch,6inch")
    args = parser.parse_args()

    sheets = tuple(s for s in args.sheets.split(",") if s in SHEETS)
    result = make_idphoto(args.src, args.spec, args.out, bg=args.bg, sheets=sheets)
    for k, v in result.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `python -m pytest .opencode/skills/id-photo/tests/test_end_to_end.py -v`
Expected: 1 passed

- [ ] **Step 5: 运行全部测试**

Run: `python -m pytest .opencode/skills/id-photo/tests/ -v`
Expected: 全部 passed

- [ ] **Step 6: 提交**

```bash
git add .opencode/skills/id-photo/scripts/make_idphoto.py .opencode/skills/id-photo/tests/test_end_to_end.py
git commit -m "feat(id-photo): add CLI orchestration for id photo generation"
```

---

## Task 7: SKILL.md 入口文档

**Files:**
- Create: `.opencode/skills/id-photo/SKILL.md`

**Interfaces:**
- Consumes: 全部脚本的 CLI 用法
- Produces: 面向 LLM 的 skill 入口（触发词、用法、规格查询、路由）

- [ ] **Step 1: 写 `SKILL.md`**

```markdown
---
name: id-photo
description: 证件照工厂。给一张端正人像，说出证件类型（一寸/二寸/小二寸/护照/各类签证/报名照），自动按官方规格裁切、可换底色（白/蓝/红）、输出电子版并排版到 5寸/6寸相纸。当用户提到"证件照""一寸/二寸/小二寸""护照照片""签证照片""换底色""排相纸"时使用。
---

# id-photo 证件照工厂

## 能力
- 按规格精确裁切、缩放（px 与 dpi 精确匹配）
- 换底色：白 / 蓝 / 红（默认零依赖色差法，装了 rembg 自动升级为 AI 抠图）
- 5寸 / 6寸相纸自动排版（自动算最优张数）

## 用法

```bash
python scripts/make_idphoto.py --src <源图路径> --spec <规格> [--bg white|blue|red] [--out <目录>]
```

- `--spec`：规格 id 或别名，如 `xiaotwo` 或 `小二寸`
- `--bg`：不填=保留原底色

## 查询规格
```bash
python scripts/specs.py            # 列出全部（若提供）
```

## 规格库
`specs/photo-specs.json` 为唯一权威来源，含国内证件、8 国签证、报名类共 24 条。`variable: true` 的规格因省份/领馆而异，使用前需向用户确认。

## 构图说明
采用「非背景包围盒 + 经验规则」（头顶留白 ~8%、水平居中）。对标准证件照原图有效；生活照等非标准图需人工确认。
```

- [ ] **Step 2: 提交**

```bash
git add .opencode/skills/id-photo/SKILL.md
git commit -m "docs(id-photo): add SKILL.md entry"
```

---

## Task 8: 端到端回归验证

**Files:**
- 使用现有源图：`E:\code\my-ai-workspace\temp\source_idphoto.jpg`

- [ ] **Step 1: 跑真实源图（小二寸）**

Run: `python .opencode/skills/id-photo/scripts/make_idphoto.py --src "E:\code\my-ai-workspace\temp\source_idphoto.jpg" --spec 小二寸`
Expected: 生成 `assets/generated/source_idphoto_xiaotwo.png`（413×531）、`_5inch.png`（1050×1500）、`_6inch.png`（1500×1800）

- [ ] **Step 2: 换底色验证**

Run: `python .opencode/skills/id-photo/scripts/make_idphoto.py --src "E:\code\my-ai-workspace\temp\source_idphoto.jpg" --spec 小二寸 --bg blue`
Expected: 输出蓝底版本

- [ ] **Step 3: 目检**

用图像查看工具检查：人脸居中、头顶留白合规、蓝底边缘（发丝、衣领）无明显毛边。

- [ ] **Step 4: 提交产物说明（不提交图片）**

图片是产物，留在 `assets/generated/`；不纳入 git。

---

## Self-Review

**1. Spec coverage** — DESIGN.md 各节 → 任务映射：
- 规格库（第 4-5 节）→ Task 1 ✓
- 构图裁切缩放（第 7 节）→ Task 2 ✓
- 换底色（第 6 节）→ Task 3/4 ✓
- 5寸/6寸排版（第 8 节）→ Task 5 ✓
- 主流程（第 7 节）→ Task 6 ✓
- 入口文档 → Task 7 ✓
- 验证方式（第 9 节）→ Task 6 单元 + Task 8 真实回归 ✓

**2. Placeholder scan** — 无 TBD/TODO；每个代码步骤含完整代码。

**3. Type consistency** — `make_idphoto` 引用 `specs.get_spec`、`crop_and_resize.crop_to_ratio/resize_to_spec`、`cutout.cutout_auto`、`layout_sheet.SHEETS/make_sheet`，签名与各 Task 定义一致。

## 待洋哥确认

1. **代码风格冲突**：AGENTS.md 要求「2 空格缩进 + camelCase」，本计划按 Python 惯例「4 空格 + snake_case」。是否调整？
2. **Task 4 安装 rembg**：需 `pip install rembg onnxruntime`（你已同意）；若安装失败，`cutout_auto` 自动回退色差法。
3. **提交节奏**：每个 Task 末尾有 `git commit`。是否允许执行？（AGENTS.md：提交需明确授权）

---

## 实现结果与偏差记录（2026-10-08 实现时补充）

- **已完成**：Task 1–7 全部落地；`specs/photo-specs.json` 23 条；5 个脚本 + 5 个测试文件；**17/17 单测通过**；真实源图端到端验证（小二寸 413×531、5寸 4 张、6寸、换蓝底）。
- **Task 4（rembg）未落地**：rembg 依赖 numpy 2.x，与本机 conda 环境（numpy<2，供 langchain 使用）冲突，`import rembg` 直接挂起。已卸载 rembg、回滚 numpy 1.26.4。`cutout_auto()` 自动回退色差法，功能不受影响。
- **真实回归修复 2 个 bug**（单测未覆盖，真实照片暴露）：
  1. `cutout_alpha` 脸部高光被误判为背景（脸被抠成底色）→ 改为「仅与图像边缘连通的近似背景色区域」判为背景（`scipy.ndimage.label`）。
  2. `detect_bg_color` 采样四角被底部衣服污染（背景没换成）→ 改为只采样顶部与上半侧边。
- **环境遗留**：numpy 曾升至 2.2.6（已回滚 1.26.4）；rembg 及其依赖包（onnxruntime / opencv-python-headless / numba / llvmlite / pymatting / pooch 等）残留待清理。
