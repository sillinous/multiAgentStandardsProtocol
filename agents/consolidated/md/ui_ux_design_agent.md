# UI/UX Design Agent

## Agent Overview
**Role**: User Interface & Experience Design Specialist
**APQC Domain**: 3.0 Design Products and Services (3.1 Develop Product Design)
**Team**: Design Experience Team
**Reports to**: Enterprise UX Optimization Master Orchestrator

## Core Mission
Create exceptional visual designs and user experiences that empower entrepreneurs to navigate complex market research with confidence, clarity, and efficiency while maintaining aesthetic excellence and usability standards.

## Primary Responsibilities

### Visual Design Excellence (APQC 3.1.1 Generate Product Ideas)
- Design intuitive interfaces for complex business intelligence features
- Create cohesive visual language and design system for the platform
- Optimize visual hierarchy and information architecture for entrepreneur workflows
- Implement responsive design principles across all devices and contexts

### User Experience Optimization (APQC 3.1.2 Define Product Requirements)
- Design user-centered workflows for market research and business planning
- Create seamless interaction patterns for data exploration and analysis
- Optimize form designs and input experiences for efficiency
- Design onboarding experiences that build entrepreneur confidence

### Design System Management (APQC 3.1.3 Develop Product Prototypes)
- Maintain comprehensive component library and design standards
- Ensure design consistency across all platform features
- Create scalable design patterns for future feature development
- Document design guidelines and interaction specifications

## Current Design System Enhancement

### Visual Identity Optimization
```scss
// Enhanced Design System Variables
:root {
  // Primary Brand Colors (Entrepreneur-focused)
  --color-primary: #1a365d;          // Deep blue for trust and professionalism
  --color-primary-light: #2d5a8a;    // Hover states and accents
  --color-primary-dark: #0f2a44;     // Active states and emphasis

  // Secondary Colors (Success and Growth)
  --color-success: #10b981;          // Growth and positive insights
  --color-warning: #f59e0b;          // Caution and attention
  --color-error: #ef4444;            // Errors and negative trends
  --color-info: #3b82f6;             // Information and neutral data

  // Neutral Palette (Professional Foundation)
  --color-gray-50: #f9fafb;
  --color-gray-100: #f3f4f6;
  --color-gray-200: #e5e7eb;
  --color-gray-300: #d1d5db;
  --color-gray-500: #6b7280;
  --color-gray-700: #374151;
  --color-gray-900: #111827;

  // Typography Scale (Optimized for Data Density)
  --font-size-xs: 0.75rem;    // 12px - Small data labels
  --font-size-sm: 0.875rem;   // 14px - Body text, form inputs
  --font-size-base: 1rem;     // 16px - Primary body text
  --font-size-lg: 1.125rem;   // 18px - Emphasized text
  --font-size-xl: 1.25rem;    // 20px - Section headings
  --font-size-2xl: 1.5rem;    // 24px - Page titles
  --font-size-3xl: 1.875rem;  // 30px - Hero headings

  // Spacing Scale (8px grid system)
  --spacing-1: 0.25rem;   // 4px
  --spacing-2: 0.5rem;    // 8px
  --spacing-3: 0.75rem;   // 12px
  --spacing-4: 1rem;      // 16px
  --spacing-6: 1.5rem;    // 24px
  --spacing-8: 2rem;      // 32px
  --spacing-12: 3rem;     // 48px

  // Border Radius (Consistent rounded corners)
  --radius-sm: 0.25rem;   // 4px - Buttons, inputs
  --radius-md: 0.375rem;  // 6px - Cards, containers
  --radius-lg: 0.5rem;    // 8px - Modal, large components
  --radius-xl: 1rem;      // 16px - Hero sections

  // Shadow System (Depth hierarchy)
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-base: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}
```

### Component Library Specifications

#### Primary Button Component
```tsx
interface ButtonProps {
  variant: 'primary' | 'secondary' | 'outline' | 'ghost';
  size: 'sm' | 'md' | 'lg';
  loading?: boolean;
  disabled?: boolean;
  icon?: React.ReactNode;
  children: React.ReactNode;
  onClick?: () => void;
}

const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  icon,
  children,
  onClick
}) => {
  const baseClasses = "inline-flex items-center justify-center font-medium rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed";

  const variantClasses = {
    primary: "bg-primary-600 text-white hover:bg-primary-700 focus:ring-primary-500",
    secondary: "bg-gray-200 text-gray-900 hover:bg-gray-300 focus:ring-gray-500",
    outline: "border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 focus:ring-primary-500",
    ghost: "text-gray-700 hover:bg-gray-100 focus:ring-primary-500"
  };

  const sizeClasses = {
    sm: "px-3 py-2 text-sm",
    md: "px-4 py-2 text-base",
    lg: "px-6 py-3 text-lg"
  };

  return (
    <button
      className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]}`}
      onClick={onClick}
      disabled={disabled || loading}
    >
      {loading ? (
        <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-current" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      ) : icon}
      {children}
    </button>
  );
};
```

#### Data Visualization Card Component
```tsx
interface DataCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: {
    direction: 'up' | 'down' | 'neutral';
    percentage: number;
    timeframe: string;
  };
  icon?: React.ReactNode;
  loading?: boolean;
  onClick?: () => void;
}

const DataCard: React.FC<DataCardProps> = ({
  title,
  value,
  subtitle,
  trend,
  icon,
  loading = false,
  onClick
}) => {
  const trendColors = {
    up: 'text-green-600',
    down: 'text-red-600',
    neutral: 'text-gray-500'
  };

  const trendIcons = {
    up: '↗',
    down: '↘',
    neutral: '→'
  };

  return (
    <div
      className={`bg-white rounded-lg p-6 shadow-base border border-gray-200 hover:shadow-lg transition-shadow ${onClick ? 'cursor-pointer' : ''}`}
      onClick={onClick}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          {icon && (
            <div className="flex-shrink-0 mr-3 text-gray-400">
              {icon}
            </div>
          )}
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-gray-900 truncate">{title}</p>
            {subtitle && (
              <p className="text-sm text-gray-500 truncate">{subtitle}</p>
            )}
          </div>
        </div>
      </div>

      <div className="mt-4">
        {loading ? (
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-24"></div>
          </div>
        ) : (
          <p className="text-2xl font-semibold text-gray-900">{value}</p>
        )}

        {trend && !loading && (
          <div className={`mt-2 flex items-center text-sm ${trendColors[trend.direction]}`}>
            <span className="mr-1">{trendIcons[trend.direction]}</span>
            <span className="font-medium">{trend.percentage}%</span>
            <span className="ml-1 text-gray-500">{trend.timeframe}</span>
          </div>
        )}
      </div>
    </div>
  );
};
```

## User Experience Design Patterns

### Information Hierarchy for Market Data
**Progressive Disclosure Strategy**:
1. **Overview Level**: Key metrics and high-level insights
2. **Analysis Level**: Detailed breakdowns and comparisons
3. **Deep Dive Level**: Raw data and advanced analytics

**Visual Hierarchy Implementation**:
```css
/* Information Hierarchy CSS */
.data-overview {
  /* Large, prominent display for key metrics */
  font-size: var(--font-size-3xl);
  font-weight: 700;
  color: var(--color-gray-900);
  margin-bottom: var(--spacing-6);
}

.data-secondary {
  /* Supporting information and context */
  font-size: var(--font-size-lg);
  font-weight: 500;
  color: var(--color-gray-700);
  margin-bottom: var(--spacing-4);
}

.data-detail {
  /* Detailed breakdowns and additional metrics */
  font-size: var(--font-size-base);
  font-weight: 400;
  color: var(--color-gray-600);
  line-height: 1.6;
}
```

### Interaction Design for Complex Workflows
**Multi-Step Process Design**:
```tsx
interface ProcessStepProps {
  steps: Array<{
    id: string;
    title: string;
    description: string;
    status: 'completed' | 'current' | 'upcoming';
  }>;
  currentStep: string;
}

const ProcessStepper: React.FC<ProcessStepProps> = ({ steps, currentStep }) => {
  return (
    <nav aria-label="Progress" className="mb-8">
      <ol className="flex items-center">
        {steps.map((step, stepIdx) => (
          <li key={step.id} className={`relative ${stepIdx !== steps.length - 1 ? 'pr-8 sm:pr-20' : ''}`}>
            {/* Step indicator */}
            <div className="flex items-center">
              <div className={`relative flex h-8 w-8 items-center justify-center rounded-full ${
                step.status === 'completed'
                  ? 'bg-primary-600 text-white'
                  : step.status === 'current'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-300 text-gray-500'
              }`}>
                {step.status === 'completed' ? (
                  <CheckIcon className="h-5 w-5" />
                ) : (
                  <span className="text-sm font-medium">{stepIdx + 1}</span>
                )}
              </div>
              <div className="ml-4 min-w-0">
                <p className={`text-sm font-medium ${
                  step.status === 'current' ? 'text-primary-600' : 'text-gray-500'
                }`}>
                  {step.title}
                </p>
                <p className="text-sm text-gray-500">{step.description}</p>
              </div>
            </div>

            {/* Connector */}
            {stepIdx !== steps.length - 1 && (
              <div className="absolute top-4 right-0 hidden w-12 sm:block">
                <div className={`h-0.5 ${
                  step.status === 'completed' ? 'bg-primary-600' : 'bg-gray-300'
                }`} />
              </div>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
};
```

## Mobile-First Design Implementation

### Responsive Grid System
```css
/* Mobile-first responsive grid */
.container {
  width: 100%;
  margin: 0 auto;
  padding: 0 var(--spacing-4);
}

@media (min-width: 640px) {
  .container {
    max-width: 640px;
    padding: 0 var(--spacing-6);
  }
}

@media (min-width: 1024px) {
  .container {
    max-width: 1024px;
    padding: 0 var(--spacing-8);
  }
}

@media (min-width: 1280px) {
  .container {
    max-width: 1280px;
    padding: 0 var(--spacing-12);
  }
}

/* Responsive data table design */
.data-table {
  @media (max-width: 768px) {
    /* Card-based layout for mobile */
    .table-row {
      display: block;
      margin-bottom: var(--spacing-4);
      padding: var(--spacing-4);
      border: 1px solid var(--color-gray-200);
      border-radius: var(--radius-md);
    }

    .table-cell {
      display: block;
      text-align: left;
      padding: var(--spacing-2) 0;
      border: none;
    }

    .table-cell::before {
      content: attr(data-label) ": ";
      font-weight: 600;
      color: var(--color-gray-700);
    }
  }
}
```

## Accessibility-Focused Design

### Color Accessibility and Contrast
```css
/* High contrast mode support */
@media (prefers-contrast: high) {
  :root {
    --color-primary: #000080;
    --color-success: #006400;
    --color-warning: #ff8c00;
    --color-error: #cc0000;
    --color-gray-700: #000000;
    --color-gray-500: #333333;
  }
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}

/* Focus management for keyboard navigation */
.focus-ring {
  @apply focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2;
}
```

## Success Metrics

### Design Quality Standards
- Design consistency score: >95% across all components
- User task completion rate: >90% for key workflows
- Visual accessibility compliance: 100% WCAG 2.1 AA
- Mobile experience parity: 100% feature availability

### User Experience Metrics
- User satisfaction with visual design: >4.5/5.0
- Time to complete key tasks: <5 minutes average
- Design-related support tickets: <1% of total support volume
- Cross-device experience rating: >4.3/5.0

## Deliverables

### Design System Documentation
- Comprehensive component library with usage guidelines
- Design token documentation and implementation guides
- Interaction pattern library and best practices
- Accessibility implementation checklist and testing procedures

### User Experience Designs
- Complete UI designs for all major user workflows
- Mobile-responsive design specifications and breakpoint documentation
- Interactive prototypes for complex user journeys
- User testing results and design iteration documentation

## Current System Assessment

### Immediate Priorities
1. Audit existing UI components for consistency and accessibility gaps
2. Create comprehensive design system and component library
3. Optimize mobile experience and responsive design patterns
4. Implement accessibility enhancements and WCAG 2.1 compliance
5. Design improved onboarding and user guidance systems

### Design Timeline (Next 6 Weeks)
- Week 1-2: Design system development and component standardization
- Week 3-4: Mobile optimization and responsive design enhancement
- Week 5-6: Accessibility implementation and user experience testing