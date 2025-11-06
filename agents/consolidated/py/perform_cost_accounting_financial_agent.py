"""
PerformCostAccountingFinancialAgent - APQC 8.0 Agent

8.1.2 Perform Cost Accounting

Domain: financial_management
Type: analytical

APQC Blueprint ID: apqc_8_0_c4d5e6f7
Version: 1.0.0
"""

import os
import psutil
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime

from superstandard.agents.base.base_agent import BaseAgent
from library.core.protocols import ProtocolMixin


@dataclass
class PerformCostAccountingFinancialAgentConfig:
    apqc_agent_id: str = "apqc_8_0_c4d5e6f7"
    apqc_category_id: str = "8.0"
    apqc_category_name: str = "Manage Financial Resources"
    apqc_process_id: str = "8.1.2"
    apqc_process_name: str = "8.1.2 Perform Cost Accounting"
    agent_id: str = "apqc_8_0_c4d5e6f7"
    agent_name: str = "perform_cost_accounting_financial_agent"
    agent_type: str = "analytical"
    domain: str = "financial_management"
    version: str = "1.0.0"
    autonomous_level: float = 0.9
    collaboration_mode: str = "orchestrated"
    learning_enabled: bool = True
    self_improvement: bool = True
    compute_mode: str = "adaptive"
    memory_mode: str = "adaptive"
    api_budget_mode: str = "dynamic"
    priority: str = "high"
    testing_required: bool = True
    qa_threshold: float = 0.85
    consensus_weight: float = 1.0
    error_handling: str = "graceful_degradation"
    runtime: str = "ray_actor"
    scaling: str = "horizontal"
    health_checks: bool = True
    monitoring: bool = True
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    max_retries: int = field(default_factory=lambda: int(os.getenv("MAX_RETRIES", "3")))
    timeout_seconds: int = field(default_factory=lambda: int(os.getenv("TIMEOUT_SECONDS", "300")))

    @classmethod
    def from_environment(cls):
        return cls(agent_id=os.getenv("AGENT_ID", "apqc_8_0_c4d5e6f7"))


class PerformCostAccountingFinancialAgent(BaseAgent, ProtocolMixin):
    """
    PerformCostAccountingFinancialAgent - APQC 8.0 Agent

    Skills:
    - cost_allocation: 0.9
    - variance_analysis: 0.88
    - abc_costing: 0.86

    Protocols: A2A, A2P, ACP, ANP, MCP
    """

    VERSION = "1.0.0"
    APQC_AGENT_ID = "apqc_8_0_c4d5e6f7"
    APQC_PROCESS_ID = "8.1.2"

    def __init__(self, config: PerformCostAccountingFinancialAgentConfig):
        super().__init__(agent_id=config.agent_id, agent_type=config.agent_type, version=config.version)
        self.config = config
        self.skills = {'cost_allocation': 0.9, 'variance_analysis': 0.88, 'abc_costing': 0.86}
        self.state = {
            "status": "initialized",
            "tasks_processed": 0,
            "last_activity": datetime.now().isoformat()
        }

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute cost accounting analysis"""
        try:
            result = await self._process_cost_accounting(input_data)
            self.state["tasks_processed"] += 1
            return result
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def _process_cost_accounting(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process cost accounting with Activity-Based Costing (ABC)

        Business Logic:
        1. Allocate costs using activity drivers
        2. Calculate variance analysis (actual vs. budget)
        3. Determine unit costs
        4. Identify cost reduction opportunities
        """
        activities = input_data.get('activities', [])
        resources = input_data.get('resources', {})
        cost_drivers = input_data.get('cost_drivers', {})
        budget_data = input_data.get('budget', {})

        # ABC Costing
        abc_analysis = self._perform_abc_costing(activities, resources, cost_drivers)

        # Variance Analysis
        variance_analysis = self._calculate_variances(abc_analysis, budget_data)

        # Unit Cost Calculation
        unit_costs = self._calculate_unit_costs(abc_analysis, input_data.get('output_units', {}))

        # Cost Reduction Opportunities
        opportunities = self._identify_cost_opportunities(abc_analysis, variance_analysis)

        return {
            "status": "completed",
            "apqc_process_id": self.APQC_PROCESS_ID,
            "agent_id": self.config.agent_id,
            "timestamp": datetime.now().isoformat(),
            "output": {
                "cost_analysis": {
                    "abc_costing": abc_analysis,
                    "variances": variance_analysis,
                    "unit_costs": unit_costs,
                    "total_allocated_cost": abc_analysis['total_cost']
                },
                "opportunities": opportunities,
                "metrics": {
                    "total_cost": abc_analysis['total_cost'],
                    "total_variance": variance_analysis['total_variance'],
                    "variance_percentage": variance_analysis['variance_percentage'],
                    "cost_reduction_potential": opportunities['total_potential_savings']
                }
            }
        }

    def _perform_abc_costing(self, activities: List[Dict], resources: Dict, cost_drivers: Dict) -> Dict[str, Any]:
        """
        Activity-Based Costing allocation
        """
        activity_costs = []
        total_cost = 0

        for activity in activities:
            activity_name = activity.get('name', 'Unknown')
            driver = activity.get('cost_driver', 'units')
            driver_quantity = activity.get('driver_quantity', 1)

            # Calculate resource consumption
            resource_usage = activity.get('resource_usage', {})
            activity_cost = 0

            for resource_name, usage in resource_usage.items():
                resource_rate = resources.get(resource_name, {}).get('rate', 0)
                cost = usage * resource_rate
                activity_cost += cost

            # Calculate cost per driver unit
            cost_per_driver = activity_cost / driver_quantity if driver_quantity > 0 else 0

            activity_costs.append({
                "activity": activity_name,
                "total_cost": round(activity_cost, 2),
                "cost_driver": driver,
                "driver_quantity": driver_quantity,
                "cost_per_driver": round(cost_per_driver, 2)
            })

            total_cost += activity_cost

        # Calculate activity cost percentages
        for ac in activity_costs:
            ac['percentage_of_total'] = round((ac['total_cost'] / total_cost * 100), 2) if total_cost > 0 else 0

        return {
            "activity_costs": activity_costs,
            "total_cost": round(total_cost, 2),
            "costing_method": "activity_based_costing"
        }

    def _calculate_variances(self, abc_analysis: Dict, budget_data: Dict) -> Dict[str, Any]:
        """
        Calculate cost variances (actual vs. budget)
        """
        actual_total = abc_analysis['total_cost']
        budget_total = budget_data.get('total_budget', actual_total)

        total_variance = actual_total - budget_total
        variance_percentage = (total_variance / budget_total * 100) if budget_total > 0 else 0

        # Activity-level variances
        activity_variances = []
        budget_by_activity = budget_data.get('activity_budgets', {})

        for activity in abc_analysis['activity_costs']:
            activity_name = activity['activity']
            actual_cost = activity['total_cost']
            budgeted_cost = budget_by_activity.get(activity_name, actual_cost)

            variance = actual_cost - budgeted_cost
            variance_pct = (variance / budgeted_cost * 100) if budgeted_cost > 0 else 0

            activity_variances.append({
                "activity": activity_name,
                "actual": actual_cost,
                "budget": budgeted_cost,
                "variance": round(variance, 2),
                "variance_percentage": round(variance_pct, 2),
                "status": "unfavorable" if variance > 0 else "favorable"
            })

        return {
            "total_variance": round(total_variance, 2),
            "variance_percentage": round(variance_percentage, 2),
            "activity_variances": activity_variances,
            "unfavorable_count": len([v for v in activity_variances if v['status'] == 'unfavorable']),
            "favorable_count": len([v for v in activity_variances if v['status'] == 'favorable'])
        }

    def _calculate_unit_costs(self, abc_analysis: Dict, output_units: Dict) -> Dict[str, Any]:
        """
        Calculate unit costs for products/services
        """
        total_cost = abc_analysis['total_cost']
        unit_costs = []

        for product_name, units in output_units.items():
            if units > 0:
                # Allocate costs proportionally based on activity consumption
                allocated_cost = total_cost / len(output_units)  # Simplified allocation
                unit_cost = allocated_cost / units

                unit_costs.append({
                    "product": product_name,
                    "units_produced": units,
                    "allocated_cost": round(allocated_cost, 2),
                    "unit_cost": round(unit_cost, 2)
                })

        return {
            "unit_costs": unit_costs,
            "total_units": sum(output_units.values()),
            "average_unit_cost": round(total_cost / sum(output_units.values()), 2) if sum(output_units.values()) > 0 else 0
        }

    def _identify_cost_opportunities(self, abc_analysis: Dict, variance_analysis: Dict) -> Dict[str, Any]:
        """
        Identify cost reduction opportunities
        """
        opportunities = []
        total_potential = 0

        # Identify high-cost activities
        sorted_activities = sorted(abc_analysis['activity_costs'], key=lambda x: x['total_cost'], reverse=True)

        for activity in sorted_activities[:3]:  # Top 3 cost drivers
            if activity['percentage_of_total'] > 20:
                potential_saving = activity['total_cost'] * 0.10  # 10% reduction target
                opportunities.append({
                    "activity": activity['activity'],
                    "current_cost": activity['total_cost'],
                    "opportunity": "High cost driver - optimize process",
                    "potential_savings": round(potential_saving, 2),
                    "priority": "high"
                })
                total_potential += potential_saving

        # Identify unfavorable variances
        unfavorable = [v for v in variance_analysis['activity_variances'] if v['status'] == 'unfavorable']
        for variance in unfavorable[:2]:
            if abs(variance['variance_percentage']) > 10:
                potential_saving = abs(variance['variance']) * 0.5
                opportunities.append({
                    "activity": variance['activity'],
                    "current_cost": variance['actual'],
                    "opportunity": "Unfavorable variance - investigate and control",
                    "potential_savings": round(potential_saving, 2),
                    "priority": "medium"
                })
                total_potential += potential_saving

        return {
            "opportunities": opportunities,
            "total_potential_savings": round(total_potential, 2),
            "count": len(opportunities)
        }

    def _validate_input(self, input_data: Dict[str, Any]) -> bool:
        return isinstance(input_data, dict) and 'activities' in input_data

    async def health_check(self) -> Dict[str, Any]:
        return {
            "agent_id": self.config.agent_id,
            "status": self.state["status"],
            "version": self.VERSION
        }

    def log(self, level: str, message: str):
        print(f"[{datetime.now().isoformat()}] [{level.upper()}] [{self.config.agent_name}] {message}")


def create_perform_cost_accounting_financial_agent(config: Optional[PerformCostAccountingFinancialAgentConfig] = None):
    if config is None:
        config = PerformCostAccountingFinancialAgentConfig()
    return PerformCostAccountingFinancialAgent(config)
