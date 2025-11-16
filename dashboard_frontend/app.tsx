/**
 * APQC Real-Time Agent Monitoring Dashboard - React Frontend
 * ===========================================================
 *
 * Production-ready React application for monitoring 118+ APQC agents
 * across 13 categories with real-time WebSocket updates.
 *
 * Features:
 * - Real-time agent grid with health status
 * - Category hierarchy view
 * - Performance metrics and charts
 * - Live event stream
 * - WebSocket auto-reconnect
 * - Responsive design
 * - Dark mode optimized for 24/7 monitoring
 *
 * Version: 1.0.0
 * Author: APQC Dashboard Team
 * Date: 2025-11-16
 */

const { useState, useEffect, useRef, useMemo } = React;

// ============================================================================
// WebSocket Hook
// ============================================================================

function useWebSocket(url) {
    const [isConnected, setIsConnected] = useState(false);
    const [data, setData] = useState(null);
    const [error, setError] = useState(null);
    const ws = useRef(null);
    const reconnectTimeout = useRef(null);

    useEffect(() => {
        connect();

        return () => {
            if (reconnectTimeout.current) {
                clearTimeout(reconnectTimeout.current);
            }
            if (ws.current) {
                ws.current.close();
            }
        };
    }, [url]);

    const connect = () => {
        try {
            ws.current = new WebSocket(url);

            ws.current.onopen = () => {
                console.log('✅ WebSocket connected');
                setIsConnected(true);
                setError(null);
            };

            ws.current.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    setData(message);
                } catch (err) {
                    console.error('Error parsing WebSocket message:', err);
                }
            };

            ws.current.onerror = (err) => {
                console.error('❌ WebSocket error:', err);
                setError('WebSocket connection error');
            };

            ws.current.onclose = () => {
                console.log('📡 WebSocket disconnected');
                setIsConnected(false);

                // Auto-reconnect after 3 seconds
                reconnectTimeout.current = setTimeout(() => {
                    console.log('🔄 Reconnecting...');
                    connect();
                }, 3000);
            };
        } catch (err) {
            console.error('Error creating WebSocket:', err);
            setError('Failed to create WebSocket connection');
        }
    };

    const send = (message) => {
        if (ws.current && ws.current.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify(message));
        }
    };

    return { isConnected, data, error, send };
}

// ============================================================================
// API Hook
// ============================================================================

function useAPI(endpoint, refreshInterval = null) {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchData = async () => {
        try {
            const response = await fetch(`http://localhost:8765${endpoint}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const result = await response.json();
            setData(result);
            setError(null);
        } catch (err) {
            console.error(`Error fetching ${endpoint}:`, err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();

        if (refreshInterval) {
            const interval = setInterval(fetchData, refreshInterval);
            return () => clearInterval(interval);
        }
    }, [endpoint, refreshInterval]);

    return { data, loading, error, refetch: fetchData };
}

// ============================================================================
// Components
// ============================================================================

// Header Component
function DashboardHeader({ isConnected, stats, onAdminClick }) {
    return (
        <header className="dashboard-header">
            <div className="header-content">
                <div className="header-title">
                    <h1>🎯 APQC Operations Center</h1>
                    <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                        Real-Time Agent Monitoring
                    </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <button
                        onClick={onAdminClick}
                        style={{
                            background: 'var(--accent-primary)',
                            color: 'white',
                            border: 'none',
                            borderRadius: '6px',
                            padding: '0.5rem 1rem',
                            cursor: 'pointer',
                            fontSize: '0.875rem',
                            fontWeight: '500',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem',
                            transition: 'var(--transition)'
                        }}
                        onMouseEnter={(e) => e.currentTarget.style.background = 'var(--accent-secondary)'}
                        onMouseLeave={(e) => e.currentTarget.style.background = 'var(--accent-primary)'}
                    >
                        <span>🔧</span>
                        Admin Panel
                    </button>
                    <div className="status-indicator">
                        <div className={`pulse ${isConnected ? '' : 'offline'}`}
                             style={{ background: isConnected ? 'var(--status-healthy)' : 'var(--status-offline)' }}></div>
                        <span style={{ fontSize: '0.875rem' }}>
                            {isConnected ? 'Connected' : 'Reconnecting...'}
                        </span>
                        {stats && (
                            <span style={{ marginLeft: '1rem', color: 'var(--text-muted)' }}>
                                {stats.total_agents} Agents
                            </span>
                        )}
                    </div>
                </div>
            </div>
        </header>
    );
}

// Stats Card Component
function StatCard({ label, value, change, icon }) {
    return (
        <div className="stat-card">
            <div className="stat-label">{label}</div>
            <div className="stat-value">{value}</div>
            {change && (
                <div className={`stat-change ${change >= 0 ? 'positive' : 'negative'}`}>
                    {change >= 0 ? '↑' : '↓'} {Math.abs(change)}%
                </div>
            )}
        </div>
    );
}

// Agent Card Component
function AgentCard({ agent, onClick }) {
    const getStatusColor = (status) => {
        const colors = {
            healthy: 'var(--status-healthy)',
            degraded: 'var(--status-degraded)',
            unhealthy: 'var(--status-unhealthy)',
            offline: 'var(--status-offline)'
        };
        return colors[status] || colors.offline;
    };

    return (
        <div className="agent-card" onClick={() => onClick && onClick(agent)}>
            <div className="agent-header">
                <div className="agent-name">{agent.agent_name}</div>
                <div className={`status-dot ${agent.status}`}
                     style={{ background: getStatusColor(agent.status) }}></div>
            </div>
            <div className="agent-metrics">
                <div className="agent-metric">
                    <span>Health:</span>
                    <span style={{ color: getStatusColor(agent.status) }}>
                        {(agent.health_score * 100).toFixed(0)}%
                    </span>
                </div>
                <div className="agent-metric">
                    <span>Tasks:</span>
                    <span>{agent.tasks_processed.toLocaleString()}</span>
                </div>
                <div className="agent-metric">
                    <span>Response:</span>
                    <span>{agent.avg_response_time.toFixed(2)}s</span>
                </div>
                <div className="agent-metric">
                    <span>Errors:</span>
                    <span style={{ color: agent.error_count > 0 ? 'var(--status-unhealthy)' : 'inherit' }}>
                        {agent.error_count}
                    </span>
                </div>
            </div>
        </div>
    );
}

// Category Card Component
function CategoryCard({ category, agents, onAgentClick }) {
    const categoryAgents = agents.filter(a => a.category_id === category.category_id);

    const healthyCount = categoryAgents.filter(a => a.status === 'healthy').length;
    const avgHealth = categoryAgents.length > 0
        ? categoryAgents.reduce((sum, a) => sum + a.health_score, 0) / categoryAgents.length
        : 0;

    return (
        <div className="category-card">
            <div className="category-header">
                <div>
                    <div className="category-title">{category.category_name}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                        {category.category_id}
                    </div>
                </div>
                <div className="category-badge">{categoryAgents.length}</div>
            </div>

            <div className="category-stats">
                <div className="category-stat">
                    <div className="category-stat-value">{healthyCount}</div>
                    <div className="category-stat-label">Healthy</div>
                </div>
                <div className="category-stat">
                    <div className="category-stat-value">{(avgHealth * 100).toFixed(0)}%</div>
                    <div className="category-stat-label">Avg Health</div>
                </div>
                <div className="category-stat">
                    <div className="category-stat-value">
                        {categoryAgents.reduce((sum, a) => sum + a.tasks_processed, 0).toLocaleString()}
                    </div>
                    <div className="category-stat-label">Total Tasks</div>
                </div>
                <div className="category-stat">
                    <div className="category-stat-value">
                        {(category.success_rate * 100).toFixed(1)}%
                    </div>
                    <div className="category-stat-label">Success Rate</div>
                </div>
            </div>

            <div className="agent-grid">
                {categoryAgents.slice(0, 6).map(agent => (
                    <AgentCard key={agent.agent_id} agent={agent} onClick={onAgentClick} />
                ))}
            </div>

            {categoryAgents.length > 6 && (
                <div style={{
                    marginTop: '1rem',
                    textAlign: 'center',
                    fontSize: '0.875rem',
                    color: 'var(--text-secondary)'
                }}>
                    +{categoryAgents.length - 6} more agents
                </div>
            )}
        </div>
    );
}

// Event Stream Component
function EventStream({ events }) {
    return (
        <div className="event-stream">
            <h3>Live Event Stream</h3>
            {events.length === 0 ? (
                <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '2rem' }}>
                    No recent events
                </div>
            ) : (
                events.map((event, index) => (
                    <div key={index} className="event-item">
                        <div className="event-time">
                            {new Date(event.timestamp).toLocaleTimeString()}
                        </div>
                        <div className="event-message">
                            <strong>{event.agent_name}:</strong> {event.message}
                        </div>
                    </div>
                ))
            )}
        </div>
    );
}

// Loading Component
function Loading({ message = "Loading dashboard..." }) {
    return (
        <div className="loading">
            <div className="spinner"></div>
            <div style={{ color: 'var(--text-secondary)' }}>{message}</div>
        </div>
    );
}

// ============================================================================
// Main Dashboard Component
// ============================================================================

function Dashboard() {
    const [view, setView] = useState('overview'); // overview, categories, agents
    const [agents, setAgents] = useState([]);
    const [categories, setCategories] = useState([]);
    const [events, setEvents] = useState([]);
    const [selectedAgent, setSelectedAgent] = useState(null);
    const [showAdminPanel, setShowAdminPanel] = useState(false);

    // WebSocket connection
    const { isConnected, data: wsData } = useWebSocket('ws://localhost:8765/ws');

    // API data
    const { data: statsData } = useAPI('/api/metrics/summary', 5000);
    const { data: agentsData } = useAPI('/api/agents', 10000);
    const { data: categoriesData } = useAPI('/api/categories', 15000);

    // Update agents from API
    useEffect(() => {
        if (agentsData?.agents) {
            setAgents(agentsData.agents);
        }
    }, [agentsData]);

    // Update categories from API
    useEffect(() => {
        if (categoriesData?.categories) {
            setCategories(categoriesData.categories);
        }
    }, [categoriesData]);

    // Handle WebSocket updates
    useEffect(() => {
        if (!wsData) return;

        console.log('WebSocket message:', wsData.type);

        switch (wsData.type) {
            case 'initial':
                if (wsData.agents) setAgents(wsData.agents);
                if (wsData.categories) setCategories(wsData.categories);
                break;

            case 'agent_update':
                setAgents(prev => {
                    const index = prev.findIndex(a => a.agent_id === wsData.agent.agent_id);
                    if (index >= 0) {
                        const updated = [...prev];
                        updated[index] = wsData.agent;
                        return updated;
                    }
                    return [...prev, wsData.agent];
                });

                // Add to event stream
                setEvents(prev => [{
                    timestamp: new Date().toISOString(),
                    agent_name: wsData.agent.agent_name,
                    message: `Status updated: ${wsData.agent.status}`
                }, ...prev.slice(0, 49)]);
                break;

            case 'heartbeat':
                // Update connection status
                break;

            default:
                console.log('Unknown message type:', wsData.type);
        }
    }, [wsData]);

    // Calculate summary stats
    const summaryStats = useMemo(() => {
        if (!agents.length) return null;

        const healthy = agents.filter(a => a.status === 'healthy').length;
        const degraded = agents.filter(a => a.status === 'degraded').length;
        const offline = agents.filter(a => a.status === 'offline').length;
        const totalTasks = agents.reduce((sum, a) => sum + a.tasks_processed, 0);
        const totalErrors = agents.reduce((sum, a) => sum + a.error_count, 0);
        const avgHealth = agents.reduce((sum, a) => sum + a.health_score, 0) / agents.length;

        return {
            total: agents.length,
            healthy,
            degraded,
            offline,
            totalTasks,
            totalErrors,
            avgHealth,
            successRate: totalTasks > 0 ? ((totalTasks - totalErrors) / totalTasks) : 1
        };
    }, [agents]);

    // Show loading state
    if (!agents.length && !agentsData) {
        return <Loading />;
    }

    // Show admin panel if active
    if (showAdminPanel) {
        return <window.AdminPanel onClose={() => setShowAdminPanel(false)} />;
    }

    return (
        <div>
            <DashboardHeader
                isConnected={isConnected}
                stats={statsData}
                onAdminClick={() => setShowAdminPanel(true)}
            />

            <div className="dashboard-container">
                {/* Summary Stats */}
                <div className="stats-grid mb-2">
                    <StatCard
                        label="Total Agents"
                        value={summaryStats?.total || 0}
                    />
                    <StatCard
                        label="Healthy Agents"
                        value={summaryStats?.healthy || 0}
                        change={summaryStats ? ((summaryStats.healthy / summaryStats.total) * 100 - 80) : 0}
                    />
                    <StatCard
                        label="Avg Health Score"
                        value={summaryStats ? `${(summaryStats.avgHealth * 100).toFixed(1)}%` : '0%'}
                    />
                    <StatCard
                        label="Total Tasks"
                        value={summaryStats?.totalTasks.toLocaleString() || '0'}
                    />
                    <StatCard
                        label="Success Rate"
                        value={summaryStats ? `${(summaryStats.successRate * 100).toFixed(1)}%` : '0%'}
                    />
                    <StatCard
                        label="Total Errors"
                        value={summaryStats?.totalErrors || 0}
                    />
                </div>

                {/* View Selector */}
                <div style={{
                    display: 'flex',
                    gap: '1rem',
                    marginBottom: '2rem',
                    borderBottom: '1px solid var(--border-color)',
                    paddingBottom: '1rem'
                }}>
                    <button
                        onClick={() => setView('overview')}
                        style={{
                            background: view === 'overview' ? 'var(--accent-primary)' : 'transparent',
                            color: 'var(--text-primary)',
                            border: '1px solid var(--border-color)',
                            padding: '0.5rem 1.5rem',
                            borderRadius: '6px',
                            cursor: 'pointer',
                            fontSize: '0.875rem',
                            fontWeight: '500',
                            transition: 'var(--transition)'
                        }}
                    >
                        Overview
                    </button>
                    <button
                        onClick={() => setView('categories')}
                        style={{
                            background: view === 'categories' ? 'var(--accent-primary)' : 'transparent',
                            color: 'var(--text-primary)',
                            border: '1px solid var(--border-color)',
                            padding: '0.5rem 1.5rem',
                            borderRadius: '6px',
                            cursor: 'pointer',
                            fontSize: '0.875rem',
                            fontWeight: '500',
                            transition: 'var(--transition)'
                        }}
                    >
                        Categories ({categories.length})
                    </button>
                    <button
                        onClick={() => setView('agents')}
                        style={{
                            background: view === 'agents' ? 'var(--accent-primary)' : 'transparent',
                            color: 'var(--text-primary)',
                            border: '1px solid var(--border-color)',
                            padding: '0.5rem 1.5rem',
                            borderRadius: '6px',
                            cursor: 'pointer',
                            fontSize: '0.875rem',
                            fontWeight: '500',
                            transition: 'var(--transition)'
                        }}
                    >
                        All Agents ({agents.length})
                    </button>
                </div>

                {/* Overview View */}
                {view === 'overview' && (
                    <div className="flex flex-col gap-2">
                        <div className="category-grid">
                            {categories.map(category => (
                                <CategoryCard
                                    key={category.category_id}
                                    category={category}
                                    agents={agents}
                                    onAgentClick={setSelectedAgent}
                                />
                            ))}
                        </div>
                        <EventStream events={events} />
                    </div>
                )}

                {/* Categories View */}
                {view === 'categories' && (
                    <div className="category-grid">
                        {categories.map(category => (
                            <CategoryCard
                                key={category.category_id}
                                category={category}
                                agents={agents}
                                onAgentClick={setSelectedAgent}
                            />
                        ))}
                    </div>
                )}

                {/* Agents View */}
                {view === 'agents' && (
                    <div>
                        <div style={{
                            marginBottom: '1.5rem',
                            padding: '1rem',
                            background: 'var(--bg-card)',
                            borderRadius: '8px',
                            border: '1px solid var(--border-color)'
                        }}>
                            <input
                                type="text"
                                placeholder="Search agents..."
                                style={{
                                    width: '100%',
                                    padding: '0.75rem',
                                    background: 'var(--bg-tertiary)',
                                    border: '1px solid var(--border-color)',
                                    borderRadius: '6px',
                                    color: 'var(--text-primary)',
                                    fontSize: '0.875rem'
                                }}
                            />
                        </div>
                        <div className="agent-grid">
                            {agents.map(agent => (
                                <AgentCard
                                    key={agent.agent_id}
                                    agent={agent}
                                    onClick={setSelectedAgent}
                                />
                            ))}
                        </div>
                    </div>
                )}

                {/* Agent Details Modal */}
                {selectedAgent && (
                    <div style={{
                        position: 'fixed',
                        top: 0,
                        left: 0,
                        right: 0,
                        bottom: 0,
                        background: 'rgba(0, 0, 0, 0.8)',
                        display: 'flex',
                        justifyContent: 'center',
                        alignItems: 'center',
                        zIndex: 1000,
                        padding: '2rem'
                    }} onClick={() => setSelectedAgent(null)}>
                        <div style={{
                            background: 'var(--bg-card)',
                            borderRadius: '12px',
                            padding: '2rem',
                            maxWidth: '600px',
                            width: '100%',
                            maxHeight: '80vh',
                            overflow: 'auto',
                            border: '1px solid var(--border-color)'
                        }} onClick={e => e.stopPropagation()}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
                                <h2>{selectedAgent.agent_name}</h2>
                                <button onClick={() => setSelectedAgent(null)} style={{
                                    background: 'transparent',
                                    border: 'none',
                                    color: 'var(--text-primary)',
                                    cursor: 'pointer',
                                    fontSize: '1.5rem'
                                }}>×</button>
                            </div>

                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem' }}>
                                <div>
                                    <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Agent ID</div>
                                    <div>{selectedAgent.agent_id}</div>
                                </div>
                                <div>
                                    <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Category</div>
                                    <div>{selectedAgent.category_name}</div>
                                </div>
                                <div>
                                    <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Process ID</div>
                                    <div>{selectedAgent.process_id}</div>
                                </div>
                                <div>
                                    <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Status</div>
                                    <div style={{
                                        color: selectedAgent.status === 'healthy' ? 'var(--status-healthy)' : 'var(--status-degraded)',
                                        fontWeight: '600'
                                    }}>{selectedAgent.status.toUpperCase()}</div>
                                </div>
                                <div>
                                    <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Health Score</div>
                                    <div>{(selectedAgent.health_score * 100).toFixed(1)}%</div>
                                </div>
                                <div>
                                    <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Tasks Processed</div>
                                    <div>{selectedAgent.tasks_processed.toLocaleString()}</div>
                                </div>
                                <div>
                                    <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Error Count</div>
                                    <div>{selectedAgent.error_count}</div>
                                </div>
                                <div>
                                    <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Avg Response Time</div>
                                    <div>{selectedAgent.avg_response_time.toFixed(3)}s</div>
                                </div>
                                <div>
                                    <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>CPU Usage</div>
                                    <div>{selectedAgent.cpu_usage.toFixed(1)}%</div>
                                </div>
                                <div>
                                    <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Memory Usage</div>
                                    <div>{selectedAgent.memory_usage.toFixed(1)}%</div>
                                </div>
                            </div>

                            <div style={{ marginTop: '1.5rem' }}>
                                <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                                    Protocols
                                </div>
                                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                                    {selectedAgent.protocols.map(protocol => (
                                        <span key={protocol} style={{
                                            background: 'var(--accent-primary)',
                                            color: 'white',
                                            padding: '0.25rem 0.75rem',
                                            borderRadius: '4px',
                                            fontSize: '0.75rem'
                                        }}>{protocol}</span>
                                    ))}
                                </div>
                            </div>

                            {selectedAgent.capabilities && selectedAgent.capabilities.length > 0 && (
                                <div style={{ marginTop: '1.5rem' }}>
                                    <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                                        Capabilities
                                    </div>
                                    <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                                        {selectedAgent.capabilities.map(cap => (
                                            <span key={cap} style={{
                                                background: 'var(--bg-tertiary)',
                                                padding: '0.25rem 0.75rem',
                                                borderRadius: '4px',
                                                fontSize: '0.75rem',
                                                border: '1px solid var(--border-color)'
                                            }}>{cap}</span>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

// ============================================================================
// Render Application
// ============================================================================

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<Dashboard />);
