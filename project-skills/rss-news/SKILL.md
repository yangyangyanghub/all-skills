---
name: rss-news
description: 每日信息收集专家，从 RSS 源收集新闻并智能评分。当用户要求"搜索新闻"、"查询新闻"、"整理新闻"、"获取某天的新闻"，或提到需要做"今日贴图""新闻贴图""每日简报图""小红书图组"时，也应触发本技能（第五步生图）。当用户要求"做今日贴图""做新闻贴图""生成今日贴图""出贴图"时，必须按第五步生成空间智研·浅色 GIS 风格的图组（默认按 L/M/H 三档自适应：L 极简 3 张 / M 标准 5-6 张 / H 扩展 7-8 张，空日子不出图）。档位可用"做今日贴图（紧凑版/标准版/展开版）"覆写。贴图统一存到 `dailynews/YYYY-MM-DD/images/`（与 daily-brief.md 同处一室）。用户说"给我今天的发图文案""今天的发图配文"时，从 daily-brief.md 的「📝 今日速览」章节提取。
---

# RSS 新闻收集器

从 RSS 源收集指定日期新闻，智能评分后存储。

## 功能

- 多线程并行抓取：10线程并发，3分钟完成167个源
- 断点续传：中断后自动从上次进度继续
- 详情抓取：深入详情页获取完整内容
- 智能合并：合并相同新闻，保留详情最丰富的版本
- 自动摘要：一句话总结 + 3-5条要点
- 5分制评分：过滤低价值内容
- 智能分类：AI/遥感/无人机/测绘地理信息/政策

## 工作流程

### **第一步：收集新闻**
```bash
# 基本用法
python .opencode/skills/rss-news/scripts/collect.py --date=2026-03-10

# 自定义并发数和超时
python .opencode/skills/rss-news/scripts/collect.py --date=2026-03-10 --workers=20 --timeout=5

# 强制重新抓取所有源
python .opencode/skills/rss-news/scripts/collect.py --date=2026-03-10 --force
```

**参数说明**：
| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--date` | today | 目标日期，支持 YYYY-MM-DD 或 today |
| `--workers` | 10 | 并发线程数 |
| `--timeout` | 8 | 请求超时秒数 |
| `--force` | false | 强制重新抓取，清除所有进度 |

### **第二步：评分**
```bash
python .opencode/skills/rss-news/scripts/rate.py --date=2026-03-10
```

### **第三步：存储**

输出到 `dailynews/[日期]/news.md`。

### **第四步：每日新闻精选**

输出到 `dailynews/[日期]/daily-brief.md`。

**格式规范**：

```markdown
# 每日新闻精选 - YYYY-MM-DD

> 收集时间：YYYY-MM-DD HH:MM | RSS源：167个 | 有效新闻：XX条

---

## 📝 今日速览（3 句话简介 · 发贴图用）

> 一句话主题：[用一句 20-30 字概括今天的核心主线，例如「GeoAI 与对地观测继续升温，测绘/遥感工程化落地加速」]
> 关键动态：①[最重要 1 条，20 字内] ②[次重要 1 条，20 字内] ③[第 3 条，20 字内]
> 发图引导语：「AI × GIS 每日速览 | M月D日」/「空间智研 | M月D日 速览」

> **本节用途**：发小红书/公众号/朋友圈时，复制这 3 句作为配文。第 1 句做标题导语，第 2 句做正文钩子，第 3 句做封面图 caption。
> **字数预算**：一句话主题 20-30 字 / 关键动态 50-80 字 / 引导语 20-30 字。**总共 3 句，不要超过 5 句**。
> **平台适配**：默认出"小红书版"（最长最全），公众号/朋友圈洋哥手动删减。平台字数上限：小红书 1000 / 公众号 300 / 朋友圈 50 / 微博 140。

---

## 🔥 今日重点

### AI 领域

**1. 新闻标题**
> 一句话摘要。
> [来源名称](链接)

**2. 新闻标题**
> 一句话摘要。
> [来源名称](链接)

---

### 测绘地理信息
...

---

### 遥感与无人机
...

---

## 📋 政策与会议

| 事项 | 时间/地点 | 关键信息 |
|------|----------|---------|
| xxx | xxx | xxx |

---

## 💼 招聘信息

- **单位名称** - 岗位描述 [详情](链接)

---

## 📦 数据资源

**数据名称**
- 说明信息
- [获取方式](链接)

---

## 🛠️ 技术工具

- **工具名称** - 简要说明 [链接](url)

---

## 📊 今日数据统计

| 分类 | 数量 | 占比 |
|------|------|------|
| 政策/通知 | XX | XX% |
| AI | XX | XX% |
| 遥感 | XX | XX% |
| 无人机 | XX | XX% |
| 测绘地理信息 | XX | XX% |
| 其他 | XX | XX% |

---

*本文由AI自动整理生成，如有错误请以原文为准。*
```

**栏目说明**：
- 🔥 今日重点：按领域分类（AI/测绘地理信息/遥感与无人机），每领域精选3-4条重要新闻
- 📋 政策与会议：以表格形式呈现，包含事项、时间/地点、关键信息
- 📊 今日数据统计：分类统计表格

### **第五步：生成空间智研·每日新闻贴图**

**触发词**：用户说"做今日贴图""做新闻贴图""生成今日贴图""出贴图""做简报图""生成小红书图"等，自动触发本步骤。

**目标**：把 `dailynews/[日期]/daily-brief.md` 转成空间智研品牌的小红书图组，可单张传播也可拼成长图。

**档位自适应（默认行为）**：根据当天新闻总量和板块数自动选 L/M/H 档，图数从 3 张到 8 张不等。不强求 6 张。

| 档位 | 触发条件 | 产出图数 | 适用场景 |
|------|---------|---------|---------|
| **L · 极简** | 总数 ≤ 8 条 **或** 板块 ≤ 2 个 | **3 张**（封面 + 1 张综合内容卡 + 1 张收尾） | 周末、节假日、低产日 |
| **M · 标准** | 8 < 总数 ≤ 25 条 **且** 板块 3-5 个 | **5-6 张**（封面 + 3-4 张内容卡 + 1 张收尾） | 正常工作日（默认） |
| **H · 扩展** | 总数 > 25 条 **或** 板块 ≥ 6 个 | **7-8 张**（封面 + 5+ 张内容卡 + 1 张收尾） | 热点日、开栏日 |

**手动覆写档位**（洋哥可主动指定，跳过自动判断）：

- 「做今日贴图（紧凑版/少图版）」→ 强制 L 档
- 「做今日贴图（标准版/6 张版）」→ 强制 M 档
- 「做今日贴图（展开版/详细版/多图版）」→ 强制 H 档

**空日子决策**（关键）：如果当天 `daily-brief.md` 中**总重点数 = 0** 或**唯一板块只有 1 条**，**完全不出图**，仅在控制台提示「今日无足够新闻，跳过贴图生成」。

> **理由**：完全没新闻的日子强制出图会暴露「AI 凑数」痕迹，损害品牌可信度。读者也会觉得没诚意。留白比凑数更体面。

**输出路径**：`dailynews/YYYY-MM-DD/images/`（与简报文本同处一室，方便按日归档与查找）

> **设计决定**：2026-08-19 起，贴图统一存到 `dailynews/YYYY-MM-DD/images/`，不再放 `assets/posters/`。原因：每日产出按日聚合到一个目录，跨目录查找麻烦。`assets/posters/` 仅保留"按主题/品牌的设计资产"（如候选小样、设计规范示例），不存每日贴图。

**L 档文件结构**（3 张）：
```
dailynews/2026-08-18/images/
├── 00-cover.png             # 封面（仅显示有内容的板块统计）
├── 01-highlights.png        # 1 张综合内容卡（合并所有重点）
├── 02-data-tools.png        # 收尾卡（数据/工具/招聘，有则放无则省）
└── prompts/                 # （可选）提示词快照
```

**M 档文件结构**（5-6 张，默认）：
```
dailynews/2026-08-18/images/
├── 00-cover.png             # 封面（全部有内容的板块统计）
├── 01-{板块1}.png           # 内容卡（每板块 1 张，按板块出现顺序）
├── 02-{板块2}.png
├── ...（按实际板块数）
├── NN-data-tools.png        # 收尾卡（数据/工具/招聘）
└── prompts/
```

**H 档文件结构**（7-8 张）：
```
dailynews/2026-08-18/images/
├── 00-cover.png             # 封面
├── 01-{板块1}.png
├── 02-{板块2}.png
├── ...（5+ 张内容卡）
├── MM-policy.png            # 政策与会议单列（如有 5+ 项政策时强制单列）
├── NN-data-tools.png        # 收尾卡
└── prompts/
```

**文件命名规则**：
- `00-cover.png` / `00-cover.jpg` — 封面永远是 0 号
- `01-` / `02-` / ... — 内容卡从 01 开始递增
- 中间名用板块的拼音或英文短名（如 `ai.png` / `surveying.png` / `rs-drone.png` / `policy.png`）
- 收尾卡固定为 `data-tools.png`（或 `data-tools-jobs.png`）
- 不用中文命名（兼容各系统）

#### 设计规范（必读）

完整规范见 `myk/设计规范/空间智研·每日新闻贴图设计规范.md`。核心要点：

- **视觉风格**：浅色 GIS 编辑风（米白纸 `#F8F5EE` 底 + 深石板蓝 `#2E5266` 主色 + 锈红 `#C44536` 唯一强调色）
- **字体**：思源宋体（中文标题/正文）+ JetBrains Mono（英文/数字元数据）
- **装饰**：手绘罗盘玫瑰 + 等高线底纹 + 经纬网格（极低对比度，地图感）
- **比例**：3:4 竖版（928×1664，DashScope 标准输出尺寸）
- **品牌**：简称「空间智研」（不带"社"），品牌线「从地理信息到空间智能」

**禁止**：
- ❌ 黑板报风格（旧标准，2026-08-19 起废弃）
- ❌ 赛博朋克霓虹、可爱卡通波普等与品牌调性冲突的风格
- ❌ emoji、渐变、光晕、3D 效果、人物插画
- ❌ 强调色出现超过 3 次

#### 内容切分标准（按档位动态切）

按 `daily-brief.md` 的实际内容切分到 N 张图（N = 实际生成的图数，3-8 张）：

| 输出文件类型 | 来源 | 卡片数 | 布局 |
|------------|------|--------|------|
| `00-cover.png` | 全部有内容的板块统计 | — | N 行数据条（板块名+数字，仅显示有内容的）|
| `01-{板块A}.png` | 板块 A 的全部条目 | 1-6 条 | 垂直堆叠卡片 |
| `02-{板块B}.png` | 板块 B 的全部条目 | 1-6 条 | 垂直堆叠卡片 |
| ... | （按实际有内容的板块）| | |
| `NN-policy.png` | 政策与会议（如有）| 1-8 项 | 表格 + 右侧时间线（5+ 项时强制单列）|
| `MM-data-tools.png` | 数据资源 + 技术工具 + 招聘 | 全部 | 三色 accent bar 分块（如有）|

**关键规则**：

- **每个有内容的板块 = 1 张图**：不是「每个板块都要有图」，是「有内容的板块才出图」。空板块直接跳过，封面也不显示空板块统计。
- **每张图的内容数 = 该板块实际条数**：板块 A 有 2 条就只放 2 条，不硬塞到 4 个；板块 B 有 6 条就放 6 条，不拆分到两张图。
- **政策与会议 ≥ 5 项时强制单列**：用表格 + 时间线布局，单独 1 张图。1-4 项时可与其他板块合并到「综合内容卡」（L 档）。
- **收尾卡（data-tools）只在 3 个子项（数据/工具/招聘）至少 1 个有内容时才出**。
- **L 档特例**：仅 1 个内容板块时，`01-highlights.png` 容纳该板块全部条目；多板块时按板块拆 01/02。

#### 板块-文件名映射

中文板块名 → 拼音短名（用于文件命名）：

| 中文板块 | 文件名 | 优先级（M 档中此板块最常出现）|
|---------|--------|------------------------------|
| 今日重点·AI | `ai` | 1 |
| 今日重点·测绘地理信息 | `surveying` | 2 |
| 今日重点·遥感与无人机 | `rs-drone` | 3 |
| 政策与会议 | `policy` | 4 |
| 招聘信息 | `jobs` | 5 |
| 数据资源 | `data` | 6 |
| 技术工具 | `tools` | 7 |
| 其他 | `misc` | 末位 |

**排序规则**：按板块在 `daily-brief.md` 中**出现的先后顺序**编号（`01-` `02-` ...），不是按上表的固定顺序。**M 档首张（除封面外）通常是「今日重点·AI」**，因为它在简报里位置最靠前。

#### 提示词模板骨架

封面（`00-cover`）：

```
Elegant light-paper GIS-style editorial poster, 3:4 vertical, information-dense cover card for daily AI & GIS news brief dated YYYY-MM-DD, inspired by professional cartography magazine covers. Warm off-white paper #F8F5EE background with very faint topographic contour lines and pale gray latitude-longitude grid. Top: small letterpress label "DAILY BRIEF · YYYY-MM-DD" in dark slate monospace, framed by thin double rules. Center headline: large editorial "AI × GIS 每日速览" in Chinese serif font, deep slate-ink #2E5266. Subhead "从地理信息到空间智能" in lighter slate italic serif, with a thin horizontal rule below. Seven data strips stacked vertically separated by thin slate rules, each with a small slate-blue #4A6B7C category icon on the left, Chinese category name, and item count number right-aligned in small monospace. Categories: [板块1 名] [数], [板块2 名] [数], ... Top-right corner: small hand-drawn compass rose in slate-blue with YYYY-MM-DD date stamp. Bottom-left: footer text "RSS · NNN sources · curated by AI" in small monospace dark gray. Bottom-right: brand mark "空间智研 · 从地理信息到空间智能" in dark slate serif. Note: brand name is "空间智研" not "空间智研社". Bottom center: highlight number "[重点总数]" in warm rust #C44536 with text "条重点 | NNN 条原始". Editorial, scholarly, calm, trustworthy, GIS-professional. NO neon, NO glow, NO cyberpunk. Clear Chinese text rendering, sharp focus, 8K print quality.
```

内容卡（`01-05`）：

```
Same elegant light-paper GIS-style editorial layout as the cover, 3:4 vertical. Warm off-white paper #F8F5EE background with very faint contour lines and pale gray latitude-longitude grid. Top-left: small letterpress label "DAILY BRIEF · YYYY-MM-DD · PART X/5" in dark slate monospace, framed by thin double rules. Top-right: small hand-drawn compass rose in slate-blue. Section title: "[板块名]" in large bold Chinese serif, deep slate-ink #2E5266. Section subtitle: "[副标题关键词1] × [关键词2] × [关键词3]" in smaller slate italic serif. A thin horizontal rule below. [N] content cards stacked vertically, each card separated by a thin slate rule. Card 1: category tag "01 · [分类]", headline "[新闻标题]", body "[一句话摘要]", source "[来源公众号名]". Card 2: ... Each card has a small left-side vertical accent line in rust #C44536 before the category tag. Bottom-left: small monospace text "RSS · NNN sources · curated by AI". Bottom-right: brand mark "空间智研 · 从地理信息到空间智能" in dark slate serif. Bottom-center: page indicator "XX / 05". Palette: paper #F8F5EE, ink #2E5266, muted blue #4A6B7C, warm rust #C44536. Source Han Serif for headlines, system serif for body, monospace for metadata. Clear Chinese text rendering, sharp focus, 8K print quality.
```

**首次落地参考**：`dailynews/2026-08-18/images/`（6 张完成图，含 `prompts/` 快照）和 `assets/posters/samples-2026-08-19/`（3 套候选小样提示词与样图）。

#### 文字渲染要求（每个 prompt 必须包含）

```
Clear Chinese text rendering, sharp focus, 8K print quality. 所有中文文字必须清晰可读，笔画完整，无模糊、无乱码、无伪文字。文字边缘锐利，呈现印刷级清晰度。字体风格统一，字距适中。严禁出现无法阅读的乱码字符或残缺笔画。
```

#### 5A. 发图文案（出图后配套）

**触发词**：

- 「给我今天的发图文案」/「今天的发图配文」/「今天的发布文字」 → 仅出文案，不出图
- 「做今日贴图+文案」/「做今日贴图（带文案）」 → 一次性出图+文案
- 「生成小红书版文案」/「公众号版文案」/「朋友圈版文案」 → 指定平台

**文案来源**：**直接读取** `daily-brief.md` 顶部「📝 今日速览」章节（前 3 句），**不重新生成**。这是简报作者已经写好的权威摘要，发布时直接复制粘贴。

**3 句使用方式**：

| 句 | 用途 | 复制位置 |
|----|------|---------|
| 第 1 句（一句话主题） | 标题/导语 | 小红书标题 / 公众号开头 / 朋友圈首句 |
| 第 2 句（关键动态 ①②③） | 正文钩子 | 小红书正文 / 公众号导语 / 微博正文 |
| 第 3 句（发图引导语） | 封面 caption | 配封面图 00-cover.png 的 caption 框 |

**平台字数裁剪**（洋哥手动 / 或让辛特助帮裁）：

| 平台 | 字数上限 | 建议策略 |
|------|---------|---------|
| 小红书 | 1000 | 全保留 + 加 #话题标签 |
| 公众号 | 300 | 删第 2 句的 ③，只留 ①② |
| 朋友圈 | 50 | 只留第 1 句 + 引导语 |
| 微博 | 140 | 第 1 句 + ① |

**输出格式**（当用户说"给我今天的发图文案"时返回）：

```markdown
## 📝 今日发图文案（2026-08-18）

**【小红书版】**（默认）
> 一句话主题：GeoAI 与对地观测继续升温，测绘/遥感工程化落地加速。
> 关键动态：①超图再登 Geoawesome Top 100 ②智慧城市"建成即闲置"问题凸显 ③阿里 HappyShrimp 让普通人写歌。
> 引导语：「AI × GIS 每日速览 | 8月18日」

**【公众号版】**（裁剪后，300 字内）
> GeoAI 与对地观测继续升温。超图再登 Geoawesome Top 100，基础模型/对地观测/三维地图成 2026 主线。智慧城市"建成即闲置"问题凸显，县级闲置率更高。
> （配图见正文）

**【朋友圈版】**（50 字内）
> GeoAI 与对地观测继续升温。AI × GIS 每日速览 | 8月18日

**【微博版】**（140 字内）
> GeoAI 与对地观测继续升温。①超图再登 Geoawesome Top 100 ②智慧城市"建成即闲置"问题凸显 #GIS #AI
```

#### 生成流程

1. 读 `dailynews/[日期]/daily-brief.md`，统计**总重点数**和**有内容的板块数**
2. 按档位判断表确定档位（L/M/H），如用户指定档位则用用户档位
3. **空日子检查**：总重点数 = 0 或唯一板块仅 1 条 → 控制台提示后退出，**不出图**
4. 按「内容切分标准」切分 N 张图的内容（N = 3-8）
5. 按模板骨架填入实际数据，生成 N 份 prompt（保存到 `prompts/prompt-XX-*.md`）
6. 用 `image-service` 技能 `text_to_image.py` 并发生成 N 张图（图片独立，可并发）
7. 全部生成后做一次质量自检（见下方）

#### 质量自检清单

- [ ] N 张图全部生成成功（N = 实际档位决定的图数）
- [ ] 每张图中文清晰可读，无乱码/鬼画符
- [ ] 封面板块计数 = 实际 daily-brief.md 中**有内容**的板块数（不含空板块）
- [ ] 每张内容卡的 category tag / headline / body / source 字段完整
- [ ] 底部品牌标记统一为「空间智研 · 从地理信息到空间智能」
- [ ] 风格统一：底色、字体、罗盘、accent bar 在 N 张图间一致
- [ ] 「总重点数」与 daily-brief.md 的"今日数据统计"对齐

#### OCR 校验（可选）

如果担心文字渲染问题，对单张图跑 OCR：

```bash
cd .opencode/skills/image-service
python core/image_to_text.py "assets/posters/daily-YYYY-MM-DD/00-cover.png" -m ocr
```

OCR 失败（API 连接问题）时，跳过校验，依靠视觉检查。

#### 修复与迭代

| 问题 | 处理方式 |
|------|---------|
| 大量小字乱码 | 重新生成，简化布局（去掉 source 行的换行） |
| 局部文字模糊 | 用 `image_to_image.py` 修复，附"修复 prompt"（见下方） |
| 风格不统一 | 删掉不一致的图，用 `image_to_image.py` 基于最满意那张重做 |
| 整张全黑/全白 | 等待 60s 重试，或检查 prompt 长度（>800 字符会被截断） |

**图生图修复 prompt**：

```
执行语意级图像重构。针对图中模糊或乱码的文字区域进行修复：
1. 保持原图的版面配置、物体座标、配色风格完全不变
2. 将模糊文字修复为清晰的简体中文：{预期文字内容}
3. 文字笔画必须呈现印刷级清晰度，边缘锐利，无压缩噪点
4. 严禁产生无法阅读的伪文字或乱码
直接输出修复后的图像。
```

#### 注意事项

- API 有频率限制（429错误），批量生成时需间隔 5-10 秒
- 每张图约需 30-60 秒生成
- 生成失败时等待 60 秒后重试
- **必须添加文字清晰后缀**（见上方）
- **生成后必须校验文字清晰度**（视觉或 OCR）
- 依赖 `image-service` 技能的 API 配置
- 单图 prompt 控制在 800 字符以内（settings.json 限制）

## 输出文件

```
dailynews/2026-03-10/
├── progress.json    # 抓取进度（断点续传）
├── raw_news.json    # 原始新闻数据
├── news.md          # 完整评分报告（66条）
├── daily-brief.md   # 每日新闻精选
└── images/          # 第五步产出（按新规范，按档位动态）
    ├── 00-cover.png                   # 封面（仅显示有内容的板块统计）
    ├── 01-{板块A}.png                 # 内容卡（按板块出现顺序，N 张）
    ├── 02-{板块B}.png
    ├── ...
    ├── MM-data-tools.png              # 收尾卡（如数据/工具/招聘任一有内容）
    └── prompts/                       # 提示词快照（可选）
        ├── prompt-00-cover.md
        ├── prompt-01-{板块A}.md
        └── ...
```

**实际图数示例**（参考 2026-08-18 简报，当天共 25 条重点 / 7 板块，属 M 档上限）：
- 2026-08-18 实产 6 张：00-cover / 01-ai / 02-surveying / 03-rs-drone / 04-policy / 05-data-tools-jobs

**档位与图数对应**：

| 档位 | 图数 | 文件名示例 |
|------|------|----------|
| L | 3 | `00-cover.png` `01-highlights.png` `02-data-tools.png` |
| M | 5-6 | `00-cover.png` `01-ai.png` `02-surveying.png` `03-rs-drone.png` `04-policy.png` `05-data-tools-jobs.png` |
| H | 7-8 | `00-cover.png` + 5+ 板块卡 + `MM-policy.png`（如政策多）+ `NN-data-tools.png` |

## 评分标准

| 分数 | 说明 |
|------|------|
| 5分 | 极高质量，强烈推荐 |
| 3-4分 | 值得一读 |
| 1-2分 | 可选或忽略 |
## 配置

- RSS源：`references/feeds.opml`（167个源）
- 分类规则：`references/categories.json`
- scripts/collect.py：收集新闻、智能合并、自动摘要
- scripts/rate.py：评分及分类

## 质量要求

- [ ] 必须尝试清单中所有的源网站
- [ ] 严禁混入非目标日期的新闻
- [ ] 禁止只抓列表页，必须进详情页
- [ ] 每条新闻必须包含具体数据和指标

## 变更记录

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-08-19 | v2.3 | **daily-brief.md 加「📝 今日速览」章节**（3 句话简介，用于发贴图时配文）。新增 5A 步「发图文案」：直接读取今日速览，不重新生成；支持小红书/公众号/朋友圈/微博 4 平台字数裁剪。 |
| 2026-08-19 | v2.2 | **存储路径统一**：贴图从 `assets/posters/daily-YYYY-MM-DD/` 改到 `dailynews/YYYY-MM-DD/images/`，与 `daily-brief.md` 同处一室，方便按日归档与查找。`assets/posters/` 仅保留品牌设计资产（候选小样、设计示例）。 |
| 2026-08-19 | v2.1 | **弹性 3 档自适应**（L 极简 3 张 / M 标准 5-6 张 / H 扩展 7-8 张）。空日子（总数=0 或仅 1 板块 1 条）直接不出图。允许手动覆写档位（紧凑版/标准版/展开版）。每个有内容板块 = 1 张图，每张图内容数 = 该板块实际条数。 |
| 2026-08-19 | v2.0 | 第五步生图标准切换：黑板报风格 → **空间智研·浅色 GIS 风格**。硬编码 6 张（封面+5 张内容卡）。完整规范见 `myk/设计规范/空间智研·每日新闻贴图设计规范.md`。 |
| 2026-08-19 之前 | v1.x | 黑板报风格（旧标准，已废弃，保留记录供参考；旧产物归档在 `myk/设计规范/_archive/v1-chalkboard/`） |