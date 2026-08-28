# Anti-Patterns System

Anti-patterns are design choices that should be avoided. This document lists anti-patterns by industry, slide type, and universal rules.

---

## By Industry

### Tech & SaaS

**Avoid**:
- ❌ **Playful illustrations** - Tech audiences expect professionalism
- ❌ **Neon colors** - Distracts from technical content
- ❌ **Handwritten fonts** - Undermines credibility
- ❌ **Dark mode with low contrast** - Hard to read in presentations
- ❌ **Too many animations** - Distracts from technical points

**Better**:
- ✅ Clean, geometric designs
- ✅ Cool color palettes (blue, gray, navy)
- ✅ Modern sans-serif fonts (Arial, Helvetica)
- ✅ Data visualization focus

---

### Finance & Banking

**Avoid**:
- ❌ **AI purple/pink gradients** - Trendy but inappropriate for finance
- ❌ **Playful icons or emojis** - Undermines trust
- ❌ **Bright, saturated colors** - Appears unprofessional
- ❌ **Informal language** - Finance requires formal tone
- ❌ **Complex animations** - Unnecessary distraction

**Better**:
- ✅ Conservative color palettes (navy, gray, gold accents)
- ✅ Professional, authoritative typography
- ✅ Clear data visualization
- ✅ Trust-building design elements

---

### Healthcare & Medical

**Avoid**:
- ❌ **Dark backgrounds** - Medical content needs clarity
- ❌ **Harsh animations** - Can be unsettling
- ❌ **Neon or saturated colors** - Inappropriate for medical context
- ❌ **Scary imagery** - Avoid alarming patients
- ❌ **Complex medical jargon** - Patients may not understand

**Better**:
- ✅ Soft, calming colors (soft blue, sage green, warm white)
- ✅ Clear, accessible typography
- ✅ Trust-building design
- ✅ Simple, clear explanations

---

### Education & Learning

**Avoid**:
- ❌ **Corporate stiffness** - Should feel approachable
- ❌ **Dense text blocks** - Overwhelms learners
- ❌ **Cold, impersonal colors** - Discourages engagement
- ❌ **Complex terminology** - Confuses beginners
- ❌ **No visual breaks** - Fatiguing to read

**Better**:
- ✅ Friendly, approachable design
- ✅ Warm color palettes
- ✅ Visual variety and breaks
- ✅ Clear step-by-step structure

---

### Creative & Design

**Avoid**:
- ❌ **Generic templates** - Should showcase creativity
- ❌ **Boring stock photos** - Contradicts creative brand
- ❌ **Safe, predictable layouts** - Fails to impress
- ❌ **Clashing fonts** - Shows poor design sense
- ❌ **Inconsistent style** - Undermines portfolio

**Better**:
- ✅ Bold, unique design choices
- ✅ High-quality visuals
- ✅ Experimental layouts
- ✅ Strong visual identity

---

### Executive & Corporate

**Avoid**:
- ❌ **Too much detail** - Executives want summaries
- ❌ **Small fonts** - Hard to read from distance
- ❌ **Playful elements** - Undermines authority
- ❌ **Long paragraphs** - Executives scan, don't read
- ❌ **Weak visual hierarchy** - Key points get lost

**Better**:
- ✅ Clear, bold headlines
- ✅ Maximum 3-5 bullet points
- ✅ Strong visual hierarchy
- ✅ Minimal, focused content

---

## By Slide Type

### Cover Page

**Avoid**:
- ❌ **No image** - Cover slides MUST have visual impact
- ❌ **Too much text** - Title should dominate
- ❌ **Weak visual hierarchy** - Title < 72px
- ❌ **Busy background** - Competes with text
- ❌ **Missing title** - Cover must have clear purpose

**Better**:
- ✅ Strong background image or solid color
- ✅ Title 72-120px, bold
- ✅ Clear subtitle (28-40px)
- ✅ Minimal supporting text

---

### Table of Contents

**Avoid**:
- ❌ **Too many sections** - Max 5-7 sections
- ❌ **Missing section numbers** - Hard to navigate
- ❌ **Plain text only** - Add visual interest
- ❌ **Inconsistent formatting** - Confuses readers
- ❌ **No visual hierarchy** - All sections look equal

**Better**:
- ✅ Clear section numbers (01, 02...)
- ✅ Consistent formatting
- ✅ Optional one-line descriptions
- ✅ Visual markers or icons

---

### Section Divider

**Avoid**:
- ❌ **Small section numbers** - Should be dominant
- ❌ **Weak color contrast** - Numbers get lost
- ❌ **Too much text** - Keep it simple
- ❌ **Inconsistent style** - All dividers should match
- ❌ **Missing page badge** - Required on all but cover

**Better**:
- ✅ Section number 72-120px, bold
- ✅ Clear title (36-48px)
- ✅ Accent color for numbers
- ✅ Consistent style across all dividers

---

### Content Page

**Avoid**:
- ❌ **Plain text only** - MUST have visual element
- ❌ **Centered body text** - Left-align paragraphs
- ❌ **More than 6 bullets** - Overwhelming
- ❌ **Title < 36px** - Needs size contrast
- ❌ **No visual breaks** - Wall of text
- ❌ **Missing page badge** - Required

**Better**:
- ✅ Visual element (image/chart/icon/SVG)
- ✅ Left-aligned body text
- ✅ Title 36-44px, bold
- ✅ Body 14-16px, regular
- ✅ Clear visual hierarchy

---

### Summary / Closing

**Avoid**:
- ❌ **New information** - Summary = recap only
- ❌ **No call-to-action** - What should audience do?
- ❌ **Weak ending** - Should be memorable
- ❌ **Too many takeaways** - Max 5 key points
- ❌ **Missing page badge** - Required

**Better**:
- ✅ Clear key takeaways (3-5)
- ✅ Strong call-to-action
- ✅ Contact information (if applicable)
- ✅ Memorable closing

---

## Universal Anti-Patterns

### Typography

- ❌ **Emojis as icons** - Use SVG (Heroicons/Lucide)
- ❌ **More than 2 font families** - Stick to 1-2
- ❌ **All caps body text** - Hard to read
- ❌ **Justified text** - Creates rivers
- ❌ **Script fonts for body** - Unreadable at small sizes

### Color

- ❌ **Low contrast text** - Ratio < 4.5:1 for body
- ❌ **Too many colors** - Max 3-4 from palette
- ❌ **Vibrating color combinations** - Hard on eyes
- ❌ **Gradients** - Use solid colors only
- ❌ **Colors outside chosen palette** - Breaks consistency

### Layout

- ❌ **Accent lines under titles** - AI-generated cliché
- ❌ **Inconsistent margins** - Keep 0.5" minimum
- ❌ **Overlapping elements** - Poor planning
- ❌ **Text over busy images** - Readability issues
- ❌ **No whitespace** - Suffocating design

### Images & Graphics

- ❌ **Low-resolution images** - Pixelated looks unprofessional
- ❌ **Watermarked stock photos** - Unprofessional
- ❌ **Irrelevant images** - Must support content
- ❌ **Too many images** - Distracting
- ❌ **Stretched/distorted images** - Maintain aspect ratio

### SVG

- ❌ **Bézier curves (Q/C)** - Not supported in PPTX
- ❌ **Arc commands (A)** - Not supported in PPTX
- ❌ **SVG for photos** - Use raster images instead
- ❌ **Complex SVG illustrations** - Use GenerateImage
- ❌ **Text overlaid on SVG** - Lost in PPTX conversion

### Interactivity

- ❌ **Animations** - Static slides only
- ❌ **Hover effects** - Not functional in PPTX
- ❌ **Transitions** - Keep slides static
- ❌ **Video/audio** - Beyond scope
- ❌ **Hyperlinks** - May not work in all contexts

---

## Quick Reference: Top 10 Anti-Patterns

1. ❌ **Accent lines under titles** - Use whitespace or background color instead
2. ❌ **More than 6 bullet points** - Split into multiple slides
3. ❌ **Emojis as icons** - Use SVG from Heroicons or Lucide
4. ❌ **Gradients** - Use solid colors only
5. ❌ **Animations** - All slides must be static
6. ❌ **Centered body text** - Left-align paragraphs and lists
7. ❌ **Text over busy images** - Add overlay or simplify background
8. ❌ **Bézier curves/arcs in SVG** - Use M/L/H/V/Z only
9. ❌ **Title < 36px** - Needs contrast with 14-16px body
10. ❌ **Missing visual elements** - Every content slide needs images/charts/icons

---

## How to Use This Reference

**Before generating each slide**:
1. Check industry-specific anti-patterns
2. Check slide-type-specific anti-patterns
3. Run through universal anti-patterns
4. Verify against pre-delivery checklist

**When reviewing generated slides**:
1. Did you avoid all industry anti-patterns?
2. Did you avoid all slide-type anti-patterns?
3. Did you avoid the top 10 universal anti-patterns?
4. Does the slide pass the pre-delivery checklist?

**Remember**: Anti-patterns are design choices that consistently lead to poor outcomes. Following them does NOT guarantee success, but avoiding them prevents common mistakes.