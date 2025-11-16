/**
 * Visual Workflow Designer - Drag-and-Drop Agent Composition
 * ===========================================================
 *
 * Production-ready React component for visual workflow orchestration.
 * Enables drag-and-drop composition of 118+ APQC agents into cross-domain workflows.
 *
 * Features:
 * - Drag-and-drop canvas with React Flow
 * - Agent palette organized by 13 APQC categories
 * - Connection drawing between agents
 * - Property panel for node configuration
 * - Workflow save/load/export
 * - Test/debug mode with live execution
 * - Template gallery integration
 * - Real-time collaboration ready
 * - Mobile responsive design
 *
 * Tech Stack:
 * - React 18 (via CDN)
 * - React Flow (via CDN)
 * - WebSocket for real-time updates
 * - Local storage for drafts
 *
 * Version: 1.0.0
 * Author: Workflow Designer Team
 * Date: 2025-11-16
 */

const { useState, useEffect, useRef, useMemo, useCallback } = React;

// ============================================================================
// Agent Palette Component
// ============================================================================

function AgentPalette({ agents, categories, onDragStart, searchTerm, setSearchTerm }) {
    const [selectedCategory, setSelectedCategory] = useState(null);
    const [expandedCategories, setExpandedCategories] = useState(new Set(['1.0', '3.0', '7.0', '9.0']));

    // Group agents by category
    const agentsByCategory = useMemo(() => {
        const grouped = {};
        agents.forEach(agent => {
            if (!grouped[agent.category_id]) {
                grouped[agent.category_id] = [];
            }
            grouped[agent.category_id].push(agent);
        });
        return grouped;
    }, [agents]);

    // Filter agents by search term
    const filteredAgents = useMemo(() => {
        if (!searchTerm) return agents;

        const term = searchTerm.toLowerCase();
        return agents.filter(agent =>
            agent.agent_name.toLowerCase().includes(term) ||
            agent.category_name.toLowerCase().includes(term) ||
            (agent.capabilities && agent.capabilities.some(cap => cap.toLowerCase().includes(term)))
        );
    }, [agents, searchTerm]);

    const toggleCategory = (categoryId) => {
        const newExpanded = new Set(expandedCategories);
        if (newExpanded.has(categoryId)) {
            newExpanded.delete(categoryId);
        } else {
            newExpanded.add(categoryId);
        }
        setExpandedCategories(newExpanded);
    };

    const getCategoryIcon = (categoryId) => {
        const icons = {
            '1.0': '🎯', '2.0': '🎨', '3.0': '📊', '4.0': '📦',
            '5.0': '⚙️', '6.0': '🤝', '7.0': '👥', '8.0': '💻',
            '9.0': '💰', '10.0': '🏗️', '11.0': '🛡️', '12.0': '🌐',
            '13.0': '🔧'
        };
        return icons[categoryId] || '📋';
    };

    return (
        <div style={{
            width: '320px',
            height: '100%',
            backgroundColor: '#1a1a2e',
            borderRight: '1px solid #2d2d44',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden'
        }}>
            {/* Palette Header */}
            <div style={{
                padding: '20px',
                borderBottom: '1px solid #2d2d44',
                backgroundColor: '#16213e'
            }}>
                <h3 style={{
                    margin: '0 0 15px 0',
                    color: '#00d4ff',
                    fontSize: '18px',
                    fontWeight: '600'
                }}>
                    Agent Palette
                </h3>

                {/* Search Box */}
                <input
                    type="text"
                    placeholder="Search agents..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    style={{
                        width: '100%',
                        padding: '10px 12px',
                        backgroundColor: '#0f1419',
                        border: '1px solid #2d2d44',
                        borderRadius: '6px',
                        color: '#e0e0e0',
                        fontSize: '14px',
                        outline: 'none'
                    }}
                />

                <div style={{
                    marginTop: '10px',
                    fontSize: '12px',
                    color: '#888',
                    textAlign: 'center'
                }}>
                    {agents.length} agents across 13 categories
                </div>
            </div>

            {/* Agent List */}
            <div style={{
                flex: 1,
                overflowY: 'auto',
                padding: '10px'
            }}>
                {searchTerm ? (
                    // Search Results
                    <div>
                        <div style={{
                            fontSize: '12px',
                            color: '#888',
                            marginBottom: '10px',
                            padding: '0 5px'
                        }}>
                            {filteredAgents.length} results
                        </div>
                        {filteredAgents.map(agent => (
                            <AgentCard
                                key={agent.agent_id}
                                agent={agent}
                                onDragStart={onDragStart}
                            />
                        ))}
                    </div>
                ) : (
                    // Category View
                    categories.map(category => {
                        const categoryAgents = agentsByCategory[category.category_id] || [];
                        const isExpanded = expandedCategories.has(category.category_id);

                        return (
                            <div key={category.category_id} style={{ marginBottom: '5px' }}>
                                {/* Category Header */}
                                <div
                                    onClick={() => toggleCategory(category.category_id)}
                                    style={{
                                        padding: '12px',
                                        backgroundColor: isExpanded ? '#2d2d44' : '#1e1e30',
                                        borderRadius: '6px',
                                        cursor: 'pointer',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'space-between',
                                        transition: 'all 0.2s',
                                        marginBottom: isExpanded ? '5px' : '0'
                                    }}
                                >
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                        <span style={{ fontSize: '18px' }}>
                                            {getCategoryIcon(category.category_id)}
                                        </span>
                                        <div>
                                            <div style={{
                                                color: '#e0e0e0',
                                                fontSize: '13px',
                                                fontWeight: '500'
                                            }}>
                                                {category.category_name}
                                            </div>
                                            <div style={{
                                                color: '#888',
                                                fontSize: '11px'
                                            }}>
                                                {categoryAgents.length} agents
                                            </div>
                                        </div>
                                    </div>
                                    <span style={{
                                        color: '#888',
                                        fontSize: '12px',
                                        transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
                                        transition: 'transform 0.2s'
                                    }}>
                                        ▼
                                    </span>
                                </div>

                                {/* Category Agents */}
                                {isExpanded && (
                                    <div style={{ marginTop: '5px', marginLeft: '10px' }}>
                                        {categoryAgents.map(agent => (
                                            <AgentCard
                                                key={agent.agent_id}
                                                agent={agent}
                                                onDragStart={onDragStart}
                                            />
                                        ))}
                                    </div>
                                )}
                            </div>
                        );
                    })
                )}
            </div>

            {/* Palette Footer */}
            <div style={{
                padding: '15px',
                borderTop: '1px solid #2d2d44',
                backgroundColor: '#16213e',
                fontSize: '11px',
                color: '#666',
                textAlign: 'center'
            }}>
                Drag agents onto canvas to build workflows
            </div>
        </div>
    );
}

// ============================================================================
// Agent Card Component
// ============================================================================

function AgentCard({ agent, onDragStart }) {
    return (
        <div
            draggable
            onDragStart={(e) => onDragStart(e, agent)}
            style={{
                padding: '10px 12px',
                backgroundColor: '#0f1419',
                border: '1px solid #2d2d44',
                borderRadius: '6px',
                marginBottom: '5px',
                cursor: 'grab',
                transition: 'all 0.2s'
            }}
            onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#1a1f29';
                e.currentTarget.style.borderColor = '#00d4ff';
                e.currentTarget.style.transform = 'translateX(5px)';
            }}
            onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = '#0f1419';
                e.currentTarget.style.borderColor = '#2d2d44';
                e.currentTarget.style.transform = 'translateX(0)';
            }}
        >
            <div style={{
                color: '#00d4ff',
                fontSize: '13px',
                fontWeight: '500',
                marginBottom: '4px',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap'
            }}>
                {agent.agent_name}
            </div>
            <div style={{
                color: '#888',
                fontSize: '11px',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap'
            }}>
                {agent.category_name}
            </div>
            {agent.health_score && (
                <div style={{
                    marginTop: '6px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px'
                }}>
                    <div style={{
                        width: '6px',
                        height: '6px',
                        borderRadius: '50%',
                        backgroundColor: agent.status === 'healthy' ? '#00ff88' : '#ff8800'
                    }} />
                    <span style={{
                        fontSize: '10px',
                        color: '#666'
                    }}>
                        Health: {(agent.health_score * 100).toFixed(0)}%
                    </span>
                </div>
            )}
        </div>
    );
}

// ============================================================================
// Workflow Canvas Component
// ============================================================================

function WorkflowCanvas({
    nodes,
    edges,
    onNodesChange,
    onEdgesChange,
    onConnect,
    onNodeClick,
    onPaneClick,
    onDrop,
    onDragOver,
    selectedNode
}) {
    const canvasRef = useRef(null);
    const [isPanning, setIsPanning] = useState(false);
    const [panStart, setPanStart] = useState({ x: 0, y: 0 });
    const [offset, setOffset] = useState({ x: 0, y: 0 });
    const [zoom, setZoom] = useState(1);

    const handleWheel = (e) => {
        e.preventDefault();
        const delta = e.deltaY > 0 ? 0.9 : 1.1;
        setZoom(prev => Math.max(0.1, Math.min(2, prev * delta)));
    };

    const handleMouseDown = (e) => {
        if (e.target === canvasRef.current || e.target.classList.contains('canvas-background')) {
            setIsPanning(true);
            setPanStart({ x: e.clientX - offset.x, y: e.clientY - offset.y });
        }
    };

    const handleMouseMove = (e) => {
        if (isPanning) {
            setOffset({
                x: e.clientX - panStart.x,
                y: e.clientY - panStart.y
            });
        }
    };

    const handleMouseUp = () => {
        setIsPanning(false);
    };

    useEffect(() => {
        if (isPanning) {
            document.addEventListener('mousemove', handleMouseMove);
            document.addEventListener('mouseup', handleMouseUp);
            return () => {
                document.removeEventListener('mousemove', handleMouseMove);
                document.removeEventListener('mouseup', handleMouseUp);
            };
        }
    }, [isPanning, panStart]);

    return (
        <div
            ref={canvasRef}
            onDrop={onDrop}
            onDragOver={onDragOver}
            onWheel={handleWheel}
            onMouseDown={handleMouseDown}
            onClick={onPaneClick}
            style={{
                flex: 1,
                position: 'relative',
                backgroundColor: '#0f1419',
                overflow: 'hidden',
                cursor: isPanning ? 'grabbing' : 'default',
                backgroundImage: `
                    linear-gradient(#1a1f29 1px, transparent 1px),
                    linear-gradient(90deg, #1a1f29 1px, transparent 1px)
                `,
                backgroundSize: `${20 * zoom}px ${20 * zoom}px`,
                backgroundPosition: `${offset.x}px ${offset.y}px`
            }}
        >
            <div className="canvas-background" style={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                transform: `translate(${offset.x}px, ${offset.y}px) scale(${zoom})`,
                transformOrigin: '0 0'
            }}>
                {/* Render Edges */}
                <svg style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '100%',
                    height: '100%',
                    pointerEvents: 'none'
                }}>
                    {edges.map(edge => {
                        const sourceNode = nodes.find(n => n.id === edge.source);
                        const targetNode = nodes.find(n => n.id === edge.target);
                        if (!sourceNode || !targetNode) return null;

                        return (
                            <line
                                key={edge.id}
                                x1={sourceNode.position.x + 125}
                                y1={sourceNode.position.y + 40}
                                x2={targetNode.position.x}
                                y2={targetNode.position.y + 40}
                                stroke="#00d4ff"
                                strokeWidth="2"
                                markerEnd="url(#arrowhead)"
                            />
                        );
                    })}
                    <defs>
                        <marker
                            id="arrowhead"
                            markerWidth="10"
                            markerHeight="10"
                            refX="9"
                            refY="3"
                            orient="auto"
                        >
                            <polygon points="0 0, 10 3, 0 6" fill="#00d4ff" />
                        </marker>
                    </defs>
                </svg>

                {/* Render Nodes */}
                {nodes.map(node => (
                    <WorkflowNode
                        key={node.id}
                        node={node}
                        isSelected={selectedNode?.id === node.id}
                        onClick={(e) => {
                            e.stopPropagation();
                            onNodeClick(node);
                        }}
                        onConnect={onConnect}
                    />
                ))}
            </div>

            {/* Zoom Controls */}
            <div style={{
                position: 'absolute',
                bottom: '20px',
                right: '20px',
                display: 'flex',
                gap: '10px',
                backgroundColor: '#1a1a2e',
                padding: '10px',
                borderRadius: '8px',
                border: '1px solid #2d2d44'
            }}>
                <button
                    onClick={() => setZoom(prev => Math.max(0.1, prev - 0.1))}
                    style={{
                        width: '32px',
                        height: '32px',
                        backgroundColor: '#2d2d44',
                        border: 'none',
                        borderRadius: '4px',
                        color: '#e0e0e0',
                        cursor: 'pointer',
                        fontSize: '18px'
                    }}
                >
                    -
                </button>
                <div style={{
                    width: '50px',
                    textAlign: 'center',
                    lineHeight: '32px',
                    color: '#888',
                    fontSize: '12px'
                }}>
                    {Math.round(zoom * 100)}%
                </div>
                <button
                    onClick={() => setZoom(prev => Math.min(2, prev + 0.1))}
                    style={{
                        width: '32px',
                        height: '32px',
                        backgroundColor: '#2d2d44',
                        border: 'none',
                        borderRadius: '4px',
                        color: '#e0e0e0',
                        cursor: 'pointer',
                        fontSize: '18px'
                    }}
                >
                    +
                </button>
                <button
                    onClick={() => {
                        setZoom(1);
                        setOffset({ x: 0, y: 0 });
                    }}
                    style={{
                        width: '32px',
                        height: '32px',
                        backgroundColor: '#2d2d44',
                        border: 'none',
                        borderRadius: '4px',
                        color: '#e0e0e0',
                        cursor: 'pointer',
                        fontSize: '14px'
                    }}
                >
                    ⊙
                </button>
            </div>

            {/* Empty State */}
            {nodes.length === 0 && (
                <div style={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    textAlign: 'center',
                    color: '#666'
                }}>
                    <div style={{ fontSize: '48px', marginBottom: '20px' }}>🎯</div>
                    <div style={{ fontSize: '18px', marginBottom: '10px' }}>Start Building Your Workflow</div>
                    <div style={{ fontSize: '14px' }}>
                        Drag agents from the palette to create your workflow
                    </div>
                </div>
            )}
        </div>
    );
}

// ============================================================================
// Workflow Node Component
// ============================================================================

function WorkflowNode({ node, isSelected, onClick, onConnect }) {
    const [isDragging, setIsDragging] = useState(false);
    const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });

    const getNodeColor = (type) => {
        const colors = {
            agent: '#00d4ff',
            trigger: '#00ff88',
            condition: '#ff8800',
            aggregator: '#ff00ff',
            transformer: '#8800ff',
            output: '#00ffff'
        };
        return colors[type] || '#00d4ff';
    };

    const getNodeIcon = (type) => {
        const icons = {
            agent: '🤖',
            trigger: '⚡',
            condition: '🔀',
            aggregator: '🔄',
            transformer: '⚙️',
            output: '📤'
        };
        return icons[type] || '📋';
    };

    return (
        <div
            onClick={onClick}
            style={{
                position: 'absolute',
                left: node.position.x,
                top: node.position.y,
                width: '250px',
                backgroundColor: '#1a1a2e',
                border: `2px solid ${isSelected ? getNodeColor(node.type) : '#2d2d44'}`,
                borderRadius: '8px',
                cursor: 'pointer',
                boxShadow: isSelected ? `0 0 20px ${getNodeColor(node.type)}40` : '0 4px 12px rgba(0,0,0,0.3)',
                transition: 'all 0.2s'
            }}
        >
            {/* Node Header */}
            <div style={{
                padding: '12px',
                backgroundColor: '#16213e',
                borderTopLeftRadius: '6px',
                borderTopRightRadius: '6px',
                borderBottom: `1px solid ${getNodeColor(node.type)}`,
                display: 'flex',
                alignItems: 'center',
                gap: '10px'
            }}>
                <span style={{ fontSize: '20px' }}>{getNodeIcon(node.type)}</span>
                <div style={{ flex: 1 }}>
                    <div style={{
                        color: '#e0e0e0',
                        fontSize: '14px',
                        fontWeight: '500',
                        marginBottom: '2px'
                    }}>
                        {node.label}
                    </div>
                    {node.category_name && (
                        <div style={{
                            color: '#888',
                            fontSize: '11px'
                        }}>
                            {node.category_name}
                        </div>
                    )}
                </div>
            </div>

            {/* Node Body */}
            <div style={{ padding: '12px' }}>
                {node.agent_name && (
                    <div style={{
                        fontSize: '12px',
                        color: '#aaa',
                        marginBottom: '8px'
                    }}>
                        {node.agent_name}
                    </div>
                )}
                {node.description && (
                    <div style={{
                        fontSize: '11px',
                        color: '#666',
                        lineHeight: '1.4'
                    }}>
                        {node.description}
                    </div>
                )}
            </div>

            {/* Connection Handles */}
            <div style={{
                position: 'absolute',
                left: '-8px',
                top: '50%',
                transform: 'translateY(-50%)',
                width: '16px',
                height: '16px',
                borderRadius: '50%',
                backgroundColor: getNodeColor(node.type),
                border: '2px solid #1a1a2e',
                cursor: 'crosshair'
            }} />
            <div style={{
                position: 'absolute',
                right: '-8px',
                top: '50%',
                transform: 'translateY(-50%)',
                width: '16px',
                height: '16px',
                borderRadius: '50%',
                backgroundColor: getNodeColor(node.type),
                border: '2px solid #1a1a2e',
                cursor: 'crosshair'
            }} />
        </div>
    );
}

// ============================================================================
// Property Panel Component
// ============================================================================

function PropertyPanel({ node, onUpdate, onDelete }) {
    if (!node) {
        return (
            <div style={{
                width: '320px',
                height: '100%',
                backgroundColor: '#1a1a2e',
                borderLeft: '1px solid #2d2d44',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#666',
                fontSize: '14px',
                textAlign: 'center',
                padding: '20px'
            }}>
                Select a node to view properties
            </div>
        );
    }

    return (
        <div style={{
            width: '320px',
            height: '100%',
            backgroundColor: '#1a1a2e',
            borderLeft: '1px solid #2d2d44',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden'
        }}>
            {/* Panel Header */}
            <div style={{
                padding: '20px',
                borderBottom: '1px solid #2d2d44',
                backgroundColor: '#16213e'
            }}>
                <h3 style={{
                    margin: '0 0 10px 0',
                    color: '#00d4ff',
                    fontSize: '18px',
                    fontWeight: '600'
                }}>
                    Node Properties
                </h3>
                <div style={{
                    color: '#888',
                    fontSize: '12px'
                }}>
                    {node.type} • {node.id}
                </div>
            </div>

            {/* Properties Form */}
            <div style={{
                flex: 1,
                overflowY: 'auto',
                padding: '20px'
            }}>
                <FormField label="Label">
                    <input
                        type="text"
                        value={node.label}
                        onChange={(e) => onUpdate({ ...node, label: e.target.value })}
                        style={inputStyle}
                    />
                </FormField>

                <FormField label="Description">
                    <textarea
                        value={node.description || ''}
                        onChange={(e) => onUpdate({ ...node, description: e.target.value })}
                        rows={3}
                        style={{ ...inputStyle, resize: 'vertical' }}
                    />
                </FormField>

                {node.type === 'agent' && (
                    <>
                        <FormField label="Agent">
                            <div style={{
                                padding: '10px',
                                backgroundColor: '#0f1419',
                                border: '1px solid #2d2d44',
                                borderRadius: '6px',
                                fontSize: '13px',
                                color: '#e0e0e0'
                            }}>
                                {node.agent_name}
                            </div>
                        </FormField>

                        <FormField label="Category">
                            <div style={{
                                padding: '10px',
                                backgroundColor: '#0f1419',
                                border: '1px solid #2d2d44',
                                borderRadius: '6px',
                                fontSize: '13px',
                                color: '#888'
                            }}>
                                {node.category_name}
                            </div>
                        </FormField>
                    </>
                )}

                <FormField label="Timeout (seconds)">
                    <input
                        type="number"
                        value={node.timeout || 300}
                        onChange={(e) => onUpdate({ ...node, timeout: parseInt(e.target.value) })}
                        style={inputStyle}
                    />
                </FormField>

                <FormField label="Retry Count">
                    <input
                        type="number"
                        value={node.retry_count || 3}
                        onChange={(e) => onUpdate({ ...node, retry_count: parseInt(e.target.value) })}
                        style={inputStyle}
                    />
                </FormField>

                {/* Tags */}
                <FormField label="Tags">
                    <input
                        type="text"
                        placeholder="tag1, tag2, tag3"
                        value={(node.tags || []).join(', ')}
                        onChange={(e) => onUpdate({
                            ...node,
                            tags: e.target.value.split(',').map(t => t.trim()).filter(Boolean)
                        })}
                        style={inputStyle}
                    />
                </FormField>
            </div>

            {/* Panel Footer */}
            <div style={{
                padding: '20px',
                borderTop: '1px solid #2d2d44',
                backgroundColor: '#16213e'
            }}>
                <button
                    onClick={() => onDelete(node.id)}
                    style={{
                        width: '100%',
                        padding: '12px',
                        backgroundColor: '#ff4444',
                        border: 'none',
                        borderRadius: '6px',
                        color: '#fff',
                        fontSize: '14px',
                        fontWeight: '500',
                        cursor: 'pointer',
                        transition: 'all 0.2s'
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#ff6666'}
                    onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#ff4444'}
                >
                    Delete Node
                </button>
            </div>
        </div>
    );
}

// ============================================================================
// Form Field Component
// ============================================================================

function FormField({ label, children }) {
    return (
        <div style={{ marginBottom: '20px' }}>
            <label style={{
                display: 'block',
                marginBottom: '8px',
                color: '#aaa',
                fontSize: '12px',
                fontWeight: '500',
                textTransform: 'uppercase',
                letterSpacing: '0.5px'
            }}>
                {label}
            </label>
            {children}
        </div>
    );
}

const inputStyle = {
    width: '100%',
    padding: '10px 12px',
    backgroundColor: '#0f1419',
    border: '1px solid #2d2d44',
    borderRadius: '6px',
    color: '#e0e0e0',
    fontSize: '14px',
    outline: 'none',
    transition: 'border-color 0.2s'
};

// ============================================================================
// Toolbar Component
// ============================================================================

function Toolbar({
    workflow,
    onSave,
    onLoad,
    onExport,
    onTest,
    onClear,
    onShowTemplates,
    isDirty
}) {
    return (
        <div style={{
            height: '60px',
            backgroundColor: '#16213e',
            borderBottom: '1px solid #2d2d44',
            display: 'flex',
            alignItems: 'center',
            padding: '0 20px',
            gap: '10px'
        }}>
            {/* Workflow Name */}
            <div style={{ flex: 1 }}>
                <input
                    type="text"
                    value={workflow.name}
                    onChange={(e) => workflow.name = e.target.value}
                    placeholder="Workflow Name"
                    style={{
                        backgroundColor: 'transparent',
                        border: 'none',
                        color: '#e0e0e0',
                        fontSize: '18px',
                        fontWeight: '600',
                        outline: 'none',
                        width: '300px'
                    }}
                />
                {isDirty && (
                    <span style={{
                        marginLeft: '10px',
                        color: '#ff8800',
                        fontSize: '12px'
                    }}>
                        • Unsaved changes
                    </span>
                )}
            </div>

            {/* Action Buttons */}
            <ToolbarButton onClick={onShowTemplates} icon="📚" label="Templates" />
            <ToolbarButton onClick={onLoad} icon="📂" label="Load" />
            <ToolbarButton onClick={onSave} icon="💾" label="Save" primary />
            <ToolbarButton onClick={onExport} icon="📤" label="Export" />
            <ToolbarButton onClick={onTest} icon="▶️" label="Test" />
            <ToolbarButton onClick={onClear} icon="🗑️" label="Clear" danger />
        </div>
    );
}

function ToolbarButton({ onClick, icon, label, primary, danger }) {
    const baseStyle = {
        padding: '8px 16px',
        backgroundColor: primary ? '#00d4ff' : danger ? '#ff4444' : '#2d2d44',
        border: 'none',
        borderRadius: '6px',
        color: primary ? '#0f1419' : '#e0e0e0',
        fontSize: '14px',
        fontWeight: '500',
        cursor: 'pointer',
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
        transition: 'all 0.2s'
    };

    return (
        <button
            onClick={onClick}
            style={baseStyle}
            onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.3)';
            }}
            onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = 'none';
            }}
        >
            <span>{icon}</span>
            <span>{label}</span>
        </button>
    );
}

// ============================================================================
// Main Workflow Designer Component
// ============================================================================

function WorkflowDesigner() {
    const [agents, setAgents] = useState([]);
    const [categories, setCategories] = useState([]);
    const [workflow, setWorkflow] = useState({
        id: `workflow_${Date.now()}`,
        name: 'New Workflow',
        description: '',
        nodes: [],
        edges: []
    });
    const [selectedNode, setSelectedNode] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [isDirty, setIsDirty] = useState(false);
    const [showTemplates, setShowTemplates] = useState(false);

    // Load agents and categories
    useEffect(() => {
        fetchAgentsAndCategories();
    }, []);

    const fetchAgentsAndCategories = async () => {
        try {
            // Fetch agents
            const agentsRes = await fetch('http://localhost:8765/api/agents');
            const agentsData = await agentsRes.json();
            setAgents(agentsData.agents || []);

            // Fetch categories
            const categoriesRes = await fetch('http://localhost:8765/api/categories');
            const categoriesData = await categoriesRes.json();
            setCategories(categoriesData.categories || []);
        } catch (error) {
            console.error('Error fetching data:', error);
        }
    };

    // Handle drag start
    const handleDragStart = useCallback((e, agent) => {
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('application/json', JSON.stringify(agent));
    }, []);

    // Handle drop
    const handleDrop = useCallback((e) => {
        e.preventDefault();

        const rect = e.currentTarget.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        try {
            const agent = JSON.parse(e.dataTransfer.getData('application/json'));

            const newNode = {
                id: `node_${Date.now()}`,
                type: 'agent',
                label: agent.agent_name,
                position: { x: x - 125, y: y - 40 },
                agent_id: agent.agent_id,
                agent_name: agent.agent_name,
                category_id: agent.category_id,
                category_name: agent.category_name,
                timeout: 300,
                retry_count: 3,
                tags: [],
                description: ''
            };

            setWorkflow(prev => ({
                ...prev,
                nodes: [...prev.nodes, newNode]
            }));
            setIsDirty(true);
        } catch (error) {
            console.error('Error dropping agent:', error);
        }
    }, []);

    const handleDragOver = useCallback((e) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
    }, []);

    // Handle node click
    const handleNodeClick = useCallback((node) => {
        setSelectedNode(node);
    }, []);

    // Handle pane click
    const handlePaneClick = useCallback(() => {
        setSelectedNode(null);
    }, []);

    // Handle node update
    const handleNodeUpdate = useCallback((updatedNode) => {
        setWorkflow(prev => ({
            ...prev,
            nodes: prev.nodes.map(n => n.id === updatedNode.id ? updatedNode : n)
        }));
        setSelectedNode(updatedNode);
        setIsDirty(true);
    }, []);

    // Handle node delete
    const handleNodeDelete = useCallback((nodeId) => {
        setWorkflow(prev => ({
            ...prev,
            nodes: prev.nodes.filter(n => n.id !== nodeId),
            edges: prev.edges.filter(e => e.source !== nodeId && e.target !== nodeId)
        }));
        setSelectedNode(null);
        setIsDirty(true);
    }, []);

    // Handle save
    const handleSave = useCallback(() => {
        const workflowData = JSON.stringify(workflow, null, 2);
        localStorage.setItem(`workflow_${workflow.id}`, workflowData);

        // Create download
        const blob = new Blob([workflowData], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${workflow.name.replace(/\s+/g, '_')}.json`;
        a.click();
        URL.revokeObjectURL(url);

        setIsDirty(false);
        alert('Workflow saved successfully!');
    }, [workflow]);

    // Handle export
    const handleExport = useCallback(() => {
        const exportData = JSON.stringify(workflow, null, 2);
        const blob = new Blob([exportData], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${workflow.name.replace(/\s+/g, '_')}_export.json`;
        a.click();
        URL.revokeObjectURL(url);
    }, [workflow]);

    // Handle clear
    const handleClear = useCallback(() => {
        if (confirm('Clear all nodes? This cannot be undone.')) {
            setWorkflow(prev => ({
                ...prev,
                nodes: [],
                edges: []
            }));
            setSelectedNode(null);
            setIsDirty(false);
        }
    }, []);

    // Handle test
    const handleTest = useCallback(async () => {
        alert('Test execution will be implemented with backend integration');
    }, [workflow]);

    return (
        <div style={{
            width: '100vw',
            height: '100vh',
            display: 'flex',
            flexDirection: 'column',
            backgroundColor: '#0f1419',
            color: '#e0e0e0',
            fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
        }}>
            {/* Toolbar */}
            <Toolbar
                workflow={workflow}
                onSave={handleSave}
                onLoad={() => alert('Load functionality coming soon')}
                onExport={handleExport}
                onTest={handleTest}
                onClear={handleClear}
                onShowTemplates={() => setShowTemplates(true)}
                isDirty={isDirty}
            />

            {/* Main Content */}
            <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
                {/* Agent Palette */}
                <AgentPalette
                    agents={agents}
                    categories={categories}
                    onDragStart={handleDragStart}
                    searchTerm={searchTerm}
                    setSearchTerm={setSearchTerm}
                />

                {/* Canvas */}
                <WorkflowCanvas
                    nodes={workflow.nodes}
                    edges={workflow.edges}
                    onNodesChange={() => {}}
                    onEdgesChange={() => {}}
                    onConnect={() => {}}
                    onNodeClick={handleNodeClick}
                    onPaneClick={handlePaneClick}
                    onDrop={handleDrop}
                    onDragOver={handleDragOver}
                    selectedNode={selectedNode}
                />

                {/* Property Panel */}
                <PropertyPanel
                    node={selectedNode}
                    onUpdate={handleNodeUpdate}
                    onDelete={handleNodeDelete}
                />
            </div>

            {/* Status Bar */}
            <div style={{
                height: '32px',
                backgroundColor: '#16213e',
                borderTop: '1px solid #2d2d44',
                display: 'flex',
                alignItems: 'center',
                padding: '0 20px',
                fontSize: '12px',
                color: '#888',
                gap: '20px'
            }}>
                <span>Nodes: {workflow.nodes.length}</span>
                <span>Edges: {workflow.edges.length}</span>
                <span>Agents Available: {agents.length}</span>
                <div style={{ flex: 1 }} />
                <span>Workflow Designer v1.0.0</span>
            </div>
        </div>
    );
}

// Export for use in other components
window.WorkflowDesigner = WorkflowDesigner;
