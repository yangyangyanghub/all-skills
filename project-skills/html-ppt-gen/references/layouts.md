# Layout Directory

31 page layout templates for HTML presentation slides. Each layout is a structural pattern — independent of theme — for arranging content within a 960×540px slide.

---

## Structural Pages

Core pages that define the presentation skeleton.

| layout | purpose | when to use |
|---|---|---|
| `cover` | Opening slide with title, subtitle, and visual anchor | Always the first slide; sets tone for entire deck |
| `toc` | Table of contents with numbered sections | After cover, whenever deck has 3+ sections |
| `section-divider` | Bold typographic transition between major parts | Before entering each new section or chapter |
| `thanks` | Closing slide with takeaway summary or contact info | Always the last slide; reinforces key message |

---

## Text & List Layouts

For presenting written content with visual hierarchy.

| layout | purpose | when to use |
|---|---|---|
| `bullets` | Standard numbered/bulleted list with icon accents | 3–6 key points; most common content layout |
| `big-quote` | Oversized quotation or statement, centered | Highlight a key insight, customer quote, or mission statement |
| `todo-checklist` | Checkbox-style list with progress indicators | Task lists, project status, sprint planning |
| `comparison` | Side-by-side comparison in two panels or cards | A vs B analysis, before vs after, old vs new |
| `pros-cons` | Two-color column layout (green/red or +/−) | Evaluating options, listing advantages and disadvantages |

---

## Column Layouts

For multi-column content arrangement.

| layout | purpose | when to use |
|---|---|---|
| `two-column` | 50/50 split: text on one side, visual on the other | Image + caption, definition + example, concept + illustration |
| `three-column` | Three equal columns for parallel content | Three features, three pillars, three-step frameworks |
| `kpi-grid` | Grid of 4–6 metric cards with large numbers and labels | Dashboard-style overview, monthly KPI summary |

---

## Data & Table Layouts

For structured, tabular, or numerical data.

| layout | purpose | when to use |
|---|---|---|
| `table` | Classic data table with alternating row colors | Financial data, comparison matrices, spec sheets |
| `stat-highlight` | One or three oversized statistic numbers with labels | "95% accuracy" type moments; single-metric callouts |
| `chart-bar` | Horizontal or vertical bar chart (inline SVG) | Ranking data, categorical comparisons, survey results |
| `chart-line` | Line chart showing trends over time (inline SVG) | Growth metrics, time-series data, stock-like trends |
| `chart-pie` | Pie or donut chart (generated as image) | Market share, budget breakdown, part-to-whole ratios |
| `chart-radar` | Radar/spider chart for multi-dimensional scoring | Skill comparisons, product feature matrices |

---

## Code & Terminal Layouts

For technical content and code demonstrations.

| layout | purpose | when to use |
|---|---|---|
| `code` | Syntax-highlighted code block with monospace font | Showing code snippets, configuration examples, API calls |
| `diff` | Side-by-side before/after with green/red highlighting | Code reviews, refactoring explanations, migration guides |
| `terminal` | Faux-terminal window with command prompt and output | CLI demos, shell commands, server logs, installation steps |

---

## Process & Timeline Layouts

For sequential or time-based information.

| layout | purpose | when to use |
|---|---|---|
| `flow-diagram` | Left-to-right or top-to-bottom flow with arrow connectors | System architecture, data pipelines, user journeys |
| `timeline` | Horizontal or vertical timeline with labeled milestones | Company history, product roadmap, project milestones |
| `roadmap` | Quarterly or phased roadmap with status indicators (✓/in progress/TODO) | Product strategy, project planning, OKR tracking |
| `process-steps` | Numbered step sequence (1→2→3→4) with short descriptions | How-to guides, methodology explanations, onboarding flows |
| `gantt` | Gantt chart with horizontal bars showing task durations and overlaps | Project management, resource allocation, sprint planning |
| `mindmap` | Central concept with branching sub-concepts | Brainstorming sessions, idea maps, topic breakdowns |
| `arch-diagram` | Architecture diagram with layered boxes and connectivity lines | System design, infrastructure overview, microservice topology |

---

## Image Layouts

For visual-first content.

| layout | purpose | when to use |
|---|---|---|
| `image-hero` | Full-bleed hero image with minimal overlay text | Product showcase, portfolio opening, brand statement |
| `image-grid` | 2×2 or 3×2 grid of images with captions | Photo gallery, product line-up, case study examples |

---

## Action Layouts

For driving engagement or closing.

| layout | purpose | when to use |
|---|---|---|
| `cta` | Call-to-action with prominent button-style element and supporting text | Sales pitch ending, signup prompts, campaign launches |
| `todo-checklist` | (Also listed under Text — see above) | Reused for action-item follow-up lists |

---

## Layout Selection Guide

### By Slide Type

| Slide Type | Recommended Layouts |
|---|---|
| **Cover** | `cover`, `image-hero` |
| **Table of Contents** | `bullets`, `three-column`, `kpi-grid` (for numbered sections) |
| **Section Divider** | `section-divider`, `big-quote` |
| **Content — Text** | `bullets`, `big-quote`, `two-column`, `todo-checklist` |
| **Content — Data** | `table`, `stat-highlight`, `kpi-grid`, `chart-bar`, `chart-line`, `chart-pie`, `chart-radar` |
| **Content — Code** | `code`, `diff`, `terminal` |
| **Content — Image** | `image-hero`, `image-grid`, `two-column` |
| **Content — Process** | `flow-diagram`, `timeline`, `roadmap`, `process-steps`, `gantt`, `mindmap`, `arch-diagram` |
| **Comparison** | `comparison`, `pros-cons` |
| **Summary / Closing** | `thanks`, `cta`, `kpi-grid`, `todo-checklist` |

### Content Volume Rules

| Content Type | Rule | Layout Choice |
|---|---|---|
| ≤ 4 items | Keep on one slide | `bullets`, `kpi-grid` |
| 5–8 items | Split into two slides | Use `two-column` + `two-column` |
| 9+ items | Use tabbed/sequential approach | `timeline` or `roadmap` |
| Single powerful stat | Full impact | `stat-highlight` |
| Single powerful quote | Typographic focus | `big-quote` |
| Complex comparison | Clear delineation | `comparison` or `pros-cons` |

### Quick Rules

1. **Never repeat the same layout twice in a row** — alternate between column, list, and visual layouts
2. **Body text ≤ 6 bullet points** — split into multiple slides if exceeding
3. **Tables ≤ 8 rows** — beyond that, paginate across multiple slides
4. **Image-first slides need minimal text** — let visuals do the heavy lifting
5. **Code slides: show only relevant lines** — hide boilerplate, highlight key changes
6. **Charts must include source line** — always add "Source: XXX" at bottom
