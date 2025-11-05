"""
ManageCompensationHumanCapitalAgent - APQC Agent
Process: 7.4.3 | ID: apqc_7_0_d2e3f4g5
Skills: salary_benchmarking (0.90), pay_equity_analysis (0.89), incentive_design (0.87)
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
class ManageCompensationHumanCapitalAgentConfig:
    apqc_agent_id: str = "apqc_7_0_d2e3f4g5"
    apqc_process_id: str = "7.4.3"
    agent_id: str = "apqc_7_0_d2e3f4g5"
    agent_name: str = "manage_compensation_human_capital_agent"
    agent_type: str = "financial" if '8_0' in agent['file'] else "strategic" if '1_0' in agent['file'] else "human_capital"
    version: str = "1.0.0"

class ManageCompensationHumanCapitalAgent(BaseAgent, ProtocolMixin):
    VERSION = "1.0.0"
    APQC_PROCESS_ID = "7.4.3"

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


    def _compa_ratio_analysis(self, employee_compensation, market_data):
        # Compa-Ratio = (Actual Salary / Midpoint of Salary Range) × 100
        compa_ratios = {}
        
        for employee in employee_compensation:
            employee_id = employee.get('employee_id')
            job_level = employee.get('job_level')
            actual_salary = employee.get('salary', 0)
            
            market_midpoint = market_data.get(job_level, {}).get('market_midpoint', actual_salary)
            
            compa_ratio = (actual_salary / market_midpoint * 100) if market_midpoint > 0 else 100
            
            # Interpretation
            if compa_ratio < 80:
                position = "Below Range"
            elif compa_ratio < 90:
                position = "Low in Range"
            elif compa_ratio <= 110:
                position = "In Range"
            elif compa_ratio <= 120:
                position = "High in Range"
            else:
                position = "Above Range"
            
            compa_ratios[employee_id] = {
                "actual_salary": actual_salary,
                "market_midpoint": market_midpoint,
                "compa_ratio": round(compa_ratio, 2),
                "position": position,
                "action_needed": compa_ratio < 85 or compa_ratio > 115
            }
        
        return compa_ratios
    
    def _pay_equity_analysis(self, employee_data):
        # Analyze pay equity across demographics
        equity_analysis = {}
        
        # Group by job level and analyze pay by gender, ethnicity, etc.
        for job_level in set(e.get('job_level') for e in employee_data):
            level_employees = [e for e in employee_data if e.get('job_level') == job_level]
            
            # Gender pay analysis
            male_avg = np.mean([e.get('salary', 0) for e in level_employees if e.get('gender') == 'M'])
            female_avg = np.mean([e.get('salary', 0) for e in level_employees if e.get('gender') == 'F'])
            
            pay_gap_pct = ((male_avg - female_avg) / male_avg * 100) if male_avg > 0 else 0
            
            equity_analysis[job_level] = {
                "male_avg_salary": round(male_avg, 2),
                "female_avg_salary": round(female_avg, 2),
                "pay_gap_pct": round(pay_gap_pct, 2),
                "equity_concern": abs(pay_gap_pct) > 5,
                "sample_size": len(level_employees)
            }
        
        return equity_analysis
    
    def _incentive_modeling(self, performance_ratings, budget_constraints):
        # Design incentive/bonus structure
        incentive_plan = {}
        
        total_budget = budget_constraints.get('total_incentive_budget', 0)
        
        # Performance-based allocation
        total_performance_score = sum(r.get('performance_score', 0) for r in performance_ratings)
        
        for employee in performance_ratings:
            employee_id = employee.get('employee_id')
            performance_score = employee.get('performance_score', 0)  # 1-5 scale
            base_salary = employee.get('base_salary', 0)
            
            # Allocate incentive based on performance
            performance_weight = (performance_score / total_performance_score) if total_performance_score > 0 else 0
            incentive_amount = total_budget * performance_weight
            
            # Calculate as percentage of salary
            incentive_pct = (incentive_amount / base_salary * 100) if base_salary > 0 else 0
            
            incentive_plan[employee_id] = {
                "performance_score": performance_score,
                "base_salary": base_salary,
                "incentive_amount": round(incentive_amount, 2),
                "incentive_pct": round(incentive_pct, 2),
                "total_compensation": round(base_salary + incentive_amount, 2)
            }
        
        return incentive_plan
    
    def _total_rewards_benchmarking(self, internal_comp, market_comp):
        # Total Rewards = Base + Bonus + Benefits + Equity
        benchmarking = {}
        
        for employee_id, comp in internal_comp.items():
            job_level = comp.get('job_level')
            
            total_internal = (comp.get('base_salary', 0) + 
                            comp.get('bonus', 0) + 
                            comp.get('benefits_value', 0) + 
                            comp.get('equity_value', 0))
            
            market_benchmark = market_comp.get(job_level, {})
            total_market = (market_benchmark.get('base', 0) + 
                          market_benchmark.get('bonus', 0) + 
                          market_benchmark.get('benefits', 0) + 
                          market_benchmark.get('equity', 0))
            
            market_position = (total_internal / total_market * 100) if total_market > 0 else 100
            
            benchmarking[employee_id] = {
                "total_rewards_internal": round(total_internal, 2),
                "total_rewards_market": round(total_market, 2),
                "market_position_pct": round(market_position, 2),
                "competitive_position": "Above Market" if market_position > 110 else "At Market" if market_position >= 90 else "Below Market"
            }
        
        return benchmarking


    async def health_check(self) -> Dict[str, Any]:
        return {"agent_id": self.config.agent_id, "status": self.state["status"], "version": self.VERSION}

    def log(self, level: str, message: str):
        print(f"[{datetime.now().isoformat()}] [{level.upper()}] [{self.config.agent_name}] {message}")

def create_manage_compensation_human_capital_agent(config=None):
    return ManageCompensationHumanCapitalAgent(config or ManageCompensationHumanCapitalAgentConfig())
