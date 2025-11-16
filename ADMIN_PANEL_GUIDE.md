# APQC Admin Panel - Comprehensive Configuration Management

## Overview

The APQC Admin Panel is a production-ready, comprehensive configuration management system that allows you to manage all aspects of the APQC dashboard **entirely through the UI** - no direct file editing required.

## Features

### 🔧 Settings Tab (Environment Variables)
- **Edit Environment Variables**: Manage LOG_LEVEL, MAX_RETRIES, TIMEOUT_SECONDS, and more
- **Category Organization**: Variables grouped by category (general, database, api, monitoring, security)
- **Secret Management**: Sensitive values are encrypted and masked in the UI
- **Direct .env Sync**: Changes are immediately written to the .env file
- **Description Support**: Add descriptions to document what each variable does

### 🔑 API Keys Tab
- **Multi-Service Support**: Manage API keys for 15+ services
  - AI Models: OpenAI, Anthropic
  - Cloud: AWS, GCP, Azure
  - CRM: Salesforce, HubSpot
  - ERP: SAP, Oracle, NetSuite
  - Accounting: QuickBooks, Xero
  - And more...
- **Encrypted Storage**: All keys encrypted at rest using AES-256
- **Expiration Management**: Set expiration dates for keys
- **Masked Display**: Keys are masked in the UI for security
- **Last Used Tracking**: Monitor when keys were last accessed

### 👥 Users Tab
- **Role-Based Access Control**:
  - **Admin**: Full access to all features
  - **Business User**: Configure workflows and agents
  - **Viewer**: Read-only access
- **User Management**: Create, update, and delete users
- **Password Policies**: Enforced password strength requirements
- **Activity Tracking**: Last login timestamps

### ⚙️ Agent Config Tab
- **118+ Agent Configuration**: Individual settings for each APQC agent
- **Category-Specific Settings**:
  - **Financial Agents (Category 9)**: Accounting system, fiscal year, currency
  - **HR Agents (Category 7)**: HR system, employee ID format
  - **Marketing Agents (Category 3)**: CRM system, email provider
  - **Supply Chain Agents (Category 4)**: WMS system, reorder points
  - **Customer Service Agents (Category 6)**: Ticketing system, SLA
- **Performance Settings**:
  - Enable/disable agents
  - Priority (0-100)
  - Rate limits
  - Timeouts
  - Retry configuration (max retries, delay, exponential backoff)
- **Search & Filter**: Quick agent lookup by name or category
- **Visual Status**: See which agents are configured vs. using defaults

### 📊 System Tab
- **Logging & Monitoring**:
  - Log level (DEBUG, INFO, WARNING, ERROR)
  - Enable/disable metrics collection
  - Enable/disable audit logging
- **Performance**:
  - Max retries
  - Global timeout settings
- **Data Management**:
  - Data retention period (days)
- **Backup**:
  - Enable/disable automatic backups
  - Backup interval configuration

### 🔌 Integrations Tab
- **20+ Integration Templates**:
  - **ERP**: SAP, Oracle, NetSuite
  - **Accounting**: QuickBooks, Xero, Sage
  - **CRM**: Salesforce, HubSpot, Dynamics 365
  - **HR**: Workday, BambooHR, ADP
  - **Supply Chain**: SAP SCM, Oracle SCM
  - **E-commerce**: Shopify
  - **Payments**: Stripe
  - **Cloud**: AWS, GCP, Azure
- **Visual Integration Cards**: Easy-to-scan status display
- **Connection Testing**: Test integration connections
- **Credential Management**: Secure, encrypted credential storage
- **OAuth Support**: Built-in OAuth flow handling
- **Sync Monitoring**: Track last sync time and status
- **Error Diagnostics**: View detailed error messages

## Installation

### 1. Install Dependencies

```bash
pip install -r admin_requirements.txt
```

### 2. Start the Dashboard Server

The admin API is automatically integrated into the dashboard server:

```bash
python dashboard_server.py
```

### 3. Access the Admin Panel

1. Open the dashboard: http://localhost:8765
2. Click the "🔧 Admin Panel" button in the top-right corner
3. Login with default credentials:
   - Username: `admin`
   - Password: `admin123`
   - **⚠️ IMPORTANT**: Change the default password immediately!

## Security Features

### Encryption
- **AES-256 Encryption**: All sensitive data encrypted at rest
- **Key Derivation**: PBKDF2 with 100,000 iterations
- **Secure Storage**: Encryption key stored separately from database

### Authentication
- **Password Hashing**: bcrypt with salt
- **Password Policies**:
  - Minimum 8 characters
  - Must contain uppercase, lowercase, and number
- **Role-Based Access**: Granular permissions by user role

### Audit Logging
- **Complete Audit Trail**: All configuration changes logged
- **User Tracking**: Know who made what changes
- **Timestamp Tracking**: When changes were made
- **Change Details**: What was changed (before/after)

## Database

The admin panel uses SQLite for data storage:

- **Database File**: `./admin_data.db`
- **Tables**:
  - `users` - User accounts and roles
  - `env_variables` - Environment variables
  - `api_keys` - API keys for external services
  - `integrations` - Integration configurations
  - `agent_configs` - Per-agent settings
  - `audit_log` - Audit trail
  - `system_settings` - Global system settings

## API Endpoints

All admin API endpoints are prefixed with `/api/admin`:

### Environment Variables
- `GET /api/admin/env` - Get all environment variables
- `POST /api/admin/env` - Set environment variable
- `DELETE /api/admin/env/{key}` - Delete environment variable

### API Keys
- `GET /api/admin/api-keys` - Get all API keys
- `POST /api/admin/api-keys` - Create API key
- `DELETE /api/admin/api-keys/{key_id}` - Delete API key

### Users
- `GET /api/admin/users` - Get all users (admin only)
- `POST /api/admin/users` - Create user (admin only)
- `PUT /api/admin/users/{user_id}` - Update user (admin only)
- `DELETE /api/admin/users/{user_id}` - Delete user (admin only)

### Integrations
- `GET /api/admin/integrations` - Get all integrations
- `POST /api/admin/integrations` - Create integration
- `PUT /api/admin/integrations/{integration_id}` - Update integration
- `POST /api/admin/integrations/{integration_id}/test` - Test connection
- `DELETE /api/admin/integrations/{integration_id}` - Delete integration

### Agent Configuration
- `GET /api/admin/agents/config` - Get all agent configs
- `GET /api/admin/agents/config/{agent_id}` - Get specific agent config
- `PUT /api/admin/agents/config/{agent_id}` - Update agent config

### System Settings
- `GET /api/admin/system/settings` - Get system settings
- `PUT /api/admin/system/settings` - Update system settings

### Audit Log
- `GET /api/admin/audit-log` - Get audit log (admin only)

## Usage Examples

### Configure a Financial Agent

1. Click "Agent Config" tab
2. Search for "PerformGeneralAccountingReportingFinancialAgent"
3. Click the agent card
4. Configure:
   - Accounting System: QuickBooks
   - Fiscal Year End: December 31
   - Currency: USD
   - Timeout: 60 seconds
   - Rate Limit: 100 requests/minute
5. Click "Save Configuration"

### Set Up Salesforce Integration

1. Click "Integrations" tab
2. Find "Salesforce" card in CRM category
3. Click to configure
4. Enter credentials:
   - Instance URL: https://yourcompany.salesforce.com
   - Client ID: (from Salesforce connected app)
   - Client Secret: (from Salesforce connected app)
   - Username: your-username@company.com
   - Password: your-password
   - Security Token: your-security-token
5. Configure settings:
   - API Version: v57.0
   - Sandbox: false
6. Click "Save Integration"
7. Click "Test Connection" to verify

### Create a Business User

1. Click "Users" tab
2. Click "Add User"
3. Enter details:
   - Username: jsmith
   - Email: jsmith@company.com
   - Password: SecurePass123
   - Role: Business User
4. Click "Create User"

### Set Environment Variables

1. Click "Settings" tab
2. Click "Add Variable"
3. Enter:
   - Key: LOG_LEVEL
   - Value: DEBUG
   - Description: Logging level for the application
   - Category: general
   - Secret: No
4. Click "Save"

## Best Practices

### Security
1. **Change Default Password**: Immediately change admin password
2. **Principle of Least Privilege**: Give users minimum required role
3. **Regular Key Rotation**: Rotate API keys periodically
4. **Monitor Audit Log**: Review audit log regularly
5. **Secure Credentials**: Never share admin credentials

### Configuration Management
1. **Test Integrations**: Always test connections after setup
2. **Document Settings**: Use descriptions for environment variables
3. **Start Conservative**: Begin with lower rate limits, increase as needed
4. **Monitor Performance**: Watch agent metrics after configuration changes
5. **Use Categories**: Organize variables and settings logically

### Agent Configuration
1. **Configure Gradually**: Don't configure all 118 agents at once
2. **Category Approach**: Configure by category based on workflows
3. **Test First**: Test agent configuration with low priority/limits
4. **Monitor Errors**: Watch for errors after enabling agents
5. **Document Customization**: Use custom_settings for specific needs

## Troubleshooting

### Admin API Not Available
- **Check**: Ensure `admin_api.py` is in the project root
- **Check**: Verify `admin_requirements.txt` dependencies installed
- **Check**: Look for import errors in server logs

### Cannot Login
- **Default Credentials**: admin / admin123
- **Reset**: Delete `admin_data.db` to recreate with defaults
- **Check**: Verify user exists in database

### Integration Test Fails
- **Credentials**: Verify all required credentials are correct
- **Network**: Check firewall/network connectivity
- **API Limits**: Check if hitting rate limits
- **Documentation**: Refer to integration's documentation

### Environment Variables Not Persisting
- **File Permissions**: Check write permissions on `.env` file
- **Format**: Ensure no special characters breaking format
- **Restart**: Restart server to pick up changes

## File Structure

```
multiAgentStandardsProtocol/
├── admin_api.py                           # Backend API (600 LOC)
├── admin_requirements.txt                 # Python dependencies
├── admin_data.db                          # SQLite database (auto-created)
├── .encryption_key                        # Encryption key (auto-created)
├── dashboard_server.py                    # Main server (includes admin routes)
└── dashboard_frontend/
    ├── index.html                         # Updated with admin components
    ├── app.tsx                            # Updated with admin button
    ├── admin_panel.tsx                    # Admin panel UI (800 LOC)
    ├── agent_config.tsx                   # Agent config UI (500 LOC)
    └── integration_manager.tsx            # Integration UI (400 LOC)
```

## Support

For issues or questions:
1. Check the audit log for error details
2. Review server logs for backend errors
3. Check browser console for frontend errors
4. Refer to integration documentation links

## Version

- **Version**: 1.0.0
- **Date**: 2025-11-16
- **Author**: APQC Admin Team

---

**Remember**: Everything is configurable through the UI. No direct file editing needed! 🎉
