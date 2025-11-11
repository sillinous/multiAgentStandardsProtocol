import { motion } from 'framer-motion'
import { Save, Key, Bell, Shield, Database } from 'lucide-react'

const Settings = () => {
  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Settings</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">Configure your SuperStandard platform</p>
      </div>

      {/* API Configuration */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm"
      >
        <div className="flex items-center space-x-3 mb-4">
          <Key className="text-primary-600" />
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">API Configuration</h2>
        </div>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              API Endpoint
            </label>
            <input
              type="text"
              defaultValue="http://localhost:8080/api"
              className="w-full px-4 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              API Key
            </label>
            <input
              type="password"
              placeholder="Enter your API key"
              className="w-full px-4 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500"
            />
          </div>
        </div>
      </motion.div>

      {/* Notifications */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm"
      >
        <div className="flex items-center space-x-3 mb-4">
          <Bell className="text-primary-600" />
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Notifications</h2>
        </div>
        <div className="space-y-3">
          {[
            { label: 'Agent Status Changes', enabled: true },
            { label: 'Pattern Discoveries', enabled: true },
            { label: 'System Alerts', enabled: true },
            { label: 'Performance Warnings', enabled: false },
          ].map((item) => (
            <div key={item.label} className="flex items-center justify-between">
              <span className="text-gray-700 dark:text-gray-300">{item.label}</span>
              <button
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  item.enabled ? 'bg-primary-600' : 'bg-gray-300 dark:bg-gray-600'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    item.enabled ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Save button */}
      <motion.button
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="flex items-center space-x-2 px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
      >
        <Save size={20} />
        <span>Save Changes</span>
      </motion.button>
    </div>
  )
}

export default Settings
