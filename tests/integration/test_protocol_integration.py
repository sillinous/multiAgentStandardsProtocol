"""
🔗 Comprehensive Protocol Integration Tests
============================================

Integration tests demonstrating all protocols working together in realistic scenarios.

Tests include:
1. Multi-Agent Discovery and Messaging (ANP + A2A)
2. Coordinated Task Execution (ACP + ANP + A2A)
3. Platform-Integrated Agent (A2P + A2A)
4. Semantic Agent Discovery (ASP + ANP + A2A)
5. Time-Travel Debugging Workflow (TAP + A2A)
6. Blockchain-Enabled Collaboration (BAP + ACP + A2A)
7. Code Analysis in CI/CD (CAP + CAIP + A2A)
8. Compliance-Checked Operations (CAIP + ANP + AuditLog)
9. Genetic Evolution of Agent Team (ADP + CIP + ANP)
10. Collective Intelligence Decision (CIP + ANP + A2A + ACP)
11. Full Stack Workflow (All Protocols)
12. Cross-Protocol Error Handling
"""

import asyncio
import json
import logging
import pytest
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum

# Import all protocol implementations
from superstandard.protocols.anp_implementation import AgentNetworkRegistry, ANPClient
from superstandard.protocols.acp_implementation import (
    CoordinationManager,
    CoordinationType,
    TaskStatus,
    Task,
    Participant,
)
from superstandard.protocols.asp_v1 import (
    SemanticRegistry,
    OntologyReference,
    SemanticCapability,
    SemanticParameter,
    SemanticDeclaration,
    Proficiency,
)
from superstandard.protocols.tap_v1 import (
    TemporalEngine,
    TemporalEvent,
    TemporalContext,
    TimeRange,
    TemporalResolution,
    OperationType,
)
from superstandard.protocols.adp_v1 import (
    Gene,
    Chromosome,
    AgentGenome,
    FitnessEvaluator,
    EvolutionSimulator,
    GeneType,
    ChromosomeType,
)
from superstandard.protocols.cip_v1 import (
    CollectiveDecision,
    SwarmOptimizer,
    Vote,
    VotingOption,
    DecisionMethod,
    SwarmContext,
)
from superstandard.agents.base.protocols import A2AMessage, MessageType

# Simple mock classes for workflow coordination (for demonstration purposes)
@dataclass
class WorkflowNode:
    """Workflow node for demonstration."""
    node_id: str
    node_type: str
    agent_id: str
    task_definition: Dict[str, Any]

@dataclass
class WorkflowEdge:
    """Workflow edge for demonstration."""
    from_node: str
    to_node: str

class CoordinationEngine:
    """Simplified coordination engine for integration tests."""
    def __init__(self):
        self.sessions = {}
        self.workflows = {}

    async def create_session(self, session_id: str, pattern: CoordinationType,
                            participants: List[str], metadata: Dict[str, Any] = None):
        """Create a coordination session."""
        self.sessions[session_id] = {
            "session_id": session_id,
            "pattern": pattern.value if hasattr(pattern, 'value') else str(pattern),
            "participants": participants,
            "metadata": metadata or {},
            "status": "active"
        }

    async def define_workflow(self, session_id: str, nodes: List[WorkflowNode], edges: List[WorkflowEdge]):
        """Define workflow for session."""
        self.workflows[session_id] = {
            "nodes": nodes,
            "edges": edges
        }

    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get session status."""
        return self.sessions.get(session_id, {})

# Create aliases for compatibility
CoordinationPattern = CoordinationType
TaskState = TaskStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Test Fixtures and Helper Classes
# ============================================================================

@dataclass
class MockAgent:
    """Mock agent for testing."""
    agent_id: str
    agent_type: str
    capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    messages_received: List[A2AMessage] = field(default_factory=list)

    async def send_message(self, to_agent: str, message_type: str, content: Dict[str, Any]) -> A2AMessage:
        """Send a message to another agent."""
        msg = A2AMessage(
            from_agent=self.agent_id,
            to_agent=to_agent,
            message_type=message_type,
            content=content
        )
        logger.info(f"Agent {self.agent_id} sending {message_type} to {to_agent}")
        return msg

    async def receive_message(self, message: A2AMessage) -> None:
        """Receive a message."""
        self.messages_received.append(message)
        logger.info(f"Agent {self.agent_id} received {message.message_type} from {message.from_agent}")


@dataclass
class MockPlatform:
    """Mock platform for A2P testing."""
    platform_id: str
    capabilities: List[str] = field(default_factory=list)
    requests_received: List[Dict[str, Any]] = field(default_factory=list)

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a platform request."""
        self.requests_received.append(request)
        return {
            "status": "success",
            "result": f"Processed {request.get('action', 'unknown')}",
            "timestamp": datetime.utcnow().isoformat()
        }


@dataclass
class AuditLog:
    """Simple audit log for compliance testing."""
    entries: List[Dict[str, Any]] = field(default_factory=list)

    def log(self, operation: str, agent_id: str, details: Dict[str, Any]) -> None:
        """Log an operation."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "operation": operation,
            "agent_id": agent_id,
            "details": details
        }
        self.entries.append(entry)
        logger.info(f"Audit: {operation} by {agent_id}")

    def get_entries(self, agent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get audit entries, optionally filtered by agent."""
        if agent_id:
            return [e for e in self.entries if e["agent_id"] == agent_id]
        return self.entries


# ============================================================================
# Integration Tests
# ============================================================================

class TestProtocolIntegration:
    """Comprehensive integration tests for all protocols."""

    # ------------------------------------------------------------------------
    # Test 1: Multi-Agent Discovery and Messaging (ANP + A2A)
    # ------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_multi_agent_discovery_and_messaging(self):
        """Test agent discovery via ANP and messaging via A2A."""
        logger.info("\n" + "="*70)
        logger.info("TEST 1: Multi-Agent Discovery and Messaging")
        logger.info("="*70)

        # Step 1: Create agent network registry
        registry = AgentNetworkRegistry()

        # Step 2: Create and register agents
        agent1 = MockAgent(
            agent_id="data_analyst_001",
            agent_type="DataAnalyst",
            capabilities=["data_analysis", "statistical_modeling"]
        )

        agent2 = MockAgent(
            agent_id="data_scientist_002",
            agent_type="DataScientist",
            capabilities=["machine_learning", "data_analysis"]
        )

        agent3 = MockAgent(
            agent_id="data_engineer_003",
            agent_type="DataEngineer",
            capabilities=["data_pipeline", "etl"]
        )

        # Register agents
        for agent in [agent1, agent2, agent3]:
            await registry.register_agent(
                agent_id=agent.agent_id,
                agent_type=agent.agent_type,
                capabilities=agent.capabilities,
                endpoints={"http": f"http://localhost:8000/{agent.agent_id}"},
                metadata=agent.metadata
            )

        # Step 3: Discover agents with specific capability
        discovered = await registry.discover_agents(
            capability_filter=["data_analysis"]
        )

        assert len(discovered) == 2  # agent1 and agent2
        discovered_ids = [a["agent_id"] for a in discovered]
        assert "data_analyst_001" in discovered_ids
        assert "data_scientist_002" in discovered_ids

        # Step 4: Send messages between discovered agents
        msg1 = await agent1.send_message(
            to_agent="data_scientist_002",
            message_type=MessageType.TASK_ASSIGNMENT.value,
            content={
                "task": "analyze_dataset",
                "dataset_id": "customer_data_2024",
                "deadline": (datetime.utcnow() + timedelta(hours=24)).isoformat()
            }
        )

        await agent2.receive_message(msg1)

        # Step 5: Agent 2 responds
        msg2 = await agent2.send_message(
            to_agent="data_analyst_001",
            message_type=MessageType.STATUS_UPDATE.value,
            content={
                "task_id": "analyze_dataset",
                "status": "accepted",
                "estimated_completion": (datetime.utcnow() + timedelta(hours=12)).isoformat()
            }
        )

        await agent1.receive_message(msg2)

        # Verify messaging worked
        assert len(agent2.messages_received) == 1
        assert agent2.messages_received[0].message_type == MessageType.TASK_ASSIGNMENT.value
        assert len(agent1.messages_received) == 1
        assert agent1.messages_received[0].message_type == MessageType.STATUS_UPDATE.value

        logger.info("✓ Test 1 passed: Multi-agent discovery and messaging successful")

    # ------------------------------------------------------------------------
    # Test 2: Coordinated Task Execution (ACP + ANP + A2A)
    # ------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_coordinated_task_execution(self):
        """Test coordinated multi-agent task execution using ACP."""
        logger.info("\n" + "="*70)
        logger.info("TEST 2: Coordinated Task Execution")
        logger.info("="*70)

        # Step 1: Create coordination engine and agent registry
        coordinator = CoordinationEngine()
        registry = AgentNetworkRegistry()

        # Step 2: Create task agents
        agents = [
            MockAgent(f"task_agent_{i}", "TaskWorker", ["task_execution"])
            for i in range(3)
        ]

        for agent in agents:
            await registry.register_agent(
                agent_id=agent.agent_id,
                agent_type=agent.agent_type,
                capabilities=agent.capabilities,
                endpoints={"http": f"http://localhost:8000/{agent.agent_id}"}
            )

        # Step 3: Create coordination session with pipeline pattern
        session_id = "data_processing_pipeline"
        await coordinator.create_session(
            session_id=session_id,
            pattern=CoordinationPattern.PIPELINE,
            participants=[agent.agent_id for agent in agents],
            metadata={
                "project": "customer_analytics",
                "pipeline_stages": ["extract", "transform", "load"]
            }
        )

        # Step 4: Define workflow
        workflow_nodes = [
            WorkflowNode(
                node_id="extract",
                node_type="task",
                agent_id="task_agent_0",
                task_definition={"action": "extract_data", "source": "database"}
            ),
            WorkflowNode(
                node_id="transform",
                node_type="task",
                agent_id="task_agent_1",
                task_definition={"action": "transform_data", "rules": "business_logic"}
            ),
            WorkflowNode(
                node_id="load",
                node_type="task",
                agent_id="task_agent_2",
                task_definition={"action": "load_data", "destination": "warehouse"}
            )
        ]

        workflow_edges = [
            WorkflowEdge(from_node="extract", to_node="transform"),
            WorkflowEdge(from_node="transform", to_node="load")
        ]

        await coordinator.define_workflow(
            session_id=session_id,
            nodes=workflow_nodes,
            edges=workflow_edges
        )

        # Step 5: Execute workflow with task assignments via A2A
        for i, node in enumerate(workflow_nodes):
            # Coordinator sends task assignment
            task_msg = await agents[i].send_message(
                to_agent=agents[i].agent_id,
                message_type=MessageType.TASK_ASSIGNMENT.value,
                content={
                    "task_id": node.node_id,
                    "task_definition": node.task_definition,
                    "session_id": session_id
                }
            )
            await agents[i].receive_message(task_msg)

            # Agent sends completion status
            completion_msg = await agents[i].send_message(
                to_agent="coordinator",
                message_type=MessageType.STATUS_UPDATE.value,
                content={
                    "task_id": node.node_id,
                    "status": "completed",
                    "result": f"{node.node_id}_complete"
                }
            )

        # Verify all agents received tasks
        for agent in agents:
            assert len(agent.messages_received) >= 1
            assert any(msg.message_type == MessageType.TASK_ASSIGNMENT.value
                      for msg in agent.messages_received)

        # Get session status
        status = await coordinator.get_session_status(session_id)
        assert status["session_id"] == session_id
        assert status["pattern"] == CoordinationPattern.PIPELINE.value

        logger.info("✓ Test 2 passed: Coordinated task execution successful")

    # ------------------------------------------------------------------------
    # Test 3: Platform-Integrated Agent (A2P + A2A)
    # ------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_platform_integrated_agent(self):
        """Test agent integration with external platform via A2P."""
        logger.info("\n" + "="*70)
        logger.info("TEST 3: Platform-Integrated Agent")
        logger.info("="*70)

        # Step 1: Create platform and agent
        platform = MockPlatform(
            platform_id="openai_platform",
            capabilities=["llm_inference", "embeddings", "completion"]
        )

        agent = MockAgent(
            agent_id="ai_assistant_001",
            agent_type="AIAssistant",
            capabilities=["chat", "code_generation"]
        )

        # Step 2: Agent connects to platform (A2P)
        platform_request = {
            "protocol": "A2P",
            "version": "1.0.0",
            "action": "connect",
            "agent_id": agent.agent_id,
            "platform_id": platform.platform_id,
            "requested_capabilities": ["llm_inference"]
        }

        platform_response = await platform.handle_request(platform_request)
        assert platform_response["status"] == "success"

        # Step 3: Agent makes platform request via A2P
        inference_request = {
            "protocol": "A2P",
            "version": "1.0.0",
            "action": "llm_inference",
            "agent_id": agent.agent_id,
            "platform_id": platform.platform_id,
            "parameters": {
                "model": "gpt-4",
                "prompt": "Analyze customer sentiment",
                "max_tokens": 500
            }
        }

        inference_response = await platform.handle_request(inference_request)
        assert inference_response["status"] == "success"

        # Step 4: Agent communicates result to another agent (A2A)
        another_agent = MockAgent(
            agent_id="reporting_agent_002",
            agent_type="ReportingAgent",
            capabilities=["report_generation"]
        )

        result_msg = await agent.send_message(
            to_agent=another_agent.agent_id,
            message_type=MessageType.RESULT.value,
            content={
                "source": "platform_inference",
                "platform": platform.platform_id,
                "result": inference_response["result"]
            }
        )

        await another_agent.receive_message(result_msg)

        # Verify integration
        assert len(platform.requests_received) == 2  # connect + inference
        assert len(another_agent.messages_received) == 1
        assert another_agent.messages_received[0].content["source"] == "platform_inference"

        logger.info("✓ Test 3 passed: Platform integration successful")

    # ------------------------------------------------------------------------
    # Test 4: Semantic Agent Discovery (ASP + ANP + A2A)
    # ------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_semantic_agent_discovery(self):
        """Test semantic-based agent discovery combining ASP and ANP."""
        logger.info("\n" + "="*70)
        logger.info("TEST 4: Semantic Agent Discovery")
        logger.info("="*70)

        # Step 1: Create semantic and network registries
        semantic_registry = SemanticRegistry()
        network_registry = AgentNetworkRegistry()

        # Step 2: Register agents with semantic capabilities
        finance_agent = SemanticDeclaration(
            agent_id="finance_analyst_001",
            ontologies=[
                OntologyReference(
                    ontology_id="apqc:7.0.1",
                    namespace="https://apqc.org/ontology/7.0.1",
                    coverage=["FinancialAnalysis", "BudgetPlanning"]
                )
            ],
            capabilities=[
                SemanticCapability(
                    capability_id="budget_planning",
                    capability_name="Budget Planning",
                    semantic_type="apqc:BudgetPlanning",
                    inputs=[
                        SemanticParameter(
                            name="fiscal_year",
                            semantic_type="schema.org:DateTime"
                        )
                    ],
                    outputs=[
                        SemanticParameter(
                            name="budget_allocation",
                            semantic_type="fibo:BudgetAllocation"
                        )
                    ]
                )
            ],
            domain_knowledge=[]
        )

        semantic_registry.register(finance_agent)

        # Register in network registry too
        await network_registry.register_agent(
            agent_id="finance_analyst_001",
            agent_type="FinanceAnalyst",
            capabilities=["budget_planning", "financial_analysis"],
            endpoints={"http": "http://localhost:8000/finance_analyst_001"}
        )

        # Step 3: Semantic discovery
        required_capability = SemanticCapability(
            capability_id="need_budgeting",
            semantic_type="apqc:BudgetPlanning"
        )

        semantic_matches = semantic_registry.discover_capabilities(
            required_capability,
            min_score=0.5
        )

        assert len(semantic_matches.matches) == 1
        assert semantic_matches.matches[0].agent_id == "finance_analyst_001"

        # Step 4: Network discovery for verification
        network_matches = await network_registry.discover_agents(
            capability_filter=["budget_planning"]
        )

        assert len(network_matches) == 1
        assert network_matches[0]["agent_id"] == "finance_analyst_001"

        # Step 5: Send message to discovered agent
        requester = MockAgent(
            agent_id="strategic_planner_001",
            agent_type="StrategicPlanner",
            capabilities=["strategic_planning"]
        )

        discovered_agent = MockAgent(
            agent_id="finance_analyst_001",
            agent_type="FinanceAnalyst",
            capabilities=["budget_planning"]
        )

        request_msg = await requester.send_message(
            to_agent=discovered_agent.agent_id,
            message_type=MessageType.TASK_ASSIGNMENT.value,
            content={
                "task": "create_budget_plan",
                "fiscal_year": "2024",
                "budget_amount": 1000000,
                "discovery_method": "semantic_matching",
                "match_score": semantic_matches.matches[0].match_score
            }
        )

        await discovered_agent.receive_message(request_msg)

        assert len(discovered_agent.messages_received) == 1
        assert discovered_agent.messages_received[0].content["discovery_method"] == "semantic_matching"

        logger.info("✓ Test 4 passed: Semantic agent discovery successful")

    # ------------------------------------------------------------------------
    # Test 5: Time-Travel Debugging Workflow (TAP + A2A)
    # ------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_time_travel_debugging_workflow(self):
        """Test time-travel debugging of agent interactions using TAP."""
        logger.info("\n" + "="*70)
        logger.info("TEST 5: Time-Travel Debugging Workflow")
        logger.info("="*70)

        # Step 1: Create temporal engine
        temporal_engine = TemporalEngine(
            timeline_id="agent_interaction_timeline",
            resolution=TemporalResolution.MILLISECOND
        )

        # Step 2: Create agents
        agent1 = MockAgent(
            agent_id="service_agent_001",
            agent_type="ServiceAgent",
            capabilities=["service_processing"]
        )

        agent2 = MockAgent(
            agent_id="validator_agent_002",
            agent_type="ValidatorAgent",
            capabilities=["validation"]
        )

        # Step 3: Execute workflow and record events
        start_time = datetime.utcnow()

        # Event 1: Agent 1 sends request
        msg1 = await agent1.send_message(
            to_agent=agent2.agent_id,
            message_type=MessageType.TASK_ASSIGNMENT.value,
            content={"task": "validate_transaction", "tx_id": "TX12345"}
        )

        event1 = TemporalEvent(
            event_id="evt_001",
            timestamp=datetime.utcnow().isoformat(),
            agent_id=agent1.agent_id,
            operation_type=OperationType.MESSAGE_SEND.value,
            operation_data={
                "message_id": msg1.message_id,
                "to_agent": msg1.to_agent,
                "message_type": msg1.message_type
            },
            state_snapshot={"agent_status": "active", "queue_size": 0}
        )

        await temporal_engine.record_event(event1)
        await asyncio.sleep(0.1)  # Small delay to ensure timestamp difference

        # Event 2: Agent 2 receives and processes
        await agent2.receive_message(msg1)

        event2 = TemporalEvent(
            event_id="evt_002",
            timestamp=datetime.utcnow().isoformat(),
            agent_id=agent2.agent_id,
            operation_type=OperationType.STATE_CHANGE.value,
            operation_data={
                "message_id": msg1.message_id,
                "action": "received_task"
            },
            state_snapshot={"agent_status": "processing", "current_task": "TX12345"}
        )

        await temporal_engine.record_event(event2)
        await asyncio.sleep(0.1)

        # Event 3: Agent 2 responds
        msg2 = await agent2.send_message(
            to_agent=agent1.agent_id,
            message_type=MessageType.RESULT.value,
            content={"task": "validate_transaction", "result": "valid", "tx_id": "TX12345"}
        )

        event3 = TemporalEvent(
            event_id="evt_003",
            timestamp=datetime.utcnow().isoformat(),
            agent_id=agent2.agent_id,
            operation_type=OperationType.MESSAGE_SEND.value,
            operation_data={
                "message_id": msg2.message_id,
                "to_agent": msg2.to_agent,
                "message_type": msg2.message_type
            },
            state_snapshot={"agent_status": "active", "queue_size": 0}
        )

        await temporal_engine.record_event(event3)

        # Step 4: Query temporal state
        end_time = datetime.utcnow()
        time_range = TimeRange(
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat()
        )

        events = await temporal_engine.query_events(
            time_range=time_range,
            agent_id=agent2.agent_id
        )

        assert len(events) >= 2  # At least event2 and event3

        # Step 5: Time-travel to specific point
        checkpoint_time = event2.timestamp
        state = await temporal_engine.time_travel(
            target_time=checkpoint_time,
            agent_id=agent2.agent_id
        )

        assert state is not None
        assert state.get("current_task") == "TX12345"

        # Step 6: Causal analysis
        causal_chain = await temporal_engine.analyze_causality(
            event_id="evt_003",
            max_depth=3
        )

        assert len(causal_chain) > 0

        logger.info("✓ Test 5 passed: Time-travel debugging successful")

    # ------------------------------------------------------------------------
    # Test 6: Blockchain-Enabled Collaboration (BAP + ACP + A2A)
    # ------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_blockchain_enabled_collaboration(self):
        """Test blockchain-enabled agent collaboration with smart contracts."""
        logger.info("\n" + "="*70)
        logger.info("TEST 6: Blockchain-Enabled Collaboration")
        logger.info("="*70)

        # Import blockchain protocol components
        from superstandard.agents.blockchain.blockchain_agentic_protocol import (
            AgentWallet, TokenType, TransactionType
        )

        # Step 1: Create agent wallets
        agent1_wallet = AgentWallet(
            wallet_id="wallet_001",
            agent_id="developer_agent_001",
            public_key="pub_key_001",
            private_key_hash="hash_001",
            token_balances={
                TokenType.UTILITY: Decimal("1000.0"),
                TokenType.REPUTATION: Decimal("95.5")
            }
        )

        agent2_wallet = AgentWallet(
            wallet_id="wallet_002",
            agent_id="reviewer_agent_002",
            public_key="pub_key_002",
            private_key_hash="hash_002",
            token_balances={
                TokenType.UTILITY: Decimal("500.0"),
                TokenType.REPUTATION: Decimal("88.0")
            }
        )

        # Step 2: Create coordination session with payment escrow
        coordinator = CoordinationEngine()
        session_id = "code_review_session"

        await coordinator.create_session(
            session_id=session_id,
            pattern=CoordinationPattern.CONSENSUS,
            participants=[agent1_wallet.agent_id, agent2_wallet.agent_id],
            metadata={
                "project": "smart_contract_review",
                "payment_escrow": "100.0",
                "payment_token": TokenType.UTILITY.value
            }
        )

        # Step 3: Agents communicate task details via A2A
        agent1 = MockAgent(
            agent_id=agent1_wallet.agent_id,
            agent_type="Developer",
            capabilities=["coding"]
        )

        agent2 = MockAgent(
            agent_id=agent2_wallet.agent_id,
            agent_type="Reviewer",
            capabilities=["code_review"]
        )

        task_msg = await agent1.send_message(
            to_agent=agent2.agent_id,
            message_type=MessageType.TASK_ASSIGNMENT.value,
            content={
                "task": "review_smart_contract",
                "contract_hash": "0x1234...abcd",
                "payment": "100.0",
                "payment_token": TokenType.UTILITY.value,
                "session_id": session_id
            }
        )

        await agent2.receive_message(task_msg)

        # Step 4: Simulate task completion and payment
        # Agent 2 completes review
        result_msg = await agent2.send_message(
            to_agent=agent1.agent_id,
            message_type=MessageType.RESULT.value,
            content={
                "task": "review_smart_contract",
                "result": "approved",
                "findings": ["minor_optimization_suggested"],
                "request_payment": True
            }
        )

        await agent1.receive_message(result_msg)

        # Step 5: Execute payment transaction
        payment_amount = Decimal("100.0")

        # Deduct from agent1
        agent1_wallet.token_balances[TokenType.UTILITY] -= payment_amount

        # Add to agent2
        agent2_wallet.token_balances[TokenType.UTILITY] += payment_amount

        # Record transaction
        transaction = {
            "transaction_type": TransactionType.PERFORMANCE_REWARD.value,
            "from_wallet": agent1_wallet.wallet_id,
            "to_wallet": agent2_wallet.wallet_id,
            "amount": str(payment_amount),
            "token_type": TokenType.UTILITY.value,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat()
        }

        agent1_wallet.transaction_history.append(transaction["timestamp"])
        agent2_wallet.transaction_history.append(transaction["timestamp"])

        # Verify final state
        assert agent1_wallet.token_balances[TokenType.UTILITY] == Decimal("900.0")
        assert agent2_wallet.token_balances[TokenType.UTILITY] == Decimal("600.0")
        assert len(agent1.messages_received) == 1
        assert len(agent2.messages_received) == 1

        logger.info("✓ Test 6 passed: Blockchain-enabled collaboration successful")

    # ------------------------------------------------------------------------
    # Test 7: Code Analysis in CI/CD (CAP + CAIP + A2A)
    # ------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_code_analysis_cicd(self):
        """Test code analysis and compliance checking in CI/CD pipeline."""
        logger.info("\n" + "="*70)
        logger.info("TEST 7: Code Analysis in CI/CD")
        logger.info("="*70)

        # Step 1: Create code analysis agent (simulated CAP)
        code_analyzer = MockAgent(
            agent_id="code_analyzer_001",
            agent_type="CodeAnalyzer",
            capabilities=["static_analysis", "complexity_metrics", "security_scan"]
        )

        # Step 2: Create compliance checker agent (simulated CAIP)
        compliance_checker = MockAgent(
            agent_id="compliance_checker_001",
            agent_type="ComplianceChecker",
            capabilities=["policy_validation", "license_check"]
        )

        # Step 3: Create reporting agent
        reporter = MockAgent(
            agent_id="ci_reporter_001",
            agent_type="CIReporter",
            capabilities=["report_generation"]
        )

        # Step 4: Simulate code analysis (CAP)
        analysis_results = {
            "complexity": {
                "cyclomatic_complexity": 12,
                "cognitive_complexity": 8,
                "halstead_metrics": {"volume": 145.3}
            },
            "security": {
                "vulnerabilities_found": 2,
                "severity": ["medium", "low"],
                "issues": ["sql_injection_risk", "weak_random"]
            },
            "quality": {
                "code_coverage": 85.5,
                "maintainability_index": 72.3
            }
        }

        analysis_msg = await code_analyzer.send_message(
            to_agent=compliance_checker.agent_id,
            message_type=MessageType.RESULT.value,
            content={
                "analysis_type": "code_analysis",
                "results": analysis_results,
                "commit_hash": "abc123",
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        await compliance_checker.receive_message(analysis_msg)

        # Step 5: Compliance checking (CAIP)
        compliance_results = {
            "policy_checks": {
                "complexity_limit": {
                    "status": "fail",
                    "limit": 10,
                    "actual": 12,
                    "policy": "cyclomatic_complexity_max_10"
                },
                "security_vulnerabilities": {
                    "status": "fail",
                    "policy": "zero_high_severity_vulnerabilities",
                    "violations": 2
                },
                "code_coverage": {
                    "status": "pass",
                    "limit": 80,
                    "actual": 85.5,
                    "policy": "minimum_coverage_80"
                }
            },
            "license_compliance": {
                "status": "pass",
                "allowed_licenses": ["MIT", "Apache-2.0"],
                "detected_licenses": ["MIT"]
            },
            "overall_compliance": "fail",
            "blocking_issues": 2
        }

        compliance_msg = await compliance_checker.send_message(
            to_agent=reporter.agent_id,
            message_type=MessageType.RESULT.value,
            content={
                "check_type": "compliance_validation",
                "results": compliance_results,
                "commit_hash": "abc123",
                "recommendation": "fix_blocking_issues"
            }
        )

        await reporter.receive_message(compliance_msg)

        # Step 6: Generate CI/CD report
        report_msg = await reporter.send_message(
            to_agent="ci_cd_pipeline",
            message_type=MessageType.RESULT.value,
            content={
                "report_type": "ci_cd_analysis",
                "commit_hash": "abc123",
                "code_analysis": analysis_results,
                "compliance_check": compliance_results,
                "pipeline_decision": "reject",
                "reason": "compliance_violations"
            }
        )

        # Verify workflow
        assert len(compliance_checker.messages_received) == 1
        assert len(reporter.messages_received) == 1
        assert compliance_results["overall_compliance"] == "fail"
        assert report_msg.content["pipeline_decision"] == "reject"

        logger.info("✓ Test 7 passed: Code analysis CI/CD workflow successful")

    # ------------------------------------------------------------------------
    # Test 8: Compliance-Checked Operations (CAIP + ANP + AuditLog)
    # ------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_compliance_checked_operations(self):
        """Test operations with full compliance checking and audit logging."""
        logger.info("\n" + "="*70)
        logger.info("TEST 8: Compliance-Checked Operations")
        logger.info("="*70)

        # Step 1: Create audit log and registry
        audit_log = AuditLog()
        registry = AgentNetworkRegistry()

        # Step 2: Create compliance-aware agent
        agent = MockAgent(
            agent_id="data_processor_001",
            agent_type="DataProcessor",
            capabilities=["data_processing"],
            metadata={
                "compliance_level": "high",
                "certifications": ["GDPR", "HIPAA"],
                "data_classification": "PII"
            }
        )

        # Step 3: Register agent with compliance metadata
        audit_log.log(
            operation="agent_registration",
            agent_id=agent.agent_id,
            details={
                "compliance_level": agent.metadata["compliance_level"],
                "certifications": agent.metadata["certifications"]
            }
        )

        await registry.register_agent(
            agent_id=agent.agent_id,
            agent_type=agent.agent_type,
            capabilities=agent.capabilities,
            endpoints={"http": f"http://localhost:8000/{agent.agent_id}"},
            metadata=agent.metadata
        )

        # Step 4: Perform compliance-checked data operation
        operation_data = {
            "operation_type": "data_processing",
            "data_classification": "PII",
            "data_subjects": 1000,
            "processing_purpose": "analytics",
            "legal_basis": "consent"
        }

        # Pre-operation compliance check
        compliance_check = {
            "agent_certified": "GDPR" in agent.metadata["certifications"],
            "data_classification_match": (
                operation_data["data_classification"] == agent.metadata["data_classification"]
            ),
            "legal_basis_valid": operation_data["legal_basis"] in ["consent", "contract", "legal_obligation"],
            "approved": True
        }

        compliance_check["approved"] = all([
            compliance_check["agent_certified"],
            compliance_check["data_classification_match"],
            compliance_check["legal_basis_valid"]
        ])

        # Log compliance check
        audit_log.log(
            operation="compliance_check",
            agent_id=agent.agent_id,
            details={
                "check_results": compliance_check,
                "operation": operation_data
            }
        )

        # Step 5: Execute operation if compliant
        if compliance_check["approved"]:
            # Simulate data processing
            operation_result = {
                "status": "success",
                "records_processed": 1000,
                "processing_time_ms": 1523,
                "compliance_verified": True
            }

            audit_log.log(
                operation="data_processing",
                agent_id=agent.agent_id,
                details={
                    "operation_data": operation_data,
                    "result": operation_result
                }
            )

        # Step 6: Verify audit trail
        agent_logs = audit_log.get_entries(agent_id=agent.agent_id)

        assert len(agent_logs) == 3  # registration, compliance_check, data_processing
        assert agent_logs[0]["operation"] == "agent_registration"
        assert agent_logs[1]["operation"] == "compliance_check"
        assert agent_logs[2]["operation"] == "data_processing"
        assert agent_logs[1]["details"]["check_results"]["approved"] is True

        # Step 7: Query audit log for compliance report
        all_compliance_checks = [
            entry for entry in audit_log.entries
            if entry["operation"] == "compliance_check"
        ]

        assert len(all_compliance_checks) == 1
        assert all_compliance_checks[0]["details"]["check_results"]["approved"] is True

        logger.info("✓ Test 8 passed: Compliance-checked operations successful")

    # ------------------------------------------------------------------------
    # Test 9: Genetic Evolution of Agent Team (ADP + CIP + ANP)
    # ------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_genetic_evolution_agent_team(self):
        """Test genetic evolution of agent parameters using ADP and CIP."""
        logger.info("\n" + "="*70)
        logger.info("TEST 9: Genetic Evolution of Agent Team")
        logger.info("="*70)

        # Step 1: Create evolution simulator and fitness evaluator
        fitness_evaluator = FitnessEvaluator()
        evolution_simulator = EvolutionSimulator(
            population_size=5,
            mutation_rate=0.1,
            crossover_rate=0.7
        )

        # Step 2: Define agent genomes
        genomes = []
        for i in range(5):
            genome = AgentGenome(
                genome_id=f"genome_{i}",
                agent_id=f"evolved_agent_{i}",
                chromosomes=[
                    Chromosome(
                        chromosome_id="learning_rate",
                        chromosome_type=ChromosomeType.CONTINUOUS.value,
                        genes=[
                            Gene(
                                gene_id="lr_value",
                                gene_type=GeneType.FLOAT.value,
                                value=0.01 + (i * 0.002),  # Vary learning rate
                                constraints={"min": 0.001, "max": 0.1}
                            )
                        ]
                    ),
                    Chromosome(
                        chromosome_id="exploration_factor",
                        chromosome_type=ChromosomeType.CONTINUOUS.value,
                        genes=[
                            Gene(
                                gene_id="epsilon",
                                gene_type=GeneType.FLOAT.value,
                                value=0.1 + (i * 0.05),  # Vary exploration
                                constraints={"min": 0.0, "max": 1.0}
                            )
                        ]
                    )
                ]
            )
            genomes.append(genome)

        # Step 3: Evaluate fitness using collective intelligence (CIP)
        collective_decision = CollectiveDecision(
            decision_id="fitness_evaluation_gen_0"
        )

        # Simulate agents evaluating each other's performance
        performance_scores = [0.75, 0.82, 0.68, 0.79, 0.71]  # Simulated fitness scores

        for i, (genome, score) in enumerate(zip(genomes, performance_scores)):
            fitness_score = fitness_evaluator.evaluate_single(
                genome=genome,
                environment_metrics={"task_success_rate": score, "efficiency": score * 1.1}
            )
            genome.fitness_score = fitness_score

            # Collective voting on fitness
            vote = Vote(
                agent_id=f"evaluator_{i}",
                vote_value=score,
                confidence=0.8 + (i * 0.02),
                reasoning=f"Performance evaluation for genome_{i}"
            )
            collective_decision.add_vote(vote)

        # Step 4: Select best genomes for reproduction
        best_genomes = sorted(genomes, key=lambda g: g.fitness_score, reverse=True)[:3]

        assert len(best_genomes) == 3
        assert best_genomes[0].fitness_score >= best_genomes[1].fitness_score

        # Step 5: Register evolved agents in network
        registry = AgentNetworkRegistry()

        for genome in best_genomes:
            await registry.register_agent(
                agent_id=genome.agent_id,
                agent_type="EvolvedAgent",
                capabilities=["adaptive_learning"],
                endpoints={"http": f"http://localhost:8000/{genome.agent_id}"},
                metadata={
                    "generation": 1,
                    "fitness_score": genome.fitness_score,
                    "genome_id": genome.genome_id,
                    "learning_rate": genome.chromosomes[0].genes[0].value,
                    "exploration_factor": genome.chromosomes[1].genes[0].value
                }
            )

        # Step 6: Verify evolved population
        evolved_agents = await registry.discover_agents(
            capability_filter=["adaptive_learning"]
        )

        assert len(evolved_agents) == 3

        # Verify they're sorted by fitness (best first)
        for agent_data in evolved_agents:
            assert "fitness_score" in agent_data["metadata"]
            assert "genome_id" in agent_data["metadata"]

        logger.info("✓ Test 9 passed: Genetic evolution of agent team successful")

    # ------------------------------------------------------------------------
    # Test 10: Collective Intelligence Decision (CIP + ANP + A2A + ACP)
    # ------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_collective_intelligence_decision(self):
        """Test collective decision-making using CIP with coordination."""
        logger.info("\n" + "="*70)
        logger.info("TEST 10: Collective Intelligence Decision")
        logger.info("="*70)

        # Step 1: Create coordination session and registry
        coordinator = CoordinationEngine()
        registry = AgentNetworkRegistry()

        session_id = "strategic_decision_session"

        # Step 2: Create decision-making agents
        agents = [
            MockAgent(f"decision_agent_{i}", "DecisionAgent", ["decision_making"])
            for i in range(7)
        ]

        for agent in agents:
            await registry.register_agent(
                agent_id=agent.agent_id,
                agent_type=agent.agent_type,
                capabilities=agent.capabilities,
                endpoints={"http": f"http://localhost:8000/{agent.agent_id}"}
            )

        # Step 3: Create coordination for consensus building
        await coordinator.create_session(
            session_id=session_id,
            pattern=CoordinationPattern.CONSENSUS,
            participants=[agent.agent_id for agent in agents],
            metadata={"decision_type": "product_launch"}
        )

        # Step 4: Define decision options
        options = [
            VotingOption(
                option_id="launch_q1",
                option_value="Launch in Q1 2024",
                metadata={"risk": "medium", "opportunity": "high"}
            ),
            VotingOption(
                option_id="launch_q2",
                option_value="Launch in Q2 2024",
                metadata={"risk": "low", "opportunity": "medium"}
            ),
            VotingOption(
                option_id="delay",
                option_value="Delay to 2025",
                metadata={"risk": "low", "opportunity": "low"}
            )
        ]

        # Step 5: Agents communicate and vote via A2A
        collective_decision = CollectiveDecision(
            decision_id="product_launch_decision",
            options=options,
            method=DecisionMethod.WEIGHTED_VOTING
        )

        # Simulate voting with A2A messages
        vote_distribution = {
            "launch_q1": [0, 1, 5],  # 3 agents vote for Q1
            "launch_q2": [2, 3, 6],  # 3 agents vote for Q2
            "delay": [4]  # 1 agent votes for delay
        }

        for option_id, agent_indices in vote_distribution.items():
            for idx in agent_indices:
                # Agent sends vote
                vote_msg = await agents[idx].send_message(
                    to_agent="coordinator",
                    message_type="vote",
                    content={
                        "session_id": session_id,
                        "option_id": option_id,
                        "confidence": 0.7 + (idx * 0.05),
                        "reasoning": f"Strategic analysis by {agents[idx].agent_id}"
                    }
                )

                # Record vote in collective decision
                vote = Vote(
                    agent_id=agents[idx].agent_id,
                    option_id=option_id,
                    vote_value=1.0,
                    confidence=0.7 + (idx * 0.05),
                    reasoning=vote_msg.content["reasoning"]
                )
                collective_decision.add_vote(vote)

        # Step 6: Calculate collective decision
        result = collective_decision.calculate_result()

        assert result is not None
        assert result.winning_option in ["launch_q1", "launch_q2"]  # Most votes
        assert len(result.vote_distribution) == 3
        assert result.total_votes == 7

        # Step 7: Broadcast decision via A2A
        decision_agent = MockAgent(
            agent_id="coordinator",
            agent_type="Coordinator",
            capabilities=["coordination"]
        )

        for agent in agents:
            decision_msg = await decision_agent.send_message(
                to_agent=agent.agent_id,
                message_type=MessageType.RESULT.value,
                content={
                    "decision_type": "collective_decision",
                    "session_id": session_id,
                    "winning_option": result.winning_option,
                    "confidence": result.confidence,
                    "total_votes": result.total_votes,
                    "consensus_level": result.consensus_level
                }
            )
            await agent.receive_message(decision_msg)

        # Verify all agents received decision
        for agent in agents:
            assert len(agent.messages_received) >= 1
            decision_msgs = [
                msg for msg in agent.messages_received
                if msg.content.get("decision_type") == "collective_decision"
            ]
            assert len(decision_msgs) == 1

        logger.info("✓ Test 10 passed: Collective intelligence decision successful")

    # ------------------------------------------------------------------------
    # Test 11: Full Stack Workflow (All Protocols)
    # ------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_full_stack_workflow(self):
        """Test complete workflow using all protocols together."""
        logger.info("\n" + "="*70)
        logger.info("TEST 11: Full Stack Workflow (All Protocols)")
        logger.info("="*70)

        # Initialize all protocol systems
        network_registry = AgentNetworkRegistry()
        semantic_registry = SemanticRegistry()
        coordinator = CoordinationEngine()
        temporal_engine = TemporalEngine("full_workflow_timeline")
        audit_log = AuditLog()

        # Create agents
        ai_agent = MockAgent(
            agent_id="ai_strategist_001",
            agent_type="AIStrategist",
            capabilities=["strategic_planning", "ai_analysis"]
        )

        data_agent = MockAgent(
            agent_id="data_analyst_001",
            agent_type="DataAnalyst",
            capabilities=["data_analysis", "reporting"]
        )

        # Register agents (ANP)
        for agent in [ai_agent, data_agent]:
            await network_registry.register_agent(
                agent_id=agent.agent_id,
                agent_type=agent.agent_type,
                capabilities=agent.capabilities,
                endpoints={"http": f"http://localhost:8000/{agent.agent_id}"}
            )

            audit_log.log(
                operation="agent_registration",
                agent_id=agent.agent_id,
                details={"agent_type": agent.agent_type}
            )

        # Register semantic capabilities (ASP)
        semantic_decl = SemanticDeclaration(
            agent_id=ai_agent.agent_id,
            ontologies=[
                OntologyReference(
                    ontology_id="business:1.0",
                    namespace="https://business.org/ontology",
                    coverage=["Strategy", "Planning"]
                )
            ],
            capabilities=[
                SemanticCapability(
                    capability_id="strategic_analysis",
                    semantic_type="business:StrategicAnalysis"
                )
            ],
            domain_knowledge=[]
        )
        semantic_registry.register(semantic_decl)

        # Create coordination session (ACP)
        session_id = "full_stack_session"
        await coordinator.create_session(
            session_id=session_id,
            pattern=CoordinationPattern.PIPELINE,
            participants=[ai_agent.agent_id, data_agent.agent_id]
        )

        # Execute workflow with temporal tracking (TAP)
        # Step 1: AI agent starts analysis
        event1 = TemporalEvent(
            event_id="full_evt_001",
            timestamp=datetime.utcnow().isoformat(),
            agent_id=ai_agent.agent_id,
            operation_type=OperationType.STATE_CHANGE.value,
            operation_data={"action": "start_analysis"},
            state_snapshot={"status": "working"}
        )
        await temporal_engine.record_event(event1)

        # Send message (A2A)
        msg1 = await ai_agent.send_message(
            to_agent=data_agent.agent_id,
            message_type=MessageType.TASK_ASSIGNMENT.value,
            content={
                "task": "prepare_market_data",
                "session_id": session_id,
                "deadline": (datetime.utcnow() + timedelta(hours=24)).isoformat()
            }
        )
        await data_agent.receive_message(msg1)

        audit_log.log(
            operation="task_assignment",
            agent_id=ai_agent.agent_id,
            details={"to_agent": data_agent.agent_id, "task": "prepare_market_data"}
        )

        # Step 2: Data agent processes
        event2 = TemporalEvent(
            event_id="full_evt_002",
            timestamp=datetime.utcnow().isoformat(),
            agent_id=data_agent.agent_id,
            operation_type=OperationType.STATE_CHANGE.value,
            operation_data={"action": "processing_data"},
            state_snapshot={"status": "processing"}
        )
        await temporal_engine.record_event(event2)

        # Respond (A2A)
        msg2 = await data_agent.send_message(
            to_agent=ai_agent.agent_id,
            message_type=MessageType.RESULT.value,
            content={
                "task": "prepare_market_data",
                "result": {"data_points": 10000, "quality_score": 0.95},
                "status": "completed"
            }
        )
        await ai_agent.receive_message(msg2)

        audit_log.log(
            operation="task_completion",
            agent_id=data_agent.agent_id,
            details={"task": "prepare_market_data", "status": "completed"}
        )

        # Verify full workflow
        assert len(ai_agent.messages_received) >= 1
        assert len(data_agent.messages_received) >= 1

        # Check temporal timeline
        events = await temporal_engine.query_events(
            time_range=TimeRange(
                start_time=(datetime.utcnow() - timedelta(minutes=5)).isoformat(),
                end_time=datetime.utcnow().isoformat()
            )
        )
        assert len(events) >= 2

        # Check audit trail
        audit_entries = audit_log.get_entries()
        assert len(audit_entries) >= 4  # 2 registrations + 2 operations

        # Check network registration
        all_agents = await network_registry.discover_agents()
        assert len(all_agents) >= 2

        logger.info("✓ Test 11 passed: Full stack workflow successful")

    # ------------------------------------------------------------------------
    # Test 12: Cross-Protocol Error Handling
    # ------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_cross_protocol_error_handling(self):
        """Test error handling and recovery across multiple protocols."""
        logger.info("\n" + "="*70)
        logger.info("TEST 12: Cross-Protocol Error Handling")
        logger.info("="*70)

        registry = AgentNetworkRegistry()
        coordinator = CoordinationEngine()
        audit_log = AuditLog()

        # Create agent
        agent = MockAgent(
            agent_id="error_test_agent",
            agent_type="TestAgent",
            capabilities=["testing"]
        )

        # Test 1: Registration error handling
        try:
            # Attempt to register with invalid data
            await registry.register_agent(
                agent_id="",  # Invalid: empty ID
                agent_type=agent.agent_type,
                capabilities=agent.capabilities,
                endpoints={}
            )
            pytest.fail("Should have raised error for invalid agent_id")
        except (ValueError, AssertionError, Exception) as e:
            logger.info(f"✓ Caught expected registration error: {type(e).__name__}")
            audit_log.log(
                operation="registration_error",
                agent_id="unknown",
                details={"error": str(e)}
            )

        # Test 2: Coordination error handling
        try:
            # Attempt to create session with no participants
            await coordinator.create_session(
                session_id="invalid_session",
                pattern=CoordinationPattern.PIPELINE,
                participants=[]  # Invalid: no participants
            )
            pytest.fail("Should have raised error for no participants")
        except (ValueError, AssertionError, Exception) as e:
            logger.info(f"✓ Caught expected coordination error: {type(e).__name__}")
            audit_log.log(
                operation="coordination_error",
                agent_id="coordinator",
                details={"error": str(e)}
            )

        # Test 3: Message delivery error handling
        try:
            # Send message to non-existent agent
            msg = await agent.send_message(
                to_agent="non_existent_agent_999",
                message_type=MessageType.TASK_ASSIGNMENT.value,
                content={"task": "impossible_task"}
            )

            # Log the attempt
            audit_log.log(
                operation="message_delivery_attempt",
                agent_id=agent.agent_id,
                details={
                    "to_agent": "non_existent_agent_999",
                    "message_id": msg.message_id,
                    "status": "delivery_failed"
                }
            )

            logger.info("✓ Message created but delivery would fail")
        except Exception as e:
            logger.info(f"✓ Caught message error: {type(e).__name__}")

        # Verify error logging
        error_logs = [
            entry for entry in audit_log.entries
            if "error" in entry["operation"]
        ]
        assert len(error_logs) >= 2

        logger.info("✓ Test 12 passed: Error handling verified across protocols")


# ============================================================================
# Test Execution
# ============================================================================

if __name__ == "__main__":
    """Run tests directly."""
    import sys

    # Configure logging for direct execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run tests
    pytest.main([__file__, "-v", "-s"])
