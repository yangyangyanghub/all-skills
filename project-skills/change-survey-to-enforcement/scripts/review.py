# 审核意见输出：屏幕显示（Markdown 文本）
import argparse
import json
import os


def render_one(r):
  lines = []
  lines.append(f"### 图斑 {r['id']}")
  lines.append("")
  lines.append(f"- **规则判定**：{r['expected']['top']}"
               + (f" · {r['expected']['category']}" if r['expected'].get('category') else "")
               + f"  （规则 `{r['expected']['ruleId']}`）")
  lines.append(f"- **县级填报**：{r['filled']['top'] or '（未填报）'}"
               + (f" · {r['filled']['category']}" if r['filled'].get('category') else ""))
  if not r["filled"]["top"]:
    lines.append("- **一致性**：⚪ 县级尚未填报，无对比")
  elif r["consistent"]:
    lines.append("- **一致性**：✅ 一致")
  else:
    lines.append("- **一致性**：🔴 **不一致，需复核**")
  if r["suspicious"]:
    lines.append("- **存疑**：⚠️ 规则无法确定，需人工判定")
  if r.get("note"):
    lines.append(f"- **说明**：{r['note']}")
  lines.append(f"- **依据**：{r['basis']}")
  ev = r.get("evidence", {})
  if ev.get("required"):
    lines.append("- **举证要求**：")
    for item in ev["required"]:
      mark = "✅" if item in ev.get("have", []) else "❌"
      lines.append(f"    - {mark} {item}")
  if ev.get("missingFields"):
    lines.append("- **违法类必填要素缺失**：" + "、".join(ev["missingFields"]))
  return "\n".join(lines)


def render_summary(results):
  total = len(results)
  unfilled = [r for r in results if not r["filled"]["top"]]
  mismatch = [r for r in results if not r["consistent"] and r["filled"]["top"]]
  suspicious = [r for r in results if r["suspicious"]]
  by_top = {}
  for r in results:
    t = r["expected"]["top"]
    by_top[t] = by_top.get(t, 0) + 1
  lines = ["## 审核汇总", ""]
  lines.append(f"- 图斑总数：**{total}**")
  lines.append(f"- 与填报不一致：**{len(mismatch)}**")
  lines.append(f"- 县级未填报：**{len(unfilled)}**")
  lines.append(f"- 存疑待人工：**{len(suspicious)}**")
  lines.append("")
  lines.append("| 规则判定类别 | 数量 |")
  lines.append("|---|---|")
  for t, n in sorted(by_top.items(), key=lambda x: -x[1]):
    lines.append(f"| {t} | {n} |")
  return "\n".join(lines)


def main():
  ap = argparse.ArgumentParser(description="审核意见输出")
  ap.add_argument("results", help="判定结果 JSON（judge.py 产出）")
  ap.add_argument("--id", help="只显示指定线索编号")
  ap.add_argument("--only-mismatch", action="store_true", help="只显示不一致的")
  args = ap.parse_args()
  with open(args.results, encoding="utf-8") as f:
    results = json.load(f)
  if args.id:
    results = [r for r in results if r["id"] == args.id]
  if args.only_mismatch:
    results = [r for r in results if not r["consistent"] and r["filled"]["top"]]
  print(render_summary(results))
  print()
  for r in results:
    print(render_one(r))
    print()


if __name__ == "__main__":
  main()
