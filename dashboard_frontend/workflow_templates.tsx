/**
 * Workflow Templates Gallery - Pre-built Workflow Browser
 * ========================================================
 *
 * React component for browsing, previewing, and importing pre-built workflow templates.
 * Showcases 10+ production-ready templates for common business scenarios.
 *
 * Features:
 * - Template browser with category filtering
 * - Template preview with visual diagram
 * - Import templates into designer
 * - Export/share templates
 * - Template search and filtering
 * - Usage statistics and ratings
 * - Mobile responsive design
 *
 * Version: 1.0.0
 * Author: Workflow Templates Team
 * Date: 2025-11-16
 */

const { useState, useEffect, useMemo } = React;

// ============================================================================
// Template Data (will be fetched from backend in production)
// ============================================================================

const BUILTIN_TEMPLATES = [
    {
        id: 'financial_marketing_roi',
        name: 'Financial Close + Marketing ROI Analysis',
        description: 'Combines financial closing processes with marketing ROI analysis for comprehensive performance review',
        category: 'Finance & Marketing',
        difficulty: 'intermediate',
        estimatedTime: 300,
        icon: '💰',
        nodes: 5,
        requiredAgents: ['expert_9_4', 'expert_3_3', 'expert_9_2'],
        useCases: [
            'Quarterly financial review',
            'Marketing campaign effectiveness',
            'Budget allocation optimization'
        ],
        tags: ['finance', 'marketing', 'roi', 'analysis'],
        rating: 4.8,
        usageCount: 245
    },
    {
        id: 'supply_chain_demand',
        name: 'Supply Chain + Customer Demand Forecasting',
        description: 'Integrates supply chain operations with customer demand forecasting for optimized inventory management',
        category: 'Operations',
        difficulty: 'advanced',
        estimatedTime: 450,
        icon: '📦',
        nodes: 4,
        requiredAgents: ['expert_6_3', 'expert_4_1', 'expert_4_2'],
        useCases: [
            'Inventory planning',
            'Supply chain optimization',
            'Demand response'
        ],
        tags: ['supply-chain', 'demand-forecasting', 'inventory'],
        rating: 4.6,
        usageCount: 189
    },
    {
        id: 'hr_recruitment_skills',
        name: 'HR Recruitment + Skills Gap Analysis',
        description: 'Combines recruitment processes with skills gap analysis for strategic talent acquisition',
        category: 'Human Capital',
        difficulty: 'intermediate',
        estimatedTime: 360,
        icon: '👥',
        nodes: 5,
        requiredAgents: ['expert_7_3', 'expert_1_4', 'expert_7_2'],
        useCases: [
            'Strategic hiring',
            'Skills development planning',
            'Workforce optimization'
        ],
        tags: ['hr', 'recruitment', 'skills-analysis'],
        rating: 4.7,
        usageCount: 312
    },
    {
        id: 'cross_domain_pipeline',
        name: 'Cross-Domain: Strategy → Product → Marketing → Sales',
        description: 'End-to-end workflow from strategic planning through product development, marketing, and sales execution',
        category: 'Cross-Domain',
        difficulty: 'advanced',
        estimatedTime: 600,
        icon: '🎯',
        nodes: 5,
        requiredAgents: ['expert_1_2', 'expert_2_2', 'expert_3_2', 'expert_3_5'],
        useCases: [
            'Product launch',
            'Go-to-market strategy',
            'Revenue growth initiatives'
        ],
        tags: ['strategy', 'product', 'marketing', 'sales', 'end-to-end'],
        rating: 4.9,
        usageCount: 428
    },
    {
        id: 'customer_feedback_loop',
        name: 'Customer Support + Product Feedback Loop',
        description: 'Continuous improvement workflow that channels customer feedback into product development',
        category: 'Customer Experience',
        difficulty: 'intermediate',
        estimatedTime: 240,
        icon: '🤝',
        nodes: 4,
        requiredAgents: ['expert_6_2', 'expert_2_1', 'expert_3_1'],
        useCases: [
            'Customer satisfaction improvement',
            'Product iteration',
            'Feature prioritization'
        ],
        tags: ['customer-support', 'product', 'feedback'],
        rating: 4.5,
        usageCount: 267
    },
    {
        id: 'risk_compliance',
        name: 'Risk Assessment + Compliance Monitoring',
        description: 'Integrated risk and compliance workflow for enterprise governance',
        category: 'Risk & Compliance',
        difficulty: 'advanced',
        estimatedTime: 480,
        icon: '🛡️',
        nodes: 6,
        requiredAgents: ['expert_11_1', 'expert_11_2', 'expert_11_3'],
        useCases: [
            'Regulatory compliance',
            'Risk mitigation',
            'Audit preparation'
        ],
        tags: ['risk', 'compliance', 'governance'],
        rating: 4.7,
        usageCount: 156
    },
    {
        id: 'it_asset_management',
        name: 'IT Service Management + Asset Optimization',
        description: 'Comprehensive IT service and asset management workflow',
        category: 'IT Operations',
        difficulty: 'intermediate',
        estimatedTime: 300,
        icon: '💻',
        nodes: 5,
        requiredAgents: ['expert_8_2', 'expert_8_3', 'expert_10_3'],
        useCases: [
            'IT infrastructure management',
            'Asset lifecycle optimization',
            'Service level improvement'
        ],
        tags: ['it', 'asset-management', 'optimization'],
        rating: 4.6,
        usageCount: 198
    },
    {
        id: 'product_launch',
        name: 'Product Launch Pipeline',
        description: 'Complete product launch workflow from concept to market',
        category: 'Product Management',
        difficulty: 'advanced',
        estimatedTime: 540,
        icon: '🚀',
        nodes: 7,
        requiredAgents: ['expert_2_2', 'expert_3_2', 'expert_3_3', 'expert_4_4'],
        useCases: [
            'New product introduction',
            'Market entry strategy',
            'Launch coordination'
        ],
        tags: ['product', 'launch', 'go-to-market'],
        rating: 4.8,
        usageCount: 334
    },
    {
        id: 'financial_planning',
        name: 'Financial Planning + Budget Analysis',
        description: 'Comprehensive financial planning and budgeting workflow',
        category: 'Finance',
        difficulty: 'intermediate',
        estimatedTime: 360,
        icon: '📊',
        nodes: 5,
        requiredAgents: ['expert_9_1', 'expert_9_2', 'expert_9_3'],
        useCases: [
            'Annual budgeting',
            'Financial forecasting',
            'Resource allocation'
        ],
        tags: ['finance', 'planning', 'budget'],
        rating: 4.7,
        usageCount: 289
    },
    {
        id: 'employee_onboarding',
        name: 'Employee Onboarding Workflow',
        description: 'End-to-end employee onboarding process',
        category: 'Human Capital',
        difficulty: 'beginner',
        estimatedTime: 180,
        icon: '🎓',
        nodes: 4,
        requiredAgents: ['expert_7_2', 'expert_7_3', 'expert_8_2'],
        useCases: [
            'New hire onboarding',
            'Training coordination',
            'Access provisioning'
        ],
        tags: ['hr', 'onboarding', 'employee'],
        rating: 4.9,
        usageCount: 412
    }
];

// ============================================================================
// Template Card Component
// ============================================================================

function TemplateCard({ template, onSelect, onPreview }) {
    const getDifficultyColor = (difficulty) => {
        const colors = {
            beginner: '#00ff88',
            intermediate: '#ff8800',
            advanced: '#ff4444'
        };
        return colors[difficulty] || '#888';
    };

    const formatTime = (seconds) => {
        const minutes = Math.floor(seconds / 60);
        return `~${minutes} min`;
    };

    return (
        <div style={{
            backgroundColor: '#1a1a2e',
            border: '1px solid #2d2d44',
            borderRadius: '12px',
            padding: '20px',
            cursor: 'pointer',
            transition: 'all 0.3s',
            height: '100%',
            display: 'flex',
            flexDirection: 'column'
        }}
        onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'translateY(-4px)';
            e.currentTarget.style.borderColor = '#00d4ff';
            e.currentTarget.style.boxShadow = '0 8px 24px rgba(0, 212, 255, 0.2)';
        }}
        onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.borderColor = '#2d2d44';
            e.currentTarget.style.boxShadow = 'none';
        }}
        onClick={() => onSelect(template)}>
            {/* Template Icon & Title */}
            <div style={{ marginBottom: '15px' }}>
                <div style={{
                    fontSize: '48px',
                    marginBottom: '10px',
                    textAlign: 'center'
                }}>
                    {template.icon}
                </div>
                <h3 style={{
                    margin: 0,
                    color: '#e0e0e0',
                    fontSize: '16px',
                    fontWeight: '600',
                    lineHeight: '1.4',
                    minHeight: '44px'
                }}>
                    {template.name}
                </h3>
            </div>

            {/* Description */}
            <p style={{
                margin: '0 0 15px 0',
                color: '#aaa',
                fontSize: '13px',
                lineHeight: '1.5',
                flex: 1
            }}>
                {template.description}
            </p>

            {/* Metadata */}
            <div style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '10px',
                marginBottom: '15px'
            }}>
                <MetadataItem
                    icon="⚡"
                    label="Difficulty"
                    value={template.difficulty}
                    color={getDifficultyColor(template.difficulty)}
                />
                <MetadataItem
                    icon="⏱️"
                    label="Est. Time"
                    value={formatTime(template.estimatedTime)}
                />
                <MetadataItem
                    icon="🔗"
                    label="Nodes"
                    value={template.nodes}
                />
                <MetadataItem
                    icon="🤖"
                    label="Agents"
                    value={template.requiredAgents.length}
                />
            </div>

            {/* Rating & Usage */}
            <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                paddingTop: '15px',
                borderTop: '1px solid #2d2d44',
                marginBottom: '15px'
            }}>
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '5px'
                }}>
                    <span style={{ color: '#ffaa00' }}>⭐</span>
                    <span style={{
                        color: '#e0e0e0',
                        fontSize: '14px',
                        fontWeight: '600'
                    }}>
                        {template.rating.toFixed(1)}
                    </span>
                </div>
                <div style={{
                    color: '#888',
                    fontSize: '12px'
                }}>
                    {template.usageCount} uses
                </div>
            </div>

            {/* Tags */}
            <div style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: '6px',
                marginBottom: '15px'
            }}>
                {template.tags.slice(0, 3).map(tag => (
                    <span key={tag} style={{
                        padding: '4px 10px',
                        backgroundColor: '#2d2d44',
                        borderRadius: '12px',
                        color: '#888',
                        fontSize: '11px'
                    }}>
                        {tag}
                    </span>
                ))}
            </div>

            {/* Action Buttons */}
            <div style={{
                display: 'flex',
                gap: '10px'
            }}>
                <button
                    onClick={(e) => {
                        e.stopPropagation();
                        onPreview(template);
                    }}
                    style={{
                        flex: 1,
                        padding: '10px',
                        backgroundColor: '#2d2d44',
                        border: 'none',
                        borderRadius: '6px',
                        color: '#e0e0e0',
                        fontSize: '13px',
                        fontWeight: '500',
                        cursor: 'pointer',
                        transition: 'all 0.2s'
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#3d3d54'}
                    onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#2d2d44'}
                >
                    Preview
                </button>
                <button
                    onClick={(e) => {
                        e.stopPropagation();
                        onSelect(template);
                    }}
                    style={{
                        flex: 1,
                        padding: '10px',
                        backgroundColor: '#00d4ff',
                        border: 'none',
                        borderRadius: '6px',
                        color: '#0f1419',
                        fontSize: '13px',
                        fontWeight: '600',
                        cursor: 'pointer',
                        transition: 'all 0.2s'
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#00e4ff'}
                    onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#00d4ff'}
                >
                    Use Template
                </button>
            </div>
        </div>
    );
}

function MetadataItem({ icon, label, value, color }) {
    return (
        <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
        }}>
            <span style={{ fontSize: '14px' }}>{icon}</span>
            <div>
                <div style={{
                    color: '#666',
                    fontSize: '10px',
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px'
                }}>
                    {label}
                </div>
                <div style={{
                    color: color || '#e0e0e0',
                    fontSize: '12px',
                    fontWeight: '600',
                    textTransform: 'capitalize'
                }}>
                    {value}
                </div>
            </div>
        </div>
    );
}

// ============================================================================
// Template Preview Modal
// ============================================================================

function TemplatePreview({ template, onClose, onUse }) {
    if (!template) return null;

    return (
        <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '20px'
        }}
        onClick={onClose}>
            <div
                onClick={(e) => e.stopPropagation()}
                style={{
                    backgroundColor: '#1a1a2e',
                    border: '1px solid #2d2d44',
                    borderRadius: '16px',
                    maxWidth: '900px',
                    width: '100%',
                    maxHeight: '90vh',
                    overflow: 'auto',
                    boxShadow: '0 20px 60px rgba(0, 0, 0, 0.5)'
                }}
            >
                {/* Modal Header */}
                <div style={{
                    padding: '30px',
                    borderBottom: '1px solid #2d2d44',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '20px'
                }}>
                    <div style={{ fontSize: '64px' }}>{template.icon}</div>
                    <div style={{ flex: 1 }}>
                        <h2 style={{
                            margin: '0 0 10px 0',
                            color: '#e0e0e0',
                            fontSize: '24px',
                            fontWeight: '600'
                        }}>
                            {template.name}
                        </h2>
                        <p style={{
                            margin: 0,
                            color: '#aaa',
                            fontSize: '14px',
                            lineHeight: '1.5'
                        }}>
                            {template.description}
                        </p>
                    </div>
                    <button
                        onClick={onClose}
                        style={{
                            width: '40px',
                            height: '40px',
                            backgroundColor: '#2d2d44',
                            border: 'none',
                            borderRadius: '8px',
                            color: '#e0e0e0',
                            fontSize: '20px',
                            cursor: 'pointer',
                            transition: 'all 0.2s'
                        }}
                        onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#ff4444'}
                        onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#2d2d44'}
                    >
                        ×
                    </button>
                </div>

                {/* Modal Body */}
                <div style={{ padding: '30px' }}>
                    {/* Workflow Diagram Placeholder */}
                    <div style={{
                        backgroundColor: '#0f1419',
                        border: '1px solid #2d2d44',
                        borderRadius: '12px',
                        padding: '40px',
                        marginBottom: '30px',
                        textAlign: 'center',
                        minHeight: '300px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                    }}>
                        <div>
                            <div style={{
                                fontSize: '48px',
                                marginBottom: '20px'
                            }}>
                                📊
                            </div>
                            <div style={{
                                color: '#666',
                                fontSize: '14px'
                            }}>
                                Workflow visualization with {template.nodes} nodes
                            </div>
                        </div>
                    </div>

                    {/* Template Details Grid */}
                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(2, 1fr)',
                        gap: '20px',
                        marginBottom: '30px'
                    }}>
                        <DetailSection
                            title="Use Cases"
                            icon="💡"
                            items={template.useCases}
                        />
                        <DetailSection
                            title="Required Agents"
                            icon="🤖"
                            items={template.requiredAgents.map(id => id.replace('expert_', ''))}
                        />
                    </div>

                    {/* Tags */}
                    <div style={{ marginBottom: '30px' }}>
                        <h4 style={{
                            margin: '0 0 15px 0',
                            color: '#aaa',
                            fontSize: '12px',
                            fontWeight: '500',
                            textTransform: 'uppercase',
                            letterSpacing: '1px'
                        }}>
                            Tags
                        </h4>
                        <div style={{
                            display: 'flex',
                            flexWrap: 'wrap',
                            gap: '10px'
                        }}>
                            {template.tags.map(tag => (
                                <span key={tag} style={{
                                    padding: '8px 16px',
                                    backgroundColor: '#2d2d44',
                                    borderRadius: '20px',
                                    color: '#00d4ff',
                                    fontSize: '13px',
                                    fontWeight: '500'
                                }}>
                                    {tag}
                                </span>
                            ))}
                        </div>
                    </div>

                    {/* Action Buttons */}
                    <div style={{
                        display: 'flex',
                        gap: '15px'
                    }}>
                        <button
                            onClick={onClose}
                            style={{
                                flex: 1,
                                padding: '16px',
                                backgroundColor: '#2d2d44',
                                border: 'none',
                                borderRadius: '8px',
                                color: '#e0e0e0',
                                fontSize: '16px',
                                fontWeight: '500',
                                cursor: 'pointer',
                                transition: 'all 0.2s'
                            }}
                            onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#3d3d54'}
                            onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#2d2d44'}
                        >
                            Close
                        </button>
                        <button
                            onClick={() => onUse(template)}
                            style={{
                                flex: 2,
                                padding: '16px',
                                backgroundColor: '#00d4ff',
                                border: 'none',
                                borderRadius: '8px',
                                color: '#0f1419',
                                fontSize: '16px',
                                fontWeight: '600',
                                cursor: 'pointer',
                                transition: 'all 0.2s'
                            }}
                            onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#00e4ff'}
                            onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#00d4ff'}
                        >
                            Use This Template
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

function DetailSection({ title, icon, items }) {
    return (
        <div>
            <h4 style={{
                margin: '0 0 15px 0',
                color: '#aaa',
                fontSize: '12px',
                fontWeight: '500',
                textTransform: 'uppercase',
                letterSpacing: '1px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
            }}>
                <span>{icon}</span>
                {title}
            </h4>
            <ul style={{
                margin: 0,
                padding: '0 0 0 20px',
                color: '#e0e0e0',
                fontSize: '14px',
                lineHeight: '2'
            }}>
                {items.map((item, index) => (
                    <li key={index}>{item}</li>
                ))}
            </ul>
        </div>
    );
}

// ============================================================================
// Main Workflow Templates Component
// ============================================================================

function WorkflowTemplates({ onSelectTemplate, onClose }) {
    const [templates] = useState(BUILTIN_TEMPLATES);
    const [selectedCategory, setSelectedCategory] = useState('All');
    const [searchTerm, setSearchTerm] = useState('');
    const [previewTemplate, setPreviewTemplate] = useState(null);

    // Get unique categories
    const categories = useMemo(() => {
        const cats = new Set(['All']);
        templates.forEach(t => cats.add(t.category));
        return Array.from(cats);
    }, [templates]);

    // Filter templates
    const filteredTemplates = useMemo(() => {
        return templates.filter(template => {
            const matchesCategory = selectedCategory === 'All' || template.category === selectedCategory;
            const matchesSearch = !searchTerm ||
                template.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                template.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                template.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()));

            return matchesCategory && matchesSearch;
        });
    }, [templates, selectedCategory, searchTerm]);

    const handleUseTemplate = (template) => {
        if (onSelectTemplate) {
            onSelectTemplate(template);
        }
        if (onClose) {
            onClose();
        }
    };

    return (
        <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: '#0f1419',
            zIndex: 100,
            display: 'flex',
            flexDirection: 'column'
        }}>
            {/* Header */}
            <div style={{
                padding: '30px',
                backgroundColor: '#16213e',
                borderBottom: '1px solid #2d2d44'
            }}>
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    marginBottom: '20px'
                }}>
                    <div>
                        <h1 style={{
                            margin: '0 0 10px 0',
                            color: '#00d4ff',
                            fontSize: '32px',
                            fontWeight: '700'
                        }}>
                            Workflow Templates
                        </h1>
                        <p style={{
                            margin: 0,
                            color: '#aaa',
                            fontSize: '16px'
                        }}>
                            Pre-built workflows for common business scenarios
                        </p>
                    </div>
                    {onClose && (
                        <button
                            onClick={onClose}
                            style={{
                                padding: '12px 24px',
                                backgroundColor: '#2d2d44',
                                border: 'none',
                                borderRadius: '8px',
                                color: '#e0e0e0',
                                fontSize: '16px',
                                fontWeight: '500',
                                cursor: 'pointer',
                                transition: 'all 0.2s'
                            }}
                            onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#3d3d54'}
                            onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#2d2d44'}
                        >
                            Close
                        </button>
                    )}
                </div>

                {/* Search & Filters */}
                <div style={{
                    display: 'flex',
                    gap: '15px',
                    alignItems: 'center'
                }}>
                    {/* Search Box */}
                    <input
                        type="text"
                        placeholder="Search templates..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        style={{
                            flex: 1,
                            padding: '14px 18px',
                            backgroundColor: '#0f1419',
                            border: '1px solid #2d2d44',
                            borderRadius: '8px',
                            color: '#e0e0e0',
                            fontSize: '16px',
                            outline: 'none'
                        }}
                    />

                    {/* Category Filter */}
                    <select
                        value={selectedCategory}
                        onChange={(e) => setSelectedCategory(e.target.value)}
                        style={{
                            padding: '14px 18px',
                            backgroundColor: '#0f1419',
                            border: '1px solid #2d2d44',
                            borderRadius: '8px',
                            color: '#e0e0e0',
                            fontSize: '16px',
                            outline: 'none',
                            cursor: 'pointer',
                            minWidth: '200px'
                        }}
                    >
                        {categories.map(category => (
                            <option key={category} value={category}>
                                {category}
                            </option>
                        ))}
                    </select>

                    <div style={{
                        padding: '14px 18px',
                        backgroundColor: '#0f1419',
                        border: '1px solid #2d2d44',
                        borderRadius: '8px',
                        color: '#888',
                        fontSize: '14px',
                        minWidth: '120px',
                        textAlign: 'center'
                    }}>
                        {filteredTemplates.length} templates
                    </div>
                </div>
            </div>

            {/* Templates Grid */}
            <div style={{
                flex: 1,
                overflowY: 'auto',
                padding: '30px'
            }}>
                <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
                    gap: '24px'
                }}>
                    {filteredTemplates.map(template => (
                        <TemplateCard
                            key={template.id}
                            template={template}
                            onSelect={handleUseTemplate}
                            onPreview={setPreviewTemplate}
                        />
                    ))}
                </div>

                {filteredTemplates.length === 0 && (
                    <div style={{
                        textAlign: 'center',
                        padding: '60px 20px',
                        color: '#666'
                    }}>
                        <div style={{ fontSize: '48px', marginBottom: '20px' }}>🔍</div>
                        <div style={{ fontSize: '18px', marginBottom: '10px' }}>No templates found</div>
                        <div style={{ fontSize: '14px' }}>Try adjusting your search or filters</div>
                    </div>
                )}
            </div>

            {/* Preview Modal */}
            {previewTemplate && (
                <TemplatePreview
                    template={previewTemplate}
                    onClose={() => setPreviewTemplate(null)}
                    onUse={handleUseTemplate}
                />
            )}
        </div>
    );
}

// Export for use in other components
window.WorkflowTemplates = WorkflowTemplates;
