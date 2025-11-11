import { motion } from 'framer-motion'
import { Brain, Sparkles, TrendingUp } from 'lucide-react'

const Consciousness = () => {
  const patterns = [
    {
      id: 'pattern-001',
      type: 'Insight',
      content: 'Market demand shows 20% increase in Q4 - opportunity for expansion',
      agents: ['agent-001', 'agent-003', 'agent-005'],
      confidence: 0.92,
      novelty: 0.78,
      timestamp: '5 min ago',
    },
    {
      id: 'pattern-002',
      type: 'Solution',
      content: 'Optimize inventory by redistributing 15% from Region A to Region B',
      agents: ['agent-002', 'agent-004'],
      confidence: 0.87,
      novelty: 0.65,
      timestamp: '12 min ago',
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Collective Consciousness</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">Emergent patterns from agent collaboration</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl p-6 text-white"
        >
          <Brain size={32} className="mb-4" />
          <div className="text-3xl font-bold">847K</div>
          <div className="text-purple-100">Thoughts Processed</div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-6 text-white"
        >
          <Sparkles size={32} className="mb-4" />
          <div className="text-3xl font-bold">2,847</div>
          <div className="text-blue-100">Patterns Emerged</div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
          className="bg-gradient-to-br from-green-500 to-green-600 rounded-xl p-6 text-white"
        >
          <TrendingUp size={32} className="mb-4" />
          <div className="text-3xl font-bold">94.2%</div>
          <div className="text-green-100">Avg Coherence</div>
        </motion.div>
      </div>

      <div className="space-y-4">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Recent Patterns</h2>
        {patterns.map((pattern, index) => (
          <motion.div
            key={pattern.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm"
          >
            <div className="flex items-start justify-between mb-4">
              <div>
                <span className="px-3 py-1 bg-purple-100 dark:bg-purple-900/20 text-purple-800 dark:text-purple-400 rounded-full text-sm font-medium">
                  {pattern.type}
                </span>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">{pattern.timestamp}</p>
              </div>
            </div>

            <p className="text-lg text-gray-900 dark:text-white mb-4">{pattern.content}</p>

            <div className="grid grid-cols-3 gap-4 mb-4">
              <div>
                <div className="text-sm text-gray-500 dark:text-gray-400">Confidence</div>
                <div className="text-lg font-semibold text-gray-900 dark:text-white">
                  {(pattern.confidence * 100).toFixed(0)}%
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-500 dark:text-gray-400">Novelty</div>
                <div className="text-lg font-semibold text-gray-900 dark:text-white">
                  {(pattern.novelty * 100).toFixed(0)}%
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-500 dark:text-gray-400">Contributing</div>
                <div className="text-lg font-semibold text-gray-900 dark:text-white">
                  {pattern.agents.length} agents
                </div>
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              {pattern.agents.map((agent) => (
                <span
                  key={agent}
                  className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded text-xs"
                >
                  {agent}
                </span>
              ))}
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  )
}

export default Consciousness
