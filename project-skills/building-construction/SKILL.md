# Skill: 施工图生成器

建筑施工图生成，用于展示技术细节、材料做法和节点大样。

## 工具依赖

- **FreeCAD CLI**：CAD施工图生成
- **阿里千问VL**：辅助说明图生成

## 触发场景

当用户提到以下关键词时使用此技能：
- 施工图、节点图、大样图
- 墙身大样、门窗节点、屋面做法
- 材料做法、技术细节
- 建筑详图、构造详图

## 核心指令

### 步骤1：详图类型识别

| 详图类型 | 内容 | 用途 |
|---------|------|------|
| 墙身大样 | 外墙构造层次 | 材料做法 |
| 门窗节点 | 门窗框安装 | 密封防水 |
| 屋面做法 | 屋面构造层次 | 防水保温 |
| 楼梯详图 | 楼梯踏步做法 | 安全舒适 |
| 幕墙节点 | 幕墙龙骨安装 | 结构安全 |
| 变形缝 | 变形缝做法 | 结构安全 |
| 散水做法 | 散水构造 | 防水排水 |

### 步骤2：构造层次设计

**墙身大样层次**（由外到内）：
1. 饰面层（涂料/石材/幕墙）
2. 找平层（水泥砂浆）
3. 保温层（XPS/EPS/岩棉）
4. 防水层（防水卷材/涂料）
5. 结构层（混凝土/砌体）
6. 找平层（水泥砂浆）
7. 饰面层（涂料/壁纸）

**屋面做法层次**（由上到下）：
1. 保护层（细石混凝土）
2. 防水层（SBS/APP卷材）
3. 找平层（水泥砂浆）
4. 保温层（XPS/挤塑板）
5. 找坡层（陶粒混凝土）
6. 结构层（混凝土屋面板）

**门窗节点构造**：
1. 窗框（铝合金/塑钢/断桥铝）
2. 玻璃（中空/三层/ Low-E）
3. 密封胶（耐候胶/结构胶）
4. 填充材料（发泡剂/岩棉）
5. 收口材料（铝板/石材）

### 步骤3：尺寸标注规范

**标注内容**：
- 构造层次厚度
- 材料规格
- 做法说明
- 节点索引

**标注规范**：
- 尺寸线：细实线，箭头清晰
- 尺寸数字：字高3mm，水平书写
- 材料标注：引线+材料名称
- 做法说明：引线+做法描述

### 步骤4：FreeCAD脚本生成

**墙身大样脚本模板**：
```python
import FreeCAD
import Part
import Draft

def create_wall_section(length, height):
    """创建墙身剖面"""
    layers = []
    
    # 饰面层（涂料）
    finish = Part.makeBox(20, height, length)
    finish.translate(FreeCAD.Vector(0, 0, 0))
    layers.append(("饰面层", finish))
    
    # 找平层
    leveling = Part.makeBox(20, height, length)
    leveling.translate(FreeCAD.Vector(20, 0, 0))
    layers.append(("找平层", leveling))
    
    # 保温层
    insulation = Part.makeBox(50, height, length)
    insulation.translate(FreeCAD.Vector(40, 0, 0))
    layers.append(("保温层", insulation))
    
    # 防水层
    waterproof = Part.makeBox(10, height, length)
    waterproof.translate(FreeCAD.Vector(90, 0, 0))
    layers.append(("防水层", waterproof))
    
    # 结构层
    structure = Part.makeBox(200, height, length)
    structure.translate(FreeCAD.Vector(100, 0, 0))
    layers.append(("结构层", structure))
    
    # 内饰面
    inner_finish = Part.makeBox(20, height, length)
    inner_finish.translate(FreeCAD.Vector(300, 0, 0))
    layers.append(("内饰面", inner_finish))
    
    return layers

def add_dimensions(layers):
    """添加尺寸标注"""
    # 各层厚度标注
    # 总厚度标注
    # 材料标注
    pass

def add_material_labels(layers):
    """添加材料标注"""
    # 引线+材料名称
    # 做法说明
    pass

def export_dwg(filename):
    """导出DWG"""
    FreeCAD.ActiveDocument.saveAs(filename)

def generate_wall_section():
    """生成墙身大样"""
    # 1. 创建墙身剖面
    layers = create_wall_section(1000, 3000)
    
    # 2. 添加尺寸标注
    add_dimensions(layers)
    
    # 3. 添加材料标注
    add_material_labels(layers)
    
    # 4. 导出
    export_dwg("wall_section.dwg")

if __name__ == "__main__":
    generate_wall_section()
```

**屋面做法脚本模板**：
```python
import FreeCAD
import Part
import Draft

def create_roof_section(length):
    """创建屋面剖面"""
    layers = []
    
    # 保护层
    protection = Part.makeBox(40, 1000, length)
    protection.translate(FreeCAD.Vector(0, 0, 0))
    layers.append(("保护层", protection))
    
    # 防水层
    waterproof = Part.makeBox(10, 1000, length)
    waterproof.translate(FreeCAD.Vector(40, 0, 0))
    layers.append(("防水层", waterproof))
    
    # 找平层
    leveling = Part.makeBox(20, 1000, length)
    leveling.translate(FreeCAD.Vector(50, 0, 0))
    layers.append(("找平层", leveling))
    
    # 保温层
    insulation = Part.makeBox(80, 1000, length)
    insulation.translate(FreeCAD.Vector(70, 0, 0))
    layers.append(("保温层", insulation))
    
    # 找坡层
    slope = Part.makeBox(100, 1000, length)
    slope.translate(FreeCAD.Vector(150, 0, 0))
    layers.append(("找坡层", slope))
    
    # 结构层
    structure = Part.makeBox(120, 1000, length)
    structure.translate(FreeCAD.Vector(250, 0, 0))
    layers.append(("结构层", structure))
    
    return layers

def generate_roof_section():
    """生成屋面做法"""
    # 1. 创建屋面剖面
    layers = create_roof_section(1000)
    
    # 2. 添加标注
    # ...
    
    # 3. 导出
    export_dwg("roof_section.dwg")
```

### 步骤5：说明图生成

**提示词模板**：
```
建筑节点详图，{详图类型}，
构造层次清晰，
材料标注完整，
尺寸标注规范，
技术图纸风格，黑白线稿
```

**生成内容**：
- 节点透视图
- 材料说明图
- 做法流程图

## 输入格式

```
项目描述：
- 建筑类型：住宅/商业/办公/文化
- 结构形式：框架/剪力墙/钢结构
- 外墙材料：涂料/石材/幕墙
- 屋面形式：平屋面/坡屋面

详图需求：
- 详图类型：墙身/门窗/屋面/楼梯/幕墙
- 详图数量：X张
- 标注详细程度：详细/简洁

特殊要求：
- 材料品牌要求
- 做法特殊要求
- 节点复杂度

输出要求：
- 图纸比例：1:10/1:20/1:50
- 输出格式：DWG + PNG
- 标注要求：尺寸/材料/做法
```

## 输出格式

```
生成结果：

[墙身大样]
构造层次（由外到内）：
1. 饰面层：外墙涂料，厚5mm
2. 找平层：水泥砂浆，厚20mm
3. 保温层：XPS保温板，厚50mm
4. 防水层：防水涂料，厚2mm
5. 结构层：混凝土墙，厚200mm
6. 找平层：水泥砂浆，厚20mm
7. 饰面层：内墙涂料，厚3mm

总厚度：300mm

节点索引：
- A节点：墙身顶部收口
- B节点：墙身底部收口
- C节点：墙身转角做法

文件：wall_section.dwg + wall_section.png

[门窗节点]
构造组成：
1. 窗框：断桥铝合金，壁厚1.8mm
2. 玻璃：中空Low-E玻璃，6+12A+6
3. 密封胶：耐候密封胶，宽10mm
4. 填充材料：聚氨酯发泡剂
5. 收口材料：铝板收口

安装要求：
- 窗框与墙体连接：膨胀螺栓固定
- 密封处理：内外双道密封
- 防水处理：外侧打胶密封

文件：window_node.dwg + window_node.png

[屋面做法]
构造层次（由上到下）：
1. 保护层：细石混凝土，厚40mm
2. 防水层：SBS改性沥青卷材，厚4mm
3. 找平层：水泥砂浆，厚20mm
4. 保温层：XPS挤塑板，厚80mm
5. 找坡层：陶粒混凝土，最薄处30mm
6. 结构层：混凝土屋面板，厚120mm

总厚度：290mm

节点索引：
- A节点：屋面女儿墙收口
- B节点：屋面出入口做法
- C节点：屋面设备基础

文件：roof_section.dwg + roof_section.png

[楼梯详图]
踏步做法：
- 踏步高度：150mm
- 踏步宽度：300mm
- 面层材料：防滑地砖
- 防滑条：不锈钢防滑条

栏杆做法：
- 栏杆形式：不锈钢栏杆
- 栏杆高度：1100mm
- 扶手材质：实木扶手

文件：stair_detail.dwg + stair_detail.png

文件位置：./output/项目名称_施工图/
```

## 约束条件

### 必须遵守
- 符合建筑构造规范
- 构造层次合理、材料正确
- 尺寸标注准确、规范
- 做法说明清晰、完整

### 禁止行为
- 构造层次错误、材料不当
- 尺寸标注错误、遗漏
- 做法说明模糊、不完整
- 节点索引混乱、矛盾

## 质量检查

### 自检清单
- [ ] 构造层次合理、材料正确
- [ ] 尺寸标注准确、规范
- [ ] 做法说明清晰、完整
- [ ] 节点索引正确、无遗漏
- [ ] 符合建筑构造规范
- [ ] DWG文件可正常打开
- [ ] 图纸比例正确、清晰

## 错误处理

| 错误类型 | 处理方式 |
|---------|---------|
| 构造层次错误 | 检查规范、调整做法 |
| 尺寸标注错误 | 校对尺寸、重新标注 |
| 做法说明不全 | 补充说明、完善内容 |
| CAD生成失败 | 检查脚本、重新生成 |

## 使用示例

### 示例1：住宅墙身大样

**输入**：
```
项目：住宅
外墙：涂料+保温
结构：剪力墙
详图类型：墙身大样
```

**输出**：
```
[墙身大样]
构造层次（由外到内）：
1. 饰面层：外墙涂料，厚5mm
2. 找平层：水泥砂浆，厚20mm
3. 保温层：XPS保温板，厚50mm
4. 防水层：防水涂料，厚2mm
5. 结构层：混凝土墙，厚200mm
6. 找平层：水泥砂浆，厚20mm
7. 饰面层：内墙涂料，厚3mm

总厚度：300mm

文件：wall_section.dwg + wall_section.png
```

### 示例2：商业幕墙节点

**输入**：
```
项目：商业综合体
外墙：玻璃幕墙
结构：框架
详图类型：幕墙节点
```

**输出**：
```
[幕墙节点]
构造组成：
1. 龙骨：铝合金龙骨，壁厚3mm
2. 面板：中空Low-E玻璃，8+12A+8
3. 密封胶：结构胶+耐候胶
4. 保温层：岩棉保温板，厚80mm
5. 防火层：防火岩棉，厚100mm

安装要求：
- 龙骨与主体连接：预埋件+转接件
- 面板与龙骨连接：压块固定
- 密封处理：双道密封

文件：curtain_wall_node.dwg + curtain_wall_node.png
```
