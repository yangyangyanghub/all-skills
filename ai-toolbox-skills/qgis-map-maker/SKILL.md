---
name: qgis-map-maker
description: >
  基于 PyQGIS 的自动化地图制图技能。支持一键加载 Shapefile / GeoJSON 矢量数据，
  智能读取数据结构和字段信息，提供预制样式模板，交互式选择图层、样式、输出规格后
  自动生成出版级地图（PNG / PDF）。
  当用户提到 "制图"、"地图"、"出图"、"map"、"Shapefile"，
  或要求生成/制作任何类型的专题地图时必须使用此技能。
  也适用于 "帮我做一张图"、"把 shp 导出图片"、"GIS 出图" 等场景。
---

# QGIS 地图制图师

基于 PyQGIS 引擎的自动化制图工具。从数据加载到图片导出，全流程自动化。

## 核心能力

| 功能 | 说明 |
|------|------|
| 🔍 数据探查 | 自动读取 Shapefile/GeoJSON 的 CRS、几何类型、要素数、字段列表 |
| 📂 图层选择 | 列出数据目录所有 shp 文件，用户勾选需要显示的图层 |
| 🎨 模板样式 | 预制 5 种专业地图模板，一键应用配色方案 |
| 📐 输出规格 | A4/A3 纵横、DPI、PNG/PDF 可选 |
| 🏷️ 智能标注 | 自动检测名称字段，支持中文标注避让 |
| 🗺️ 地图要素 | 标题、图例、比例尺、指北针自动生成 |

## 交互流程

### 第一步：数据探查

**环境检测**：先确认 QGIS 可用。
1. 尝试默认路径：`C:\Program Files\QGIS 3.40.9\bin\python-qgis-ltr.bat`
2. 若不存在，自动搜索：`dir "C:\Program Files\QGIS*" /b` 找到最新版本
3. 仍未找到时，询问用户："未检测到 QGIS，请提供 python-qgis-ltr.bat 路径"
4. 记住检测到的路径，后续步骤复用。

当用户提供数据目录路径时，运行数据探查脚本：

```bash
& "<QGIS路径>\python-qgis-ltr.bat" scripts/inspect_data.py --data <数据目录路径>
```

向用户展示探测结果后，**询问确认**：
```
📊 数据探查完成，共 4 个图层，坐标系 EPSG:4499。
请问：
1. 是否需要调整图层显示顺序？（默认底→顶）
2. 是否需要排除某个图层？（直接告诉我图层名）
3. 确认可用？（回复"可以"进入下一步）
```

### 第二步：图层选择、模板选择与输出规格

**数据探查结果展示格式**（供参考）：
```
📂 检测到 4 个图层：
  ☑ 水体_p.shp      面(Polygon)   300 要素
  ☑ 市_点_p.shp    点(Point)      9 要素   [可标注字段: NAME]
  ☑ 市级行政区划.shp  面(Polygon)  9 要素
  ☑ 道路_p.shp      线(Polyline)  1198 要素

🌍 坐标系: EPSG:4499 (CGCS2000 / Gauss-Kruger zone 21)
```

#### 2.1 图层列表确认

向用户展示图层列表，默认全选，用户可去掉不需要的：
```
☑ 水体_p.shp（面，底图）
☑ 市_点_p.shp（点，标注）
☑ 道路_p.shp（线，交通）

图层顺序（底→顶）：[水体] → [道路] → [标注点]
是否需要调整？（回复图层名调整顺序，或"不用"继续）
```

#### 2.2 模板/样式选择

每个专题脚本内置独立样式。常见场景直接选择对应脚本：

| 场景 | 脚本 | 说明 |
|------|------|------|
| **城市关系强度图** | `city_relationship_map_v2.py` | 连线分级渲染（弱/中/强强度），通用地图基座 |
| **梵高星月夜路网** | `road_map_starry_night.py` | 深蓝底图 + 金色流线道路 + 星光标注 |
| **人口分布图** | `dot_density_map.py` | 点密度渲染 |
| **水系/政区/交通等** | 复制 `city_relationship_map_v2.py` | 修改样式参数即可 |

💡 **快速选择**：
- 有连线分级需求 → `city_relationship_map_v2.py`
- 需要艺术化风格 → `road_map_starry_night.py`
- 其他专题 → 基于 `city_relationship_map_v2.py` 新建脚本

#### 2.3 输出规格（必须询问）

**⚠️ 铁律：不得跳过此步骤直接执行。必须展示输出选项并等待用户回复。**

```
📐 输出设置（请选择或回复"默认"使用推荐值）：

📄 纸张尺寸：
  A4 (210×297mm) | A3 (297×420mm) | A2 (420×594mm) | A1 (594×841mm)
  （根据数据范围建议：省级→A3，市级→A4，小区域→A4纵向）

🔄 纸张方向：
  纵向 (Portrait) | 横向 (Landscape)
  （东西跨度大→横向，南北跨度大→纵向）

⚙️ 分辨率：
  150 DPI (预览/屏幕查看) | 300 DPI (标准/文档插入) | 600 DPI (印刷出版)

📁 输出格式：
  PNG (推荐) | PDF (可打印矢量)

💡 快捷回复示例：
  • "A3 横向 300DPI PNG" — 默认推荐
  • "A4 纵向 300DPI" — 文档插入
  • "默认" — 使用 A3 横向 300DPI PNG
```

#### 2.4 地图要素配置

```
🗺️ 地图要素（默认全部包含，可回复"去掉图例"等调整）：
  ☑ 标题（自动生成，如"人口分布图"）
  ☑ 图例（图层符号说明）
  ☑ 比例尺（公里单位）
  ☑ 指北针
  ☑ 数据来源标注（默认"公开地理信息数据"，可自定义）
```

### 第三步：执行制图

收集完所有参数后，调用核心制图引擎：

```bash
& "<QGIS路径>\python-qgis-ltr.bat" scripts/city_relationship_map_v2.py \
  --data <数据目录> \
  --output <输出 PNG 路径> \
  --paper-size <A4|A3|A2|A1|A0> \
  --orientation <portrait|landscape> \
  --dpi <DPI值> \
  --title <地图标题> \
  --source <数据来源>
```

### 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--data` | ✅ | Shapefile 所在目录 |
| `--output` | ❌ | 输出路径，默认 `assets/generated/地图.png` |
| `--paper-size` | ❌ | 纸张尺寸，可选：`A4` `A3` `A2` `A1` `A0`，默认 `A3` |
| `--orientation` | ❌ | 纸张方向，可选：`portrait`（纵向） `landscape`（横向），默认 `landscape` |
| `--dpi` | ❌ | 分辨率，默认 300 |
| `--title` | ❌ | 地图标题 |
| `--source` | ❌ | 数据来源标注，如 `"自然资源局"` |

> **注意**：`--paper-size` 和 `--orientation` 组合自动计算 `--width` 和 `--height`，无需手动指定毫米值。
> 如需自定义尺寸，仍可使用 `--width` 和 `--height`（单位 mm）。

### 纸张尺寸参考

| 尺寸 | 纵向 (宽×高 mm) | 横向 (宽×高 mm) |
|------|----------------|----------------|
| A4 | 210 × 297 | 297 × 210 |
| A3 | 297 × 420 | 420 × 297 |
| A2 | 420 × 594 | 594 × 420 |
| A1 | 594 × 841 | 841 × 594 |
| A0 | 841 × 1189 | 1189 × 841 |

## 模板体系

每个专题脚本（如 `city_relationship_map_v2.py`, `road_map_starry_night.py`）内置独立的样式配置。
新增模板时，复制现有专题脚本并修改样式参数即可。

## 模板扩展方式

1. 复制 `scripts/city_relationship_map_v2.py` 为新文件（如 `scripts/new_topic_map.py`）
2. 修改 `apply_styles()` 函数中的配色方案
3. 修改 `main()` 中的参数解析（`--title`, `--source` 等）
4. 测试通过后入库：`scripts/` 目录

样式配置格式（在脚本中修改）：
```python
# 示例：政区地图样式
admin_symbol = QgsFillSymbol.createSimple({
    'color': '255,248,220,200',    # RGBA 填充
    'outline_color': '139,115,85', # RGB 描边
    'outline_width': '0.6'         # 描边宽度 (mm)
})
```

## 异常处理与 Fallback

### ⚠️ 铁律：禁止静默降级

**遇到技术问题时的正确处理方式：**
1. **停止执行**，不要自动尝试降级方案
2. **向用户报告**具体错误和可选方案
3. **等待用户决策**，用户同意后才继续

**错误示例（严格禁止）：**
```python
# ❌ 禁止：布局渲染失败后自动简化，未经用户同意
if layout_failed:
    use_simple_render()
```

**正确示例（必须执行）：**
```
❌ 遇到问题：QgsPrintLayout 渲染失败（API 兼容性问题）

可选方案：
A. 使用简化渲染（仅地图主体，无标题/图例/比例尺）— 快速出图
B. 尝试修复布局代码 — 可能耗时较长
C. 取消操作，手动在 QGIS 桌面版调整

请选择方案（A/B/C）：
```

### ⚠️ 铁律：禁止纯地图渲染

**任何输出给用户的地图必须包含完整的地图要素：标题、图例、比例尺、指北针、数据源。**

**严格禁止使用 `QgsMapRendererCustomPainterJob` 进行最终输出。** 该渲染器仅输出地图主体（无布局要素），输出结果不符合专业制图规范。

```python
# ❌ 严令禁止：纯地图渲染，缺少标题/图例/比例尺/指北针
from qgis.core import QgsMapRendererCustomPainterJob
job = QgsMapRendererCustomPainterJob(settings, painter)  # 禁止用于最终输出！

# ✅ 正确方式：基于 QgsPrintLayout 的完整布局渲染
from qgis.core import QgsPrintLayout
layout = QgsPrintLayout(project)
# ... 添加 map_item + title + legend + scalebar + north_arrow + source
exporter = QgsLayoutExporter(layout)
exporter.exportToImage(path, settings)
```

**如果布局渲染失败：**
- 不要自动降级到 `QgsMapRendererCustomPainterJob`
- 不要输出不带地图要素的半成品
- 必须停止执行，向用户报告错误并提供选项

### QGIS 3.40.9 API 兼容性备忘

| 废弃/变更 API | 正确用法 |
|---------------|----------|
| `QgsLayoutItemScaleBar.setNumberOfSegmentsRight()` | 已移除，只保留 `setNumberOfSegmentsLeft()` |
| `QgsLayoutItemScaleBar.setNumberOfSegments(2)` | 使用 `applyDefaultSize()` 自动计算 |
| `QgsLayoutItemLabel.setFont(QFont)` | 改用 `setTextFormat(QgsTextFormat)`（旧方法有 DeprecationWarning 但仍可用） |
| `QgsLayoutItemScaleBar.setFont(QFont)` | 同上，仍可用但有警告 |
| `QgsPrintLayout.pageCollection().page(0).setPageSize(QgsLayoutSize)` | ✅ 正确写法 |

**降级规则：**
- 任何样式、布局、渲染引擎的降级**必须**先征得用户同意
- 不得以"先出一版看看"为由跳过确认
- 用户回复后，记录降级选择，便于后续优化

### QGIS 环境问题
- **路径不存在**：默认 `C:\Program Files\QGIS 3.40.9\bin\python-qgis-ltr.bat` 找不到时，执行 `where qgis` 或 `dir "C:\Program Files\QGIS*" /b` 自动搜索安装路径，或询问用户。
- **QGIS 未安装**：提示 "检测到未安装 QGIS，请先安装 QGIS 3.x 或指定 python-qgis-ltr.bat 路径"。
- **API 兼容性**：QGIS 版本升级可能导致部分 API 废弃（如 `QgsComposition` → `QgsPrintLayout`）。遇到此类问题时，**不要自行降级**，应向用户报告具体错误信息并等待指示。常见兼容问题：
  - `QgsComposition` 已废弃 → 使用 `QgsPrintLayout`
  - `QgsLayoutItemPage.setPageSize()` 签名变化 → 使用 `setPageSizeWithUnits()`
  - `QgsPalLayerSettings.Centroid` 枚举变更 → 检查 QGIS 版本文档
  - **指北针 SVG 路径变更** → `share/svg/north_arrows/` 已废弃，改为 `apps/qgis-ltr/svg/arrows/NorthArrow_*.svg`（QGIS 3.40.9）

### 数据问题
- **数据目录为空/无 shp**：提示 "目录中未找到 .shp 文件，请确认路径正确"，停止后续步骤。
- **shp 文件损坏**：`inspect_data.py` 报错时，提示 "[文件名] 无法读取，可能已损坏"，跳过该文件继续探查其他。
- **CRS 不一致**：探测到多个图层 CRS 不同时，**必须警告用户**："⚠️ 检测到不同坐标系（图层A: EPSG:XXXX, 图层B: EPSG:YYYY），叠加可能偏移。建议统一 CRS 后重试。" 但**仍允许用户确认后继续**。
- **Excel 关联失败**：人口数据 Excel 无法与行政区划匹配时，提示用户检查关联字段（PAC/NAME），不得强行渲染。

### 制图执行失败
- **引擎报错**：脚本返回非零退出码时，输出完整错误日志，并提供排查指引：
  ```
  ❌ 制图失败，常见原因：
  1. 数据目录不存在或无.shp文件 → 检查--data参数路径
  2. 数据文件被占用（如QGIS桌面版打开）→ 关闭QGIS后重试
  3. 输出路径无权限 → 检查磁盘空间或更换输出目录
  4. QGIS API兼容性问题 → 报告具体错误行号，查阅references/pyqgis-api-reference.md
  
  请根据错误信息调整后重试，或告知我具体报错内容。
  ```
- **输出路径不存在**：自动创建父目录（`os.makedirs(output_dir, exist_ok=True)`），**并告知用户**已创建。
- **输出目录无权限**：回退到 `assets/generated/` 前**必须告知用户**："输出目录无权限，已回退到备用路径：assets/generated/"。
- **样式/布局问题**：如果默认样式库或布局引擎不可用，**不得静默降级**。必须向用户报告并询问处理方式。

### 执行前确认（阻塞性步骤）

调用制图引擎**之前**，必须向用户展示最终参数并等待明确确认。**未获得确认不得执行。**

```
🚀 即将开始制图，参数如下：
  📂 数据目录：D:/gis_data/
  📑 图层：水体_p, 市_点_p, 市级行政区划, 道路_p（4个）
  🎨 模板：政区地图（典雅）
  📐 输出：A3 横向 300DPI → PNG
  🗺️ 要素：标题+图例+比例尺+指北针+数据来源
  💾 保存到：assets/generated/政区地图_20260414.png

确认开始？[是/否]（请明确回复）
```

**确认规则（严格执行）：**
- 用户回复"是"/"确认"/"开始" → 执行
- 用户回复"否"/"调整" → 返回第二步修改参数
- 用户提出修改意见 → 更新参数后再次确认
- **用户未回复或回复不明确 → 等待，绝对不得执行**
- 任何参数变更（即使用户只改了 DPI）→ 重新展示完整参数并确认

## 脚本目录维护

`scripts/` 目录仅保留核心脚本，定期清理临时文件：
- ✅ 保留：`city_relationship_map_v2.py`（城市关系/通用地图基座）, `road_map_starry_night.py`（星月夜路网）, `inspect_data.py`, `dot_density_map.py`, `create_od_lines.py`, `read_excel.py`, `relationship_map.py`
- ❌ 清理：`map_engine.py`（已废弃，由专题脚本替代）, `temp_inspect.py`, `inspect_result.txt`, `quick_inspect.py`, `__pycache__/`（运行残留）
- ⚠️ 新增专题脚本必须以 `QgsPrintLayout` 为渲染基座，测试通过后入库，测试脚本使用后删除

## 注意事项

- 坐标系自动从数据文件中读取，无需手动指定
- 中文标注优先使用 NAME/名称/市名 等常见字段
- QGIS 安装路径可根据实际版本调整（见"异常处理"章节的自动搜索机制）
- **PyQGIS API 变更**: 遇到参数签名错误、属性不存在时，**优先查阅** `references/pyqgis-api-reference.md`，确认当前 QGIS 版本的正确用法
  - 文档地址: https://qgis.org/pyqgis/master/core/
  - 构建工具仓库: https://github.com/qgis/pyqgis-api-docs-builder

## 交互规范检查清单

每次执行制图任务前，**必须**逐项确认：

- [ ] 已展示输出规格选项（纸张/方向/DPI/格式）并等待用户回复
- [ ] 已展示地图要素配置并得到确认
- [ ] 已展示完整参数汇总（执行前确认）
- [ ] 已获得用户明确的"是/确认/开始"回复
- [ ] 未遇到技术问题时，未自行降级处理
- [ ] **使用 QgsPrintLayout 渲染，未使用 QgsMapRendererCustomPainterJob**
- [ ] 临时脚本已清理（`temp_*.py`, `__pycache__`）
- [ ] 遇到 API 报错时，已查阅 `references/pyqgis-api-reference.md` 确认正确用法

**输出后自检清单**（导出完成后必须执行）：

### 零、自动化验证（脚本执行后自动检查）
1. 使用 `look_at` 工具查看输出图片
2. 按以下清单逐项确认，**任一不通过则修正后重新导出**

### 一、要素完整性
- [ ] 标题存在且位置正确（地图区域外部，顶部居中）
- [ ] 图例存在且包含所有图层符号说明（地图内部右下角）
- [ ] 比例尺存在且单位合理（地图内部底部居中）
- [ ] 指北针存在（地图内部右上角）
- [ ] 数据来源标注存在（地图内部左下角）

### 二、要素位置合理性
- [ ] 所有地图要素均在页面范围内，**无超出页面边界**
- [ ] 比例尺、图例、数据源、指北针**不与地图内容（标注、连线、边界）重叠**
- [ ] 图例带有**半透明背景**，不遮挡地图内容

### 三、地图内容完整性
- [ ] **行政区边界完整**，无任何边界线被图框截断
- [ ] **所有图层内容（连线、点标注、多边形）完整可见**，无出图框现象
- [ ] 标注文字不被图例、比例尺等要素遮挡

### 四、字体与协调性
- [ ] 标题字号适中（A3 横版推荐 20pt Bold），与地图比例协调
- [ ] 图例、比例尺、数据源字体清晰可读（推荐 7-8pt）

### 五、技术规范检查
- [ ] 地图框尺寸与设定值一致（`actual_rect` = `map_w`x`map_h`）
- [ ] 地图比例缩放合理（`extent.scale(1.15)` 保证边界不贴边）
- [ ] 所有 overlay 元素通过 `raiseItem()` 提升层级

**任一项自检未通过，不得交付给用户，必须修正后重新导出。**
