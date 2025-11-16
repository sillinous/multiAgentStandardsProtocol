"""
Unit Tests for Agent Network Protocol (ANP) v1.0

Comprehensive test coverage including:
- Agent registration (valid, invalid, updates)
- Agent deregistration
- Heartbeat processing
- Health monitoring and timeout
- Agent discovery (by capability, type, region, tags, load)
- Network topology tracking
- Event handlers
- Load balancing
- Statistics gathering
"""

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timedelta
from dataclasses import asdict

from superstandard.protocols.anp_implementation import (
    # Data models
    AgentStatus,
    ANPRegistration,
    AgentInfo,
    DiscoveryQuery,
    NetworkTopology,

    # Core classes
    AgentNetworkRegistry,
    ANPClient,
)


@pytest_asyncio.fixture
async def registry():
    """Create a test registry with short timeout."""
    reg = AgentNetworkRegistry(heartbeat_timeout=2)  # 2 seconds for testing
    await reg.start()
    yield reg
    await reg.stop()


@pytest_asyncio.fixture
async def client(registry):
    """Create a test client."""
    return ANPClient(registry)


@pytest.fixture
def sample_registration():
    """Create a sample registration."""
    return ANPRegistration(
        agent_id="test-agent-1",
        agent_type="analyzer",
        capabilities=["text-analysis", "sentiment"],
        endpoints={"http": "http://localhost:8001"},
        metadata={"version": "1.0.0"}
    )


# ============================================================================
# REGISTRATION TESTS
# ============================================================================


@pytest.mark.unit
@pytest.mark.protocol
class TestAgentRegistration:
    """Test agent registration functionality."""

    @pytest.mark.asyncio
    async def test_register_agent_success(self, registry, sample_registration):
        """Test successful agent registration."""
        result = await registry.register_agent(sample_registration)

        assert result["success"] is True
        assert result["agent_id"] == "test-agent-1"
        assert result["is_update"] is False
        assert "agent_info" in result
        assert result["agent_info"]["agent_type"] == "analyzer"
        assert len(result["agent_info"]["capabilities"]) == 2

    @pytest.mark.asyncio
    async def test_register_agent_missing_agent_id(self, registry):
        """Test registration failure with missing agent_id."""
        registration = ANPRegistration(
            agent_id="",  # Empty agent_id
            agent_type="analyzer",
            capabilities=["test"]
        )

        result = await registry.register_agent(registration)
        assert result["success"] is False
        assert "agent_id is required" in result["error"]

    @pytest.mark.asyncio
    async def test_register_agent_missing_agent_type(self, registry):
        """Test registration failure with missing agent_type."""
        registration = ANPRegistration(
            agent_id="test-agent",
            agent_type="",  # Empty agent_type
            capabilities=["test"]
        )

        result = await registry.register_agent(registration)
        assert result["success"] is False
        assert "agent_type is required" in result["error"]

    @pytest.mark.asyncio
    async def test_register_agent_update_existing(self, registry, sample_registration):
        """Test updating an existing agent registration."""
        # Initial registration
        result1 = await registry.register_agent(sample_registration)
        assert result1["success"] is True

        # Update with new capabilities
        sample_registration.capabilities = ["text-analysis", "translation"]
        result2 = await registry.register_agent(sample_registration)

        assert result2["success"] is True
        assert result2["is_update"] is True
        assert "translation" in result2["agent_info"]["capabilities"]

    @pytest.mark.asyncio
    async def test_register_multiple_agents(self, registry):
        """Test registering multiple agents."""
        agents = []
        for i in range(5):
            reg = ANPRegistration(
                agent_id=f"agent-{i}",
                agent_type="worker",
                capabilities=["processing"]
            )
            result = await registry.register_agent(reg)
            assert result["success"] is True
            agents.append(result["agent_id"])

        # Verify all agents are registered
        all_agents = await registry.list_all_agents()
        assert len(all_agents) == 5

    @pytest.mark.asyncio
    async def test_register_agent_with_metadata(self, registry):
        """Test registration with custom metadata."""
        registration = ANPRegistration(
            agent_id="meta-agent",
            agent_type="analyzer",
            capabilities=["test"],
            metadata={
                "custom_field": "value",
                "version": "2.0.0",
                "tags": ["production", "critical"]
            }
        )

        result = await registry.register_agent(registration)
        assert result["success"] is True
        assert result["agent_info"]["metadata"]["custom_field"] == "value"


# ============================================================================
# DEREGISTRATION TESTS
# ============================================================================


@pytest.mark.unit
@pytest.mark.protocol
class TestAgentDeregistration:
    """Test agent deregistration functionality."""

    @pytest.mark.asyncio
    async def test_deregister_agent_success(self, registry, sample_registration):
        """Test successful agent deregistration."""
        # Register first
        await registry.register_agent(sample_registration)

        # Deregister
        result = await registry.deregister_agent("test-agent-1")
        assert result["success"] is True
        assert result["agent_id"] == "test-agent-1"

        # Verify agent is removed
        agent_info = await registry.get_agent("test-agent-1")
        assert agent_info is None

    @pytest.mark.asyncio
    async def test_deregister_nonexistent_agent(self, registry):
        """Test deregistering an agent that doesn't exist."""
        result = await registry.deregister_agent("nonexistent-agent")
        assert result["success"] is False
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_deregister_removes_from_indexes(self, registry):
        """Test that deregistration removes agent from all indexes."""
        # Register agent with specific capabilities
        registration = ANPRegistration(
            agent_id="indexed-agent",
            agent_type="analyzer",
            capabilities=["unique-capability"]
        )
        await registry.register_agent(registration)

        # Verify agent is discoverable
        query = DiscoveryQuery(capabilities=["unique-capability"])
        result = await registry.discover_agents(query)
        assert result["count"] == 1

        # Deregister
        await registry.deregister_agent("indexed-agent")

        # Verify agent is no longer discoverable
        result = await registry.discover_agents(query)
        assert result["count"] == 0


# ============================================================================
# HEARTBEAT TESTS
# ============================================================================


@pytest.mark.unit
@pytest.mark.protocol
class TestHeartbeat:
    """Test heartbeat functionality."""

    @pytest.mark.asyncio
    async def test_heartbeat_success(self, registry, sample_registration):
        """Test successful heartbeat processing."""
        await registry.register_agent(sample_registration)

        result = await registry.heartbeat("test-agent-1")
        assert result["success"] is True
        assert result["agent_id"] == "test-agent-1"
        assert result["heartbeat_count"] == 1

    @pytest.mark.asyncio
    async def test_heartbeat_nonexistent_agent(self, registry):
        """Test heartbeat for unregistered agent."""
        result = await registry.heartbeat("nonexistent-agent")
        assert result["success"] is False
        assert "not registered" in result["error"]

    @pytest.mark.asyncio
    async def test_heartbeat_increments_count(self, registry, sample_registration):
        """Test that heartbeat count increments."""
        await registry.register_agent(sample_registration)

        # Send multiple heartbeats
        for i in range(5):
            result = await registry.heartbeat("test-agent-1")
            assert result["heartbeat_count"] == i + 1

    @pytest.mark.asyncio
    async def test_heartbeat_updates_health_status(self, registry, sample_registration):
        """Test heartbeat updates health status."""
        await registry.register_agent(sample_registration)

        # Update health status via heartbeat
        await registry.heartbeat(
            "test-agent-1",
            health_status=AgentStatus.DEGRADED.value
        )

        agent_info = await registry.get_agent("test-agent-1")
        assert agent_info["health_status"] == AgentStatus.DEGRADED.value

    @pytest.mark.asyncio
    async def test_heartbeat_updates_load_score(self, registry, sample_registration):
        """Test heartbeat updates load score."""
        await registry.register_agent(sample_registration)

        # Update load score
        await registry.heartbeat("test-agent-1", load_score=0.75)

        agent_info = await registry.get_agent("test-agent-1")
        assert agent_info["load_score"] == 0.75

    @pytest.mark.asyncio
    async def test_heartbeat_clamps_load_score(self, registry, sample_registration):
        """Test heartbeat clamps load score to valid range."""
        await registry.register_agent(sample_registration)

        # Try invalid load scores
        await registry.heartbeat("test-agent-1", load_score=1.5)
        agent_info = await registry.get_agent("test-agent-1")
        assert agent_info["load_score"] == 1.0

        await registry.heartbeat("test-agent-1", load_score=-0.5)
        agent_info = await registry.get_agent("test-agent-1")
        assert agent_info["load_score"] == 0.0


# ============================================================================
# HEALTH MONITORING TESTS
# ============================================================================


@pytest.mark.unit
@pytest.mark.protocol
class TestHealthMonitoring:
    """Test health monitoring and timeout detection."""

    @pytest.mark.asyncio
    async def test_health_check_marks_offline(self, sample_registration):
        """Test that agents are marked offline after timeout."""
        # Create registry with 1-second timeout
        registry = AgentNetworkRegistry(heartbeat_timeout=1)
        await registry.start()

        try:
            # Register agent
            await registry.register_agent(sample_registration)

            # Wait for timeout
            await asyncio.sleep(2)

            # Manually trigger health check
            await registry._check_agent_health()

            # Verify agent is marked offline
            agent_info = await registry.get_agent("test-agent-1")
            assert agent_info["health_status"] == AgentStatus.OFFLINE.value
        finally:
            await registry.stop()

    @pytest.mark.asyncio
    async def test_health_check_respects_heartbeat(self, sample_registration):
        """Test that heartbeats prevent timeout."""
        registry = AgentNetworkRegistry(heartbeat_timeout=1)
        await registry.start()

        try:
            await registry.register_agent(sample_registration)

            # Send heartbeat within timeout window
            await asyncio.sleep(0.5)
            await registry.heartbeat("test-agent-1")
            await asyncio.sleep(0.7)

            # Check health - should still be healthy
            await registry._check_agent_health()
            agent_info = await registry.get_agent("test-agent-1")
            assert agent_info["health_status"] == AgentStatus.HEALTHY.value
        finally:
            await registry.stop()

    @pytest.mark.asyncio
    async def test_health_check_event_emission(self, sample_registration):
        """Test that offline event is emitted."""
        registry = AgentNetworkRegistry(heartbeat_timeout=1)
        await registry.start()

        event_data = []

        def handler(data):
            event_data.append(data)

        registry.on_event("agent_offline", handler)

        try:
            await registry.register_agent(sample_registration)
            await asyncio.sleep(2)
            await registry._check_agent_health()

            assert len(event_data) == 1
            assert event_data[0].agent_id == "test-agent-1"
        finally:
            await registry.stop()


# ============================================================================
# DISCOVERY TESTS
# ============================================================================


@pytest.mark.unit
@pytest.mark.protocol
class TestAgentDiscovery:
    """Test agent discovery functionality."""

    @pytest.mark.asyncio
    async def test_discover_all_agents(self, registry):
        """Test discovering all agents without filters."""
        # Register multiple agents
        for i in range(3):
            reg = ANPRegistration(
                agent_id=f"agent-{i}",
                agent_type="worker",
                capabilities=["processing"]
            )
            await registry.register_agent(reg)

        query = DiscoveryQuery()
        result = await registry.discover_agents(query)

        assert result["success"] is True
        assert result["count"] == 3

    @pytest.mark.asyncio
    async def test_discover_by_capability(self, registry):
        """Test discovering agents by capability."""
        # Register agents with different capabilities
        agents = [
            ("agent-1", ["text-analysis", "sentiment"]),
            ("agent-2", ["text-analysis", "translation"]),
            ("agent-3", ["image-processing"]),
        ]

        for agent_id, capabilities in agents:
            reg = ANPRegistration(
                agent_id=agent_id,
                agent_type="analyzer",
                capabilities=capabilities
            )
            await registry.register_agent(reg)

        # Search for text-analysis capability
        query = DiscoveryQuery(capabilities=["text-analysis"])
        result = await registry.discover_agents(query)

        assert result["count"] == 2
        found_ids = {agent["agent_id"] for agent in result["agents"]}
        assert "agent-1" in found_ids
        assert "agent-2" in found_ids

    @pytest.mark.asyncio
    async def test_discover_by_agent_type(self, registry):
        """Test discovering agents by type."""
        # Register different agent types
        types = [
            ("agent-1", "analyzer"),
            ("agent-2", "analyzer"),
            ("agent-3", "coordinator"),
        ]

        for agent_id, agent_type in types:
            reg = ANPRegistration(
                agent_id=agent_id,
                agent_type=agent_type,
                capabilities=["test"]
            )
            await registry.register_agent(reg)

        query = DiscoveryQuery(agent_type="analyzer")
        result = await registry.discover_agents(query)

        assert result["count"] == 2

    @pytest.mark.asyncio
    async def test_discover_by_region(self, registry):
        """Test discovering agents by region."""
        # Register agents in different regions
        regions = [
            ("agent-1", "us-west"),
            ("agent-2", "us-west"),
            ("agent-3", "eu-central"),
        ]

        for agent_id, region in regions:
            reg = ANPRegistration(
                agent_id=agent_id,
                agent_type="worker",
                capabilities=["test"]
            )
            result = await registry.register_agent(reg)
            # Update region in agent info
            registry.agents[agent_id].region = region
            registry._update_indexes(registry.agents[agent_id])

        query = DiscoveryQuery(region="us-west")
        result = await registry.discover_agents(query)

        assert result["count"] == 2

    @pytest.mark.asyncio
    async def test_discover_by_load_threshold(self, registry):
        """Test discovering agents by load score."""
        # Register agents with different load scores
        loads = [
            ("agent-1", 0.2),
            ("agent-2", 0.5),
            ("agent-3", 0.9),
        ]

        for agent_id, load in loads:
            reg = ANPRegistration(agent_id=agent_id, agent_type="worker", capabilities=["test"])
            await registry.register_agent(reg)
            await registry.heartbeat(agent_id, load_score=load)

        # Find agents with load < 0.6
        query = DiscoveryQuery(max_load=0.6)
        result = await registry.discover_agents(query)

        assert result["count"] == 2
        # Verify load scores are sorted (lowest first)
        assert result["agents"][0]["load_score"] < result["agents"][1]["load_score"]

    @pytest.mark.asyncio
    async def test_discover_by_health_status(self, registry):
        """Test discovering agents by health status."""
        # Register agents with different health statuses
        statuses = [
            ("agent-1", AgentStatus.HEALTHY.value),
            ("agent-2", AgentStatus.DEGRADED.value),
            ("agent-3", AgentStatus.HEALTHY.value),
        ]

        for agent_id, status in statuses:
            reg = ANPRegistration(
                agent_id=agent_id,
                agent_type="worker",
                capabilities=["test"],
                health_status=status
            )
            await registry.register_agent(reg)

        query = DiscoveryQuery(health_status=AgentStatus.HEALTHY.value)
        result = await registry.discover_agents(query)

        assert result["count"] == 2

    @pytest.mark.asyncio
    async def test_discover_with_limit(self, registry):
        """Test discovery result limiting."""
        # Register many agents
        for i in range(10):
            reg = ANPRegistration(
                agent_id=f"agent-{i}",
                agent_type="worker",
                capabilities=["test"]
            )
            await registry.register_agent(reg)

        query = DiscoveryQuery(limit=5)
        result = await registry.discover_agents(query)

        assert result["count"] == 5
        assert len(result["agents"]) == 5

    @pytest.mark.asyncio
    async def test_discover_load_balanced_sorting(self, registry):
        """Test that discovery sorts by load for load balancing."""
        # Register agents with specific load scores
        for i, load in enumerate([0.8, 0.2, 0.5, 0.1, 0.9]):
            reg = ANPRegistration(
                agent_id=f"agent-{i}",
                agent_type="worker",
                capabilities=["test"]
            )
            await registry.register_agent(reg)
            await registry.heartbeat(f"agent-{i}", load_score=load)

        query = DiscoveryQuery()
        result = await registry.discover_agents(query)

        # Verify sorted by load (ascending)
        loads = [agent["load_score"] for agent in result["agents"]]
        assert loads == sorted(loads)


# ============================================================================
# NETWORK TOPOLOGY TESTS
# ============================================================================


@pytest.mark.unit
@pytest.mark.protocol
class TestNetworkTopology:
    """Test network topology tracking."""

    @pytest.mark.asyncio
    async def test_topology_total_agents(self, registry):
        """Test topology reports correct agent count."""
        # Register agents
        for i in range(5):
            reg = ANPRegistration(
                agent_id=f"agent-{i}",
                agent_type="worker",
                capabilities=["test"]
            )
            await registry.register_agent(reg)

        topology = await registry.get_network_topology()
        assert topology.total_agents == 5

    @pytest.mark.asyncio
    async def test_topology_agents_by_type(self, registry):
        """Test topology counts agents by type."""
        types = [
            ("agent-1", "analyzer"),
            ("agent-2", "analyzer"),
            ("agent-3", "coordinator"),
            ("agent-4", "worker"),
        ]

        for agent_id, agent_type in types:
            reg = ANPRegistration(
                agent_id=agent_id,
                agent_type=agent_type,
                capabilities=["test"]
            )
            await registry.register_agent(reg)

        topology = await registry.get_network_topology()
        assert topology.agents_by_type["analyzer"] == 2
        assert topology.agents_by_type["coordinator"] == 1
        assert topology.agents_by_type["worker"] == 1

    @pytest.mark.asyncio
    async def test_topology_agents_by_region(self, registry):
        """Test topology counts agents by region."""
        for i in range(3):
            reg = ANPRegistration(
                agent_id=f"agent-{i}",
                agent_type="worker",
                capabilities=["test"]
            )
            await registry.register_agent(reg)
            # Set custom region
            registry.agents[f"agent-{i}"].region = "us-east" if i < 2 else "eu-west"

        topology = await registry.get_network_topology()
        assert topology.agents_by_region["us-east"] == 2
        assert topology.agents_by_region["eu-west"] == 1

    @pytest.mark.asyncio
    async def test_topology_capability_coverage(self, registry):
        """Test topology tracks capability coverage."""
        capabilities_list = [
            ["text-analysis", "sentiment"],
            ["text-analysis", "translation"],
            ["image-processing"],
        ]

        for i, capabilities in enumerate(capabilities_list):
            reg = ANPRegistration(
                agent_id=f"agent-{i}",
                agent_type="worker",
                capabilities=capabilities
            )
            await registry.register_agent(reg)

        topology = await registry.get_network_topology()
        assert topology.capability_coverage["text-analysis"] == 2
        assert topology.capability_coverage["sentiment"] == 1
        assert topology.capability_coverage["translation"] == 1
        assert topology.capability_coverage["image-processing"] == 1

    @pytest.mark.asyncio
    async def test_topology_average_load(self, registry):
        """Test topology calculates average load."""
        loads = [0.2, 0.4, 0.6, 0.8]

        for i, load in enumerate(loads):
            reg = ANPRegistration(
                agent_id=f"agent-{i}",
                agent_type="worker",
                capabilities=["test"]
            )
            await registry.register_agent(reg)
            await registry.heartbeat(f"agent-{i}", load_score=load)

        topology = await registry.get_network_topology()
        expected_avg = sum(loads) / len(loads)
        assert abs(topology.average_load - expected_avg) < 0.01


# ============================================================================
# EVENT SYSTEM TESTS
# ============================================================================


@pytest.mark.unit
@pytest.mark.protocol
class TestEventSystem:
    """Test event handler system."""

    @pytest.mark.asyncio
    async def test_event_registration_success(self, registry, sample_registration):
        """Test event is emitted on registration."""
        events = []

        def handler(data):
            events.append(("registered", data.agent_id))

        registry.on_event("agent_registered", handler)
        await registry.register_agent(sample_registration)

        assert len(events) == 1
        assert events[0] == ("registered", "test-agent-1")

    @pytest.mark.asyncio
    async def test_event_deregistration(self, registry, sample_registration):
        """Test event is emitted on deregistration."""
        events = []

        def handler(data):
            events.append(("deregistered", data.agent_id))

        await registry.register_agent(sample_registration)
        registry.on_event("agent_deregistered", handler)
        await registry.deregister_agent("test-agent-1")

        assert len(events) == 1
        assert events[0] == ("deregistered", "test-agent-1")

    @pytest.mark.asyncio
    async def test_event_async_handler(self, registry, sample_registration):
        """Test async event handlers work correctly."""
        events = []

        async def async_handler(data):
            await asyncio.sleep(0.01)
            events.append(data.agent_id)

        registry.on_event("agent_registered", async_handler)
        await registry.register_agent(sample_registration)

        await asyncio.sleep(0.05)  # Wait for async handler
        assert len(events) == 1

    @pytest.mark.asyncio
    async def test_multiple_event_handlers(self, registry, sample_registration):
        """Test multiple handlers for same event."""
        events1 = []
        events2 = []

        def handler1(data):
            events1.append("handler1")

        def handler2(data):
            events2.append("handler2")

        registry.on_event("agent_registered", handler1)
        registry.on_event("agent_registered", handler2)
        await registry.register_agent(sample_registration)

        assert len(events1) == 1
        assert len(events2) == 1


# ============================================================================
# ANP CLIENT TESTS
# ============================================================================


@pytest.mark.unit
@pytest.mark.protocol
class TestANPClient:
    """Test ANP client functionality."""

    @pytest.mark.asyncio
    async def test_client_register(self, client):
        """Test client registration."""
        result = await client.register(
            agent_id="client-agent",
            agent_type="worker",
            capabilities=["processing"],
            endpoints={"http": "http://localhost:8000"}
        )

        assert result["success"] is True
        assert result["agent_id"] == "client-agent"

    @pytest.mark.asyncio
    async def test_client_deregister(self, client):
        """Test client deregistration."""
        await client.register(
            agent_id="client-agent",
            agent_type="worker",
            capabilities=["processing"]
        )

        result = await client.deregister("client-agent")
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_client_heartbeat(self, client):
        """Test client heartbeat."""
        await client.register(
            agent_id="client-agent",
            agent_type="worker",
            capabilities=["processing"]
        )

        result = await client.heartbeat(
            "client-agent",
            health_status=AgentStatus.HEALTHY.value,
            load_score=0.5
        )

        assert result["success"] is True
        assert result["heartbeat_count"] == 1

    @pytest.mark.asyncio
    async def test_client_discover(self, client):
        """Test client discovery."""
        # Register some agents
        await client.register(
            agent_id="agent-1",
            agent_type="analyzer",
            capabilities=["text-analysis"]
        )
        await client.register(
            agent_id="agent-2",
            agent_type="analyzer",
            capabilities=["text-analysis"]
        )

        # Discover
        agents = await client.discover(capabilities=["text-analysis"])
        assert len(agents) == 2

    @pytest.mark.asyncio
    async def test_client_get_network_info(self, client):
        """Test client getting network info."""
        await client.register(
            agent_id="agent-1",
            agent_type="worker",
            capabilities=["test"]
        )

        info = await client.get_network_info()
        assert info["total_agents"] == 1
        assert "agents_by_type" in info


# ============================================================================
# STATISTICS TESTS
# ============================================================================


@pytest.mark.unit
@pytest.mark.protocol
class TestStatistics:
    """Test statistics gathering."""

    @pytest.mark.asyncio
    async def test_registration_stats(self, registry):
        """Test registration statistics."""
        for i in range(3):
            reg = ANPRegistration(
                agent_id=f"agent-{i}",
                agent_type="worker",
                capabilities=["test"]
            )
            await registry.register_agent(reg)

        stats = await registry.get_statistics()
        assert stats["stats"]["total_registrations"] == 3

    @pytest.mark.asyncio
    async def test_discovery_stats(self, registry):
        """Test discovery statistics."""
        reg = ANPRegistration(
            agent_id="agent-1",
            agent_type="worker",
            capabilities=["test"]
        )
        await registry.register_agent(reg)

        # Perform discoveries
        for _ in range(5):
            await registry.discover_agents(DiscoveryQuery())

        stats = await registry.get_statistics()
        assert stats["stats"]["total_discoveries"] == 5

    @pytest.mark.asyncio
    async def test_heartbeat_stats(self, registry, sample_registration):
        """Test heartbeat statistics."""
        await registry.register_agent(sample_registration)

        # Send heartbeats
        for _ in range(10):
            await registry.heartbeat("test-agent-1")

        stats = await registry.get_statistics()
        assert stats["stats"]["total_heartbeats"] == 10

    @pytest.mark.asyncio
    async def test_deregistration_stats(self, registry):
        """Test deregistration statistics."""
        for i in range(3):
            reg = ANPRegistration(
                agent_id=f"agent-{i}",
                agent_type="worker",
                capabilities=["test"]
            )
            await registry.register_agent(reg)
            await registry.deregister_agent(f"agent-{i}")

        stats = await registry.get_statistics()
        assert stats["stats"]["total_deregistrations"] == 3


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


@pytest.mark.integration
@pytest.mark.protocol
class TestANPIntegration:
    """Integration tests for complete ANP workflows."""

    @pytest.mark.asyncio
    async def test_complete_agent_lifecycle(self, registry):
        """Test complete agent lifecycle."""
        # Register
        reg = ANPRegistration(
            agent_id="lifecycle-agent",
            agent_type="worker",
            capabilities=["processing"],
            endpoints={"http": "http://localhost:8000"}
        )
        result = await registry.register_agent(reg)
        assert result["success"] is True

        # Send heartbeats
        for i in range(3):
            result = await registry.heartbeat("lifecycle-agent", load_score=0.5)
            assert result["success"] is True

        # Update registration
        reg.capabilities = ["processing", "analysis"]
        result = await registry.register_agent(reg)
        assert result["is_update"] is True

        # Discover
        query = DiscoveryQuery(capabilities=["analysis"])
        result = await registry.discover_agents(query)
        assert result["count"] == 1

        # Deregister
        result = await registry.deregister_agent("lifecycle-agent")
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_multi_agent_coordination_discovery(self, registry):
        """Test discovering agents for coordination."""
        # Register diverse agent fleet
        agents = [
            ("analyzer-1", "analyzer", ["text-analysis", "sentiment"], 0.3),
            ("analyzer-2", "analyzer", ["text-analysis", "translation"], 0.7),
            ("coordinator-1", "coordinator", ["orchestration"], 0.5),
            ("worker-1", "worker", ["data-processing"], 0.2),
            ("worker-2", "worker", ["data-processing"], 0.9),
        ]

        for agent_id, agent_type, capabilities, load in agents:
            reg = ANPRegistration(
                agent_id=agent_id,
                agent_type=agent_type,
                capabilities=capabilities
            )
            await registry.register_agent(reg)
            await registry.heartbeat(agent_id, load_score=load)

        # Find least loaded text analyzers
        query = DiscoveryQuery(
            capabilities=["text-analysis"],
            max_load=0.5,
            limit=10
        )
        result = await registry.discover_agents(query)

        assert result["count"] == 1
        assert result["agents"][0]["agent_id"] == "analyzer-1"

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, registry):
        """Test concurrent registration and discovery."""
        # Register multiple agents concurrently
        tasks = []
        for i in range(10):
            reg = ANPRegistration(
                agent_id=f"concurrent-{i}",
                agent_type="worker",
                capabilities=["test"]
            )
            tasks.append(registry.register_agent(reg))

        results = await asyncio.gather(*tasks)
        assert all(r["success"] for r in results)

        # Concurrent discoveries
        discovery_tasks = [
            registry.discover_agents(DiscoveryQuery())
            for _ in range(5)
        ]
        results = await asyncio.gather(*discovery_tasks)
        assert all(r["count"] == 10 for r in results)
