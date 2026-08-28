# Scene Transitions

A transition tells the v
iewer how two scenes relate. A crossfade says
 "this continues." A push slide says "next po
int." A blur crossfade says "drift with me." 
Choose transitions that match what the conten
t is doing emotionally, not just technically.


## Animation Rules for Multi-Scene Composit
ions

These are non-negotiable for every mult
i-scene composition:

1. **Every composition 
uses transitions.** No exceptions. Scenes wit
hout transitions feel like jump cuts.
2. **Ev
ery scene uses entrance animations.** Element
s animate IN via `gsap.from()` — opacity, p
osition, scale, etc. No scene should pop full
y-formed onto screen.
3. **Exit animations ar
e BANNED** except on the final scene. Do NOT 
use `gsap.to()` to animate elements out befor
e a transition fires. The transition IS the e
xit. Outgoing scene content must be fully vis
ible when the transition starts — the trans
ition handles the visual handoff.
4. **Final 
scene exception:** The last scene MAY fade el
ements out (e.g., fade to black at the end of
 the composition). This is the only scene whe
re exit animations are allowed.

## Energy �
� Transition Character

The energy of a beat 
tells you what motion character the transitio
n should have — not which specific transiti
on to use. The motion character is a quality 
you derive from the brand and content, then f
ind a transition that has that quality.

**So
ft/organic character:** transitions that brea
the, dissolve, or drift. Nothing sharp, mecha
nical, or percussive. Duration 0.5–0.8s, sm
ooth easing curves.

**Directional/purposeful
 character:** transitions that move content d
ecisively. Clear direction, readable momentum
. Duration 0.3–0.5s, clean deceleration.

*
*Percussive/instant character:** transitions 
that hit like a cut. Immediate, almost hard-c
ut energy. Duration 0.15–0.3s, aggressive o
r near-instant easing.

These are calibration
 ranges, not recipes. A brand that treats its
 "high energy" section with restraint might u
se 0.4s for a moment that another brand trans
itions in 0.2s — both are correct for their
 brand. Pick ONE character that defines the v
ideo's primary transitions, then use 1–2 co
ntrasting moments as intentional accents. See
 the **Mood → Motion Quality** section belo
w to find transitions with the right characte
r for a given mood.

## Mood → Motion Quali
ty

Think about what the transition _communic
ates_, not what it looks like. The question i
s: **what motion quality serves this mood?** 
Then find transitions that have that quality 
in the catalog (`transitions/catalog.md`).

|
 Mood                     | Motion quality th
at fits                                      
                              | Why          
                                             
                          |
| ---------------
--------- | ---------------------------------
---------------------------------------------
------------- | -----------------------------
---------------------------------------------
--------- |
| **Warm / inviting**      | Soft
 edges, dissolving, color-temperature washes 
— nothing sharp, mechanical, or percussive 
| Warmth reads as continuity and flow; hard c
uts or compression feel cold             |
| 
**Cold / clinical**      | Mechanical transfo
rmation — compression, slicing, gridding, p
recision                       | The content 
appears to be processed or structured, reinfo
rcing a systematic quality |
| **Editorial / 
magazine** | Clean directional movement — l
ike turning a page                           
                 | Feels like content is bein
g browsed or curated, not revealed           
             |
| **Tech / futuristic**    | D
ata-like fragmentation, digital displacement,
 scan artifacts                              
 | Transition feels computational rather than
 physical                                 |
|
 **Tense / edgy**         | Instability, dist
ortion, displacement — something slightly w
rong about the image            | Introduces 
friction where smooth transitions would relea
se tension                  |
| **Playful / f
un**        | Overshoot, expansion, rotation 
— motion with personality and bounce       
                  | Transitions that feel lik
e objects rather than effects                
              |
| **Dramatic / cinematic** | 
Scale, weight, light extremes — the cut is 
an event, not a bridge                       
    | Every shader and every hard cut carries
 narrative gravity                           
|
| **Premium / luxury**     | Restraint — 
transitions that are barely visible, or invis
ible                               | Luxury c
ommunicates through what it withholds        
                               |
| **Retro / 
analog**       | Organic imperfection — lig
ht bleed, scan lines, color wash             
                     | Physical film artifact
s; imperfection as authenticity              
                 |

Use this table to derive 
what **quality** the transition should have, 
then look at the specific options in `transit
ions/catalog.md` to find one that has that qu
ality for this brand. The transitions listed 
in the catalog are all available; none are re
served for a specific mood.

## Narrative Pos
ition

Each position in the video has a diffe
rent job to do. What transition you pick for 
each should come from the brand's motion char
acter and the storyboard's intent — not fro
m a rule about "climax = boldest."

- **Openi
ng** — establishes the motion language for 
the entire video. Make a deliberate choice; w
hatever you pick here sets the viewer's expec
tation for everything that follows.
- **Betwe
en related points** — should be almost invi
sible. The content is continuing; the transit
ion shouldn't draw attention to itself. Consi
stency matters more than distinctiveness here
.
- **Topic change** — needs enough contras
t from your primary that it signals "somethin
g different is starting." The contrast is in 
motion character, not just duration.
- **Clim
ax / hero reveal** — this is the moment the
 video has been building to. The transition s
hould feel earned by what came before. "Use y
our boldest transition here" is a default, no
t a rule — the climax of a restrained edito
rial piece might be a hard cut.
- **Wind-down
** — returns to a motion character that all
ows the viewer to exhale. Matches the opening
 in tone, not necessarily in technique.
- **O
utro** — no new energy. Slowest and simples
t in the video. Closure.

## Blur and Motion 
Intensity

Blur and duration should express t
he energy of the content, not match a lookup 
table. The ranges below are calibration refer
ences — starting points to adjust from base
d on what the brand and storyboard call for.


Higher-energy transitions: shorter duration,
 less blur, no hold at peak. The motion is im
mediate.
Lower-energy transitions: longer dur
ation, more blur, longer hold at peak. The mo
tion has weight.

Calibration ranges (not pre
scriptions):

- Soft/organic: blur 20–30px,
 duration 0.8–1.2s, hold 0.3–0.5s
- Direc
tional/purposeful: blur 8–15px, duration 0.
4–0.6s, hold 0.1–0.2s
- Percussive/instan
t: blur 3–6px, duration 0.2–0.3s, no hold


A brand that uses these as a formula will p
roduce transitions that feel the same across 
every video. A brand-derived choice asks: wha
t blur and duration expresses the weight this
 transition should have?

## Presets

| Prese
t     | Duration | Easing            |
| ----
------ | -------- | ----------------- |
| `sn
appy`   | 0.2s     | `power4.inOut`    |
| `s
mooth`   | 0.4s     | `power2.inOut`    |
| `
gentle`   | 0.6s     | `sine.inOut`      |
| 
`dramatic` | 0.5s     | `power3.in` → out |

| `instant`  | 0.15s    | `expo.inOut`      
|
| `luxe`     | 0.7s     | `power1.inOut`   
 |

## Implementation

Read [transitions/cata
log.md](transitions/catalog.md) for GSAP code
 and hard rules for every transition type.

|
 Category    | CSS                           
                                 | Shader (We
bGL)                                         
                   |
| ----------- | --------
---------------------------------------------
--------- | ---------------------------------
---------------------------------------- |
| 
Push/slide  | Push slide, vertical push, elas
tic push, squeeze               | Whip pan   
                                             
                  |
| Scale/zoom  | Zoom thro
ugh, zoom out, gravity drop, 3D flip         
         | Cinematic zoom, gravitational lens
                                        |
| R
eveal/mask | Circle iris, diamond iris, diago
nal split, clock wipe, shutter | SDF iris    
                                             
                 |
| Dissolve    | Crossfade,
 blur crossfade, focus pull, color dip       
        | Cross-warp morph, domain warp      
                                       |
| Co
ver       | Staggered blocks, horizontal blin
ds, vertical blinds           | —          
                                             
                  |
| Light       | Light lea
k, overexposure burn, film burn              
         | Light leak (shader), thermal disto
rtion                                   |
| D
istortion  | Glitch, chromatic aberration, ri
pple, VHS tape                 | Glitch (shad
er), chromatic split, ridged burn, ripple wav
es, swirl vortex |
| Pattern     | Grid disso
lve, morph circle                            
        | —                                
                                         |

#
# Transitions That Don't Work in CSS

Avoid: 
star iris, tilt-shift, lens flare, hinge/door
. See catalog.md for why.

## CSS vs Shader


CSS transitions animate scene containers with
 opacity, transforms, clip-path, and filters.
 Shader transitions composite both scene text
ures per-pixel on a WebGL canvas — they can
 warp, dissolve, and morph in ways CSS cannot
.

**Both are first-class options.** Shaders 
are provided by the `@hyperframes/shader-tran
sitions` package — import from the package 
instead of writing raw GLSL. CSS transitions 
are simpler to set up. Choose based on the ef
fect you want, not based on which is easier.


**Mixing is supported.** You can have some t
ransitions use WebGL shaders and others use a
 CSS crossfade in the same composition. Omit 
the `shader` field on any `TransitionConfig` 
entry to get a smooth opacity crossfade inste
ad of a WebGL effect:

```js
var tl = HyperSh
ader.init({
  bgColor: "#000",
  accentColor:
 "#6366f1",
  scenes: ["s1", "s2", "s3", "s4"
],
  transitions: [
    { time: 4.0, shader: 
"sdf-iris", duration: 0.7 }, // WebGL shader

    { time: 8.5, duration: 0.8 }, // no shade
r → CSS crossfade
    { time: 13.0, shader:
 "domain-warp", duration: 0.6 }, // WebGL sha
der
  ],
});
```

HyperShader manages all sce
ne visibility regardless of transition type. 
Let it create the timeline (don't pass `timel
ine:` into `init()`) and add your beat animat
ions to the returned `tl` after the call.

##
 Shader-Compatible CSS Rules

Shader transiti
ons capture DOM scenes to WebGL textures via 
html2canvas. The canvas 2D rendering pipeline
 doesn't match CSS exactly. Follow these rule
s to avoid visible artifacts at transition bo
undaries:

1. **No `transparent` keyword in g
radients.** Canvas interpolates `transparent`
 as `rgba(0,0,0,0)` (black at zero alpha), cr
eating dark fringes. Always use the target co
lor at zero alpha: `rgba(200,117,51,0)` not `
transparent`.
2. **No gradient backgrounds on
 elements thinner than 4px.** Canvas can't ma
tch CSS gradient rendering on 1-2px elements.
 Use solid `background-color` on thin accent 
lines.
3. **No CSS variables (`var()`) on ele
ments visible during capture.** html2canvas d
oesn't reliably resolve custom properties. Us
e literal color values in inline styles.
4. *
*Mark uncapturable decorative elements with `
data-no-capture`.** The capture function skip
s these. They're present on the live DOM but 
absent from the shader texture. Use for eleme
nts that can't follow the rules above.
5. **N
o gradient opacity below 0.15.** Gradient ele
ments below 10% opacity render differently in
 canvas vs CSS. Increase to 0.15+ or use a so
lid color at equivalent brightness.
6. **Ever
y `.scene` div must have explicit `background
-color`, AND pass the same color as `bgColor`
 in the `init()` config.** The package captur
es scene elements via html2canvas. Both the C
SS `background-color` on `.scene` and the `bg
Color` config must match. Without either, the
 texture renders as black.

These rules only 
apply to shader transition compositions. CSS-
only compositions have no restrictions.

## V
isual Pattern Warning

Avoid transitions that
 create visible repeating geometric patterns 
— grids of tiles, hexagonal cells, uniform 
dot arrays, evenly-spaced blob circles. These
 look cheap and artificial regardless of the 
math behind them. Organic noise (FBM, domain 
warping) is good because it's irregular. Geom
etric repetition is bad because the eye insta
ntly sees the grid.


