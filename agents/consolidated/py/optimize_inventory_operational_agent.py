"""
OptimizeInventoryOperationalAgent - APQC 4.0
4.4.1 Optimize Inventory
APQC ID: apqc_4_0_l3m4n5o6
"""

import os
import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from datetime import datetime
from math import sqrt

from library.core.base_agent import BaseAgent
from library.core.protocols import ProtocolMixin


@dataclass
class OptimizeInventoryOperationalAgentConfig:
    apqc_agent_id: str = "apqc_4_0_l3m4n5o6"
    apqc_process_id: str = "4.4.1"
    agent_name: str = "optimize_inventory_operational_agent"
    agent_type: str = "operational"
    version: str = "1.0.0"


class OptimizeInventoryOperationalAgent(BaseAgent, ProtocolMixin):
    """
    Skills: eoq_calculation: 0.92, safety_stock: 0.88, abc_analysis: 0.86, reorder_point: 0.85
    """

    VERSION = "1.0.0"
    APQC_PROCESS_ID = "4.4.1"

    def __init__(self, config: OptimizeInventoryOperationalAgentConfig):
        super().__init__(agent_id=config.apqc_agent_id, agent_type=config.agent_type, version=config.version)
        self.config = config
        self.skills = {'eoq_calculation': 0.92, 'safety_stock': 0.88, 'abc_analysis': 0.86, 'reorder_point': 0.85}

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize inventory using EOQ, safety stock, ABC analysis, and reorder points
        """
        demand_forecast = input_data.get('demand_forecast', {})
        lead_times = input_data.get('lead_times', {})
        holding_costs = input_data.get('holding_costs', {})
        ordering_costs = input_data.get('ordering_costs', {})
        items = input_data.get('items', [])

        # EOQ Calculation
        eoq_analysis = self._calculate_eoq(items, demand_forecast, holding_costs, ordering_costs)

        # Safety Stock Calculation
        safety_stock = self._calculate_safety_stock(items, demand_forecast, lead_times)

        # ABC Analysis
        abc_classification = self._perform_abc_analysis(items, demand_forecast)

        # Reorder Points
        reorder_points = self._calculate_reorder_points(items, demand_forecast, lead_times, safety_stock)

        return {
            "status": "completed",
            "apqc_process_id": self.APQC_PROCESS_ID,
            "timestamp": datetime.now().isoformat(),
            "output": {
                "inventory_plan": {
                    "eoq_recommendations": eoq_analysis,
                    "safety_stocks": safety_stock,
                    "reorder_points": reorder_points,
                    "abc_categories": abc_classification
                },
                "metrics": {
                    "total_inventory_value": eoq_analysis['total_inventory_value'],
                    "average_order_quantity": eoq_analysis['average_eoq'],
                    "category_a_items": len(abc_classification['category_a']),
                    "recommended_safety_stock_value": safety_stock['total_safety_stock_value']
                }
            }
        }

    def _calculate_eoq(self, items: List[Dict], demand: Dict, holding_costs: Dict, ordering_costs: Dict) -> Dict[str, Any]:
        """
        Calculate Economic Order Quantity (EOQ)
        EOQ = sqrt((2 * D * S) / H)
        Where: D = annual demand, S = ordering cost, H = holding cost per unit
        """
        eoq_results = []
        total_inventory_value = 0

        for item in items:
            item_id = item.get('item_id')
            item_name = item.get('name', 'Unknown')
            unit_cost = item.get('unit_cost', 0)

            annual_demand = demand.get(item_id, {}).get('annual_demand', 0)
            ordering_cost = ordering_costs.get(item_id, 100)  # Default $100
            holding_cost_rate = holding_costs.get(item_id, 0.25)  # Default 25% of unit cost
            holding_cost_per_unit = unit_cost * holding_cost_rate

            if annual_demand > 0 and holding_cost_per_unit > 0:
                # EOQ Formula
                eoq = sqrt((2 * annual_demand * ordering_cost) / holding_cost_per_unit)

                # Total Cost at EOQ
                number_of_orders = annual_demand / eoq if eoq > 0 else 0
                ordering_cost_total = number_of_orders * ordering_cost
                average_inventory = eoq / 2
                holding_cost_total = average_inventory * holding_cost_per_unit
                total_cost = ordering_cost_total + holding_cost_total

                eoq_results.append({
                    "item_id": item_id,
                    "item_name": item_name,
                    "eoq": round(eoq, 0),
                    "annual_demand": annual_demand,
                    "number_of_orders_per_year": round(number_of_orders, 1),
                    "total_annual_cost": round(total_cost, 2),
                    "average_inventory": round(average_inventory, 0)
                })

                total_inventory_value += average_inventory * unit_cost

        average_eoq = np.mean([r['eoq'] for r in eoq_results]) if eoq_results else 0

        return {
            "eoq_by_item": eoq_results,
            "average_eoq": round(average_eoq, 0),
            "total_inventory_value": round(total_inventory_value, 2)
        }

    def _calculate_safety_stock(self, items: List[Dict], demand: Dict, lead_times: Dict) -> Dict[str, Any]:
        """
        Calculate Safety Stock
        Safety Stock = Z * σ * sqrt(LT)
        Where: Z = service level factor, σ = demand std dev, LT = lead time
        """
        service_level_z = 1.65  # 95% service level

        safety_stock_results = []
        total_safety_stock_value = 0

        for item in items:
            item_id = item.get('item_id')
            item_name = item.get('name', 'Unknown')
            unit_cost = item.get('unit_cost', 0)

            demand_data = demand.get(item_id, {})
            average_demand = demand_data.get('average_daily_demand', 0)
            demand_std_dev = demand_data.get('demand_std_dev', average_demand * 0.2)  # Default 20% variability

            lead_time_days = lead_times.get(item_id, 7)  # Default 7 days

            if average_demand > 0:
                # Safety Stock Formula
                safety_stock = service_level_z * demand_std_dev * sqrt(lead_time_days)

                safety_stock_results.append({
                    "item_id": item_id,
                    "item_name": item_name,
                    "safety_stock": round(safety_stock, 0),
                    "service_level": "95%",
                    "lead_time_days": lead_time_days,
                    "average_daily_demand": round(average_demand, 1)
                })

                total_safety_stock_value += safety_stock * unit_cost

        return {
            "safety_stock_by_item": safety_stock_results,
            "total_safety_stock_value": round(total_safety_stock_value, 2),
            "service_level": "95%"
        }

    def _perform_abc_analysis(self, items: List[Dict], demand: Dict) -> Dict[str, Any]:
        """
        Perform ABC Analysis
        A items: Top 20% of items, 80% of value
        B items: Next 30% of items, 15% of value
        C items: Bottom 50% of items, 5% of value
        """
        item_values = []

        for item in items:
            item_id = item.get('item_id')
            unit_cost = item.get('unit_cost', 0)
            annual_demand = demand.get(item_id, {}).get('annual_demand', 0)
            annual_value = unit_cost * annual_demand

            item_values.append({
                "item_id": item_id,
                "item_name": item.get('name', 'Unknown'),
                "annual_value": annual_value,
                "unit_cost": unit_cost,
                "annual_demand": annual_demand
            })

        # Sort by annual value
        item_values.sort(key=lambda x: x['annual_value'], reverse=True)

        # Calculate cumulative percentage
        total_value = sum(item['annual_value'] for item in item_values)
        cumulative_value = 0
        cumulative_percentage = []

        for item in item_values:
            cumulative_value += item['annual_value']
            cumulative_pct = (cumulative_value / total_value * 100) if total_value > 0 else 0
            cumulative_percentage.append(cumulative_pct)
            item['cumulative_percentage'] = round(cumulative_pct, 2)

        # Classify into ABC categories
        category_a = []
        category_b = []
        category_c = []

        for item in item_values:
            if item['cumulative_percentage'] <= 80:
                category_a.append(item)
                item['category'] = 'A'
            elif item['cumulative_percentage'] <= 95:
                category_b.append(item)
                item['category'] = 'B'
            else:
                category_c.append(item)
                item['category'] = 'C'

        return {
            "category_a": category_a,
            "category_b": category_b,
            "category_c": category_c,
            "classification_summary": {
                "a_count": len(category_a),
                "b_count": len(category_b),
                "c_count": len(category_c),
                "a_value_percentage": round((sum(i['annual_value'] for i in category_a) / total_value * 100), 2) if total_value > 0 else 0,
                "b_value_percentage": round((sum(i['annual_value'] for i in category_b) / total_value * 100), 2) if total_value > 0 else 0,
                "c_value_percentage": round((sum(i['annual_value'] for i in category_c) / total_value * 100), 2) if total_value > 0 else 0
            }
        }

    def _calculate_reorder_points(self, items: List[Dict], demand: Dict, lead_times: Dict, safety_stock: Dict) -> Dict[str, Any]:
        """
        Calculate Reorder Points
        ROP = (Average Daily Demand * Lead Time) + Safety Stock
        """
        safety_stock_map = {ss['item_id']: ss['safety_stock'] for ss in safety_stock['safety_stock_by_item']}

        reorder_points = []

        for item in items:
            item_id = item.get('item_id')
            item_name = item.get('name', 'Unknown')

            average_daily_demand = demand.get(item_id, {}).get('average_daily_demand', 0)
            lead_time_days = lead_times.get(item_id, 7)
            safety_stock_qty = safety_stock_map.get(item_id, 0)

            # Reorder Point Formula
            rop = (average_daily_demand * lead_time_days) + safety_stock_qty

            reorder_points.append({
                "item_id": item_id,
                "item_name": item_name,
                "reorder_point": round(rop, 0),
                "lead_time_demand": round(average_daily_demand * lead_time_days, 0),
                "safety_stock": round(safety_stock_qty, 0),
                "current_stock": item.get('current_stock', 0),
                "order_needed": item.get('current_stock', 0) < rop
            })

        items_to_order = [r for r in reorder_points if r['order_needed']]

        return {
            "reorder_points_by_item": reorder_points,
            "items_requiring_order": items_to_order,
            "immediate_orders_count": len(items_to_order)
        }

    def log(self, level: str, message: str):
        print(f"[{datetime.now().isoformat()}] [{level}] {message}")


def create_optimize_inventory_operational_agent(config: Optional[OptimizeInventoryOperationalAgentConfig] = None):
    if config is None:
        config = OptimizeInventoryOperationalAgentConfig()
    return OptimizeInventoryOperationalAgent(config)
