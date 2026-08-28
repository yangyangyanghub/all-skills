# Typography

The compiler embeds supported f
onts — just write `font-family` in CSS.

##
 Banned

Training-data defaults that every LL
M reaches for. These produce monoculture acro
ss compositions.

Inter, Roboto, Open Sans, N
oto Sans, Arimo, Lato, Source Sans, PT Sans, 
Nunito, Poppins, Outfit, Sora, Playfair Displ
ay, Cormorant Garamond, Bodoni Moda, EB Garam
ond, Cinzel, Prata, Syne

**Syne in particula
r** is the most overused "distinctive" displa
y font. It is an instant AI design tell.

## 
Guardrails

You know these rules but you viol
ate them. Stop.

- **Don't pair two sans-seri
fs.** You do this constantly — one for head
lines, one for body. Cross the boundary: seri
f + sans, or sans + mono.
- **One expressive 
font per scene.** You pick two interesting fo
nts trying to make it "better." One performs,
 one recedes.
- **Weight contrast must be ext
reme.** You default to 400 vs 700. Video need
s 300 vs 900. The difference must be visible 
in motion at a glance.
- **Video sizes, not w
eb sizes.** Body: 20px minimum. Headlines: 60
px+. Data labels: 16px. You will try to use 1
4px. Don't.

## What You Don't Do Without Bei
ng Told

- **Tension should mean something.**
 Don't pattern-match pairings. Ask WHY these 
two fonts disagree. The pairing should embody
 the content's contradiction — mechanical v
s human, public vs private, institutional vs 
personal. If you can't articulate the tension
, it's arbitrary.
- **Register switching.** A
ssign different fonts to different communicat
ive modes — one voice for statements, anoth
er for data, another for attribution. Not hie
rarchy on a page. Voices in a conversation.
-
 **Tension can live inside a single font.** A
 font that looks familiar but is secretly str
ange creates tension with the viewer's expect
ations, not with another font.
- **One variab
le changed = dramatic contrast.** Same letter
forms, monospaced vs proportional. Same famil
y at different optical sizes. Changing only r
hythm while everything else stays constant.
-
 **Double personality works.** Two expressive
 fonts can coexist if they share an attitude 
(both irreverent, both precise) even when the
ir forms are completely different.
- **Time i
s hierarchy.** The first element to appear is
 the most important. In video, sequence repla
ces position.
- **Motion is typography.** How
 a word enters carries as much meaning as the
 font. A 0.1s slam vs a 2s fade — same font
, completely different message.
- **Fixed rea
ding time.** 3 seconds on screen = must be re
adable in 2. Fewer words, larger type.
- **Tr
acking tighter than web.** -0.03em to -0.05em
 on display sizes. Video encoding compresses 
letter detail.

## Finding Fonts

Don't defau
lt to what you know. If the content is luxury
, a grotesque sans might create more tension 
than the expected Didone serif. Decide the re
gister first, then search.

Save this script 
to `/tmp/fontquery.py` and run with `curl -s 
'https://fonts.google.com/metadata/fonts' > /
tmp/gfonts.json && python3 /tmp/fontquery.py 
/tmp/gfonts.json`:

```python
import json, sy
s, random
from collections import OrderedDict


random.seed()  # true random each run

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
its.get(cat,10)]
    if not items: continue
 
   print(f"--- {cat} ({len(items)}) ---")
   
 for ff in items:
        var = "VAR" if ff.g
et("axes") else "   "
        print(f'  {ff.g
et("popularity"):4d} | {var} | {ff["family"]}
')
    print()
```

Five categories: trending
 sans, trending serif, monospace, impact/cond
ensed, script/handwriting. All dynamically fi
ltered from Google Fonts metadata — no hard
coded font names. Cross classification bounda
ries when pairing.

## Selection Thinking

Do
n't pick fonts by category reflex (editorial 
→ serif, tech → mono, modern → geometri
c sans). That's pattern matching, not design.


1. **Name the register.** What voice is the
 content speaking in? Institutional authority
? Personal confession? Technical precision? C
asual irreverence? The register narrows the f
ield more than the category.
2. **Think physi
cally.** Imagine the font as a physical objec
t the brand could ship — a museum exhibit c
aption, a hand-painted shop sign, a 1970s mai
nframe terminal manual, a fabric label inside
 a coat, a children's book printed on cheap n
ewsprint, a tax form. Whichever physical obje
ct fits the register is pointing at the right
 _kind_ of typeface.
3. **Reject your first i
nstinct.** The first font that feels right is
 usually your training-data default for that 
register. If you picked it last time too, fin
d something else.
4. **Cross-check the assump
tion.** An editorial brief does NOT need a se
rif. A technical brief does NOT need a sans. 
A children's product does NOT need a rounded 
display font. The most distinctive choice oft
en contradicts the category expectation.

## 
Similar-Font Pairing

Never pair two fonts th
at are similar but not identical — two geom
etric sans-serifs, two transitional serifs, t
wo humanist sans. They create visual friction
 without clear hierarchy. The viewer senses s
omething is "off" but can't articulate it. Ei
ther use one font at two weights, or pair fon
ts that contrast on multiple axes: serif + sa
ns, condensed + wide, geometric + humanist.


## Dark Backgrounds

Light text on dark backg
rounds creates two optical illusions you need
 to compensate for:

- **Increased apparent w
eight.** Light-on-dark reads heavier than dar
k-on-light at the same `font-weight`. Use 350
 instead of 400 for body text. Headlines are 
less affected because size compensates.
- **T
ighter apparent spacing.** Light halos around
 letterforms reduce perceived gaps. Increase 
`line-height` by 0.05-0.1 beyond your light-b
ackground value. For display sizes, add 0.01e
m `letter-spacing` to counteract.

## OpenTyp
e Features for Data

Most fonts ship with Ope
nType features that are off by default. Turn 
them on for data compositions:

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


`tabular-nums` is essential any time numbers
 are stacked vertically — stat callouts, ti
mers, scoreboards, data tables. Without it, d
igits have proportional widths and columns do
n't align.


