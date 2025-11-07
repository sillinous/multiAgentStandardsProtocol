"""
ManageProductionQualityOperationalAgent - APQC Agent
Process: 4.3.3 | ID: apqc_4_0_v4w5x6y7
Skills: spc_analysis (0.92), six_sigma (0.89), defect_tracking (0.90), process_capability (0.88)
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
class ManageProductionQualityOperationalAgentConfig:
    apqc_agent_id: str = "apqc_4_0_v4w5x6y7"
    apqc_process_id: str = "4.3.3"
    agent_id: str = "apqc_4_0_v4w5x6y7"
    agent_name: str = "manage_production_quality_operational_agent"
    agent_type: str = "operational"
    version: str = "1.0.0"


class ManageProductionQualityOperationalAgent(BaseAgent, ProtocolMixin):
    VERSION = "1.0.0"
    APQC_PROCESS_ID = "4.3.3"

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

    def _calculate_process_capability(self, measurements, spec_limits):
        # Cp and Cpk calculations for process capability
        usl = spec_limits.get("upper_spec_limit")
        lsl = spec_limits.get("lower_spec_limit")
        target = spec_limits.get("target", (usl + lsl) / 2)

        mean = np.mean(measurements)
        std_dev = np.std(measurements, ddof=1)

        # Cp: Process Capability (centered process)
        cp = (usl - lsl) / (6 * std_dev) if std_dev > 0 else 0

        # Cpk: Process Capability Index (actual process)
        cpu = (usl - mean) / (3 * std_dev) if std_dev > 0 else 0
        cpl = (mean - lsl) / (3 * std_dev) if std_dev > 0 else 0
        cpk = min(cpu, cpl)

        # Interpretation
        if cpk >= 1.33:
            status = "Capable"
        elif cpk >= 1.0:
            status = "Marginally Capable"
        else:
            status = "Not Capable"

        return {
            "cp": round(cp, 3),
            "cpk": round(cpk, 3),
            "mean": round(mean, 3),
            "std_dev": round(std_dev, 3),
            "status": status,
        }

    def _control_chart_analysis(self, measurements):
        # Statistical Process Control chart calculations
        mean = np.mean(measurements)
        std_dev = np.std(measurements, ddof=1)

        ucl = mean + 3 * std_dev  # Upper Control Limit
        lcl = mean - 3 * std_dev  # Lower Control Limit

        out_of_control = [m for m in measurements if m > ucl or m < lcl]

        return {
            "mean": round(mean, 3),
            "ucl": round(ucl, 3),
            "lcl": round(lcl, 3),
            "out_of_control_points": len(out_of_control),
            "in_control": len(out_of_control) == 0,
        }

    def _defect_rate_analysis(self, defects, total_units):
        # DPMO: Defects Per Million Opportunities
        defect_rate = defects / total_units if total_units > 0 else 0
        dpmo = defect_rate * 1000000

        # Sigma level approximation
        if dpmo <= 3.4:
            sigma_level = 6.0
        elif dpmo <= 233:
            sigma_level = 5.0
        elif dpmo <= 6210:
            sigma_level = 4.0
        elif dpmo <= 66807:
            sigma_level = 3.0
        else:
            sigma_level = 2.0

        return {
            "defect_rate_pct": round(defect_rate * 100, 4),
            "dpmo": round(dpmo, 2),
            "sigma_level": sigma_level,
            "quality_rating": (
                "World Class"
                if sigma_level >= 6
                else "Industry Average" if sigma_level >= 4 else "Needs Improvement"
            ),
        }

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


def create_manage_production_quality_operational_agent(config=None):
    return ManageProductionQualityOperationalAgent(
        config or ManageProductionQualityOperationalAgentConfig()
    )
