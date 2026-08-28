# Video Composition

Video frames are not web
 pages. These rules apply to every compositio
n regardless of brand, style, or design spec.


## The Design Spec Is Brand, Not Layout

Th
e design spec (`frame.md` or `design.md`) def
ines what the brand looks like: colors, fonts
, personality, constraints. It does NOT defin
e how to compose a video frame. Use brand col
ors at video-appropriate intensity — not at
 web-UI opacity.

**Strict from the spec:** h
ex values (including background color), font 
families, weight relationships, Do's and Don'
ts. If the user chose a light canvas, use a l
ight canvas. If they chose dark, use dark. Do
 not override their palette.

**Adapt for vid
eo:** type sizes, spacing, decorative opacity
, border weight, component treatments. A web 
UI card at `border: 1px solid #e2e3e6` with `
box-shadow: 0 2px 4px rgba(0,0,0,0.06)` is in
visible on video. The brand color is sacred; 
the application is yours.

## Density

A beat
 with 3 elements looks empty. A beat with 8-1
0 feels alive.

Every scene needs:

- **Backg
round texture** — radial glow, oversized gh
ost type, color panel, grain, grid. Never sol
id flat color.
- **Midground content** — th
e actual message. Cards, stats, code blocks, 
images.
- **Foreground accents** — dividers
, labels, data bars, registration marks, mono
space metadata. The details that make it feel
 produced, not generated.

Aim for 8-10 visua
l elements per scene. Two of those should be 
decorative elements the user didn't ask for �
�� you add them because empty frames look bro
ken.

## Color Presence

Muted is fine. Flat 
is not. Every scene should have at least one 
color that pulls the eye.

- Brand accent sho
uld be VISIBLE — not a 5% opacity glow lost
 in compression. 15-25% for atmospheric, full
 saturation for focal elements.
- **Light can
vases work differently than dark.** On dark: 
accent glows pop naturally. On light: use bol
der borders (2px+ solid), stronger structural
 elements (rules, dividers), and full-saturat
ion accent hits. Light backgrounds need textu
re (subtle grain, patterns) to avoid the "bla
nk slide" feel. Don't switch to dark — make
 light cinematic.
- Tint neutrals toward the 
brand hue. Dead gray reads as undesigned.

##
 Scale

Web sizes are invisible on video. Eve
rything scales up.

| Element            | We
b     | Video    |
| ------------------ | ---
---- | -------- |
| Headlines          | 32-4
8px | 64-120px |
| Body text          | 14-16
px | 28-42px  |
| Labels             | 12px  
  | 18-24px  |
| Decorative opacity | 3-8%   
 | 12-25%   |
| Borders            | 1px     
| 2-4px    |
| Padding            | 16-32px |
 60-140px |

If you're writing a font-size un
der 24px in a video composition, justify it. 
If you're writing decorative opacity under 10
%, it's invisible.

## Motion Intensity

Subt
le reads as static at 30fps. Err toward more 
movement than feels safe.

- Every decorative
 element should have ambient motion: breathe,
 drift, pulse, orbit. Static decoratives feel
 dead.
- Vary motion per scene — don't repe
at the same ambient pattern.
- Scene entrance
s should use 3+ different eases and direction
s. If every element enters from `y: 30, opaci
ty: 0`, the scene has no choreography.

## Fr
ame Composition

- **Two focal points minimum
.** The eye needs somewhere to travel.
- **Fi
ll the frame.** Hero text: 60-80% of frame wi
dth.
- **Anchor to edges.** Pin content to le
ft/top or right/bottom. Centered-and-floating
 is a web layout pattern.
- **Split frames.**
 Data panel left, content right. Top bar with
 metadata, full-width below. Zone-based layou
ts over centered stacks.
- **Structural eleme
nts.** Rules, dividers, border panels. They c
reate visual paths and animate well (`scaleX:
 0` → `1`).


