# SuperStandard React Dashboard 🚀

A beautiful, modern React dashboard for the SuperStandard Multi-Agent Platform. Built with React 18, Tailwind CSS, Framer Motion, and Recharts.

![Dashboard Preview](https://img.shields.io/badge/React-18.2-blue) ![Tailwind CSS](https://img.shields.io/badge/TailwindCSS-3.3-38B2AC) ![Vite](https://img.shields.io/badge/Vite-5.0-646CFF)

## ✨ Features

### 🎨 Beautiful Modern UI
- **Dark Mode Support** - Toggle between light and dark themes
- **Responsive Design** - Works perfectly on mobile, tablet, and desktop
- **Smooth Animations** - Powered by Framer Motion
- **Custom Color Palette** - Professional gradient-based color system

### 📊 Rich Visualizations
- **Real-time Charts** - Line, Area, Bar, and Pie charts using Recharts
- **Live Data Updates** - WebSocket integration for real-time monitoring
- **Interactive Dashboards** - 5 comprehensive dashboard views

### 🤖 Multi-Agent Management
- **Agent Network View** - Monitor all agents with status, load, and capabilities
- **Coordination Dashboard** - Track multi-agent coordination sessions
- **Consciousness View** - Visualize emergent patterns from collective intelligence
- **Settings Panel** - Configure API endpoints and preferences

### 🎯 Key Screens

1. **Dashboard** - Overview with stats, charts, and recent activity
2. **Agent Network** - Manage and monitor your agent fleet
3. **Coordination** - Multi-agent coordination sessions
4. **Consciousness** - Collective intelligence patterns
5. **Settings** - Configuration and preferences

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm/yarn/pnpm
- SuperStandard API server running (default: `http://localhost:8080`)

### Installation

```bash
# Navigate to the dashboard directory
cd react-dashboard

# Install dependencies
npm install
# or
yarn install
# or
pnpm install
```

### Development

```bash
# Start the development server
npm run dev
# or
yarn dev
# or
pnpm dev
```

The dashboard will be available at `http://localhost:3000`

### Build for Production

```bash
# Build the production bundle
npm run build
# or
yarn build
# or
pnpm build

# Preview the production build
npm run preview
# or
yarn preview
# or
pnpm preview
```

## 📁 Project Structure

```
react-dashboard/
├── src/
│   ├── components/
│   │   └── Layout.jsx          # Main layout with sidebar and header
│   ├── pages/
│   │   ├── Dashboard.jsx       # Main dashboard view
│   │   ├── AgentNetwork.jsx    # Agent management view
│   │   ├── Coordination.jsx    # Coordination sessions view
│   │   ├── Consciousness.jsx   # Collective consciousness view
│   │   └── Settings.jsx        # Settings and configuration
│   ├── hooks/                  # Custom React hooks (future)
│   ├── utils/                  # Utility functions (future)
│   ├── App.jsx                 # Main app component with routing
│   ├── main.jsx                # React entry point
│   └── index.css               # Global styles and Tailwind imports
├── public/                     # Static assets
├── index.html                  # HTML template
├── vite.config.js              # Vite configuration
├── tailwind.config.js          # Tailwind CSS configuration
├── package.json                # Dependencies and scripts
└── README.md                   # This file
```

## 🎨 Design System

### Colors

The dashboard uses a professional color palette with semantic meaning:

- **Primary (Blue)**: Main actions, links, and primary UI elements
- **Success (Green)**: Healthy states, confirmations, positive metrics
- **Warning (Orange)**: Warnings, busy states, attention needed
- **Danger (Red)**: Errors, offline states, critical issues
- **Purple**: Coordination, consciousness, advanced features

### Typography

- **Headings**: Bold, clear hierarchy
- **Body**: Readable, comfortable line height
- **Code**: Monospace for IDs and technical content

### Spacing

Consistent spacing system based on Tailwind's spacing scale (4px base unit).

## 🔌 API Integration

### Connecting to SuperStandard API

The dashboard proxies API requests through Vite's dev server:

```javascript
// vite.config.js
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8080',  // Your API server
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8080',     // WebSocket endpoint
        ws: true,
      },
    },
  },
})
```

### Example API Calls

```javascript
// Fetch agents
const response = await fetch('/api/anp/agents')
const data = await response.json()

// Register an agent
await fetch('/api/anp/agents/register', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'your-api-key',  // Required if auth is enabled
  },
  body: JSON.stringify({
    agent_id: 'my-agent',
    agent_type: 'analyzer',
    capabilities: ['analysis', 'processing'],
  }),
})
```

### WebSocket Integration

```javascript
// Connect to WebSocket for real-time updates
const ws = new WebSocket('ws://localhost:8080/ws/dashboard?token=your-api-key')

ws.onmessage = (event) => {
  const data = JSON.parse(event.data)
  // Handle real-time updates
  console.log('Real-time update:', data)
}
```

## 🛠️ Customization

### Adding New Pages

1. Create a new component in `src/pages/`:

```jsx
// src/pages/MyNewPage.jsx
import { motion } from 'framer-motion'

const MyNewPage = () => {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
        My New Page
      </h1>
      {/* Your content */}
    </div>
  )
}

export default MyNewPage
```

2. Add route in `App.jsx`:

```jsx
import MyNewPage from './pages/MyNewPage'

// In Routes component:
<Route path="/my-page" element={<MyNewPage />} />
```

3. Add navigation item in `Layout.jsx`:

```jsx
const navItems = [
  // ... existing items
  { path: '/my-page', label: 'My Page', icon: YourIcon },
]
```

### Customizing Colors

Edit `tailwind.config.js`:

```javascript
theme: {
  extend: {
    colors: {
      primary: {
        // Your custom color scale
        500: '#your-color',
      },
    },
  },
},
```

### Adding Charts

Install additional chart libraries if needed:

```bash
npm install recharts  # Already included
npm install d3        # For D3.js integration
npm install chart.js  # For Chart.js
```

## 🧪 Testing (Future Enhancement)

```bash
# Run tests (to be implemented)
npm test

# Run tests with coverage
npm test -- --coverage
```

## 📦 Dependencies

### Core Dependencies

- **react** & **react-dom**: React 18
- **react-router-dom**: Client-side routing
- **recharts**: Chart library
- **framer-motion**: Animation library
- **lucide-react**: Beautiful icon library
- **clsx** & **tailwind-merge**: Utility class helpers

### Dev Dependencies

- **vite**: Fast build tool
- **@vitejs/plugin-react**: React plugin for Vite
- **tailwindcss**: Utility-first CSS framework
- **autoprefixer** & **postcss**: CSS processing
- **eslint**: Code linting

## 🚢 Deployment

### Deploy to Vercel

```bash
npm install -g vercel
vercel
```

### Deploy to Netlify

```bash
npm run build
# Upload the `dist` folder to Netlify
```

### Deploy with Docker

```dockerfile
# Dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

```bash
docker build -t superstandard-dashboard .
docker run -p 80:80 superstandard-dashboard
```

## 🎯 Performance Optimization

### Current Optimizations

- ✅ Code splitting with React Router
- ✅ Lazy loading of components
- ✅ Optimized bundle size with Vite
- ✅ Tree-shaking of unused code
- ✅ CSS purging with Tailwind

### Lighthouse Scores (Target)

- Performance: 95+
- Accessibility: 100
- Best Practices: 100
- SEO: 100

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -am 'Add my feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Submit a pull request

### Code Style

- Use functional components with hooks
- Follow React best practices
- Use Tailwind CSS for styling
- Add comments for complex logic
- Keep components small and focused

## 📝 License

This project is part of the SuperStandard Multi-Agent Platform.
License: Apache 2.0

## 🙏 Acknowledgments

- **React Team** - For the amazing React library
- **Tailwind CSS** - For the utility-first CSS framework
- **Recharts** - For beautiful, customizable charts
- **Framer Motion** - For smooth animations
- **Lucide** - For the beautiful icon set

## 📞 Support

For questions or issues:

1. Check the main SuperStandard documentation
2. Open an issue on GitHub
3. Join our community discussions

---

**Made with ❤️ for the SuperStandard Multi-Agent Platform**

🚀 **Start building beautiful multi-agent dashboards today!**
