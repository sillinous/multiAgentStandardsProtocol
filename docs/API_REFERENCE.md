# 📖 API Reference

Complete reference for the Agentic Forge REST API.

**Base URL**: `http://localhost:8080`

**Version**: 0.1.0-alpha

---

## Table of Contents

- [Authentication](#authentication)
- [Health & Status](#health--status)
- [Agents](#agents)
- [Agent Cards](#agent-cards)
- [Agent Card Versioning](#agent-card-versioning)
- [Agent Card Templates](#agent-card-templates)
- [Agent Card Comparison](#agent-card-comparison)
- [Agent Card Archive](#agent-card-archive)
- [Workflows](#workflows)
- [Protocols](#protocols)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [V2 API - Database-Backed](#v2-api---database-backed-implementations)
  - [AI Conversations](#ai-conversations-v2)
  - [AI Usage Logging](#ai-usage-logging-v2)
  - [AI Provider Configuration](#ai-provider-configuration-v2)
  - [Execution Queue](#execution-queue-v2)
  - [Secrets Management](#secrets-management-v2)
  - [Enterprise Operations](#enterprise-operations-v2)
  - [Platform Operations](#platform-operations-v2)
  - [Workflow Definitions](#workflow-definitions-v2)
  - [Test Suites](#test-suites-v2)
  - [Marketplace](#marketplace-v2)
  - [Health & Monitoring](#health--monitoring-v2)

---

## Authentication

Currently in alpha, authentication is optional. When enabled, include your API key in the header:

```http
Authorization: Bearer your_api_key_here
```

---

## Health & Status

### Get Health Status

```http
GET /api/health
```

**Response**:
```json
{
  "status": "ok"
}
```

### Get Version

```http
GET /api/version
```

**Response**:
```json
{
  "version": "0.1.0-alpha"
}
```

---

## Agents

### List All Agents

```http
GET /api/agents
```

**Response**:
```json
[
  ["agent_abc123", "DataAnalyzer"],
  ["agent_xyz789", "ReportGenerator"]
]
```

### Create Agent

```http
POST /api/agents
Content-Type: application/json

{
  "template_id": "tmpl.standard.worker",
  "name": "MyAgent",
  "description": "A custom agent for data analysis"
}
```

**Response**:
```json
{
  "id": "agent_abc123"
}
```

**Available Templates**:
- `tmpl.standard.worker` - Standard worker agent with MCP and A2A support

### Get Agent Details

```http
GET /api/agents/{agent_id}/detail
```

**Response**:
```json
{
  "id": "agent_abc123",
  "name": "DataAnalyzer",
  "description": "Analyzes data and generates insights",
  "role": "worker",
  "model": "claude-3-opus",
  "provider": "anthropic",
  "tags": ["standard", "worker"],
  "version": "1.0.0",
  "config": [
    ["protocol:mcp", "1.0"],
    ["protocol:a2a", "1.0"]
  ]
}
```

### Get Agent Compliance

```http
GET /api/agents/{agent_id}/compliance
```

**Response**:
```json
{
  "standard": "std.mcp.v1",
  "compliant": true,
  "missing_protocols": [],
  "missing_capabilities": [],
  "notes": []
}
```

### Delete Agent

```http
DELETE /api/agents/{agent_id}
```

**Response**:
```json
true
```

### Send Message to Agent

```http
POST /api/agents/{agent_id}/messages
Content-Type: application/json

{
  "content": "Analyze this data: Q1: 100, Q2: 150, Q3: 200"
}
```

**Response**:
```json
true
```

### Get Agent Message History

```http
GET /api/agents/{agent_id}/messages
```

**Response**:
```json
[
  {
    "ts": "2024-01-15T10:30:00Z",
    "from": "user",
    "to": "agent_abc123",
    "content": "Analyze this data..."
  },
  {
    "ts": "2024-01-15T10:30:05Z",
    "from": "agent_abc123",
    "to": "user",
    "content": "ANALYSIS RESULT..."
  }
]
```

---

## Agent Cards

Agent Cards are APQC-aligned workflow definitions that can be copied, versioned, templated, and archived.

### List Agent Cards

```http
GET /api/agent-cards
```

**Query Parameters**:
- `category` (optional): Filter by APQC category
- `search` (optional): Search in name/description

**Response**:
```json
{
  "total": 42,
  "cards": [
    {
      "apqc_id": "1.1.1",
      "apqc_name": "Develop Business Strategy",
      "filename": "apqc_1_1_1_develop_business_strategy.json"
    }
  ]
}
```

### Get Agent Card

```http
GET /api/agent-cards/{apqc_code}
```

**Response**: Full agent card JSON structure

### Copy Agent Card

```http
POST /api/agent-cards/{apqc_code}/copy
Content-Type: application/json

{
  "new_apqc_id": "1.1.1.custom",
  "new_name": "Custom Business Strategy"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Agent card copied successfully",
  "source_apqc_id": "1.1.1",
  "new_apqc_id": "1.1.1.custom",
  "new_name": "Custom Business Strategy",
  "filename": "apqc_1_1_1_custom_custom_business_strategy.json"
}
```

### Bulk Copy Agent Cards

```http
POST /api/agent-cards/bulk/copy
Content-Type: application/json

{
  "copies": [
    {
      "source_apqc_code": "1.1.1",
      "new_apqc_id": "1.1.1.v2",
      "new_name": "Strategy V2"
    },
    {
      "source_apqc_code": "1.1.2",
      "new_apqc_id": "1.1.2.v2",
      "new_name": "Planning V2"
    }
  ],
  "stop_on_error": false
}
```

**Response**:
```json
{
  "success": true,
  "total_requested": 2,
  "successful": 2,
  "failed": 0,
  "results": [
    {"source": "1.1.1", "new_apqc_id": "1.1.1.v2", "status": "success", "filename": "..."},
    {"source": "1.1.2", "new_apqc_id": "1.1.2.v2", "status": "success", "filename": "..."}
  ]
}
```

### Clone Agent Card with Modifications

```http
POST /api/agent-cards/{apqc_code}/clone
Content-Type: application/json

{
  "new_apqc_id": "1.1.1.modified",
  "new_name": "Modified Strategy",
  "modifications": {
    "description": "Updated description",
    "priority": "high"
  },
  "step_modifications": [
    {
      "step_index": 0,
      "task": "Updated first step task"
    }
  ]
}
```

**Response**:
```json
{
  "success": true,
  "message": "Agent card cloned with modifications",
  "source_apqc_id": "1.1.1",
  "new_apqc_id": "1.1.1.modified",
  "modifications_applied": ["description", "priority"],
  "filename": "apqc_1_1_1_modified_modified_strategy.json"
}
```

---

## Agent Card Versioning

Track and restore previous versions of agent cards.

### Create Version Snapshot

```http
POST /api/agent-cards/{apqc_code}/versions?description=Initial%20version
```

**Response**:
```json
{
  "success": true,
  "apqc_id": "1.1.1",
  "version": 1,
  "timestamp": "2024-01-15T10:30:00Z",
  "description": "Initial version"
}
```

### List Versions

```http
GET /api/agent-cards/{apqc_code}/versions
```

**Response**:
```json
{
  "apqc_id": "1.1.1",
  "total_versions": 3,
  "versions": [
    {"version": 1, "timestamp": "2024-01-15T10:30:00Z", "description": "Initial version"},
    {"version": 2, "timestamp": "2024-01-16T14:20:00Z", "description": "Added new steps"},
    {"version": 3, "timestamp": "2024-01-17T09:00:00Z", "description": "Bug fix"}
  ]
}
```

### Get Specific Version

```http
GET /api/agent-cards/{apqc_code}/versions/{version}
```

**Response**: Full version entry with snapshot

### Restore Version

```http
POST /api/agent-cards/{apqc_code}/versions/{version}/restore?create_backup=true
```

**Response**:
```json
{
  "success": true,
  "apqc_id": "1.1.1",
  "restored_to_version": 2,
  "backup_created": true
}
```

### Compare Versions

```http
GET /api/agent-cards/{apqc_code}/versions/{v1}/compare/{v2}
```

**Response**:
```json
{
  "apqc_id": "1.1.1",
  "version_1": 1,
  "version_2": 2,
  "timestamp_1": "2024-01-15T10:30:00Z",
  "timestamp_2": "2024-01-16T14:20:00Z",
  "total_differences": 5,
  "differences": [
    {"path": "description", "type": "modified", "old_value": "...", "new_value": "..."}
  ]
}
```

---

## Agent Card Templates

Create reusable templates from existing agent cards.

### Create Template from Card

```http
POST /api/agent-cards/{apqc_code}/template
Content-Type: application/json

{
  "template_name": "Strategy Template",
  "description": "Base template for strategy workflows",
  "category": "strategy",
  "tags": ["business", "planning", "strategy"]
}
```

**Response**:
```json
{
  "success": true,
  "template_id": "tpl_strategy_template",
  "template_name": "Strategy Template",
  "source_apqc_id": "1.1.1"
}
```

### List Templates

```http
GET /api/templates?category=strategy&tag=planning
```

**Response**:
```json
{
  "total": 5,
  "filters": {"category": "strategy", "tag": "planning"},
  "templates": [
    {
      "template_id": "tpl_strategy_template",
      "template_name": "Strategy Template",
      "description": "Base template for strategy workflows",
      "category": "strategy",
      "tags": ["business", "planning", "strategy"],
      "source_apqc_id": "1.1.1"
    }
  ]
}
```

### Get Template

```http
GET /api/templates/{template_id}
```

**Response**: Full template with card_template content

### Create Card from Template

```http
POST /api/templates/{template_id}/instantiate
Content-Type: application/json

{
  "apqc_id": "99.1.1",
  "apqc_name": "Custom Strategy Implementation",
  "overrides": {
    "description": "Custom implementation description"
  }
}
```

**Response**:
```json
{
  "success": true,
  "apqc_id": "99.1.1",
  "apqc_name": "Custom Strategy Implementation",
  "template_id": "tpl_strategy_template",
  "filename": "apqc_99_1_1_custom_strategy_implementat.json"
}
```

### Delete Template

```http
DELETE /api/templates/{template_id}
```

**Response**:
```json
{
  "success": true,
  "deleted_template": "tpl_strategy_template"
}
```

---

## Agent Card Comparison

Compare two different agent cards to see differences.

### Compare Two Cards

```http
GET /api/agent-cards/compare?apqc_code_1=1.1.1&apqc_code_2=1.1.2
```

**Response**:
```json
{
  "card_1": "1.1.1",
  "card_2": "1.1.2",
  "total_differences": 12,
  "differences": [
    {"path": "apqc_name", "type": "modified", "old_value": "...", "new_value": "..."},
    {"path": "agent_cards[0].task", "type": "modified", "old_value": "...", "new_value": "..."}
  ],
  "summary": {
    "added": 2,
    "removed": 1,
    "modified": 9
  }
}
```

---

## Agent Card Archive

Soft delete and restore agent cards.

### Archive Card

```http
POST /api/agent-cards/{apqc_code}/archive?reason=Deprecated%20workflow
```

**Response**:
```json
{
  "success": true,
  "apqc_id": "1.1.1",
  "archived_at": "2024-01-15T10:30:00Z",
  "reason": "Deprecated workflow"
}
```

### List Archived Cards

```http
GET /api/agent-cards/archived
```

**Response**:
```json
{
  "total": 3,
  "archived_cards": [
    {
      "apqc_id": "1.1.1",
      "apqc_name": "Old Strategy",
      "archived_at": "2024-01-15T10:30:00Z",
      "archive_reason": "Deprecated workflow",
      "filename": "apqc_1_1_1_old_strategy.json"
    }
  ]
}
```

### Restore Archived Card

```http
POST /api/agent-cards/archived/{apqc_code}/restore
```

**Response**:
```json
{
  "success": true,
  "apqc_id": "1.1.1",
  "restored_to": "apqc_1_1_1_old_strategy.json"
}
```

### Permanently Delete Archived Card

```http
DELETE /api/agent-cards/archived/{apqc_code}
```

**Response**:
```json
{
  "success": true,
  "apqc_id": "1.1.1",
  "permanently_deleted": true
}
```

---

## Workflows

### List Workflows

```http
GET /api/workflows
```

**Response**:
```json
[
  {
    "id": "wf-1234567890",
    "supervisor_id": "agent_sup123",
    "worker_ids": ["agent_w1", "agent_w2", "agent_w3"]
  }
]
```

### Create Workflow

```http
POST /api/workflows
Content-Type: application/json

{
  "supervisor": "SupervisorAgent",
  "n": 3,
  "template_id": "tmpl.standard.worker"
}
```

**Parameters**:
- `supervisor` (string): Name for the supervisor agent
- `n` (number): Number of worker agents to create
- `template_id` (string): Template ID for worker agents

**Response**:
```json
{
  "id": "wf-1234567890",
  "supervisor_id": "agent_sup123",
  "worker_ids": ["agent_w1", "agent_w2", "agent_w3"]
}
```

### Get Workflow Details

```http
GET /api/workflows/{workflow_id}
```

**Response**:
```json
{
  "id": "wf-1234567890",
  "supervisor_id": "agent_sup123",
  "worker_ids": ["agent_w1", "agent_w2", "agent_w3"]
}
```

---

## Protocols

### MCP (Model Context Protocol)

#### List Available Tools

```http
GET /api/protocols/mcp/{agent_id}/tools
```

**Response**:
```json
[
  {
    "name": "echo",
    "description": "Echo back input"
  },
  {
    "name": "reverse",
    "description": "Reverse input string"
  }
]
```

#### Invoke Tool

```http
POST /api/protocols/mcp/{agent_id}/invoke
Content-Type: application/json

{
  "tool": "echo",
  "input": "Hello World"
}
```

**Response**:
```json
{
  "tool": "echo",
  "input": "Hello World",
  "output": "Hello World"
}
```

### A2A (Agent-to-Agent Protocol)

#### Send Agent Message

```http
POST /api/protocols/a2a/send
Content-Type: application/json

{
  "from": "agent_abc123",
  "to": "agent_xyz789",
  "content": "Hello from Agent 1!"
}
```

**Response**:
```json
{
  "from": "agent_abc123",
  "to": "agent_xyz789",
  "content": "Hello from Agent 1!"
}
```

---

## Templates

### List Templates

```http
GET /api/templates
```

**Response**:
```json
[
  ["tmpl.standard.worker", "Standard Worker"]
]
```

### Get Template Details

```http
GET /api/templates/{template_id}
```

**Response**:
```json
"Standard Worker - Worker agent compliant with MCP and A2A (recommended)"
```

---

## Error Handling

### Error Response Format

All errors follow this format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_REQUEST` | 400 | Malformed request body or parameters |
| `NOT_FOUND` | 404 | Resource not found |
| `INTERNAL_ERROR` | 500 | Server error |
| `UNAUTHORIZED` | 401 | Authentication required |
| `RATE_LIMITED` | 429 | Too many requests |

### Example Error

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Agent with ID 'agent_xyz' not found",
    "details": {
      "agent_id": "agent_xyz"
    }
  }
}
```

---

## Rate Limiting

**Current Limits** (configurable):
- 100 requests per minute per IP
- 1000 requests per hour per IP

When rate limited, you'll receive:

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 60

{
  "error": {
    "code": "RATE_LIMITED",
    "message": "Rate limit exceeded. Please retry after 60 seconds."
  }
}
```

---

## WebSocket API (Coming Soon)

Real-time updates via WebSocket:

```javascript
const ws = new WebSocket('ws://localhost:8080/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Agent event:', data);
};

// Subscribe to agent events
ws.send(JSON.stringify({
  type: 'subscribe',
  agent_id: 'agent_abc123'
}));
```

**Event Types**:
- `agent.created`
- `agent.status_changed`
- `agent.task_completed`
- `workflow.started`
- `workflow.completed`
- `learning.event`

---

## Code Examples

### JavaScript/Node.js

```javascript
const axios = require('axios');

const BASE_URL = 'http://localhost:8080';

// Create an agent
async function createAgent() {
  const response = await axios.post(`${BASE_URL}/api/agents`, {
    template_id: 'tmpl.standard.worker',
    name: 'DataAnalyzer',
    description: 'Analyzes data'
  });
  return response.data.id;
}

// List agents
async function listAgents() {
  const response = await axios.get(`${BASE_URL}/api/agents`);
  return response.data;
}
```

### Python

```python
import requests

BASE_URL = 'http://localhost:8080'

# Create an agent
def create_agent():
    response = requests.post(
        f'{BASE_URL}/api/agents',
        json={
            'template_id': 'tmpl.standard.worker',
            'name': 'DataAnalyzer',
            'description': 'Analyzes data'
        }
    )
    return response.json()['id']

# List agents
def list_agents():
    response = requests.get(f'{BASE_URL}/api/agents')
    return response.json()
```

### cURL

```bash
# Create agent
curl -X POST http://localhost:8080/api/agents \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "tmpl.standard.worker",
    "name": "DataAnalyzer",
    "description": "Analyzes data"
  }'

# List agents
curl http://localhost:8080/api/agents

# Get agent details
curl http://localhost:8080/api/agents/{agent_id}/detail
```

---

## Pagination (Coming Soon)

For large result sets:

```http
GET /api/agents?page=1&limit=50
```

**Response** includes pagination metadata:
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 150,
    "total_pages": 3
  }
}
```

---

## Filtering & Sorting (Coming Soon)

```http
GET /api/agents?role=worker&tags=standard&sort=created_at:desc
```

---

## V2 API - Database-Backed Implementations

The V2 API provides persistent, database-backed implementations of all features. These endpoints should be used for production deployments.

**Base URL**: `http://localhost:8000/v2`

### V2 Status

```http
GET /v2/status
```

Returns status of all V2 implementations and database counts.

---

### AI Conversations (V2)

All conversation data is persisted to SQLite database.

#### Create Conversation

```http
POST /v2/ai/conversations
Content-Type: application/json

{
  "model": "gpt-4",
  "provider": "openai",
  "title": "Code Review Session",
  "system_prompt": "You are a helpful code reviewer."
}
```

#### List Conversations

```http
GET /v2/ai/conversations?status=active&provider=openai&limit=50
```

#### Get Conversation

```http
GET /v2/ai/conversations/{conversation_id}
```

#### Update Conversation

```http
PUT /v2/ai/conversations/{conversation_id}
Content-Type: application/json

{
  "title": "Updated Title",
  "status": "archived"
}
```

#### Delete Conversation

```http
DELETE /v2/ai/conversations/{conversation_id}
```

#### Send Message

```http
POST /v2/ai/conversations/{conversation_id}/messages
Content-Type: application/json

{
  "content": "Please review this code snippet..."
}
```

#### Get Messages

```http
GET /v2/ai/conversations/{conversation_id}/messages
```

---

### AI Usage Logging (V2)

Track token usage and costs across providers.

#### Log Usage

```http
POST /v2/ai/usage
Content-Type: application/json

{
  "provider": "openai",
  "model": "gpt-4",
  "prompt_tokens": 150,
  "completion_tokens": 200,
  "cost_cents": 5,
  "latency_ms": 1200
}
```

#### Get Usage Logs

```http
GET /v2/ai/usage?provider=openai&hours=24&limit=100
```

#### Get Usage Summary

```http
GET /v2/ai/usage/summary?days=30
```

---

### AI Provider Configuration (V2)

Manage AI provider settings and credentials.

#### List Providers

```http
GET /v2/ai/providers
```

#### Configure Provider

```http
POST /v2/ai/providers
Content-Type: application/json

{
  "provider": "openai",
  "display_name": "OpenAI GPT",
  "api_key": "sk-...",
  "default_model": "gpt-4",
  "enabled": true
}
```

#### Test Provider Connection

```http
POST /v2/ai/providers/{provider}/test
```

#### Delete Provider

```http
DELETE /v2/ai/providers/{provider}
```

---

### Execution Queue (V2)

Queue and track agent/workflow executions.

#### Queue Execution

```http
POST /v2/executions
Content-Type: application/json

{
  "agent_id": "agent_abc123",
  "input_data": {"task": "process data"},
  "priority": 5
}
```

#### List Executions

```http
GET /v2/executions?status=running&limit=50
```

#### Get Execution Status

```http
GET /v2/executions/{execution_id}
```

#### Cancel Execution

```http
PUT /v2/executions/{execution_id}/cancel
```

#### Update Progress

```http
PUT /v2/executions/{execution_id}/progress
Content-Type: application/json

{
  "progress": 75.5,
  "current_step": "Processing batch 3 of 4"
}
```

#### Get Execution History

```http
GET /v2/executions/history?status=completed&hours=24
```

#### Archive Execution

```http
POST /v2/executions/{execution_id}/archive
```

---

### Secrets Management (V2)

Encrypted secrets storage with Fernet (AES-128-CBC) encryption.

**Note**: Set `SECRETS_ENCRYPTION_KEY` environment variable for production!

#### Create Secret

```http
POST /v2/secrets
Content-Type: application/json

{
  "name": "API_KEY_SERVICE_X",
  "value": "secret-value-here",
  "secret_type": "api_key",
  "description": "API key for Service X",
  "expires_at": "2025-12-31T23:59:59Z",
  "allowed_agents": ["agent_abc123"]
}
```

#### List Secrets

```http
GET /v2/secrets?organization_id=1
```

**Note**: Values are never returned in list responses.

#### Get Secret Metadata

```http
GET /v2/secrets/{secret_id}
```

#### Reveal Secret Value

```http
POST /v2/secrets/{secret_id}/reveal
Content-Type: application/json

{
  "agent_id": "agent_abc123"
}
```

**Note**: Access is logged for audit purposes.

#### Update Secret

```http
PUT /v2/secrets/{secret_id}
Content-Type: application/json

{
  "value": "new-secret-value",
  "reason": "Scheduled rotation"
}
```

#### Rotate Secret

```http
POST /v2/secrets/{secret_id}/rotate
Content-Type: application/json

{
  "value": "rotated-secret-value",
  "reason": "Security policy rotation"
}
```

#### List Secret Versions

```http
GET /v2/secrets/{secret_id}/versions
```

#### Revoke Secret

```http
DELETE /v2/secrets/{secret_id}
```

#### Check Encryption Status

```http
GET /v2/secrets/encryption-status
```

Returns whether using development key or production key.

---

### Enterprise Operations (V2)

See the Enterprise tab in the dashboard for:
- Billing Management
- Quota Management
- Data Retention
- Backup/Restore
- SSO Configuration
- MFA Setup
- Security Policies
- Disaster Recovery

---

### Platform Operations (V2)

See the Operations tab in the dashboard for:
- Scheduled Jobs
- Event Management
- Notifications
- Audit Logs
- Feature Flags
- A/B Experiments
- Connectors
- Batch Processing

---

### Workflow Definitions (V2)

Manage reusable workflow definitions with step validation and versioning.

#### Create Workflow Definition

```http
POST /v2/workflow-definitions
Content-Type: application/json

{
  "name": "Invoice Processing",
  "description": "Automated invoice processing workflow",
  "steps": [
    {"step_id": "extract", "agent_id": "agent_001", "dependencies": []},
    {"step_id": "validate", "agent_id": "agent_002", "dependencies": ["extract"]},
    {"step_id": "approve", "agent_id": "agent_003", "dependencies": ["validate"]}
  ],
  "triggers": [{"type": "webhook", "config": {}}],
  "variables": {"threshold": 1000},
  "error_handling": {"retry_count": 3},
  "tags": ["finance", "automation"]
}
```

#### List Workflow Definitions

```http
GET /v2/workflow-definitions?tag=finance&status=active&limit=50
```

#### Get Workflow Definition

```http
GET /v2/workflow-definitions/{definition_id}
```

#### Update Workflow Definition

```http
PUT /v2/workflow-definitions/{definition_id}
Content-Type: application/json

{
  "name": "Updated Workflow Name",
  "steps": [...],
  "status": "active"
}
```

**Note**: Updates increment the version number automatically.

#### Clone Workflow Definition

```http
POST /v2/workflow-definitions/{definition_id}/clone
Content-Type: application/json

{
  "name": "Cloned Workflow",
  "tags": ["cloned"]
}
```

#### Archive Workflow Definition

```http
DELETE /v2/workflow-definitions/{definition_id}
```

**Note**: Soft delete - sets status to "archived".

---

### Test Suites (V2)

Manage test suites and test runs for agents and workflows.

#### Create Test Suite

```http
POST /v2/test-suites
Content-Type: application/json

{
  "name": "Invoice Processing Tests",
  "description": "Tests for the invoice processing workflow",
  "target_type": "workflow",
  "target_id": "wf_def_abc123",
  "test_cases": [
    {"name": "valid_invoice", "input": {...}, "expected_output": {...}},
    {"name": "invalid_amount", "input": {...}, "expected_output": {...}}
  ],
  "tags": ["finance", "critical"]
}
```

#### List Test Suites

```http
GET /v2/test-suites?target_type=workflow&status=active&limit=50
```

#### Get Test Suite

```http
GET /v2/test-suites/{suite_id}
```

#### Update Test Suite

```http
PUT /v2/test-suites/{suite_id}
Content-Type: application/json

{
  "name": "Updated Suite Name",
  "test_cases": [...]
}
```

#### Run Test Suite

```http
POST /v2/test-suites/{suite_id}/run
Content-Type: application/json

{
  "environment": "staging",
  "trigger_type": "manual"
}
```

#### List Test Runs

```http
GET /v2/test-runs?suite_id=suite_abc123&status=completed&limit=50
```

#### Get Test Run Details

```http
GET /v2/test-runs/{run_id}
```

#### Complete Test Run

```http
PUT /v2/test-runs/{run_id}/complete
Content-Type: application/json

{
  "status": "completed",
  "passed": 8,
  "failed": 2,
  "skipped": 0,
  "duration_ms": 5432,
  "test_results": [
    {"test_name": "valid_invoice", "status": "passed", "duration_ms": 234},
    {"test_name": "invalid_amount", "status": "failed", "error": "Expected error not thrown"}
  ],
  "summary": "8/10 tests passed"
}
```

---

### Marketplace (V2)

Manage marketplace listings for agents, workflows, and templates.

#### Create Listing

```http
POST /v2/marketplace/listings
Content-Type: application/json

{
  "organization_id": 1,
  "name": "Invoice Processor Agent",
  "description": "Automated invoice processing with ML extraction",
  "category": "finance",
  "listing_type": "agent",
  "resource_id": "agent_abc123",
  "pricing_model": "subscription",
  "price": 49.99,
  "tags": ["finance", "automation", "ml"]
}
```

#### List Published Listings

```http
GET /v2/marketplace/listings?category=finance
```

#### Get Listing Details

```http
GET /v2/marketplace/listings/{listing_id}
```

#### Update Listing

```http
PUT /v2/marketplace/listings/{listing_id}
Content-Type: application/json

{
  "name": "Updated Listing Name",
  "price": 59.99
}
```

#### Publish Listing

```http
PUT /v2/marketplace/listings/{listing_id}/publish
```

#### Unpublish Listing

```http
PUT /v2/marketplace/listings/{listing_id}/unpublish
```

#### Add Review

```http
POST /v2/marketplace/listings/{listing_id}/reviews
Content-Type: application/json

{
  "user_id": 1,
  "rating": 5,
  "title": "Excellent agent!",
  "review_text": "Saved us hours of manual work..."
}
```

---

### Health & Monitoring (V2)

Production-ready health checks and system metrics for monitoring and orchestration.

#### Comprehensive Health Check

```http
GET /v2/health
```

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "components": {
    "database": {
      "status": "healthy",
      "latency_ms": 2.5,
      "agent_count": 42,
      "workflow_count": 15
    },
    "encryption": {
      "status": "healthy",
      "algorithm": "Fernet (AES-128-CBC)"
    },
    "ai_providers": {
      "status": "healthy",
      "configured_count": 3,
      "providers": ["openai", "anthropic", "ollama"]
    },
    "memory": {
      "status": "healthy",
      "used_mb": 256.5,
      "available_mb": 1024.0,
      "percent_used": 25.0
    }
  },
  "version": "0.3.0-alpha"
}
```

#### Kubernetes Readiness Probe

```http
GET /v2/health/ready
```

Returns 200 if the service is ready to accept traffic, 503 if not ready.

**Response (healthy)**:
```json
{
  "ready": true,
  "checks": {
    "database": true,
    "encryption": true
  }
}
```

**Response (unhealthy)** - HTTP 503:
```json
{
  "ready": false,
  "checks": {
    "database": false,
    "encryption": true
  },
  "reason": "Database connection failed"
}
```

#### Kubernetes Liveness Probe

```http
GET /v2/health/live
```

Simple liveness check - returns 200 if the service is running.

**Response**:
```json
{
  "alive": true,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### System Metrics

```http
GET /v2/metrics
```

**Response**:
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "system": {
    "cpu_percent": 15.5,
    "memory_used_mb": 256.5,
    "memory_available_mb": 1024.0,
    "memory_percent": 25.0,
    "disk_used_gb": 50.2,
    "disk_free_gb": 200.8,
    "disk_percent": 20.0
  },
  "database": {
    "agents": 42,
    "workflows": 15,
    "conversations": 128,
    "executions_pending": 5,
    "executions_completed": 230,
    "test_suites": 12,
    "marketplace_listings": 45
  },
  "uptime_seconds": 86400.5
}
```

#### API Request Metrics

```http
GET /v2/metrics/api
```

**Response**:
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "requests": {
    "total": 15420,
    "by_method": {
      "GET": 12000,
      "POST": 2500,
      "PUT": 800,
      "DELETE": 120
    },
    "by_status": {
      "2xx": 14800,
      "4xx": 520,
      "5xx": 100
    }
  },
  "latency": {
    "avg_ms": 45.2,
    "p50_ms": 32.0,
    "p95_ms": 120.5,
    "p99_ms": 250.0
  },
  "errors": {
    "rate_percent": 4.02,
    "recent": [
      {
        "timestamp": "2024-01-15T10:29:55Z",
        "endpoint": "/v2/executions",
        "method": "POST",
        "status": 500,
        "message": "Execution timeout"
      }
    ]
  }
}
```

---

## Changelog

### v0.3.0-alpha (Current)
- **V2 Database-Backed API**: All critical data now persisted to SQLite
- **Health & Monitoring**: Production-ready health checks and metrics
  - Comprehensive health check with component status
  - Kubernetes-style readiness and liveness probes
  - System metrics (CPU, memory, disk)
  - API request metrics with latency percentiles
- **Dashboard Enhancements**:
  - V2 System Health & Metrics visualization in Metrics tab
  - AI Usage Analytics with provider cost tracking and token usage
  - AI Conversations browser with message history viewer
  - AI Provider Management (configure, test connections)
  - Workflow Definitions management (create, list, clone)
  - Marketplace listings management (create, browse, publish)
  - Data Export functionality (JSON export of agents, workflows, conversations)
  - Statistics Export (system metrics, AI usage, health status)
  - Testing tab with test suite management and system health
- AI Conversations with full CRUD and message history
- AI Usage Logging with provider analytics and cost tracking
- AI Provider Configuration with dynamic provider management
- Execution Queue with progress tracking, history, and cancellation
- Secrets Management with Fernet encryption (AES-128-CBC)
- Secret versioning and rotation support
- Audit logging for secret access
- Workflow Definitions with step validation and versioning
- Workflow cloning support
- Test Suites with test case management and run tracking
- Test Runs with detailed results and history
- Marketplace Listings with full CRUD, publish/unpublish, reviews
- Dashboard Execution Queue UI with real-time status
- Ollama local LLM provider support
- Added cryptography package for production encryption
- Silent exception handlers now properly log errors
- Fixed duplicate variable definition issues

### v0.2.0-alpha
- Agent Card management endpoints (copy, clone, CRUD)
- Bulk copy operations for agent cards
- Version tracking with snapshot/restore
- Template system for reusable card structures
- Diff comparison between cards and versions
- Archive/restore functionality for soft deletes

### v0.1.0-alpha
- Initial API release
- Basic agent CRUD operations
- Workflow creation
- MCP and A2A protocol support
- Simple message passing

### Upcoming Features
- WebSocket real-time updates
- Advanced filtering and search
- Agent execution API
- Learning insights endpoint
- Genome management API

---

## Support

- **Documentation**: [README.md](./README.md)
- **Quick Start**: [QUICKSTART.md](./QUICKSTART.md)
- **GitHub Issues**: [Report bugs](https://github.com/sillinous/multiAgentStandardsProtocol/issues)
- **Discussions**: [Community forum](https://github.com/sillinous/multiAgentStandardsProtocol/discussions)

---

**Built with ❤️ by the Sillinous team**
