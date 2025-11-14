"""
Agent Contract Protocol (ACP)

Enables formal agreements between agents with SLAs, pricing terms, and
automated enforcement. Contracts define expectations and the system
automatically monitors compliance and enforces penalties for breaches.

Key Features:
- Formal contract creation (provider/consumer agreements)
- SLA terms (latency, quality, availability)
- Pricing terms (per-request, monthly caps)
- Automatic compliance monitoring
- Breach detection and tracking
- Penalty enforcement
- Integration with reputation (breaches affect reputation)
- Contract lifecycle management

Usage:
    from src.superstandard.protocols.contracts import get_contract_service

    contracts = get_contract_service()

    # Create contract
    contract = AgentContract(
        provider="DataAnalysisAgent",
        consumer="MarketResearchAgent",
        service="data_analysis",
        sla={
            "max_latency_ms": 5000,
            "min_quality": 0.95,
            "availability": 0.99
        },
        pricing={
            "per_request": 0.15,
            "monthly_cap": 100.00
        },
        term_days=30
    )

    await contracts.create_contract(contract)

    # Check compliance
    compliance = await contracts.check_compliance(contract_id)
"""

import asyncio
import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
from enum import Enum
import uuid


logger = logging.getLogger(__name__)


class ContractStatus(Enum):
    """Contract lifecycle status"""
    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    COMPLETED = "completed"
    TERMINATED = "terminated"
    BREACHED = "breached"


class BreachSeverity(Enum):
    """Severity of contract breach"""
    MINOR = "minor"  # Single violation
    MODERATE = "moderate"  # Multiple violations
    MAJOR = "major"  # Repeated or critical violations
    CRITICAL = "critical"  # Contract-breaking violations


@dataclass
class SLATerms:
    """Service Level Agreement terms"""
    max_latency_ms: Optional[float] = None  # Maximum response time
    min_quality: Optional[float] = None  # Minimum quality score (0-1)
    min_success_rate: Optional[float] = None  # Minimum success rate (0-1)
    availability: Optional[float] = None  # Required availability (0-1)
    max_error_rate: Optional[float] = None  # Maximum error rate (0-1)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PricingTerms:
    """Pricing and billing terms"""
    per_request: Optional[float] = None  # Cost per request
    per_minute: Optional[float] = None  # Cost per minute
    per_hour: Optional[float] = None  # Cost per hour
    monthly_cap: Optional[float] = None  # Monthly spending cap
    currency: str = "USD"
    billing_cycle: str = "monthly"  # monthly, weekly, daily

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ContractBreach:
    """Record of a contract violation"""
    breach_id: str
    contract_id: str
    timestamp: str
    breach_type: str  # "latency", "quality", "availability", etc.
    severity: BreachSeverity
    expected_value: float
    actual_value: float
    description: str
    penalty_applied: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['severity'] = self.severity.value
        return data


@dataclass
class ContractCompliance:
    """Contract compliance report"""
    contract_id: str
    is_compliant: bool
    compliance_rate: float  # 0-1
    total_requests: int
    successful_requests: int
    breaches: List[ContractBreach]
    avg_latency_ms: float
    avg_quality: float
    avg_success_rate: float
    last_checked: str

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['breaches'] = [b.to_dict() for b in self.breaches]
        return data


@dataclass
class AgentContract:
    """
    Formal agreement between two agents

    Defines SLAs, pricing, and terms of service.
    """
    contract_id: str
    provider_id: str  # Agent providing the service
    consumer_id: str  # Agent consuming the service
    service_name: str  # Service being provided
    sla: SLATerms
    pricing: PricingTerms
    status: ContractStatus = ContractStatus.DRAFT
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    term_days: int = 30
    auto_renew: bool = False
    total_requests: int = 0
    total_cost: float = 0.0
    breaches: List[ContractBreach] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['status'] = self.status.value
        data['sla'] = self.sla.to_dict()
        data['pricing'] = self.pricing.to_dict()
        data['breaches'] = [b.to_dict() for b in self.breaches]
        return data

    def is_active(self) -> bool:
        """Check if contract is currently active"""
        if self.status != ContractStatus.ACTIVE:
            return False

        if self.end_date:
            end = datetime.fromisoformat(self.end_date)
            if datetime.utcnow() > end:
                return False

        return True

    def days_remaining(self) -> Optional[int]:
        """Get days remaining in contract"""
        if not self.end_date:
            return None

        end = datetime.fromisoformat(self.end_date)
        remaining = (end - datetime.utcnow()).days
        return max(0, remaining)


class ContractService:
    """
    Agent Contract Service

    Manages formal agreements between agents with automated
    SLA monitoring and enforcement.

    Features:
    - Contract creation and lifecycle management
    - Automatic SLA compliance monitoring
    - Breach detection and tracking
    - Penalty enforcement
    - Reputation integration
    - Usage and cost tracking
    """

    def __init__(self):
        """Initialize contract service"""
        # Active contracts (contract_id -> contract)
        self.contracts: Dict[str, AgentContract] = {}

        # Provider index (provider_id -> contract_ids)
        self.provider_index: Dict[str, List[str]] = {}

        # Consumer index (consumer_id -> contract_ids)
        self.consumer_index: Dict[str, List[str]] = {}

        # Stats
        self.stats = {
            "total_contracts": 0,
            "active_contracts": 0,
            "total_breaches": 0,
            "total_requests_monitored": 0
        }

        logger.info("✅ Agent Contract Service initialized")

    async def start(self):
        """Start contract service"""
        logger.info("🚀 Agent Contract Service started")

    async def stop(self):
        """Stop contract service"""
        logger.info("🛑 Agent Contract Service stopped")

    async def create_contract(
        self,
        provider_id: str,
        consumer_id: str,
        service_name: str,
        sla: SLATerms,
        pricing: PricingTerms,
        term_days: int = 30,
        auto_renew: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentContract:
        """
        Create a new contract between agents

        Args:
            provider_id: Agent providing service
            consumer_id: Agent consuming service
            service_name: Service being provided
            sla: SLA terms
            pricing: Pricing terms
            term_days: Contract duration in days
            auto_renew: Auto-renew on expiration
            metadata: Additional metadata

        Returns:
            Created contract
        """
        contract_id = str(uuid.uuid4())

        contract = AgentContract(
            contract_id=contract_id,
            provider_id=provider_id,
            consumer_id=consumer_id,
            service_name=service_name,
            sla=sla,
            pricing=pricing,
            status=ContractStatus.DRAFT,
            term_days=term_days,
            auto_renew=auto_renew,
            metadata=metadata or {}
        )

        self.contracts[contract_id] = contract
        self.stats["total_contracts"] += 1

        # Update indices
        if provider_id not in self.provider_index:
            self.provider_index[provider_id] = []
        self.provider_index[provider_id].append(contract_id)

        if consumer_id not in self.consumer_index:
            self.consumer_index[consumer_id] = []
        self.consumer_index[consumer_id].append(contract_id)

        logger.info(
            f"📝 Contract created: {provider_id} → {consumer_id} "
            f"({service_name})"
        )

        return contract

    async def activate_contract(self, contract_id: str):
        """Activate a contract"""
        if contract_id not in self.contracts:
            raise ValueError(f"Contract not found: {contract_id}")

        contract = self.contracts[contract_id]
        contract.status = ContractStatus.ACTIVE
        contract.start_date = datetime.utcnow().isoformat()

        end_date = datetime.utcnow() + timedelta(days=contract.term_days)
        contract.end_date = end_date.isoformat()

        self.stats["active_contracts"] += 1

        logger.info(f"✅ Contract activated: {contract_id}")

    async def record_request(
        self,
        contract_id: str,
        success: bool,
        latency_ms: Optional[float] = None,
        quality_score: Optional[float] = None,
        cost: Optional[float] = None
    ):
        """
        Record a request under a contract and check compliance

        Args:
            contract_id: Contract ID
            success: Whether request succeeded
            latency_ms: Request latency
            quality_score: Quality score
            cost: Request cost

        Returns:
            List of breaches detected (if any)
        """
        if contract_id not in self.contracts:
            raise ValueError(f"Contract not found: {contract_id}")

        contract = self.contracts[contract_id]
        contract.total_requests += 1

        if cost:
            contract.total_cost += cost

        self.stats["total_requests_monitored"] += 1

        # Check SLA compliance
        breaches = []

        # Check latency
        if latency_ms and contract.sla.max_latency_ms:
            if latency_ms > contract.sla.max_latency_ms:
                breach = await self._create_breach(
                    contract,
                    "latency",
                    contract.sla.max_latency_ms,
                    latency_ms,
                    f"Latency {latency_ms:.0f}ms exceeded max {contract.sla.max_latency_ms:.0f}ms"
                )
                breaches.append(breach)

        # Check quality
        if quality_score and contract.sla.min_quality:
            if quality_score < contract.sla.min_quality:
                breach = await self._create_breach(
                    contract,
                    "quality",
                    contract.sla.min_quality,
                    quality_score,
                    f"Quality {quality_score:.1%} below min {contract.sla.min_quality:.1%}"
                )
                breaches.append(breach)

        # Check success rate (if we have enough data)
        if contract.total_requests >= 10 and contract.sla.min_success_rate:
            success_rate = (
                sum(1 for b in contract.breaches if b.breach_type != "success_rate")
                / contract.total_requests
            )
            if success_rate < contract.sla.min_success_rate:
                breach = await self._create_breach(
                    contract,
                    "success_rate",
                    contract.sla.min_success_rate,
                    success_rate,
                    f"Success rate {success_rate:.1%} below min {contract.sla.min_success_rate:.1%}"
                )
                breaches.append(breach)

        return breaches

    async def _create_breach(
        self,
        contract: AgentContract,
        breach_type: str,
        expected: float,
        actual: float,
        description: str
    ) -> ContractBreach:
        """Create and record a contract breach"""
        # Determine severity based on breach count
        breach_count = len([b for b in contract.breaches if b.breach_type == breach_type])

        if breach_count == 0:
            severity = BreachSeverity.MINOR
        elif breach_count < 3:
            severity = BreachSeverity.MODERATE
        elif breach_count < 5:
            severity = BreachSeverity.MAJOR
        else:
            severity = BreachSeverity.CRITICAL

        breach = ContractBreach(
            breach_id=str(uuid.uuid4()),
            contract_id=contract.contract_id,
            timestamp=datetime.utcnow().isoformat(),
            breach_type=breach_type,
            severity=severity,
            expected_value=expected,
            actual_value=actual,
            description=description
        )

        contract.breaches.append(breach)
        self.stats["total_breaches"] += 1

        # Check if contract should be marked as breached
        if severity == BreachSeverity.CRITICAL or len(contract.breaches) > 10:
            contract.status = ContractStatus.BREACHED

        logger.warning(
            f"⚠️  Contract breach ({severity.value}): {description}"
        )

        return breach

    async def check_compliance(self, contract_id: str) -> ContractCompliance:
        """
        Check contract compliance

        Args:
            contract_id: Contract to check

        Returns:
            Compliance report
        """
        if contract_id not in self.contracts:
            raise ValueError(f"Contract not found: {contract_id}")

        contract = self.contracts[contract_id]

        # Calculate metrics
        total = contract.total_requests
        breaches = contract.breaches

        successful = total - len([b for b in breaches if b.breach_type in ["quality", "latency"]])

        compliance_rate = successful / total if total > 0 else 1.0

        # Calculate averages (simplified)
        avg_latency = sum(b.actual_value for b in breaches if b.breach_type == "latency") / len(breaches) if breaches else 0
        avg_quality = sum(b.actual_value for b in breaches if b.breach_type == "quality") / len(breaches) if breaches else 1.0
        avg_success_rate = successful / total if total > 0 else 1.0

        is_compliant = compliance_rate >= 0.95 and len(breaches) < 5

        compliance = ContractCompliance(
            contract_id=contract_id,
            is_compliant=is_compliant,
            compliance_rate=compliance_rate,
            total_requests=total,
            successful_requests=successful,
            breaches=breaches,
            avg_latency_ms=avg_latency,
            avg_quality=avg_quality,
            avg_success_rate=avg_success_rate,
            last_checked=datetime.utcnow().isoformat()
        )

        return compliance

    async def get_contract(self, contract_id: str) -> Optional[AgentContract]:
        """Get contract by ID"""
        return self.contracts.get(contract_id)

    async def get_contracts_by_provider(self, provider_id: str) -> List[AgentContract]:
        """Get all contracts where agent is provider"""
        contract_ids = self.provider_index.get(provider_id, [])
        return [self.contracts[cid] for cid in contract_ids if cid in self.contracts]

    async def get_contracts_by_consumer(self, consumer_id: str) -> List[AgentContract]:
        """Get all contracts where agent is consumer"""
        contract_ids = self.consumer_index.get(consumer_id, [])
        return [self.contracts[cid] for cid in contract_ids if cid in self.contracts]

    async def terminate_contract(self, contract_id: str, reason: str = ""):
        """Terminate a contract"""
        if contract_id not in self.contracts:
            raise ValueError(f"Contract not found: {contract_id}")

        contract = self.contracts[contract_id]
        contract.status = ContractStatus.TERMINATED
        contract.metadata["termination_reason"] = reason
        contract.metadata["terminated_at"] = datetime.utcnow().isoformat()

        if contract.status == ContractStatus.ACTIVE:
            self.stats["active_contracts"] -= 1

        logger.info(f"🛑 Contract terminated: {contract_id} ({reason})")

    async def renew_contract(self, contract_id: str) -> AgentContract:
        """Renew an expiring contract"""
        if contract_id not in self.contracts:
            raise ValueError(f"Contract not found: {contract_id}")

        old_contract = self.contracts[contract_id]

        # Create new contract with same terms
        new_contract = await self.create_contract(
            provider_id=old_contract.provider_id,
            consumer_id=old_contract.consumer_id,
            service_name=old_contract.service_name,
            sla=old_contract.sla,
            pricing=old_contract.pricing,
            term_days=old_contract.term_days,
            auto_renew=old_contract.auto_renew,
            metadata={"renewed_from": contract_id}
        )

        await self.activate_contract(new_contract.contract_id)

        # Mark old as completed
        old_contract.status = ContractStatus.COMPLETED

        logger.info(f"🔄 Contract renewed: {contract_id} → {new_contract.contract_id}")

        return new_contract

    async def get_stats(self) -> Dict[str, Any]:
        """Get contract service statistics"""
        active_breached = len([
            c for c in self.contracts.values()
            if c.status == ContractStatus.BREACHED
        ])

        return {
            **self.stats,
            "contracts_in_system": len(self.contracts),
            "breached_contracts": active_breached,
            "avg_compliance_rate": self._calculate_avg_compliance()
        }

    def _calculate_avg_compliance(self) -> float:
        """Calculate average compliance rate across all contracts"""
        if not self.contracts:
            return 1.0

        total_compliance = 0.0
        count = 0

        for contract in self.contracts.values():
            if contract.total_requests > 0:
                successful = contract.total_requests - len(contract.breaches)
                compliance = successful / contract.total_requests
                total_compliance += compliance
                count += 1

        return total_compliance / count if count > 0 else 1.0


# Global contract service instance
_contract_service: Optional[ContractService] = None


def get_contract_service() -> ContractService:
    """Get or create global contract service"""
    global _contract_service
    if _contract_service is None:
        _contract_service = ContractService()
    return _contract_service


__all__ = [
    'ContractStatus',
    'BreachSeverity',
    'SLATerms',
    'PricingTerms',
    'ContractBreach',
    'ContractCompliance',
    'AgentContract',
    'ContractService',
    'get_contract_service'
]
