# Pre-Delivery Checklist

Use this checklist to validate every slide before deployment. Run through all applicable checks for each slide type.

---

## ✅ All Slides (Universal Checks)

### Structure & Layout
- [ ] `.slide-content` wrapper present
- [ ] Dimensions exactly 960×540px
- [ ] All content within boundaries (no overflow)
- [ ] Margins ≥ 0.5" (48px at 96 DPI)
- [ ] No scrollbars on rendered slide

### Typography
- [ ] Chinese-first font system applied (Noto Serif SC titles, Noto Sans SC body)
- [ ] Font sizes follow hierarchy (title > body)
- [ ] Body text left-aligned (not centered)
- [ ] No more than 2 font families used
- [ ] No emojis as icons (use SVG instead)

### Color
- [ ] All colors from chosen palette only
- [ ] Text contrast ratio ≥ 4.5:1 for body text
- [ ] Text contrast ratio ≥ 3:1 for large text (18px+)
- [ ] No gradients used (solid colors only)
- [ ] Consistent color application across slides

### CSS & Styling
- [ ] Inline CSS only (except Appendix A scaling snippet)
- [ ] No `<style>` blocks (except responsive scaling)
- [ ] No external stylesheets
- [ ] No CSS classes or class-based styling
- [ ] Background on `.slide-content` directly (no nested full-size div)

### SVG & Graphics
- [ ] SVG paths use only M/L/H/V/Z commands
- [ ] No Bézier curves (Q/C/S/T)
- [ ] No arc commands (A)
- [ ] No rotated shapes (`transform="rotate()"`)
- [ ] Text inside SVG using `<text>` element (not overlaid `<span>`)

### Interactivity
- [ ] No CSS animations
- [ ] No `@keyframes`
- [ ] No transitions
- [ ] No JavaScript animations
- [ ] No hover effects with motion
- [ ] No SVG animations

---

## 📄 Cover Page Checks

### Content
- [ ] Main title present
- [ ] Title size 72-120px
- [ ] Title bold weight
- [ ] Subtitle present (if applicable)
- [ ] Subtitle size 28-40px
- [ ] Supporting text minimal (optional)

### Visual
- [ ] Background image OR strong visual motif present
- [ ] Image path is actual file (not placeholder)
- [ ] Image resolution sufficient for 960×540
- [ ] Text readable over background
- [ ] Overlay used if background is busy

### Layout
- [ ] No page number badge
- [ ] Clear visual hierarchy (title dominates)
- [ ] Asymmetric or center-aligned layout chosen
- [ ] All elements within safe margins

---

## 📑 Table of Contents Checks

### Content
- [ ] Page title present (e.g., "Table of Contents")
- [ ] Section numbers present (01, 02... or I, II...)
- [ ] Section titles clear and concise
- [ ] Max 5-7 sections (more becomes cluttered)
- [ ] Optional descriptions (one-line each)

### Layout
- [ ] Page number badge present (bottom-right)
- [ ] Consistent formatting for all sections
- [ ] Visual hierarchy clear (numbers vs titles)
- [ ] Layout chosen: Vertical list / Grid / Sidebar / Card-based

### Typography
- [ ] Page title 36-44px
- [ ] Section numbers 28-36px
- [ ] Section titles 20-28px
- [ ] Descriptions 14-16px

---

## 📊 Section Divider Checks

### Content
- [ ] Section number present
- [ ] Section number size 72-120px (dominant element)
- [ ] Section number bold
- [ ] Section title 36-48px
- [ ] Optional intro text 16-20px

### Layout
- [ ] Page number badge present (bottom-right)
- [ ] SVG accent shapes used (bars, lines, blocks)
- [ ] Layout chosen: Bold Center / Left-Aligned / Split / Full-Bleed
- [ ] Style consistent with other dividers

### Color
- [ ] Section number uses accent color
- [ ] Clear contrast between number and background
- [ ] Colors from chosen palette

---

## 📝 Content Page Checks

### Content Structure
- [ ] Slide title present (always required)
- [ ] Slide title 36-44px, bold
- [ ] Body content matches assigned subtype
- [ ] Visual element present (image/chart/icon/SVG)
- [ ] Source/caption included (if showing data)

### Body Text
- [ ] Body text 14-16px, regular weight
- [ ] Body text LEFT-ALIGNED (never centered)
- [ ] Section headers 20-24px, bold
- [ ] Captions/sources 10-12px
- [ ] Stat callouts 60-72px (if used)

### Visual Element
- [ ] Image generated using `generate_image.ts`
- [ ] Image path valid (actual file exists)
- [ ] Image resolution appropriate
- [ ] Chart uses only allowed SVG elements (rect, circle, line, path M/L/H/V/Z)
- [ ] Pie chart generated as image (not SVG)

### Layout
- [ ] Page number badge present (bottom-right)
- [ ] Layout varies from previous content slides
- [ ] Content blocks separated by 0.3-0.5" (29-48px)
- [ ] Margins ≥ 0.5" (48px)

### Content Subtype Checks

**4a. Text**:
- [ ] Bullets/quotes/paragraphs present
- [ ] Icons or SVG shapes included (not plain text)
- [ ] Max 6 bullet points

**4b. Mixed Media**:
- [ ] Two-column layout (image + text)
- [ ] Image on one side, text on other
- [ ] Balance between visual and text

**4c. Data Visualization**:
- [ ] SVG chart present (bar/progress/ring)
- [ ] 1-3 key takeaways listed
- [ ] Data source cited

**4d. Comparison**:
- [ ] Side-by-side columns or cards
- [ ] Clear comparison (A vs B, pros/cons)
- [ ] Visual distinction between options

**4e. Timeline / Process**:
- [ ] Steps numbered or lettered
- [ ] Arrows/connectors between steps
- [ ] Logical flow left-to-right or top-to-bottom

**4f. Image Showcase**:
- [ ] Hero image as primary element
- [ ] Text supports (doesn't compete with) image
- [ ] Caption or supporting text included

---

## ✅ Summary / Closing Page Checks

### Content
- [ ] Closing title 48-72px, bold
- [ ] 3-5 takeaway points present
- [ ] Takeaways 18-24px, scannable
- [ ] Call-to-action clear (if applicable)
- [ ] Contact info included (14-16px, muted)

### Layout
- [ ] Page number badge present (bottom-right)
- [ ] Layout chosen: Key Takeaways / CTA / Thank You / Split Recap
- [ ] No new information introduced

### Tone
- [ ] Memorable ending
- [ ] Clear next steps (if applicable)
- [ ] Consistent with overall presentation tone

---

## 🔍 Technical Validation

### HTML Structure
- [ ] Valid HTML5 doctype present
- [ ] Responsive scaling snippet included (Appendix A)
- [ ] All text wrapped in text tags (`<p>`, `<h1>`-`<h6>`, `<ul>`, `<ol>`, `<li>`)
- [ ] No raw text directly inside `<div>`
- [ ] No manual bullet symbols (use `<ul>` or `<ol>`)

### File Structure
- [ ] File named correctly: `slide-01.html`, `slide-02.html`, etc.
- [ ] Zero-padded numbering (01, 02... not 1, 2)
- [ ] Images stored in `slides/imgs/` directory
- [ ] Image filenames descriptive (not generic like `image1.png`)

### Browser Rendering
- [ ] Slide renders correctly in Chrome/Firefox
- [ ] No JavaScript errors in console
- [ ] Text selectable (not background images)
- [ ] All images load successfully
- [ ] **`.slide-content` centered with zero overflow** — visual inspection MISSES shifted/off-canvas content. Verify quantitatively in a real browser (deployed index or HTTP server):
  ```js
  // .slide-content must be centered and fully inside the viewport
  const r = slideContent.getBoundingClientRect();
  r.x >= 0 && r.y >= 0 &&
  r.x + r.width <= window.innerWidth &&
  r.y + r.height <= window.innerHeight &&
  Math.abs(r.x - (window.innerWidth - r.width) / 2) < 2; // horizontally centered
  ```
  Common failure: `aside.notes` without `display:none` expands `section.slide`; `.slide-content` then clips off the LEFT edge (negative `r.x`) with blank space on the RIGHT. Symptom: "content shifted left, right side empty" — fix = `section.slide { display:flex; justify-content:center; align-items:center; }` + `aside.notes { display:none; }` (see html-implementation.md Appendix A).

---

## 📋 Final Deployment Checks

### Before Merging
- [ ] All slides verified individually
- [ ] Slide count matches outline
- [ ] Page badges numbered sequentially
- [ ] Consistent design across all slides
- [ ] No duplicate layouts back-to-back

### Deployment
- [ ] Run `deploy_presentation.ts` successfully
- [ ] Output directory created
- [ ] `index.html` with navigation generated
- [ ] `navigation.js` created
- [ ] All slide HTML files copied
- [ ] Images directory copied

### Post-Deployment
- [ ] Open `index.html` in browser
- [ ] Test navigation (arrow keys, number keys, buttons)
- [ ] Verify all slides display correctly
- [ ] Check keyboard controls work
- [ ] Test on different screen sizes (responsive)

---

## 🚨 Critical Checks (MUST PASS)

These checks are non-negotiable. If any fail, the slide is broken:

1. ✅ **Dimensions**: Exactly 960×540px
2. ✅ **Font**: Noto Serif SC (titles) + Noto Sans SC (body)
3. ✅ **No gradients**: Solid colors only
4. ✅ **No animations**: Static slides only
5. ✅ **SVG paths**: M/L/H/V/Z commands only
6. ✅ **Page badges**: Present on all slides except cover
7. ✅ **Inline CSS**: No style blocks (except scaling snippet)
8. ✅ **No Bézier/arcs**: Q/C/A commands forbidden
9. ✅ **Text inside SVG**: Not overlaid with absolute positioning
10. ✅ **Background on `.slide-content`**: Not nested full-size div

---

## 📝 Verification Script Usage

Use the automated verification tool:

```bash
# Verify single slide
bun scripts/verify_layout.ts --html slides/slide-01.html --type cover

# Verify content slide with subtype
bun scripts/verify_layout.ts --html slides/slide-02.html --type content --page-type text

# Verify all slides (example)
for i in {01..10}; do
  bun scripts/verify_layout.ts --html slides/slide-$i.html --type content
done
```

The verification script checks:
- Slide structure
- Dimensions
- Font usage
- Page badge presence
- Gradients/Animations
- SVG path constraints
- Type-specific requirements

---

## ✅ Quick Checklist (Copy-Paste)

For quick reference during slide creation:

```
SLIDE VERIFICATION:
- [ ] .slide-content wrapper
- [ ] 960×540px dimensions
- [ ] Chinese font system (Noto Serif SC / Noto Sans SC)
- [ ] No gradients
- [ ] No animations
- [ ] Inline CSS only
- [ ] SVG: M/L/H/V/Z only
- [ ] Page badge (except cover)
- [ ] Visual element (content slides)
- [ ] Left-aligned body text
- [ ] Title 36pt+ vs body 14-16pt
- [ ] Margins ≥ 0.5"
```

---

## 🎯 Best Practices

1. **Run verification AFTER each slide** - Don't batch validate
2. **Fix issues immediately** - Don't continue with broken slides
3. **Keep this checklist open** - Reference during creation
4. **Use automated tools** - `verify_layout.ts` catches 90% of issues
5. **Test in browser** - Some issues only visible when rendered

---

## 📚 Related References

- **Anti-patterns**: `references/anti-patterns.md` - What NOT to do
- **HTML Implementation**: `references/html-implementation.md` - Technical rules
- **SVG Guidelines**: `references/svg-guidelines.md` - SVG constraints
- **Design Styles**: `references/design-styles.md` - Style specifications