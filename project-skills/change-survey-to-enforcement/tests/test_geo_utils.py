# geo_utils 测试：投影正算 + shp/dbf 读取
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))

from geo_utils import gk_forward, m2_to_mu, read_shp, read_dbf, find_row  # noqa: E402

REAL_SHP = (r"E:\2026卫片执法专项\2026年变更调查\进度\20260914"
            r"\2026年上半年变更调查新增建设线索处置(1548个)0066910266358979"
            r"\2026年上半年变更调查新增建设线索处置(1548个).shp")


def test_gk_forward_central_meridian():
  # 中央经线 114°、纬度 0 → X=38500000, Y=0
  x, y = gk_forward(114.0, 0.0)
  assert abs(x - 38500000) < 0.01, x
  assert abs(y) < 0.01, y


def test_gk_forward_known_point():
  # 邯郸附近 114.5, 36.7 → 应在 3850 万 / 406 万 附近
  x, y = gk_forward(114.5, 36.7)
  assert 38500000 < x < 38600000, x
  assert 4000000 < y < 4100000, y


def test_m2_to_mu():
  assert abs(m2_to_mu(666.667) - 1.0) < 1e-3
  assert abs(m2_to_mu(260.0) - 0.39) < 0.01


def test_read_real_shp_dbf_if_present():
  if not os.path.exists(REAL_SHP):
    print("  SKIP: 真实 shp 不在本机")
    return
  geoms = read_shp(REAL_SHP)
  assert len(geoms) == 1548, f"要素数 {len(geoms)}"
  recs = read_dbf(REAL_SHP.replace(".shp", ".dbf"))
  assert len(recs) == 1548
  # 用 find_row 找目标图斑并读几何
  row = find_row(recs, "130403SJBG26210183")
  poly = geoms[row]
  # 图斑面积（度²）应在合理量级（0.8 亩 ≈ 540 m² ≈ 5e-8 度²）
  assert 1e-9 < poly.area < 1e-6, poly.area


def test_projected_area_matches_excel():
  # 130403SJBG26210183 套合表面积 0.81 亩（实测 0.812）
  if not os.path.exists(REAL_SHP):
    print("  SKIP: 真实 shp 不在本机")
    return
  from geo_utils import to_projected
  from shapely.ops import unary_union
  recs = read_dbf(REAL_SHP.replace(".shp", ".dbf"))
  row = find_row(recs, "130403SJBG26210183")
  poly = to_projected(read_shp(REAL_SHP)[row])
  mu = m2_to_mu(poly.area)
  assert abs(mu - 0.81) < 0.01, mu


if __name__ == "__main__":
  for name, fn in sorted(globals().items()):
    if name.startswith("test_") and callable(fn):
      fn()
      print(f"PASS {name}")
  print("ALL PASS")
