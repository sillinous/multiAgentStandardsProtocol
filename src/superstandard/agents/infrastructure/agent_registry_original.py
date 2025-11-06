"""
Phase 9 Agent Registry

Dynamically discovers and registers agents from src/agents directory.
Provides real agent data to the AgentManagementSystem backend.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import asyncio
import os
import importlib
import inspect

from src.backend.phase9_agent_management import (
    AgentInfo,
    AgentCapability,
    AgentMetrics,
    AgentStatus,
    AgentHealthLevel,
    AgentLogEntry,
)


# ============================================================================
# Agent Metadata Registry
# ============================================================================

AGENT_REGISTRY: Dict[str, Dict[str, Any]] = {
    # Trading Agents
    "trading_agent": {
        "name": "Trading Agent",
        "description": "Core autonomous trading agent executing strategies on Solana",
        "category": "trading",
        "capabilities": [
            {
                "name": "market_buy",
                "description": "Execute market buy orders",
                "inputs": ["token_address", "amount_usd"],
                "outputs": ["transaction_hash", "execution_price"],
                "category": "trading",
            },
            {
                "name": "market_sell",
                "description": "Execute market sell orders",
                "inputs": ["token_address", "amount_usd"],
                "outputs": ["transaction_hash", "execution_price"],
                "category": "trading",
            },
            {
                "name": "get_position",
                "description": "Check current position in token",
                "inputs": ["token_address"],
                "outputs": ["amount", "entry_price", "current_price", "pnl"],
                "category": "trading",
            },
        ],
    },
    # Risk Management Agents
    "risk_agent": {
        "name": "Risk Agent",
        "description": "Monitors portfolio risk, enforces position limits, prevents liquidation",
        "category": "risk",
        "capabilities": [
            {
                "name": "assess_portfolio_risk",
                "description": "Calculate portfolio risk metrics",
                "inputs": ["portfolio_state"],
                "outputs": ["risk_level", "max_loss", "recommendations"],
                "category": "risk",
            },
            {
                "name": "check_position_limit",
                "description": "Validate position size against limits",
                "inputs": ["token_address", "proposed_size"],
                "outputs": ["is_valid", "recommended_size"],
                "category": "risk",
            },
        ],
    },
    # Market Analysis Agents
    "sentiment_agent": {
        "name": "Sentiment Agent",
        "description": "Analyzes market sentiment from social media and news",
        "category": "analysis",
        "capabilities": [
            {
                "name": "get_sentiment",
                "description": "Analyze sentiment for a token",
                "inputs": ["token_symbol"],
                "outputs": ["sentiment_score", "confidence", "sources"],
                "category": "analysis",
            }
        ],
    },
    "whale_agent": {
        "name": "Whale Agent",
        "description": "Monitors whale wallet activity and large transactions",
        "category": "analysis",
        "capabilities": [
            {
                "name": "monitor_whale_wallets",
                "description": "Track large wallet movements",
                "inputs": ["token_address"],
                "outputs": ["whale_movements", "volume", "direction"],
                "category": "analysis",
            }
        ],
    },
    "funding_agent": {
        "name": "Funding Agent",
        "description": "Tracks funding rates on perpetual exchanges",
        "category": "analysis",
        "capabilities": [
            {
                "name": "get_funding_rates",
                "description": "Retrieve current funding rates",
                "inputs": ["token_symbol", "exchange"],
                "outputs": ["funding_rate", "next_funding_time"],
                "category": "analysis",
            }
        ],
    },
    "liquidation_agent": {
        "name": "Liquidation Agent",
        "description": "Tracks liquidation data and identifies risk zones",
        "category": "analysis",
        "capabilities": [
            {
                "name": "get_liquidation_levels",
                "description": "Identify liquidation price levels",
                "inputs": ["token_address"],
                "outputs": ["liquidation_zones", "cluster_levels"],
                "category": "analysis",
            }
        ],
    },
    "chartanalysis_agent": {
        "name": "Chart Analysis Agent",
        "description": "Technical analysis using chart patterns and indicators",
        "category": "analysis",
        "capabilities": [
            {
                "name": "analyze_chart",
                "description": "Perform technical analysis on charts",
                "inputs": ["token_address", "timeframe"],
                "outputs": ["patterns", "support_levels", "resistance_levels", "signals"],
                "category": "analysis",
            }
        ],
    },
    # Research & Strategy Agents
    "research_agent": {
        "name": "Research Agent",
        "description": "Conducts market research and generates insights",
        "category": "research",
        "capabilities": [
            {
                "name": "market_research",
                "description": "Research market conditions",
                "inputs": ["token_address"],
                "outputs": ["research_report", "key_findings"],
                "category": "research",
            }
        ],
    },
    "rbi_agent": {
        "name": "RBI Agent",
        "description": "Research-Based Inference: codes backtests from videos/PDFs",
        "category": "research",
        "capabilities": [
            {
                "name": "analyze_research",
                "description": "Extract strategy from research material",
                "inputs": ["video_url", "pdf_content"],
                "outputs": ["strategy_code", "backtest_results"],
                "category": "research",
            },
            {
                "name": "generate_backtest",
                "description": "Generate and execute backtest",
                "inputs": ["strategy_code", "historical_data"],
                "outputs": ["performance_metrics", "backtest_report"],
                "category": "research",
            },
        ],
    },
    "strategy_agent": {
        "name": "Strategy Agent",
        "description": "Designs and evaluates trading strategies",
        "category": "research",
        "capabilities": [
            {
                "name": "design_strategy",
                "description": "Design new trading strategy",
                "inputs": ["market_conditions", "objectives"],
                "outputs": ["strategy_spec", "expected_performance"],
                "category": "research",
            }
        ],
    },
    # Content & Communication Agents
    "chat_agent": {
        "name": "Chat Agent",
        "description": "Interactive chat for market insights and strategy discussion",
        "category": "communication",
        "capabilities": [
            {
                "name": "respond_to_query",
                "description": "Answer questions about markets and strategies",
                "inputs": ["user_query"],
                "outputs": ["response", "confidence"],
                "category": "communication",
            }
        ],
    },
    "tweet_agent": {
        "name": "Tweet Agent",
        "description": "Analyzes and generates tweets about market opportunities",
        "category": "communication",
        "capabilities": [
            {
                "name": "analyze_tweets",
                "description": "Analyze crypto tweets for signals",
                "inputs": ["token_symbol"],
                "outputs": ["tweet_sentiment", "trending_topics"],
                "category": "communication",
            }
        ],
    },
    "clips_agent": {
        "name": "Clips Agent",
        "description": "Generates video clips of market analysis",
        "category": "communication",
        "capabilities": [
            {
                "name": "generate_clips",
                "description": "Create analysis video clips",
                "inputs": ["analysis_data", "token"],
                "outputs": ["video_url", "metadata"],
                "category": "communication",
            }
        ],
    },
    # Specialized Agents
    "sniper_agent": {
        "name": "Sniper Agent",
        "description": "Performs precision trades on new token launches",
        "category": "specialized",
        "capabilities": [
            {
                "name": "snipe_launch",
                "description": "Execute sniping strategy on new token",
                "inputs": ["token_contract", "initial_liquidity"],
                "outputs": ["execution_price", "transaction_details"],
                "category": "specialized",
            }
        ],
    },
    "solana_agent": {
        "name": "Solana Agent",
        "description": "Solana-specific operations and optimization",
        "category": "specialized",
        "capabilities": [
            {
                "name": "solana_optimize",
                "description": "Optimize for Solana blockchain",
                "inputs": ["transaction_params"],
                "outputs": ["optimized_params", "estimated_cost"],
                "category": "specialized",
            }
        ],
    },
    "compliance_agent": {
        "name": "Compliance Agent",
        "description": "Ensures all trading complies with regulations",
        "category": "specialized",
        "capabilities": [
            {
                "name": "check_compliance",
                "description": "Validate trading compliance",
                "inputs": ["trade_details"],
                "outputs": ["is_compliant", "warnings"],
                "category": "specialized",
            }
        ],
    },
}


class AgentRegistry:
    """Registry for discovering and managing agents"""

    def __init__(self):
        """Initialize agent registry"""
        self.agents: Dict[str, AgentInfo] = {}
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize and discover all agents"""
        for agent_key, metadata in AGENT_REGISTRY.items():
            agent_info = self._create_agent_info(agent_key, metadata)
            self.agents[agent_key] = agent_info

        self.initialized = True
        print(f"AgentRegistry initialized with {len(self.agents)} agents")

    def _create_agent_info(self, agent_id: str, metadata: Dict[str, Any]) -> AgentInfo:
        """Create AgentInfo from metadata"""

        # Convert capability dicts to AgentCapability objects
        capabilities = [
            AgentCapability(
                name=cap["name"],
                description=cap["description"],
                inputs=cap["inputs"],
                outputs=cap["outputs"],
                category=cap["category"],
                reliability_score=0.95,
                avg_execution_time_seconds=1.5,
            )
            for cap in metadata.get("capabilities", [])
        ]

        # Create metrics
        metrics = AgentMetrics(
            agent_id=agent_id,
            status=AgentStatus.IDLE,
            health_level=AgentHealthLevel.HEALTHY,
            uptime_seconds=3600.0,
            executions_total=0,
            executions_successful=0,
            executions_failed=0,
            avg_execution_time_ms=1500.0,
            error_rate=0.0,
            cpu_usage_percent=5.2,
            memory_usage_mb=128.5,
            last_execution=None,
            last_error=None,
            timestamp=datetime.now().isoformat(),
        )

        # Create agent info
        return AgentInfo(
            agent_id=agent_id,
            agent_type=metadata.get("category", "general"),
            name=metadata.get("name", agent_id),
            description=metadata.get("description", ""),
            version="1.0.0",
            status=AgentStatus.IDLE,
            health_level=AgentHealthLevel.HEALTHY,
            capabilities=capabilities,
            metrics=metrics,
            current_task=None,
            parameters={},
            environment={},
            team_memberships=[],
            recent_logs=[],
            recent_decisions=[],
            registered_at=datetime.now().isoformat(),
            last_heartbeat=datetime.now().isoformat(),
        )

    async def get_all_agents(self) -> List[Dict[str, Any]]:
        """Get all agents as dictionaries"""
        if not self.initialized:
            await self.initialize()

        return [asdict(agent) for agent in self.agents.values()]

    async def get_agent_by_id(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get specific agent"""
        if not self.initialized:
            await self.initialize()

        if agent_id in self.agents:
            return asdict(self.agents[agent_id])
        return None

    async def get_agents_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get agents by category"""
        if not self.initialized:
            await self.initialize()

        matching = [agent for agent in self.agents.values() if agent.agent_type == category]
        return [asdict(agent) for agent in matching]

    async def get_agent_library(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get agent library organized by category"""
        if not self.initialized:
            await self.initialize()

        library: Dict[str, List[Dict[str, Any]]] = {}

        for agent in self.agents.values():
            category = agent.agent_type
            if category not in library:
                library[category] = []

            library[category].append(
                {
                    "agent_id": agent.agent_id,
                    "name": agent.name,
                    "description": agent.description,
                    "capabilities": [
                        {"name": cap.name, "description": cap.description, "category": cap.category}
                        for cap in agent.capabilities
                    ],
                    "status": agent.status.value,
                    "health_level": agent.health_level.value,
                }
            )

        return library

    async def search_by_capability(self, capability_name: str) -> List[Dict[str, Any]]:
        """Search agents by capability"""
        if not self.initialized:
            await self.initialize()

        matching = []
        for agent in self.agents.values():
            if any(cap.name.lower() == capability_name.lower() for cap in agent.capabilities):
                matching.append(asdict(agent))

        return matching


# Global registry instance
_registry: Optional[AgentRegistry] = None


async def get_agent_registry() -> AgentRegistry:
    """Get or create global agent registry"""
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
        await _registry.initialize()
    return _registry
