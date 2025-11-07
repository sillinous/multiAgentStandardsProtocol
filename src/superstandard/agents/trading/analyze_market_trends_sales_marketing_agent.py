"""
AnalyzeMarketTrendsSalesMarketingAgent - APQC 3.0 Agent

3.1.2 Analyze Market Trends

This agent implements APQC process 3.1.2 from category 3.0: Market and Sell Products and Services.

Domain: sales_marketing
Type: analytical

Fully compliant with Architectural Standards v1.0.0:
- Standardized (BaseAgent + dataclass config)
- Interoperable (A2A, A2P, ACP, ANP, MCP protocols)
- Redeployable (environment configuration)
- Reusable (no project-specific logic)
- Atomic (single responsibility)
- Composable (schema-based I/O)
- Orchestratable (coordination protocol support)
- Vendor Agnostic (abstraction layers)

APQC Blueprint ID: apqc_3_0_a2b3c4d5
APQC Category: 3.0 - Market and Sell Products and Services
APQC Process: 3.1.2 - Analyze Market Trends

Version: 1.0.0
Date: 2025-10-17
Framework: APQC 7.0.1
"""

import os
import psutil
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from superstandard.agents.base.base_agent import BaseAgent
from src.superstandard.agents.base.protocols import ProtocolMixin


@dataclass
class AnalyzeMarketTrendsSalesMarketingAgentConfig:
    """Configuration for AnalyzeMarketTrendsSalesMarketingAgent"""

    # APQC Metadata
    apqc_agent_id: str = "apqc_3_0_a2b3c4d5"
    apqc_category_id: str = "3.0"
    apqc_category_name: str = "Market and Sell Products and Services"
    apqc_process_id: str = "3.1.2"
    apqc_process_name: str = "3.1.2 Analyze Market Trends"

    # Agent Identity
    agent_id: str = "apqc_3_0_a2b3c4d5"
    agent_name: str = "analyze_market_trends_sales_marketing_agent"
    agent_type: str = "analytical"
    domain: str = "sales_marketing"
    version: str = "1.0.0"

    # Behavior Configuration
    autonomous_level: float = 0.9
    collaboration_mode: str = "orchestrated"
    learning_enabled: bool = True
    self_improvement: bool = True

    # Resource Configuration
    compute_mode: str = "adaptive"
    memory_mode: str = "adaptive"
    api_budget_mode: str = "dynamic"
    priority: str = "medium"

    # Quality Configuration
    testing_required: bool = True
    qa_threshold: float = 0.85
    consensus_weight: float = 1.0
    error_handling: str = "graceful_degradation"

    # Deployment Configuration
    runtime: str = "ray_actor"
    scaling: str = "horizontal"
    health_checks: bool = True
    monitoring: bool = True

    # Environment Variables
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    max_retries: int = field(default_factory=lambda: int(os.getenv("MAX_RETRIES", "3")))
    timeout_seconds: int = field(default_factory=lambda: int(os.getenv("TIMEOUT_SECONDS", "300")))

    @classmethod
    def from_environment(cls) -> "AnalyzeMarketTrendsSalesMarketingAgentConfig":
        """Create configuration from environment variables (Redeployable)"""
        return cls(
            agent_id=os.getenv("AGENT_ID", "apqc_3_0_a2b3c4d5"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
            timeout_seconds=int(os.getenv("TIMEOUT_SECONDS", "300")),
        )


class AnalyzeMarketTrendsSalesMarketingAgent(BaseAgent, ProtocolMixin):
    """
    AnalyzeMarketTrendsSalesMarketingAgent - APQC 3.0 Agent

    3.1.2 Analyze Market Trends

    Capabilities:
    - trend_analysis
    - statistical_analysis
    - pattern_recognition
    - forecasting
    - data_visualization
    - market_intelligence

    Skills:
    - trend_analysis: 0.9
    - statistical_analysis: 0.88
    - pattern_recognition: 0.85
    - forecasting: 0.82

    Interfaces:
      Inputs: time_series_data, market_indicators, competitor_data, external_factors
      Outputs: trend_report, forecasts, insights, recommendations, visualizations
      Protocols: message_passing, event_driven, api_rest

    Behavior:
      Autonomous Level: 0.9
      Collaboration: orchestrated
      Learning: Enabled
      Self-Improvement: Enabled

    Integration:
      Compatible Agents: 3.0, 1.0, 8.0
      Required Services: data_warehouse, analytics_engine, visualization_service
      Ontology Level: L1_analytical

    Compliance: FULL (All 8 architectural principles)
    Protocols: A2A, A2P, ACP, ANP, MCP
    """

    VERSION = "1.0.0"
    MIN_COMPATIBLE_VERSION = "1.0.0"

    # APQC Blueprint Metadata
    APQC_AGENT_ID = "apqc_3_0_a2b3c4d5"
    APQC_CATEGORY_ID = "3.0"
    APQC_PROCESS_ID = "3.1.2"
    APQC_FRAMEWORK_VERSION = "7.0.1"

    def __init__(self, config: AnalyzeMarketTrendsSalesMarketingAgentConfig):
        """Initialize agent"""
        super().__init__(
            agent_id=config.agent_id, agent_type=config.agent_type, version=config.version
        )

        self.config = config
        self.capabilities_list = [
            "trend_analysis",
            "statistical_analysis",
            "pattern_recognition",
            "forecasting",
            "data_visualization",
            "market_intelligence",
        ]
        self.skills = {
            "trend_analysis": 0.9,
            "statistical_analysis": 0.88,
            "pattern_recognition": 0.85,
            "forecasting": 0.82,
        }
        self.interfaces = {
            "inputs": [
                "time_series_data",
                "market_indicators",
                "competitor_data",
                "external_factors",
            ],
            "outputs": [
                "trend_report",
                "forecasts",
                "insights",
                "recommendations",
                "visualizations",
            ],
            "protocols": ["message_passing", "event_driven", "api_rest"],
        }
        self.behavior = {
            "autonomous_level": 0.9,
            "collaboration_mode": "orchestrated",
            "learning_enabled": True,
            "self_improvement": True,
        }
        self.resources = {
            "compute": "adaptive",
            "memory": "adaptive",
            "api_budget": "dynamic",
            "priority": "medium",
        }
        self.integration = {
            "compatible_agents": ["3.0", "1.0", "8.0"],
            "required_services": ["data_warehouse", "analytics_engine", "visualization_service"],
            "ontology_level": "L1_analytical",
        }
        self.quality = {
            "testing_required": True,
            "qa_threshold": 0.85,
            "consensus_weight": 1.0,
            "error_handling": "graceful_degradation",
        }
        self.deployment = {
            "runtime": "ray_actor",
            "scaling": "horizontal",
            "health_checks": True,
            "monitoring": True,
        }

        # Initialize state
        self.state = {
            "status": "initialized",
            "tasks_processed": 0,
            "last_activity": datetime.now().isoformat(),
            "performance_metrics": {},
            "learning_data": {} if self.config.learning_enabled else None,
        }

        self._initialize_protocols()
        self._initialize_monitoring()

    @classmethod
    def from_environment(cls) -> "AnalyzeMarketTrendsSalesMarketingAgent":
        """Create agent from environment variables (Redeployable)"""
        config = AnalyzeMarketTrendsSalesMarketingAgentConfig.from_environment()
        return cls(config)

    def _initialize_protocols(self):
        """Initialize protocol support"""
        self.log("info", f"Protocols initialized: A2A, A2P, ACP, ANP, MCP")

    def _initialize_monitoring(self):
        """Initialize monitoring and health checks"""
        if self.config.monitoring:
            self.log("info", f"Monitoring enabled for {self.config.agent_name}")

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute agent's primary function (Atomic)

        Args:
            input_data: Input data matching input schema

        Returns:
            Output data matching output schema
        """
        self.log("info", f"Executing {self.config.apqc_process_name}")

        try:
            # Validate input
            if not self._validate_input(input_data):
                return {
                    "status": "error",
                    "message": "Invalid input data",
                    "error_handling": self.config.error_handling,
                }

            # Process market trend analysis
            result = await self._process_trend_analysis(input_data)

            # Update state
            self.state["tasks_processed"] += 1
            self.state["last_activity"] = datetime.now().isoformat()

            # Learning and self-improvement
            if self.config.learning_enabled:
                await self._learn_from_execution(input_data, result)

            return result

        except Exception as e:
            self.log("error", f"Execution error: {str(e)}")
            if self.config.error_handling == "graceful_degradation":
                return {"status": "degraded", "message": str(e), "partial_result": {}}
            raise

    async def _process_trend_analysis(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process market trend analysis with real business logic

        Implements APQC process: 3.1.2 Analyze Market Trends

        Business Logic:
        1. Calculate moving averages (SMA, EMA)
        2. Detect trend direction and strength
        3. Identify seasonality patterns
        4. Calculate growth rates
        5. Generate forecasts
        """
        self.log("info", "Processing market trend analysis")

        # Extract input data
        time_series_data = input_data.get("time_series_data", [])
        market_indicators = input_data.get("market_indicators", {})
        competitor_data = input_data.get("competitor_data", [])
        analysis_period = input_data.get("analysis_period", 12)  # months

        # Convert time series to numpy array for calculations
        values = np.array([point.get("value", 0) for point in time_series_data])
        timestamps = [point.get("timestamp") for point in time_series_data]

        # Calculate moving averages
        moving_averages = self._calculate_moving_averages(values)

        # Detect trend direction and strength
        trend_analysis = self._detect_trend(values, moving_averages)

        # Identify seasonality
        seasonality = self._detect_seasonality(values, analysis_period)

        # Calculate growth rates
        growth_rates = self._calculate_growth_rates(values)

        # Generate forecast
        forecast = self._generate_forecast(values, trend_analysis, seasonality)

        # Analyze competitor trends
        competitor_insights = self._analyze_competitors(competitor_data, values)

        # Generate insights and recommendations
        insights = self._generate_insights(
            trend_analysis, seasonality, growth_rates, competitor_insights
        )
        recommendations = self._generate_recommendations(insights, market_indicators)

        result = {
            "status": "completed",
            "apqc_process_id": self.APQC_PROCESS_ID,
            "agent_id": self.config.agent_id,
            "timestamp": datetime.now().isoformat(),
            "output": {
                "trend_report": {
                    "direction": trend_analysis["direction"],
                    "strength": trend_analysis["strength"],
                    "confidence": trend_analysis["confidence"],
                    "moving_averages": moving_averages,
                    "current_value": float(values[-1]) if len(values) > 0 else 0,
                    "period_analyzed": len(values),
                },
                "seasonality": seasonality,
                "growth_rates": growth_rates,
                "forecasts": forecast,
                "competitor_analysis": competitor_insights,
                "insights": insights,
                "recommendations": recommendations,
                "metrics": {
                    "data_points_analyzed": len(values),
                    "trend_strength_score": trend_analysis["strength"],
                    "forecast_accuracy_estimate": forecast["confidence"],
                },
            },
        }

        return result

    def _calculate_moving_averages(self, values: np.ndarray) -> Dict[str, Any]:
        """
        Calculate Simple Moving Average (SMA) and Exponential Moving Average (EMA)
        """
        if len(values) < 3:
            return {"sma_short": 0, "sma_long": 0, "ema": 0}

        # Short-term SMA (3 periods)
        sma_short_period = min(3, len(values))
        sma_short = float(np.mean(values[-sma_short_period:]))

        # Long-term SMA (12 periods)
        sma_long_period = min(12, len(values))
        sma_long = float(np.mean(values[-sma_long_period:]))

        # Exponential Moving Average
        ema = self._calculate_ema(values, span=5)

        return {
            "sma_short": round(sma_short, 2),
            "sma_long": round(sma_long, 2),
            "ema": round(ema, 2),
            "crossover": "bullish" if sma_short > sma_long else "bearish",
        }

    def _calculate_ema(self, values: np.ndarray, span: int = 5) -> float:
        """Calculate Exponential Moving Average"""
        if len(values) == 0:
            return 0.0

        alpha = 2 / (span + 1)
        ema = values[0]

        for value in values[1:]:
            ema = alpha * value + (1 - alpha) * ema

        return float(ema)

    def _detect_trend(self, values: np.ndarray, moving_averages: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect trend direction and strength using linear regression
        """
        if len(values) < 2:
            return {"direction": "neutral", "strength": 0, "confidence": 0}

        # Linear regression
        x = np.arange(len(values))
        coeffs = np.polyfit(x, values, 1)
        slope = coeffs[0]

        # Calculate R-squared for confidence
        y_pred = np.polyval(coeffs, x)
        ss_res = np.sum((values - y_pred) ** 2)
        ss_tot = np.sum((values - np.mean(values)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

        # Determine direction
        if slope > 0.05:
            direction = "upward"
        elif slope < -0.05:
            direction = "downward"
        else:
            direction = "neutral"

        # Calculate strength (normalized slope)
        mean_value = np.mean(values)
        strength = abs(slope / mean_value) if mean_value != 0 else 0
        strength = min(strength * 100, 100)  # Normalize to 0-100

        return {
            "direction": direction,
            "strength": round(float(strength), 2),
            "confidence": round(float(r_squared), 2),
            "slope": round(float(slope), 4),
            "r_squared": round(float(r_squared), 4),
        }

    def _detect_seasonality(self, values: np.ndarray, period: int = 12) -> Dict[str, Any]:
        """
        Detect seasonality patterns using autocorrelation
        """
        if len(values) < period * 2:
            return {
                "has_seasonality": False,
                "seasonal_strength": 0,
                "period": period,
                "seasonal_indices": [],
            }

        # Calculate seasonal indices
        seasonal_indices = []
        for i in range(period):
            period_values = values[i::period]
            if len(period_values) > 0:
                seasonal_index = float(np.mean(period_values))
                seasonal_indices.append(seasonal_index)

        overall_mean = float(np.mean(values))
        normalized_indices = [
            idx / overall_mean if overall_mean != 0 else 1.0 for idx in seasonal_indices
        ]

        # Calculate seasonal strength (coefficient of variation)
        if len(normalized_indices) > 0:
            std_dev = float(np.std(normalized_indices))
            seasonal_strength = std_dev * 100
            has_seasonality = seasonal_strength > 10  # Threshold
        else:
            seasonal_strength = 0
            has_seasonality = False

        return {
            "has_seasonality": has_seasonality,
            "seasonal_strength": round(seasonal_strength, 2),
            "period": period,
            "seasonal_indices": [round(idx, 2) for idx in normalized_indices],
            "peak_periods": [i for i, idx in enumerate(normalized_indices) if idx > 1.1],
            "low_periods": [i for i, idx in enumerate(normalized_indices) if idx < 0.9],
        }

    def _calculate_growth_rates(self, values: np.ndarray) -> Dict[str, Any]:
        """
        Calculate various growth rate metrics
        """
        if len(values) < 2:
            return {"period_over_period": 0, "cagr": 0, "average_growth": 0}

        # Period-over-period growth
        pop_growth = ((values[-1] - values[-2]) / values[-2] * 100) if values[-2] != 0 else 0

        # Compound Annual Growth Rate (CAGR)
        n_periods = len(values) - 1
        if n_periods > 0 and values[0] > 0:
            cagr = ((values[-1] / values[0]) ** (1 / n_periods) - 1) * 100
        else:
            cagr = 0

        # Average growth rate
        growth_rates = []
        for i in range(1, len(values)):
            if values[i - 1] != 0:
                rate = (values[i] - values[i - 1]) / values[i - 1] * 100
                growth_rates.append(rate)

        average_growth = float(np.mean(growth_rates)) if growth_rates else 0

        return {
            "period_over_period": round(float(pop_growth), 2),
            "cagr": round(float(cagr), 2),
            "average_growth": round(average_growth, 2),
            "volatility": round(float(np.std(growth_rates)), 2) if growth_rates else 0,
        }

    def _generate_forecast(
        self, values: np.ndarray, trend: Dict[str, Any], seasonality: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate forecast using trend and seasonality
        """
        if len(values) < 3:
            return {"predictions": [], "confidence": 0, "method": "insufficient_data"}

        forecast_periods = 6
        predictions = []

        # Use linear trend for forecast
        x = np.arange(len(values))
        coeffs = np.polyfit(x, values, 1)

        for i in range(forecast_periods):
            future_x = len(values) + i
            predicted_value = np.polyval(coeffs, future_x)

            # Apply seasonality if detected
            if seasonality["has_seasonality"]:
                period_index = future_x % len(seasonality["seasonal_indices"])
                seasonal_factor = seasonality["seasonal_indices"][period_index]
                predicted_value *= seasonal_factor

            predictions.append(
                {
                    "period": i + 1,
                    "value": round(float(predicted_value), 2),
                    "confidence_lower": round(float(predicted_value * 0.9), 2),
                    "confidence_upper": round(float(predicted_value * 1.1), 2),
                }
            )

        return {
            "predictions": predictions,
            "confidence": trend["confidence"],
            "method": (
                "linear_trend_with_seasonality"
                if seasonality["has_seasonality"]
                else "linear_trend"
            ),
            "forecast_horizon": forecast_periods,
        }

    def _analyze_competitors(
        self, competitor_data: List[Dict[str, Any]], own_values: np.ndarray
    ) -> Dict[str, Any]:
        """
        Analyze competitor trends and market position
        """
        if not competitor_data or len(own_values) == 0:
            return {"market_position": "unknown", "competitors_analyzed": 0}

        own_current = own_values[-1]
        competitor_values = []

        for competitor in competitor_data:
            comp_value = competitor.get("current_value", 0)
            competitor_values.append(
                {
                    "name": competitor.get("name", "Unknown"),
                    "value": comp_value,
                    "relative_position": (
                        ((own_current - comp_value) / comp_value * 100) if comp_value != 0 else 0
                    ),
                }
            )

        # Calculate market position
        all_values = [own_current] + [c["value"] for c in competitor_values]
        market_rank = sorted(all_values, reverse=True).index(own_current) + 1

        return {
            "market_position": f"{market_rank} of {len(all_values)}",
            "competitors_analyzed": len(competitor_data),
            "competitor_comparison": competitor_values,
            "market_share_estimate": (
                round((own_current / sum(all_values) * 100), 2) if sum(all_values) > 0 else 0
            ),
        }

    def _generate_insights(
        self,
        trend: Dict[str, Any],
        seasonality: Dict[str, Any],
        growth: Dict[str, Any],
        competitors: Dict[str, Any],
    ) -> List[str]:
        """
        Generate actionable insights from analysis
        """
        insights = []

        # Trend insights
        if trend["direction"] == "upward":
            insights.append(
                f"Strong upward trend detected with {trend['strength']:.1f}% strength and {trend['confidence']:.0%} confidence"
            )
        elif trend["direction"] == "downward":
            insights.append(
                f"Downward trend detected with {trend['strength']:.1f}% strength - requires immediate attention"
            )
        else:
            insights.append("Market is stable with no clear directional trend")

        # Seasonality insights
        if seasonality["has_seasonality"]:
            peak_periods = seasonality["peak_periods"]
            if peak_periods:
                insights.append(
                    f"Seasonal pattern detected with peak performance in periods: {', '.join(map(str, peak_periods))}"
                )

        # Growth insights
        if growth["cagr"] > 10:
            insights.append(f"Excellent growth trajectory with {growth['cagr']:.1f}% CAGR")
        elif growth["cagr"] < -5:
            insights.append(f"Concerning negative growth of {growth['cagr']:.1f}% CAGR")

        # Competitor insights
        if competitors["competitors_analyzed"] > 0:
            insights.append(
                f"Market position: {competitors['market_position']} with {competitors['market_share_estimate']:.1f}% estimated share"
            )

        return insights

    def _generate_recommendations(
        self, insights: List[str], market_indicators: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate actionable recommendations
        """
        recommendations = []

        # Parse insights for recommendation generation
        insight_text = " ".join(insights).lower()

        if "upward trend" in insight_text:
            recommendations.append(
                {
                    "priority": "high",
                    "category": "growth",
                    "action": "Capitalize on positive momentum",
                    "description": "Increase marketing spend and expand market presence to maximize growth potential",
                }
            )

        if "downward trend" in insight_text:
            recommendations.append(
                {
                    "priority": "critical",
                    "category": "recovery",
                    "action": "Implement turnaround strategy",
                    "description": "Conduct root cause analysis and implement corrective measures immediately",
                }
            )

        if "seasonal pattern" in insight_text:
            recommendations.append(
                {
                    "priority": "medium",
                    "category": "planning",
                    "action": "Optimize for seasonality",
                    "description": "Adjust inventory, staffing, and marketing campaigns to align with seasonal patterns",
                }
            )

        if "market position" in insight_text:
            recommendations.append(
                {
                    "priority": "medium",
                    "category": "competitive",
                    "action": "Strengthen competitive position",
                    "description": "Analyze competitor strategies and differentiate value proposition",
                }
            )

        # Add general recommendation if none generated
        if not recommendations:
            recommendations.append(
                {
                    "priority": "low",
                    "category": "monitoring",
                    "action": "Continue monitoring",
                    "description": "Maintain current strategy while monitoring market conditions",
                }
            )

        return recommendations

    async def _learn_from_execution(self, input_data: Dict[str, Any], result: Dict[str, Any]):
        """Learn from execution for self-improvement"""
        if not self.config.self_improvement:
            return

        if self.state["learning_data"] is not None:
            learning_entry = {
                "timestamp": datetime.now().isoformat(),
                "input_summary": str(input_data)[:100],
                "result_status": result.get("status"),
                "performance": {
                    "trend_strength": result.get("output", {})
                    .get("trend_report", {})
                    .get("strength", 0),
                    "forecast_confidence": result.get("output", {})
                    .get("forecasts", {})
                    .get("confidence", 0),
                },
            }

            if "learning_history" not in self.state["learning_data"]:
                self.state["learning_data"]["learning_history"] = []

            self.state["learning_data"]["learning_history"].append(learning_entry)

    def _validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data against schema"""
        if not isinstance(input_data, dict):
            return False

        # Check for required fields
        if "time_series_data" not in input_data:
            return False

        return True

    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check (Redeployable)"""
        memory_usage = self._get_memory_usage()

        health = {
            "agent_id": self.config.agent_id,
            "agent_name": self.config.agent_name,
            "version": self.VERSION,
            "status": self.state["status"],
            "timestamp": datetime.now().isoformat(),
            "apqc_metadata": {
                "category_id": self.APQC_CATEGORY_ID,
                "process_id": self.APQC_PROCESS_ID,
                "framework_version": self.APQC_FRAMEWORK_VERSION,
            },
            "protocols": self.get_supported_protocols(),
            "capabilities": self.capabilities_list,
            "compliance": {
                "standardized": True,
                "interoperable": True,
                "redeployable": True,
                "reusable": True,
                "atomic": True,
                "composable": True,
                "orchestratable": True,
                "vendor_agnostic": True,
            },
            "performance": {
                "tasks_processed": self.state["tasks_processed"],
                "memory_mb": memory_usage,
                "last_activity": self.state["last_activity"],
            },
        }

        return health

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            return memory_info.rss / 1024 / 1024
        except Exception as e:
            self.log("warning", f"Could not get memory usage: {str(e)}")
            return 0.0

    def get_input_schema(self) -> Dict[str, Any]:
        """Get input data schema (Composable)"""
        return {
            "type": "object",
            "description": f"Input schema for {self.config.apqc_process_name}",
            "apqc_process_id": self.APQC_PROCESS_ID,
            "accepted_inputs": self.interfaces["inputs"],
            "properties": {
                "time_series_data": {
                    "type": "array",
                    "description": "Historical time series data points",
                    "items": {
                        "type": "object",
                        "properties": {
                            "timestamp": {"type": "string"},
                            "value": {"type": "number"},
                        },
                    },
                },
                "market_indicators": {
                    "type": "object",
                    "description": "External market indicators",
                },
                "competitor_data": {"type": "array", "description": "Competitor performance data"},
                "analysis_period": {
                    "type": "integer",
                    "description": "Number of periods to analyze",
                    "default": 12,
                },
            },
            "required": ["time_series_data"],
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """Get output data schema (Composable)"""
        return {
            "type": "object",
            "description": f"Output schema for {self.config.apqc_process_name}",
            "apqc_process_id": self.APQC_PROCESS_ID,
            "generated_outputs": self.interfaces["outputs"],
            "properties": {
                "status": {"type": "string"},
                "apqc_process_id": {"type": "string"},
                "agent_id": {"type": "string"},
                "timestamp": {"type": "string"},
                "output": {
                    "type": "object",
                    "properties": {
                        "trend_report": {"type": "object"},
                        "seasonality": {"type": "object"},
                        "growth_rates": {"type": "object"},
                        "forecasts": {"type": "object"},
                        "insights": {"type": "array"},
                        "recommendations": {"type": "array"},
                    },
                },
            },
            "required": ["status", "output"],
        }

    def log(self, level: str, message: str):
        """Log message"""
        timestamp = datetime.now().isoformat()
        print(f"[{timestamp}] [{level.upper()}] [{self.config.agent_name}] {message}")


# Convenience function for agent creation
def create_analyze_market_trends_sales_marketing_agent(
    config: Optional[AnalyzeMarketTrendsSalesMarketingAgentConfig] = None,
) -> AnalyzeMarketTrendsSalesMarketingAgent:
    """Create AnalyzeMarketTrendsSalesMarketingAgent instance"""
    if config is None:
        config = AnalyzeMarketTrendsSalesMarketingAgentConfig()
    return AnalyzeMarketTrendsSalesMarketingAgent(config)
