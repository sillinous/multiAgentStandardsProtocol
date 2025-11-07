"""
CalculateTransportationCostsLogisticsAgent - APQC 4.5.4
Calculate and Analyze Transportation Costs for Ride-Sharing Operations
APQC ID: apqc_4_5_c1o2s3t4

This agent calculates comprehensive transportation costs including fuel, driver compensation,
vehicle depreciation, and operational overhead for ride-sharing services.
"""

import os
import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

from superstandard.agents.base.base_agent import BaseAgent
from src.superstandard.agents.base.protocols import ProtocolMixin


@dataclass
class CalculateTransportationCostsLogisticsAgentConfig:
    apqc_agent_id: str = "apqc_4_5_c1o2s3t4"
    apqc_process_id: str = "4.5.4"
    agent_name: str = "calculate_transportation_costs_logistics_agent"
    agent_type: str = "operational"
    version: str = "1.0.0"


class CalculateTransportationCostsLogisticsAgent(BaseAgent, ProtocolMixin):
    """
    APQC 4.5.4 - Calculate Transportation Costs

    Skills:
    - cost_modeling: 0.91 (comprehensive cost calculation)
    - efficiency_analysis: 0.89 (cost per mile/ride optimization)
    - profitability_tracking: 0.87 (margin analysis)
    - variance_analysis: 0.85 (actual vs. budget tracking)

    Use Cases:
    - Calculate cost per ride
    - Analyze driver profitability
    - Track fuel efficiency
    - Optimize operational costs
    """

    VERSION = "1.0.0"
    APQC_PROCESS_ID = "4.5.4"

    def __init__(self, config: CalculateTransportationCostsLogisticsAgentConfig):
        super().__init__(
            agent_id=config.apqc_agent_id, agent_type=config.agent_type, version=config.version
        )
        self.config = config
        self.skills = {
            "cost_modeling": 0.91,
            "efficiency_analysis": 0.89,
            "profitability_tracking": 0.87,
            "variance_analysis": 0.85,
        }

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate transportation costs for ride-sharing operations

        Input:
        {
            "ride_data": {
                "total_rides": 1500,
                "total_distance_km": 45000,
                "total_revenue": 125000,
                "active_drivers": 150,
                "period_days": 30
            },
            "cost_inputs": {
                "fuel_price_per_liter": 1.50,
                "average_fuel_efficiency_km_per_liter": 12.0,
                "driver_commission_rate": 0.75,
                "platform_fee_per_ride": 2.50,
                "insurance_cost_per_month": 200,
                "vehicle_depreciation_per_km": 0.15,
                "maintenance_cost_per_km": 0.08
            },
            "budget": {
                "target_cost_per_km": 0.80,
                "target_cost_per_ride": 25.00,
                "target_margin_percentage": 0.20
            }
        }
        """
        ride_data = input_data.get("ride_data", {})
        cost_inputs = input_data.get("cost_inputs", {})
        budget = input_data.get("budget", {})

        # Calculate detailed cost breakdown
        cost_breakdown = self._calculate_cost_breakdown(ride_data, cost_inputs)

        # Calculate efficiency metrics
        efficiency_metrics = self._calculate_efficiency_metrics(ride_data, cost_breakdown)

        # Calculate profitability analysis
        profitability = self._calculate_profitability(ride_data, cost_breakdown)

        # Perform variance analysis against budget
        variance_analysis = self._perform_variance_analysis(
            efficiency_metrics, profitability, budget
        )

        # Generate cost optimization recommendations
        recommendations = self._generate_cost_recommendations(
            cost_breakdown, efficiency_metrics, variance_analysis
        )

        return {
            "status": "completed",
            "apqc_process_id": self.APQC_PROCESS_ID,
            "timestamp": datetime.now().isoformat(),
            "output": {
                "cost_breakdown": cost_breakdown,
                "efficiency_metrics": efficiency_metrics,
                "profitability_analysis": profitability,
                "variance_analysis": variance_analysis,
                "recommendations": recommendations,
                "summary": {
                    "total_costs": cost_breakdown["total_costs"],
                    "cost_per_ride": efficiency_metrics["cost_per_ride"],
                    "cost_per_km": efficiency_metrics["cost_per_km"],
                    "profit_margin_percentage": profitability["margin_percentage"],
                    "budget_variance_percentage": variance_analysis["overall_variance_percentage"],
                },
            },
        }

    def _calculate_cost_breakdown(
        self, ride_data: Dict[str, Any], cost_inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate detailed breakdown of all transportation costs
        """
        total_distance = ride_data.get("total_distance_km", 0)
        total_rides = ride_data.get("total_rides", 0)
        total_revenue = ride_data.get("total_revenue", 0)
        active_drivers = ride_data.get("active_drivers", 0)
        period_days = ride_data.get("period_days", 30)

        # 1. Fuel Costs
        fuel_price = cost_inputs.get("fuel_price_per_liter", 1.50)
        fuel_efficiency = cost_inputs.get("average_fuel_efficiency_km_per_liter", 12.0)

        fuel_consumed_liters = total_distance / fuel_efficiency if fuel_efficiency > 0 else 0
        fuel_costs = fuel_consumed_liters * fuel_price

        # 2. Driver Compensation
        driver_commission_rate = cost_inputs.get("driver_commission_rate", 0.75)
        driver_compensation = total_revenue * driver_commission_rate

        # 3. Platform Fees
        platform_fee_per_ride = cost_inputs.get("platform_fee_per_ride", 2.50)
        platform_fees = total_rides * platform_fee_per_ride

        # 4. Insurance Costs
        insurance_per_month = cost_inputs.get("insurance_cost_per_month", 200)
        months = period_days / 30
        insurance_costs = active_drivers * insurance_per_month * months

        # 5. Vehicle Depreciation
        depreciation_per_km = cost_inputs.get("vehicle_depreciation_per_km", 0.15)
        depreciation_costs = total_distance * depreciation_per_km

        # 6. Maintenance Costs
        maintenance_per_km = cost_inputs.get("maintenance_cost_per_km", 0.08)
        maintenance_costs = total_distance * maintenance_per_km

        # 7. Other Operational Costs (estimated 5% of revenue)
        other_costs = total_revenue * 0.05

        # Total Costs
        total_costs = (
            fuel_costs
            + driver_compensation
            + platform_fees
            + insurance_costs
            + depreciation_costs
            + maintenance_costs
            + other_costs
        )

        # Calculate percentage breakdown
        cost_percentages = {}
        if total_costs > 0:
            cost_percentages = {
                "fuel": round((fuel_costs / total_costs) * 100, 1),
                "driver_compensation": round((driver_compensation / total_costs) * 100, 1),
                "platform_fees": round((platform_fees / total_costs) * 100, 1),
                "insurance": round((insurance_costs / total_costs) * 100, 1),
                "depreciation": round((depreciation_costs / total_costs) * 100, 1),
                "maintenance": round((maintenance_costs / total_costs) * 100, 1),
                "other": round((other_costs / total_costs) * 100, 1),
            }

        return {
            "fuel_costs": round(fuel_costs, 2),
            "driver_compensation": round(driver_compensation, 2),
            "platform_fees": round(platform_fees, 2),
            "insurance_costs": round(insurance_costs, 2),
            "depreciation_costs": round(depreciation_costs, 2),
            "maintenance_costs": round(maintenance_costs, 2),
            "other_operational_costs": round(other_costs, 2),
            "total_costs": round(total_costs, 2),
            "cost_percentages": cost_percentages,
            "fuel_efficiency_km_per_liter": round(fuel_efficiency, 2),
            "total_fuel_consumed_liters": round(fuel_consumed_liters, 2),
        }

    def _calculate_efficiency_metrics(
        self, ride_data: Dict[str, Any], cost_breakdown: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate cost efficiency metrics
        """
        total_distance = ride_data.get("total_distance_km", 0)
        total_rides = ride_data.get("total_rides", 0)
        total_revenue = ride_data.get("total_revenue", 0)
        active_drivers = ride_data.get("active_drivers", 0)
        period_days = ride_data.get("period_days", 30)

        total_costs = cost_breakdown["total_costs"]

        # Cost per km
        cost_per_km = total_costs / total_distance if total_distance > 0 else 0

        # Cost per ride
        cost_per_ride = total_costs / total_rides if total_rides > 0 else 0

        # Revenue per km
        revenue_per_km = total_revenue / total_distance if total_distance > 0 else 0

        # Revenue per ride
        revenue_per_ride = total_revenue / total_rides if total_rides > 0 else 0

        # Average ride distance
        avg_ride_distance = total_distance / total_rides if total_rides > 0 else 0

        # Rides per driver per day
        rides_per_driver_per_day = (
            total_rides / (active_drivers * period_days)
            if (active_drivers * period_days) > 0
            else 0
        )

        # Distance per driver per day
        km_per_driver_per_day = (
            total_distance / (active_drivers * period_days)
            if (active_drivers * period_days) > 0
            else 0
        )

        # Utilization rate (assume 12-hour work day)
        # Calculate effective working hours based on average speed of 30 km/h
        avg_speed_kmh = 30
        total_driving_hours = total_distance / avg_speed_kmh if avg_speed_kmh > 0 else 0
        available_hours = active_drivers * period_days * 12
        utilization_rate = total_driving_hours / available_hours if available_hours > 0 else 0

        return {
            "cost_per_km": round(cost_per_km, 2),
            "cost_per_ride": round(cost_per_ride, 2),
            "revenue_per_km": round(revenue_per_km, 2),
            "revenue_per_ride": round(revenue_per_ride, 2),
            "average_ride_distance_km": round(avg_ride_distance, 2),
            "rides_per_driver_per_day": round(rides_per_driver_per_day, 2),
            "km_per_driver_per_day": round(km_per_driver_per_day, 2),
            "driver_utilization_rate": round(utilization_rate, 2),
            "total_driving_hours": round(total_driving_hours, 1),
        }

    def _calculate_profitability(
        self, ride_data: Dict[str, Any], cost_breakdown: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate profitability metrics and margins
        """
        total_revenue = ride_data.get("total_revenue", 0)
        total_costs = cost_breakdown["total_costs"]
        total_rides = ride_data.get("total_rides", 0)
        active_drivers = ride_data.get("active_drivers", 0)

        # Gross profit
        gross_profit = total_revenue - total_costs

        # Margin percentage
        margin_percentage = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0

        # Profit per ride
        profit_per_ride = gross_profit / total_rides if total_rides > 0 else 0

        # Profit per driver
        profit_per_driver = gross_profit / active_drivers if active_drivers > 0 else 0

        # Break-even analysis
        # Variable costs (fuel, maintenance, depreciation)
        variable_costs = (
            cost_breakdown["fuel_costs"]
            + cost_breakdown["maintenance_costs"]
            + cost_breakdown["depreciation_costs"]
        )

        # Fixed costs (insurance, platform fees, other operational, driver base compensation)
        fixed_costs = total_costs - variable_costs

        variable_cost_per_ride = variable_costs / total_rides if total_rides > 0 else 0
        avg_revenue_per_ride = total_revenue / total_rides if total_rides > 0 else 0

        # Contribution margin per ride
        contribution_margin = avg_revenue_per_ride - variable_cost_per_ride

        # Break-even rides
        breakeven_rides = fixed_costs / contribution_margin if contribution_margin > 0 else 0

        # Operating leverage
        operating_leverage = (
            contribution_margin * total_rides / gross_profit if gross_profit != 0 else 0
        )

        return {
            "total_revenue": round(total_revenue, 2),
            "total_costs": round(total_costs, 2),
            "gross_profit": round(gross_profit, 2),
            "margin_percentage": round(margin_percentage, 1),
            "profit_per_ride": round(profit_per_ride, 2),
            "profit_per_driver": round(profit_per_driver, 2),
            "variable_costs": round(variable_costs, 2),
            "fixed_costs": round(fixed_costs, 2),
            "contribution_margin_per_ride": round(contribution_margin, 2),
            "breakeven_rides": round(breakeven_rides, 0),
            "actual_vs_breakeven_percentage": (
                round((total_rides / breakeven_rides * 100), 1) if breakeven_rides > 0 else 0
            ),
            "operating_leverage": round(operating_leverage, 2),
        }

    def _perform_variance_analysis(
        self,
        efficiency_metrics: Dict[str, Any],
        profitability: Dict[str, Any],
        budget: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Analyze variances between actual and budgeted costs
        """
        variances = []

        # Cost per km variance
        target_cost_per_km = budget.get("target_cost_per_km", 0)
        actual_cost_per_km = efficiency_metrics["cost_per_km"]

        if target_cost_per_km > 0:
            cost_per_km_variance = actual_cost_per_km - target_cost_per_km
            cost_per_km_variance_pct = (cost_per_km_variance / target_cost_per_km) * 100

            variances.append(
                {
                    "metric": "cost_per_km",
                    "target": round(target_cost_per_km, 2),
                    "actual": round(actual_cost_per_km, 2),
                    "variance": round(cost_per_km_variance, 2),
                    "variance_percentage": round(cost_per_km_variance_pct, 1),
                    "status": "favorable" if cost_per_km_variance < 0 else "unfavorable",
                }
            )

        # Cost per ride variance
        target_cost_per_ride = budget.get("target_cost_per_ride", 0)
        actual_cost_per_ride = efficiency_metrics["cost_per_ride"]

        if target_cost_per_ride > 0:
            cost_per_ride_variance = actual_cost_per_ride - target_cost_per_ride
            cost_per_ride_variance_pct = (cost_per_ride_variance / target_cost_per_ride) * 100

            variances.append(
                {
                    "metric": "cost_per_ride",
                    "target": round(target_cost_per_ride, 2),
                    "actual": round(actual_cost_per_ride, 2),
                    "variance": round(cost_per_ride_variance, 2),
                    "variance_percentage": round(cost_per_ride_variance_pct, 1),
                    "status": "favorable" if cost_per_ride_variance < 0 else "unfavorable",
                }
            )

        # Margin percentage variance
        target_margin = budget.get("target_margin_percentage", 0) * 100
        actual_margin = profitability["margin_percentage"]

        if target_margin > 0:
            margin_variance = actual_margin - target_margin
            margin_variance_pct = (margin_variance / target_margin) * 100

            variances.append(
                {
                    "metric": "margin_percentage",
                    "target": round(target_margin, 1),
                    "actual": round(actual_margin, 1),
                    "variance": round(margin_variance, 1),
                    "variance_percentage": round(margin_variance_pct, 1),
                    "status": "favorable" if margin_variance > 0 else "unfavorable",
                }
            )

        # Calculate overall variance score
        unfavorable_count = sum(1 for v in variances if v["status"] == "unfavorable")
        total_variance = sum(abs(v["variance_percentage"]) for v in variances)
        avg_variance = total_variance / len(variances) if variances else 0

        overall_status = "on_target"
        if avg_variance > 10:
            overall_status = "significant_variance"
        elif avg_variance > 5:
            overall_status = "minor_variance"

        return {
            "variances": variances,
            "unfavorable_variances": unfavorable_count,
            "favorable_variances": len(variances) - unfavorable_count,
            "overall_variance_percentage": round(avg_variance, 1),
            "overall_status": overall_status,
        }

    def _generate_cost_recommendations(
        self,
        cost_breakdown: Dict[str, Any],
        efficiency_metrics: Dict[str, Any],
        variance_analysis: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Generate cost optimization recommendations
        """
        recommendations = []

        # Analyze fuel efficiency
        fuel_efficiency = cost_breakdown.get("fuel_efficiency_km_per_liter", 0)
        if fuel_efficiency < 10:
            recommendations.append(
                {
                    "category": "fuel_efficiency",
                    "priority": "high",
                    "issue": f"Low fuel efficiency at {fuel_efficiency:.1f} km/L",
                    "recommendation": "Implement driver training on eco-driving techniques",
                    "potential_savings_percentage": 10,
                    "estimated_annual_savings": round(cost_breakdown["fuel_costs"] * 0.10 * 12, 2),
                }
            )

        # Analyze driver utilization
        utilization = efficiency_metrics.get("driver_utilization_rate", 0)
        if utilization < 0.6:
            recommendations.append(
                {
                    "category": "driver_utilization",
                    "priority": "high",
                    "issue": f"Low driver utilization at {utilization*100:.1f}%",
                    "recommendation": "Optimize driver scheduling and positioning to increase utilization",
                    "potential_savings_percentage": 15,
                    "estimated_annual_savings": round(cost_breakdown["total_costs"] * 0.15 * 12, 2),
                }
            )

        # Analyze cost per ride
        cost_per_ride = efficiency_metrics.get("cost_per_ride", 0)
        if cost_per_ride > 30:
            recommendations.append(
                {
                    "category": "ride_efficiency",
                    "priority": "medium",
                    "issue": f"High cost per ride at ${cost_per_ride:.2f}",
                    "recommendation": "Implement route optimization to reduce empty miles and increase rides per driver",
                    "potential_savings_percentage": 8,
                    "estimated_annual_savings": round(cost_breakdown["total_costs"] * 0.08 * 12, 2),
                }
            )

        # Analyze maintenance costs
        maintenance_pct = cost_breakdown["cost_percentages"].get("maintenance", 0)
        if maintenance_pct > 10:
            recommendations.append(
                {
                    "category": "maintenance",
                    "priority": "medium",
                    "issue": f"High maintenance costs at {maintenance_pct:.1f}% of total",
                    "recommendation": "Implement preventive maintenance program to reduce reactive repairs",
                    "potential_savings_percentage": 12,
                    "estimated_annual_savings": round(
                        cost_breakdown["maintenance_costs"] * 0.12 * 12, 2
                    ),
                }
            )

        # Analyze unfavorable variances
        for variance in variance_analysis.get("variances", []):
            if variance["status"] == "unfavorable" and abs(variance["variance_percentage"]) > 10:
                recommendations.append(
                    {
                        "category": "budget_variance",
                        "priority": "high",
                        "issue": f"{variance['metric']} is {variance['variance_percentage']:.1f}% over budget",
                        "recommendation": f"Investigate root causes of {variance['metric']} variance and implement corrective actions",
                        "potential_savings_percentage": min(
                            abs(variance["variance_percentage"]), 20
                        ),
                        "target_value": variance["target"],
                    }
                )

        # Sort by priority and potential savings
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(
            key=lambda x: (
                priority_order.get(x["priority"], 3),
                -x.get("potential_savings_percentage", 0),
            )
        )

        return recommendations

    def get_input_schema(self) -> Dict[str, Any]:
        """Return input schema for cost calculation"""
        return {
            "type": "object",
            "required": ["ride_data", "cost_inputs"],
            "properties": {
                "ride_data": {
                    "type": "object",
                    "description": "Ride statistics and operational data",
                },
                "cost_inputs": {"type": "object", "description": "Cost parameters and rates"},
                "budget": {"type": "object", "description": "Budget targets for variance analysis"},
            },
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """Return output schema"""
        return {
            "type": "object",
            "properties": {
                "cost_breakdown": {"type": "object"},
                "efficiency_metrics": {"type": "object"},
                "profitability_analysis": {"type": "object"},
                "variance_analysis": {"type": "object"},
                "recommendations": {"type": "array"},
            },
        }


def create_calculate_transportation_costs_logistics_agent() -> (
    CalculateTransportationCostsLogisticsAgent
):
    """Factory function to create CalculateTransportationCostsLogisticsAgent"""
    config = CalculateTransportationCostsLogisticsAgentConfig()
    return CalculateTransportationCostsLogisticsAgent(config)
