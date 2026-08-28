---
name: city-renewal-shapefile
description: >
  创建符合《河北省城市更新资源数据成果汇交要求》的Shapefile空表。当用户需要创建城市更新资源数据库、
  生成符合规范的GIS空表、批量创建Shapefile文件、或需要按照汇交要求设置字段长度和几何类型时使用。
  触发词：城市更新、Shapefile、空表、汇交要求、GIS数据库、字段长度、几何类型。
allowed-tools:
  - Bash(python *)
  - Bash(pip install *)
  - Read
  - Write
  - Edit
---

# 城市更新资源Shapefile创建工具

本技能用于创建符合《河北省城市更新资源数据成果汇交要求》的84个Shapefile空表，包含正确的字段长度、几何类型和坐标系设置。

## 核心功能

- 创建84个Shapefile文件（居住类12个、产业类8个、公共设施类50个、公共空间类5个、历史风貌类7个、其他类2个）
- 字段长度按汇交要求精确设置（非默认80）
- 正确的几何类型分配（Point/Polygon/LineString）
- 坐标系：CGCS2000 (EPSG:4490)
- UTF-8编码（支持中文）
- 生成配套字段说明CSV和ArcGIS元数据XML

## 使用场景

### 场景1：创建完整的84个Shapefile

当用户需要创建完整的城市更新资源数据库空表时：

```bash
# 1. 确保Python环境已安装依赖
pip install fiona geopandas shapely

# 2. 运行创建脚本
python create_shapefiles.py

# 3. 验证文件
python verify_shapefiles.py
```

### 场景2：创建特定类型的Shapefile

当用户只需要某一类资源（如居住类、产业类）时，可以修改脚本只创建需要的部分。

### 场景3：修改字段结构

当用户需要调整字段长度或添加新字段时，编辑 `create_shapefiles.py` 中的字段定义。

## 技术规范

### 字段长度规范

| 字段代码 | 字段名称 | 类型 | 长度 | 说明 |
|---------|---------|------|------|------|
| BSM | 标识码 | str | 18 | 唯一标识 |
| DSDM | 地市代码 | str | 6 | 行政区划代码 |
| DSMC | 地市名称 | str | 50 | 地市名称 |
| MC | 名称 | str | 50 | 资源名称 |
| WZ | 位置 | str | 200 | 地址或四至范围 |
| QTWTMS | 其他问题描述 | str | 100 | 问题描述 |
| BZ | 备注 | str | 254 | 备注信息 |
| WF/XFSSDB等 | 是否类字段 | str | 1 | 0：否，1：是 |
| TDQS/JGXS等 | 分类类字段 | str | 2 | 分类代码 |
| HS/LDS等 | 数量类字段 | int | - | 整数 |
| YDMJ/JZMJ等 | 面积类字段 | float | - | 浮点数 |

### 几何类型分配

- **Point（点）**：建筑、设施、场站等（52个文件，61.9%）
- **Polygon（面）**：小区、厂区、街区等（22个文件，26.2%）
- **LineString（线）**：道路、管线等（10个文件，11.9%）

## 工作流程

### 步骤1：环境准备

```bash
# 安装Python依赖
pip install fiona geopandas shapely

# 验证安装
python -c "import fiona; import geopandas; print('OK')"
```

### 步骤2：运行创建脚本

```bash
# 进入工作目录
cd "E:\code\my-ai-workspace\myk\调研笔记\城市更新政策研究\database_schema"

# 运行创建脚本
python create_shapefiles.py
```

### 步骤3：验证结果

```bash
# 进入输出目录
cd "城市更新资源空表_最终版"

# 验证文件数量和结构
python verify_shapefiles.py
```

### 步骤4：在GIS软件中使用

**ArcGIS：**
1. 打开ArcMap或ArcGIS Pro
2. 添加数据 → 选择.shp文件
3. 字段别名会自动从XML文件读取

**QGIS：**
1. 打开QGIS
2. 图层 → 添加图层 → 添加矢量图层
3. 参考 `_字段说明.csv` 了解字段含义

## 文件结构

```
城市更新资源空表_最终版/
├── FCTZF.shp              # 非成套住房（面）
├── FCTZF.shx              # 几何索引
├── FCTZF.dbf              # 属性数据
├── FCTZF.prj              # 坐标系定义
├── FCTZF_字段说明.csv     # 字段说明
├── FCTZF.shp.xml          # ArcGIS元数据
├── ...                    # 其他83个文件
├── verify_all.py          # 验证脚本
└── 84个Shapefile完整清单.md  # 完整清单
```

## 常见问题

### Q1: 字段长度为什么不是80？
A: 按照《河北省城市更新资源数据成果汇交要求》，字段长度需要精确设置，如BSM为18位，DSDM为6位等。

### Q2: 如何在ArcGIS中看到中文别名？
A: Shapefile的.dbf文件不支持中文别名，但生成了配套的XML文件，ArcGIS会自动读取。

### Q3: 如何修改字段结构？
A: 编辑 `create_shapefiles.py` 中的字段定义字典，然后重新运行脚本。

### Q4: 几何类型如何确定？
A: 根据附件2的要求，按照资源类型分配：
- 点：建筑、设施、场站
- 线：道路、管线
- 面：小区、厂区、街区

## 参考文档

- 《河北省城市更新资源数据成果汇交要求（试行）》
- `84个Shapefile完整清单.md` - 完整的文件清单
- `工作日志_2026-07-14.md` - 创建工作记录

## 技术实现

使用 `fiona` 库创建Shapefile，精确控制字段类型和长度：

```python
import fiona
from fiona.crs import from_epsg

schema = {
    'geometry': 'Polygon',
    'properties': {
        'BSM': 'str:18',
        'DSDM': 'str:6',
        'DSMC': 'str:50',
        # ... 其他字段
    }
}

with fiona.open('output.shp', 'w', 
                driver='ESRI Shapefile',
                crs=from_epsg(4490),
                schema=schema,
                encoding='utf-8') as dst:
    pass  # 创建空表
```

## 版本历史

- v1.0 (2026-07-14): 初始版本，创建84个Shapefile
- v2.0 (2026-07-14): 修复字段长度问题
- v3.0 (2026-07-14): 修复几何类型问题，完整创建84个文件
- v4.0 (2026-07-14): 封装为技能，支持多平台调用
