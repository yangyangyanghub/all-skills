# HTML Presentation Generator - Tools

This directory contains automated tools for generating, verifying, and deploying HTML presentations.

## Installation

```bash
npm install
# or
bun install

# Install Playwright browsers (for screenshot tool)
npx playwright install chromium
```

## Available Tools

### 1. generate_image.ts - Image Generation

Generate images for slides using baoyu-image-gen skill.

**Usage:**
```bash
bun scripts/generate_image.ts --prompt "A cat on a rooftop" --output slides/imgs/cat.png --ar 16:9 --quality 2k --provider google
```

**Options:**
- `--prompt, -p`: Image description (required)
- `--output, -o`: Output file path (required)
- `--ar`: Aspect ratio (default: 16:9, options: 1:1, 16:9, 9:16, 4:3, 3:4, 2.35:1)
- `--quality`: Quality preset (default: 2k, options: normal, 2k)
- `--provider`: AI provider (default: google, options: google, openai, dashscope, replicate)
- `--model, -m`: Specific model ID

**Examples:**
```bash
# Cover image (16:9 landscape)
bun scripts/generate_image.ts -p "Modern city skyline at sunset, cinematic" -o slides/imgs/cover.png --ar 16:9

# Portrait image (9:16)
bun scripts/generate_image.ts -p "A woman in a red dress" -o slides/imgs/portrait.png --ar 9:16

# Square image (1:1)
bun scripts/generate_image.ts -p "Logo design for tech company" -o slides/imgs/logo.png --ar 1:1
```

---

### 2. screenshot_html.ts - HTML Screenshot

Take high-quality screenshots of HTML slides using Playwright.

**Usage:**
```bash
bun scripts/screenshot_html.ts --html slides/slide-01.html --output slides/screenshots/slide-01.png
```

**Options:**
- `--html, -h`: Path to HTML file (required)
- `--output, -o`: Output screenshot path (optional, defaults to HTML path with .png extension)
- `--width, -w`: Viewport width (default: 960)
- `--height`: Viewport height (default: 540)
- `--full-page`: Capture full page instead of viewport

**Examples:**
```bash
# Standard slide screenshot
bun scripts/screenshot_html.ts --html slides/slide-01.html

# Custom dimensions
bun scripts/screenshot_html.ts --html slides/slide-01.html --width 1920 --height 1080

# Full page capture
bun scripts/screenshot_html.ts --html slides/slide-01.html --full-page
```

---

### 3. verify_layout.ts - Layout Verification

Automatically verify slide layout for common issues.

**Usage:**
```bash
bun scripts/verify_layout.ts --html slides/slide-01.html --type cover
bun scripts/verify_layout.ts --html slides/slide-02.html --type content --page-type text
```

**Options:**
- `--html, -h`: Path to HTML file (required)
- `--type, -t`: Slide type (required, options: cover, toc, divider, content, summary)
- `--page-type`: Content page subtype (for content slides: text, mixed, data, comparison, timeline, image)
- `--screenshot, -s`: Screenshot path for visual verification (optional)

**Checks performed (14 total):**

**Core Requirements (9 checks):**
- ✓ Slide content container (.slide-content)
- ✓ Correct dimensions (960×540px)
- ✓ Times New Roman font
- ✓ Page number badge (except cover)
- ✓ No gradients
- ✓ No animations
- ✓ Inline CSS only (except scaling snippet)
- ✓ SVG path constraints (M/L/H/V/Z only)
- ✓ Type-specific requirements (cover image, visual elements)

**Anti-Pattern Checks (5 checks):**
- ✓ No accent lines under titles
- ✓ Body text alignment (left-aligned, not centered)
- ✓ Bullet point count (≤ 6 recommended)
- ✓ Title size hierarchy (≥ 36px for contrast)
- ✓ No emojis as icons (use SVG instead)

**Output:**
```json
{
  "passed": true,
  "checks": [
    { "name": "Slide content container", "passed": true, "details": "✓ .slide-content div found" },
    ...
  ],
  "issues": [],
  "suggestions": []
}
```

---

### 4. deploy_presentation.ts - Deployment

Merge all slides into a deployable presentation package with navigation.

**Usage:**
```bash
bun scripts/deploy_presentation.ts --slides ./slides --output ./dist --title "My Presentation"
```

**Options:**
- `--slides, -s`: Directory containing slide HTML files (required)
- `--output, -o`: Output directory for deployed presentation (required)
- `--title, -t`: Presentation title (optional, default: "Presentation")

**What it does:**
1. Copies all slide HTML files to output directory
2. Copies images directory if exists
3. Creates `index.html` with slide navigation
4. Creates `navigation.js` for keyboard navigation

**Output:**
```
dist/
├── index.html           # Main presentation viewer
├── navigation.js        # Navigation controls
├── slide-01.html        # Individual slides
├── slide-02.html
├── ...
└── imgs/                # Images directory
    ├── cover.png
    └── ...
```

**Keyboard controls:**
- `→` or `Space`: Next slide
- `←`: Previous slide
- `1-9`: Jump to slide number

---

## Workflow Integration

These tools are designed to work together in the presentation generation workflow:

### Step 1: Generate Images
```bash
# Generate cover image
bun scripts/generate_image.ts -p "Healthcare AI theme" -o slides/imgs/cover.png --ar 16:9

# Generate content images
bun scripts/generate_image.ts -p "Medical diagnosis illustration" -o slides/imgs/diagnosis.png
```

### Step 2: Create HTML Slides
Follow the SKILL.md guidelines to create HTML slide files in `slides/` directory.

### Step 3: Verify Layout
```bash
# Verify each slide
bun scripts/verify_layout.ts --html slides/slide-01.html --type cover
bun scripts/verify_layout.ts --html slides/slide-02.html --type content --page-type text
```

### Step 4: Take Screenshots (optional)
```bash
bun scripts/screenshot_html.ts --html slides/slide-01.html --output screenshots/slide-01.png
```

### Step 5: Deploy
```bash
bun scripts/deploy_presentation.ts --slides ./slides --output ./dist --title "AI in Healthcare"
```

---

## Requirements

- Node.js 18+ or Bun
- Playwright (for screenshot tool): `npx playwright install chromium`
- baoyu-image-gen skill (for image generation)

## Environment Variables

Image generation requires API keys:

```bash
# Google (default)
export GOOGLE_API_KEY="your-key"

# OpenAI
export OPENAI_API_KEY="your-key"

# DashScope (阿里云)
export DASHSCOPE_API_KEY="your-key"

# Replicate
export REPLICATE_API_TOKEN="your-token"
```

## Troubleshooting

### "Playwright not found"
```bash
npx playwright install chromium
```

### "Image generation failed"
- Check API key is set correctly
- Verify prompt length (< 1500 characters)
- Ensure output directory exists

### "Screenshot black/blank"
- HTML file must contain `.slide-content` element
- Check for JavaScript errors in HTML
- Verify file path is correct

### "Verification failed"
- Check the specific checks that failed
- Review suggestions in output
- Consult SKILL.md for detailed requirements