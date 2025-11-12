"""
APQC PCF Agent: Prioritize and Select Target Markets (1.1.3.4)

Makes final market selection decisions by combining attractiveness and fit analysis.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List
import random

from superstandard.agents.pcf.base import (
    ActivityAgentBase,
    PCFMetadata,
    PCFAgentConfig,
)


class SelectTargetMarketsAgent(ActivityAgentBase):
    """Agent for selecting target markets."""

    def __init__(self, config: PCFAgentConfig = None):
        if config is None:
            config = self._create_default_config()
        super().__init__(config)

    @staticmethod
    def _create_default_config() -> PCFAgentConfig:
        metadata = PCFMetadata(
            pcf_element_id="10035",
            hierarchy_id="1.1.3.4",
            level=4,
            level_name="Activity",
            category_id="1.0",
            category_name="Develop Vision and Strategy",
            process_group_id="1.1",
            process_group_name="Define the business concept and long-term vision",
            process_id="1.1.3",
            process_name="Select relevant markets",
            activity_id="1.1.3.4",
            activity_name="Prioritize and select target markets",
            parent_element_id="10035",
            kpis=[
                {"name": "markets_selected", "type": "count", "unit": "number"},
                {"name": "total_market_value", "type": "currency", "unit": "USD"},
                {"name": "portfolio_balance_score", "type": "score", "unit": "0-10"}
            ]
        )

        return PCFAgentConfig(
            agent_id="select_target_markets_agent_001",
            pcf_metadata=metadata,
            track_kpis=True,
            execution_timeout=180
        )

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Select target markets."""
        execution_start = datetime.utcnow()

        # Get segments with attractiveness and fit scores
        segments = input_data.get("segments", self._get_mock_segments())
        max_markets = input_data.get("max_target_markets", 3)
        min_combined_score = input_data.get("min_combined_score", 7.0)

        # Combine attractiveness and fit scores
        combined_scores = await self._calculate_combined_scores(segments)

        # Apply selection criteria
        selected_markets = await self._select_markets(
            combined_scores, max_markets, min_combined_score
        )

        # Create market entry roadmap
        roadmap = await self._create_entry_roadmap(selected_markets)

        # Portfolio optimization
        portfolio_analysis = await self._analyze_portfolio_balance(selected_markets)

        execution_end = datetime.utcnow()
        execution_duration = (execution_end - execution_start).total_seconds()

        total_value = sum(m.get("market_size_usd", random.randint(200000000, 2000000000)) for m in selected_markets)

        result = {
            "selection_overview": {
                "execution_date": execution_start.isoformat(),
                "markets_evaluated": len(segments),
                "markets_selected": len(selected_markets),
                "selection_criteria": {
                    "max_targets": max_markets,
                    "min_combined_score": min_combined_score
                }
            },
            "selected_markets": selected_markets,
            "rejected_markets": [
                {
                    "segment_id": s["segment_id"],
                    "segment_name": s["segment_name"],
                    "rejection_reason": s.get("rejection_reason", "Below threshold")
                }
                for s in combined_scores if s not in selected_markets
            ][:5],
            "entry_roadmap": roadmap,
            "portfolio_analysis": portfolio_analysis,
            "strategic_recommendations": [
                f"Prioritize {selected_markets[0]['segment_name']} for immediate entry",
                f"Build capabilities for {selected_markets[1]['segment_name'] if len(selected_markets) > 1 else 'additional markets'}",
                "Establish partnerships to accelerate market entry",
                "Monitor performance and adjust strategy quarterly"
            ],
            "kpis": {
                "markets_selected": len(selected_markets),
                "total_market_value": total_value,
                "portfolio_balance_score": round(portfolio_analysis["balance_score"], 1),
                "execution_time_seconds": round(execution_duration, 2)
            }
        }

        return result

    async def _calculate_combined_scores(
        self,
        segments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Calculate combined attractiveness + fit scores."""
        await asyncio.sleep(0.05)

        combined = []
        for segment in segments:
            attractiveness = segment.get("attractiveness_score", round(random.uniform(5.0, 9.5), 1))
            fit = segment.get("fit_score", round(random.uniform(5.0, 9.0), 1))

            combined_score = (attractiveness * 0.55 + fit * 0.45)

            combined.append({
                "segment_id": segment.get("segment_id", "SEG_001"),
                "segment_name": segment.get("name", "Segment"),
                "attractiveness_score": attractiveness,
                "fit_score": fit,
                "combined_score": round(combined_score, 1),
                "market_size_usd": segment.get("market_size_usd", random.randint(200000000, 2000000000)),
                "priority_tier": "High" if combined_score >= 8.0 else "Medium" if combined_score >= 6.5 else "Low"
            })

        combined.sort(key=lambda x: x["combined_score"], reverse=True)
        return combined

    async def _select_markets(
        self,
        scored_segments: List[Dict[str, Any]],
        max_markets: int,
        min_score: float
    ) -> List[Dict[str, Any]]:
        """Apply selection criteria."""
        await asyncio.sleep(0.05)

        selected = []
        for segment in scored_segments:
            if len(selected) >= max_markets:
                segment["rejection_reason"] = "Portfolio limit reached"
                break

            if segment["combined_score"] < min_score:
                segment["rejection_reason"] = f"Score {segment['combined_score']} below threshold {min_score}"
                continue

            selected.append({
                **segment,
                "selection_rationale": f"Strong combined score ({segment['combined_score']}/10)",
                "entry_priority": len(selected) + 1,
                "recommended_strategy": random.choice([
                    "Direct market entry",
                    "Partnership-based entry",
                    "Phased rollout",
                    "Acquisition-led entry"
                ])
            })

        return selected

    async def _create_entry_roadmap(
        self,
        selected_markets: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create market entry roadmap."""
        await asyncio.sleep(0.05)

        roadmap = {
            "phase_1_immediate": [],
            "phase_2_near_term": [],
            "phase_3_future": []
        }

        for i, market in enumerate(selected_markets):
            entry = {
                "market": market["segment_name"],
                "timeline": f"Q{i+1}-Q{i+2}" if i < 2 else f"Q{i+1}-Q{i+3}",
                "investment_required": random.randint(500000, 5000000),
                "key_activities": random.sample([
                    "Market research deep dive",
                    "Partnership development",
                    "Pilot program launch",
                    "Sales team hiring",
                    "Marketing campaign",
                    "Product localization"
                ], 3)
            }

            if i == 0:
                roadmap["phase_1_immediate"].append(entry)
            elif i < 3:
                roadmap["phase_2_near_term"].append(entry)
            else:
                roadmap["phase_3_future"].append(entry)

        return roadmap

    async def _analyze_portfolio_balance(
        self,
        selected_markets: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze portfolio balance."""
        await asyncio.sleep(0.05)

        # Assess balance across dimensions
        priority_distribution = {"High": 0, "Medium": 0, "Low": 0}
        for market in selected_markets:
            priority_distribution[market["priority_tier"]] += 1

        # Calculate balance score
        ideal_high = max(1, len(selected_markets) // 2)
        actual_high = priority_distribution["High"]
        balance_score = 10 - abs(ideal_high - actual_high) * 2

        return {
            "balance_score": max(0, min(10, balance_score)),
            "priority_distribution": priority_distribution,
            "diversity_assessment": "Balanced" if balance_score >= 7 else "Concentrated",
            "risk_profile": "Moderate" if len(selected_markets) >= 2 else "High concentration",
            "recommendations": [
                "Portfolio shows good balance across priority tiers" if balance_score >= 7 else "Consider adding more medium-priority markets for balance",
                "Diversification reduces execution risk"
            ]
        }

    def _get_mock_segments(self) -> List[Dict[str, Any]]:
        return [
            {
                "segment_id": f"SEG_{i:03d}",
                "name": f"Market Segment {i}",
                "attractiveness_score": round(random.uniform(6.0, 9.5), 1),
                "fit_score": round(random.uniform(5.5, 9.0), 1)
            }
            for i in range(1, 8)
        ]


__all__ = ['SelectTargetMarketsAgent']
