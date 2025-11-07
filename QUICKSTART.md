# SuperStandard Platform - Quick Start Guide

## 🚀 Get Up and Running in 5 Minutes

This guide will have you running the complete SuperStandard Multi-Agent Platform with real-time dashboards in just a few commands.

---

## Prerequisites

- Python 3.8+
- pip
- Modern web browser (Chrome, Firefox, Edge, Safari)

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/sillinous/multiAgentStandardsProtocol.git
cd multiAgentStandardsProtocol
```

### 2. Install Dependencies

```bash
# Install API server dependencies
pip install -r requirements-api.txt

# Install protocol dependencies (if not already installed)
pip install -r requirements.txt
```

---

## Running the Platform

### Option 1: Automated Live Demo (Recommended)

This is the **easiest way** to see everything working together!

**Step 1**: Start the API server in one terminal:

```bash
python -m uvicorn src.superstandard.api.server:app --reload --port 8080
```

You should see:

```
============================================================================
SuperStandard Multi-Agent Platform API Server
================================================================================

🚀 Server starting...
   Start time: 2025-01-06T...

📡 Protocols initialized:
   ✅ ANP (Agent Network Protocol)
   ✅ ACP (Agent Coordination Protocol)
   ✅ AConsP (Agent Consciousness Protocol)

🌐 Dashboards available at:
   - http://localhost:8080/dashboard/user
   - http://localhost:8080/dashboard/admin
   - http://localhost:8080/dashboard/network
   - http://localhost:8080/dashboard/coordination
   - http://localhost:8080/dashboard/consciousness

================================================================================
```

**Step 2**: In a **new terminal**, run the live demo:

```bash
python examples/live_platform_demo.py
```

The demo will:
- ✅ Register 6 specialized agents
- ✅ Create coordination sessions
- ✅ Submit thoughts to collective consciousness
- ✅ Discover emergent patterns
- ✅ **Auto-open all dashboards in your browser**
- ✅ Show real-time updates!

**Step 3**: Watch the magic happen! 🎉

The dashboards will display **real-time data** as the demo executes.

---

### Option 2: Manual Exploration

**Start the server**:

```bash
python -m uvicorn src.superstandard.api.server:app --reload --port 8080
```

**Open dashboards** in your browser:

- **User Panel**: http://localhost:8080/dashboard/user
- **Admin Dashboard**: http://localhost:8080/dashboard/admin
- **Network Topology**: http://localhost:8080/dashboard/network
- **Coordination**: http://localhost:8080/dashboard/coordination
- **Consciousness**: http://localhost:8080/dashboard/consciousness

**Interact via API**:

```bash
# Register an agent
curl -X POST http://localhost:8080/api/anp/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "my_agent_001",
    "agent_type": "analyst",
    "capabilities": ["analysis", "processing"],
    "endpoints": {"http": "http://localhost:9000"}
  }'

# Create a coordination session
curl -X POST http://localhost:8080/api/acp/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My First Session",
    "coordination_type": "pipeline",
    "description": "Testing the platform"
  }'

# Submit a thought
curl -X POST http://localhost:8080/api/aconsp/collectives/main/thoughts \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "my_agent_001",
    "thought_type": "insight",
    "content": "This platform is amazing!",
    "confidence": 0.95
  }'
```

---

## Dashboard Overview

### 🎛️ **User Control Panel** (`/dashboard/user`)

**What it does**: User-friendly interface for common operations

**Features**:
- Quick actions (register agent, create session, join collective)
- Protocol overview cards
- Recent activity feed
- Modal forms for easy input

**Use when**: You want to perform simple operations without code

---

### 📊 **Admin Dashboard** (`/dashboard/admin`)

**What it does**: Single-pane-of-glass system overview

**Features**:
- System health indicator
- Stats for all 3 protocols (ANP, ACP, AConsP)
- Quick action buttons
- Real-time activity feed

**Use when**: You need high-level system monitoring

---

### 🌐 **Network Topology Dashboard** (`/dashboard/network`)

**What it does**: Visualize agent network in real-time

**Features**:
- **Live force-directed graph** with physics simulation
- Agent discovery query builder
- Registered agents list with health status
- Network statistics

**Use when**: You want to see agent relationships and network health

---

### 🤝 **Coordination Dashboard** (`/dashboard/coordination`)

**What it does**: Manage multi-agent coordination sessions

**Features**:
- Active sessions grid with progress bars
- Global task queue with priorities
- Session participants view
- Workflow visualization canvas

**Use when**: You're orchestrating complex multi-agent workflows

---

### 🧠 **Consciousness Dashboard** (`/dashboard/consciousness`)

**What it does**: Monitor collective intelligence emergence

**Features**:
- Thought entanglement graph
- Real-time thought stream
- Pattern discovery visualization
- Collective awareness metrics

**Use when**: You want to see emergent intelligence in action

---

## Example Scenarios

### Scenario 1: Supply Chain Optimization

**Goal**: Use multiple agents to optimize a supply chain

```bash
# Start server
python -m uvicorn src.superstandard.api.server:app --reload --port 8080

# Run the live demo (includes supply chain scenario)
python examples/live_platform_demo.py
```

**What happens**:
1. 6 specialized agents register (analyst, optimizer, inventory manager, etc.)
2. Pipeline coordination session created
3. 5 tasks added (analysis, forecasting, optimization, planning, cost analysis)
4. Agents contribute insights to collective consciousness
5. Emergent patterns discovered (e.g., "40% cost reduction with 5% longer lead times")

---

### Scenario 2: Multi-Agent Data Analysis

**Manual approach**:

```python
import requests

API = "http://localhost:8080"

# Register analyst agents
for i in range(3):
    requests.post(f"{API}/api/anp/agents/register", json={
        "agent_id": f"analyst_{i+1}",
        "agent_type": "analyst",
        "capabilities": ["data_analysis", "statistics"]
    })

# Create swarm session
response = requests.post(f"{API}/api/acp/sessions", json={
    "name": "Data Analysis Swarm",
    "coordination_type": "swarm"
})
session_id = response.json()["session_id"]

# Add parallel analysis tasks
for dataset in ["customers", "products", "transactions"]:
    requests.post(f"{API}/api/acp/sessions/{session_id}/tasks", json={
        "task_type": "analysis",
        "description": f"Analyze {dataset} dataset",
        "priority": 10
    })

# Agents contribute findings to collective
requests.post(f"{API}/api/aconsp/collectives/analytics/thoughts", json={
    "agent_id": "analyst_1",
    "thought_type": "insight",
    "content": "Customer churn correlates with product quality scores",
    "confidence": 0.87
})

# Query for emergent patterns
response = requests.post(
    f"{API}/api/aconsp/collectives/analytics/query",
    json={
        "query": "What patterns emerged from the analysis?",
        "min_coherence": 0.6
    }
)

patterns = response.json()["patterns"]
print(f"Discovered {len(patterns)} patterns!")
```

---

## API Documentation

### Interactive API Docs

FastAPI provides **automatic interactive documentation**:

- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc

These allow you to:
- ✅ See all available endpoints
- ✅ Try API calls directly in browser
- ✅ See request/response schemas
- ✅ Test authentication

---

### Quick API Reference

#### ANP Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/anp/agents/register` | Register agent on network |
| POST | `/api/anp/agents/discover` | Discover agents by criteria |
| GET | `/api/anp/agents` | List all agents |
| POST | `/api/anp/agents/{id}/heartbeat` | Send heartbeat |
| GET | `/api/anp/stats` | Network statistics |

#### ACP Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/acp/sessions` | Create coordination session |
| GET | `/api/acp/sessions` | List all sessions |
| POST | `/api/acp/sessions/{id}/tasks` | Add task to session |
| GET | `/api/acp/sessions/{id}/tasks` | List session tasks |
| GET | `/api/acp/stats` | Coordination statistics |

#### AConsP Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/aconsp/collectives/{id}/thoughts` | Submit thought |
| POST | `/api/aconsp/collectives/{id}/query` | Query for patterns |
| GET | `/api/aconsp/collectives/{id}/state` | Get collective state |
| GET | `/api/aconsp/stats` | Consciousness statistics |

#### Admin Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/stats` | Complete system stats |
| GET | `/api/health` | Health check |

#### WebSocket Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/ws/admin` | Admin dashboard updates |
| `/ws/network` | Network topology updates |
| `/ws/coordination` | Session updates |
| `/ws/consciousness` | Consciousness stream |

---

## WebSocket Example

```javascript
// Connect to consciousness stream
const ws = new WebSocket('ws://localhost:8080/ws/consciousness');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Event:', data.type);

    if (data.type === 'thought_contributed') {
        console.log(`${data.agent_id} thought: ${data.content}`);
    }
};

ws.onopen = () => {
    console.log('Connected to consciousness stream!');
};
```

---

## Troubleshooting

### Server won't start

**Error**: `ModuleNotFoundError: No module named 'fastapi'`

**Fix**: Install dependencies

```bash
pip install -r requirements-api.txt
```

---

### Port already in use

**Error**: `OSError: [Errno 48] Address already in use`

**Fix**: Use a different port

```bash
python -m uvicorn src.superstandard.api.server:app --reload --port 8081
```

(Update API calls to use port 8081)

---

### Dashboards not loading

**Issue**: Blank page or 404 error

**Fix**: Check server is running and file paths are correct

```bash
# Verify server is running
curl http://localhost:8080/api/health

# Should return: {"status":"healthy",...}
```

---

### Demo script can't connect

**Error**: `Server not responding`

**Fix**: Make sure API server is running FIRST

```bash
# Terminal 1: Start server
python -m uvicorn src.superstandard.api.server:app --reload --port 8080

# Terminal 2: Run demo (wait for server to start)
python examples/live_platform_demo.py
```

---

## Next Steps

### 1. Explore the Dashboards

Open each dashboard and explore the features:
- Use discovery queries in Network dashboard
- Create sessions in Coordination dashboard
- Submit thoughts in Consciousness dashboard

### 2. Run the Consciousness Demo

```bash
python examples/consciousness_demo.py
```

Demonstrates the consciousness protocol in isolation.

### 3. Read the Documentation

- `UNIFIED_PLATFORM_COMPLETE.md` - Complete platform overview
- `UI_SUITE_COMPLETE.md` - Dashboard documentation
- `FINAL_DELIVERY.md` - Project summary

### 4. Build Your Own Agents

Create a custom agent using the mixins:

```python
from superstandard.agents.base.base_agent import BaseAgent
from superstandard.agents.base.network_mixin import NetworkAwareMixin
from superstandard.agents.base.coordination_mixin import CoordinationMixin
from superstandard.agents.base.consciousness_mixin import ConsciousnessMixin

class MyCustomAgent(NetworkAwareMixin, CoordinationMixin, ConsciousnessMixin, BaseAgent):
    async def execute_task(self, task):
        # Your custom logic here
        result = await self.process(task)

        # Share insight with collective
        await self.think(
            ThoughtType.INSIGHT,
            f"Completed {task['type']}: {result}",
            confidence=0.9
        )

        return result
```

### 5. Integrate with Your Systems

The API is RESTful and can be called from any language:

```bash
# Python
import requests

# JavaScript/Node.js
fetch('http://localhost:8080/api/...')

# curl
curl -X POST http://localhost:8080/api/...

# Any HTTP client!
```

---

## Support & Community

- **Issues**: https://github.com/sillinous/multiAgentStandardsProtocol/issues
- **Documentation**: See `docs/` directory
- **Examples**: See `examples/` directory

---

## What's Included

✅ **3 Complete Protocols** (ANP, ACP, AConsP)
✅ **Production API Server** (FastAPI + WebSocket)
✅ **5 Beautiful Dashboards** (Real-time monitoring)
✅ **Automated Demo** (Supply chain scenario)
✅ **Comprehensive Documentation**
✅ **Example Code** (Multiple scenarios)

---

## Summary

You now have a **complete, production-ready multi-agent platform** with:

1. **Agent Network Protocol (ANP)** - Agent discovery and health
2. **Agent Coordination Protocol (ACP)** - Multi-agent orchestration
3. **Agent Consciousness Protocol (AConsP)** - Collective intelligence
4. **REST API** - Full programmatic access
5. **WebSocket Streaming** - Real-time updates
6. **Beautiful Dashboards** - Visual monitoring
7. **Live Demo** - Automated showcase

**The platform is ready for production deployment!** 🚀

---

**Last Updated**: 2025-01-06
**Version**: 1.0.0
**Status**: ✅ Production Ready
