# Visual Techniques Reference

13 primitive animation techniques from production HyperFrames videos — SVG drawing, kinetic typography, variable fonts, WebGL shaders, motion-path, etc. Compose these into beats; they are the building blocks, not finished recipes. Each entry includes a minimal code pattern you can adapt.

These are NOT advanced — they're standard motion design patterns that every composition should use at least 2-3 of. For pre-built UI templates (terminal chrome, device mockups, moodboard layouts), look in the `registry/blocks/` directory instead — those are recipes, not techniques.

**These are starting points, not copy-paste templates.** Every code pattern below is a minimal working example from a real production video. Adapt them toyour needs — change colors, sizes, timings, easings, element counts, layout. Combine techniques, mix parts from different patterns, invent variations. The goal is to understand the PRINCIPLE behind each technique so you can build something original, not to reproduce these examples exactly.

## Table of Contents


**Named text animation effects**(per-character, per-word, per-line, whole-element) — 24 effects with exact GSAP specs come from the separate `pixel-point/animate-text` skill. See [`text-effects.md`](text-effects.md) for the effect-name vocabulary and instructions for loading the upstream skill. Use those for all headline and label animations instead of inventing timing from scratch.

**HTML-in-Canvas patterns** (live DOM as GPU texture: iPhone/MacBook mockups, liquid glass, magnetic, portal, shatter, text cursor — using `drawElementImage` + `layoutsubtree`) are in [`html- in-canvas-patterns.md`](html-in-canvas-patterns.md) — 504 lines, one shared boilerplate
+ ~6 effect recipes. Use for 1–3 hero beatsper video, not every beat.

---

| # | Tec
hnique | What it does

 | Best for
 |
| --- | -------------
-------------------- | ----------------------
---------------------------------------------
------- | -----------------------------------
----------- |
| 1 | **SVG Path Drawing**
 | Logos/icons draw themselves stro
ke by stroke |
Logo reveals, diagram builds, connector lines
 |
| 2 | **Canvas 2D Procedural Art**
 | Animated noise, particles, data viz — fr
ame-by-frame via GSAP proxy | Generati
ve backgrounds, ambient texture |
| 3
 | **CSS 3D Transforms** | Card
flips, perspective grids, folding panels
 | Product reveals, c
omparison scenes |
| 4 | **Per-
Word Kinetic Typography** | Text animates w
ord-by-word with stagger timing
 | Thesis statements, key messa
ges, quotes |
| 5 | **Lottie Animati
on** | Captured or external Lott
ie plays as overlay/background
 | Brand animations, micro-interactions
 |
| 6 | **Video Compositing**
 | Product videos play inline, masked,
 overlaid | Dem
o footage, screen recordings |

| 7 | **Character-by-Character Typing**|
Terminal-style code reveals, search bar inter
actions | Developer too
ls, CLI demos |
| 8 | *
*Variable Font Axis Animation** | Weight, wi
dth, slant, optical size morph over time
 | Premium typography, bra
nd wordmarks |
| 9 | **GSAP Moti
onPathPlugin** | Elements follow SVG
curves, orbital motion, spirals
 | Dynamic entrances, connector anim
ations |
| 10 | **Velocity-Matched Tr
ansitions** | Outgoing blur/translate matche
s incoming for seamless cuts
| Beat transitions, scene changes
 |
| 11 | **Audio-Reactive Animation**
 | Elements pulse to narration frequency ba
nds | Backgrou
nd textures, text glow, ambient motion |
| 12
 | **Clip-Path Reveal Masks** | Fixed
 window that content slides through (text/ima
ges enter from one side) | Headline intros, i
mage reveals, wipe effects |
| 13 | **WebG
L Fragment Shader Art** | Full GPU genera
tive backgrounds — FBM domain warp, cosine
palettes | Hero backgrounds, atmosphe
ric scenes |

---

## 1. SVG Path Drawing

A path draws itself in real-time, like someone tracing with a pen. Use for revealing diagrams, arrows, connector lines, or brand marks.

```html
<svg viewBox="0 0 400 200">

 <path
 class="draw-path"
 d="M 50 10
0 L 200 50 L 350 100"
 stroke="#c84f1c"

 stroke-width="4"
 fill="none"
 stroke
-linecap="round"
 />
</svg>
<style>
 .draw-
path {
 stroke-dasharray: 280;
 stroke-
dashoffset: 280;
 }
</style>
<script>
 tl.t
o(".draw-path", { strokeDashoffset: 0, durati
on: 0.7, ease: "power2.out" }, 0.5);
</script
>
```

Use `path.getTotalLength()` to calculate the dasharray value dynamically.

---

##
2. Canvas 2D Procedural Art

Animated noise,
particle fields, data visualizations — anyt
hing that evolves frame-by-frame. Drive it wi
th a GSAP proxy.

```html
<canvas id="proc-ca
nvas" width="1920" height="1080"></canvas>
<s
cript>
 var canvas = document.getElementById
("proc-canvas");
 var ctx = canvas.getContex
t("2d");

 function hash(x, y) {
 var n =
 x * 374761393 + y * 668265263;
 n = (n ^
(n >> 13)) * 1274126177;
 return ((n ^ (n
>> 16)) & 0x7fffffff) / 0x7fffffff;
 }

 fu
nction drawFrame(t) {
 ctx.fillStyle = "#0
a0a0a";
 ctx.fillRect(0, 0, 1920, 1080);

 for (var i = 0; i < 200; i++) {
 var
x = hash(i, 0) * 1920;
 var y = hash(i,
1) * 1080;
 var brightness = hash(i, Mat
h.floor(t * 10)) * 255;
 ctx.fillStyle =
 "rgba(255, 255, 255, " + brightness / 255 +
")";
 ctx.beginPath();
 ctx.arc(x,
y, 2, 0, Math.PI * 2);
 ctx.fill();

}
 }

 var proxy = { time: 0 };
 tl.to(

 proxy,
 {
 time: 5,
 duration:
 5,
 ease: "none",
 onUpdate: funct
ion () {
 drawFrame(proxy.time);

 },
 },
 0,
 );
</script>
```

The `ha
sh()` function is deterministic — same fram
e renders identically every time.

---

## 3.CSS 3D Transforms

Perspective rotations create depth. Use for product showcases, card flips, architectural reveals.

```html
<div cla
ss="stage" style="perspective: 900px;">
 <di
v class="card-3d" style="transform-style: pre
serve-3d;">
 <div class="face front">Produ
ct</div>
 <div class="face back" style="tr
ansform: rotateY(180deg);">Details</div>
 </
div>
</div>
<script>
 tl.to(".card-3d", { ro
tationY: 360, rotationX: 15, duration: 1.2, e
ase: "sine.inOut" }, 0);
</script>
```

Always set `perspective` on the parent, `transform -style: preserve-3d` on the animated element.


---

## 4. Per-Word Kinetic Typography

Wor
ds appear one-by-one, synced to transcript.js
on timestamps. The core technique for narrati
on-driven videos.

```html
<div class="headli
ne">
 <span class="word w-0">Anything</span>

 <span class="word w-1">a</span>
 <span cl
ass="word w-2">browser</span>
 <span class="
word w-3">can</span>
 <span class="word w-4"
>render</span>
</div>
<style>
 .word {
 d
isplay: inline-block;
 opacity: 0;
 mar
gin: 0 0.12em;
 }
</style>
<script>
 // Wor
d onset times from transcript.json (seconds r
elative to beat start)
 var timings = [0.0,
0.23, 0.28, 0.63, 0.78];
 var slides = [80,
60, 50, 25, 12]; // horizontal slide decay (p
x)

 document.querySelectorAll(".word").forE
ach(function (word, i) {
 tl.from(
 w
ord,
 {
 x: slides[i],
 y:
 14,
 opacity: 0,
 duration: 0.
35,
 ease: "power2.out",
 },

 timings[i],
 );
 });
</script>
```

The
 slide distance DECAYS per word (80→12px) �
�� mimics a camera settling.

---

## 5. Lottie Animation

Vector animations that play inside a composition. Use for logos, character animations, icons.

```html
<div id="anim" cla
ss="lottie"></div>
<script src="https://cdnjs
.cloudflare.com/ajax/libs/bodymovin/5.12.2/lo
ttie.min.js"></script>
<script>
 window.__hf
Lottie = window.__hfLottie || [];

 const an
im = lottie.loadAnimation({
 container: do
cument.getElementById("anim"),
 renderer:
"svg",
 loop: false,
 autoplay: false,

 path: "capture/assets/lottie/animation-0.
json",
 });
 window.__hfLottie.push(anim);


 gsap.set("#anim", { scale: 0.3, opacity: 0
 });
 tl.to("#anim", { scale: 1, opacity: 1,
 duration: 0.35, ease: "back.out(1.6)" }, 0.2
);
</script>
```

---

## 6. Video Compositin
g

Embed real video footage inside compositio
ns. Videos must be `muted` with `playsinline`
.

```html
<div class="video-frame" style="wi
dth:680px;height:840px;border-radius:16px;ove
rflow:hidden;">
 <video
 id="footage"

 src="capture/assets/videos/clip.mp4"
 mut
ed
 playsinline
 style="width:100%;heig
ht:100%;object-fit:cover;"
 ></video>
</div>

<script>
 // Video playback is controlled b
y the framework — don't call play() manuall
y
 tl.from(".video-frame", { scale: 0.9, opa
city: 0, duration: 0.3, ease: "power2.out" },
 0);
</script>
```

The HyperFrames runtime h
andles video seeking and playback.

---

## 7. Character-by-Character Typing

Terminal typing effect using `tl.call()` to update text content character by character.

```html
<div
class="terminal-line">
 <span class="prompt"
>❯</span>
 <span class="typed" id="typed-t
ext"></span>
 <span class="cursor" style="wi
dth:11px;height:22px;background:#333;display:
inline-block;"></span>
</div>
<script>
 var
CMD = "npx hyperframes init";
 var typed = d
ocument.getElementById("typed-text");

 // C
ursor blinks
 tl.to(".cursor", { opacity: 0,
 duration: 0.12, yoyo: true, repeat: 20, ease
: "steps(1)" }, 0);

 // Type each character

 for (var i = 0; i < CMD.length; i++) {

 (function (idx) {
 tl.call(
 fun
ction () {
 typed.textContent = CMD.
substring(0, idx + 1);
 },
 nul
l,
 (idx / CMD.length) * 0.9,
 );

 })(i);
 }
</script>
```

Use `ease: "steps(1)"` for cursor blink — creates discrete on/off.

---

## 8. Variable Font Axis Anim
ation

Animate font-variation-settings to res
hape glyphs in real-time. Works with variable
 fonts that have axes like optical size (opsz
), weight (wght), softness (SOFT).

```html
<
style>
 /* Load the captured local variable
font — do NOT use Google Fonts @import.

 Replace this placeholder with an @font-face
 pointing to capture/assets/fonts/. */
 @fon
t-face {
 font-family: "Fraunces";
 src
: url("capture/assets/fonts/Fraunces-Variable
.woff2") format("woff2");
 font-weight: 10
0 900;
 font-style: normal;
 font-displ
ay: block;
 }
 .wordmark {
 --opsz: 144;

 --wght: 440;
 font-family: "Fraunces"
, serif;
 font-variation-settings:
 "
opsz" var(--opsz),
 "wght" var(--wght);

 font-size: 200px;
 }
</style>
<script>

 tl.to(".wordmark", { "--opsz": 72, "--wght":
 300, duration: 0.45, ease: "power2.out" }, 0
);
</script>
```

The glyph subtly reshapes a
s axes animate — optical size adjusts detai
l, weight changes thickness.

---

## 9. GSAPMotionPathPlugin

Animate an element along an arbitrary SVG path. Use for sliders following curves, particles along trajectories, guided reveals.

```html
<script src="https://cdn
.jsdelivr.net/npm/gsap@3.14.2/dist/MotionPath
Plugin.min.js"></script>
<div class="dot" sty
le="width:20px;height:20px;background:#2a8a7c
;border-radius:50%;"></div>
<script>
 gsap.r
egisterPlugin(MotionPathPlugin);
 tl.to(

 ".dot",
 {
 motionPath: { path: "M 1
2 300 C 280 280 520 80 820 50 S 1200 48 1308
38" },
 duration: 1.5,
 ease: "powe
r2.out",
 },
 0,
 );
</script>
```

-- -

## 10. Velocity-Matched Transitions

Exit one beat and enter the next with matched velocities — creates perceived continuous motion.

```javascript
// EXIT (in outgoing compos
ition): accelerating with blur
tl.to(
 ".con
tent",
 {
 y: -150,
 filter: "blur(30p
x)",
 opacity: 0,
 duration: 0.33,

ease: "power2.in", // accelerates
 },
 pars
eFloat(root.dataset.duration) - 0.33, // star
t exit 0.33s before beat ends
);

// ENTRY (i
n incoming composition): decelerating from bl
ur
gsap.set(".content", { y: 150, filter: "bl
ur(30px)" });
tl.to(
 ".content",
 {
 y:
 0,
 filter: "blur(0px)",
 duration: 1.
0,
 ease: "power2.out", // decelerates
 }
,
 0,
);
```

The fastest point of both curves meets at the cut — the viewer perceives smooth camera motion. Match ease families: `. in` for exits, `.out` for entries.

---

## 1
1. Audio-Reactive Animation

Drive any GSAP-t
weenable property from the playing audio. Bas
s pulses a logo on kick drums. Treble glows a
 CTA on cymbals. Amplitude breathes a backgro
und during quiet phrases. The result: motion
that feels locked to the track in a way pre-a
uthored tweens never can.

**When to use:** A
ny video with music or dramatic narration —
 brand reels, product launches, hype edits. S
kip for calm/tutorial pacing.

**How it works
:**Pre-extract audio frequency bands into a
JSON file, then sample per-frame via `tl.call
()`:

```js
// audio-data.json: { fps: 30, to
talFrames: 900, frames: [{ bands: [0.82, 0.45
, 0.31,...] },...] }
for (var f = 0; f < AU
DIO_DATA.totalFrames; f++) {
 tl.call(
 (
function (frame) {
 return function () {

 var bass = frame.bands[0]; // 0–1

 var treble = frame.bands[13];

 gsap.set(".logo", { scale: 1 + bass * 0.04 }
); // 3–4% pulse on bass
 gsap.set("
.cta", { filter: `drop-shadow(0 0 ${treble *
24}px #00C3FF)` });
 };
 })(AUDIO_DAT
A.frames[f]),
 [],
 f / AUDIO_DATA.fps,

 );
}
```

Per-frame sampling is required �
�� a single tween will not react. Use the ext
ract script:

```bash
python3 skills/gsap/scr
ipts/extract-audio-data.py narration.wav --fp
s 30 --bands 16 -o audio-data.json
```

Keep
text/logo intensity subtle (≤5% scale, ≤3
0% glow) — audio-reactive motion on tiny el
ements reads as jitter. Bigger backgrounds ca
n push to 10–30%.

**Never do:** equalizer
bars, spectrum analyzers, waveform displays,
strobing, rainbow color cycling. The audio pr
ovides _timing and intensity_; the visual voc
abulary still comes from the brand. See `skil
ls/hyperframes/references/audio-reactive.md`
for the full API and anti-patterns.

---

##
12. Clip-Path Reveal Masks

A fixed window that content slides through — text or images enter from one side and are clipped by an invisible boundary. Different from SVG path drawing: the mask is static, the content moves.


```html
<div id="reveal-mask">
 <div id="rev
eal-content">Your headline text here</div>
</
div>
<style>
 #reveal-mask {
 position: a
bsolute;
 inset: 0;
 clip-path: inset(0
 200px 0 0); /* clips 200px from right */

 display: flex;
 align-items: center;

justify-content: center;
 }
 #reveal-conten
t {
 font-size: 108px;
 white-space: no
wrap;
 }
</style>
<script>
 // Content star
ts offscreen right, slides left through the m
ask window
 gsap.set("#reveal-content", { x:
 400, opacity: 0 });
 tl.to("#reveal-content
", { x: 0, opacity: 1, duration: 1, ease: "po
wer2.out" }, 0);
</script>
```

Variations: ` clip-path: circle(0% at 50% 50%)` → `circle (100%)` for iris reveals. `clip-path: polygon (...)` for custom shapes.

---

## 13. WebGL
Fragment Shader Art

Full GPU generative back
grounds — domain-warped FBM noise, cosine p
alette coloring, iridescent organic patterns.
 Far richer than Canvas 2D.

```html
<canvas
id="shader-bg" width="1920" height="1080"></c
anvas>
<script>
 var canvas = document.getEl
ementById("shader-bg");
 var gl = canvas.get
Context("webgl");
 if (!gl) {
 /* fallbac
k to gradient */
 }

 var fsrc = `
 prec
ision mediump float;
 varying vec2 v_uv;

 uniform float u_time;
 uniform vec2 u_r
es;

 float hash(vec2 p) { return fract(si
n(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}
 float noise(vec2 p) {
 vec2 i = fl
oor(p), f = fract(p);
 f = f * f * (3.0
- 2.0 * f);
 return mix(mix(hash(i), has
h(i+vec2(1, 0)), f.x),
 mix(ha
sh(i+vec2(0, 1)), hash(i+vec2(1, 1)), f.x), f.y
);
 }
 float fbm(vec2 p) {
 float
v = 0.0, a = 0.5;
 mat2 R = mat2(0.8, 0.
6, -0.6, 0.8);
 for (int i = 0; i < 5; i
++) { v += a*noise(p); p = R*p*2.02; a *= 0.5
; }
 return v;
 }
 vec3 palette(fl
oat t) {
 return vec3(0.5)+vec3(0.5)*cos
(6.28318*(vec3(1)*t+vec3(0.0, 0.33, 0.67)));

 }
 void main() {
 vec2 uv = v_uv; u
v.x *= u_res.x/u_res.y;
 float t = u_tim
e * 0.4;
 vec2 q = vec2(fbm(uv*3.0+t*0.3
), fbm(uv*3.0+vec2(5.2, 1.3)+t*0.2));
 ve
c2 r = vec2(fbm(uv*3.0+q*4.0+vec2(1.7, 9.2)+t*
0.15), fbm(uv*3.0+q*4.0+vec2(8.3, 2.8)+t*0.1))
;
 float n = fbm(uv*3.0+r*2.0);
 ve
c3 col = palette(n*2.0+t*0.2);
 col = mi
x(col, palette(length(q)*3.0+t*0.1), 0.4);

 col *= 0.7+0.3*n;
 float vig = 1.0-0
.4*length(v_uv-0.5);
 gl_FragColor = vec
4(col*vig, 1.0);
 }
 `;

 // Compile, li
nk, set up fullscreen quad, then render via G
SAP proxy:
 var proxy = { time: 0.5 };
 tl.
to(
 proxy,
 {
 time: 5,
 dur
ation: BEAT_DUR,
 ease: "none",
 on
Update: function () {
 gl.uniform1f(uT
ime, proxy.time);
 gl.drawArrays(gl.TR
IANGLE_STRIP, 0, 4);
 },
 },
 0,

 );
</script>
```

Always include a Canvas 2D
 gradient fallback for environments without W
ebGL.

---

## Easing Vocabulary

GSAP offers a deep easing library. Every composition should use at least 3 different easings — using `power2.out` for everything produces flat, monotonous motion. Think of easings as tone of voice: a video that only whispers is boring ; one that varies between whisper, normal, and punch is engaging.

**The full palette**(each family has `.in`, `.out`, `.inOut` variants):

| Family | Character

 | Typical use

 | | ------------ -------- | ---------------------------------- ------------------------------------------ | --------------------------------------------- --------------------------------------------- -------- |
| `power1`–`power4` | Gentle
(1) to aggressive (4) acceleration curves | General purpose. power2 is the workhorse, power4 for dramatic snaps | | `back (N)` | Overshoot then settle. N controls how far past the target (1=subtle, 4=wild) | Logo reveals, badge pops, card entrances. `back.out(2.5)` for playful, `back.out(1. 2)` for elegant |
| `elastic(amp, freq)` | Sp
ring bounce. amp=magnitude, freq=oscillation speed | Panel scatter, energetic drops, fun reveals | | `bounce` | Ball-drop bouncing

 | Physical interactions, icons landing, score counters | | `expo` | Extreme acceleration curve (much steeper than power4) | Premium/ luxury reveals, dramatic entrances

 |
| `sine` | Smooth, organic,
no hard edges | Ambient float, breathing, Ken Burns, anything that loops. `.inOut` for yoyo motion | | `circ` | Circular acceleration (starts very fast, ends very gentle or vice versa) | Camera moves, scene transitions, orbital motion

 |
| `steps(N)` | Discrete N-s
tep jumps, no interpolation | Typing effects, cursor blink, counter ticks, retro/digital aesthetics |

**Mood mapping:** Match easing character to the beat's emotional content. Smooth/organic easings (`sine`, `power1`) feel contemplative and drifting. Aggressive deceleration (`power4.out`, `expo.out`) feels snappy and confident. Spring overshoot (`back.out`) feels bouncy and physical. The storyboard's mood description should guide which character fits — not a formula.


---

## Choosing techniques

Don't match te
chniques to video type on autopilot — match
 them to the**concept of the specific beat**
. Ask: what visual treatment makes this exact
 idea land? A beat about speed needs motion t
hat communicates speed; a beat about precisio
n needs geometry and structure; a beat about
warmth needs texture and organic drift.

Read
 the storyboard beat's concept and mood, then
 scan this list for techniques whose _visual
character_ serves that concept. Any technique
 can appear in any video type — the questio
n is whether it earns its place in this beat.



