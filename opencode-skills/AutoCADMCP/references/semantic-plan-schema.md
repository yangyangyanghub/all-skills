# 语义 `plan.json` 结构约定

`plan.json` 是预览、批量落图和校验三者共享的唯一几何真源。本文件说明它的字段、对象形态和落图前的校验要点。

## 目录

1. 顶层结构
2. 每个对象的证据字段
3. 各类对象写法
4. 展开成图元简写
5. 校验要点

## 1. 顶层结构

坐标一律毫米，笛卡尔坐标系，正 Y 为图纸上方（除非 `meta.orientation` 另有说明）。室内平面图用下面的结构：

```json
{
  "meta": {
    "title": "示例户型",
    "units": "mm",
    "plan_size": [8000, 6000],
    "orientation": "north-up",
    "reference_required": false,
    "source": "用户尺寸表",
    "assumptions": ["内墙厚按 120 推断"]
  },
  "layers": ["A-WALL-EXIST", "A-OPENING", "A-DOOR", "A-DOOR-SWING"],
  "walls": [],
  "openings": [],
  "windows": [],
  "sliding": [],
  "doors": [],
  "rooms": [],
  "fixed_furniture": [],
  "movable_furniture": [],
  "fixtures": [],
  "dims": [],
  "notes": [],
  "entities": []
}
```

`entities` 放 schema 没覆盖的中性细节或通用几何，字段见 [通用实体契约](general-plan-schema.md)。室内计划的其余数组即使为空也保留，方便校验和计数；非室内计划仅使用通用契约，不要求这些数组。

`meta.reference_required` 必须是布尔值：任务带图片、扫描、截图或已有 CAD 等几何真源时写 `true`，纯自主设计写 `false`。写 `true` 时，流程要求先完成原图对照审查（见 `pre-draw-gate.md`）再落图。

## 2. 每个对象的证据字段

每个对象尽量带上：

- `id`：全局唯一、稳定，便于断点恢复；
- `confidence`：`explicit`（源资料直接给出）、`inferred`（推断）或 `unresolved`（只描线、不解释）；
- `source`：尺寸表、图片区域、CAD 句柄、设计假设等出处；
- `layer`：最终图层；类别有固定默认层时可省，但显式写更稳。

可选字段：

- `source_ref`：文件名、DWG handle、标注编号或图片区域；
- `only_trace: true`：只保留线形、不赋予语义；
- `notes`：冲突、限制或待确认事项。

## 3. 各类对象写法

墙体（矩形）：

```json
{"id":"wall_01","rect":[0,0,200,6000],"layer":"A-WALL-EXIST","confidence":"explicit","source":"外轮廓"}
```

洞口与窗：

```json
{"id":"opening_d01","p0":[1800,120],"p1":[2700,120],"layer":"A-OPENING","confidence":"explicit","source":"门洞尺寸"}
{"id":"window_w01","p0":[800,100],"p1":[1600,100],"orientation":"H","frame_offset":35,"layer":"A-WINDOW","confidence":"explicit","source":"南窗"}
```

平开门（`leaf_end` 为完全开启时的门扇端点，角度为 CAD 度）：

```json
{"id":"door_d01","hinge":[1800,200],"leaf_end":[1800,1100],"width":900,"angle0":0,"angle1":90,"layer":"A-DOOR","confidence":"explicit","source":"D01"}
```

房间：

```json
{"id":"room_living","name":"客厅","area":"18.0㎡","label":[4300,2600],"rect":[2800,200,7800,4300],"confidence":"explicit","source":"功能标注"}
```

家具（床用 `BED_W`/`BED_E`/`BED_N`/`BED_S` 标床头朝向；常见 `kind` 还有 `WARDROBE`、`COUNTER`、`SOFA`、`DINING`、`COFFEE`、`CHAIR`、`DESK`、`TV`、`FRIDGE`、`WASHER`）：

```json
{"id":"bed_01","kind":"BED_W","rect":[200,1300,2200,3100],"contacts":["W"],"layer":"A-MOVE-FURN","confidence":"inferred","source":"按双人床 2000×1800 布置"}
```

洁具设备（`TOILET` 用 `anchor` 标水箱侧贴墙点、`orientation` 指向那面墙）：

```json
{"id":"toilet_01","kind":"TOILET","anchor":[6500,5800],"orientation":"N","layer":"A-SANITARY","confidence":"explicit","source":"卫生间布置"}
{"id":"shower_01","kind":"SHOWER","rect":[6900,4800,7900,5800],"layer":"A-SANITARY","confidence":"inferred","source":"功能净空"}
```

标注与说明：

```json
{"id":"dim_total_w","p0":[0,-600],"p1":[8000,-600],"text_position":[4000,-750],"value":8000,"layer":"A-DIMS","confidence":"explicit","source":"总尺寸"}
{"id":"note_01","text":"单位：mm","point":[0,-1100],"height":180,"layer":"A-NOTE","confidence":"explicit","source":"制图说明"}
```

未分类线稿：

```json
{"id":"trace_01","kind":"polyline","points":[[100,100],[300,180],[520,160]],"closed":false,"layer":"A-NOTE","confidence":"unresolved","only_trace":true,"source":"原图右上角未知轮廓"}
```

## 4. 展开成图元简写

用 `scripts/plan_to_shorthand.py` 把 `plan.json` 一次性展开成 `draw_entities` 的简写文本（一行一个图元）。对应关系：

- 墙体 `rect` → 一条 `rect` 简写 + 一条 `hatch` 填充（放 `A-WALL-FILL`）；
- 窗 → 按 `orientation` 与 `frame_offset` 展开成平行线与端帽；
- 门 → `hinge` 到 `leaf_end` 的门扇矩形 + 开启 `arc`；
- 家具与矩形洁具 → 外轮廓 `rect` + 内部符号（`line`/`circle`/`ellipse`）；
- 房间与说明 → `text`；
- 尺寸 → `dimension`（不要用普通文字冒充尺寸）。

展开规则与顺序以 `plan_to_shorthand.py` 里的 `PlanToShorthand` 为准。

计数要区分「语义对象数」和「展开后的简写行数」，落图核对用后者。

## 5. 校验要点

- 所有 `id` 唯一；坐标都是有限数值；矩形满足 `x0 < x1`、`y0 < y1`。
- 除标注和说明外，图元不超出 `meta.plan_size`。
- 墙在门窗处断开；门扇长度与 `width` 一致。
- 窗端点与 `orientation` 一致；家具与洁具不超界。
- 带 `contacts` 的家具相应边贴墙；床头、马桶水箱侧贴墙。
- 门扇开启线和采样后的扫掠包络不穿过家具或洁具。
- 所有 `inferred`、`unresolved` 对象必须出现在交付报告。
