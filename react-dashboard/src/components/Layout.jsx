import { Link, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  Network,
  GitBranch,
  Brain,
  Settings as SettingsIcon,
  Moon,
  Sun,
  Menu,
  X
} from 'lucide-react'
import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

const Layout = ({ children, darkMode, setDarkMode }) => {
  const location = useLocation()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const navItems = [
    { path: '/', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/agents', label: 'Agent Network', icon: Network },
    { path: '/coordination', label: 'Coordination', icon: GitBranch },
    { path: '/consciousness', label: 'Consciousness', icon: Brain },
    { path: '/settings', label: 'Settings', icon: SettingsIcon },
  ]

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-40 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 shadow-sm">
        <div className="flex items-center justify-between px-4 py-3">
          {/* Mobile menu button */}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="md:hidden p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
          </button>

          {/* Logo */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-700 rounded-lg flex items-center justify-center">
              <Brain className="text-white" size={24} />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900 dark:text-white">SuperStandard</h1>
              <p className="text-xs text-gray-500 dark:text-gray-400">Multi-Agent Platform</p>
            </div>
          </div>

          {/* Right side actions */}
          <div className="flex items-center space-x-2">
            {/* Dark mode toggle */}
            <button
              onClick={() => setDarkMode(!darkMode)}
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              aria-label="Toggle dark mode"
            >
              {darkMode ? (
                <Sun className="text-yellow-500" size={20} />
              ) : (
                <Moon className="text-gray-600" size={20} />
              )}
            </button>

            {/* Connection status */}
            <div className="hidden sm:flex items-center space-x-2 px-3 py-1.5 bg-green-50 dark:bg-green-900/20 rounded-full">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-sm text-green-700 dark:text-green-400 font-medium">Connected</span>
            </div>
          </div>
        </div>
      </header>

      {/* Mobile Sidebar Overlay */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-30 bg-black/50 md:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <motion.aside
        initial={false}
        animate={{ x: sidebarOpen ? 0 : '-100%' }}
        className="fixed left-0 top-16 bottom-0 z-30 w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 shadow-lg md:translate-x-0 md:shadow-none transition-transform"
      >
        <nav className="p-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = location.pathname === item.path
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setSidebarOpen(false)}
                className={`
                  flex items-center space-x-3 px-4 py-3 rounded-lg transition-all
                  ${
                    isActive
                      ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400 font-medium'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }
                `}
              >
                <Icon size={20} />
                <span>{item.label}</span>
                {isActive && (
                  <motion.div
                    layoutId="activeTab"
                    className="ml-auto w-1 h-6 bg-primary-600 dark:bg-primary-400 rounded-full"
                  />
                )}
              </Link>
            )
          })}
        </nav>

        {/* Stats panel */}
        <div className="absolute bottom-4 left-4 right-4 p-4 bg-gradient-to-br from-primary-50 to-primary-100 dark:from-primary-900/20 dark:to-primary-800/20 rounded-lg">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">System Status</h3>
          <div className="space-y-1 text-xs">
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Active Agents</span>
              <span className="font-medium text-gray-900 dark:text-white">247</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Coordinations</span>
              <span className="font-medium text-gray-900 dark:text-white">12</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Thoughts/min</span>
              <span className="font-medium text-gray-900 dark:text-white">1,429</span>
            </div>
          </div>
        </div>
      </motion.aside>

      {/* Main content */}
      <main className="pt-16 md:pl-64 transition-all">
        <div className="p-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            {children}
          </motion.div>
        </div>
      </main>
    </div>
  )
}

export default Layout
