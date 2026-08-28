# Captions

## Language Rule (Non-Negotiable)


**Never use `.en` models unless the user ex
plicitly states the audio is English.** `.en`
 models TRANSLATE non-English audio into Engl
ish instead of transcribing it.

1. User says
 the language → `--model small --language <
code>` (no `.en`)
2. User says English → `-
-model small.en`
3. Language unknown → `--m
odel small` (no `.en`, no `--language`) — a
uto-detects

---

Analyze spoken content to d
etermine caption style. If user specifies a s
tyle, use that. Otherwise, detect tone from t
he transcript.

## Transcript Source

```json

[
  { "text": "Hello", "start": 0.0, "end": 
0.5 },
  { "text": "world.", "start": 0.6, "e
nd": 1.2 }
]
```

For transcription commands,
 whisper models, external APIs, see [transcri
pt-guide.md](transcript-guide.md).

## Style 
Detection (When No Style Specified)

Read the
 full transcript before choosing. Four dimens
ions:

**1. Visual feel** — corporate→cle
an; energetic→bold; storytelling→elegant;
 technical→precise; social→playful.

**2.
 Color palette** — dark+bright for energy; 
muted for professional; high contrast for cla
rity; one accent color.

**3. Font mood** —
 heavy/condensed for impact; clean sans for m
odern; rounded for friendly; serif for elegan
ce.

**4. Animation character** — scale-pop
 for punchy; gentle fade for calm; word-by-wo
rd for emphasis; typewriter for technical.

#
# Per-Word Styling

Scan for words deserving 
distinct treatment:

- **Brand/product names*
* — larger size, unique color
- **ALL CAPS*
* — scale boost, flash, accent color
- **Nu
mbers/statistics** — bold weight, accent co
lor
- **Emotional keywords** — exaggerated 
animation (overshoot, bounce)
- **Call-to-act
ion** — highlight, underline, color pop
- *
*Marker highlight** — for beyond-color emph
asis, see [css-patterns.md](css-patterns.md)


## Script-to-Style Mapping

| Tone         |
 Font mood                | Animation        
                  | Color                    
   | Size    |
| ------------ | -------------
----------- | -------------------------------
--- | --------------------------- | ------- |

| Hype/launch  | Heavy condensed, 800-900 | 
Scale-pop, back.out(1.7), 0.1-0.2s | Bright o
n dark              | 72-96px |
| Corporate  
  | Clean sans, 600-700      | Fade+slide, po
wer3.out, 0.3s       | White/neutral, muted a
ccent | 56-72px |
| Tutorial     | Mono/clean
 sans, 500-600 | Typewriter/fade, 0.4-0.5s   
       | High contrast, minimal      | 48-64p
x |
| Storytelling | Serif/elegant, 400-500  
 | Slow fade, power2.out, 0.5-0.6s    | Warm 
muted tones            | 44-56px |
| Social  
     | Rounded sans, 700-800    | Bounce, ela
stic.out, word-by-word  | Playful, colored pi
lls      | 56-80px |

## Word Grouping

- **H
igh energy:** 2-3 words. Quick turnover.
- **
Conversational:** 3-5 words. Natural phrases.

- **Measured/calm:** 4-6 words. Longer group
s.

Break on sentence boundaries, 150ms+ paus
es, or max word count.

## Positioning

- **L
andscape (1920x1080):** Bottom 80-120px, cent
ered
- **Portrait (1080x1920):** Lower middle
 ~600-700px from bottom, centered
- Never cov
er the subject's face
- `position: absolute` 
— never relative
- One caption group visibl
e at a time

## Text Overflow Prevention

Use
 `window.__hyperframes.fitTextFontSize()`:

`
``js
var result = window.__hyperframes.fitTex
tFontSize(group.text.toUpperCase(), {
  fontF
amily: "Outfit",
  fontWeight: 900,
  maxWidt
h: 1600,
});
el.style.fontSize = result.fontS
ize + "px";
```

Options: `maxWidth` (1600 la
ndscape, 900 portrait), `baseFontSize` (78), 
`minFontSize` (42), `fontWeight`, `fontFamily
`, `step` (2).

CSS safety nets: `max-width` 
on container, `overflow: visible` (**not** `h
idden` — hidden clips scaled emphasis words
 and glow effects), `position: absolute`, exp
licit `height`. When per-word styling uses `s
cale > 1.0`, compute `maxWidth = safeWidth / 
maxScale` to leave headroom.

**Container pat
tern:** Full-width absolute container, center
ed. Do **not** use `left: 50%; transform: tra
nslateX(-50%)` — causes clipping at composi
tion edges.

## Caption Exit Guarantee

Every
 group **must** have a hard kill after exit a
nimation:

```js
tl.to(groupEl, { opacity: 0,
 scale: 0.95, duration: 0.12, ease: "power2.i
n" }, group.end - 0.12);
tl.set(groupEl, { op
acity: 0, visibility: "hidden" }, group.end);
 // deterministic kill
```

Self-lint after b
uilding timeline — place **before** `window
.__timelines[id] = tl` so it runs at composit
ion init:

```js
GROUPS.forEach(function (gro
up, gi) {
  var el = document.getElementById(
"cg-" + gi);
  if (!el) return;
  tl.seek(gro
up.end + 0.01);
  var computed = window.getCo
mputedStyle(el);
  if (computed.opacity !== "
0" && computed.visibility !== "hidden") {
   
 console.warn(
      "[caption-lint] group " 
+ gi + " still visible at t=" + (group.end + 
0.01).toFixed(2) + "s",
    );
  }
});
tl.see
k(0);
```

## Pre-Built Caption Components

B
efore building caption styles from scratch, c
heck the registry — 15 ready-to-use caption
 components cover the most common styles. Ins
tall with `npx hyperframes add <name>` and us
e as a sub-composition via `data-composition-
src`.

```bash
npx hyperframes catalog --tag 
caption-style   # list all caption components

npx hyperframes add caption-highlight       
  # install a specific one
```

| Style      
               | Component                   
 | Best for                     |
| ---------
---------------- | --------------------------
-- | ---------------------------- |
| TikTok-
style highlight    | `caption-highlight`     
     | Social, high-energy          |
| Karao
ke pill              | `caption-pill-karaoke`
       | Music, lyric videos          |
| Cin
ematic editorial       | `caption-editorial-e
mphasis` | Documentary, storytelling    |
| G
litch / cyber            | `caption-glitch-rg
b`         | Tech, gaming                 |
|
 Full-screen slam          | `caption-kinetic
-slam`       | Hype, announcements          |

| Neon glow                 | `caption-neon-
glow`          | Night, club, neon aesthetics
 |
| Neon accent (multi-color) | `caption-neo
n-accent`        | Colorful, playful         
   |
| Wipe reveal               | `caption-c
lip-wipe`          | Clean, modern           
     |
| Gradient fill             | `caption
-gradient-fill`      | Vibrant, eye-catching 
       |
| Matrix decode             | `capti
on-matrix-decode`      | Sci-fi, tech reveals
         |
| Emoji pop                 | `cap
tion-emoji-pop`          | Social, casual    
           |
| Parallax layers           | `c
aption-parallax-layers`    | Depth, cinematic
             |
| Particle burst            | 
`caption-particle-burst`     | Celebration, i
mpact keywords |
| Lava texture              
| `caption-texture`            | Bold, dramat
ic               |
| Weight shift            
  | `caption-weight-shift`       | Elegant, t
ypographic         |

Browse all with preview
s: [hyperframes.heygen.com/catalog](https://h
yperframes.heygen.com/catalog)

Caption compo
nents ship with transparent backgrounds — t
hey're pure overlays. If the underlying video
 is bright or busy, add a contrast layer (e.g
. a semi-transparent dark div) in the host co
mposition beneath the caption sub-composition
, not inside the component itself.

## Furthe
r References

- [dynamic-techniques.md](dynam
ic-techniques.md) — karaoke, clip-path reve
als, slam words, scatter exits, elastic, 3D r
otation
- [transcript-guide.md](transcript-gu
ide.md) — transcription commands, whisper m
odels, external APIs
- [css-patterns.md](css-
patterns.md) — CSS+GSAP marker highlighting
 (deterministic, fully seekable)

## Constrai
nts

- Deterministic. No `Math.random()`, no 
`Date.now()`.
- Sync to transcript timestamps
.
- One group visible at a time.
- Every grou
p must have a hard `tl.set` kill at `group.en
d`.
- The compiler embeds supported fonts aut
omatically — just declare `font-family` in 
CSS.


