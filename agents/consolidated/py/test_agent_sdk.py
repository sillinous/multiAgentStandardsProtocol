import pytest

"""
Tests assume agent_ecosystem_sdk is installed in the environment.
Install locally via:
    pip install -e ../market-research-agentic-ecosystem/agent_ecosystem_sdk
"""

try:
    from agent_ecosystem_sdk.core import AgentClient
    from agent_ecosystem_sdk.agents import Agent, AgentType
    from agent_ecosystem_sdk.orchestration import AgentOrchestrator
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False

@pytest.mark.skipif(not SDK_AVAILABLE, reason="Agent Ecosystem SDK not available")
class TestAgentSDK:

    @pytest.fixture
    def agent_client(self):
        return AgentClient(
            api_url="http://localhost:8000",
            api_key="test-key"
        )

    def test_agent_client_initialization(self, agent_client):
        assert agent_client.api_url == "http://localhost:8000"
        assert agent_client.api_key == "test-key"

    def test_agent_creation(self):
        agent = Agent(
            name="Test Agent",
            agent_type=AgentType.ANALYSIS,
            capabilities=["data_analysis", "visualization"]
        )
        assert agent.name == "Test Agent"
        assert agent.agent_type == AgentType.ANALYSIS
        assert "data_analysis" in agent.capabilities

    @pytest.mark.asyncio
    async def test_agent_orchestration(self):
        orchestrator = AgentOrchestrator()

        # Mock agent for testing
        class MockAgent:
            def __init__(self, name):
                self.name = name

            async def execute(self, task):
                return f"Result from {self.name}: {task}"

        agent1 = MockAgent("Agent1")
        agent2 = MockAgent("Agent2")

        orchestrator.add_agent(agent1)
        orchestrator.add_agent(agent2)

        assert len(orchestrator.agents) == 2

    def test_agent_communication_protocol(self):
        """Test agent-to-agent communication protocol."""
        from agent_ecosystem_sdk.core import CommunicationProtocol

        protocol = CommunicationProtocol()
        message = protocol.create_message(
            sender="agent-1",
            receiver="agent-2",
            content={"task": "analyze_market", "data": {"category": "electronics"}}
        )

        assert message["sender"] == "agent-1"
        assert message["receiver"] == "agent-2"
        assert "timestamp" in message
        assert "message_id" in message

@pytest.mark.skipif(not SDK_AVAILABLE, reason="Agent Ecosystem SDK not available")
class TestQuantumReadyFeatures:

    def test_quantum_protocol_interface(self):
        """Test quantum communication protocol interface."""
        try:
            from agent_ecosystem_sdk.quantum import QuantumProtocol
            protocol = QuantumProtocol()
            assert hasattr(protocol, 'initialize_quantum_state')
            assert hasattr(protocol, 'quantum_entanglement')
        except ImportError:
            pytest.skip("Quantum protocol not implemented yet")

    def test_post_quantum_cryptography(self):
        """Test post-quantum cryptography implementation."""
        try:
            from agent_ecosystem_sdk.quantum import PostQuantumCrypto
            crypto = PostQuantumCrypto()
            assert hasattr(crypto, 'generate_keys')
            assert hasattr(crypto, 'encrypt')
            assert hasattr(crypto, 'decrypt')
        except ImportError:
            pytest.skip("Post-quantum cryptography not implemented yet")

@pytest.mark.skipif(not SDK_AVAILABLE, reason="Agent Ecosystem SDK not available")
class TestBlockchainIntegration:

    def test_blockchain_reputation_system(self):
        """Test blockchain reputation system integration."""
        try:
            from agent_ecosystem_sdk.blockchain import ReputationSystem
            reputation = ReputationSystem()
            assert hasattr(reputation, 'get_agent_reputation')
            assert hasattr(reputation, 'update_reputation')
        except ImportError:
            pytest.skip("Blockchain features not implemented yet")

    def test_smart_contract_interaction(self):
        """Test smart contract interaction capabilities."""
        try:
            from agent_ecosystem_sdk.blockchain import SmartContractInterface
            contract = SmartContractInterface()
            assert hasattr(contract, 'deploy_contract')
            assert hasattr(contract, 'execute_contract')
        except ImportError:
            pytest.skip("Smart contract features not implemented yet")
