# Resource Allocation Protocol (RAP) 💰

## Overview

The **Resource Allocation Protocol (RAP)** is the production safety layer for multi-agent systems. It prevents runaway costs, enforces spending limits, and ensures fair resource distribution across all agents in the ecosystem.

**THIS IS CRITICAL FOR PRODUCTION DEPLOYMENTS!**

## Why RAP Matters

Without RAP:
- ❌ Autonomous agents can exhaust budgets
- ❌ No visibility into cost per agent
- ❌ API quotas easily exceeded
- ❌ Resource hogging by individual agents
- ❌ Unpredictable operational costs

With RAP:
- ✅ Hard budget caps prevent cost explosions
- ✅ Complete cost tracking per agent/task
- ✅ API quota enforcement
- ✅ Fair resource distribution
- ✅ Predictable, controlled costs
- ✅ Production-ready safety layer

## Core Concepts

### Resource Types

RAP manages six types of resources:

```python
class ResourceType(Enum):
    API_CALLS = "api_calls"              # Number of API calls
    BUDGET_USD = "budget_usd"            # Monetary budget
    COMPUTE_SECONDS = "compute_seconds"  # CPU time
    MEMORY_MB = "memory_mb"              # Memory usage
    STORAGE_GB = "storage_gb"            # Storage quota
    CONCURRENT_TASKS = "concurrent_tasks" # Parallel execution
```

### Allocation Statuses

```python
class AllocationStatus(Enum):
    PENDING = "pending"       # Awaiting approval
    APPROVED = "approved"     # Approved but not active
    ACTIVE = "active"         # Currently in use
    EXHAUSTED = "exhausted"   # Quota exceeded
    EXPIRED = "expired"       # Time limit reached
    REVOKED = "revoked"       # Manually cancelled
```

### Resource Quotas

Define limits for each resource type:

```python
@dataclass
class ResourceQuota:
    resource_type: ResourceType
    limit: float              # Maximum allowed
    period_seconds: int       # Time window (default: 1 hour)
    description: str          # Human-readable description
```

## Basic Usage

### 1. Request Resource Allocation

```python
from src.superstandard.protocols.resources import get_resource_service, ResourceType, ResourceQuota

resources = get_resource_service()

# Request allocation
allocation = await resources.request_allocation(
    agent_id="agent-123",
    quotas={
        ResourceType.API_CALLS.value: ResourceQuota(
            ResourceType.API_CALLS,
            limit=1000,
            description="API quota"
        ),
        ResourceType.BUDGET_USD.value: ResourceQuota(
            ResourceType.BUDGET_USD,
            limit=10.00,
            description="Budget quota"
        )
    },
    priority=5,           # 1-10 scale
    duration_hours=24,    # Allocation valid for 24 hours
    auto_approve=True     # Automatically approve
)

print(f"Allocation ID: {allocation.allocation_id}")
print(f"Status: {allocation.status.value}")
```

### 2. Activate Allocation

```python
# Activate to start using resources
await resources.activate_allocation("agent-123")
```

### 3. Record Resource Usage

```python
# Record usage (auto-checks quotas!)
usage_record = await resources.record_usage(
    agent_id="agent-123",
    api_calls=45,
    cost_usd=4.50,
    compute_seconds=120.5,
    task_id="task-456",
    metadata={"operation": "data_analysis"}
)
```

### 4. Check Budget Status

```python
# Check if budget exceeded
if await resources.is_budget_exceeded("agent-123"):
    raise BudgetExceededError("Stop execution!")

# Get remaining budget
remaining = await resources.get_remaining_budget("agent-123")
print(f"Remaining: ${remaining:.2f}")
```

### 5. Get Usage Summary

```python
summary = await resources.get_usage_summary("agent-123")

print(f"API Calls: {summary['usage']['api_calls']['used']}/{summary['usage']['api_calls']['limit']}")
print(f"Budget: ${summary['usage']['budget_usd']['used']:.2f}/${summary['usage']['budget_usd']['limit']:.2f}")
print(f"Remaining: ${summary['usage']['budget_usd']['remaining']:.2f}")
```

## Advanced Features

### Priority-Based Allocation

Agents can have different priority levels (1-10, higher = more priority):

```python
# High-priority agent
await resources.request_allocation(
    agent_id="agent-critical",
    priority=9  # High priority
)

# Low-priority agent
await resources.request_allocation(
    agent_id="agent-background",
    priority=3  # Low priority
)
```

**Note**: Future schedulers can use priority to allocate resources preferentially.

### Quota Management

```python
# Check specific quota
is_exceeded = await resources.is_quota_exceeded(
    agent_id="agent-123",
    resource_type=ResourceType.API_CALLS
)

# Get allocation details
allocation = await resources.get_allocation("agent-123")
usage_percent = allocation.get_usage_percent(ResourceType.BUDGET_USD)
print(f"Budget usage: {usage_percent:.1f}%")
```

### Allocation Lifecycle

```python
# Extend allocation time
allocation = await resources.extend_allocation(
    agent_id="agent-123",
    additional_hours=12  # Add 12 more hours
)

# Revoke allocation
await resources.revoke_allocation(
    agent_id="agent-123",
    reason="Policy violation"
)
```

### Analytics

```python
# Get top consumers
top_consumers = await resources.get_top_consumers(limit=10)

for consumer in top_consumers:
    print(f"{consumer['agent_id']}: ${consumer['total_cost_usd']:.2f}")

# Service statistics
stats = await resources.get_stats()
print(f"Total Cost: ${stats['total_cost_usd']:.2f}")
print(f"Active Allocations: {stats['active_count']}")
print(f"Budget Exceeded Count: {stats['budget_exceeded_count']}")
```

## Protocol Integration

RAP integrates seamlessly with other protocols to create intelligent resource management.

### Integration with Contracts

When a contract is created, RAP automatically creates resource allocation based on pricing terms:

```python
from src.superstandard.protocols.integration import enable_auto_sync

# Enable integration
enable_auto_sync()

# Create contract
contract = await contracts.create_contract(
    provider_id="agent-nlp",
    consumer_id="agent-app",
    pricing=PricingTerms(
        per_request=0.15,    # $0.15 per request
        monthly_cap=50.00    # $50/month max
    )
)

# RAP automatically creates allocation for consumer!
allocation = await resources.get_allocation("agent-app")
# Budget = $50.00 (from contract)
# API Calls = 333 (calculated: $50 / $0.15)
```

**Benefits**:
- ✅ No manual resource allocation needed
- ✅ Contract pricing determines limits
- ✅ Automatic budget enforcement

### Integration with Reputation

High-reputation agents get priority and larger quotas:

```python
# Enable integration
enable_auto_sync()

# Agent with high reputation (0.95)
allocation = await resources.request_allocation(
    agent_id="agent-excellent"
)
# Priority: 9/10 (auto-assigned!)
# Quota: 1.45x multiplier (boosted!)

# Agent with low reputation (0.40)
allocation = await resources.request_allocation(
    agent_id="agent-poor"
)
# Priority: 4/10 (lower)
# Quota: 0.90x multiplier (reduced)
```

**Formula**:
- **Priority**: Scales from 1-10 based on reputation (0.9+ = priority 9)
- **Quota Multiplier**: 0.5x to 1.5x based on reputation (formula: 1.0 + (reputation - 0.5))

**Benefits**:
- ✅ Rewards good performance with more resources
- ✅ Limits resources for poor performers
- ✅ Self-optimizing resource allocation

## Production Patterns

### Pattern 1: Budget-Controlled Execution

```python
async def execute_with_budget_control(agent_id: str, tasks: list):
    """Execute tasks with automatic budget control"""
    resources = get_resource_service()

    # Allocate budget
    await resources.request_allocation(
        agent_id=agent_id,
        quotas={
            ResourceType.BUDGET_USD.value: ResourceQuota(
                ResourceType.BUDGET_USD,
                limit=100.00
            )
        }
    )

    for task in tasks:
        # Check budget before each task
        if await resources.is_budget_exceeded(agent_id):
            logger.warning(f"Budget exceeded! Stopping execution.")
            break

        # Execute task
        result = await execute_task(task)

        # Record usage
        await resources.record_usage(
            agent_id=agent_id,
            cost_usd=result.cost,
            api_calls=result.api_calls
        )
```

### Pattern 2: Cost Monitoring

```python
async def monitor_costs():
    """Monitor costs in real-time"""
    resources = get_resource_service()

    while True:
        stats = await resources.get_stats()

        if stats['total_cost_usd'] > 1000.00:
            send_alert("High cost detected!")

        top_consumers = await resources.get_top_consumers(limit=5)
        logger.info(f"Top consumers: {top_consumers}")

        await asyncio.sleep(300)  # Check every 5 minutes
```

### Pattern 3: Fair Distribution

```python
async def allocate_fairly(agent_ids: list, total_budget: float):
    """Distribute budget fairly across agents"""
    resources = get_resource_service()

    budget_per_agent = total_budget / len(agent_ids)

    for agent_id in agent_ids:
        await resources.request_allocation(
            agent_id=agent_id,
            quotas={
                ResourceType.BUDGET_USD.value: ResourceQuota(
                    ResourceType.BUDGET_USD,
                    limit=budget_per_agent
                )
            }
        )
```

## Data Models

### ResourceAllocation

```python
@dataclass
class ResourceAllocation:
    allocation_id: str                    # Unique ID
    agent_id: str                         # Agent receiving allocation
    quotas: Dict[str, ResourceQuota]      # Resource quotas
    priority: int                         # Priority level (1-10)
    status: AllocationStatus              # Current status
    allocated_at: str                     # Timestamp
    expires_at: Optional[str]             # Expiration time

    # Usage tracking
    used_api_calls: int
    used_budget_usd: float
    used_compute_seconds: float
    used_memory_mb: float
    used_storage_gb: float
    current_concurrent_tasks: int

    metadata: Dict[str, Any]              # Additional data
```

### ResourceUsageRecord

```python
@dataclass
class ResourceUsageRecord:
    record_id: str                # Unique ID
    agent_id: str                 # Agent ID
    allocation_id: str            # Associated allocation
    timestamp: str                # When recorded
    api_calls: int                # API calls made
    cost_usd: float               # Cost incurred
    compute_seconds: float        # Compute time
    memory_mb: float              # Memory used
    storage_gb: float             # Storage used
    task_id: Optional[str]        # Associated task
    metadata: Dict[str, Any]      # Additional data
```

## Service API

### Allocation Methods

- `request_allocation(agent_id, quotas, priority, duration_hours, auto_approve)` - Request allocation
- `activate_allocation(agent_id)` - Activate approved allocation
- `revoke_allocation(agent_id, reason)` - Cancel allocation
- `extend_allocation(agent_id, additional_hours)` - Extend expiration
- `get_allocation(agent_id)` - Get allocation details

### Usage Methods

- `record_usage(agent_id, api_calls, cost_usd, ...)` - Record usage
- `is_budget_exceeded(agent_id)` - Check if budget exceeded
- `is_quota_exceeded(agent_id, resource_type)` - Check specific quota
- `get_remaining_budget(agent_id)` - Get remaining budget
- `get_usage_summary(agent_id)` - Get usage breakdown

### Analytics Methods

- `get_stats()` - Get service statistics
- `get_top_consumers(limit)` - Get top resource consumers

## Statistics Tracked

The service tracks comprehensive statistics:

```python
stats = await resources.get_stats()

# Available stats:
{
    "total_allocations": 150,        # Total allocations created
    "active_allocations": 45,        # Currently active
    "total_usage_records": 5000,     # Total usage records
    "total_cost_usd": 1234.56,       # Total cost
    "total_api_calls": 50000,        # Total API calls
    "budget_exceeded_count": 3,      # Times budget exceeded
    "allocations_count": 150,        # Current allocations
    "active_count": 45,              # Active allocations
    "exhausted_count": 3,            # Exhausted allocations
    "avg_cost_per_agent": 8.23       # Average cost
}
```

## Best Practices

### 1. Always Set Budgets

```python
# ✅ Good: Set realistic budget
await resources.request_allocation(
    agent_id="agent-123",
    quotas={
        ResourceType.BUDGET_USD.value: ResourceQuota(
            ResourceType.BUDGET_USD,
            limit=50.00
        )
    }
)

# ❌ Bad: No budget limit
# (Risk of unlimited costs!)
```

### 2. Check Before Expensive Operations

```python
# ✅ Good: Check budget first
if not await resources.is_budget_exceeded(agent_id):
    await expensive_operation()
else:
    logger.warning("Budget exceeded, skipping operation")

# ❌ Bad: Execute without checking
await expensive_operation()  # May exceed budget!
```

### 3. Record All Usage

```python
# ✅ Good: Record every operation
result = await operation()
await resources.record_usage(
    agent_id=agent_id,
    cost_usd=result.cost,
    api_calls=result.api_calls
)

# ❌ Bad: Forget to record
await operation()  # Usage not tracked!
```

### 4. Monitor in Production

```python
# ✅ Good: Regular monitoring
async def monitor():
    stats = await resources.get_stats()
    if stats['total_cost_usd'] > threshold:
        send_alert()

# ❌ Bad: No monitoring
# (Costs can explode unnoticed)
```

### 5. Use Integration

```python
# ✅ Good: Enable integration
from src.superstandard.protocols.integration import enable_auto_sync
enable_auto_sync()
# Contracts auto-create allocations!
# Reputation auto-sets priorities!

# ❌ Bad: Manual allocation for every contract
# (More work, error-prone)
```

## Demo

Run the comprehensive demo to see all features:

```bash
python examples/resource_allocation_demo.py
```

**Demo includes**:
1. Basic allocation and quota enforcement
2. Budget exceeded detection
3. Multiple agents and analytics
4. Contract-based allocation (integration)
5. Reputation-based priorities (integration)
6. Service statistics

## Architecture

```
┌─────────────────────────────────────────┐
│    ResourceAllocationService            │
│  (Global Singleton)                     │
├─────────────────────────────────────────┤
│  Allocations: {agent_id -> allocation}  │
│  Usage History: [records...]            │
│  Global Quotas: {defaults...}           │
└─────────────────────────────────────────┘
            │
            ▼
    request_allocation()
            │
            ▼
    ┌───────────────┐
    │  Allocation   │
    │  (APPROVED)   │
    └───────────────┘
            │
            ▼
     activate_allocation()
            │
            ▼
    ┌───────────────┐
    │  Allocation   │
    │  (ACTIVE)     │
    └───────────────┘
            │
            ▼
      record_usage()
            │
            ├─> Update allocation.used_*
            ├─> Create usage record
            ├─> Check quotas
            │
            ▼
    Is quota exceeded?
      │           │
     Yes         No
      │           │
      ▼           ▼
  EXHAUSTED    Continue
```

## Integration Architecture

```
Contract Created
      │
      ▼
Integration._wrap_contract_creation()
      │
      ├─> Calculate budget from pricing
      ├─> Calculate API calls limit
      │
      ▼
Resources.request_allocation()
      │
      ▼
Auto-created allocation!


Reputation Updated
      │
      ▼
Integration._wrap_resource_requests()
      │
      ├─> Get reputation score
      ├─> Calculate priority (1-10)
      ├─> Calculate quota multiplier
      │
      ▼
Resources.request_allocation()
      │
      ▼
Priority & quotas adjusted!
```

## Key Benefits

### For Production Deployments
- ✅ **Cost control**: Hard caps prevent unlimited spending
- ✅ **Predictability**: Know costs in advance
- ✅ **Safety**: Automatic enforcement
- ✅ **Audit trail**: Complete usage history

### For Business
- ✅ **Budget governance**: Enforce organizational policies
- ✅ **Chargeback**: Track costs per agent/team
- ✅ **ROI analysis**: Cost vs performance metrics
- ✅ **Compliance**: Resource usage auditing

### For Developers
- ✅ **Simple API**: Request, use, track
- ✅ **Auto-enforcement**: Quota checks automatic
- ✅ **Rich analytics**: Comprehensive stats
- ✅ **Integration-ready**: Works with contracts & reputation

## Conclusion

The Resource Allocation Protocol is the **production safety layer** that makes autonomous multi-agent systems safe for real-world deployment.

**Key Takeaways**:
- 💰 Prevents runaway costs with hard budget caps
- 📊 Complete visibility into resource usage
- 🤝 Integrates with contracts and reputation
- 🛡️ Production-ready safety and governance
- 🚀 Essential for enterprise deployments

**Without RAP, you're flying blind. With RAP, you have complete control.**

---

**Next Steps**:
1. Run the demo: `python examples/resource_allocation_demo.py`
2. Review integration: See `src/superstandard/protocols/integration.py`
3. Try it in your agents: Add resource tracking to your workflows
4. Monitor in production: Set up cost monitoring and alerts

🎯 **PRODUCTION-SAFE MULTI-AGENT SYSTEMS!**
