# 判定引擎测试
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))

from judge import load_rules, judge_parcel  # noqa: E402

DICT_PATH = os.path.join(HERE, "..", "data", "rule-dictionary.json")
RULES = load_rules(DICT_PATH)


def make_parcel(**over):
  p = {
    "id": "T1",
    "county": "测试县",
    "areaMu": 1.0,
    "dileiCode": "",
    "townCode": "",
    "filled": {"opinion": "", "category": "", "detail": "", "projectName": "",
               "buildTime": "", "projectSubject": ""},
    "evidence": {"photos": 0, "attachments": [], "overlay": {}},
    "raw": {},
  }
  p.update(over)
  return p


def test_rural_road_by_dilei_1006():
  p = make_parcel(dileiCode="1006")
  r = judge_parcel(p, RULES)
  assert r["expected"]["top"] == "农村道路", r["expected"]
  assert r["expected"]["ruleId"] == "FARMLAND_ROAD"


def test_facility_agriculture_by_dilei_1202():
  p = make_parcel(dileiCode="1202")
  r = judge_parcel(p, RULES)
  assert r["expected"]["top"] == "设施农用地"


def test_rural_housing_is_other():
  p = make_parcel(dileiCode="0702")
  r = judge_parcel(p, RULES)
  assert r["expected"]["top"] == "其他"
  assert r["expected"]["category"] == "农村宅基地"


def test_203_is_other():
  p = make_parcel(townCode="203")
  r = judge_parcel(p, RULES)
  assert r["expected"]["top"] == "其他"
  assert r["expected"]["category"] == "203范围及开天窗"


def test_legal_by_piwen_field():
  p = make_parcel(dileiCode="0601", raw={"用地审批批准文号": "冀政地〔2026〕1号"})
  r = judge_parcel(p, RULES)
  assert r["expected"]["top"] == "合法"
  assert r["expected"]["category"] == "批文"


def test_illegal_fallback():
  p = make_parcel(dileiCode="0601")
  r = judge_parcel(p, RULES)
  assert r["expected"]["top"] == "非农违法"
  assert r["expected"]["ruleId"] == "ILLEGAL_FALLBACK"


def test_consistency_flag_when_filled_mismatch():
  # 县区填「农村道路」，但实地地类=1202 明确指向设施农用地 → 不一致（该类别可核实）
  p = make_parcel(dileiCode="1202", filled={"opinion": "农村道路", "category": "", "detail": "",
                                            "projectName": "", "buildTime": "", "projectSubject": ""})
  r = judge_parcel(p, RULES)
  assert r["expected"]["top"] == "设施农用地"
  assert r["consistent"] is False


def test_consistency_flag_when_filled_match():
  p = make_parcel(dileiCode="1006", filled={"opinion": "农村道路", "category": "", "detail": "",
                                            "projectName": "", "buildTime": "", "projectSubject": ""})
  r = judge_parcel(p, RULES)
  assert r["consistent"] is True


def test_evidence_missing_reported():
  p = make_parcel(dileiCode="1006")
  r = judge_parcel(p, RULES)
  assert len(r["evidence"]["required"]) > 0
  assert len(r["evidence"]["missing"]) == len(r["evidence"]["required"])


def test_illegal_required_fields_checked():
  p = make_parcel(dileiCode="0601")
  r = judge_parcel(p, RULES)
  assert r["expected"]["ruleId"] == "ILLEGAL_FALLBACK"
  assert len(r["evidence"]["missingFields"]) > 0


def test_basis_cites_rule_id():
  p = make_parcel(dileiCode="1006")
  r = judge_parcel(p, RULES)
  assert "FARMLAND_ROAD" in r["basis"]


def test_suspicious_default_false_for_deterministic():
  p = make_parcel(dileiCode="1006")
  r = judge_parcel(p, RULES)
  assert r["suspicious"] is False


def test_town_203_from_attribute_column():
  # 实测：203 值可能落在「城镇村属性」列，而非「城镇村属性码」列
  p = make_parcel(dileiCode="0601", raw={"城镇村属性": "203"})
  r = judge_parcel(p, RULES)
  assert r["expected"]["top"] == "其他", r["expected"]
  assert r["expected"]["category"] == "203范围及开天窗"


def test_category_alias_203_range():
  # 实测：县区填「203范围」，明白纸枚举写「203范围及开天窗」——需归一后一致
  p = make_parcel(dileiCode="0601", raw={"城镇村属性": "203"},
                  filled={"opinion": "其他", "category": "203范围", "detail": "",
                          "projectName": "", "buildTime": "", "projectSubject": ""})
  r = judge_parcel(p, RULES)
  assert r["expected"]["top"] == "其他"
  assert r["consistent"] is True, r


def test_category_alias_slope_treatment():
  # 实测：县区填「边坡治理地块」，明白纸枚举写「边坡治理」
  p = make_parcel(dileiCode="0601", filled={"opinion": "其他", "category": "边坡治理地块", "detail": "",
                                            "projectName": "", "buildTime": "", "projectSubject": ""})
  r = judge_parcel(p, RULES)
  assert r["expected"]["top"] == "其他", r["expected"]
  assert r["consistent"] is True, r


def test_legal_evidence_absent_marks_suspicious_not_mismatch():
  # 导出表缺批文号/占比字段时，填「合法」不应报不一致，应标存疑
  p = make_parcel(dileiCode="0601",
                  filled={"opinion": "合法", "category": "", "detail": "",
                          "projectName": "", "buildTime": "", "projectSubject": ""})
  r = judge_parcel(p, RULES)
  assert r["expected"]["ruleId"] == "ILLEGAL_FALLBACK"
  assert r["suspicious"] is True
  assert r["consistent"] is True, "证据不足时不应报不一致"
  assert "举证" in r["note"]


def test_legal_confirmed_when_piwen_present():
  # 有批文号时，合法类可确认，不标存疑
  p = make_parcel(dileiCode="0601", raw={"用地审批批准文号": "冀政地〔2026〕1号"})
  r = judge_parcel(p, RULES)
  assert r["expected"]["ruleId"] == "LEGAL_PIWEN"
  assert r["suspicious"] is False


def test_filled_legal_but_no_evidence_is_suspicious_not_mismatch():
  # 实测场景：县区填「合法·登记发证」，但导出表无不动产权证号 → 标存疑，不报不一致
  p = make_parcel(dileiCode="0601", raw={"城镇村属性": "203"},
                  filled={"opinion": "合法", "category": "登记发证", "detail": "",
                          "projectName": "", "buildTime": "", "projectSubject": ""})
  r = judge_parcel(p, RULES)
  assert r["expected"]["top"] == "其他"
  assert r["consistent"] is True, "无法核实时不报不一致"
  assert r["suspicious"] is True
  assert "举证字段" in r["note"]


def test_pseudo_change_is_suspicious_not_mismatch():
  # 实测场景：县区填「伪变化」（无字段可核）→ 存疑，不报不一致
  p = make_parcel(dileiCode="", filled={"opinion": "伪变化", "category": "", "detail": "",
                                        "projectName": "种植", "buildTime": "", "projectSubject": "农作物种植"})
  r = judge_parcel(p, RULES)
  assert r["consistent"] is True
  assert r["suspicious"] is True


def test_opinion_alias_shidiweisheshi():
  # 实测场景：县区填「实地为设施」→ 归一为「设施农用地」；无设施举证字段 → 存疑
  p = make_parcel(dileiCode="1109", filled={"opinion": "实地为设施", "category": "", "detail": "",
                                            "projectName": "", "buildTime": "", "projectSubject": ""})
  r = judge_parcel(p, RULES)
  assert r["filled"]["normalized"] == "设施农用地"
  assert r["suspicious"] is True
  assert r["consistent"] is True


if __name__ == "__main__":
  for name, fn in sorted(globals().items()):
    if name.startswith("test_") and callable(fn):
      fn()
      print(f"PASS {name}")
  print("ALL PASS")
