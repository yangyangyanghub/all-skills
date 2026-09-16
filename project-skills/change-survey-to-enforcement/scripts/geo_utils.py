# GIS 基础工具（纯 Python 零依赖）：读 SHP/DBF + 高斯-克吕格正算
#
# 为什么纯 Python：
#   - 环境里没有 fiona/pyshp/geopandas/pyproj，且不装依赖
#   - .shp/.dbf 是公开格式，解析代码 ~80 行
#   - 高斯-克吕格正算（CGCS2000 3度带）是公开公式
import math
import struct

from shapely.geometry import Polygon

# ---------- 高斯-克吕格正算（CGCS2000 3度带） ----------
# 默认 38 带（中央经线 114°，东伪偏移 38500000），可传参覆盖
_A = 6378137.0
_F = 1 / 298.257222101
_E2 = 2 * _F - _F * _F
_EP2 = _E2 / (1 - _E2)


def gk_forward(lon, lat, central_meridian=114.0, false_easting=38500000.0):
  """经纬度（CGCS2000/WGS84 度）→ 高斯-克吕格投影（米）"""
  cm = math.radians(central_meridian)
  b = math.radians(lat)
  l = math.radians(lon) - cm
  n = _A / math.sqrt(1 - _E2 * math.sin(b) ** 2)
  t = math.tan(b)
  c = _EP2 * math.cos(b) ** 2
  ad = l * math.cos(b)
  m = _A * ((1 - _E2 / 4 - 3 * _E2 ** 2 / 64 - 5 * _E2 ** 3 / 256) * b
            - (3 * _E2 / 8 + 3 * _E2 ** 2 / 32 + 45 * _E2 ** 3 / 1024) * math.sin(2 * b)
            + (15 * _E2 ** 2 / 256 + 45 * _E2 ** 3 / 1024) * math.sin(4 * b)
            - (35 * _E2 ** 3 / 3072) * math.sin(6 * b))
  x = false_easting + n * (ad + (1 - t * t + c) * ad ** 3 / 6
                           + (5 - 18 * t * t + t ** 4 + 14 * c - 58 * c * t * t) * ad ** 5 / 120)
  y = m + n * t * (ad * ad / 2 + (5 - t * t + 9 * c + 4 * c * c) * ad ** 4 / 24
                   + (61 - 58 * t * t + t ** 4) * ad ** 6 / 720)
  return x, y


# ---------- SHP 读取（只支持 polygon 类型 5） ----------
def read_shp(path):
  """读 .shp，返回 shapely Polygon 列表（经纬度或投影坐标，取决于文件本身）"""
  data = open(path, "rb").read()
  assert data[:4] == b"\x00\x00\x27\x0a", f"非 SHP 文件: {path}"
  geoms = []
  off = 100
  while off + 8 <= len(data):
    _rec_num, clen = struct.unpack(">ii", data[off:off + 8])
    c = data[off + 8: off + 8 + clen * 2]
    off += 8 + clen * 2
    if struct.unpack("<i", c[0:4])[0] == 5:  # polygon
      num_parts = struct.unpack("<i", c[36:40])[0]
      num_points = struct.unpack("<i", c[40:44])[0]
      parts = struct.unpack("<%di" % num_parts, c[44:44 + num_parts * 4])
      base = 44 + num_parts * 4
      pts = [struct.unpack("<dd", c[base + i * 16: base + i * 16 + 16]) for i in range(num_points)]
      rings = []
      for pi in range(num_parts):
        s0 = parts[pi]
        e0 = parts[pi + 1] if pi + 1 < num_parts else num_points
        rings.append(pts[s0:e0])
      geoms.append(Polygon(rings[0], rings[1:]))
  return geoms


def read_dbf(path):
  """读 .dbf（属性表），返回 dict 列表（GBK 解码）"""
  data = open(path, "rb").read()
  num_rec = struct.unpack("<i", data[4:8])[0]
  header_len = struct.unpack("<H", data[8:10])[0]
  rec_len = struct.unpack("<H", data[10:12])[0]
  fields = []
  off = 32
  while off < header_len - 1:
    d = data[off:off + 32]
    if d[0] == 0x0D:
      break
    fields.append((d[:11].split(b"\x00")[0].decode("gbk", "ignore"), d[16]))
    off += 32
  recs = []
  base = header_len
  for i in range(num_rec):
    rec = data[base + i * rec_len: base + (i + 1) * rec_len]
    if rec[0] == 0x2A:  # 删除标记
      recs.append({})
      continue
    d = {}
    p = 1
    for name, fl in fields:
      d[name] = rec[p:p + fl].split(b"\x00")[0].strip().decode("gbk", "ignore")
      p += fl
    recs.append(d)
  return recs


def find_row(records, field_value):
  """在 DBF 记录里按值找行号（匹配任意字段）"""
  for i, r in enumerate(records):
    if field_value in r.values():
      return i
  raise ValueError(f"DBF 中未找到: {field_value}")


def to_projected(polygon, **kw):
  """经纬度 Polygon → GK 投影米 Polygon"""
  pts = [gk_forward(x, y, **kw) for x, y in polygon.exterior.coords]
  return Polygon(pts)


def m2_to_mu(m2):
  return m2 / 666.667
