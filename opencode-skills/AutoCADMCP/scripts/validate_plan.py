from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from general_entities import INTERIOR_TYPES, drawing_type, validate_entities


# plan.json 顶层必须出现的语义数组；缺一个都是结构错误。
REQUIRED_LISTS = (
    "walls",
    "openings",
    "windows",
    "sliding",
    "doors",
    "rooms",
    "fixed_furniture",
    "movable_furniture",
    "fixtures",
    "dims",
    "notes",
    "entities",
)
# 证据置信度的合法取值。
CONFIDENCE = {"explicit", "inferred", "unresolved"}
# 几何比较的容差（毫米），用于判断「贴墙」「共线」这类近似关系。
TOLERANCE_MM = 2.0


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="校验语义 plan.json 的结构与几何约束")
    parser.add_argument("plan", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--tolerance", type=float, default=TOLERANCE_MM)
    return parser.parse_args()


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def valid_point(value: Any) -> bool:
    return isinstance(value, list) and len(value) in (2, 3) and all(is_number(item) for item in value)


def valid_rect(value: Any) -> bool:
    return (
        isinstance(value, list)
        and len(value) == 4
        and all(is_number(item) for item in value)
        and value[0] < value[2]
        and value[1] < value[3]
    )


def each_object(plan: dict[str, Any]) -> Iterable[tuple[str, int, dict[str, Any]]]:
    """按类别遍历所有语义对象，产出 (类别, 下标, 对象)。"""
    for category in REQUIRED_LISTS:
        values = plan.get(category, [])
        if isinstance(values, list):
            for index, item in enumerate(values):
                if isinstance(item, dict):
                    yield category, index, item


def collect_wall_faces(
    walls: list[dict[str, Any]],
) -> tuple[list[tuple[float, float, float]], list[tuple[float, float, float]]]:
    """把墙矩形拆成竖直/水平两组墙面，供「贴墙」判定使用。

    竖直面记 (x, y0, y1)，水平面记 (y, x0, x1)。
    """
    vertical: list[tuple[float, float, float]] = []
    horizontal: list[tuple[float, float, float]] = []
    for wall in walls:
        rect = wall.get("rect")
        if not valid_rect(rect):
            continue
        x0, y0, x1, y1 = map(float, rect)
        vertical.extend(((x0, y0, y1), (x1, y0, y1)))
        horizontal.extend(((y0, x0, x1), (y1, x0, x1)))
    return vertical, horizontal


def intervals_overlap(a0: float, a1: float, b0: float, b1: float, tolerance: float) -> bool:
    return min(a1, b1) - max(a0, b0) > tolerance


def rect_edge_on_wall(
    rect: list[float],
    direction: str,
    vertical: list[tuple[float, float, float]],
    horizontal: list[tuple[float, float, float]],
    tolerance: float,
) -> bool:
    """判断矩形的某条边是否贴到墙面（按 N/S/E/W 方向）。"""
    x0, y0, x1, y1 = map(float, rect)
    direction = direction.upper()
    if direction in {"W", "E"}:
        x = x0 if direction == "W" else x1
        return any(abs(face - x) <= tolerance and intervals_overlap(y0, y1, a, b, tolerance) for face, a, b in vertical)
    if direction in {"S", "N"}:
        y = y0 if direction == "S" else y1
        return any(abs(face - y) <= tolerance and intervals_overlap(x0, x1, a, b, tolerance) for face, a, b in horizontal)
    return False


def point_on_wall(
    point: list[float],
    direction: str,
    vertical: list[tuple[float, float, float]],
    horizontal: list[tuple[float, float, float]],
    tolerance: float,
) -> bool:
    """判断一个点（按方向投影后）是否落在墙面上。"""
    x, y = map(float, point[:2])
    direction = direction.upper()
    if direction in {"W", "E"}:
        return any(abs(face - x) <= tolerance and a - tolerance <= y <= b + tolerance for face, a, b in vertical)
    if direction in {"S", "N"}:
        return any(abs(face - y) <= tolerance and a - tolerance <= x <= b + tolerance for face, a, b in horizontal)
    return False


def point_inside_rect(point: tuple[float, float], rect: list[float], tolerance: float = 0.0) -> bool:
    x, y = point
    x0, y0, x1, y1 = map(float, rect)
    return x0 - tolerance <= x <= x1 + tolerance and y0 - tolerance <= y <= y1 + tolerance


def cross2d(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> float:
    """二维叉积，判断 c 在直线 ab 的哪一侧。"""
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def segments_intersect(
    a: tuple[float, float],
    b: tuple[float, float],
    c: tuple[float, float],
    d: tuple[float, float],
    tolerance: float,
) -> bool:
    return cross2d(a, b, c) * cross2d(a, b, d) < -tolerance and cross2d(c, d, a) * cross2d(c, d, b) < -tolerance


def segment_hits_rect(a: tuple[float, float], b: tuple[float, float], rect: list[float], tolerance: float) -> bool:
    """判断线段是否与矩形相交（含端点落入矩形或穿过任意边）。"""
    if point_inside_rect(a, rect, -tolerance) or point_inside_rect(b, rect, -tolerance):
        return True
    x0, y0, x1, y1 = map(float, rect)
    edges = (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0)))
    return any(segments_intersect(a, b, c, d, tolerance) for c, d in edges)


def validate(plan: dict[str, Any], source: Path, tolerance: float) -> dict[str, Any]:
    if drawing_type(plan) not in INTERIOR_TYPES:
        return validate_general(plan, source)
    errors: list[str] = []
    warnings: list[str] = []

    meta = plan.get("meta")
    if not isinstance(meta, dict):
        errors.append("顶层 meta 应为对象")
        meta = {}
    if meta.get("units") != "mm":
        errors.append("meta.units 需为 mm")
    size = meta.get("plan_size")
    if not valid_point(size) or len(size) != 2 or size[0] <= 0 or size[1] <= 0:
        errors.append("meta.plan_size 需为正数的 [宽, 高]")
        width = height = 0.0
    else:
        width, height = map(float, size)

    for category in REQUIRED_LISTS:
        if not isinstance(plan.get(category), list):
            errors.append(f"{category} 字段应为数组")

    seen_ids: set[str] = set()
    confidence_counts: Counter[str] = Counter()
    layer_counts: Counter[str] = Counter()
    for category, index, item in each_object(plan):
        label = f"{category}[{index}]"
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id.strip():
            errors.append(f"{label} 缺少非空 id")
        elif item_id in seen_ids:
            errors.append(f"id 重复: {item_id}")
        else:
            seen_ids.add(item_id)
        confidence = item.get("confidence")
        if confidence not in CONFIDENCE:
            errors.append(f"{label} 的 confidence 取值应为 explicit/inferred/unresolved")
        else:
            confidence_counts[confidence] += 1
        if confidence in {"inferred", "unresolved"} and not item.get("source"):
            errors.append(f"{label} 标为 {confidence}，应补充 source 说明依据")
        if confidence == "unresolved" and not item.get("only_trace"):
            warnings.append(f"{label} 为 unresolved，建议加 only_trace=true")
        layer = item.get("layer")
        if isinstance(layer, str) and layer:
            layer_counts[layer] += 1

    walls = plan.get("walls") if isinstance(plan.get("walls"), list) else []
    for index, wall in enumerate(walls):
        rect = wall.get("rect") if isinstance(wall, dict) else None
        if not valid_rect(rect):
            errors.append(f"walls[{index}] 的 rect 不合法")
        elif width and (rect[0] < -tolerance or rect[1] < -tolerance or rect[2] > width + tolerance or rect[3] > height + tolerance):
            errors.append(f"walls[{index}] 越出 plan_size 范围")

    vertical, horizontal = collect_wall_faces([wall for wall in walls if isinstance(wall, dict)])
    obstacles: list[dict[str, Any]] = []
    for category in ("fixed_furniture", "movable_furniture"):
        for index, item in enumerate(plan.get(category, [])):
            if not isinstance(item, dict) or not valid_rect(item.get("rect")):
                errors.append(f"{category}[{index}] 的 rect 不合法")
                continue
            rect = item["rect"]
            obstacles.append({"id": item.get("id", f"{category}[{index}]"), "rect": rect})
            if width and (rect[0] < -tolerance or rect[1] < -tolerance or rect[2] > width + tolerance or rect[3] > height + tolerance):
                errors.append(f"{category}[{index}] 越出 plan_size 范围")
            bed_direction = {"BED_W": "W", "BED_E": "E", "BED_S": "S", "BED_N": "N"}.get(str(item.get("kind", "")).upper())
            if bed_direction and not rect_edge_on_wall(rect, bed_direction, vertical, horizontal, tolerance):
                errors.append(f"{item.get('id')} 床头未靠到 {bed_direction} 向墙面")
            contacts = item.get("contacts", [])
            if not isinstance(contacts, list):
                errors.append(f"{item.get('id')} 的 contacts 应为数组")
            else:
                for direction in contacts:
                    if str(direction).upper() not in {"N", "S", "E", "W"}:
                        errors.append(f"{item.get('id')} 的 contacts 含无效方向 {direction}")
                    elif not rect_edge_on_wall(rect, str(direction), vertical, horizontal, tolerance):
                        errors.append(f"{item.get('id')} 未靠到要求的 {direction} 向墙面")

    for index, fixture in enumerate(plan.get("fixtures", [])):
        if not isinstance(fixture, dict):
            errors.append(f"fixtures[{index}] 应为对象")
            continue
        kind = str(fixture.get("kind", "")).upper()
        if kind == "TOILET":
            anchor = fixture.get("anchor")
            direction = str(fixture.get("orientation", "")).upper()
            if not valid_point(anchor) or direction not in {"N", "S", "E", "W"}:
                errors.append(f"fixtures[{index}] 马桶需要 anchor 和 N/S/E/W 的 orientation")
            elif not point_on_wall(anchor, direction, vertical, horizontal, tolerance):
                errors.append(f"{fixture.get('id')} 马桶水箱侧未贴墙")
            else:
                x, y = map(float, anchor[:2])
                bounds = {"N": [x - 300, y - 1050, x + 300, y], "S": [x - 300, y, x + 300, y + 1050], "E": [x - 1050, y - 300, x, y + 300], "W": [x, y - 300, x + 1050, y + 300]}[direction]
                obstacles.append({"id": fixture.get("id"), "rect": bounds})
        elif kind in {"SHOWER", "WASHER"}:
            if not valid_rect(fixture.get("rect")):
                errors.append(f"fixtures[{index}] {kind} 需要 rect")
            else:
                obstacles.append({"id": fixture.get("id"), "rect": fixture["rect"]})

    for index, window in enumerate(plan.get("windows", [])):
        if not isinstance(window, dict) or not valid_point(window.get("p0")) or not valid_point(window.get("p1")):
            errors.append(f"windows[{index}] 需要 p0 和 p1")
            continue
        p0, p1 = window["p0"], window["p1"]
        orientation_value = str(window.get("orientation", "")).upper()
        if orientation_value == "H" and abs(float(p0[1]) - float(p1[1])) > tolerance:
            errors.append(f"windows[{index}] 标为 H 但两端点不水平")
        elif orientation_value == "V" and abs(float(p0[0]) - float(p1[0])) > tolerance:
            errors.append(f"windows[{index}] 标为 V 但两端点不垂直")
        elif orientation_value not in {"H", "V"}:
            errors.append(f"windows[{index}] 的 orientation 需为 H 或 V")

    for index, door in enumerate(plan.get("doors", [])):
        if not isinstance(door, dict) or not valid_point(door.get("hinge")) or not valid_point(door.get("leaf_end")) or not is_number(door.get("width")):
            errors.append(f"doors[{index}] 需要 hinge、leaf_end 和 width")
            continue
        hinge = tuple(map(float, door["hinge"][:2]))
        leaf_end = tuple(map(float, door["leaf_end"][:2]))
        width_value = float(door["width"])
        if abs(math.dist(hinge, leaf_end) - width_value) > max(tolerance, width_value * 0.01):
            errors.append(f"{door.get('id')} 门扇长度与 width 不一致")
        for obstacle in obstacles:
            if segment_hits_rect(hinge, leaf_end, obstacle["rect"], tolerance):
                errors.append(f"{door.get('id')} 完全开启门扇与 {obstacle['id']} 相交")
                continue
            angle0, angle1 = door.get("angle0"), door.get("angle1")
            if is_number(angle0) and is_number(angle1) and float(angle1) > float(angle0):
                for step in range(1, 19):
                    angle = math.radians(float(angle0) + (float(angle1) - float(angle0)) * step / 18)
                    sweep_end = (hinge[0] + width_value * math.cos(angle), hinge[1] + width_value * math.sin(angle))
                    if segment_hits_rect(hinge, sweep_end, obstacle["rect"], tolerance):
                        errors.append(f"{door.get('id')} 开启包络与 {obstacle['id']} 相交")
                        break

    planned_calls = (
        len(walls)
        + len(plan.get("openings", []))
        + sum(5 for _ in plan.get("windows", []))
        + sum(3 for _ in plan.get("sliding", []))
        + sum(2 for _ in plan.get("doors", []))
        + len(plan.get("fixed_furniture", []))
        + len(plan.get("movable_furniture", []))
        + len(plan.get("fixtures", []))
        + sum(2 for _ in plan.get("rooms", []))
        + len(plan.get("dims", []))
        + len(plan.get("notes", []))
        + len(plan.get("entities", []))
    )
    errors.extend(validate_entities(plan.get("entities", [])))
    return {
        "source": str(source.resolve()),
        "plan_sha256": sha256_file(source),
        "status": "ok" if not errors else "failed",
        "errors": errors,
        "warnings": warnings,
        "counts": {category: len(plan.get(category, [])) if isinstance(plan.get(category), list) else 0 for category in REQUIRED_LISTS},
        "confidence_counts": dict(confidence_counts),
        "semantic_layer_counts": dict(layer_counts),
        "estimated_mcp_calls": planned_calls,
    }


def validate_general(plan: dict[str, Any], source: Path) -> dict[str, Any]:
    errors = validate_entities(plan.get("entities"))
    meta = plan.get("meta")
    if not isinstance(meta, dict):
        errors.append("meta 需为对象")
        meta = {}
    if meta.get("units") != "mm":
        errors.append("meta.units 需为 mm")
    if not isinstance(meta.get("drawing_type"), str) or not meta["drawing_type"].strip():
        errors.append("meta.drawing_type 需明确实际图种")
    if not isinstance(meta.get("reference_required"), bool):
        errors.append("meta.reference_required 需为布尔值")
    for key in REQUIRED_LISTS:
        if key != "entities" and plan.get(key):
            errors.append(f"通用计划不展开 {key}；请转换为 entities")
    entities = plan.get("entities") if isinstance(plan.get("entities"), list) else []
    if not entities:
        errors.append("entities 不得为空")
    return {
        "source": str(source.resolve()), "plan_sha256": sha256_file(source),
        "drawing_type": drawing_type(plan), "validation_scope": "general_2d_geometry",
        "status": "failed" if errors else "ok", "errors": errors,
        "warnings": ["仅完成通用二维几何检查；未自动验证图种专业规范、尺寸关系及设计合理性，需目视复核"],
        "counts": {"entities": len(entities)},
        "semantic_layer_counts": dict(Counter(e.get("layer") for e in entities if isinstance(e, dict) and isinstance(e.get("layer"), str))),
        "estimated_mcp_calls": len(entities),
    }


def validate_plan_file(plan_path, tolerance: float = TOLERANCE_MM, output=None) -> dict[str, Any]:
    """校验一个 plan.json 文件，返回校验结果 dict；可选写出 JSON 报告。

    这是给 Agent 模块化调用的主入口，等价于 CLI 的核心逻辑。文件缺失或 JSON
    非法时不抛异常，而是在结果里返回 ``status="failed"``。
    """
    source = Path(plan_path).expanduser().resolve()
    try:
        with source.open("r", encoding="utf-8-sig") as handle:
            plan = json.load(handle)
        if not isinstance(plan, dict):
            raise ValueError("plan.json 根节点必须是对象")
        result = validate(plan, source, tolerance)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {"source": str(source), "status": "failed", "errors": [str(exc)], "warnings": [], "counts": {}}
    if output:
        out = Path(output).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main() -> int:
    args = parse_args()
    result = validate_plan_file(args.plan, args.tolerance, args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
