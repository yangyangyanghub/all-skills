# 预制地图模板库

每个模板定义了面/线/点三种几何类型的配色方案和标注参数。

## 模板总览

| 模板名 | 图标 | 分类 | 适用场景 |
|--------|------|------|---------|
| `water` | 🌊 | 基础类 | 河流、湖泊、水文 |
| `admin` | 🏛️ | 基础类 | 政务报告、行政管理 |
| `transport` | 🛣️ | 基础类 | 公路、铁路、交通规划 |
| `minimal` | ⚡ | 基础类 | 论文插图、通用底图 |
| `landuse` | 🌾 | 自然地理类 | 耕地、林地、建设用地 |
| `geology` | 🪨 | 自然地理类 | 地层、岩性、构造 |
| `vegetation` | 🌿 | 自然地理类 | 森林、草原、湿地 |
| `population` | 👥 | 人文经济类 | 人口密度、迁移 |
| `economy` | 📊 | 人文经济类 | GDP、产业布局 |
| `planning` | 📐 | 规划工程类 | 国土空间用途管制 |
| `environment` | 🌍 | 规划工程类 | 环评、生态敏感区 |
| `heatmap` | 🔥 | 特殊用途 | 分级设色统计 |
| `military` | ⚔️ | 特殊用途 | 军事地形 |
| `nautical` | ⛵ | 特殊用途 | 水深、航道 |
| `starry_night` | 🌌 | 艺术风格 | 梵高星月夜、暗色城市 |

## 配色参考

模板配色遵循专业地图制图规范：
- **水系图**：蓝色系（天蓝+品蓝）符合国际水文图规范
- **政区图**：米黄色+棕线，暖色调庄重典雅
- **交通图**：灰调主体+橙色关键节点，突出路网层次
- **土地利用**：绿色系（浅绿+森林绿）表现植被土地类型
- **地质图**：土黄+栗棕，表现地层岩性感
- **人口/经济**：品红/金色，高饱和度吸引注意力
- **规划图**：紫色系（梅紫+紫罗兰），规划专用色
- **环保图**：绿色底+橙红警戒边，环保+警示结合
- **军事图**：军橄榄绿（#6B8E23），专业军事制图标
- **航海图**：海军蓝+天蓝，国际航海图标准色

### 1. 🌊 水系地图（water）

河流、湖泊、水库等水体专题地图。

```json
{
  "name": "water",
  "icon": "🌊",
  "title": "水 系 地 图",
  "styles": {
    "polygon": {
      "description": "面状水体（湖泊、水库）",
      "color": "100,180,255,200",
      "outline_color": "25,100,200",
      "outline_width": "0.5"
    },
    "line": {
      "description": "线状水系（河流）",
      "color": "65,105,225",
      "width": "0.8",
      "capstyle": "round"
    },
    "point": {
      "description": "水文站点",
      "color": "50,50,50",
      "size": "2.5",
      "outline_color": "255,255,255",
      "outline_width": "0.5"
    },
    "label": {
      "font_family": "Microsoft YaHei",
      "font_size": 9,
      "color": "30,30,30",
      "buffer_color": "255,255,255",
      "buffer_size": "0.8"
    }
  }
}
```

### 2. 🏛️ 政区地图（admin）

行政区划图，政务报告用途。

```json
{
  "name": "admin",
  "icon": "🏛️",
  "title": "行 政 区 划 图",
  "styles": {
    "polygon": {
      "description": "行政区域面",
      "color": "255,248,220,200",
      "outline_color": "139,115,85",
      "outline_width": "0.6"
    },
    "line": {
      "description": "行政边界线",
      "color": "169,169,169",
      "width": "0.4",
      "capstyle": "square"
    },
    "point": {
      "description": "行政中心",
      "color": "200,0,0",
      "size": "3.0",
      "outline_color": "255,255,255",
      "outline_width": "0.8"
    },
    "label": {
      "font_family": "Microsoft YaHei",
      "font_size": 10,
      "color": "20,20,20",
      "buffer_color": "255,255,255",
      "buffer_size": "1.0"
    }
  }
}
```

### 3. 🛣️ 交通路网（transport）

道路、铁路、航线等交通专题图。

```json
{
  "name": "transport",
  "icon": "🛣️",
  "title": "交 通 路 网 图",
  "styles": {
    "polygon": {
      "description": "区域底色",
      "color": "245,245,245,80",
      "outline_color": "200,200,200",
      "outline_width": "0.3"
    },
    "line": {
      "description": "道路/铁路",
      "color": "100,100,100",
      "width": "0.5",
      "capstyle": "round"
    },
    "point": {
      "description": "交通枢纽",
      "color": "255,140,0",
      "size": "3.0",
      "outline_color": "50,50,50",
      "outline_width": "0.5"
    },
        "label": {
            "font_family": "Microsoft YaHei",
            "font_size": 8,
            "color": "0,0,80",
            "buffer_color": "255,255,255",
            "buffer_size": 0.6
        }
    }
}
```

### 6. 🌌 梵高星月夜（starry_night）

艺术风格地图。深蓝夜空背景，建筑呈现发光质感，致敬梵高名作。

```json
{
    "name": "starry_night",
    "icon": "🌌",
    "title": "梵 高 · 星 月 夜",
    "styles": {
        "polygon": {
            "description": "建筑/面状要素（深蓝填充，深色描边）",
            "color": "44,90,160,180",
            "outline_color": "10,26,58",
            "outline_width": "0.8"
        },
        "line": {
            "description": "路网（隐身模式，与极深背景融为一体）",
            "color": "10,15,28",
            "width": "0.8",
            "capstyle": "round"
        },
        "point": {
            "description": "高亮要素（黄色光点）",
            "color": "249,215,28",
            "size": "2.5",
            "outline_color": "249,215,28",
            "outline_width": "1.0"
        },
        "label": {
            "font_family": "Microsoft YaHei",
            "font_size": 8,
            "color": "212,224,245",
            "buffer_color": "10,26,58",
            "buffer_size": 1.0
        }
    }
}
```

## 画幅预设

| 预设 | 宽度 mm | 高度 mm | 说明 |
|------|---------|---------|------|
| A4纵向 | 210 | 297 | 报告插图常用 |
| A4横向 | 297 | 210 | PPT 插入常用 |
| A3纵向 | 297 | 420 | 海报 |
| A3横向 | 420 | 297 | 大幅展示 |

## 输出设置

- 地图框边距：上下 15mm，左右 20mm
- 图例：右下角，70mm 宽
- 比例尺：左下角，自动适配地图范围
- 指北针：右上角，12x12mm
- 标题：顶部居中，字号 20pt 加粗

---

## CARTOColors 配色方案

来源：https://carto.com/carto-colors/
专为地图数据可视化设计，支持浅色/深色底图适配。

### 顺序色带（Sequential）- 适合数值型数据（人口密度、高程等）

| 名称 | 色阶（5级 HEX） | 适用场景 |
|------|----------------|---------|
| burg | `#840000` → `#E60033` → `#E85D75` → `#ECAE91` → `#F0E7CB` | 深色底图、风险等级 |
| burgyl | `#810F7C` → `#88419D` → `#8C96C6` → `#B3CDE3` → `#EDF8FB` | 紫色到蓝、学术研究 |
| burgyn | `#810F7C` → `#88419D` → `#6BAED6` → `#4292C6` → `#2171B5` | 紫到蓝、温度变化 |
| emrld | `#045040` → `#04693E` → `#01843C` → `#02A13A` → `#56BC4B` | 翡翠绿、植被/生态 |
| bluyl | `#014057` → `#03627C` → `#0B88A0` → `#54B0CB` → `#C2DCF1` | 蓝到黄、温度/水深 |
| ag_sunset | `#2A043B` → `#6D0F50` → `#C81F57` → `#FE5433` → `#FECF3A` | 日落色、热力/密度 |
| teal | `#00384D` → `#004F66` → `#006D80` → `#0092A1` → `#2ABFC7` | 深青色、海洋深度 |
| darkmint | `#014F4D` → `#00605E` → `#007A6E` → `#0EA58A` → `#5BD3B0` | 薄荷绿、深色底图 |
| mint | `#B0F2BC` → `#76DBB1` → `#45C48C` → `#3BA87C` → `#1A7A5C` | 明亮薄荷、浅色底图 |
| peach | `#2C010B` → `#8B0110` → `#C93A19` → `#E77338` → `#F5AF7A` | 暖色、人口/经济 |
| pinkyl | `#380C3B` → `#7D0D45` → `#C42D43` → `#E87E4B` → `#FFD08C` | 粉到黄、分类统计 |
| purp | `#402062` → `#6A276E` → `#963074` → `#C03D78` → `#E55A7C` | 紫色系、规划/专题 |
| purpor | `#3B0059` → `#7A007A` → `#B3007A` → `#E0405E` → `#FFB36A` | 紫红到橙、风险图示 |
| redor | `#7A0011` → `#BB0026` → `#F02B3E` → `#FF7F5E` → `#FFD29C` | 红到橙、高温/密度 |
| sunset | `#2D0940` → `#7B0831` → `#CC3F28` → `#F08033` → `#FBD14A` | 日落渐变、综合专题 |
| sunsetdark | `#230B30` → `#6D0F50` → `#C81F57` → `#FE5433` → `#FECF3A` | 深日落、暗色底图 |
| ylgd | `#562800` → `#8B4500` → `#C47A2B` → `#E8B95C` → `#F5E8A0` | 黄绿到金、土地/农业 |
| ylmag | `#3B1900` → `#8B3A00` → `#D45400` → `#E88A3A` → `#FFD08C` | 黄到品红、经济统计 |
| ylgn | `#006837` → `#238B45` → `#41AB5D` → `#78C679` → `#C7E9C0` | 黄绿、植被覆盖率 |
| ylorbr | `#8C510A` → `#BF812D` → `#DFC27D` → `#F6E8C1` → `#FFFFCC` | 黄橙棕、地质/土壤 |
|ylorrd | `#800026` → `#BD0026` → `#E31A1C` → `#FC4E2A` → `#FD8D3C` | 黄橙红、人口密度 |

### 发散色带（Diverging）- 适合正负对比数据

| 名称 | 色阶 | 适用场景 |
|------|------|---------|
| armsosa | `#C2185B` → `#E57373` → `#F5F5F5` → `#90CAF9` → `#1976D2` | 红到蓝、温度异常 |
| curl | `#D7301F` → `#FC8D59` → `#FEE090` → `#E0F3F8` → `#4575B4` | 橙到蓝、降雨偏差 |
| earth | `#8B4513` → `#D2B48C` → `#F5F5DC` → `#87CEEB` → `#1E90FF` | 土色到蓝、海拔正负 |
| geyser | `#CB4335` → `#F1948A` → `#FDFEFE` → `#85C1E9` → `#2E4057` | 红到灰蓝、地质 |
| temps | `#2B83BA` → `#ABD9E9` → `#FFFFFF` → `#FDAE61` → `#D7191C` | 冷到热、温度对比 |
| tealrose | `#006D6F` → `#4DB6AC` → `#F5F5F5` → `#F48FB1` → `#AD1457` | 青到玫瑰、对比鲜明 |
| fall | `#556B2F` → `#DAA520` → `#FFF8DC` → `#FF6347` → `#8B0000` | 秋色、季节变化 |

### 分类色带（Qualitative）- 适合类别区分

| 名称 | 颜色数 | HEX 色值 | 适用场景 |
|------|--------|---------|---------|
| antique | 9 | `#8DD3C7` `#FFFFB3` `#BEBADA` `#FB8072` `#80B1D3` `#FDB462` `#FCCDE5` `#D9C4A6` `#BC80BD` | 行政区划 |
| bold | 9 | `#E58606` `#5D69B1` `#52BCA3` `#99C7DB` `#9B6F9B` `#FF9B3C` `#6D58C4` `#8BDB4C` `#F7523F` | 高对比分类 |
| pastel | 9 | `#B3E2CD` `#FDCDAC` `#D4A5A5` `#CCEBC5` `#FCCDE5` `#B3DE69` `#BC80BD` `#FFED6F` `#80B1D3` | 柔和分类 |
| safe | 7 | `#CCBC4B` `#4CB4E8` `#E88C4C` `#5BB09C` `#C86BCD` `#E85C5C` `#7AA4E3` | 色盲友好 |
| vivid | 9 | `#E58606` `#5D69B1` `#52BCA3` `#99C7DB` `#9B6F9B` `#FF9B3C` `#6D58C4` `#8BDB4C` `#F7523F` | 鲜明对比 |
| prism | 9 | `#5EBE8E` `#E58606` `#5D69B1` `#FF6B6B` `#FFD93D` `#6BCB77` `#4D96FF` `#FF6B9D` `#C084E8` | 多类区分 |

### PyQGIS 使用 CARTOColors 示例

```python
from qgis.core import QgsColorRampShader, QgsRasterShader, QgsSingleBandPseudoColorRenderer
from qgis.PyQt.QtGui import QColor

# 示例：使用 burg 色带渲染人口密度
burg_colors = [
    (0, QColor(240, 231, 203), "极低"),      # #F0E7CB
    (25, QColor(236, 174, 145), "低"),        # #ECAE91
    (50, QColor(232, 93, 117), "中"),         # #E85D75
    (75, QColor(230, 0, 51), "高"),           # #E60033
    (100, QColor(132, 0, 0), "极高"),         # #840000
]

fnc = QgsColorRampShader()
fnc.setColorRampType(QgsColorRampShader.Interpolated)
items = [QgsColorRampShader.ColorRampItem(v, c, l) for v, c, l in burg_colors]
fnc.setColorRampItemList(items)

shader = QgsRasterShader()
shader.setRasterShaderFunction(fnc)
renderer = QgsSingleBandPseudoColorRenderer(layer.dataProvider(), 1, shader)
layer.setRenderer(renderer)
layer.triggerRepaint()
```
