# 读「图斑列表」导出表 → 结构化图斑对象
# 只依赖标准库 + openpyxl（仅 xlsx 入口需要）
import argparse
import json
import os

# 源表列名 → 内部字段名
COL_ID = "线索编号"
COL_COUNTY = "县级行政区名称"
COL_AREA = "图斑面积(亩)"
COL_DILEI = "实地地类"
COL_TOWN = "城镇村属性码"

FILLED_MAP = {
  "opinion": "核实认定意见",
  "category": "分类",
  "detail": "用途分类细化",
  "projectName": "项目名称",
  "buildTime": "建设时间",
  "projectSubject": "项目主体",
}


def _to_float(v):
  if v is None or v == "":
    return 0.0
  try:
    return float(v)
  except (TypeError, ValueError):
    return 0.0


def _to_str(v):
  if v is None:
    return ""
  return str(v).strip()


def _row_to_parcel(row):
  filled = {}
  for key, col in FILLED_MAP.items():
    filled[key] = _to_str(row.get(col))
  return {
    "id": _to_str(row.get(COL_ID)),
    "county": _to_str(row.get(COL_COUNTY)),
    "areaMu": _to_float(row.get(COL_AREA)),
    "dileiCode": _to_str(row.get(COL_DILEI)),
    "townCode": _to_str(row.get(COL_TOWN)),
    "filled": filled,
    "evidence": {
      "photos": 0,
      "attachments": [],
      "overlay": {},
    },
    # 保留原始行，供判定引擎按需读取其他列
    "raw": {k: _to_str(v) for k, v in row.items()},
  }


def load_from_rows(rows):
  return [_row_to_parcel(r) for r in rows]


def load_from_xlsx(path, sheet_name="图斑列表"):
  import openpyxl
  wb = openpyxl.load_workbook(path, data_only=True)
  ws = wb[sheet_name]
  it = ws.iter_rows(values_only=True)
  header = [_to_str(c) for c in next(it)]
  rows = []
  for r in it:
    rows.append({header[i]: r[i] for i in range(len(header)) if header[i]})
  wb.close()
  return load_from_rows(rows)


def main():
  ap = argparse.ArgumentParser(description="读图斑列表导出表 → 结构化 JSON")
  ap.add_argument("xlsx", help="图斑列表 xlsx 路径")
  ap.add_argument("-o", "--out", required=True, help="输出 JSON 路径")
  ap.add_argument("--sheet", default="图斑列表")
  args = ap.parse_args()
  parcels = load_from_xlsx(args.xlsx, args.sheet)
  os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
  with open(args.out, "w", encoding="utf-8") as f:
    json.dump(parcels, f, ensure_ascii=False, indent=2)
  print(f"已导出 {len(parcels)} 个图斑 → {args.out}")


if __name__ == "__main__":
  main()
