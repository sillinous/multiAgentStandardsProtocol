# Design System Implementation Guide
## SuperStandard Multi-Agent Platform

---

## Quick Start

### 1. Include the Design System CSS

Add the design system stylesheet to your HTML:

```html
<link rel="stylesheet" href="/design-system.css">
```

### 2. Basic Page Structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Your Dashboard</title>
  <link rel="stylesheet" href="/design-system.css">
</head>
<body>
  <!-- Your content here -->
</body>
</html>
```

---

## Common Patterns

### Dashboard Layout

```html
<!-- Top Navigation -->
<nav class="nav-bar">
  <a href="/" class="nav-logo">
    <span class="logo-icon">🚀</span>
    <span>SuperStandard</span>
  </a>
  <div class="nav-links">
    <a href="/dashboard" class="nav-link active">Dashboard</a>
    <a href="/agents" class="nav-link">Agents</a>
  </div>
  <div class="nav-actions">
    <button class="btn btn-sm btn-primary">New Agent</button>
  </div>
</nav>

<!-- Layout Container -->
<div class="app-layout">
  <!-- Sidebar (optional) -->
  <aside class="sidebar">
    <div class="sidebar-section">
      <h3 class="sidebar-section-title">Navigation</h3>
      <a href="/dashboard" class="sidebar-item active">
        <span class="sidebar-item-icon">📊</span>
        <span>Dashboard</span>
      </a>
    </div>
  </aside>

  <!-- Main Content Area -->
  <main class="app-main">
    <div class="app-content">
      <!-- Page content goes here -->
    </div>
  </main>
</div>
```

### Metrics Dashboard Grid

```html
<div class="dashboard-grid">
  <!-- 4 stat cards in a row -->
  <div class="col-span-3">
    <div class="stat-card">
      <div class="stat-icon">👥</div>
      <div class="stat-value">1,247</div>
      <div class="stat-label">Total Agents</div>
      <div class="stat-change positive">↑ +12%</div>
    </div>
  </div>

  <div class="col-span-3">
    <div class="stat-card">
      <div class="stat-icon">🔄</div>
      <div class="stat-value">89</div>
      <div class="stat-label">Active Sessions</div>
    </div>
  </div>

  <div class="col-span-3">
    <div class="stat-card">
      <div class="stat-icon">💭</div>
      <div class="stat-value">15.2k</div>
      <div class="stat-label">Thoughts</div>
    </div>
  </div>

  <div class="col-span-3">
    <div class="stat-card">
      <div class="stat-icon">🎯</div>
      <div class="stat-value">342</div>
      <div class="stat-label">Patterns</div>
    </div>
  </div>

  <!-- Full-width chart panel -->
  <div class="col-span-12">
    <div class="panel">
      <div class="panel-header">
        <h3 class="panel-title">Activity Chart</h3>
        <div class="panel-actions">
          <button class="btn btn-sm btn-ghost">Export</button>
        </div>
      </div>
      <div class="panel-body">
        <!-- Chart goes here -->
      </div>
    </div>
  </div>
</div>
```

### Data Table

```html
<div class="panel">
  <div class="panel-header">
    <h3 class="panel-title">Active Agents</h3>
    <div class="panel-actions">
      <input type="search" class="form-input" placeholder="Search...">
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
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><code>agent-001</code></td>
            <td>DataCollector</td>
            <td>
              <div class="status-indicator status-online">
                <span class="status-dot"></span>
                <span>Online</span>
              </div>
            </td>
            <td>
              <div class="btn-group">
                <button class="btn btn-sm btn-ghost">View</button>
                <button class="btn btn-sm btn-ghost">Edit</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</div>
```

### Form Layout

```html
<div class="card">
  <div class="card-header">
    <h3 class="card-title">Register New Agent</h3>
  </div>
  <div class="card-body">
    <form>
      <div class="form-group">
        <label class="form-label required">Agent Name</label>
        <input type="text" class="form-input" placeholder="Enter name">
        <div class="form-help">Choose a unique name</div>
      </div>

      <div class="form-group">
        <label class="form-label">Agent Type</label>
        <select class="form-select">
          <option>Select type...</option>
          <option>Worker</option>
          <option>Coordinator</option>
        </select>
      </div>

      <div class="form-group">
        <label class="form-checkbox">
          <input type="checkbox" class="form-checkbox-input">
          <span class="form-checkbox-label">Enable monitoring</span>
        </label>
      </div>

      <div class="btn-group">
        <button type="submit" class="btn btn-primary">Register</button>
        <button type="button" class="btn btn-secondary">Cancel</button>
      </div>
    </form>
  </div>
</div>
```

### Modal Dialog

```html
<!-- Modal Overlay -->
<div class="modal-overlay">
  <div class="modal">
    <div class="modal-header">
      <h3 class="modal-title">Confirm Action</h3>
      <button class="modal-close">×</button>
    </div>
    <div class="modal-body">
      <p>Are you sure you want to delete this agent?</p>
    </div>
    <div class="modal-footer">
      <button class="btn btn-secondary">Cancel</button>
      <button class="btn btn-danger">Delete</button>
    </div>
  </div>
</div>
```

### Notification Toast

```html
<!-- Toast Container (fixed position) -->
<div class="toast-container">
  <div class="toast">
    <div class="toast-icon">✅</div>
    <div class="toast-content">
      <div class="toast-title">Success</div>
      <div class="toast-message">Agent registered successfully</div>
    </div>
    <button class="toast-close">×</button>
  </div>
</div>
```

### Alert Banner

```html
<div class="alert alert-success">
  <div class="alert-icon">✅</div>
  <div class="alert-content">
    <div class="alert-title">Operation successful</div>
    <div class="alert-message">Your changes have been saved</div>
  </div>
</div>
```

---

## JavaScript Integration Examples

### Real-time Data Updates

```javascript
// Update stat card value
function updateStat(value, label) {
  const statCard = document.querySelector('.stat-card');
  statCard.querySelector('.stat-value').textContent = value;
  statCard.querySelector('.stat-label').textContent = label;
}

// Add new row to table
function addTableRow(data) {
  const tbody = document.querySelector('.table tbody');
  const row = document.createElement('tr');
  row.innerHTML = `
    <td><code>${data.id}</code></td>
    <td>${data.name}</td>
    <td>
      <div class="status-indicator status-online">
        <span class="status-dot"></span>
        <span>Online</span>
      </div>
    </td>
    <td>
      <button class="btn btn-sm btn-ghost">View</button>
    </td>
  `;
  tbody.appendChild(row);
}
```

### Show/Hide Modal

```javascript
function showModal() {
  const overlay = document.querySelector('.modal-overlay');
  overlay.style.display = 'flex';
}

function hideModal() {
  const overlay = document.querySelector('.modal-overlay');
  overlay.style.display = 'none';
}

// Close modal when clicking overlay
document.querySelector('.modal-overlay').addEventListener('click', (e) => {
  if (e.target.classList.contains('modal-overlay')) {
    hideModal();
  }
});

// Close modal with X button
document.querySelector('.modal-close').addEventListener('click', hideModal);
```

### Show Toast Notification

```javascript
function showToast(title, message, type = 'success') {
  const container = document.querySelector('.toast-container') || createToastContainer();

  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.innerHTML = `
    <div class="toast-icon">${type === 'success' ? '✅' : '❌'}</div>
    <div class="toast-content">
      <div class="toast-title">${title}</div>
      <div class="toast-message">${message}</div>
    </div>
    <button class="toast-close">×</button>
  `;

  container.appendChild(toast);

  // Auto-remove after 5 seconds
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 5000);

  // Remove on click
  toast.querySelector('.toast-close').addEventListener('click', () => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  });
}

function createToastContainer() {
  const container = document.createElement('div');
  container.className = 'toast-container';
  document.body.appendChild(container);
  return container;
}

// Usage
showToast('Success', 'Agent registered successfully', 'success');
```

### Loading States

```javascript
// Show loading spinner in button
function setButtonLoading(button, isLoading) {
  if (isLoading) {
    button.disabled = true;
    button.innerHTML = `
      <div class="spinner"></div>
      <span>Loading...</span>
    `;
  } else {
    button.disabled = false;
    button.textContent = 'Submit';
  }
}

// Show skeleton loaders while loading data
function showSkeletonLoaders() {
  const container = document.querySelector('.panel-body');
  container.innerHTML = `
    <div class="skeleton skeleton-title"></div>
    <div class="skeleton skeleton-text"></div>
    <div class="skeleton skeleton-text"></div>
    <div class="skeleton skeleton-text" style="width: 70%;"></div>
  `;
}

// Show actual data
function showData(data) {
  const container = document.querySelector('.panel-body');
  container.innerHTML = data;
}
```

### Progress Bar Updates

```javascript
function updateProgress(percentage) {
  const progressFill = document.querySelector('.progress-fill');
  progressFill.style.width = percentage + '%';
}

// Simulate upload progress
let progress = 0;
const interval = setInterval(() => {
  progress += 10;
  updateProgress(progress);

  if (progress >= 100) {
    clearInterval(interval);
    showToast('Success', 'Upload complete!');
  }
}, 500);
```

---

## WebSocket Integration for Real-time Updates

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8080/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch(data.type) {
    case 'agent_registered':
      addTableRow(data.agent);
      updateStat(data.totalAgents, 'Total Agents');
      showToast('New Agent', `${data.agent.name} registered`);
      break;

    case 'session_created':
      updateStat(data.activeSessions, 'Active Sessions');
      break;

    case 'metric_update':
      updateMetrics(data.metrics);
      break;
  }
};

function updateMetrics(metrics) {
  document.querySelector('#totalAgents').textContent = metrics.totalAgents;
  document.querySelector('#activeSessions').textContent = metrics.activeSessions;
  document.querySelector('#totalThoughts').textContent = metrics.totalThoughts;
}
```

---

## Responsive Behavior

The design system includes built-in responsive breakpoints:

- **Mobile (< 640px)**: Single column layout, hidden sidebar
- **Tablet (641px - 1024px)**: 6-column grid
- **Desktop (> 1024px)**: 12-column grid

### Show/Hide Sidebar on Mobile

```javascript
function toggleSidebar() {
  const sidebar = document.querySelector('.sidebar');
  sidebar.classList.toggle('open');
}

// Add hamburger menu button for mobile
const menuButton = document.createElement('button');
menuButton.className = 'btn btn-icon';
menuButton.innerHTML = '☰';
menuButton.addEventListener('click', toggleSidebar);

// Insert before nav links
const navBar = document.querySelector('.nav-bar');
navBar.insertBefore(menuButton, navBar.querySelector('.nav-links'));

// Hide menu button on desktop
if (window.innerWidth > 640) {
  menuButton.style.display = 'none';
}
```

---

## Accessibility Best Practices

### Keyboard Navigation

```html
<!-- Ensure all interactive elements are keyboard accessible -->
<button class="btn btn-primary" tabindex="0">
  Click me
</button>

<!-- Skip to main content link (for screen readers) -->
<a href="#main-content" class="sr-only">Skip to main content</a>
<main id="main-content">
  <!-- Content -->
</main>
```

### ARIA Labels

```html
<!-- Button with icon only -->
<button class="btn btn-icon" aria-label="Close modal">
  ×
</button>

<!-- Status indicator -->
<div class="status-indicator status-online" role="status" aria-live="polite">
  <span class="status-dot"></span>
  <span>All systems operational</span>
</div>

<!-- Form validation -->
<input
  type="text"
  class="form-input error"
  aria-invalid="true"
  aria-describedby="error-message"
>
<div id="error-message" class="form-error" role="alert">
  This field is required
</div>
```

### Focus Management

```javascript
// Trap focus within modal
function trapFocus(element) {
  const focusableElements = element.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );

  const firstElement = focusableElements[0];
  const lastElement = focusableElements[focusableElements.length - 1];

  element.addEventListener('keydown', (e) => {
    if (e.key === 'Tab') {
      if (e.shiftKey && document.activeElement === firstElement) {
        lastElement.focus();
        e.preventDefault();
      } else if (!e.shiftKey && document.activeElement === lastElement) {
        firstElement.focus();
        e.preventDefault();
      }
    }
  });
}

// Usage
const modal = document.querySelector('.modal');
trapFocus(modal);
```

---

## Color Usage Guidelines

### Text Colors
- **Primary text**: `var(--color-neutral-900)` on light backgrounds
- **Secondary text**: `var(--color-neutral-700)` for less important info
- **Tertiary text**: `var(--color-neutral-600)` for metadata, timestamps
- **Disabled text**: `var(--color-neutral-500)`

### Background Colors
- **Page background**: `var(--color-neutral-50)`
- **Card background**: `var(--color-white)`
- **Hover background**: `var(--color-neutral-100)`

### Interactive Elements
- **Primary actions**: `var(--color-primary-700)`
- **Success states**: `var(--color-success-600)`
- **Warning states**: `var(--color-warning-600)`
- **Error states**: `var(--color-error-600)`

---

## Chart Integration

### Chart.js Example

```javascript
import Chart from 'chart.js/auto';

const ctx = document.getElementById('activityChart').getContext('2d');
const chart = new Chart(ctx, {
  type: 'line',
  data: {
    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    datasets: [{
      label: 'Agent Activity',
      data: [12, 19, 3, 5, 2, 3, 7],
      borderColor: 'var(--color-primary-700)',
      backgroundColor: 'var(--color-primary-100)',
      fill: true,
      tension: 0.4
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      }
    },
    scales: {
      y: {
        beginAtZero: true
      }
    }
  }
});

// Update chart with real-time data
function updateChart(newData) {
  chart.data.datasets[0].data = newData;
  chart.update('none'); // 'none' = no animation for performance
}
```

---

## Performance Tips

### 1. Use CSS Transitions (not JavaScript)
```css
/* Good - GPU accelerated */
.card {
  transform: translateY(0);
  transition: transform 0.3s ease;
}

.card:hover {
  transform: translateY(-5px);
}
```

### 2. Debounce Frequent Updates
```javascript
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// Usage
const debouncedUpdate = debounce(updateMetrics, 300);
ws.onmessage = (event) => {
  debouncedUpdate(JSON.parse(event.data));
};
```

### 3. Batch DOM Updates
```javascript
// Bad - multiple reflows
for (let i = 0; i < 100; i++) {
  const row = createRow(data[i]);
  tbody.appendChild(row);
}

// Good - single reflow
const fragment = document.createDocumentFragment();
for (let i = 0; i < 100; i++) {
  fragment.appendChild(createRow(data[i]));
}
tbody.appendChild(fragment);
```

---

## Browser Support

Tested and supported in:
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

### Fallbacks for Older Browsers

```css
/* Fallback for CSS custom properties */
.btn-primary {
  background: #4f46e5; /* Fallback */
  background: var(--color-primary-700);
}

/* Fallback for CSS Grid */
@supports not (display: grid) {
  .dashboard-grid {
    display: flex;
    flex-wrap: wrap;
  }
}
```

---

## Common Pitfalls to Avoid

### 1. Don't Override Base Styles Unnecessarily
```css
/* Bad */
.my-button {
  padding: 10px;
  border-radius: 5px;
  /* ... duplicating all button styles */
}

/* Good */
<button class="btn btn-primary">My Button</button>
```

### 2. Use Design Tokens (CSS Variables)
```css
/* Bad */
.custom-card {
  border-radius: 12px;
  padding: 24px;
}

/* Good */
.custom-card {
  border-radius: var(--radius-lg);
  padding: var(--spacing-6);
}
```

### 3. Don't Hardcode Colors
```css
/* Bad */
.status {
  color: #22c55e;
}

/* Good */
.status {
  color: var(--color-success-600);
}
```

---

## Migration from Existing Dashboards

### Step 1: Replace Inline Styles
```html
<!-- Before -->
<div style="padding: 20px; background: white; border-radius: 10px;">
  Content
</div>

<!-- After -->
<div class="card">
  Content
</div>
```

### Step 2: Use Semantic Components
```html
<!-- Before -->
<div class="box">
  <div class="box-header">Title</div>
  <div class="box-body">Content</div>
</div>

<!-- After -->
<div class="panel">
  <div class="panel-header">
    <h3 class="panel-title">Title</h3>
  </div>
  <div class="panel-body">
    Content
  </div>
</div>
```

### Step 3: Update Color Classes
```html
<!-- Before -->
<span class="green-badge">Success</span>

<!-- After -->
<span class="badge badge-success">Success</span>
```

---

## Questions & Support

For questions about implementation or to report issues:

1. Check the **DESIGN_SYSTEM.md** for complete specifications
2. View **design-system-showcase.html** for visual examples
3. Refer to existing dashboard implementations in `/src/superstandard/api/`

**Remember**: Consistency is key. Use the design system components as-is whenever possible, and only create custom components when absolutely necessary.
