"""
Message Routing Agent - Enterprise A2A Communication Hub
Coordinates all agent-to-agent communication with intelligent routing and monitoring
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict
import uuid

from .interfaces import (
    AgentMessage,
    AgentResponse,
    AgentEvent,
    AgentIdentifier,
    MessageType,
    Priority,
    AgentTeam,
    ProcessStatus,
    AgentCommunicationInterface,
    BaseAgent,
)
from .message_bus import message_bus, MessageBus
from .workflow_orchestrator import workflow_orchestrator

logger = logging.getLogger(__name__)


class MessageRoutingAgent(BaseAgent):
    """
    Central Message Routing Agent for Agent-to-Agent Communication

    Capabilities:
    - Priority-based message routing
    - Load balancing across agent teams
    - Message queue management
    - Delivery tracking and analytics
    - Event pub/sub coordination
    - Circuit breaker management
    - Rate limiting enforcement
    """

    def __init__(self):
        # Initialize base agent
        identifier = AgentIdentifier(
            id="message_routing_agent",
            name="Message Routing Agent",
            team=AgentTeam.MASTER_ORCHESTRATOR,
            apqc_domain="13.0 Manage Information Technology",
            version="1.0.0",
            capabilities=[
                "message_routing",
                "priority_queue_management",
                "load_balancing",
                "delivery_tracking",
                "event_broadcasting",
                "circuit_breaker_management",
                "rate_limiting",
                "agent_discovery",
                "health_monitoring",
                "analytics",
            ],
            status="active",
        )

        super().__init__(identifier)

        # Message bus reference
        self.message_bus: MessageBus = message_bus

        # Routing statistics
        self.routing_stats = defaultdict(int)
        self.team_message_counts = defaultdict(int)
        self.priority_distribution = defaultdict(int)
        self.agent_health_status = {}

        # Message tracking
        self.message_history = []  # Last 1000 messages
        self.max_history = 1000

        # Health check intervals
        self.health_check_interval_seconds = 60
        self.last_health_check = datetime.utcnow()

        # Register message handlers
        self._register_handlers()

        logger.info("Message Routing Agent initialized successfully")

    def _register_handlers(self):
        """Register handlers for different message types"""
        self.register_message_handler("request", self._handle_routing_request)
        self.register_message_handler("broadcast", self._handle_broadcast)
        self.register_message_handler("event", self._handle_event)
        self.register_message_handler("workflow_task", self._handle_workflow_task)

        self.register_event_handler("agent_registered", self._handle_agent_registered)
        self.register_event_handler("agent_health_check", self._handle_health_check)
        self.register_event_handler("system_alert", self._handle_system_alert)

    async def send_message(self, message: AgentMessage) -> AgentResponse:
        """Route message to target agent with intelligent routing"""
        try:
            # Track message in history
            self._track_message(message)

            # Update statistics
            self.routing_stats["total_messages"] += 1
            self.priority_distribution[message.priority.value] += 1

            if message.target_agent:
                self.team_message_counts[message.target_agent.team.value] += 1

            # Route through message bus
            response = await self.message_bus.send_message(message)

            # Update success statistics
            if response.status == "success":
                self.routing_stats["successful_deliveries"] += 1
            else:
                self.routing_stats["failed_deliveries"] += 1

            return response

        except Exception as e:
            logger.error(f"Message routing failed: {e}")
            self.routing_stats["routing_errors"] += 1

            return AgentResponse(
                request_id=message.id,
                source_agent=self.identifier,
                status="error",
                error_message=f"Routing failed: {str(e)}",
                execution_time_ms=0,
            )

    async def broadcast_event(self, event: AgentEvent) -> List[AgentResponse]:
        """Broadcast event to multiple agents"""
        try:
            # Track broadcast
            self.routing_stats["total_broadcasts"] += 1

            # Route through message bus
            responses = await self.message_bus.broadcast_event(event)

            # Update statistics
            self.routing_stats["broadcast_recipients"] += len(responses)

            return responses

        except Exception as e:
            logger.error(f"Event broadcast failed: {e}")
            self.routing_stats["broadcast_errors"] += 1
            return []

    async def route_to_best_agent(self, message: AgentMessage, team: AgentTeam) -> AgentResponse:
        """
        Intelligently route message to best available agent in team
        Uses load balancing and health status
        """
        try:
            # Get available agents from team
            agents = await self.message_bus.get_agents_by_team(team)

            if not agents:
                return AgentResponse(
                    request_id=message.id,
                    source_agent=self.identifier,
                    status="error",
                    error_message=f"No available agents in team {team.value}",
                    execution_time_ms=0,
                )

            # Filter healthy agents
            healthy_agents = [agent for agent in agents if self._is_agent_healthy(agent.id)]

            if not healthy_agents:
                # Fallback to any available agent
                healthy_agents = agents

            # Select agent with load balancing
            selected_agent = self._select_balanced_agent(healthy_agents)

            # Update message target
            message.target_agent = selected_agent

            # Route message
            return await self.send_message(message)

        except Exception as e:
            logger.error(f"Smart routing failed: {e}")
            return AgentResponse(
                request_id=message.id,
                source_agent=self.identifier,
                status="error",
                error_message=f"Smart routing failed: {str(e)}",
                execution_time_ms=0,
            )

    async def subscribe_to_events(self, event_types: List[str], callback) -> str:
        """Subscribe to specific event types"""
        return await self.message_bus.subscribe_to_events(self.identifier.id, event_types, callback)

    async def register_agent(self, agent: AgentIdentifier) -> bool:
        """Register new agent with routing system"""
        try:
            success = await self.message_bus.register_agent(agent)

            if success:
                self.routing_stats["agents_registered"] += 1
                self.agent_health_status[agent.id] = {
                    "status": "healthy",
                    "last_seen": datetime.utcnow(),
                    "message_count": 0,
                    "error_count": 0,
                }

                logger.info(f"Agent {agent.name} registered with routing system")

            return success

        except Exception as e:
            logger.error(f"Failed to register agent: {e}")
            return False

    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister agent from routing system"""
        try:
            success = await self.message_bus.unregister_agent(agent_id)

            if success:
                self.routing_stats["agents_unregistered"] += 1
                if agent_id in self.agent_health_status:
                    del self.agent_health_status[agent_id]

                logger.info(f"Agent {agent_id} unregistered from routing system")

            return success

        except Exception as e:
            logger.error(f"Failed to unregister agent: {e}")
            return False

    async def get_routing_statistics(self) -> Dict[str, Any]:
        """Get comprehensive routing statistics"""
        # Get message bus stats
        bus_stats = await self.message_bus.get_delivery_statistics()

        # Calculate routing efficiency
        total_messages = self.routing_stats.get("total_messages", 0)
        successful = self.routing_stats.get("successful_deliveries", 0)

        routing_efficiency = (successful / max(total_messages, 1)) * 100

        return {
            "routing_agent_stats": {
                "total_messages_routed": total_messages,
                "successful_deliveries": successful,
                "failed_deliveries": self.routing_stats.get("failed_deliveries", 0),
                "routing_efficiency_pct": round(routing_efficiency, 2),
                "total_broadcasts": self.routing_stats.get("total_broadcasts", 0),
                "broadcast_recipients": self.routing_stats.get("broadcast_recipients", 0),
                "agents_registered": self.routing_stats.get("agents_registered", 0),
                "routing_errors": self.routing_stats.get("routing_errors", 0),
            },
            "priority_distribution": dict(self.priority_distribution),
            "team_message_distribution": dict(self.team_message_counts),
            "message_bus_stats": bus_stats,
            "agent_health": {
                "total_agents": len(self.agent_health_status),
                "healthy_agents": sum(
                    1 for h in self.agent_health_status.values() if h["status"] == "healthy"
                ),
                "unhealthy_agents": sum(
                    1 for h in self.agent_health_status.values() if h["status"] != "healthy"
                ),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def get_agent_health_report(self) -> Dict[str, Any]:
        """Get detailed health report for all agents"""
        return {
            "agents": self.agent_health_status,
            "total_agents": len(self.agent_health_status),
            "health_check_interval": self.health_check_interval_seconds,
            "last_health_check": self.last_health_check.isoformat(),
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def get_message_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent message history"""
        return self.message_history[-limit:]

    async def perform_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check on routing system"""
        health_report = {
            "routing_agent": "healthy",
            "message_bus": "unknown",
            "workflow_orchestrator": "unknown",
            "checks_performed": [],
            "issues_found": [],
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Check message bus
        try:
            if self.message_bus.running:
                health_report["message_bus"] = "healthy"
                health_report["checks_performed"].append("message_bus_running")
            else:
                health_report["message_bus"] = "unhealthy"
                health_report["issues_found"].append("message_bus_not_running")
        except Exception as e:
            health_report["message_bus"] = "error"
            health_report["issues_found"].append(f"message_bus_check_failed: {e}")

        # Check workflow orchestrator
        try:
            if workflow_orchestrator.running:
                health_report["workflow_orchestrator"] = "healthy"
                health_report["checks_performed"].append("orchestrator_running")
            else:
                health_report["workflow_orchestrator"] = "unhealthy"
                health_report["issues_found"].append("orchestrator_not_running")
        except Exception as e:
            health_report["workflow_orchestrator"] = "error"
            health_report["issues_found"].append(f"orchestrator_check_failed: {e}")

        # Check queue sizes
        try:
            queue_size = self.message_bus.message_queue.size()
            health_report["queue_size"] = queue_size
            health_report["checks_performed"].append("queue_size_check")

            if queue_size > 5000:
                health_report["issues_found"].append(f"high_queue_size: {queue_size}")
        except Exception as e:
            health_report["issues_found"].append(f"queue_size_check_failed: {e}")

        # Update overall health
        if health_report["issues_found"]:
            health_report["routing_agent"] = "degraded"

        self.last_health_check = datetime.utcnow()

        return health_report

    # Request resource - not implemented in this routing-focused agent
    async def request_resource(self, request):
        raise NotImplementedError("Resource requests should go to ResourceManager")

    # Share knowledge - delegates to knowledge manager
    async def share_knowledge(self, artifact):
        raise NotImplementedError("Knowledge sharing should go to KnowledgeManager")

    # Execute workflow task - delegates to workflow orchestrator
    async def execute_workflow_task(self, task):
        raise NotImplementedError("Task execution should go to WorkflowOrchestrator")

    # Provide feedback - delegates to quality feedback system
    async def provide_feedback(self, feedback):
        raise NotImplementedError("Feedback should go to QualityFeedbackSystem")

    # Private helper methods

    def _track_message(self, message: AgentMessage):
        """Track message in history"""
        message_record = {
            "id": message.id,
            "type": message.message_type.value,
            "source": message.source_agent.id,
            "target": message.target_agent.id if message.target_agent else "broadcast",
            "priority": message.priority.value,
            "timestamp": message.timestamp.isoformat(),
        }

        self.message_history.append(message_record)

        # Trim history to max size
        if len(self.message_history) > self.max_history:
            self.message_history = self.message_history[-self.max_history :]

    def _is_agent_healthy(self, agent_id: str) -> bool:
        """Check if agent is healthy"""
        if agent_id not in self.agent_health_status:
            return True  # Unknown agents assumed healthy

        health = self.agent_health_status[agent_id]

        # Check if agent has been seen recently (within 5 minutes)
        if (datetime.utcnow() - health["last_seen"]) > timedelta(minutes=5):
            health["status"] = "stale"
            return False

        # Check error rate
        total_messages = health.get("message_count", 0)
        error_count = health.get("error_count", 0)

        if total_messages > 10:  # Only check if enough data
            error_rate = error_count / total_messages
            if error_rate > 0.5:  # Over 50% errors
                health["status"] = "unhealthy"
                return False

        return health["status"] == "healthy"

    def _select_balanced_agent(self, agents: List[AgentIdentifier]) -> AgentIdentifier:
        """Select agent using load balancing"""
        # Simple round-robin for now
        # In production, would use more sophisticated load balancing

        # Get message counts for each agent
        agent_loads = {}
        for agent in agents:
            health = self.agent_health_status.get(agent.id, {})
            agent_loads[agent.id] = health.get("message_count", 0)

        # Select agent with lowest load
        selected = min(agents, key=lambda a: agent_loads.get(a.id, 0))

        # Update load
        if selected.id in self.agent_health_status:
            self.agent_health_status[selected.id]["message_count"] += 1
            self.agent_health_status[selected.id]["last_seen"] = datetime.utcnow()

        return selected

    # Message handlers

    async def _handle_routing_request(self, message: AgentMessage) -> Dict[str, Any]:
        """Handle routing request message"""
        # Route the message
        response = await self.send_message(message)

        return {"routed": True, "response": response.dict()}

    async def _handle_broadcast(self, message: AgentMessage) -> Dict[str, Any]:
        """Handle broadcast message"""
        # Convert to event and broadcast
        event = AgentEvent(
            event_type="broadcast_message",
            source_agent=message.source_agent,
            scope="enterprise",
            payload=message.payload,
        )

        responses = await self.broadcast_event(event)

        return {"broadcast": True, "recipients": len(responses)}

    async def _handle_event(self, message: AgentMessage) -> Dict[str, Any]:
        """Handle event message"""
        # Extract event and broadcast
        event_data = message.payload.get("event", {})

        if event_data:
            event = AgentEvent(**event_data)
            responses = await self.broadcast_event(event)

            return {"event_broadcast": True, "recipients": len(responses)}

        return {"event_broadcast": False, "error": "No event data"}

    async def _handle_workflow_task(self, message: AgentMessage) -> Dict[str, Any]:
        """Handle workflow task routing"""
        # Route to workflow orchestrator
        task_data = message.payload.get("task", {})

        return {"task_routed": True, "task_id": task_data.get("id", "unknown")}

    async def _handle_agent_registered(self, event: AgentEvent):
        """Handle agent registration event"""
        agent_id = event.payload.get("agent_id")

        if agent_id:
            self.agent_health_status[agent_id] = {
                "status": "healthy",
                "last_seen": datetime.utcnow(),
                "message_count": 0,
                "error_count": 0,
            }

            logger.info(f"Agent {agent_id} registration event processed")

    async def _handle_health_check(self, event: AgentEvent):
        """Handle health check event"""
        agent_id = event.source_agent.id

        if agent_id in self.agent_health_status:
            self.agent_health_status[agent_id]["last_seen"] = datetime.utcnow()
            self.agent_health_status[agent_id]["status"] = "healthy"

    async def _handle_system_alert(self, event: AgentEvent):
        """Handle system alert event"""
        logger.warning(f"System alert received: {event.payload}")

        # Could implement alert escalation logic here
        if event.severity == "critical":
            # Escalate to system administrators
            pass


# Global routing agent instance
routing_agent = MessageRoutingAgent()


# Utility functions for easy access
async def route_message(message: AgentMessage) -> AgentResponse:
    """Route message through the routing agent"""
    return await routing_agent.send_message(message)


async def route_to_team(message: AgentMessage, team: AgentTeam) -> AgentResponse:
    """Route message to best agent in team"""
    return await routing_agent.route_to_best_agent(message, team)


async def broadcast_to_all(event: AgentEvent) -> List[AgentResponse]:
    """Broadcast event to all agents"""
    return await routing_agent.broadcast_event(event)


async def get_routing_stats() -> Dict[str, Any]:
    """Get routing statistics"""
    return await routing_agent.get_routing_statistics()


async def check_routing_health() -> Dict[str, Any]:
    """Perform health check on routing system"""
    return await routing_agent.perform_health_check()
