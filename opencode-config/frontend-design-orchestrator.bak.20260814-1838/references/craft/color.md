# Color craft rules

Universal color rules applied on top of the active `DESIGN.md`. The
design system supplies the palette tokens; this file enforces how to
*use* them.

> Adapted from [refero_skill](https://github.com/referodesign/refero_skill)
> (MIT). All examples reference Open Design's standard tokens
> (`--bg`, `--surface`, `--fg`, `--muted`, `--border`, `--accent`).

## Palette structure

A coherent palette has four layers. Plan all four before writing any CSS.

| Layer | Share of pixels | Tokens |
|---|---|---|
| **Neutrals** | 70–90% | `--bg`, `--surface`, `--fg`, `--muted`, `--border` |
| **Accent** (one) | 5–10% | `--accent` only — never invent a second accent |
| **Semantic** | 0–5% | `--success`, `--warn`, `--danger` |
| **Effect** | <1% | gradients, glows; rarely justified |

## Accent discipline

The single biggest readability failure in AI-generated UIs is accent
overuse. Hard caps:

- **At most 2 visible uses of `--accent` per screen.** Typical pair:
  one eyebrow / chip + one primary CTA. Or one accent card + one tab
  pill. Pick a pair, not a flood.
- Links count as accent; demote to `--fg` underline if you also have a
  CTA on the same screen.
- Hover/focus rings count as accent. Ration accordingly.

## Contrast minimums

Run these as gates, not goals:

| Pair | Minimum |
|---|---|
| Body text (≤16 px) on background | **4.5:1** |
| Large text (>18 px or 14 px bold) | **3:1** |
| UI components against adjacent surfaces | **3:1** |

When the brand color clashes (low-contrast indigo on light background is
common), darken the accent to a `600`-level shade for text use; reserve
the brand-bright variant for fills only.

## Dark themes

Avoid pure black and pure white — both cause vibration and eye strain.

| Token | Dark theme | Light theme |
|---|---|---|
| Background | `#0f0f0f` (not `#000`) | `#fafafa` (not `#fff`) |
| Foreground | `#f0f0f0` (not `#fff`) | `#111111` (not `#000`) |

On dark surfaces, prefer **semi-transparent white borders** over solid
dark borders — a 1px `rgba(255,255,255,0.08)` reads as structure
without adding visual noise.

## Semantic color naming

Always name tokens by **purpose**, never by hue:

```css
/* good */
--accent: #2f6feb;
--success: #17a34a;

/* bad — locks you out of theming */
--blue-500: #2f6feb;
--green-500: #17a34a;
```

## Anti-defaults

- **Indigo `#6366f1`** (Tailwind `indigo-500`) is the most reliable
  AI-slop tell. The active `DESIGN.md` provides `--accent`; use it. If
  the brief truly needs indigo, make the user say so explicitly. If
  your `DESIGN.md` encodes indigo as `--accent`, that is intentional —
  the linter only flags hardcoded hex, so `var(--accent)` uses are
  unaffected even when the resolved color happens to be `#6366f1`.
- **Two-stop "trust" gradient** (purple → blue, blue → cyan, etc.) on a
  hero is the second most reliable tell. A flat surface + one
  type-driven hierarchy beats it every time.
- **Decorative gradients with no functional purpose**. Gradients should
  separate hierarchies (header → body, primary CTA → secondary), not
  decorate empty space.

## OKLCH color space

> Added from agentic-island design system analysis. OKLCH is the modern
> alternative to sRGB/HEX for theme systems.

### Why OKLCH

OKLCH (Oklab Lightness-Chroma-Hue) is a **perceptually uniform** color
space. Unlike sRGB where the same hex delta can look very different
depending on the hue, OKLCH guarantees that equal numeric changes produce
equal perceived changes. This matters for theme systems:

| Property | sRGB/HEX | OKLCH |
|---|---|---|
| Perceptual uniformity | No — blue looks darker than yellow at same luminance | Yes — lightness is linear |
| Gamut | Limited to sRGB triangle | Wider (covers P3 display gamut) |
| Theme switching | Must manually adjust each hex | Change lightness axis, colors stay harmonious |
| Accessibility | Must check each pair individually | Lightness axis maps directly to WCAG contrast |

### OKLCH syntax

```css
/* OKLCH: lightness (0-1), chroma (0-0.4), hue (0-360) */
--accent: oklch(0.65 0.2 250);

/* Dark theme: same hue, lower lightness */
--accent-dark: oklch(0.55 0.2 250);

/* Light theme: same hue, higher lightness */
--accent-light: oklch(0.75 0.2 250);
```

### When to use OKLCH

- **Theme systems** with light/dark variants — lightness axis maps directly
- **Design tokens** that need to stay harmonious across themes
- **Dynamic color generation** (user-picked brand colors → full palette)
- **Accessibility-first** palettes — lightness guarantees contrast

### When to stick with sRGB/HEX

- **Brand colors** already defined in HEX (don't migrate existing brands)
- **Simple projects** with 1-2 fixed colors
- **Legacy codebases** where migration cost exceeds benefit
- **Cross-platform consistency** — not all tools support OKLCH yet

### OKLCH theme generation pattern

```css
:root {
  /* Define accent in OKLCH */
  --accent-hue: 250;
  --accent-chroma: 0.2;

  /* Light theme: high lightness */
  --accent: oklch(0.65 var(--accent-chroma) var(--accent-hue));
  --bg: oklch(0.98 0.01 var(--accent-hue));
  --fg: oklch(0.15 0.02 var(--accent-hue));
}

@media (prefers-color-scheme: dark) {
  :root {
    /* Dark theme: low lightness, same hue */
    --accent: oklch(0.55 var(--accent-chroma) var(--accent-hue));
    --bg: oklch(0.12 0.02 var(--accent-hue));
    --fg: oklch(0.92 0.01 var(--accent-hue));
  }
}
```

### Browser support

OKLCH is supported in Chrome 111+, Firefox 113+, Safari 15.4+. For older
browsers, use a PostCSS plugin or provide HEX fallbacks.

### Tools

> Source: [evilmartians/oklch-picker](https://github.com/evilmartians/oklch-picker) (MIT).

- **[oklch.com](https://oklch.com)** — OKLCH color picker & converter.
  Convert hex/RGB/HSL → OKLCH visually; preview how a color family shifts
  as you drag lightness/chroma/hue.
- **[lch.oklch.com](https://lch.oklch.com)** — LCH color picker (legacy
  Lab-based variant; useful when you need the pre-OKLCH behavior).

**Why OKLCH over HSL/RGB (from the project README):**

| Benefit | Explanation |
|---|---|
| Native browser support | `oklch()` function works in modern browsers |
| Wider gamut | Encodes P3, Rec. 2020 and beyond — not just sRGB |
| Predictable contrast | After color transforms, contrast stays predictable (unlike HSL, which [shifts perceived lightness unpredictably](https://wildbit.com/blog/accessible-palette-stop-using-hsl-for-color-systems)) |
| No hue shift | Unlike LCH/Lab, chroma changes [do not shift hue](https://bottosson.github.io/posts/oklab/#blending-colors) |
| Palette accessibility | Great for generating accessible palettes |

**Reference reading:**

- [OKLCH in CSS: why we moved from RGB and HSL](https://evilmartians.com/chronicles/oklch-in-css-why-quit-rgb-hsl) — evilmartians, the why
- [The article by Oklab creator](https://bottosson.github.io/posts/oklab/) — Björn Ottosson, the math & origin

### Common mistakes

- **Using OKLCH for brand colors** — brands are defined in HEX, don't
  introduce a new color space for existing assets.
- **Ignoring chroma limits** — chroma > 0.37 at high lightness exceeds
  sRGB gamut and gets clipped. Test on sRGB displays.
- **Forgetting fallbacks** — provide HEX fallbacks for browsers without
  OKLCH support.
