# 城市更新资源Shapefile创建技能

## 技能简介

本技能用于创建符合《河北省城市更新资源数据成果汇交要求》的84个Shapefile空表，包含正确的字段长度、几何类型和坐标系设置。

## 在不同平台使用

### 1. OpenCode

在OpenCode中，技能会自动加载。当你提到相关关键词时，AI会自动使用这个技能。

**触发方式：**
- 直接说："帮我创建城市更新资源的Shapefile"
- 或："按照汇交要求创建GIS空表"
- 或："生成84个Shapefile文件"

**使用示例：**
```
用户：帮我创建城市更新资源的Shapefile空表
AI：[自动加载city-renewal-shapefile技能]
    [运行create_shapefiles.py脚本]
    [生成84个Shapefile文件]
```

### 2. Claude Code

在Claude Code中，技能文件位于 `~/.claude/skills/city-renewal-shapefile/`。

**步骤：**
1. 将技能目录复制到Claude Code的技能目录：
   ```bash
   cp -r C:\Users\HP\.config\opencode\skills\city-renewal-shapefile ~/.claude/skills/
   ```

2. 在Claude Code中使用：
   ```
   用户：创建城市更新资源数据库
   Claude：[读取SKILL.md]
           [执行create_shapefiles.py]
   ```

### 3. WorkBuddy

WorkBuddy支持自定义技能。

**配置步骤：**
1. 在WorkBuddy中添加技能目录
2. 指向 `C:\Users\HP\.config\opencode\skills\city-renewal-shapefile\`
3. WorkBuddy会自动识别SKILL.md

**使用方式：**
```
用户：我需要创建符合汇交要求的Shapefile
WorkBuddy：[加载技能]
           [询问输出目录]
           [运行脚本]
           [验证结果]
```

## 技能文件结构

```
city-renewal-shapefile/
├── SKILL.md                    # 技能定义文件
├── create_shapefiles.py        # 创建脚本
├── verify_shapefiles.py        # 验证脚本
└── README.md                   # 本文件
```

## 手动使用（不依赖AI）

如果你不想通过AI调用，也可以直接使用Python脚本：

```bash
# 1. 安装依赖
pip install fiona geopandas shapely

# 2. 运行创建脚本
python create_shapefiles.py

# 3. 验证结果
python verify_shapefiles.py
```

## 自定义修改

### 修改输出目录

编辑 `create_shapefiles.py`，修改第13行：

```python
output_dir = Path("你的输出目录")
```

### 修改字段结构

编辑 `create_shapefiles.py`，修改各资源类型的字段定义，例如：

```python
'BSM': ('str', 18),      # 修改长度
'DSDM': ('str', 6),      # 修改长度
'NEW_FIELD': ('str', 50), # 添加新字段
```

### 修改几何类型

编辑 `create_shapefiles.py`，修改几何类型参数：

```python
create_empty_shapefile(
    "FCTZF", "Polygon",  # 改为 "Point" 或 "LineString"
    {...}
)
```

## 技能触发关键词

以下关键词会触发本技能：

- 城市更新
- Shapefile
- 空表
- 汇交要求
- GIS数据库
- 字段长度
- 几何类型
- 84个文件
- CGCS2000
- EPSG:4490

## 依赖要求

- Python 3.7+
- fiona
- geopandas
- shapely

安装命令：
```bash
pip install fiona geopandas shapely
```

## 输出文件

运行后会生成：

- 84个Shapefile文件（.shp, .shx, .dbf, .prj）
- 84个字段说明CSV文件
- 84个ArcGIS元数据XML文件
- 验证报告

## 验证结果

```
======================================================================
84个Shapefile完整性验证
======================================================================

总文件数: 84

关键文件验证:
----------------------------------------------------------------------
非成套住房                       | 几何: OK   | 字段: OK   | 19个字段
C级危险住房                      | 几何: OK   | 字段: OK   | 15个字段
...

验证完成
======================================================================
```

## 故障排除

### 问题1：ImportError: No module named 'fiona'

**解决：**
```bash
pip install fiona
```

### 问题2：字段长度还是80

**原因：** 使用了旧版本的脚本

**解决：** 确保使用 `create_shapefiles.py`（不是create_shapefiles_final.py）

### 问题3：几何类型错误

**原因：** 脚本中的geometry参数设置错误

**解决：** 检查create_empty_shapefile调用的第二个参数

## 版本历史

- v1.0 (2026-07-14): 初始版本
- v2.0 (2026-07-14): 修复字段长度问题
- v3.0 (2026-07-14): 修复几何类型问题
- v4.0 (2026-07-14): 封装为技能，支持多平台调用

## 联系和支持

如有问题，请查看：
- `SKILL.md` - 详细使用说明
- `84个Shapefile完整清单.md` - 文件清单
- `工作日志_2026-07-14.md` - 创建记录
