# Design Sources Reference

This document catalogs external design resources and their appropriate usage boundaries for the frontend-design-orchestrator skill.

## Awesome Design MD

**URL**: https://github.com/VoltAgent/awesome-design-md

### What It Is
A curated collection of DESIGN.md files from real-world projects. These serve as:
- **Reference patterns** for structure and organization
- **Inspiration** for visual direction and interface patterns
- **Validation** against industry standards

### How to Use
1. **Browse**, don't copy. Use samples to understand structure, not to duplicate content.
2. **Extract patterns**. Note common sections, naming conventions, and organizational approaches.
3. **Adapt, don't adopt**. Tailor patterns to your specific project needs.

### Recommended Samples

#### SaaS Dashboard Design
- **Style**: Clean, data-dense, professional
- **Good for**: Admin panels, analytics dashboards, B2B applications
- **Key sections**: Data visualization, table layouts, filter patterns

#### E-commerce Product Page
- **Style**: Conversion-focused, image-heavy, trust signals
- **Good for**: Product detail pages, checkout flows, shopping carts
- **Key sections**: Image galleries, pricing displays, CTA patterns

#### Landing Page Design
- **Style**: Bold, single-purpose, scroll-driven
- **Good for**: Marketing sites, product launches, campaign pages
- **Key sections**: Hero sections, feature grids, social proof

### Boundaries
- **DO** use for structural inspiration and pattern recognition
- **DO NOT** copy entire sections verbatim without adaptation
- **DO NOT** assume all samples follow current best practices (check dates)

---

## UI Skills

**URL**: https://ui-skills.com/

### What It Is
An aggregation of skills and resources for UI/UX design.

### How to Use
1. **Discover tools**. Find specialized design tools and resources.
2. **Learn techniques**. Access tutorials and best practice guides.
3. **Stay current**. Check for emerging design patterns and trends.

### Boundaries
- **DO** use as a discovery resource for tools and techniques
- **DO NOT** treat as authoritative source without verification
- **DO NOT** rely on it for core skill functionality (may require network)

---

## Style Examples

### Minimalism
```
Visual Theme: Minimalist
- Clean whitespace (generous margins, 40-80px section spacing)
- Monochrome or limited color palette (2-3 colors max)
- Sans-serif typography, single font family
- Flat design, no shadows or gradients
- Focus on content over decoration

Use when: Content clarity is paramount, luxury/premium positioning,
          readability-focused applications
```

### Glassmorphism
```
Visual Theme: Glassmorphism
- Translucent surfaces with soft blur and layered depth
- Subtle light borders that separate surfaces without heavy framing
- Floating layers with depth
- Light, airy feel
- Often combined with vibrant gradient backgrounds

Use when: Modern, tech-forward aesthetic desired, dashboard UIs,
          overlay-heavy interfaces

Caution: Validate readability and hierarchy so the effect does not overpower content
```

### Brutalism
```
Visual Theme: Brutalism
- High contrast (pure black/white, neon accents)
- System fonts, bold typography
- Exposed grid lines and borders
- Unexpected layouts, broken grids
- Raw, unpolished aesthetic

Use when: Artistic/creative projects, standing out from standard SaaS look,
          making a bold statement

Caution: Accessibility challenges with high contrast, test thoroughly
```

---

## External Resource Guidelines

### Network Dependency
- **Core workflow**: Must work offline. Do not require network access for basic skill functionality.
- **Enhanced workflow**: Network-only browsing or inspiration gathering is optional and must never block core design reasoning.

### Attribution
- Always attribute external sources when referencing specific designs
- Note version/dates for resources that may evolve

### Currency
- Design trends change rapidly
- Verify external resources are current before applying
- Prefer timeless patterns over trendy implementations

---

## Quick Reference

| Resource | Type | Offline OK | Use For |
|----------|------|------------|---------|
| awesome-design-md | Pattern library | Yes (if cloned) | Structure inspiration |
| ui-skills.com | Tool directory | No | Discovery |
| Material Design | Guidelines | Yes (if cached) | Component patterns |
| Tailwind UI | Pattern library | Yes (if purchased) | Visual pattern inspiration |

---

*Reference for frontend-design-orchestrator skill*
