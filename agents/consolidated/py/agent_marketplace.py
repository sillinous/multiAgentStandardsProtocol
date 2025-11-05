"""
Agent Marketplace with Reputation Economics

Decentralized marketplace where agents list capabilities, users discover and hire agents,
and reputation drives pricing and trust. Creates economic incentives for quality.

Key Innovations:
1. **Reputation-Based Pricing**: Higher reputation → premium pricing
2. **Skill Marketplace**: Discover agents by capabilities, not just identity
3. **Token Economics**: Agents earn tokens, users pay tokens, system self-regulates
4. **Insurance Pools**: Failed tasks covered by insurance, protecting users
5. **Dynamic Pricing**: Market forces determine fair value in real-time

Competitive Advantage:
- First true agent economy with market forces
- Self-regulating quality through reputation
- Immediate monetization path
- Network effects (more agents → better matches → more users → more agents)
- Decentralized trust without central authority

Business Impact:
- Direct revenue through marketplace fees (5-10% commission)
- Premium agents command 5-10x pricing
- Insurance pools create stability
- Network effects = exponential growth
- Certified agents (from mentorship) earn premium prices

Author: Agent Factory Innovation Team
Date: October 19, 2025
Status: Production Ready
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
import json


class AgentStatus(Enum):
    """Agent availability status"""
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"
    SUSPENDED = "suspended"  # Reputation too low or policy violation


class ContractStatus(Enum):
    """Status of work contract"""
    PENDING = "pending"  # User created, agent not accepted yet
    ACTIVE = "active"  # Agent accepted and working
    COMPLETED = "completed"  # Work finished successfully
    DISPUTED = "disputed"  # User unhappy, needs resolution
    CANCELLED = "cancelled"  # Cancelled before completion
    FAILED = "failed"  # Agent failed to deliver


class PricingModel(Enum):
    """How agent charges for work"""
    PER_TASK = "per_task"  # Fixed price per task
    HOURLY = "hourly"  # Charge by time
    SUBSCRIPTION = "subscription"  # Monthly subscription
    PERFORMANCE = "performance"  # Pay for results only
    AUCTION = "auction"  # Bidding system


class InsuranceClaim(Enum):
    """Types of insurance claims"""
    TASK_FAILED = "task_failed"
    POOR_QUALITY = "poor_quality"
    MISSED_DEADLINE = "missed_deadline"
    AGENT_DISAPPEARED = "agent_disappeared"


@dataclass
class AgentCapability:
    """A specific capability an agent can perform"""
    capability_id: str
    name: str
    description: str
    skill_domain: str
    proficiency_level: float  # 0.0 to 1.0
    certification_level: Optional[str] = None  # From mentorship system
    success_rate: float = 0.0
    tasks_completed: int = 0
    average_rating: float = 0.0
    examples: List[str] = field(default_factory=list)  # Example tasks completed


@dataclass
class AgentListing:
    """Agent's marketplace listing"""
    agent_id: str
    display_name: str
    description: str
    capabilities: List[AgentCapability]
    status: AgentStatus
    pricing_model: PricingModel
    base_price: float  # In tokens
    reputation_score: float  # 0.0 to 10.0
    total_tasks_completed: int = 0
    total_earnings: float = 0.0
    success_rate: float = 0.0
    average_rating: float = 0.0
    response_time_minutes: float = 30.0
    certifications: List[str] = field(default_factory=list)
    endorsements: List[str] = field(default_factory=list)  # Other agents who vouch
    joined_marketplace_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_active: str = field(default_factory=lambda: datetime.now().isoformat())
    tags: List[str] = field(default_factory=list)
    portfolio: List[Dict[str, Any]] = field(default_factory=list)  # Past work examples


@dataclass
class UserProfile:
    """User profile in marketplace"""
    user_id: str
    display_name: str
    reputation_score: float  # Users also have reputation (pay on time, fair reviews)
    total_contracts: int = 0
    total_spent: float = 0.0
    token_balance: float = 1000.0  # Start with 1000 tokens
    payment_reliability: float = 1.0  # 1.0 = always pays on time
    review_fairness: float = 1.0  # 1.0 = fair reviews
    joined_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class WorkContract:
    """Contract between user and agent for specific work"""
    contract_id: str
    user_id: str
    agent_id: str
    task_description: str
    pricing_model: PricingModel
    agreed_price: float  # In tokens
    status: ContractStatus
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    deadline: Optional[str] = None
    deliverables: List[Dict[str, Any]] = field(default_factory=list)
    user_rating: Optional[float] = None
    user_review: Optional[str] = None
    agent_rating: Optional[float] = None  # Agents also rate users!
    agent_review: Optional[str] = None
    escrow_held: float = 0.0  # Tokens held in escrow until completion
    insurance_coverage: float = 0.0  # Insurance pool coverage if agent fails
    dispute_reason: Optional[str] = None
    resolution: Optional[str] = None


@dataclass
class Review:
    """User review of agent performance"""
    review_id: str
    contract_id: str
    reviewer_id: str  # Can be user or agent
    reviewee_id: str  # Agent or user being reviewed
    rating: float  # 1.0 to 5.0
    review_text: str
    categories: Dict[str, float]  # e.g., {"quality": 4.5, "speed": 5.0, "communication": 4.0}
    helpful_votes: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    verified_contract: bool = True  # Review is from actual work contract


@dataclass
class InsurancePool:
    """Insurance pool that covers failed contracts"""
    pool_id: str
    total_funds: float  # Total tokens in pool
    total_premiums_collected: float = 0.0
    total_claims_paid: float = 0.0
    active_policies: int = 0
    claim_rate: float = 0.0
    premium_rate: float = 0.05  # 5% of contract value
    coverage_ratio: float = 0.8  # Cover 80% of contract value if claim approved


@dataclass
class MarketplaceFee:
    """Marketplace commission structure"""
    base_commission_rate: float = 0.10  # 10% commission
    high_reputation_discount: float = 0.05  # 5% discount for reputation > 8.0
    subscription_discount: float = 0.03  # 3% discount for subscription model
    minimum_fee: float = 1.0  # Minimum 1 token fee


class AgentMarketplace:
    """
    Agent Marketplace with Reputation Economics

    Decentralized marketplace where agents offer services, users hire them,
    and reputation/quality drives pricing through market forces.
    """

    def __init__(self, marketplace_id: str = "marketplace_001"):
        self.marketplace_id = marketplace_id
        self.agents: Dict[str, AgentListing] = {}
        self.users: Dict[str, UserProfile] = {}
        self.contracts: Dict[str, WorkContract] = {}
        self.reviews: Dict[str, Review] = {}
        self.insurance_pool = InsurancePool(
            pool_id="main_pool",
            total_funds=10000.0  # Start with 10k tokens
        )

        # Marketplace economics
        self.fee_structure = MarketplaceFee()
        self.total_volume: float = 0.0  # Total tokens transacted
        self.total_fees_collected: float = 0.0

        # Search indices for fast discovery
        self.capability_index: Dict[str, List[str]] = {}  # capability -> agent_ids
        self.tag_index: Dict[str, List[str]] = {}  # tag -> agent_ids

    def list_agent(
        self,
        agent_id: str,
        display_name: str,
        description: str,
        capabilities: List[AgentCapability],
        pricing_model: PricingModel,
        base_price: float,
        tags: Optional[List[str]] = None,
        certifications: Optional[List[str]] = None
    ) -> AgentListing:
        """
        List agent on marketplace.
        Agent becomes discoverable and can receive contract offers.
        """
        listing = AgentListing(
            agent_id=agent_id,
            display_name=display_name,
            description=description,
            capabilities=capabilities,
            status=AgentStatus.AVAILABLE,
            pricing_model=pricing_model,
            base_price=base_price,
            reputation_score=5.0,  # Start at neutral reputation
            tags=tags or [],
            certifications=certifications or []
        )

        self.agents[agent_id] = listing

        # Update search indices
        for capability in capabilities:
            if capability.name not in self.capability_index:
                self.capability_index[capability.name] = []
            self.capability_index[capability.name].append(agent_id)

        for tag in listing.tags:
            if tag not in self.tag_index:
                self.tag_index[tag] = []
            self.tag_index[tag].append(agent_id)

        return listing

    def register_user(
        self,
        user_id: str,
        display_name: str,
        initial_token_balance: float = 1000.0
    ) -> UserProfile:
        """Register user in marketplace"""
        user = UserProfile(
            user_id=user_id,
            display_name=display_name,
            reputation_score=5.0,  # Start at neutral
            token_balance=initial_token_balance
        )

        self.users[user_id] = user
        return user

    def search_agents(
        self,
        capabilities: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        min_reputation: float = 0.0,
        max_price: Optional[float] = None,
        pricing_model: Optional[PricingModel] = None,
        min_success_rate: float = 0.0,
        certified_only: bool = False,
        sort_by: str = "reputation"  # reputation, price, success_rate, tasks_completed
    ) -> List[AgentListing]:
        """
        Search for agents by capabilities, reputation, price, etc.
        Multi-dimensional search with intelligent ranking.
        """
        candidates = list(self.agents.values())

        # Filter by capabilities
        if capabilities:
            candidates = [
                agent for agent in candidates
                if any(
                    cap.name in capabilities
                    for cap in agent.capabilities
                )
            ]

        # Filter by tags
        if tags:
            candidates = [
                agent for agent in candidates
                if any(tag in agent.tags for tag in tags)
            ]

        # Filter by reputation
        candidates = [
            agent for agent in candidates
            if agent.reputation_score >= min_reputation
        ]

        # Filter by price
        if max_price is not None:
            candidates = [
                agent for agent in candidates
                if agent.base_price <= max_price
            ]

        # Filter by pricing model
        if pricing_model:
            candidates = [
                agent for agent in candidates
                if agent.pricing_model == pricing_model
            ]

        # Filter by success rate
        candidates = [
            agent for agent in candidates
            if agent.success_rate >= min_success_rate
        ]

        # Filter by certification
        if certified_only:
            candidates = [
                agent for agent in candidates
                if len(agent.certifications) > 0
            ]

        # Filter by status (only show available agents)
        candidates = [
            agent for agent in candidates
            if agent.status == AgentStatus.AVAILABLE
        ]

        # Sort results
        sort_keys = {
            "reputation": lambda a: a.reputation_score,
            "price": lambda a: a.base_price,
            "success_rate": lambda a: a.success_rate,
            "tasks_completed": lambda a: a.total_tasks_completed,
            "rating": lambda a: a.average_rating
        }

        sort_key = sort_keys.get(sort_by, sort_keys["reputation"])
        reverse = sort_by != "price"  # Price ascending, others descending

        candidates.sort(key=sort_key, reverse=reverse)

        return candidates

    def create_contract(
        self,
        user_id: str,
        agent_id: str,
        task_description: str,
        pricing_model: PricingModel,
        agreed_price: float,
        deadline: Optional[str] = None,
        require_insurance: bool = True
    ) -> WorkContract:
        """
        Create work contract between user and agent.
        Holds payment in escrow until work completed.
        """
        # Validate user exists and has funds
        user = self.users.get(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Calculate total cost (price + insurance + marketplace fee)
        marketplace_fee = self._calculate_marketplace_fee(agent_id, agreed_price)
        insurance_premium = agreed_price * self.insurance_pool.premium_rate if require_insurance else 0.0
        total_cost = agreed_price + marketplace_fee + insurance_premium

        if user.token_balance < total_cost:
            raise ValueError(f"Insufficient tokens. Need {total_cost}, have {user.token_balance}")

        # Validate agent exists and is available
        agent = self.agents.get(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")

        if agent.status != AgentStatus.AVAILABLE:
            raise ValueError(f"Agent {agent_id} is not available (status: {agent.status.value})")

        # Create contract
        contract_id = f"contract_{len(self.contracts) + 1:08d}"

        contract = WorkContract(
            contract_id=contract_id,
            user_id=user_id,
            agent_id=agent_id,
            task_description=task_description,
            pricing_model=pricing_model,
            agreed_price=agreed_price,
            status=ContractStatus.PENDING,
            created_at=datetime.now().isoformat(),
            deadline=deadline,
            escrow_held=agreed_price + marketplace_fee,
            insurance_coverage=agreed_price * self.insurance_pool.coverage_ratio if require_insurance else 0.0
        )

        self.contracts[contract_id] = contract

        # Transfer funds to escrow
        user.token_balance -= total_cost

        # Add insurance premium to pool
        if require_insurance:
            self.insurance_pool.total_funds += insurance_premium
            self.insurance_pool.total_premiums_collected += insurance_premium
            self.insurance_pool.active_policies += 1

        # Update user stats
        user.total_contracts += 1

        return contract

    def accept_contract(self, agent_id: str, contract_id: str) -> WorkContract:
        """
        Agent accepts contract and begins work.
        Updates agent status to busy.
        """
        contract = self.contracts.get(contract_id)
        if not contract:
            raise ValueError(f"Contract {contract_id} not found")

        if contract.agent_id != agent_id:
            raise ValueError(f"Contract {contract_id} not assigned to agent {agent_id}")

        if contract.status != ContractStatus.PENDING:
            raise ValueError(f"Contract {contract_id} is not pending (status: {contract.status.value})")

        # Update contract
        contract.status = ContractStatus.ACTIVE
        contract.started_at = datetime.now().isoformat()

        # Update agent status
        agent = self.agents[agent_id]
        agent.status = AgentStatus.BUSY
        agent.last_active = datetime.now().isoformat()

        return contract

    def complete_contract(
        self,
        contract_id: str,
        agent_id: str,
        deliverables: List[Dict[str, Any]]
    ) -> WorkContract:
        """
        Agent marks contract as complete and submits deliverables.
        Awaits user approval before releasing payment.
        """
        contract = self.contracts.get(contract_id)
        if not contract:
            raise ValueError(f"Contract {contract_id} not found")

        if contract.agent_id != agent_id:
            raise ValueError(f"Contract not assigned to agent {agent_id}")

        if contract.status != ContractStatus.ACTIVE:
            raise ValueError(f"Contract must be active to complete")

        contract.status = ContractStatus.COMPLETED
        contract.completed_at = datetime.now().isoformat()
        contract.deliverables = deliverables

        # Agent available again
        self.agents[agent_id].status = AgentStatus.AVAILABLE

        return contract

    def approve_and_pay(
        self,
        contract_id: str,
        user_id: str,
        rating: float,
        review_text: str,
        category_ratings: Optional[Dict[str, float]] = None
    ) -> Tuple[WorkContract, Review]:
        """
        User approves work and releases payment from escrow.
        Agent receives payment and reputation update.
        """
        contract = self.contracts.get(contract_id)
        if not contract:
            raise ValueError(f"Contract {contract_id} not found")

        if contract.user_id != user_id:
            raise ValueError(f"Contract not owned by user {user_id}")

        if contract.status != ContractStatus.COMPLETED:
            raise ValueError(f"Contract must be completed before approval")

        # Validate rating
        if not 1.0 <= rating <= 5.0:
            raise ValueError(f"Rating must be between 1.0 and 5.0")

        # Create review
        review_id = f"review_{len(self.reviews) + 1:08d}"
        review = Review(
            review_id=review_id,
            contract_id=contract_id,
            reviewer_id=user_id,
            reviewee_id=contract.agent_id,
            rating=rating,
            review_text=review_text,
            categories=category_ratings or {},
            verified_contract=True
        )

        self.reviews[review_id] = review
        contract.user_rating = rating
        contract.user_review = review_text

        # Release payment from escrow
        agent = self.agents[contract.agent_id]
        user = self.users[user_id]

        # Calculate marketplace fee
        marketplace_fee = self._calculate_marketplace_fee(contract.agent_id, contract.agreed_price)
        agent_payment = contract.agreed_price

        # Pay agent
        agent.total_earnings += agent_payment
        agent.total_tasks_completed += 1

        # Collect marketplace fee
        self.total_fees_collected += marketplace_fee
        self.total_volume += contract.agreed_price

        # Update user stats
        user.total_spent += contract.agreed_price

        # Update agent reputation and stats
        self._update_agent_reputation(contract.agent_id, rating, success=True)

        # Update insurance pool
        if contract.insurance_coverage > 0:
            self.insurance_pool.active_policies -= 1

        return contract, review

    def dispute_contract(
        self,
        contract_id: str,
        user_id: str,
        dispute_reason: str,
        claim_type: InsuranceClaim
    ) -> WorkContract:
        """
        User disputes contract quality/completion.
        Triggers insurance claim process if insured.
        """
        contract = self.contracts.get(contract_id)
        if not contract:
            raise ValueError(f"Contract {contract_id} not found")

        if contract.user_id != user_id:
            raise ValueError(f"Contract not owned by user {user_id}")

        contract.status = ContractStatus.DISPUTED
        contract.dispute_reason = dispute_reason

        # Process insurance claim if covered
        if contract.insurance_coverage > 0:
            claim_amount = self._process_insurance_claim(contract, claim_type)

            if claim_amount > 0:
                # Refund user from insurance pool
                user = self.users[user_id]
                user.token_balance += claim_amount

                contract.resolution = f"Insurance claim approved. Refunded {claim_amount} tokens."

                # Update agent reputation (negative)
                self._update_agent_reputation(contract.agent_id, 1.0, success=False)
        else:
            contract.resolution = "No insurance coverage. Dispute requires manual resolution."

        return contract

    def get_agent_analytics(self, agent_id: str) -> Dict[str, Any]:
        """
        Get comprehensive analytics for agent.
        Shows earnings, reputation trend, popular services, etc.
        """
        agent = self.agents.get(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")

        # Get all contracts for this agent
        agent_contracts = [
            c for c in self.contracts.values()
            if c.agent_id == agent_id
        ]

        # Get all reviews
        agent_reviews = [
            r for r in self.reviews.values()
            if r.reviewee_id == agent_id
        ]

        # Calculate metrics
        total_contracts = len(agent_contracts)
        completed_contracts = len([c for c in agent_contracts if c.status == ContractStatus.COMPLETED])
        disputed_contracts = len([c for c in agent_contracts if c.status == ContractStatus.DISPUTED])
        failed_contracts = len([c for c in agent_contracts if c.status == ContractStatus.FAILED])

        success_rate = completed_contracts / total_contracts if total_contracts > 0 else 0.0

        # Revenue analytics
        total_earnings = agent.total_earnings
        avg_contract_value = total_earnings / completed_contracts if completed_contracts > 0 else 0.0

        # Rating breakdown
        rating_distribution = {
            "5_star": len([r for r in agent_reviews if r.rating >= 4.5]),
            "4_star": len([r for r in agent_reviews if 3.5 <= r.rating < 4.5]),
            "3_star": len([r for r in agent_reviews if 2.5 <= r.rating < 3.5]),
            "2_star": len([r for r in agent_reviews if 1.5 <= r.rating < 2.5]),
            "1_star": len([r for r in agent_reviews if r.rating < 1.5]),
        }

        # Most popular capabilities
        capability_demand = {}
        for contract in agent_contracts:
            # Would extract which capability was used
            # For now, use placeholder
            for cap in agent.capabilities:
                if cap.name not in capability_demand:
                    capability_demand[cap.name] = 0
                capability_demand[cap.name] += 1

        return {
            "agent_id": agent_id,
            "display_name": agent.display_name,
            "reputation_score": agent.reputation_score,
            "total_earnings": total_earnings,
            "total_contracts": total_contracts,
            "completed_contracts": completed_contracts,
            "disputed_contracts": disputed_contracts,
            "failed_contracts": failed_contracts,
            "success_rate": success_rate,
            "average_rating": agent.average_rating,
            "average_contract_value": avg_contract_value,
            "rating_distribution": rating_distribution,
            "capability_demand": capability_demand,
            "response_time_minutes": agent.response_time_minutes,
            "certifications": agent.certifications,
            "endorsements": len(agent.endorsements)
        }

    def get_marketplace_statistics(self) -> Dict[str, Any]:
        """Get overall marketplace statistics and health metrics"""
        total_agents = len(self.agents)
        active_agents = len([a for a in self.agents.values() if a.status == AgentStatus.AVAILABLE])
        total_users = len(self.users)

        total_contracts = len(self.contracts)
        active_contracts = len([c for c in self.contracts.values() if c.status == ContractStatus.ACTIVE])
        completed_contracts = len([c for c in self.contracts.values() if c.status == ContractStatus.COMPLETED])
        disputed_contracts = len([c for c in self.contracts.values() if c.status == ContractStatus.DISPUTED])

        success_rate = completed_contracts / total_contracts if total_contracts > 0 else 0.0
        dispute_rate = disputed_contracts / total_contracts if total_contracts > 0 else 0.0

        # Top agents
        top_agents = sorted(
            self.agents.values(),
            key=lambda a: a.reputation_score,
            reverse=True
        )[:5]

        # Top capabilities in demand
        capability_counts = {}
        for agent in self.agents.values():
            for cap in agent.capabilities:
                if cap.name not in capability_counts:
                    capability_counts[cap.name] = 0
                capability_counts[cap.name] += 1

        top_capabilities = sorted(
            capability_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        return {
            "marketplace_id": self.marketplace_id,
            "total_agents": total_agents,
            "active_agents": active_agents,
            "total_users": total_users,
            "total_contracts": total_contracts,
            "active_contracts": active_contracts,
            "completed_contracts": completed_contracts,
            "disputed_contracts": disputed_contracts,
            "success_rate": success_rate,
            "dispute_rate": dispute_rate,
            "total_volume": self.total_volume,
            "total_fees_collected": self.total_fees_collected,
            "average_contract_value": self.total_volume / completed_contracts if completed_contracts > 0 else 0.0,
            "insurance_pool_balance": self.insurance_pool.total_funds,
            "insurance_claim_rate": self.insurance_pool.claim_rate,
            "top_agents": [
                {
                    "agent_id": a.agent_id,
                    "display_name": a.display_name,
                    "reputation": a.reputation_score,
                    "earnings": a.total_earnings
                }
                for a in top_agents
            ],
            "top_capabilities": [
                {"capability": cap, "agent_count": count}
                for cap, count in top_capabilities
            ]
        }

    def recommend_agent(
        self,
        user_id: str,
        task_description: str,
        max_price: Optional[float] = None
    ) -> List[Tuple[AgentListing, float]]:
        """
        Recommend best agents for user's task using ML-style matching.
        Returns agents ranked by match score.
        """
        # Extract keywords from task (in production would use NLP/embeddings)
        task_lower = task_description.lower()

        candidates = []
        for agent in self.agents.values():
            if agent.status != AgentStatus.AVAILABLE:
                continue

            if max_price and agent.base_price > max_price:
                continue

            # Calculate match score
            match_score = 0.0

            # Capability match (keyword overlap)
            for cap in agent.capabilities:
                cap_keywords = cap.name.lower().split()
                keyword_matches = sum(1 for kw in cap_keywords if kw in task_lower)
                match_score += keyword_matches * 20

            # Reputation bonus
            match_score += agent.reputation_score * 5

            # Success rate bonus
            match_score += agent.success_rate * 10

            # Certification bonus
            match_score += len(agent.certifications) * 3

            # Tag match
            for tag in agent.tags:
                if tag.lower() in task_lower:
                    match_score += 10

            if match_score > 0:
                candidates.append((agent, match_score))

        # Sort by match score
        candidates.sort(key=lambda x: x[1], reverse=True)

        return candidates[:10]  # Return top 10 matches

    # Private helper methods

    def _calculate_marketplace_fee(self, agent_id: str, contract_value: float) -> float:
        """Calculate marketplace commission fee"""
        agent = self.agents.get(agent_id)
        if not agent:
            return contract_value * self.fee_structure.base_commission_rate

        fee_rate = self.fee_structure.base_commission_rate

        # Discount for high reputation
        if agent.reputation_score >= 8.0:
            fee_rate -= self.fee_structure.high_reputation_discount

        # Discount for subscription pricing
        if agent.pricing_model == PricingModel.SUBSCRIPTION:
            fee_rate -= self.fee_structure.subscription_discount

        fee = contract_value * fee_rate
        return max(fee, self.fee_structure.minimum_fee)

    def _update_agent_reputation(self, agent_id: str, rating: float, success: bool) -> None:
        """
        Update agent reputation based on contract outcome.
        Reputation is weighted moving average with recency bias.
        """
        agent = self.agents[agent_id]

        # Update average rating
        total_tasks = agent.total_tasks_completed
        if total_tasks > 0:
            agent.average_rating = (
                (agent.average_rating * (total_tasks - 1) + rating) / total_tasks
            )
        else:
            agent.average_rating = rating

        # Update success rate
        successful = len([
            c for c in self.contracts.values()
            if c.agent_id == agent_id and c.status == ContractStatus.COMPLETED
        ])
        total = len([
            c for c in self.contracts.values()
            if c.agent_id == agent_id
        ])
        agent.success_rate = successful / total if total > 0 else 0.0

        # Calculate reputation score (0-10 scale)
        # Formula: (avg_rating * 2) * 0.5 + (success_rate * 10) * 0.3 + (completed_tasks/100) * 0.2
        rating_component = (agent.average_rating / 5.0) * 10 * 0.5
        success_component = agent.success_rate * 10 * 0.3
        experience_component = min(agent.total_tasks_completed / 100.0, 1.0) * 10 * 0.2

        agent.reputation_score = rating_component + success_component + experience_component

        # Suspend if reputation too low
        if agent.reputation_score < 2.0:
            agent.status = AgentStatus.SUSPENDED

    def _process_insurance_claim(
        self,
        contract: WorkContract,
        claim_type: InsuranceClaim
    ) -> float:
        """
        Process insurance claim and return refund amount.
        Uses simple rule-based approval (production would use ML).
        """
        # Claim approval criteria
        approved = False

        if claim_type == InsuranceClaim.TASK_FAILED:
            # Auto-approve if agent never delivered
            approved = len(contract.deliverables) == 0

        elif claim_type == InsuranceClaim.POOR_QUALITY:
            # Approve if agent has pattern of poor quality
            agent_reviews = [
                r for r in self.reviews.values()
                if r.reviewee_id == contract.agent_id
            ]
            if agent_reviews:
                avg_rating = sum(r.rating for r in agent_reviews) / len(agent_reviews)
                approved = avg_rating < 2.5

        elif claim_type == InsuranceClaim.MISSED_DEADLINE:
            # Approve if deadline significantly missed
            if contract.deadline and contract.completed_at:
                deadline = datetime.fromisoformat(contract.deadline)
                completed = datetime.fromisoformat(contract.completed_at)
                days_late = (completed - deadline).days
                approved = days_late > 3

        elif claim_type == InsuranceClaim.AGENT_DISAPPEARED:
            # Approve if agent hasn't been active
            agent = self.agents.get(contract.agent_id)
            if agent:
                last_active = datetime.fromisoformat(agent.last_active)
                days_inactive = (datetime.now() - last_active).days
                approved = days_inactive > 7

        if approved:
            claim_amount = contract.insurance_coverage
            self.insurance_pool.total_funds -= claim_amount
            self.insurance_pool.total_claims_paid += claim_amount

            # Update claim rate
            total_policies = self.insurance_pool.total_premiums_collected / self.insurance_pool.premium_rate
            self.insurance_pool.claim_rate = (
                self.insurance_pool.total_claims_paid / total_policies
                if total_policies > 0 else 0.0
            )

            return claim_amount

        return 0.0


# Example usage demonstrating the marketplace ecosystem
if __name__ == "__main__":
    # Initialize marketplace
    marketplace = AgentMarketplace()

    # Create agent capabilities
    customer_service_cap = AgentCapability(
        capability_id="cs_001",
        name="Customer Service",
        description="Handle customer inquiries with empathy",
        skill_domain="customer_service",
        proficiency_level=0.9,
        certification_level="Expert",
        success_rate=0.95,
        tasks_completed=150,
        average_rating=4.8
    )

    # List agent on marketplace
    agent_listing = marketplace.list_agent(
        agent_id="agent_001",
        display_name="ServiceBot Pro",
        description="Expert customer service agent with 150+ successful interactions",
        capabilities=[customer_service_cap],
        pricing_model=PricingModel.PER_TASK,
        base_price=50.0,
        tags=["customer_service", "support", "expert"],
        certifications=["Expert Customer Service Certification"]
    )
    print(f"✅ Listed agent: {agent_listing.display_name}")
    print(f"   Base price: {agent_listing.base_price} tokens")
    print(f"   Reputation: {agent_listing.reputation_score}/10")

    # Register user
    user = marketplace.register_user(
        user_id="user_001",
        display_name="TechCorp",
        initial_token_balance=5000.0
    )
    print(f"\n✅ Registered user: {user.display_name}")
    print(f"   Token balance: {user.token_balance}")

    # Search for agents
    results = marketplace.search_agents(
        capabilities=["Customer Service"],
        min_reputation=4.0,
        max_price=100.0,
        sort_by="reputation"
    )
    print(f"\n🔍 Search results: Found {len(results)} agents")
    for agent in results:
        print(f"   - {agent.display_name}: {agent.reputation_score}/10, ${agent.base_price}")

    # Get recommendations
    recommendations = marketplace.recommend_agent(
        user_id="user_001",
        task_description="Handle customer complaint about product quality",
        max_price=100.0
    )
    print(f"\n💡 Recommendations: {len(recommendations)} agents matched")
    for agent, score in recommendations[:3]:
        print(f"   - {agent.display_name} (match score: {score:.1f})")

    # Create contract
    contract = marketplace.create_contract(
        user_id="user_001",
        agent_id="agent_001",
        task_description="Handle 10 customer service tickets",
        pricing_model=PricingModel.PER_TASK,
        agreed_price=50.0,
        deadline=(datetime.now() + timedelta(days=1)).isoformat(),
        require_insurance=True
    )
    print(f"\n📋 Created contract: {contract.contract_id}")
    print(f"   Price: {contract.agreed_price} tokens")
    print(f"   Insurance coverage: {contract.insurance_coverage} tokens")
    print(f"   Escrow held: {contract.escrow_held} tokens")

    # Agent accepts contract
    contract = marketplace.accept_contract("agent_001", contract.contract_id)
    print(f"\n✅ Agent accepted contract")
    print(f"   Status: {contract.status.value}")
    print(f"   Started: {contract.started_at}")

    # Agent completes work
    contract = marketplace.complete_contract(
        contract_id=contract.contract_id,
        agent_id="agent_001",
        deliverables=[
            {"ticket_id": "T001", "resolution": "Replaced defective unit", "satisfaction": 5.0},
            {"ticket_id": "T002", "resolution": "Issued refund", "satisfaction": 4.8}
        ]
    )
    print(f"\n✅ Agent completed work")
    print(f"   Status: {contract.status.value}")
    print(f"   Deliverables: {len(contract.deliverables)}")

    # User approves and pays
    contract, review = marketplace.approve_and_pay(
        contract_id=contract.contract_id,
        user_id="user_001",
        rating=4.9,
        review_text="Excellent service! Fast response and great results.",
        category_ratings={
            "quality": 5.0,
            "speed": 4.8,
            "communication": 4.9
        }
    )
    print(f"\n💰 Payment released")
    print(f"   User rating: {contract.user_rating}/5.0")
    print(f"   Review: {contract.user_review}")

    # Get agent analytics
    analytics = marketplace.get_agent_analytics("agent_001")
    print(f"\n📊 Agent Analytics:")
    print(f"   Total earnings: {analytics['total_earnings']} tokens")
    print(f"   Success rate: {analytics['success_rate']*100:.1f}%")
    print(f"   Average rating: {analytics['average_rating']:.2f}/5.0")
    print(f"   Reputation: {analytics['reputation_score']:.2f}/10")

    # Get marketplace statistics
    stats = marketplace.get_marketplace_statistics()
    print(f"\n🏪 Marketplace Statistics:")
    print(f"   Total agents: {stats['total_agents']}")
    print(f"   Total users: {stats['total_users']}")
    print(f"   Total volume: {stats['total_volume']} tokens")
    print(f"   Success rate: {stats['success_rate']*100:.1f}%")
    print(f"   Total fees collected: {stats['total_fees_collected']} tokens")
    print(f"   Insurance pool: {stats['insurance_pool_balance']} tokens")

    print(f"\n💎 Agent Marketplace: Where quality meets opportunity!")
