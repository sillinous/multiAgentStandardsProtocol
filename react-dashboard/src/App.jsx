import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { useState } from 'react'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import AgentNetwork from './pages/AgentNetwork'
import Coordination from './pages/Coordination'
import Consciousness from './pages/Consciousness'
import Settings from './pages/Settings'

function App() {
  const [darkMode, setDarkMode] = useState(true)

  return (
    <div className={darkMode ? 'dark' : ''}>
      <Router>
        <Layout darkMode={darkMode} setDarkMode={setDarkMode}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/agents" element={<AgentNetwork />} />
            <Route path="/coordination" element={<Coordination />} />
            <Route path="/consciousness" element={<Consciousness />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </Layout>
      </Router>
    </div>
  )
}

export default App
