"""
PlanSupplyChainResourcesOperationalAgent - APQC Agent
Process: 4.1.4 | ID: apqc_4_0_x6y7z8a9
Skills: sales_operations_planning (0.92), capacity_modeling (0.89), resource_optimization (0.88)
Compliance: All 8 principles | Protocols: A2A, A2P, ACP, ANP, MCP
"""

import os
import psutil
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from library.core.base_agent import BaseAgent
from library.core.protocols import ProtocolMixin

@dataclass
class PlanSupplyChainResourcesOperationalAgentConfig:
    apqc_agent_id: str = "apqc_4_0_x6y7z8a9"
    apqc_process_id: str = "4.1.4"
    agent_id: str = "apqc_4_0_x6y7z8a9"
    agent_name: str = "plan_supply_chain_resources_operational_agent"
    agent_type: str = "operational"
    version: str = "1.0.0"

class PlanSupplyChainResourcesOperationalAgent(BaseAgent, ProtocolMixin):
    VERSION = "1.0.0"
    APQC_PROCESS_ID = "4.1.4"

    def __init__(self, config):
        super().__init__(agent_id=config.agent_id, agent_type=config.agent_type, version=config.version)
        self.config = config
        self.state = {"status": "initialized", "tasks_processed": 0}

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Execute business logic based on agent type
            result = {}
            
            # Call appropriate methods based on input
            if 'contracts' in input_data:
                result['contract_analysis'] = self._analyze_contract_value(input_data['contracts'])
                result['renewal_recommendations'] = self._optimize_renewals(input_data['contracts'], input_data.get('market_rates', {}))
            
            if 'measurements' in input_data and 'spec_limits' in input_data:
                result['process_capability'] = self._calculate_process_capability(input_data['measurements'], input_data['spec_limits'])
                result['control_chart'] = self._control_chart_analysis(input_data['measurements'])
            
            if 'warehouse_layout' in input_data:
                result['space_utilization'] = self._calculate_space_utilization(input_data['warehouse_layout'], input_data.get('inventory', []))
            
            if 'demand_forecast' in input_data:
                result['sop_plan'] = self._sales_operations_planning(input_data['demand_forecast'], input_data.get('capacity_data', {}))
            
            if 'shipments' in input_data:
                result['route_optimization'] = self._optimize_routes(input_data['shipments'], input_data.get('routes', []))
                result['load_consolidation'] = self._consolidate_loads(input_data['shipments'])
            
            return {
                "status": "completed",
                "apqc_process_id": self.APQC_PROCESS_ID,
                "agent_id": self.config.agent_id,
                "timestamp": datetime.now().isoformat(),
                "output": result
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}


    def _sales_operations_planning(self, demand_forecast, capacity_data):
        # S&OP: Align demand forecast with capacity
        sop_plan = {}
        
        for period in demand_forecast:
            period_id = period.get('period')
            forecasted_demand = period.get('demand_units', 0)
            capacity = capacity_data.get(period_id, {}).get('available_capacity', 0)
            
            utilization = (forecasted_demand / capacity * 100) if capacity > 0 else 0
            
            if utilization > 100:
                gap = forecasted_demand - capacity
                action = "Increase capacity or outsource"
            elif utilization < 70:
                gap = capacity - forecasted_demand
                action = "Reduce costs or increase sales"
            else:
                gap = 0
                action = "Maintain current plan"
            
            sop_plan[period_id] = {
                "demand": forecasted_demand,
                "capacity": capacity,
                "utilization_pct": round(utilization, 2),
                "gap": gap,
                "recommended_action": action
            }
        
        return sop_plan
    
    def _capacity_constraint_analysis(self, resource_constraints):
        # Theory of Constraints: Identify bottlenecks
        bottlenecks = []
        
        for resource, data in resource_constraints.items():
            demand = data.get('required_hours', 0)
            available = data.get('available_hours', 0)
            
            constraint_ratio = demand / available if available > 0 else 999
            
            if constraint_ratio > 1.0:
                bottlenecks.append({
                    "resource": resource,
                    "constraint_ratio": round(constraint_ratio, 3),
                    "shortage_hours": round(demand - available, 2),
                    "priority": "critical" if constraint_ratio > 1.5 else "high"
                })
        
        # Sort by severity
        bottlenecks.sort(key=lambda x: x['constraint_ratio'], reverse=True)
        
        return bottlenecks
    
    def _scenario_planning(self, base_plan, scenarios):
        # Scenario analysis for risk mitigation
        scenario_results = {}
        
        for scenario_name, assumptions in scenarios.items():
            demand_multiplier = assumptions.get('demand_change', 1.0)
            cost_multiplier = assumptions.get('cost_change', 1.0)
            
            adjusted_revenue = base_plan.get('revenue', 0) * demand_multiplier
            adjusted_costs = base_plan.get('costs', 0) * cost_multiplier
            adjusted_profit = adjusted_revenue - adjusted_costs
            
            scenario_results[scenario_name] = {
                "revenue": round(adjusted_revenue, 2),
                "costs": round(adjusted_costs, 2),
                "profit": round(adjusted_profit, 2),
                "profit_change_pct": round((adjusted_profit - base_plan.get('profit', 0)) / base_plan.get('profit', 1) * 100, 2)
            }
        
        return scenario_results


    async def health_check(self) -> Dict[str, Any]:
        return {"agent_id": self.config.agent_id, "status": self.state["status"], "version": self.VERSION}

    def log(self, level: str, message: str):
        print(f"[{datetime.now().isoformat()}] [{level.upper()}] [{self.config.agent_name}] {message}")

def create_plan_supply_chain_resources_operational_agent(config=None):
    return PlanSupplyChainResourcesOperationalAgent(config or PlanSupplyChainResourcesOperationalAgentConfig())
