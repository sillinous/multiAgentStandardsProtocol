"""
PerformStrategicPlanningStrategicAgent - APQC Agent
Process: 1.2.2 | ID: apqc_1_0_b0c1d2e3
Skills: swot_analysis (0.90), scenario_planning (0.88), strategic_alignment (0.87)
Compliance: All 8 principles | Protocols: A2A, A2P, ACP, ANP, MCP
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
class PerformStrategicPlanningStrategicAgentConfig:
    apqc_agent_id: str = "apqc_1_0_b0c1d2e3"
    apqc_process_id: str = "1.2.2"
    agent_id: str = "apqc_1_0_b0c1d2e3"
    agent_name: str = "perform_strategic_planning_strategic_agent"
    agent_type: str = "financial" if '8_0' in agent['file'] else "strategic" if '1_0' in agent['file'] else "human_capital"
    version: str = "1.0.0"

class PerformStrategicPlanningStrategicAgent(BaseAgent, ProtocolMixin):
    VERSION = "1.0.0"
    APQC_PROCESS_ID = "1.2.2"

    def __init__(self, config):
        super().__init__(agent_id=config.agent_id, agent_type=config.agent_type, version=config.version)
        self.config = config
        self.state = {"status": "initialized", "tasks_processed": 0}

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            result = {}
            
            # Execute based on agent specialty
            if 'revenue_data' in input_data and 'variable_costs' in input_data:
                result['contribution_margin'] = self._calculate_contribution_margin(input_data['revenue_data'], input_data['variable_costs'])
            
            if 'fixed_costs' in input_data:
                result['breakeven_analysis'] = self._breakeven_analysis(
                    input_data['fixed_costs'],
                    input_data.get('contribution_margin_pct', 30),
                    input_data.get('price_per_unit', 100)
                )
            
            if 'ar_data' in input_data or 'ar_balance' in input_data:
                if 'ar_data' in input_data:
                    result['cash_forecast'] = self._forecast_cash_flow(
                        input_data['ar_data'],
                        input_data.get('ap_data', []),
                        input_data.get('revenue_forecast', []),
                        input_data.get('payment_terms', {})
                    )
                else:
                    result['working_capital'] = self._working_capital_ratios(
                        input_data.get('ar_balance', 0),
                        input_data.get('inventory_balance', 0),
                        input_data.get('ap_balance', 0),
                        input_data.get('revenue_annual', 1),
                        input_data.get('cogs_annual', 1)
                    )
            
            if 'internal_capabilities' in input_data:
                result['swot_analysis'] = self._swot_analysis(
                    input_data['internal_capabilities'],
                    input_data.get('market_conditions', {}),
                    input_data.get('competitive_landscape', {})
                )
            
            if 'total_budget' in input_data and 'cost_centers' in input_data:
                result['budget_allocation'] = self._allocate_budget(
                    input_data['total_budget'],
                    input_data['cost_centers'],
                    input_data.get('strategic_priorities', {})
                )
            
            if 'employee_compensation' in input_data:
                result['compa_ratio_analysis'] = self._compa_ratio_analysis(
                    input_data['employee_compensation'],
                    input_data.get('market_data', {})
                )
            
            return {
                "status": "completed",
                "apqc_process_id": self.APQC_PROCESS_ID,
                "agent_id": self.config.agent_id,
                "timestamp": datetime.now().isoformat(),
                "output": result
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}


    def _swot_analysis(self, internal_capabilities, market_conditions, competitive_landscape):
        swot = {
            "strengths": [],
            "weaknesses": [],
            "opportunities": [],
            "threats": []
        }
        
        # Analyze internal capabilities
        for cap_name, cap_score in internal_capabilities.items():
            if cap_score >= 0.8:
                swot["strengths"].append({"capability": cap_name, "score": cap_score})
            elif cap_score < 0.5:
                swot["weaknesses"].append({"capability": cap_name, "score": cap_score})
        
        # Analyze market conditions
        market_growth = market_conditions.get('growth_rate', 0)
        if market_growth > 0.10:
            swot["opportunities"].append({"factor": "High market growth", "impact": "high"})
        elif market_growth < 0:
            swot["threats"].append({"factor": "Market contraction", "impact": "high"})
        
        # Competitive analysis
        competitor_count = len(competitive_landscape.get('competitors', []))
        if competitor_count < 5:
            swot["opportunities"].append({"factor": "Low competition", "impact": "medium"})
        elif competitor_count > 20:
            swot["threats"].append({"factor": "Intense competition", "impact": "high"})
        
        return swot
    
    def _scenario_modeling(self, base_case, scenarios):
        scenario_results = {}
        
        for scenario_name, scenario_params in scenarios.items():
            revenue_impact = scenario_params.get('revenue_multiplier', 1.0)
            cost_impact = scenario_params.get('cost_multiplier', 1.0)
            probability = scenario_params.get('probability', 0.33)
            
            scenario_revenue = base_case.get('revenue', 0) * revenue_impact
            scenario_costs = base_case.get('costs', 0) * cost_impact
            scenario_profit = scenario_revenue - scenario_costs
            
            expected_value = scenario_profit * probability
            
            scenario_results[scenario_name] = {
                "revenue": round(scenario_revenue, 2),
                "costs": round(scenario_costs, 2),
                "profit": round(scenario_profit, 2),
                "probability": probability,
                "expected_value": round(expected_value, 2)
            }
        
        return scenario_results
    
    def _strategic_fit_analysis(self, initiatives, strategic_objectives):
        fit_scores = {}
        
        for initiative in initiatives:
            initiative_id = initiative.get('initiative_id')
            alignment_score = 0
            
            # Check alignment with each strategic objective
            for objective in strategic_objectives:
                if objective.get('focus_area') in initiative.get('focus_areas', []):
                    alignment_score += objective.get('priority_weight', 1.0)
            
            # Normalize score to 0-100
            max_possible = sum(obj.get('priority_weight', 1.0) for obj in strategic_objectives)
            normalized_score = (alignment_score / max_possible * 100) if max_possible > 0 else 0
            
            fit_scores[initiative_id] = {
                "alignment_score": round(normalized_score, 2),
                "strategic_fit": "High" if normalized_score >= 75 else "Medium" if normalized_score >= 50 else "Low",
                "recommendation": "Prioritize" if normalized_score >= 75 else "Consider" if normalized_score >= 50 else "Defer"
            }
        
        return fit_scores
    
    def _capability_gap_assessment(self, required_capabilities, current_capabilities):
        gaps = []
        
        for req_cap, req_level in required_capabilities.items():
            current_level = current_capabilities.get(req_cap, 0)
            gap = req_level - current_level
            
            if gap > 0:
                gaps.append({
                    "capability": req_cap,
                    "required_level": req_level,
                    "current_level": current_level,
                    "gap": round(gap, 2),
                    "priority": "critical" if gap > 0.5 else "high" if gap > 0.3 else "medium"
                })
        
        # Sort by gap size
        gaps.sort(key=lambda x: x['gap'], reverse=True)
        
        return gaps


    async def health_check(self) -> Dict[str, Any]:
        return {"agent_id": self.config.agent_id, "status": self.state["status"], "version": self.VERSION}

    def log(self, level: str, message: str):
        print(f"[{datetime.now().isoformat()}] [{level.upper()}] [{self.config.agent_name}] {message}")

def create_perform_strategic_planning_strategic_agent(config=None):
    return PerformStrategicPlanningStrategicAgent(config or PerformStrategicPlanningStrategicAgentConfig())
