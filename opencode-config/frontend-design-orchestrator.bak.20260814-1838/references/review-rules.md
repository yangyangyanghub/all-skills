# Review Rules Reference

Actionable review checklist for applying Vercel Web Interface Guidelines to DESIGN.md reviews and UI audits.

## Scope

- Source: Vercel Web Interface Guidelines — https://vercel.com/design/guidelines
- Purpose: catch high-impact interface issues before implementation or during design review
- Boundary: this is **not** an exhaustive accessibility or WCAG audit document

## Review Checklist

Use the checklist as a pass/fail review list. Record issues as `guideline -> problem -> correction`.

### 1. Interaction & Accessibility

- [ ] **Keyboard works everywhere**: primary flows, menus, dialogs, tabs, and forms are fully keyboard-operable.
- [ ] **Clear focus**: every focusable control has a visible focus state; grouped controls use `:focus-within` where needed.
- [ ] **Manage focus intentionally**: dialogs, popovers, and async flows move, trap, and restore focus correctly.
- [ ] **Match visual and hit targets**: tiny visible controls get expanded hit areas; mobile tap targets are at least 44px.
- [ ] **Respect zoom and mobile input rules**: browser zoom is never disabled; mobile inputs use 16px+ text or an equivalent safe viewport strategy.
- [ ] **Links are links / buttons are buttons**: navigational elements keep native link behavior; actions use buttons.
- [ ] **Async feedback is announced**: loading, toast, and inline validation changes are communicated with accessible text or polite live regions.
- [ ] **Semantics before ARIA**: native elements, labels, headings, and skip links exist before adding `aria-*` workarounds.

### 2. Responsive Layout & Structure

- [ ] **Deliberate alignment**: each element aligns to a grid, edge, baseline, or optical center; no accidental offsets.
- [ ] **Responsive coverage**: layouts are reviewed on mobile, laptop, and ultra-wide widths.
- [ ] **Safe areas are respected**: sticky bars, drawers, and full-screen UI account for notches and inset areas.
- [ ] **No accidental scrollbars**: overflow is intentional and extra horizontal/vertical scrollbars are removed.
- [ ] **Let the browser size things**: flex, grid, and intrinsic layout are preferred over JavaScript measurement hacks.
- [ ] **Long and short content both fit**: cards, tables, and navigation survive sparse, dense, and user-generated content.

### 3. Content, States & Forms

- [ ] **Inline help first**: guidance appears near the problem; tooltips are not carrying core instructions.
- [ ] **All states are designed**: empty, loading, sparse, dense, success, and error states are explicitly covered.
- [ ] **Stable skeletons**: placeholders match final layout to avoid layout shift.
- [ ] **Redundant status cues**: state is not communicated by color alone; text or icons reinforce meaning.
- [ ] **Icons still have labels**: icon-only buttons have descriptive names; decorative icons stay hidden from assistive tech.
- [ ] **Accurate page titles and headings**: titles reflect current context, heading hierarchy stays logical.
- [ ] **Form labels and errors are local**: each control has a label, errors appear next to the field, and submit focuses the first error.
- [ ] **Form behavior stays forgiving**: submit is not pre-disabled, typing is not blocked, paste/password managers still work.
- [ ] **Copy is concise and specific**: active voice, clear button labels, positive error guidance, and consistent nouns.
- [ ] **Use the actual ellipsis character**: follow-up actions and loading labels use `…`, not three periods.

### 4. Motion & Performance

- [ ] **Honor reduced motion**: provide a reduced-motion variant for non-essential animation.
- [ ] **Animation has a reason**: motion clarifies cause/effect or deliberate delight; autoplay is avoided.
- [ ] **Animation is implementation-safe**: prefer CSS, avoid `transition: all`, and animate compositor-friendly properties.
- [ ] **Animation is interruptible**: user input can stop or override ongoing transitions.
- [ ] **Loading states avoid flicker**: spinners and skeletons use a short delay and minimum visible duration when needed.
- [ ] **Latency feels responsive**: keystrokes stay cheap, expensive work leaves the main thread, and network mutations feel fast.
- [ ] **Visual stability is protected**: images reserve space, large lists are virtualized when necessary, and layout work is minimized.

### 5. Visual Craft

- [ ] **Contrast supports interaction**: hover, active, and focus states increase clarity instead of reducing it.
- [ ] **Layered depth is deliberate**: shadows use multiple layers and borders stay crisp.
- [ ] **Nested radii are consistent**: child radii do not exceed parent radii and corners stay concentric.
- [ ] **Text/icon lockups feel balanced**: icon weight, spacing, and color are adjusted so text and icon do not clash.
- [ ] **Browser chrome matches the theme**: `theme-color` and `color-scheme` are aligned with the design when relevant.

### 8. 5-Dimension Creative Expert Review

*Use this section when the user asks for "Design Quality Critique" or "Creative Review". Score 0-10 for each dimension.*

- [ ] **Philosophical Consistency**: Does the design strictly follow the chosen style/philosophy (e.g., Bauhaus, Cyberpunk)? Are there conflicting styles mixed in?
- [ ] **Visual Hierarchy (0-10)**: Is the information priority clear through size, color, and spacing? Does the eye naturally go to the primary action?
- [ ] **Detail Execution (0-10)**: Check alignment, whitespace rhythm, typography pairing, and icon consistency. Are there "pixel-level" flaws?
- [ ] **Functionality (0-10)**: Does the design actually support the core user task? Is navigation intuitive?
- [ ] **Innovation & Hook (0-10)**: Is there a memorable visual hook that makes the design stand out, without breaking usability?

### 6. Anti-AI Slop & AI 默认模式禁令

**来源**: [awesome-claude-design/break-default-aesthetic](https://github.com/rohitg00/awesome-claude-design/blob/main/prompts/break-default-aesthetic.md)

**CRITICAL**: 这些规则用于中和 LLM 生成前端设计时的可观察默认模式。在生成 DESIGN.md 或审查现有工作时严格执行。

#### EXPLICIT REJECTIONS — 除非用户明确要求，否则禁止产生以下内容：

- [ ] **禁止默认 teal 色**: 不得将 `#16d5e6` 或邻近色作为默认强调色。强调色必须在 DESIGN.md 中定义且唯一。
- [ ] **禁止动画状态指示器**: 导航、头部或英雄区中不得出现动画点、闪烁灯、"live" 徽章或脉冲球。状态展示使用静态图标和明确文本。
- [ ] **禁止容器超过 2 层嵌套**: 最大嵌套深度为 2（如 section > card，不是 section > card > pill > tag > content）。禁止卡片套卡片装饰。
- [ ] **禁止默认 Inter/Roboto/Arial/system-ui 作为主字体**: 除非 DESIGN.md 明确指定。 headline 字重、字间距、光学尺寸都必须在 token 中声明。
- [ ] **禁止三栏特性网格**: 英雄区或第二节不得使用三栏特性网格。数据异构时不得使用相同宽高比的卡片网格。
- [ ] **禁止装饰性左边框色条**: 4px 彩色左边框仅保留给一个语义角色（如严重性、状态），绝不用于装饰。
- [ ] **禁止混合图标库**: 每个项目仅选择一个图标库（Phosphor、Heroicons、Tabler、自定义）。未指定时优先纯文本方案而非默认 Lucide。
- [ ] **禁止紫色渐变英雄图**: 英雄插图和生成图像只能使用 DESIGN.md 中声明的颜色。深色背景上禁止紫粉色渐变。禁止磨砂/毛玻璃卡片堆叠作为英雄组合。
- [ ] **禁止装饰性动效**: 动效仅用于传递状态、层级或空间关系。浮动粒子、摇摆图标、滚动视差需要用户明确要求。始终尊重 `prefers-reduced-motion`。
- [ ] **禁止泛化文案**: 微文案必须与产品相关。禁止 "Welcome to {Product}" 英雄文案、"Built for teams" 副标题、无动作动词的 "Get Started" CTA。

#### POSITIVE BIAS — 无明确方向时优先选择：

- 适合品牌声音的独特字体选择
- 一个大胆的美学方向，而非含糊的 "modern minimal"
- 基于边框的深度而非投影
- 编辑节奏（max-width、垂直呼吸空间）而非统一网格
- 内容优先的英雄区（类型、表格、演示）而非装饰性英雄区
- 真实产品界面（设置、空状态、边界情况）而非纯营销英雄区

#### 自验证清单 — 生成后自行审计：

| 检查项 | 预期结果 |
|--------|----------|
| 强调色是否为 teal？ | 必须 FAIL |
| 是否有动画状态点？ | 必须 FAIL |
| 是否有 3+ 层容器嵌套？ | 必须 FAIL |
| 主字体是否为 Inter/Roboto/Arial？ | 必须 FAIL |
| 第二节是否为三栏特性网格？ | 必须 FAIL |
| 装饰性左边框是否用于超过一个语义角色？ | 必须 FAIL |
| 英雄插图是否超出 DESIGN.md 调色板？ | 必须 FAIL |

任何 FAIL 项都应在向用户展示前重新生成受影响区域。

### 7. Anti-AI Slop 基础质量阈值

- [ ] **无填充内容**: 每个元素都必须有存在的理由。拒绝用假文本、假统计数据或"data slop"填充的设计。
- [ ] **占位符保真度**: 缺失资源使用描述性占位符（如 `[16:9 Hero Image]`），而非绘制糟糕的 SVG 或通用图标。
- [ ] **安全尺寸规则**: 
  - 桌面端文本不得小于 24px。
  - 移动端点击目标不得小于 44px。
  - 打印文档最小 12pt。
- [ ] **真实设计系统锚定**: 设计 token、间距比例和字体栈必须匹配提供的源文件（而非"训练数据记忆"）。

## Severity Levels

Classify each finding by user impact and release risk.

| Severity | When to use | Example violation | Expected correction |
|---|---|---|---|
| `critical` | Blocks core task completion, navigation, accessibility, or causes serious breakage across devices/states | Checkout dialog cannot be used with keyboard; destructive action fires with no confirmation; mobile layout hides the submit button below an accidental horizontal scroll area | Restore keyboard path, add focus management or confirmation/undo, remove blocking overflow or layout break before release |
| `major` | Strongly harms clarity, trust, responsiveness, or state comprehension but does not fully block usage | Error state uses color alone; loading button swaps to spinner with no label; tabs do not persist in the URL; reduced-motion mode is ignored | Add redundant text/status cues, keep loading label visible, persist shareable state, provide reduced-motion treatment |
| `minor` | Polish, consistency, or craft issues with low functional risk | Uses `...` instead of `…`; button copy says `Continue` instead of `Save API Key`; icon/text pair feels visually unbalanced by 1px | Fix wording, typography, spacing, or optical alignment in the next revision pass |
| `style` | AI-generated design rot or low-value filler content. See Section 6 (Anti-AI Slop & AI 默认模式禁令) for the full 10-rule rejection list. | Overuse of generic gradients; padding design with fake "data slop" stats; defaulting to Roboto/Inter without brand reasons; teal accent without brand justification; animated status dots; container nesting > 2 levels; decorative left-border color bars; mixed icon libraries; purple-gradient hero on dark bg; decorative motion; generic CTA copy like "Get Started" | Switch to brand-aligned tokens, use explicit `[Asset Placeholder]` tags, and remove unnecessary decorative elements. Enforce Section 6 checklist before showing output. |

## Example Violations & Corrections

### Example 1 — Critical
- **Violation**: Modal opens visually, but keyboard focus stays behind the overlay.
- **Why it fails**: Breaks “Keyboard works everywhere” and “Manage focus”.
- **Correction**: Move focus into the modal on open, trap focus while open, and return focus to the trigger on close.

### Example 2 — Major
- **Violation**: A destructive “Delete Project” action executes immediately with no confirmation or undo.
- **Why it fails**: Violates “Confirm destructive actions”.
- **Correction**: Add a confirmation step or provide an undo toast with a safe recovery window.

### Example 3 — Major
- **Violation**: Empty state only says “No data” and gives no next step.
- **Why it fails**: Violates “No dead ends” and “All states designed”.
- **Correction**: Explain why the state is empty and add a clear recovery CTA such as “Create Project”.

### Example 4 — Minor
- **Violation**: Primary button label says `Continue`, while the actual action is storing an API token.
- **Why it fails**: Violates Vercel copy guidance on clarity and avoiding ambiguity.
- **Correction**: Rename the action to `Save API Key`.

## Revision Workflow

Follow this order when applying fixes.

1. **Capture the finding**
   - Note the checklist item, affected screen/state, severity, and visible symptom.
2. **Fix critical issues first**
   - Resolve blockers involving keyboard access, focus, destructive actions, hidden primary actions, broken responsive layout, or catastrophic performance regressions.
3. **Fix major issues by flow**
   - Group related findings by user journey (navigation, form completion, settings update, review state) and remove friction end-to-end.
4. **Polish minor issues last**
   - Clean up wording, spacing, ellipsis usage, icon alignment, and visual consistency after behavior is sound.
5. **Re-test affected states**
   - Re-check keyboard path, focus order, loading/error/empty states, reduced motion, responsive breakpoints, and long-content cases.
6. **Record the revision result**
   - Mark each finding as fixed, deferred with rationale, or blocked by a separate dependency.

## Suggested Review Output Format

```md
- [critical] Manage focus -> Modal traps no focus on open -> Move focus to first actionable control and restore on close
- [major] All states designed -> Empty state has no recovery CTA -> Add explanatory copy and primary action
- [minor] Avoid ambiguity -> "Continue" button hides the real action -> Rename to "Save API Key"
```

---

*Reference for frontend-design-orchestrator skill*
