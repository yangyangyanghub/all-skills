# Animation Directory

27 CSS entry animations + 20 Canvas FX effects. These are **optional** and only enabled when the user explicitly requests animated slides. By default, all slides are static (see `references/html-implementation.md` for the no-animation mandate).

---

## CSS Entry Animations (27)

Applied to individual elements via `data-anim="animation-name"` attribute. These handle how content appears on screen.

### Fade & Slide (8)

| animation | description | best for |
|---|---|---|
| `fade-up` | Content fades in while sliding up 20px | Standard bullet list entrances |
| `fade-down` | Content fades in while sliding down 20px | Subtitle or supporting text reveals |
| `fade-left` | Content fades in from the right side | Multi-panel sequential entrances |
| `fade-right` | Content fades in from the left side | Timeline entries, left-to-right flow |
| `rise-in` | Content rises from bottom with slight bounce | Page title entrances, stat callouts |
| `blur-in` | Content starts blurred, sharpens to focus | Quote reveals, emphasis moments |
| `scale-in` | Content scales from 80% to 100% with fade | Card or image appearances |
| `swing-in` | Content swings in like a pendulum with easing | Playful or creative presentations |

### Zoom & Pop (4)

| animation | description | best for |
|---|---|---|
| `zoom-pop` | Quick scale zoom with overshoot, then settle | Stat numbers, key metrics reveal |
| `parallax-tilt` | Layered elements move at different scroll speeds | Cover page depth effects |
| `perspective-zoom` | 3D perspective camera zoom through content | Opening sequences, immersive moments |
| `kenburns` | Slow pan + zoom on background image (Ken Burns effect) | Hero image backgrounds, photo showcases |

### Text Effects (5)

| animation | description | best for |
|---|---|---|
| `typewriter` | Characters appear one-by-one with cursor blink | Code demos, terminal outputs, key phrases |
| `glitch-in` | Digital glitch distortion resolving into clear text | Tech/cybersecurity themes, error states |
| `neon-glow` | Text appears with pulsing neon glow effect | Cyberpunk themes, nightlife/gaming |
| `stagger-list` | List items appear in sequence with fixed delay | Bullet lists, numbered items, step sequences |
| `counter-up` | Numbers count up from 0 to final value | Statistics, KPIs, metric highlights |

### Visual Sweep (4)

| animation | description | best for |
|---|---|---|
| `shimmer-sweep` | Light band sweeps across element (shimmer effect) | Premium feel, product launches |
| `gradient-flow` | Background gradient slowly shifts position | Cover page backgrounds, accent bars |
| `ripple-reveal` | Content appears with expanding ripple effect | CTA buttons, interactive feels |
| `spotlight` | Dimmed background with moving light highlight | Focus attention on specific area |

### Shape Morphing (3)

| animation | description | best for |
|---|---|---|
| `path-draw` | SVG path appears as if being drawn in real-time | Line charts, connector arrows, diagrams |
| `morph-shape` | One SVG shape smoothly morphs into another | Before/after transitions, concept evolution |
| `card-flip-3d` | 3D card rotation revealing back face | Comparison reveals (flip from A to B) |

### 3D Effects (3)

| animation | description | best for |
|---|---|---|
| `cube-rotate-3d` | Content appears from 3D cube rotation | Section transitions, topic changes |
| `page-turn-3d` | 3D page flip revealing next content | Storytelling, narrative flows |

### Scroll / Continuous

| animation | description | best for |
|---|---|---|
| `marquee-scroll` | Horizontal scrolling text ticker | News tickers, rolling announcements, live stats |

---

## Canvas FX Effects (20)

Background or overlay effects rendered in a `<canvas>` element. Controlled via `data-fx="fx-name"` attribute. Auto-initialized by `fx-runtime.js` when present.

### Particle Effects (5)

| fx | description | best for |
|---|---|---|
| `particle-burst` | Burst of particles radiating from center, fading out | Cover page opening moments, celebration |
| `confetti-cannon` | Multi-colored confetti falling from top with gravity | Achievement slides, milestone celebrations |
| `firework` | Firework explosion trails on dark background | Festival themes, year-end wrap-ups |
| `sparkle-trail` | Sparkling particles follow mouse/pointer movement | Interactive covers, engagement-focused |
| `shockwave` | Expanding ring shockwave from a point | Impact moments, product launch reveals |

### Space & Network (5)

| fx | description | best for |
|---|---|---|
| `starfield` | Stars moving toward viewer, creating warp-speed effect | Futuristic covers, space-related topics |
| `constellation` | Dots connected by forming lines (constellation pattern) | Network topics, connection metaphors |
| `orbit-ring` | Objects orbiting a central point with trails | System architecture, ecosystem views |
| `galaxy-swirl` | Swirling spiral of particles (galaxy simulation) | Big data, complex system visualizations |
| `matrix-rain` | Falling green characters (Matrix-style digital rain) | Cybersecurity, coding, hacker themes |

### Abstract & Data (5)

| fx | description | best for |
|---|---|---|
| `knowledge-graph` | Nodes forming connections with labeled edges | Knowledge management, concept mapping |
| `neural-net` | Layered nodes simulating neural network activations | AI/ML topics, deep learning visualizations |
| `data-stream` | Horizontal streams of data particles flowing | Real-time data, analytics, flow metaphors |
| `gradient-blob` | Organic amorphous blobs slowly morphing | Creative covers, abstract backgrounds |
| `magnetic-field` | Field lines emanating from poles, animated | Physics topics, force/energy metaphors |

### Typography FX (3)

| fx | description | best for |
|---|---|---|
| `word-cascade` | Words falling into place from above, cascading sequence | Poetry, manifesto, vision statement slides |
| `letter-explode` | Letters scatter and then assemble into words | Creative reveals, puzzle-solving moments |
| `typewriter-multi` | Multiple lines typing simultaneously at different speeds | Multi-point reveals, code generation demos |

### Counter & Chain (2)

| fx | description | best for |
|---|---|---|
| `chain-react` | One element triggers next in visible chain reaction | Process flows, cause-and-effect stories |
| `counter-explosion` | Counter rapidly increases; upon completion, particles explode | KPI achievement moments, big reveals |

---

## Usage Guide

### HTML Attribute Syntax

```html
<!-- Element entrance animation -->
<div data-anim="fade-up" data-delay="0.2s">Content</div>

<!-- Background canvas effect -->
<canvas data-fx="particle-burst" data-fx-intensity="medium"></canvas>
```

### Attributes

| attribute | values | default | purpose |
|---|---|---|---|
| `data-anim` | Any CSS animation name from this file | (none) | Entry animation for element |
| `data-delay` | Time string (e.g., `0.2s`, `500ms`) | `0s` | Delay before animation starts |
| `data-duration` | Time string (e.g., `0.8s`) | Auto-detect | Animation duration override |
| `data-fx` | Any Canvas FX name from this file | (none) | Background canvas effect |
| `data-fx-intensity` | `low`, `medium`, `high` | `medium` | FX particle density / activity |

### Staggering Lists

```html
<div data-anim="stagger-list">
  <div data-stagger="0">First item</div>
  <div data-stagger="1">Second item</div>
  <div data-stagger="2">Third item</div>
</div>
```

### Runtime Initialization

When `fx-runtime.js` is included in the presentation, Canvas FX effects are auto-detected and initialized:

```html
<!-- Include at bottom of merged presentation HTML -->
<script src="fx-runtime.js"></script>
```

`fx-runtime.js` will:
1. Scan all pages for `data-fx` attributes on `<canvas>` elements
2. Initialize the named FX effect for each canvas found
3. Respect `data-fx-intensity` setting for particle density
4. Clean up canvases when navigating away from a page

### Animation Guidelines

| guideline | detail |
|---|---|
| **Default = static** | Unless user explicitly requests animations, all slides are static |
| **Max 2 animations per slide** | Too many animations create visual chaos |
| **Avoid on mobile export** | Animations may not survive PPTX export; web-only feature |
| **Stagger sequentially** | Use `data-delay` or `data-stagger` for ordered reveal effect |
| **Keep duration ≤ 1.2s** | Longer animations feel sluggish on slides |
| **Match FX to theme** | `matrix-rain` on `catppuccin` theme will look wrong — coordinate |
| **Test in browser first** | Canvas FX requires a live browser environment, not file preview |

### Compatibility Notes

- CSS animations: Compatible with all modern browsers (Chrome, Firefox, Safari, Edge)
- Canvas FX: Requires WebCanvas support; does **not** translate to PPTX export
- `fx-runtime.js`: Must be bundled alongside merged presentation
- Animations are **skip-able** via URL parameter `?static` — useful for accessibility

### Recommended Combos

| Scenario | CSS Animation | Canvas FX |
|---|---|---|
| Cover page opening | `zoom-pop` on title | `particle-burst` or `gradient-blob` |
| Stat reveal | `counter-up` on number | None |
| Code demo | `typewriter` on code block | None |
| Achievement slide | `zoom-pop` on badge | `confetti-cannon` |
| Network topic | `fade-up` stagger | `constellation` or `neural-net` |
| Cybersecurity | `glitch-in` on headings | `matrix-rain` |
