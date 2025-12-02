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

## Changelog

### v0.2.0-alpha (Current)
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
