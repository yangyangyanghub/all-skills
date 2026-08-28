---
name: html-ppt-gen
description: "Generate professional HTML presentations with template-driven authoring, 36 CSS themes, presenter mode, and PPTX export. TRIGGERS: PPT, 演示文稿, presentation, HTML slides, 幻灯片, slide deck, 汇报, 报告, keynote, 演讲稿, 分享稿, 逐字稿, tech sharing, 小红书图文."
---

# HTML Presentation Generator

## Overview

You generate multi-page HTML presentations. Each slide is a standalone HTML file rendered at **960×540px** (except 小红书 3:4 竖版 at 720×960). Full pipeline: research → choose starting point → plan outline → generate slides (with image gen + verification) → deploy.

**Core principle**: **Never author from scratch**. Always start from the closest template, then replace content.

**One-glance flow**:

```
1. Research (facts only, time-boxed) 
   ↓
2. Choose: 风格路线 → 主题/模板 → 色板  [🔴 CHECKPOINT: 三要素确认]
   ↓
3. Outline: 5 页类型 + 4a-4f 子类型，4 质量闸门  [🔴 CHECKPOINT: 大纲确认]
   ↓
4. Generate: 模板驱动 + 生图 + verify_layout 脚本
   ↓
5. Deploy: deploy_presentation.ts + pre-delivery-checklist
```

---

## Workflow

### Step 1 — Research (if needed)

**Research protocol**:
- **Scope**: Only the facts the deck's claims depend on — industry stats, market size, product names, dates. Do NOT research generic presentation design.
- **Depth**: 2-3 authoritative sources minimum per key claim. Cross-validate numbers.
- **Time-box**: Max 2 search rounds. Uncertain facts → mark `[待核实]` in outline, flag at Step 3 checkpoint.
- **Output**: Compact fact list (5-10 items) with source attribution. Never invent metrics — see Failure Handling.

### Step 2 — Choose Your Starting Point

**Decision order (route first, then specifics)**:

**Route A: CSS Theme (default)** — standard business/tech/academic decks. One `<link>` switches the whole look, press `T` to cycle at runtime.

| Tone | Recommended Themes |
|------|-------------------|
| Business / investor | `pitch-deck-vc`, `corporate-clean`, `swiss-grid` |
| Tech sharing / engineering | `tokyo-night`, `dracula`, `catppuccin-mocha`, `terminal-green`, `blueprint` |
| 小红书图文 | `xiaohongshu-white`, `soft-pastel`, `rainbow-gradient`, `magazine-bold` |
| Academic / report | `academic-paper`, `editorial-serif`, `minimal-white` |
| Edgy / cyber / launch | `cyberpunk-neon`, `vaporwave`, `y2k-chrome`, `neo-brutalism` |
| Education / warm | `soft-pastel`, `catppuccin-latte`, `gruvbox-dark` |

All 36 themes: `minimal-white`, `editorial-serif`, `soft-pastel`, `sharp-mono`, `arctic-cool`, `sunset-warm`, `catppuccin-latte`, `catppuccin-mocha`, `dracula`, `tokyo-night`, `nord`, `solarized-light`, `gruvbox-dark`, `rose-pine`, `neo-brutalism`, `glassmorphism`, `bauhaus`, `swiss-grid`, `terminal-green`, `xiaohongshu-white`, `rainbow-gradient`, `aurora`, `blueprint`, `memphis-pop`, `cyberpunk-neon`, `y2k-chrome`, `retro-tv`, `japanese-minimal`, `vaporwave`, `midcentury`, `corporate-clean`, `academic-paper`, `news-broadcast`, `pitch-deck-vc`, `magazine-bold`, `engineering-whiteprint`. Full when-to-use guide: `references/themes.md`.

**Route B: Art-Directed Deck (32 Zhangzara)** — when you need **strong visual personality** (brand manifesto, creative pitch, fashion/lifestyle, editorial feature). Each is a **closed design system** (locked fonts, palette, decorative vocabulary) — workflow is **clone → replace content**, NOT compose from layouts.

> ⚠️ **Never mix layouts across zhangzara templates.** If a layout doesn't exist, design it from scratch using the same fonts/palette/decorative grammar.

| Mood | Template | Slides | Best For |
|------|----------|--------|----------|
| **Bold / Graphic** | `zhangzara-block-frame`, `bold-poster`, `neo-grid-bold`, `raw-grid`, `studio` | 10–12 | Creative pitch, brand manifesto, product launch |
| **Warm / Friendly** | `zhangzara-coral`, `playful`, `daisy-days`, `capsule`, `grove`, `long-table`, `mat`, `pin-and-paper` | 8–12 | Fashion/beauty, lifestyle, education, creator portfolio |
| **Editorial / Literary** | `zhangzara-broadside`, `editorial-tri-tone`, `soft-editorial`, `monochrome`, `vellum`, `biennale-yellow`, `stencil-tablet` | 8–16 | Magazine feature, research report, cultural institution |
| **Professional** | `zhangzara-blue-professional`, `signal`, `cartesian` | 10–18 | B2B pitch, investor deck, investment thesis |
| **Creative / Experimental** | `zhangzara-creative-mode`, `pink-script`, `scatterbrain`, `8-bit-orbit`, `retro-windows`, `retro-zine`, `sakura-chroma`, `cobalt-grid` | 8–10 | Gaming, indie zine, fashion brand, workshop |

Full mood→template map with palette/typography previews: `templates/art-directed/README.md`. Templates live at `templates/art-directed/html-ppt-zhangzara-{name}/` (`SKILL.md` + `template.json` + `example.html` + `LICENSE`).

**Route C: Full-Deck Concept Template (15 described, 1 physical)** — 15 templates fully described in `references/full-decks.md` (structure, page counts, visual features) but **no physical directory** — build per description + HTML rules.

- Pitch `pitch-deck` · Product Launch `product-launch` · Tech Sharing `tech-sharing` · Weekly Report `weekly-report` · **小红书 3:4 竖版 `xhs-post` (9 pages)** · Course Module `course-module` · 演讲者模式 `presenter-mode-reveal` · 8 real-world extractions: `xhs-white-editorial`, `graphify-dark-graph`, `knowledge-arch-blueprint`, `hermes-cyber-terminal`, `obsidian-claude-gradient`, `testing-safety-alert`, `xhs-pastel-card`, `dir-key-nav-minimal`

**Physical template**: `templates/full-decks/swiss-government-report/` is the ONLY full-deck with actual files — use as structural reference when building any concept template.

**Route D: Custom 4-Dimension Design System** — when no theme fits, define visual personality: **Texture** (clean/grid/organic/paper) × **Mood** (professional/warm/cool/vibrant/dark/neutral) × **Typography** (geometric/humanist/editorial/technical) × **Density** (minimal/balanced/dense). Specs: `references/design-styles.md`.

**Then pick color palette** — 18 Chinese palettes in `references/color-palettes.md`. Key ones:

| # | 名称 | 适用场景 |
|---|------|----------|
| 1 | 现代与健康 | 医疗健康、心理咨询、护肤 |
| 2 | 商务与权威 | 年度汇报、金融分析、政务 |
| 7 | 活力与科技 | 创业路演、体育赛事 |
| 9 | 科技与夜景 | 科技发布、高端汽车 |
| 15 | 纯净科技蓝 | 云计算/AI、洁净能源 |
| 18 | 铂金白金 | Agent 产品、金融科技 |

**Font — MANDATORY DEFAULT**: Chinese body → `Noto Sans SC`, titles → `Noto Serif SC`, English fallback → `Times New Roman`. `font-family: 'Noto Sans SC', 'Noto Serif SC', 'Times New Roman', serif;` (PPTX export font notes in HTML Implementation Rules.)

**🔴 CHECKPOINT · 🛑 STOP after Step 2**: Confirm the THREE choices with the user: ① theme or art-directed template, ② full-deck template or layout approach, ③ color palette. Present compactly ("我将用 X 主题 + Y 模板 + Z 色板") and wait for confirmation. Font is MANDATORY — do NOT ask; single-page layouts (Step 4a) and design-system dimensions (Route D) are YOUR refinements, not user choices. This prevents 20 minutes of work in the wrong visual direction.

### Step 3 — Plan the Outline

Classify every slide as one of the 5 **Slide Page Types** below; content pages get a subtype (4a-4f). Ensure layout variety; typical structure Cover → TOC → [Divider → Content...] → Summary.

**Input**: confirmed Step 2 choices + user's content brief + Step 1 fact list.
**Output**: slide list in this exact format:

```
| 页码 | 类型 | 子类型 | 标题 |
|------|------|--------|------|
| 01 | Cover | — | [标题] |
| 02 | TOC | — | [章节列表] |
| 03 | Section Divider | — | [章节名] |
| 04 | Content | 4c Data Viz | [要点] |
```

**Quality gates**: ① every slide has a page type (5 types only) ② content slides have a subtype (4a-4f) ③ no two adjacent slides share the same layout ④ page count matches user's request ±1.

**🔴 CHECKPOINT · 🛑 STOP before Step 4**: Show the outline (slide list with page types) and wait for confirmation. Do NOT generate slides until approved. If user has no opinion, state your default outline and proceed only after explicit "OK" / "可以" / "go ahead".

### Step 4 — Generate Slides

Generate up to 5 slides concurrently. For **each slide**:
1. Save as `slides/slide-01.html` etc. (zero-padded); images in `slides/imgs/`
2. Use exact 960×540 `.slide-content` (720×960 for xhs 3:4)
3. **Noto Sans SC** body + **Noto Serif SC** titles
4. 🎤 Presenter mode (演讲/分享/讲稿/逐字稿): per "Presenter Mode" section — 150-300 words 逐字稿 in `<aside class="notes">`
5. **Images MANDATORY** for cover + content pages (below)
6. Verify: `bun scripts/verify_layout.ts --html slides/slide-XX.html --type <type>`
7. Fix any issues before moving on

**Image generation**: `bun scripts/generate_image.ts --prompt "..." --output slides/imgs/cover.png --ar 16:9` — Cover: MANDATORY hero; Content: MANDATORY supporting visual; TOC/Divider/Summary: optional.

**Before writing HTML**: Read `references/html-implementation.md` + `references/svg-guidelines.md`.

**4a. Template-Driven Authoring (NOT from scratch)** — copy the closest `<section class="slide">` block from:
1. `templates/art-directed/html-ppt-zhangzara-*/example.html` — 32 self-contained decks (best structural reference)
2. `templates/full-decks/swiss-government-report/deck.html` — official full-deck
3. `references/layouts.md` — 31 single-page layout descriptions

Then replace content. Standalone slides use inline CSS per `references/html-implementation.md` (Appendix A-G).

**4b. 🎤 Presenter Mode** — trigger words: **演讲 / 分享 / 讲稿 / 逐字稿 / presenter / 演讲者视图**. Build per `presenter-mode-reveal` concept template (`references/full-decks.md` + `references/presenter-mode.md`). Full spec in "Presenter Mode" section below.

**4c. Keyboard Navigation** — every deck MUST include `<script src="../assets/runtime.js"></script>`. Full key map in "Keyboard Shortcuts" section below.

**4d. Animations (optional)** — 27 CSS animations (`data-anim="fade-up"`) + 20 Canvas FX (`data-fx="particle-burst"`), catalog: `references/animations.md`. All opt-in — static by default.

### Step 5 — Deploy

Run `bun scripts/deploy_presentation.ts --slides ./slides --output ./dist`. Before deployment: validate via `references/pre-delivery-checklist.md`.

---

## Slide Page Types

### Type 1: Cover — opening, tone-setting
- **Elements**: Title (72–120px bold), Subtitle (28–40px), presenter/date (18–24px), bg image/motif
- **Layouts**: Asymmetric Left-Right, Center-Aligned · **Image: MANDATORY** · **No page badge**

### Type 2: Table of Contents — navigation, 3–5 sections
- **Elements**: Page title, section numbers (01…), section titles, optional descriptions, **page badge (MANDATORY)**
- **Layouts**: Numbered Vertical List, Two-Column Grid, Sidebar Navigation, Card-Based · Image: optional

### Type 3: Section Divider — transitions between major parts
- **Elements**: Section number (72–120px accent), title (36–48px), optional intro, **page badge (MANDATORY)**
- **Layouts**: Bold Center, Left-Aligned Accent Block, Split Background, Full-Bleed Overlay · Image: optional

### Type 4: Content — core info. Pick ONE subtype:

| Subtype | Description |
|---------|-------------|
| **4a. Text** | Bullets, quotes — requires icons/SVG, never plain text only |
| **4b. Mixed Media** | Two-column: image + text |
| **4c. Data Viz** | SVG chart + 1–3 takeaways + data source |
| **4d. Comparison** | Side-by-side columns (A vs B) |
| **4e. Timeline/Process** | Steps with arrows, numbered connectors |
| **4f. Image Showcase** | Hero image dominant, text supporting |

- **Elements**: Title (36–44px), body (14–16px **LEFT-ALIGNED**), visual element (always required), **page badge (MANDATORY)**
- **Image**: **MANDATORY**

### Type 5: Summary / Closing — wrap-up, action items, thank-you
- **Elements**: Closing title (48–72px), takeaways (18–24px), CTA, contact, **page badge (MANDATORY)**
- **Layouts**: Key Takeaways, CTA/Next Steps, Thank You/Contact, Split Recap · Image: optional

---

## Presenter Mode (🎤 演讲者模式)

Press **S** opens a new window with 4 draggable/resizable magnetic cards (positions persist to `localStorage`):
- 🔵 **CURRENT** — iframe preview of current slide
- 🟣 **NEXT** — iframe preview of next slide
- 🟠 **SPEAKER SCRIPT** — large-font 逐字稿 (scrollable)
- 🟢 **TIMER** — elapsed time + slide counter + prev/next/reset

Previews use `<iframe src="?preview=N">` — same CSS/fonts as audience view, pixel-perfect.

**逐字稿 rules**: 150-300 words/slide, 口语化, keywords bold, transition sentences standalone (过渡句独立成段). NEVER put presenter-only text on the slide — use `<aside class="notes">` (visible in presenter).

**⚠️ CRITICAL: `<aside class="notes">` is NOT auto-hidden.** Without explicit CSS it renders on the slide AND expands `section.slide`, breaking flex centering — `.slide-content` shifts off-viewport under `transform: scale()` (content appears cropped/shifted). Every slide with notes MUST include in the Appendix A style block:

```css
section.slide { display:flex; justify-content:center; align-items:center; width:100%; height:100%; }
aside.notes { display:none; }
```

`aside.notes { display:none; }` hides it from the audience slide while `N` drawer still reads `innerHTML` — hiding does NOT break presenter mode.

All 15 full-deck concept templates support presenter mode (built per `references/full-decks.md`). `presenter-mode-reveal` has built-in 逐字稿 examples in its description.

---

## Keyboard Shortcuts

| Key | Audience | Presenter Window |
|-----|----------|-----------------|
| `←` `→` `Space` | Navigate | Navigate (syncs) |
| `F` | Fullscreen | — |
| `T` | Cycle themes | — |
| `A` | Cycle animations | — |
| `S` | Open presenter | — |
| `O` | Overview grid | — |
| `N` | Notes drawer | — |
| `#/N` | Deep-link to slide N | — |
| `R` | — | Reset timer |
| `Esc` | Close overlays | Close popup |

---

## HTML Implementation Rules

**MUST read** `references/html-implementation.md` + `references/svg-guidelines.md` before writing any HTML.

**Critical constraints**:
- ✅ Inline CSS only (except responsive scaling snippet in Appendix A)
- ✅ Solid colors only (no gradients)
- ✅ SVG for decorative shapes only
- ⚠️ SVG paths: **M/L/H/V/Z commands ONLY** — no Bézier curves, no arcs (PPTX converter skips them)
- ⚠️ **NO absolute-positioned text over SVG** — text lost in PPTX export
- ⚠️ Pie charts: use `GenerateImage`, not SVG (SVG pie fails in PPTX)
- ⚠️ Page number badge: required on ALL slides except cover
- ⚠️ **Font for PPTX export**: prefer `Times New Roman` / `Arial` over Noto fonts — Windows PPTX converter may lack CJK fonts. Embed note: "如需 PPTX 导出，建议在 HTML 中临时切换为 Times New Roman 以避免中文缺字"

---

## Failure Handling（失败模式与兜底）

> **PRINCIPLE**: Every script can fail. Every template may be missing. Never leave the user with a broken deck or a silent error. Always have a fallback path.

**Escalate BEFORE asking the user:**

### 1. Template missing → rebuild from references

| Trigger | First-line fix | Still failing → Fallback |
|---------|---------------|--------------------------|
| `templates/full-decks/<name>/` or `templates/art-directed/<name>/` does not exist | Re-check spelling; search nearest existing (`templates/full-decks/*` or `templates/art-directed/*`) | Build from `references/full-decks.md` / `references/layouts.md` description + `references/html-implementation.md` rules, inline CSS only |
| CSS theme file missing in `assets/themes/` | Use closest existing theme from `references/themes.md` | Fall back to 4-dimension design system (Route D) + default Noto fonts |

### 2. Script failures → manual fallback

| Trigger | First-line fix | Still failing → Fallback |
|---------|---------------|--------------------------|
| `bun scripts/verify_layout.ts` exits non-zero | Read reported check; fix slide (badge, dimensions, font) | Manually verify: 960×540 `.slide-content`, badge except cover, left-aligned body, no emoji-as-icon |
| `bun scripts/generate_image.ts` fails (network/API key) | Retry once; simplify prompt | Inline SVG placeholder with `[Image: description]` label; tell user image step skipped |
| `bun scripts/deploy_presentation.ts` fails | Check output dir writable; slides exist | Deliver `slides/` directory as-is (each slide standalone) |

### 3. Runtime / asset failures → degrade gracefully

| Trigger | First-line fix | Still failing → Fallback |
|---------|---------------|--------------------------|
| `runtime.js` missing from `../assets/` | Inline keyboard-nav code into deck HTML | Ship with browser-native arrow-key nav (inline `onkeydown`); note limitation |
| Noto fonts fail (offline) | Keep font stack (degrades to sans-serif) | PPTX export: switch to Times New Roman/Arial per HTML Rules |
| PPTX shows missing CJK glyphs | Temporary font swap in HTML | Deliver HTML-only; tell user PPTX requires font swap |

### 4. User content problems → ask, don't invent

| Trigger | First-line fix | Still failing → Fallback |
|---------|---------------|--------------------------|
| User gives too little content for N slides | Ask ONE clarifying question about key facts | Build outline with `[User data: X]` placeholders — never fabricate metrics |
| Request contradicts template (e.g. 3:4 xhs + presenter mode) | Ask which constraint wins | Default: format over mode (3:4 wins, skip presenter notes) |

**Escalation rule**: If first-line fix + fallback both fail, STOP and report: what failed, what you tried, what you delivered instead. Never claim a slide was verified when it was not.

---

## Anti-Patterns (Top 10)

1. ❌ Accent lines under titles — use whitespace or background color
2. ❌ More than 6 bullet points — split into multiple slides
3. ❌ Emojis as icons — use SVG (Heroicons/Lucide)
4. ❌ Gradients or animations when PPTX export needed — solid + static only
5. ❌ Centered body text — left-align paragraphs and lists
6. ❌ Bézier curves/arcs in SVG paths — M/L/H/V/Z only
7. ❌ Text-only slides — always add images/icons/charts
8. ❌ Low-contrast elements — ensure strong contrast against background
9. ❌ Repeating same layout — vary columns, cards, callouts
10. ❌ Presenter notes visible on slide — use `<aside class="notes">`, not visible `<p>`

---

## Tools Reference

| Tool Script | Purpose | Command |
|-------------|---------|---------|
| Image Generation | Create slide images | `bun scripts/generate_image.ts --prompt "..." --output path.png` |
| Screenshot | Capture slide as PNG | `bun scripts/screenshot_html.ts --html slide.html --output out.png` |
| Layout Verify | Check slide structure | `bun scripts/verify_layout.ts --html slide.html --type cover` |
| Deploy | Merge slides | `bun scripts/deploy_presentation.ts --slides ./slides --output ./dist` |

Full usage: `scripts/README.md`.

**Prerequisites**: `npm install` (or `bun install`) · `npx playwright install chromium` (for screenshot).

---

## Reference Files

Read via `read_skill_file` as needed:

- **Design & Style**: `references/design-styles.md` (4-dim system) · `references/color-palettes.md` (18 palettes) · `references/themes.md` (36 themes)
- **Quality**: `references/anti-patterns.md` · `references/pre-delivery-checklist.md`
- **Technical**: `references/html-implementation.md` (Appendix A-G) · `references/svg-guidelines.md`
- **Templates**: `references/full-decks.md` (15 concept decks) · `references/layouts.md` (31 layouts) · `references/animations.md` (27 CSS + 20 FX) · `references/presenter-mode.md` · `references/authoring-guide.md`
- **Art-Directed**: `templates/art-directed/README.md` (32-template catalog) · `templates/art-directed/html-ppt-zhangzara-{name}/` (SKILL.md / template.json / example.html / LICENSE)
- **Tools**: `scripts/README.md`
