# 通用二维计划

立面、剖面、节点、机械二维图与简单草图共用此契约；室内语义计划里的 `entities` 也遵循此实体契约。校验、预览和简写转换覆盖相同的图元类型，未知类型和字段报错，不静默忽略。

```json
{
  "meta": {
    "drawing_type": "elevation",
    "units": "mm",
    "reference_required": false,
    "assumptions": ["示例轮廓宽 4000、高 3000"]
  },
  "entities": [
    {"id": "outline", "kind": "rect", "rect": [0, 0, 4000, 3000], "layer": "A-OUTLINE", "confidence": "inferred", "source": "示例设计假设"},
    {"id": "title", "kind": "text", "point": [0, -300], "height": 120, "text": "立面示意", "layer": "A-TEXT", "confidence": "explicit", "source": "图名"}
  ]
}
```

非室内图不需要 `walls/rooms/doors` 等数组，也不要求 `plan_size`。预览按全部实体包围范围等比例取景，支持负坐标。`meta.drawing_type` 保留真实图种；旧室内文件缺少该字段但含 `walls` 时兼容按室内处理，新文件应显式填写。

每个图元必须包含非空 `id`、`layer`、`source`，以及 `confidence: explicit/inferred/unresolved`；`id` 唯一。可选 `only_trace` 记录中性描线。所有坐标为有限数值 `[x,y]` 或 `[x,y,0]`，正 Y 向上，单位毫米。

| kind | 几何字段 |
| --- | --- |
| `line` | `p0`、`p1`，不同端点 |
| `polyline` | `points`，至少两点；可选布尔 `closed`，闭合时至少三个不同点 |
| `rect` | `rect: [xmin,ymin,xmax,ymax]`，宽高为正 |
| `circle` | `center`、正数 `radius` |
| `arc` | `center`、正数 `radius`、`angle0`、`angle1`；角度单位为度，从正 X 轴逆时针，可跨 0°，整圆用 circle |
| `text` | `point`、正数 `height`、非空单行 `text`；左侧基线插入点 |

当前通用路径采用默认白色 CAD 图元和图层组织；PNG 白底深色显示。文字字体采用本机中文字体，CAD 使用配置的中文文字样式，预览不保证字形排版与 CAD 完全一致。文字及图层不得含 `|` 或换行。

填充、椭圆、样条、原生尺寸标注、旋转文字、块等尚未纳入本通用契约。任务需要时，优先使用成熟库适配，并保证同一计划的校验、预览、落图三端覆盖一致；也可在用户所需精度与可编辑性允许时明确拆成受支持实体，记录转换与近似误差。要求原生尺寸或块时不得偷偷用普通线和文字替代。无法可靠表达必要内容才阻塞，不能因为缺少某个图种的专用插件就一概停止。

基础校验检查字段、唯一 ID、有限二维坐标、正尺寸、退化线段及支持范围；不自动验证尺寸链、碰撞、专业规范或设计合理性。Agent 须按任务目视复核这些事项，并披露未覆盖范围。室内图仍额外执行现有室内语义检查。

执行入口见 [落图前闸门](pre-draw-gate.md)。预览依赖现有 Pillow；校验和简写转换只需 Python 标准库。有原图的任务继续生成并审看对照图，通用路径不免除对照审查。
