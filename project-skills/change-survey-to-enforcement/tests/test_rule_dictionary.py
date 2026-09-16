# 规则字典完整性校验：枚举必须与《一体化执法填报明白纸》一致
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DICT_PATH = os.path.join(HERE, "..", "data", "rule-dictionary.json")

EXPECTED_TOP = ["合法", "其他", "非农违法", "农村道路", "设施农用地"]

EXPECTED_OTHER_CATEGORIES = [
    "边角细缝", "边坡治理", "地下管廊（网）", "农村宅基地",
    "直接服务于河道的水工建筑/涉海用地", "JY", "农村土坟",
    "203范围及开天窗", "SM", "省外飞地", "出入口", "紧急用地",
    "合法矿区内的矿山修复治理", "生态修复用地", "电力设施",
    "灾毁地块", "水面高架桥", "其他",
]

EXPECTED_ILLEGAL_CATEGORIES = {
    "工矿商服": ["厂房类", "光伏", "硬化", "文旅", "采矿用地", "挖湖造景"],
    "民生公益": ["公共管理和公共服务", "城镇住宅", "特殊用地"],
    "道路交通": ["高速高铁", "国省干道", "地方城镇道路"],
    "圈占堆放等其他用地": ["圈占/堆放压占"],
}


def load_dict():
  with open(DICT_PATH, encoding="utf-8") as f:
    return json.load(f)


def test_top_level_matches_spec():
  d = load_dict()
  assert d["top_level"] == EXPECTED_TOP, d["top_level"]


def test_other_categories_complete():
  d = load_dict()
  assert d["other_categories"] == EXPECTED_OTHER_CATEGORIES


def test_illegal_categories_complete():
  d = load_dict()
  fallback = [r for r in d["rules"] if r["id"] == "ILLEGAL_FALLBACK"]
  assert len(fallback) == 1
  assert fallback[0]["categories"] == EXPECTED_ILLEGAL_CATEGORIES


def test_every_rule_has_required_keys():
  d = load_dict()
  for r in d["rules"]:
    for k in ["id", "top", "condition", "evidence", "auto"]:
      assert k in r, f"规则 {r.get('id')} 缺 {k}"
    assert r["top"] in EXPECTED_TOP, r["id"]


def test_rule_ids_unique():
  d = load_dict()
  ids = [r["id"] for r in d["rules"]]
  assert len(ids) == len(set(ids)), "规则 id 重复"


def test_legal_categories_present():
  d = load_dict()
  legal = [r for r in d["rules"] if r["top"] == "合法"]
  cats = {r["category"] for r in legal}
  assert cats == {"批文", "供地手续", "登记发证", "其他"}, cats


if __name__ == "__main__":
  for name, fn in sorted(globals().items()):
    if name.startswith("test_") and callable(fn):
      fn()
      print(f"PASS {name}")
  print("ALL PASS")
