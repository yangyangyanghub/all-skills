# SVG Guidelines

Detailed SVG usage patterns, constraints, and best practices for HTML presentations.

---

## When to Use SVG

✅ **Use SVG for**:
- Decorative shapes (lines, dividers, corner accents, badges, frames, arrows)
- Masks and overlays
- Simple icons
- Diagram-like UI elements (timeline rails, connectors)
- Background patterns

❌ **Do NOT use SVG for**:
- Photos or illustrations → use `GenerateImage`
- Complex diagrams with text → use `GenerateImage`
- Pie charts → use `GenerateImage` (SVG arcs are FORBIDDEN)
- Hero visuals → use `GenerateImage`

---

## Supported SVG Elements (WHITELIST)

These elements are fully supported in HTML-to-PPTX conversion:

| Element | Notes |
|---------|-------|
| `<rect>` | Rectangles with `rx`/`ry` for rounded corners |
| `<circle>` | Circles |
| `<ellipse>` | Ellipses |
| `<line>` | Straight lines |
| `<polyline>` | Connected line segments (stroke only, NO fill) |
| `<polygon>` | Closed polyline (stroke only, NO fill) |
| `<path>` | **ONLY with M/L/H/V/Z commands** |
| `<pattern>` | Repeating patterns |
| `<defs>` | Definitions container |
| `<text>` | Text inside SVG (must use proper attributes) |

---

## Path Command Restrictions (CRITICAL)

### ✅ SUPPORTED Commands

| Command | Name | Usage |
|---------|------|-------|
| `M/m` | moveTo | Move to point |
| `L/l` | lineTo | Line to point |
| `H/h` | horizontal line | Horizontal line |
| `V/v` | vertical line | Vertical line |
| `Z/z` | close path | Close path |

### ❌ FORBIDDEN Commands (Will Fail in PPTX)

| Command | Name | Reason |
|---------|------|--------|
| `Q/q` | Quadratic Bézier | Not supported |
| `C/c` | Cubic Bézier | Not supported |
| `S/s` | Smooth cubic Bézier | Not supported |
| `T/t` | Smooth quadratic Bézier | Not supported |
| `A/a` | Elliptical arc | Not supported |

### Examples

```html
<!-- ✅ SUPPORTED: Straight line path -->
<svg width="100" height="100">
  <path d="M10 10 L50 10 L50 50 L10 50 Z" fill="#bc6c25"/>
</svg>

<!-- ✅ SUPPORTED: L-shaped corner -->
<svg width="40" height="40">
  <path d="M0 35 L0 0 L35 0" stroke="currentColor" stroke-width="2" fill="none"/>
</svg>

<!-- ❌ FORBIDDEN: Bézier curves -->
<svg><path d="M0 10 Q25 0 50 10 T100 10" stroke="#dda15e"/></svg>

<!-- ❌ FORBIDDEN: Arc commands -->
<svg><path d="M16 4a8 8 0 0 1 5 14.3" stroke="#dda15e"/></svg>

<!-- ⚠️ WORKAROUND: Approximate curves with line segments -->
<svg><path d="M0 10 L12 6 L25 4 L37 6 L50 10" stroke="#dda15e" stroke-width="2"/></svg>
```

---

## Pie Charts — CRITICAL CONSTRAINT

**Pie charts MUST be created using `GenerateImage`. There is NO SVG alternative.**

### Why?

- SVG pie charts require arc commands (`A`) which are FORBIDDEN
- All workarounds will fail in PPTX:
  - ❌ Layered circles with `stroke-dasharray`
  - ❌ Clip-paths
  - ❌ Conic-gradient (CSS, also forbidden)
  - ❌ Rotated segments

### Correct Approach

```
1. Use GenerateImage to create pie chart as PNG/JPG
2. Embed with <img> tag
3. Ensure high resolution for crisp rendering
```

---

## Text in SVG

### Text INSIDE SVG (Correct)

```html
<!-- ✅ Text inside SVG using <text> element -->
<svg width="180" height="52" viewBox="0 0 180 52">
  <rect width="180" height="52" rx="26" fill="#fb8500"/>
  <text x="90" y="26" text-anchor="middle" dominant-baseline="central"
        font-size="16" font-weight="700" fill="#ffffff">LABEL</text>
</svg>
```

**Required attributes for `<text>`**:
- `text-anchor="middle"` — horizontal centering
- `dominant-baseline="central"` — vertical centering
- `x` and `y` — position coordinates

### Text OVERLAY on SVG (WRONG)

```html
<!-- ❌ Text overlaid on SVG using absolute positioning -->
<!-- This text will be LOST in PPTX -->
<div class="badge">
  <svg aria-hidden="true"><rect .../></svg>
  <span style="position:absolute;">LABEL</span>
</div>
```

**Reason**: Absolute positioned text over SVG is not preserved in PPTX conversion.

---

## Common Patterns

### 1. Dividers

```html
<!-- Horizontal divider -->
<svg width="320" height="2" aria-hidden="true">
  <rect width="320" height="2" fill="rgba(255,255,255,0.35)"/>
</svg>

<!-- With rounded corners -->
<svg width="320" height="4" aria-hidden="true">
  <rect width="320" height="4" rx="2" fill="#219ebc"/>
</svg>

<!-- With vector-effect for scaling stability -->
<svg overflow="visible" width="320" height="2" aria-hidden="true">
  <path vector-effect="non-scaling-stroke" d="M0 1 L320 1" 
        stroke="rgba(255,255,255,0.55)" stroke-width="2"/>
</svg>
```

### 2. Badges / Tags

```html
<!-- Pill badge with text -->
<svg width="100" height="32" viewBox="0 0 100 32">
  <rect width="100" height="32" rx="16" fill="#bc6c25"/>
  <text x="50" y="16" text-anchor="middle" dominant-baseline="central"
        font-size="14" font-weight="700" fill="#fefae0">丰收季</text>
</svg>

<!-- Circle badge with number -->
<svg width="36" height="36" viewBox="0 0 36 36">
  <circle cx="18" cy="18" r="18" fill="#219ebc"/>
  <text x="18" y="18" text-anchor="middle" dominant-baseline="central"
        font-size="14" font-weight="600" fill="#ffffff">3</text>
</svg>
```

### 3. Icons

```html
<!-- Checkmark (polyline) -->
<svg width="24" height="24" viewBox="0 0 24 24" fill="none" 
     stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
  <polyline points="20 6 9 17 4 12"/>
</svg>

<!-- Arrow (path with L/M) -->
<svg width="24" height="24" viewBox="0 0 24 24" fill="none" 
     stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M5 12 L19 12 M12 5 L19 12 L12 19"/>
</svg>

<!-- Plus sign (lines) -->
<svg width="24" height="24" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
  <line x1="12" y1="5" x2="12" y2="19"/>
  <line x1="5" y1="12" x2="19" y2="12"/>
</svg>
```

### 4. Progress Indicators

```html
<!-- Horizontal progress bar -->
<svg width="200" height="12" viewBox="0 0 200 12">
  <rect x="0" y="0" width="200" height="12" rx="6" fill="#e0e0e0"/>
  <rect x="0" y="0" width="140" height="12" rx="6" fill="#2196F3"/>
</svg>

<!-- Percentage ring (70%) -->
<svg width="100" height="100" viewBox="0 0 100 100">
  <circle cx="50" cy="50" r="40" stroke="#e0e0e0" stroke-width="8" fill="none"/>
  <circle cx="50" cy="50" r="40" stroke="#4CAF50" stroke-width="8" fill="none"
          stroke-dasharray="251.3" stroke-dashoffset="75.4" stroke-linecap="round"
          transform="rotate(-90 50 50)"/>
  <text x="50" y="50" text-anchor="middle" dominant-baseline="central" 
        font-size="20" font-weight="bold" fill="currentColor">70%</text>
</svg>
```

### 5. Mini Charts

```html
<!-- Mini bar chart -->
<svg width="80" height="40" viewBox="0 0 80 40">
  <rect x="0" y="20" width="12" height="20" fill="currentColor" opacity="0.6"/>
  <rect x="17" y="10" width="12" height="30" fill="currentColor" opacity="0.8"/>
  <rect x="34" y="5" width="12" height="35" fill="currentColor"/>
  <rect x="51" y="15" width="12" height="25" fill="currentColor" opacity="0.7"/>
  <rect x="68" y="8" width="12" height="32" fill="currentColor" opacity="0.9"/>
</svg>
```

### 6. Overlays

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

### 7. Background Patterns

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

---

## SVG Best Practices

### 1. Use `vector-effect="non-scaling-stroke"`

Keeps stroke widths stable under `transform: scale()`:

```html
<svg overflow="visible" width="320" height="2">
  <path vector-effect="non-scaling-stroke" d="M0 1 L320 1" 
        stroke="rgba(255,255,255,0.55)" stroke-width="2"/>
</svg>
```

### 2. Use `aria-hidden="true"` for Decorative SVGs

```html
<svg width="120" height="4" aria-hidden="true">
  <rect width="120" height="4" rx="2" fill="#219ebc"/>
</svg>
```

### 3. Use `currentColor` for Easy Theming

```html
<!-- Inherits text color from parent -->
<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor">
  <polyline points="20 6 9 17 4 12"/>
</svg>
```

### 4. Use `pointer-events: none` for Overlays

```html
<svg width="100%" height="300" style="position:absolute;bottom:0;left:0;pointer-events:none;">
  <rect width="100%" height="100%" fill="#000000" fill-opacity="0.7"/>
</svg>
```

### 5. Use `overflow="visible"` When Needed

When SVG needs to extend beyond its box:

```html
<svg overflow="visible" width="320" height="2">
  ...
</svg>
```

---

## Common Mistakes

### ❌ Using CSS Background Instead of SVG

```html
<!-- Wrong: CSS background (blurs under scaling) -->
<div style="width: 120px; height: 4px; background: #219ebc;"></div>

<!-- Correct: SVG (stays crisp) -->
<svg width="120" height="4" aria-hidden="true">
  <rect width="120" height="4" fill="#219ebc"/>
</svg>
```

### ❌ Overlaying Text on SVG with Absolute Positioning

```html
<!-- Wrong: Text will be LOST in PPTX -->
<div class="badge">
  <svg><rect .../></svg>
  <span style="position:absolute;">LABEL</span>
</div>

<!-- Correct: Text inside SVG -->
<svg width="100" height="32">
  <rect width="100" height="32" rx="16" fill="#bc6c25"/>
  <text x="50" y="16" text-anchor="middle" dominant-baseline="central">LABEL</text>
</svg>
```

### ❌ Using Bézier Curves or Arcs

```html
<!-- Wrong: Bézier curves (will fail in PPTX) -->
<svg><path d="M0 10 Q25 0 50 10" stroke="#dda15e"/></svg>

<!-- Correct: Approximate with line segments -->
<svg><path d="M0 10 L12 6 L25 4 L37 6 L50 10" stroke="#dda15e"/></svg>
```

### ❌ Using SVG for Complex Visuals

```html
<!-- Wrong: SVG illustration -->
<svg width="400" height="300">
  <!-- Hundreds of paths trying to draw a landscape -->
</svg>

<!-- Correct: Generate as image -->
<img src="landscape.png" width="400" height="300"/>
```

---

## Quick Reference

| Use Case | SVG Support | Alternative |
|----------|-------------|-------------|
| Decorative shapes | ✅ Full support | — |
| Simple icons | ✅ Full support | — |
| Dividers | ✅ Full support | — |
| Badges/Tags | ✅ With `<text>` inside | — |
| Progress bars | ✅ Full support | — |
| Mini bar charts | ✅ Full support | — |
| Pie charts | ❌ NO (arcs forbidden) | `GenerateImage` |
| Line charts | ⚠️ Approximate with lines | `GenerateImage` |
| Complex diagrams | ❌ NO | `GenerateImage` |
| Photos/Illustrations | ❌ NO | `GenerateImage` |