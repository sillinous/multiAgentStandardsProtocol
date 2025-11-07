"""
🏭 AgentFactory - Agent Instantiation and Management
====================================================

Central factory for creating and managing live agent instances.

Features:
- Discovers available agent classes from the agent modules
- Instantiates agents based on type
- Manages lifecycle of all running agents
- Provides registry of instantiated vs. registered-only agents

Usage:
    factory = AgentFactory()

    # Create and start an agent
    runtime_agent = await factory.create_agent(
        agent_id="analyst-001",
        agent_type="analytics",
        capabilities=["data_analysis"],
        auto_start=True
    )

    # Get all running agents
    running = factory.get_running_agents()

    # Stop an agent
    await factory.stop_agent("analyst-001")
"""

import asyncio
import logging
import importlib
import inspect
from typing import Dict, Any, Optional, Type, List
from pathlib import Path

from ..base.base_agent import BaseAgent
from .runtime_agent import RuntimeAgent, AgentState

logger = logging.getLogger(__name__)


class AgentFactory:
    """
    Factory for creating and managing live agent instances.

    Maintains registry of:
    - Available agent classes (by type)
    - Running agent instances
    - Agent metadata and capabilities
    """

    def __init__(self):
        """Initialize the agent factory"""
        self.available_agents: Dict[str, Type[BaseAgent]] = {}
        self.running_agents: Dict[str, RuntimeAgent] = {}

        # Discover available agent classes
        self._discover_agent_classes()

        logger.info(f"🏭 AgentFactory initialized")
        logger.info(f"   Available agent types: {list(self.available_agents.keys())}")

    def _discover_agent_classes(self):
        """
        Discover all available agent classes from the agents module.

        Scans the agents directory and imports agent classes.
        """
        # Map of common agent types to their modules
        agent_type_map = {
            "analytics": "superstandard.agents.analysis.analytics_agent_v1.AnalyticsAgent",
            "sentiment": "superstandard.agents.analysis.sentiment_analysis_agent.SentimentAnalysisAgent",
            "anomaly_detection": "superstandard.agents.analysis.anomaly_detection_task_agent_v1.AnomalyDetectionAgent",
            "coordinator": "superstandard.agents.coordination.agent_ecosystem_coordinator.AgentEcosystemCoordinator",
            "monitor": "superstandard.agents.monitoring.activity_tracker_agent_v1.ActivityTrackerAgent",
            "processor": "superstandard.agents.data.data_processor_agent.DataProcessorAgent",
        }

        for agent_type, module_path in agent_type_map.items():
            try:
                # Parse module path
                parts = module_path.rsplit('.', 1)
                module_name = parts[0]
                class_name = parts[1]

                # Import module and get class
                module = importlib.import_module(module_name)
                agent_class = getattr(module, class_name)

                # Verify it's a BaseAgent subclass
                if inspect.isclass(agent_class) and issubclass(agent_class, BaseAgent):
                    self.available_agents[agent_type] = agent_class
                    logger.info(f"   ✅ Registered agent type: {agent_type} ({class_name})")
                else:
                    logger.warning(f"   ⚠️ {class_name} is not a BaseAgent subclass")

            except Exception as e:
                logger.warning(f"   ⚠️ Could not load {agent_type}: {e}")

        # Add generic fallback agent
        self.available_agents["generic"] = self._create_generic_agent_class()

    def _create_generic_agent_class(self) -> Type[BaseAgent]:
        """Create a generic agent class for unknown types"""
        from ..base.base_agent import BaseAgent, AgentCapability

        class GenericAgent(BaseAgent):
            """Generic agent for testing and unknown types"""

            def __init__(self, agent_id: str, agent_type: str, capabilities: List[str], **kwargs):
                # Convert string capabilities to AgentCapability enum
                cap_enum = []
                for cap in capabilities:
                    try:
                        cap_enum.append(AgentCapability(cap.lower()))
                    except ValueError:
                        # Use a default if capability doesn't match enum
                        cap_enum.append(AgentCapability.TESTING)

                super().__init__(
                    agent_id=agent_id,
                    agent_type=agent_type,
                    capabilities=cap_enum if cap_enum else [AgentCapability.TESTING],
                    workspace_path=kwargs.get("workspace_path", "./workspace")
                )

            async def initialize_agent(self):
                """Initialize generic agent (no network registration needed for demo)"""
                logger.info(f"[{self.agent_id}] Generic agent initialized")
                return None

            async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
                """Execute generic task"""
                task_type = task.get("type", "unknown")
                logger.info(f"[{self.agent_id}] Executing generic task: {task_type}")

                return {
                    "agent_id": self.agent_id,
                    "task_type": task_type,
                    "status": "completed",
                    "message": f"Generic agent processed {task_type} task"
                }

            async def analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
                """Perform generic analysis"""
                logger.info(f"[{self.agent_id}] Performing generic analysis")

                return {
                    "agent_id": self.agent_id,
                    "analysis": "Generic analysis complete",
                    "data_received": len(input_data),
                    "confidence": 0.5
                }

        return GenericAgent

    async def create_agent(
        self,
        agent_id: str,
        agent_type: str,
        capabilities: List[str],
        metadata: Optional[Dict[str, Any]] = None,
        auto_start: bool = True
    ) -> RuntimeAgent:
        """
        Create and optionally start an agent instance.

        Args:
            agent_id: Unique agent identifier
            agent_type: Type of agent to create
            capabilities: Agent capabilities
            metadata: Additional metadata
            auto_start: Whether to start agent immediately

        Returns:
            RuntimeAgent wrapper around the agent instance
        """
        # Check if agent already running
        if agent_id in self.running_agents:
            logger.warning(f"Agent {agent_id} already exists")
            return self.running_agents[agent_id]

        # Get agent class
        agent_class = self.available_agents.get(agent_type)
        if not agent_class:
            logger.warning(f"Unknown agent type '{agent_type}', using generic agent")
            agent_class = self.available_agents["generic"]

        # Instantiate agent
        try:
            logger.info(f"🏭 Creating agent: {agent_id} (type: {agent_type})")

            # Create agent instance
            agent_instance = agent_class(
                agent_id=agent_id,
                agent_type=agent_type,
                capabilities=capabilities,
                workspace_path=f"./workspace/{agent_id}"
            )

            # Wrap with runtime
            runtime_agent = RuntimeAgent(agent_instance)

            # Start if requested
            if auto_start:
                await runtime_agent.start()

            # Register in running agents
            self.running_agents[agent_id] = runtime_agent

            logger.info(f"✅ Agent {agent_id} created and {'started' if auto_start else 'ready'}")

            return runtime_agent

        except Exception as e:
            logger.error(f"❌ Failed to create agent {agent_id}: {e}")
            raise

    async def stop_agent(self, agent_id: str) -> bool:
        """
        Stop a running agent.

        Args:
            agent_id: ID of agent to stop

        Returns:
            True if stopped successfully
        """
        if agent_id not in self.running_agents:
            logger.warning(f"Agent {agent_id} not found")
            return False

        runtime_agent = self.running_agents[agent_id]
        await runtime_agent.stop()
        del self.running_agents[agent_id]

        logger.info(f"⭕ Agent {agent_id} stopped and removed")
        return True

    async def pause_agent(self, agent_id: str) -> bool:
        """Pause an agent"""
        if agent_id not in self.running_agents:
            return False

        await self.running_agents[agent_id].pause()
        return True

    async def resume_agent(self, agent_id: str) -> bool:
        """Resume a paused agent"""
        if agent_id not in self.running_agents:
            return False

        await self.running_agents[agent_id].resume()
        return True

    async def submit_task(self, agent_id: str, task: Dict[str, Any]) -> Optional[str]:
        """
        Submit a task to a running agent.

        Args:
            agent_id: Target agent ID
            task: Task specification

        Returns:
            Task ID if successful
        """
        if agent_id not in self.running_agents:
            logger.warning(f"Agent {agent_id} not found")
            return None

        runtime_agent = self.running_agents[agent_id]
        return await runtime_agent.submit_task(task)

    def get_running_agents(self) -> List[Dict[str, Any]]:
        """Get list of all running agents"""
        return [
            runtime_agent.get_status()
            for runtime_agent in self.running_agents.values()
        ]

    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get status of specific agent"""
        if agent_id not in self.running_agents:
            return None

        return self.running_agents[agent_id].get_status()

    def get_available_types(self) -> List[str]:
        """Get list of available agent types"""
        return list(self.available_agents.keys())

    async def stop_all_agents(self):
        """Stop all running agents"""
        logger.info(f"Stopping all {len(self.running_agents)} agents...")

        for agent_id in list(self.running_agents.keys()):
            await self.stop_agent(agent_id)

        logger.info("✅ All agents stopped")
