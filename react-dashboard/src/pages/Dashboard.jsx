import { motion } from 'framer-motion'
import {
  Activity,
  Users,
  Zap,
  TrendingUp,
  Brain,
  Network,
  ArrowUp,
  ArrowDown,
} from 'lucide-react'
import { LineChart, Line, AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const Dashboard = () => {
  // Sample data for charts
  const activityData = [
    { time: '00:00', agents: 45, thoughts: 120, coordinations: 3 },
    { time: '04:00', agents: 67, thoughts: 180, coordinations: 5 },
    { time: '08:00', agents: 123, thoughts: 340, coordinations: 8 },
    { time: '12:00', agents: 187, thoughts: 520, coordinations: 12 },
    { time: '16:00', agents: 245, thoughts: 680, coordinations: 15 },
    { time: '20:00', agents: 198, thoughts: 450, coordinations: 10 },
  ]

  const agentTypeData = [
    { name: 'Analyzers', value: 45, color: '#0ea5e9' },
    { name: 'Processors', value: 32, color: '#8b5cf6' },
    { name: 'Coordinators', value: 28, color: '#22c55e' },
    { name: 'Monitors', value: 18, color: '#f59e0b' },
  ]

  const thoughtTypeData = [
    { type: 'Observation', count: 145 },
    { type: 'Inference', count: 98 },
    { type: 'Insight', count: 76 },
    { type: 'Question', count: 54 },
    { type: 'Intention', count: 42 },
  ]

  const stats = [
    {
      label: 'Active Agents',
      value: '247',
      change: '+12%',
      trend: 'up',
      icon: Users,
      color: 'blue',
    },
    {
      label: 'Coordinations',
      value: '15',
      change: '+3',
      trend: 'up',
      icon: Network,
      color: 'purple',
    },
    {
      label: 'Thoughts/min',
      value: '1,429',
      change: '+8%',
      trend: 'up',
      icon: Brain,
      color: 'green',
    },
    {
      label: 'System Load',
      value: '67%',
      change: '-5%',
      trend: 'down',
      icon: Activity,
      color: 'orange',
    },
  ]

  const colorMap = {
    blue: 'from-blue-500 to-blue-600',
    purple: 'from-purple-500 to-purple-600',
    green: 'from-green-500 to-green-600',
    orange: 'from-orange-500 to-orange-600',
  }

  const recentActivity = [
    { id: 1, type: 'agent_registered', agent: 'analytics-047', time: '2 min ago', status: 'success' },
    { id: 2, type: 'coordination_created', name: 'Market Analysis Pipeline', time: '5 min ago', status: 'success' },
    { id: 3, type: 'thought_contributed', agent: 'ml-engine-12', time: '7 min ago', status: 'success' },
    { id: 4, type: 'pattern_emerged', pattern: 'Supply Chain Optimization', time: '12 min ago', status: 'insight' },
    { id: 5, type: 'agent_offline', agent: 'processor-089', time: '15 min ago', status: 'warning' },
  ]

  const statusColors = {
    success: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400',
    warning: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400',
    insight: 'bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-400',
  }

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">Real-time overview of your multi-agent system</p>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => {
          const Icon = stat.icon
          return (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="flex items-center justify-between mb-4">
                <div className={`p-3 rounded-lg bg-gradient-to-br ${colorMap[stat.color]}`}>
                  <Icon className="text-white" size={24} />
                </div>
                <div className={`flex items-center space-x-1 text-sm font-medium ${
                  stat.trend === 'up' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                }`}>
                  {stat.trend === 'up' ? <ArrowUp size={16} /> : <ArrowDown size={16} />}
                  <span>{stat.change}</span>
                </div>
              </div>
              <div>
                <div className="text-3xl font-bold text-gray-900 dark:text-white">{stat.value}</div>
                <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">{stat.label}</div>
              </div>
            </motion.div>
          )
        })}
      </div>

      {/* Charts grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Activity over time */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm"
        >
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Activity Over Time</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={activityData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.2} />
              <XAxis dataKey="time" stroke="#9ca3af" />
              <YAxis stroke="#9ca3af" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1f2937',
                  border: 'none',
                  borderRadius: '8px',
                  color: '#fff',
                }}
              />
              <Legend />
              <Area type="monotone" dataKey="agents" stackId="1" stroke="#0ea5e9" fill="#0ea5e9" fillOpacity={0.6} />
              <Area type="monotone" dataKey="thoughts" stackId="2" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.6} />
            </AreaChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Agent distribution */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm"
        >
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Agent Distribution</h3>
          <div className="flex items-center justify-center">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={agentTypeData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {agentTypeData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: 'none',
                    borderRadius: '8px',
                    color: '#fff',
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Thought types */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm"
        >
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Thought Types</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={thoughtTypeData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.2} />
              <XAxis dataKey="type" stroke="#9ca3af" angle={-45} textAnchor="end" height={80} />
              <YAxis stroke="#9ca3af" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1f2937',
                  border: 'none',
                  borderRadius: '8px',
                  color: '#fff',
                }}
              />
              <Bar dataKey="count" fill="#22c55e" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Recent activity */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
          className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm"
        >
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Recent Activity</h3>
          <div className="space-y-3">
            {recentActivity.map((activity, index) => (
              <motion.div
                key={activity.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.8 + index * 0.1 }}
                className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              >
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${statusColors[activity.status]}`}>
                      {activity.type.replace(/_/g, ' ')}
                    </span>
                  </div>
                  <p className="text-sm text-gray-700 dark:text-gray-300 mt-1">
                    {activity.agent || activity.name || activity.pattern}
                  </p>
                </div>
                <span className="text-xs text-gray-500 dark:text-gray-400">{activity.time}</span>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Bottom cards */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.9 }}
          className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-6 text-white shadow-lg"
        >
          <Zap size={32} className="mb-4" />
          <h3 className="text-2xl font-bold">98.7%</h3>
          <p className="text-blue-100 mt-1">System Uptime</p>
          <p className="text-sm text-blue-100 mt-3">Last 30 days</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.0 }}
          className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl p-6 text-white shadow-lg"
        >
          <TrendingUp size={32} className="mb-4" />
          <h3 className="text-2xl font-bold">2,847</h3>
          <p className="text-purple-100 mt-1">Patterns Discovered</p>
          <p className="text-sm text-purple-100 mt-3">This month</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.1 }}
          className="bg-gradient-to-br from-green-500 to-green-600 rounded-xl p-6 text-white shadow-lg"
        >
          <Brain size={32} className="mb-4" />
          <h3 className="text-2xl font-bold">847K</h3>
          <p className="text-green-100 mt-1">Thoughts Processed</p>
          <p className="text-sm text-green-100 mt-3">Last 24 hours</p>
        </motion.div>
      </div>
    </div>
  )
}

export default Dashboard
