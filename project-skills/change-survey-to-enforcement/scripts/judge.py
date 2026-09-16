# 判定引擎：规则匹配（确定性） + 一致性校验 + 举证核查
# 设计原则：只输出「应该是哪类」和「举证缺什么」，绝不下「违法/合法」定性结论
import argparse
import json
import os


def load_rules(dict_path):
  with open(dict_path, encoding="utf-8") as f:
    return json.load(f)


def _rule_by_id(rules, rule_id):
  for r in rules["rules"]:
    if r["id"] == rule_id:
      return r
  raise KeyError(f"规则不存在: {rule_id}")


def _is_nonempty(v):
  return v is not None and str(v).strip() != ""


def _is_gt_zero(v):
  try:
    return float(v) > 0
  except (TypeError, ValueError):
    return False


def _field_value(parcel, field):
  # 源表列名 → 图斑对象键；未映射的从 raw 取
  # 实测：203 值可能落在「城镇村属性码」或「城镇村属性」列，两列都要看
  if field in ("城镇村属性码", "城镇村属性"):
    return parcel.get("townCode", "") or parcel.get("raw", {}).get("城镇村属性", "")
  mapped = {
    "实地地类": parcel.get("dileiCode", ""),
    "基础库地类编码": parcel.get("dileiCode", ""),
  }
  if field in mapped:
    return mapped[field]
  return parcel.get("raw", {}).get(field, "")


def _normalize_category(cat, rules):
  # 系统实际值与明白纸枚举存在别名差异，统一归一
  return rules.get("aliases", {}).get("分类", {}).get(cat, cat)


def _normalize_opinion(opinion, rules):
  # 核实认定意见的别名归一（如「实地为设施」→「设施农用地」）
  return rules.get("aliases", {}).get("核实认定意见", {}).get(opinion, opinion)


def _clause_match(clause, parcel, rules):
  ctype = clause.get("type")
  raw = parcel.get("raw", {})
  if ctype == "field_nonempty":
    return any(_is_nonempty(raw.get(f)) for f in clause["fields"])
  if ctype == "field_gt_zero":
    return any(_is_gt_zero(raw.get(f)) for f in clause["fields"])
  if ctype == "field_equal":
    return _field_value(parcel, clause["field"]) in clause["values"]
  if ctype == "filled_category_in_set":
    cat = _normalize_category(parcel.get("filled", {}).get("category", ""), rules)
    return _is_nonempty(cat) and cat in rules[clause["set"]]
  # manual / fallback 不参与自动匹配
  return False


def _match_condition(cond, parcel, rules):
  clauses = cond.get("clauses", [])
  if not clauses:
    return False
  results = [_clause_match(c, parcel, rules) for c in clauses]
  if cond.get("match") == "all":
    return all(results)
  return any(results)


def _determine(parcel, rules):
  # 顺序：合法类 → 设施农用地 → 农村道路 → 其他类 → 非农违法（兜底）
  order = ["LEGAL_PIWEN", "LEGAL_SUPPLY", "LEGAL_REGISTRATION",
           "FACILITY_AGRICULTURE", "FARMLAND_ROAD", "OTHER_BY_CATEGORY"]
  for rule_id in order:
    rule = _rule_by_id(rules, rule_id)
    if _match_condition(rule["condition"], parcel, rules):
      category = rule.get("category", "")
      if rule_id == "OTHER_BY_CATEGORY":
        category = _resolve_other_category(parcel, rules)
      return {"top": rule["top"], "category": category, "ruleId": rule_id}
  return {"top": "非农违法", "category": "", "ruleId": "ILLEGAL_FALLBACK"}


def _resolve_other_category(parcel, rules):
  cat = _normalize_category(parcel.get("filled", {}).get("category", ""), rules)
  if cat in rules["other_categories"]:
    return cat
  if _field_value(parcel, "城镇村属性码") == "203":
    return "203范围及开天窗"
  if parcel.get("dileiCode") == "0702":
    return "农村宅基地"
  return ""


# 举证类型 → 判定关键词（把规则要求的举证项与系统实际有的材料对应起来）
EVIDENCE_KEYWORDS = {
  "现场照片": ["照片"],
  "附件资料": ["批文", "合同", "证明", "备案", "文件", "材料", "移交函", "接收函"],
  "套合结果": ["矢量", "SHP", "套合"],
}


def _check_evidence(parcel, rule):
  required = list(rule.get("evidence", []))
  ev = parcel.get("evidence", {})
  have = []
  if ev.get("photos", 0) > 0:
    have.append("现场照片")
  if ev.get("attachments"):
    have.append("附件资料")
  if ev.get("overlay"):
    have.append("套合结果")
  missing = []
  for req in required:
    satisfied = False
    for kind, keywords in EVIDENCE_KEYWORDS.items():
      if kind in have and any(k in req for k in keywords):
        satisfied = True
        break
    if not satisfied:
      missing.append(req)
  result = {"required": required, "have": have, "missing": missing}
  # 违法类额外查必填要素
  if rule.get("required_fields"):
    raw = parcel.get("raw", {})
    miss_fields = [f for f in rule["required_fields"] if not _is_nonempty(raw.get(f))]
    result["requiredFields"] = rule["required_fields"]
    result["missingFields"] = miss_fields
  return result


# 各类别「确认性举证字段」（导出表实测全空；缺失时无法核实县级填报）
CONFIRM_FIELDS = {
  "合法": ["用地审批批准文号", "合法用地批文", "用地审批占比（%）",
           "土地供应批准文号", "土地供应占比（%）",
           "不动产权证号", "不动产登记占比（%）",
           "临时用地批准文号", "临时用地占比（%）"],
  "设施农用地": ["设施农用地上图入库号", "是否认定设施", "设施农用地占比（%）"],
}


def _can_verify_filled(parcel, rules):
  # 导出表里是否有足够字段核实县级填报；缺失则只能标存疑，不能报不一致
  filled_top = _normalize_opinion(parcel.get("filled", {}).get("opinion", ""), rules)
  if filled_top in rules.get("top_level_extra", []):
    return False  # 伪变化等无字段可核
  fields = CONFIRM_FIELDS.get(filled_top)
  if not fields:
    return True
  raw = parcel.get("raw", {})
  return any(_is_nonempty(raw.get(f)) or _is_gt_zero(raw.get(f)) for f in fields)


def judge_parcel(parcel, rules):
  expected = _determine(parcel, rules)
  rule = _rule_by_id(rules, expected["ruleId"])
  filled_raw = parcel.get("filled", {}).get("opinion", "")
  filled_top = _normalize_opinion(filled_raw, rules)
  # 县级填报为空时不算不一致（尚未填报）
  consistent = True if not _is_nonempty(filled_top) else (filled_top == expected["top"])
  evidence = _check_evidence(parcel, rule)
  suspicious = bool(rule.get("auto") is False) or expected["ruleId"] == "LEGAL_MANUAL"
  note = ""
  # 导出表缺该类的确认性举证字段时，无法核实县级填报 → 标存疑而非不一致
  if not consistent and not _can_verify_filled(parcel, rules):
    suspicious = True
    note = f"导出表缺少「{filled_top}」的举证字段，无法核实县级填报，需读系统确认"
    consistent = True  # 证据不足时不报不一致，避免误报
  basis = (
    f"规则 {expected['ruleId']}（{rule['top']}"
    + (f"·{rule['category']}" if rule.get("category") else "")
    + f"）：依据字段判定为「{expected['top']}」"
  )
  if rule.get("precondition"):
    basis += f"；前置条件：{rule['precondition']}"
  return {
    "id": parcel.get("id", ""),
    "expected": expected,
    "filled": {
      "top": filled_raw,
      "normalized": filled_top,
      "category": parcel.get("filled", {}).get("category", ""),
      "detail": parcel.get("filled", {}).get("detail", ""),
    },
    "consistent": consistent,
    "evidence": evidence,
    "suspicious": suspicious,
    "note": note,
    "basis": basis,
  }


def judge_all(parcels, rules):
  return [judge_parcel(p, rules) for p in parcels]


def main():
  ap = argparse.ArgumentParser(description="规则引擎批量判定")
  ap.add_argument("parcels", help="结构化图斑 JSON（load_parcels.py 产出）")
  ap.add_argument("-o", "--out", required=True, help="判定结果 JSON 输出路径")
  ap.add_argument("--rules", default=os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "rules", "rule-dictionary.json"))
  args = ap.parse_args()
  with open(args.parcels, encoding="utf-8") as f:
    parcels = json.load(f)
  rules = load_rules(args.rules)
  results = judge_all(parcels, rules)
  with open(args.out, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
  mismatch = [r for r in results if not r["consistent"]]
  print(f"判定完成 {len(results)} 个；与填报不一致 {len(mismatch)} 个 → {args.out}")


if __name__ == "__main__":
  main()
