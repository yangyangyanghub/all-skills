---
name: hyperframes-cli
description: HyperF
rames CLI dev loop — `npx hyperframes` for 
scaffolding (init), validation (lint, inspect
), preview, render, and environment troublesh
ooting (doctor, browser, info, upgrade). Use 
when running any of these commands or trouble
shooting the HyperFrames build/render environ
ment. For asset preprocessing commands (`tts`
, `transcribe`, `remove-background`), invoke 
the `hyperframes-media` skill instead.
---

#
 HyperFrames CLI

Everything runs through `np
x hyperframes`. Requires Node.js >= 22 and FF
mpeg.

## Workflow

1. **Scaffold** — `npx 
hyperframes init my-video`
2. **Write** — a
uthor HTML composition (see the `hyperframes`
 skill)
3. **Lint** — `npx hyperframes lint
`
4. **Visual inspect** — `npx hyperframes 
inspect`
5. **Preview** — `npx hyperframes 
preview`
6. **Render** — `npx hyperframes r
ender`

Lint and inspect before preview. `lin
t` catches missing `data-composition-id`, ove
rlapping tracks, and unregistered timelines. 
`inspect` opens the rendered composition in h
eadless Chrome, seeks through the timeline, a
nd reports text spilling out of bubbles/conta
iners or off the canvas.

## Scaffolding

```
bash
npx hyperframes init my-video           
             # interactive wizard
npx hyperfr
ames init my-video --example warm-grain   # p
ick an example
npx hyperframes init my-video 
--video clip.mp4        # with video file
npx
 hyperframes init my-video --audio track.mp3 
      # with audio file
npx hyperframes init 
my-video --example blank --tailwind # with Ta
ilwind v4 browser runtime
npx hyperframes ini
t my-video --non-interactive       # skip pro
mpts (CI/agents)
```

Templates: `blank`, `wa
rm-grain`, `play-mode`, `swiss-grid`, `vignel
li`, `decision-tree`, `kinetic-type`, `produc
t-promo`, `nyt-graph`.

`init` creates the ri
ght file structure, copies media, transcribes
 audio with Whisper, and installs AI coding s
kills. Use it instead of creating files by ha
nd.

When using `--tailwind`, invoke the `tai
lwind` skill before editing classes or theme 
tokens. The scaffold uses Tailwind v4.2 via t
he browser runtime, not Studio's Tailwind v3 
setup.

## Linting

```bash
npx hyperframes l
int                  # current directory
npx 
hyperframes lint ./my-project     # specific 
project
npx hyperframes lint --verbose       
 # info-level findings
npx hyperframes lint -
-json           # machine-readable
```

Lints
 `index.html` and all files in `compositions/
`. Reports errors (must fix), warnings (shoul
d fix), and info (with `--verbose`).

## Visu
al Inspect

```bash
npx hyperframes inspect  
               # inspect rendered layout over
 the timeline
npx hyperframes inspect ./my-pr
oject    # specific project
npx hyperframes i
nspect --json          # agent-readable findi
ngs
npx hyperframes inspect --samples 15    #
 denser timeline sweep
npx hyperframes inspec
t --at 1.5,4,7.25 # explicit hero-frame times
tamps
```

Use this after `lint` and `validat
e`, especially for compositions with speech b
ubbles, cards, captions, or tight typography.
 It reports:

- Text extending outside the ne
arest visual container or bubble
- Text clipp
ed by its own fixed-width/fixed-height box
- 
Text extending outside the composition canvas

- Children escaping clipping containers

Err
ors should be fixed before rendering. Warning
s are surfaced for agent review; add `--stric
t` to fail on warnings too. Repeated static i
ssues are collapsed by default so JSON output
 stays compact for LLM context windows. If ov
erflow is intentional for an entrance/exit an
imation, mark the element or ancestor with `d
ata-layout-allow-overflow`. If a decorative e
lement should never be audited, mark it with 
`data-layout-ignore`.

`npx hyperframes layou
t` remains available as a compatibility alias
 for the same visual inspection pass.

## Pre
viewing

```bash
npx hyperframes preview     
              # serve current directory
npx h
yperframes preview --port 4567       # custom
 port (default 3002)
```

Hot-reloads on file
 changes. Opens the studio in your browser au
tomatically.

When handing a project back to 
the user, use the Studio project URL, not the

source `index.html` path:

```text
http://lo
calhost:<port>/#project/<project-name>
```

U
se the actual port from the preview output an
d the project directory name. For
example, af
ter `npx hyperframes preview --port 3017` in 
`codex-openai-video`,
report `http://localhos
t:3017/#project/codex-openai-video`.

Treat `
index.html` as source-code context only. It i
s fine to link it as an
implementation file, 
but do not label it as the project or preview
 surface.

## Rendering

```bash
npx hyperfra
mes render                                # s
tandard MP4
npx hyperframes render --output f
inal.mp4             # named output
npx hyper
frames render --quality draft                
# fast iteration
npx hyperframes render --fps
 60 --quality high        # final delivery
np
x hyperframes render --format webm           
       # transparent WebM
npx hyperframes ren
der --docker                       # byte-ide
ntical
```

| Flag                 | Options 
              | Default                    | 
Notes                                        
                      |
| -------------------
- | --------------------- | -----------------
--------- | ---------------------------------
--------------------------------- |
| `--outp
ut`           | path                  | rende
rs/name_timestamp.mp4 | Output path          
                                             
 |
| `--fps`              | 24, 30, 60       
     | 30                         | 60fps dou
bles render time                             
             |
| `--quality`          | draft
, standard, high | standard                  
 | draft for iterating                       
                         |
| `--format`      
     | mp4, webm             | mp4           
             | WebM supports transparency    
                                     |
| `--w
orkers`          | 1-8 or auto           | au
to                       | Each spawns Chrome
                                             
    |
| `--docker`           | flag          
        | off                        | Reprod
ucible output                                
                |
| `--gpu`              | fl
ag                  | off                    
    | GPU-accelerated encoding               
                            |
| `--strict`   
        | flag                  | off        
                | Fail on lint errors        
                                        |
| `
--strict-all`       | flag                  |
 off                        | Fail on errors 
AND warnings                                 
       |
| `--variables`        | JSON object
           | —                          | O
verride variable values declared in `data-com
position-variables`  |
| `--variables-file`  
 | path                  | —               
           | JSON file with variable values (
alternative to `--variables`)      |
| `--str
ict-variables` | flag                  | off 
                       | Fail render on undec
lared keys or type mismatches in `--variables
` |

**Quality guidance:** `draft` while iter
ating, `standard` for review, `high` for fina
l delivery.

**Parametrized renders:** the co
mposition declares its variables on the `<htm
l>` root with **`data-composition-variables`*
* — a JSON **array of declarations** (`{id,
 type, label, default}` per entry) that defin
es the schema. Scripts inside read the resolv
ed values via `window.__hyperframes.getVariab
les()`. The CLI **`--variables '{"title":"Q4 
Report"}'`** is a JSON **object keyed by id**
 that overrides those declared defaults for o
ne render; missing keys fall through, so the 
same composition runs unchanged in dev previe
w and in production. (Sub-comp hosts can also
 override per-instance with **`data-variable-
values`** — same object shape, scoped to on
e mount of the sub-composition. See the `hype
rframes` skill for the full pattern.)

## Ass
et Preprocessing

`npx hyperframes tts`, `tra
nscribe`, and `remove-background` produce ass
ets (narration audio, word-level transcripts,
 transparent video) that get dropped into a c
omposition. Each downloads its own model on f
irst run. For voice selection, whisper model 
rules (the `.en`-translates-non-English gotch
a), output format choice (VP9 alpha WebM vs P
roRes), and the TTS → transcribe → captio
ns chain, invoke the `hyperframes-media` skil
l.

## Troubleshooting

```bash
npx hyperfram
es doctor       # check environment (Chrome, 
FFmpeg, Node, memory)
npx hyperframes browser
      # manage bundled Chrome
npx hyperframes
 info         # version and environment detai
ls
npx hyperframes upgrade      # check for u
pdates
```

Run `doctor` first if rendering f
ails. Common issues: missing FFmpeg, missing 
Chrome, low memory.

## Other

```bash
npx hy
perframes compositions   # list compositions 
in project
npx hyperframes docs           # o
pen documentation
npx hyperframes benchmark .
    # benchmark render performance
```


