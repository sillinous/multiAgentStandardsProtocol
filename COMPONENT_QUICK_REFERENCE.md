# Component Quick Reference
## SuperStandard Design System - Cheat Sheet

---

## Buttons

```html
<!-- Primary -->
<button class="btn btn-primary">Primary</button>

<!-- Secondary -->
<button class="btn btn-secondary">Secondary</button>

<!-- Ghost -->
<button class="btn btn-ghost">Ghost</button>

<!-- Success/Danger -->
<button class="btn btn-success">Success</button>
<button class="btn btn-danger">Danger</button>

<!-- Sizes -->
<button class="btn btn-sm btn-primary">Small</button>
<button class="btn btn-primary">Default</button>
<button class="btn btn-lg btn-primary">Large</button>

<!-- With Icons -->
<button class="btn btn-primary">
  <span>➕</span>
  <span>New Agent</span>
</button>

<!-- Icon Only -->
<button class="btn btn-icon btn-ghost">⚙️</button>

<!-- Full Width -->
<button class="btn btn-primary btn-block">Full Width</button>

<!-- Disabled -->
<button class="btn btn-primary" disabled>Disabled</button>
```

---

## Form Inputs

```html
<!-- Text Input -->
<div class="form-group">
  <label class="form-label required">Name</label>
  <input type="text" class="form-input" placeholder="Enter name">
  <div class="form-help">Helper text</div>
  <div class="form-error">Error message</div>
</div>

<!-- Select Dropdown -->
<div class="form-group">
  <label class="form-label">Type</label>
  <select class="form-select">
    <option>Select...</option>
    <option>Option 1</option>
  </select>
</div>

<!-- Textarea -->
<div class="form-group">
  <label class="form-label">Description</label>
  <textarea class="form-textarea" rows="3"></textarea>
</div>

<!-- Checkbox -->
<label class="form-checkbox">
  <input type="checkbox" class="form-checkbox-input">
  <span class="form-checkbox-label">Enable feature</span>
</label>

<!-- Radio Button -->
<label class="form-radio">
  <input type="radio" name="priority" class="form-radio-input">
  <span class="form-radio-label">High Priority</span>
</label>

<!-- Error State -->
<input type="text" class="form-input error" value="Invalid">
```

---

## Cards

```html
<!-- Standard Card -->
<div class="card">
  <div class="card-header">
    <div>
      <h3 class="card-title">Title</h3>
      <p class="card-subtitle">Subtitle</p>
    </div>
    <button class="btn btn-sm btn-ghost">Action</button>
  </div>
  <div class="card-body">
    Content goes here
  </div>
  <div class="card-footer">
    <span>Footer text</span>
    <button class="btn btn-sm btn-primary">Button</button>
  </div>
</div>

<!-- Stat Card -->
<div class="stat-card">
  <div class="stat-icon">👥</div>
  <div class="stat-value">1,247</div>
  <div class="stat-label">Total Agents</div>
  <div class="stat-change positive">↑ +12%</div>
</div>

<!-- Panel -->
<div class="panel">
  <div class="panel-header">
    <h3 class="panel-title">Panel Title</h3>
    <div class="panel-actions">
      <button class="btn btn-sm btn-ghost">Action</button>
    </div>
  </div>
  <div class="panel-body">
    Content
  </div>
</div>
```

---

## Navigation

```html
<!-- Top Nav Bar -->
<nav class="nav-bar">
  <a href="/" class="nav-logo">
    <span class="logo-icon">🚀</span>
    <span>App Name</span>
  </a>
  <div class="nav-links">
    <a href="#" class="nav-link active">Link</a>
    <a href="#" class="nav-link">Link</a>
  </div>
  <div class="nav-actions">
    <button class="btn btn-sm btn-primary">Action</button>
  </div>
</nav>

<!-- Sidebar -->
<aside class="sidebar">
  <div class="sidebar-section">
    <h3 class="sidebar-section-title">Section</h3>
    <a href="#" class="sidebar-item active">
      <span class="sidebar-item-icon">📊</span>
      <span>Item</span>
      <span class="sidebar-item-badge">3</span>
    </a>
  </div>
</aside>

<!-- Breadcrumbs -->
<nav class="breadcrumbs">
  <a href="#" class="breadcrumb-item">Home</a>
  <span class="breadcrumb-separator">/</span>
  <a href="#" class="breadcrumb-item">Dashboard</a>
  <span class="breadcrumb-separator">/</span>
  <span class="breadcrumb-item current">Page</span>
</nav>
```

---

## Tables

```html
<div class="table-container">
  <table class="table">
    <thead>
      <tr>
        <th class="sortable">Column 1</th>
        <th class="sortable sorted-asc">Column 2</th>
        <th>Column 3</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Data</td>
        <td>Data</td>
        <td>
          <button class="btn btn-sm btn-ghost">Action</button>
        </td>
      </tr>
      <tr class="selected">
        <td>Selected row</td>
        <td>Data</td>
        <td>Actions</td>
      </tr>
    </tbody>
  </table>
</div>

<!-- Compact Table -->
<table class="table compact">
  <!-- ... -->
</table>

<!-- Striped Table -->
<table class="table striped">
  <!-- ... -->
</table>
```

---

## Badges & Status

```html
<!-- Badges -->
<span class="badge badge-primary">Primary</span>
<span class="badge badge-success">Success</span>
<span class="badge badge-warning">Warning</span>
<span class="badge badge-error">Error</span>
<span class="badge badge-info">Info</span>
<span class="badge badge-neutral">Neutral</span>

<!-- Badge with Dot -->
<span class="badge badge-success with-dot">Online</span>

<!-- Status Indicators -->
<div class="status-indicator status-online">
  <span class="status-dot"></span>
  <span>Online</span>
</div>

<div class="status-indicator status-offline">
  <span class="status-dot"></span>
  <span>Offline</span>
</div>

<div class="status-indicator status-warning">
  <span class="status-dot"></span>
  <span>Warning</span>
</div>

<div class="status-indicator status-error">
  <span class="status-dot"></span>
  <span>Error</span>
</div>
```

---

## Alerts & Notifications

```html
<!-- Alert Banners -->
<div class="alert alert-success">
  <div class="alert-icon">✅</div>
  <div class="alert-content">
    <div class="alert-title">Success</div>
    <div class="alert-message">Operation completed</div>
  </div>
</div>

<div class="alert alert-warning">
  <div class="alert-icon">⚠️</div>
  <div class="alert-content">
    <div class="alert-title">Warning</div>
    <div class="alert-message">Please review</div>
  </div>
</div>

<div class="alert alert-error">
  <div class="alert-icon">❌</div>
  <div class="alert-content">
    <div class="alert-title">Error</div>
    <div class="alert-message">Something went wrong</div>
  </div>
</div>

<div class="alert alert-info">
  <div class="alert-icon">ℹ️</div>
  <div class="alert-content">
    <div class="alert-title">Info</div>
    <div class="alert-message">For your information</div>
  </div>
</div>

<!-- Toast Notification -->
<div class="toast-container">
  <div class="toast">
    <div class="toast-icon">✅</div>
    <div class="toast-content">
      <div class="toast-title">Success</div>
      <div class="toast-message">Saved!</div>
    </div>
    <button class="toast-close">×</button>
  </div>
</div>
```

---

## Modals

```html
<div class="modal-overlay">
  <div class="modal">
    <div class="modal-header">
      <h3 class="modal-title">Modal Title</h3>
      <button class="modal-close">×</button>
    </div>
    <div class="modal-body">
      <p>Modal content goes here</p>
    </div>
    <div class="modal-footer">
      <button class="btn btn-secondary">Cancel</button>
      <button class="btn btn-primary">Confirm</button>
    </div>
  </div>
</div>
```

---

## Loading States

```html
<!-- Spinner -->
<div class="spinner"></div>
<div class="spinner-lg"></div>

<!-- Button with Spinner -->
<button class="btn btn-primary" disabled>
  <div class="spinner"></div>
  <span>Loading...</span>
</button>

<!-- Progress Bar -->
<div class="progress-bar">
  <div class="progress-fill" style="width: 75%;"></div>
</div>

<!-- Success Progress -->
<div class="progress-bar success">
  <div class="progress-fill" style="width: 100%;"></div>
</div>

<!-- Indeterminate Progress -->
<div class="progress-bar indeterminate">
  <div class="progress-fill"></div>
</div>

<!-- Skeleton Loaders -->
<div class="skeleton skeleton-title"></div>
<div class="skeleton skeleton-text"></div>
<div class="skeleton skeleton-text"></div>
<div class="skeleton skeleton-avatar"></div>
<div class="skeleton skeleton-card"></div>
```

---

## Empty States

```html
<div class="empty-state">
  <div class="empty-state-icon">📭</div>
  <h3 class="empty-state-title">No data found</h3>
  <p class="empty-state-message">
    Get started by creating your first item
  </p>
  <div class="empty-state-actions">
    <button class="btn btn-primary">Create Item</button>
    <button class="btn btn-secondary">Learn More</button>
  </div>
</div>
```

---

## Layout Grid

```html
<!-- Dashboard Grid (12 columns) -->
<div class="dashboard-grid">
  <!-- 3 columns (25% width) -->
  <div class="col-span-3">Content</div>

  <!-- 4 columns (33% width) -->
  <div class="col-span-4">Content</div>

  <!-- 6 columns (50% width) -->
  <div class="col-span-6">Content</div>

  <!-- 8 columns (66% width) -->
  <div class="col-span-8">Content</div>

  <!-- Full width -->
  <div class="col-span-12">Content</div>
</div>

<!-- Typical Dashboard Layout -->
<div class="dashboard-grid">
  <!-- 4 stat cards across top -->
  <div class="col-span-3"><div class="stat-card">...</div></div>
  <div class="col-span-3"><div class="stat-card">...</div></div>
  <div class="col-span-3"><div class="stat-card">...</div></div>
  <div class="col-span-3"><div class="stat-card">...</div></div>

  <!-- Main chart (2/3 width) + sidebar (1/3 width) -->
  <div class="col-span-8"><div class="panel">Chart</div></div>
  <div class="col-span-4"><div class="panel">Sidebar</div></div>

  <!-- Full width table -->
  <div class="col-span-12"><div class="panel">Table</div></div>
</div>
```

---

## Page Layouts

```html
<!-- Full Layout with Sidebar -->
<div class="app-layout">
  <aside class="sidebar">Sidebar</aside>
  <main class="app-main">
    <div class="app-content">
      Content
    </div>
  </main>
</div>

<!-- Without Sidebar -->
<div class="app-main" style="margin-left: 0;">
  <div class="app-content">
    Content
  </div>
</div>
```

---

## Utility Classes

```html
<!-- Spacing -->
<div class="m-0">No margin</div>
<div class="mt-4">Margin top</div>
<div class="mb-6">Margin bottom</div>
<div class="p-4">Padding all sides</div>

<!-- Text -->
<p class="text-sm">Small text</p>
<p class="text-center">Centered text</p>
<p class="font-bold">Bold text</p>

<!-- Display -->
<div class="flex">Flexbox</div>
<div class="grid">Grid</div>
<div class="hidden">Hidden</div>

<!-- Flexbox -->
<div class="flex items-center">Center items</div>
<div class="flex justify-between">Space between</div>
<div class="flex gap-4">Gap spacing</div>
```

---

## CSS Custom Properties (Most Used)

```css
/* Colors */
var(--color-primary-700)
var(--color-success-600)
var(--color-warning-600)
var(--color-error-600)
var(--color-neutral-900)
var(--color-white)

/* Spacing */
var(--spacing-2)   /* 8px */
var(--spacing-4)   /* 16px */
var(--spacing-6)   /* 24px */
var(--spacing-8)   /* 32px */

/* Typography */
var(--font-size-xs)    /* 12px */
var(--font-size-sm)    /* 14px */
var(--font-size-base)  /* 16px */
var(--font-size-lg)    /* 20px */
var(--font-size-xl)    /* 24px */

/* Border Radius */
var(--radius-md)   /* 12px */
var(--radius-lg)   /* 16px */
var(--radius-full) /* Pill shape */

/* Shadows */
var(--shadow-sm)
var(--shadow-md)
var(--shadow-lg)

/* Transitions */
var(--duration-normal)  /* 200ms */
var(--ease-in-out)
var(--transition-base)
```

---

## Common Patterns

### Stat Cards Row
```html
<div class="dashboard-grid">
  <div class="col-span-3">
    <div class="stat-card">
      <div class="stat-icon">👥</div>
      <div class="stat-value">1,247</div>
      <div class="stat-label">Total Agents</div>
    </div>
  </div>
  <!-- Repeat 3 more times -->
</div>
```

### Form with Actions
```html
<div class="card">
  <div class="card-header">
    <h3 class="card-title">Form Title</h3>
  </div>
  <div class="card-body">
    <form>
      <!-- Form fields -->
    </form>
  </div>
  <div class="card-footer">
    <span></span>
    <div class="btn-group">
      <button class="btn btn-secondary">Cancel</button>
      <button class="btn btn-primary">Submit</button>
    </div>
  </div>
</div>
```

### Panel with Actions
```html
<div class="panel">
  <div class="panel-header">
    <h3 class="panel-title">Title</h3>
    <div class="panel-actions">
      <button class="btn btn-sm btn-ghost">Action 1</button>
      <button class="btn btn-sm btn-primary">Action 2</button>
    </div>
  </div>
  <div class="panel-body no-padding">
    <!-- Table or other content -->
  </div>
</div>
```

### Search + Action Header
```html
<div class="panel-header">
  <h3 class="panel-title">Items</h3>
  <div class="panel-actions">
    <input type="search" class="form-input" placeholder="Search...">
    <button class="btn btn-sm btn-primary">Add New</button>
  </div>
</div>
```

---

## Quick Tips

### Hover Effects
- Cards automatically lift on hover
- Buttons have built-in hover states
- Add `transition: var(--transition-base)` for smooth effects

### Spacing
- Use multiples of 8px (spacing scale)
- Card padding: `var(--spacing-6)` (24px)
- Button padding: `var(--spacing-3) var(--spacing-5)` (12px 20px)

### Colors
- Use semantic colors (success, warning, error, info) for status
- Use primary colors for interactive elements
- Use neutral colors for text and backgrounds

### Responsive
- Grid collapses to single column on mobile
- Sidebar hides on mobile (< 640px)
- Use `col-span-*` classes that auto-adjust

### Accessibility
- Always include labels for form inputs
- Use semantic HTML (button, nav, main, etc.)
- Add aria-labels for icon-only buttons
- Ensure sufficient color contrast

---

## Copy-Paste Examples

### Quick Dashboard
```html
<nav class="nav-bar">
  <a href="/" class="nav-logo">
    <span>🚀</span>
    <span>Dashboard</span>
  </a>
</nav>

<div class="app-main" style="margin-left: 0;">
  <div class="app-content">
    <h1 style="font-size: var(--font-size-3xl); margin-bottom: var(--spacing-6);">
      Dashboard
    </h1>

    <div class="dashboard-grid">
      <div class="col-span-3">
        <div class="stat-card">
          <div class="stat-value">100</div>
          <div class="stat-label">Metric</div>
        </div>
      </div>
      <div class="col-span-3">
        <div class="stat-card">
          <div class="stat-value">200</div>
          <div class="stat-label">Metric</div>
        </div>
      </div>
      <div class="col-span-3">
        <div class="stat-card">
          <div class="stat-value">300</div>
          <div class="stat-label">Metric</div>
        </div>
      </div>
      <div class="col-span-3">
        <div class="stat-card">
          <div class="stat-value">400</div>
          <div class="stat-label">Metric</div>
        </div>
      </div>
    </div>
  </div>
</div>
```

### Quick Form
```html
<div class="card" style="max-width: 500px; margin: var(--spacing-8) auto;">
  <div class="card-header">
    <h3 class="card-title">Form Title</h3>
  </div>
  <div class="card-body">
    <form>
      <div class="form-group">
        <label class="form-label required">Name</label>
        <input type="text" class="form-input" placeholder="Enter name">
      </div>
      <div class="form-group">
        <label class="form-label">Type</label>
        <select class="form-select">
          <option>Select...</option>
          <option>Option 1</option>
        </select>
      </div>
      <button type="submit" class="btn btn-primary btn-block">Submit</button>
    </form>
  </div>
</div>
```

### Quick Table
```html
<div class="panel">
  <div class="panel-header">
    <h3 class="panel-title">Data Table</h3>
  </div>
  <div class="panel-body no-padding">
    <div class="table-container">
      <table class="table">
        <thead>
          <tr>
            <th>Column 1</th>
            <th>Column 2</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Data</td>
            <td>Data</td>
            <td>
              <button class="btn btn-sm btn-ghost">View</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</div>
```
