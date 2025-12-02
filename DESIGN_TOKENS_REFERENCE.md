# Design Tokens Reference
## SuperStandard Multi-Agent Platform Design System v1.0

Quick visual reference for all design tokens (CSS custom properties)

---

## Color Tokens

### Primary Colors (Indigo)
```
--color-primary-900: #3730a3  ██████  Darkest - Emphasis text
--color-primary-800: #4338ca  ██████  Dark - Headers
--color-primary-700: #4f46e5  ██████  Main - Primary buttons, links
--color-primary-600: #6366f1  ██████  Medium - Hover states
--color-primary-500: #818cf8  ██████  Light - Accents
--color-primary-400: #a5b4fc  ██████  Pale - Backgrounds
--color-primary-300: #c7d2fe  ██████  Paler - Subtle backgrounds
--color-primary-200: #e0e7ff  ██████  Very pale - Hover backgrounds
--color-primary-100: #eef2ff  ██████  Lightest - Selected backgrounds
```

### Secondary Colors (Purple)
```
--color-secondary-900: #581c87  ██████  Darkest
--color-secondary-800: #6b21a8  ██████  Dark
--color-secondary-700: #7e22ce  ██████  Main
--color-secondary-600: #9333ea  ██████  Medium
--color-secondary-500: #a855f7  ██████  Light
--color-secondary-400: #c084fc  ██████  Pale
--color-secondary-300: #d8b4fe  ██████  Paler
--color-secondary-200: #e9d5ff  ██████  Very pale
--color-secondary-100: #f3e8ff  ██████  Lightest
```

### Neutral Colors (Grays)
```
--color-neutral-900: #18181b  ██████  Near black - Primary text
--color-neutral-800: #27272a  ██████  Very dark - Secondary text
--color-neutral-700: #3f3f46  ██████  Dark - Body text
--color-neutral-600: #52525b  ██████  Medium dark - Tertiary text
--color-neutral-500: #71717a  ██████  Medium - Placeholder text
--color-neutral-400: #a1a1aa  ██████  Medium light - Borders
--color-neutral-300: #d4d4d8  ██████  Light - Dividers
--color-neutral-200: #e4e4e7  ██████  Very light - Borders
--color-neutral-100: #f4f4f5  ██████  Pale - Backgrounds
--color-neutral-50:  #fafafa  ██████  Off white - Page background
--color-white:       #ffffff  ██████  Pure white
```

### Semantic Colors

#### Success (Green)
```
--color-success-700: #15803d  ██████  Dark
--color-success-600: #16a34a  ██████  Main - Buttons, text
--color-success-500: #22c55e  ██████  Medium
--color-success-400: #4ade80  ██████  Light - Icons
--color-success-100: #dcfce7  ██████  Background
```

#### Warning (Orange)
```
--color-warning-700: #c2410c  ██████  Dark
--color-warning-600: #ea580c  ██████  Main
--color-warning-500: #f97316  ██████  Medium
--color-warning-400: #fb923c  ██████  Light
--color-warning-100: #ffedd5  ██████  Background
```

#### Error (Red)
```
--color-error-700: #b91c1c  ██████  Dark
--color-error-600: #dc2626  ██████  Main
--color-error-500: #ef4444  ██████  Medium
--color-error-400: #f87171  ██████  Light
--color-error-100: #fee2e2  ██████  Background
```

#### Info (Blue)
```
--color-info-700: #0369a1  ██████  Dark
--color-info-600: #0284c7  ██████  Main
--color-info-500: #0ea5e9  ██████  Medium
--color-info-400: #38bdf8  ██████  Light
--color-info-100: #dbeafe  ██████  Background
```

### Data Visualization Colors
```
--color-chart-1:  #6366f1  ██████  Indigo
--color-chart-2:  #8b5cf6  ██████  Purple
--color-chart-3:  #ec4899  ██████  Pink
--color-chart-4:  #f59e0b  ██████  Amber
--color-chart-5:  #10b981  ██████  Emerald
--color-chart-6:  #06b6d4  ██████  Cyan
--color-chart-7:  #f97316  ██████  Orange
--color-chart-8:  #84cc16  ██████  Lime
--color-chart-9:  #6366f1  ██████  Indigo (repeat)
--color-chart-10: #14b8a6  ██████  Teal
```

---

## Typography Tokens

### Font Families
```css
--font-family-primary:  Inter, system-ui, sans-serif
--font-family-mono:     JetBrains Mono, SF Mono, monospace
--font-family-display:  Inter Display, Inter, system-ui
```

### Font Sizes
```
--font-size-xs:   0.75rem   (12px)  Labels, fine print
--font-size-sm:   0.875rem  (14px)  Body small, captions
--font-size-base: 1rem      (16px)  Body text
--font-size-md:   1.125rem  (18px)  Body large
--font-size-lg:   1.25rem   (20px)  H4
--font-size-xl:   1.5rem    (24px)  H3
--font-size-2xl:  1.875rem  (30px)  H2
--font-size-3xl:  2.25rem   (36px)  H1
--font-size-4xl:  3rem      (48px)  Display headings
--font-size-5xl:  3.75rem   (60px)  Hero text
```

### Font Weights
```
--font-weight-light:     300  Light text
--font-weight-normal:    400  Regular body text
--font-weight-medium:    500  Emphasized text
--font-weight-semibold:  600  Subheadings
--font-weight-bold:      700  Headings
--font-weight-extrabold: 800  Display text
```

### Line Heights
```
--line-height-tight:   1.25   Headings
--line-height-normal:  1.5    Body text
--line-height-relaxed: 1.75   Long-form content
```

### Letter Spacing
```
--letter-spacing-tight:  -0.025em  Large headings
--letter-spacing-normal:  0        Body text
--letter-spacing-wide:    0.025em  Buttons, labels
--letter-spacing-wider:   0.05em   Small caps
```

---

## Spacing Tokens

### Spacing Scale (8px base unit)
```
--spacing-0:   0        (0px)   No spacing
--spacing-1:   0.25rem  (4px)   Tight spacing
--spacing-2:   0.5rem   (8px)   Compact spacing
--spacing-3:   0.75rem  (12px)  Comfortable spacing
--spacing-4:   1rem     (16px)  Base spacing ⭐ Most used
--spacing-5:   1.25rem  (20px)  Medium spacing
--spacing-6:   1.5rem   (24px)  Spacious ⭐ Most used
--spacing-8:   2rem     (32px)  Large spacing
--spacing-10:  2.5rem   (40px)  Extra large
--spacing-12:  3rem     (48px)  Section spacing
--spacing-16:  4rem     (64px)  Page section
--spacing-20:  5rem     (80px)  Large sections
--spacing-24:  6rem     (96px)  Hero sections
```

**Common Uses**:
- **Buttons**: `padding: var(--spacing-3) var(--spacing-5)` (12px 20px)
- **Cards**: `padding: var(--spacing-6)` (24px)
- **Panels**: `padding: var(--spacing-5) var(--spacing-6)` (20px 24px)
- **Grid gaps**: `gap: var(--spacing-6)` (24px)
- **Section margins**: `margin-bottom: var(--spacing-8)` (32px)

---

## Border Radius Tokens
```
--radius-none:  0           Sharp corners
--radius-sm:    0.25rem     (4px)   Subtle rounding
--radius-base:  0.5rem      (8px)   Default rounding
--radius-md:    0.75rem     (12px)  Medium rounding ⭐ Most used
--radius-lg:    1rem        (16px)  Large rounding ⭐ Most used
--radius-xl:    1.5rem      (24px)  Extra large
--radius-2xl:   2rem        (32px)  Very large
--radius-full:  9999px              Pill/circular
```

**Common Uses**:
- **Buttons**: `var(--radius-md)` (12px)
- **Cards/Panels**: `var(--radius-lg)` (16px)
- **Input fields**: `var(--radius-md)` (12px)
- **Badges**: `var(--radius-full)` (pill shape)
- **Avatars**: `var(--radius-full)` (circular)

---

## Shadow Tokens

### Box Shadows
```
--shadow-xs:   0 1px 2px rgba(0,0,0,0.05)
               Subtle depth

--shadow-sm:   0 1px 3px rgba(0,0,0,0.1)
               Small elevation ⭐ Cards default

--shadow-base: 0 4px 6px rgba(0,0,0,0.1)
               Medium elevation

--shadow-md:   0 10px 15px rgba(0,0,0,0.1)
               Raised elevation ⭐ Card hover

--shadow-lg:   0 20px 25px rgba(0,0,0,0.1)
               High elevation

--shadow-xl:   0 25px 50px rgba(0,0,0,0.25)
               Very high ⭐ Modals, toasts

--shadow-2xl:  0 50px 100px rgba(0,0,0,0.5)
               Maximum elevation

--shadow-inner: inset 0 2px 4px rgba(0,0,0,0.05)
                Inset shadow
```

### Colored Shadows
```
--shadow-primary: 0 10px 40px rgba(99,102,241,0.4)   Indigo glow
--shadow-success: 0 10px 40px rgba(34,197,94,0.4)    Green glow
--shadow-error:   0 10px 40px rgba(239,68,68,0.4)    Red glow
```

---

## Z-Index Tokens
```
--z-index-base:         0      Base layer
--z-index-dropdown:     1000   Dropdowns
--z-index-sticky:       1020   Sticky nav ⭐
--z-index-fixed:        1030   Fixed elements
--z-index-overlay:      1040   Modal overlays ⭐
--z-index-modal:        1050   Modal dialogs ⭐
--z-index-popover:      1060   Popovers
--z-index-tooltip:      1070   Tooltips
--z-index-notification: 1080   Toasts ⭐
```

---

## Animation Tokens

### Duration
```
--duration-instant:  0ms     No animation
--duration-fast:     100ms   Micro-interactions
--duration-normal:   200ms   Standard transitions ⭐ Most used
--duration-slow:     300ms   Deliberate animations
--duration-slower:   500ms   Emphasis animations
```

### Easing
```
--ease-linear:   linear                          Constant speed
--ease-in:       cubic-bezier(0.4, 0, 1, 1)     Start slow
--ease-out:      cubic-bezier(0, 0, 0.2, 1)     End slow
--ease-in-out:   cubic-bezier(0.4, 0, 0.2, 1)   ⭐ Most used
--ease-bounce:   cubic-bezier(0.68, -0.55, 0.265, 1.55)
--ease-spring:   cubic-bezier(0.175, 0.885, 0.32, 1.275)
```

### Pre-built Transitions
```css
--transition-base:      all 200ms ease-in-out ⭐ Most used
--transition-color:     color, background-color, border-color 200ms
--transition-shadow:    box-shadow 200ms ease-in-out
--transition-transform: transform 200ms ease-in-out
```

---

## Usage Examples

### Building a Button
```css
.custom-button {
  /* Typography */
  font-family: var(--font-family-primary);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);

  /* Spacing */
  padding: var(--spacing-3) var(--spacing-5);

  /* Colors */
  color: var(--color-white);
  background: var(--color-primary-700);

  /* Border */
  border: 1px solid transparent;
  border-radius: var(--radius-md);

  /* Shadow & Transition */
  box-shadow: var(--shadow-sm);
  transition: var(--transition-base);
}

.custom-button:hover {
  background: var(--color-primary-600);
  box-shadow: var(--shadow-md);
}
```

### Building a Card
```css
.custom-card {
  /* Colors */
  background: var(--color-white);
  border: 1px solid var(--color-neutral-200);

  /* Spacing */
  padding: var(--spacing-6);

  /* Border & Shadow */
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);

  /* Transition */
  transition: var(--transition-shadow);
}

.custom-card:hover {
  box-shadow: var(--shadow-md);
}
```

### Building a Text Style
```css
.heading-1 {
  font-family: var(--font-family-display);
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-bold);
  line-height: var(--line-height-tight);
  letter-spacing: var(--letter-spacing-tight);
  color: var(--color-neutral-900);
  margin-bottom: var(--spacing-4);
}

.body-text {
  font-family: var(--font-family-primary);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-normal);
  line-height: var(--line-height-normal);
  color: var(--color-neutral-700);
}
```

---

## Color Usage Guidelines

### Text Colors
| Use Case | Token | Example |
|----------|-------|---------|
| Primary text | `--color-neutral-900` | Main headings, body text |
| Secondary text | `--color-neutral-700` | Subheadings, descriptions |
| Tertiary text | `--color-neutral-600` | Metadata, timestamps |
| Disabled text | `--color-neutral-500` | Disabled inputs |
| Placeholder | `--color-neutral-500` | Input placeholders |
| Link text | `--color-primary-700` | Interactive links |

### Background Colors
| Use Case | Token | Example |
|----------|-------|---------|
| Page background | `--color-neutral-50` | Body background |
| Card background | `--color-white` | Cards, panels |
| Hover background | `--color-neutral-100` | Button hover (light) |
| Selected background | `--color-primary-100` | Active nav items |
| Disabled background | `--color-neutral-100` | Disabled inputs |

### Border Colors
| Use Case | Token | Example |
|----------|-------|---------|
| Default border | `--color-neutral-200` | Card borders |
| Input border | `--color-neutral-300` | Text inputs |
| Divider | `--color-neutral-200` | Section dividers |
| Focus border | `--color-primary-600` | Focused inputs |
| Error border | `--color-error-600` | Invalid inputs |

---

## Spacing Patterns

### Common Patterns
```
Button padding:      12px 20px  (spacing-3 spacing-5)
Card padding:        24px       (spacing-6)
Panel padding:       20px 24px  (spacing-5 spacing-6)
Grid gap:            24px       (spacing-6)
Form field spacing:  20px       (spacing-5)
Section spacing:     32px       (spacing-8)
Page padding:        32px       (spacing-8)
```

### Responsive Spacing
```
Mobile padding:   16px  (spacing-4)
Tablet padding:   24px  (spacing-6)
Desktop padding:  32px  (spacing-8)
```

---

## Typography Scale Usage

| Element | Token | Size | Use Case |
|---------|-------|------|----------|
| Hero heading | `--font-size-5xl` | 60px | Landing pages |
| Display heading | `--font-size-4xl` | 48px | Major sections |
| H1 | `--font-size-3xl` | 36px | Page titles |
| H2 | `--font-size-2xl` | 30px | Section headings |
| H3 | `--font-size-xl` | 24px | Panel titles |
| H4 | `--font-size-lg` | 20px | Card titles |
| Body large | `--font-size-md` | 18px | Emphasis text |
| Body | `--font-size-base` | 16px | Main content |
| Body small | `--font-size-sm` | 14px | Captions, metadata |
| Fine print | `--font-size-xs` | 12px | Labels, footnotes |

---

## Quick Token Finder

**Need a color for...**
- Primary action → `--color-primary-700`
- Success state → `--color-success-600`
- Error state → `--color-error-600`
- Warning state → `--color-warning-600`
- Body text → `--color-neutral-700`
- Page background → `--color-neutral-50`

**Need spacing for...**
- Button padding → `var(--spacing-3) var(--spacing-5)`
- Card padding → `var(--spacing-6)`
- Grid gap → `var(--spacing-6)`
- Section margin → `var(--spacing-8)`

**Need a shadow for...**
- Card → `var(--shadow-sm)`
- Card hover → `var(--shadow-md)`
- Modal → `var(--shadow-xl)`

**Need border radius for...**
- Button → `var(--radius-md)`
- Card → `var(--radius-lg)`
- Badge → `var(--radius-full)`

**Need font size for...**
- Page title → `var(--font-size-3xl)`
- Section heading → `var(--font-size-2xl)`
- Body text → `var(--font-size-base)`
- Small text → `var(--font-size-sm)`

---

## Token Combinations

### Primary Button
```css
background: var(--color-primary-700);
color: var(--color-white);
padding: var(--spacing-3) var(--spacing-5);
border-radius: var(--radius-md);
font-size: var(--font-size-base);
font-weight: var(--font-weight-semibold);
box-shadow: var(--shadow-sm);
transition: var(--transition-base);
```

### Card Component
```css
background: var(--color-white);
border: 1px solid var(--color-neutral-200);
border-radius: var(--radius-lg);
padding: var(--spacing-6);
box-shadow: var(--shadow-sm);
```

### Text Input
```css
padding: var(--spacing-3) var(--spacing-4);
font-size: var(--font-size-base);
color: var(--color-neutral-900);
background: var(--color-white);
border: 1px solid var(--color-neutral-300);
border-radius: var(--radius-md);
transition: var(--transition-base);
```

### Heading 1
```css
font-size: var(--font-size-3xl);
font-weight: var(--font-weight-bold);
line-height: var(--line-height-tight);
color: var(--color-neutral-900);
margin-bottom: var(--spacing-4);
```

---

**Design Tokens Reference v1.0**
**SuperStandard Multi-Agent Platform Design System**
