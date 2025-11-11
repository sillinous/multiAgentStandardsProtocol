import { motion } from 'framer-motion'
import { useState } from 'react'
import {
  Search,
  Filter,
  Plus,
  Activity,
  AlertCircle,
  CheckCircle,
  XCircle,
  MoreVertical,
  Eye,
  Trash2,
  RefreshCw,
} from 'lucide-react'

const AgentNetwork = () => {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedType, setSelectedType] = useState('all')

  const agents = [
    {
      id: 'agent-001',
      name: 'Market Analyzer Alpha',
      type: 'Analyzer',
      status: 'healthy',
      load: 34,
      capabilities: ['market-analysis', 'trend-detection', 'forecasting'],
      uptime: '99.8%',
      tasks: 1247,
      lastSeen: '2 min ago',
    },
    {
      id: 'agent-002',
      name: 'Data Processor Beta',
      type: 'Processor',
      status: 'healthy',
      load: 67,
      capabilities: ['data-processing', 'transformation', 'validation'],
      uptime: '99.2%',
      tasks: 3891,
      lastSeen: '1 min ago',
    },
    {
      id: 'agent-003',
      name: 'ML Engine Gamma',
      type: 'ML/AI',
      status: 'busy',
      load: 89,
      capabilities: ['machine-learning', 'prediction', 'classification'],
      uptime: '100%',
      tasks: 2156,
      lastSeen: 'Just now',
    },
    {
      id: 'agent-004',
      name: 'Coordinator Delta',
      type: 'Coordinator',
      status: 'healthy',
      load: 23,
      capabilities: ['coordination', 'task-assignment', 'monitoring'],
      uptime: '99.9%',
      tasks: 567,
      lastSeen: '3 min ago',
    },
    {
      id: 'agent-005',
      name: 'Monitor Epsilon',
      type: 'Monitor',
      status: 'warning',
      load: 12,
      capabilities: ['monitoring', 'alerting', 'logging'],
      uptime: '98.5%',
      tasks: 892,
      lastSeen: '10 min ago',
    },
    {
      id: 'agent-006',
      name: 'Security Agent Zeta',
      type: 'Security',
      status: 'offline',
      load: 0,
      capabilities: ['security', 'compliance', 'audit'],
      uptime: '97.8%',
      tasks: 445,
      lastSeen: '2 hours ago',
    },
  ]

  const statusConfig = {
    healthy: { color: 'green', icon: CheckCircle, label: 'Healthy' },
    busy: { color: 'yellow', icon: Activity, label: 'Busy' },
    warning: { color: 'orange', icon: AlertCircle, label: 'Warning' },
    offline: { color: 'red', icon: XCircle, label: 'Offline' },
  }

  const getLoadColor = (load) => {
    if (load < 40) return 'bg-green-500'
    if (load < 70) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  const filteredAgents = agents.filter((agent) => {
    const matchesSearch = agent.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      agent.id.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesType = selectedType === 'all' || agent.type === selectedType
    return matchesSearch && matchesType
  })

  const agentTypes = ['all', ...new Set(agents.map((a) => a.type))]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Agent Network</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Manage and monitor your agent fleet</p>
        </div>
        <button className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
          <Plus size={20} />
          <span>Register Agent</span>
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Total Agents', value: agents.length, color: 'blue' },
          {
            label: 'Healthy',
            value: agents.filter((a) => a.status === 'healthy').length,
            color: 'green',
          },
          {
            label: 'Busy',
            value: agents.filter((a) => a.status === 'busy').length,
            color: 'yellow',
          },
          {
            label: 'Offline',
            value: agents.filter((a) => a.status === 'offline').length,
            color: 'red',
          },
        ].map((stat, index) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: index * 0.1 }}
            className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm"
          >
            <div className="text-sm text-gray-500 dark:text-gray-400">{stat.label}</div>
            <div className="text-2xl font-bold text-gray-900 dark:text-white mt-1">{stat.value}</div>
          </motion.div>
        ))}
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm">
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Search */}
          <div className="flex-1 relative">
            <Search
              className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
              size={20}
            />
            <input
              type="text"
              placeholder="Search agents..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>

          {/* Type filter */}
          <div className="flex items-center space-x-2">
            <Filter size={20} className="text-gray-400" />
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="px-4 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              {agentTypes.map((type) => (
                <option key={type} value={type}>
                  {type.charAt(0).toUpperCase() + type.slice(1)}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Agents list */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {filteredAgents.map((agent, index) => {
          const StatusIcon = statusConfig[agent.status].icon
          const statusColor = statusConfig[agent.status].color

          return (
            <motion.div
              key={agent.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm hover:shadow-md transition-all"
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-start space-x-3">
                  <div className={`p-2 rounded-lg bg-${statusColor}-100 dark:bg-${statusColor}-900/20`}>
                    <StatusIcon className={`text-${statusColor}-600 dark:text-${statusColor}-400`} size={24} />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-white">{agent.name}</h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">{agent.id}</p>
                  </div>
                </div>
                <button className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors">
                  <MoreVertical size={20} className="text-gray-400" />
                </button>
              </div>

              {/* Status badge */}
              <div className="flex items-center justify-between mb-4">
                <span className={`px-3 py-1 rounded-full text-sm font-medium bg-${statusColor}-100 text-${statusColor}-800 dark:bg-${statusColor}-900/20 dark:text-${statusColor}-400`}>
                  {statusConfig[agent.status].label}
                </span>
                <span className="text-sm text-gray-500 dark:text-gray-400">{agent.lastSeen}</span>
              </div>

              {/* Load bar */}
              <div className="mb-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Load</span>
                  <span className="text-sm font-medium text-gray-900 dark:text-white">{agent.load}%</span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${agent.load}%` }}
                    transition={{ duration: 1, delay: index * 0.1 }}
                    className={`${getLoadColor(agent.load)} h-2 rounded-full`}
                  />
                </div>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <div className="text-sm text-gray-500 dark:text-gray-400">Tasks</div>
                  <div className="text-lg font-semibold text-gray-900 dark:text-white">{agent.tasks.toLocaleString()}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500 dark:text-gray-400">Uptime</div>
                  <div className="text-lg font-semibold text-gray-900 dark:text-white">{agent.uptime}</div>
                </div>
              </div>

              {/* Capabilities */}
              <div className="mb-4">
                <div className="text-sm text-gray-500 dark:text-gray-400 mb-2">Capabilities</div>
                <div className="flex flex-wrap gap-2">
                  {agent.capabilities.map((cap) => (
                    <span
                      key={cap}
                      className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded text-xs"
                    >
                      {cap}
                    </span>
                  ))}
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center space-x-2 pt-4 border-t border-gray-200 dark:border-gray-700">
                <button className="flex-1 flex items-center justify-center space-x-2 px-4 py-2 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg transition-colors">
                  <Eye size={16} />
                  <span>View</span>
                </button>
                <button className="flex-1 flex items-center justify-center space-x-2 px-4 py-2 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg transition-colors">
                  <RefreshCw size={16} />
                  <span>Restart</span>
                </button>
                <button className="p-2 bg-red-100 dark:bg-red-900/20 hover:bg-red-200 dark:hover:bg-red-900/40 text-red-600 dark:text-red-400 rounded-lg transition-colors">
                  <Trash2 size={16} />
                </button>
              </div>
            </motion.div>
          )
        })}
      </div>

      {/* Empty state */}
      {filteredAgents.length === 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-12"
        >
          <div className="text-gray-400 dark:text-gray-600 mb-4">
            <Search size={48} className="mx-auto" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">No agents found</h3>
          <p className="text-gray-500 dark:text-gray-400">Try adjusting your search or filters</p>
        </motion.div>
      )}
    </div>
  )
}

export default AgentNetwork
