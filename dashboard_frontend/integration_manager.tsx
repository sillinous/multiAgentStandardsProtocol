/**
 * Integration Manager Component - External System Configuration
 * ==============================================================
 *
 * Production-ready component for managing integrations with external
 * systems like Salesforce, SAP, QuickBooks, Workday, etc.
 *
 * Features:
 * - Visual integration cards
 * - Connection testing
 * - Credential management (encrypted)
 * - OAuth flow handling
 * - Enable/disable integrations
 * - Sync status monitoring
 * - Error handling and diagnostics
 *
 * Version: 1.0.0
 * Author: APQC Admin Team
 * Date: 2025-11-16
 */

const { useState, useEffect, useMemo } = React;

// ============================================================================
// Data Models
// ============================================================================

interface Integration {
    integration_id: string;
    name: string;
    type: string;
    is_enabled: boolean;
    credentials: Record<string, string>;
    settings: any;
    last_sync?: string;
    status: 'not_configured' | 'active' | 'error';
    error_message?: string;
    created_at: string;
    updated_at: string;
}

interface IntegrationTemplate {
    type: string;
    name: string;
    category: string;
    icon: string;
    description: string;
    credentialFields: Array<{
        key: string;
        label: string;
        type: 'text' | 'password' | 'url';
        required: boolean;
        placeholder?: string;
    }>;
    settingFields: Array<{
        key: string;
        label: string;
        type: 'text' | 'number' | 'boolean' | 'select';
        options?: string[];
        default?: any;
    }>;
    documentationUrl?: string;
}

// ============================================================================
// Integration Templates
// ============================================================================

const INTEGRATION_TEMPLATES: IntegrationTemplate[] = [
    // ERP Systems
    {
        type: 'sap',
        name: 'SAP ERP',
        category: 'ERP',
        icon: '🏢',
        description: 'SAP ERP system integration for financial and supply chain operations',
        credentialFields: [
            { key: 'host', label: 'SAP Host', type: 'url', required: true, placeholder: 'https://sap.company.com' },
            { key: 'client', label: 'Client ID', type: 'text', required: true },
            { key: 'username', label: 'Username', type: 'text', required: true },
            { key: 'password', label: 'Password', type: 'password', required: true }
        ],
        settingFields: [
            { key: 'sync_interval', label: 'Sync Interval (minutes)', type: 'number', default: 15 },
            { key: 'enable_realtime', label: 'Enable Real-time Sync', type: 'boolean', default: false }
        ],
        documentationUrl: 'https://help.sap.com'
    },
    {
        type: 'oracle',
        name: 'Oracle ERP',
        category: 'ERP',
        icon: '🔴',
        description: 'Oracle ERP Cloud integration for enterprise resource planning',
        credentialFields: [
            { key: 'instance_url', label: 'Instance URL', type: 'url', required: true },
            { key: 'username', label: 'Username', type: 'text', required: true },
            { key: 'password', label: 'Password', type: 'password', required: true }
        ],
        settingFields: [
            { key: 'sync_interval', label: 'Sync Interval (minutes)', type: 'number', default: 30 }
        ]
    },
    {
        type: 'netsuite',
        name: 'NetSuite',
        category: 'ERP',
        icon: '☁️',
        description: 'NetSuite cloud ERP integration',
        credentialFields: [
            { key: 'account_id', label: 'Account ID', type: 'text', required: true },
            { key: 'consumer_key', label: 'Consumer Key', type: 'text', required: true },
            { key: 'consumer_secret', label: 'Consumer Secret', type: 'password', required: true },
            { key: 'token_id', label: 'Token ID', type: 'text', required: true },
            { key: 'token_secret', label: 'Token Secret', type: 'password', required: true }
        ],
        settingFields: [
            { key: 'sync_interval', label: 'Sync Interval (minutes)', type: 'number', default: 20 }
        ]
    },

    // Accounting Systems
    {
        type: 'quickbooks',
        name: 'QuickBooks Online',
        category: 'Accounting',
        icon: '💚',
        description: 'QuickBooks Online accounting integration',
        credentialFields: [
            { key: 'client_id', label: 'Client ID', type: 'text', required: true },
            { key: 'client_secret', label: 'Client Secret', type: 'password', required: true },
            { key: 'refresh_token', label: 'Refresh Token', type: 'password', required: true },
            { key: 'realm_id', label: 'Company ID (Realm ID)', type: 'text', required: true }
        ],
        settingFields: [
            { key: 'environment', label: 'Environment', type: 'select', options: ['sandbox', 'production'], default: 'production' }
        ],
        documentationUrl: 'https://developer.intuit.com/app/developer/qbo/docs/get-started'
    },
    {
        type: 'xero',
        name: 'Xero',
        category: 'Accounting',
        icon: '💙',
        description: 'Xero cloud accounting integration',
        credentialFields: [
            { key: 'client_id', label: 'Client ID', type: 'text', required: true },
            { key: 'client_secret', label: 'Client Secret', type: 'password', required: true }
        ],
        settingFields: []
    },
    {
        type: 'sage',
        name: 'Sage Intacct',
        category: 'Accounting',
        icon: '📗',
        description: 'Sage Intacct financial management integration',
        credentialFields: [
            { key: 'company_id', label: 'Company ID', type: 'text', required: true },
            { key: 'user_id', label: 'User ID', type: 'text', required: true },
            { key: 'password', label: 'Password', type: 'password', required: true }
        ],
        settingFields: []
    },

    // CRM Systems
    {
        type: 'salesforce',
        name: 'Salesforce',
        category: 'CRM',
        icon: '⛅',
        description: 'Salesforce CRM integration for customer data and workflows',
        credentialFields: [
            { key: 'instance_url', label: 'Instance URL', type: 'url', required: true, placeholder: 'https://yourcompany.salesforce.com' },
            { key: 'client_id', label: 'Client ID', type: 'text', required: true },
            { key: 'client_secret', label: 'Client Secret', type: 'password', required: true },
            { key: 'username', label: 'Username', type: 'text', required: true },
            { key: 'password', label: 'Password', type: 'password', required: true },
            { key: 'security_token', label: 'Security Token', type: 'password', required: true }
        ],
        settingFields: [
            { key: 'api_version', label: 'API Version', type: 'text', default: 'v57.0' },
            { key: 'sandbox', label: 'Sandbox Environment', type: 'boolean', default: false }
        ],
        documentationUrl: 'https://developer.salesforce.com/'
    },
    {
        type: 'hubspot',
        name: 'HubSpot',
        category: 'CRM',
        icon: '🧡',
        description: 'HubSpot CRM and marketing automation',
        credentialFields: [
            { key: 'api_key', label: 'API Key', type: 'password', required: true }
        ],
        settingFields: []
    },
    {
        type: 'dynamics',
        name: 'Microsoft Dynamics 365',
        category: 'CRM',
        icon: '🔷',
        description: 'Microsoft Dynamics 365 CRM integration',
        credentialFields: [
            { key: 'organization_url', label: 'Organization URL', type: 'url', required: true },
            { key: 'client_id', label: 'Client ID', type: 'text', required: true },
            { key: 'client_secret', label: 'Client Secret', type: 'password', required: true },
            { key: 'tenant_id', label: 'Tenant ID', type: 'text', required: true }
        ],
        settingFields: []
    },

    // HR Systems
    {
        type: 'workday',
        name: 'Workday',
        category: 'HR',
        icon: '👥',
        description: 'Workday HCM integration for HR and payroll',
        credentialFields: [
            { key: 'tenant_url', label: 'Tenant URL', type: 'url', required: true },
            { key: 'username', label: 'Username', type: 'text', required: true },
            { key: 'password', label: 'Password', type: 'password', required: true }
        ],
        settingFields: [
            { key: 'api_version', label: 'API Version', type: 'text', default: 'v38.0' }
        ]
    },
    {
        type: 'bamboo_hr',
        name: 'BambooHR',
        category: 'HR',
        icon: '🎋',
        description: 'BambooHR integration for employee management',
        credentialFields: [
            { key: 'subdomain', label: 'Subdomain', type: 'text', required: true, placeholder: 'yourcompany' },
            { key: 'api_key', label: 'API Key', type: 'password', required: true }
        ],
        settingFields: []
    },
    {
        type: 'adp',
        name: 'ADP Workforce Now',
        category: 'HR',
        icon: '💼',
        description: 'ADP payroll and HR integration',
        credentialFields: [
            { key: 'client_id', label: 'Client ID', type: 'text', required: true },
            { key: 'client_secret', label: 'Client Secret', type: 'password', required: true }
        ],
        settingFields: []
    },

    // Supply Chain
    {
        type: 'sap_scm',
        name: 'SAP SCM',
        category: 'Supply Chain',
        icon: '📦',
        description: 'SAP Supply Chain Management integration',
        credentialFields: [
            { key: 'host', label: 'SAP Host', type: 'url', required: true },
            { key: 'client', label: 'Client ID', type: 'text', required: true },
            { key: 'username', label: 'Username', type: 'text', required: true },
            { key: 'password', label: 'Password', type: 'password', required: true }
        ],
        settingFields: []
    },
    {
        type: 'oracle_scm',
        name: 'Oracle SCM Cloud',
        category: 'Supply Chain',
        icon: '🚚',
        description: 'Oracle Supply Chain Management Cloud',
        credentialFields: [
            { key: 'instance_url', label: 'Instance URL', type: 'url', required: true },
            { key: 'username', label: 'Username', type: 'text', required: true },
            { key: 'password', label: 'Password', type: 'password', required: true }
        ],
        settingFields: []
    },

    // E-commerce & Payments
    {
        type: 'shopify',
        name: 'Shopify',
        category: 'E-commerce',
        icon: '🛍️',
        description: 'Shopify e-commerce platform integration',
        credentialFields: [
            { key: 'shop_url', label: 'Shop URL', type: 'url', required: true, placeholder: 'yourstore.myshopify.com' },
            { key: 'api_key', label: 'API Key', type: 'text', required: true },
            { key: 'api_secret', label: 'API Secret', type: 'password', required: true }
        ],
        settingFields: []
    },
    {
        type: 'stripe',
        name: 'Stripe',
        category: 'Payments',
        icon: '💳',
        description: 'Stripe payment processing integration',
        credentialFields: [
            { key: 'publishable_key', label: 'Publishable Key', type: 'text', required: true },
            { key: 'secret_key', label: 'Secret Key', type: 'password', required: true }
        ],
        settingFields: [
            { key: 'mode', label: 'Mode', type: 'select', options: ['test', 'live'], default: 'test' }
        ]
    },

    // Cloud Providers
    {
        type: 'aws',
        name: 'AWS',
        category: 'Cloud',
        icon: '☁️',
        description: 'Amazon Web Services integration',
        credentialFields: [
            { key: 'access_key_id', label: 'Access Key ID', type: 'text', required: true },
            { key: 'secret_access_key', label: 'Secret Access Key', type: 'password', required: true },
            { key: 'region', label: 'Region', type: 'text', required: true, placeholder: 'us-east-1' }
        ],
        settingFields: []
    },
    {
        type: 'gcp',
        name: 'Google Cloud Platform',
        category: 'Cloud',
        icon: '☁️',
        description: 'Google Cloud Platform integration',
        credentialFields: [
            { key: 'project_id', label: 'Project ID', type: 'text', required: true },
            { key: 'service_account_key', label: 'Service Account Key (JSON)', type: 'password', required: true }
        ],
        settingFields: []
    },
    {
        type: 'azure',
        name: 'Microsoft Azure',
        category: 'Cloud',
        icon: '☁️',
        description: 'Microsoft Azure integration',
        credentialFields: [
            { key: 'subscription_id', label: 'Subscription ID', type: 'text', required: true },
            { key: 'client_id', label: 'Client ID', type: 'text', required: true },
            { key: 'client_secret', label: 'Client Secret', type: 'password', required: true },
            { key: 'tenant_id', label: 'Tenant ID', type: 'text', required: true }
        ],
        settingFields: []
    }
];

// ============================================================================
// API Helper Functions
// ============================================================================

const ADMIN_API = 'http://localhost:8765/api/admin';

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

function Input({ label, value, onChange, type = 'text', placeholder = '', required = false }: any) {
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
                    {label} {required && <span style={{ color: 'var(--status-unhealthy)' }}>*</span>}
                </label>
            )}
            <input
                type={type}
                value={value}
                onChange={(e) => onChange(e.target.value)}
                placeholder={placeholder}
                required={required}
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

// ============================================================================
// Integration Card Component
// ============================================================================

function IntegrationCard({ integration, template, onConfigure, onTest, onToggle, onDelete }: any) {
    const [testing, setTesting] = useState(false);
    const [testResult, setTestResult] = useState<any>(null);

    async function handleTest() {
        setTesting(true);
        setTestResult(null);
        try {
            const result = await apiCall(`${ADMIN_API}/integrations/${integration.integration_id}/test`, 'POST');
            setTestResult(result);
        } catch (error) {
            setTestResult({ status: 'error', message: String(error) });
        } finally {
            setTesting(false);
        }
    }

    const statusColor = integration.status === 'active' ? 'var(--status-healthy)' :
                       integration.status === 'error' ? 'var(--status-unhealthy)' :
                       'var(--status-offline)';

    return (
        <div style={{
            background: 'var(--bg-tertiary)',
            border: '1px solid var(--border-color)',
            borderRadius: '8px',
            padding: '1.5rem',
            transition: 'var(--transition)'
        }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '1rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <div style={{ fontSize: '2rem' }}>{template.icon}</div>
                    <div>
                        <div style={{ fontSize: '1rem', fontWeight: '600', color: 'var(--text-primary)' }}>
                            {template.name}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                            {template.category}
                        </div>
                    </div>
                </div>

                <div style={{
                    width: '10px',
                    height: '10px',
                    borderRadius: '50%',
                    background: statusColor
                }}></div>
            </div>

            <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                {template.description}
            </div>

            {/* Status Info */}
            <div style={{
                padding: '0.75rem',
                background: 'var(--bg-secondary)',
                borderRadius: '6px',
                marginBottom: '1rem'
            }}>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.75rem', fontSize: '0.75rem' }}>
                    <div>
                        <div style={{ color: 'var(--text-muted)' }}>Status</div>
                        <div style={{ fontWeight: '600', color: statusColor, textTransform: 'uppercase' }}>
                            {integration.status}
                        </div>
                    </div>
                    <div>
                        <div style={{ color: 'var(--text-muted)' }}>Last Sync</div>
                        <div style={{ fontWeight: '500' }}>
                            {integration.last_sync
                                ? new Date(integration.last_sync).toLocaleString()
                                : 'Never'}
                        </div>
                    </div>
                </div>

                {integration.error_message && (
                    <div style={{
                        marginTop: '0.75rem',
                        padding: '0.5rem',
                        background: 'var(--status-unhealthy)',
                        color: 'white',
                        borderRadius: '4px',
                        fontSize: '0.75rem'
                    }}>
                        {integration.error_message}
                    </div>
                )}
            </div>

            {/* Test Result */}
            {testResult && (
                <div style={{
                    padding: '0.75rem',
                    background: testResult.status === 'success' ? 'var(--status-healthy)' : 'var(--status-unhealthy)',
                    color: 'white',
                    borderRadius: '6px',
                    marginBottom: '1rem',
                    fontSize: '0.875rem'
                }}>
                    {testResult.status === 'success' ? '✓' : '✗'} {testResult.message}
                    {testResult.latency_ms && ` (${testResult.latency_ms}ms)`}
                </div>
            )}

            {/* Actions */}
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                <Button onClick={onConfigure} variant="primary" small>
                    Configure
                </Button>
                <Button onClick={handleTest} variant="secondary" small disabled={testing}>
                    {testing ? 'Testing...' : 'Test Connection'}
                </Button>
                <Button
                    onClick={() => onToggle(!integration.is_enabled)}
                    variant={integration.is_enabled ? 'secondary' : 'success'}
                    small
                >
                    {integration.is_enabled ? 'Disable' : 'Enable'}
                </Button>
                <Button onClick={onDelete} variant="danger" small>
                    Delete
                </Button>
            </div>
        </div>
    );
}

// ============================================================================
// Integration Configuration Dialog
// ============================================================================

function IntegrationDialog({ template, integration, onSave, onCancel }: any) {
    const [formData, setFormData] = useState<any>(
        integration || {
            name: template.name,
            type: template.type,
            credentials: {},
            settings: {}
        }
    );

    // Initialize default settings
    useEffect(() => {
        if (!integration) {
            const defaultSettings: any = {};
            template.settingFields.forEach((field: any) => {
                if (field.default !== undefined) {
                    defaultSettings[field.key] = field.default;
                }
            });
            setFormData((prev: any) => ({ ...prev, settings: defaultSettings }));
        }
    }, [template]);

    function handleSave() {
        // Validate required fields
        const missingFields = template.credentialFields
            .filter((field: any) => field.required && !formData.credentials[field.key])
            .map((field: any) => field.label);

        if (missingFields.length > 0) {
            alert(`Please fill in required fields: ${missingFields.join(', ')}`);
            return;
        }

        onSave(formData);
    }

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
            zIndex: 1000,
            overflow: 'auto'
        }} onClick={onCancel}>
            <div
                style={{
                    background: 'var(--bg-card)',
                    borderRadius: '12px',
                    padding: '2rem',
                    width: '100%',
                    maxWidth: '600px',
                    maxHeight: '90vh',
                    overflow: 'auto',
                    border: '1px solid var(--border-color)',
                    margin: '1rem'
                }}
                onClick={(e) => e.stopPropagation()}
            >
                <h3 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ fontSize: '1.5rem' }}>{template.icon}</span>
                    {integration ? 'Edit' : 'Configure'} {template.name}
                </h3>

                {/* Basic Info */}
                <div style={{ marginBottom: '2rem' }}>
                    <Input
                        label="Integration Name"
                        value={formData.name}
                        onChange={(val: string) => setFormData({ ...formData, name: val })}
                        placeholder={template.name}
                        required
                    />
                </div>

                {/* Credentials */}
                <div style={{ marginBottom: '2rem' }}>
                    <h4 style={{ marginBottom: '1rem', fontSize: '1rem', fontWeight: '600' }}>
                        Credentials
                    </h4>
                    {template.credentialFields.map((field: any) => (
                        <Input
                            key={field.key}
                            label={field.label}
                            value={formData.credentials[field.key] || ''}
                            onChange={(val: string) => setFormData({
                                ...formData,
                                credentials: { ...formData.credentials, [field.key]: val }
                            })}
                            type={field.type}
                            placeholder={field.placeholder}
                            required={field.required}
                        />
                    ))}
                </div>

                {/* Settings */}
                {template.settingFields.length > 0 && (
                    <div style={{ marginBottom: '2rem' }}>
                        <h4 style={{ marginBottom: '1rem', fontSize: '1rem', fontWeight: '600' }}>
                            Settings
                        </h4>
                        {template.settingFields.map((field: any) => {
                            if (field.type === 'boolean') {
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
                                                checked={formData.settings[field.key] || false}
                                                onChange={(e) => setFormData({
                                                    ...formData,
                                                    settings: { ...formData.settings, [field.key]: e.target.checked }
                                                })}
                                            />
                                            <span style={{ fontSize: '0.875rem' }}>{field.label}</span>
                                        </label>
                                    </div>
                                );
                            } else if (field.type === 'select') {
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
                                            value={formData.settings[field.key] || field.default}
                                            onChange={(e) => setFormData({
                                                ...formData,
                                                settings: { ...formData.settings, [field.key]: e.target.value }
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
                                            {field.options.map((opt: string) => (
                                                <option key={opt} value={opt}>{opt}</option>
                                            ))}
                                        </select>
                                    </div>
                                );
                            } else {
                                return (
                                    <Input
                                        key={field.key}
                                        label={field.label}
                                        value={formData.settings[field.key] || ''}
                                        onChange={(val: string) => setFormData({
                                            ...formData,
                                            settings: { ...formData.settings, [field.key]: val }
                                        })}
                                        type={field.type}
                                    />
                                );
                            }
                        })}
                    </div>
                )}

                {/* Documentation Link */}
                {template.documentationUrl && (
                    <div style={{ marginBottom: '2rem' }}>
                        <a
                            href={template.documentationUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{
                                color: 'var(--accent-primary)',
                                fontSize: '0.875rem',
                                textDecoration: 'none'
                            }}
                        >
                            📚 View Documentation
                        </a>
                    </div>
                )}

                {/* Actions */}
                <div style={{ display: 'flex', gap: '1rem' }}>
                    <Button onClick={handleSave} variant="success">
                        Save Integration
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
// Main Integration Manager Component
// ============================================================================

function IntegrationManager() {
    const [integrations, setIntegrations] = useState<Integration[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedTemplate, setSelectedTemplate] = useState<IntegrationTemplate | null>(null);
    const [editingIntegration, setEditingIntegration] = useState<Integration | null>(null);
    const [filterCategory, setFilterCategory] = useState('all');

    useEffect(() => {
        loadIntegrations();
    }, []);

    async function loadIntegrations() {
        try {
            const data = await apiCall(`${ADMIN_API}/integrations`);
            setIntegrations(data.integrations || []);
        } catch (error) {
            console.error('Failed to load integrations:', error);
        } finally {
            setLoading(false);
        }
    }

    async function saveIntegration(data: any) {
        try {
            if (editingIntegration) {
                await apiCall(`${ADMIN_API}/integrations/${editingIntegration.integration_id}`, 'PUT', data);
            } else {
                await apiCall(`${ADMIN_API}/integrations`, 'POST', data);
            }
            await loadIntegrations();
            setSelectedTemplate(null);
            setEditingIntegration(null);
        } catch (error) {
            alert(`Failed to save integration: ${error}`);
        }
    }

    async function toggleIntegration(integration: Integration, enabled: boolean) {
        try {
            await apiCall(`${ADMIN_API}/integrations/${integration.integration_id}`, 'PUT', { is_enabled: enabled });
            await loadIntegrations();
        } catch (error) {
            alert(`Failed to toggle integration: ${error}`);
        }
    }

    async function deleteIntegration(integration: Integration) {
        if (!confirm(`Delete ${integration.name}?`)) return;

        try {
            await apiCall(`${ADMIN_API}/integrations/${integration.integration_id}`, 'DELETE');
            await loadIntegrations();
        } catch (error) {
            alert(`Failed to delete integration: ${error}`);
        }
    }

    const categories = useMemo(() => {
        const cats = new Set(INTEGRATION_TEMPLATES.map(t => t.category));
        return Array.from(cats);
    }, []);

    const filteredTemplates = useMemo(() => {
        if (filterCategory === 'all') return INTEGRATION_TEMPLATES;
        return INTEGRATION_TEMPLATES.filter(t => t.category === filterCategory);
    }, [filterCategory]);

    if (loading) {
        return <div style={{ textAlign: 'center', padding: '3rem' }}>Loading...</div>;
    }

    return (
        <div>
            <Card
                title="Integration Manager"
                actions={
                    <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                        {integrations.length} active integrations
                    </div>
                }
            >
                <div style={{ marginBottom: '1.5rem', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                    Connect APQC agents to external systems like Salesforce, SAP, QuickBooks, and more.
                    All credentials are encrypted at rest.
                </div>

                {/* Filter */}
                <div style={{ marginBottom: '2rem' }}>
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
                        {categories.map(cat => (
                            <option key={cat} value={cat}>{cat}</option>
                        ))}
                    </select>
                </div>

                {/* Configured Integrations */}
                {integrations.length > 0 && (
                    <div style={{ marginBottom: '2rem' }}>
                        <h4 style={{ marginBottom: '1rem', fontSize: '1rem', fontWeight: '600' }}>
                            Active Integrations
                        </h4>
                        <div style={{
                            display: 'grid',
                            gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))',
                            gap: '1rem'
                        }}>
                            {integrations.map(integration => {
                                const template = INTEGRATION_TEMPLATES.find(t => t.type === integration.type);
                                if (!template) return null;

                                return (
                                    <IntegrationCard
                                        key={integration.integration_id}
                                        integration={integration}
                                        template={template}
                                        onConfigure={() => {
                                            setEditingIntegration(integration);
                                            setSelectedTemplate(template);
                                        }}
                                        onTest={() => {}}
                                        onToggle={(enabled: boolean) => toggleIntegration(integration, enabled)}
                                        onDelete={() => deleteIntegration(integration)}
                                    />
                                );
                            })}
                        </div>
                    </div>
                )}

                {/* Available Integrations */}
                <div>
                    <h4 style={{ marginBottom: '1rem', fontSize: '1rem', fontWeight: '600' }}>
                        Available Integrations
                    </h4>
                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
                        gap: '1rem'
                    }}>
                        {filteredTemplates.map(template => {
                            const existingIntegration = integrations.find(i => i.type === template.type);

                            return (
                                <div
                                    key={template.type}
                                    onClick={() => !existingIntegration && setSelectedTemplate(template)}
                                    style={{
                                        background: 'var(--bg-tertiary)',
                                        border: '1px solid var(--border-color)',
                                        borderRadius: '8px',
                                        padding: '1rem',
                                        cursor: existingIntegration ? 'not-allowed' : 'pointer',
                                        opacity: existingIntegration ? 0.5 : 1,
                                        transition: 'var(--transition)',
                                        textAlign: 'center'
                                    }}
                                    onMouseEnter={(e) => {
                                        if (!existingIntegration) {
                                            e.currentTarget.style.borderColor = 'var(--accent-primary)';
                                            e.currentTarget.style.background = 'var(--bg-hover)';
                                        }
                                    }}
                                    onMouseLeave={(e) => {
                                        if (!existingIntegration) {
                                            e.currentTarget.style.borderColor = 'var(--border-color)';
                                            e.currentTarget.style.background = 'var(--bg-tertiary)';
                                        }
                                    }}
                                >
                                    <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>{template.icon}</div>
                                    <div style={{ fontSize: '0.875rem', fontWeight: '600', marginBottom: '0.25rem' }}>
                                        {template.name}
                                    </div>
                                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                        {template.category}
                                    </div>
                                    {existingIntegration && (
                                        <div style={{
                                            marginTop: '0.5rem',
                                            fontSize: '0.75rem',
                                            color: 'var(--status-healthy)',
                                            fontWeight: '600'
                                        }}>
                                            CONFIGURED
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                </div>
            </Card>

            {/* Configuration Dialog */}
            {selectedTemplate && (
                <IntegrationDialog
                    template={selectedTemplate}
                    integration={editingIntegration}
                    onSave={saveIntegration}
                    onCancel={() => {
                        setSelectedTemplate(null);
                        setEditingIntegration(null);
                    }}
                />
            )}
        </div>
    );
}

// Export component
window.IntegrationManager = IntegrationManager;
