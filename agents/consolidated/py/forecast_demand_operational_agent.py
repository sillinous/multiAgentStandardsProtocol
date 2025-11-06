"""
ForecastDemandOperationalAgent - APQC 4.0
4.1.3 Forecast Demand
APQC ID: apqc_4_0_e6f7g8h9
"""

import os
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime

from superstandard.agents.base.base_agent import BaseAgent
from library.core.protocols import ProtocolMixin


@dataclass
class ForecastDemandOperationalAgentConfig:
    apqc_agent_id: str = "apqc_4_0_e6f7g8h9"
    apqc_process_id: str = "4.1.3"
    agent_name: str = "forecast_demand_operational_agent"
    agent_type: str = "analytical"
    version: str = "1.0.0"


class ForecastDemandOperationalAgent(BaseAgent, ProtocolMixin):
    """
    Skills: time_series_forecasting: 0.92, seasonality_detection: 0.88, demand_planning: 0.86
    """

    VERSION = "1.0.0"
    APQC_PROCESS_ID = "4.1.3"

    def __init__(self, config: ForecastDemandOperationalAgentConfig):
        super().__init__(agent_id=config.apqc_agent_id, agent_type=config.agent_type, version=config.version)
        self.config = config
        self.skills = {'time_series_forecasting': 0.92, 'seasonality_detection': 0.88, 'demand_planning': 0.86}

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Forecast demand using exponential smoothing and seasonal decomposition
        """
        historical_demand = np.array(input_data.get('historical_demand', []))
        seasonality_factors = input_data.get('seasonality_factors', {})
        external_indicators = input_data.get('external_indicators', {})
        forecast_periods = input_data.get('forecast_periods', 12)

        # Exponential Smoothing
        forecast = self._exponential_smoothing(historical_demand, forecast_periods)

        # Seasonal Decomposition
        seasonal_decomp = self._seasonal_decomposition(historical_demand, seasonality_factors)

        # Apply seasonality to forecast
        final_forecast = self._apply_seasonality(forecast, seasonal_decomp)

        # Calculate confidence intervals
        confidence_intervals = self._calculate_confidence_intervals(historical_demand, final_forecast)

        return {
            "status": "completed",
            "apqc_process_id": self.APQC_PROCESS_ID,
            "timestamp": datetime.now().isoformat(),
            "output": {
                "demand_forecast": {
                    "predictions": final_forecast,
                    "confidence_intervals": confidence_intervals,
                    "seasonality_patterns": seasonal_decomp,
                    "forecast_method": "exponential_smoothing_with_seasonality"
                },
                "metrics": {
                    "forecast_accuracy_estimate": seasonal_decomp.get('seasonal_strength', 0),
                    "average_forecasted_demand": round(float(np.mean(final_forecast)), 2),
                    "forecast_horizon": forecast_periods
                }
            }
        }

    def _exponential_smoothing(self, data: np.ndarray, periods: int, alpha: float = 0.3) -> List[float]:
        """Exponential smoothing forecast"""
        if len(data) == 0:
            return [0] * periods

        forecast = []
        smoothed = data[0]

        for value in data[1:]:
            smoothed = alpha * value + (1 - alpha) * smoothed

        # Forecast future periods
        trend = (data[-1] - data[0]) / len(data) if len(data) > 1 else 0
        for i in range(periods):
            predicted = smoothed + trend * (i + 1)
            forecast.append(round(float(predicted), 2))

        return forecast

    def _seasonal_decomposition(self, data: np.ndarray, seasonality_factors: Dict) -> Dict[str, Any]:
        """Decompose time series into seasonal components"""
        period = seasonality_factors.get('period', 12)

        if len(data) < period:
            return {"has_seasonality": False, "seasonal_indices": [], "seasonal_strength": 0}

        seasonal_indices = []
        for i in range(period):
            season_values = data[i::period]
            if len(season_values) > 0:
                seasonal_indices.append(float(np.mean(season_values)))

        overall_mean = float(np.mean(data))
        normalized_indices = [idx / overall_mean if overall_mean != 0 else 1.0 for idx in seasonal_indices]

        seasonal_strength = float(np.std(normalized_indices)) * 100

        return {
            "has_seasonality": seasonal_strength > 10,
            "seasonal_indices": [round(idx, 3) for idx in normalized_indices],
            "seasonal_strength": round(seasonal_strength, 2),
            "period": period
        }

    def _apply_seasonality(self, forecast: List[float], seasonal: Dict) -> List[float]:
        """Apply seasonal adjustments to forecast"""
        if not seasonal.get('has_seasonality'):
            return forecast

        indices = seasonal['seasonal_indices']
        adjusted = []

        for i, value in enumerate(forecast):
            seasonal_idx = indices[i % len(indices)]
            adjusted.append(round(value * seasonal_idx, 2))

        return adjusted

    def _calculate_confidence_intervals(self, historical: np.ndarray, forecast: List[float]) -> Dict[str, Any]:
        """Calculate confidence intervals"""
        if len(historical) < 2:
            return {"lower": forecast, "upper": forecast}

        std_dev = float(np.std(historical))

        lower = [max(0, round(f - 1.96 * std_dev, 2)) for f in forecast]
        upper = [round(f + 1.96 * std_dev, 2) for f in forecast]

        return {"lower_95": lower, "upper_95": upper, "std_dev": round(std_dev, 2)}

    def log(self, level: str, message: str):
        print(f"[{datetime.now().isoformat()}] [{level}] {message}")


def create_forecast_demand_operational_agent(config: Optional[ForecastDemandOperationalAgentConfig] = None):
    if config is None:
        config = ForecastDemandOperationalAgentConfig()
    return ForecastDemandOperationalAgent(config)
