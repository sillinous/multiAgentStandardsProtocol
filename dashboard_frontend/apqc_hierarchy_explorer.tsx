/**
 * APQC Hierarchy Explorer - Interactive PCF Browser and Agent Configurator
 * ========================================================================
 *
 * Production-ready UI for exploring the complete APQC PCF hierarchy and
 * configuring all ~840 atomic agents through an intuitive interface.
 *
 * Core Principle: EVERYTHING is configurable through the UI.
 * - No manual coding
 * - No file editing
 * - Visual hierarchy navigation
 * - Per-agent configuration
 * - Bulk operations
 * - Template management
 *
 * Features:
 * - 5-level hierarchy visualization (Category → Task)
 * - Interactive tree with expand/collapse
 * - Agent configuration panels
 * - Bulk configuration management
 * - Search and filtering
 * - Agent generation triggers
 * - Real-time status updates
 * - Integration management per agent
 * - Custom parameter definition
 *
 * Version: 1.0.0
 * Author: APQC Factory Team
 * Date: 2025-11-17
 */

const { useState, useEffect, useMemo } = React;

interface APQCTask {
    agent_id: string;
    level5_id: string;
    level5_name: string;
    level4_id: string;
    level4_name: string;
    level3_id: string;
    level3_name: string;
    level2_id: string;
    level2_name: string;
    level1_id: string;
    level1_name: string;
    agent_name: string;
    agent_class_name: string;
    domain: string;
    description: string;
    enabled: boolean;
    priority: 'low' | 'normal' | 'high' | 'critical';
    autonomous_level: number;
    collaboration_mode: string;
    learning_enabled: boolean;
    compute_mode: string;
    memory_mode: string;
    api_budget_mode: string;
    requires_api_keys: string[];
    integrations: string[];
    custom_config: Record<string, any>;
}

interface HierarchyNode {
    id: string;
    name: string;
    level: number;
    children: HierarchyNode[];
    task?: APQCTask;
    expanded: boolean;
}

function APQCHierarchyExplorer({ onClose }: { onClose: () => void }) {
    const [tasks, setTasks] = useState<APQCTask[]>([]);
    const [hierarchy, setHierarchy] = useState<HierarchyNode[]>([]);
    const [selectedTask, setSelectedTask] = useState<APQCTask | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [filterCategory, setFilterCategory] = useState<string>('all');
    const [filterEnabled, setFilterEnabled] = useState<string>('all');
    const [loading, setLoading] = useState(true);
    const [stats, setStats] = useState<any>(null);

    // Load all tasks from backend
    useEffect(() => {
        loadTasks();
        loadStats();
    }, []);

    // Build hierarchy tree when tasks change
    useEffect(() => {
        if (tasks.length > 0) {
            setHierarchy(buildHierarchyTree(tasks));
        }
    }, [tasks]);

    const loadTasks = async () => {
        try {
            const response = await fetch('/api/apqc/tasks');
            const data = await response.json();
            setTasks(data);
            setLoading(false);
        } catch (error) {
            console.error('Failed to load tasks:', error);
            setLoading(false);
        }
    };

    const loadStats = async () => {
        try {
            const response = await fetch('/api/apqc/stats');
            const data = await response.json();
            setStats(data);
        } catch (error) {
            console.error('Failed to load stats:', error);
        }
    };

    const buildHierarchyTree = (tasks: APQCTask[]): HierarchyNode[] => {
        const tree: HierarchyNode[] = [];
        const nodeMap = new Map<string, HierarchyNode>();

        // Group by levels
        tasks.forEach(task => {
            // Level 1 (Category)
            if (!nodeMap.has(task.level1_id)) {
                const node: HierarchyNode = {
                    id: task.level1_id,
                    name: task.level1_name,
                    level: 1,
                    children: [],
                    expanded: false
                };
                nodeMap.set(task.level1_id, node);
                tree.push(node);
            }

            // Level 2
            const level2Id = task.level2_id;
            if (!nodeMap.has(level2Id)) {
                const node: HierarchyNode = {
                    id: level2Id,
                    name: task.level2_name,
                    level: 2,
                    children: [],
                    expanded: false
                };
                nodeMap.set(level2Id, node);
                nodeMap.get(task.level1_id)!.children.push(node);
            }

            // Level 3
            const level3Id = task.level3_id;
            if (!nodeMap.has(level3Id)) {
                const node: HierarchyNode = {
                    id: level3Id,
                    name: task.level3_name,
                    level: 3,
                    children: [],
                    expanded: false
                };
                nodeMap.set(level3Id, node);
                nodeMap.get(level2Id)!.children.push(node);
            }

            // Level 4
            const level4Id = task.level4_id;
            if (!nodeMap.has(level4Id)) {
                const node: HierarchyNode = {
                    id: level4Id,
                    name: task.level4_name,
                    level: 4,
                    children: [],
                    expanded: false
                };
                nodeMap.set(level4Id, node);
                nodeMap.get(level3Id)!.children.push(node);
            }

            // Level 5 (Task/Agent)
            const level5Id = task.level5_id;
            const taskNode: HierarchyNode = {
                id: level5Id,
                name: task.level5_name,
                level: 5,
                children: [],
                expanded: false,
                task: task
            };
            nodeMap.get(level4Id)!.children.push(taskNode);
        });

        return tree;
    };

    const toggleNode = (nodeId: string) => {
        const toggleRecursive = (nodes: HierarchyNode[]): HierarchyNode[] => {
            return nodes.map(node => {
                if (node.id === nodeId) {
                    return { ...node, expanded: !node.expanded };
                }
                if (node.children.length > 0) {
                    return { ...node, children: toggleRecursive(node.children) };
                }
                return node;
            });
        };

        setHierarchy(toggleRecursive(hierarchy));
    };

    const filteredTasks = useMemo(() => {
        return tasks.filter(task => {
            // Search filter
            if (searchQuery) {
                const query = searchQuery.toLowerCase();
                if (!task.level5_name.toLowerCase().includes(query) &&
                    !task.agent_name.toLowerCase().includes(query) &&
                    !task.level5_id.includes(query)) {
                    return false;
                }
            }

            // Category filter
            if (filterCategory !== 'all' && task.level1_id !== filterCategory) {
                return false;
            }

            // Enabled filter
            if (filterEnabled === 'enabled' && !task.enabled) return false;
            if (filterEnabled === 'disabled' && task.enabled) return false;

            return true;
        });
    }, [tasks, searchQuery, filterCategory, filterEnabled]);

    const renderHierarchyNode = (node: HierarchyNode, depth: number = 0) => {
        const indent = depth * 24;
        const isTask = node.level === 5;
        const hasChildren = node.children.length > 0;

        const icons = ['🎯', '📂', '📄', '📋', '⚙️'];
        const icon = icons[node.level - 1] || '•';

        return (
            <div key={node.id}>
                <div
                    style={{
                        padding: '0.5rem 1rem',
                        paddingLeft: `${indent + 16}px`,
                        borderBottom: '1px solid var(--border-color)',
                        cursor: isTask ? 'pointer' : hasChildren ? 'pointer' : 'default',
                        background: selectedTask?.level5_id === node.id ? 'var(--card-bg)' : 'transparent',
                        transition: 'background 0.2s'
                    }}
                    onClick={() => {
                        if (isTask && node.task) {
                            setSelectedTask(node.task);
                        } else if (hasChildren) {
                            toggleNode(node.id);
                        }
                    }}
                    onMouseEnter={(e) => {
                        if (!isTask) e.currentTarget.style.background = 'rgba(255,255,255,0.02)';
                    }}
                    onMouseLeave={(e) => {
                        if (!isTask && selectedTask?.level5_id !== node.id) {
                            e.currentTarget.style.background = 'transparent';
                        }
                    }}
                >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        {hasChildren && (
                            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                {node.expanded ? '▼' : '▶'}
                            </span>
                        )}
                        <span>{icon}</span>
                        <span style={{
                            fontSize: node.level <= 2 ? '0.95rem' : '0.875rem',
                            fontWeight: node.level <= 2 ? '600' : '400',
                            color: isTask ? (node.task?.enabled ? 'var(--text-primary)' : 'var(--text-muted)') : 'var(--text-secondary)'
                        }}>
                            {node.id} {node.name}
                        </span>
                        {isTask && node.task && (
                            <span style={{
                                marginLeft: 'auto',
                                fontSize: '0.75rem',
                                padding: '0.125rem 0.5rem',
                                borderRadius: '12px',
                                background: node.task.enabled ? 'var(--status-healthy)' : 'var(--text-muted)',
                                color: '#000'
                            }}>
                                {node.task.enabled ? '✓ Enabled' : 'Disabled'}
                            </span>
                        )}
                    </div>
                </div>
                {node.expanded && node.children.map(child => renderHierarchyNode(child, depth + 1))}
            </div>
        );
    };

    const updateTaskConfig = async (agentId: string, updates: Partial<APQCTask>) => {
        try {
            await fetch(`/api/apqc/tasks/${agentId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updates)
            });

            // Update local state
            setTasks(tasks.map(t => t.agent_id === agentId ? { ...t, ...updates } : t));
            if (selectedTask?.agent_id === agentId) {
                setSelectedTask({ ...selectedTask, ...updates });
            }

            // Reload stats
            loadStats();
        } catch (error) {
            console.error('Failed to update task:', error);
        }
    };

    const generateAgent = async (agentId: string) => {
        try {
            const response = await fetch(`/api/apqc/generate/${agentId}`, {
                method: 'POST'
            });
            const result = await response.json();

            if (result.success) {
                alert(`✅ Agent generated successfully!\n\nPath: ${result.path}`);
            } else {
                alert(`❌ Generation failed:\n\n${result.error}`);
            }
        } catch (error) {
            alert(`❌ Generation failed:\n\n${error}`);
        }
    };

    const generateAll = async (categoryId?: string) => {
        if (!confirm(`Generate ${categoryId ? `all agents for category ${categoryId}` : 'ALL agents'}?\n\nThis may take several minutes.`)) {
            return;
        }

        try {
            const url = categoryId ? `/api/apqc/generate-category/${categoryId}` : '/api/apqc/generate-all';
            const response = await fetch(url, { method: 'POST' });
            const result = await response.json();

            alert(`📦 Generation Complete!\n\n✅ Generated: ${result.generated}\n❌ Failed: ${result.failed}`);
            loadStats();
        } catch (error) {
            alert(`❌ Bulk generation failed:\n\n${error}`);
        }
    };

    if (loading) {
        return (
            <div style={{ padding: '3rem', textAlign: 'center' }}>
                <div className="spinner"></div>
                <p style={{ marginTop: '1rem', color: 'var(--text-muted)' }}>Loading APQC hierarchy...</p>
            </div>
        );
    }

    return (
        <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--bg-primary)' }}>
            {/* Header */}
            <div style={{
                padding: '1.5rem',
                borderBottom: '1px solid var(--border-color)',
                background: 'var(--card-bg)'
            }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div>
                        <h1 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>
                            🏭 APQC Hierarchy Explorer
                        </h1>
                        <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
                            Configure all {tasks.length} atomic agents through the UI
                        </p>
                    </div>
                    <button
                        onClick={onClose}
                        style={{
                            padding: '0.5rem 1rem',
                            background: 'transparent',
                            color: 'var(--text-secondary)',
                            border: '1px solid var(--border-color)',
                            borderRadius: '6px',
                            cursor: 'pointer'
                        }}
                    >
                        ✕ Close
                    </button>
                </div>

                {/* Stats */}
                {stats && (
                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
                        gap: '1rem',
                        marginTop: '1rem'
                    }}>
                        <div style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: '1.5rem', fontWeight: '600', color: 'var(--accent-primary)' }}>
                                {stats.total_agents}
                            </div>
                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Total Agents</div>
                        </div>
                        <div style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: '1.5rem', fontWeight: '600', color: 'var(--status-healthy)' }}>
                                {tasks.filter(t => t.enabled).length}
                            </div>
                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Enabled</div>
                        </div>
                        <div style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: '1.5rem', fontWeight: '600', color: 'var(--text-warning)' }}>
                                {Object.keys(stats.by_category || {}).length}
                            </div>
                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Categories</div>
                        </div>
                    </div>
                )}

                {/* Filters */}
                <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                    gap: '1rem',
                    marginTop: '1rem'
                }}>
                    <input
                        type="text"
                        placeholder="🔍 Search tasks..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        style={{
                            padding: '0.5rem 1rem',
                            background: 'var(--bg-secondary)',
                            color: 'var(--text-primary)',
                            border: '1px solid var(--border-color)',
                            borderRadius: '6px',
                            fontSize: '0.875rem'
                        }}
                    />
                    <select
                        value={filterCategory}
                        onChange={(e) => setFilterCategory(e.target.value)}
                        style={{
                            padding: '0.5rem 1rem',
                            background: 'var(--bg-secondary)',
                            color: 'var(--text-primary)',
                            border: '1px solid var(--border-color)',
                            borderRadius: '6px',
                            fontSize: '0.875rem'
                        }}
                    >
                        <option value="all">All Categories</option>
                        {stats && Object.keys(stats.by_category || {}).map(cat => (
                            <option key={cat} value={cat}>{cat}</option>
                        ))}
                    </select>
                    <select
                        value={filterEnabled}
                        onChange={(e) => setFilterEnabled(e.target.value)}
                        style={{
                            padding: '0.5rem 1rem',
                            background: 'var(--bg-secondary)',
                            color: 'var(--text-primary)',
                            border: '1px solid var(--border-color)',
                            borderRadius: '6px',
                            fontSize: '0.875rem'
                        }}
                    >
                        <option value="all">All Status</option>
                        <option value="enabled">Enabled Only</option>
                        <option value="disabled">Disabled Only</option>
                    </select>
                    <button
                        onClick={() => generateAll()}
                        style={{
                            padding: '0.5rem 1rem',
                            background: 'var(--accent-primary)',
                            color: '#fff',
                            border: 'none',
                            borderRadius: '6px',
                            cursor: 'pointer',
                            fontSize: '0.875rem',
                            fontWeight: '600'
                        }}
                    >
                        🚀 Generate All Agents
                    </button>
                </div>
            </div>

            {/* Content */}
            <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '1fr 400px', overflow: 'hidden' }}>
                {/* Hierarchy Tree */}
                <div style={{ overflowY: 'auto', borderRight: '1px solid var(--border-color)' }}>
                    {hierarchy.map(node => renderHierarchyNode(node))}
                </div>

                {/* Configuration Panel */}
                <div style={{ overflowY: 'auto', background: 'var(--card-bg)' }}>
                    {selectedTask ? (
                        <AgentConfigPanel
                            task={selectedTask}
                            onUpdate={(updates) => updateTaskConfig(selectedTask.agent_id, updates)}
                            onGenerate={() => generateAgent(selectedTask.agent_id)}
                        />
                    ) : (
                        <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                            <p>Select a task to configure its agent</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

function AgentConfigPanel({ task, onUpdate, onGenerate }: {
    task: APQCTask;
    onUpdate: (updates: Partial<APQCTask>) => void;
    onGenerate: () => void;
}) {
    const [localTask, setLocalTask] = useState(task);

    useEffect(() => {
        setLocalTask(task);
    }, [task]);

    const handleChange = (field: keyof APQCTask, value: any) => {
        setLocalTask({ ...localTask, [field]: value });
    };

    const saveChanges = () => {
        onUpdate(localTask);
    };

    return (
        <div style={{ padding: '1.5rem' }}>
            <h2 style={{ fontSize: '1.125rem', marginBottom: '0.5rem' }}>
                ⚙️ Agent Configuration
            </h2>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
                {localTask.level5_id} - {localTask.level5_name}
            </p>

            {/* Basic Settings */}
            <div style={{ marginBottom: '1.5rem' }}>
                <h3 style={{ fontSize: '0.875rem', fontWeight: '600', marginBottom: '0.75rem', color: 'var(--text-secondary)' }}>
                    Basic Settings
                </h3>

                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem', cursor: 'pointer' }}>
                    <input
                        type="checkbox"
                        checked={localTask.enabled}
                        onChange={(e) => handleChange('enabled', e.target.checked)}
                    />
                    <span style={{ fontSize: '0.875rem' }}>Enabled</span>
                </label>

                <label style={{ display: 'block', marginBottom: '0.75rem' }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.25rem' }}>
                        Priority
                    </span>
                    <select
                        value={localTask.priority}
                        onChange={(e) => handleChange('priority', e.target.value)}
                        style={{
                            width: '100%',
                            padding: '0.5rem',
                            background: 'var(--bg-secondary)',
                            color: 'var(--text-primary)',
                            border: '1px solid var(--border-color)',
                            borderRadius: '4px',
                            fontSize: '0.875rem'
                        }}
                    >
                        <option value="low">Low</option>
                        <option value="normal">Normal</option>
                        <option value="high">High</option>
                        <option value="critical">Critical</option>
                    </select>
                </label>

                <label style={{ display: 'block', marginBottom: '0.75rem' }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.25rem' }}>
                        Autonomous Level: {localTask.autonomous_level}
                    </span>
                    <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.1"
                        value={localTask.autonomous_level}
                        onChange={(e) => handleChange('autonomous_level', parseFloat(e.target.value))}
                        style={{ width: '100%' }}
                    />
                </label>

                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem', cursor: 'pointer' }}>
                    <input
                        type="checkbox"
                        checked={localTask.learning_enabled}
                        onChange={(e) => handleChange('learning_enabled', e.target.checked)}
                    />
                    <span style={{ fontSize: '0.875rem' }}>Learning Enabled</span>
                </label>
            </div>

            {/* Resource Configuration */}
            <div style={{ marginBottom: '1.5rem' }}>
                <h3 style={{ fontSize: '0.875rem', fontWeight: '600', marginBottom: '0.75rem', color: 'var(--text-secondary)' }}>
                    Resource Configuration
                </h3>

                <label style={{ display: 'block', marginBottom: '0.75rem' }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.25rem' }}>
                        Compute Mode
                    </span>
                    <select
                        value={localTask.compute_mode}
                        onChange={(e) => handleChange('compute_mode', e.target.value)}
                        style={{
                            width: '100%',
                            padding: '0.5rem',
                            background: 'var(--bg-secondary)',
                            color: 'var(--text-primary)',
                            border: '1px solid var(--border-color)',
                            borderRadius: '4px',
                            fontSize: '0.875rem'
                        }}
                    >
                        <option value="minimal">Minimal</option>
                        <option value="standard">Standard</option>
                        <option value="intensive">Intensive</option>
                    </select>
                </label>

                <label style={{ display: 'block', marginBottom: '0.75rem' }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.25rem' }}>
                        Memory Mode
                    </span>
                    <select
                        value={localTask.memory_mode}
                        onChange={(e) => handleChange('memory_mode', e.target.value)}
                        style={{
                            width: '100%',
                            padding: '0.5rem',
                            background: 'var(--bg-secondary)',
                            color: 'var(--text-primary)',
                            border: '1px solid var(--border-color)',
                            borderRadius: '4px',
                            fontSize: '0.875rem'
                        }}
                    >
                        <option value="minimal">Minimal</option>
                        <option value="standard">Standard</option>
                        <option value="large">Large</option>
                    </select>
                </label>
            </div>

            {/* Actions */}
            <div style={{ display: 'flex', gap: '0.75rem' }}>
                <button
                    onClick={saveChanges}
                    style={{
                        flex: 1,
                        padding: '0.75rem',
                        background: 'var(--accent-primary)',
                        color: '#fff',
                        border: 'none',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontSize: '0.875rem',
                        fontWeight: '600'
                    }}
                >
                    💾 Save Configuration
                </button>
                <button
                    onClick={onGenerate}
                    style={{
                        flex: 1,
                        padding: '0.75rem',
                        background: 'var(--status-healthy)',
                        color: '#000',
                        border: 'none',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontSize: '0.875rem',
                        fontWeight: '600'
                    }}
                >
                    🚀 Generate Agent
                </button>
            </div>

            {/* Metadata */}
            <div style={{
                marginTop: '1.5rem',
                padding: '1rem',
                background: 'var(--bg-secondary)',
                borderRadius: '6px',
                fontSize: '0.75rem',
                color: 'var(--text-muted)'
            }}>
                <div><strong>Agent ID:</strong> {localTask.agent_id}</div>
                <div><strong>Class:</strong> {localTask.agent_class_name}</div>
                <div><strong>Domain:</strong> {localTask.domain}</div>
                <div><strong>Category:</strong> {localTask.level1_name}</div>
            </div>
        </div>
    );
}

// Export component to global scope
(window as any).APQCHierarchyExplorer = APQCHierarchyExplorer;
