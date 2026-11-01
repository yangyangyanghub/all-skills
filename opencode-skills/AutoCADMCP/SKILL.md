---
name: AutoCADMCP
description: 通过内置的 AutoCADMCP Server 在 AutoCAD、中望CAD、浩辰CAD 或 BricsCAD 中规划、绘制、复刻和交付专业的分层二维 CAD 图纸。适用于室内平面、建筑立面、剖面、节点及其他二维 CAD。 无需安装插件。如果无法连接使用管理员启动CAD和建筑学长电脑版。
metadata:
  requiresMcp: autocad
  requiresUserSetup: true
---

# AutoCADMCP 工作流

`plan.json` 是唯一几何真源，AutoCADMCP 只负责落图。工具没报错不等于图纸正确。

宿主用 `cad_mcp_launcher.py` 起服务，再经 Windows COM 连接 CAD（探测顺序 zwcad → autocad → bricscad → gcad）。连接器自己从用户缓存、注册表 `CurVer` 和本机 ProgID 里找可用版本。不要猜版本号，不要绕过 MCP 写 COM。绘图走 `draw_entities` 简写，图层/块/文件/实体走 `manage_*`，核对走 `export_data`。后端没有 `authorize_drawing` 硬闸门，落图前的校验和审图是流程约束：第一笔图元之前必须做完。

不要开工通读 `references/`。写到哪一步，再读那一份，见文末。

## 任务模式

先定一种，不要把证据和设计假设混在一起：

| 输入 | 模式 | 做法 |
| --- | --- | --- |
| 只有功能和尺寸 | 自主设计 | 写明假设，再出方案 |
| 图片、扫描件、截图、尺寸表 | 有源重建 | 原图定几何，标注定语义，推断要记账 |
| 已有 DWG/DXF 上继续画 | 增量绘制 | 不覆盖既有内容，只用本任务的新图层 |
| 只要简单几何 | 快速绘制 | 可省略完整语义分类，坐标仍要先算清 |

凡是会产生图元的任务都先写 `plan.json` 并过审图。少量自由创意图元可用通用 `entities` 计划，但不能跳过审图。

## 计划

- 毫米，笛卡尔坐标。除非 `meta.orientation` 另写，正 Y 是图纸上方。
- 写到用户项目输出目录，UTF-8 无 BOM。不要改 Skill 里的示例。
- `meta.drawing_type` 写真实图种。只有室内平面才从 [assets/example_plan.json](assets/example_plan.json) 抄室内结构；立面、剖面、节点和通用图用 `entities` 计划，不要套房间/墙体/家具字段。
- 每个对象有稳定唯一的 `id`、图层、来源：`explicit` 是资料直接给出，`inferred` 是推导，`unresolved` 只留中性线、不擅自加建筑语义。
- 室内图：墙在门窗处断开；门洞、门扇、开启弧分开；固定家具和活动家具分层。
- `meta.assumptions` 记下单位、比例基准、方向、默认墙厚和重要假设。

写室内计划前读 [semantic-plan-schema.md](references/semantic-plan-schema.md)；写其他图种前读 [general-plan-schema.md](references/general-plan-schema.md)。只读对上的那一份。

## 落图前

所有图种都要基础几何校验加预览审图。室内图再加室内语义检查。`validate_plan.py` 按图种分流；`render_interior_plan_preview.py` 只用于室内计划，不要拿去渲别的图种。

室内：

```powershell
${Python} scripts\validate_plan.py plan.json --output plan_validation.json
${Python} scripts\render_interior_plan_preview.py plan.json --output plan_preview.png
```

立面、剖面、节点、机械二维图、简单草图：

```powershell
${Python} scripts\validate_plan.py plan.json --output plan_validation.json
${Python} scripts\render_general_plan_preview.py plan.json --output plan_preview.png
```

缺图种专用校验器不阻塞：通用校验和预览过了就可以画，但要说明哪些专业规范没自动查。通用通过不等于专业认证。基础校验失败、必要图元预览不出来、审图问题没改完，才停。不能静默漏画，也不能先画后补。

无原图：改完校验错误，实际看预览，确认轮廓、布局、文字、尺寸自洽。有原图：跑 `prepare_reference_review.py` 出并排对照图和待审报告，看对照图核对轮廓、锚点、洞口、文字尺寸，改计划重跑，直到 `status=passed`、检查项都过、`blocking_issues=[]`。审图步骤见 [pre-draw-gate.md](references/pre-draw-gate.md)。

然后 `manage_session` 看一次连接（`status` 的 `connected=true`）。没有就 `connect`，还失败就停。

## 怎么落图

- 整图、专业图、复刻图：先 `scripts/plan_to_shorthand.py` 把计划展开成简写，再一次交给 `draw_entities`。
- 图元少、要边画边看、或增量绘制：对话里分批 `draw_entities`，每批一个图层的一类图元，行数不要堆太多。
- 不要自造 `process_command` 这类自然语言草绘。尺寸敏感的图优先 `draw_entities`。
- CAD 侧没有事务。一批失败就停，不要跳过错误继续画。成功/失败数在返回值里。
- 简写是一行一个图元、`|` 分字段、点用 `x,y`。字段顺序和类型表在 [mcp-tool-contract.md](references/mcp-tool-contract.md)，**写简写或 `manage_*` 参数之前读对应小节**，不要凭记忆编语法。

这些脚本可以 import（把 Skill 的 `scripts` 加进模块路径，函数名即契约），不必 subprocess：

| 脚本 | 入口 |
| --- | --- |
| `validate_plan.py` | `validate_plan_file(plan_path, tolerance=2.0, output=None)` |
| `render_interior_plan_preview.py` / `render_general_plan_preview.py` | `render_preview(plan_path, output_path, width=1800, height=1280)` |
| `plan_to_shorthand.py` | `convert_plan_to_shorthand(plan_path, output_path=None)` |

落图顺序：室内按墙体与外轮廓、洞口窗、门扇与开启弧、固定家具、活动家具、洁具设备、房间名与面积、标注说明。其他图种按主轮廓、构件、文字标注。每批记下成功数、失败数、最后一个稳定 `id`。墙体、门窗、家具、文字这几个大阶段之后 `manage_files save`。增量任务只动本任务声明的图层，不清用户已有图层。

用户要「一笔一画 / 逐笔 / 实时」时，这只改展示方式，不改几何：审图仍然先做完；按上面的顺序逐批 `draw_entities`，不要靠打开成品或开关图层假装在画；图元超过约 800 时先说耗时，建议加快或只展示关键阶段。

## 核对与完成

1. `manage_files save` 到用户输出目录的绝对 `.dwg` 路径。
2. `export_data(scope="all", format="json")` 拿实体数、图层、类型、文字样式。
3. 对上计划的展开行数和 `draw_entities` 的 `created`/`total`。批量任务要 `created == total`，文字样式落在配置的中文样式（默认 `CAD_CN`）。

同时满足才算完成：计划里的对象都画了，或逐项写了没画的原因；校验无错，预览看过；有原图时对照报告通过且哈希对得上当前 plan、原图和预览；`.dwg` 路径明确；图层数量和 `export_data` 对过；`inferred`、`unresolved`、质量警告和没自动查的专业项都说了。会话观感不能冒充文件核对。

交付至少有 `.dwg`、`plan.json`、`plan_validation.json`、预览图和它的 `.manifest.json`。有原图再加对照图和 `_reference_review.json`。

## 按任务再读

| 何时 | 读什么 |
| --- | --- |
| 写简写或 `manage_*` 参数 | [mcp-tool-contract.md](references/mcp-tool-contract.md) 里对应小节 |
| 写室内 `plan.json` | [semantic-plan-schema.md](references/semantic-plan-schema.md)、[professional-drawing-rules.md](references/professional-drawing-rules.md) |
| 写其他图种的 `entities` 计划 | [general-plan-schema.md](references/general-plan-schema.md) |
| 有原图要重建 | [source-reconstruction.md](references/source-reconstruction.md) |
| 做落图前审图 | [pre-draw-gate.md](references/pre-draw-gate.md) |
| 分批失败要恢复 | [execution-and-recovery.md](references/execution-and-recovery.md) |
