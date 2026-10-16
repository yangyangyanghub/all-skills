#!/usr/bin/env python3
"""软件开发预算测算脚本（sw-cost-estimate skill）

依据 GB/T 36964-2018 + CSBMK®-202510 城市基准费率，生成预算测算明细表。
算术全部由本脚本完成，输出 markdown 表格（含换算过程列与合计校验）。

支持三种计费方法（method 字段）:
    personmonth  人月法：人月 × 人月单价（默认；模块给 personmonths 或 fp 换算）
    fp_unit      功能点单价法：调整后功能点 × 功能点单价（山东/北京评审口径）
                 单价 = CSBMK 北京基准 1243.52 元/FP × 城市系数（城市人月费率/北京人月费率）

用法:
    python calc_budget.py <input.json> [-o output.md]

输入 JSON 字段:
    project       项目名称（必需）
    city          城市名（必需，用于查 CSBMK 城市费率；支持别名映射）
    method        "personmonth"（默认）| "fp_unit"
    rate_mode     "auto"=按城市基准（默认）；"custom"=用 rate_override
    rate_override 元/人月（rate_mode=custom 时生效）
    cf            规模变更因子（fp_unit 模式用：概算 1.39 / 投标 1.21 / 需求分析 1.10 / 交付 1.00，默认 1.39）
    pdr           生产率，人时/功能点（默认 6.41 = CSBMK 202510 电子政务 P50）
    hm            人月折算系数（默认 176）
    modules       模块清单，每项:
                    name          模块名（必需）
                    role          角色列文本（可选）
                    work          工作内容列文本（可选）
                    personmonths  人月数（personmonth 模式，与 fp 二选一）
                    fp            估算功能点（必需，fp_unit 模式；personmonth 模式配合 re）
                    re            复用度: "1"|"2/3"|"1/3"（fp 模式下必需，默认 "1"）
    sections_note 口径说明文字（可选，输出在表尾）
"""

import json
import argparse
import sys
from pathlib import Path

# CSBMK®-202510 表 4.7 城市软件开发基准人月费率（元/人月，P50，含利润含税）
CITY_RATES = {
    "北京": (32198, "A"), "上海": (31309, "A"), "深圳": (32122, "A"),
    "广州": (27748, "B"), "杭州": (28813, "B"), "南京": (27795, "B"),
    "苏州": (27471, "B"), "宁波": (26241, "B"), "福州": (26586, "B"),
    "厦门": (26823, "B"), "成都": (26112, "B"), "西安": (25415, "B"),
    "济南": (23339, "C"), "青岛": (24085, "C"), "重庆": (23849, "C"),
    "武汉": (23806, "C"), "长沙": (23292, "C"), "合肥": (24881, "C"),
    "昆明": (23635, "C"), "天津": (24641, "C"), "太原": (22920, "C"),
    "南昌": (23296, "C"), "南宁": (22659, "C"), "海口": (22963, "C"),
    "贵阳": (23155, "C"), "沈阳": (22752, "C"), "大连": (23216, "C"),
    "哈尔滨": (22614, "C"), "拉萨": (23919, "C"),
    "石家庄": (20410, "D"), "郑州": (21836, "D"), "兰州": (20923, "D"),
    "长春": (20954, "D"), "乌鲁木齐": (20495, "D"), "西宁": (20746, "D"),
    "呼和浩特": (19883, "E"), "银川": (19234, "E"),
}

# CSBMK®-202510 4.6.1 功能点单价基准（北京，元/功能点）
BJ_FP_PRICE = 1243.52
BJ_RATE = CITY_RATES["北京"][0]

# 城市别名 → 基准对标城市（非省会地级市对标本省省会或同类别最近城市）
CITY_ALIAS = {
    "邯郸": "石家庄", "保定": "石家庄", "唐山": "石家庄", "秦皇岛": "石家庄",
    "邢台": "石家庄", "张家口": "石家庄", "承德": "石家庄", "沧州": "石家庄",
    "廊坊": "石家庄", "衡水": "石家庄", "雄安": "石家庄",
    "洛阳": "郑州", "开封": "郑州", "新乡": "郑州", "安阳": "郑州",
    "聊城": "济南", "德州": "济南", "菏泽": "济南", "济宁": "济南",
    "临汾": "太原", "运城": "太原",
}

RE_MAP = {"1": 1.0, "1.0": 1.0, "低": 1.0, "2/3": 2 / 3, "中": 2 / 3, "1/3": 1 / 3, "高": 1 / 3}


def resolve_rate(cfg: dict):
    """返回 (rate元/人月, rate说明文本)"""
    if cfg.get("rate_mode") == "custom" and cfg.get("rate_override"):
        return float(cfg["rate_override"]), f"用户指定值（建议取值，报审前按 CSBMK 基准校准）"
    city = cfg.get("city", "")
    base = CITY_ALIAS.get(city, city)
    if base in CITY_RATES:
        rate, cat = CITY_RATES[base]
        note = f"CSBMK®-202510 {base}（{cat} 类城市）基准 20410 元/人月（P50）" if rate == 20410 else \
               f"CSBMK®-202510 {base}（{cat} 类城市）基准 {rate} 元/人月（P50）"
        return rate, note
    if city in CITY_RATES:
        rate, cat = CITY_RATES[city]
        return rate, f"CSBMK®-202510 {city}（{cat} 类城市）基准 {rate} 元/人月（P50）"
    # 未匹配：用同类别无法确定时取 D 类均值并警示
    print(f"[警告] 城市「{city}」不在 CSBMK 202510 城市表内，已用 D 类城市均值 20894 元/人月，请在测算表假设节注明。", file=sys.stderr)
    return 20894.0, f"CSBMK®-202510 D 类城市均值 20894 元/人月（P50）；{city} 未在列，取同类别均值"


def pm_from_fp(fp: float, re_str: str, pdr: float, hm: int) -> tuple:
    """功能点→人月，返回 (人月原始值, 换算过程文本)"""
    re_val = RE_MAP.get(str(re_str), 1.0)
    raw = fp * re_val * pdr / hm
    expr = f"{fp:g}×{re_str}×{pdr:g}÷{hm}≈{raw:.2f}"
    return raw, expr


def round_pm(raw: float) -> float:
    """按 0.25 人月粒度取整"""
    return round(raw * 4) / 4


def resolve_fp_price(city: str, rate_override=None) -> tuple:
    """功能点单价法：返回 (单价元/FP, 说明文本)。单价 = 北京基准 1243.52 × 城市人月费率/北京人月费率"""
    base = CITY_ALIAS.get(city, city)
    if base in CITY_RATES:
        rate, cat = CITY_RATES[base]
    elif city in CITY_RATES:
        rate, cat = CITY_RATES[city]
    else:
        rate, cat = 20894, "D"
    price = BJ_FP_PRICE * rate / BJ_RATE
    if rate_override:
        price = BJ_FP_PRICE * float(rate_override) / BJ_RATE
        return price, f"北京基准 {BJ_FP_PRICE} 元/FP × 指定人月费率折算"
    return price, f"北京基准 {BJ_FP_PRICE} 元/FP × 城市系数（{base} {rate}/北京 {BJ_RATE} = {rate / BJ_RATE:.4f}），{base} 为 {cat} 类城市"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="输入 JSON 文件")
    ap.add_argument("-o", "--output", help="输出 markdown 文件（缺省打印到 stdout）")
    args = ap.parse_args()

    cfg = json.loads(Path(args.input).read_text(encoding="utf-8"))
    method = cfg.get("method", "personmonth")
    if method == "fp_unit":
        out = run_fp_unit(cfg)
    else:
        out = run_personmonth(cfg)

    if args.output:
        Path(args.output).write_text(out + "\n", encoding="utf-8")
        print(f"已生成: {args.output}")
    else:
        print(out)


def run_fp_unit(cfg: dict) -> str:
    project = cfg["project"]
    cf = float(cfg.get("cf", 1.39))
    fp_price, price_note = resolve_fp_price(cfg.get("city", ""), cfg.get("rate_override"))

    L = []
    L.append(f"# {project} 软件开发费功能点单价法测算明细")
    L.append("")
    L.append(f"- 功能点单价：{fp_price:,.2f} 元/功能点（{price_note}）")
    L.append(f"- 规模变更因子：{cf:g}（CSBMK®-202510：概算/预算 1.39、投标/计划 1.21、需求分析 1.10、交付 1.00）")
    L.append(f"- 费用公式：调整后功能点 × 复用度调整 × 规模变更因子 × 功能点单价")
    L.append("")
    L.append("| 序号 | 模块 | 工作内容 | 功能点 | 复用度 | 调整后功能点 | 金额（万元） |")
    L.append("|:---:|------|------------|:---:|:---:|:---:|:---:|")
    total_fp = total_amt = 0.0
    idx = 0
    for m in cfg.get("modules", []):
        idx += 1
        fp = float(m["fp"])
        re_val = RE_MAP.get(str(m.get("re", "1")), 1.0)
        adj = fp * re_val * cf
        amt = round(adj * fp_price / 10000, 1)
        total_fp += adj
        total_amt += amt
        L.append(f"| {idx} | {m['name']} | {m.get('work', '')} | {fp:g} | {m.get('re', '1')} | {adj:,.1f} | {amt:g} |")
    L.append(f"| | **合计** | | | | **{total_fp:,.1f}** | **{total_amt:g}** |")
    L.append("")
    if cfg.get("sections_note"):
        L.append(f"> {cfg['sections_note']}")
        L.append("")
    L.append(f"**校验**：调整后功能点 {total_fp:,.1f} FP × 单价 {fp_price:,.2f} 元 × 因子已含 = {total_fp * fp_price / 10000:,.1f} 万元，与分项合计 {total_amt:g} 万元{'一致' if abs(total_fp * fp_price / 10000 - total_amt) < 0.15 else '不一致！请检查'}。")
    return "\n".join(L)


def run_personmonth(cfg: dict) -> str:
    project = cfg["project"]
    pdr = float(cfg.get("pdr", 6.41))
    hm = int(cfg.get("hm", 176))
    rate, rate_note = resolve_rate(cfg)

    rows = []  # (序号, 名称, 内容, 角色, 人月, 金额, 换算备注)
    subtotal_groups = []

    for m in cfg.get("modules", []):
        name, role, work = m["name"], m.get("role", ""), m.get("work", "")
        if "sub_items" in m:
            grp_pm = 0.0
            lines = []
            for sub in m["sub_items"]:
                raw, expr = pm_from_fp(sub["fp"], sub.get("re", "1"), pdr, hm)
                per = round_pm(raw)
                cnt = sub["count"]
                pm = round(per * cnt, 2)
                grp_pm += pm
                lines.append((sub["name"], cnt, sub["fp"], expr, per, pm))
            amount = round(grp_pm * rate / 10000, 1)
            detail = "；".join(f"{n}{c}个({fp}FP→{per:g}人月/个)" for n, c, fp, e, per, pm in lines)
            rows.append(("sub", name, detail, role, grp_pm, amount, ""))
            for n, c, fp, e, per, pm in lines:
                pass
            subtotal_groups.append((name, grp_pm, amount, lines))
        else:
            if "personmonths" in m:
                pm = float(m["personmonths"])
                expr = "工作量给定"
            else:
                raw, expr = pm_from_fp(m["fp"], m.get("re", "1"), pdr, hm)
                pm = round_pm(raw)
            amount = round(pm * rate / 10000, 1)
            rows.append(("mod", name, work, role, pm, amount, expr))

    total_pm = round(sum(r[4] for r in rows), 2)
    total_amt = round(sum(r[5] for r in rows), 1)

    L = []
    L.append(f"# {project} 软件开发费人月法测算明细")
    L.append("")
    L.append(f"- 人月单价：{rate:,.0f} 元/人月（{rate_note}）")
    L.append(f"- 生产率：{pdr:g} 人时/功能点（CSBMK®-202510 电子政务 P50）")
    L.append(f"- 人月折算系数：{hm} 人时/月；复用度：高 1/3、中 2/3、低 1")
    L.append("")
    L.append("| 序号 | 板块 | 主要工作内容 | 角色 | 人月 | 金额（万元） |")
    L.append("|:---:|------|------------|------|:---:|:---:|")
    idx = 0
    for kind, name, work, role, pm, amount, expr in rows:
        idx += 1
        L.append(f"| {idx} | {name} | {work} | {role} | {pm:g} | {amount:g} |")
    L.append(f"| | **合计** | | | **{total_pm:g}** | **{total_amt:g}** |")
    L.append("")
    if cfg.get("sections_note"):
        L.append(f"> {cfg['sections_note']}")
        L.append("")
    L.append(f"**校验**：合计人月 {total_pm:g} × 单价 {rate:,.0f} 元 = {total_pm * rate / 10000:,.1f} 万元，与分项合计 {total_amt:g} 万元{'一致' if abs(total_pm * rate / 10000 - total_amt) < 0.15 else '不一致！请检查'}。")

    return "\n".join(L)


if __name__ == "__main__":
    main()
