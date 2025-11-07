"""
🔷 CANONICAL BaseAgent Implementation - SuperStandard v1.0 🔷

This is THE SINGLE SOURCE OF TRUTH for all agents in the ecosystem.
All agents MUST inherit from this class to ensure protocol compliance.

⚠️ IMPORTANT: Do NOT create new BaseAgent classes!
   Import from this file: from src.superstandard.agents.base.base_agent import BaseAgent

Protocols Supported:
- A2A (Agent-to-Agent): Direct agent communication
- A2P (Agent-to-Pay): Financial transactions between agents
- ACP (Agent Coordination Protocol): Multi-agent coordination
- ANP (Agent Network Protocol): Agent discovery and registration
- MCP (Model Context Protocol): AI model integration

Version: 2.0.0 (Protocol-Compliant)
Date: 2025-10-15
Canonical Status: Established 2025-11-06 (BaseAgent Consolidation Phase 1)
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
import json
import os

# Import protocol support
from .protocols import (
    ProtocolMixin,
    A2AMessage,
    ANPRegistration,
    AgentStatus,
    MessageType as ProtocolMessageType,
)


class AgentCapability(Enum):
    """Agent capabilities"""

    TESTING = "testing"
    DESIGN = "design"
    DEVELOPMENT = "development"
    QA_EVALUATION = "qa_evaluation"
    ORCHESTRATION = "orchestration"


class MessageType(Enum):
    """Message types for inter-agent communication"""

    TEST_REPORT = "test_report"
    DESIGN_SPEC = "design_spec"
    IMPLEMENTATION_REPORT = "implementation_report"
    QA_REVIEW = "qa_review"
    CONSENSUS_CHECK = "consensus_check"
    TASK_ASSIGNMENT = "task_assignment"
    STATUS_UPDATE = "status_update"


class BaseAgent(ABC, ProtocolMixin):
    """
    Protocol-Compliant Base Agent

    ALL agents MUST inherit from this class to ensure:
    - A2A (Agent-to-Agent) communication
    - A2P (Agent-to-Pay) capability
    - ACP (Agent Coordination Protocol) support
    - ANP (Agent Network Protocol) registration
    - MCP (Model Context Protocol) integration

    This class provides:
    - Abstract methods for task execution and analysis
    - Workspace management and artifact persistence
    - Message passing with protocol compliance
    - Network registration and heartbeat
    - Knowledge base access
    """

    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        capabilities: List[AgentCapability],
        workspace_path: str = "./autonomous-ecosystem/workspace",
    ):
        # Initialize ProtocolMixin FIRST for protocol support
        super().__init__()

        # Agent identity
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.capabilities = capabilities
        self.capabilities_list = [cap.value for cap in capabilities]

        # Workspace
        self.workspace_path = workspace_path
        os.makedirs(workspace_path, exist_ok=True)

        # State
        self.current_iteration = 1
        self.messages_sent = []
        self.messages_received = []

        # Protocol registration (will be set on network registration)
        self._registration = None

    @abstractmethod
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a specific task assigned to this agent

        Args:
            task: Task specification

        Returns:
            Task execution result
        """
        pass

    @abstractmethod
    async def analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze input and generate recommendations

        Args:
            input_data: Data to analyze

        Returns:
            Analysis results
        """
        pass

    def send_message(
        self,
        message_type: MessageType,
        recipient: str,
        content: Dict[str, Any],
        iteration: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Send a message to another agent or the orchestrator

        Args:
            message_type: Type of message
            recipient: Agent ID of recipient
            content: Message content
            iteration: Current iteration number

        Returns:
            Message record
        """
        message = {
            "id": f"msg_{datetime.now().timestamp()}",
            "type": message_type.value,
            "sender": self.agent_id,
            "recipient": recipient,
            "timestamp": datetime.now().isoformat(),
            "iteration": iteration or self.current_iteration,
            "content": content,
        }

        # Save message to workspace
        self._save_message(message)
        self.messages_sent.append(message)

        return message

    def receive_message(self, message: Dict[str, Any]) -> None:
        """
        Receive a message from another agent

        Args:
            message: Message to receive
        """
        self.messages_received.append(message)

    def _save_message(self, message: Dict[str, Any]) -> None:
        """Save message to workspace"""
        iteration_path = os.path.join(
            self.workspace_path, f"iterations/iteration_{str(self.current_iteration).zfill(3)}"
        )
        os.makedirs(iteration_path, exist_ok=True)

        message_file = os.path.join(iteration_path, f"{message['type']}_{message['id']}.json")

        with open(message_file, "w") as f:
            json.dump(message, f, indent=2)

    def load_knowledge_base(self) -> Dict[str, Any]:
        """Load knowledge base documents"""
        kb_path = os.path.join(self.workspace_path, "knowledge_base")
        knowledge = {}

        if os.path.exists(kb_path):
            for filename in os.listdir(kb_path):
                if filename.endswith(".md") or filename.endswith(".json"):
                    filepath = os.path.join(kb_path, filename)
                    with open(filepath, "r") as f:
                        knowledge[filename] = f.read()

        return knowledge

    def save_artifact(
        self, artifact_type: str, content: Any, filename: str, iteration: Optional[int] = None
    ) -> str:
        """
        Save an artifact to the workspace

        Args:
            artifact_type: Type of artifact (test_reports, design_specs, etc.)
            content: Artifact content
            filename: Filename for artifact
            iteration: Iteration number

        Returns:
            Path to saved artifact
        """
        iter_num = iteration or self.current_iteration
        artifact_path = os.path.join(
            self.workspace_path, f"iterations/iteration_{str(iter_num).zfill(3)}", artifact_type
        )
        os.makedirs(artifact_path, exist_ok=True)

        filepath = os.path.join(artifact_path, filename)

        if isinstance(content, (dict, list)):
            with open(filepath, "w") as f:
                json.dump(content, f, indent=2)
        else:
            with open(filepath, "w") as f:
                f.write(str(content))

        return filepath

    def load_artifact(
        self, artifact_type: str, filename: str, iteration: Optional[int] = None
    ) -> Any:
        """
        Load an artifact from the workspace

        Args:
            artifact_type: Type of artifact
            filename: Filename of artifact
            iteration: Iteration number

        Returns:
            Artifact content
        """
        iter_num = iteration or self.current_iteration
        filepath = os.path.join(
            self.workspace_path,
            f"iterations/iteration_{str(iter_num).zfill(3)}",
            artifact_type,
            filename,
        )

        if not os.path.exists(filepath):
            return None

        with open(filepath, "r") as f:
            if filename.endswith(".json"):
                return json.load(f)
            else:
                return f.read()

    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "capabilities": [cap.value for cap in self.capabilities],
            "current_iteration": self.current_iteration,
            "messages_sent": len(self.messages_sent),
            "messages_received": len(self.messages_received),
            "timestamp": datetime.now().isoformat(),
        }

    # ========================================================================
    # PROTOCOL-COMPLIANT METHODS
    # Override ProtocolMixin methods to integrate with workspace
    # ========================================================================

    async def send_a2a_message(
        self,
        target_agent_id: str,
        message_type: str,
        payload: Dict[str, Any],
        correlation_id: Optional[str] = None,
    ) -> A2AMessage:
        """
        Send A2A-compliant message (overrides ProtocolMixin)

        This method extends the parent's A2A messaging with workspace
        persistence to maintain message history.

        Args:
            target_agent_id: Target agent ID
            message_type: Message type (request, response, etc.)
            payload: Message payload
            correlation_id: Optional correlation ID for request/response

        Returns:
            A2AMessage object
        """
        # Use parent's A2A protocol
        message = await super().send_a2a_message(
            target_agent_id, message_type, payload, correlation_id
        )

        # Persist to workspace
        self._save_message(message.to_dict())
        self.messages_sent.append(message.to_dict())

        return message

    async def initialize_agent(self) -> ANPRegistration:
        """
        Initialize agent and register on network

        This method should be called after agent instantiation to:
        - Register agent on the network (ANP)
        - Advertise capabilities
        - Begin heartbeat monitoring

        Returns:
            ANPRegistration object
        """
        self._registration = await self.register_on_network()
        print(f"[{self.agent_id}] Registered on network")
        print(f"  - Protocols: {', '.join(self.get_supported_protocols())}")
        print(f"  - Status: {AgentStatus.HEALTHY.value}")
        print(f"  - Capabilities: {', '.join(self.capabilities_list)}")

        return self._registration

    def is_protocol_compliant(self) -> bool:
        """
        Check if agent is protocol-compliant

        Returns:
            True if agent supports all required protocols
        """
        required_protocols = ["A2A", "A2P", "ACP", "ANP", "MCP"]
        supported = self.get_supported_protocols()
        return all(protocol in supported for protocol in required_protocols)
