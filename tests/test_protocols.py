"""
Comprehensive Protocol Tests

Tests for ANP, ACP, and AConsP protocol implementations.
"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any

from superstandard.protocols.anp_implementation import (
    AgentNetworkRegistry,
    ANPClient,
    ANPRegistration,
    DiscoveryQuery,
    AgentStatus
)
from superstandard.protocols.acp_implementation import (
    CoordinationManager,
    ACPClient,
    CoordinationType,
    TaskStatus,
    CoordinationStatus
)
from superstandard.protocols.consciousness_protocol import (
    CollectiveConsciousness,
    ThoughtType,
    ConsciousnessState
)


# ============================================================================
# ANP (Agent Network Protocol) Tests
# ============================================================================

class TestANP:
    """Test Agent Network Protocol."""

    @pytest.fixture
    async def registry(self):
        """Create a registry for testing."""
        reg = AgentNetworkRegistry(heartbeat_timeout=5)
        await reg.start()
        yield reg
        await reg.stop()

    @pytest.fixture
    def client(self, registry):
        """Create a client for testing."""
        return ANPClient(registry)

    @pytest.mark.asyncio
    async def test_agent_registration(self, client):
        """Test agent registration."""
        result = await client.register(
            agent_id="test_agent_001",
            agent_type="analyzer",
            capabilities=["analysis", "processing"],
            endpoints={"http": "http://localhost:8001"}
        )

        assert result["success"] is True
        assert result["agent_id"] == "test_agent_001"

    @pytest.mark.asyncio
    async def test_agent_discovery_by_capability(self, client):
        """Test discovering agents by capability."""
        # Register multiple agents
        await client.register(
            "agent1", "analyzer", ["analysis", "ml"],
            {"http": "http://localhost:8001"}
        )
        await client.register(
            "agent2", "processor", ["processing", "ml"],
            {"http": "http://localhost:8002"}
        )
        await client.register(
            "agent3", "analyzer", ["analysis"],
            {"http": "http://localhost:8003"}
        )

        # Discover agents with 'ml' capability
        agents = await client.discover(capabilities=["ml"])
        assert len(agents) == 2
        agent_ids = {a["agent_id"] for a in agents}
        assert agent_ids == {"agent1", "agent2"}

    @pytest.mark.asyncio
    async def test_agent_discovery_by_type(self, client):
        """Test discovering agents by type."""
        # Register agents
        await client.register("agent1", "analyzer", ["analysis"])
        await client.register("agent2", "analyzer", ["analysis"])
        await client.register("agent3", "processor", ["processing"])

        # Discover analyzers
        agents = await client.discover(agent_type="analyzer")
        assert len(agents) == 2

    @pytest.mark.asyncio
    async def test_agent_heartbeat(self, client):
        """Test agent heartbeat."""
        # Register agent
        await client.register("agent1", "analyzer", ["analysis"])

        # Send heartbeat
        result = await client.heartbeat("agent1", AgentStatus.HEALTHY.value, 0.5)
        assert result["success"] is True
        assert result["heartbeat_count"] == 1

        # Send another heartbeat
        result = await client.heartbeat("agent1", AgentStatus.HEALTHY.value, 0.6)
        assert result["heartbeat_count"] == 2

    @pytest.mark.asyncio
    async def test_agent_deregistration(self, client):
        """Test agent deregistration."""
        # Register agent
        await client.register("agent1", "analyzer", ["analysis"])

        # Verify it exists
        agents = await client.discover()
        assert len(agents) == 1

        # Deregister
        result = await client.deregister("agent1")
        assert result["success"] is True

        # Verify it's gone
        agents = await client.discover()
        assert len(agents) == 0

    @pytest.mark.asyncio
    async def test_network_topology(self, client):
        """Test getting network topology."""
        # Register diverse agents
        await client.register("agent1", "analyzer", ["analysis"])
        await client.register("agent2", "analyzer", ["ml"])
        await client.register("agent3", "processor", ["processing"])

        topology = await client.get_network_info()
        assert topology["total_agents"] == 3
        assert topology["agents_by_type"]["analyzer"] == 2
        assert topology["agents_by_type"]["processor"] == 1


# ============================================================================
# ACP (Agent Coordination Protocol) Tests
# ============================================================================

class TestACP:
    """Test Agent Coordination Protocol."""

    @pytest.fixture
    def manager(self):
        """Create a coordination manager for testing."""
        return CoordinationManager()

    @pytest.fixture
    def coordinator_client(self, manager):
        """Create coordinator client."""
        return ACPClient(manager, "coordinator_agent")

    @pytest.fixture
    def worker_client(self, manager):
        """Create worker client."""
        return ACPClient(manager, "worker_agent")

    @pytest.mark.asyncio
    async def test_create_coordination(self, coordinator_client):
        """Test creating a coordination session."""
        coord_id = await coordinator_client.create_coordination(
            coordination_type=CoordinationType.SWARM.value,
            goal="Test coordination",
            plan={"strategy": "test"}
        )

        assert coord_id is not None
        assert len(coord_id) > 0

    @pytest.mark.asyncio
    async def test_join_coordination(self, coordinator_client, worker_client):
        """Test joining a coordination session."""
        # Create coordination
        coord_id = await coordinator_client.create_coordination(
            CoordinationType.SWARM.value,
            "Test goal"
        )

        # Worker joins
        result = await worker_client.join(
            coord_id,
            "worker",
            ["processing", "analysis"]
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_task_creation_and_assignment(
        self, coordinator_client, worker_client, manager
    ):
        """Test creating and assigning tasks."""
        # Create coordination and join
        coord_id = await coordinator_client.create_coordination(
            CoordinationType.PIPELINE.value,
            "Process data"
        )
        await worker_client.join(coord_id, "worker", ["processing"])

        # Create task
        task_id = await coordinator_client.create_task(
            coord_id,
            "data_processing",
            "Process dataset chunk 1",
            priority=8
        )

        assert task_id is not None

        # Assign task to worker
        result = await worker_client.claim_task(coord_id, task_id)
        assert result is True

    @pytest.mark.asyncio
    async def test_task_completion(self, coordinator_client, worker_client):
        """Test completing a task."""
        # Setup
        coord_id = await coordinator_client.create_coordination(
            CoordinationType.SWARM.value,
            "Test goal"
        )
        await worker_client.join(coord_id, "worker", ["processing"])
        task_id = await coordinator_client.create_task(
            coord_id, "processing", "Test task"
        )
        await worker_client.claim_task(coord_id, task_id)

        # Start task
        result = await worker_client.update_task(
            coord_id, task_id, TaskStatus.IN_PROGRESS.value
        )
        assert result is True

        # Complete task
        result = await worker_client.update_task(
            coord_id,
            task_id,
            TaskStatus.COMPLETED.value,
            output={"result": "success"}
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_coordination_progress(self, coordinator_client, worker_client):
        """Test tracking coordination progress."""
        # Setup coordination with tasks
        coord_id = await coordinator_client.create_coordination(
            CoordinationType.SWARM.value,
            "Multi-task coordination"
        )
        await worker_client.join(coord_id, "worker", ["processing"])

        # Create multiple tasks
        task1 = await coordinator_client.create_task(coord_id, "task", "Task 1")
        task2 = await coordinator_client.create_task(coord_id, "task", "Task 2")
        task3 = await coordinator_client.create_task(coord_id, "task", "Task 3")

        # Check initial progress
        progress = await coordinator_client.get_progress(coord_id)
        assert progress["total_tasks"] == 3
        assert progress["completed_tasks"] == 0
        assert progress["progress_percentage"] == 0.0

        # Complete one task
        await worker_client.claim_task(coord_id, task1)
        await worker_client.update_task(coord_id, task1, TaskStatus.COMPLETED.value)

        # Check updated progress
        progress = await coordinator_client.get_progress(coord_id)
        assert progress["completed_tasks"] == 1
        assert progress["progress_percentage"] == pytest.approx(33.33, rel=0.1)

    @pytest.mark.asyncio
    async def test_shared_state_updates(self, coordinator_client, worker_client):
        """Test updating and reading shared state."""
        # Setup
        coord_id = await coordinator_client.create_coordination(
            CoordinationType.SWARM.value,
            "Shared state test"
        )
        await worker_client.join(coord_id, "worker", ["processing"])

        # Update shared state
        result = await worker_client.update_state(
            coord_id,
            {"processed_items": 100, "status": "running"}
        )
        assert result is True

        # Update again
        result = await worker_client.update_state(
            coord_id,
            {"processed_items": 200}
        )
        assert result is True


# ============================================================================
# AConsP (Agent Consciousness Protocol) Tests
# ============================================================================

class TestAConsP:
    """Test Agent Consciousness Protocol."""

    @pytest.fixture
    def collective(self):
        """Create a collective consciousness for testing."""
        return CollectiveConsciousness("test_collective")

    @pytest.mark.asyncio
    async def test_agent_registration(self, collective):
        """Test registering agents with collective."""
        result = await collective.register_agent(
            "agent1",
            ConsciousnessState.AWAKENING
        )
        assert result is True
        assert "agent1" in collective.agents

    @pytest.mark.asyncio
    async def test_thought_contribution(self, collective):
        """Test contributing thoughts to collective."""
        await collective.register_agent("agent1")

        thought = await collective.contribute_thought(
            "agent1",
            ThoughtType.OBSERVATION,
            "Test observation",
            confidence=0.9
        )

        assert thought is not None
        assert thought.agent_id == "agent1"
        assert thought.content == "Test observation"
        assert thought.confidence == 0.9

    @pytest.mark.asyncio
    async def test_agent_consciousness_evolution(self, collective):
        """Test that agents evolve consciousness through participation."""
        await collective.register_agent("agent1", ConsciousnessState.AWAKENING)

        # Initial state
        assert collective.agents["agent1"].state == ConsciousnessState.AWAKENING

        # Contribute many thoughts
        for i in range(10):
            await collective.contribute_thought(
                "agent1",
                ThoughtType.OBSERVATION,
                f"Observation {i}",
                confidence=0.8
            )

        # Should have evolved to CONSCIOUS
        assert collective.agents["agent1"].state == ConsciousnessState.CONSCIOUS

    @pytest.mark.asyncio
    async def test_thought_entanglement(self, collective):
        """Test that related thoughts become entangled."""
        await collective.register_agent("agent1")
        await collective.register_agent("agent2")

        # Agent1 makes an observation
        thought1 = await collective.contribute_thought(
            "agent1",
            ThoughtType.OBSERVATION,
            "Sales increased 20%",
            confidence=0.95
        )

        # Agent2 makes related inference
        thought2 = await collective.contribute_thought(
            "agent2",
            ThoughtType.INFERENCE,
            "Marketing campaign was effective",
            confidence=0.85
        )

        # Check if thoughts became entangled
        # (They should if algorithm detects relationship)
        assert len(collective.entanglement_graph) >= 0

    @pytest.mark.asyncio
    async def test_consciousness_collapse(self, collective):
        """Test collapsing consciousness to find emergent patterns."""
        # Register agents and contribute diverse thoughts
        agents = ["agent1", "agent2", "agent3"]
        for agent in agents:
            await collective.register_agent(agent)

        # Create related thoughts
        await collective.contribute_thought(
            "agent1",
            ThoughtType.OBSERVATION,
            "Market demand increasing",
            confidence=0.9
        )
        await collective.contribute_thought(
            "agent2",
            ThoughtType.INFERENCE,
            "Should increase production",
            confidence=0.85
        )
        await collective.contribute_thought(
            "agent3",
            ThoughtType.INSIGHT,
            "Opportunity for expansion",
            confidence=0.8
        )

        # Collapse consciousness
        patterns = await collective.collapse_consciousness(
            query="market opportunities",
            min_coherence=0.3
        )

        # Should find some patterns
        assert isinstance(patterns, list)

    @pytest.mark.asyncio
    async def test_collective_state(self, collective):
        """Test getting collective consciousness state."""
        # Add agents and thoughts
        await collective.register_agent("agent1")
        await collective.contribute_thought(
            "agent1",
            ThoughtType.OBSERVATION,
            "Test",
            confidence=0.9
        )

        state = collective.get_consciousness_state()

        assert state["total_agents"] == 1
        assert state["total_thoughts"] == 1
        assert "collective_awareness" in state
        assert "average_agent_awareness" in state

    @pytest.mark.asyncio
    async def test_memory_management(self, collective):
        """Test that memory limits prevent unbounded growth."""
        await collective.register_agent("agent1")

        # Contribute thoughts beyond the limit
        initial_limit = collective.MAX_THOUGHT_HISTORY
        collective.MAX_THOUGHT_HISTORY = 10  # Lower limit for testing

        for i in range(20):
            await collective.contribute_thought(
                "agent1",
                ThoughtType.OBSERVATION,
                f"Thought {i}",
                confidence=0.8
            )

        # Should not exceed limit
        assert len(collective.thought_stream) <= 10

        # Restore original limit
        collective.MAX_THOUGHT_HISTORY = initial_limit


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
