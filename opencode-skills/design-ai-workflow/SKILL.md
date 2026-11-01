---
name: design-ai-workflow
description: 建筑、室内、景观、规划项目的 AI 出图与图纸交付工作流。按前期概念/中期深化/后期精修三阶段，决定设计概念图、总平面图、分析图、效果图、施工图五类图纸的 AI 介入方式、保真预期与交付定位。当用户要求出效果图、白模出图、彩平转鸟瞰、总平上色、手绘转概念图、生成分析图、旧房或街区改造效果图、出施工图、CAD 落图，或问"这张图能不能交给甲方/客户""AI 能不能出这张图""出到什么程度算能用"时使用。也适用于开工前判断给定底图能否出图、属于可交付还是仅意向。
---

# 设计 AI 出图工作流

一句话：**先判断这张图能不能交付，再决定怎么出图。** 反过来做，就是拿意向图当交付物，翻车在甲方那一关。

## 一、先判断该不该用本技能

| 任务 | 用本技能 | 不用 |
|---|---|---|
| 出效果图/总平/概念图/分析图/施工图 | ✅ | |
| 判断底图能否出图、可不可交付 | ✅ | |
| 只下载参考图 | ❌ 用 `arch-image-downloader` | |
| 只做 P 图（去水印/压缩/抠图） | 部分（见 [post-process.md](references/post-process.md)） | 与图纸无关的通用修图 |
| 与出图无关的建模/算量 | | ❌ |

**不用本技能时要说一句为什么。** 不要默默跳过，也不要为了合规硬套一个不合适的流程。

## 二、定位：三阶段 × 五图纸

| 图纸 | 前期概念 | 中期深化 | 后期精修 | 必需控制图 | 保真 | 交付定位 |
|---|---|---|---|---|---|---|
| 设计概念图 | 主力 | 可用 | — | 手绘草图 / 体块模型 / 按色指认区域 | 低（本来就该变） | **可交付** |
| 总平面图 | 可用 | 主力 | 可用 | **体块模型鸟瞰 + 分区涂鸦** | 高 | 三查后可交付 |
| 分析图 | 主力 | 主力 | — | 三维底图；**逻辑人定**，表现层走两步法 | 中 | 两步法后可交付（`analysis-energy` 仅意向） |
| 效果图 | 意向 | 主力 | 主力 | **体块白模（强制）** | 高（白模）/ 低（实景） | 白模→视觉交付；实景→意向 |
| 施工图 | — | 底稿 | 校对 | CAD 线稿 | 低 | **CAD 落图才可交付** |

判断口诀：**视角不变 + 结构不改 → 保真高；换视角或改结构 → 保真低。** 完整矩阵见 [control-inputs.md](references/control-inputs.md)。

## 三、前置：参考图从哪来

| 需求 | 工具 |
|---|---|
| 采集案例/意向图（ArchDaily / 谷德 / 有方） | `arch-image-downloader` |
| 只有一张参考图，要转成风格描述 | [style/infer-style.md](references/style/infer-style.md)（反推描述词） |
| 8 个预设风格够用 | [style/index.md](references/style/index.md) |

## 四、造输入：四层控制，顺序不能变

| 顺序 | 层 | 手段 | 缺了会怎样 |
|---|---|---|---|
| 1 | 几何 | 手绘草图 / 简单 CAD 线稿 / 体块白模 | 结构必漂（实测：总平水体 1→2） |
| 2 | 局部 | 分区涂鸦 → mask → 局部重绘 / 生成后合成 | 整图重绘会把改造画成重建 |
| 3 | 质感 | 意向图 → 氛围稿 → 第二参考图 | 图面发空、窗外全白 |
| 4 | 语义 | 风格词表 + 提示词（遥控器） | 风格跑偏 |

**先补几何，再谈模型。** 换更贵的模型救不了没有几何控制的图。

## 五、后置：交付闸门（不许自己给自己打分）

出图之后、交付之前，**必须写交付清单并跑校验**：

```powershell
python scripts\check_delivery.py --manifest 交付清单.json
```

三档状态：`review`（核对稿）/ `design-draft`（草案）/ `design-final`（终稿）。
每张图必须带：控制图路径、三查结果、证据截图、差异说明。

规则细节见 [delivery-gate.md](references/delivery-gate.md)。**脚本通过 ≠ 可以交付**——照片相似度、造型、截图真实性仍须人看。

## 六、八条红线

1. **没有几何控制图的，只能出意向图**，不得声称可交付。
2. **改造类禁止整图重绘**，必须涂鸦 + 生成后合成。见 [zoning-mask.md](references/zoning-mask.md)。
3. **施工图必须走 CAD 落图**（AutoCADMCP），位图施工图不得作为交付。见 [drawing-05-construction.md](references/drawing-05-construction.md)。
4. **验收看画面，不看返回值。** 出图后必做三查：数主要元素 / 数楼层 / 对路网或开口。
5. **单模型直出不得作为终稿**。终稿走"氛围稿 → 双参考融合"。见 [pipeline-fusion.md](references/pipeline-fusion.md)。
6. **分析图不得由图像模型一次性生成**。底图可由 AI 出，箭头/色块/标注/图例必须矢量叠加。见 [drawing-03-analysis.md](references/drawing-03-analysis.md)。
7. **概念图不得当方案图用，不得拿来对图纸。** 它证明的是"方向可行"，不是"布局成立"；甲方拿它量尺寸或定位，当场制止。见 [drawing-01-concept.md](references/drawing-01-concept.md)。
8. **没修好的缺陷不许标已修复。** 台账见 [known-issues.md](references/known-issues.md)。

## 七、标准流程

```
① 判断   查表决定图种、阶段、能不能交付；不适用就直说
② 备料   采集参考图（可选）→ 反推风格（可选）→ 补几何（没有就停下来要）
③ 造输入 几何 → 局部 → 质感 → 语义
④ 出图   先 compose_prompt.py --list 挑配方，再按图种走对应主路（见下）
⑤ 验收   看画面 → 三查 → 写交付清单 → check_delivery.py
⑥ 交付   位图 + 交付声明（哪些未自动校验、哪些是推断、哪些是意向）
⑦ 收尾   新缺陷登记台账；同类任务只提醒一次可沉淀为技能
```

### 第 ④ 步的三条路，别走错

| 图种 | 怎么出 | 为什么 |
|---|---|---|
| **分析图 / 图解类** | **两步法**：① 单参考 `wan2.7` 出结构稿 → ② `compose_prompt.py --fuse` + 双参考 `[原底图 + 该结构稿]` 出定稿 | 单参考会把矢量感抹平（出成照片）；纯文生图能出矢量感但丢结构。两条单步路各对一半，**实测都不足以交付** |
| **效果图 / 总平** | 两步：氛围稿（`qwen-3.0-pro`）→ 双参考融合（`wan2.7`）。**带 ref 只能到 2K（2048²），要 4K 得后期放大** | 单参考窗外全白、图面空；直出 4K 拿不到 |
| **概念图 / 施工图** | 概念图单模型即可；施工图走 AutoCADMCP 落真图元 | 概念图无保真要求；位图施工图不可交付 |

**两步法的关键是 ref2**：它只能带"质感与图面语言"，不能带构图。分析图的 ref2 必须是**同一底图的第一轮产物**——用别的场地会两套布局互相平均，比单参考更糟。风险排序见 [pipeline-fusion.md](references/pipeline-fusion.md) 第九节。

## 八、按任务再读

| 什么时候 | 读什么 |
|---|---|
| 判断底图能不能出图、保真几档 | [control-inputs.md](references/control-inputs.md) |
| 出效果图（室内/外观/改造/鸟瞰） | [drawing-04-render.md](references/drawing-04-render.md) → [pipeline-fusion.md](references/pipeline-fusion.md) |
| 出概念图 | [drawing-01-concept.md](references/drawing-01-concept.md) |
| 出总平、彩平转鸟瞰 | [drawing-02-masterplan.md](references/drawing-02-masterplan.md) |
| 出分析图 | [drawing-03-analysis.md](references/drawing-03-analysis.md) |
| 出施工图、CAD 落图 | [drawing-05-construction.md](references/drawing-05-construction.md) |
| 改造类要保住原结构 | [zoning-mask.md](references/zoning-mask.md) |
| 选风格 / 写 prompt / 反推风格 | [style/index.md](references/style/index.md) · [style/prompt-template.md](references/style/prompt-template.md) · [style/infer-style.md](references/style/infer-style.md) |
| **出分析图 / 效果图用现成配方** | **[style/recipes/_index.md](references/style/recipes/_index.md)（21 条配方）** · 字段定义 [_schema.md](references/style/recipes/_schema.md) · 锚点库 [_anchors.md](references/style/recipes/_anchors.md) |
| 判定能不能交、写交付声明 | [acceptance.md](references/acceptance.md) · [delivery-gate.md](references/delivery-gate.md) |
| 交付前修图（去水印/放大/压缩/转白模） | [post-process.md](references/post-process.md) |
| 不知道能不能支持某个输入/设备够不够 | [scope-and-degrade.md](references/scope-and-degrade.md) |
| 客户质疑"这图不对" | [known-issues.md](references/known-issues.md) |
| **哪些配方验过、验到什么程度** | [recipes/_validation.md](references/style/recipes/_validation.md)（19 条实测记录 + 3 次失败归因） |
| `compose.py` 生成后合成的用法 | [scripts/compose.md](scripts/compose.md) |

## 九、工具分工

| 环节 | 工具 | 备注 |
|---|---|---|
| 采参考图 | `arch-image-downloader` | 三站，自动取最高分辨率 |
| **选模型** | `scripts\select_model.py` | **查表决定，不让 LLM 猜**；见 [pipeline-fusion.md](references/pipeline-fusion.md) 第七节 |
| **套配方出 prompt** | `scripts\compose_prompt.py` | `--list` 挑配方 / `--check` 自检 / `--recipe X --set k=v` 拼装 / **`--fuse` 出双参考版**。21 条配方见 [recipes/_index.md](references/style/recipes/_index.md) |
| 读图（写空间描述/反推风格） | 视觉模型直接看，或 `bl omni` / `bl vision` | 见 [style/infer-style.md](references/style/infer-style.md) |
| 出氛围稿 | `baoyu-image-gen` + `qwen-image-3.0-pro` | **不吃 `--ref`**，纯文生图 |
| 融合出图 | `baoyu-image-gen` + `wan2.7-image-pro` | 最多 9 张 `--ref`；带 ref 上限 2048² |
| 局部重绘（需 mask） | `bl image edit`，或 `scripts\compose.py` 生成后合成 | CLI 无 `--mask`，见 [known-issues.md](references/known-issues.md) K-08 |
| 落真图 | `AutoCADMCP` | `draw_entities` / `manage_layers` / `export_data` |
| 交付校验 | `scripts\check_delivery.py` | 三档状态机 + 证据绑定 |
| 看图判断 | 直接看（`read` / `ViewImage`） | **禁止** cv2/OCR 去"分析"图片内容 |

## 十、操作约束

- **看图有上限**：连续查看超过约 18 张后，早先的图会退化成路径。**看图过程中及时把结论写下来**，不要依赖回看。
- **改文件前先备份**：除非用户明确要求在源文件上改。
- **删除要可恢复**：能移回收站就不直接删；删完告知删了什么。
- **长任务放宽超时**：单次出图 2~3 分钟，脚本超时按需放大。

## 十一、沉淀：什么时候提议存成技能

任务成功后，同时满足两个条件才提议：

1. 有明确可复用的多步骤流程
2. 用户很可能再次需要同类操作

只提议，不擅自创建。**同一类任务只提一次。** 不确定时倾向于不提。

## 十二、开工前先问清三件事

1. **这张图给谁看**：内部推敲 / 甲方汇报 / 交付归档。决定保真要求。
2. **有没有几何控制图**：白模、CAD 线稿、手绘草图。没有就没有保真。
3. **改不改原结构**：改结构走生成，保结构走涂鸦 + 合成。

三个都不清就别出图——出了也是废图。
