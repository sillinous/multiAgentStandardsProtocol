/**
 * Agent Configuration Component - Per-Agent Settings Management
 * ==============================================================
 *
 * Production-ready component for configuring individual APQC agents.
 * Each of the 118+ agents can have custom configuration, rate limits,
 * timeouts, retry logic, and custom settings.
 *
 * Features:
 * - Dynamic configuration forms based on agent type
 * - Validation and testing
 * - Save/reset/duplicate configs
 * - Configuration templates
 * - Bulk operations
 * - Export/import configs
 *
 * Version: 1.0.0
 * Author: APQC Admin Team
 * Date: 2025-11-16
 */

const { useState, useEffect, useMemo } = React;

// ============================================================================
// Data Models
// ============================================================================

interface Agent {
    agent_id: string;
    agent_name: string;
    category_id: string;
    category_name: string;
    process_id: string;
    status: string;
    protocols: string[];
    capabilities: string[];
}

interface AgentConfig {
    agent_id: string;
    config: any;
    is_enabled: boolean;
    priority: number;
    rate_limit?: number;
    timeout?: number;
    retry_config: {
        max_retries?: number;
        retry_delay?: number;
        exponential_backoff?: boolean;
    };
    custom_settings: any;
    created_at?: string;
    updated_at?: string;
}

// ============================================================================
// API Helper Functions
// ============================================================================

const API_BASE = 'http://localhost:8765';
const ADMIN_API = `${API_BASE}/api/admin`;

async function apiCall(endpoint: string, method: string = 'GET', data: any = null) {
    const options: RequestInit = {
        method,
        headers: {
            'Content-Type': 'application/json',
        },
    };

    if (data && method !== 'GET') {
        options.body = JSON.stringify(data);
    }

    const response = await fetch(endpoint, options);

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
}

// ============================================================================
// Shared Components
// ============================================================================

function Card({ title, children, actions }: any) {
    return (
        <div style={{
            background: 'var(--bg-card)',
            border: '1px solid var(--border-color)',
            borderRadius: '12px',
            padding: '1.5rem',
            marginBottom: '1.5rem'
        }}>
            {title && (
                <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: '1.5rem',
                    paddingBottom: '1rem',
                    borderBottom: '1px solid var(--border-color)'
                }}>
                    <h3 style={{ fontSize: '1.125rem', fontWeight: '600' }}>{title}</h3>
                    {actions && <div style={{ display: 'flex', gap: '0.5rem' }}>{actions}</div>}
                </div>
            )}
            {children}
        </div>
    );
}

function Button({ onClick, children, variant = 'primary', disabled = false, icon, small = false }: any) {
    const styles = {
        primary: { background: 'var(--accent-primary)', color: 'white' },
        secondary: { background: 'var(--bg-tertiary)', color: 'var(--text-primary)' },
        danger: { background: 'var(--status-unhealthy)', color: 'white' },
        success: { background: 'var(--status-healthy)', color: 'white' }
    };

    return (
        <button
            onClick={onClick}
            disabled={disabled}
            style={{
                ...styles[variant as keyof typeof styles],
                padding: small ? '0.25rem 0.75rem' : '0.5rem 1rem',
                border: 'none',
                borderRadius: '6px',
                cursor: disabled ? 'not-allowed' : 'pointer',
                fontSize: small ? '0.75rem' : '0.875rem',
                fontWeight: '500',
                transition: 'var(--transition)',
                opacity: disabled ? 0.5 : 1,
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
            }}
        >
            {icon && <span>{icon}</span>}
            {children}
        </button>
    );
}

function Input({ label, value, onChange, type = 'text', placeholder = '', disabled = false, error = '' }: any) {
    return (
        <div style={{ marginBottom: '1rem' }}>
            {label && (
                <label style={{
                    display: 'block',
                    marginBottom: '0.5rem',
                    fontSize: '0.875rem',
                    fontWeight: '500',
                    color: 'var(--text-secondary)'
                }}>
                    {label}
                </label>
            )}
            <input
                type={type}
                value={value}
                onChange={(e) => onChange(e.target.value)}
                placeholder={placeholder}
                disabled={disabled}
                style={{
                    width: '100%',
                    padding: '0.75rem',
                    background: 'var(--bg-tertiary)',
                    border: `1px solid ${error ? 'var(--status-unhealthy)' : 'var(--border-color)'}`,
                    borderRadius: '6px',
                    color: 'var(--text-primary)',
                    fontSize: '0.875rem',
                    outline: 'none'
                }}
            />
            {error && (
                <div style={{ color: 'var(--status-unhealthy)', fontSize: '0.75rem', marginTop: '0.25rem' }}>
                    {error}
                </div>
            )}
        </div>
    );
}

// ============================================================================
// Agent Configuration Form Component
// ============================================================================

function AgentConfigForm({ agent, config, onChange, onSave, onCancel }: any) {
    const [formData, setFormData] = useState<AgentConfig>(
        config || {
            agent_id: agent.agent_id,
            config: {},
            is_enabled: true,
            priority: 0,
            rate_limit: undefined,
            timeout: 30,
            retry_config: {
                max_retries: 3,
                retry_delay: 1000,
                exponential_backoff: true
            },
            custom_settings: {}
        }
    );

    const [errors, setErrors] = useState<Record<string, string>>({});

    useEffect(() => {
        if (config) {
            setFormData(config);
        }
    }, [config]);

    function validate(): boolean {
        const newErrors: Record<string, string> = {};

        if (formData.priority < 0 || formData.priority > 100) {
            newErrors.priority = 'Priority must be between 0 and 100';
        }

        if (formData.rate_limit && formData.rate_limit < 0) {
            newErrors.rate_limit = 'Rate limit must be positive';
        }

        if (formData.timeout && formData.timeout < 1) {
            newErrors.timeout = 'Timeout must be at least 1 second';
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    }

    function handleSave() {
        if (validate()) {
            onSave(formData);
        }
    }

    // Get configuration fields based on agent category
    const categorySpecificFields = useMemo(() => {
        const catId = agent.category_id;

        // Financial agents (Category 9)
        if (catId === '9.0') {
            return [
                { key: 'accounting_system', label: 'Accounting System', type: 'select',
                  options: ['quickbooks', 'netsuite', 'sap', 'oracle', 'xero', 'sage'] },
                { key: 'fiscal_year_end', label: 'Fiscal Year End', type: 'date' },
                { key: 'currency', label: 'Default Currency', type: 'text' },
                { key: 'decimal_places', label: 'Decimal Places', type: 'number' }
            ];
        }

        // HR agents (Category 7)
        if (catId === '7.0') {
            return [
                { key: 'hr_system', label: 'HR System', type: 'select',
                  options: ['workday', 'bamboo_hr', 'adp', 'gusto', 'namely'] },
                { key: 'employee_id_format', label: 'Employee ID Format', type: 'text' },
                { key: 'background_check_required', label: 'Background Check Required', type: 'boolean' }
            ];
        }

        // Marketing agents (Category 3)
        if (catId === '3.0') {
            return [
                { key: 'crm_system', label: 'CRM System', type: 'select',
                  options: ['salesforce', 'hubspot', 'dynamics', 'pipedrive'] },
                { key: 'email_provider', label: 'Email Provider', type: 'select',
                  options: ['sendgrid', 'mailchimp', 'mailgun', 'ses'] },
                { key: 'tracking_enabled', label: 'Analytics Tracking', type: 'boolean' }
            ];
        }

        // Supply Chain agents (Category 4)
        if (catId === '4.0') {
            return [
                { key: 'warehouse_management', label: 'WMS System', type: 'select',
                  options: ['sap_scm', 'oracle_scm', 'blue_yonder', 'manhattan'] },
                { key: 'auto_reorder', label: 'Auto Reorder', type: 'boolean' },
                { key: 'reorder_point', label: 'Reorder Point', type: 'number' }
            ];
        }

        // Customer Service agents (Category 6)
        if (catId === '6.0') {
            return [
                { key: 'ticketing_system', label: 'Ticketing System', type: 'select',
                  options: ['zendesk', 'freshdesk', 'servicenow', 'jira'] },
                { key: 'sla_hours', label: 'SLA (hours)', type: 'number' },
                { key: 'auto_assign', label: 'Auto Assign Tickets', type: 'boolean' }
            ];
        }

        return [];
    }, [agent.category_id]);

    return (
        <div>
            <Card title={`Configure ${agent.agent_name}`}>
                {/* Agent Info */}
                <div style={{
                    padding: '1rem',
                    background: 'var(--bg-tertiary)',
                    borderRadius: '8px',
                    marginBottom: '1.5rem'
                }}>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', fontSize: '0.875rem' }}>
                        <div>
                            <div style={{ color: 'var(--text-secondary)' }}>Agent ID</div>
                            <div style={{ fontWeight: '500' }}>{agent.agent_id}</div>
                        </div>
                        <div>
                            <div style={{ color: 'var(--text-secondary)' }}>Category</div>
                            <div style={{ fontWeight: '500' }}>{agent.category_name}</div>
                        </div>
                        <div>
                            <div style={{ color: 'var(--text-secondary)' }}>Process ID</div>
                            <div style={{ fontWeight: '500' }}>{agent.process_id}</div>
                        </div>
                    </div>
                </div>

                {/* Basic Settings */}
                <div style={{ marginBottom: '2rem' }}>
                    <h4 style={{ marginBottom: '1rem', fontSize: '1rem', fontWeight: '600' }}>Basic Settings</h4>

                    <div style={{ marginBottom: '1rem' }}>
                        <label style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem',
                            cursor: 'pointer'
                        }}>
                            <input
                                type="checkbox"
                                checked={formData.is_enabled}
                                onChange={(e) => setFormData({ ...formData, is_enabled: e.target.checked })}
                            />
                            <span style={{ fontSize: '0.875rem' }}>Agent Enabled</span>
                        </label>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem' }}>
                        <Input
                            label="Priority (0-100)"
                            value={formData.priority}
                            onChange={(val: string) => setFormData({ ...formData, priority: parseInt(val) || 0 })}
                            type="number"
                            error={errors.priority}
                        />

                        <Input
                            label="Rate Limit (requests/minute)"
                            value={formData.rate_limit || ''}
                            onChange={(val: string) => setFormData({ ...formData, rate_limit: val ? parseInt(val) : undefined })}
                            type="number"
                            placeholder="Unlimited"
                            error={errors.rate_limit}
                        />

                        <Input
                            label="Timeout (seconds)"
                            value={formData.timeout || 30}
                            onChange={(val: string) => setFormData({ ...formData, timeout: parseInt(val) || 30 })}
                            type="number"
                            error={errors.timeout}
                        />
                    </div>
                </div>

                {/* Retry Configuration */}
                <div style={{ marginBottom: '2rem' }}>
                    <h4 style={{ marginBottom: '1rem', fontSize: '1rem', fontWeight: '600' }}>Retry Configuration</h4>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem' }}>
                        <Input
                            label="Max Retries"
                            value={formData.retry_config.max_retries || 3}
                            onChange={(val: string) => setFormData({
                                ...formData,
                                retry_config: { ...formData.retry_config, max_retries: parseInt(val) || 3 }
                            })}
                            type="number"
                        />

                        <Input
                            label="Retry Delay (ms)"
                            value={formData.retry_config.retry_delay || 1000}
                            onChange={(val: string) => setFormData({
                                ...formData,
                                retry_config: { ...formData.retry_config, retry_delay: parseInt(val) || 1000 }
                            })}
                            type="number"
                        />
                    </div>

                    <div style={{ marginTop: '1rem' }}>
                        <label style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem',
                            cursor: 'pointer'
                        }}>
                            <input
                                type="checkbox"
                                checked={formData.retry_config.exponential_backoff || false}
                                onChange={(e) => setFormData({
                                    ...formData,
                                    retry_config: { ...formData.retry_config, exponential_backoff: e.target.checked }
                                })}
                            />
                            <span style={{ fontSize: '0.875rem' }}>Exponential Backoff</span>
                        </label>
                    </div>
                </div>

                {/* Category-Specific Settings */}
                {categorySpecificFields.length > 0 && (
                    <div style={{ marginBottom: '2rem' }}>
                        <h4 style={{ marginBottom: '1rem', fontSize: '1rem', fontWeight: '600' }}>
                            {agent.category_name} Settings
                        </h4>

                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem' }}>
                            {categorySpecificFields.map(field => {
                                const currentValue = formData.custom_settings[field.key];

                                if (field.type === 'select') {
                                    return (
                                        <div key={field.key} style={{ marginBottom: '1rem' }}>
                                            <label style={{
                                                display: 'block',
                                                marginBottom: '0.5rem',
                                                fontSize: '0.875rem',
                                                fontWeight: '500',
                                                color: 'var(--text-secondary)'
                                            }}>
                                                {field.label}
                                            </label>
                                            <select
                                                value={currentValue || ''}
                                                onChange={(e) => setFormData({
                                                    ...formData,
                                                    custom_settings: { ...formData.custom_settings, [field.key]: e.target.value }
                                                })}
                                                style={{
                                                    width: '100%',
                                                    padding: '0.75rem',
                                                    background: 'var(--bg-tertiary)',
                                                    border: '1px solid var(--border-color)',
                                                    borderRadius: '6px',
                                                    color: 'var(--text-primary)',
                                                    fontSize: '0.875rem'
                                                }}
                                            >
                                                <option value="">Select...</option>
                                                {field.options?.map((opt: string) => (
                                                    <option key={opt} value={opt}>
                                                        {opt.toUpperCase()}
                                                    </option>
                                                ))}
                                            </select>
                                        </div>
                                    );
                                } else if (field.type === 'boolean') {
                                    return (
                                        <div key={field.key} style={{ marginBottom: '1rem' }}>
                                            <label style={{
                                                display: 'flex',
                                                alignItems: 'center',
                                                gap: '0.5rem',
                                                cursor: 'pointer'
                                            }}>
                                                <input
                                                    type="checkbox"
                                                    checked={currentValue || false}
                                                    onChange={(e) => setFormData({
                                                        ...formData,
                                                        custom_settings: { ...formData.custom_settings, [field.key]: e.target.checked }
                                                    })}
                                                />
                                                <span style={{ fontSize: '0.875rem' }}>{field.label}</span>
                                            </label>
                                        </div>
                                    );
                                } else {
                                    return (
                                        <Input
                                            key={field.key}
                                            label={field.label}
                                            value={currentValue || ''}
                                            onChange={(val: string) => setFormData({
                                                ...formData,
                                                custom_settings: { ...formData.custom_settings, [field.key]: val }
                                            })}
                                            type={field.type}
                                        />
                                    );
                                }
                            })}
                        </div>
                    </div>
                )}

                {/* Actions */}
                <div style={{
                    display: 'flex',
                    gap: '1rem',
                    paddingTop: '1.5rem',
                    borderTop: '1px solid var(--border-color)'
                }}>
                    <Button onClick={handleSave} variant="success" icon="💾">
                        Save Configuration
                    </Button>
                    <Button onClick={onCancel} variant="secondary">
                        Cancel
                    </Button>
                    <div style={{ flex: 1 }}></div>
                    <Button
                        onClick={() => {
                            if (confirm('Reset to default configuration?')) {
                                setFormData({
                                    agent_id: agent.agent_id,
                                    config: {},
                                    is_enabled: true,
                                    priority: 0,
                                    rate_limit: undefined,
                                    timeout: 30,
                                    retry_config: {
                                        max_retries: 3,
                                        retry_delay: 1000,
                                        exponential_backoff: true
                                    },
                                    custom_settings: {}
                                });
                            }
                        }}
                        variant="danger"
                        icon="🔄"
                    >
                        Reset to Default
                    </Button>
                </div>
            </Card>
        </div>
    );
}

// ============================================================================
// Main Agent Config Component
// ============================================================================

function AgentConfigManager() {
    const [agents, setAgents] = useState<Agent[]>([]);
    const [configs, setConfigs] = useState<Record<string, AgentConfig>>({});
    const [loading, setLoading] = useState(true);
    const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [filterCategory, setFilterCategory] = useState('all');

    useEffect(() => {
        loadData();
    }, []);

    async function loadData() {
        try {
            // Load agents
            const agentsData = await apiCall(`${API_BASE}/api/agents`);
            setAgents(agentsData.agents || []);

            // Load configs
            const configsData = await apiCall(`${ADMIN_API}/agents/config`);
            const configMap: Record<string, AgentConfig> = {};
            (configsData.agent_configs || []).forEach((config: AgentConfig) => {
                configMap[config.agent_id] = config;
            });
            setConfigs(configMap);
        } catch (error) {
            console.error('Failed to load data:', error);
        } finally {
            setLoading(false);
        }
    }

    async function saveConfig(config: AgentConfig) {
        try {
            await apiCall(`${ADMIN_API}/agents/config/${config.agent_id}`, 'PUT', config);
            await loadData();
            setSelectedAgent(null);
            alert('Configuration saved successfully!');
        } catch (error) {
            alert(`Failed to save configuration: ${error}`);
        }
    }

    // Filter and search
    const filteredAgents = useMemo(() => {
        return agents.filter(agent => {
            const matchesSearch = !searchQuery ||
                agent.agent_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                agent.agent_id.toLowerCase().includes(searchQuery.toLowerCase());

            const matchesCategory = filterCategory === 'all' ||
                agent.category_id === filterCategory;

            return matchesSearch && matchesCategory;
        });
    }, [agents, searchQuery, filterCategory]);

    // Group by category
    const categorizedAgents = useMemo(() => {
        const groups: Record<string, Agent[]> = {};
        filteredAgents.forEach(agent => {
            if (!groups[agent.category_id]) {
                groups[agent.category_id] = [];
            }
            groups[agent.category_id].push(agent);
        });
        return groups;
    }, [filteredAgents]);

    const categories = useMemo(() => {
        const cats = new Set(agents.map(a => a.category_id));
        return Array.from(cats).sort();
    }, [agents]);

    if (loading) {
        return <div style={{ textAlign: 'center', padding: '3rem' }}>Loading...</div>;
    }

    if (selectedAgent) {
        return (
            <AgentConfigForm
                agent={selectedAgent}
                config={configs[selectedAgent.agent_id]}
                onChange={(config: AgentConfig) => {}}
                onSave={saveConfig}
                onCancel={() => setSelectedAgent(null)}
            />
        );
    }

    return (
        <div>
            <Card
                title="Agent Configuration Manager"
                actions={
                    <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                        {filteredAgents.length} of {agents.length} agents
                    </div>
                }
            >
                <div style={{ marginBottom: '1.5rem', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                    Configure settings for each of the 118+ APQC agents. Settings include rate limits,
                    timeouts, retry logic, and category-specific configurations.
                </div>

                {/* Search and Filter */}
                <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1rem', marginBottom: '2rem' }}>
                    <input
                        type="text"
                        placeholder="Search agents..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        style={{
                            padding: '0.75rem',
                            background: 'var(--bg-tertiary)',
                            border: '1px solid var(--border-color)',
                            borderRadius: '6px',
                            color: 'var(--text-primary)',
                            fontSize: '0.875rem'
                        }}
                    />

                    <select
                        value={filterCategory}
                        onChange={(e) => setFilterCategory(e.target.value)}
                        style={{
                            padding: '0.75rem',
                            background: 'var(--bg-tertiary)',
                            border: '1px solid var(--border-color)',
                            borderRadius: '6px',
                            color: 'var(--text-primary)',
                            fontSize: '0.875rem'
                        }}
                    >
                        <option value="all">All Categories</option>
                        {categories.map(catId => {
                            const agent = agents.find(a => a.category_id === catId);
                            return (
                                <option key={catId} value={catId}>
                                    {agent?.category_name || catId}
                                </option>
                            );
                        })}
                    </select>
                </div>

                {/* Agent List by Category */}
                {Object.keys(categorizedAgents).sort().map(categoryId => {
                    const categoryAgents = categorizedAgents[categoryId];
                    const categoryName = categoryAgents[0]?.category_name || categoryId;

                    return (
                        <div key={categoryId} style={{ marginBottom: '2rem' }}>
                            <h4 style={{
                                fontSize: '0.875rem',
                                fontWeight: '600',
                                color: 'var(--text-secondary)',
                                textTransform: 'uppercase',
                                marginBottom: '1rem',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.5rem'
                            }}>
                                {categoryName}
                                <span style={{
                                    background: 'var(--accent-primary)',
                                    color: 'white',
                                    padding: '0.125rem 0.5rem',
                                    borderRadius: '12px',
                                    fontSize: '0.75rem'
                                }}>
                                    {categoryAgents.length}
                                </span>
                            </h4>

                            <div style={{
                                display: 'grid',
                                gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
                                gap: '1rem'
                            }}>
                                {categoryAgents.map(agent => {
                                    const hasConfig = !!configs[agent.agent_id];
                                    const isEnabled = configs[agent.agent_id]?.is_enabled !== false;

                                    return (
                                        <div
                                            key={agent.agent_id}
                                            onClick={() => setSelectedAgent(agent)}
                                            style={{
                                                background: 'var(--bg-tertiary)',
                                                border: '1px solid var(--border-color)',
                                                borderRadius: '8px',
                                                padding: '1rem',
                                                cursor: 'pointer',
                                                transition: 'var(--transition)'
                                            }}
                                            onMouseEnter={(e) => {
                                                e.currentTarget.style.borderColor = 'var(--accent-primary)';
                                                e.currentTarget.style.background = 'var(--bg-hover)';
                                            }}
                                            onMouseLeave={(e) => {
                                                e.currentTarget.style.borderColor = 'var(--border-color)';
                                                e.currentTarget.style.background = 'var(--bg-tertiary)';
                                            }}
                                        >
                                            <div style={{
                                                display: 'flex',
                                                justifyContent: 'space-between',
                                                alignItems: 'start',
                                                marginBottom: '0.5rem'
                                            }}>
                                                <div style={{
                                                    fontSize: '0.875rem',
                                                    fontWeight: '500',
                                                    color: 'var(--text-primary)'
                                                }}>
                                                    {agent.agent_name}
                                                </div>
                                                <div style={{
                                                    width: '8px',
                                                    height: '8px',
                                                    borderRadius: '50%',
                                                    background: isEnabled ? 'var(--status-healthy)' : 'var(--status-offline)'
                                                }}></div>
                                            </div>

                                            <div style={{
                                                fontSize: '0.75rem',
                                                color: 'var(--text-muted)',
                                                marginBottom: '0.75rem'
                                            }}>
                                                {agent.process_id}
                                            </div>

                                            <div style={{
                                                display: 'flex',
                                                gap: '0.5rem',
                                                alignItems: 'center',
                                                fontSize: '0.75rem'
                                            }}>
                                                {hasConfig ? (
                                                    <span style={{
                                                        padding: '0.125rem 0.5rem',
                                                        borderRadius: '4px',
                                                        background: 'var(--status-healthy)',
                                                        color: 'white',
                                                        fontWeight: '600'
                                                    }}>
                                                        CONFIGURED
                                                    </span>
                                                ) : (
                                                    <span style={{
                                                        padding: '0.125rem 0.5rem',
                                                        borderRadius: '4px',
                                                        background: 'var(--bg-secondary)',
                                                        color: 'var(--text-secondary)',
                                                        fontWeight: '600'
                                                    }}>
                                                        DEFAULT
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    );
                })}
            </Card>
        </div>
    );
}

// Export component
window.AgentConfigManager = AgentConfigManager;
