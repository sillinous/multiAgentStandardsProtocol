"""
A2A Message Bus

Central message routing and delivery infrastructure for agent-to-agent communication.
Implements pub/sub patterns, request-response, and point-to-point messaging.
"""

import asyncio
import logging
from typing import Dict, List, Callable, Awaitable, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime

from .protocol import (
    A2AEnvelope,
    A2AMessage,
    MessageType,
    AgentInfo,
    Priority
)


@dataclass
class MessageHandler:
    """Handler for processing A2A messages"""
    agent_id: str
    message_types: Set[MessageType]
    handler: Callable[[A2AEnvelope], Awaitable[Optional[A2AEnvelope]]]


@dataclass
class BusMetrics:
    """Metrics for A2A message bus"""
    total_messages: int = 0
    successful_deliveries: int = 0
    failed_deliveries: int = 0
    agents_registered: int = 0
    broadcast_messages: int = 0

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "total_messages": self.total_messages,
            "successful_deliveries": self.successful_deliveries,
            "failed_deliveries": self.failed_deliveries,
            "agents_registered": self.agents_registered,
            "broadcast_messages": self.broadcast_messages
        }


class A2AMessageBus:
    """
    A2A Message Bus for Agent Communication

    Provides:
    - Agent registration and discovery
    - Message routing and delivery
    - Pub/sub patterns
    - Request-response patterns
    - Message prioritization
    - Metrics and monitoring
    """

    def __init__(self):
        """Initialize message bus"""
        self.logger = logging.getLogger(__name__)

        # Agent registry
        self.agents: Dict[str, AgentInfo] = {}

        # Message handlers
        self.handlers: Dict[str, List[MessageHandler]] = {}

        # Pending responses (for request-response pattern)
        self.pending_responses: Dict[str, asyncio.Future] = {}

        # Metrics
        self.metrics = BusMetrics()

        # Message queue by priority
        self.message_queues: Dict[Priority, asyncio.Queue] = {
            Priority.CRITICAL: asyncio.Queue(),
            Priority.HIGH: asyncio.Queue(),
            Priority.NORMAL: asyncio.Queue(),
            Priority.LOW: asyncio.Queue()
        }

        # Processing task
        self.processing_task: Optional[asyncio.Task] = None
        self.running = False

        self.logger.info("✅ A2A Message Bus initialized")

    async def start(self):
        """Start message processing"""
        if self.running:
            return

        self.running = True
        self.processing_task = asyncio.create_task(self._process_messages())
        self.logger.info("🚀 A2A Message Bus started")

    async def stop(self):
        """Stop message processing"""
        if not self.running:
            return

        self.running = False
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass

        self.logger.info("⏹️  A2A Message Bus stopped")

    def register_agent(self, agent_info: AgentInfo):
        """Register an agent with the bus"""
        self.agents[agent_info.agent_id] = agent_info
        self.metrics.agents_registered = len(self.agents)
        self.logger.info(f"📝 Registered agent: {agent_info.name} ({agent_info.agent_id})")

    def unregister_agent(self, agent_id: str):
        """Unregister an agent from the bus"""
        if agent_id in self.agents:
            agent_info = self.agents[agent_id]
            del self.agents[agent_id]
            self.metrics.agents_registered = len(self.agents)
            self.logger.info(f"🗑️  Unregistered agent: {agent_info.name} ({agent_id})")

            # Remove handlers
            if agent_id in self.handlers:
                del self.handlers[agent_id]

    def register_handler(
        self,
        agent_id: str,
        message_types: Set[MessageType],
        handler: Callable[[A2AEnvelope], Awaitable[Optional[A2AEnvelope]]]
    ):
        """Register a message handler for an agent"""
        if agent_id not in self.handlers:
            self.handlers[agent_id] = []

        self.handlers[agent_id].append(
            MessageHandler(
                agent_id=agent_id,
                message_types=message_types,
                handler=handler
            )
        )

        self.logger.info(
            f"📥 Registered handler for {agent_id}: {[mt.value for mt in message_types]}"
        )

    async def send(self, envelope: A2AEnvelope) -> bool:
        """
        Send a message to the bus for delivery

        Args:
            envelope: A2A envelope to send

        Returns:
            True if message was queued successfully
        """
        self.metrics.total_messages += 1

        # Check if expired
        if envelope.is_expired():
            self.logger.warning(f"❌ Message {envelope.message_id} expired (TTL exceeded)")
            self.metrics.failed_deliveries += 1
            return False

        # Add to appropriate priority queue
        try:
            await self.message_queues[envelope.priority].put(envelope)
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to queue message: {e}")
            self.metrics.failed_deliveries += 1
            return False

    async def broadcast(self, envelope: A2AEnvelope) -> int:
        """
        Broadcast a message to all registered agents

        Args:
            envelope: A2A envelope to broadcast

        Returns:
            Number of agents message was delivered to
        """
        self.metrics.broadcast_messages += 1
        delivered = 0

        for agent_id in self.agents.keys():
            # Clone envelope for each recipient
            envelope.to_agent = agent_id

            if await self._deliver_message(envelope):
                delivered += 1

        self.logger.info(f"📡 Broadcast delivered to {delivered}/{len(self.agents)} agents")
        return delivered

    async def request(
        self,
        envelope: A2AEnvelope,
        timeout_seconds: float = 30.0
    ) -> Optional[A2AEnvelope]:
        """
        Send a request and wait for response

        Args:
            envelope: A2A envelope to send
            timeout_seconds: Timeout for waiting for response

        Returns:
            Response envelope or None if timeout
        """
        # Create future for response
        correlation_id = envelope.correlation_id or envelope.message_id
        future = asyncio.Future()
        self.pending_responses[correlation_id] = future

        # Send request
        if not await self.send(envelope):
            del self.pending_responses[correlation_id]
            return None

        # Wait for response
        try:
            response = await asyncio.wait_for(future, timeout=timeout_seconds)
            return response
        except asyncio.TimeoutError:
            self.logger.warning(f"⏱️  Request {correlation_id} timed out")
            if correlation_id in self.pending_responses:
                del self.pending_responses[correlation_id]
            return None

    async def _process_messages(self):
        """Main message processing loop"""
        while self.running:
            try:
                # Process messages by priority (highest first)
                envelope = None

                for priority in [Priority.CRITICAL, Priority.HIGH, Priority.NORMAL, Priority.LOW]:
                    try:
                        envelope = await asyncio.wait_for(
                            self.message_queues[priority].get(),
                            timeout=0.1
                        )
                        break
                    except asyncio.TimeoutError:
                        continue

                if envelope is None:
                    await asyncio.sleep(0.1)
                    continue

                # Deliver message
                await self._deliver_message(envelope)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error processing message: {e}", exc_info=True)

    async def _deliver_message(self, envelope: A2AEnvelope) -> bool:
        """
        Deliver a message to its recipient(s)

        Args:
            envelope: A2A envelope to deliver

        Returns:
            True if delivered successfully
        """
        try:
            # Check if expired
            if envelope.is_expired():
                self.logger.warning(f"Message {envelope.message_id} expired during delivery")
                self.metrics.failed_deliveries += 1
                return False

            # Handle broadcast
            if envelope.to_agent == "*":
                delivered = False
                for agent_id in self.agents.keys():
                    if await self._deliver_to_agent(agent_id, envelope):
                        delivered = True
                if delivered:
                    self.metrics.successful_deliveries += 1
                return delivered

            # Deliver to specific agent
            if envelope.to_agent:
                if await self._deliver_to_agent(envelope.to_agent, envelope):
                    self.metrics.successful_deliveries += 1
                    return True
                else:
                    self.metrics.failed_deliveries += 1
                    return False

            # No recipient specified
            self.logger.warning(f"Message {envelope.message_id} has no recipient")
            self.metrics.failed_deliveries += 1
            return False

        except Exception as e:
            self.logger.error(f"Error delivering message: {e}", exc_info=True)
            self.metrics.failed_deliveries += 1
            return False

    async def _deliver_to_agent(self, agent_id: str, envelope: A2AEnvelope) -> bool:
        """Deliver message to a specific agent"""
        if agent_id not in self.agents:
            self.logger.warning(f"Agent {agent_id} not found")
            return False

        if agent_id not in self.handlers:
            self.logger.debug(f"No handlers registered for agent {agent_id}")
            return False

        # Call all matching handlers
        message_type = envelope.message.message_type if envelope.message else None
        if not message_type:
            return False

        delivered = False
        for handler_info in self.handlers[agent_id]:
            if message_type in handler_info.message_types:
                try:
                    # Call handler
                    response = await handler_info.handler(envelope)

                    # If handler returns a response, handle it
                    if response:
                        # Check if this is a response to a pending request
                        if response.correlation_id and response.correlation_id in self.pending_responses:
                            future = self.pending_responses[response.correlation_id]
                            if not future.done():
                                future.set_result(response)
                            del self.pending_responses[response.correlation_id]
                        else:
                            # Send response back through bus
                            await self.send(response)

                    delivered = True

                except Exception as e:
                    self.logger.error(
                        f"Error in handler for {agent_id}: {e}",
                        exc_info=True
                    )

        return delivered

    def get_agent(self, agent_id: str) -> Optional[AgentInfo]:
        """Get agent info by ID"""
        return self.agents.get(agent_id)

    def get_all_agents(self) -> List[AgentInfo]:
        """Get all registered agents"""
        return list(self.agents.values())

    def get_metrics(self) -> BusMetrics:
        """Get bus metrics"""
        return self.metrics

    def get_stats(self) -> Dict:
        """Get bus statistics"""
        return {
            "agents_registered": len(self.agents),
            "handlers_registered": sum(len(h) for h in self.handlers.values()),
            "pending_responses": len(self.pending_responses),
            "metrics": self.metrics.to_dict()
        }


# Global message bus instance
_global_bus: Optional[A2AMessageBus] = None


def get_message_bus() -> A2AMessageBus:
    """Get global message bus instance"""
    global _global_bus
    if _global_bus is None:
        _global_bus = A2AMessageBus()
    return _global_bus
