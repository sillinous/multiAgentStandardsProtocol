"""
Intelligent Supply Chain Operations Agent - Example Implementation

Demonstrates AI-powered supply chain and operations capabilities:
- Demand forecasting with AI-driven predictions
- Inventory optimization across locations
- Supplier risk assessment and monitoring
- Logistics route optimization
- Quality control anomaly detection
- Supply chain disruption prediction

This is a reference implementation showing best practices for
building AI-powered APQC-compliant operations agents.

APQC Categories:
- 4.0 Deliver Physical Products
- 4.1 Plan for and Acquire Necessary Resources
- 4.2 Procure Materials and Services
- 4.3 Produce/Manufacture/Deliver Product
- 4.4 Manage Logistics and Warehousing
"""

import asyncio
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import json


class SupplyChainRiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class InventoryStatus(Enum):
    OPTIMAL = "optimal"
    LOW = "low_stock"
    CRITICAL = "critical_stock"
    OVERSTOCK = "overstock"
    OUT_OF_STOCK = "out_of_stock"


@dataclass
class SupplyChainConfig:
    """Configuration for the Supply Chain Operations Agent"""
    agent_id: str = "intelligent_supply_chain_001"
    agent_name: str = "Intelligent Supply Chain Operations Agent"

    # AI Configuration
    ai_provider: str = "auto"  # auto, openai, anthropic, ollama, mock
    confidence_threshold: float = 0.75
    max_analysis_depth: int = 3

    # Operational Modes
    enable_demand_forecasting: bool = True
    enable_inventory_optimization: bool = True
    enable_supplier_risk_monitoring: bool = True
    enable_logistics_optimization: bool = True
    enable_quality_monitoring: bool = True
    enable_disruption_prediction: bool = True

    # Thresholds
    safety_stock_days: int = 14
    reorder_point_multiplier: float = 1.5
    supplier_risk_threshold: float = 0.6
    quality_anomaly_sensitivity: float = 0.85
    forecast_horizon_days: int = 90

    # Optimization Parameters
    optimize_for: str = "cost"  # cost, speed, quality, balanced


class IntelligentSupplyChainAgent:
    """
    AI-Powered Supply Chain Operations Agent

    Capabilities:
    - Demand forecasting with seasonal adjustments
    - Multi-location inventory optimization
    - Supplier risk scoring and monitoring
    - Route and logistics optimization
    - Quality control with anomaly detection
    - Supply chain disruption early warning

    Integration:
    - Uses OperationsProcessor from smart_processing
    - Integrates with AIService for predictive analytics
    - APQC Process: 4.0 - Deliver Physical Products
    """

    APQC_CATEGORY_ID = "4.0"
    APQC_PROCESS_IDS = ["4.1", "4.2", "4.3", "4.4"]

    def __init__(self, config: Optional[SupplyChainConfig] = None):
        self.config = config or SupplyChainConfig()
        self.forecast_cache = {}
        self.supplier_scores = {}
        self.state = {
            "forecasts_generated": 0,
            "optimizations_performed": 0,
            "alerts_generated": 0,
            "disruptions_predicted": 0,
            "last_analysis": None
        }

    async def analyze_supply_chain(self, supply_chain_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive AI-powered supply chain analysis

        Args:
            supply_chain_data: Dict containing:
                - inventory: Current inventory levels by location/SKU
                - suppliers: Supplier information and performance
                - orders: Open orders and historical demand
                - logistics: Shipping and routing data
                - quality_metrics: Production quality data

        Returns:
            Comprehensive analysis with AI-driven insights and recommendations
        """
        from superstandard.services.smart_processing import get_processor
        from superstandard.services.ai_service import get_ai_service

        start_time = datetime.now()

        # Get domain processor and AI service
        processor = get_processor("operations")
        ai_service = get_ai_service()

        results = {
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "ai_powered": True,
            "apqc_category": self.APQC_CATEGORY_ID,
            "agent_id": self.config.agent_id,
            "components": {}
        }

        # Step 1: Demand Forecasting
        if self.config.enable_demand_forecasting:
            forecast = await self._forecast_demand(
                supply_chain_data.get("orders", {}),
                ai_service
            )
            results["components"]["demand_forecast"] = forecast

        # Step 2: Inventory Optimization
        if self.config.enable_inventory_optimization:
            inventory_analysis = await self._optimize_inventory(
                supply_chain_data.get("inventory", {}),
                results["components"].get("demand_forecast", {}),
                processor
            )
            results["components"]["inventory_optimization"] = inventory_analysis

        # Step 3: Supplier Risk Assessment
        if self.config.enable_supplier_risk_monitoring:
            supplier_risk = await self._assess_supplier_risk(
                supply_chain_data.get("suppliers", []),
                ai_service
            )
            results["components"]["supplier_risk"] = supplier_risk

        # Step 4: Logistics Optimization
        if self.config.enable_logistics_optimization:
            logistics = await self._optimize_logistics(
                supply_chain_data.get("logistics", {}),
                processor
            )
            results["components"]["logistics_optimization"] = logistics

        # Step 5: Quality Monitoring
        if self.config.enable_quality_monitoring:
            quality = await self._monitor_quality(
                supply_chain_data.get("quality_metrics", {}),
                processor
            )
            results["components"]["quality_monitoring"] = quality

        # Step 6: Disruption Prediction
        if self.config.enable_disruption_prediction:
            disruptions = await self._predict_disruptions(
                supply_chain_data,
                ai_service
            )
            results["components"]["disruption_prediction"] = disruptions

        # Generate consolidated recommendations
        results["recommendations"] = await self._generate_recommendations(results, ai_service)

        # Update state
        self.state["forecasts_generated"] += 1
        self.state["last_analysis"] = datetime.now().isoformat()

        # Calculate processing time
        results["processing_time_ms"] = (datetime.now() - start_time).total_seconds() * 1000

        return results

    async def _forecast_demand(
        self,
        order_data: Dict[str, Any],
        ai_service
    ) -> Dict[str, Any]:
        """Generate AI-powered demand forecast"""

        historical_demand = order_data.get("historical", [])
        seasonality = order_data.get("seasonality_factors", {})
        market_trends = order_data.get("market_trends", {})

        # AI-powered demand prediction
        ai_forecast = await ai_service.analyze(
            prompt=f"""Analyze demand patterns and generate forecast:

            Historical Data Points: {len(historical_demand)}
            Seasonality Factors: {json.dumps(seasonality)}
            Market Trends: {json.dumps(market_trends)}
            Forecast Horizon: {self.config.forecast_horizon_days} days

            Provide:
            1. Expected demand trend (increase/stable/decrease)
            2. Confidence level (0-1)
            3. Key factors affecting demand
            4. Seasonal adjustments needed
            5. Risk factors for forecast accuracy
            """,
            data={"orders": order_data}
        )

        return {
            "forecast_generated": datetime.now().isoformat(),
            "horizon_days": self.config.forecast_horizon_days,
            "ai_prediction": ai_forecast,
            "methodology": "ai_enhanced_time_series",
            "confidence": ai_forecast.get("confidence", 0.7),
            "next_period_estimate": ai_forecast.get("estimate", {}),
            "risk_factors": ai_forecast.get("risk_factors", [])
        }

    async def _optimize_inventory(
        self,
        inventory_data: Dict[str, Any],
        demand_forecast: Dict[str, Any],
        processor
    ) -> Dict[str, Any]:
        """Optimize inventory levels across locations"""

        current_levels = inventory_data.get("levels", {})
        locations = inventory_data.get("locations", [])
        lead_times = inventory_data.get("lead_times", {})

        # Use operations processor for optimization
        optimization_result = await processor.process(
            {
                "inventory": current_levels,
                "demand_forecast": demand_forecast,
                "lead_times": lead_times,
                "safety_stock_days": self.config.safety_stock_days
            },
            task_type="inventory_optimization"
        )

        # Classify inventory status by SKU
        inventory_status = {}
        recommendations = []

        for sku, data in current_levels.items():
            level = data.get("quantity", 0)
            avg_daily_demand = data.get("avg_daily_demand", 10)
            days_of_stock = level / avg_daily_demand if avg_daily_demand > 0 else 999

            if level == 0:
                status = InventoryStatus.OUT_OF_STOCK
                recommendations.append({
                    "sku": sku,
                    "action": "urgent_reorder",
                    "priority": "critical"
                })
            elif days_of_stock < 7:
                status = InventoryStatus.CRITICAL
                recommendations.append({
                    "sku": sku,
                    "action": "expedite_reorder",
                    "priority": "high"
                })
            elif days_of_stock < self.config.safety_stock_days:
                status = InventoryStatus.LOW
                recommendations.append({
                    "sku": sku,
                    "action": "standard_reorder",
                    "priority": "medium"
                })
            elif days_of_stock > 60:
                status = InventoryStatus.OVERSTOCK
                recommendations.append({
                    "sku": sku,
                    "action": "reduce_orders",
                    "priority": "low"
                })
            else:
                status = InventoryStatus.OPTIMAL

            inventory_status[sku] = {
                "status": status.value,
                "days_of_stock": round(days_of_stock, 1),
                "quantity": level
            }

        return {
            "optimization_performed": datetime.now().isoformat(),
            "total_skus_analyzed": len(current_levels),
            "inventory_status": inventory_status,
            "recommendations": recommendations,
            "critical_items": len([r for r in recommendations if r["priority"] == "critical"]),
            "high_priority_items": len([r for r in recommendations if r["priority"] == "high"]),
            "reorder_suggestions": optimization_result.get("result", {}).get("suggestions", [])
        }

    async def _assess_supplier_risk(
        self,
        suppliers: List[Dict[str, Any]],
        ai_service
    ) -> Dict[str, Any]:
        """AI-powered supplier risk assessment"""

        supplier_assessments = []

        for supplier in suppliers[:10]:  # Limit for demo
            supplier_id = supplier.get("id", "unknown")
            performance = supplier.get("performance_metrics", {})
            financials = supplier.get("financial_health", {})
            location = supplier.get("location", {})

            # AI risk analysis
            risk_analysis = await ai_service.assess_risk(
                scenario={
                    "supplier_id": supplier_id,
                    "on_time_delivery_rate": performance.get("on_time_rate", 0.9),
                    "quality_defect_rate": performance.get("defect_rate", 0.02),
                    "financial_stability": financials.get("stability_score", 0.7),
                    "geographic_risk": location.get("risk_factors", []),
                    "single_source": supplier.get("is_single_source", False)
                },
                risk_categories=["operational", "financial", "geographic", "quality"]
            )

            # Calculate composite risk score
            risk_score = risk_analysis.get("overall_risk_score", 0.5)

            if risk_score >= 0.8:
                risk_level = SupplyChainRiskLevel.CRITICAL
            elif risk_score >= 0.6:
                risk_level = SupplyChainRiskLevel.HIGH
            elif risk_score >= 0.4:
                risk_level = SupplyChainRiskLevel.MEDIUM
            else:
                risk_level = SupplyChainRiskLevel.LOW

            supplier_assessments.append({
                "supplier_id": supplier_id,
                "supplier_name": supplier.get("name", supplier_id),
                "risk_score": round(risk_score, 2),
                "risk_level": risk_level.value,
                "risk_factors": risk_analysis.get("key_concerns", []),
                "mitigations": risk_analysis.get("mitigations", [])
            })

            # Cache for monitoring
            self.supplier_scores[supplier_id] = risk_score

        # Sort by risk (highest first)
        supplier_assessments.sort(key=lambda x: x["risk_score"], reverse=True)

        # Count alerts
        alerts = [s for s in supplier_assessments if s["risk_level"] in ["high", "critical"]]
        if alerts:
            self.state["alerts_generated"] += len(alerts)

        return {
            "assessment_date": datetime.now().isoformat(),
            "suppliers_assessed": len(supplier_assessments),
            "assessments": supplier_assessments,
            "high_risk_suppliers": len(alerts),
            "critical_alerts": [s for s in alerts if s["risk_level"] == "critical"],
            "average_risk_score": round(
                sum(s["risk_score"] for s in supplier_assessments) / len(supplier_assessments)
                if supplier_assessments else 0,
                2
            )
        }

    async def _optimize_logistics(
        self,
        logistics_data: Dict[str, Any],
        processor
    ) -> Dict[str, Any]:
        """Optimize logistics and routing"""

        shipments = logistics_data.get("pending_shipments", [])
        warehouses = logistics_data.get("warehouses", [])
        carriers = logistics_data.get("carriers", [])

        # Use processor for logistics planning
        logistics_plan = await processor.plan_logistics({
            "shipments": shipments,
            "warehouses": warehouses,
            "carriers": carriers,
            "optimize_for": self.config.optimize_for
        })

        # Calculate optimization metrics
        total_shipments = len(shipments)
        consolidation_opportunities = logistics_plan.get("logistics_plan", {}).get(
            "consolidation_opportunities", []
        )

        return {
            "optimization_date": datetime.now().isoformat(),
            "total_pending_shipments": total_shipments,
            "warehouses_active": len(warehouses),
            "carriers_available": len(carriers),
            "optimization_strategy": self.config.optimize_for,
            "recommended_routes": logistics_plan.get("logistics_plan", {}).get("routes", []),
            "consolidation_opportunities": len(consolidation_opportunities),
            "estimated_savings": logistics_plan.get("logistics_plan", {}).get("savings", {}),
            "ai_recommendations": logistics_plan.get("logistics_plan", {}).get("ai_suggestions", [])
        }

    async def _monitor_quality(
        self,
        quality_data: Dict[str, Any],
        processor
    ) -> Dict[str, Any]:
        """Monitor quality metrics and detect anomalies"""

        defect_rates = quality_data.get("defect_rates", {})
        inspection_results = quality_data.get("inspections", [])
        production_metrics = quality_data.get("production", {})

        # Use processor for quality assessment
        quality_assessment = await processor.monitor_quality({
            "defect_rates": defect_rates,
            "inspections": inspection_results,
            "production_metrics": production_metrics,
            "sensitivity": self.config.quality_anomaly_sensitivity
        })

        # Identify anomalies
        anomalies = []
        baseline_defect_rate = quality_data.get("baseline_defect_rate", 0.02)

        for product, rate in defect_rates.items():
            if rate > baseline_defect_rate * 2:  # More than 2x baseline
                anomalies.append({
                    "product": product,
                    "current_rate": rate,
                    "baseline_rate": baseline_defect_rate,
                    "severity": "high" if rate > baseline_defect_rate * 3 else "medium"
                })

        return {
            "monitoring_date": datetime.now().isoformat(),
            "products_monitored": len(defect_rates),
            "inspections_reviewed": len(inspection_results),
            "overall_quality_score": quality_assessment.get("quality_assessment", {}).get("score", 0.9),
            "anomalies_detected": len(anomalies),
            "anomaly_details": anomalies,
            "trends": quality_assessment.get("quality_assessment", {}).get("trends", {}),
            "recommendations": quality_assessment.get("quality_assessment", {}).get("recommendations", [])
        }

    async def _predict_disruptions(
        self,
        supply_chain_data: Dict[str, Any],
        ai_service
    ) -> Dict[str, Any]:
        """AI-powered supply chain disruption prediction"""

        # Gather risk signals
        supplier_risks = self.supplier_scores
        inventory_status = supply_chain_data.get("inventory", {})
        external_factors = supply_chain_data.get("external_factors", {})

        # AI disruption analysis
        disruption_analysis = await ai_service.analyze(
            prompt=f"""Analyze supply chain for potential disruptions:

            Supplier Risk Scores: {json.dumps(dict(list(supplier_risks.items())[:5]))}
            External Factors: {json.dumps(external_factors)}

            Identify:
            1. High-probability disruption scenarios
            2. Early warning indicators
            3. Potential impact severity
            4. Recommended preventive actions
            5. Contingency recommendations

            Focus on near-term (30-day) and medium-term (90-day) risks.
            """,
            data={"supply_chain_summary": supply_chain_data}
        )

        predictions = disruption_analysis.get("insights", [])

        # Track predictions
        if predictions:
            self.state["disruptions_predicted"] += len(predictions)

        return {
            "prediction_date": datetime.now().isoformat(),
            "analysis_horizon": "90_days",
            "disruption_scenarios": predictions,
            "early_warning_signals": disruption_analysis.get("warnings", []),
            "risk_score": disruption_analysis.get("risk_score", 0.3),
            "preventive_actions": disruption_analysis.get("preventive_actions", []),
            "contingency_plans": disruption_analysis.get("contingencies", [])
        }

    async def _generate_recommendations(
        self,
        analysis_results: Dict[str, Any],
        ai_service
    ) -> List[Dict[str, Any]]:
        """Generate consolidated AI-powered recommendations"""

        components = analysis_results.get("components", {})

        # Build context for AI recommendations
        context = {
            "inventory_critical_items": components.get("inventory_optimization", {}).get("critical_items", 0),
            "high_risk_suppliers": components.get("supplier_risk", {}).get("high_risk_suppliers", 0),
            "quality_anomalies": components.get("quality_monitoring", {}).get("anomalies_detected", 0),
            "disruption_risk": components.get("disruption_prediction", {}).get("risk_score", 0)
        }

        recommendations = await ai_service.generate_recommendations(
            context=context,
            constraints=["actionable", "prioritized", "specific"],
            max_recommendations=5
        )

        return [
            {
                "id": i + 1,
                "action": rec.get("action", ""),
                "priority": rec.get("priority", "medium"),
                "impact": rec.get("impact", "unknown"),
                "category": rec.get("category", "general"),
                "rationale": rec.get("rationale", "")
            }
            for i, rec in enumerate(recommendations)
        ]

    async def optimize_reorder_quantities(
        self,
        sku_list: List[str],
        constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate optimal reorder quantities for SKUs"""
        from superstandard.services.smart_processing import get_processor

        processor = get_processor("operations")

        results = await processor.process(
            {
                "skus": sku_list,
                "constraints": constraints,
                "optimization_target": self.config.optimize_for
            },
            task_type="reorder_optimization"
        )

        self.state["optimizations_performed"] += 1

        return {
            "optimization_date": datetime.now().isoformat(),
            "skus_optimized": len(sku_list),
            "strategy": self.config.optimize_for,
            "recommendations": results.get("result", {}),
            "total_order_value": results.get("result", {}).get("total_value", 0)
        }

    def get_state(self) -> Dict[str, Any]:
        """Get current agent state and statistics"""
        return {
            **self.state,
            "config": {
                "agent_id": self.config.agent_id,
                "agent_name": self.config.agent_name,
                "optimization_strategy": self.config.optimize_for,
                "forecast_horizon_days": self.config.forecast_horizon_days
            },
            "supplier_risk_cache_size": len(self.supplier_scores),
            "forecast_cache_size": len(self.forecast_cache)
        }


# =============================================================================
# Example Usage
# =============================================================================

async def demo_supply_chain_agent():
    """Demonstrate the Supply Chain Operations Agent"""

    print("=" * 60)
    print("Intelligent Supply Chain Operations Agent Demo")
    print("=" * 60)

    # Create agent with custom config
    config = SupplyChainConfig(
        agent_name="Demo Supply Chain Agent",
        optimize_for="balanced",
        forecast_horizon_days=60,
        safety_stock_days=10
    )

    agent = IntelligentSupplyChainAgent(config)

    # Sample supply chain data
    supply_chain_data = {
        "inventory": {
            "levels": {
                "SKU-001": {"quantity": 500, "avg_daily_demand": 50},
                "SKU-002": {"quantity": 100, "avg_daily_demand": 30},
                "SKU-003": {"quantity": 0, "avg_daily_demand": 20},
                "SKU-004": {"quantity": 2000, "avg_daily_demand": 25}
            },
            "locations": ["warehouse_east", "warehouse_west"],
            "lead_times": {"default": 7, "expedited": 3}
        },
        "suppliers": [
            {
                "id": "SUP-001",
                "name": "Premium Parts Co",
                "performance_metrics": {"on_time_rate": 0.95, "defect_rate": 0.01},
                "financial_health": {"stability_score": 0.85},
                "is_single_source": False
            },
            {
                "id": "SUP-002",
                "name": "Budget Materials Ltd",
                "performance_metrics": {"on_time_rate": 0.78, "defect_rate": 0.05},
                "financial_health": {"stability_score": 0.55},
                "is_single_source": True
            }
        ],
        "orders": {
            "historical": [100, 120, 115, 130, 140, 125, 150],
            "seasonality_factors": {"q4": 1.3, "q1": 0.9},
            "market_trends": {"growth": "moderate", "competition": "increasing"}
        },
        "logistics": {
            "pending_shipments": [
                {"id": "SHIP-001", "destination": "NY", "weight": 500},
                {"id": "SHIP-002", "destination": "LA", "weight": 300}
            ],
            "warehouses": ["warehouse_east", "warehouse_west"],
            "carriers": ["fedex", "ups", "freight_co"]
        },
        "quality_metrics": {
            "defect_rates": {"SKU-001": 0.01, "SKU-002": 0.08, "SKU-003": 0.02},
            "baseline_defect_rate": 0.02,
            "inspections": [{"date": "2025-01-01", "passed": 95, "failed": 5}]
        },
        "external_factors": {
            "weather_alerts": [],
            "geopolitical_risks": ["trade_policy_uncertainty"],
            "market_conditions": "stable"
        }
    }

    print("\n1. Running comprehensive supply chain analysis...")
    results = await agent.analyze_supply_chain(supply_chain_data)

    print(f"\n   Status: {results['status']}")
    print(f"   AI-Powered: {results['ai_powered']}")
    print(f"   Processing Time: {results['processing_time_ms']:.1f}ms")

    # Print component summaries
    components = results.get("components", {})

    if "inventory_optimization" in components:
        inv = components["inventory_optimization"]
        print(f"\n2. Inventory Optimization:")
        print(f"   - SKUs Analyzed: {inv['total_skus_analyzed']}")
        print(f"   - Critical Items: {inv['critical_items']}")
        print(f"   - High Priority Items: {inv['high_priority_items']}")

    if "supplier_risk" in components:
        sup = components["supplier_risk"]
        print(f"\n3. Supplier Risk Assessment:")
        print(f"   - Suppliers Assessed: {sup['suppliers_assessed']}")
        print(f"   - High Risk Suppliers: {sup['high_risk_suppliers']}")
        print(f"   - Average Risk Score: {sup['average_risk_score']}")

    if "demand_forecast" in components:
        fcst = components["demand_forecast"]
        print(f"\n4. Demand Forecast:")
        print(f"   - Horizon: {fcst['horizon_days']} days")
        print(f"   - Confidence: {fcst['confidence']}")

    if "quality_monitoring" in components:
        qual = components["quality_monitoring"]
        print(f"\n5. Quality Monitoring:")
        print(f"   - Products Monitored: {qual['products_monitored']}")
        print(f"   - Anomalies Detected: {qual['anomalies_detected']}")

    if "disruption_prediction" in components:
        disr = components["disruption_prediction"]
        print(f"\n6. Disruption Prediction:")
        print(f"   - Risk Score: {disr['risk_score']}")
        print(f"   - Analysis Horizon: {disr['analysis_horizon']}")

    # Print recommendations
    recommendations = results.get("recommendations", [])
    if recommendations:
        print(f"\n7. AI Recommendations ({len(recommendations)}):")
        for rec in recommendations[:3]:
            print(f"   [{rec['priority'].upper()}] {rec['action']}")

    # Print agent state
    print(f"\n8. Agent State:")
    state = agent.get_state()
    print(f"   - Forecasts Generated: {state['forecasts_generated']}")
    print(f"   - Alerts Generated: {state['alerts_generated']}")
    print(f"   - Optimizations Performed: {state['optimizations_performed']}")

    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)

    return results


if __name__ == "__main__":
    asyncio.run(demo_supply_chain_agent())
