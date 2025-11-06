"""
ManageVehicleFleetAssetAgent - APQC 9.3.1
Manage Vehicle Fleet Assets and Lifecycle
APQC ID: apqc_9_3_m1v2f3l4

This agent manages vehicle fleet operations including maintenance scheduling,
lifecycle optimization, depreciation tracking, and utilization analysis.
"""

import os
import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

from library.core.base_agent import BaseAgent
from library.core.protocols import ProtocolMixin


@dataclass
class ManageVehicleFleetAssetAgentConfig:
    apqc_agent_id: str = "apqc_9_3_m1v2f3l4"
    apqc_process_id: str = "9.3.1"
    agent_name: str = "manage_vehicle_fleet_asset_agent"
    agent_type: str = "operational"
    version: str = "1.0.0"


class ManageVehicleFleetAssetAgent(BaseAgent, ProtocolMixin):
    """
    APQC 9.3.1 - Manage Vehicle Fleet

    Skills:
    - maintenance_planning: 0.91 (predictive maintenance)
    - lifecycle_optimization: 0.88 (replacement timing)
    - depreciation_modeling: 0.86 (asset value tracking)
    - utilization_tracking: 0.84 (efficiency metrics)

    Use Cases:
    - Schedule preventive maintenance
    - Optimize vehicle replacement cycles
    - Track depreciation and asset values
    - Analyze vehicle utilization
    """

    VERSION = "1.0.0"
    APQC_PROCESS_ID = "9.3.1"

    def __init__(self, config: ManageVehicleFleetAssetAgentConfig):
        super().__init__(
            agent_id=config.apqc_agent_id, agent_type=config.agent_type, version=config.version
        )
        self.config = config
        self.skills = {
            "maintenance_planning": 0.91,
            "lifecycle_optimization": 0.88,
            "depreciation_modeling": 0.86,
            "utilization_tracking": 0.84,
        }

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Manage vehicle fleet operations

        Input:
        {
            "vehicle": {
                "vehicle_id": "VEH12345",
                "make": "Toyota",
                "model": "Camry",
                "year": 2021,
                "purchase_date": "2021-03-15",
                "purchase_price": 28000,
                "current_mileage_km": 45000,
                "last_maintenance_km": 42000,
                "last_maintenance_date": "2025-09-15"
            },
            "usage_data": {
                "rides_last_30_days": 180,
                "km_driven_last_30_days": 3600,
                "revenue_last_30_days": 5400,
                "idle_hours_last_30_days": 120,
                "active_hours_last_30_days": 200
            },
            "maintenance_history": [
                {"date": "2025-09-15", "type": "oil_change", "cost": 60},
                {"date": "2025-06-10", "type": "tire_rotation", "cost": 80},
                {"date": "2025-03-20", "type": "brake_service", "cost": 250}
            ],
            "fleet_standards": {
                "maintenance_interval_km": 5000,
                "max_vehicle_age_years": 10,
                "target_utilization_rate": 0.65,
                "replacement_threshold_km": 250000
            }
        }
        """
        vehicle = input_data.get("vehicle", {})
        usage = input_data.get("usage_data", {})
        maint_history = input_data.get("maintenance_history", [])
        standards = input_data.get("fleet_standards", {})

        # Schedule maintenance
        maintenance_plan = self._plan_maintenance(vehicle, usage, standards)

        # Calculate depreciation
        depreciation_analysis = self._calculate_depreciation(vehicle)

        # Analyze utilization
        utilization_metrics = self._analyze_utilization(usage, standards)

        # Assess lifecycle status
        lifecycle_assessment = self._assess_lifecycle(
            vehicle, usage, standards, depreciation_analysis
        )

        # Calculate total cost of ownership
        tco_analysis = self._calculate_tco(vehicle, usage, maint_history, depreciation_analysis)

        # Generate fleet recommendations
        recommendations = self._generate_fleet_recommendations(
            maintenance_plan, lifecycle_assessment, utilization_metrics, tco_analysis
        )

        return {
            "status": "completed",
            "apqc_process_id": self.APQC_PROCESS_ID,
            "timestamp": datetime.now().isoformat(),
            "output": {
                "vehicle_id": vehicle.get("vehicle_id"),
                "maintenance_plan": maintenance_plan,
                "depreciation_analysis": depreciation_analysis,
                "utilization_metrics": utilization_metrics,
                "lifecycle_assessment": lifecycle_assessment,
                "tco_analysis": tco_analysis,
                "recommendations": recommendations,
                "summary": {
                    "next_maintenance_due_km": maintenance_plan["next_service"]["due_at_km"],
                    "current_value": depreciation_analysis["current_value"],
                    "utilization_rate": utilization_metrics["utilization_rate"],
                    "lifecycle_stage": lifecycle_assessment["stage"],
                },
            },
        }

    def _plan_maintenance(self, vehicle: Dict, usage: Dict, standards: Dict) -> Dict[str, Any]:
        """Plan preventive maintenance schedule"""
        current_km = vehicle.get("current_mileage_km", 0)
        last_maint_km = vehicle.get("last_maintenance_km", 0)
        maint_interval = standards.get("maintenance_interval_km", 5000)

        # Calculate km since last maintenance
        km_since_last = current_km - last_maint_km

        # Calculate km until next maintenance
        km_until_next = maint_interval - km_since_last

        # Estimate days until next based on usage
        km_per_day = usage.get("km_driven_last_30_days", 0) / 30
        days_until_next = (km_until_next / km_per_day) if km_per_day > 0 else 999

        # Determine urgency
        if km_until_next <= 0:
            urgency = "overdue"
            priority = "critical"
        elif km_until_next <= 500:
            urgency = "due_soon"
            priority = "high"
        elif days_until_next <= 7:
            urgency = "due_within_week"
            priority = "medium"
        else:
            urgency = "scheduled"
            priority = "low"

        # Recommended service items
        service_items = []
        if km_since_last >= maint_interval or urgency == "overdue":
            service_items.extend(
                [
                    {"item": "Oil and filter change", "estimated_cost": 60, "required": True},
                    {"item": "Tire rotation", "estimated_cost": 40, "required": True},
                    {"item": "Fluid level check", "estimated_cost": 0, "required": True},
                    {"item": "Brake inspection", "estimated_cost": 0, "required": True},
                ]
            )

        # Mileage-based additional services
        if current_km >= 60000 and current_km % 30000 < maint_interval:
            service_items.append(
                {"item": "Transmission service", "estimated_cost": 150, "required": False}
            )

        if current_km >= 80000 and current_km % 40000 < maint_interval:
            service_items.append(
                {"item": "Brake pad replacement", "estimated_cost": 250, "required": False}
            )

        total_estimated_cost = sum(item["estimated_cost"] for item in service_items)

        return {
            "next_service": {
                "due_at_km": last_maint_km + maint_interval,
                "km_remaining": km_until_next,
                "estimated_days": round(days_until_next, 0),
                "urgency": urgency,
                "priority": priority,
            },
            "service_items": service_items,
            "total_estimated_cost": total_estimated_cost,
            "maintenance_interval_km": maint_interval,
            "km_since_last_service": km_since_last,
        }

    def _calculate_depreciation(self, vehicle: Dict) -> Dict[str, Any]:
        """Calculate vehicle depreciation and current value"""
        purchase_price = vehicle.get("purchase_price", 0)
        purchase_date_str = vehicle.get("purchase_date")
        current_km = vehicle.get("current_mileage_km", 0)
        year = vehicle.get("year", 2020)

        # Calculate vehicle age
        try:
            purchase_date = datetime.fromisoformat(purchase_date_str)
            age_years = (datetime.now() - purchase_date).days / 365.25
        except:
            age_years = datetime.now().year - year

        # Depreciation model (declining balance)
        # Year 1: 20%, Year 2: 15%, Year 3: 10%, Year 4+: 8% per year
        depreciation_rates = [0.20, 0.15, 0.10, 0.08, 0.08, 0.08, 0.08, 0.08, 0.08, 0.08]

        remaining_value = purchase_price
        for i in range(min(int(age_years), len(depreciation_rates))):
            remaining_value *= 1 - depreciation_rates[i]

        # Additional depreciation for high mileage
        # Every 10k km over 100k reduces value by 2%
        if current_km > 100000:
            excess_km = current_km - 100000
            mileage_depreciation = (excess_km / 10000) * 0.02
            remaining_value *= 1 - mileage_depreciation

        current_value = max(purchase_price * 0.10, remaining_value)  # Floor at 10% of original

        total_depreciation = purchase_price - current_value
        depreciation_percentage = (
            (total_depreciation / purchase_price * 100) if purchase_price > 0 else 0
        )

        # Annual depreciation rate
        annual_depreciation = total_depreciation / age_years if age_years > 0 else 0

        return {
            "purchase_price": purchase_price,
            "current_value": round(current_value, 2),
            "total_depreciation": round(total_depreciation, 2),
            "depreciation_percentage": round(depreciation_percentage, 1),
            "annual_depreciation": round(annual_depreciation, 2),
            "age_years": round(age_years, 1),
            "mileage_km": current_km,
        }

    def _analyze_utilization(self, usage: Dict, standards: Dict) -> Dict[str, Any]:
        """Analyze vehicle utilization metrics"""
        active_hours = usage.get("active_hours_last_30_days", 0)
        idle_hours = usage.get("idle_hours_last_30_days", 0)
        total_hours = active_hours + idle_hours

        rides = usage.get("rides_last_30_days", 0)
        km_driven = usage.get("km_driven_last_30_days", 0)
        revenue = usage.get("revenue_last_30_days", 0)

        # Utilization rate
        available_hours_per_month = 30 * 12  # Assume 12-hour availability per day
        utilization_rate = (
            total_hours / available_hours_per_month if available_hours_per_month > 0 else 0
        )

        # Active utilization (excluding idle time)
        active_utilization = (
            active_hours / available_hours_per_month if available_hours_per_month > 0 else 0
        )

        # Performance metrics
        revenue_per_hour = revenue / active_hours if active_hours > 0 else 0
        revenue_per_km = revenue / km_driven if km_driven > 0 else 0
        km_per_hour = km_driven / active_hours if active_hours > 0 else 0
        rides_per_day = rides / 30

        # Compare to target
        target_util = standards.get("target_utilization_rate", 0.65)
        utilization_vs_target = utilization_rate - target_util
        performance_status = (
            "excellent"
            if utilization_rate >= target_util * 1.1
            else (
                "good"
                if utilization_rate >= target_util
                else "below_target" if utilization_rate >= target_util * 0.8 else "poor"
            )
        )

        return {
            "utilization_rate": round(utilization_rate, 3),
            "active_utilization_rate": round(active_utilization, 3),
            "target_utilization": target_util,
            "utilization_vs_target": round(utilization_vs_target, 3),
            "performance_status": performance_status,
            "metrics": {
                "active_hours": active_hours,
                "idle_hours": idle_hours,
                "total_hours": total_hours,
                "rides_per_day": round(rides_per_day, 1),
                "km_per_hour": round(km_per_hour, 1),
                "revenue_per_hour": round(revenue_per_hour, 2),
                "revenue_per_km": round(revenue_per_km, 2),
            },
        }

    def _assess_lifecycle(
        self, vehicle: Dict, usage: Dict, standards: Dict, depreciation: Dict
    ) -> Dict[str, Any]:
        """Assess vehicle lifecycle stage and replacement timing"""
        age_years = depreciation["age_years"]
        current_km = vehicle.get("current_mileage_km", 0)
        max_age = standards.get("max_vehicle_age_years", 10)
        replacement_km = standards.get("replacement_threshold_km", 250000)

        # Calculate remaining useful life
        years_remaining = max_age - age_years
        km_remaining = replacement_km - current_km

        # Estimate months until replacement
        km_per_month = usage.get("km_driven_last_30_days", 0)
        months_until_replacement_km = (km_remaining / km_per_month) if km_per_month > 0 else 999
        months_until_replacement_age = years_remaining * 12

        months_until_replacement = min(months_until_replacement_km, months_until_replacement_age)

        # Determine lifecycle stage
        if age_years <= 2 or current_km <= 50000:
            stage = "new"
        elif age_years <= 5 or current_km <= 150000:
            stage = "prime"
        elif age_years <= 8 or current_km <= 200000:
            stage = "mature"
        else:
            stage = "aging"

        # Replacement recommendation
        if months_until_replacement <= 6:
            replacement_urgency = "immediate"
            recommendation = "Schedule replacement within 6 months"
        elif months_until_replacement <= 12:
            replacement_urgency = "plan"
            recommendation = "Begin planning replacement within next year"
        elif months_until_replacement <= 24:
            replacement_urgency = "monitor"
            recommendation = "Monitor condition and plan for future replacement"
        else:
            replacement_urgency = "none"
            recommendation = "Vehicle in good lifecycle position"

        return {
            "stage": stage,
            "age_years": age_years,
            "mileage_km": current_km,
            "years_remaining": round(years_remaining, 1),
            "km_remaining": round(km_remaining, 0),
            "months_until_replacement": round(months_until_replacement, 0),
            "replacement_urgency": replacement_urgency,
            "recommendation": recommendation,
        }

    def _calculate_tco(
        self, vehicle: Dict, usage: Dict, maintenance: List[Dict], depreciation: Dict
    ) -> Dict[str, Any]:
        """Calculate total cost of ownership"""
        age_years = depreciation["age_years"]
        current_km = vehicle.get("current_mileage_km", 0)

        # Depreciation cost
        depreciation_cost = depreciation["total_depreciation"]

        # Maintenance costs
        total_maintenance_cost = sum(m.get("cost", 0) for m in maintenance)

        # Estimate fuel costs (assume $1.50/L, 12 km/L efficiency)
        fuel_cost_per_km = 1.50 / 12
        total_fuel_cost = current_km * fuel_cost_per_km

        # Insurance (estimate $2000/year)
        insurance_per_year = 2000
        total_insurance = insurance_per_year * age_years

        # Total TCO
        total_tco = depreciation_cost + total_maintenance_cost + total_fuel_cost + total_insurance

        # TCO per km
        tco_per_km = total_tco / current_km if current_km > 0 else 0

        # Monthly TCO
        monthly_tco = total_tco / (age_years * 12) if age_years > 0 else 0

        # Revenue metrics
        monthly_revenue = usage.get("revenue_last_30_days", 0)
        monthly_profit = monthly_revenue - monthly_tco

        return {
            "total_cost_of_ownership": round(total_tco, 2),
            "cost_breakdown": {
                "depreciation": round(depreciation_cost, 2),
                "maintenance": round(total_maintenance_cost, 2),
                "fuel": round(total_fuel_cost, 2),
                "insurance": round(total_insurance, 2),
            },
            "cost_per_km": round(tco_per_km, 2),
            "monthly_tco": round(monthly_tco, 2),
            "monthly_revenue": monthly_revenue,
            "monthly_profit": round(monthly_profit, 2),
            "roi_positive": monthly_profit > 0,
        }

    def _generate_fleet_recommendations(
        self, maintenance: Dict, lifecycle: Dict, utilization: Dict, tco: Dict
    ) -> List[Dict[str, Any]]:
        """Generate fleet management recommendations"""
        recommendations = []

        # Maintenance recommendations
        if maintenance["next_service"]["urgency"] in ["overdue", "due_soon"]:
            recommendations.append(
                {
                    "category": "maintenance",
                    "priority": maintenance["next_service"]["priority"],
                    "action": "Schedule maintenance service",
                    "reason": f"Service {maintenance['next_service']['urgency']}",
                    "estimated_cost": maintenance["total_estimated_cost"],
                    "due_in_days": maintenance["next_service"]["estimated_days"],
                }
            )

        # Utilization recommendations
        if utilization["performance_status"] == "poor":
            recommendations.append(
                {
                    "category": "utilization",
                    "priority": "high",
                    "action": "Improve vehicle utilization",
                    "reason": f"Utilization at {utilization['utilization_rate']:.0%}, target is {utilization['target_utilization']:.0%}",
                    "expected_impact": "Increase revenue per vehicle by 20-30%",
                    "suggestions": [
                        "Increase driver availability",
                        "Optimize positioning",
                        "Reduce idle time",
                    ],
                }
            )

        # Lifecycle recommendations
        if lifecycle["replacement_urgency"] in ["immediate", "plan"]:
            recommendations.append(
                {
                    "category": "lifecycle",
                    "priority": (
                        "high" if lifecycle["replacement_urgency"] == "immediate" else "medium"
                    ),
                    "action": lifecycle["recommendation"],
                    "reason": f"Vehicle in {lifecycle['stage']} stage",
                    "timeline_months": lifecycle["months_until_replacement"],
                }
            )

        # Profitability recommendations
        if tco["monthly_profit"] < 0:
            recommendations.append(
                {
                    "category": "profitability",
                    "priority": "critical",
                    "action": "Review vehicle profitability",
                    "reason": f"Monthly loss of ${abs(tco['monthly_profit']):.2f}",
                    "options": ["Increase utilization", "Reduce costs", "Consider retirement"],
                }
            )

        return recommendations

    def get_input_schema(self) -> Dict[str, Any]:
        """Return input schema"""
        return {
            "type": "object",
            "required": ["vehicle", "usage_data"],
            "properties": {
                "vehicle": {"type": "object"},
                "usage_data": {"type": "object"},
                "maintenance_history": {"type": "array"},
                "fleet_standards": {"type": "object"},
            },
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """Return output schema"""
        return {
            "type": "object",
            "properties": {
                "maintenance_plan": {"type": "object"},
                "depreciation_analysis": {"type": "object"},
                "utilization_metrics": {"type": "object"},
                "lifecycle_assessment": {"type": "object"},
                "tco_analysis": {"type": "object"},
                "recommendations": {"type": "array"},
            },
        }


def create_manage_vehicle_fleet_asset_agent() -> ManageVehicleFleetAssetAgent:
    """Factory function to create ManageVehicleFleetAssetAgent"""
    config = ManageVehicleFleetAssetAgentConfig()
    return ManageVehicleFleetAssetAgent(config)
