"""
Agent Registry Updater - Meta-Agent for Automatic Dashboard Updates
APQC: Meta-Level Agent (13.2 - Manage Business Capabilities)

This meta-agent automatically discovers all agents across all APQC levels
and updates the agent library/dashboard to maintain synchronization between
code and documentation.

Key Capabilities:
- Automatic agent discovery across all levels
- Agent registry database updates
- Dashboard synchronization
- Capability mapping
- APQC alignment tracking
"""

import asyncio
import logging
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from app.a2a_communication.message_routing_agent import routing_agent
from app.a2a_communication.interfaces import (
    AgentIdentifier, AgentTeam
)

logger = logging.getLogger(__name__)


class AgentRegistryUpdater:
    """
    Meta-Agent: Automatic Agent Registry Updates

    Responsibilities:
    - Discover all agents across APQC levels (5, 4, 3, 2, 1)
    - Extract agent metadata (identifier, capabilities, APQC domain)
    - Update agent registry database
    - Synchronize dashboard with current agents
    - Generate agent inventory reports
    - Track APQC framework coverage

    Value Proposition:
    - Eliminates manual dashboard updates
    - Ensures documentation stays in sync with code
    - Provides real-time agent inventory
    - Tracks framework implementation progress
    """

    def __init__(self):
        self.identifier = AgentIdentifier(
            id="agent_registry_updater",
            name="Agent Registry Updater",
            team=AgentTeam.MASTER_ORCHESTRATOR,
            apqc_domain="13.2 Manage Business Capabilities (Meta-Agent)",
            version="1.0.0",
            capabilities=[
                "agent_discovery",
                "registry_updates",
                "dashboard_synchronization",
                "capability_mapping",
                "apqc_tracking"
            ],
            status="active"
        )

        # Base paths for agent discovery
        self.base_path = Path(__file__).parent.parent

        # Level-specific paths
        self.level_paths = {
            5: [
                self.base_path / "enrichment_workflow_coordinator.py",
                self.base_path / "enrichment_agents_a2a.py",
                self.base_path / "product_data_validation_agent.py",
                self.base_path / "market_opportunity_scoring_agent.py",
                self.base_path / "pricing_strategy_agent_a2a.py",
                self.base_path / "customer_profiling_agent_a2a.py",
                self.base_path / "business_model_agent_a2a.py"
            ],
            4: [
                self.base_path / "activities"
            ],
            3: [
                self.base_path / "processes"
            ],
            2: [
                self.base_path / "process_groups"
            ]
        }

        # Registry database path
        self.registry_path = self.base_path / "registry" / "agent_registry.json"

        # Register with routing system
        asyncio.create_task(self._register_with_routing_system())

        logger.info(f"🔄 {self.identifier.name} initialized (Meta-Agent)")

    async def _register_with_routing_system(self):
        """Register this meta-agent with MessageRoutingAgent"""
        try:
            await routing_agent.register_agent(self.identifier)
            logger.info(f"✓ Meta-Agent registered")
        except Exception as e:
            logger.error(f"Failed to register: {e}")

    async def discover_and_update_registry(
        self,
        options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Discover all agents and update registry

        This is the main entry point for automatic updates

        Args:
            options: Configuration options

        Returns:
            Complete registry update report
        """
        start_time = datetime.utcnow()
        update_id = f"registry_update_{int(start_time.timestamp())}"

        logger.info(f"🔄 Starting Agent Registry Update")
        logger.info(f"   Update ID: {update_id}")

        result = {
            "update_id": update_id,
            "started_at": start_time.isoformat(),
            "levels_scanned": [],
            "agents_discovered": {},
            "registry_updated": False,
            "dashboard_synchronized": False,
            "errors": []
        }

        try:
            # Step 1: Discover agents at all levels
            logger.info("🔍 Step 1: Discovering agents across all levels")

            for level in [5, 4, 3, 2, 1]:
                discovered = await self._discover_agents_at_level(level)
                result["levels_scanned"].append(level)
                result["agents_discovered"][f"level_{level}"] = discovered
                logger.info(f"   Level {level}: {len(discovered)} agents discovered")

            # Step 2: Update registry database
            logger.info("💾 Step 2: Updating agent registry")
            registry_data = self._build_registry_data(result["agents_discovered"])
            await self._update_registry_database(registry_data)
            result["registry_updated"] = True

            # Step 3: Synchronize dashboard
            logger.info("📊 Step 3: Synchronizing dashboard")
            await self._synchronize_dashboard(registry_data)
            result["dashboard_synchronized"] = True

            # Step 4: Generate reports
            logger.info("📈 Step 4: Generating coverage reports")
            result["coverage_report"] = self._generate_coverage_report(registry_data)

            # Finalize result
            end_time = datetime.utcnow()
            result["completed_at"] = end_time.isoformat()
            result["duration_seconds"] = (end_time - start_time).total_seconds()
            result["status"] = "success"

            logger.info(
                f"✅ Agent Registry Update complete: "
                f"{sum(len(agents) for agents in result['agents_discovered'].values())} total agents, "
                f"{result['duration_seconds']:.2f}s"
            )

            return result

        except Exception as e:
            logger.error(f"❌ Agent Registry Update failed: {e}", exc_info=True)
            result["status"] = "failed"
            result["errors"].append(str(e))
            return result

    async def _discover_agents_at_level(self, level: int) -> List[Dict[str, Any]]:
        """
        Discover all agents at a specific APQC level

        Uses Python introspection to find agent classes
        """
        discovered_agents = []

        try:
            if level == 5:
                # Level 5: Atomic task agents
                discovered_agents = await self._discover_level_5_agents()
            elif level == 4:
                # Level 4: Activity agents
                discovered_agents = await self._discover_level_4_agents()
            elif level == 3:
                # Level 3: Process agents
                discovered_agents = await self._discover_level_3_agents()
            elif level == 2:
                # Level 2: Process group agents
                discovered_agents = await self._discover_level_2_agents()
            elif level == 1:
                # Level 1: Enterprise agents
                discovered_agents = await self._discover_level_1_agents()

        except Exception as e:
            logger.error(f"Error discovering Level {level} agents: {e}")

        return discovered_agents

    async def _discover_level_5_agents(self) -> List[Dict[str, Any]]:
        """Discover Level 5 atomic task agents"""
        agents = []

        # Import and inspect Level 5 agents
        try:
            from app.agents import (
                product_data_validation_agent,
                market_opportunity_scoring_agent
            )

            # ProductDataValidationAgent
            if hasattr(product_data_validation_agent, 'validation_agent'):
                agent = product_data_validation_agent.validation_agent
                agents.append(self._extract_agent_metadata(agent, 5))

            # MarketOpportunityScoringAgent
            if hasattr(market_opportunity_scoring_agent, 'scoring_agent'):
                agent = market_opportunity_scoring_agent.scoring_agent
                agents.append(self._extract_agent_metadata(agent, 5))

            # A2A Enrichment Agents
            try:
                from app.agents.enrichment_agents_a2a import (
                    product_intelligence_agent,
                    market_analysis_agent,
                    competitive_intelligence_agent,
                    pricing_strategy_agent,
                    customer_profiling_agent,
                    business_model_agent,
                    image_discovery_agent
                )

                for agent_obj in [
                    product_intelligence_agent,
                    market_analysis_agent,
                    competitive_intelligence_agent,
                    pricing_strategy_agent,
                    customer_profiling_agent,
                    business_model_agent,
                    image_discovery_agent
                ]:
                    agents.append(self._extract_agent_metadata(agent_obj, 5))

            except ImportError as e:
                logger.warning(f"Could not import A2A agents: {e}")

        except Exception as e:
            logger.error(f"Error discovering Level 5 agents: {e}")

        return agents

    async def _discover_level_4_agents(self) -> List[Dict[str, Any]]:
        """Discover Level 4 activity agents"""
        agents = []

        try:
            from app.agents.activities import (
                product_analysis_activity,
                market_research_activity,
                business_viability_activity
            )

            for activity in [
                product_analysis_activity,
                market_research_activity,
                business_viability_activity
            ]:
                agents.append(self._extract_agent_metadata(activity, 4))

        except Exception as e:
            logger.error(f"Error discovering Level 4 agents: {e}")

        return agents

    async def _discover_level_3_agents(self) -> List[Dict[str, Any]]:
        """Discover Level 3 process agents"""
        agents = []

        try:
            from app.agents.processes import (
                product_selection_process,
                market_entry_process
            )

            for process in [product_selection_process, market_entry_process]:
                agents.append(self._extract_agent_metadata(process, 3))

        except Exception as e:
            logger.error(f"Error discovering Level 3 agents: {e}")

        return agents

    async def _discover_level_2_agents(self) -> List[Dict[str, Any]]:
        """Discover Level 2 process group agents"""
        agents = []

        try:
            from app.agents.process_groups import market_and_sell_process_group

            agents.append(self._extract_agent_metadata(market_and_sell_process_group, 2))

        except Exception as e:
            logger.error(f"Error discovering Level 2 agents: {e}")

        return agents

    async def _discover_level_1_agents(self) -> List[Dict[str, Any]]:
        """Discover Level 1 domain enterprise agents"""
        agents = []

        try:
            from app.agents.level_1_domain import market_and_sell_enterprise

            agents.append(self._extract_agent_metadata(market_and_sell_enterprise, 1))

        except Exception as e:
            logger.error(f"Error discovering Level 1 agents: {e}")

        return agents

    def _extract_agent_metadata(self, agent_obj: Any, level: int) -> Dict[str, Any]:
        """Extract metadata from an agent object"""
        metadata = {
            "level": level,
            "id": "unknown",
            "name": "Unknown Agent",
            "apqc_domain": "Unknown",
            "capabilities": [],
            "status": "unknown",
            "version": "1.0.0"
        }

        try:
            if hasattr(agent_obj, 'identifier'):
                identifier = agent_obj.identifier
                metadata["id"] = identifier.id
                metadata["name"] = identifier.name
                metadata["apqc_domain"] = identifier.apqc_domain
                metadata["capabilities"] = identifier.capabilities
                metadata["status"] = identifier.status
                metadata["version"] = identifier.version
                if hasattr(identifier, 'team'):
                    metadata["team"] = identifier.team.value if hasattr(identifier.team, 'value') else str(identifier.team)

        except Exception as e:
            logger.warning(f"Error extracting metadata: {e}")

        return metadata

    def _build_registry_data(self, discovered_agents: Dict[str, List]) -> Dict[str, Any]:
        """Build comprehensive registry data structure"""
        registry = {
            "last_updated": datetime.utcnow().isoformat(),
            "total_agents": sum(len(agents) for agents in discovered_agents.values()),
            "levels": {},
            "by_capability": {},
            "by_apqc_domain": {},
            "by_team": {}
        }

        # Organize by level
        for level_key, agents in discovered_agents.items():
            level = int(level_key.split("_")[1])
            registry["levels"][level] = {
                "count": len(agents),
                "agents": agents
            }

            # Index by capability
            for agent in agents:
                for capability in agent.get("capabilities", []):
                    if capability not in registry["by_capability"]:
                        registry["by_capability"][capability] = []
                    registry["by_capability"][capability].append({
                        "id": agent["id"],
                        "name": agent["name"],
                        "level": agent["level"]
                    })

            # Index by APQC domain
            for agent in agents:
                domain = agent.get("apqc_domain", "Unknown")
                if domain not in registry["by_apqc_domain"]:
                    registry["by_apqc_domain"][domain] = []
                registry["by_apqc_domain"][domain].append({
                    "id": agent["id"],
                    "name": agent["name"],
                    "level": agent["level"]
                })

            # Index by team
            for agent in agents:
                team = agent.get("team", "Unknown")
                if team not in registry["by_team"]:
                    registry["by_team"][team] = []
                registry["by_team"][team].append({
                    "id": agent["id"],
                    "name": agent["name"],
                    "level": agent["level"]
                })

        return registry

    async def _update_registry_database(self, registry_data: Dict[str, Any]):
        """Update the agent registry database file"""
        try:
            # Ensure registry directory exists
            self.registry_path.parent.mkdir(parents=True, exist_ok=True)

            # Write registry data
            with open(self.registry_path, 'w') as f:
                json.dump(registry_data, f, indent=2)

            logger.info(f"✓ Registry database updated: {self.registry_path}")

        except Exception as e:
            logger.error(f"Failed to update registry database: {e}")
            raise

    async def _synchronize_dashboard(self, registry_data: Dict[str, Any]):
        """Synchronize agent library dashboard with registry"""
        try:
            # Generate dashboard data
            dashboard_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "summary": {
                    "total_agents": registry_data["total_agents"],
                    "levels_implemented": len(registry_data["levels"]),
                    "total_capabilities": len(registry_data["by_capability"]),
                    "apqc_domains_covered": len(registry_data["by_apqc_domain"])
                },
                "levels": registry_data["levels"],
                "capabilities": registry_data["by_capability"],
                "apqc_coverage": registry_data["by_apqc_domain"]
            }

            # Write dashboard data
            dashboard_path = self.base_path / "registry" / "dashboard_data.json"
            with open(dashboard_path, 'w') as f:
                json.dump(dashboard_data, f, indent=2)

            logger.info(f"✓ Dashboard synchronized: {dashboard_path}")

        except Exception as e:
            logger.error(f"Failed to synchronize dashboard: {e}")
            raise

    def _generate_coverage_report(self, registry_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate APQC framework coverage report"""
        return {
            "total_agents": registry_data["total_agents"],
            "levels_implemented": len(registry_data["levels"]),
            "level_breakdown": {
                level: data["count"]
                for level, data in registry_data["levels"].items()
            },
            "apqc_domains_covered": len(registry_data["by_apqc_domain"]),
            "top_capabilities": sorted(
                registry_data["by_capability"].items(),
                key=lambda x: len(x[1]),
                reverse=True
            )[:10]
        }


# Global meta-agent instance
agent_registry_updater = AgentRegistryUpdater()
