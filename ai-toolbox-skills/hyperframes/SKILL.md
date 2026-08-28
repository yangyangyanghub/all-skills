---
name: hyperframes
description: Create vid
eo compositions, animations, title cards, ove
rlays, captions, voiceovers, audio-reactive v
isuals, and scene transitions in HyperFrames 
HTML. Use when asked to build any HTML-based 
video content, add captions or subtitles sync
ed to audio, generate text-to-speech narratio
n, create audio-reactive animation (beat sync
, glow, pulse driven by music), add animated 
text highlighting (marker sweeps, hand-drawn 
circles, burst lines, scribble, sketchout), o
r add transitions between scenes (crossfades,
 wipes, reveals, shader transitions). Covers 
composition authoring, timing, media, and the
 full video production workflow. For dev-loop
 CLI commands (init, lint, inspect, preview, 
render) see the hyperframes-cli skill; for as
set preprocessing commands (tts, transcribe, 
remove-background) see the hyperframes-media 
skill.
---

# HyperFrames

HTML is the source
 of truth for video. A composition is an HTML
 file with `data-*` attributes for timing, a 
GSAP timeline for animation, and CSS for appe
arance. The framework handles clip visibility
, media playback, and timeline sync.

## Appr
oach

### Discovery (exploratory requests onl
y)

For open-ended requests ("make me a produ
ct launch video", "create something for our b
rand") where the user hasn't committed to a d
irection, understand intent before picking co
lors:

- **Audience** — who watches this? D
evelopers? Executives? General consumers?
- *
*Platform** — where does it play? Social (1
5s), website hero, product demo, internal?
- 
**Priority** — what matters most? Motion qu
ality? Content accuracy? Brand fidelity? Spee
d?
- **Variations** — does the user want op
tions, or a single best shot?

For specific r
equests ("add a title card", "fix the timing 
on scene 3"), skip discovery.

For explorator
y requests, consider offering 2-3 variations 
that differ meaningfully — not just color s
waps, but different pacing, energy levels, or
 structural approaches. One safe/expected, on
e ambitious. Don't mandate this — it's a to
ol available when appropriate.

### Step 1: D
esign system

If a design spec exists in the 
project, read it first. Look in precedence or
der: `frame.md` → `design.md` → `DESIGN.m
d` (`design.md` and `DESIGN.md` are different
 files on Linux — check both casings; `fram
e.md` is always lowercase, no `FRAME.md` vari
ant). `frame.md` is the preferred spec for vi
deo/hyperframes projects and wins if more tha
n one exists; it uses the same format as `des
ign.md`. It's the source of truth for brand c
olors, fonts, and constraints. Use its exact 
values — don't invent colors or substitute 
fonts. Any format works (YAML frontmatter, pr
ose, tables — just extract the values).

If
 it names fonts you can't find locally (no `f
onts/` directory with `.woff2` files, not a b
uilt-in font), warn the user before writing H
TML: "the spec specifies [font name] but no f
ont files found. Please add .woff2 files to `
fonts/` or I'll fall back to [closest built-i
n alternative]."

If no `frame.md` or `design
.md` exists, offer the user a choice:

1. **U
ser named a style or mood?** → Read [visual
-styles.md](./visual-styles.md) for the 8 nam
ed presets. Pick the closest match.
2. **Want
 to browse options visually?** → Run the de
sign picker: read [references/design-picker.m
d](references/design-picker.md) for the full 
workflow. This serves a visual picker page. T
he user configures mood, palette, typography,
 and motion in the browser, then copies the g
enerated design.md and pastes it back into th
e conversation.
3. **Want to skip and go fast
?** → Ask: mood, light or dark, any brand c
olors/fonts? Then pick a palette from [house-
style.md](./house-style.md).

**The design sp
ec defines the brand. It does not define vide
o composition rules.** Those come from [refer
ences/video-composition.md](references/video-
composition.md) and [house-style.md](./house-
style.md). Use brand colors at video-appropri
ate scale — not at web-UI opacity.

### Ste
p 2: Prompt expansion

Always run on every co
mposition (except single-scene pieces and tri
vial edits). This step grounds the user's int
ent against the design spec (`frame.md` or `d
esign.md`) and `house-style.md` and produces 
a consistent intermediate that every downstre
am agent reads the same way.

Read [reference
s/prompt-expansion.md](references/prompt-expa
nsion.md) for the full process and output for
mat.

### Step 3: Plan

Before writing HTML, 
think at a high level:

1. **What** — what 
should the viewer experience? Identify the na
rrative arc, key moments, and emotional beats
.
2. **Structure** — how many compositions,
 which are sub-compositions vs inline, what t
racks carry what (video, audio, overlays, cap
tions).
3. **Rhythm** — declare your scene 
rhythm before implementing. Which scenes are 
quick hits, which are holds, where do shaders
 land, where does energy peak. Name the patte
rn: fast-fast-SLOW-fast-SHADER-hold. Read [re
ferences/beat-direction.md](references/beat-d
irection.md) for rhythm templates.
4. **Timin
g** — which clips drive the duration, where
 do transitions land, what's the pacing.
5. *
*Layout** — build the end-state first. See 
"Layout Before Animation" below.
6. **Animate
** — then add motion using the rules below.


**Build what was asked.** A request for "a 
title card" is not a request for "a title car
d + 3 supporting scenes + ambient music + cap
tions." Every scene, every element, every twe
en should earn its place. If additional scene
s or elements would genuinely improve the pie
ce, propose them — don't add them.

For sma
ll edits (fix a color, adjust timing, add one
 element), skip straight to the rules.

<HARD
-GATE>
Before writing ANY composition HTML �
� verify you have a visual identity from Step
 1. If you're reaching for `#333`, `#3b82f6`,
 or `Roboto`, you skipped it.
</HARD-GATE>

#
# Layout Before Animation

Position every ele
ment where it should be at its **most visible
 moment** — the frame where it's fully ente
red, correctly placed, and not yet exiting. W
rite this as static HTML+CSS first. No GSAP y
et.

**Why this matters:** If you position el
ements at their animated start state (offscre
en, scaled to 0, opacity 0) and tween them to
 where you think they should land, you're gue
ssing the final layout. Overlaps are invisibl
e until the video renders. By building the en
d state first, you can see and fix layout pro
blems before adding any motion.

### The proc
ess

1. **Identify the hero frame** for each 
scene — the moment when the most elements a
re simultaneously visible. This is the layout
 you build.
2. **Write static CSS** for that 
frame. The `.scene-content` container MUST fi
ll the full scene using `width: 100%; height:
 100%; padding: Npx;` with `display: flex; fl
ex-direction: column; gap: Npx; box-sizing: b
order-box`. Use padding to push content inwar
d — NEVER `position: absolute; top: Npx` on
 a content container. Absolute-positioned con
tent containers overflow when content is tall
er than the remaining space. Reserve `positio
n: absolute` for decoratives only.
3. **Add e
ntrances with `gsap.from()`** — animate FRO
M offscreen/invisible TO the CSS position. Th
e CSS position is the ground truth; the tween
 describes the journey to get there. (In sub-
compositions loaded via `data-composition-src
`, prefer `gsap.fromTo()` — see load-bearin
g GSAP rules in [references/motion-principles
.md](references/motion-principles.md).)
4. **
Add exits with `gsap.to()`** — animate TO o
ffscreen/invisible FROM the CSS position.

##
# Example

```css
/* scene-content fills the 
scene, padding positions content */
.scene-co
ntent {
  display: flex;
  flex-direction: co
lumn;
  justify-content: center;
  width: 100
%;
  height: 100%;
  padding: 120px 160px;
  
gap: 24px;
  box-sizing: border-box;
}
.title
 {
  font-size: 120px;
}
.subtitle {
  font-s
ize: 42px;
}
/* Container fills any scene siz
e (1920x1080, 1080x1920, etc).
   Padding pos
itions content. Flex + gap handles spacing. *
/
```

**WRONG — hardcoded dimensions and a
bsolute positioning:**

```css
.scene-content
 {
  position: absolute;
  top: 200px;
  left
: 160px;
  width: 1920px;
  height: 1080px;
 
 display: flex; /* ... */
}
```

```js
// Ste
p 3: Animate INTO those positions
tl.from(".t
itle", { y: 60, opacity: 0, duration: 0.6, ea
se: "power3.out" }, 0);
tl.from(".subtitle", 
{ y: 40, opacity: 0, duration: 0.5, ease: "po
wer3.out" }, 0.2);
tl.from(".logo", { scale: 
0.8, opacity: 0, duration: 0.4, ease: "power2
.out" }, 0.3);

// Step 4: Animate OUT from t
hose positions
tl.to(".title", { y: -40, opac
ity: 0, duration: 0.4, ease: "power2.in" }, 3
);
tl.to(".subtitle", { y: -30, opacity: 0, d
uration: 0.3, ease: "power2.in" }, 3.1);
tl.t
o(".logo", { scale: 0.9, opacity: 0, duration
: 0.3, ease: "power2.in" }, 3.2);
```

### Wh
en elements share space across time

If eleme
nt A exits before element B enters in the sam
e area, both should have correct CSS position
s for their respective hero frames. The timel
ine ordering guarantees they never visually c
oexist — but if you skip the layout step, y
ou won't catch the case where they accidental
ly overlap due to a timing error.

### What c
ounts as intentional overlap

Layered effects
 (glow behind text, shadow elements, backgrou
nd patterns) and z-stacked designs (card stac
ks, depth layers) are intentional. The layout
 step is about catching **unintentional** ove
rlap — two headlines landing on top of each
 other, a stat covering a label, content blee
ding off-frame.

## Data Attributes

### All 
Clips

| Attribute          | Required       
                   | Values                  
                               |
| ----------
-------- | --------------------------------- 
| -------------------------------------------
----------- |
| `id`               | Yes     
                          | Unique identifier
                                      |
| `da
ta-start`       | Yes                        
       | Seconds or clip ID reference (`"el-1
"`, `"intro + 2"`) |
| `data-duration`    | R
equired for img/div/compositions | Seconds. V
ideo/audio defaults to media duration.       
|
| `data-track-index` | Yes                 
              | Integer. Same-track clips can
not overlap.              |
| `data-media-sta
rt` | No                                | Tri
m offset into source (seconds)               
       |
| `data-volume`      | No           
                     | 0-1 (default 1)       
                                 |

`data-tra
ck-index` does **not** affect visual layering
 — use CSS `z-index`.

### Composition Clip
s

| Attribute                    | Required 
| Values                                     
                       |
| ------------------
---------- | -------- | ---------------------
-------------------------------------------- 
|
| `data-composition-id`        | Yes      |
 Unique composition ID                       
                      |
| `data-start`       
          | Yes      | Start time (root compo
sition: use `"0"`)                          |

| `data-duration`              | Yes      | 
Takes precedence over GSAP timeline duration 
                     |
| `data-width` / `data
-height` | Yes      | Pixel dimensions (1920x
1080 or 1080x1920)                         |

| `data-composition-src`       | No       | P
ath to external HTML file                    
                    |
| `data-variable-values
`       | No       | JSON object of per-insta
nce variable overrides on a sub-comp host |


On the root `<html>` element:

| Attribute   
                 | Required | Values         
                                             
                                             
                      |
| -------------------
--------- | -------- | ----------------------
---------------------------------------------
---------------------------------------------
-------------- |
| `data-composition-variable
s` | No       | JSON array of declared variab
les (id/type/label/default) — drives Studio
 editing UI and provides defaults for `getVar
iables()` |

## Composition Structure

Sub-co
mpositions loaded via `data-composition-src` 
use a `<template>` wrapper. **Standalone comp
ositions (the main index.html) do NOT use `<t
emplate>`** — they put the `data-compositio
n-id` div directly in `<body>`. Using `<templ
ate>` on a standalone file hides all content 
from the browser and breaks rendering.

Sub-c
omposition structure:

```html
<template id="
my-comp-template">
  <div data-composition-id
="my-comp" data-width="1920" data-height="108
0">
    <!-- content -->
    <style>
      [d
ata-composition-id="my-comp"] {
        /* sc
oped styles */
      }
    </style>
    <scri
pt src="https://cdn.jsdelivr.net/npm/gsap@3.1
4.2/dist/gsap.min.js"></script>
    <script>

      window.__timelines = window.__timelines
 || {};
      const tl = gsap.timeline({ paus
ed: true });
      // tweens...
      window.
__timelines["my-comp"] = tl;
    </script>
  
</div>
</template>
```

Load in root: `<div i
d="el-1" data-composition-id="my-comp" data-c
omposition-src="compositions/my-comp.html" da
ta-start="0" data-duration="10" data-track-in
dex="1"></div>`

## Variables (Parametrized C
ompositions)

Render the same composition wit
h different content — title, theme color, p
rices, captions — without editing the sourc
e HTML.

**Three-step pattern:**

1. **Declar
e** variables on the composition's `<html>` r
oot with `data-composition-variables`. Each e
ntry needs `id`, `type` (one of `string`, `nu
mber`, `color`, `boolean`, `enum`), `label`, 
and `default`. Enum entries also need `option
s: [{value, label}, ...]`.
2. **Read** the re
solved values inside the composition's script
 with `window.__hyperframes.getVariables()`. 
Returns the merged result of declared default
s + per-instance overrides + CLI overrides.
3
. **Override** at render time with `npx hyper
frames render --variables '{...}'` (top-level
) or with `data-variable-values='{...}'` on t
he host element (per-instance for sub-comps).


```html
<!doctype html>
<html
  data-compos
ition-variables='[
  {"id":"title","type":"st
ring","label":"Title","default":"Hello"},
  {
"id":"theme","type":"enum","label":"Theme","d
efault":"light","options":[
    {"value":"lig
ht","label":"Light"},
    {"value":"dark","la
bel":"Dark"}
  ]}
]'
>
  <body>
    <div data
-composition-id="root" data-width="1920" data
-height="1080">
      <h1 id="hero" class="cl
ip" data-start="0" data-duration="3"></h1>
  
    <script>
        const { title, theme } =
 window.__hyperframes.getVariables();
       
 document.getElementById("hero").textContent 
= title;
        document.body.dataset.theme 
= theme;
      </script>
    </div>
  </body>

</html>
```

```bash
# Dev preview uses decl
ared defaults
npx hyperframes preview

# Rend
er with overrides
npx hyperframes render --va
riables '{"title":"Q4 Report","theme":"dark"}
' --output q4.mp4

# Or from a JSON file
npx 
hyperframes render --variables-file ./vars.js
on
```

**Sub-composition per-instance values
:** the same `getVariables()` works inside su
b-comps loaded via `data-composition-src`. Ea
ch host element passes its own values:

```ht
ml
<div
  data-composition-id="card-pro"
  da
ta-composition-src="compositions/card.html"
 
 data-variable-values='{"title":"Pro","price"
:"$29"}'
></div>
<div
  data-composition-id="
card-enterprise"
  data-composition-src="comp
ositions/card.html"
  data-variable-values='{
"title":"Enterprise","price":"Custom"}'
></di
v>
```

The runtime layers each host's `data-
variable-values` over the sub-comp's declared
 defaults on a per-instance basis, so the sam
e source can be embedded multiple times with 
different content.

**Rules of thumb:**

- Al
ways provide a sensible `default` for every d
eclared variable. Dev preview uses defaults �
�� without them, the composition won't render
 correctly until `--variables` is provided.
-
 Read variables once at the top of the script
 (`const { title } = ...`), not inside frame 
loops or event handlers — `getVariables()` 
allocates a fresh object per call.
- Use `--s
trict-variables` in CI to fail fast on undecl
ared keys or type mismatches.
- Variable type
s are validated at render time. `string`, `nu
mber`, `boolean`, and `color` (hex string) ch
eck `typeof`; `enum` checks the value is in t
he declared `options`.

## Video and Audio

V
ideo must be `muted playsinline`. Audio is al
ways a separate `<audio>` element:

```html
<
video
  id="el-v"
  data-start="0"
  data-dur
ation="30"
  data-track-index="0"
  src="vide
o.mp4"
  muted
  playsinline
></video>
<audio

  id="el-a"
  data-start="0"
  data-duration
="30"
  data-track-index="2"
  src="video.mp4
"
  data-volume="1"
></audio>
```

## Timelin
e Contract

- All timelines start `{ paused: 
true }` — the player controls playback
- Re
gister every timeline: `window.__timelines["<
composition-id>"] = tl`
- Framework auto-nest
s sub-timelines — do NOT manually add them

- Duration comes from `data-duration`, not fr
om GSAP timeline length
- Never create empty 
tweens to set duration

## Rules (Non-Negotia
ble)

**Deterministic:** No `Math.random()`, 
`Date.now()`, or time-based logic. Use a seed
ed PRNG if you need pseudo-random values (e.g
. mulberry32).

**GSAP:** Only animate visual
 properties (`opacity`, `x`, `y`, `scale`, `r
otation`, `color`, `backgroundColor`, `border
Radius`, transforms). Do NOT animate `visibil
ity`, `display`, or call `video.play()`/`audi
o.play()`.

**Animation conflicts:** Never an
imate the same property on the same element f
rom multiple timelines simultaneously.

**No 
`repeat: -1`:** Infinite-repeat timelines bre
ak the capture engine. Calculate the exact re
peat count from composition duration: `repeat
: Math.ceil(duration / cycleDuration) - 1`.


**Synchronous timeline construction:** Never 
build timelines inside `async`/`await`, `setT
imeout`, or Promises. The capture engine read
s `window.__timelines` synchronously after pa
ge load. Fonts are embedded by the compiler, 
so they're available immediately — no need 
to wait for font loading.

**Never do:**

1. 
Forget `window.__timelines` registration
2. U
se video for audio — always muted video + s
eparate `<audio>`
3. Nest video inside a time
d div — use a non-timed wrapper
4. Use `dat
a-layer` (use `data-track-index`) or `data-en
d` (use `data-duration`)
5. Animate video ele
ment dimensions — animate a wrapper div
6. 
Call play/pause/seek on media — framework o
wns playback
7. Create a top-level container 
without `data-composition-id`
8. Use `repeat:
 -1` on any timeline or tween — always fini
te repeats
9. Build timelines asynchronously 
(inside `async`, `setTimeout`, `Promise`)
10.
 Use `gsap.set()` on clip elements from later
 scenes — they don't exist in the DOM at pa
ge load. Use `tl.set(selector, vars, timePosi
tion)` inside the timeline at or after the cl
ip's `data-start` time instead.
11. Use `<br>
` in content text — forced line breaks don'
t account for actual rendered font width. Tex
t that wraps naturally + a `<br>` produces an
 extra unwanted break, causing overlap. Let t
ext wrap via `max-width` instead. Exception: 
short display titles where each word is delib
erately on its own line (e.g., "THE\nIMMORTAL
\nGAME" at 130px).

## Scene Transitions (Non
-Negotiable)

Every multi-scene composition M
UST follow ALL of these rules. Violating any 
one of them is a broken composition.

1. **AL
WAYS use transitions between scenes.** No jum
p cuts. No exceptions.
2. **ALWAYS use entran
ce animations on every scene.** Every element
 animates IN via `gsap.from()`. No element ma
y appear fully-formed. If a scene has 5 eleme
nts, it needs 5 entrance tweens.
3. **NEVER u
se exit animations** except on the final scen
e. This means: NO `gsap.to()` that animates o
pacity to 0, y offscreen, scale to 0, or any 
other "out" animation before a transition fir
es. The transition IS the exit. The outgoing 
scene's content MUST be fully visible at the 
moment the transition starts.
4. **Final scen
e only:** The last scene may fade elements ou
t (e.g., fade to black). This is the ONLY sce
ne where `gsap.to(..., { opacity: 0 })` is al
lowed.

**WRONG — exit animation before tra
nsition:**

```js
// BANNED — this empties 
the scene before the transition can use it
tl
.to("#s1-title", { opacity: 0, y: -40, durati
on: 0.4 }, 6.5);
tl.to("#s1-subtitle", { opac
ity: 0, duration: 0.3 }, 6.7);
// transition 
fires on empty frame
```

**RIGHT — entranc
e only, transition handles exit:**

```js
// 
Scene 1 entrance animations
tl.from("#s1-titl
e", { y: 50, opacity: 0, duration: 0.7, ease:
 "power3.out" }, 0.3);
tl.from("#s1-subtitle"
, { y: 30, opacity: 0, duration: 0.5, ease: "
power2.out" }, 0.6);
// NO exit tweens — tr
ansition at 7.2s handles the scene change
// 
Scene 2 entrance animations
tl.from("#s2-head
ing", { x: -40, opacity: 0, duration: 0.6, ea
se: "expo.out" }, 8.0);
```

## Animation Gua
rdrails

- Offset first animation 0.1-0.3s (n
ot t=0)
- Vary eases across entrance tweens �
�� use at least 3 different eases per scene
-
 Don't repeat an entrance pattern within a sc
ene
- Avoid full-screen linear gradients on d
ark backgrounds (H.264 banding — use radial
 or solid + localized glow)
- 60px+ headlines
, 20px+ body, 16px+ data labels for rendered 
video
- `font-variant-numeric: tabular-nums` 
on number columns

If no `frame.md` or `desig
n.md` exists, follow [house-style.md](./house
-style.md) for aesthetic defaults.

## Typogr
aphy and Assets

- **Built-in fonts:** Write 
the `font-family` you want in CSS — the com
piler embeds supported fonts automatically.
-
 **Custom fonts:** If the spec (`frame.md` or
 `design.md`) names a font that isn't built-i
n, the user must provide `.woff2` files in a 
`fonts/` directory. If missing, warn before w
riting HTML. When files exist, add `@font-fac
e` declarations pointing to the local files.

- Add `crossorigin="anonymous"` to external m
edia
- For dynamic text overflow, use `window
.__hyperframes.fitTextFontSize(text, { maxWid
th, fontFamily, fontWeight })`
- All files li
ve at the project root alongside `index.html`
; sub-compositions use `../`

## Editing Exis
ting Compositions

- **Read actual files, don
't guess.** When editing, extending, or creat
ing companion compositions, read the existing
 source. Don't reconstruct hex codes from mem
ory. Don't guess GSAP easing patterns. The co
mposition IS the spec — extract exact value
s from it.
- Match existing fonts, colors, an
imation patterns from what you read
- Only ch
ange what was requested
- Preserve timing of 
unrelated clips

## Output Checklist

**Fast 
(run immediately, block on results):**

- [ ]
 `npx hyperframes lint` and `npx hyperframes 
validate` both pass
- [ ] Design adherence ve
rified if a design spec (`frame.md` or `desig
n.md`) exists

**Slow (run in parallel while 
presenting the preview to the user):**

- [ ]
 `npx hyperframes inspect` passes, or every r
eported overflow is intentionally marked
- [ 
] Contrast warnings addressed (see Quality Ch
ecks below)
- [ ] Animation choreography veri
fied (see Quality Checks below)

## Quality C
hecks

### Visual Inspect

`hyperframes inspe
ct` runs the composition in headless Chrome, 
seeks through the timeline, and maps visual l
ayout issues with timestamps, selectors, boun
ding boxes, and fix hints. Run it after `lint
` and `validate`:

```bash
npx hyperframes in
spect
npx hyperframes inspect --json
```

Fai
lures usually mean text is spilling out of a 
bubble/card, a fixed-size label is clipping d
ynamic copy, or text has moved off the canvas
. Fix by increasing container size or padding
, reducing font size or letter spacing, addin
g a real `max-width` so text wraps inside the
 container, or using `window.__hyperframes.fi
tTextFontSize(...)` for dynamic copy.

Use `-
-samples 15` for dense videos and `--at 1.5,4
,7.25` for specific hero frames. Repeated sta
tic issues are collapsed by default to avoid 
flooding agent context. If overflow is intent
ional for an entrance/exit animation, mark th
e element or ancestor with `data-layout-allow
-overflow`. If a decorative element should ne
ver be audited, mark it with `data-layout-ign
ore`.

`hyperframes layout` is the compatibil
ity alias for the same check.

### Contrast


`hyperframes validate` runs a WCAG contrast a
udit by default. It seeks to 5 timestamps, sc
reenshots the page, samples background pixels
 behind every text element, and computes cont
rast ratios. Failures appear as warnings:

``
`
⚠ WCAG AA contrast warnings (3):
  · .su
btitle "secondary text" — 2.67:1 (need 4.5:
1, t=5.3s)
```

If warnings appear:

- On dar
k backgrounds: brighten the failing color unt
il it clears 4.5:1 (normal text) or 3:1 (larg
e text, 24px+ or 19px+ bold)
- On light backg
rounds: darken it
- Stay within the palette f
amily — don't invent a new color, adjust th
e existing one
- Re-run `hyperframes validate
` until clean

Use `--no-contrast` to skip if
 iterating rapidly and you'll check later.

#
## Design Adherence

If a design spec (`frame
.md` or `design.md`) exists, verify the compo
sition follows it after authoring. Read the H
TML and check:

1. **Colors** — every hex v
alue in the composition appears in the spec's
 palette section (however the user labeled it
: Colors, Palette, Theme, etc.). Flag any inv
ented colors.
2. **Typography** — font fami
lies and weights match the spec's type spec. 
No substitutions.
3. **Corners** — border-r
adius values match the declared corner style,
 if specified.
4. **Spacing** — padding and
 gap values fall within the declared density 
range, if specified.
5. **Depth** — shadow 
usage matches the declared depth level, if sp
ecified (flat = none, subtle = light, layered
 = glows).
6. **Avoidance rules** — if the 
spec has a section listing things to avoid (c
ommonly "What NOT to Do", "Don'ts", "Anti-pat
terns", or "Do's and Don'ts"), verify none ar
e present.

Report violations as a checklist.
 Fix each one before serving.

If no design s
pec exists (house-style-only path), verify:


1. **Palette consistency** — the same bg, f
g, and accent colors are used across all scen
es. No per-scene color invention.
2. **No laz
y defaults** — check the composition agains
t house-style.md's "Lazy Defaults to Question
" list. If any appear, they must be a deliber
ate choice for the content, not a default.

#
## Animation Map

After authoring animations,
 run the animation map to verify choreography
:

```bash
node skills/hyperframes/scripts/an
imation-map.mjs <composition-dir> \
  --out <
composition-dir>/.hyperframes/anim-map
```

O
utputs a single `animation-map.json` with:

-
 **Per-tween summaries**: `"#card1 animates o
pacity+y over 0.50s. moves 23px up. fades in.
 ends at (120, 200)"`
- **ASCII timeline**: G
antt chart of all tweens across the compositi
on duration
- **Stagger detection**: reports 
actual intervals (`"3 elements stagger at 120
ms"`)
- **Dead zones**: periods over 1s with 
no animation — intentional hold or missing 
entrance?
- **Element lifecycles**: first/las
t animation time, final visibility
- **Scene 
snapshots**: visible element state at 5 key t
imestamps
- **Flags**: `offscreen`, `collisio
n`, `invisible`, `paced-fast` (under 0.2s), `
paced-slow` (over 2s)

Read the JSON. Scan su
mmaries for anything unexpected. Check every 
flag — fix or justify. Verify the timeline 
shows the intended choreography rhythm. Re-ru
n after fixes.

Skip on small edits (fixing a
 color, adjusting one duration). Run on new c
ompositions and significant animation changes
.

---

## References (loaded on demand)

- *
*[references/captions.md](references/captions
.md)** — Captions, subtitles, lyrics, karao
ke synced to audio. Tone-adaptive style detec
tion, per-word styling, text overflow prevent
ion, caption exit guarantees, word grouping. 
Read when adding any text synced to audio tim
ing.
- **[references/audio-reactive.md](refer
ences/audio-reactive.md)** — Audio-reactive
 animation: map frequency bands and amplitude
 to GSAP properties. Read when visuals should
 respond to music, voice, or sound.
- **[refe
rences/css-patterns.md](references/css-patter
ns.md)** — CSS+GSAP marker highlighting: hi
ghlight, circle, burst, scribble, sketchout. 
Deterministic, fully seekable. Read when addi
ng visual emphasis to text.
- **[references/v
ideo-composition.md](references/video-composi
tion.md)** — Video-medium rules: density, c
olor presence, scale, frame composition, the 
design spec as brand not layout. **Always rea
d** — these override web instincts.
- **[re
ferences/beat-direction.md](references/beat-d
irection.md)** — Beat planning: concept, mo
od, choreography verbs, rhythm templates, tra
nsition decisions, depth layers. **Always rea
d for multi-scene compositions.**
- **[refere
nces/typography.md](references/typography.md)
** — Typography: font pairing, OpenType fea
tures, dark-background adjustments, font disc
overy script. **Always read** — every compo
sition has text.
- **[references/motion-princ
iples.md](references/motion-principles.md)** 
— Motion design principles, image motion tr
eatment, load-bearing GSAP rules. **Always re
ad** — every composition has motion.
- **[r
eferences/techniques.md](references/technique
s.md)** — 13 primitive animation techniques
 with code patterns: SVG drawing, Canvas 2D, 
CSS 3D, kinetic type, Lottie, video compositi
ng, typing, variable fonts, MotionPath, veloc
ity transitions, audio-reactive, clip-path re
veals, WebGL shaders. Adapt the patterns — 
don't copy-paste. (For pre-built UI templates
 — terminal chrome, device mockups, moodboa
rd layouts — see `registry/blocks/`.)
- **[
references/html-in-canvas-patterns.md](refere
nces/html-in-canvas-patterns.md)** — HTML-i
n-Canvas patterns: live DOM as GPU texture vi
a `drawElementImage` + `layoutsubtree`. Share
d boilerplate + ~6 effect recipes (iPhone/Mac
Book mockups, liquid glass, magnetic, portal,
 shatter, text cursor). Use for 1–3 hero be
ats per video.
- **[references/narration.md](
references/narration.md)** — Pacing, tone, 
script structure, number pronunciation, openi
ng line patterns. Read when the composition i
ncludes voiceover or TTS.
- **[references/des
ign-picker.md](references/design-picker.md)**
 — Create a design.md via visual picker. Re
ad when no `frame.md` or `design.md` exists a
nd the user wants to create one.
- **[visual-
styles.md](visual-styles.md)** — 8 named vi
sual styles with hex palettes, GSAP easing si
gnatures, and shader pairings. Read when user
 names a style or when generating a design sp
ec.
- **[house-style.md](house-style.md)** �
� Default motion, sizing, and color palettes 
when no `frame.md` or `design.md` is specifie
d.
- **[patterns.md](patterns.md)** — PiP, 
title cards, slide show patterns.
- **[data-i
n-motion.md](data-in-motion.md)** — Data, s
tats, and infographic patterns.
- **[referenc
es/transcript-guide.md](references/transcript
-guide.md)** — Caption-side transcript hand
ling: input formats, mandatory quality check,
 cleaning JS, OpenAI/Groq API fallback, "if n
o transcript exists" flow. (For the `transcri
be` CLI invocation, model selection rules, an
d the `.en` gotcha, see the `hyperframes-medi
a` skill.)
- **[references/dynamic-techniques
.md](references/dynamic-techniques.md)** — 
Dynamic caption animation techniques (karaoke
, clip-path, slam, scatter, elastic, 3D).

- 
**[references/transitions.md](references/tran
sitions.md)** — Scene transitions: crossfad
es, wipes, reveals, shader transitions. Energ
y/mood selection, CSS vs WebGL guidance. **Al
ways read for multi-scene compositions** — 
scenes without transitions feel like jump cut
s.
  - [transitions/catalog.md](references/tr
ansitions/catalog.md) — Hard rules, scene t
emplate, and routing to per-type implementati
on code.
  - Shader transitions are in `@hype
rframes/shader-transitions` (`packages/shader
-transitions/`) — read package source, not 
skill files.

GSAP patterns and effects are i
n the `/gsap` skill.


