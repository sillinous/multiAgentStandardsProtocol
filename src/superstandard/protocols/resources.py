"""
Resource Allocation Protocol (RAP)

Manages resource allocation, budgets, and quotas across the multi-agent ecosystem.
Prevents runaway costs, enforces spending limits, and ensures fair resource distribution.

Key Features:
- Budget allocation and enforcement
- API quota management
- Rate limiting per agent
- Cost tracking in real-time
- Resource request/approval flow
- Priority-based allocation
- Integration with contracts (pricing)
- Integration with reputation (allocate more to high-rep agents)
- Automatic enforcement and alerts

Usage:
    from src.superstandard.protocols.resources import get_resource_service

    resources = get_resource_service()

    # Request resources
    allocation = await resources.request_allocation(
        agent_id="agent-123",
        resources={
            "api_calls": 100,
            "budget_usd": 10.00,
            "max_duration_seconds": 300
        }
    )

    # Record usage
    await resources.record_usage(
        agent_id="agent-123",
        api_calls=45,
        cost_usd=4.50,
        duration_seconds=120
    )

    # Check if budget exceeded
    if await resources.is_budget_exceeded(agent_id):
        raise BudgetExceededError("Stop execution!")
"""

import asyncio
import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
from enum import Enum
import uuid


logger = logging.getLogger(__name__)


class ResourceType(Enum):
    """Types of resources that can be allocated"""
    API_CALLS = "api_calls"
    BUDGET_USD = "budget_usd"
    COMPUTE_SECONDS = "compute_seconds"
    MEMORY_MB = "memory_mb"
    STORAGE_GB = "storage_gb"
    CONCURRENT_TASKS = "concurrent_tasks"


class AllocationStatus(Enum):
    """Status of resource allocation"""
    PENDING = "pending"
    APPROVED = "approved"
    ACTIVE = "active"
    EXHAUSTED = "exhausted"
    EXPIRED = "expired"
    REVOKED = "revoked"


@dataclass
class ResourceQuota:
    """Resource quota definition"""
    resource_type: ResourceType
    limit: float
    period_seconds: int = 3600  # Default: 1 hour
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['resource_type'] = self.resource_type.value
        return data


@dataclass
class ResourceAllocation:
    """Resource allocation for an agent"""
    allocation_id: str
    agent_id: str
    quotas: Dict[str, ResourceQuota]
    priority: int = 5  # 1-10, higher = more priority
    status: AllocationStatus = AllocationStatus.PENDING
    allocated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    expires_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Usage tracking
    used_api_calls: int = 0
    used_budget_usd: float = 0.0
    used_compute_seconds: float = 0.0
    used_memory_mb: float = 0.0
    used_storage_gb: float = 0.0
    current_concurrent_tasks: int = 0

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['status'] = self.status.value
        data['quotas'] = {k: v.to_dict() for k, v in self.quotas.items()}
        return data

    def get_usage_percent(self, resource_type: ResourceType) -> float:
        """Get usage percentage for a resource type"""
        quota_key = resource_type.value
        if quota_key not in self.quotas:
            return 0.0

        quota = self.quotas[quota_key]
        if quota.limit == 0:
            return 0.0

        used = getattr(self, f"used_{quota_key}", 0)
        return (used / quota.limit) * 100

    def is_quota_exceeded(self, resource_type: ResourceType) -> bool:
        """Check if quota is exceeded for a resource type"""
        quota_key = resource_type.value
        if quota_key not in self.quotas:
            return False

        quota = self.quotas[quota_key]
        used = getattr(self, f"used_{quota_key}", 0)
        return used >= quota.limit

    def is_expired(self) -> bool:
        """Check if allocation has expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() >= datetime.fromisoformat(self.expires_at)


@dataclass
class ResourceUsageRecord:
    """Record of resource usage"""
    record_id: str
    agent_id: str
    allocation_id: str
    timestamp: str
    api_calls: int = 0
    cost_usd: float = 0.0
    compute_seconds: float = 0.0
    memory_mb: float = 0.0
    storage_gb: float = 0.0
    task_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ResourceAllocationService:
    """
    Resource Allocation Service

    Manages resource allocation, budgets, and quotas across the ecosystem.
    Prevents runaway costs and ensures fair resource distribution.

    Features:
    - Budget allocation and enforcement
    - API quota management
    - Rate limiting
    - Cost tracking
    - Priority-based allocation
    - Automatic enforcement
    - Integration with contracts and reputation
    """

    def __init__(self):
        """Initialize resource allocation service"""
        # Active allocations (agent_id -> allocation)
        self.allocations: Dict[str, ResourceAllocation] = {}

        # Usage records (for auditing)
        self.usage_history: List[ResourceUsageRecord] = []

        # Global quotas (fallback if agent has no specific allocation)
        self.global_quotas: Dict[str, ResourceQuota] = {
            ResourceType.API_CALLS.value: ResourceQuota(
                ResourceType.API_CALLS, 1000, 3600, "Default API quota"
            ),
            ResourceType.BUDGET_USD.value: ResourceQuota(
                ResourceType.BUDGET_USD, 10.0, 3600, "Default budget"
            )
        }

        # Stats
        self.stats = {
            "total_allocations": 0,
            "active_allocations": 0,
            "total_usage_records": 0,
            "total_cost_usd": 0.0,
            "total_api_calls": 0,
            "budget_exceeded_count": 0
        }

        logger.info("✅ Resource Allocation Service initialized")

    async def start(self):
        """Start resource service"""
        logger.info("🚀 Resource Allocation Service started")

    async def stop(self):
        """Stop resource service"""
        logger.info("🛑 Resource Allocation Service stopped")

    async def request_allocation(
        self,
        agent_id: str,
        quotas: Optional[Dict[str, ResourceQuota]] = None,
        priority: int = 5,
        duration_hours: int = 24,
        auto_approve: bool = True
    ) -> ResourceAllocation:
        """
        Request resource allocation for an agent

        Args:
            agent_id: Agent requesting resources
            quotas: Resource quotas (uses global defaults if None)
            priority: Priority level (1-10, higher = more priority)
            duration_hours: How long allocation is valid
            auto_approve: Automatically approve request

        Returns:
            ResourceAllocation
        """
        allocation_id = str(uuid.uuid4())

        # Use global quotas if none provided
        if quotas is None:
            quotas = dict(self.global_quotas)

        # Calculate expiration
        expires_at = (
            datetime.utcnow() + timedelta(hours=duration_hours)
        ).isoformat()

        allocation = ResourceAllocation(
            allocation_id=allocation_id,
            agent_id=agent_id,
            quotas=quotas,
            priority=priority,
            status=AllocationStatus.APPROVED if auto_approve else AllocationStatus.PENDING,
            expires_at=expires_at
        )

        self.allocations[agent_id] = allocation
        self.stats["total_allocations"] += 1
        self.stats["active_allocations"] = len([
            a for a in self.allocations.values()
            if a.status == AllocationStatus.ACTIVE or a.status == AllocationStatus.APPROVED
        ])

        logger.info(
            f"📝 Resource allocation requested: {agent_id} "
            f"(priority: {priority}, expires: {duration_hours}h)"
        )

        return allocation

    async def activate_allocation(self, agent_id: str):
        """Activate an approved allocation"""
        if agent_id not in self.allocations:
            raise ValueError(f"No allocation found for {agent_id}")

        allocation = self.allocations[agent_id]
        allocation.status = AllocationStatus.ACTIVE

        logger.info(f"✅ Allocation activated: {agent_id}")

    async def record_usage(
        self,
        agent_id: str,
        api_calls: int = 0,
        cost_usd: float = 0.0,
        compute_seconds: float = 0.0,
        memory_mb: float = 0.0,
        storage_gb: float = 0.0,
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ResourceUsageRecord:
        """
        Record resource usage

        Args:
            agent_id: Agent ID
            api_calls: Number of API calls made
            cost_usd: Cost in USD
            compute_seconds: Compute time in seconds
            memory_mb: Memory used in MB
            storage_gb: Storage used in GB
            task_id: Associated task ID
            metadata: Additional metadata

        Returns:
            ResourceUsageRecord
        """
        if agent_id not in self.allocations:
            # Create default allocation on first use
            await self.request_allocation(agent_id)

        allocation = self.allocations[agent_id]

        # Update allocation usage
        allocation.used_api_calls += api_calls
        allocation.used_budget_usd += cost_usd
        allocation.used_compute_seconds += compute_seconds
        allocation.used_memory_mb += memory_mb
        allocation.used_storage_gb += storage_gb

        # Create usage record
        record = ResourceUsageRecord(
            record_id=str(uuid.uuid4()),
            agent_id=agent_id,
            allocation_id=allocation.allocation_id,
            timestamp=datetime.utcnow().isoformat(),
            api_calls=api_calls,
            cost_usd=cost_usd,
            compute_seconds=compute_seconds,
            memory_mb=memory_mb,
            storage_gb=storage_gb,
            task_id=task_id,
            metadata=metadata or {}
        )

        self.usage_history.append(record)

        # Update stats
        self.stats["total_usage_records"] += 1
        self.stats["total_cost_usd"] += cost_usd
        self.stats["total_api_calls"] += api_calls

        # Check if any quotas exceeded
        for resource_type in ResourceType:
            if allocation.is_quota_exceeded(resource_type):
                allocation.status = AllocationStatus.EXHAUSTED
                self.stats["budget_exceeded_count"] += 1
                logger.warning(
                    f"⚠️  Quota exceeded for {agent_id}: {resource_type.value} "
                    f"({allocation.get_usage_percent(resource_type):.1f}%)"
                )

        logger.debug(
            f"📊 Usage recorded: {agent_id} "
            f"(calls: {api_calls}, cost: ${cost_usd:.2f})"
        )

        return record

    async def is_budget_exceeded(self, agent_id: str) -> bool:
        """Check if agent has exceeded budget"""
        if agent_id not in self.allocations:
            return False

        allocation = self.allocations[agent_id]
        return allocation.is_quota_exceeded(ResourceType.BUDGET_USD)

    async def is_quota_exceeded(
        self,
        agent_id: str,
        resource_type: ResourceType
    ) -> bool:
        """Check if agent has exceeded specific quota"""
        if agent_id not in self.allocations:
            return False

        allocation = self.allocations[agent_id]
        return allocation.is_quota_exceeded(resource_type)

    async def get_remaining_budget(self, agent_id: str) -> float:
        """Get remaining budget for agent"""
        if agent_id not in self.allocations:
            return 0.0

        allocation = self.allocations[agent_id]
        budget_quota = allocation.quotas.get(ResourceType.BUDGET_USD.value)

        if not budget_quota:
            return 0.0

        return budget_quota.limit - allocation.used_budget_usd

    async def get_allocation(self, agent_id: str) -> Optional[ResourceAllocation]:
        """Get allocation for agent"""
        return self.allocations.get(agent_id)

    async def get_usage_summary(self, agent_id: str) -> Dict[str, Any]:
        """Get usage summary for agent"""
        if agent_id not in self.allocations:
            return {"error": "No allocation found"}

        allocation = self.allocations[agent_id]

        return {
            "agent_id": agent_id,
            "allocation_id": allocation.allocation_id,
            "status": allocation.status.value,
            "usage": {
                "api_calls": {
                    "used": allocation.used_api_calls,
                    "limit": allocation.quotas.get(ResourceType.API_CALLS.value, ResourceQuota(ResourceType.API_CALLS, 0)).limit,
                    "percent": allocation.get_usage_percent(ResourceType.API_CALLS)
                },
                "budget_usd": {
                    "used": allocation.used_budget_usd,
                    "limit": allocation.quotas.get(ResourceType.BUDGET_USD.value, ResourceQuota(ResourceType.BUDGET_USD, 0)).limit,
                    "percent": allocation.get_usage_percent(ResourceType.BUDGET_USD),
                    "remaining": await self.get_remaining_budget(agent_id)
                },
                "compute_seconds": {
                    "used": allocation.used_compute_seconds,
                    "limit": allocation.quotas.get(ResourceType.COMPUTE_SECONDS.value, ResourceQuota(ResourceType.COMPUTE_SECONDS, 0)).limit,
                    "percent": allocation.get_usage_percent(ResourceType.COMPUTE_SECONDS)
                }
            },
            "expires_at": allocation.expires_at,
            "is_expired": allocation.is_expired()
        }

    async def revoke_allocation(self, agent_id: str, reason: str = ""):
        """Revoke resource allocation"""
        if agent_id not in self.allocations:
            raise ValueError(f"No allocation found for {agent_id}")

        allocation = self.allocations[agent_id]
        allocation.status = AllocationStatus.REVOKED
        allocation.metadata["revocation_reason"] = reason
        allocation.metadata["revoked_at"] = datetime.utcnow().isoformat()

        logger.info(f"🚫 Allocation revoked: {agent_id} ({reason})")

    async def extend_allocation(
        self,
        agent_id: str,
        additional_hours: int
    ) -> ResourceAllocation:
        """Extend allocation expiration time"""
        if agent_id not in self.allocations:
            raise ValueError(f"No allocation found for {agent_id}")

        allocation = self.allocations[agent_id]

        if allocation.expires_at:
            current_expiry = datetime.fromisoformat(allocation.expires_at)
            new_expiry = current_expiry + timedelta(hours=additional_hours)
            allocation.expires_at = new_expiry.isoformat()

        logger.info(
            f"⏰ Allocation extended: {agent_id} (+{additional_hours}h)"
        )

        return allocation

    async def get_stats(self) -> Dict[str, Any]:
        """Get resource service statistics"""
        return {
            **self.stats,
            "allocations_count": len(self.allocations),
            "active_count": len([
                a for a in self.allocations.values()
                if a.status == AllocationStatus.ACTIVE
            ]),
            "exhausted_count": len([
                a for a in self.allocations.values()
                if a.status == AllocationStatus.EXHAUSTED
            ]),
            "avg_cost_per_agent": (
                self.stats["total_cost_usd"] / len(self.allocations)
                if self.allocations else 0.0
            )
        }

    async def get_top_consumers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top resource consumers"""
        consumers = []

        for agent_id, allocation in self.allocations.items():
            consumers.append({
                "agent_id": agent_id,
                "total_cost_usd": allocation.used_budget_usd,
                "api_calls": allocation.used_api_calls,
                "compute_seconds": allocation.used_compute_seconds
            })

        # Sort by cost
        consumers.sort(key=lambda x: x["total_cost_usd"], reverse=True)

        return consumers[:limit]


# Global resource service instance
_resource_service: Optional[ResourceAllocationService] = None


def get_resource_service() -> ResourceAllocationService:
    """Get or create global resource service"""
    global _resource_service
    if _resource_service is None:
        _resource_service = ResourceAllocationService()
    return _resource_service


__all__ = [
    'ResourceType',
    'AllocationStatus',
    'ResourceQuota',
    'ResourceAllocation',
    'ResourceUsageRecord',
    'ResourceAllocationService',
    'get_resource_service'
]
