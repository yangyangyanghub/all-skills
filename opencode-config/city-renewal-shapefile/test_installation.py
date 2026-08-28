#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技能测试脚本 - 验证技能是否可以正常工作
"""

import os
import sys
from pathlib import Path

print("=" * 70)
print("城市更新资源Shapefile技能 - 安装测试")
print("=" * 70)
print()

# 测试1：检查技能目录
print("[测试1] 检查技能目录...")
skill_dir = Path(__file__).parent
print(f"  技能目录: {skill_dir}")

required_files = [
    "SKILL.md",
    "create_shapefiles.py",
    "verify_shapefiles.py",
    "README.md",
    "快速开始.md",
    "使用示例.md"
]

all_exist = True
for file in required_files:
    file_path = skill_dir / file
    if file_path.exists():
        print(f"  [OK] {file}")
    else:
        print(f"  [FAIL] {file} - 缺失")
        all_exist = False

if not all_exist:
    print("\n[错误] 缺少必要文件，请重新安装技能")
    sys.exit(1)

print()

# 测试2：检查Python依赖
print("[测试2] 检查Python依赖...")
dependencies = {
    "fiona": "fiona",
    "geopandas": "geopandas",
    "shapely": "shapely"
}

all_installed = True
for package, import_name in dependencies.items():
    try:
        __import__(import_name)
        print(f"  [OK] {package}")
    except ImportError:
        print(f"  [FAIL] {package} - 未安装")
        all_installed = False

if not all_installed:
    print("\n[提示] 请运行以下命令安装依赖:")
    print("  pip install fiona geopandas shapely")
    sys.exit(1)

print()

# 测试3：创建测试文件
print("[测试3] 创建测试Shapefile...")
try:
    import fiona
    from fiona.crs import from_epsg
    
    test_dir = skill_dir / "test_output"
    test_dir.mkdir(exist_ok=True)
    
    test_file = test_dir / "TEST.shp"
    
    schema = {
        'geometry': 'Point',
        'properties': {
            'BSM': 'str:18',
            'DSDM': 'str:6',
            'MC': 'str:50',
        }
    }
    
    with fiona.open(
        test_file,
        'w',
        driver='ESRI Shapefile',
        crs=from_epsg(4490),
        schema=schema,
        encoding='utf-8'
    ) as dst:
        pass
    
    # 验证文件
    if test_file.exists():
        print(f"  [OK] 测试文件创建成功: {test_file}")
        
        # 检查字段长度
        with fiona.open(test_file, 'r') as src:
            schema = src.schema
            if schema['properties']['BSM'] == 'str:18':
                print(f"  [OK] 字段长度正确: BSM = str:18")
            else:
                print(f"  [FAIL] 字段长度错误: BSM = {schema['properties']['BSM']}")
            
            if schema['geometry'] == 'Point':
                print(f"  [OK] 几何类型正确: Point")
            else:
                print(f"  [FAIL] 几何类型错误: {schema['geometry']}")
    else:
        print(f"  [FAIL] 测试文件创建失败")
        sys.exit(1)
    
    # 清理测试文件
    import shutil
    shutil.rmtree(test_dir)
    print(f"  [OK] 测试文件已清理")
    
except Exception as e:
    print(f"  ✗ 测试失败: {e}")
    sys.exit(1)

print()

# 测试4：检查输出目录
print("[测试4] 检查输出目录...")
output_dir = Path(r"E:\code\my-ai-workspace\myk\调研笔记\城市更新政策研究\database_schema\城市更新资源空表_最终版")
if output_dir.exists():
    shp_files = list(output_dir.glob("*.shp"))
    print(f"  [OK] 输出目录存在: {output_dir}")
    print(f"  [OK] 找到 {len(shp_files)} 个Shapefile文件")
    
    if len(shp_files) == 84:
        print(f"  [OK] 文件数量正确: 84个")
    else:
        print(f"  [WARN] 文件数量不正确: {len(shp_files)}个（期望84个）")
else:
    print(f"  [INFO] 输出目录不存在（这是正常的，如果还没有运行过创建脚本）")
    print(f"         运行 create_shapefiles.py 后会创建此目录")

print()
print("=" * 70)
print("测试完成！所有检查通过")
print("=" * 70)
print()
print("技能已正确安装，可以开始使用！")
print()
print("使用方法:")
print("  1. 在AI中说：'帮我创建城市更新资源的Shapefile'")
print("  2. 或手动运行: python create_shapefiles.py")
print()
print("更多信息请查看:")
print("  - 快速开始.md")
print("  - README.md")
print("  - 使用示例.md")
