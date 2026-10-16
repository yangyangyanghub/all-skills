#!/usr/bin/env python3
"""工程类七专业收费估算脚本（eng-cost-estimate skill）

依据各专业收费锚点（2002 勘察设计标准 / 670 号监理文 / 中规协 2004 / 湘粤国空计费）
+ 市场行情区间，生成"锚点价 + 市场浮动 + 校验"报价测算表（markdown）。

用法:
    python calc_eng_fee.py <input.json> [-o output.md]

通用输入字段:
    project       项目名称（必需）
    profession    surveying|supervision|design|landscape|detail_plan|spatial_plan|master_plan（必需）
    params        各专业参数（见下）
    discount      市场折扣（如 0.8），缺省不打折、仅输出锚点价与市场区间
    notes         口径说明（可选）

各专业 params:
    surveying     items: [{type, qty, difficulty?}]
                  type 键见 FEE_SURVEYING（topo_drone_1500/ortho_05_flat/house_residential/cadastral...）
    supervision   investment(万元), complexity(0.85|1.0|1.15, 默认1.0), profession_coef(默认1.0)
    design        investment(万元), profession_coef(默认1.0 建筑/市政), complexity(默认1.0)
    landscape     mode="unit": area_m2 + land_type；mode="pct": cost(万元) + pct
    detail_plan   subtype("kx"|"xg_juzhu"|"xg_yiban"|"xg_zhongdian"), area_ha(公顷)
    spatial_plan  level="county": area_km2
                  level="township": mode("alone"|"merged"), area_km2(alone) 或 count(merged)
                  level="village": village_type("重点村"|"一般村"|"通则式"), population(人), count(默认1)
    master_plan   population_wan(万人)
"""

import json
import argparse
import sys
from pathlib import Path

# ---- 基价表（万元）----
TBL_670 = [(500, 16.5), (1000, 30.1), (3000, 78.1), (5000, 120.8), (8000, 181.0),
           (10000, 218.6), (20000, 393.4), (40000, 708.2), (60000, 991.4),
           (80000, 1255.8), (100000, 1507.0), (200000, 2712.5), (400000, 4882.6),
           (600000, 6835.6), (800000, 8658.4), (1000000, 10390.1)]

TBL_2002 = [(200, 9.0), (500, 20.9), (1000, 38.8), (3000, 103.8), (5000, 163.9),
            (8000, 249.6), (10000, 304.8), (20000, 566.8), (40000, 1054.0),
            (60000, 1515.2), (100000, 2393.4), (200000, 4450.8)]

# 中设协 2024 建筑设计成本底线（万元）
TBL_COST = [(200, 10.4), (500, 24.0), (1000, 44.6), (3000, 119.4), (5000, 188.5),
            (10000, 335.3), (20000, 623.5), (100000, 2632.7)]

# 测绘市场单价（元）
FEE_SURVEYING = {
    "drone_mobilization": (1050, "元/次", "无人机航飞出工按次参考(挂网600-1500中值,低配,不含DLG成图;小面积按此起步价计)"),
    "topo_field_1500": (11390.33, "元/幅", "全野外地形数据采集1:500(财建2009-17号Ⅱ类;1幅=0.0625km²,不足1幅按1幅)"),
    "topo_field_11000": (28906.07, "元/幅", "全野外地形数据采集1:1000(财建2009-17号Ⅱ类;1幅=0.25km²)"),
    "topo_field_12000": (38899.39, "元/幅", "全野外地形数据采集1:2000(财建2009-17号Ⅱ类;1幅=1km²)"),
    "topo_drone_1500": (25000, "元/km²", "无人机航测地形图 1:500"),
    "topo_drone_11000": (6500, "元/km²", "无人机航测地形图 1:1000"),
    "topo_drone_12000": (4000, "元/km²", "无人机航测地形图 1:2000"),
    "ortho_05_flat": (1500, "元/km²", "正射影像0.5m平原(1200-1800中值)"),
    "ortho_05_hill": (2400, "元/km²", "正射影像0.5m丘陵(2000-2800中值)"),
    "ortho_05_mount": (3750, "元/km²", "正射影像0.5m山地(3000-4500中值)"),
    "tilting_3d": (8500, "元/km²", "倾斜摄影三维建模5cm(7000-10000中值)"),
    "house_residential": (1.36, "元/m²", "房产测绘-住宅"),
    "house_commercial": (2.04, "元/m²", "房产测绘-商业"),
    "house_mixed": (2.72, "元/m²", "房产测绘-综合楼"),
    "cadastral": (0.2, "元/m²", "地籍测绘(0.1-0.3中值)"),
}

# 景观单价（元/m²）
FEE_LANDSCAPE = {
    "eco_green": (3, 8, "风景林/生态绿地"), "suburban_park": (8, 15, "郊区公园"),
    "city_park": (18, 35, "城市公园"), "city_square": (28, 56, "城市广场"),
    "residential_high": (45, 75, "居住区(高)"), "residential_mid": (20, 45, "居住区(中)"),
    "residential_low": (10, 20, "居住区(一般)"), "road_green": (6, 10, "道路绿化"),
    "road_landscape": (12, 25, "道路综合景观"), "campus": (15, 20, "校园"),
    "factory": (12, 22, "厂区/工业园"),
}

# 控规地段单价（元/公顷）
KX_PRICE = {"新区/开发区": 2500, "一般地段": 3000, "重点地段": 3500}
# 修规阶梯（元/公顷）：面积上限 → 单价
XG_TABLE = {
    "xg_juzhu": [(3, 20000), (10, 15000), (20, 12000), (30, 10000), (50, 9000), (float("inf"), 8000)],
    "xg_yiban": [(3, 20000), (10, 18000), (20, 15000), (30, 12000), (50, 10000), (float("inf"), 9000)],
}
XG_ZHONGDIAN = (16000, 18000)  # 重点地段区间


def interp(amount, table):
    """分档直线内插；低于表首线性折减；高于表尾按表尾费率外推"""
    lo_a, lo_b = table[0]
    hi_a, hi_b = table[-1]
    if amount <= lo_a:
        return round(lo_b * amount / lo_a, 1), "低于表首按比例折减"
    if amount >= hi_a:
        tail_rate = hi_b / hi_a
        return round(amount * tail_rate, 1), "超表尾按费率外推"
    for i in range(len(table) - 1):
        a1, b1 = table[i]
        a2, b2 = table[i + 1]
        if a1 <= amount <= a2:
            v = b1 + (amount - a1) / (a2 - a1) * (b2 - b1)
            return round(v, 1), f"{a1}-{a2}万档内插"


def w(v):
    return f"{v:,.1f}"


def run_surveying(p, cfg):
    L = ["| 项目类型 | 规模 | 困难系数 | 单价 | 金额（元） |", "|------|:---:|:---:|:---:|:---:|"]
    total = 0.0
    for it in p.get("items", []):
        price, unit, desc = FEE_SURVEYING[it["type"]]
        qty = float(it["qty"])
        diff = float(it.get("difficulty", 1.0))
        amt = price * qty * diff
        total += amt
        L.append(f"| {desc} | {qty:g} | {diff:g} | {price:g} {unit} | {amt:,.0f} |")
    L.append(f"| | **合计** | | | **{total:,.0f} 元 ≈ {total / 10000:,.1f} 万** |")
    note = "市场单价来源：2024-2025 调研（izfc.cn 挂网价、广元市自然资源局公示、2002 年《测绘工程产品价格》房产部分）"
    return total / 10000, L, note


def run_supervision(p, cfg):
    inv = float(p["investment"])
    cx = float(p.get("complexity", 1.0))
    pc = float(p.get("profession_coef", 1.0))
    base, interp_note = interp(inv, TBL_670)
    anchor = base * cx * pc
    L = [f"- 概算投资额：{inv:,.0f} 万元（基价内插：{interp_note}）",
         f"- 基价 {base} 万 × 复杂系数 {cx:g} × 专业系数 {pc:g} = **锚点价 {anchor:,.1f} 万元**",
         "",
         "| 概算区间 | 市场参考费率 | 对应金额 |",
         "|------|:---:|:---:|"]
    bands = [(500, 2.5, None), (1000, 1.9, 2.5), (5000, 1.3, 1.9), (10000, 1.1, 1.3),
             (50000, 0.7, 1.1), (100000, 0.5, 0.7)]
    for lo, rlo, rhi in bands:
        if inv <= lo:
            rhi = rlo if rhi is None else rhi
            L.append(f"| ≤{lo:,} 万 | {rlo}%~{rhi}% | {inv * rlo / 100:,.1f} ~ {inv * rhi / 100:,.1f} 万 |")
            break
    disc = cfg.get("discount")
    extra = ""
    if disc:
        extra = f"；折扣后 {anchor * disc:,.1f} 万（{disc:.0%}）"
    L.append("")
    L.append(f"锚点价依据 670 号基价表（已废止·锚点），市场成交常下浮 10-30%{extra}。")
    return anchor, L, "锚点：发改价格〔2007〕670号基价表（已废止·行业锚点）；市场区间：2024-2025 调研"


def run_design(p, cfg):
    inv = float(p["investment"])
    cx = float(p.get("complexity", 1.0))
    pc = float(p.get("profession_coef", 1.0))
    base, interp_note = interp(inv, TBL_2002)
    anchor = base * cx * pc
    cost, _ = interp(inv, TBL_COST)
    cost_adj = cost * cx
    L = [f"- 概算投资额：{inv:,.0f} 万元（基价内插：{interp_note}）",
         f"- 基价 {base} 万 × 专业系数 {pc:g} × 复杂系数 {cx:g} = **锚点价 {anchor:,.1f} 万元**",
         f"- 中设协 2024 成本底线：{cost} 万 × 复杂系数 = **{cost_adj:,.1f} 万（报价不低于此线）**",
         "",
         f"市场行情：住宅全专业 15-50 元/m²（低价竞争 6.5-10）；公建 25-80 元/m²。"]
    warn = ""
    if anchor < cost_adj:
        warn = f"\n\n⚠️ 锚点价 {anchor:,.1f} 万低于成本底线 {cost_adj:,.1f} 万——按红线须向用户警示。"
    return anchor, L, "锚点：计价格〔2002〕10号基价表（已废止·行业锚点）+ 中设协 2024 成本基准" + warn


def run_landscape(p, cfg):
    if p.get("mode") == "pct":
        cost = float(p["cost"])
        pct = p["pct"]
        lo, hi = pct if isinstance(pct, list) else (pct, pct)
        amt_lo, amt_hi = cost * lo / 100, cost * hi / 100
        mid = (amt_lo + amt_hi) / 2
        L = [f"- 景观工程造价 {cost:,.0f} 万 × {lo}%~{hi}%",
             f"- 金额区间：**{amt_lo:,.1f} ~ {amt_hi:,.1f} 万元**（中值 {mid:,.1f} 万）"]
        return mid, L, "造价百分比参考：构筑物 5-10%/水景 6-12%/照明 8-16%（2018 指导意见）"
    area = float(p["area_m2"])
    lt = p["land_type"]
    lo, hi, desc = FEE_LANDSCAPE[lt]
    amt_lo, amt_hi = area * lo / 10000, area * hi / 10000
    mid = (amt_lo + amt_hi) / 2
    L = [f"- 景观面积 {area:,.0f} m²（{desc}，单价 {lo}-{hi} 元/m²）",
         f"- 金额区间：**{amt_lo:,.1f} ~ {amt_hi:,.1f} 万元**（中值 {mid:,.1f} 万）"]
    return mid, L, "单价来源：《园林景观规划设计计费标准指导意见》2018 修订版"


def run_detail_plan(p, cfg):
    sub = p["subtype"]
    area = float(p["area_ha"])
    if sub == "kx":
        district = p.get("district", "一般地段")
        unit = KX_PRICE.get(district, 3000)
        amt = area * unit / 10000 + 10
        L = [f"- 控规 {area:g} 公顷（{district}，{unit} 元/公顷）+ 基价 10 万",
             f"- **金额：{amt:,.1f} 万元**（加分项：分图则 +500 元/公顷、形体示意 +2,000 元/公顷）"]
        return amt, L, "中规协 2004《城市规划设计计费指导意见》；市场执行常为标准 60-100%"
    table = XG_TABLE.get(sub)
    if sub == "xg_zhongdian":
        unit = sum(XG_ZHONGDIAN) / 2
        amt = area * unit / 10000 + 6
        L = [f"- 修规（重点地段/大型公建）{area:g} 公顷 × {unit:,.0f} 元/公顷 + 基价 6 万",
             f"- **金额：{amt:,.1f} 万元**"]
    else:
        unit = next(u for cap, u in table if area <= cap)
        base_fee = 5
        amt = area * unit / 10000 + base_fee
        L = [f"- 修规 {area:g} 公顷 × {unit:,} 元/公顷（面积档）+ 基价 {base_fee} 万",
             f"- **金额：{amt:,.1f} 万元**"]
    return amt, L, "中规协 2004《城市规划设计计费指导意见》；市场执行常为标准 60-100%"


def run_spatial_plan(p, cfg):
    level = p["level"]
    if level == "county":
        area = float(p["area_km2"])
        seg = min(area, 1000) * 3000 + min(max(area - 1000, 0), 2000) * 1000 + max(area - 3000, 0) * 500
        amt = seg / 10000 + 300
        L = [f"- 县域 {area:g} km² 阶梯计费（≤1000km² 3,000 元/km²、1000-3000 1,000、>3000 500）+ 基价 300 万",
             f"- **金额：{amt:,.1f} 万元**（湖南 2025 标准，调节系数 1.1-1.3）"]
        return amt, L, "湘空规会字〔2025〕10号"
    if level == "township":
        if p.get("mode") == "merged":
            cnt = int(p.get("count", 1))
            L = [f"- 乡镇级总规（与市县合并编制）{cnt} 个 × 20-40 万/个（广东 2021）",
                 f"- **金额区间：{cnt * 20} ~ {cnt * 40} 万元**"]
            return cnt * 30, L, "广东 2021 + 湖南 2025（合并按单村 60-80%）"
        area = float(p["area_km2"])
        unit = 0.8 if area <= 30 else (0.4 if area <= 50 else 0.2)
        amt = area * unit + 24
        L = [f"- 乡镇域 {area:g} km² × {unit:g} 万元/km² + 基价 24 万（湖南 2025）",
             f"- **金额：{amt:,.1f} 万元**；河北合并编制参照 20-40 万/个"]
        return amt, L, "湘空规会字〔2025〕10号"
    vt = p.get("village_type", "重点村")
    pop = float(p.get("population", 2000))
    count = int(p.get("count", 1))
    if pop <= 2000:
        std = 20
    elif pop <= 4000:
        std = 25
    elif pop <= 6000:
        std = 30
    else:
        std = 30 + (pop - 6000) / 1000 * 2
    coef = {"重点村": 1.0, "一般村": 0.65, "通则式": 0.25}[vt]
    per = std * coef
    amt = per * count
    L = [f"- {vt}（{pop:,.0f} 人）× {count} 个：标准 {std:g} 万/村 × {coef:g} = **{per:g} 万/村**",
         f"- **合计：{amt:,.1f} 万元**",
         f"- 河北市场对照：重点村 10-20 万、一般村 5-10 万、通则式 3-5 万（招标推算）"]
    return amt, L, "湘空规会字〔2025〕10号 + 河北招标市场价"


def run_master_plan(p, cfg):
    pop = float(p["population_wan"])
    unit = 1.0 if pop <= 50 else (0.8 if pop <= 100 else 0.6)
    amt = pop * unit + 150
    L = [f"- 城市总人口 {pop:g} 万人 × {unit:g} 万元/万人 + 基价 150 万（2004 指导意见）",
         f"- **金额：{amt:,.1f} 万元**（人口分档单价为概化处理，精确分档待验证）"]
    return amt, L, "中规协 2004《城市规划设计计费指导意见》"


RUNNERS = {"surveying": run_surveying, "supervision": run_supervision, "design": run_design,
           "landscape": run_landscape, "detail_plan": run_detail_plan,
           "spatial_plan": run_spatial_plan, "master_plan": run_master_plan}

TITLES = {"surveying": "测绘", "supervision": "工程监理", "design": "建筑/市政工程设计",
          "landscape": "园林景观设计", "detail_plan": "控制性/修建性详细规划",
          "spatial_plan": "国土空间规划编制", "master_plan": "城市总体规划"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("-o", "--output")
    args = ap.parse_args()

    cfg = json.loads(Path(args.input).read_text(encoding="utf-8"))
    prof = cfg["profession"]
    if prof not in RUNNERS:
        print(f"未知 profession: {prof}", file=sys.stderr)
        sys.exit(1)

    anchor, body, basis = RUNNERS[prof](cfg.get("params", {}), cfg)

    disc = cfg.get("discount")
    L = [f"# {cfg['project']} {TITLES[prof]}收费测算", "",
         f"- 计费依据：{basis}",
         f"- **锚点价：{anchor:,.1f} 万元**（标准计算，评审可辩护）"]
    if disc:
        L.append(f"- 折后价：{anchor * disc:,.1f} 万元（{disc:.0%}，市场折扣）")
    L.append("")
    L.extend(body)
    L.append("")
    if cfg.get("notes"):
        L.append(f"> {cfg['notes']}")
        L.append("")

    out = "\n".join(L)
    if args.output:
        Path(args.output).write_text(out + "\n", encoding="utf-8")
        print(f"已生成: {args.output}")
    else:
        print(out)


if __name__ == "__main__":
    main()
