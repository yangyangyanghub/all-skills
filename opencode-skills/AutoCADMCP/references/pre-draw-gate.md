# 落图前文档级质量闸门

AutoCADMCP 后端没有 `authorize_drawing` 硬闸门，落图前闸门是**流程约束**：Agent 必须先完成校验、匹配图种的预览和（有原图时）对照审查并记录结论，再用 `manage_session status` 确认连接后，才允许第一笔 `draw_entities`。不得“先画后补材料”。

## 图种分流

| `drawing_type` | 计划/预览要求 |
| --- | --- |
| `interior_plan` / `floor_plan` | 使用 `validate_plan.py` 和 `render_interior_plan_preview.py` |
| `elevation` / `section` / `detail` | 使用 [通用实体 schema](general-plan-schema.md)、`validate_plan.py` 和 `render_general_plan_preview.py`；按实际图种补充专业复核 |
| `general` / 其他非室内二维图种 | 使用同一通用实体校验和预览路径 |

不得为了通过闸门而谎报 `drawing_type`，不得使用室内平面预览器渲染其他图种。

图种写在 `meta.drawing_type`。专用校验器缺失本身不是阻塞项：基础几何检查、预览和必要对照审查通过后可落图，但必须披露专业规范未自动校验的范围，不得把通用通过说成专业合规。基础数据错误、不支持的必要图元、无法生成或查看预览、未修复的审查问题才阻塞。依赖缺失时可使用能覆盖全部必要图元的成熟工具生成等比例预览，仍须记录实际工具、检查范围和当前文件哈希。

## 无原图任务

1. 生成 `plan.json`。
2. 运行 `validate_plan.py`，得到 `status=ok` 且无 errors；室内图执行室内专项检查，其他图种执行通用二维几何检查。
3. 生成图种对应的预览图及证据清单并**实际查看**（Agent 读取预览图，确认轮廓、布局、文字、尺寸自洽）。
4. 修正所有几何、布局、文字与尺寸问题并重新生成。
5. 披露 warnings 与未自动检查的专业要求，记录实际复核结果。用 `manage_session status` 确认 CAD 已连接，在会话中记录“预览已审看、无阻塞问题”结论，然后开始落图。

## 有原图任务

先完成计划校验和图种匹配预览，再生成对照材料：

```powershell
${Python} scripts\prepare_reference_review.py `
  --plan plan.json `
  --source source.png `
  --preview plan_preview.png `
  --comparison plan_reference_comparison.png `
  --report plan_reference_review.json `
  --drawing-type interior_plan
```

上例为室内图；其他图种将 `--drawing-type` 替换为 `meta.drawing_type` 的实际值。脚本适用于各图种，只生成并排对照图和 `pending` 报告，不会自动宣称一致。Agent 必须实际查看 `comparison_image`，按原图比例和语义审查：

1. 整体轮廓与长宽比例；
2. 至少三个分散的稳定锚点；
3. 主要结构、洞口和构件位置；
4. 细节、文字、尺寸及原图明确标注；
5. 推断与未决内容是否如实披露。

发现差异就修改 `plan.json`，重新校验、预览、生成对照报告。只有全部检查项 `status=passed`、`blocking_issues=[]`、报告总状态为 `passed`，且 Agent 在会话中记录“对照审查已通过”，才能落图。

校验报告带 plan SHA-256，预览证据清单带 plan 和 preview SHA-256，审查报告带 plan、source 和 preview SHA-256。Agent 修改任一文件后旧证据失效，必须重新校验、预览和审查。

## 落图前确认

每次开始落图前，用一次 `manage_session`：

```json
[{"action":"status"}]
```

确认 `connected=true` 后开始。若未连接，先 `connect`，仍失败则报告连接问题并停止，不得当作已落图。

## 文档级闸门要点

- 预览和原图审查必须发生在第一笔 CAD 图元之前，而不是画完以后补材料。
- Agent 的“已审看”必须以实际读取预览/对照图为前提，并在交付中记录审看结论与发现的问题。
- 后端不会在连接 CAD 前拦截绘图工具；责任落在流程上，Agent 不得跳过第 3 节的校验与预览。
