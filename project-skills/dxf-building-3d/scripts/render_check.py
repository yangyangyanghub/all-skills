# -*- coding: utf-8 -*-
"""
2D 核对图生成器（验证提取结果是否与图纸一致）
用法: python render_check.py <提取数据目录> [--out 核对图.png]

读 walls.json / windows.json / doors.json（extract_dxf.py 的输出），画：
  灰线=墙线  蓝线=窗玻璃段  红/绿线=门板朝向  数字=门rot
人可直接目检：构件是否沿墙、方向是否正确（这是目录 SKILL.md 验证清单的最终判据）
"""
import json, math, os, argparse
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False


def load(d, name):
    p = os.path.join(d, name)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data_dir")
    ap.add_argument("--out", default="check.png")
    a = ap.parse_args()
    walls = load(a.data_dir, "walls.json")
    windows = load(a.data_dir, "windows.json")
    doors = load(a.data_dir, "doors.json")
    columns = load(a.data_dir, "columns.json")
    furniture = load(a.data_dir, "furniture.json")

    fig, ax = plt.subplots(figsize=(30, 20), dpi=100)
    for w in walls:
        ax.plot([w[0], w[2]], [w[1], w[3]], color="#AAA", lw=1.2, zorder=1)
    for c in columns:
        ax.add_patch(plt.Rectangle((c[0]-0.28, c[1]-0.28), 0.56, 0.56, facecolor="#8A8D90", zorder=3))
    for f in furniture:
        w, d = f[2], f[3]
        if f[4] % 180 == 0:
            ax.add_patch(plt.Rectangle((f[0]-w/2, f[1]-d/2), w, d, facecolor="#E8E2D6", edgecolor="#BBB", zorder=2))
        else:
            ax.add_patch(plt.Rectangle((f[0]-d/2, f[1]-w/2), d, w, facecolor="#E8E2D6", edgecolor="#BBB", zorder=2))
    for b in windows:
        if b["axis"] == "x":
            ax.plot([b["a"], b["b"]], [b["y"], b["y"]], color="#1A5FB4", lw=5, zorder=4, solid_capstyle="butt")
        else:
            ax.plot([b["x"], b["x"]], [b["a"], b["b"]], color="#1A5FB4", lw=5, zorder=4, solid_capstyle="butt")
    for dr in doors:
        x, z, rot, w = dr
        # 门朝向：rot % 180 == 0 → 门在竖墙（沿 z）；否则沿 x
        if int(rot) % 180 == 0:
            ax.plot([x, x], [z-w/2, z+w/2], color="#1A7A1A", lw=5, zorder=5, solid_capstyle="butt")
        else:
            ax.plot([x-w/2, x+w/2], [z, z], color="#1A7A1A", lw=5, zorder=5, solid_capstyle="butt")
        ax.text(x, z+0.5, f"{rot:.0f}", fontsize=6, color="#555", ha="center", zorder=6)

    ax.set_aspect("equal"); ax.axis("off")
    ax.set_title("核对图：灰=墙 蓝=窗 绿=门板朝向（应沿墙）", fontsize=16)
    plt.savefig(a.out, bbox_inches="tight", facecolor="#FAFAF7")
    print("saved", a.out)


if __name__ == "__main__":
    main()
