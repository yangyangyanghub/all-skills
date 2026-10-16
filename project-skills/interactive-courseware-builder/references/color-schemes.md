# Color Schemes

Six preset color schemes for different subjects. All use the same CSS variable
names — switching is a one-block `:root` replacement.

## Variable System

| Variable | Role | Typical Use |
|----------|------|-------------|
| `--primary` | Main color | Titles, navigation bar, chapter markers |
| `--primary-light` | Light main | Sub-titles, links, hover states |
| `--accent` | Accent | Buttons, highlights, active controls |
| `--accent-soft` | Soft accent | Tag backgrounds, inactive controls |
| `--ink` | Body text | Main body text color |
| `--paper` | Background | Page background |
| `--paper-2` | Card | Info cards, panel backgrounds |
| `--line` | Divider | Separator lines, borders |
| `--green` | Success | Correct answers, pass indicators |
| `--red` | Error | Wrong answers, warning markers |
| `--shadow` | Shadow | Card/popup drop shadows |

---

## Scheme A · Deep Blue Academic

For: Math, Physics, Chemistry, Computer Science.

```css
:root {
  --primary: #1A3A5C; --primary-light: #3A7DC8;
  --accent: #E8832A; --accent-soft: #F5C282;
  --ink: #2C2C2C; --paper: #FAFAFA; --paper-2: #EEEEEE;
  --line: #D0D0D0; --green: #2E7D32; --red: #C62828;
  --shadow: 0 4px 20px rgba(0,0,0,.08);
}
```

---

## Scheme B · Sapphire Tech

For: Math, Physics, Chemistry, Computer Science.

```css
:root {
  --primary: #1565C0; --primary-light: #42A5F5;
  --accent: #00ACC1; --accent-soft: #80DEEA;
  --ink: #263238; --paper: #F5F7FA; --paper-2: #E3F2FD;
  --line: #CFD8DC; --green: #43A047; --red: #E53935;
  --shadow: 0 4px 20px rgba(0,0,0,.06);
}
```

---

## Scheme C · Crimson Gold

For: History, Chinese, Politics, Social Studies.

```css
:root {
  --primary: #C8102E; --primary-light: #E57373;
  --accent: #E6B422; --accent-soft: #F3D98B;
  --ink: #1F1A17; --paper: #FBF6EC; --paper-2: #F3E9D6;
  --line: #D9C9A8; --green: #2E7D32; --red: #B71C1C;
  --shadow: 0 8px 28px rgba(60,30,10,.12);
}
```

---

## Scheme D · Ink Wash

For: History, Chinese, Politics, Social Studies.

```css
:root {
  --primary: #2C2C2C; --primary-light: #616161;
  --accent: #D4453B; --accent-soft: #EF9A9A;
  --ink: #3A3A3A; --paper: #F8F4EC; --paper-2: #EFEBE3;
  --line: #D7CCC8; --green: #388E3C; --red: #C62828;
  --shadow: 0 4px 16px rgba(0,0,0,.08);
}
```

---

## Scheme E · Fresh Green

For: Biology, Geography.

```css
:root {
  --primary: #2E7D32; --primary-light: #66BB6A;
  --accent: #F9A825; --accent-soft: #FFF176;
  --ink: #2C2C2C; --paper: #FAFAF5; --paper-2: #E8F5E9;
  --line: #C8E6C9; --green: #43A047; --red: #E53935;
  --shadow: 0 4px 20px rgba(0,0,0,.06);
}
```

---

## Scheme F · Earth Warm

For: Biology, Geography.

```css
:root {
  --primary: #8D6E63; --primary-light: #BCAAA4;
  --accent: #FF8F00; --accent-soft: #FFE082;
  --ink: #3E2723; --paper: #FFF8F0; --paper-2: #FBE9E7;
  --line: #D7CCC8; --green: #00897B; --red: #D84315;
  --shadow: 0 4px 16px rgba(62,39,35,.08);
}
```

---

## Universal Visual Standards

All schemes share these standards:

- **Font stack**: `"Noto Serif SC","Songti SC",STSong,"Microsoft YaHei",serif`
- **Code font**: `"JetBrains Mono","Consolas",monospace`
- **Minimum text size**: 20px (classroom visibility)
- **Title**: 32–40px bold
- **Body**: 20–24px
- **Notes**: 16px
- **Touch target**: ≥44×44px on mobile
- **Responsive breakpoint**: `@media(max-width:768px)` — single column, touch-friendly
