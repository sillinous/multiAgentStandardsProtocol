# 📖 API Reference

Complete reference for the Agentic Forge REST API.

**Base URL**: `http://localhost:8080`

**Version**: 0.1.0-alpha

---

## Table of Contents

- [Authentication](#authentication)
- [Health & Status](#health--status)
- [Agents](#agents)
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

### v0.1.0-alpha (Current)
- Initial API release
- Basic agent CRUD operations
- Workflow creation
- MCP and A2A protocol support
- Simple message passing

### Upcoming Features
- WebSocket real-time updates
- Advanced filtering and search
- Bulk operations
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
