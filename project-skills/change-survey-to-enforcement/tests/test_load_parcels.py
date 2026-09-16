# 导出表加载器测试
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))

from load_parcels import load_from_rows  # noqa: E402

FIXTURE = os.path.join(HERE, "fixtures", "sample_rows.json")


def load_fixture():
  with open(FIXTURE, encoding="utf-8") as f:
    return json.load(f)


def test_returns_one_parcel_per_row():
  parcels = load_from_rows(load_fixture())
  assert len(parcels) == 2


def test_maps_identity_fields():
  p = load_from_rows(load_fixture())[0]
  assert p["id"] == "130431SJBG26210188"
  assert p["county"] == "鸡泽县"
  assert p["areaMu"] == 0.36
  assert p["dileiCode"] == "0601"


def test_maps_filled_block():
  p = load_from_rows(load_fixture())[0]
  assert p["filled"]["opinion"] == "其他"
  assert p["filled"]["category"] == "农村宅基地"
  assert p["filled"]["detail"] == ""
  assert p["filled"]["projectSubject"] == "个人"


def test_missing_columns_become_empty_not_crash():
  parcels = load_from_rows([{"线索编号": "X1"}])
  p = parcels[0]
  assert p["id"] == "X1"
  assert p["county"] == ""
  assert p["areaMu"] == 0
  assert p["filled"]["opinion"] == ""


def test_numeric_conversion():
  p = load_from_rows(load_fixture())[1]
  assert isinstance(p["areaMu"], float)
  assert p["areaMu"] == 0.93


if __name__ == "__main__":
  for name, fn in sorted(globals().items()):
    if name.startswith("test_") and callable(fn):
      fn()
      print(f"PASS {name}")
  print("ALL PASS")
