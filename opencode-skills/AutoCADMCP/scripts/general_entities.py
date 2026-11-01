"""通用二维实体契约，供校验、预览与简写转换共同使用。"""
from __future__ import annotations

import math

KINDS = {"line", "polyline", "rect", "circle", "arc", "text"}
INTERIOR_TYPES = ("interior_plan", "floor_plan")


def drawing_type(plan):
    meta = plan.get("meta", {})
    # 兼容没有 drawing_type 的旧室内计划。
    return meta.get("drawing_type", "interior_plan" if "walls" in plan else "general") if isinstance(meta, dict) else "general"


def number(value):
    return isinstance(value, (float, int)) and not isinstance(value, bool) and math.isfinite(value)


def point(value):
    return (isinstance(value, list) and len(value) in (2, 3)
            and all(number(v) for v in value) and (len(value) == 2 or value[2] == 0))


def entity_errors(entity):
    if not isinstance(entity, dict):
        return ["图元应为对象"]
    errors = []
    kind = entity.get("kind")
    if not isinstance(kind, str) or kind not in KINDS:
        return [f"不支持的 kind: {kind}；需适配或明确转换为支持的二维图元"]
    for key in ("id", "layer", "source"):
        if not isinstance(entity.get(key), str) or not entity[key].strip():
            errors.append(f"{key} 需为非空字符串")
    if any(c in str(entity.get("layer", "")) for c in "|\r\n"):
        errors.append("layer 不得含简写分隔符或换行")
    if entity.get("confidence") not in ("explicit", "inferred", "unresolved"):
        errors.append("confidence 需为 explicit/inferred/unresolved")
    fields = {"line": ("p0", "p1"), "circle": ("center",), "arc": ("center",), "text": ("point",)}
    for key in fields.get(kind, ()):
        if not point(entity.get(key)):
            errors.append(f"{key} 需为有限二维坐标 [x,y] 或 [x,y,0]")
    if kind == "line" and point(entity.get("p0")) and point(entity.get("p1")):
        if entity["p0"][:2] == entity["p1"][:2]:
            errors.append("直线长度必须大于 0")
    if kind == "rect":
        r = entity.get("rect")
        if not (isinstance(r, list) and len(r) == 4 and all(number(v) for v in r) and r[0] < r[2] and r[1] < r[3]):
            errors.append("rect 需为 [xmin,ymin,xmax,ymax] 且宽高为正")
    if kind == "polyline":
        pts = entity.get("points")
        if not isinstance(entity.get("closed", False), bool):
            errors.append("closed 需为布尔值")
        minimum = 3 if entity.get("closed") else 2
        if not (isinstance(pts, list) and len(pts) >= minimum and all(point(p) for p in pts)):
            errors.append(f"points 需至少 {minimum} 个有限二维点")
        elif len({tuple(p[:2]) for p in pts}) < minimum or any(a[:2] == b[:2] for a, b in zip(pts, pts[1:])):
            errors.append("多段线含退化线段或不同顶点不足")
    for key in (("radius",) if kind in {"circle", "arc"} else ("height",) if kind == "text" else ()):
        if not number(entity.get(key)) or entity[key] <= 0:
            errors.append(f"{key} 需为有限正数")
    if kind == "arc":
        if not all(number(entity.get(key)) for key in ("angle0", "angle1")):
            errors.append("angle0/angle1 需为有限角度（度）")
        elif not 0 < (entity["angle1"] - entity["angle0"]) % 360 < 360:
            errors.append("圆弧角度不得重合；整圆使用 circle")
    if kind == "text":
        value = entity.get("text")
        if not isinstance(value, str) or not value.strip() or any(c in value for c in "|\r\n"):
            errors.append("text 需为非空单行文字且不含 |")
    allowed = {"id", "kind", "layer", "source", "confidence", "only_trace"}
    allowed.update({"line": {"p0", "p1"}, "polyline": {"points", "closed"}, "rect": {"rect"},
                    "circle": {"center", "radius"}, "arc": {"center", "radius", "angle0", "angle1"},
                    "text": {"point", "text", "height"}}[kind])
    if set(entity) - allowed:
        errors.append(f"不支持的图元字段: {', '.join(sorted(set(entity) - allowed))}")
    return errors


def validate_entities(entities):
    if not isinstance(entities, list):
        return ["entities 需为数组"]
    errors, ids = [], set()
    for index, entity in enumerate(entities):
        errors.extend(f"entities[{index}]: {error}" for error in entity_errors(entity))
        identity = entity.get("id") if isinstance(entity, dict) else None
        if isinstance(identity, str):
            if identity in ids:
                errors.append(f"id 重复: {identity}")
            ids.add(identity)
    return errors


def draw_entity(draw, entity, xy, scale, font_factory):
    """使用 Pillow 绘制已校验实体，Y 轴翻转由 xy 负责。"""
    color = "#c43b3b" if entity["confidence"] == "unresolved" else "#333333"
    kind = entity["kind"]
    if kind in {"line", "polyline"}:
        points = [xy(p) for p in (entity["points"] if kind == "polyline" else [entity["p0"], entity["p1"]])]
        if entity.get("closed"):
            points.append(points[0])
        draw.line(points, fill=color, width=2)
    elif kind == "rect":
        x0, y0, x1, y1 = entity["rect"]
        draw.rectangle([xy([x0, y1]), xy([x1, y0])], outline=color, width=2)
    elif kind in {"circle", "arc"}:
        x, y = xy(entity["center"])
        r = entity["radius"] * scale
        box = [x-r, y-r, x+r, y+r]
        if kind == "circle":
            draw.ellipse(box, outline=color, width=2)
        else:
            sweep = (entity["angle1"] - entity["angle0"]) % 360
            draw.arc(box, start=-entity["angle0"]-sweep, end=-entity["angle0"], fill=color, width=2)
    elif kind == "text":
        draw.text(xy(entity["point"]), entity["text"], fill=color,
                  font=font_factory(max(1, round(entity["height"] * scale))), anchor="ls")
