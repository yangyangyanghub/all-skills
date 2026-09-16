# 批文覆盖率计算：图斑 shp ∩ 批文矢量 shp → 覆盖率
#
# 用法：
#   # 本地合法手续图层（不用下载）
#   python overlay_coverage.py --parcel "1548个.shp" --parcel-dbf "1548个.dbf" --id 130403SJBG26210183 \
#       --approval "用地审批已批.shp"
#
#   # 从系统下载的批文矢量 .zip（解压后）
#   python overlay_coverage.py --parcel "1548个.shp" --parcel-dbf "1548个.dbf" --id 130403SJBG26210183 \
#       --approval "97批次.shp"
#
#   # 多个合法手续图层一起算
#   python overlay_coverage.py ... --approval "用地审批已批.shp" "土地供应.shp" "临时用地.shp"
#
# 坐标系自动处理：
#   - 图斑若是经纬度（shp bbox 在 100-120 区间），自动 GK 正算投影到米
#   - 批文若是投影坐标（bbox 在 3800 万区间），直接用
#   覆盖率是比例，双方必须在同一坐标系
import argparse
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from geo_utils import read_shp, read_dbf, find_row, to_projected, m2_to_mu  # noqa: E402
from shapely.ops import unary_union  # noqa: E402


def _is_geographic(poly):
  """bbox 在 ±180 内 → 经纬度；否则投影米"""
  minx, miny, maxx, maxy = poly.bounds
  return -180 <= minx <= 180 and -90 <= maxy <= 90


def main():
  ap = argparse.ArgumentParser(description="批文覆盖率：图斑 ∩ 批文矢量")
  ap.add_argument("--parcel", required=True, help="图斑 .shp")
  ap.add_argument("--parcel-dbf", help="图斑 .dbf（默认与 shp 同名）")
  ap.add_argument("--id", required=True, help="图斑编号（匹配 dbf 任意字段）")
  ap.add_argument("--approval", nargs="+", required=True, help="批文矢量 .shp 或 .zip（可多个图层）")
  args = ap.parse_args()

  dbf = args.parcel_dbf or args.parcel.replace(".shp", ".dbf")
  parcels = read_shp(args.parcel)
  records = read_dbf(dbf)
  row = find_row(records, args.id)
  parcel = parcels[row]

  # 图斑坐标系归一：经纬度 → 投影米
  if _is_geographic(parcel):
    parcel = to_projected(parcel)

  total = parcel.area
  print(f"图斑 {args.id}: 面积 {total:.2f} m² = {m2_to_mu(total):.3f} 亩\n")

  # 批文矢量：解压 .zip 或直接读 .shp
  approval_polys = []
  for src in args.approval:
    if src.endswith(".zip"):
      ex = os.path.join(os.path.dirname(os.path.abspath(src)),
                        "_extracted_" + os.path.basename(src).replace(".zip", ""))
      with zipfile.ZipFile(src) as z:
        z.extractall(ex)
      shp = [f for f in os.listdir(ex) if f.endswith(".shp")]
      if not shp:
        print(f"  ✗ {src} 里没有 .shp"); continue
      src = os.path.join(ex, shp[0])
    if not src.endswith(".shp"):
      print(f"  ✗ {src} 不是 .shp/.zip"); continue
    polys = read_shp(src)
    # 若批文是经纬度，也投影（与图斑统一）
    if polys and _is_geographic(polys[0]):
      polys = [to_projected(p) for p in polys]
    approval_polys.extend(polys)
    print(f"  图层 {os.path.basename(src)}: {len(polys)} 个要素")

  if not approval_polys:
    print("没有可用的批文矢量"); sys.exit(1)

  union = unary_union(approval_polys)
  inter = parcel.intersection(union)
  cover = inter.area / total * 100 if total else 0

  print(f"\n=== 覆盖率 ===")
  print(f"批文覆盖: {inter.area:.2f} m² = {m2_to_mu(inter.area):.3f} 亩")
  print(f"覆盖率:   {cover:.2f}%")
  uncovered_mu = m2_to_mu(total - inter.area)
  print(f"未覆盖:   {100 - cover:.2f}% = {uncovered_mu:.3f} 亩")
  if uncovered_mu > 0.001:  # 容差 0.001 亩，避免浮点误差误报
    print(f"\n⚠️ 批文未完全覆盖（差 {uncovered_mu:.3f} 亩）"
          f"→ 按规则需查看现场照片确认是否为边角地")


if __name__ == "__main__":
  main()
