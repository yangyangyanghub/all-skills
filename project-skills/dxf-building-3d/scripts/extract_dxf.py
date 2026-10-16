# -*- coding: utf-8 -*-
"""
通用 DXF 建筑图纸提取器（天正 CAD 标准图层）
用法:
  python extract_dxf.py <图纸.dxf> [--origin X,Y] [--mirror z|none] [--out 输出目录]

输出（JSON，坐标系已按参数归一）:
  walls.json       墙线段 [x1,z1,x2,z2]（已剔窗框线，保留窗间墙）
  windows.json     窗玻璃段 {axis,y/x,a,b}（当前仅"窗块 INSERT"一种来源；成对线/轮廓线见 SKILL.md 映射表，需另行补齐）
  doors.json       门 [x,z,rot,宽]（宽=XSCALE）
  columns.json     结构柱 [x,z]
  stairs.json      楼梯间 [x0,z0,x1,z1]（踏步区）
  furniture.json   家具 [x,z,短边,长边,rot]
  room_labels.json 房间名标注 [文字,x,z]
"""
import sys, json, math, argparse, collections

# ---- 天正标准图层（可改）----
L_WALL = ("WALL", "PUB_WALL")
L_WINDOW = "WINDOW"
L_COLUMN = "COLUMN"
L_STAIR = "STAIR"
L_SURFACE = "SURFACE"
L_SPACE = "SPACE"
L_PUBTEXT = "PUB_TEXT"
L_FURNITURE = ("ZP-活动家具", "fur")
DOOR_BLOCK_KEY = "Dor"
WINDOW_BLOCK_KEY = "WIN"


def parse_dxf(path):
    """解析 DXF 的 ENTITIES 段（支持 GBK/UTF-8）"""
    raw = open(path, "rb").read()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("gbk", errors="replace")
    lines = text.splitlines()
    ents, cur, in_ent, i, n = [], None, False, 0, len(lines)
    while i < n - 1:
        code = lines[i].strip(); val = lines[i + 1]
        if code == "0" and val.strip() == "SECTION":
            in_ent = (lines[i + 3].strip() == "ENTITIES" if i + 3 < n else False)
            i += 2; continue
        if code == "0" and val.strip() == "ENDSEC":
            in_ent = False
            if cur: ents.append(cur); cur = None
            i += 2; continue
        if not in_ent:
            i += 2; continue
        if code == "0":
            if cur: ents.append(cur)
            cur = {"type": val.strip(), "pairs": []}
        elif cur is not None:
            try: cur["pairs"].append((int(code), val.strip()))
            except ValueError: pass
        i += 2
    return ents


def g(pairs, code, default=None):
    return next((v for cc, v in pairs if cc == code), default)


def make_sc(origin, mirror, zmax):
    ox, oy = origin
    def sc(x, y):
        sx = float(x) / 1000.0 - ox
        sy = float(y) / 1000.0
        return (round(sx, 2), round(zmax - oy - sy, 2) if mirror == "z" else round(sy - oy, 2))
    return sc


def _ymax_m(ents, oy=None):
    ys = []
    for e in ents:
        for c, v in e["pairs"]:
            if c == 20:
                try: ys.append(float(v) / 1000.0)
                except ValueError: pass
    return max(ys) if ys else 0.0


def seg_of(e, sc):
    """实体 → [(x1,z1,x2,z2)]"""
    if e["type"] == "LINE":
        try:
            p = e["pairs"]
            a = sc(g(p, 10), g(p, 20)); b = sc(g(p, 11), g(p, 21))
            return [(a[0], a[1], b[0], b[1])]
        except (TypeError, ValueError):
            return []
    if e["type"] == "LWPOLYLINE":
        verts, x = [], None
        for c, v in e["pairs"]:
            if c == 10: x = float(v)
            elif c == 20 and x is not None:
                verts.append(sc(x, float(v))); x = None
        return [(verts[k][0], verts[k][1], verts[k+1][0], verts[k+1][1]) for k in range(len(verts)-1)]
    return []


def in_main(x1, z1, x2, z2, bounds):
    x0, z0, x1m, z1m = bounds
    return (x0 < min(x1, x2) and max(x1, x2) < x1m and z0 < min(z1, z2) and max(z1, z2) < z1m)


def extract(path, origin, mirror, bounds):
    ents = parse_dxf(path)
    zmax = _ymax_m(ents, origin[1]) if mirror == "z" else 0.0
    sc = make_sc(origin, mirror, zmax)

    walls, wall_lines, surf_lines, wall_all = [], [], [], []
    for e in ents:
        layer = g(e["pairs"], 8, "")
        if layer in L_WALL or layer == L_SURFACE:
            for s in seg_of(e, sc):
                if not in_main(*s, bounds): continue
                L = math.hypot(s[2]-s[0], s[3]-s[1])
                if L < 0.15: continue
                if layer in L_WALL:
                    wall_lines.append(s + (L,)); wall_all.append(s)
                else:
                    surf_lines.append(s + (L,))

    # 窗：①块 ②成对线 ③轮廓线 —— 方向=墙端点分布，宽=XSCALE
    def wall_angle(x, z):
        pts = []
        for x1, z1, x2, z2 in wall_all:
            if math.hypot(x1-x, z1-z) < 1.6: pts.append((x1, z1))
            if math.hypot(x2-x, z2-z) < 1.6: pts.append((x2, z2))
        if len(pts) < 2: return None
        xs = [p[0] for p in pts]; zs = [p[1] for p in pts]
        return 0 if (max(xs)-min(xs)) >= (max(zs)-min(zs)) else math.pi/2

    windows, used = [], []
    for e in ents:
        if e["type"] != "INSERT": continue
        blk, layer = g(e["pairs"], 2, ""), g(e["pairs"], 8, "")
        if WINDOW_BLOCK_KEY not in blk and layer != L_WINDOW: continue
        if DOOR_BLOCK_KEY in blk: continue
        x, y = g(e["pairs"], 10), g(e["pairs"], 20)
        if x is None: continue
        wx, wz = sc(x, y)
        if not in_main(wx, wz, wx, wz, bounds): continue
        w = max(0.6, min(abs(float(g(e["pairs"], 41, "1800"))) / 1000.0, 8.0))
        ang = wall_angle(wx, wz)
        if ang is None:
            ang = 0 if float(g(e["pairs"], 50, "0")) % 180 == 0 else math.pi/2
        if abs(ang) < 0.1:
            windows.append({"axis": "x", "y": round(wz, 2), "a": round(wx-w/2, 2), "b": round(wx+w/2, 2)})
        else:
            windows.append({"axis": "z", "x": round(wx, 2), "a": round(wz-w/2, 2), "b": round(wz+w/2, 2)})
        used.append((wx, wz))

    # 门（宽=XSCALE）
    doors = []
    for e in ents:
        if e["type"] != "INSERT" or DOOR_BLOCK_KEY not in g(e["pairs"], 2, ""): continue
        x, y = g(e["pairs"], 10), g(e["pairs"], 20)
        if x is None: continue
        dx, dz = sc(x, y)
        if not in_main(dx, dz, dx, dz, bounds): continue
        w = max(0.6, min(abs(float(g(e["pairs"], 41, "1000"))) / 1000.0, 2.0))
        doors.append([dx, dz, round(float(g(e["pairs"], 50, "0")) % 360, 1), round(w, 2)])

    # 柱 / 楼梯 / 家具 / 房间名
    columns = []
    for e in ents:
        if e["type"] != "INSERT" or g(e["pairs"], 8, "") != L_COLUMN: continue
        x, y = g(e["pairs"], 10), g(e["pairs"], 20)
        if x is None: continue
        cx, cz = sc(x, y)
        if in_main(cx, cz, cx, cz, bounds): columns.append([cx, cz])

    stair_pts = collections.defaultdict(list)
    for e in ents:
        if g(e["pairs"], 8, "") != L_STAIR: continue
        for s in seg_of(e, sc):
            if in_main(*s, bounds): stair_pts[round((s[0]+s[2])/2)].append(s)

    furniture = []
    for e in ents:
        if e["type"] != "LWPOLYLINE" or g(e["pairs"], 8, "") not in L_FURNITURE: continue
        if not any(c == 70 and v == "1" for c, v in e["pairs"]): continue
        verts, x = [], None
        for c, v in e["pairs"]:
            if c == 10: x = float(v)
            elif c == 20 and x is not None: verts.append(sc(x, float(v))); x = None
        if len(verts) < 3: continue
        xs = [p[0] for p in verts]; zs = [p[1] for p in verts]
        cx, cz = round(sum(xs)/len(xs), 2), round(sum(zs)/len(zs), 2)
        if not in_main(cx, cz, cx, cz, bounds): continue
        w = round(max(xs)-min(xs), 2); d = round(max(zs)-min(zs), 2)
        if max(w, d) > 6: continue
        furniture.append([cx, cz, min(w, d), max(w, d), 0 if w >= d else 90])

    labels = []
    for e in ents:
        if e["type"] not in ("TEXT", "MTEXT"): continue
        if g(e["pairs"], 8, "") not in (L_SPACE, L_PUBTEXT): continue
        content = g(e["pairs"], 1, "")
        x, y = g(e["pairs"], 10), g(e["pairs"], 20)
        if content and x is not None:
            lx, lz = sc(x, y)
            if in_main(lx, lz, lx, lz, bounds): labels.append([content, lx, lz])

    stairs = []
    for segs in stair_pts.values():
        xs = [v for s in segs for v in (s[0], s[2])]
        zs = [v for s in segs for v in (s[1], s[3])]
        stairs.append([round(min(xs), 2), round(min(zs), 2), round(max(xs), 2), round(max(zs), 2)])
    # 合并相邻碎片（同一楼梯间的踏步线被按 x 中值拆成多组）
    stairs.sort()
    merged = []
    for b in stairs:
        if merged and b[0] - merged[-1][2] <= 2.0 and max(merged[-1][1], b[1]) - min(merged[-1][3], b[3]) <= 1.0:
            merged[-1] = [merged[-1][0], min(merged[-1][1], b[1]), max(merged[-1][2], b[2]), max(merged[-1][3], b[3])]
        else:
            merged.append(b[:])
    stairs = merged

    return {
        "walls": [[round(v, 2) for v in s] for s in wall_all],
        "windows": windows, "doors": doors, "columns": columns,
        "stairs": stairs, "furniture": furniture, "room_labels": labels,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dxf")
    ap.add_argument("--origin", default="0,0", help="原点偏移（米），如 203,11")
    ap.add_argument("--mirror", default="z", choices=["z", "none"])
    ap.add_argument("--bounds", default="0,0,100,60", help="主图范围 x0,z0,x1,z1（米）")
    ap.add_argument("--out", default="./out")
    a = ap.parse_args()
    ox, oy = [float(v) for v in a.origin.split(",")]
    bounds = [float(v) for v in a.bounds.split(",")]
    data = extract(a.dxf, (ox, oy), a.mirror, bounds)
    import os
    os.makedirs(a.out, exist_ok=True)
    for k, v in data.items():
        json.dump(v, open(os.path.join(a.out, f"{k}.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
        print(f"{k}: {len(v)}")
    print("注意：房间边界请用 flood-fill 提取（见 SKILL.md 技术点3），本脚本不含房间轮廓推断")


if __name__ == "__main__":
    main()
