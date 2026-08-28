---
name: frontend-design-orchestrator
description: Use when the user asks for a page/module DESIGN.md or design spec (login page, dashboard, 页面方案, 页面结构, 设计文档, 设计规范), to review or audit an existing DESIGN.md/设计稿审查/设计评审, to choose or standardize an icon system/图标规范 or resolve icon conflicts, or to produce the spec offline with built-in references only, including Vercel guideline review.
---

# Frontend Design Orchestrator

A hub-type skill that generates DESIGN.md documents, runs design reviews/audits, resolves icon conflicts, and reverse-engineers design systems from existing codebases. **Produces design specifications only — no implementation code.**

## Intent Router（快速路由）

| User says... | Route to |
|-------------|----------|
| "生成 / 写一份 DESIGN.md / 设计规范 / 设计文档" | → **Primary**: Generate DESIGN.md |
| "审查 / review / audit 这个设计" (with doc/URL) | → **Tertiary**: Design Review or **Quaternary**: Live Site Audit |
| "图标用哪个 / icon冲突 / Lucide vs Heroicons" | → **Secondary**: Icon Resolution |
| "从代码/仓库提取设计系统 / reverse-engineer" | → **Quinary**: Existing Repo → Design System |
| "我是PM/非技术，要看到效果" (visual verification) | → **Optional**: Interactive Prototype |
| 跨多个工作流（"review + 让它像 Linear"） | → 参见 Failure Handling §1 |

## Workflow Overview

### Primary: Generate DESIGN.md

1. **Analyze Intent**: Specific Brand (user has guidelines/repo/URL) vs. Style Reference (vibe/layout only — **NEVER** scrape hex/logos).
2. **Brand Asset Protocol** (Specific Brand only): Ask for guidelines → multi-URL scrape (homepage/pricing/docs/app) → extract hex via frequency + font via computed style → output `brand-spec.md` with Confidence labels (HIGH/MEDIUM/LOW).
3. **Junior Designer Mode**: Output 3 assumptions + 1–2 ASCII wireframes. **🔴 CHECKPOINT · 🛑 STOP**: "Are these assumptions correct? Proceed to full spec?" — prevents 20 min of wrong-direction work.
4. **Generate Full Document**: 10-section DESIGN.md (see template below).
5. **Review Output** (if requested): Vercel Guidelines + 5-Dimension critique.
6. **Deliver**: DESIGN.md + (opt) Tweaks Prototype.

### Secondary: Icon System Resolution

1. Identify conflicts → 2. Apply namespacing from `icon-systems.md` → 3. Document decision in DESIGN.md §7.

### Tertiary: Design Review

1. Load document → 2. Apply Vercel checklist + craft/anti-ai-slop.md + craft/color.md + craft/typography.md (minimum) → 3. **🔴 CHECKPOINT · 🛑 STOP**: Show problem list (severity: critical/major/minor/style). "Does this list look right? Any misses?" → 4. Generate structured report with fixes.

### Quaternary: Live Site Audit

*Use when the user provides a URL and wants a structured design audit of a live website.*

1. Scope URLs (homepage+pricing+docs+app) → 2. Run 7-dimension audit (Hierarchy/Spacing/Color/Accessibility/AI-Slop/Motion/Copy) → 3. Score each 0–10, top 3 issues per category with priority (P0/P1/P2) → 4. **🔴 CHECKPOINT · 🛑 STOP**: Show scores. "Any scores that feel off?" → 5. Generate punch list (impact × effort).

### Quinary: Existing Repo → Design System

*Use when the user wants to reverse-engineer a DESIGN.md from an existing codebase. Target: ~90% inference from code + ~10% editorial polish. Common failure modes → see Failure Handling §2.*

1. Scope: one package, NOT monorepo root → 2. Target: `globals.css` + `tailwind.config.{js,ts}` + `src/components/` + `theme.ts`. Exclude `dist/`, `build/`, `node_modules/` → 3. Infer tokens: cite `file:line`, label observed/inferred → 4. Editorial pass: fix crossed color roles, collapsed spacing, missed variants, swallowed dark mode → 5. **🔴 CHECKPOINT · 🛑 STOP**: Show extracted tokens with confidence. "Do these look accurate?" → 6. Commit DESIGN.md.

### Optional: Interactive Prototype with Tweaks

*Use when the user is a non-technical stakeholder (PM/Designer) who needs visual verification rather than a technical spec.*

For non-technical stakeholders needing visual verification.

1. Generate base DESIGN.md (Primary workflow) → 2. Guide `frontend-design` skill to scaffold HTML prototype → 3. Implement Tweaks panel (CSS variables, `/*EDITMODE-BEGIN*/.../*EDITMODE-END*/` markers, `postMessage` contracts) → 4. **🔴 CHECKPOINT · 🛑 STOP**: "DESIGN.md + prototype ready. Review together or proceed?" → 5. Deliver dual artifacts.

## DESIGN.md Structure（10-Section Template）

| # | Section | What to cover |
|---|---------|--------------|
| 1 | Visual Theme | Mood, visual direction, reference inspirations, design rationale |
| 2 | Color Palette | Primary/secondary/accent/semantic/neutral with hex + roles; dark theme values |
| 3 | Typography | Font stack (display/body/mono), type scale (px + rem), weight rules |
| 4 | Components | Key UI primitives (buttons/inputs/cards/modals/tables) with states and variants |
| 5 | Layout | Grid system, breakpoints, spacing scale, shell structure (sidebar/navbar/canvas) |
| 6 | Depth | Shadows, layering (z-index), elevation system |
| 7 | Icon System | Icon library choice, sizing, stroke width, naming convention |
| 8 | Responsive | Breakpoint strategy, mobile adaptations, touch target minimums (44px) |
| 9 | Review Log | Date, reviewer, checklist basis, findings, revision status |
| 10 | Assumptions & Open Questions | What was assumed, what needs user confirmation, confidence ratings |

Full template: `references/design-md-template.md`. Examples: `references/design-md-examples/`.

## Design Principles

**Junior Designer Mode (default)**: Never go dark. Show assumptions + wireframes BEFORE the full spec. "Correcting early is 100× cheaper."

**Anti-AI Slop — the 4 P0 violations you MUST avoid** (full checklist: `references/craft/anti-ai-slop.md`):

| # | P0 Rule | Fix |
|---|---------|-----|
| 1 | Default Tailwind indigo (`#6366f1` etc.) as accent | Use brand-derived `--accent` from DESIGN.md |
| 2 | Two-stop "trust" gradient on hero (purple→blue, blue→cyan) | Flat surface + intentional type |
| 3 | Emoji as feature icons (`✨🚀🎯⚡🔥💡`) | 1.6–1.8px-stroke monoline SVG, `currentColor` |
| 4 | Rounded card + colored left-border accent | Drop radius OR drop the left border |

Additional P0/P1/P2 rules + auto-check guidance → `references/craft/anti-ai-slop.md` + `review-rules.md` §6.

**Content discipline**: Never invent metrics. Placeholder `[User data: X]`. Desktop text ≥24px, mobile targets ≥44px. Max 1–2 background colors.

## Common Mistakes（防坑速查）

| If you catch yourself... | Stop and do this instead |
|--------------------------|--------------------------|
| Skipping sections in the 10-section template | Use `design-md-template.md` — never skip |
| Writing CSS/React/Vue implementation | Redirect: "This skill produces design specs. For implementation, use `frontend-design`." |
| Handling non-design requests (backend, business logic) | Reject: "This skill handles frontend design specifications only." |
| Using "to be confirmed" to defer decisions | Distinguish: open questions (minor) vs. must-resolve constraints (core) — document rationale for the latter |
| Designing from memory instead of reading actual theme.css | Extract exact values (hex/spacing/fonts/radii) from source files — `file:line` citations required |
| Filling empty sections with fake data | Use `[User's Actual Copy Here]` — ask user, don't invent |
| Justifying gaps with "implementation can fill in" | Flag missing info as a blocker, not a footnote |

## Failure Handling（失败模式与兜底）

> When execution hits a wall, escalate BEFORE guessing. Every workflow has a fallback.

### 1. Ambiguous intent → route correctly

| Trigger | First-line fix | Still failing → Fallback |
|---------|---------------|--------------------------|
| Request matches 2+ workflows | Ask ONE clarifying question (include "do you have a screenshot/URL/file?"); ask ONCE — if no response, proceed to fallback | Default to Primary workflow |
| "Design document" but no context at all | Start Junior Designer Mode with 3 domain-default assumptions | Ask: "What is the ONE thing you know about this design?" |

### 2. Missing assets → degrade, don't invent

| Trigger | First-line fix | Still failing → Fallback |
|---------|---------------|--------------------------|
| **Specific Brand** route: no guidelines/repo/URL | Switch to Style Reference; document in assumptions | If user volunteered a reference (e.g. "像 Apple") — use directly, do NOT ask again. If none: ask for ONE reference product (vibe only). **Critical**: even Apple/Linear/Stripe/Vercel are Style Reference — NEVER extract their hex/logos/exact fonts. |
| Multi-URL scrape fails | Retry `?format=text`; skip failed URLs; tag `[could not fetch]` | Homepage-only + "Confidence: LOW" labels |
| `globals.css` / `tailwind.config.ts` not found | Re-check scope; ask user for one package/directory | Report missing files + ask for correct path |

### 3. Review target unclear → define, don't improvise

| Trigger | First-line fix | Still failing → Fallback |
|---------|---------------|--------------------------|
| Design Review: no document, verbal description only | Treat description as document; "confidence: MEDIUM" | Ask for ONE screenshot or URL |
| Live Site Audit: URL returns 4xx/5xx or login wall | Ask for alternative URL or credentials | Audit public surfaces only; `[login required — not reviewed]` |
| Review finds 0 issues in clearly problematic design | Re-run with ALL craft rulebooks (anti-ai-slop + color + typography + accessibility-baseline minimum) | Report + suggest expanding scope |

### 4. Downstream agent unavailable → adapt delivery

| Trigger | First-line fix | Still failing → Fallback |
|---------|---------------|--------------------------|
| `frontend-design` skill not available (Interactive Prototype) | Scaffold minimal HTML inline (layout + CSS variables, no Tweaks) | Deliver DESIGN.md only + install guide |
| User asks for implementation code | Redirect: "This skill produces specs only" | Point to Excluded Outputs; guide to implementation skills |

**Escalation rule**: If first-line fix + fallback both fail, STOP and report: what failed, what you tried, what you can still deliver. Never fabricate brand data, URLs, or repo contents.

## Reference Files Index

Read via `read_skill_file` as needed:

- **Core templates**: `design-md-template.md` (10-section structure) · `design-md-examples/` (Linear, Vercel, Apple) · `design-sources.md` (inspiration)
- **Review rules**: `review-rules.md` (Vercel + Anti-AI Slop checklist) · `icon-systems.md`
- **Craft rules** (brand-agnostic design discipline): `craft/README.md` (index) · `craft/anti-ai-slop.md` (P0 auto-checked) · `craft/color.md` · `craft/typography.md` · `craft/typography-hierarchy.md` · `craft/typography-hierarchy-editorial.md` · `craft/laws-of-ux.md` · `craft/animation-discipline.md` · `craft/accessibility-baseline.md` · `craft/state-coverage.md` · `craft/form-validation.md` · `craft/rtl-and-bidi.md`

## Output Artifacts

### Primary: DESIGN.md (10 sections)
Visual Theme → Color Palette → Typography → Components → Layout → Depth → Icon System → Responsive → Review Log → Assumptions & Open Questions.

### Secondary: Review Artifacts
Structured problem list with severity (critical/major/minor/style), specific fixes, and Vercel guideline references.

### Excluded
No implementation code, token mapping files, icon inventories, build config, or asset downloads.

## Quick Start

| User says | Expected workflow |
|-----------|------------------|
| "I need a design document for a dashboard homepage" | → Primary: Junior Designer → show assumptions → confirm → generate full 10-section DESIGN.md |
| "Review this design against Vercel guidelines" | → Tertiary: Load document → apply craft/anti-ai-slop + craft/color + craft/typography → show problem list ✓ → generate report |
| "We have both Lucide and Heroicons — which one?" | → Secondary: Apply criteria from `icon-systems.md` → document decision in DESIGN.md §7 |
