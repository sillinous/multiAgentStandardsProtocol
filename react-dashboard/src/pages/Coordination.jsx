import { motion } from 'framer-motion'
import { Play, Pause, CheckCircle, Clock, Users } from 'lucide-react'

const Coordination = () => {
  const coordinations = [
    {
      id: 'coord-001',
      name: 'Supply Chain Optimization',
      type: 'Pipeline',
      status: 'active',
      progress: 67,
      participants: 5,
      tasks: { total: 12, completed: 8, inProgress: 3, pending: 1 },
      startedAt: '2 hours ago',
    },
    {
      id: 'coord-002',
      name: 'Market Analysis Swarm',
      type: 'Swarm',
      status: 'active',
      progress: 45,
      participants: 8,
      tasks: { total: 24, completed: 11, inProgress: 7, pending: 6 },
      startedAt: '1 hour ago',
    },
    {
      id: 'coord-003',
      name: 'Data Processing Pipeline',
      type: 'Pipeline',
      status: 'completed',
      progress: 100,
      participants: 3,
      tasks: { total: 8, completed: 8, inProgress: 0, pending: 0 },
      startedAt: '5 hours ago',
    },
  ]

  const statusColors = {
    active: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400',
    paused: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400',
    completed: 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400',
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Coordination</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">Multi-agent coordination sessions</p>
      </div>

      <div className="grid grid-cols-1 gap-6">
        {coordinations.map((coord, index) => (
          <motion.div
            key={coord.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm"
          >
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white">{coord.name}</h3>
                <p className="text-sm text-gray-500 dark:text-gray-400">{coord.id}</p>
              </div>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${statusColors[coord.status]}`}>
                {coord.status}
              </span>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div>
                <div className="text-sm text-gray-500 dark:text-gray-400">Type</div>
                <div className="font-semibold text-gray-900 dark:text-white">{coord.type}</div>
              </div>
              <div>
                <div className="text-sm text-gray-500 dark:text-gray-400">Participants</div>
                <div className="flex items-center space-x-1">
                  <Users size={16} className="text-gray-400" />
                  <span className="font-semibold text-gray-900 dark:text-white">{coord.participants}</span>
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-500 dark:text-gray-400">Tasks</div>
                <div className="font-semibold text-gray-900 dark:text-white">
                  {coord.tasks.completed}/{coord.tasks.total}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-500 dark:text-gray-400">Started</div>
                <div className="font-semibold text-gray-900 dark:text-white">{coord.startedAt}</div>
              </div>
            </div>

            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600 dark:text-gray-400">Progress</span>
                <span className="text-sm font-medium text-gray-900 dark:text-white">{coord.progress}%</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  className="bg-primary-600 h-2 rounded-full transition-all duration-1000"
                  style={{ width: `${coord.progress}%` }}
                />
              </div>
            </div>

            <div className="flex space-x-2">
              <button className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">
                {coord.status === 'active' ? <Pause size={16} /> : <Play size={16} />}
                <span>{coord.status === 'active' ? 'Pause' : 'Resume'}</span>
              </button>
              <button className="px-4 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600">
                View Details
              </button>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  )
}

export default Coordination
