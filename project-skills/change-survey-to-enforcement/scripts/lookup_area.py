# 面积权威查询：给定线索编号，从「套合结果表」查该图斑的权威面积
#
# 用途：审核单个/多个图斑时，面积一律以套合结果表为准（不读系统页面）。
# 背景：系统「套合结果」tab 显示的是**父图斑级**数据，与子图斑填报值不可直接比。
#
# 用法：
#   python lookup_area.py --truth "套合结果.xlsx" --id 130427SJBG26210310_3
#   python lookup_area.py --truth "..." --ids "a,b,c"
#   python lookup_area.py --truth "..." --ids-file ids.txt
#   python lookup_area.py --truth "..." --id xxx --filled "图斑列表.xlsx"   # 同时对比填报值
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from verify_areas import TRUTH_MAP, FILLED_MAP, FIELD_LABEL, load_sheet, build_index  # noqa: E402

DEFAULT_TRUTH = (r"E:\2026卫片执法专项\2026年变更调查\进度\20260914"
                 r"\2026年上半年变更调查新增建设线索处置(1548个)0066910266358979"
                 r"\2026年上半年变更调查新增建设线索处置_1548个__套合结果.xlsx")

EXTRA_COLS = ["变更地类", "平差通过", "县区", "乡镇名称", "村名称"]


def lookup(truth_path, ids, filled_path=None, truth_sheet="套合面积审核表",
           filled_sheet="图斑列表"):
  truth_rows = load_sheet(truth_path, truth_sheet)
  truth = build_index(truth_rows, "图斑标识", TRUTH_MAP)
  extra = {}
  for r in truth_rows:
    k = r.get("图斑标识")
    if k is None:
      continue
    extra[str(k).strip()] = {c: r.get(c) for c in EXTRA_COLS}

  filled = {}
  if filled_path and os.path.exists(filled_path):
    filled = build_index(load_sheet(filled_path, filled_sheet), "线索编号", FILLED_MAP)

  out = []
  for pid in ids:
    t = truth.get(pid)
    if t is None:
      out.append({"id": pid, "found": False})
      continue
    item = {"id": pid, "found": True, "truth": t, "extra": extra.get(pid, {})}
    if filled:
      f = filled.get(pid)
      item["filled"] = f
      if f:
        item["diffs"] = [
          {"field": FIELD_LABEL[k], "filled": f.get(k), "truth": t.get(k),
           "diff": round((f.get(k) or 0) - (t.get(k) or 0), 4)}
          for k in TRUTH_MAP
          if f.get(k) is not None and t.get(k) is not None
          and abs(f[k] - t[k]) > 0.01
        ]
    out.append(item)
  return out


def render(results):
  lines = []
  for r in results:
    lines.append(f"### {r['id']}")
    if not r["found"]:
      lines.append("")
      lines.append("❌ **套合结果表中未找到该图斑**")
      lines.append("")
      continue
    t, e = r["truth"], r.get("extra", {})
    lines.append("")
    lines.append("| 字段 | 套合（权威） |")
    lines.append("|---|---|")
    for k in ["areaMu", "cultivated", "basicFarmland", "nonCultivatedAgri", "unused", "ecoRedline", "construction"]:
      lines.append(f"| {FIELD_LABEL[k]} | {t.get(k)} |")
    for c in EXTRA_COLS:
      if e.get(c) not in (None, ""):
        lines.append(f"| {c} | {e[c]} |")
    if "diffs" in r and r.get("filled"):
      lines.append("")
      if r["diffs"]:
        lines.append("**与填报值差异**：")
        lines.append("")
        lines.append("| 字段 | 填报 | 套合 | 差异 |")
        lines.append("|---|---|---|---|")
        for d in r["diffs"]:
          lines.append(f"| {d['field']} | {d['filled']} | {d['truth']} | {d['diff']} |")
      else:
        lines.append("✅ **面积与填报一致**")
    lines.append("")
  return "\n".join(lines)


def main():
  ap = argparse.ArgumentParser(description="从套合结果表查图斑权威面积")
  ap.add_argument("--truth", default=DEFAULT_TRUTH, help="套合结果表（默认用 20260914 那份）")
  ap.add_argument("--id", help="单个线索编号")
  ap.add_argument("--ids", help="多个线索编号，逗号分隔")
  ap.add_argument("--ids-file", help="线索编号文件（每行一个）")
  ap.add_argument("--filled", help="可选：图斑列表导出表，用于对比填报值")
  ap.add_argument("--truth-sheet", default="套合面积审核表")
  ap.add_argument("--filled-sheet", default="图斑列表")
  ap.add_argument("--json", action="store_true", help="输出 JSON")
  args = ap.parse_args()

  ids = []
  if args.id:
    ids.append(args.id.strip())
  if args.ids:
    ids.extend(x.strip() for x in args.ids.split(",") if x.strip())
  if args.ids_file:
    with open(args.ids_file, encoding="utf-8") as f:
      ids.extend(l.strip() for l in f if l.strip())
  if not ids:
    ap.error("需要 --id 或 --ids 或 --ids-file")

  if not os.path.exists(args.truth):
    print(f"❌ 套合结果表不存在：{args.truth}", file=sys.stderr)
    sys.exit(1)

  results = lookup(args.truth, ids, args.filled, args.truth_sheet, args.filled_sheet)
  if args.json:
    print(json.dumps(results, ensure_ascii=False, indent=2))
  else:
    print(render(results))


if __name__ == "__main__":
  main()
