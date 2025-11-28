# Multi-Agent Platform Design System
## Enterprise-Grade UI Specification v1.0

---

## Table of Contents
1. [Design Philosophy](#design-philosophy)
2. [Foundation](#foundation)
   - [Color System](#color-system)
   - [Typography](#typography)
   - [Spacing & Layout](#spacing--layout)
   - [Elevation & Shadows](#elevation--shadows)
   - [Animation & Motion](#animation--motion)
3. [Component Library](#component-library)
4. [Layout System](#layout-system)
5. [Data Visualization](#data-visualization)
6. [Interaction Patterns](#interaction-patterns)
7. [Implementation Guidelines](#implementation-guidelines)

---

## Design Philosophy

**Core Principles:**
- **Professional & Trustworthy**: Clean, modern aesthetic that conveys reliability
- **Data-First**: Optimized for displaying complex metrics and real-time data
- **Accessible**: WCAG 2.1 AA compliant, keyboard navigable, screen reader friendly
- **Responsive**: Seamless experience across desktop, tablet, and mobile
- **Performance**: Optimized for real-time updates and large datasets
- **Consistent**: Unified design language across all dashboards

**Design Inspiration:**
- Microsoft Azure Portal (clean, professional, data-dense)
- AWS Console (organized, hierarchical, functional)
- Stripe Dashboard (modern, minimalist, delightful)
- Datadog (real-time data visualization excellence)

---

## Foundation

### Color System

#### Primary Palette
```css
/* Brand Colors */
--color-primary-900: #3730a3;    /* Deep indigo - headings, emphasis */
--color-primary-800: #4338ca;    /* Dark indigo - interactive elements */
--color-primary-700: #4f46e5;    /* Indigo - primary actions */
--color-primary-600: #6366f1;    /* Medium indigo - hover states */
--color-primary-500: #818cf8;    /* Light indigo - accents */
--color-primary-400: #a5b4fc;    /* Pale indigo - backgrounds */
--color-primary-300: #c7d2fe;    /* Very pale indigo - subtle backgrounds */
--color-primary-200: #e0e7ff;    /* Lightest indigo - hover backgrounds */
--color-primary-100: #eef2ff;    /* Near white indigo - subtle tints */
```

#### Secondary Palette
```css
/* Purple Accents */
--color-secondary-900: #581c87;  /* Deep purple */
--color-secondary-800: #6b21a8;  /* Dark purple */
--color-secondary-700: #7e22ce;  /* Purple */
--color-secondary-600: #9333ea;  /* Medium purple */
--color-secondary-500: #a855f7;  /* Light purple */
--color-secondary-400: #c084fc;  /* Pale purple */
--color-secondary-300: #d8b4fe;  /* Very pale purple */
--color-secondary-200: #e9d5ff;  /* Lightest purple */
--color-secondary-100: #f3e8ff;  /* Near white purple */
```

#### Neutral Palette
```css
/* Grays for text, borders, backgrounds */
--color-neutral-900: #18181b;    /* Near black - primary text */
--color-neutral-800: #27272a;    /* Dark gray - secondary text */
--color-neutral-700: #3f3f46;    /* Gray - tertiary text */
--color-neutral-600: #52525b;    /* Medium gray - disabled text */
--color-neutral-500: #71717a;    /* Light gray - placeholder text */
--color-neutral-400: #a1a1aa;    /* Pale gray - borders */
--color-neutral-300: #d4d4d8;    /* Very pale gray - dividers */
--color-neutral-200: #e4e4e7;    /* Lightest gray - backgrounds */
--color-neutral-100: #f4f4f5;    /* Near white - subtle backgrounds */
--color-neutral-50:  #fafafa;    /* Off white - page backgrounds */
--color-white:       #ffffff;    /* Pure white */
```

#### Semantic Colors
```css
/* Success */
--color-success-700: #15803d;    /* Dark green */
--color-success-600: #16a34a;    /* Green */
--color-success-500: #22c55e;    /* Medium green */
--color-success-400: #4ade80;    /* Light green */
--color-success-100: #dcfce7;    /* Pale green background */

/* Warning */
--color-warning-700: #c2410c;    /* Dark orange */
--color-warning-600: #ea580c;    /* Orange */
--color-warning-500: #f97316;    /* Medium orange */
--color-warning-400: #fb923c;    /* Light orange */
--color-warning-100: #ffedd5;    /* Pale orange background */

/* Error */
--color-error-700: #b91c1c;      /* Dark red */
--color-error-600: #dc2626;      /* Red */
--color-error-500: #ef4444;      /* Medium red */
--color-error-400: #f87171;      /* Light red */
--color-error-100: #fee2e2;      /* Pale red background */

/* Info */
--color-info-700: #0369a1;       /* Dark blue */
--color-info-600: #0284c7;       /* Blue */
--color-info-500: #0ea5e9;       /* Medium blue */
--color-info-400: #38bdf8;       /* Light blue */
--color-info-100: #dbeafe;       /* Pale blue background */
```

#### Data Visualization Colors
```css
/* Chart Colors - Carefully selected for accessibility and distinction */
--color-chart-1: #6366f1;   /* Indigo */
--color-chart-2: #8b5cf6;   /* Purple */
--color-chart-3: #ec4899;   /* Pink */
--color-chart-4: #f59e0b;   /* Amber */
--color-chart-5: #10b981;   /* Emerald */
--color-chart-6: #06b6d4;   /* Cyan */
--color-chart-7: #f97316;   /* Orange */
--color-chart-8: #84cc16;   /* Lime */
--color-chart-9: #6366f1;   /* Indigo (repeat) */
--color-chart-10: #14b8a6;  /* Teal */

/* Gradient Backgrounds */
--gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
--gradient-secondary: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
--gradient-success: linear-gradient(135deg, #4ade80 0%, #22c55e 100%);
--gradient-info: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
--gradient-dark: linear-gradient(135deg, #1f2937 0%, #111827 100%);
```

### Typography

#### Font Families
```css
/* Primary Font Stack */
--font-family-primary: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI',
                       'Roboto', 'Helvetica Neue', Arial, sans-serif;

/* Monospace Font Stack */
--font-family-mono: 'JetBrains Mono', 'SF Mono', Monaco, 'Cascadia Code',
                    'Roboto Mono', 'Courier New', monospace;

/* Display Font (for large headings) */
--font-family-display: 'Inter Display', 'Inter', system-ui, sans-serif;
```

#### Font Sizes
```css
/* Type Scale (1.25 - Major Third) */
--font-size-xs:   0.75rem;   /* 12px - Fine print, labels */
--font-size-sm:   0.875rem;  /* 14px - Body small, captions */
--font-size-base: 1rem;      /* 16px - Body text */
--font-size-md:   1.125rem;  /* 18px - Body large */
--font-size-lg:   1.25rem;   /* 20px - H4 */
--font-size-xl:   1.5rem;    /* 24px - H3 */
--font-size-2xl:  1.875rem;  /* 30px - H2 */
--font-size-3xl:  2.25rem;   /* 36px - H1 */
--font-size-4xl:  3rem;      /* 48px - Display headings */
--font-size-5xl:  3.75rem;   /* 60px - Hero text */
```

#### Font Weights
```css
--font-weight-light:     300;
--font-weight-normal:    400;
--font-weight-medium:    500;
--font-weight-semibold:  600;
--font-weight-bold:      700;
--font-weight-extrabold: 800;
```

#### Line Heights
```css
--line-height-tight:   1.25;   /* Headings */
--line-height-normal:  1.5;    /* Body text */
--line-height-relaxed: 1.75;   /* Long-form content */
```

#### Letter Spacing
```css
--letter-spacing-tight:  -0.025em;  /* Large headings */
--letter-spacing-normal:  0;        /* Body text */
--letter-spacing-wide:    0.025em;  /* Buttons, labels */
--letter-spacing-wider:   0.05em;   /* Small caps */
```

### Spacing & Layout

#### Spacing Scale
```css
/* 8px base unit - all spacing is multiples of 8 */
--spacing-0:   0;
--spacing-1:   0.25rem;  /* 4px  - Tight spacing */
--spacing-2:   0.5rem;   /* 8px  - Compact spacing */
--spacing-3:   0.75rem;  /* 12px - Comfortable spacing */
--spacing-4:   1rem;     /* 16px - Base spacing */
--spacing-5:   1.25rem;  /* 20px - Medium spacing */
--spacing-6:   1.5rem;   /* 24px - Spacious */
--spacing-8:   2rem;     /* 32px - Large spacing */
--spacing-10:  2.5rem;   /* 40px - Extra large */
--spacing-12:  3rem;     /* 48px - Section spacing */
--spacing-16:  4rem;     /* 64px - Page section */
--spacing-20:  5rem;     /* 80px - Large sections */
--spacing-24:  6rem;     /* 96px - Hero sections */
```

#### Border Radius
```css
--radius-none:   0;
--radius-sm:     0.25rem;  /* 4px  - Subtle rounding */
--radius-base:   0.5rem;   /* 8px  - Default rounding */
--radius-md:     0.75rem;  /* 12px - Medium rounding */
--radius-lg:     1rem;     /* 16px - Large rounding */
--radius-xl:     1.5rem;   /* 24px - Extra large */
--radius-2xl:    2rem;     /* 32px - Very large */
--radius-full:   9999px;   /* Pill/circular */
```

#### Container Widths
```css
--container-sm:  640px;   /* Small screens */
--container-md:  768px;   /* Medium screens */
--container-lg:  1024px;  /* Large screens */
--container-xl:  1280px;  /* Extra large screens */
--container-2xl: 1536px;  /* Maximum width */
```

#### Grid System
```css
/* 12-column grid */
--grid-columns: 12;
--grid-gap: var(--spacing-6);  /* 24px gap */

/* Breakpoints */
--breakpoint-sm:  640px;
--breakpoint-md:  768px;
--breakpoint-lg:  1024px;
--breakpoint-xl:  1280px;
--breakpoint-2xl: 1536px;
```

### Elevation & Shadows

#### Box Shadows
```css
/* Elevation system for depth */
--shadow-xs:  0 1px 2px 0 rgba(0, 0, 0, 0.05);
--shadow-sm:  0 1px 3px 0 rgba(0, 0, 0, 0.1),
              0 1px 2px -1px rgba(0, 0, 0, 0.1);
--shadow-base: 0 4px 6px -1px rgba(0, 0, 0, 0.1),
               0 2px 4px -2px rgba(0, 0, 0, 0.1);
--shadow-md:  0 10px 15px -3px rgba(0, 0, 0, 0.1),
              0 4px 6px -4px rgba(0, 0, 0, 0.1);
--shadow-lg:  0 20px 25px -5px rgba(0, 0, 0, 0.1),
              0 8px 10px -6px rgba(0, 0, 0, 0.1);
--shadow-xl:  0 25px 50px -12px rgba(0, 0, 0, 0.25);
--shadow-2xl: 0 50px 100px -20px rgba(0, 0, 0, 0.5);

/* Inner shadows */
--shadow-inner: inset 0 2px 4px 0 rgba(0, 0, 0, 0.05);

/* Colored shadows for emphasis */
--shadow-primary: 0 10px 40px -10px rgba(99, 102, 241, 0.4);
--shadow-success: 0 10px 40px -10px rgba(34, 197, 94, 0.4);
--shadow-error:   0 10px 40px -10px rgba(239, 68, 68, 0.4);
```

#### Z-Index Layers
```css
--z-index-base:      0;
--z-index-dropdown:  1000;
--z-index-sticky:    1020;
--z-index-fixed:     1030;
--z-index-overlay:   1040;
--z-index-modal:     1050;
--z-index-popover:   1060;
--z-index-tooltip:   1070;
--z-index-notification: 1080;
```

### Animation & Motion

#### Transition Durations
```css
--duration-instant:  0ms;
--duration-fast:     100ms;   /* Micro-interactions */
--duration-normal:   200ms;   /* Standard transitions */
--duration-slow:     300ms;   /* Deliberate animations */
--duration-slower:   500ms;   /* Emphasis animations */
```

#### Easing Functions
```css
--ease-linear:     linear;
--ease-in:         cubic-bezier(0.4, 0, 1, 1);
--ease-out:        cubic-bezier(0, 0, 0.2, 1);
--ease-in-out:     cubic-bezier(0.4, 0, 0.2, 1);
--ease-bounce:     cubic-bezier(0.68, -0.55, 0.265, 1.55);
--ease-spring:     cubic-bezier(0.175, 0.885, 0.32, 1.275);
```

#### Common Transitions
```css
--transition-base:   all var(--duration-normal) var(--ease-in-out);
--transition-color:  color var(--duration-normal) var(--ease-in-out),
                     background-color var(--duration-normal) var(--ease-in-out),
                     border-color var(--duration-normal) var(--ease-in-out);
--transition-shadow: box-shadow var(--duration-normal) var(--ease-in-out);
--transition-transform: transform var(--duration-normal) var(--ease-in-out);
```

---

## Component Library

### 1. Navigation Components

#### Top Navigation Bar
```css
.nav-bar {
  background: var(--color-white);
  border-bottom: 1px solid var(--color-neutral-200);
  height: 64px;
  padding: 0 var(--spacing-6);
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: sticky;
  top: 0;
  z-index: var(--z-index-sticky);
  box-shadow: var(--shadow-sm);
}

.nav-logo {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-primary-700);
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
}

.nav-links {
  display: flex;
  gap: var(--spacing-2);
  align-items: center;
}

.nav-link {
  padding: var(--spacing-2) var(--spacing-4);
  border-radius: var(--radius-md);
  color: var(--color-neutral-700);
  text-decoration: none;
  font-weight: var(--font-weight-medium);
  font-size: var(--font-size-sm);
  transition: var(--transition-color);
}

.nav-link:hover {
  background: var(--color-neutral-100);
  color: var(--color-neutral-900);
}

.nav-link.active {
  background: var(--color-primary-100);
  color: var(--color-primary-700);
}
```

**HTML Structure:**
```html
<nav class="nav-bar">
  <a href="/" class="nav-logo">
    <span class="logo-icon">🚀</span>
    <span>SuperStandard</span>
  </a>
  <div class="nav-links">
    <a href="/dashboard" class="nav-link active">Dashboard</a>
    <a href="/agents" class="nav-link">Agents</a>
    <a href="/sessions" class="nav-link">Sessions</a>
    <a href="/docs" class="nav-link">Docs</a>
  </div>
  <div class="nav-actions">
    <button class="btn btn-sm btn-secondary">Settings</button>
    <button class="btn btn-sm btn-primary">New Agent</button>
  </div>
</nav>
```

#### Sidebar Navigation
```css
.sidebar {
  width: 280px;
  height: 100vh;
  background: var(--color-white);
  border-right: 1px solid var(--color-neutral-200);
  padding: var(--spacing-6) var(--spacing-4);
  overflow-y: auto;
  position: fixed;
  left: 0;
  top: 64px; /* Below top nav */
  z-index: var(--z-index-sticky);
}

.sidebar-section {
  margin-bottom: var(--spacing-6);
}

.sidebar-section-title {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  text-transform: uppercase;
  letter-spacing: var(--letter-spacing-wider);
  color: var(--color-neutral-500);
  margin-bottom: var(--spacing-3);
  padding: 0 var(--spacing-3);
}

.sidebar-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  padding: var(--spacing-3) var(--spacing-3);
  border-radius: var(--radius-md);
  color: var(--color-neutral-700);
  text-decoration: none;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  transition: var(--transition-color);
  cursor: pointer;
}

.sidebar-item:hover {
  background: var(--color-neutral-100);
  color: var(--color-neutral-900);
}

.sidebar-item.active {
  background: var(--color-primary-100);
  color: var(--color-primary-700);
}

.sidebar-item-icon {
  font-size: var(--font-size-lg);
  width: 24px;
  text-align: center;
}

.sidebar-item-badge {
  margin-left: auto;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  background: var(--color-primary-100);
  color: var(--color-primary-700);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
}
```

#### Breadcrumbs
```css
.breadcrumbs {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  font-size: var(--font-size-sm);
  color: var(--color-neutral-600);
  margin-bottom: var(--spacing-4);
}

.breadcrumb-item {
  color: var(--color-neutral-600);
  text-decoration: none;
  transition: color var(--duration-normal);
}

.breadcrumb-item:hover {
  color: var(--color-primary-600);
}

.breadcrumb-item.current {
  color: var(--color-neutral-900);
  font-weight: var(--font-weight-medium);
}

.breadcrumb-separator {
  color: var(--color-neutral-400);
}
```

### 2. Cards & Panels

#### Standard Card
```css
.card {
  background: var(--color-white);
  border: 1px solid var(--color-neutral-200);
  border-radius: var(--radius-lg);
  padding: var(--spacing-6);
  box-shadow: var(--shadow-sm);
  transition: var(--transition-shadow);
}

.card:hover {
  box-shadow: var(--shadow-md);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--spacing-4);
}

.card-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-neutral-900);
  margin: 0;
}

.card-subtitle {
  font-size: var(--font-size-sm);
  color: var(--color-neutral-600);
  margin-top: var(--spacing-1);
}

.card-body {
  color: var(--color-neutral-700);
  line-height: var(--line-height-normal);
}

.card-footer {
  margin-top: var(--spacing-4);
  padding-top: var(--spacing-4);
  border-top: 1px solid var(--color-neutral-200);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
```

#### Stat Card (Metrics Display)
```css
.stat-card {
  background: var(--color-white);
  border: 1px solid var(--color-neutral-200);
  border-radius: var(--radius-lg);
  padding: var(--spacing-6);
  text-align: center;
  transition: var(--transition-base);
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.stat-value {
  font-size: var(--font-size-4xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-primary-700);
  line-height: var(--line-height-tight);
  margin-bottom: var(--spacing-2);
}

.stat-label {
  font-size: var(--font-size-sm);
  color: var(--color-neutral-600);
  font-weight: var(--font-weight-medium);
  text-transform: uppercase;
  letter-spacing: var(--letter-spacing-wide);
}

.stat-change {
  margin-top: var(--spacing-2);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
}

.stat-change.positive {
  color: var(--color-success-600);
}

.stat-change.negative {
  color: var(--color-error-600);
}

.stat-icon {
  font-size: var(--font-size-2xl);
  margin-bottom: var(--spacing-3);
  opacity: 0.8;
}
```

#### Dashboard Panel
```css
.panel {
  background: var(--color-white);
  border: 1px solid var(--color-neutral-200);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.panel-header {
  padding: var(--spacing-5) var(--spacing-6);
  border-bottom: 1px solid var(--color-neutral-200);
  background: var(--color-neutral-50);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-neutral-900);
  margin: 0;
}

.panel-actions {
  display: flex;
  gap: var(--spacing-2);
}

.panel-body {
  padding: var(--spacing-6);
}

.panel-body.compact {
  padding: var(--spacing-4);
}

.panel-body.no-padding {
  padding: 0;
}
```

### 3. Buttons

#### Button Variants
```css
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-2);
  padding: var(--spacing-3) var(--spacing-5);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  line-height: 1;
  text-decoration: none;
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: var(--transition-base);
  white-space: nowrap;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  pointer-events: none;
}

/* Primary Button */
.btn-primary {
  background: var(--color-primary-700);
  color: var(--color-white);
  box-shadow: var(--shadow-sm);
}

.btn-primary:hover {
  background: var(--color-primary-600);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.btn-primary:active {
  transform: translateY(0);
  box-shadow: var(--shadow-sm);
}

/* Secondary Button */
.btn-secondary {
  background: var(--color-white);
  color: var(--color-neutral-700);
  border-color: var(--color-neutral-300);
}

.btn-secondary:hover {
  background: var(--color-neutral-50);
  border-color: var(--color-neutral-400);
  color: var(--color-neutral-900);
}

/* Tertiary / Ghost Button */
.btn-ghost {
  background: transparent;
  color: var(--color-neutral-700);
}

.btn-ghost:hover {
  background: var(--color-neutral-100);
  color: var(--color-neutral-900);
}

/* Success Button */
.btn-success {
  background: var(--color-success-600);
  color: var(--color-white);
}

.btn-success:hover {
  background: var(--color-success-700);
}

/* Danger Button */
.btn-danger {
  background: var(--color-error-600);
  color: var(--color-white);
}

.btn-danger:hover {
  background: var(--color-error-700);
}

/* Button Sizes */
.btn-sm {
  padding: var(--spacing-2) var(--spacing-3);
  font-size: var(--font-size-sm);
}

.btn-lg {
  padding: var(--spacing-4) var(--spacing-8);
  font-size: var(--font-size-lg);
}

.btn-icon {
  padding: var(--spacing-3);
  aspect-ratio: 1;
}

/* Full Width Button */
.btn-block {
  width: 100%;
}

/* Button Group */
.btn-group {
  display: inline-flex;
  gap: var(--spacing-2);
}
```

### 4. Form Components

#### Text Input
```css
.form-group {
  margin-bottom: var(--spacing-5);
}

.form-label {
  display: block;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-neutral-900);
  margin-bottom: var(--spacing-2);
}

.form-label.required::after {
  content: " *";
  color: var(--color-error-600);
}

.form-input {
  width: 100%;
  padding: var(--spacing-3) var(--spacing-4);
  font-size: var(--font-size-base);
  font-family: inherit;
  color: var(--color-neutral-900);
  background: var(--color-white);
  border: 1px solid var(--color-neutral-300);
  border-radius: var(--radius-md);
  transition: var(--transition-base);
}

.form-input:hover {
  border-color: var(--color-neutral-400);
}

.form-input:focus {
  outline: none;
  border-color: var(--color-primary-600);
  box-shadow: 0 0 0 3px var(--color-primary-100);
}

.form-input:disabled {
  background: var(--color-neutral-100);
  color: var(--color-neutral-500);
  cursor: not-allowed;
}

.form-input.error {
  border-color: var(--color-error-600);
}

.form-input.error:focus {
  box-shadow: 0 0 0 3px var(--color-error-100);
}

.form-help {
  margin-top: var(--spacing-2);
  font-size: var(--font-size-sm);
  color: var(--color-neutral-600);
}

.form-error {
  margin-top: var(--spacing-2);
  font-size: var(--font-size-sm);
  color: var(--color-error-600);
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
}
```

#### Select Dropdown
```css
.form-select {
  width: 100%;
  padding: var(--spacing-3) var(--spacing-4);
  font-size: var(--font-size-base);
  font-family: inherit;
  color: var(--color-neutral-900);
  background: var(--color-white);
  border: 1px solid var(--color-neutral-300);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: var(--transition-base);
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath fill='%2352525b' d='M1.41 0L6 4.58 10.59 0 12 1.41l-6 6-6-6z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right var(--spacing-4) center;
  padding-right: var(--spacing-10);
}

.form-select:hover {
  border-color: var(--color-neutral-400);
}

.form-select:focus {
  outline: none;
  border-color: var(--color-primary-600);
  box-shadow: 0 0 0 3px var(--color-primary-100);
}
```

#### Checkbox
```css
.form-checkbox {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  cursor: pointer;
}

.form-checkbox-input {
  appearance: none;
  width: 20px;
  height: 20px;
  border: 2px solid var(--color-neutral-400);
  border-radius: var(--radius-sm);
  background: var(--color-white);
  cursor: pointer;
  transition: var(--transition-base);
  position: relative;
  flex-shrink: 0;
}

.form-checkbox-input:checked {
  background: var(--color-primary-700);
  border-color: var(--color-primary-700);
}

.form-checkbox-input:checked::after {
  content: "";
  position: absolute;
  left: 5px;
  top: 2px;
  width: 6px;
  height: 10px;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.form-checkbox-input:focus {
  outline: none;
  box-shadow: 0 0 0 3px var(--color-primary-100);
}

.form-checkbox-label {
  font-size: var(--font-size-sm);
  color: var(--color-neutral-900);
}
```

#### Radio Button
```css
.form-radio {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  cursor: pointer;
}

.form-radio-input {
  appearance: none;
  width: 20px;
  height: 20px;
  border: 2px solid var(--color-neutral-400);
  border-radius: var(--radius-full);
  background: var(--color-white);
  cursor: pointer;
  transition: var(--transition-base);
  position: relative;
  flex-shrink: 0;
}

.form-radio-input:checked {
  border-color: var(--color-primary-700);
}

.form-radio-input:checked::after {
  content: "";
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 10px;
  height: 10px;
  border-radius: var(--radius-full);
  background: var(--color-primary-700);
}

.form-radio-input:focus {
  outline: none;
  box-shadow: 0 0 0 3px var(--color-primary-100);
}

.form-radio-label {
  font-size: var(--font-size-sm);
  color: var(--color-neutral-900);
}
```

### 5. Tables & Data Grids

#### Standard Table
```css
.table-container {
  overflow-x: auto;
  border: 1px solid var(--color-neutral-200);
  border-radius: var(--radius-lg);
  background: var(--color-white);
}

.table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--font-size-sm);
}

.table thead {
  background: var(--color-neutral-50);
  border-bottom: 2px solid var(--color-neutral-200);
}

.table th {
  padding: var(--spacing-4) var(--spacing-4);
  text-align: left;
  font-weight: var(--font-weight-semibold);
  color: var(--color-neutral-900);
  font-size: var(--font-size-xs);
  text-transform: uppercase;
  letter-spacing: var(--letter-spacing-wide);
}

.table td {
  padding: var(--spacing-4) var(--spacing-4);
  color: var(--color-neutral-700);
  border-bottom: 1px solid var(--color-neutral-200);
}

.table tbody tr:last-child td {
  border-bottom: none;
}

.table tbody tr:hover {
  background: var(--color-neutral-50);
}

.table tbody tr.selected {
  background: var(--color-primary-50);
}

/* Sortable column headers */
.table th.sortable {
  cursor: pointer;
  user-select: none;
}

.table th.sortable:hover {
  background: var(--color-neutral-100);
}

.table th.sorted-asc::after {
  content: " ↑";
  color: var(--color-primary-600);
}

.table th.sorted-desc::after {
  content: " ↓";
  color: var(--color-primary-600);
}

/* Compact table variant */
.table.compact td,
.table.compact th {
  padding: var(--spacing-2) var(--spacing-3);
}

/* Striped rows */
.table.striped tbody tr:nth-child(even) {
  background: var(--color-neutral-50);
}
```

### 6. Status Indicators & Badges

#### Badge
```css
.badge {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-1);
  padding: var(--spacing-1) var(--spacing-3);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  line-height: 1;
  border-radius: var(--radius-full);
  text-transform: uppercase;
  letter-spacing: var(--letter-spacing-wide);
}

.badge-primary {
  background: var(--color-primary-100);
  color: var(--color-primary-700);
}

.badge-success {
  background: var(--color-success-100);
  color: var(--color-success-700);
}

.badge-warning {
  background: var(--color-warning-100);
  color: var(--color-warning-700);
}

.badge-error {
  background: var(--color-error-100);
  color: var(--color-error-700);
}

.badge-info {
  background: var(--color-info-100);
  color: var(--color-info-700);
}

.badge-neutral {
  background: var(--color-neutral-200);
  color: var(--color-neutral-700);
}

/* Badge with dot indicator */
.badge.with-dot::before {
  content: "";
  width: 6px;
  height: 6px;
  border-radius: var(--radius-full);
  background: currentColor;
}
```

#### Status Indicator
```css
.status-indicator {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-2);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: var(--radius-full);
  flex-shrink: 0;
}

.status-online .status-dot {
  background: var(--color-success-500);
  box-shadow: 0 0 0 2px var(--color-success-100);
  animation: pulse 2s infinite;
}

.status-offline .status-dot {
  background: var(--color-neutral-400);
}

.status-warning .status-dot {
  background: var(--color-warning-500);
}

.status-error .status-dot {
  background: var(--color-error-500);
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}
```

### 7. Modals & Dialogs

#### Modal
```css
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  z-index: var(--z-index-modal);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-4);
  animation: fadeIn var(--duration-normal) var(--ease-out);
}

.modal {
  background: var(--color-white);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-2xl);
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  animation: slideUp var(--duration-slow) var(--ease-out);
}

.modal-header {
  padding: var(--spacing-6);
  border-bottom: 1px solid var(--color-neutral-200);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-neutral-900);
  margin: 0;
}

.modal-close {
  padding: var(--spacing-2);
  background: none;
  border: none;
  cursor: pointer;
  color: var(--color-neutral-500);
  transition: color var(--duration-normal);
  font-size: var(--font-size-xl);
  line-height: 1;
}

.modal-close:hover {
  color: var(--color-neutral-900);
}

.modal-body {
  padding: var(--spacing-6);
  overflow-y: auto;
  flex: 1;
}

.modal-footer {
  padding: var(--spacing-6);
  border-top: 1px solid var(--color-neutral-200);
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-3);
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
```

### 8. Notifications & Alerts

#### Alert Banner
```css
.alert {
  padding: var(--spacing-4) var(--spacing-5);
  border-radius: var(--radius-md);
  border-left: 4px solid;
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-3);
  margin-bottom: var(--spacing-4);
}

.alert-icon {
  font-size: var(--font-size-xl);
  flex-shrink: 0;
}

.alert-content {
  flex: 1;
}

.alert-title {
  font-weight: var(--font-weight-semibold);
  margin-bottom: var(--spacing-1);
}

.alert-message {
  font-size: var(--font-size-sm);
  line-height: var(--line-height-normal);
}

.alert-success {
  background: var(--color-success-100);
  border-left-color: var(--color-success-600);
  color: var(--color-success-900);
}

.alert-warning {
  background: var(--color-warning-100);
  border-left-color: var(--color-warning-600);
  color: var(--color-warning-900);
}

.alert-error {
  background: var(--color-error-100);
  border-left-color: var(--color-error-600);
  color: var(--color-error-900);
}

.alert-info {
  background: var(--color-info-100);
  border-left-color: var(--color-info-600);
  color: var(--color-info-900);
}
```

#### Toast Notification
```css
.toast-container {
  position: fixed;
  top: var(--spacing-6);
  right: var(--spacing-6);
  z-index: var(--z-index-notification);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
  max-width: 400px;
}

.toast {
  background: var(--color-white);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl);
  padding: var(--spacing-4) var(--spacing-5);
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-3);
  animation: slideInRight var(--duration-slow) var(--ease-out);
  border: 1px solid var(--color-neutral-200);
}

.toast-icon {
  font-size: var(--font-size-xl);
  flex-shrink: 0;
}

.toast-content {
  flex: 1;
}

.toast-title {
  font-weight: var(--font-weight-semibold);
  color: var(--color-neutral-900);
  margin-bottom: var(--spacing-1);
}

.toast-message {
  font-size: var(--font-size-sm);
  color: var(--color-neutral-700);
}

.toast-close {
  padding: var(--spacing-1);
  background: none;
  border: none;
  cursor: pointer;
  color: var(--color-neutral-500);
  line-height: 1;
  flex-shrink: 0;
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(100px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}
```

### 9. Loading States

#### Spinner
```css
.spinner {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 2px solid var(--color-neutral-300);
  border-top-color: var(--color-primary-700);
  border-radius: var(--radius-full);
  animation: spin 0.8s linear infinite;
}

.spinner-lg {
  width: 40px;
  height: 40px;
  border-width: 3px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
```

#### Skeleton Loader
```css
.skeleton {
  background: linear-gradient(
    90deg,
    var(--color-neutral-200) 25%,
    var(--color-neutral-100) 50%,
    var(--color-neutral-200) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: var(--radius-md);
}

.skeleton-text {
  height: 1em;
  margin-bottom: var(--spacing-2);
}

.skeleton-title {
  height: 1.5em;
  width: 60%;
  margin-bottom: var(--spacing-3);
}

.skeleton-avatar {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-full);
}

.skeleton-card {
  height: 200px;
  width: 100%;
}

@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}
```

#### Progress Bar
```css
.progress-bar {
  height: 8px;
  background: var(--color-neutral-200);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--color-primary-700);
  border-radius: var(--radius-full);
  transition: width var(--duration-slow) var(--ease-out);
}

.progress-bar.success .progress-fill {
  background: var(--color-success-600);
}

.progress-bar.warning .progress-fill {
  background: var(--color-warning-600);
}

.progress-bar.error .progress-fill {
  background: var(--color-error-600);
}

/* Indeterminate progress */
.progress-bar.indeterminate .progress-fill {
  width: 30%;
  animation: indeterminate 1.5s infinite;
}

@keyframes indeterminate {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(400%);
  }
}
```

### 10. Empty States

```css
.empty-state {
  text-align: center;
  padding: var(--spacing-12) var(--spacing-6);
}

.empty-state-icon {
  font-size: var(--font-size-5xl);
  opacity: 0.3;
  margin-bottom: var(--spacing-6);
}

.empty-state-title {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-neutral-900);
  margin-bottom: var(--spacing-3);
}

.empty-state-message {
  font-size: var(--font-size-base);
  color: var(--color-neutral-600);
  margin-bottom: var(--spacing-6);
  max-width: 500px;
  margin-left: auto;
  margin-right: auto;
}

.empty-state-actions {
  display: flex;
  justify-content: center;
  gap: var(--spacing-3);
}
```

---

## Layout System

### Page Layout
```css
/* Main application layout with sidebar */
.app-layout {
  display: flex;
  min-height: 100vh;
  background: var(--color-neutral-50);
}

.app-sidebar {
  /* See Sidebar Navigation component */
}

.app-main {
  flex: 1;
  margin-left: 280px; /* Sidebar width */
  padding-top: 64px; /* Top nav height */
}

.app-header {
  /* See Top Navigation Bar component */
}

.app-content {
  padding: var(--spacing-8);
  max-width: var(--container-2xl);
  margin: 0 auto;
}
```

### Dashboard Grid Layout
```css
.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: var(--spacing-6);
  margin-bottom: var(--spacing-6);
}

/* Responsive column spans */
.col-span-1  { grid-column: span 1; }
.col-span-2  { grid-column: span 2; }
.col-span-3  { grid-column: span 3; }
.col-span-4  { grid-column: span 4; }
.col-span-6  { grid-column: span 6; }
.col-span-8  { grid-column: span 8; }
.col-span-12 { grid-column: span 12; }

/* Example: 3-column stat cards on large screens, 1 column on mobile */
@media (max-width: 768px) {
  .col-span-4 { grid-column: span 12; }
}
```

### Content Density
```css
/* Comfortable (default) */
.content-comfortable {
  --spacing-scale: 1;
}

/* Compact */
.content-compact {
  --spacing-scale: 0.75;
}

.content-compact .card {
  padding: calc(var(--spacing-4) * var(--spacing-scale));
}

.content-compact .table td,
.content-compact .table th {
  padding: calc(var(--spacing-3) * var(--spacing-scale));
}

/* Spacious */
.content-spacious {
  --spacing-scale: 1.25;
}
```

### Responsive Breakpoints
```css
/* Mobile First approach */

/* Small devices (phones, up to 640px) */
@media (max-width: 640px) {
  .app-sidebar {
    transform: translateX(-100%);
    transition: transform var(--duration-slow);
  }

  .app-sidebar.open {
    transform: translateX(0);
  }

  .app-main {
    margin-left: 0;
  }
}

/* Medium devices (tablets, 641px - 1024px) */
@media (min-width: 641px) and (max-width: 1024px) {
  .dashboard-grid {
    grid-template-columns: repeat(6, 1fr);
  }
}

/* Large devices (desktops, 1024px+) */
@media (min-width: 1024px) {
  .dashboard-grid {
    grid-template-columns: repeat(12, 1fr);
  }
}
```

---

## Data Visualization

### Chart Container
```css
.chart-container {
  background: var(--color-white);
  border: 1px solid var(--color-neutral-200);
  border-radius: var(--radius-lg);
  padding: var(--spacing-6);
  margin-bottom: var(--spacing-6);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-6);
}

.chart-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-neutral-900);
}

.chart-controls {
  display: flex;
  gap: var(--spacing-2);
}

.chart-wrapper {
  min-height: 300px;
  position: relative;
}
```

### Chart Color Guidelines

**Line Charts:**
- Use single primary color for single metric
- Use up to 5 distinct colors for multiple lines
- Make lines 2-3px thick
- Use semi-transparent areas under lines

**Bar Charts:**
- Primary color for single dataset
- Gradient colors for value ranges
- 8px border radius on bar tops

**Pie/Donut Charts:**
- Use chart color palette (--color-chart-1 through 10)
- Ensure sufficient contrast between adjacent segments
- Consider color-blind friendly palettes

**Real-time Charts:**
- Smooth animations with 300ms transitions
- Fade in new data points
- Slide existing data left

### Metric Display Cards
```css
.metric-card {
  background: var(--color-white);
  border: 1px solid var(--color-neutral-200);
  border-radius: var(--radius-lg);
  padding: var(--spacing-5);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}

.metric-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.metric-label {
  font-size: var(--font-size-sm);
  color: var(--color-neutral-600);
  font-weight: var(--font-weight-medium);
}

.metric-value {
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-neutral-900);
  line-height: 1;
}

.metric-trend {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
}

.metric-trend.up {
  color: var(--color-success-600);
}

.metric-trend.down {
  color: var(--color-error-600);
}

.metric-sparkline {
  height: 40px;
  margin-top: var(--spacing-2);
}
```

### Heatmap Visualization
```css
.heatmap {
  display: grid;
  gap: var(--spacing-1);
}

.heatmap-cell {
  aspect-ratio: 1;
  border-radius: var(--radius-sm);
  transition: transform var(--duration-fast);
  cursor: pointer;
}

.heatmap-cell:hover {
  transform: scale(1.1);
  z-index: 1;
}

.heatmap-cell[data-intensity="0"] {
  background: var(--color-neutral-100);
}

.heatmap-cell[data-intensity="1"] {
  background: var(--color-primary-200);
}

.heatmap-cell[data-intensity="2"] {
  background: var(--color-primary-400);
}

.heatmap-cell[data-intensity="3"] {
  background: var(--color-primary-600);
}

.heatmap-cell[data-intensity="4"] {
  background: var(--color-primary-800);
}
```

---

## Interaction Patterns

### Hover States
```css
/* Interactive elements should have clear hover states */
.interactive:hover {
  /* Recommended effects (use 1-2, not all): */
  /* 1. Background change */
  background: var(--color-neutral-100);

  /* 2. Subtle elevation */
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);

  /* 3. Border highlight */
  border-color: var(--color-primary-600);

  /* 4. Color intensification */
  color: var(--color-neutral-900);
}
```

### Focus States
```css
/* All interactive elements must have visible focus states for accessibility */
.focusable:focus {
  outline: none;
  box-shadow: 0 0 0 3px var(--color-primary-100);
  border-color: var(--color-primary-600);
}

/* For dark backgrounds */
.focusable.on-dark:focus {
  box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.3);
}
```

### Active/Pressed States
```css
.clickable:active {
  transform: scale(0.98);
  box-shadow: var(--shadow-sm);
}
```

### Disabled States
```css
.disabled,
[disabled] {
  opacity: 0.5;
  cursor: not-allowed;
  pointer-events: none;
}
```

### Micro-animations
```css
/* Button pulse effect for important actions */
@keyframes pulse-ring {
  0% {
    box-shadow: 0 0 0 0 var(--color-primary-600);
  }
  100% {
    box-shadow: 0 0 0 10px rgba(99, 102, 241, 0);
  }
}

.btn-pulse {
  animation: pulse-ring 1.5s infinite;
}

/* Gentle bounce for new items */
@keyframes bounce-in {
  0% {
    opacity: 0;
    transform: scale(0.9);
  }
  50% {
    transform: scale(1.02);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}

.new-item {
  animation: bounce-in var(--duration-slow) var(--ease-bounce);
}
```

---

## Implementation Guidelines

### CSS Architecture

**Recommended structure:**
```
styles/
├── foundation/
│   ├── reset.css         # CSS reset/normalize
│   ├── variables.css     # CSS custom properties
│   └── typography.css    # Font imports and base styles
├── components/
│   ├── buttons.css
│   ├── forms.css
│   ├── cards.css
│   ├── tables.css
│   └── ...
├── layouts/
│   ├── grid.css
│   ├── navigation.css
│   └── page-layouts.css
└── utilities/
    ├── spacing.css
    └── helpers.css
```

### Utility Classes

```css
/* Spacing utilities */
.m-0  { margin: 0; }
.m-1  { margin: var(--spacing-1); }
.mt-4 { margin-top: var(--spacing-4); }
.mb-6 { margin-bottom: var(--spacing-6); }
.p-4  { padding: var(--spacing-4); }

/* Text utilities */
.text-sm     { font-size: var(--font-size-sm); }
.text-center { text-align: center; }
.font-bold   { font-weight: var(--font-weight-bold); }

/* Color utilities */
.text-primary   { color: var(--color-primary-700); }
.text-neutral   { color: var(--color-neutral-700); }
.bg-white       { background: var(--color-white); }
.bg-neutral-50  { background: var(--color-neutral-50); }

/* Display utilities */
.flex       { display: flex; }
.grid       { display: grid; }
.hidden     { display: none; }
.block      { display: block; }
.inline     { display: inline; }

/* Flexbox utilities */
.items-center   { align-items: center; }
.justify-between { justify-content: space-between; }
.flex-col       { flex-direction: column; }
.gap-4          { gap: var(--spacing-4); }

/* Border utilities */
.rounded-md { border-radius: var(--radius-md); }
.rounded-lg { border-radius: var(--radius-lg); }
.border     { border: 1px solid var(--color-neutral-200); }
```

### Accessibility Checklist

- [ ] All interactive elements are keyboard accessible
- [ ] Focus states are clearly visible
- [ ] Color contrast meets WCAG AA standards (4.5:1 for text)
- [ ] Form inputs have associated labels
- [ ] Error messages are announced to screen readers
- [ ] Images have alt text
- [ ] Buttons have descriptive labels (not just icons)
- [ ] Modals trap focus and can be closed with Escape
- [ ] Skip links provided for keyboard navigation
- [ ] ARIA labels used where appropriate

### Performance Best Practices

1. **CSS Loading:**
   - Critical CSS inlined in `<head>`
   - Non-critical CSS loaded asynchronously
   - Use CSS containment for complex components

2. **Animations:**
   - Use `transform` and `opacity` for animations (GPU accelerated)
   - Avoid animating `width`, `height`, `top`, `left`
   - Use `will-change` sparingly

3. **Images:**
   - Use WebP with fallbacks
   - Implement lazy loading
   - Provide multiple sizes for responsive images

4. **Real-time Updates:**
   - Debounce frequent updates
   - Use CSS transitions instead of JavaScript animations
   - Batch DOM updates

### Browser Support

**Target browsers:**
- Chrome/Edge (last 2 versions)
- Firefox (last 2 versions)
- Safari (last 2 versions)

**Graceful degradation:**
- CSS Grid with Flexbox fallback
- CSS custom properties with fallback values
- Modern features with @supports queries

### Dark Mode Support (Future Enhancement)

```css
/* Prepare for dark mode with CSS custom properties */
@media (prefers-color-scheme: dark) {
  :root {
    --color-neutral-900: #fafafa;
    --color-neutral-50: #18181b;
    --color-white: #27272a;
    /* ... invert neutral palette ... */
  }
}
```

---

## Complete Example: Dashboard Page

### HTML Structure
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Admin Dashboard - SuperStandard Platform</title>
  <link rel="stylesheet" href="/styles/main.css">
</head>
<body>
  <!-- Top Navigation -->
  <nav class="nav-bar">
    <a href="/" class="nav-logo">
      <span class="logo-icon">🚀</span>
      <span>SuperStandard</span>
    </a>
    <div class="nav-links">
      <a href="/dashboard" class="nav-link active">Dashboard</a>
      <a href="/agents" class="nav-link">Agents</a>
      <a href="/sessions" class="nav-link">Sessions</a>
    </div>
    <div class="nav-actions">
      <button class="btn btn-sm btn-secondary">Settings</button>
      <button class="btn btn-sm btn-primary">New Agent</button>
    </div>
  </nav>

  <div class="app-layout">
    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="sidebar-section">
        <h3 class="sidebar-section-title">Dashboards</h3>
        <a href="/dashboard/admin" class="sidebar-item active">
          <span class="sidebar-item-icon">📊</span>
          <span>Admin</span>
        </a>
        <a href="/dashboard/network" class="sidebar-item">
          <span class="sidebar-item-icon">🌐</span>
          <span>Network</span>
        </a>
        <a href="/dashboard/coordination" class="sidebar-item">
          <span class="sidebar-item-icon">🤝</span>
          <span>Coordination</span>
          <span class="sidebar-item-badge">3</span>
        </a>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="app-main">
      <div class="app-content">
        <!-- Page Header -->
        <div class="page-header">
          <nav class="breadcrumbs">
            <a href="/" class="breadcrumb-item">Home</a>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item current">Dashboard</span>
          </nav>
          <h1 class="page-title">Admin Dashboard</h1>
          <p class="page-subtitle">System-wide overview and real-time metrics</p>
        </div>

        <!-- Status Indicator -->
        <div class="status-indicator status-online">
          <span class="status-dot"></span>
          <span>All systems operational</span>
        </div>

        <!-- Metrics Grid -->
        <div class="dashboard-grid">
          <!-- Stat Cards -->
          <div class="col-span-3">
            <div class="stat-card">
              <div class="stat-icon">👥</div>
              <div class="stat-value">1,247</div>
              <div class="stat-label">Total Agents</div>
              <div class="stat-change positive">+12% this week</div>
            </div>
          </div>

          <div class="col-span-3">
            <div class="stat-card">
              <div class="stat-icon">🔄</div>
              <div class="stat-value">89</div>
              <div class="stat-label">Active Sessions</div>
              <div class="stat-change positive">+5% this week</div>
            </div>
          </div>

          <div class="col-span-3">
            <div class="stat-card">
              <div class="stat-icon">💭</div>
              <div class="stat-value">15.2k</div>
              <div class="stat-label">Thoughts Shared</div>
              <div class="stat-change positive">+23% this week</div>
            </div>
          </div>

          <div class="col-span-3">
            <div class="stat-card">
              <div class="stat-icon">🎯</div>
              <div class="stat-value">342</div>
              <div class="stat-label">Patterns Found</div>
              <div class="stat-change positive">+8% this week</div>
            </div>
          </div>

          <!-- Chart Panel -->
          <div class="col-span-8">
            <div class="panel">
              <div class="panel-header">
                <h3 class="panel-title">Agent Activity (Last 7 Days)</h3>
                <div class="panel-actions">
                  <button class="btn btn-sm btn-ghost">Export</button>
                </div>
              </div>
              <div class="panel-body">
                <div class="chart-wrapper" id="activityChart">
                  <!-- Chart rendered here via JavaScript -->
                </div>
              </div>
            </div>
          </div>

          <!-- Recent Activity -->
          <div class="col-span-4">
            <div class="panel">
              <div class="panel-header">
                <h3 class="panel-title">Recent Activity</h3>
              </div>
              <div class="panel-body no-padding">
                <div class="activity-feed">
                  <div class="activity-item">
                    <div class="activity-icon">
                      <span class="badge badge-success">New</span>
                    </div>
                    <div class="activity-content">
                      <p class="activity-title">Agent registered</p>
                      <p class="activity-meta">DataAnalyzer-42 • 2m ago</p>
                    </div>
                  </div>
                  <!-- More activity items... -->
                </div>
              </div>
            </div>
          </div>

          <!-- Table Example -->
          <div class="col-span-12">
            <div class="panel">
              <div class="panel-header">
                <h3 class="panel-title">Active Agents</h3>
                <div class="panel-actions">
                  <input type="search" class="form-input" placeholder="Search agents...">
                  <button class="btn btn-sm btn-primary">Add Agent</button>
                </div>
              </div>
              <div class="panel-body no-padding">
                <div class="table-container">
                  <table class="table">
                    <thead>
                      <tr>
                        <th class="sortable">Agent ID</th>
                        <th class="sortable">Name</th>
                        <th>Type</th>
                        <th>Status</th>
                        <th>Last Active</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td><code>agent-001</code></td>
                        <td>DataCollector</td>
                        <td><span class="badge badge-primary">Worker</span></td>
                        <td>
                          <div class="status-indicator status-online">
                            <span class="status-dot"></span>
                            <span>Online</span>
                          </div>
                        </td>
                        <td>2 minutes ago</td>
                        <td>
                          <div class="btn-group">
                            <button class="btn btn-sm btn-ghost">View</button>
                            <button class="btn btn-sm btn-ghost">Edit</button>
                          </div>
                        </td>
                      </tr>
                      <!-- More rows... -->
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>

  <script src="/scripts/main.js"></script>
</body>
</html>
```

### CSS (main.css)
```css
/* Import foundation */
@import url('foundation/variables.css');
@import url('foundation/reset.css');
@import url('foundation/typography.css');

/* Import components */
@import url('components/buttons.css');
@import url('components/forms.css');
@import url('components/cards.css');
@import url('components/tables.css');
@import url('components/navigation.css');

/* Import layouts */
@import url('layouts/grid.css');
@import url('layouts/page-layouts.css');

/* Global styles */
body {
  font-family: var(--font-family-primary);
  font-size: var(--font-size-base);
  line-height: var(--line-height-normal);
  color: var(--color-neutral-900);
  background: var(--color-neutral-50);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Page-specific styles */
.page-header {
  margin-bottom: var(--spacing-8);
}

.page-title {
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-neutral-900);
  margin-bottom: var(--spacing-2);
}

.page-subtitle {
  font-size: var(--font-size-base);
  color: var(--color-neutral-600);
}

.activity-feed {
  display: flex;
  flex-direction: column;
}

.activity-item {
  display: flex;
  gap: var(--spacing-4);
  padding: var(--spacing-4);
  border-bottom: 1px solid var(--color-neutral-200);
}

.activity-item:last-child {
  border-bottom: none;
}

.activity-title {
  font-weight: var(--font-weight-medium);
  color: var(--color-neutral-900);
  margin-bottom: var(--spacing-1);
}

.activity-meta {
  font-size: var(--font-size-sm);
  color: var(--color-neutral-600);
}
```

---

## Summary

This design system provides:

1. **Complete Foundation**: Colors, typography, spacing, shadows, and animations
2. **Comprehensive Components**: 10+ component categories with variants
3. **Flexible Layouts**: Grid system and responsive patterns
4. **Data Visualization**: Chart containers and metric displays
5. **Interaction Patterns**: Hover, focus, active states with accessibility
6. **Implementation Ready**: HTML examples, CSS code, and best practices

**Key Differentiators:**
- Professional, enterprise-grade aesthetic
- Optimized for data-heavy dashboards
- Real-time update friendly
- Accessibility built-in
- Performance-conscious
- Consistent and scalable

This system will ensure the Multi-Agent Platform has a cohesive, professional appearance across all dashboards while maintaining flexibility for future enhancements.
