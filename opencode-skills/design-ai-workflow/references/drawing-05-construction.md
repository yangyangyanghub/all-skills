# 施工图（CAD 落图主路）

> 定位：唯一"真交付物"图种。位图施工图不是施工图，是施工图的照片。
> 依赖技能：`AutoCADMCP`（已安装并实测跑通，见它的 `SKILL.md` 与 `INSTALL-NOTES.md`）。

## 一、三条路，只有一条能交付

| 路线 | 产出 | 可编辑 | 尺寸真实 | 能交付 |
|---|---|---|---|---|
| 图像模型出"施工图风格位图" | PNG | ❌ | ❌ | ❌ 只能当图面示意 |
| **CAD MCP 落真图元** | DWG + 图层 + 标注 | ✅ | ✅ | ✅ |
| 人工画 | DWG | ✅ | ✅ | ✅ 但慢 |

培训 PPT（slide 28）给的那段施工图 prompt 生成的是**位图**——看起来像施工图，但没有一个图元、没有图层、没有真实尺寸，甲方改一个门宽就得重画。**它只能放在"给甲方看排版/图面风格"这一格。**

## 二、主路流程（AutoCADMCP）

不重复它的规则，只写本域的判断。完整契约见 `AutoCADMCP/SKILL.md` 与 `references/pre-draw-gate.md`。

```
① 定图种     meta.drawing_type：interior_plan / elevation / section / detail / general
② 写 plan    plan.json 是唯一几何真源，毫米、笛卡尔坐标
③ 校验       validate_plan.py → status=ok、无 errors
④ 看预览     render_interior_plan_preview.py 或 render_general_plan_preview.py
             → 必须实际看图，确认轮廓/布局/文字/尺寸自洽
⑤ 有原图      prepare_reference_review.py 出并排对照图 + pending 报告
             → 实看对照图，改计划重跑，直到 status=passed
⑥ 确认连接   manage_session status → connected=true
⑦ 建文档     manage_files new（如果要新建图纸）
⑧ 建图层     manage_layers create —— **必须在 ⑦ 之后**
⑨ 落图       plan_to_shorthand → draw_entities（按图层分阶段）
⑩ 核对       export_data → 逐实体看 Layer 字段，不能只数 count
⑪ 保存       manage_files save 到绝对 .dwg 路径
```

**⑦⑧ 的顺序是会翻车的地方。** `manage_files new` 会切到一个空白文档，之前建的图层不在里面；顺序反了，图元会静默落到 0 层而 `success` 依然为 true。实测对照见 [known-issues.md](known-issues.md) 的 K-06。

## 三、本域特有的图种判断（AutoCADMCP 没有的部分）

| 图种 | 有自动校验器 | 可承诺 |
|---|---|---|
| 平面 / 室内平面 | ✅ `validate_plan` + 室内语义检查 | 几何可用，需人工审图 |
| 立面 / 剖面 / 节点 | ✅ 通用几何校验 + 预览 | 几何可用，**专业规范未自动查** |
| 结构 / 水电 / 暖通 | ❌ 无 | **不得承诺合规**，只能出底稿供人工画 |

通用校验通过 ≠ 专业合规。交付时必须写清"哪些项没自动校验"。

## 四、实测记录（本机 AutoCAD 2023 + CASS11，2026-10-29）

| 步骤 | 结果 |
|---|---|
| `connect`（CAD 已运行） | ✅ 4.2 秒，ProgID `AutoCAD.Application.24.2` |
| `connect`（CAD 未运行） | ⚠️ 330 秒（adapter 冷启动 AutoCAD）。**流程上应先让 CAD 打开** |
| `status` | ✅ `{"autocad": "connected"}` |
| `manage_files new` | ✅ |
| `draw_entities` 4 图元 | ✅ 4/4 created，返回 handle |
| `export_data` | ✅ 矩形 `Area=48000000`（8000×6000 正确）、圆 `Radius=600` 正确 |
| `manage_files save` | ✅ 写出 `.dwg` |

### 两个必须记住的坑

**坑 1：`manage_files new` 之后再建图层 —— 顺序反了会静默落到 0 层。**

正确顺序：`manage_files new` → `manage_layers create` → `draw_entities`。

反了会怎样：`draw_entities` 返回 `success=true`，图元全部落到 `0` 层，**不报错不警告**。
两种顺序的 `export_data` 的 `count` 都是 7，所以**必须逐实体看 `Layer` 字段**，不能只数个数。

实测对照（同一批 7 个图元）：

| 顺序 | 各图层实体数 | 落在 0 层 |
|---|---|---|
| layers → new → draw | 全部为 0 | **7** |
| new → layers → draw | A-WALL 1 / A-DIM 1 / A-DOOR 2 / A-WALL-IN 1 / A-TEXT 2 | **0** |

**坑 2：`lineweight` 必须是整数（1/100 mm）。**

```
manage_layers: create|TEST-WALL|white|0.3   ← 失败：Input should be a valid integer
manage_layers: create|TEST-WALL|white|30    ← 成功 = 0.30 mm
```

## 五、图像模型在这一节剩两个位置

| 位置 | 用法 | 边界 |
|---|---|---|
| 图面风格/排版参考 | 出"施工图风格位图"给甲方看排版习惯 | 只当示意，不入交付 |
| 现状读取辅助 | 从扫描件/照片辅助读出现状（层数、开间） | 几何最终以 plan.json 为准，推断项标 `inferred` |

## 六、交付物清单

最少 6 件：`.dwg` + `plan.json` + `plan_validation.json` + 预览图 + 预览 `.manifest.json`；有原图再加对照图 + `_reference_review.json`。

## 六·五、核对用数值，不靠目测（本机实测结论）

本机 `export_view` 与 `screenshot` 都不可用（见 [known-issues.md](known-issues.md) 的 K-11 / K-12），所以核对以 `export_data` 的**几何数值**为主：

| 核对项 | 期望关系 | 实测（4200×3600 房间） |
|---|---|---|
| 矩形面积 | 长 × 宽 | `15,120,000` ✅ |
| 矩形周长 | 2 × (长 + 宽) | `15,600` ✅ |
| 隔墙长度 | 端点距离 | `3,600` ✅ |
| 门弧半径 | 设计门宽 | `900` ✅ |
| 图层归属 | 逐实体看 Layer | 全中，0 层为 0 ✅ |

**这套比目测强**：目测看不出"面积差 200"。但它查不出文字内容、线型规范、排版美观——这些让用户自己扫一眼 DWG。

## 七、红线

1. 位图施工图不得作为交付。
2. 结构/水电/暖通没有自动校验器，不得写"符合规范"。
3. `export_data` 读的是当前文档内存状态，不能证明用户后续手工修改的结果。
4. 落图前闸门是流程约束，不是代码闸门——**跳过校验直接画 = 交付事故隐患**。
