# Merged Themes Reference — 全技能主题总索引

> 合并自 3 个开源 PPT Skill 的主题库，加上我们自建的瑞士政务风。
> 选主题时只从本文件选，不要跨文件拼凑。

---

## 如何选

| 场景 | 推荐主题 | 来源 |
| :--- | :--- | :--- |
| 政务汇报 / 售前方案 / 客户决策会 | `swiss-government` (自建) | html-ppt-gen |
| 行业观察 / 商业发布 / 人文分享 | `ink-monocle` / `indigo-porcelain` | guizang-ppt-skill |
| 技术架构 / 知识图谱 / AI 概念 | `dark-signal` / `cyber-terminal` | frontend-slides + html-ppt-gen |
| 融资路演 / BP 展示 | `bold-signal` / `electric-studio` | frontend-slides |
| 小红书图文 | `xhs-white-editorial` / `xhs-pastel-card` | html-ppt-gen |
| 学术报告 / 论文答辩 | `academic-paper` / `swiss-minimal` | html-ppt-gen + guizang-ppt-skill |
| 安全审计 / 风险提示 | `testing-safety-alert` / `dark-botanical` | html-ppt-gen + frontend-slides |

---

## A. 自建主题 (html-ppt-gen)

13 套：`swiss-government` `minimal-white` `editorial-serif` `corporate-clean` `academic-paper` `xhs-white-editorial` `xhs-pastel-card` `dir-key-nav-minimal` `graphify-dark-graph` `knowledge-arch-blueprint` `hermes-cyber-terminal` `obsidian-claude-gradient` `testing-safety-alert`

色值见 `references/color-palettes.md`、`references/themes.md`、`references/full-decks.md`。

---

## B. guizang-ppt-skill 迁移主题

### B1. 风格 A · 电子杂志 × 电子墨水

| # | 名称 | 核心色 | 适用场景 |
|---|------|--------|----------|
| B1 | `ink-monocle` | `--ink` / `--paper` / 金色点缀 | 人文分享、商业洞察 |
| B2 | `indigo-porcelain` | 靛蓝 / 瓷白 / 银灰 | 高端品牌、文化展示 |
| B3 | `forest-ink` | 深绿 / 墨黑 / 米白 | 环保、自然、农业 |
| B4 | `kraft-paper` | 暖棕 / 牛皮纸 / 炭灰 | 手作、咖啡、传统文化 |
| B5 | `dune` | 沙色 / 赭石 / 深褐 | 慢生活、有机食品 |

### B2. 风格 B · 瑞士国际主义

| # | 名称 | 锚点色 | 适用场景 |
|---|------|--------|----------|
| B6 | `swiss-ikb-blue` | 巴黎蓝 `#0033A0` | 设计报告、建筑展示 |
| B7 | `swiss-yellow` | 柠檬黄 `#FFD700` | 活力发布、创意展示 |
| B8 | `swiss-green` | 森林绿 `#228B22` | ESG、可持续发展 |
| B9 | `swiss-orange` | 活力橙 `#FF7F50` | 产品发布、营销材料 |

详见 `migrated/guizang/references/layouts-swiss.md` (22 种瑞士版式)。

---

## C. frontend-slides 迁移主题

### C1. Dark Themes (6 套)
`dark-bold-signal` `dark-electric-studio` `dark-creative-voltage` `dark-botanical` `dark-terminal-legacy` `dark-ghost-minimal`

### C2. Light Themes (3 套)
`light-margaret-oliphant` `light-editorial-sans` `light-geometric-grid`

### C3. Special Themes (7 套)
`swiss-minimal` `japandi` `retro-futurist` `neo-brutalist` `claymorphism` `bento-grid` `glassmorphism`

色值详见 `migrated/frontend-slides/STYLE_PRESETS.md`。

---

## 迁移文件索引

| 文件 | 来源 | 用途 |
|------|------|------|
| `migrated/guizang/references/layouts-swiss.md` | guizang-ppt-skill | 22 种瑞士版式骨架 |
| `migrated/guizang/references/components.md` | guizang-ppt-skill | 组件参考手册 |
| `migrated/guizang/references/checklist.md` | guizang-ppt-skill | 质量检查清单 (P0/P1) |
| `migrated/guizang/references/swiss-layout-lock.md` | guizang-ppt-skill | 瑞士版式硬约束 |
| `migrated/guizang/references/image-prompts.md` | guizang-ppt-skill | AI 配图 Prompt 库 |
| `migrated/guizang/scripts/validate-swiss-deck.mjs` | guizang-ppt-skill | 瑞士 deck 校验脚本 |
| `migrated/frontend-slides/STYLE_PRESETS.md` | frontend-slides | 16+ 种风格预设 |
| `migrated/frontend-slides/animation-patterns.md` | frontend-slides | 动画模式参考 |
| `migrated/frontend-slides/viewport-base.css` | frontend-slides | viewport 基础适配 |
| `migrated/frontend-slides/html-template.md` | frontend-slides | HTML 架构模板 |

---

## D. awesome-claude-design 迁移主题 (35 套设计系统)

按 10 大视觉家族分类，详见 `migrated/awesome-claude-design/design-md/`。

### D1. Warm Editorial (暖色编辑风)
`claude` (Terracotta 陶土 / 奶油底) | `mercury` (暖白 / 柔和墨)
→ 人文分享、品牌叙事、教育

### D2. Brutalist (粗野报风)
`the-verge` (纯黑白 + 单色橙、0 圆角、报风)
→ 安全审计、风险警示

### D3. Cinematic (大制作电影风)
`bmw` | `ferrari` | `lamborghini` | `nvidia` | `cohere` | `minimax` | `renault` | `runway` | `tavus`
→ 产品发布、品牌宣讲、高影响力路演

### D4. Data-Dense (数据密集看板)
`clickhouse` | `datadog` | `mongodb` | `posthog`
→ 技术架构、数据汇报、复杂指标展示

### D5. Editorial (精致编辑)
`linear` | `vercel`
→ 投资者报告、商业提案、SaaS 演示

### D6. Glass (玻璃拟态)
`apple` | `arc`
→ 高端产品、Apple 风演示、极简高质感

### D7. Indie (独立手作)
`granola`
→ 慢生活、有机品牌、手作文化

### D8. Playful (活泼互动)
`canva` | `figma` | `toss`
→ 产品特性、创意设计、面向非技术受众

### D9. Terminal (极客终端)
`ollama` | `opencode` | `warp`
→ 技术分享、开发工具、极客文化

### D10. Remix (跨界混搭)
`granola-x-criterion` | `linear-x-claude` | `mercury-x-linear` | `notion-x-duolingo` | `ollama-x-elevenlabs` | `stripe-x-a24` | `vercel-x-pitchfork` | `warp-x-sentry`
→ 两个知名品牌风格融合，创新场景

## 迁移文件索引追加

| 文件 | 来源 | 用途 |
|------|------|------|
| `migrated/awesome-claude-design/design-md/` (35 文件) | rohitg00/awesome-claude-design | 35 套完整设计系统 |
| `migrated/awesome-claude-design/recipes/` (13 文件) | rohitg00/awesome-claude-design | 可复用 UI 组件配方 |
| `migrated/awesome-claude-design/prompts/` (7 文件) | rohitg00/awesome-claude-design | 品牌匹配设计系统提示词 |
| `migrated/awesome-claude-design/showcase/` (5 文件) | rohitg00/awesome-claude-design | 实际 HTML 产出示例 |
