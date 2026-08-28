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

Everything runs through `npx hyperframes`. Requires Node.js >= 22 and FFmpeg.

## Workflow

1. **Scaffold** — `npx hyperframes init my-video`
2. **Write** — author HTML composition (see the `hyperframes`skill)
3. **Lint** — `npx hyperframes lint `
4. **Visual inspect** — `npx hyperframes inspect`
5. **Preview** — `npx hyperframes preview`
6. **Render** — `npx hyperframes render`

Lint and inspect before preview. `lint` catches missing `data-composition-id`, overlapping tracks, and unregistered timelines. `inspect` opens the rendered composition in headless Chrome, seeks through the timeline, and reports text spilling out of bubbles/containers or off the canvas.

## Scaffolding

```
bash
npx hyperframes init my-video
 # interactive wizard
npx hyperfr
ames init my-video --example warm-grain # p
ick an example
npx hyperframes init my-video
--video clip.mp4 # with video file
npx
 hyperframes init my-video --audio track.mp3
 # with audio file
npx hyperframes init
my-video --example blank --tailwind # with Ta
ilwind v4 browser runtime
npx hyperframes ini
t my-video --non-interactive # skip pro
mpts (CI/agents)
```

Templates: `blank`, `warm-grain`, `play-mode`, `swiss-grid`, `vignelli`, `decision-tree`, `kinetic-type`, `product-promo`, `nyt-graph`.

`init` creates the right file structure, copies media, transcribesaudio with Whisper, and installs AI coding skills. Use it instead of creating files by hand.

When using `--tailwind`, invoke the `tailwind` skill before editing classes or theme tokens. The scaffold uses Tailwind v4.2 via the browser runtime, not Studio's Tailwind v3 setup.

## Linting

```bash
npx hyperframes l
int # current directory
npx
hyperframes lint./my-project # specific
project
npx hyperframes lint --verbose
 # info-level findings
npx hyperframes lint -
-json # machine-readable
```

Lints`index.html` and all files in `compositions/ `. Reports errors (must fix), warnings (should fix), and info (with `--verbose`).

## Visual Inspect

```bash
npx hyperframes inspect
 # inspect rendered layout over
 the timeline
npx hyperframes inspect./my-pr
oject # specific project
npx hyperframes i
nspect --json # agent-readable findi
ngs
npx hyperframes inspect --samples 15 #
 denser timeline sweep
npx hyperframes inspec
t --at 1.5, 4,7.25 # explicit hero-frame times
tamps
```

Use this after `lint` and `validate`, especially for compositions with speech bubbles, cards, captions, or tight typography.It reports:

- Text extending outside the nearest visual container or bubble
- Text clipped by its own fixed-width/fixed-height box - Text extending outside the composition canvas

- Children escaping clipping containers

Errors should be fixed before rendering. Warnings are surfaced for agent review; add `--strict` to fail on warnings too. Repeated static issues are collapsed by default so JSON outputstays compact for LLM context windows. If overflow is intentional for an entrance/exit animation, mark the element or ancestor with `data-layout-allow-overflow`. If a decorative element should never be audited, mark it with `data-layout-ignore`.

`npx hyperframes layout` remains available as a compatibility aliasfor the same visual inspection pass.

## Previewing

```bash
npx hyperframes preview
 # serve current directory
npx h
yperframes preview --port 4567 # custom
 port (default 3002)
```

Hot-reloads on filechanges. Opens the studio in your browser automatically.

When handing a project back to the user, use the Studio project URL, not the

source `index.html` path:

```text
http://lo
calhost:<port>/#project/<project-name>
```

Use the actual port from the preview output and the project directory name. Forexample, after `npx hyperframes preview --port 3017` in `codex-openai-video`, report `http://localhost:3017/#project/codex-openai-video`.

Treat ` index.html` as source-code context only. It is fine to link it as animplementation file, but do not label it as the project or previewsurface.

## Rendering

```bash
npx hyperfra
mes render # s
tandard MP4
npx hyperframes render --output f
inal.mp4 # named output
npx hyper
frames render --quality draft
# fast iteration
npx hyperframes render --fps
 60 --quality high # final delivery
np
x hyperframes render --format webm
 # transparent WebM
npx hyperframes ren
der --docker # byte-ide
ntical
```

| Flag | Options
 | Default |
Notes | | -------------------
- | --------------------- | ----------------- --------- | --------------------------------- --------------------------------- | | `--output` | path | renders/name_timestamp.mp4 | Output path

 |
| `--fps` | 24, 30, 60
 | 30 | 60fps dou
bles render time |
| `--quality` | draft
, standard, high | standard | draft for iterating | | `--format`
 | mp4, webm | mp4
 | WebM supports transparency | | `--workers` | 1-8 or auto | auto | Each spawns Chrome

 |
| `--docker` | flag
 | off | Reprod
ucible output |
| `--gpu` | fl
ag | off | GPU-accelerated encoding | | `--strict`
 | flag | off
 | Fail on lint errors | | ` --strict-all` | flag |off | Fail on errors AND warnings |
| `--variables` | JSON object
 | — | O
verride variable values declared in `data-composition-variables` | | `--variables-file`
 | path | —
 | JSON file with variable values ( alternative to `--variables`) | | `--strict-variables` | flag | off | Fail render on undeclared keys or type mismatches in `--variables ` |

**Quality guidance:**`draft` while iterating, `standard` for review, `high` for final delivery.

**Parametrized renders:** the composition declares its variables on the `<html>` root with**`data-composition-variables`*
* — a JSON**array of declarations**(`{id, type, label, default}` per entry) that defines the schema. Scripts inside read the resolved values via `window.__hyperframes.getVariables()`. The CLI**`--variables '{"title":"Q4 Report"}'`** is a JSON**object keyed by id** that overrides those declared defaults for one render; missing keys fall through, so the same composition runs unchanged in dev preview and in production. (Sub-comp hosts can also override per-instance with**`data-variable- values`** — same object shape, scoped to one mount of the sub-composition. See the `hyperframes` skill for the full pattern.)

## Asset Preprocessing

`npx hyperframes tts`, `transcribe`, and `remove-background` produce assets (narration audio, word-level transcripts, transparent video) that get dropped into a composition. Each downloads its own model on first run. For voice selection, whisper model rules (the `.en`-translates-non-English gotcha), output format choice (VP9 alpha WebM vs ProRes), and the TTS → transcribe → captions chain, invoke the `hyperframes-media` skill.

## Troubleshooting

```bash
npx hyperfram
es doctor # check environment (Chrome,
FFmpeg, Node, memory)
npx hyperframes browser
 # manage bundled Chrome
npx hyperframes
 info # version and environment detai
ls
npx hyperframes upgrade # check for u
pdates
```

Run `doctor` first if rendering fails. Common issues: missing FFmpeg, missing Chrome, low memory.

## Other

```bash
npx hy
perframes compositions # list compositions
in project
npx hyperframes docs # o
pen documentation
npx hyperframes benchmark.
 # benchmark render performance
```


