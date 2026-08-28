# HTML Implementation Rules

This document contains all HTML implementation rules (Appendix A-G). Read before writing ANY slide HTML.

---

## Appendix A — Responsive Scaling Snippet (REQUIRED)

Every slide HTML file MUST include this in `<head>` and before `</body>`:

```html
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
html, body {
  margin: 0;
  padding: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #000;
}
.slide-content {
  width: 960px;
  height: 540px;
  position: relative;
  transform-origin: center center;
}
/* REQUIRED: section.slide is the flex child of body — it MUST also be a flex
   centering container, or .slide-content aligns top-left and clips off-viewport
   when scaled. REQUIRED: hide notes, or they render on slide and expand the section. */
section.slide {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
}
aside.notes { display: none; }
</style>
<script>
function scaleSlide() {
  const slide = document.querySelector('.slide-content');
  if (!slide) return;
  const slideWidth = 960;
  const slideHeight = 540;
  const scaleX = window.innerWidth / slideWidth;
  const scaleY = window.innerHeight / slideHeight;
  const scale = Math.min(scaleX, scaleY);
  slide.style.width = slideWidth + 'px';
  slide.style.height = slideHeight + 'px';
  slide.style.transform = `scale(${scale})`;
  slide.style.transformOrigin = 'center center';
  slide.style.flexShrink = '0';
}
window.addEventListener('load', scaleSlide);
window.addEventListener('resize', scaleSlide);
</script>
```

---

## Appendix B — CSS Rules (REQUIRED)

### ⚠️ Inline-Only CSS

**All CSS styles MUST be inline (except the snippet in Appendix A).**

- Do NOT use `<style>` blocks outside Appendix A
- Do NOT use external stylesheets
- Do NOT use CSS classes or class-based styling

```html
<!-- ✅ Correct: Inline styles -->
<div style="position:absolute; left:60px; top:120px; width:840px; height:240px; background:#023047;"></div>
<p style="position:absolute; left:60px; top:140px; font-size:28px; color:#ffffff;">Title</p>

<!-- ❌ Wrong: Style blocks or classes -->
<style>
.card { background:#023047; }
</style>
<div class="card"></div>
```

### ⚠️ Background on .slide-content Directly

**Do NOT create a full-size background DIV inside `.slide-content`. Set the background directly on `.slide-content` itself.**

```html
<!-- ✅ Correct: Background directly on .slide-content -->
<div class="slide-content" style="background:#023047;">
  <p style="position:absolute; left:60px; top:140px; ...">Title</p>
</div>

<!-- ❌ Wrong: Nested full-size background DIV -->
<div class="slide-content">
  <div style="position:absolute; left:0; top:0; width:960px; height:540px; background:#023047;"></div>
  <p style="position:absolute; left:60px; top:140px; ...">Title</p>
</div>
```

### ⚠️ No Bold for Body Text and Captions

- Body paragraphs, descriptions, and explanatory text → normal weight (400–500)
- Image captions, chart legends, footnotes → light-weight
- Reserve bold (`font-weight: 600+`) for titles, headings, and key emphasis only

### ⚠️ Chinese-First Font System

All text must use the Chinese-first font stack:

| Element | `font-family` Declaration |
|---------|--------------------------|
| **标题/大字** | `font-family: 'Noto Serif SC', 'Times New Roman', 'SimSun', serif;` |
| **正文/段落/列表** | `font-family: 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif;` |
| **代码/技术内容** | `font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;` |

**Implementation tips:**
- SVG `<text>` elements must include matching `font-family` attributes
- Inline text styling should reference this stack, not bare `sans-serif`/`serif`
- English letters and numbers render naturally through Noto's Latin glyphs

---

## Appendix C — Color Palette Rules (REQUIRED)

### ⚠️ Strict Color Palette Adherence

- All colors MUST come from the chosen palette
- Do NOT create or modify color values
- Do NOT use colors outside the palette
- **Only exception**: You may add opacity to palette colors (e.g., `rgba(r,g,b,0.1)`)

### ⚠️ No Gradients Allowed

- No CSS `linear-gradient()`, `radial-gradient()`, `conic-gradient()`
- No SVG `<linearGradient>`, `<radialGradient>`
- All fills, backgrounds, borders → solid colors only

### ⚠️ No Animations Allowed

- No CSS `animation`, `@keyframes`, or `transition`
- No JavaScript animations
- No hover effects with motion
- No SVG animations (`<animate>`, `<animateTransform>`, `<animateMotion>`)
- All slides are static presentation assets

**For visual hierarchy without gradients/animations:**
1. Use different colors from the palette
2. Use solid color + opacity overlay
3. Combine palette colors strategically

---

## Appendix D — SVG Conversion Constraints (CRITICAL)

The HTML-to-PPTX converter has STRICT SVG support limitations.

### Supported SVG Elements (WHITELIST)

- ✅ `<rect>` — rectangles (with `rx`/`ry` for rounded corners)
- ✅ `<circle>` — circles
- ✅ `<ellipse>` — ellipses
- ✅ `<line>` — straight lines
- ✅ `<polyline>` — connected line segments (stroke only, NO fill)
- ✅ `<polygon>` — closed polyline (stroke only, NO fill)
- ✅ `<path>` — **ONLY with M/L/H/V/Z commands**
- ✅ `<pattern>` — repeating patterns

### `<path>` Command Restrictions (CRITICAL)

**ONLY these commands are supported:**
- ✅ `M/m` — moveTo
- ✅ `L/l` — lineTo
- ✅ `H/h` — horizontal line
- ✅ `V/v` — vertical line
- ✅ `Z/z` — close path

**FORBIDDEN commands (SVG will be SKIPPED in PPTX):**
- ❌ `Q/q` — quadratic Bézier curve
- ❌ `C/c` — cubic Bézier curve
- ❌ `S/s` — smooth cubic Bézier
- ❌ `T/t` — smooth quadratic Bézier
- ❌ `A/a` — elliptical arc

### Additional SVG Constraints

- ❌ NO rotated shapes — `transform="rotate()"` causes fallback failure
- ❌ NO `<text>` in complex SVGs — becomes rasterized in PPTX
- ❌ Filled `<path>` must form closed rectangles (M/L/H/V/Z only)
- ⚠️ Gradients technically supported but DISCOURAGED

### ⚠️ CRITICAL: Pie Charts — Image Generation Tool is MANDATORY

**Pie charts MUST be created using `GenerateImage`. There is NO SVG alternative.**

- SVG pie charts require arc commands (`A`) which are FORBIDDEN
- ALL workarounds (layered circles, stroke-dasharray, clip-paths, conic-gradient, rotated segments) WILL FAIL in PPTX
- The ONLY correct approach: generate as PNG/JPG image via `GenerateImage`, embed with `<img>`

```html
<!-- ✅ SUPPORTED: Simple shapes -->
<svg width="200" height="4">
  <rect width="200" height="4" rx="2" fill="#dda15e"/>
</svg>

<!-- ✅ SUPPORTED: Straight line paths -->
<svg width="100" height="100">
  <path d="M10 10 L50 10 L50 50 L10 50 Z" fill="#bc6c25"/>
</svg>

<!-- ❌ FORBIDDEN: Bézier curves -->
<svg><path d="M0 10 Q25 0 50 10 T100 10" stroke="#dda15e"/></svg>

<!-- ❌ FORBIDDEN: Arc commands -->
<svg><path d="M16 4a8 8 0 0 1 5 14.3" stroke="#dda15e"/></svg>

<!-- ⚠️ WORKAROUND: Approximate curves with line segments -->
<svg><path d="M0 10 L12 6 L25 4 L37 6 L50 10" stroke="#dda15e" stroke-width="2"/></svg>
```

---

## Appendix E — Advanced Techniques (REQUIRED)

### SVG — ONLY for Decorative Shapes (NOT a replacement for real images)

- ⚠️ SVG is for **decorative elements ONLY**. It does NOT satisfy the "real image" requirement.
- You MUST still use `GenerateImage` for actual photos/illustrations even if SVG is used for diagrams.
- Do NOT use SVG to "draw" illustrations, backgrounds, or hero visuals.

### SVG Usage Guidelines

- Prefer SVG for all decorative shapes (lines/dividers, corner accents, badges, frames, arrows)
- SVG gives pixel-crisp geometry that won't blur under `transform: scale()`
- Use SVG for masks/overlays and diagram-like UI (timeline rails, connectors)
- Rule of thumb: if it's a "shape" (not text, not a photo), SVG is usually cleanest
- ⚠️ ALWAYS check Appendix D constraints before writing SVG paths

### ⚠️ CRITICAL: Background Shapes Must Use SVG

Do NOT use CSS background/border for decorative background shapes. These must use SVG:
- Badge/tag backgrounds (rounded rectangles, pill shapes)
- Feature tag backgrounds
- Card borders
- Button-like backgrounds
- Dividers (NOT CSS `background`, `border`, or `<hr>`)

**Reason**: CSS borders/backgrounds blur under `transform: scale()`. SVG stays crisp.

```html
<!-- ✅ Correct: SVG badge with text INSIDE the SVG -->
<svg width="180" height="52" viewBox="0 0 180 52">
  <rect width="180" height="52" rx="26" fill="#fb8500"/>
  <text x="90" y="26" text-anchor="middle" dominant-baseline="central"
        font-family="'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif"
        font-size="16" font-weight="700" fill="#ffffff">LABEL</text>
</svg>

<!-- ❌ Wrong: span overlay on SVG (text lost in PPTX) -->
<div class="badge">
  <svg><rect .../></svg>
  <span>LABEL</span>
</div>

<!-- ❌ Wrong: CSS background -->
<div style="background: #fb8500; border-radius: 26px;"><span>LABEL</span></div>

<!-- ✅ Correct: SVG divider -->
<svg width="120" height="4" aria-hidden="true">
  <rect width="120" height="4" rx="2" fill="#219ebc"/>
</svg>

<!-- ❌ Wrong: CSS divider -->
<div style="width: 120px; height: 4px; background: #219ebc;"></div>
```

### SVG Use Cases

**1. Background Patterns** — Geometric textures for visual depth:

```html
<!-- Dot grid pattern -->
<svg width="100%" height="100%" style="position:absolute;top:0;left:0;opacity:0.08;pointer-events:none;">
  <defs>
    <pattern id="dots" x="0" y="0" width="40" height="40" patternUnits="userSpaceOnUse">
      <circle cx="20" cy="20" r="2" fill="currentColor"/>
    </pattern>
  </defs>
  <rect width="100%" height="100%" fill="url(#dots)"/>
</svg>

<!-- Diagonal stripes -->
<svg width="100%" height="100%" style="position:absolute;top:0;left:0;opacity:0.05;pointer-events:none;">
  <defs>
    <pattern id="stripes" width="20" height="20" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
      <rect width="10" height="20" fill="currentColor"/>
    </pattern>
  </defs>
  <rect width="100%" height="100%" fill="url(#stripes)"/>
</svg>
```

**2. Decorative Elements**:

```html
<!-- L-shaped corner decoration -->
<svg width="40" height="40" style="position:absolute;top:0;left:0;" aria-hidden="true">
  <path d="M0 35 L0 0 L35 0" stroke="currentColor" stroke-width="2" fill="none" opacity="0.4"/>
</svg>

<!-- Straight divider line -->
<svg width="400" height="2" aria-hidden="true">
  <rect width="400" height="2" fill="currentColor" opacity="0.3"/>
</svg>

<!-- Simple arrow (right-pointing) -->
<svg width="40" height="16" viewBox="0 0 40 16" aria-hidden="true">
  <path d="M0 8 L32 8 M24 2 L32 8 L24 14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
</svg>
```

**3. Icons**:

```html
<!-- Checkmark icon (polyline - SUPPORTED) -->
<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
  <polyline points="20 6 9 17 4 12"/>
</svg>

<!-- Simple arrow icon (path with L/M - SUPPORTED) -->
<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M5 12 L19 12 M12 5 L19 12 L12 19"/>
</svg>

<!-- Plus sign icon (lines - SUPPORTED) -->
<svg width="24" height="24" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
  <line x1="12" y1="5" x2="12" y2="19"/>
  <line x1="5" y1="12" x2="19" y2="12"/>
</svg>
```

**4. Data Visualization Helpers**:

```html
<!-- Percentage ring (70%) -->
<svg width="100" height="100" viewBox="0 0 100 100">
  <circle cx="50" cy="50" r="40" stroke="#e0e0e0" stroke-width="8" fill="none"/>
  <circle cx="50" cy="50" r="40" stroke="#4CAF50" stroke-width="8" fill="none"
          stroke-dasharray="251.3" stroke-dashoffset="75.4" stroke-linecap="round"
          transform="rotate(-90 50 50)"/>
  <text x="50" y="50" text-anchor="middle" dominant-baseline="central"
        font-family="'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif"
        font-size="20" font-weight="bold" fill="currentColor">70%</text>
</svg>

<!-- Horizontal progress bar -->
<svg width="200" height="12" viewBox="0 0 200 12">
  <rect x="0" y="0" width="200" height="12" rx="6" fill="#e0e0e0"/>
  <rect x="0" y="0" width="140" height="12" rx="6" fill="#2196F3"/>
</svg>

<!-- Mini bar chart -->
<svg width="80" height="40" viewBox="0 0 80 40">
  <rect x="0" y="20" width="12" height="20" fill="currentColor" opacity="0.6"/>
  <rect x="17" y="10" width="12" height="30" fill="currentColor" opacity="0.8"/>
  <rect x="34" y="5" width="12" height="35" fill="currentColor"/>
  <rect x="51" y="15" width="12" height="25" fill="currentColor" opacity="0.7"/>
  <rect x="68" y="8" width="12" height="32" fill="currentColor" opacity="0.9"/>
</svg>
```

**5. Masks & Overlays**:

```html
<!-- Bottom overlay for text readability -->
<svg width="100%" height="300" style="position:absolute;bottom:0;left:0;pointer-events:none;">
  <rect width="100%" height="100%" fill="#000000" fill-opacity="0.7"/>
</svg>

<!-- Side overlay -->
<svg width="400" height="100%" style="position:absolute;left:0;top:0;pointer-events:none;">
  <rect width="100%" height="100%" fill="#000000" fill-opacity="0.8"/>
</svg>
```

### SVG Implementation Tips

- Use `vector-effect="non-scaling-stroke"` to keep stroke widths stable under `transform: scale()`
- For thin lines, prefer filled rectangles to avoid stroke anti-alias artifacts
- Use `overflow="visible"` when SVG needs to extend beyond its box
- Use `aria-hidden="true"` for purely decorative SVGs
- Use `currentColor` for easy theming
- Use `pointer-events: none` for overlay SVGs

### Minimal Patterns

```html
<!-- Crisp divider line -->
<svg overflow="visible" width="320" height="2" aria-hidden="true">
  <rect width="320" height="2" fill="rgba(255,255,255,0.35)"></rect>
</svg>

<!-- Consistent stroke under scaling -->
<svg overflow="visible" width="320" height="2" aria-hidden="true">
  <path vector-effect="non-scaling-stroke" d="M0 1 L320 1" stroke="rgba(255,255,255,0.55)" stroke-width="2"></path>
</svg>

<!-- Solid overlay -->
<svg width="100%" height="200" style="position:absolute;bottom:0;left:0;pointer-events:none;">
  <rect width="100%" height="100%" fill="#000000" fill-opacity="0.6"/>
</svg>
```

---

## Appendix F — HTML2PPTX Validation Rules (REQUIRED)

### Layout and Dimensions

- Slide content must not overflow (no scrollbars)
- Text elements larger than 12pt must be at least 0.5″ above bottom edge
- HTML body dimensions must match 960×540

### Backgrounds and Images

- No CSS gradients
- No `background-image` on `div` elements
- For slide backgrounds, use a real `<img>` element
- Solid background colors → on `.slide-content` directly

### Text Elements

- `p`, `h1`–`h6`, `ul`, `ol`, `li` must NOT have background, border, or shadow
- Inline elements (`span`, `b`, `i`, `u`, `strong`, `em`) must NOT have margins
- Do NOT use manual bullet symbols — use `<ul>` or `<ol>` lists
- Do NOT leave raw text directly inside `div` — wrap all text in text tags

### SVG and Text

- Do NOT place text (`<span>`, `<p>`) as overlay on SVG using absolute positioning — text will be LOST in PPTX
- When badge/tag/label needs text on SVG background, put text INSIDE SVG using `<text>` element
- SVG `<text>` must use `text-anchor="middle"` and `dominant-baseline="central"` for centering

```html
<!-- ✅ Correct: Text inside SVG -->
<svg width="100" height="32" viewBox="0 0 100 32">
  <rect width="100" height="32" rx="16" fill="#bc6c25"/>
  <text x="50" y="16" text-anchor="middle" dominant-baseline="central"
        font-family="'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif"
        font-size="14" font-weight="700" fill="#fefae0" letter-spacing="3">丰收季</text>
</svg>

<!-- ❌ Wrong: Text overlaid on SVG (LOST in PPTX) -->
<div class="badge">
  <svg aria-hidden="true"><rect .../></svg>
  <span style="position:absolute;">丰收季</span>
</div>
```

### Placeholders

- Elements with class `placeholder` must have non-zero width and height

---

## Appendix G — Page Number Badge / 角标 (REQUIRED)

All slides **except Cover Page** MUST include a page number badge showing the current slide number in the bottom-right corner.

- **Position**: `position:absolute; right:32px; bottom:24px;`
- **Must use SVG** (text inside `<text>`, not overlaid `<span>`)
- Colors from palette only; keep it subtle; same style across all slides
- Show current number only (e.g. `3` or `03`), NOT "3/12"

```html
<!-- ✅ Circle badge (default) -->
<svg style="position:absolute; right:32px; bottom:24px;" width="36" height="36" viewBox="0 0 36 36">
  <circle cx="18" cy="18" r="18" fill="#219ebc"/>
  <text x="18" y="18" text-anchor="middle" dominant-baseline="central"
        font-family="'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif"
        font-size="14" font-weight="600" fill="#ffffff">3</text>
</svg>

<!-- ✅ Pill badge -->
<svg style="position:absolute; right:32px; bottom:24px;" width="48" height="28" viewBox="0 0 48 28">
  <rect width="48" height="28" rx="14" fill="#219ebc"/>
  <text x="24" y="14" text-anchor="middle" dominant-baseline="central"
        font-family="'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif"
        font-size="13" font-weight="600" fill="#ffffff">03</text>
</svg>

<!-- ✅ Minimal (number only) -->
<p style="position:absolute; right:36px; bottom:24px; margin:0; font-size:13px; font-weight:500; color:#8ecae6;">03</p>
```