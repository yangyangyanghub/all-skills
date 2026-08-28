# Design Review Report — 电商首页合规性审查

> **审查对象**:用户描述的电商首页设计
> **设计描述**:Inter 字体 / 蓝紫渐变 Hero banner / emoji 做功能图标 / 圆角卡片 + 彩色左边框
> **审查依据**:Vercel Web Interface Guidelines + Anti-AI Slop Constraints(craft/anti-ai-slop.md + review-rules.md Section 6)
> **审查工作流**:Tertiary Workflow(Load Document → Apply Guidelines → Generate Report)
> **严重度体系**:见 review-rules.md Severity Levels(critical / major / minor / **style**)

---

## 一、问题清单(Problem List)

按严重度从高到低排列。SKILL.md 推荐格式:`- [severity] Section — issue summary — why it matters — required DESIGN.md update`

### P0 — style(AI-slop 标志,自动检查器会拦截)

- **[P0 / style] Typography — 全文 Inter 字体且无字体声明**
  - **命中禁条**:
    - `craft/anti-ai-slop.md` 第 4 条 cardinal sin — "Sans-serif on display text when the seed binds a serif: h1/h2 must use `var(--font-display)`, not a hardcoded Inter / Roboto / `system-ui`"
    - `review-rules.md` Section 6 EXPLICIT REJECTIONS — "禁止默认 Inter/Roboto/Arial/system-ui 作为主字体:除非 DESIGN.md 明确指定"
    - `SKILL.md` Forbidden Tropes — "Avoid overused font families: Defaulting to Inter, Roboto, Arial, or system fonts without justification is forbidden"
  - **为什么重要**:Inter 是 LLM 训练数据的视觉基线,直接选用 = 路人皆知的"AI 出厂设置"。font-display 决定整页气质;若不显式声明,后续所有字重/字距/光学尺寸决策都失去锚点。
  - **修正方向**:
    - 在 DESIGN.md Typography 章节显式定义 `--font-display` 和 `--font-body`,并给出 **选择理由**(非默认之选)。
    - 推荐方向(任选其一,需与品牌语态对齐):衬线表达编辑感(GT Sectra、Source Serif 4)、Display 表达克制现代(Söhne、Söhne Mono、Inter Display 的字距自定义)、可变字重表达张力(General Sans、Switzer)。
    - 将 h1/h2 绑定到 `var(--font-display)`,禁止任何模块用 `font-family: Inter` 硬编码覆盖。

---

- **[P0 / style] Color & Hero — 蓝紫渐变 Hero banner**
  - **命中禁条**:
    - `craft/anti-ai-slop.md` 第 2 条 cardinal sin — "Two-stop 'trust' gradient on the hero: purple→blue, blue→cyan, indigo→pink. A flat surface + intentional type beats this every time"
    - `review-rules.md` Section 6 EXPLICIT REJECTIONS — "禁止紫色渐变英雄图:英雄插图和生成图像只能使用 DESIGN.md 中声明的颜色。深色背景上禁止紫粉色渐变"
    - `craft/color.md` Anti-defaults — "Two-stop 'trust' gradient (purple → blue, blue → cyan, etc.) on a hero is the second most reliable tell"
  - **为什么重要**:这是 AI 设计中"科技感/可信赖感"的速成模板,几乎所有 LLM 默认 hero 输出都是这个。`color.md` palette 结构规定 Effect 层(渐变/发光)占比 < 1%,只能用于层级区分(Header→Body / Primary CTA→Secondary),不能装饰空场。
  - **修正方向**:
    - **首选**:Flat surface + 类型驱动的 hero — 大字标题 + 一行支撑句 + 一个 CTA,背景使用 `--bg` 或 `--surface` 单色。
    - **若必须使用渐变**:渐变必须与 `--accent` 同源,且用于区分层级(例:CTA 按钮内部从 `--accent-600` 到 `--accent-800`),不得铺满整个 hero 区域。
    - 在 DESIGN.md Color 章节写入 "Hero 渐变禁令",作为 lint-artifact 规则的镜像。

---

- **[P0 / style] Icon System — emoji 作为功能图标**
  - **命中禁条**:
    - `craft/anti-ai-slop.md` 第 3 条 cardinal sin — "Emoji as feature icons: `✨🚀🎯⚡🔥💡` inside `<h*>`, `<button>`, `<li>`, or `class*="icon"`. Use 1.6–1.8px-stroke monoline SVG with `currentColor`"
  - **为什么重要**:emoji 在 OS/浏览器中渲染效果不可控(Windows/Mac/Android 各家表情字体差异巨大),且无法响应 `currentColor`,hover/focus 状态失效。1.6–1.8px stroke monoline SVG 才能保证品牌一致性 + 状态联动。
  - **修正方向**:
    - 在 DESIGN.md Icon System 章节选定一个图标库(Phosphor / Heroicons / Tabler / Lucide,二选一,禁止混用 — `review-rules.md` §6 "禁止混合图标库")。
    - 所有功能图标替换为 1.6–1.8px stroke 单色 SVG,使用 `currentColor` 接管色彩。
    - 若功能图标的视觉权重需要差异化,通过 stroke-width 而非 emoji 变体实现。

---

- **[P0 / style] Components — 圆角卡片 + 彩色左边框(AI dashboard tile 经典形态)**
  - **命中禁条**:
    - `craft/anti-ai-slop.md` 第 5 条 cardinal sin — "Rounded card with a colored left-border accent: the canonical 'AI dashboard tile' shape. Drop either the radius or the left border"
    - `review-rules.md` Section 6 EXPLICIT REJECTIONS — "禁止装饰性左边框色条:4px 彩色左边框仅保留给一个语义角色(如严重性、状态),绝不用于装饰"
  - **为什么重要**:这是 LLM 训练数据中"卡片组件"最稳定的视觉签名,任何看到它的评审都会瞬间识别为 AI 出厂。左边框作为唯一装饰维度,既不传达信息也不引导视线。
  - **修正方向(三选一)**:
    1. **保留圆角,去掉左边框** — 用 surface 提升 + border 替代装饰,例:`background: var(--surface); border: 1px solid var(--border); border-radius: 12px`。
    2. **保留左边框,去掉圆角** — 适合状态/严重性语义,例:`border-left: 3px solid var(--severity-critical); border-radius: 0`。
    3. **两者都换** — 改用 base 卡片 + 内嵌图标 + 标题排版差异,无任何装饰维度。
  - 决策依据:若卡片承载状态信息,选 2;否则选 1。

---

## 二、严重度汇总

| 编号 | 位置 | 违规 | 严重度 | 自动检查 | 命中禁条数 |
|---|---|---|---|---|---|
| 1 | Typography | Inter 默认字体 | P0 / style | 是 | 3 处冗余命中 |
| 2 | Color / Hero | 蓝紫渐变 banner | P0 / style | 是 | 3 处冗余命中 |
| 3 | Icon System | emoji 功能图标 | P0 / style | 是 | 1 处命中(直接) |
| 4 | Components | 圆角 + 彩色左边框 | P0 / style | 是 | 2 处冗余命中 |

**全部 4 条违规均达到 P0 / style 阈值**,无任何可豁免项。
按 review-rules.md "严重度判定"标准,style 级违规在 release 前必须修复,不可"deferred"。

---

## 三、所需 DESIGN.md 更新

针对每条问题,以下章节必须修订:

| 章节 | 必须更新内容 |
|---|---|
| §1 Visual Theme | 删去"科技蓝紫"叙事,替换为 1 句类型/品牌驱动的美学宣言 |
| §2 Color Palette | 显式列 `Effect(gradients): < 1%` 比例;Hero 区域禁止渐变填充 |
| §3 Typography | 声明 `--font-display` 和 `--font-body`,带选择理由;h1/h2 强制 `var(--font-display)` |
| §4 Components | Card 组件:决策"radius or left-border",写明不同时使用两者的规则 |
| §7 Icon System | 选定 1 个图标库;列出禁止 emoji 的硬规则;所有功能图标换 monoline SVG |

---

## 四、Review Log(待追加)

```
## [本次审查] design-review | 电商首页初稿
- 依据: Vercel Web Interface Guidelines + craft/anti-ai-slop.md(7 cardinal sins)+ review-rules.md §6(10 EXPLICIT REJECTIONS)
- 问题: 4 项 P0 / style 违规
- 状态: 待洋哥确认 DESIGN.md 修订方向
```

---

> **审查员备注**:本次仅完成 Tertiary Workflow 的"问题清单生成"阶段。后续若洋哥确认采纳修订意见,需按 SKILL.md "Review Output Format" 推进到 DESIGN.md 章节级修订,并在修订后回跑同一 checklist 验证所有 P0 项已清零。
