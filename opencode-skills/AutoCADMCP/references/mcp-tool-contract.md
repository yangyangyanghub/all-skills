# AutoCADMCP 工具契约

## 运行原则

先查看运行环境真实暴露的工具清单，再按本表映射。不要调用未注册工具，也不要把宿主文件执行工具误认为 MCP 绘图工具。

本 Skill 内置 `cad_mcp_launcher.py` 和完整 `src/` MCP 服务。宿主以 stdio 启动名为 `autocad` 的服务，服务通过 Windows COM 自动探测并连接 AutoCAD、中望CAD（ZWCAD）、浩辰CAD（GstarCAD）或 BricsCAD，探测顺序 zwcad → autocad → bricscad → gcad；未运行时会尝试启动。连接是懒加载的：第一次调用工具时才真正连接。连接由宿主管理时直接调用工具，不主动断开或重复连接。

连接链路：

```text
Agent 宿主
  -> autocad stdio 配置
  -> cad_mcp_launcher.py
  -> src/server.py
  -> src/adapters（pywin32 COM，线程本地、懒连接）
  -> AutoCAD / 中望CAD / 浩辰CAD / BricsCAD
```

## 七个统一工具

坐标使用 `x,y` 或 `x,y,z`（简写内用 `x,y`），角度单位为度，单位为毫米。

| 工具 | 用途 | 输入 |
| --- | --- | --- |
| `manage_session` | 连接、视图、历史、截图、状态 | JSON 操作数组 |
| `draw_entities` | 一次性绘制多类图元（批量落图） | 简写文本（或 JSON） |
| `manage_layers` | 图层增删改查 | 简写文本（或 JSON） |
| `manage_blocks` | 图块增插查、属性 | 简写文本（或 JSON） |
| `manage_files` | 保存/新建/关闭/切换/列举文档 | 简写文本（或 JSON） |
| `manage_entities` | 选择/移动/旋转/缩放/改色/改层/复制/删除实体 | 简写文本（或 JSON） |
| `export_data` | 导出当前文档实体数据用于核对 | `scope` + `format` |

`manage_session` 只接受 JSON 数组，其余 `manage_*` 与 `draw_entities` 同时接受简写与 JSON。

## `manage_session`（JSON 数组）

每个元素含 `action` 字段，按顺序执行：

- 连接：`connect`、`disconnect`、`status`、`list_supported`、`discover`、`check_running`
- 视图：`zoom_extents`、`screenshot`（含窗口边框）、`export_view`（纯图纸渲染，窗口被遮挡也有效）
- 历史：`undo`、`redo`（可选 `count`，默认 1）
- 仪表盘：`open_dashboard`（可选 `host`/`port`，默认取 `config.json`）

```json
[{"action":"connect"},{"action":"zoom_extents"},{"action":"undo","count":3}]
```

显式发现与选择：先调用 `[{"action":"discover"}]`，再把推荐项原样传给 `[{"action":"connect","cad_type":"autocad","prog_id":"AutoCAD.Application.24"}]`。

落图前用 `status` 确认已连接（`connected=true`），不要默认连接必然成功。
`connect` 会从用户缓存、注册表 `CurVer` 和本机实际注册的版本化 ProgID 中自动发现可用连接，不需要猜测版本号。连接诊断时可调用 `discover`，它只探测已注册候选和运行状态，不启动 CAD。
需要显式选择时，把 `discover.recommended` 返回的 `cad_type` 和 `prog_id` 一起传给 `connect`；后端只接受本次可发现白名单中的 ProgID，不执行任意 COM 标识。

## `draw_entities`（简写）

每图元一行，`|` 分隔字段；点坐标用 `x,y`，多点用 `;` 分隔。默认 `color=white`、`layer=0`。

| 类型 | 语法 | 说明 |
| --- | --- | --- |
| 直线 | `line\|start\|end\|color\|layer` | |
| 圆 | `circle\|center\|radius\|color\|layer` | |
| 圆弧 | `arc\|center\|radius\|start_angle\|end_angle\|color\|layer` | |
| 矩形 | `rect\|corner1\|corner2\|color\|layer` | 别名 `rectangle` |
| 多段线 | `polyline\|points(;)\|closed\|color\|layer` | |
| 样条 | `spline\|points(;)\|closed\|color\|layer` | |
| 椭圆 | `ellipse\|center\|major_axis_end\|ratio\|color\|layer` | `major_axis_end` 为长轴端点（绝对坐标），`0<ratio<=1` |
| 填充 | `hatch\|points(;)\|pattern\|scale\|angle\|color\|layer` | `pattern` 默认 `SOLID` |
| 文字 | `text\|position\|text\|height\|color\|layer` | |
| 标注 | `dimension\|start\|end\|color\|layer\|text\|offset` | `text` 为文字覆盖，可省略 |
| 引线 | `leader\|points(;)\|text\|height\|color\|layer\|type` | 内部统一为 MLeader |
| 多引线 | `mleader\|base\|group1~~group2\|text\|height\|color\|layer` | 组内点 `;` 分隔 |
| 表格 | `table\|insert\|rows\|cols\|row_h\|col_w\|title\|headers\|data` | 行 `~~` 分隔，单元格 `;` 分隔 |

示例：

```text
line|0,0|100,0|white|A-WALL-EXIST
rect|0,0|20,15|white|A-WALL-NEW
circle|50,40|10|blue
arc|1000,0|900|0|90|white|A-DOOR-SWING
ellipse|6200,5100|6200,5450|0.857|white|A-SANITARY
hatch|0,0;900,0;900,200;0,200|SOLID|1.0|0.0|white|A-WALL-FILL
text|50,40|客厅|180|white|A-ROOM-TEXT
dimension|0,-500|8000,-500|white|A-DIMS|8000
```

注意：简写以 `|` 与 `;` 为分隔符，文字内容含这些字符会破坏解析，应先用 `scripts/plan_to_shorthand.py` 的 `_safe_text` 替换为全角等价字符。

## `manage_layers`

动作（简写一行一个，`|` 分隔字段）：

- `create\|name\|color\|lineweight`
- `delete\|name`
- `rename\|old_name\|new_name`
- `on\|names`（逗号分隔，别名 `turn_on`）、`off\|names`（别名 `turn_off`）
- `set_color\|name\|color`
- `list`、`info`、`is_on\|name`

## `manage_blocks`

动作：

- `list`、`info\|block_name`
- `insert\|block_name\|insertion_point\|scale\|rotation\|layer\|color`
- `create\|block_name\|entity_handles\|insertion_point\|description`
- `get_attrs\|handle`、`set_attrs\|handle\|attributes`（`attributes` 为 JSON 字符串）

## `manage_files`

动作：

- `save\|filepath`（含路径则视为绝对路径，否则视为文件名）或 `save\|filename\|format`
- `new`、`close\|save_changes`、`list`、`switch\|drawing_name`

## `manage_entities`

动作（`handles` 为逗号分隔实体 handle，来自 `draw_entities` 返回的 `handle` 字段）：

- `select\|by\|value`
- `move\|handles\|offset_x\|offset_y`
- `rotate\|handles\|angle\|center_x\|center_y`
- `scale\|handles\|scale_factor\|center_x\|center_y`
- `set_color\|handles\|color`、`set_layer\|handles\|layer_name`、`set_color_bylayer\|handles`
- `copy\|handles`、`paste\|base_point`、`delete\|handles`

## `export_data`

```text
export_data(scope="all" | "selected", format="json" | "excel")
```

- `scope=all`：导出当前文档全部实体；`scope=selected`：导出当前选择集。
- `format=json`：返回实体数、图层、实体类型与文字样式统计，用于落图后核对。
- `format=excel`：写 `.xlsx`；若环境缺 `openpyxl`，返回明确提示（不静默失败）。

## 状态资源与核对

`export_data(scope="all", format="json")` 是从当前 CAD 文档读取的统计，可作文件级核对依据；它不是从磁盘 DWG 重新解析的结果，不证明用户在 CAD 中手工修改后的最终状态。落图后的核对流程见 `execution-and-recovery.md`。

## 已知能力边界

当前契约：

- **没有 `authorize_drawing` 硬闸门**：落图前的校验、预览、对照审查是文档级流程约束（见 `pre-draw-gate.md`），后端不会在连接 CAD 前拦截绘图工具。
- **没有 DWG 只读回读工具**：用 `export_data` 核对实体，或用 `manage_session screenshot/export_view` 目视复核。
- 删除/回滚能力有限：`manage_entities delete` 可按 handle 删除实体，但没有按图层清理、没有事务；批量落图出错后不承诺自动重跑。
- 中文字体默认使用 `config.json` 的 `text_style`（样式 `CAD_CN` + 宋体 `simsun.ttc`），可自行修改；核对时用 `export_data` 返回的文字样式统计。

因此：

1. 重跑前需先确认已删除/撤销上一轮图元；不得假定自动清理。
2. 文件级核对用 `export_data`，会话观感不能替代它。
3. 需要新增能力时先探测当前工具；只有真实存在才使用。

## 返回处理

- 任何包含“错误”、异常或空结果的调用都视为失败。
- 批量落图后检查返回的 `created` 与 `total`；`failed`（或 `created < total`）时定位失败实体。
- 单批首次失败就停止该批，记录已成功对象，不要跳过继续。
