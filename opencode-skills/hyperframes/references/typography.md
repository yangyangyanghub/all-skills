# Typography

The compiler embeds supported fonts — just write `font-family` in CSS.

## Banned

Training-data defaults that every LLM reaches for. These produce monoculture across compositions.

Inter, Roboto, Open Sans, Noto Sans, Arimo, Lato, Source Sans, PT Sans, Nunito, Poppins, Outfit, Sora, Playfair Display, Cormorant Garamond, Bodoni Moda, EB Garamond, Cinzel, Prata, Syne

**Syne in particular** is the most overused "distinctive" display font. It is an instant AI design tell.

## Guardrails

You know these rules but you violate them. Stop.

- **Don't pair two sans-serifs.** You do this constantly — one for headlines, one for body. Cross the boundary: serif + sans, or sans + mono.
- **One expressive font per scene.** You pick two interesting fonts trying to make it "better." One performs, one recedes.
- **Weight contrast must be extreme.** You default to 400 vs 700. Video needs 300 vs 900. The difference must be visible in motion at a glance.
- **Video sizes, not web sizes.** Body: 20px minimum. Headlines: 60px+. Data labels: 16px. You will try to use 14px. Don't.

## What You Don't Do Without Being Told

- **Tension should mean something.** Don't pattern-match pairings. Ask WHY these two fonts disagree. The pairing should embody the content's contradiction — mechanical vs human, public vs private, institutional vs personal. If you can't articulate the tension, it's arbitrary.
- **Register switching.** Assign different fonts to different communicative modes — one voice for statements, another for data, another for attribution. Not hierarchy on a page. Voices in a conversation. - **Tension can live inside a single font.** A font that looks familiar but is secretly strange creates tension with the viewer's expectations, not with another font.
- **One variable changed = dramatic contrast.** Same letterforms, monospaced vs proportional. Same family at different optical sizes. Changing only rhythm while everything else stays constant. -**Double personality works.** Two expressivefonts can coexist if they share an attitude (both irreverent, both precise) even when their forms are completely different.
- **Time is hierarchy.** The first element to appear isthe most important. In video, sequence replaces position.
- **Motion is typography.** Howa word enters carries as much meaning as thefont. A 0.1s slam vs a 2s fade — same font, completely different message.
- **Fixed reading time.**3 seconds on screen = must be readable in 2. Fewer words, larger type.
- **Tracking tighter than web.**-0.03em to -0.05emon display sizes. Video encoding compresses letter detail.

## Finding Fonts

Don't default to what you know. If the content is luxury, a grotesque sans might create more tension than the expected Didone serif. Decide the register first, then search.

Save this script to `/tmp/fontquery.py` and run with `curl -s 'https://fonts.google.com/metadata/fonts' > / tmp/gfonts.json && python3 /tmp/fontquery.py /tmp/gfonts.json`:

```python
import json, sy
s, random
from collections import OrderedDict


random.seed() # true random each run

with
 open(sys.argv[1]) as f:
 data = json.load
(f)
fonts = data.get("familyMetadataList", []
)

ban = {"Inter","Roboto","Open Sans","Noto
Sans","Lato","Poppins","Source Sans 3",

 "PT Sans","Nunito","Outfit","Sora","Playfai
r Display","Cormorant Garamond",
 "Bodo
ni Moda","EB Garamond","Cinzel","Prata","Arim
o","Source Sans Pro","Syne"}
skip_pfx = ("Rob
oto","Noto ","Google Sans","Bpmf","Playwrite"
,"Anek","BIZ ",
 "Nanum","Shippori
","Sawarabi","Zen ","Kaisei","Kiwi ","Yuji ",
"Radio ")

def ok(f):
 if f["family"] in b
an: return False
 if any(f["family"].start
swith(b) for b in skip_pfx): return False

 if "latin" not in (f.get("subsets") or []):
return False
 return True

seen = set()
R
= OrderedDict()

# Trending Sans — recent (
2022+), popular (<300)
R["Trending Sans"] = [
]
for f in fonts:
 if not ok(f) or f["fami
ly"] in seen: continue
 if f.get("category
") in ("Sans Serif","Display") and f.get("dat
eAdded","") >= "2022-01-01" and f.get("popula
rity",9999) < 300:
 R["Trending Sans"]
.append(f); seen.add(f["family"])

# Trending
 Serif — recent (2018+), popular (<600)
R["
Trending Serif"] = []
for f in fonts:
 if
not ok(f) or f["family"] in seen: continue

 if f.get("category") == "Serif" and f.get("
dateAdded","") >= "2018-01-01" and f.get("pop
ularity",9999) < 600:
 R["Trending Ser
if"].append(f); seen.add(f["family"])

# Mono
space — recent (2018+), popular (<600)
R["M
onospace"] = []
for f in fonts:
 if not ok
(f) or f["family"] in seen: continue
 if f
.get("category") == "Monospace" and f.get("da
teAdded","") >= "2018-01-01" and f.get("popul
arity",9999) < 600:
 R["Monospace"].ap
pend(f); seen.add(f["family"])

# Impact & Co
ndensed — heavy display fonts with 800+ wei
ght
R["Impact & Condensed"] = []
for f in fon
ts:
 if not ok(f) or f["family"] in seen:
continue
 has_heavy = any(k in list(f.get(
"fonts",{}).keys()) for k in ("800","900"))

 is_display = f.get("category") in ("Sans S
erif","Display")
 if has_heavy and is_disp
lay and f.get("popularity",9999) < 400:

 R["Impact & Condensed"].append(f); seen.ad
d(f["family"])

# Script & Handwriting — po
pular (<300)
R["Script & Handwriting"] = []
f
or f in fonts:
 if not ok(f) or f["family"
] in seen: continue
 if f.get("category")
== "Handwriting" and f.get("popularity",9999)
 < 300:
 R["Script & Handwriting"].app
end(f); seen.add(f["family"])


# Randomize t
he top 5 in each category so the LLM doesn't
always pick the same first result
for cat in
R:
 R[cat].sort(key=lambda x: x.get("popul
arity",9999))
 top5 = R[cat][:5]
 rest
= R[cat][5:]
 random.shuffle(top5)
 R[c
at] = top5 + rest
limits = {"Trending Sans":1
5,"Trending Serif":12,"Monospace":8,

 "Impact & Condensed":12,"Script & Handwriti
ng":10}
for cat in R:
 items = R[cat][:lim
its.get(cat, 10)]
 if not items: continue

 print(f"--- {cat} ({len(items)}) ---")

 for ff in items:
 var = "VAR" if ff.g
et("axes") else " "
 print(f' {ff.g
et("popularity"):4d} | {var} | {ff["family"]}
')
 print()
```

Five categories: trendingsans, trending serif, monospace, impact/condensed, script/handwriting. All dynamically filtered from Google Fonts metadata — no hardcoded font names. Cross classification boundaries when pairing.

## Selection Thinking

Don't pick fonts by category reflex (editorial → serif, tech → mono, modern → geometric sans). That's pattern matching, not design.


1. **Name the register.** What voice is thecontent speaking in? Institutional authority ? Personal confession? Technical precision? Casual irreverence? The register narrows the field more than the category.
2. **Think physically.** Imagine the font as a physical object the brand could ship — a museum exhibit caption, a hand-painted shop sign, a 1970s mainframe terminal manual, a fabric label insidea coat, a children's book printed on cheap newsprint, a tax form. Whichever physical object fits the register is pointing at the right_kind_ of typeface.
3. **Reject your first instinct.** The first font that feels right isusually your training-data default for that register. If you picked it last time too, find something else.
4. **Cross-check the assumption.** An editorial brief does NOT need a serif. A technical brief does NOT need a sans. A children's product does NOT need a rounded display font. The most distinctive choice often contradicts the category expectation.

## Similar-Font Pairing

Never pair two fonts that are similar but not identical — two geometric sans-serifs, two transitional serifs, two humanist sans. They create visual frictionwithout clear hierarchy. The viewer senses something is "off" but can't articulate it. Either use one font at two weights, or pair fonts that contrast on multiple axes: serif + sans, condensed + wide, geometric + humanist.


## Dark Backgrounds

Light text on dark backgrounds creates two optical illusions you needto compensate for:

- **Increased apparent weight.** Light-on-dark reads heavier than dark-on-light at the same `font-weight`. Use 350instead of 400 for body text. Headlines are less affected because size compensates.
- **Tighter apparent spacing.** Light halos aroundletterforms reduce perceived gaps. Increase `line-height` by 0.05-0.1 beyond your light-background value. For display sizes, add 0.01em `letter-spacing` to counteract.

## OpenType Features for Data

Most fonts ship with OpenType features that are off by default. Turn them on for data compositions:

```css
/* Tab
ular numbers — digits align vertically in c
olumns */
.stat-value,
.timer,
.data-column {

 font-variant-numeric: tabular-nums;
}

/*
Diagonal fractions — renders 1/2 as ½ */
.
recipe-amount,
.ratio {
 font-variant-numeri
c: diagonal-fractions;
}

/* Small caps for a
bbreviations — less visual shouting */
.abb
reviation,
.unit {
 font-variant-caps: all-s
mall-caps;
}

/* Disable ligatures in code �
� fi, fl, ffi should stay separate */
code,
.
code {
 font-variant-ligatures: none;
}
```


`tabular-nums` is essential any time numbersare stacked vertically — stat callouts, timers, scoreboards, data tables. Without it, digits have proportional widths and columns don't align.


