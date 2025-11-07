"""
OptimizeAssetUtilizationAssetManagementAgent - APQC 9.0
9.2.2 Optimize Asset Utilization
APQC ID: apqc_9_0_o6p7q8r9
"""

import os
import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from datetime import datetime

from superstandard.agents.base.base_agent import BaseAgent
from src.superstandard.agents.base.protocols import ProtocolMixin


@dataclass
class OptimizeAssetUtilizationAssetManagementAgentConfig:
    apqc_agent_id: str = "apqc_9_0_o6p7q8r9"
    apqc_process_id: str = "9.2.2"
    agent_name: str = "optimize_asset_utilization_asset_management_agent"
    agent_type: str = "operational"
    version: str = "1.0.0"


class OptimizeAssetUtilizationAssetManagementAgent(BaseAgent, ProtocolMixin):
    """
    Skills: oee_calculation: 0.92, capacity_planning: 0.88, utilization_analytics: 0.86
    """

    VERSION = "1.0.0"
    APQC_PROCESS_ID = "9.2.2"

    def __init__(self, config: OptimizeAssetUtilizationAssetManagementAgentConfig):
        super().__init__(
            agent_id=config.apqc_agent_id, agent_type=config.agent_type, version=config.version
        )
        self.config = config
        self.skills = {
            "oee_calculation": 0.92,
            "capacity_planning": 0.88,
            "utilization_analytics": 0.86,
        }

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize asset utilization using OEE, capacity analysis, and bottleneck identification
        """
        asset_data = input_data.get("asset_data", [])
        downtime_data = input_data.get("downtime", {})
        production_metrics = input_data.get("production_metrics", {})
        quality_metrics = input_data.get("quality_metrics", {})

        # OEE Calculation
        oee_analysis = self._calculate_oee(
            asset_data, downtime_data, production_metrics, quality_metrics
        )

        # Capacity Utilization
        capacity_analysis = self._analyze_capacity_utilization(asset_data, production_metrics)

        # Bottleneck Identification
        bottlenecks = self._identify_bottlenecks(capacity_analysis, oee_analysis)

        # Optimization Opportunities
        opportunities = self._identify_optimization_opportunities(oee_analysis, bottlenecks)

        return {
            "status": "completed",
            "apqc_process_id": self.APQC_PROCESS_ID,
            "timestamp": datetime.now().isoformat(),
            "output": {
                "utilization_report": {
                    "oee": oee_analysis,
                    "capacity_utilization": capacity_analysis,
                    "bottlenecks": bottlenecks,
                    "optimization_opportunities": opportunities,
                },
                "metrics": {
                    "overall_oee": oee_analysis["overall_oee"],
                    "average_utilization": capacity_analysis["average_utilization"],
                    "bottleneck_count": len(bottlenecks["critical_bottlenecks"]),
                    "improvement_potential": opportunities["total_potential_gain"],
                },
            },
        }

    def _calculate_oee(
        self, assets: List[Dict], downtime: Dict, production: Dict, quality: Dict
    ) -> Dict[str, Any]:
        """
        Calculate Overall Equipment Effectiveness (OEE)
        OEE = Availability × Performance × Quality
        """
        oee_by_asset = []
        total_oee_sum = 0

        for asset in assets:
            asset_id = asset.get("asset_id")
            asset_name = asset.get("name", "Unknown")

            # Get metrics
            planned_production_time = asset.get("planned_production_time", 480)  # minutes
            downtime_minutes = downtime.get(asset_id, 0)
            ideal_cycle_time = asset.get("ideal_cycle_time", 1)  # minutes per unit
            actual_units = production.get(asset_id, {}).get("actual_units", 0)
            good_units = quality.get(asset_id, {}).get("good_units", actual_units)

            # Availability = (Planned Production Time - Downtime) / Planned Production Time
            operating_time = planned_production_time - downtime_minutes
            availability = (
                (operating_time / planned_production_time) if planned_production_time > 0 else 0
            )

            # Performance = (Ideal Cycle Time × Total Units) / Operating Time
            ideal_production_time = ideal_cycle_time * actual_units
            performance = (ideal_production_time / operating_time) if operating_time > 0 else 0
            performance = min(performance, 1.0)  # Cap at 100%

            # Quality = Good Units / Total Units
            quality_rate = (good_units / actual_units) if actual_units > 0 else 0

            # OEE = Availability × Performance × Quality
            oee = availability * performance * quality_rate

            oee_by_asset.append(
                {
                    "asset_id": asset_id,
                    "asset_name": asset_name,
                    "availability": round(availability * 100, 1),
                    "performance": round(performance * 100, 1),
                    "quality": round(quality_rate * 100, 1),
                    "oee": round(oee * 100, 1),
                    "oee_category": self._categorize_oee(oee * 100),
                    "downtime_minutes": downtime_minutes,
                    "units_produced": actual_units,
                    "good_units": good_units,
                }
            )

            total_oee_sum += oee

        overall_oee = (total_oee_sum / len(assets) * 100) if assets else 0

        # Identify best and worst performers
        sorted_assets = sorted(oee_by_asset, key=lambda x: x["oee"], reverse=True)

        return {
            "oee_by_asset": oee_by_asset,
            "overall_oee": round(overall_oee, 1),
            "best_performers": sorted_assets[:3],
            "worst_performers": sorted_assets[-3:],
            "world_class_threshold": 85,  # World-class OEE is typically 85%+
            "assets_meeting_world_class": len([a for a in oee_by_asset if a["oee"] >= 85]),
        }

    def _categorize_oee(self, oee: float) -> str:
        """Categorize OEE performance"""
        if oee >= 85:
            return "world_class"
        elif oee >= 65:
            return "good"
        elif oee >= 50:
            return "acceptable"
        else:
            return "needs_improvement"

    def _analyze_capacity_utilization(self, assets: List[Dict], production: Dict) -> Dict[str, Any]:
        """
        Analyze capacity utilization
        """
        utilization_by_asset = []

        for asset in assets:
            asset_id = asset.get("asset_id")
            asset_name = asset.get("name", "Unknown")

            max_capacity = asset.get("max_capacity_units_per_day", 100)
            actual_production = production.get(asset_id, {}).get("actual_units", 0)

            utilization_pct = (actual_production / max_capacity * 100) if max_capacity > 0 else 0

            # Determine status
            if utilization_pct >= 90:
                status = "near_capacity"
            elif utilization_pct >= 70:
                status = "optimal"
            elif utilization_pct >= 50:
                status = "underutilized"
            else:
                status = "significantly_underutilized"

            utilization_by_asset.append(
                {
                    "asset_id": asset_id,
                    "asset_name": asset_name,
                    "max_capacity": max_capacity,
                    "actual_production": actual_production,
                    "utilization_pct": round(utilization_pct, 1),
                    "status": status,
                    "spare_capacity": max_capacity - actual_production,
                }
            )

        # Calculate averages
        avg_utilization = (
            np.mean([u["utilization_pct"] for u in utilization_by_asset])
            if utilization_by_asset
            else 0
        )
        total_spare_capacity = sum(u["spare_capacity"] for u in utilization_by_asset)

        return {
            "utilization_by_asset": utilization_by_asset,
            "average_utilization": round(avg_utilization, 1),
            "total_spare_capacity": total_spare_capacity,
            "overutilized_assets": [u for u in utilization_by_asset if u["utilization_pct"] >= 90],
            "underutilized_assets": [u for u in utilization_by_asset if u["utilization_pct"] < 50],
        }

    def _identify_bottlenecks(self, capacity: Dict, oee: Dict) -> Dict[str, Any]:
        """
        Identify production bottlenecks
        """
        critical_bottlenecks = []
        moderate_bottlenecks = []

        # Check for high utilization + low OEE (most critical)
        for asset in capacity["utilization_by_asset"]:
            asset_id = asset["asset_id"]

            # Find corresponding OEE
            oee_data = next((o for o in oee["oee_by_asset"] if o["asset_id"] == asset_id), None)

            if not oee_data:
                continue

            # Critical: High utilization (>80%) + Low OEE (<65%)
            if asset["utilization_pct"] > 80 and oee_data["oee"] < 65:
                critical_bottlenecks.append(
                    {
                        "asset_id": asset_id,
                        "asset_name": asset["asset_name"],
                        "utilization": asset["utilization_pct"],
                        "oee": oee_data["oee"],
                        "issue": "High demand but poor efficiency",
                        "impact": "high",
                    }
                )

            # Moderate: Either high utilization OR low OEE
            elif asset["utilization_pct"] > 85 or oee_data["oee"] < 50:
                moderate_bottlenecks.append(
                    {
                        "asset_id": asset_id,
                        "asset_name": asset["asset_name"],
                        "utilization": asset["utilization_pct"],
                        "oee": oee_data["oee"],
                        "issue": (
                            "Capacity constraint"
                            if asset["utilization_pct"] > 85
                            else "Efficiency issue"
                        ),
                        "impact": "medium",
                    }
                )

        return {
            "critical_bottlenecks": critical_bottlenecks,
            "moderate_bottlenecks": moderate_bottlenecks,
            "total_bottlenecks": len(critical_bottlenecks) + len(moderate_bottlenecks),
            "action_required": len(critical_bottlenecks) > 0,
        }

    def _identify_optimization_opportunities(self, oee: Dict, bottlenecks: Dict) -> Dict[str, Any]:
        """
        Identify optimization opportunities
        """
        opportunities = []

        # Opportunity 1: Improve OEE on worst performers
        for asset in oee["worst_performers"]:
            if asset["oee"] < 65:
                # Calculate potential gain if OEE improved to 75%
                current_output = asset["units_produced"]
                potential_output = current_output * (75 / asset["oee"]) if asset["oee"] > 0 else 0
                potential_gain = potential_output - current_output

                opportunities.append(
                    {
                        "asset": asset["asset_name"],
                        "type": "oee_improvement",
                        "current_oee": asset["oee"],
                        "target_oee": 75,
                        "potential_gain_units": round(potential_gain, 0),
                        "priority": "high",
                        "focus_areas": self._identify_oee_focus_areas(asset),
                    }
                )

        # Opportunity 2: Address bottlenecks
        for bottleneck in bottlenecks["critical_bottlenecks"]:
            opportunities.append(
                {
                    "asset": bottleneck["asset_name"],
                    "type": "bottleneck_resolution",
                    "issue": bottleneck["issue"],
                    "potential_gain_units": "TBD - requires detailed analysis",
                    "priority": "critical",
                    "recommendations": [
                        "Add capacity",
                        "Improve process efficiency",
                        "Reduce downtime",
                        "Balance workload",
                    ],
                }
            )

        # Calculate total potential
        total_potential = sum(
            opp.get("potential_gain_units", 0)
            for opp in opportunities
            if isinstance(opp.get("potential_gain_units"), (int, float))
        )

        return {
            "opportunities": opportunities,
            "total_potential_gain": round(total_potential, 0),
            "high_priority_count": len(
                [o for o in opportunities if o["priority"] in ["critical", "high"]]
            ),
        }

    def _identify_oee_focus_areas(self, asset: Dict) -> List[str]:
        """Identify which OEE component needs most improvement"""
        focus_areas = []

        if asset["availability"] < 80:
            focus_areas.append("Reduce downtime")
        if asset["performance"] < 80:
            focus_areas.append("Improve speed/efficiency")
        if asset["quality"] < 95:
            focus_areas.append("Improve quality/reduce defects")

        return focus_areas if focus_areas else ["General improvement"]

    def log(self, level: str, message: str):
        print(f"[{datetime.now().isoformat()}] [{level}] {message}")


def create_optimize_asset_utilization_asset_management_agent(
    config: Optional[OptimizeAssetUtilizationAssetManagementAgentConfig] = None,
):
    if config is None:
        config = OptimizeAssetUtilizationAssetManagementAgentConfig()
    return OptimizeAssetUtilizationAssetManagementAgent(config)
