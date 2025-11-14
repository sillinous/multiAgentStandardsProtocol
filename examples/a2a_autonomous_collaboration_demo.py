#!/usr/bin/env python3
"""
A2A Autonomous Collaboration Demo

Demonstrates the revolutionary A2A (Agent-to-Agent) protocol and meta-agents:

1. FactoryMetaAgent creates specialized agents on-demand
2. CoordinatorMetaAgent orchestrates multi-agent workflows
3. Agents communicate via standards-compliant A2A protocol
4. Autonomous multi-phase workflow execution

This is THE ULTIMATE demonstration of:
- Agents creating other agents (meta-cognition!)
- Autonomous coordination and collaboration
- Standards-compliant A2A messaging
- Self-organizing agent teams

THE SYSTEM BUILDS ITSELF! 🤯

Usage:
    python examples/a2a_autonomous_collaboration_demo.py
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import time

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.superstandard.a2a.bus import A2AMessageBus, get_message_bus
from src.superstandard.a2a.protocol import (
    AgentInfo,
    Capability,
    A2AEnvelope,
    MessageType,
    create_task_completed
)
from src.superstandard.meta_agents.factory import FactoryMetaAgent, AgentSpec
from src.superstandard.meta_agents.coordinator import (
    CoordinatorMetaAgent,
    WorkflowPhase,
    Task
)
from src.superstandard.monitoring.dashboard import get_dashboard

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SimulatedSpecializedAgent:
    """
    Simulated specialized agent for demonstration.

    In production, these would be real agents with actual capabilities.
    For demo purposes, we simulate agent behavior.
    """

    def __init__(self, agent_info: AgentInfo, bus: A2AMessageBus):
        """Initialize simulated agent"""
        self.agent_info = agent_info
        self.bus = bus
        self.logger = logging.getLogger(f"Agent.{agent_info.name}")

        # Register with bus
        self.bus.register_agent(agent_info)

        # Register message handler
        self.bus.register_handler(
            agent_info.agent_id,
            {MessageType.TASK_ASSIGNMENT},
            self._handle_task_assignment
        )

        self.logger.info(f"✅ {agent_info.name} initialized")

    async def _handle_task_assignment(
        self,
        envelope: A2AEnvelope
    ) -> Optional[A2AEnvelope]:
        """Handle task assignment"""
        content = envelope.message.content
        task_id = content.get("task_id")
        task_type = content.get("task_type")
        parameters = content.get("parameters", {})

        self.logger.info(f"📥 Received task: {task_type} (ID: {task_id})")
        self.logger.info(f"   Parameters: {parameters}")

        # Simulate work
        await asyncio.sleep(2)

        # Simulate result based on task type
        if "data_collection" in task_type:
            result = {
                "data_collected": True,
                "records": 150,
                "quality_score": 95.5,
                "source": self.agent_info.name
            }
        elif "analysis" in task_type:
            result = {
                "analysis_completed": True,
                "insights_found": 12,
                "confidence": 87.3,
                "analyzer": self.agent_info.name
            }
        elif "synthesis" in task_type:
            result = {
                "synthesis_completed": True,
                "patterns_identified": 8,
                "recommendations": 5,
                "synthesizer": self.agent_info.name
            }
        elif "validation" in task_type:
            result = {
                "validation_completed": True,
                "passed_checks": 15,
                "quality_score": 98.2,
                "validator": self.agent_info.name
            }
        else:
            result = {
                "task_completed": True,
                "agent": self.agent_info.name
            }

        self.logger.info(f"✅ Task completed: {task_id}")

        # Send completion message
        response = create_task_completed(
            self.agent_info,
            task_id,
            result,
            reply_to=envelope.message_id
        )

        return response


class A2ADemo:
    """
    A2A Autonomous Collaboration Demo

    Demonstrates the full power of A2A protocol and meta-agents.
    """

    def __init__(self):
        """Initialize demo"""
        self.bus = get_message_bus()
        self.dashboard = get_dashboard()

        self.factory = FactoryMetaAgent(self.bus)
        self.coordinator = CoordinatorMetaAgent("OpportunityWorkflowCoordinator", self.bus)

        self.created_agents: Dict[str, SimulatedSpecializedAgent] = {}

        logger.info("✅ A2A Demo initialized")

    async def run(self):
        """Run the complete demonstration"""
        print("\n" + "=" * 80)
        print("🚀 A2A AUTONOMOUS COLLABORATION DEMO")
        print("=" * 80)
        print("\nDemonstrating:")
        print("  • Meta-agents creating specialized agents")
        print("  • Standards-compliant A2A protocol communication")
        print("  • Autonomous multi-phase workflow execution")
        print("  • Agent coordination and collaboration")
        print("\n" + "=" * 80)
        print()

        # Start message bus
        await self.bus.start()

        # Broadcast system health
        await self.dashboard.system_health_updated(
            cpu_percent=15.0,
            memory_percent=40.0,
            active_agents=0
        )

        try:
            # Phase 1: Create Specialized Agents
            print("\n" + "─" * 80)
            print("PHASE 1: Meta-Agent Creates Specialized Agents")
            print("─" * 80)

            agents = await self._create_agent_team()

            print(f"\n✅ Created {len(agents)} specialized agents using FactoryMetaAgent")
            print(f"   Agents registered with A2A message bus")
            print()

            # Phase 2: Define Workflow
            print("─" * 80)
            print("PHASE 2: Define Multi-Phase Workflow")
            print("─" * 80)

            workflow = self._define_workflow()

            print(f"\n✅ Workflow defined: {len(workflow)} phases")
            for i, phase in enumerate(workflow, 1):
                print(f"   {i}. {phase.name} ({len(phase.tasks)} tasks)")
            print()

            # Phase 3: Execute Workflow
            print("─" * 80)
            print("PHASE 3: CoordinatorMetaAgent Orchestrates Execution")
            print("─" * 80)
            print("\nAgents communicating via A2A protocol...")
            print()

            start_time = time.time()

            results = await self.coordinator.execute_workflow(
                workflow_id="opportunity-discovery-001",
                phases=workflow,
                agents=agents
            )

            duration = time.time() - start_time

            # Phase 4: Display Results
            print("\n" + "─" * 80)
            print("PHASE 4: Autonomous Workflow Complete!")
            print("─" * 80)

            self._display_results(results, duration)

            # Phase 5: Show Statistics
            print("\n" + "─" * 80)
            print("PHASE 5: System Statistics")
            print("─" * 80)

            self._display_statistics()

            print("\n" + "=" * 80)
            print("✅ DEMO COMPLETE - THE SYSTEM BUILT ITSELF!")
            print("=" * 80)
            print("\nKey Achievements:")
            print("  ✅ Meta-agent created specialized agents autonomously")
            print("  ✅ Agents coordinated via standards-compliant A2A protocol")
            print("  ✅ Multi-phase workflow executed without human intervention")
            print("  ✅ Agents communicated peer-to-peer using A2A messages")
            print("  ✅ Coordinator orchestrated the entire process")
            print("\n🤯 This is the future of autonomous AI systems!")
            print()

        finally:
            # Cleanup
            await self.bus.stop()

    async def _create_agent_team(self) -> list[AgentInfo]:
        """Create a team of specialized agents using FactoryMetaAgent"""
        agent_specs = [
            AgentSpec(
                agent_type="data_collector",
                name="DataCollectorAgent",
                capabilities=["data_collection"],
                configuration={"max_records": 1000, "timeout": 30},
                description="Collects data from external sources"
            ),
            AgentSpec(
                agent_type="analyzer",
                name="AnalysisAgent",
                capabilities=["analysis"],
                configuration={"analysis_depth": "deep", "confidence_threshold": 0.8},
                description="Analyzes collected data for insights"
            ),
            AgentSpec(
                agent_type="synthesizer",
                name="SynthesisAgent",
                capabilities=["synthesis"],
                configuration={"pattern_matching": True, "recommendation_count": 5},
                description="Synthesizes analysis results into actionable insights"
            ),
            AgentSpec(
                agent_type="validator",
                name="ValidationAgent",
                capabilities=["validation"],
                configuration={"validation_rules": ["completeness", "accuracy", "consistency"]},
                description="Validates results against quality criteria"
            )
        ]

        print(f"\n🏭 FactoryMetaAgent creating {len(agent_specs)} specialized agents...")
        print()

        created_infos = []
        for spec in agent_specs:
            print(f"   Creating: {spec.name}...")
            agent_info = await self.factory.create_agent(spec)

            if agent_info:
                # Create simulated agent with behavior
                simulated_agent = SimulatedSpecializedAgent(agent_info, self.bus)
                self.created_agents[agent_info.agent_id] = simulated_agent
                created_infos.append(agent_info)
                print(f"   ✅ {spec.name} created and registered")

        return created_infos

    def _define_workflow(self) -> list[WorkflowPhase]:
        """Define multi-phase workflow"""
        return [
            WorkflowPhase(
                phase_id="phase-1",
                name="Data Collection",
                parallel=True,
                tasks=[
                    Task(
                        task_id="task-1-1",
                        task_type="data_collection",
                        parameters={"source": "market_data", "region": "US"}
                    ),
                    Task(
                        task_id="task-1-2",
                        task_type="data_collection",
                        parameters={"source": "competitor_data", "region": "US"}
                    )
                ]
            ),
            WorkflowPhase(
                phase_id="phase-2",
                name="Analysis",
                parallel=False,
                tasks=[
                    Task(
                        task_id="task-2-1",
                        task_type="analysis",
                        parameters={"analysis_type": "market_trends", "depth": "deep"}
                    )
                ]
            ),
            WorkflowPhase(
                phase_id="phase-3",
                name="Synthesis",
                parallel=False,
                tasks=[
                    Task(
                        task_id="task-3-1",
                        task_type="synthesis",
                        parameters={"pattern_types": ["convergent", "divergent"]}
                    )
                ]
            ),
            WorkflowPhase(
                phase_id="phase-4",
                name="Validation",
                parallel=False,
                tasks=[
                    Task(
                        task_id="task-4-1",
                        task_type="validation",
                        parameters={"criteria": ["completeness", "accuracy", "actionability"]}
                    )
                ]
            )
        ]

    def _display_results(self, results: Dict[str, Any], duration: float):
        """Display workflow results"""
        print(f"\n⏱️  Total Execution Time: {duration:.2f}s")
        print(f"\n📊 Results by Phase:")
        print()

        for phase_id, phase_results in results.items():
            print(f"   {phase_id.upper()}:")
            for task_id, task_result in phase_results.items():
                if "error" in task_result:
                    print(f"      ❌ {task_id}: {task_result['error']}")
                else:
                    print(f"      ✅ {task_id}:")
                    for key, value in task_result.items():
                        print(f"         • {key}: {value}")
            print()

    def _display_statistics(self):
        """Display system statistics"""
        print()

        # Factory stats
        factory_stats = self.factory.get_stats()
        print("🏭 FactoryMetaAgent Statistics:")
        print(f"   • Total Agents Created: {factory_stats['total_agents_created']}")
        print(f"   • Active Agents: {len(factory_stats['active_agents'])}")
        print()

        # Coordinator stats
        coord_stats = self.coordinator.get_stats()
        print("🎯 CoordinatorMetaAgent Statistics:")
        print(f"   • Active Workflows: {coord_stats['active_workflows']}")
        print(f"   • Total Tasks: {coord_stats['total_tasks']}")
        print(f"   • Completed Tasks: {coord_stats['completed_tasks']}")
        print(f"   • Failed Tasks: {coord_stats['failed_tasks']}")
        print()

        # Bus stats
        bus_stats = self.bus.get_stats()
        print("📡 A2A Message Bus Statistics:")
        print(f"   • Agents Registered: {bus_stats['agents_registered']}")
        print(f"   • Total Messages: {bus_stats['metrics']['total_messages']}")
        print(f"   • Successful Deliveries: {bus_stats['metrics']['successful_deliveries']}")
        print(f"   • Failed Deliveries: {bus_stats['metrics']['failed_deliveries']}")
        print()


async def main():
    """Main entry point"""
    demo = A2ADemo()
    await demo.run()


if __name__ == "__main__":
    asyncio.run(main())
