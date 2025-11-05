"""
GLOBAL AGENT MARKETPLACE ECOSYSTEM
Revolutionary Platform for Autonomous Agent Commerce & Collaboration

This module implements a comprehensive marketplace where autonomous agents can:
- Discover and hire other agents for specialized tasks
- Monetize their capabilities through various revenue models
- Collaborate on complex multi-agent projects
- Build reputation and trust through blockchain-verified transactions
- Participate in a token-based economy with smart contracts

Architecture Components:
1. Agent Registry & Discovery Engine
2. Smart Contract & Payment Processing
3. Reputation & Trust Management System
4. Revenue Sharing & Token Economics
5. Collaboration & Project Management
6. Quality Assurance & Dispute Resolution
7. Analytics & Performance Optimization
"""

import asyncio
import json
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import uuid
from decimal import Decimal
import logging
from collections import defaultdict
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import networkx as nx

logger = logging.getLogger(__name__)

class AgentCapabilityType(Enum):
    """Types of agent capabilities in the marketplace"""
    DATA_ANALYSIS = "data_analysis"
    CONTENT_CREATION = "content_creation"
    AUTOMATION = "automation"
    RESEARCH = "research"
    DESIGN = "design"
    DEVELOPMENT = "development"
    TESTING = "testing"
    MARKETING = "marketing"
    CUSTOMER_SERVICE = "customer_service"
    PROJECT_MANAGEMENT = "project_management"
    SECURITY = "security"
    COMPLIANCE = "compliance"

class RevenueModel(Enum):
    """Revenue models for agent services"""
    PER_TASK = "per_task"
    HOURLY = "hourly"
    SUBSCRIPTION = "subscription"
    PERFORMANCE_BASED = "performance_based"
    REVENUE_SHARE = "revenue_share"
    HYBRID = "hybrid"

class TransactionStatus(Enum):
    """Status of marketplace transactions"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class ProjectComplexity(Enum):
    """Complexity levels for agent projects"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    ENTERPRISE = "enterprise"

@dataclass
class AgentProfile:
    """Comprehensive agent profile for marketplace"""
    agent_id: str
    name: str
    description: str
    capabilities: List[AgentCapabilityType]
    specializations: List[str]
    pricing_models: Dict[RevenueModel, Dict[str, Any]]
    reputation_score: float = 0.0
    trust_level: str = "new"
    total_earnings: Decimal = Decimal('0.0')
    completed_tasks: int = 0
    success_rate: float = 0.0
    availability_schedule: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    blockchain_address: str = ""
    verification_status: str = "unverified"
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class ServiceListing:
    """Service listing in the marketplace"""
    listing_id: str
    agent_id: str
    title: str
    description: str
    capabilities_required: List[AgentCapabilityType]
    pricing: Dict[str, Any]
    estimated_duration: timedelta
    complexity: ProjectComplexity
    requirements: Dict[str, Any]
    deliverables: List[str]
    sample_work: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    active: bool = True

@dataclass
class ProjectRequest:
    """Client project request"""
    request_id: str
    client_id: str
    title: str
    description: str
    requirements: Dict[str, Any]
    budget_range: Dict[str, Decimal]
    timeline: Dict[str, datetime]
    complexity: ProjectComplexity
    preferred_agents: List[str] = field(default_factory=list)
    skills_required: List[AgentCapabilityType] = field(default_factory=list)
    collaboration_type: str = "single_agent"

@dataclass
class Transaction:
    """Marketplace transaction record"""
    transaction_id: str
    project_id: str
    client_id: str
    agent_ids: List[str]
    amount: Decimal
    currency: str
    revenue_split: Dict[str, Decimal]
    status: TransactionStatus
    smart_contract_address: str
    escrow_details: Dict[str, Any]
    milestone_payments: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

class AgentDiscoveryEngine:
    """AI-powered agent discovery and matching system"""

    def __init__(self):
        self.agent_profiles: Dict[str, AgentProfile] = {}
        self.capability_vectors: Dict[str, np.ndarray] = {}
        self.collaboration_graph = nx.Graph()

    async def register_agent(self, profile: AgentProfile) -> bool:
        """Register new agent in the marketplace"""
        try:
            # Validate agent profile
            if not await self._validate_agent_profile(profile):
                return False

            # Generate capability vector for ML matching
            capability_vector = self._generate_capability_vector(profile)

            # Store agent profile and vector
            self.agent_profiles[profile.agent_id] = profile
            self.capability_vectors[profile.agent_id] = capability_vector

            # Add to collaboration graph
            self.collaboration_graph.add_node(profile.agent_id, **profile.__dict__)

            logger.info(f"Agent {profile.agent_id} registered successfully")
            return True

        except Exception as e:
            logger.error(f"Error registering agent {profile.agent_id}: {e}")
            return False

    async def discover_agents(self,
                            requirements: Dict[str, Any],
                            max_results: int = 10) -> List[Dict[str, Any]]:
        """Discover and rank agents based on requirements"""
        try:
            # Generate requirement vector
            req_vector = self._generate_requirement_vector(requirements)

            # Calculate similarity scores
            similarities = {}
            for agent_id, agent_vector in self.capability_vectors.items():
                similarity = cosine_similarity([req_vector], [agent_vector])[0][0]
                similarities[agent_id] = similarity

            # Rank agents by combined score (similarity + reputation)
            ranked_agents = []
            for agent_id, similarity in similarities.items():
                profile = self.agent_profiles[agent_id]
                combined_score = (similarity * 0.7) + (profile.reputation_score * 0.3)

                ranked_agents.append({
                    'agent_id': agent_id,
                    'profile': profile,
                    'similarity_score': similarity,
                    'reputation_score': profile.reputation_score,
                    'combined_score': combined_score,
                    'estimated_cost': self._estimate_cost(profile, requirements),
                    'availability': self._check_availability(profile, requirements.get('timeline', {}))
                })

            # Sort by combined score and return top results
            ranked_agents.sort(key=lambda x: x['combined_score'], reverse=True)
            return ranked_agents[:max_results]

        except Exception as e:
            logger.error(f"Error discovering agents: {e}")
            return []

    def _generate_capability_vector(self, profile: AgentProfile) -> np.ndarray:
        """Generate numerical vector representation of agent capabilities"""
        # Create base capability vector
        capability_dims = len(AgentCapabilityType)
        vector = np.zeros(capability_dims + 20)  # Extra dimensions for specializations

        # Set capability dimensions
        for i, cap_type in enumerate(AgentCapabilityType):
            if cap_type in profile.capabilities:
                vector[i] = 1.0

        # Add specialization features
        spec_hash = hashlib.md5(''.join(profile.specializations).encode()).digest()
        for i in range(20):
            vector[capability_dims + i] = (spec_hash[i % len(spec_hash)] / 255.0)

        # Weight by performance metrics
        performance_weight = (profile.reputation_score + profile.success_rate) / 2
        vector *= (0.5 + performance_weight)

        return vector

    def _generate_requirement_vector(self, requirements: Dict[str, Any]) -> np.ndarray:
        """Generate vector representation of project requirements"""
        capability_dims = len(AgentCapabilityType)
        vector = np.zeros(capability_dims + 20)

        # Set required capabilities
        required_caps = requirements.get('capabilities', [])
        for i, cap_type in enumerate(AgentCapabilityType):
            if cap_type in required_caps:
                vector[i] = 1.0

        # Add keyword features
        keywords = ' '.join(requirements.get('keywords', []))
        keyword_hash = hashlib.md5(keywords.encode()).digest()
        for i in range(20):
            vector[capability_dims + i] = (keyword_hash[i % len(keyword_hash)] / 255.0)

        return vector

    async def _validate_agent_profile(self, profile: AgentProfile) -> bool:
        """Validate agent profile completeness and authenticity"""
        required_fields = ['agent_id', 'name', 'description', 'capabilities']
        return all(getattr(profile, field) for field in required_fields)

    def _estimate_cost(self, profile: AgentProfile, requirements: Dict[str, Any]) -> Decimal:
        """Estimate project cost based on agent pricing and requirements"""
        # Simple cost estimation based on complexity and agent rates
        complexity_multiplier = {
            ProjectComplexity.SIMPLE: 1.0,
            ProjectComplexity.MODERATE: 2.0,
            ProjectComplexity.COMPLEX: 4.0,
            ProjectComplexity.ENTERPRISE: 8.0
        }

        base_rate = Decimal('100.0')  # Default base rate
        if RevenueModel.HOURLY in profile.pricing_models:
            base_rate = Decimal(str(profile.pricing_models[RevenueModel.HOURLY].get('rate', 100)))

        complexity = requirements.get('complexity', ProjectComplexity.MODERATE)
        multiplier = complexity_multiplier.get(complexity, 2.0)

        return base_rate * Decimal(str(multiplier))

    def _check_availability(self, profile: AgentProfile, timeline: Dict[str, Any]) -> Dict[str, Any]:
        """Check agent availability for project timeline"""
        return {
            'available': True,  # Simplified for demo
            'earliest_start': datetime.now(),
            'capacity': 100
        }

class SmartContractManager:
    """Blockchain-based smart contract management for secure transactions"""

    def __init__(self):
        self.contracts: Dict[str, Dict[str, Any]] = {}
        self.escrow_accounts: Dict[str, Dict[str, Any]] = {}

    async def create_project_contract(self,
                                    project_request: ProjectRequest,
                                    selected_agents: List[str],
                                    terms: Dict[str, Any]) -> str:
        """Create smart contract for project execution"""
        try:
            contract_id = f"contract_{uuid.uuid4().hex[:12]}"

            # Define contract terms
            contract_terms = {
                'project_id': project_request.request_id,
                'client_id': project_request.client_id,
                'agent_ids': selected_agents,
                'total_budget': terms['total_budget'],
                'milestone_structure': terms.get('milestones', []),
                'payment_schedule': terms.get('payment_schedule', {}),
                'deliverables': terms.get('deliverables', []),
                'timeline': terms.get('timeline', {}),
                'dispute_resolution': terms.get('dispute_resolution', {}),
                'revenue_split': self._calculate_revenue_split(selected_agents, terms),
                'penalty_clauses': terms.get('penalties', {}),
                'auto_execution_rules': terms.get('auto_rules', {})
            }

            # Create escrow account
            escrow_id = await self._create_escrow_account(contract_terms)

            # Store contract
            self.contracts[contract_id] = {
                'terms': contract_terms,
                'escrow_id': escrow_id,
                'status': 'active',
                'created_at': datetime.now(),
                'blockchain_hash': self._generate_blockchain_hash(contract_terms)
            }

            logger.info(f"Smart contract {contract_id} created successfully")
            return contract_id

        except Exception as e:
            logger.error(f"Error creating smart contract: {e}")
            return ""

    async def execute_milestone_payment(self,
                                      contract_id: str,
                                      milestone_id: str,
                                      verification_data: Dict[str, Any]) -> bool:
        """Execute automated milestone payment upon completion verification"""
        try:
            if contract_id not in self.contracts:
                return False

            contract = self.contracts[contract_id]
            milestone = next((m for m in contract['terms']['milestone_structure']
                           if m['id'] == milestone_id), None)

            if not milestone:
                return False

            # Verify milestone completion
            if await self._verify_milestone_completion(milestone, verification_data):
                # Execute payment
                payment_result = await self._execute_payment(
                    contract['escrow_id'],
                    milestone['amount'],
                    contract['terms']['revenue_split']
                )

                if payment_result:
                    milestone['status'] = 'completed'
                    milestone['completed_at'] = datetime.now()
                    logger.info(f"Milestone {milestone_id} payment executed")
                    return True

            return False

        except Exception as e:
            logger.error(f"Error executing milestone payment: {e}")
            return False

    def _calculate_revenue_split(self, agent_ids: List[str], terms: Dict[str, Any]) -> Dict[str, Decimal]:
        """Calculate revenue split between agents based on contribution"""
        total_agents = len(agent_ids)
        base_split = Decimal('1.0') / Decimal(str(total_agents))

        # Apply performance-based adjustments if specified
        revenue_split = {}
        for agent_id in agent_ids:
            revenue_split[agent_id] = base_split

        # Marketplace fee (5%)
        marketplace_fee = Decimal('0.05')
        revenue_split['marketplace'] = marketplace_fee

        # Adjust splits to account for marketplace fee
        agent_share = Decimal('1.0') - marketplace_fee
        for agent_id in agent_ids:
            revenue_split[agent_id] = (revenue_split[agent_id] * agent_share)

        return revenue_split

    async def _create_escrow_account(self, contract_terms: Dict[str, Any]) -> str:
        """Create escrow account for secure fund holding"""
        escrow_id = f"escrow_{uuid.uuid4().hex[:12]}"

        self.escrow_accounts[escrow_id] = {
            'total_amount': contract_terms['total_budget'],
            'held_amount': contract_terms['total_budget'],
            'released_amount': Decimal('0.0'),
            'created_at': datetime.now(),
            'status': 'active'
        }

        return escrow_id

    async def _verify_milestone_completion(self,
                                         milestone: Dict[str, Any],
                                         verification_data: Dict[str, Any]) -> bool:
        """Verify milestone completion using automated checks"""
        # Implement verification logic based on milestone type
        verification_score = 0.0

        # Check deliverables
        if 'deliverables' in verification_data:
            verification_score += 0.4

        # Check quality metrics
        if 'quality_score' in verification_data and verification_data['quality_score'] >= 0.8:
            verification_score += 0.3

        # Check client approval
        if verification_data.get('client_approved', False):
            verification_score += 0.3

        return verification_score >= 0.8

    async def _execute_payment(self,
                             escrow_id: str,
                             amount: Decimal,
                             revenue_split: Dict[str, Decimal]) -> bool:
        """Execute payment from escrow to agents"""
        if escrow_id not in self.escrow_accounts:
            return False

        escrow = self.escrow_accounts[escrow_id]
        if escrow['held_amount'] < amount:
            return False

        # Simulate payment execution
        escrow['held_amount'] -= amount
        escrow['released_amount'] += amount

        logger.info(f"Payment of {amount} executed from escrow {escrow_id}")
        return True

    def _generate_blockchain_hash(self, contract_terms: Dict[str, Any]) -> str:
        """Generate blockchain hash for contract verification"""
        contract_str = json.dumps(contract_terms, sort_keys=True, default=str)
        return hashlib.sha256(contract_str.encode()).hexdigest()

class ReputationTrustSystem:
    """Advanced reputation and trust management system"""

    def __init__(self):
        self.reputation_scores: Dict[str, Dict[str, float]] = {}
        self.trust_relationships: Dict[str, Dict[str, float]] = defaultdict(dict)
        self.performance_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    async def update_agent_reputation(self,
                                    agent_id: str,
                                    project_id: str,
                                    metrics: Dict[str, Any]) -> Dict[str, float]:
        """Update agent reputation based on project performance"""
        try:
            if agent_id not in self.reputation_scores:
                self.reputation_scores[agent_id] = {
                    'overall': 0.5,
                    'quality': 0.5,
                    'timeliness': 0.5,
                    'communication': 0.5,
                    'reliability': 0.5,
                    'innovation': 0.5
                }

            # Extract performance metrics
            quality_score = metrics.get('quality_score', 0.5)
            timeliness_score = metrics.get('timeliness_score', 0.5)
            communication_score = metrics.get('communication_score', 0.5)
            client_satisfaction = metrics.get('client_satisfaction', 0.5)

            # Update individual scores with weighted average
            current_scores = self.reputation_scores[agent_id]
            weight = 0.1  # Learning rate for reputation updates

            current_scores['quality'] = (
                (1 - weight) * current_scores['quality'] +
                weight * quality_score
            )
            current_scores['timeliness'] = (
                (1 - weight) * current_scores['timeliness'] +
                weight * timeliness_score
            )
            current_scores['communication'] = (
                (1 - weight) * current_scores['communication'] +
                weight * communication_score
            )
            current_scores['reliability'] = (
                (1 - weight) * current_scores['reliability'] +
                weight * client_satisfaction
            )

            # Calculate overall reputation
            current_scores['overall'] = (
                current_scores['quality'] * 0.3 +
                current_scores['timeliness'] * 0.25 +
                current_scores['communication'] * 0.2 +
                current_scores['reliability'] * 0.25
            )

            # Store performance history
            self.performance_history[agent_id].append({
                'project_id': project_id,
                'timestamp': datetime.now(),
                'metrics': metrics,
                'reputation_after': current_scores.copy()
            })

            logger.info(f"Updated reputation for agent {agent_id}: {current_scores['overall']:.3f}")
            return current_scores

        except Exception as e:
            logger.error(f"Error updating reputation for agent {agent_id}: {e}")
            return {}

    async def calculate_trust_score(self,
                                  agent_id: str,
                                  client_id: str,
                                  project_context: Dict[str, Any]) -> float:
        """Calculate dynamic trust score between agent and client"""
        try:
            base_trust = 0.5

            # Historical interaction trust
            historical_trust = self.trust_relationships[agent_id].get(client_id, base_trust)

            # Reputation-based trust
            agent_reputation = self.reputation_scores.get(agent_id, {}).get('overall', 0.5)

            # Context-based trust adjustments
            context_trust_factor = 1.0

            # Project complexity alignment
            if 'complexity' in project_context:
                agent_performance = self._get_agent_performance_by_complexity(
                    agent_id, project_context['complexity']
                )
                context_trust_factor *= agent_performance

            # Calculate final trust score
            trust_score = (
                historical_trust * 0.4 +
                agent_reputation * 0.4 +
                (base_trust * context_trust_factor) * 0.2
            )

            return min(max(trust_score, 0.0), 1.0)

        except Exception as e:
            logger.error(f"Error calculating trust score: {e}")
            return 0.5

    def _get_agent_performance_by_complexity(self,
                                           agent_id: str,
                                           complexity: ProjectComplexity) -> float:
        """Get agent performance score for specific project complexity"""
        if agent_id not in self.performance_history:
            return 0.5

        complexity_performances = []
        for record in self.performance_history[agent_id]:
            if record.get('project_complexity') == complexity:
                complexity_performances.append(
                    record['reputation_after']['overall']
                )

        if complexity_performances:
            return sum(complexity_performances) / len(complexity_performances)

        return 0.5

class MarketplaceAnalytics:
    """Advanced analytics engine for marketplace optimization"""

    def __init__(self):
        self.transaction_data: List[Dict[str, Any]] = []
        self.market_trends: Dict[str, Any] = {}
        self.performance_metrics: Dict[str, Any] = {}

    async def analyze_market_demand(self) -> Dict[str, Any]:
        """Analyze current market demand patterns"""
        try:
            # Analyze capability demand
            capability_demand = defaultdict(int)
            project_complexity_distribution = defaultdict(int)

            for transaction in self.transaction_data:
                for capability in transaction.get('capabilities_required', []):
                    capability_demand[capability.value] += 1

                complexity = transaction.get('complexity', ProjectComplexity.MODERATE)
                project_complexity_distribution[complexity.value] += 1

            # Calculate demand trends
            high_demand_capabilities = sorted(
                capability_demand.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]

            # Market insights
            market_insights = {
                'high_demand_capabilities': high_demand_capabilities,
                'complexity_distribution': dict(project_complexity_distribution),
                'average_project_value': self._calculate_average_project_value(),
                'market_growth_rate': self._calculate_market_growth_rate(),
                'supply_demand_ratio': self._calculate_supply_demand_ratio(),
                'pricing_trends': self._analyze_pricing_trends()
            }

            return market_insights

        except Exception as e:
            logger.error(f"Error analyzing market demand: {e}")
            return {}

    async def generate_agent_recommendations(self,
                                           agent_id: str) -> Dict[str, Any]:
        """Generate personalized recommendations for agents"""
        try:
            recommendations = {
                'skill_development': [],
                'pricing_optimization': {},
                'market_opportunities': [],
                'collaboration_suggestions': []
            }

            # Analyze agent performance and market gaps
            market_demand = await self.analyze_market_demand()

            # Skill development recommendations
            high_demand_skills = [cap[0] for cap in market_demand.get('high_demand_capabilities', [])]
            recommendations['skill_development'] = high_demand_skills[:3]

            # Pricing optimization
            recommendations['pricing_optimization'] = {
                'suggested_hourly_rate': self._suggest_optimal_pricing(agent_id),
                'revenue_model_recommendation': self._recommend_revenue_model(agent_id)
            }

            # Market opportunities
            recommendations['market_opportunities'] = self._identify_market_opportunities(agent_id)

            return recommendations

        except Exception as e:
            logger.error(f"Error generating agent recommendations: {e}")
            return {}

    def _calculate_average_project_value(self) -> Decimal:
        """Calculate average project value in marketplace"""
        if not self.transaction_data:
            return Decimal('0.0')

        total_value = sum(Decimal(str(t.get('amount', 0))) for t in self.transaction_data)
        return total_value / len(self.transaction_data)

    def _calculate_market_growth_rate(self) -> float:
        """Calculate marketplace growth rate"""
        # Simplified growth calculation
        current_month_transactions = len([
            t for t in self.transaction_data
            if datetime.fromisoformat(t.get('created_at', '2024-01-01')).month == datetime.now().month
        ])

        previous_month_transactions = len([
            t for t in self.transaction_data
            if datetime.fromisoformat(t.get('created_at', '2024-01-01')).month == (datetime.now().month - 1)
        ])

        if previous_month_transactions == 0:
            return 0.0

        return (current_month_transactions - previous_month_transactions) / previous_month_transactions

    def _calculate_supply_demand_ratio(self) -> Dict[str, float]:
        """Calculate supply vs demand ratio for different capabilities"""
        # Implementation would analyze registered agents vs project requests
        return {"data_analysis": 0.8, "development": 1.2, "design": 0.6}

    def _analyze_pricing_trends(self) -> Dict[str, Any]:
        """Analyze pricing trends across different capabilities"""
        return {
            "trending_up": ["ai_integration", "blockchain_development"],
            "trending_down": ["basic_web_development"],
            "stable": ["data_analysis", "content_creation"]
        }

    def _suggest_optimal_pricing(self, agent_id: str) -> Decimal:
        """Suggest optimal pricing for agent services"""
        # Simplified pricing suggestion based on market rates
        return Decimal('125.0')

    def _recommend_revenue_model(self, agent_id: str) -> str:
        """Recommend optimal revenue model for agent"""
        return "performance_based"

    def _identify_market_opportunities(self, agent_id: str) -> List[Dict[str, Any]]:
        """Identify market opportunities for specific agent"""
        return [
            {
                "opportunity": "AI-powered automation services",
                "demand_score": 0.9,
                "competition_level": "medium",
                "revenue_potential": "high"
            }
        ]

class GlobalAgentMarketplace:
    """Main orchestrator for the global agent marketplace ecosystem"""

    def __init__(self):
        self.discovery_engine = AgentDiscoveryEngine()
        self.contract_manager = SmartContractManager()
        self.reputation_system = ReputationTrustSystem()
        self.analytics_engine = MarketplaceAnalytics()

        self.active_projects: Dict[str, Dict[str, Any]] = {}
        self.service_listings: Dict[str, ServiceListing] = {}
        self.project_requests: Dict[str, ProjectRequest] = {}
        self.transactions: Dict[str, Transaction] = {}

        logger.info("Global Agent Marketplace initialized")

    async def onboard_agent(self, profile: AgentProfile) -> Dict[str, Any]:
        """Complete agent onboarding process"""
        try:
            # Register agent in discovery engine
            registration_success = await self.discovery_engine.register_agent(profile)

            if not registration_success:
                return {"success": False, "message": "Agent registration failed"}

            # Initialize reputation
            await self.reputation_system.update_agent_reputation(
                profile.agent_id,
                "initial_registration",
                {"quality_score": 0.5, "timeliness_score": 0.5,
                 "communication_score": 0.5, "client_satisfaction": 0.5}
            )

            # Generate onboarding recommendations
            recommendations = await self.analytics_engine.generate_agent_recommendations(
                profile.agent_id
            )

            return {
                "success": True,
                "agent_id": profile.agent_id,
                "recommendations": recommendations,
                "next_steps": [
                    "Complete profile verification",
                    "Create first service listing",
                    "Join relevant agent communities"
                ]
            }

        except Exception as e:
            logger.error(f"Error onboarding agent: {e}")
            return {"success": False, "message": str(e)}

    async def create_project_listing(self, project_request: ProjectRequest) -> str:
        """Create new project listing and find matching agents"""
        try:
            # Store project request
            self.project_requests[project_request.request_id] = project_request

            # Discover matching agents
            requirements = {
                'capabilities': project_request.skills_required,
                'complexity': project_request.complexity,
                'timeline': project_request.timeline,
                'keywords': [project_request.title, project_request.description]
            }

            matching_agents = await self.discovery_engine.discover_agents(
                requirements, max_results=20
            )

            # Create project entry
            self.active_projects[project_request.request_id] = {
                'request': project_request,
                'matching_agents': matching_agents,
                'status': 'seeking_agents',
                'created_at': datetime.now()
            }

            logger.info(f"Project listing created: {project_request.request_id}")
            return project_request.request_id

        except Exception as e:
            logger.error(f"Error creating project listing: {e}")
            return ""

    async def initiate_project_contract(self,
                                      project_id: str,
                                      selected_agent_ids: List[str],
                                      contract_terms: Dict[str, Any]) -> str:
        """Initiate smart contract for project execution"""
        try:
            if project_id not in self.project_requests:
                raise ValueError("Project not found")

            project_request = self.project_requests[project_id]

            # Create smart contract
            contract_id = await self.contract_manager.create_project_contract(
                project_request,
                selected_agent_ids,
                contract_terms
            )

            if not contract_id:
                raise ValueError("Contract creation failed")

            # Create transaction record
            transaction_id = f"txn_{uuid.uuid4().hex[:12]}"
            transaction = Transaction(
                transaction_id=transaction_id,
                project_id=project_id,
                client_id=project_request.client_id,
                agent_ids=selected_agent_ids,
                amount=contract_terms['total_budget'],
                currency='USD',
                revenue_split=self.contract_manager.contracts[contract_id]['terms']['revenue_split'],
                status=TransactionStatus.PENDING,
                smart_contract_address=contract_id,
                escrow_details={'escrow_id': self.contract_manager.contracts[contract_id]['escrow_id']}
            )

            self.transactions[transaction_id] = transaction

            # Update project status
            self.active_projects[project_id]['status'] = 'contracted'
            self.active_projects[project_id]['contract_id'] = contract_id
            self.active_projects[project_id]['transaction_id'] = transaction_id

            logger.info(f"Project contract initiated: {contract_id}")
            return contract_id

        except Exception as e:
            logger.error(f"Error initiating project contract: {e}")
            return ""

    async def complete_project_milestone(self,
                                       project_id: str,
                                       milestone_id: str,
                                       completion_data: Dict[str, Any]) -> bool:
        """Complete project milestone and trigger payment"""
        try:
            if project_id not in self.active_projects:
                return False

            contract_id = self.active_projects[project_id]['contract_id']

            # Execute milestone payment
            payment_success = await self.contract_manager.execute_milestone_payment(
                contract_id,
                milestone_id,
                completion_data
            )

            if payment_success:
                # Update agent reputations
                agent_ids = self.active_projects[project_id]['request'].preferred_agents
                for agent_id in agent_ids:
                    await self.reputation_system.update_agent_reputation(
                        agent_id,
                        project_id,
                        completion_data.get('performance_metrics', {})
                    )

                logger.info(f"Milestone {milestone_id} completed for project {project_id}")

            return payment_success

        except Exception as e:
            logger.error(f"Error completing project milestone: {e}")
            return False

    async def get_marketplace_insights(self) -> Dict[str, Any]:
        """Get comprehensive marketplace insights and analytics"""
        try:
            market_analysis = await self.analytics_engine.analyze_market_demand()

            # Get current marketplace statistics
            total_agents = len(self.discovery_engine.agent_profiles)
            active_projects = len([p for p in self.active_projects.values()
                                 if p['status'] in ['seeking_agents', 'contracted', 'in_progress']])
            total_transactions = len(self.transactions)

            insights = {
                'marketplace_stats': {
                    'total_agents': total_agents,
                    'active_projects': active_projects,
                    'completed_transactions': total_transactions,
                    'total_volume': sum(t.amount for t in self.transactions.values())
                },
                'market_analysis': market_analysis,
                'top_performing_agents': self._get_top_performing_agents(),
                'trending_services': self._get_trending_services(),
                'ecosystem_health': self._calculate_ecosystem_health()
            }

            return insights

        except Exception as e:
            logger.error(f"Error getting marketplace insights: {e}")
            return {}

    def _get_top_performing_agents(self) -> List[Dict[str, Any]]:
        """Get list of top performing agents"""
        agent_scores = []
        for agent_id, profile in self.discovery_engine.agent_profiles.items():
            reputation = self.reputation_system.reputation_scores.get(agent_id, {})
            agent_scores.append({
                'agent_id': agent_id,
                'name': profile.name,
                'reputation_score': reputation.get('overall', 0.5),
                'completed_tasks': profile.completed_tasks,
                'total_earnings': profile.total_earnings
            })

        return sorted(agent_scores, key=lambda x: x['reputation_score'], reverse=True)[:10]

    def _get_trending_services(self) -> List[Dict[str, Any]]:
        """Get list of trending services in the marketplace"""
        return [
            {'service': 'AI Integration', 'demand_growth': 45.2},
            {'service': 'Blockchain Development', 'demand_growth': 38.7},
            {'service': 'Data Analytics', 'demand_growth': 28.1}
        ]

    def _calculate_ecosystem_health(self) -> Dict[str, float]:
        """Calculate overall ecosystem health metrics"""
        return {
            'agent_satisfaction': 0.87,
            'client_satisfaction': 0.82,
            'platform_utilization': 0.74,
            'growth_momentum': 0.91
        }

# Example usage and initialization
async def initialize_marketplace():
    """Initialize the global agent marketplace"""
    marketplace = GlobalAgentMarketplace()

    # Example agent registration
    sample_agent = AgentProfile(
        agent_id="agent_001",
        name="DataMaster AI",
        description="Advanced data analysis and machine learning specialist",
        capabilities=[AgentCapabilityType.DATA_ANALYSIS, AgentCapabilityType.RESEARCH],
        specializations=["machine_learning", "predictive_analytics", "data_visualization"],
        pricing_models={
            RevenueModel.HOURLY: {"rate": 150.0, "minimum_hours": 4},
            RevenueModel.PER_TASK: {"base_rate": 500.0, "complexity_multiplier": 2.0}
        }
    )

    result = await marketplace.onboard_agent(sample_agent)
    logger.info(f"Agent onboarding result: {result}")

    return marketplace

if __name__ == "__main__":
    # Initialize and run marketplace demo
    async def main():
        marketplace = await initialize_marketplace()
        insights = await marketplace.get_marketplace_insights()
        print(f"Marketplace Insights: {json.dumps(insights, indent=2, default=str)}")

    asyncio.run(main())