# Icon Systems Reference

Guidance for selecting, configuring, and resolving conflicts between icon systems in frontend projects.

## Supported Icon Sources

### 1. Lucide Icons

**URL**: https://lucide.dev/

**Best for**: Modern, clean interfaces; consistent with shadcn/ui ecosystem

**Pros**:
- Clean, consistent design language
- Tree-shakeable (import only what you use)
- Active maintenance
- SVG-based, scalable

**Cons**:
- Smaller set than some alternatives (~1000 icons)
- May lack niche/specific icons

**Naming Convention**:
```
lucide-{name}
Examples: lucide-home, lucide-settings, lucide-user
```

**Design note**:
- Prefer this source when the product needs a calm, modern baseline icon language with broad UI coverage.

---

### 2. Heroicons

**URL**: https://heroicons.com/

**Best for**: Tailwind CSS projects; simple, friendly aesthetic

**Pros**:
- Created by Tailwind Labs
- Three styles: outline, solid, mini
- Consistent with Tailwind design philosophy
- Optimized SVGs

**Cons**:
- Smaller set (~300 icons)
- Limited niche categories

**Naming Convention**:
```
heroicons-{style}-{name}
Examples: heroicons-outline-home, heroicons-solid-settings
```

**Design note**:
- Use when the interface benefits from a friendlier icon tone or when outline/solid contrast is part of the visual language.

---

### 3. Ant Design Icons

**URL**: https://ant.design/components/icon/

**Best for**: Ant Design ecosystem; enterprise applications

**Pros**:
- Large, comprehensive set
- Consistent with Ant Design system
- Good coverage of business/domain icons
- Supports icon font and SVG

**Cons**:
- Heavier bundle size if using all icons
- Distinctive style may not fit all projects

**Naming Convention**:
```
antd-{name}
Examples: antd-home, antd-setting, antd-dashboard
```

**Design note**:
- Use when the product needs stronger enterprise/business semantics and broader coverage for operational concepts.

---

### 4. Iconfont.cn

**URL**: https://www.iconfont.cn/

**Best for**: Chinese projects; custom icon sets; when you need specific icons

**Pros**:
- Massive collection (Chinese and international icons)
- Ability to create custom icon projects
- Font and SVG support
- Free for commercial use

**Cons**:
- Primarily Chinese language interface
- Variable quality
- May need VPN in some regions

**Naming Convention**:
```
iconfont-{project}-{name}
Examples: iconfont-custom-logo, iconfont-app-home
```

**Design note**:
- Treat as a fallback or legacy-oriented source unless the existing product language already depends on it.

---

### 5. Custom SVG Icons

**Best for**: Brand-specific icons; unique requirements

**Pros**:
- Full control over design
- Perfect brand alignment
- No external dependencies

**Cons**:
- Maintenance burden
- Must ensure consistency
- Accessibility responsibility

**Naming Convention**:
```
custom-{category}-{name}
Examples: custom-brand-logo, custom-nav-dashboard
```

---

## Icon Conflict Resolution

### Problem
Projects often accumulate icons from multiple sources, leading to:
- Inconsistent visual styles
- Naming collisions
- Bundle size bloat
- Confusion about which icon to use

### Conflict Detection Rules

Detect conflicts before selecting a primary library or writing migration notes.

#### Detection Inputs

Create a simple inventory table with one row per icon candidate:

| Field | Required | Example |
|------|----------|---------|
| `source` | Yes | `lucide`, `heroicons-outline`, `custom-brand` |
| `raw_name` | Yes | `home`, `cog`, `logo` |
| `usage_context` | Yes | `sidebar nav`, `settings action`, `brand header` |
| `status` | Yes | `active`, `legacy`, `proposed` |

#### Canonical Name Rule

Normalize each candidate to a canonical comparison key before checking conflicts:

1. Convert to lowercase
2. Replace spaces and underscores with hyphens
3. Remove source-specific suffix noise when it does not change meaning
   - Example: `home-icon` → `home`
   - Example: `settings-filled` stays `settings-filled` because style is meaningful
4. Keep semantic modifiers that change usage
   - Example: `arrow-left` and `chevron-left` are NOT the same icon

#### What Counts as a Conflict

A conflict exists when **the same canonical icon purpose appears from different sources** and at least one of the following is true:

1. **Same name, different source**
   - Example: `home` exists in Lucide and Heroicons
2. **Same usage context, different source**
   - Example: sidebar navigation uses `lucide-home` in one screen and `heroicons-outline-home` in another
3. **Same semantic role, custom asset overlaps library asset**
   - Example: `custom-nav-dashboard` and `lucide-layout-dashboard` both represent the dashboard entry
4. **Same source family used with multiple style variants without an explicit rule**
   - Example: `heroicons-outline-home` and `heroicons-solid-home` both appear in primary navigation

#### What Does NOT Count as a Conflict

- Different icons for different semantics (`user` vs `users`)
- Intentional brand exceptions (`custom-brand-logo`)
- Intentional platform exceptions (`social-github`, `flag-cn`)
- Temporary migration overlap that is explicitly marked `legacy`

#### Minimum Detection Output

If any conflict is found, the design document or review note must record:

- canonical name
- all conflicting sources
- affected usage contexts
- proposed primary source
- whether a rename or replacement is required

### Resolution Strategy: Prefix-Based Namespacing

Use prefixes to make the selected source explicit in names, review notes, and migration tables.

**Step 1**: Identify all icon sources in use
**Step 2**: Detect conflicts using canonical names and usage context
**Step 3**: Choose primary source (usually 1, maximum 2)
**Step 4**: Apply consistent prefixing:

```
Primary: lucide-* (default for generic product UI)
Secondary: custom-* (reserved for brand-specific icons)
Legacy: iconfont-* (retained only during transition)
```

**Step 5**: Document exceptions:
```
EXCEPTIONS:
- Logo icons: always custom-brand-*
- Flags: use flag-{country} convention
- Social icons: use social-{platform}
```

### Resolution Rules

1. **One canonical winner per semantic slot**
   - For each conflicting canonical name, choose one source as the active source of truth.
   - Do not keep two active icons for the same semantic slot.
2. **Keep source prefix in planning artifacts**
   - Use fully qualified names such as `lucide-home`, `heroicons-outline-home`, `custom-brand-logo`.
   - This keeps design discussions and review notes unambiguous.
3. **Primary library wins common UI semantics**
   - Navigation, actions, status, and generic product UI should come from the primary library.
4. **Custom prefix is reserved for brand or product-specific meaning**
   - Use `custom-*` only when no library icon matches the required meaning or the asset is brand-owned.
5. **Legacy prefixes are transitional, not permanent**
   - `iconfont-*` or other legacy prefixes must be marked for replacement or explicit exemption.
6. **Do not resolve conflict by mixing styles silently**
   - If outline vs solid is intentional, document the rule by context.
   - If no rule exists, treat it as a conflict and standardize.

### Prefix Strategy by Source

| Source type | Prefix rule | Example | Notes |
|------------|-------------|---------|-------|
| Primary library | `{source}-{name}` in docs and reports | `lucide-home` | Canonical choice for generic UI |
| Secondary approved library | `{source}-{name}` always retained | `heroicons-outline-home` | Allowed only for documented exception zones |
| Custom asset | `custom-{category}-{name}` | `custom-brand-logo` | Reserve for brand or domain-specific meaning |
| Legacy source | `legacy-{source}-{name}` or existing source prefix | `legacy-iconfont-home` | Must include migration note |

### Resolution Examples

#### Example 1: Same Name, Different Source

Conflict:

| Canonical name | Source | Current name | Usage |
|---------------|--------|--------------|-------|
| `home` | Lucide | `lucide-home` | Sidebar nav |
| `home` | Heroicons | `heroicons-outline-home` | Header breadcrumb |

Resolution:

- Choose `lucide-home` as the primary icon because navigation already uses Lucide.
- Replace `heroicons-outline-home` in product UI.
- Record Heroicons as `disallowed for generic nav semantics`.

#### Example 2: Library Icon vs Custom Asset

Conflict:

| Canonical name | Source | Current name | Usage |
|---------------|--------|--------------|-------|
| `dashboard` | Lucide | `lucide-layout-dashboard` | App navigation |
| `dashboard` | Custom | `custom-nav-dashboard` | Marketing screenshot badge |

Resolution:

- Keep `lucide-layout-dashboard` for application navigation.
- Rename the custom asset to `custom-badge-dashboard-overview` if it is truly a marketing badge.
- If the custom asset is intended for the same nav slot, replace it instead of keeping both.

#### Example 3: Same Source Family, Different Style Variant

Conflict:

| Canonical name | Source | Current name | Usage |
|---------------|--------|--------------|-------|
| `settings` | Heroicons | `heroicons-outline-cog` | Table action |
| `settings` | Heroicons | `heroicons-solid-cog` | Toolbar action |

Resolution:

- Define a rule such as `outline for default actions, solid only for selected state`.
- If no rule is needed, standardize to one style and remove the other.

### Conflict Report Format

When a project has 1 or more conflicts, produce a conflict report section in Markdown.

#### Required Structure

```markdown
## Icon Conflict Report

| Canonical name | Sources | Usage contexts | Decision | Resolved name(s) | Action | Rationale |
|---------------|---------|----------------|----------|------------------|--------|-----------|
| home | lucide, heroicons-outline | sidebar nav; header breadcrumb | lucide is primary | lucide-home | replace heroicons-outline-home | matches existing app navigation style |

### Exceptions
- custom-brand-logo: brand-owned asset, exempt from replacement

### Migration Notes
- Replace legacy iconfont-* entries during next navigation refactor
```

#### Field Definitions

| Field | Meaning |
|------|---------|
| `Canonical name` | Normalized semantic key used for conflict detection |
| `Sources` | All conflicting icon sources |
| `Usage contexts` | Where each icon currently appears |
| `Decision` | Chosen source of truth or exception |
| `Resolved name(s)` | Final prefixed name(s) to document |
| `Action` | `keep`, `replace`, `rename`, `exempt`, or `deprecate` |
| `Rationale` | Why this decision fits the design system |

#### Action Meanings

- `keep`: already aligned with the chosen source
- `replace`: swap to the chosen source
- `rename`: keep the asset but move it to a non-conflicting semantic name
- `exempt`: allow the conflict because of a documented exception
- `deprecate`: leave temporarily during migration, but do not use in new UI

#### Example Conflict Report

```markdown
## Icon Conflict Report

| Canonical name | Sources | Usage contexts | Decision | Resolved name(s) | Action | Rationale |
|---------------|---------|----------------|----------|------------------|--------|-----------|
| home | lucide, heroicons-outline | sidebar nav; header breadcrumb | use Lucide for generic product navigation | lucide-home | replace heroicons-outline-home | Lucide already defines the app navigation language |
| logo | custom-brand, lucide | header brand; onboarding card | custom-brand is exempt | custom-brand-logo | exempt | brand asset must preserve trademark shape |
| settings | heroicons-outline, heroicons-solid | table action; toolbar action | keep outline as default, solid only for selected state | heroicons-outline-cog; heroicons-solid-cog-selected | rename | style difference is meaningful only in selected state |
```

### Decision Criteria

When choosing between icon sources, consider:

| Criterion | Weight | Evaluation |
|-----------|--------|------------|
| Visual consistency | High | Does it match the design system? |
| Icon coverage | High | Does it have all needed icons? |
| Bundle size | Medium | Impact on performance? |
| Maintenance | Medium | Is it actively maintained? |
| Ecosystem | Low | Does it match your framework? |

### Migration Path

**From multiple sources to single source**:

1. **Inventory**: List all icons in use
2. **Map**: Create mapping table (old → new)
3. **Replace**: Update icon selections in design specs and decision records
4. **Document**: Record decisions in DESIGN.md
5. **Deprecate**: Mark old icon sources as disallowed for new UI work

**Example mapping**:
```
OLD                    → NEW
lucide-home           → lucide-home (keep)
heroicons-outline-cog → lucide-settings (replace)
antd-dashboard        → lucide-layout-dashboard (replace)
```

---

## Icon Usage Guidelines

### Size Scale

| Token | Size | Usage |
|-------|------|-------|
| xs | 12px | Inline with text, compact UI |
| sm | 16px | Buttons, list items |
| md | 20px | Default size, navigation |
| lg | 24px | Emphasis, standalone icons |
| xl | 32px | Feature highlights, empty states |
| 2xl | 48px | Hero sections, large CTAs |

### Color Rules

**Default**: Inherit from text color (`currentColor`)

**Explicit colors**:
- Primary actions may use the main accent color.
- Muted/supporting icons should align with secondary text tone.
- Success/error colors should be reserved for icons that communicate state, not decoration.

### Accessibility

- Always provide `aria-label` for standalone icons
- Use `aria-hidden="true"` for decorative icons
- Ensure minimum touch target (44×44px for interactive icons)
- Maintain sufficient contrast (4.5:1 minimum)

### Stroke Width

Keep consistent stroke width across icon set:
- **Lucide**: 1.5-2px
- **Heroicons**: 1.5px (outline), fill (solid)
- **Ant Design**: 1px

---

## Icon System Section in DESIGN.md

When documenting icon choices, keep the section focused on design decisions rather than setup details:

```markdown
## Icon System

### Primary Library
**Lucide Icons**
- Rationale: clean, modern, and consistent for generic product UI

### Secondary Sources
- **Custom SVG**: Brand logos, custom icons
  - Naming: custom-{name}
- **Legacy sources**: allowed only when explicitly documented as transitional

### Icon Standards
- Size scale: sm(16), md(20), lg(24)
- Color: currentColor (inherit from text)
- Stroke width: keep visually consistent within the chosen family

### Exceptions
- Brand marks may remain custom
- Country flags and other specialist symbol sets require a documented exception rule
```

---

*Reference for frontend-design-orchestrator skill*
