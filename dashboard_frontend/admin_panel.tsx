/**
 * Admin Panel Component - Comprehensive Configuration Management UI
 * =================================================================
 *
 * Production-ready admin panel for managing all APQC dashboard configuration.
 * Everything is configurable through this UI - no direct file editing needed.
 *
 * Features:
 * - Environment Variables Management
 * - API Keys Management (encrypted)
 * - User Management (role-based access)
 * - Per-Agent Configuration
 * - System Settings
 * - Integration Management
 * - Audit Log Viewer
 *
 * Security:
 * - Role-based access control
 * - Secure credential handling
 * - Audit logging
 *
 * Version: 1.0.0
 * Author: APQC Admin Team
 * Date: 2025-11-16
 */

const { useState, useEffect, useMemo } = React;

// ============================================================================
// Data Models
// ============================================================================

interface EnvironmentVariable {
    key: string;
    value: string;
    description?: string;
    is_secret: boolean;
    category: string;
}

interface APIKey {
    key_id: string;
    name: string;
    service: string;
    key_value: string;
    is_active: boolean;
    created_at: string;
    last_used?: string;
    expires_at?: string;
    metadata: any;
}

interface User {
    user_id: string;
    username: string;
    email: string;
    role: 'admin' | 'business_user' | 'viewer';
    is_active: boolean;
    created_at: string;
    last_login?: string;
}

interface Integration {
    integration_id: string;
    name: string;
    type: string;
    is_enabled: boolean;
    credentials: Record<string, string>;
    settings: any;
    last_sync?: string;
    status: string;
    error_message?: string;
}

interface AgentConfig {
    agent_id: string;
    config: any;
    is_enabled: boolean;
    priority: number;
    rate_limit?: number;
    timeout?: number;
    retry_config: any;
    custom_settings: any;
}

interface SystemSettings {
    log_level: string;
    max_retries: number;
    timeout_seconds: number;
    enable_metrics: boolean;
    enable_audit_log: boolean;
    data_retention_days: number;
    backup_enabled: boolean;
    backup_interval_hours: number;
}

// ============================================================================
// API Helper Functions
// ============================================================================

const API_BASE = 'http://localhost:8765/api/admin';

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

    const response = await fetch(`${API_BASE}${endpoint}`, options);

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
}

// ============================================================================
// Shared Components
// ============================================================================

function TabButton({ active, onClick, children, icon }: any) {
    return (
        <button
            onClick={onClick}
            style={{
                padding: '0.75rem 1.5rem',
                background: active ? 'var(--accent-primary)' : 'transparent',
                color: active ? 'white' : 'var(--text-primary)',
                border: '1px solid var(--border-color)',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '0.875rem',
                fontWeight: '500',
                transition: 'var(--transition)',
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

function Button({ onClick, children, variant = 'primary', disabled = false, icon }: any) {
    const styles = {
        primary: {
            background: 'var(--accent-primary)',
            color: 'white',
        },
        secondary: {
            background: 'var(--bg-tertiary)',
            color: 'var(--text-primary)',
        },
        danger: {
            background: 'var(--status-unhealthy)',
            color: 'white',
        },
        success: {
            background: 'var(--status-healthy)',
            color: 'white',
        }
    };

    return (
        <button
            onClick={onClick}
            disabled={disabled}
            style={{
                ...styles[variant as keyof typeof styles],
                padding: '0.5rem 1rem',
                border: 'none',
                borderRadius: '6px',
                cursor: disabled ? 'not-allowed' : 'pointer',
                fontSize: '0.875rem',
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

function Input({ label, value, onChange, type = 'text', placeholder = '', disabled = false }: any) {
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
                    border: '1px solid var(--border-color)',
                    borderRadius: '6px',
                    color: 'var(--text-primary)',
                    fontSize: '0.875rem',
                    outline: 'none'
                }}
            />
        </div>
    );
}

function Select({ label, value, onChange, options, disabled = false }: any) {
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
            <select
                value={value}
                onChange={(e) => onChange(e.target.value)}
                disabled={disabled}
                style={{
                    width: '100%',
                    padding: '0.75rem',
                    background: 'var(--bg-tertiary)',
                    border: '1px solid var(--border-color)',
                    borderRadius: '6px',
                    color: 'var(--text-primary)',
                    fontSize: '0.875rem',
                    outline: 'none',
                    cursor: 'pointer'
                }}
            >
                {options.map((opt: any) => (
                    <option key={opt.value} value={opt.value}>
                        {opt.label}
                    </option>
                ))}
            </select>
        </div>
    );
}

function Table({ columns, data, onRowClick }: any) {
    return (
        <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                    <tr style={{ borderBottom: '2px solid var(--border-color)' }}>
                        {columns.map((col: any) => (
                            <th key={col.key} style={{
                                padding: '0.75rem',
                                textAlign: 'left',
                                fontSize: '0.75rem',
                                fontWeight: '600',
                                color: 'var(--text-secondary)',
                                textTransform: 'uppercase'
                            }}>
                                {col.label}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {data.map((row: any, idx: number) => (
                        <tr
                            key={idx}
                            onClick={() => onRowClick && onRowClick(row)}
                            style={{
                                borderBottom: '1px solid var(--border-color)',
                                cursor: onRowClick ? 'pointer' : 'default',
                                transition: 'var(--transition)'
                            }}
                            onMouseEnter={(e) => {
                                if (onRowClick) e.currentTarget.style.background = 'var(--bg-hover)';
                            }}
                            onMouseLeave={(e) => {
                                if (onRowClick) e.currentTarget.style.background = 'transparent';
                            }}
                        >
                            {columns.map((col: any) => (
                                <td key={col.key} style={{
                                    padding: '0.75rem',
                                    fontSize: '0.875rem',
                                    color: 'var(--text-primary)'
                                }}>
                                    {col.render ? col.render(row[col.key], row) : row[col.key]}
                                </td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
            {data.length === 0 && (
                <div style={{
                    textAlign: 'center',
                    padding: '3rem',
                    color: 'var(--text-muted)'
                }}>
                    No data available
                </div>
            )}
        </div>
    );
}

// ============================================================================
// Environment Variables Tab
// ============================================================================

function EnvironmentVariablesTab() {
    const [variables, setVariables] = useState<EnvironmentVariable[]>([]);
    const [loading, setLoading] = useState(true);
    const [editingVar, setEditingVar] = useState<EnvironmentVariable | null>(null);
    const [showAddDialog, setShowAddDialog] = useState(false);

    useEffect(() => {
        loadVariables();
    }, []);

    async function loadVariables() {
        try {
            const data = await apiCall('/env');
            setVariables(data.variables);
        } catch (error) {
            console.error('Failed to load variables:', error);
        } finally {
            setLoading(false);
        }
    }

    async function saveVariable(variable: EnvironmentVariable) {
        try {
            await apiCall('/env', 'POST', variable);
            await loadVariables();
            setEditingVar(null);
            setShowAddDialog(false);
        } catch (error) {
            alert(`Failed to save variable: ${error}`);
        }
    }

    async function deleteVariable(key: string) {
        if (!confirm(`Delete variable ${key}?`)) return;

        try {
            await apiCall(`/env/${key}`, 'DELETE');
            await loadVariables();
        } catch (error) {
            alert(`Failed to delete variable: ${error}`);
        }
    }

    const categories = useMemo(() => {
        const cats = new Set(variables.map(v => v.category));
        return Array.from(cats);
    }, [variables]);

    if (loading) {
        return <div style={{ textAlign: 'center', padding: '3rem' }}>Loading...</div>;
    }

    return (
        <div>
            <Card
                title="Environment Variables"
                actions={
                    <Button onClick={() => setShowAddDialog(true)} icon="+">
                        Add Variable
                    </Button>
                }
            >
                <div style={{ marginBottom: '1rem', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                    Manage environment variables for the APQC dashboard. Changes are written to .env file.
                </div>

                {categories.map(category => {
                    const catVars = variables.filter(v => v.category === category);
                    return (
                        <div key={category} style={{ marginBottom: '2rem' }}>
                            <h4 style={{
                                fontSize: '0.875rem',
                                fontWeight: '600',
                                color: 'var(--text-secondary)',
                                textTransform: 'uppercase',
                                marginBottom: '1rem'
                            }}>
                                {category}
                            </h4>
                            <Table
                                columns={[
                                    { key: 'key', label: 'Key' },
                                    {
                                        key: 'value',
                                        label: 'Value',
                                        render: (val: string, row: EnvironmentVariable) =>
                                            row.is_secret ? '********' : val
                                    },
                                    { key: 'description', label: 'Description' },
                                    {
                                        key: 'actions',
                                        label: 'Actions',
                                        render: (_: any, row: EnvironmentVariable) => (
                                            <div style={{ display: 'flex', gap: '0.5rem' }}>
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        setEditingVar(row);
                                                    }}
                                                    style={{
                                                        padding: '0.25rem 0.5rem',
                                                        background: 'var(--accent-primary)',
                                                        color: 'white',
                                                        border: 'none',
                                                        borderRadius: '4px',
                                                        cursor: 'pointer',
                                                        fontSize: '0.75rem'
                                                    }}
                                                >
                                                    Edit
                                                </button>
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        deleteVariable(row.key);
                                                    }}
                                                    style={{
                                                        padding: '0.25rem 0.5rem',
                                                        background: 'var(--status-unhealthy)',
                                                        color: 'white',
                                                        border: 'none',
                                                        borderRadius: '4px',
                                                        cursor: 'pointer',
                                                        fontSize: '0.75rem'
                                                    }}
                                                >
                                                    Delete
                                                </button>
                                            </div>
                                        )
                                    }
                                ]}
                                data={catVars}
                            />
                        </div>
                    );
                })}
            </Card>

            {/* Add/Edit Dialog */}
            {(showAddDialog || editingVar) && (
                <EnvironmentVariableDialog
                    variable={editingVar}
                    onSave={saveVariable}
                    onCancel={() => {
                        setShowAddDialog(false);
                        setEditingVar(null);
                    }}
                />
            )}
        </div>
    );
}

function EnvironmentVariableDialog({ variable, onSave, onCancel }: any) {
    const [formData, setFormData] = useState<EnvironmentVariable>(
        variable || {
            key: '',
            value: '',
            description: '',
            is_secret: false,
            category: 'general'
        }
    );

    return (
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
            zIndex: 1000
        }} onClick={onCancel}>
            <div
                style={{
                    background: 'var(--bg-card)',
                    borderRadius: '12px',
                    padding: '2rem',
                    width: '100%',
                    maxWidth: '500px',
                    border: '1px solid var(--border-color)'
                }}
                onClick={(e) => e.stopPropagation()}
            >
                <h3 style={{ marginBottom: '1.5rem' }}>
                    {variable ? 'Edit Variable' : 'Add Variable'}
                </h3>

                <Input
                    label="Key"
                    value={formData.key}
                    onChange={(val: string) => setFormData({ ...formData, key: val })}
                    placeholder="LOG_LEVEL"
                    disabled={!!variable}
                />

                <Input
                    label="Value"
                    value={formData.value}
                    onChange={(val: string) => setFormData({ ...formData, value: val })}
                    type={formData.is_secret ? 'password' : 'text'}
                    placeholder="INFO"
                />

                <Input
                    label="Description"
                    value={formData.description || ''}
                    onChange={(val: string) => setFormData({ ...formData, description: val })}
                    placeholder="Logging level for the application"
                />

                <Select
                    label="Category"
                    value={formData.category}
                    onChange={(val: string) => setFormData({ ...formData, category: val })}
                    options={[
                        { value: 'general', label: 'General' },
                        { value: 'database', label: 'Database' },
                        { value: 'api', label: 'API' },
                        { value: 'monitoring', label: 'Monitoring' },
                        { value: 'security', label: 'Security' }
                    ]}
                />

                <div style={{ marginBottom: '1rem' }}>
                    <label style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                        cursor: 'pointer'
                    }}>
                        <input
                            type="checkbox"
                            checked={formData.is_secret}
                            onChange={(e) => setFormData({ ...formData, is_secret: e.target.checked })}
                        />
                        <span style={{ fontSize: '0.875rem' }}>Secret (encrypted)</span>
                    </label>
                </div>

                <div style={{ display: 'flex', gap: '1rem', marginTop: '2rem' }}>
                    <Button onClick={() => onSave(formData)} variant="primary">
                        Save
                    </Button>
                    <Button onClick={onCancel} variant="secondary">
                        Cancel
                    </Button>
                </div>
            </div>
        </div>
    );
}

// ============================================================================
// API Keys Tab
// ============================================================================

function APIKeysTab() {
    const [apiKeys, setApiKeys] = useState<APIKey[]>([]);
    const [loading, setLoading] = useState(true);
    const [showAddDialog, setShowAddDialog] = useState(false);

    useEffect(() => {
        loadAPIKeys();
    }, []);

    async function loadAPIKeys() {
        try {
            const data = await apiCall('/api-keys');
            setApiKeys(data.api_keys);
        } catch (error) {
            console.error('Failed to load API keys:', error);
        } finally {
            setLoading(false);
        }
    }

    async function createAPIKey(keyData: any) {
        try {
            await apiCall('/api-keys', 'POST', keyData);
            await loadAPIKeys();
            setShowAddDialog(false);
        } catch (error) {
            alert(`Failed to create API key: ${error}`);
        }
    }

    async function deleteAPIKey(keyId: string) {
        if (!confirm('Delete this API key?')) return;

        try {
            await apiCall(`/api-keys/${keyId}`, 'DELETE');
            await loadAPIKeys();
        } catch (error) {
            alert(`Failed to delete API key: ${error}`);
        }
    }

    if (loading) {
        return <div style={{ textAlign: 'center', padding: '3rem' }}>Loading...</div>;
    }

    return (
        <div>
            <Card
                title="API Keys"
                actions={
                    <Button onClick={() => setShowAddDialog(true)} icon="+">
                        Add API Key
                    </Button>
                }
            >
                <div style={{ marginBottom: '1rem', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                    Manage API keys for external services. Keys are encrypted at rest.
                </div>

                <Table
                    columns={[
                        { key: 'name', label: 'Name' },
                        { key: 'service', label: 'Service' },
                        { key: 'key_value', label: 'Key (masked)' },
                        {
                            key: 'is_active',
                            label: 'Status',
                            render: (val: boolean) => (
                                <span style={{
                                    padding: '0.25rem 0.5rem',
                                    borderRadius: '4px',
                                    fontSize: '0.75rem',
                                    fontWeight: '600',
                                    background: val ? 'var(--status-healthy)' : 'var(--status-offline)',
                                    color: 'white'
                                }}>
                                    {val ? 'Active' : 'Inactive'}
                                </span>
                            )
                        },
                        {
                            key: 'created_at',
                            label: 'Created',
                            render: (val: string) => new Date(val).toLocaleDateString()
                        },
                        {
                            key: 'actions',
                            label: 'Actions',
                            render: (_: any, row: APIKey) => (
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        deleteAPIKey(row.key_id);
                                    }}
                                    style={{
                                        padding: '0.25rem 0.5rem',
                                        background: 'var(--status-unhealthy)',
                                        color: 'white',
                                        border: 'none',
                                        borderRadius: '4px',
                                        cursor: 'pointer',
                                        fontSize: '0.75rem'
                                    }}
                                >
                                    Delete
                                </button>
                            )
                        }
                    ]}
                    data={apiKeys}
                />
            </Card>

            {showAddDialog && (
                <APIKeyDialog
                    onSave={createAPIKey}
                    onCancel={() => setShowAddDialog(false)}
                />
            )}
        </div>
    );
}

function APIKeyDialog({ onSave, onCancel }: any) {
    const [formData, setFormData] = useState({
        name: '',
        service: 'openai',
        key_value: '',
        expires_days: null as number | null
    });

    const services = [
        'openai', 'anthropic', 'aws', 'gcp', 'azure',
        'salesforce', 'hubspot', 'sap', 'oracle', 'netsuite',
        'quickbooks', 'xero', 'workday', 'stripe', 'shopify'
    ];

    return (
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
            zIndex: 1000
        }} onClick={onCancel}>
            <div
                style={{
                    background: 'var(--bg-card)',
                    borderRadius: '12px',
                    padding: '2rem',
                    width: '100%',
                    maxWidth: '500px',
                    border: '1px solid var(--border-color)'
                }}
                onClick={(e) => e.stopPropagation()}
            >
                <h3 style={{ marginBottom: '1.5rem' }}>Add API Key</h3>

                <Input
                    label="Name"
                    value={formData.name}
                    onChange={(val: string) => setFormData({ ...formData, name: val })}
                    placeholder="Production OpenAI Key"
                />

                <Select
                    label="Service"
                    value={formData.service}
                    onChange={(val: string) => setFormData({ ...formData, service: val })}
                    options={services.map(s => ({ value: s, label: s.toUpperCase() }))}
                />

                <Input
                    label="API Key"
                    value={formData.key_value}
                    onChange={(val: string) => setFormData({ ...formData, key_value: val })}
                    type="password"
                    placeholder="sk-..."
                />

                <Input
                    label="Expires in (days, optional)"
                    value={formData.expires_days || ''}
                    onChange={(val: string) => setFormData({ ...formData, expires_days: val ? parseInt(val) : null })}
                    type="number"
                    placeholder="365"
                />

                <div style={{ display: 'flex', gap: '1rem', marginTop: '2rem' }}>
                    <Button onClick={() => onSave(formData)} variant="primary">
                        Save
                    </Button>
                    <Button onClick={onCancel} variant="secondary">
                        Cancel
                    </Button>
                </div>
            </div>
        </div>
    );
}

// ============================================================================
// Users Tab
// ============================================================================

function UsersTab() {
    const [users, setUsers] = useState<User[]>([]);
    const [loading, setLoading] = useState(true);
    const [showAddDialog, setShowAddDialog] = useState(false);

    useEffect(() => {
        loadUsers();
    }, []);

    async function loadUsers() {
        try {
            const data = await apiCall('/users');
            setUsers(data.users);
        } catch (error) {
            console.error('Failed to load users:', error);
        } finally {
            setLoading(false);
        }
    }

    async function createUser(userData: any) {
        try {
            await apiCall('/users', 'POST', userData);
            await loadUsers();
            setShowAddDialog(false);
        } catch (error) {
            alert(`Failed to create user: ${error}`);
        }
    }

    async function deleteUser(userId: string) {
        if (!confirm('Delete this user?')) return;

        try {
            await apiCall(`/users/${userId}`, 'DELETE');
            await loadUsers();
        } catch (error) {
            alert(`Failed to delete user: ${error}`);
        }
    }

    if (loading) {
        return <div style={{ textAlign: 'center', padding: '3rem' }}>Loading...</div>;
    }

    return (
        <div>
            <Card
                title="User Management"
                actions={
                    <Button onClick={() => setShowAddDialog(true)} icon="+">
                        Add User
                    </Button>
                }
            >
                <div style={{ marginBottom: '1rem', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                    Manage user accounts and permissions. Roles: Admin (full access), Business User (workflow config), Viewer (read-only).
                </div>

                <Table
                    columns={[
                        { key: 'username', label: 'Username' },
                        { key: 'email', label: 'Email' },
                        {
                            key: 'role',
                            label: 'Role',
                            render: (val: string) => (
                                <span style={{
                                    padding: '0.25rem 0.5rem',
                                    borderRadius: '4px',
                                    fontSize: '0.75rem',
                                    fontWeight: '600',
                                    background: val === 'admin' ? 'var(--accent-primary)' :
                                               val === 'business_user' ? 'var(--accent-secondary)' :
                                               'var(--bg-tertiary)',
                                    color: 'white'
                                }}>
                                    {val.replace('_', ' ').toUpperCase()}
                                </span>
                            )
                        },
                        {
                            key: 'is_active',
                            label: 'Status',
                            render: (val: boolean) => (
                                <span style={{
                                    padding: '0.25rem 0.5rem',
                                    borderRadius: '4px',
                                    fontSize: '0.75rem',
                                    fontWeight: '600',
                                    background: val ? 'var(--status-healthy)' : 'var(--status-offline)',
                                    color: 'white'
                                }}>
                                    {val ? 'Active' : 'Inactive'}
                                </span>
                            )
                        },
                        {
                            key: 'created_at',
                            label: 'Created',
                            render: (val: string) => new Date(val).toLocaleDateString()
                        },
                        {
                            key: 'actions',
                            label: 'Actions',
                            render: (_: any, row: User) => (
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        deleteUser(row.user_id);
                                    }}
                                    style={{
                                        padding: '0.25rem 0.5rem',
                                        background: 'var(--status-unhealthy)',
                                        color: 'white',
                                        border: 'none',
                                        borderRadius: '4px',
                                        cursor: 'pointer',
                                        fontSize: '0.75rem'
                                    }}
                                >
                                    Delete
                                </button>
                            )
                        }
                    ]}
                    data={users}
                />
            </Card>

            {showAddDialog && (
                <UserDialog
                    onSave={createUser}
                    onCancel={() => setShowAddDialog(false)}
                />
            )}
        </div>
    );
}

function UserDialog({ onSave, onCancel }: any) {
    const [formData, setFormData] = useState({
        username: '',
        email: '',
        password: '',
        role: 'viewer'
    });

    return (
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
            zIndex: 1000
        }} onClick={onCancel}>
            <div
                style={{
                    background: 'var(--bg-card)',
                    borderRadius: '12px',
                    padding: '2rem',
                    width: '100%',
                    maxWidth: '500px',
                    border: '1px solid var(--border-color)'
                }}
                onClick={(e) => e.stopPropagation()}
            >
                <h3 style={{ marginBottom: '1.5rem' }}>Add User</h3>

                <Input
                    label="Username"
                    value={formData.username}
                    onChange={(val: string) => setFormData({ ...formData, username: val })}
                    placeholder="jsmith"
                />

                <Input
                    label="Email"
                    value={formData.email}
                    onChange={(val: string) => setFormData({ ...formData, email: val })}
                    type="email"
                    placeholder="jsmith@company.com"
                />

                <Input
                    label="Password"
                    value={formData.password}
                    onChange={(val: string) => setFormData({ ...formData, password: val })}
                    type="password"
                    placeholder="Min 8 chars, 1 uppercase, 1 number"
                />

                <Select
                    label="Role"
                    value={formData.role}
                    onChange={(val: string) => setFormData({ ...formData, role: val })}
                    options={[
                        { value: 'viewer', label: 'Viewer (Read-only)' },
                        { value: 'business_user', label: 'Business User (Workflow Config)' },
                        { value: 'admin', label: 'Admin (Full Access)' }
                    ]}
                />

                <div style={{ display: 'flex', gap: '1rem', marginTop: '2rem' }}>
                    <Button onClick={() => onSave(formData)} variant="primary">
                        Create User
                    </Button>
                    <Button onClick={onCancel} variant="secondary">
                        Cancel
                    </Button>
                </div>
            </div>
        </div>
    );
}

// ============================================================================
// System Settings Tab
// ============================================================================

function SystemSettingsTab() {
    const [settings, setSettings] = useState<SystemSettings | null>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        loadSettings();
    }, []);

    async function loadSettings() {
        try {
            const data = await apiCall('/system/settings');
            setSettings(data);
        } catch (error) {
            console.error('Failed to load settings:', error);
        } finally {
            setLoading(false);
        }
    }

    async function saveSettings() {
        if (!settings) return;

        setSaving(true);
        try {
            await apiCall('/system/settings', 'PUT', settings);
            alert('Settings saved successfully!');
        } catch (error) {
            alert(`Failed to save settings: ${error}`);
        } finally {
            setSaving(false);
        }
    }

    if (loading || !settings) {
        return <div style={{ textAlign: 'center', padding: '3rem' }}>Loading...</div>;
    }

    return (
        <div>
            <Card
                title="System Settings"
                actions={
                    <Button onClick={saveSettings} variant="success" disabled={saving}>
                        {saving ? 'Saving...' : 'Save Settings'}
                    </Button>
                }
            >
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1.5rem' }}>
                    <div>
                        <h4 style={{ marginBottom: '1rem', fontSize: '1rem', fontWeight: '600' }}>
                            Logging & Monitoring
                        </h4>

                        <Select
                            label="Log Level"
                            value={settings.log_level}
                            onChange={(val: string) => setSettings({ ...settings, log_level: val })}
                            options={[
                                { value: 'DEBUG', label: 'DEBUG' },
                                { value: 'INFO', label: 'INFO' },
                                { value: 'WARNING', label: 'WARNING' },
                                { value: 'ERROR', label: 'ERROR' }
                            ]}
                        />

                        <div style={{ marginBottom: '1rem' }}>
                            <label style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.5rem',
                                cursor: 'pointer'
                            }}>
                                <input
                                    type="checkbox"
                                    checked={settings.enable_metrics}
                                    onChange={(e) => setSettings({ ...settings, enable_metrics: e.target.checked })}
                                />
                                <span style={{ fontSize: '0.875rem' }}>Enable Metrics Collection</span>
                            </label>
                        </div>

                        <div style={{ marginBottom: '1rem' }}>
                            <label style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.5rem',
                                cursor: 'pointer'
                            }}>
                                <input
                                    type="checkbox"
                                    checked={settings.enable_audit_log}
                                    onChange={(e) => setSettings({ ...settings, enable_audit_log: e.target.checked })}
                                />
                                <span style={{ fontSize: '0.875rem' }}>Enable Audit Logging</span>
                            </label>
                        </div>
                    </div>

                    <div>
                        <h4 style={{ marginBottom: '1rem', fontSize: '1rem', fontWeight: '600' }}>
                            Performance
                        </h4>

                        <Input
                            label="Max Retries"
                            value={settings.max_retries}
                            onChange={(val: string) => setSettings({ ...settings, max_retries: parseInt(val) || 0 })}
                            type="number"
                        />

                        <Input
                            label="Timeout (seconds)"
                            value={settings.timeout_seconds}
                            onChange={(val: string) => setSettings({ ...settings, timeout_seconds: parseInt(val) || 0 })}
                            type="number"
                        />
                    </div>

                    <div>
                        <h4 style={{ marginBottom: '1rem', fontSize: '1rem', fontWeight: '600' }}>
                            Data Management
                        </h4>

                        <Input
                            label="Data Retention (days)"
                            value={settings.data_retention_days}
                            onChange={(val: string) => setSettings({ ...settings, data_retention_days: parseInt(val) || 0 })}
                            type="number"
                        />
                    </div>

                    <div>
                        <h4 style={{ marginBottom: '1rem', fontSize: '1rem', fontWeight: '600' }}>
                            Backup
                        </h4>

                        <div style={{ marginBottom: '1rem' }}>
                            <label style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.5rem',
                                cursor: 'pointer'
                            }}>
                                <input
                                    type="checkbox"
                                    checked={settings.backup_enabled}
                                    onChange={(e) => setSettings({ ...settings, backup_enabled: e.target.checked })}
                                />
                                <span style={{ fontSize: '0.875rem' }}>Enable Automatic Backups</span>
                            </label>
                        </div>

                        <Input
                            label="Backup Interval (hours)"
                            value={settings.backup_interval_hours}
                            onChange={(val: string) => setSettings({ ...settings, backup_interval_hours: parseInt(val) || 0 })}
                            type="number"
                            disabled={!settings.backup_enabled}
                        />
                    </div>
                </div>
            </Card>
        </div>
    );
}

// ============================================================================
// Main Admin Panel Component
// ============================================================================

function AdminPanel({ onClose }: { onClose: () => void }) {
    const [activeTab, setActiveTab] = useState('env');

    const tabs = [
        { id: 'env', label: 'Settings', icon: '🔧', component: EnvironmentVariablesTab },
        { id: 'api-keys', label: 'API Keys', icon: '🔑', component: APIKeysTab },
        { id: 'users', label: 'Users', icon: '👥', component: UsersTab },
        { id: 'agents', label: 'Agent Config', icon: '⚙️', component: () => <window.AgentConfigManager /> },
        { id: 'system', label: 'System', icon: '📊', component: SystemSettingsTab },
        { id: 'integrations', label: 'Integrations', icon: '🔌', component: () => <window.IntegrationManager /> }
    ];

    const ActiveComponent = tabs.find(t => t.id === activeTab)?.component || (() => null);

    return (
        <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'var(--bg-primary)',
            zIndex: 999,
            overflow: 'auto'
        }}>
            {/* Header */}
            <header style={{
                background: 'linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-tertiary) 100%)',
                borderBottom: '1px solid var(--border-color)',
                padding: '1.5rem 2rem',
                position: 'sticky',
                top: 0,
                zIndex: 100
            }}>
                <div style={{
                    maxWidth: '1920px',
                    margin: '0 auto',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                }}>
                    <div>
                        <h1 style={{
                            fontSize: '1.75rem',
                            fontWeight: '700',
                            background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
                            WebkitBackgroundClip: 'text',
                            WebkitTextFillColor: 'transparent',
                            backgroundClip: 'text'
                        }}>
                            APQC Admin Panel
                        </h1>
                        <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                            Comprehensive Configuration Management
                        </p>
                    </div>
                    <Button onClick={onClose} variant="secondary" icon="←">
                        Back to Dashboard
                    </Button>
                </div>
            </header>

            {/* Content */}
            <div style={{
                maxWidth: '1920px',
                margin: '0 auto',
                padding: '2rem'
            }}>
                {/* Tab Navigation */}
                <div style={{
                    display: 'flex',
                    gap: '1rem',
                    marginBottom: '2rem',
                    borderBottom: '1px solid var(--border-color)',
                    paddingBottom: '1rem',
                    overflowX: 'auto'
                }}>
                    {tabs.map(tab => (
                        <TabButton
                            key={tab.id}
                            active={activeTab === tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            icon={tab.icon}
                        >
                            {tab.label}
                        </TabButton>
                    ))}
                </div>

                {/* Tab Content */}
                <div>
                    <ActiveComponent />
                </div>
            </div>
        </div>
    );
}

// Export component (for use in main dashboard)
window.AdminPanel = AdminPanel;
