# Motion Principles

## Common defaults that 
produce monoculture

These are the patterns L
LMs reach for without thinking. None of them 
are wrong in isolation — they're wrong as d
efaults. If every scene of every video lands 
on the same easing, the same speed, and the s
ame entrance direction, the compositions blur
 into one another no matter what the brand is
.

- **Same ease on every tween.** `power2.ou
t` is the most common default. Aim for variet
y: no more than two independent tweens sharin
g an ease within a scene. Eases are like font
 weights — vary them deliberately.
- **Same
 speed on every tween.** 0.4–0.5s is a comm
on default that flattens rhythm. The slowest 
motion in a scene should be roughly 3× slowe
r than the fastest. Vary duration so the eye 
can tell what's important.
- **Same entrance 
direction.** `y: 30, opacity: 0` is the unive
rsal LLM entrance. The same scene can use ent
rances from left, from right, from scale, fro
m blur, opacity-only, letter-spacing — each
 one says something different about the eleme
nt.
- **Same stagger across scenes.** Each sc
ene should have its own rhythm. A 0.08s stagg
er in beat 1 and a 0.15s stagger in beat 2 ma
kes the two beats feel like different moments
.
- **Ambient zoom on every scene.** Slow-sca
le-up is the default ambient motion and it te
legraphs "LLM-generated video." Vary the ambi
ent motion per scene: slow pan, subtle rotati
on, color temperature shift, gentle drift —
 and sometimes nothing. Stillness after motio
n has real weight.
- **First animation at t=0
.** Zero-delay feels like a jump cut. Offset 
the opening 0.1–0.3s so the scene reads as 
composed rather than thrown together.

## Eas
ing is emotion, not technique

The motion is 
the verb. The easing is the adverb. A slide-i
n with `expo.out` feels confident. With `sine
.inOut`, dreamy. With `elastic.out`, playful.
 Same motion, three different meanings. Choos
e the adverb deliberately.

**Direction rules
:**

- `.out` for elements entering. Starts f
ast, decelerates. Feels responsive. This is t
he default for entrances.
- `.in` for element
s leaving. Starts slow, accelerates away. Sen
ds them off with momentum.
- `.inOut` for ele
ments moving between positions, neither enter
ing nor leaving the scene.

Ease-in on an ent
rance feels sluggish. Ease-out on an exit fee
ls reluctant. These are the most common rever
sals and they're worth checking your work aga
inst.

## Speed expresses weight

Duration is
 one of the most direct ways a composition co
mmunicates what it values. Faster motion read
s as confident, urgent, kinetic — it gives 
the viewer less time to study what's happenin
g, which means the work has to land in fewer 
frames. Slower motion reads as deliberate, co
nsidered, weighty — the viewer has time to 
take in the element, which means each element
 has to earn that attention.

Useful calibrat
ion ranges (not prescriptions — what a dura
tion _expresses_ depends on what surrounds it
):

- **0.15–0.3s** — quick, percussive, 
kinetic. The motion reads as something happen
ing _to_ the frame.
- **0.3–0.5s** — comf
ortable, professional. The motion reads as co
mposed and reliable.
- **0.5–0.8s** — del
iberate. The motion has visible weight and as
ks for attention.
- **0.8s+** — atmospheric
. The motion becomes part of what the scene _
is_, not something happening within it.

A co
mposition that uses only one of these ranges 
feels one-note. Mix them — a scene where th
e headline takes 0.7s to settle and the suppo
rting details land in 0.25s creates contrast 
that reinforces hierarchy without needing dif
ferent colors or sizes.

## Scene structure: 
build, breathe, resolve

Every scene has thre
e phases. The most common failure is dumping 
everything into the build and leaving nothing
 for the other two.

- **Build (0–30%)** �
� elements enter, staggered. Not all at once.

- **Breathe (30–70%)** — content visible
, alive with one ambient motion. The viewer r
eads, registers, settles.
- **Resolve (70–1
00%)** — exit or decisive end. Exits are fa
ster than entrances (see Asymmetry below).

A
 scene that's all build feels like a slidesho
w. A scene with no breathe phase doesn't let 
the content land.

## Transitions carry meani
ng

The transition type tells the viewer how 
two scenes relate:

- **Crossfade** — "this
 continues." Connective tissue between relate
d ideas.
- **Hard cut** — "wake up" or a re
gister shift. Disruption, surprise, percussiv
e emphasis.
- **Slow dissolve** — "drift wi
th me." Atmospheric, meditative, between-thou
ghts.

Crossfade is the default and it's defe
nsible most of the time. The thing to watch f
or is using it for everything — when every 
transition is a crossfade, the viewer stops r
egistering scene changes as meaningful. Hard 
cuts and slow dissolves are tools for the mom
ents where the change in scene _is_ the messa
ge.

## Choreography is hierarchy

The elemen
t that moves first is perceived as most impor
tant. Stagger in order of importance, not DOM
 order. Don't wait for one entrance to comple
te before starting the next — overlap entri
es. Total stagger sequence under 500ms regard
less of item count keeps the scene from feeli
ng like a slow drip.

## Asymmetry between en
trances and exits

Entrances need longer than
 exits. A card might take 0.4s to appear but 
0.25s to disappear — entrances build presen
ce, exits remove it, and remove takes less ti
me than build.

## Visual composition

Video 
frames are not web pages. Web layout patterns
 that work on a scrollable page often look br
oken in a fixed-frame composition.

- **Two f
ocal points minimum per scene.** The eye need
s somewhere to travel. A single text block fl
oating in empty space reads as unfinished.
- 
**Fill the frame.** Hero text typically wants
 60–80% of frame width. Web type sizes — 
16px body, 32px headlines — disappear at vi
deo distance.
- **Three layers minimum.** Bac
kground treatment (glow, oversized faded type
, color panel), foreground content, accent el
ements (dividers, labels, data bars). A scene
 with only one layer reads flat.
- **Backgrou
nd is not empty.** Radial glows, oversized fa
ded type bleeding off-frame, subtle border pa
nels, hairline rules. Pure solid `#000` reads
 as "nothing loaded."
- **Anchor to edges.** 
Pin content to left/top or right/bottom. Cent
ered-and-floating is a web pattern that looks
 lost on a 16:9 canvas.
- **Split frames.** D
ata panel on the left, content on the right. 
Top bar with metadata, full-width below. Zone
-based layouts beat centered stacks.
- **Use 
structural elements.** Rules, dividers, borde
r panels. They create paths for the eye and a
nimate well (`scaleX` from 0).

## Image moti
on treatment

Embedded images shouldn't sit f
lat — every image earns some motion treatme
nt:

- **Perspective tilt** — `gsap.set(el,
 { transformPerspective: 1200, rotationY: -8 
})` plus a `box-shadow` creates depth. Do NOT
 use CSS `transform: perspective(...)`; GSAP 
will overwrite it.
- **Slow zoom (Ken Burns)*
* — GSAP `scale: 1` → `1.04` over beat du
ration. Makes photos feel cinematic rather th
an pasted in.
- **Device frame** — wrap in 
a laptop or phone shape using `border-radius`
 and `box-shadow`.
- **Floating UI** — extr
act a key element and animate it at a differe
nt z-depth for parallax.
- **Scroll reveal** 
— clip the image to a viewport window and a
nimate `y` position.

## Load-Bearing GSAP Ru
les

Rules below came out of two independent 
website-to-hyperframes builds (2026-04-20) wh
ere compositions lint-clean and still ship br
oken — elements that never appear, ambient 
motion that doesn't scrub, entrance tweens th
at silently kill their target. The linter can
not catch these; the rules must be followed b
y the author.

- **No iframes for captured co
ntent.** Iframes do not seek deterministicall
y with the timeline — the capture engine ca
nnot scrub inside them, so they appear frozen
 (or blank) in the rendered output. If the so
urce you're stylizing is a live web app, use 
the screenshots from `capture/` as stacked pa
nels or layered images, not live embeds.

- *
*Never stack two transform tweens on the same
 element.** A common failure: a `y` entrance 
plus a `scale` Ken Burns on the same `<img>`.
 The second tween's `immediateRender: true` w
rites the element's initial state at construc
tion time, overwriting whatever the first twe
en set — leaving the element invisible or o
ffscreen with no lint warning. A secondary me
chanism: `tl.from()` resets to its declared "
from" state when the playhead is seeked past 
the timeline's end, so an element that looked
 correct in linear playback vanishes in the c
apture engine's non-linear seek. Fix one of t
wo ways:

  ```html
  <!-- BAD: two transform
s on one element -->
  <img class="hero" src=
"..." />
  <script>
    tl.from(".hero", { y:
 50, opacity: 0, duration: 0.6 }, 0);
    tl.
to(".hero", { scale: 1.04, duration: beat }, 
0); // kills the entrance
  </script>

  <!--
 GOOD option A: combine into one tween -->
  
<script>
    tl.fromTo(
      ".hero",
      
{ y: 50, opacity: 0, scale: 1.0 },
      { y:
 0, opacity: 1, scale: 1.04, duration: beat, 
ease: "none" },
      0,
    );
  </script>


  <!-- GOOD option B: split across parent + c
hild -->
  <div class="hero-wrap"><img class=
"hero" src="..." /></div>
  <script>
    tl.f
rom(".hero-wrap", { y: 50, opacity: 0, durati
on: 0.6 }, 0); // entrance on parent
    tl.t
o(".hero", { scale: 1.04, duration: beat }, 0
); // Ken Burns on child
  </script>
  ```

-
 **Prefer `tl.fromTo()` over `tl.from()` insi
de `.clip` scenes.** `gsap.from()` sets `imme
diateRender: true` by default, which writes t
he "from" state at timeline construction — 
before the `.clip` scene's `data-start` is ac
tive. Elements can flash visible, start from 
the wrong position, or skip their entrance en
tirely when the scene is seeked non-linearly 
(which the capture engine does). Explicit `fr
omTo` makes the state at every timeline posit
ion deterministic:

  ```js
  // BRITTLE: imm
ediateRender interacts badly with scene bound
aries
  tl.from(el, { opacity: 0, y: 50, dura
tion: 0.6 }, t);

  // DETERMINISTIC: state i
s defined at both ends, no immediateRender su
rprise
  tl.fromTo(el, { opacity: 0, y: 50 },
 { opacity: 1, y: 0, duration: 0.6 }, t);
  `
``

- **Ambient pulses must attach to the see
kable `tl`, never bare `gsap.to()`.** Auras, 
shimmers, gentle float loops, logo breathing 
— all of these must be added to the scene's
 timeline, not fired standalone. Standalone t
weens run on wallclock time and do not scrub 
with the capture engine, so the effect is abs
ent in the rendered video even though it look
s correct in the studio preview:

  ```js
  /
/ BAD: lives outside the timeline, never rend
ers in capture
  gsap.to(".aura", { scale: 1.
08, yoyo: true, repeat: 5, duration: 1.2 });


  // GOOD: seekable, deterministic, renders

  tl.to(".aura", { scale: 1.08, yoyo: true, r
epeat: 5, duration: 1.2 }, 0);
  ```

- **Har
d-kill every scene boundary, not just caption
s.** The same hard-kill pattern from `caption
s.md` generalizes to all elements with exit a
nimations: any element whose visibility chang
es at a beat boundary needs a deterministic `
tl.set()` kill after its fade, because later 
tweens on the same element (or `immediateRend
er` from a sibling tween) can resurrect it. A
pply to every element with an exit animation:


  ```js
  tl.to(el, { opacity: 0, duration:
 0.3 }, beatEnd);
  tl.set(el, { opacity: 0, 
visibility: "hidden" }, beatEnd + 0.3); // de
terministic kill
  ```

These are the exact r
ules with the exact code examples — don't s
ummarize or shorten them. They exist because 
compositions that lint clean still ship broke
n without them.


