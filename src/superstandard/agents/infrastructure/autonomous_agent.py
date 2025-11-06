"""
Autonomous Agent Base Class
Event-driven agents with message bus integration
"""

import threading
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from abc import ABC, abstractmethod

from .message_bus import MessageBus, Message, MessagePriority
from .shared_memory import SharedMemory
from .consensus import ConsensusManager, VoteType
from .protocols import (
    ProtocolManager,
    A2AMessage,
    A2APerformative,
    FIPAMessage,
    FIPAPerformative,
    AgentCapability,
    MCPTool,
    PaymentRequest,
    PaymentType,
)


class AutonomousAgent(ABC):
    """
    Base class for autonomous agents
    Provides event-driven architecture with message bus integration
    """

    def __init__(
        self,
        agent_id: str,
        message_bus: MessageBus,
        shared_memory: SharedMemory,
        consensus_manager: ConsensusManager,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize autonomous agent with protocol support

        Args:
            agent_id: Unique agent identifier
            message_bus: MessageBus instance for communication
            shared_memory: SharedMemory instance for data sharing
            consensus_manager: ConsensusManager for voting
            config: Optional agent configuration
        """
        self.agent_id = agent_id
        self.bus = message_bus
        self.memory = shared_memory
        self.consensus = consensus_manager
        self.config = config or {}

        # Protocol manager for standards compliance
        self.protocols = ProtocolManager(shared_memory, message_bus)

        # Agent state
        self.running = False
        self.agent_thread = None
        self.last_activity = None

        # Message handling
        self.message_handlers = {}  # {topic: handler_function}
        self.subscribed_topics = []

        # Performance tracking
        self.messages_sent = 0
        self.messages_received = 0
        self.decisions_made = 0
        self.votes_cast = 0

        # Capabilities and tools
        self.capabilities = []  # List of AgentCapability
        self.tools = []  # List of MCPTool this agent provides

        print(
            f"[{self.agent_id}] Initialized autonomous agent with protocols: {self.protocols.get_supported_protocols()}"
        )

    @abstractmethod
    def on_start(self):
        """Called when agent starts - implement initialization logic"""
        pass

    @abstractmethod
    def on_stop(self):
        """Called when agent stops - implement cleanup logic"""
        pass

    @abstractmethod
    def on_message(self, message: Message):
        """
        Handle incoming messages
        Override this to process messages for your agent

        Args:
            message: Incoming message from message bus
        """
        pass

    def start(self):
        """Start the autonomous agent"""
        if self.running:
            print(f"[{self.agent_id}] Already running")
            return

        self.running = True

        # Subscribe to topics
        self._setup_subscriptions()

        # Call custom start logic
        self.on_start()

        # Start agent loop in background thread
        self.agent_thread = threading.Thread(target=self._agent_loop, daemon=True)
        self.agent_thread.start()

        print(f"[{self.agent_id}] Started")

    def stop(self):
        """Stop the autonomous agent"""
        if not self.running:
            return

        self.running = False

        # Call custom stop logic
        self.on_stop()

        # Unsubscribe from topics
        for topic in self.subscribed_topics:
            self.bus.unsubscribe(topic, self.agent_id)

        # Wait for thread to finish
        if self.agent_thread:
            self.agent_thread.join(timeout=5)

        print(f"[{self.agent_id}] Stopped")

    def _setup_subscriptions(self):
        """Setup message bus subscriptions"""
        # Subscribe to agent-specific messages
        self.subscribe(f"agent.{self.agent_id}.*", self._handle_direct_message)

        # Subscribe to broadcast messages
        self.subscribe("broadcast.*", self._handle_broadcast)

        # Subscribe to consensus messages
        self.subscribe("consensus.*", self._handle_consensus_message)

    def subscribe(self, topic: str, handler: Optional[Callable] = None):
        """
        Subscribe to a topic

        Args:
            topic: Topic to subscribe to (supports wildcards)
            handler: Optional custom handler (defaults to on_message)
        """
        if topic not in self.subscribed_topics:
            callback = handler if handler else self.on_message
            self.bus.subscribe(topic, self.agent_id, callback)
            self.subscribed_topics.append(topic)
            print(f"[{self.agent_id}] Subscribed to {topic}")

    def publish(
        self,
        topic: str,
        data: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        requires_response: bool = False,
    ) -> str:
        """
        Publish a message to the bus

        Args:
            topic: Message topic
            data: Message payload
            priority: Message priority
            requires_response: Whether sender expects responses

        Returns:
            correlation_id for tracking responses
        """
        correlation_id = str(uuid.uuid4())

        self.bus.publish(
            topic=topic,
            data=data,
            sender=self.agent_id,
            priority=priority,
            correlation_id=correlation_id,
            requires_response=requires_response,
        )

        self.messages_sent += 1
        return correlation_id

    def send_direct_message(
        self,
        target_agent: str,
        data: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
    ):
        """
        Send direct message to another agent

        Args:
            target_agent: Target agent ID
            data: Message payload
            priority: Message priority
        """
        topic = f"agent.{target_agent}.direct"
        self.publish(topic, data, priority)

    def broadcast(
        self,
        event_type: str,
        data: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
    ):
        """
        Broadcast message to all agents

        Args:
            event_type: Type of broadcast event
            data: Event data
            priority: Message priority
        """
        topic = f"broadcast.{event_type}"
        self.publish(topic, data, priority)

    def propose_consensus(
        self,
        action: str,
        data: Dict[str, Any],
        min_votes: int = 3,
        threshold: float = 0.6,
        timeout_seconds: int = 30,
    ) -> str:
        """
        Propose an action for consensus voting

        Args:
            action: Action to propose
            data: Action parameters
            min_votes: Minimum votes needed
            threshold: Approval threshold (0.0 - 1.0)
            timeout_seconds: Voting timeout

        Returns:
            proposal_id for tracking
        """
        proposal_id = self.consensus.propose_action(
            proposer=self.agent_id,
            action=action,
            data=data,
            min_votes=min_votes,
            threshold=threshold,
            timeout_seconds=timeout_seconds,
        )

        return proposal_id

    def vote(
        self, proposal_id: str, approve: bool, confidence: float, reasoning: Optional[str] = None
    ):
        """
        Cast a vote on a proposal

        Args:
            proposal_id: Proposal to vote on
            approve: True to approve, False to reject
            confidence: Confidence level (0.0 - 1.0)
            reasoning: Optional explanation
        """
        vote_type = VoteType.APPROVE if approve else VoteType.REJECT

        success = self.consensus.cast_vote(
            proposal_id=proposal_id,
            agent_id=self.agent_id,
            vote_type=vote_type,
            confidence=confidence,
            reasoning=reasoning,
        )

        if success:
            self.votes_cast += 1

    def set_memory(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Store data in shared memory

        Args:
            key: Memory key
            value: Value to store
            ttl: Time-to-live in seconds
        """
        self.memory.set(key, value, ttl=ttl, agent_id=self.agent_id)

    def get_memory(self, key: str, default: Any = None) -> Any:
        """
        Retrieve data from shared memory

        Args:
            key: Memory key
            default: Default if not found

        Returns:
            Stored value or default
        """
        return self.memory.get(key, default)

    def publish_event(self, event_type: str, data: Dict[str, Any]):
        """
        Publish an event to shared memory history

        Args:
            event_type: Type of event
            data: Event data
        """
        self.memory.publish_event(event_type, data, self.agent_id)

    def _handle_direct_message(self, message: Message):
        """Handle direct messages to this agent"""
        self.messages_received += 1
        self.last_activity = datetime.now()
        self.on_message(message)

    def _handle_broadcast(self, message: Message):
        """Handle broadcast messages"""
        self.messages_received += 1
        self.last_activity = datetime.now()
        self.on_message(message)

    def _handle_consensus_message(self, message: Message):
        """Handle consensus-related messages"""
        topic = message.topic

        if topic == "consensus.vote_request":
            # New proposal - agent can decide whether to vote
            proposal_data = message.data
            self._on_vote_request(proposal_data)

        elif topic == "consensus.decision_approved":
            # Proposal was approved
            self._on_proposal_approved(message.data)

        elif topic == "consensus.decision_rejected":
            # Proposal was rejected
            self._on_proposal_rejected(message.data)

    def _on_vote_request(self, proposal_data: Dict[str, Any]):
        """
        Called when a vote is requested
        Override this to implement custom voting logic

        Args:
            proposal_data: Proposal details
        """
        pass  # Agents can override to participate in voting

    def _on_proposal_approved(self, decision_data: Dict[str, Any]):
        """
        Called when a proposal is approved
        Override this to react to approved proposals

        Args:
            decision_data: Decision details including votes
        """
        pass  # Agents can override to react to decisions

    def _on_proposal_rejected(self, decision_data: Dict[str, Any]):
        """
        Called when a proposal is rejected
        Override this to react to rejected proposals

        Args:
            decision_data: Decision details including votes
        """
        pass  # Agents can override to react to decisions

    def _agent_loop(self):
        """
        Main agent loop - runs in background thread
        Override this for custom autonomous behavior
        """
        print(f"[{self.agent_id}] Agent loop started")

        while self.running:
            try:
                # Agents can override this for periodic tasks
                self._periodic_task()

                # Sleep briefly to avoid busy waiting
                time.sleep(1)

            except Exception as e:
                print(f"[{self.agent_id}] Error in agent loop: {e}")
                time.sleep(5)  # Back off on errors

    def _periodic_task(self):
        """
        Periodic task executed in agent loop
        Override this for custom periodic behavior
        """
        pass  # Agents can override for periodic tasks

    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        return {
            "agent_id": self.agent_id,
            "running": self.running,
            "subscribed_topics": len(self.subscribed_topics),
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "decisions_made": self.decisions_made,
            "votes_cast": self.votes_cast,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "capabilities_count": len(self.capabilities),
            "tools_count": len(self.tools),
            "protocols_supported": self.protocols.get_supported_protocols(),
        }

    # ============================================================================
    # Protocol Methods - Standards Compliance
    # ============================================================================

    def register_capability(
        self,
        capability_type: str,
        description: str,
        input_types: List[str],
        output_types: List[str],
        cost_model: Optional[Dict[str, Any]] = None,
    ):
        """
        Register agent capability for discovery

        Args:
            capability_type: Type of capability (e.g., 'trading', 'analysis')
            description: Human-readable description
            input_types: What data types this capability accepts
            output_types: What data types this capability produces
            cost_model: Optional pricing information
        """
        capability = AgentCapability(
            agent_id=self.agent_id,
            capability_type=capability_type,
            description=description,
            input_types=input_types,
            output_types=output_types,
            protocols_supported=self.protocols.get_supported_protocols(),
            cost_model=cost_model,
        )

        self.capabilities.append(capability)
        self.protocols.capabilities.register_capability(capability)

        print(f"[{self.agent_id}] Capability registered: {capability_type}")

    def register_tool(
        self,
        tool_name: str,
        description: str,
        parameters: Dict[str, Any],
        cost: Optional[float] = None,
        rate_limit: Optional[int] = None,
    ):
        """
        Register MCP tool for other agents to discover and use

        Args:
            tool_name: Unique tool name
            description: What the tool does
            parameters: JSON schema for tool parameters
            cost: Cost per invocation
            rate_limit: Maximum calls per minute
        """
        tool = MCPTool(
            name=tool_name,
            description=description,
            parameters=parameters,
            provider=self.agent_id,
            cost=cost,
            rate_limit=rate_limit,
        )

        self.tools.append(tool)
        self.protocols.mcp.register_tool(tool)

        print(f"[{self.agent_id}] Tool registered: {tool_name}")

    def discover_tools(
        self, provider: Optional[str] = None, capability: Optional[str] = None
    ) -> List[MCPTool]:
        """
        Discover available tools from other agents

        Args:
            provider: Filter by specific agent
            capability: Search for specific capability

        Returns:
            List of available tools
        """
        return self.protocols.mcp.discover_tools(provider, capability)

    def discover_agents(self, capability_type: str) -> List[AgentCapability]:
        """
        Find agents with specific capability

        Args:
            capability_type: Type of capability to find

        Returns:
            List of agent capabilities
        """
        return self.protocols.capabilities.discover_agents(capability_type)

    def send_a2a_message(
        self,
        receiver: str,
        performative: A2APerformative,
        content: Dict[str, Any],
        conversation_id: Optional[str] = None,
    ):
        """
        Send A2A protocol standard message

        Args:
            receiver: Target agent ID
            performative: Message type (INFORM, REQUEST, etc.)
            content: Message payload
            conversation_id: Thread ID for multi-message conversations
        """
        if conversation_id is None:
            conversation_id = str(uuid.uuid4())

        message = A2AMessage(
            performative=performative,
            sender=self.agent_id,
            receiver=receiver,
            content=content,
            conversation_id=conversation_id,
        )

        self.protocols.send_a2a_message(message)
        self.messages_sent += 1

    def send_fipa_message(
        self,
        receiver: str,
        performative: FIPAPerformative,
        content: str,
        protocol: Optional[str] = None,
    ):
        """
        Send FIPA ACL compliant message

        Args:
            receiver: Target agent ID
            performative: FIPA performative type
            content: Message content
            protocol: Interaction protocol name
        """
        message = FIPAMessage(
            performative=performative,
            sender=self.agent_id,
            receiver=receiver,
            content=content,
            protocol=protocol,
        )

        self.protocols.send_fipa_message(message)
        self.messages_sent += 1

    def request_payment(
        self, to_agent: str, amount: float, currency: str, payment_type: PaymentType, reason: str
    ) -> str:
        """
        Request payment from another agent (A2Pay protocol)

        Args:
            to_agent: Agent to pay
            amount: Payment amount
            currency: Currency type
            payment_type: Type of payment
            reason: What service is being paid for

        Returns:
            invoice_id for tracking
        """
        payment = PaymentRequest(
            from_agent=self.agent_id,
            to_agent=to_agent,
            amount=amount,
            currency=currency,
            payment_type=payment_type,
            reason=reason,
        )

        return self.protocols.a2pay.request_payment(payment)

    def propose_negotiation(
        self, recipient: str, terms: Dict[str, Any], timeout_seconds: int = 300
    ) -> str:
        """
        Start negotiation with another agent (ANP protocol)

        Args:
            recipient: Agent to negotiate with
            terms: Negotiation terms
            timeout_seconds: How long negotiation remains open

        Returns:
            offer_id for tracking
        """
        return self.protocols.anp.propose_negotiation(
            proposer=self.agent_id,
            recipient=recipient,
            terms=terms,
            timeout_seconds=timeout_seconds,
        )

    def accept_negotiation(self, offer_id: str) -> bool:
        """Accept a negotiation offer"""
        return self.protocols.anp.accept_offer(offer_id)

    def reject_negotiation(self, offer_id: str) -> bool:
        """Reject a negotiation offer"""
        return self.protocols.anp.reject_offer(offer_id)

    def invoke_tool(self, tool_name: str, provider: str, parameters: Dict[str, Any]) -> str:
        """
        Invoke a tool from another agent (MCP protocol)

        Args:
            tool_name: Name of tool to invoke
            provider: Agent providing the tool
            parameters: Tool parameters

        Returns:
            invocation_id for tracking async response
        """
        return self.protocols.mcp.invoke_tool(tool_name, provider, parameters)

    def __repr__(self):
        return f"AutonomousAgent(id='{self.agent_id}', running={self.running}, protocols={len(self.protocols.get_supported_protocols())})"
