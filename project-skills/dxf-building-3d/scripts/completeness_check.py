# -*- coding: utf-8 -*-
"""
完整性质检器（全程双向：漏 + 多）—— 墙 / 柱 / 窗 / 门 全覆盖
用法:
  python completeness_check.py <图纸.dxf> <提取数据目录> [--origin X,Y] [--mirror z|none] [--bounds x0,z0,x1,z1] [--tol 0.8]

基准（重要）：<提取数据目录> 必须是"你最终模型"的构件数据——不是本技能提取器自己的输出。
  用自研/更全的提取器时，喂它的输出；且 --origin/--mirror/--bounds 必须与模型坐标系一致，
  否则对账几何全错（症状：几乎全部报"漏"，脚本会自动报警）。

输出：
  ① 图层普查      —— DXF 所有图层 + 实体数（找"应建模却没建"的图层）
  ② 构件双向对账  —— 墙/柱/窗/门 逐类：DXF源 vs 模型，算"漏"(源有模型无) 和 "多"(模型有源无)
      · 漏 = 图纸有、模型没有 → 缺构件
      · 多 = 模型有、图纸没有 → 假构件（如把墙错建成窗）
      · 窗的"多"用强窗(块+WINDOW层线)判定——只靠 SURFACE 线支撑的幕墙段判为可疑假窗
"""
import sys, os, json, math, argparse, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_dxf as X


def load_json(d, name):
    p = os.path.join(d, name)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else []


def dseg(px, pz, x1, z1, x2, z2):
    dx, dz = x2 - x1, z2 - z1
    L2 = dx * dx + dz * dz
    t = ((px - x1) * dx + (pz - z1) * dz) / L2 if L2 > 0 else 0.0
    t = max(0.0, min(1.0, t))
    return math.hypot(px - (x1 + t * dx), pz - (z1 + t * dz))


def min_seg(px, pz, segs):
    m = 999.0
    for s in segs:
        d = dseg(px, pz, s[0], s[1], s[2], s[3])
        if d < m:
            m = d
    return m


def min_pt(px, pz, pts):
    m = 999.0
    for p in pts:
        d = math.hypot(px - p[0], pz - p[1])
        if d < m:
            m = d
    return m


def seg_cov(dxf_segs, model_segs, tol):
    miss = []
    for s in dxf_segs:
        L = math.hypot(s[2] - s[0], s[3] - s[1])
        n = max(2, int(L / 0.3))
        for i in range(n + 1):
            px = s[0] + (s[2] - s[0]) * i / n
            pz = s[1] + (s[3] - s[1]) * i / n
            if min_seg(px, pz, model_segs) > tol:
                miss.append(s)
                break
    extra = []
    for s in model_segs:
        mx, mz = (s[0] + s[2]) / 2, (s[1] + s[3]) / 2
        if min_seg(mx, mz, dxf_segs) > tol:
            extra.append(s)
    return miss, extra


def pt_cov(dxf_pts, model_pts, tol):
    miss = [p for p in dxf_pts if min_pt(p[0], p[1], model_pts) > tol]
    extra = [p for p in model_pts if min_pt(p[0], p[1], dxf_pts) > tol]
    return miss, extra


def _show(tag, segs):
    for s in sorted(segs, key=lambda s: -math.hypot(s[2] - s[0], s[3] - s[1]))[:8]:
        print(f"     {tag} [{[round(v, 2) for v in s]}] len={math.hypot(s[2] - s[0], s[3] - s[1]):.2f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dxf")
    ap.add_argument("data_dir")
    ap.add_argument("--origin", default="0,0")
    ap.add_argument("--mirror", default="z", choices=["z", "none"])
    ap.add_argument("--bounds", default="-100000,-100000,100000,100000")
    ap.add_argument("--tol", type=float, default=0.8)
    a = ap.parse_args()
    ox, oy = [float(v) for v in a.origin.split(",")]
    bounds = [float(v) for v in a.bounds.split(",")]
    ents = X.parse_dxf(a.dxf)
    zmax = X._ymax_m(ents, oy) if a.mirror == "z" else 0.0
    sc = X.make_sc((ox, oy), a.mirror, zmax)

    # ---------- ① 图层普查 ----------
    by = collections.Counter(X.g(e["pairs"], 8, "") for e in ents)
    print("=== ① 图层普查（实体数，降序）===")
    for L, n in by.most_common():
        print(f"  {n:6d}  {L}")

    # ---------- 采 DXF 各类构件 ----------
    dxf_wall, dxf_win, dxf_win_strong, dxf_door, dxf_col = [], [], [], [], []
    for e in ents:
        L = X.g(e["pairs"], 8, ""); t = e["type"]; blk = X.g(e["pairs"], 2, "")
        if L in X.L_WALL:
            for s in X.seg_of(e, sc):
                if X.in_main(*s, bounds) and math.hypot(s[2] - s[0], s[3] - s[1]) >= 0.15:
                    dxf_wall.append(s)
        elif L == X.L_SURFACE and t in ("LINE", "LWPOLYLINE"):
            for s in X.seg_of(e, sc):
                if X.in_main(*s, bounds) and math.hypot(s[2] - s[0], s[3] - s[1]) >= 0.8:
                    dxf_win.append(s)
        elif L == X.L_WINDOW and t in ("LINE", "LWPOLYLINE"):
            for s in X.seg_of(e, sc):
                if X.in_main(*s, bounds) and math.hypot(s[2] - s[0], s[3] - s[1]) >= 0.8:
                    dxf_win.append(s); dxf_win_strong.append(s)
        if t == "INSERT":
            x, y = X.g(e["pairs"], 10), X.g(e["pairs"], 20)
            if x is None:
                continue
            p = sc(x, y)
            if not X.in_main(p[0], p[1], p[0], p[1], bounds):
                continue
            if X.DOOR_BLOCK_KEY in blk:
                dxf_door.append(p)
            elif X.WINDOW_BLOCK_KEY in blk or L == X.L_WINDOW:
                w = max(0.6, min(abs(float(X.g(e["pairs"], 41, "1800"))) / 1000.0, 8.0))
                s = [p[0] - w / 2, p[1], p[0] + w / 2, p[1]]
                dxf_win.append(s); dxf_win_strong.append(s)
            elif L == X.L_COLUMN:
                dxf_col.append(p)

    m_wall = load_json(a.data_dir, "walls.json")
    m_win = [[w["a"], w["y"], w["b"], w["y"]] if w.get("axis") == "x" else [w["x"], w["a"], w["x"], w["b"]]
             for w in load_json(a.data_dir, "windows.json")]
    m_door = [[d[0], d[1]] for d in load_json(a.data_dir, "doors.json")]
    m_col = [[c[0], c[1]] for c in load_json(a.data_dir, "columns.json")]

    # ---------- ② 构件双向对账 ----------
    print("\n=== ② 构件双向对账（漏=图纸有模型无；多=模型有图纸无）===")
    wm, we = seg_cov(dxf_wall, m_wall, 0.4)
    print(f"  墙  DXF={len(dxf_wall):4d} 模型={len(m_wall):4d}   漏={len(wm):3d}  多={len(we):3d}")
    _show("漏墙", wm); _show("多墙", we)

    wim, _ = seg_cov(dxf_win, m_win, a.tol)
    _, wie_strong = seg_cov(dxf_win_strong, m_win, 1.5)
    print(f"  窗  DXF={len(dxf_win):4d} 模型={len(m_win):4d}   漏={len(wim):3d}  多(仅SURFACE支撑)={len(wie_strong):3d}")
    _show("漏窗", wim); _show("假窗", wie_strong)

    colmiss, colex = pt_cov(dxf_col, m_col, 1.0)
    print(f"  柱  DXF={len(dxf_col):4d} 模型={len(m_col):4d}   漏={len(colmiss):3d}  多={len(colex):3d}")

    dmiss, dex = pt_cov(dxf_door, m_door, 1.0)
    print(f"  门  DXF={len(dxf_door):4d} 模型={len(m_door):4d}   漏={len(dmiss):3d}  多={len(dex):3d}")

    # 坐标对齐自检
    if dxf_wall and len(wm) >= len(dxf_wall) * 0.9:
        print("\n  ⚠️ 墙几乎全部报'漏' → 基准数据与图纸坐标系不一致（--origin/--mirror/--bounds 没对齐），先对齐再解读！")
    print("\n判据：墙/柱/窗/门 四类的「漏」都应为 0；「多」为 0（或逐条确认是刻意取舍）。")


if __name__ == "__main__":
    main()
