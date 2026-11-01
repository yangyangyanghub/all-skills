# 已知缺陷台账

> 目的：**防止把没修的缺陷标成已修复。**
> 做法来源：建筑学长 `新户型稳定性测试.md` 的 S-01 / S-02 台账——每个缺陷有编号、现状、测试处理，并写明"不能据此把该缺陷标记为已修复"。

## 一、规矩

1. 每个已复现的问题给编号（`K-xx`），登记：现象、复现条件、当前处理、是否已修。
2. **没修就不能标已修。** 可以在文档里"绕过"，但不能写"已解决"。
3. 修了之后要能复现原失败用例并显示通过，否则仍算未修。
4. 新发现的先登记，再决定修不修。

## 二、当前台账（design-ai-workflow v0.1）

| 编号 | 现象 | 复现条件 | 当前处理 | 状态 |
|---|---|---|---|---|
| **K-01** | 单参考出图窗外全白、图面空 | `wan2.7-image-pro` 只用白模一个 `--ref` | 改走双参考两段式 | **绕过，未修**（模型行为，非我们能改） |
| **K-02** | 彩平转鸟瞰布局漂移（水体 1→2） | 手绘/彩平作单参考，`--ar 16:9` | 降级为意向图；高保真改走体块模型+涂鸦 | **未修**（换视角的结构性限制） |
| **K-03** | 实景照片整图重绘画成重建 | 街景照片 + "改造"类 prompt | 必须涂鸦 + 生成后合成 | **未修**（同上） |
| **K-04** | 外观白模的实墙被换成玻璃幕墙 | 白模未标材质 + 含"玻璃/现代"类词 | prompt 明确"实墙保持为 X 材质"；出图后必查 | **未修**（模型倾向） |
| **K-05** | 实景照片出图被内容审核拦截 | 画面含可辨认招牌/人群，报 `DataInspectionFailed` | 去掉人物与文字要求；仍失败则裁切/模糊招牌 | **未修**（平台策略） |
| **K-06** | CAD 图元静默落到 0 层 | **先 `manage_files new` 建文档，再在旧文档里建图层，然后画** | 顺序必须改成：`new` → `manage_layers create` → `draw_entities` → `export_data` 核对 Layer | **可绕过**（见下方根因） |
| **K-07** | `manage_layers` 传小数线宽失败 | `lineweight=0.3` | 用整数（1/100 mm，`30`=0.30 mm） | **已知用法**，非缺陷 |
| **K-08** | `baoyu-image-gen` 无 `--mask` | 想做真 mask 局部重绘 | 走生成后合成（`compose.py`）或涂鸦当 ref | **未实现**（CLI 限制） |
| **K-09** | Google `gemini-3-pro-image`（**出图**模型）配额为 0 | 用本机免费 tier key 调该模型 | 出图走 DashScope；**读图另走 `gemini-3-flash-preview`，实测可用** | **半解决**：出图不可、读图可用 |
| **K-10** | 带 `--ref` 拿不到 4K | `wan2.7-image-pro` + `--ref` 上限 2048² | 2K 出图 + 后期放大（[post-process.md](post-process.md)） | **未修**（API 限制） |
| **K-11** | `export_view` 报"输入无效" | 本机 AutoCAD 2023 + CASS11；改输出目录去空格后仍失败 | 改用外部窗口截图（PowerShell `CopyFromScreen`） | **未修**（疑似依赖 Express Tools 的 `PNGOUT`，参数格式未定位） |
| **K-12** | `screenshot` 报"Could not find window for autocad" | 本机窗口标题为"南方CASS11 - [xxx.dwg]"，不含 `AutoCAD` | 同上，用外部截图 | **未修**（窗口标题匹配失败） |
| **K-13** | 视觉模型不可用时无法看图判断 | 当前会话 `look_at` 返回"模型不支持图像输入" | 改用 `export_data` 的几何数值核对（见下） | **环境限制**，非缺陷 |

## 三、K-06 根因（2026-10-29 实测确认）

第一版判断只说"图层不存在会回退到 0 层"，**不完整**。真实根因是**文档切换**：

```
原来以为的顺序（错）：  create layers → new → draw   → 全部落到 0 层
正确顺序：              new → create layers → draw   → 图层全部正确
```

原因：`manage_files new` 会新建一个**空白文档**。之前在外层文档建的图层不在新文档里，所以 `draw_entities` 找不到目标图层，静默回退到 `0`。

**实测对照：**

| 顺序 | A-WALL | A-DIM | A-DOOR | A-WALL-IN | A-TEXT | 落在 0 层 |
|---|---|---|---|---|---|---|
| layers → new → draw | 0 | 0 | 0 | 0 | 0 | **7** |
| new → layers → draw | 1 | 1 | 2 | 1 | 2 | **0** |

所以 `export_data` 核对时必须**逐实体看 Layer 字段**，不能只数 `count`——两种顺序的 `count` 都是 7。

## 四、K-13：视觉不可用时的替代核对（数值核对法）

当看图能力不可用（视觉模型缺失、或图太多超出上下文），CAD 落图仍然可以**严格核对**，因为几何量是可算的：

| 核对项 | 期望关系 | 实测例（本机） |
|---|---|---|
| 矩形房间面积 | 长 × 宽 | `Area = 15,120,000` = 4200 × 3600 ✅ |
| 矩形周长 | 2 ×（长 + 宽） | `Length = 15,600` = 2×(4200+3600) ✅ |
| 隔墙长度 | 端点距离 | `Length = 3,600` ✅ |
| 门弧半径 | 设计门宽 | `Radius = 900` ✅ |
| 实体类型与数量 | 与计划逐项对应 | 1 矩形 / 1 线 / 2 弧 / 2 文字 / 1 标注 ✅ |
| 图层归属 | 与计划图层一致 | 全部命中，0 层为 0 ✅ |

**这套方法的强度高于目测**：目测看不出"面积差 200"，但数值能。

它查不出的：文字内容对不对、线型是否符合制图规范、图面排版美不美——这些仍需人看。所以数值核对之后，还要让用户自己扫一眼 DWG。

## 五、怎么用这张表

| 场景 | 动作 |
|---|---|
| 交付前 | 扫一遍有没有踩到 K-01~K-05，踩到就在交付声明里写明 |
| 客户提问"为什么这图不对" | 先查台账，是已知缺陷就直说原因，不要辩解 |
| 想升级模型/换服务商 | 用台账当回归用例清单，逐条重测 |

## 六、新增缺陷的格式

```markdown
| **K-11** | <一句话现象> | <能复现的最小条件> | <当前怎么处理> | **未修 / 可绕过 / 已修（附验证方式）** |
```

写"已修"必须附：原失败用例、修复后通过的证据（截图路径或脚本输出）。

## 七、Token Plan 与实际鉴权（2026-10-29 修正，推翻了此前结论）

### 事实

1. **本机使用的是阿里百炼 Token Plan 套餐**，不是按量付费。
2. **真实凭据在 `C:\Users\HP\.baoyu-skills\.env`**：
   - `DASHSCOPE_API_KEY = sk-sp-...`（len 115，Token Plan 专用）
   - `DASHSCOPE_ENDPOINT = https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1/chat/completions`
   - 文件注释明写：**旧的按量 key `sk-5404be66…` 已废弃**
3. **shell 环境变量里的 `DASHSCOPE_API_KEY` 是那个已废弃的按量 key**。用它直连 `dashscope.aliyuncs.com` 会得到 `403 FreeTierOnly` / `403 access_denied`——**这不是"额度用完了"，是拿错了 key**。
4. **Token Plan 白名单实测只有 21 个模型**（`GET /compatible-mode/v1/models` 拉取）：

```
auto  decision-model-preview
deepseek-v4-flash-0731  deepseek-v4-pro  deepseek-v4-pro-0813
deepseek-v4.1-flash  deepseek-v4.1-flash-1017
glm-5.2  glm-5.3
qwen-audio-3.0-asr-flash  qwen-audio-3.0-realtime-plus  qwen-audio-3.0-tts-plus
qwen-image-3.0-pro
qwen3.6-flash  qwen3.7-max  qwen3.7-plus  qwen3.8-flash  qwen3.8-max
wan2.7-image  wan2.7-image-pro
wan3.0-video
```

5. **白名单里没有任何视觉理解模型**（无 `qwen-vl-*` / `qwen3-vl-*` / `*-omni`）。用 TP key 请求 `qwen3-vl-plus`、`qwen-vl-max-latest`、`qwen3-vl-235b-a22b-instruct` 全部返回 `404 Model not exist`。
6. **TP 端点必须直连**。走本机代理 `127.0.0.1:7890` 会连接失败；`requests.Session().trust_env = False` 后正常。

### 结论：读图也能走 TP，但不能靠模型名猜

**第一次判断错了**：我只测了 `qwen-vl-*` / `qwen3-vl-*` 就断言"TP 没有视觉模型"，漏了 `qwen3.x` 旗舰本身支持图像输入。

按 21 个白名单逐个用「图 + 文」打了一遍（`viz/vl-probe.md`）：

| 模型 | HTTP | 实际表现 | 可用 |
|---|---|---|---|
| `qwen3.8-max` | 200 | 读出 10 个房间名（含"卫生间"两处）+ `7.20m²`；街景读出 POS / 拉卡拉 / 乡下菜馆 / 和平交易厅 / 架空电线 | ✅ **高精度档** |
| `qwen3.8-flash` | 200 | 同上，房间名一致；街景细节略少 | ✅ **默认档** |
| `qwen3.7-plus` | 200 | 房间名准确；街景大致对 | ✅ 备选 |
| `auto` | 200 | 平面图可读，街景返回空 | ✅ 兜底 |
| **`deepseek-v4.1-flash`** | **200** | **会编**：街景把招牌读成"巴拉巴拉""擦擦"，实际不存在 | ❌ **禁用** |
| `deepseek-v4-pro` | 200 | 明说"我没有看到图片" | ❌ |
| `deepseek-v4-flash-0731` | 200 | 明说"我无法理解图片" | ❌ |
| `glm-5.2` | 200 | 只回"你好" | ❌ |
| `glm-5.3` | 400 | 明确拒绝：only supports text modality | ❌ |
| `qwen3.7-max` | 400 | Unexpected item type in content | ❌ |
| `decision-model-preview` | 400 | url error | ❌ |
| `qwen3-vl-plus` / `qwen-vl-max-latest` | 404 | Model not exist（不在白名单） | ❌ |

**所以正确分工是：**

| 能力 | 走哪 | 模型 |
|---|---|---|
| 出图 | Token Plan | `qwen-image-3.0-pro` / `wan2.7-image` / `wan2.7-image-pro` |
| **读图** | **Token Plan** | **`qwen3.8-flash`（默认）/ `qwen3.8-max`（高精度）** |
| 读图（跨厂商冗余） | Google | `gemini-3-flash-preview` |

### 两个陷阱

**陷阱一：HTTP 200 ≠ 模型看了图。**
`deepseek-v4.1-flash`、`glm-5.2`、`deepseek-v4-pro` 全部返回 200，但都没读图——前两个在编，第三个老实承认。**只看状态码会误判成"能用"。**

**陷阱二：单张图测不出幻觉。**
`deepseek-v4.1-flash` 在平面图上"答对"了 10 个房间名（大概是靠建筑平面的高频先验），但换一张街景立刻露馅（编出不存在的招牌）。
**抗幻觉验证必须用第二张、且问只有真看过才能答的细节。**


### 三条教训

1. **遇到 403 先查三件事，再谈额度**：① key 是不是当前套餐的 ② 端点是不是该套餐的 ③ 模型在不在白名单里。这三件没查清就下"额度耗尽"的结论，会误导后续所有决策。
2. **白名单不是能力清单**。同一个套餐里，`qwen3.8-max` 能读图、`deepseek-v4.1` 不能、`glm-5.3` 直接拒。按模型名推断能力一律不可靠，必须逐个实测。
3. **能力判断要两张图**：一张验"能不能读"，第二张验"是不是在编"。
