# -*- coding: utf-8 -*-
"""
数据探查工具
用法:
  python-qgis-ltr.bat scripts/inspect_data.py --data 数据目录路径
"""

import os
import sys
import glob
import json
import argparse

from qgis.core import QgsApplication, QgsVectorLayer

def main():
    parser = argparse.ArgumentParser(description="探测 Shapefile/GeoJSON 数据信息")
    parser.add_argument("--data", required=True, help="数据目录路径")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    args = parser.parse_args()

    qgs = QgsApplication([], False)
    qgs.initQgis()

    data_dir = args.data
    if not os.path.isdir(data_dir):
        print(f"❌ 目录不存在: {data_dir}")
        sys.exit(1)

    # 扫描 shp 文件
    shp_files = sorted(glob.glob(os.path.join(data_dir, "*.shp")))
    if not shp_files:
        print(f"⚠️ 目录 {data_dir} 中没有找到 .shp 文件")
        sys.exit(0)

    layers = []
    for shp_path in shp_files:
        layer = QgsVectorLayer(shp_path, os.path.basename(shp_path), "ogr")
        if not layer.isValid():
            continue

        geom_type_names = {0: "点(Point)", 1: "线(Polyline)", 2: "面(Polygon)"}
        geom_type = geom_type_names.get(layer.geometryType(), "未知")

        # 找可标注字段
        label_candidates = ["NAME", "name", "名称", "市名", "NAME_CHN", "县名", "省名"]
        label_field = None
        for f in layer.fields():
            if f.name() in label_candidates:
                label_field = f.name()
                break
        if not label_field:
            for f in layer.fields():
                if f.type() == 10:  # QString
                    label_field = f.name()
                    break

        layers.append({
            "name": os.path.basename(shp_path).replace(".shp", ""),
            "file": os.path.basename(shp_path),
            "geom_type": geom_type,
            "geom_code": layer.geometryType(),
            "count": layer.featureCount(),
            "fields": [f.name() for f in layer.fields()],
            "label_field": label_field,
            "crs": layer.crs().authid(),
            "extent": layer.extent().toString() if not layer.extent().isEmpty() else "",
        })

    crs_set = set(l["crs"] for l in layers)

    if args.json:
        print(json.dumps({"layers": layers, "crs_count": len(crs_set)}, ensure_ascii=False, indent=2))
    else:
        print("=" * 60)
        print(f"   数据探查报告: {data_dir}")
        print("=" * 60)
        print(f"\n📂 检测到 {len(layers)} 个图层：")
        for i, l in enumerate(layers, 1):
            label_info = f'  [可标注: {l["label_field"]}]' if l["label_field"] else ""
            print(f'  ☑ {l["name"]:<20s} {l["geom_type"]:<15s} {l["count"]} 要素{label_info}')

        if len(crs_set) == 1:
            print(f"\n🌍 坐标系: {list(crs_set)[0]}")
        else:
            print(f"\n⚠️ 发现 {len(crs_set)} 个不同坐标系:")
            for c in crs_set:
                print(f"   - {c}")

        print()
        for l in layers:
            print(f'  [{l["name"]}] 字段: {", ".join(l["fields"])}')

    qgs.exitQgis()

if __name__ == "__main__":
    main()
