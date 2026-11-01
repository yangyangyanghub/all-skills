#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把语义 plan.json 展开为 AutoCADMCP 的 `draw_entities` 简写文本。

本脚本只做「plan.json → 简写文本」的纯映射，不接触 COM；生成的简写文本可直接
作为 `draw_entities` 工具的 `entities` 参数一次性批量落图。这样批量绘制与逐实体
MCP 工具共享同一套底层实现，避免两套画法漂移。

语义展开规则见 ``references/semantic-plan-schema.md`` 第 4 节「转换为 MCP 图元」，
落图顺序见 ``references/execution-and-recovery.md``「默认顺序」。展开逻辑对齐
``plan_renderer.py``，仅将「调用 controller 方法」替换为
「输出一行简写」。

简写语法（每图元一行，``|`` 分隔字段；点内坐标用 ``,``，多点用 ``;`` 分隔）：

    line|start|end|color|layer
    rect|corner1|corner2|color|layer
    circle|center|radius|color|layer
    arc|center|radius|start_angle|end_angle|color|layer
    ellipse|center|major_axis_end|minor_axis_ratio|color|layer
    hatch|points(;)|pattern|scale|angle|color|layer
    text|position|text|height|color|layer
    dimension|start|end|color|layer|text|offset
    polyline|points(;)|closed|color|layer

用法：

    python plan_to_shorthand.py path/to/plan.json [-o output.shorthand.txt]
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from general_entities import INTERIOR_TYPES, drawing_type, validate_entities

# 墙体填充层（固定），与 semantic-plan-schema.md 约定一致。
LAYER_WALL_FILL = "A-WALL-FILL"
# 所有图元默认颜色（原 plan_renderer 未显式指定颜色，均取默认白色）。
COLOR = "white"


def _f(value: Any, default: float = 0.0) -> float:
    """宽松转 float，失败回退 default。"""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _num(value: Any, ndigits: int = 4) -> str:
    """数值转紧凑字符串：整数不带小数点，浮点保留至多 ndigits 位并去尾零。"""
    try:
        f = float(value)
    except (TypeError, ValueError):
        return "0"
    if abs(f - round(f)) < 1e-9:
        return str(int(round(f)))
    s = f"{f:.{ndigits}f}".rstrip("0").rstrip(".")
    return s if s not in ("", "-") else "0"


def _pt(p: Any) -> str:
    """二维坐标点转 ``x,y`` 字符串。"""
    return f"{_num(p[0])},{_num(p[1])}"


def _safe_text(value: Any) -> str:
    """转义文本，避免破坏简写分隔符。

    ``|`` 是字段分隔符、``;`` 是点内多点/多条目分隔符，文本中出现会破坏解析，
    统一替换为全角等价字符；换行压成空格。
    """
    return (
        str(value)
        .replace("\r", " ")
        .replace("\n", " ")
        .replace("|", "｜")
        .replace(";", "；")
    )


def _rect4(rect: Any) -> tuple:
    """矩形 ``[x0, y0, x1, y1]`` → 四元 float 组。"""
    return _f(rect[0]), _f(rect[1]), _f(rect[2]), _f(rect[3])


def ellipse_line(
    center: List[float],
    major: float,
    minor: float,
    rotation: float,
    layer: str,
    color: str = COLOR,
) -> str:
    """由中心/两半轴/旋转角生成 ``ellipse`` 简写行。

    AutoCADMCP 的椭圆用「中心 + 长轴端点 + 短长比」描述（``AddEllipse``），且要求
    短长比 ``0 < ratio <= 1``。因此当 ``minor > major`` 时交换两轴方向（长轴取
    ``rotation+90°``、比取 ``major/minor``），保持几何形状不变。
    """
    cx, cy = _f(center[0]), _f(center[1])
    a = _f(major)   # 沿 rotation 方向的半轴长
    b = _f(minor)   # 沿 rotation+90° 方向的半轴长

    if a >= b:
        axis_angle = math.radians(_f(rotation))
        axis_len = a
        ratio = (b / a) if a > 0 else 1.0
    else:
        axis_angle = math.radians(_f(rotation) + 90.0)
        axis_len = b
        ratio = (a / b) if b > 0 else 1.0

    mx = cx + axis_len * math.cos(axis_angle)
    my = cy + axis_len * math.sin(axis_angle)
    return f"ellipse|{_num(cx)},{_num(cy)}|{_num(mx)},{_num(my)}|{_num(ratio)}|{color}|{layer}"


class PlanToShorthand:
    """按语义 schema 逐项展开 plan.json，输出简写行与计数。"""

    def __init__(self) -> None:
        self.lines: List[str] = []
        # category → 展开后的图元数量（= 落图核对用 MCP 调用数）
        self.stats: Dict[str, int] = {}
        # 各语义数组 → 语义对象数量
        self.semantic_counts: Dict[str, int] = {}

    # -- 计数 ------------------------------------------------------------

    def _emit(self, category: str, line: str) -> None:
        self.lines.append(line)
        self.stats[category] = self.stats.get(category, 0) + 1

    def _count_semantic(self, name: str, items: List[Any]) -> None:
        self.semantic_counts[name] = len(items) if isinstance(items, list) else 0

    # -- 基础图元封装 -----------------------------------------------------

    def _line(self, category: str, a: List[float], b: List[float], layer: str) -> None:
        self._emit(category, f"line|{_pt(a)}|{_pt(b)}|{COLOR}|{layer}")

    def _rect(self, category: str, rect: List[float], layer: str) -> None:
        x0, y0, x1, y1 = _rect4(rect)
        self._emit(category, f"rect|{_num(x0)},{_num(y0)}|{_num(x1)},{_num(y1)}|{COLOR}|{layer}")

    def _hatch(self, category: str, rect: List[float], layer: str) -> None:
        x0, y0, x1, y1 = _rect4(rect)
        pts = f"{_num(x0)},{_num(y0)};{_num(x1)},{_num(y0)};{_num(x1)},{_num(y1)};{_num(x0)},{_num(y1)}"
        self._emit(category, f"hatch|{pts}|SOLID|1.0|0.0|{COLOR}|{layer}")

    def _circle(self, category: str, center: List[float], radius: float, layer: str) -> None:
        self._emit(category, f"circle|{_pt(center)}|{_num(radius)}|{COLOR}|{layer}")

    def _ellipse(
        self,
        category: str,
        center: List[float],
        major: float,
        minor: float,
        layer: str,
        rotation: float = 0.0,
    ) -> None:
        self._emit(category, ellipse_line(center, major, minor, rotation, layer))

    def _arc(
        self, category: str, center: List[float], radius: float, a0: float, a1: float, layer: str
    ) -> None:
        self._emit(
            category,
            f"arc|{_pt(center)}|{_num(radius)}|{_num(a0)}|{_num(a1)}|{COLOR}|{layer}",
        )

    def _text(
        self,
        category: str,
        text: str,
        position: List[float],
        height: float,
        layer: str,
    ) -> None:
        self._emit(
            category,
            f"text|{_pt(position)}|{_safe_text(text)}|{_num(height)}|{COLOR}|{layer}",
        )

    def _dimension(self, p0: List[float], p1: List[float], layer: str, value: Any) -> None:
        text = _num(value) if value is not None else ""
        self._emit("dims", f"dimension|{_pt(p0)}|{_pt(p1)}|{COLOR}|{layer}|{text}")

    # -- 主入口 ----------------------------------------------------------

    def render(self, plan: Dict[str, Any]) -> List[str]:
        if drawing_type(plan) not in INTERIOR_TYPES:
            from validate_plan import REQUIRED_LISTS
            if any(plan.get(key) for key in REQUIRED_LISTS if key != "entities"):
                raise ValueError("通用计划仅支持 entities，不得混用室内语义数组")
            self._entities(plan.get("entities", []))
            return self.lines
        # 顺序对齐 execution-and-recovery.md 默认顺序
        self._walls(plan.get("walls", []))
        self._openings(plan.get("openings", []))
        self._windows(plan.get("windows", []))
        self._sliding(plan.get("sliding", []))
        self._doors(plan.get("doors", []))
        self._furniture(plan.get("fixed_furniture", []), "fixed_furniture")
        self._furniture(plan.get("movable_furniture", []), "movable_furniture")
        self._fixtures(plan.get("fixtures", []))
        self._rooms(plan.get("rooms", []))
        self._dims(plan.get("dims", []))
        self._notes(plan.get("notes", []))
        self._entities(plan.get("entities", []))
        return self.lines

    # -- 各图种 ----------------------------------------------------------

    def _walls(self, walls: List[Any]) -> None:
        self._count_semantic("walls", walls)
        for wall in walls:
            if not isinstance(wall, dict):
                continue
            rect = wall.get("rect")
            if not isinstance(rect, list) or len(rect) != 4:
                continue
            layer = wall.get("layer", "A-WALL-EXIST")
            self._hatch("walls", rect, LAYER_WALL_FILL)  # 先填充再轮廓，避免填充盖住轮廓
            self._rect("walls", rect, layer)

    def _openings(self, openings: List[Any]) -> None:
        self._count_semantic("openings", openings)
        for opening in openings:
            if not isinstance(opening, dict):
                continue
            p0, p1 = opening.get("p0"), opening.get("p1")
            if not isinstance(p0, list) or not isinstance(p1, list):
                continue
            self._line("openings", p0, p1, opening.get("layer", "A-OPENING"))

    def _windows(self, windows: List[Any]) -> None:
        self._count_semantic("windows", windows)
        for window in windows:
            if not isinstance(window, dict):
                continue
            p0, p1 = window.get("p0"), window.get("p1")
            if not isinstance(p0, list) or not isinstance(p1, list):
                continue
            layer = window.get("layer", "A-WINDOW")
            off = _f(window.get("frame_offset", 35), 35)
            orientation = str(window.get("orientation", "H")).upper()
            if orientation == "H":
                y0, y1 = _f(p0[1]), _f(p1[1])
                for offset in (-off, 0, off):
                    self._line("windows", [_f(p0[0]), y0 + offset], [_f(p1[0]), y1 + offset], layer)
                self._line("windows", [_f(p0[0]), y0 - 80], [_f(p0[0]), y0 + 80], layer)
                self._line("windows", [_f(p1[0]), y1 - 80], [_f(p1[0]), y1 + 80], layer)
            else:
                x0, x1 = _f(p0[0]), _f(p1[0])
                for offset in (-off, 0, off):
                    self._line("windows", [x0 + offset, _f(p0[1])], [x1 + offset, _f(p1[1])], layer)
                self._line("windows", [x0 - 80, _f(p0[1])], [x0 + 80, _f(p0[1])], layer)
                self._line("windows", [x1 - 80, _f(p1[1])], [x1 + 80, _f(p1[1])], layer)

    def _sliding(self, sliding: List[Any]) -> None:
        self._count_semantic("sliding", sliding)
        for item in sliding:
            if not isinstance(item, dict):
                continue
            p0, p1 = item.get("p0"), item.get("p1")
            if not isinstance(p0, list) or not isinstance(p1, list):
                continue
            layer = item.get("layer", "A-SLIDING")
            orientation = str(item.get("orientation", "H")).upper()
            pattern = str(item.get("pattern", "")).lower()
            gap = 45
            if pattern == "staggered":
                overlap = _f(item.get("overlap", 120), 120)
                panel_gap = 30
                if orientation == "V":
                    x0, y0, y1 = _f(p0[0]), _f(p0[1]), _f(p1[1])
                    mid = (y0 + y1) / 2
                    upper = mid + overlap / 2
                    lower = mid - overlap / 2
                    self._line("sliding", [x0 - 45, y0], [x0 - 45, upper], layer)
                    self._line("sliding", [x0 - 45 + panel_gap, y0], [x0 - 45 + panel_gap, upper], layer)
                    self._line("sliding", [x0 + 45 - panel_gap, lower], [x0 + 45 - panel_gap, y1], layer)
                    self._line("sliding", [x0 + 45, lower], [x0 + 45, y1], layer)
                else:
                    x0, x1, y0 = _f(p0[0]), _f(p1[0]), _f(p0[1])
                    mid = (x0 + x1) / 2
                    upper = mid + overlap / 2
                    lower = mid - overlap / 2
                    self._line("sliding", [x0, y0 + 45], [upper, y0 + 45], layer)
                    self._line("sliding", [x0, y0 + 45 - panel_gap], [upper, y0 + 45 - panel_gap], layer)
                    self._line("sliding", [lower, y0 - 45 + panel_gap], [x1, y0 - 45 + panel_gap], layer)
                    self._line("sliding", [lower, y0 - 45], [x1, y0 - 45], layer)
            elif orientation == "V":
                for offset in (-gap, 0, gap):
                    self._line("sliding", [_f(p0[0]) + offset, _f(p0[1])], [_f(p1[0]) + offset, _f(p1[1])], layer)
            else:
                for offset in (-gap, 0, gap):
                    self._line("sliding", [_f(p0[0]), _f(p0[1]) + offset], [_f(p1[0]), _f(p1[1]) + offset], layer)

    def _doors(self, doors: List[Any]) -> None:
        self._count_semantic("doors", doors)
        for door in doors:
            if not isinstance(door, dict):
                continue
            hinge, leaf_end = door.get("hinge"), door.get("leaf_end")
            if not isinstance(hinge, list) or not isinstance(leaf_end, list):
                continue
            hx, hy = _f(hinge[0]), _f(hinge[1])
            ex, ey = _f(leaf_end[0]), _f(leaf_end[1])
            thickness = _f(door.get("leaf_thick", 40), 40)
            width = _f(door.get("width", 900), 900)
            layer = door.get("layer", "A-DOOR")
            if abs(hy - ey) < 1:
                rect = [min(hx, ex), hy - thickness / 2, max(hx, ex), hy + thickness / 2]
            else:
                rect = [hx - thickness / 2, min(hy, ey), hx + thickness / 2, max(hy, ey)]
            self._rect("doors", rect, layer)
            a0 = _f(door.get("angle0", 0), 0)
            a1 = _f(door.get("angle1", 90), 90)
            self._arc("doors", [hx, hy], width, a0, a1, "A-DOOR-SWING")

    def _furniture(self, items: List[Any], category: str) -> None:
        self._count_semantic(category, items)
        default_layer = "A-FIXED-FURN" if category == "fixed_furniture" else "A-MOVE-FURN"
        for item in items:
            if not isinstance(item, dict):
                continue
            rect = item.get("rect")
            if not isinstance(rect, list) or len(rect) != 4:
                continue
            layer = item.get("layer", default_layer)
            kind = str(item.get("kind", "")).upper()
            x0, y0, x1, y1 = _rect4(rect)
            self._rect(category, rect, layer)
            if kind in ("BED_W", "BED_E"):
                head_x = x0 + 100 if kind == "BED_W" else x1 - 100
                self._line(category, [head_x, y0], [head_x, y1], layer)
                mid = (y0 + y1) / 2
                pillow_x0 = x0 + 180 if kind == "BED_W" else x1 - 650
                pillow_x1 = x0 + 650 if kind == "BED_W" else x1 - 180
                self._rect(category, [pillow_x0, y0 + 150, pillow_x1, mid - 50], layer)
                self._rect(category, [pillow_x0, mid + 50, pillow_x1, y1 - 150], layer)
            elif kind in ("BED_S", "BED_N"):
                head_y = y0 + 100 if kind == "BED_S" else y1 - 100
                self._line(category, [x0, head_y], [x1, head_y], layer)
                mid = (x0 + x1) / 2
                pillow_y0 = y0 + 180 if kind == "BED_S" else y1 - 650
                pillow_y1 = y0 + 650 if kind == "BED_S" else y1 - 180
                self._rect(category, [x0 + 150, pillow_y0, mid - 50, pillow_y1], layer)
                self._rect(category, [mid + 50, pillow_y0, x1 - 150, pillow_y1], layer)
            elif kind == "WARDROBE":
                if (x1 - x0) > (y1 - y0):
                    mid = (x0 + x1) / 2
                    self._line(category, [mid, y0], [mid, y1], layer)
                else:
                    mid = (y0 + y1) / 2
                    self._line(category, [x0, mid], [x1, mid], layer)
            elif kind == "SOFA":
                self._line(category, [x0 + 100, y0 + 100], [x0 + 100, y1 - 100], layer)
            elif kind == "DINING":
                mid = (y0 + y1) / 2
                self._line(category, [x0 + 120, mid], [x1 - 120, mid], layer)
            elif kind in ("TV", "FRIDGE"):
                mid = (x0 + x1) / 2
                self._line(category, [mid, y0], [mid, y1], layer)
            elif kind == "WASHER":
                cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
                self._circle(category, [cx, cy], min(x1 - x0, y1 - y0) * 0.35, layer)

    def _fixtures(self, fixtures: List[Any]) -> None:
        self._count_semantic("fixtures", fixtures)
        for fixture in fixtures:
            if not isinstance(fixture, dict):
                continue
            kind = str(fixture.get("kind", "")).upper()
            layer = fixture.get("layer", "A-SANITARY")
            if kind == "TOILET":
                self._toilet(fixture, layer)
            elif kind == "SHOWER":
                rect = fixture.get("rect")
                if isinstance(rect, list) and len(rect) == 4:
                    x0, y0, x1, y1 = _rect4(rect)
                    self._rect("fixtures", rect, layer)
                    self._line("fixtures", [x0, y0], [x1, y1], layer)
                    self._line("fixtures", [x0, y1], [x1, y0], layer)
                    self._circle("fixtures", [x1 - 180, y1 - 180], 40, layer)
            elif kind == "BASIN":
                self._basin(fixture, layer)
            elif kind in ("SINK", "STOVE"):
                self._sink_stove(fixture, layer, kind)
            elif kind == "WASHER":
                rect = fixture.get("rect")
                if isinstance(rect, list) and len(rect) == 4:
                    x0, y0, x1, y1 = _rect4(rect)
                    self._rect("fixtures", rect, layer)
                    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
                    self._circle("fixtures", [cx, cy], min(x1 - x0, y1 - y0) * 0.35, layer)

    def _toilet(self, fixture: Dict[str, Any], layer: str) -> None:
        anchor = fixture.get("anchor")
        if not isinstance(anchor, list):
            return
        x, y = _f(anchor[0]), _f(anchor[1])
        orientation = str(fixture.get("orientation", "N")).upper()
        if orientation == "N":
            self._rect("fixtures", [x - 260, y - 380, x + 260, y], layer)
            self._ellipse("fixtures", [x, y - 700], 300, 350, layer)
            self._circle("fixtures", [x, y - 700], 95, layer)
        elif orientation == "S":
            self._rect("fixtures", [x - 260, y, x + 260, y + 380], layer)
            self._ellipse("fixtures", [x, y + 700], 300, 350, layer)
            self._circle("fixtures", [x, y + 700], 95, layer)
        elif orientation == "E":
            self._rect("fixtures", [x - 380, y - 260, x, y + 260], layer)
            self._ellipse("fixtures", [x - 700, y], 350, 300, layer)
            self._circle("fixtures", [x - 700, y], 95, layer)
        else:  # W
            self._rect("fixtures", [x, y - 260, x + 380, y + 260], layer)
            self._ellipse("fixtures", [x + 700, y], 350, 300, layer)
            self._circle("fixtures", [x + 700, y], 95, layer)

    def _basin(self, fixture: Dict[str, Any], layer: str) -> None:
        anchor = fixture.get("anchor")
        if not isinstance(anchor, list):
            return
        x, y = _f(anchor[0]), _f(anchor[1])
        orientation = str(fixture.get("orientation", "W")).upper()
        if orientation == "W":
            self._rect("fixtures", [x, y - 350, x + 600, y + 350], layer)
            self._ellipse("fixtures", [x + 330, y], 220, 250, layer)
        elif orientation == "E":
            self._rect("fixtures", [x - 600, y - 350, x, y + 350], layer)
            self._ellipse("fixtures", [x - 330, y], 220, 250, layer)
        elif orientation == "S":
            self._rect("fixtures", [x - 450, y, x + 450, y + 550], layer)
            self._ellipse("fixtures", [x, y + 300], 330, 180, layer)
        else:  # N
            self._rect("fixtures", [x - 450, y - 550, x + 450, y], layer)
            self._ellipse("fixtures", [x, y - 300], 330, 180, layer)

    def _sink_stove(self, fixture: Dict[str, Any], layer: str, kind: str) -> None:
        center = fixture.get("center")
        if not isinstance(center, list):
            return
        x, y = _f(center[0]), _f(center[1])
        vertical_stove = kind == "STOVE" and str(fixture.get("orientation", "")).upper() == "V"
        if vertical_stove:
            self._rect("fixtures", [x - 240, y - 380, x + 240, y + 380], layer)
        else:
            self._rect("fixtures", [x - 380, y - 240, x + 380, y + 240], layer)
        if kind == "SINK":
            self._ellipse("fixtures", [x, y], 260, 150, layer)
            self._circle("fixtures", [x, y], 35, layer)
        elif vertical_stove:
            for dx in (-90, 90):
                for dy in (-170, 170):
                    self._circle("fixtures", [x + dx, y + dy], 60, layer)
        else:
            for dx in (-170, 170):
                for dy in (-90, 90):
                    self._circle("fixtures", [x + dx, y + dy], 60, layer)

    def _rooms(self, rooms: List[Any]) -> None:
        self._count_semantic("rooms", rooms)
        for room in rooms:
            if not isinstance(room, dict):
                continue
            label = room.get("label")
            if not isinstance(label, list):
                continue
            name = str(room.get("name", ""))
            area = str(room.get("area", ""))
            if name:
                self._text("rooms", name, [_f(label[0]) - 260, _f(label[1]) + 80], 180, "A-ROOM-TEXT")
            if area:
                self._text("rooms", area, [_f(label[0]) - 220, _f(label[1]) - 170], 120, "A-ROOM-TEXT")

    def _dims(self, dims: List[Any]) -> None:
        self._count_semantic("dims", dims)
        for dim in dims:
            if not isinstance(dim, dict):
                continue
            p0, p1 = dim.get("p0"), dim.get("p1")
            if not isinstance(p0, list) or not isinstance(p1, list):
                continue
            self._dimension(p0, p1, dim.get("layer", "A-DIMS"), dim.get("value"))

    def _notes(self, notes: List[Any]) -> None:
        self._count_semantic("notes", notes)
        for note in notes:
            if not isinstance(note, dict):
                continue
            point = note.get("point")
            if not isinstance(point, list):
                continue
            text = str(note.get("text", ""))
            if not text:
                continue
            self._text("notes", text, point, _f(note.get("height", 180), 180), note.get("layer", "A-NOTE"))

    def _entities(self, entities: List[Any]) -> None:
        errors = validate_entities(entities)
        if errors:
            raise ValueError("; ".join(errors))
        self._count_semantic("entities", entities)
        for ent in entities:
            if not isinstance(ent, dict):
                continue
            kind = str(ent.get("kind", "")).lower()
            layer = ent.get("layer", "A-NOTE")
            if kind == "polyline" and isinstance(ent.get("points"), list):
                points = ent["points"]
                if len(points) >= 2:
                    pts_str = ";".join(_pt(p) for p in points)
                    closed = bool(ent.get("closed", False))
                    closed_str = "closed" if closed else "false"
                    self._emit("entities", f"polyline|{pts_str}|{closed_str}|{COLOR}|{layer}")
            elif kind == "line" and isinstance(ent.get("p0"), list) and isinstance(ent.get("p1"), list):
                self._line("entities", ent["p0"], ent["p1"], layer)
            elif kind == "rect":
                self._rect("entities", ent["rect"], layer)
            elif kind == "circle":
                self._circle("entities", ent["center"], ent["radius"], layer)
            elif kind == "arc":
                self._arc("entities", ent["center"], ent["radius"], ent["angle0"], ent["angle1"], layer)
            elif kind == "text":
                self._text("entities", ent["text"], ent["point"], ent["height"], layer)


def load_plan(plan_path: str) -> Dict[str, Any]:
    path = Path(plan_path).expanduser().resolve()
    if not path.is_file():
        raise ValueError(f"plan.json 不存在: {path}")
    with path.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("plan.json 根节点必须是对象")
    return data


def expand_plan_to_shorthand(plan: Dict[str, Any]) -> tuple:
    """展开已加载的 plan dict，返回 (简写行列表, 渲染器)。"""
    renderer = PlanToShorthand()
    lines = renderer.render(plan)
    return lines, renderer


def convert_plan_to_shorthand(plan_path: str, output_path: Optional[str] = None) -> str:
    """把 plan.json 展开为 draw_entities 简写文本；可选写出文件。

    这是给 Agent 模块化调用的主入口，等价于 CLI 的核心逻辑。
    """
    plan = load_plan(plan_path)
    lines, _renderer = expand_plan_to_shorthand(plan)
    text = "\n".join(lines) + "\n"
    if output_path:
        out = Path(output_path).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    return text


def _print_summary(renderer: PlanToShorthand, total: int) -> None:
    print("语义对象 → 展开图元统计:")
    order = [
        "walls", "openings", "windows", "sliding", "doors",
        "fixed_furniture", "movable_furniture", "fixtures", "rooms",
        "dims", "notes", "entities",
    ]
    for name in order:
        semantic = renderer.semantic_counts.get(name, 0)
        expanded = renderer.stats.get(name, 0)
        if semantic or expanded:
            print(f"  {name:<18} 语义对象 {semantic:>3}  →  展开图元 {expanded:>4}")
    print(f"  {'总计':<18} {'—':>3}      →  展开图元 {total:>4}")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="把语义 plan.json 展开为 AutoCADMCP draw_entities 简写文本。"
    )
    parser.add_argument("plan", help="plan.json 路径")
    parser.add_argument(
        "-o",
        "--output",
        help="输出简写文本路径（默认：与 plan.json 同目录、同名 .shorthand.txt）",
    )
    args = parser.parse_args(argv)

    plan = load_plan(args.plan)
    lines, renderer = expand_plan_to_shorthand(plan)

    output = Path(args.output) if args.output else Path(args.plan).with_suffix(".shorthand.txt")
    output = output.expanduser().resolve()
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")

    _print_summary(renderer, len(lines))
    print(f"\n已写出 {len(lines)} 条简写图元 → {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
