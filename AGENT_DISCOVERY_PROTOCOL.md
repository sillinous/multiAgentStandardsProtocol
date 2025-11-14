# 🔍 Agent Discovery Protocol (ADP)

## The Missing Piece of Multi-Agent Systems

The **Agent Discovery Protocol (ADP)** enables dynamic agent discovery in multi-agent ecosystems. Instead of hardcoded agent references, agents can discover each other by **capabilities**, **metadata**, and **performance characteristics**.

## 🎯 The Problem It Solves

Traditional multi-agent systems require:
- Hardcoded agent references
- Manual configuration of agent endpoints
- Static agent allocation
- No visibility into agent capabilities
- Duplicate agent creation
- Inefficient resource usage

**Agent Discovery Protocol solves all of these!**

## ✨ Key Features

### 1. **Capability-Based Discovery**
Find agents by what they can do, not by their name or ID.

```python
# Find all agents that can do data analysis
agents = await discovery.find_agents(
    required_capabilities=["data_analysis"]
)
```

### 2. **Rich Metadata Filtering**
Filter by cost, latency, quality, reputation, and custom tags.

```python
# Find cheap, fast, high-quality agents
agents = await discovery.find_agents(
    required_capabilities=["market_analysis"],
    filters={
        "cost_per_request": {"max": 0.20},
        "avg_latency_ms": {"max": 1000},
        "min_reputation": 0.85
    }
)
```

### 3. **Smart Agent Reuse**
Avoid duplicate agent creation by finding existing agents first.

```python
# Factory checks discovery before creating new agent
agent = await factory.find_or_create_agent(spec, reuse_existing=True)
```

### 4. **Status Tracking**
Monitor agent availability in real-time.

```python
# Update agent status
await discovery.update_status(agent_id, AgentStatus.BUSY)

# Find only available agents
agents = await discovery.find_agents(..., only_available=True)
```

### 5. **Performance-Based Selection**
Sort agents by reputation, cost, latency, or quality.

```python
# Get best agents first
agents = await discovery.find_agents(
    required_capabilities=["data_analysis"],
    sort_by="-reputation_score",  # - means descending
    limit=5
)
```

## 🏗️ Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                     Agent Ecosystem                            │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │ Agent A  │  │ Agent B  │  │ Agent C  │  │ Agent D  │     │
│  │ [data]   │  │ [market] │  │  [nlp]   │  │ [vision] │     │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘     │
│       │ register    │ register    │ register    │ register  │
│       └─────────────┼─────────────┼─────────────┘           │
└─────────────────────┼─────────────┼──────────────────────────┘
                      │             │
                      ▼             ▼
        ┌──────────────────────────────────────┐
        │   Agent Discovery Service (ADS)      │
        │                                       │
        │  ┌────────────────────────────────┐  │
        │  │  Agent Registry                │  │
        │  │  • agent_id → RegisteredAgent │  │
        │  └────────────────────────────────┘  │
        │                                       │
        │  ┌────────────────────────────────┐  │
        │  │  Capability Index               │  │
        │  │  • capability → Set[agent_ids] │  │
        │  └────────────────────────────────┘  │
        │                                       │
        │  ┌────────────────────────────────┐  │
        │  │  Type Index                     │  │
        │  │  • agent_type → Set[agent_ids] │  │
        │  └────────────────────────────────┘  │
        └───────────────┬──────────────────────┘
                        │
                        │ query
                        ▼
        ┌───────────────────────────────────────┐
        │  Agents Requesting Discovery          │
        │  • FactoryMetaAgent                   │
        │  • CoordinatorMetaAgent               │
        │  • Other agents                       │
        └───────────────────────────────────────┘
```

## 📦 Data Structures

### AgentCapability

```python
@dataclass
class AgentCapability:
    name: str                      # e.g., "data_analysis"
    version: str = "1.0.0"
    parameters: Dict[str, Any]
    description: str = ""
```

### AgentMetadata

```python
@dataclass
class AgentMetadata:
    # Performance
    avg_latency_ms: Optional[float]
    avg_quality_score: Optional[float]
    success_rate: Optional[float]

    # Cost
    cost_per_request: Optional[float]
    cost_currency: str = "USD"
    cost_model: str = "per_request"

    # Capacity
    max_concurrent_tasks: int = 10
    current_load: int = 0

    # Reputation
    reputation_score: Optional[float]
    total_tasks_completed: int = 0

    # Additional
    tags: List[str]
    custom: Dict[str, Any]
```

### RegisteredAgent

```python
@dataclass
class RegisteredAgent:
    agent_id: str
    name: str
    agent_type: str
    capabilities: List[AgentCapability]
    metadata: AgentMetadata
    status: AgentStatus
    registered_at: str
    last_heartbeat: str
    endpoint: Optional[str]
    version: str = "1.0.0"
```

### AgentStatus

```python
class AgentStatus(Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    FAILED = "failed"
```

## 🚀 Usage Guide

### 1. Start Discovery Service

```python
from src.superstandard.protocols.discovery import get_discovery_service

discovery = get_discovery_service()
await discovery.start()
```

### 2. Register Agents

```python
from src.superstandard.protocols.discovery import (
    AgentCapability,
    AgentMetadata
)

await discovery.register_agent(
    agent_id="agent-001",
    name="DataAnalysisAgent",
    agent_type="data_analyst",
    capabilities=[
        AgentCapability("data_analysis", "1.0.0", {}, "Statistical analysis"),
        AgentCapability("visualization", "1.0.0", {}, "Data visualization")
    ],
    metadata=AgentMetadata(
        avg_latency_ms=450.0,
        avg_quality_score=0.95,
        success_rate=0.98,
        cost_per_request=0.15,
        reputation_score=0.92,
        tags=["premium", "fast"]
    )
)
```

### 3. Find Agents by Capability

```python
# Simple capability search
agents = await discovery.find_agents(
    required_capabilities=["data_analysis"]
)

# Multiple capabilities (AND operation)
agents = await discovery.find_agents(
    required_capabilities=["market_analysis", "competitor_analysis"]
)

# With filters
agents = await discovery.find_agents(
    required_capabilities=["data_analysis"],
    filters={
        "cost_per_request": {"max": 0.20},
        "min_reputation": 0.85,
        "tags": ["premium"]
    }
)

# Sorted results
agents = await discovery.find_agents(
    required_capabilities=["data_analysis"],
    sort_by="-reputation_score",  # Best reputation first
    limit=5
)
```

### 4. Advanced Filtering

```python
# By cost range
agents = await discovery.find_agents(
    filters={
        "cost_per_request": {"min": 0.05, "max": 0.20}
    }
)

# By latency
agents = await discovery.find_agents(
    filters={
        "avg_latency_ms": {"max": 1000}  # Under 1 second
    }
)

# By reputation
agents = await discovery.find_agents(
    filters={
        "min_reputation": 0.90  # 90% or higher
    }
)

# By success rate
agents = await discovery.find_agents(
    filters={
        "min_success_rate": 0.95  # 95% or higher
    }
)

# By status
agents = await discovery.find_agents(
    filters={
        "status": ["available", "busy"]
    }
)

# By tags (AND operation)
agents = await discovery.find_agents(
    filters={
        "tags": ["premium", "fast"]  # Must have BOTH tags
    }
)

# By agent type
agents = await discovery.find_agents(
    filters={
        "agent_type": "data_analyst"
    }
)

# Combine multiple filters
agents = await discovery.find_agents(
    required_capabilities=["data_analysis"],
    filters={
        "cost_per_request": {"max": 0.15},
        "avg_latency_ms": {"max": 500},
        "min_reputation": 0.90,
        "tags": ["premium"]
    },
    sort_by="-reputation_score",
    limit=3
)
```

### 5. Update Agent Status

```python
# Mark agent as busy
await discovery.update_status(agent_id, AgentStatus.BUSY)

# Mark agent as available
await discovery.update_status(agent_id, AgentStatus.AVAILABLE)

# Mark agent as offline
await discovery.update_status(agent_id, AgentStatus.OFFLINE)
```

### 6. Update Agent Metadata

```python
await discovery.update_metadata(
    agent_id,
    {
        "avg_latency_ms": 420.0,
        "reputation_score": 0.94,
        "total_tasks_completed": 1523
    }
)
```

### 7. Heartbeat

```python
# Send periodic heartbeat to keep agent alive
await discovery.heartbeat(agent_id)
```

### 8. Integration with FactoryMetaAgent

```python
from src.superstandard.meta_agents.factory import FactoryMetaAgent, AgentSpec

factory = FactoryMetaAgent(bus, discovery)

spec = AgentSpec(
    agent_type="data_analyst",
    name="DataAnalysisAgent",
    capabilities=["data_analysis"],
    configuration={"model": "advanced"},
    description="Advanced data analysis"
)

# Smart method: Find existing or create new
agent = await factory.find_or_create_agent(
    spec,
    reuse_existing=True  # Check discovery first!
)
```

### 9. Discovery Statistics

```python
stats = await discovery.get_stats()
print(f"Total registrations: {stats['total_registrations']}")
print(f"Active agents: {stats['active_agents']}")
print(f"Total discoveries: {stats['total_discoveries']}")

# List all capabilities
capabilities = await discovery.list_capabilities()

# List all agent types
types = await discovery.list_agent_types()
```

### 10. Unregister Agent

```python
await discovery.unregister_agent(agent_id)
```

## 📊 Filter Reference

| Filter Key | Type | Example | Description |
|------------|------|---------|-------------|
| `cost_per_request` | `float` or `{"min": float, "max": float}` | `{"max": 0.20}` | Cost per request in USD |
| `avg_latency_ms` | `float` or `{"min": float, "max": float}` | `{"max": 1000}` | Average response time |
| `min_reputation` | `float` | `0.90` | Minimum reputation score (0-1) |
| `min_success_rate` | `float` | `0.95` | Minimum success rate (0-1) |
| `status` | `str` or `List[str]` | `["available", "busy"]` | Agent status |
| `tags` | `str` or `List[str]` | `["premium", "fast"]` | Agent tags (AND) |
| `agent_type` | `str` | `"data_analyst"` | Agent type filter |

## 🎨 Sort Options

| Sort Key | Direction | Example | Description |
|----------|-----------|---------|-------------|
| `reputation_score` | `asc` / `-desc` | `"-reputation_score"` | Sort by reputation |
| `cost_per_request` | `asc` / `-desc` | `"cost_per_request"` | Sort by cost (cheapest first) |
| `avg_latency_ms` | `asc` / `-desc` | `"avg_latency_ms"` | Sort by latency (fastest first) |
| `success_rate` | `asc` / `-desc` | `"-success_rate"` | Sort by success rate |

**Note**: Prefix with `-` for descending order (e.g., `-reputation_score` for highest reputation first)

## 🔧 Configuration

### Heartbeat Timeout

```python
discovery = AgentDiscoveryService(
    heartbeat_timeout_seconds=60  # Mark offline after 60s
)
```

Agents missing heartbeats for longer than this duration are automatically marked as `OFFLINE`.

## 📈 Performance Characteristics

| Operation | Time Complexity | Description |
|-----------|----------------|-------------|
| Register agent | O(c) | c = number of capabilities |
| Unregister agent | O(c) | c = number of capabilities |
| Find by capability | O(n) | n = matching agents |
| Find with filters | O(n*f) | n = agents, f = filters |
| Update status | O(1) | Direct dictionary access |
| Heartbeat | O(1) | Direct dictionary access |

**Memory Usage**: ~1KB per registered agent

## 🎯 Use Cases

### 1. **Cost-Optimized Agent Selection**

```python
# Find cheapest agent that meets requirements
agents = await discovery.find_agents(
    required_capabilities=["data_analysis"],
    filters={"min_reputation": 0.80},
    sort_by="cost_per_request",
    limit=1
)
```

### 2. **Performance-Optimized Selection**

```python
# Find fastest high-quality agent
agents = await discovery.find_agents(
    required_capabilities=["nlp"],
    filters={"min_success_rate": 0.95},
    sort_by="avg_latency_ms",
    limit=1
)
```

### 3. **Load Balancing**

```python
# Find available agents with capacity
agents = await discovery.find_agents(
    required_capabilities=["market_analysis"],
    only_available=True
)

# Select agent with lowest current load
selected = min(agents, key=lambda a: a.metadata.current_load)
```

### 4. **Agent Marketplace**

```python
# List all agents with pricing
all_agents = await discovery.find_agents(
    filters={},
    sort_by="cost_per_request",
    only_available=False
)

for agent in all_agents:
    print(f"{agent.name}: ${agent.metadata.cost_per_request}/request")
```

### 5. **Dynamic Team Formation**

```python
# Assemble team with complementary skills
team = []

# Find data analyst
team.append(await discovery.find_agents(
    required_capabilities=["data_analysis"],
    filters={"min_reputation": 0.85},
    limit=1
)[0])

# Find market researcher
team.append(await discovery.find_agents(
    required_capabilities=["market_analysis"],
    filters={"min_reputation": 0.85},
    limit=1
)[0])

# Find NLP specialist
team.append(await discovery.find_agents(
    required_capabilities=["text_analysis"],
    filters={"min_reputation": 0.85},
    limit=1
)[0])
```

## 🚨 Troubleshooting

### Issue: No agents found

**Cause**: No agents match the criteria
**Solution**: Relax filters or check agent registration

```python
# Check what capabilities are available
caps = await discovery.list_capabilities()
print(f"Available capabilities: {caps}")
```

### Issue: Agent marked offline unexpectedly

**Cause**: Missing heartbeats
**Solution**: Implement periodic heartbeat

```python
# Send heartbeat every 30 seconds
while True:
    await discovery.heartbeat(agent_id)
    await asyncio.sleep(30)
```

### Issue: Duplicate agents created

**Cause**: Not using find_or_create pattern
**Solution**: Use factory's smart reuse

```python
# Use this instead of create_agent directly
agent = await factory.find_or_create_agent(spec, reuse_existing=True)
```

## 🌟 Best Practices

### 1. **Always Use find_or_create**

```python
# ✅ Good: Check discovery first
agent = await factory.find_or_create_agent(spec, reuse_existing=True)

# ❌ Bad: Always create new
agent = await factory.create_agent(spec)
```

### 2. **Register Rich Metadata**

```python
# ✅ Good: Rich metadata enables smart filtering
metadata = AgentMetadata(
    avg_latency_ms=450.0,
    avg_quality_score=0.95,
    success_rate=0.98,
    cost_per_request=0.15,
    reputation_score=0.92,
    tags=["premium", "fast", "accurate"]
)

# ❌ Bad: Empty metadata limits discovery
metadata = AgentMetadata()
```

### 3. **Implement Heartbeats**

```python
# ✅ Good: Keep agent alive
async def heartbeat_loop(agent_id):
    while True:
        await discovery.heartbeat(agent_id)
        await asyncio.sleep(30)

# ❌ Bad: No heartbeat, agent marked offline
```

### 4. **Update Metadata Regularly**

```python
# ✅ Good: Keep metrics current
await discovery.update_metadata(agent_id, {
    "avg_latency_ms": new_latency,
    "total_tasks_completed": task_count
})

# ❌ Bad: Stale metadata leads to suboptimal selection
```

### 5. **Use Appropriate Filters**

```python
# ✅ Good: Balanced filtering
agents = await discovery.find_agents(
    required_capabilities=["data_analysis"],
    filters={
        "cost_per_request": {"max": 0.25},
        "min_reputation": 0.80
    }
)

# ❌ Bad: Too restrictive (may find nothing)
agents = await discovery.find_agents(
    required_capabilities=["data_analysis"],
    filters={
        "cost_per_request": {"max": 0.01},  # Unrealistic
        "min_reputation": 0.99  # Too high
    }
)
```

## 🔮 Future Enhancements

Planned features for Agent Discovery Protocol:
1. **Distributed Discovery** - Multiple discovery services with sync
2. **Capability Versioning** - Semantic versioning for capabilities
3. **Agent Health Checks** - Active health monitoring
4. **Performance History** - Trend analysis for reputation
5. **Agent Recommendations** - ML-powered agent selection
6. **Cost Prediction** - Estimate cost before execution
7. **Load Prediction** - Forecast agent availability
8. **Federation** - Cross-platform agent discovery

## 📚 Related Documentation

- [Main README](README.md) - Platform overview
- [A2A Protocol](A2A_PROTOCOL_META_AGENTS.md) - Agent communication
- [Architecture](ARCHITECTURE.md) - System architecture
- [Getting Started](GETTING_STARTED.md) - Quick start guide

---

**The Agent Discovery Protocol is THE MISSING PIECE that makes multi-agent systems truly dynamic and scalable!** 🚀

No more hardcoded references. No more duplicate agents. Just pure, dynamic, capability-based discovery.
