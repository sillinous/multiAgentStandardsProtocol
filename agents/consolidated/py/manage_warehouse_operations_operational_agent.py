"""
ManageWarehouseOperationsOperationalAgent - APQC Agent
Process: 4.4.2 | ID: apqc_4_0_w5x6y7z8
Skills: space_optimization (0.91), picking_optimization (0.89), throughput_analysis (0.87)
Compliance: All 8 principles | Protocols: A2A, A2P, ACP, ANP, MCP
"""

import os
import psutil
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from superstandard.agents.base.base_agent import BaseAgent
from src.superstandard.agents.base.protocols import ProtocolMixin


@dataclass
class ManageWarehouseOperationsOperationalAgentConfig:
    apqc_agent_id: str = "apqc_4_0_w5x6y7z8"
    apqc_process_id: str = "4.4.2"
    agent_id: str = "apqc_4_0_w5x6y7z8"
    agent_name: str = "manage_warehouse_operations_operational_agent"
    agent_type: str = "operational"
    version: str = "1.0.0"


class ManageWarehouseOperationsOperationalAgent(BaseAgent, ProtocolMixin):
    VERSION = "1.0.0"
    APQC_PROCESS_ID = "4.4.2"

    def __init__(self, config):
        super().__init__(
            agent_id=config.agent_id, agent_type=config.agent_type, version=config.version
        )
        self.config = config
        self.state = {"status": "initialized", "tasks_processed": 0}

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Execute business logic based on agent type
            result = {}

            # Call appropriate methods based on input
            if "contracts" in input_data:
                result["contract_analysis"] = self._analyze_contract_value(input_data["contracts"])
                result["renewal_recommendations"] = self._optimize_renewals(
                    input_data["contracts"], input_data.get("market_rates", {})
                )

            if "measurements" in input_data and "spec_limits" in input_data:
                result["process_capability"] = self._calculate_process_capability(
                    input_data["measurements"], input_data["spec_limits"]
                )
                result["control_chart"] = self._control_chart_analysis(input_data["measurements"])

            if "warehouse_layout" in input_data:
                result["space_utilization"] = self._calculate_space_utilization(
                    input_data["warehouse_layout"], input_data.get("inventory", [])
                )

            if "demand_forecast" in input_data:
                result["sop_plan"] = self._sales_operations_planning(
                    input_data["demand_forecast"], input_data.get("capacity_data", {})
                )

            if "shipments" in input_data:
                result["route_optimization"] = self._optimize_routes(
                    input_data["shipments"], input_data.get("routes", [])
                )
                result["load_consolidation"] = self._consolidate_loads(input_data["shipments"])

            return {
                "status": "completed",
                "apqc_process_id": self.APQC_PROCESS_ID,
                "agent_id": self.config.agent_id,
                "timestamp": datetime.now().isoformat(),
                "output": result,
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _calculate_space_utilization(self, warehouse_layout, inventory):
        total_capacity = warehouse_layout.get("total_cubic_feet", 0)
        total_aisles = warehouse_layout.get("total_aisles", 1)

        used_space = sum(item.get("cubic_feet", 0) for item in inventory)
        utilization_pct = (used_space / total_capacity * 100) if total_capacity > 0 else 0

        # Optimal utilization is 85% (allows for operations)
        optimal = 85
        efficiency_score = 100 - abs(utilization_pct - optimal)

        return {
            "total_capacity_cuft": total_capacity,
            "used_space_cuft": round(used_space, 2),
            "utilization_pct": round(utilization_pct, 2),
            "efficiency_score": round(efficiency_score, 2),
            "status": (
                "Optimal"
                if 75 <= utilization_pct <= 90
                else "Underutilized" if utilization_pct < 75 else "Overcrowded"
            ),
        }

    def _optimize_pick_paths(self, orders, locations):
        # Simple pick path optimization using nearest neighbor
        total_distance = 0
        total_picks = 0

        for order in orders:
            items = order.get("items", [])
            if not items:
                continue

            # Get locations for items
            item_locations = []
            for item in items:
                loc = next((l for l in locations if l.get("item_id") == item.get("item_id")), None)
                if loc:
                    item_locations.append(loc)

            # Calculate total pick distance (simplified)
            if item_locations:
                distances = [
                    abs(item_locations[i].get("aisle", 0) - item_locations[i - 1].get("aisle", 0))
                    for i in range(1, len(item_locations))
                ]
                total_distance += sum(distances)
                total_picks += len(items)

        avg_distance_per_pick = total_distance / total_picks if total_picks > 0 else 0

        return {
            "total_picks": total_picks,
            "total_distance": total_distance,
            "avg_distance_per_pick": round(avg_distance_per_pick, 2),
            "efficiency_rating": (
                "Excellent"
                if avg_distance_per_pick < 5
                else "Good" if avg_distance_per_pick < 10 else "Needs Improvement"
            ),
        }

    def _abc_slotting_analysis(self, inventory):
        # ABC analysis for optimal slotting
        sorted_items = sorted(
            inventory,
            key=lambda x: x.get("pick_frequency", 0) * x.get("unit_value", 0),
            reverse=True,
        )
        total_value = sum(
            item.get("pick_frequency", 0) * item.get("unit_value", 0) for item in sorted_items
        )

        cumulative = 0
        abc_classification = {}

        for item in sorted_items:
            item_value = item.get("pick_frequency", 0) * item.get("unit_value", 0)
            cumulative += item_value
            pct = (cumulative / total_value * 100) if total_value > 0 else 0

            if pct <= 80:
                classification = "A"  # High value, frequent picks - front of warehouse
            elif pct <= 95:
                classification = "B"  # Medium value - middle zones
            else:
                classification = "C"  # Low value - back areas

            abc_classification[item.get("item_id")] = {
                "classification": classification,
                "recommended_zone": (
                    "Front"
                    if classification == "A"
                    else "Middle" if classification == "B" else "Back"
                ),
            }

        return abc_classification

    async def health_check(self) -> Dict[str, Any]:
        return {
            "agent_id": self.config.agent_id,
            "status": self.state["status"],
            "version": self.VERSION,
        }

    def log(self, level: str, message: str):
        print(
            f"[{datetime.now().isoformat()}] [{level.upper()}] [{self.config.agent_name}] {message}"
        )


def create_manage_warehouse_operations_operational_agent(config=None):
    return ManageWarehouseOperationsOperationalAgent(
        config or ManageWarehouseOperationsOperationalAgentConfig()
    )
