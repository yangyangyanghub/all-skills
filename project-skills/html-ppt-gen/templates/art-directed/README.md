# Art-Directed Decks — 32 套 Zhangzara 模板

> 来源：[zarazhangrui/beautiful-html-templates](https://github.com/zarazhangrui/beautiful-html-templates)（MIT），由 Open Design 收录并标准化。
>
> 每套模板是**自包含的完整设计系统**——字体、色板、装饰语言、版式词汇全部内聚，**禁止跨模板混搭**。选中一套 → 克隆 `example.html` → 替换内容 → 保持设计系统不变。

## 使用流程

1. **根据场合/mood 选模板**（见下方映射表）
2. **克隆 `example.html`** 到 `slides/` 目录
3. **替换占位内容**：真实标题、正文、数字、图片
4. **保持设计系统**：不改字体、不换色板、不删装饰元素
5. **调整页数**：内容多则复制同布局页，内容少则从尾部删页
6. **不跨模板混搭**：如需本模板没有的布局，用同字体/色板/装饰从零设计

## Mood → 模板映射

### 温暖 / 亲近（Warm / Friendly）
| Mood | 模板 | 页数 | 场合 |
|------|------|------|------|
| warm, modern, confident | `zhangzara-coral` | 10 | 时尚/美妆/健身 pitch |
| warm, approachable, indie | `zhangzara-playful` | 10 | 创作者 portfolio |
| warm, intimate, small-batch | `zhangzara-long-table` | 8 | 晚宴/社交品牌 |
| warm-modern, tactile | `zhangzara-mat` | 9 | 设计工作室 credentials |
| warm, handmade, literary | `zhangzara-pin-and-paper` | 11 | 有性格的研究报告 |
| cheerful, sunny, wholesome | `zhangzara-daisy-days` | 10 | 教育/课堂 |
| warm, organic, natural | `zhangzara-grove` | 12 | 可持续品牌 |
| playful, modern, fun | `zhangzara-capsule` | 10 | 生活方式品牌 |

### 大胆 / 图形（Bold / Graphic）
| Mood | 模板 | 页数 | 场合 |
|------|------|------|------|
| bold, graphic, punchy | `zhangzara-block-frame` | 10 | 创意 agency pitch |
| bold, editorial, loud | `zhangzara-bold-poster` | 10 | 品牌宣言 |
| confident, punchy, editorial | `zhangzara-neo-grid-bold` | 12 | 产品发布 |
| raw, punchy, energetic | `zhangzara-raw-grid` | 10 | 创业 pitch |
| electric, high-contrast, design-led | `zhangzara-studio` | 12 | 设计工作室 credentials |
| activist, loud, graphic | `zhangzara-peoples-platform` | 10 | 文化评论 |

### 编辑 / 文学（Editorial / Literary）
| Mood | 模板 | 页数 | 场合 |
|------|------|------|------|
| editorial, dramatic, newspaper | `zhangzara-broadside` | 16 | 品牌宣言 |
| editorial, warm, moody | `zhangzara-editorial-tri-tone` | 8 | 编辑/杂志 pitch |
| literary, elegant, quiet | `zhangzara-soft-editorial` | 12 | 编辑 feature |
| restrained, literary, archival | `zhangzara-monochrome` | 16 | 用户研究综合报告 |
| scholarly, quiet, intellectual | `zhangzara-vellum` | 9 | 研究报告 |
| atmospheric, warm, cultural | `zhangzara-biennale-yellow` | 8 | 展览/biennale |
| archival, earthy, tactile | `zhangzara-stencil-tablet` | 11 | 博物馆/文化机构 |

### 专业 / 机构（Professional / Institutional）
| Mood | 模板 | 页数 | 场合 |
|------|------|------|------|
| professional, modern, calm | `zhangzara-blue-professional` | 10 | B2B SaaS pitch |
| institutional, trustworthy, weighty | `zhangzara-signal` | 18 | 投资人 deck |
| quiet, considered, elegant | `zhangzara-cartesian` | 10 | 投资论文 |

### 创意 / 实验（Creative / Experimental）
| Mood | 模板 | 页数 | 场合 |
|------|------|------|------|
| creative, confident, design-led | `zhangzara-creative-mode` | 8 | 创意 agency pitch |
| nocturnal, moody, luxe | `zhangzara-pink-script` | 9 | 时尚品牌 deck |
| playful, messy-on-purpose | `zhangzara-scatterbrain` | 10 | 头脑风暴/workshop |
| retro-tech, cyberpunk | `zhangzara-8-bit-orbit` | 10 | 游戏 pitch |
| nostalgic, retro, geeky | `zhangzara-retro-windows` | 10 | 复古游戏 pitch |
| lo-fi, underground, warm-retro | `zhangzara-retro-zine` | 10 | indie zine/出版物 |
| retro, kawaii-tech, tactile | `zhangzara-sakura-chroma` | 8 | 产品发布/目录 |
| editorial, modernist, monochrome | `zhangzara-cobalt-grid` | 8 | 设计趋势/研究报告 |

## 目录结构

每套模板包含：
```
zhangzara-{name}/
├── SKILL.md       # 技能描述（设计理念、适用/不适用场景、工作流）
├── template.json  # 结构化元数据（色板 hex、字体、mood、场合、页数）
├── example.html   # 完整 deck（自包含 HTML，内联 CSS/JS + 键盘导航）
└── LICENSE        # MIT 许可证（上游 zarazhangrui/beautiful-html-templates）
```

## 与 CSS Theme 系统的区别

| | CSS Themes（36 套） | Art-Directed Decks（32 套） |
|---|---|---|
| 设计方式 | 主题 = 全局 CSS 变量，可任意切换 | 整体艺术指导，字体/色板/装饰一体化 |
| 灵活性 | 同一个 deck 按 `T` 键换主题 | 每个模板是封闭系统，不可混搭 |
| 适用场景 | 标准商务/技术/学术演示 | 需要强烈视觉个性的品牌/创意 deck |
| 起点 | 从 31 个单页布局组装 | 直接克隆 example.html，替换内容 |
