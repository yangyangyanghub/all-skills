# lookup_area.py 测试：优先用真实套合表；表不存在则只测纯逻辑
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))

from lookup_area import lookup, render, DEFAULT_TRUTH  # noqa: E402


def test_render_missing_parcel():
  out = render([{"id": "X1", "found": False}])
  assert "X1" in out
  assert "未找到" in out


def test_render_with_truth():
  r = [{
    "id": "T1", "found": True,
    "truth": {"areaMu": 0.23, "cultivated": 0.0, "basicFarmland": 0.0,
              "nonCultivatedAgri": 0.23, "unused": 0.0, "ecoRedline": 0.0, "construction": 0.0},
    "extra": {"变更地类": "工业用地", "县区": "磁县"},
  }]
  out = render(r)
  assert "0.23" in out
  assert "工业用地" in out
  assert "磁县" in out


def test_render_reports_diff():
  r = [{
    "id": "T2", "found": True,
    "truth": {"areaMu": 0.23, "cultivated": 0.0, "basicFarmland": 0.0,
              "nonCultivatedAgri": 0.23, "unused": 0.0, "ecoRedline": 0.0, "construction": 0.0},
    "extra": {},
    "filled": {"areaMu": 0.5, "cultivated": 0.0, "basicFarmland": 0.0,
               "nonCultivatedAgri": 0.5, "unused": 0.0, "ecoRedline": 0.0, "construction": None},
    "diffs": [{"field": "地块面积", "filled": 0.5, "truth": 0.23, "diff": 0.27}],
  }]
  out = render(r)
  assert "与填报值差异" in out
  assert "地块面积" in out


def test_render_reports_match():
  r = [{
    "id": "T3", "found": True,
    "truth": {"areaMu": 0.23, "cultivated": 0.0, "basicFarmland": 0.0,
              "nonCultivatedAgri": 0.23, "unused": 0.0, "ecoRedline": 0.0, "construction": 0.0},
    "extra": {}, "filled": {"areaMu": 0.23}, "diffs": [],
  }]
  out = render(r)
  assert "面积与填报一致" in out


def test_lookup_real_file_if_present():
  if not os.path.exists(DEFAULT_TRUTH):
    print("  SKIP: 套合结果表不在本机")
    return
  res = lookup(DEFAULT_TRUTH, ["130427SJBG26210310_3"])
  assert len(res) == 1
  assert res[0]["found"] is True, "真实表里应能找到该图斑"
  assert res[0]["truth"]["areaMu"] == 0.23


if __name__ == "__main__":
  for name, fn in sorted(globals().items()):
    if name.startswith("test_") and callable(fn):
      fn()
      print(f"PASS {name}")
  print("ALL PASS")
