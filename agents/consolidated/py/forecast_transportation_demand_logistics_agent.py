"""
ForecastTransportationDemandLogisticsAgent - APQC 4.1.4
Forecast Transportation Demand for Ride-Sharing
APQC ID: apqc_4_1_f1t2d3m4

This agent forecasts ride demand using time-series analysis, event correlation,
weather impact modeling, and seasonal pattern detection.
"""

import os
import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

from superstandard.agents.base.base_agent import BaseAgent
from library.core.protocols import ProtocolMixin


@dataclass
class ForecastTransportationDemandLogisticsAgentConfig:
    apqc_agent_id: str = "apqc_4_1_f1t2d3m4"
    apqc_process_id: str = "4.1.4"
    agent_name: str = "forecast_transportation_demand_logistics_agent"
    agent_type: str = "analytical"
    version: str = "1.0.0"


class ForecastTransportationDemandLogisticsAgent(BaseAgent, ProtocolMixin):
    """
    APQC 4.1.4 - Forecast Transportation Demand

    Skills:
    - demand_forecasting: 0.93 (time-series prediction)
    - event_correlation: 0.90 (event-driven surge prediction)
    - seasonality_detection: 0.88 (pattern recognition)
    - weather_impact: 0.85 (weather-demand correlation)

    Use Cases:
    - Predict hourly ride demand
    - Forecast event-based surges
    - Model weather impact on demand
    - Identify seasonal patterns
    """

    VERSION = "1.0.0"
    APQC_PROCESS_ID = "4.1.4"

    def __init__(self, config: ForecastTransportationDemandLogisticsAgentConfig):
        super().__init__(
            agent_id=config.apqc_agent_id, agent_type=config.agent_type, version=config.version
        )
        self.config = config
        self.skills = {
            "demand_forecasting": 0.93,
            "event_correlation": 0.90,
            "seasonality_detection": 0.88,
            "weather_impact": 0.85,
        }

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Forecast transportation demand

        Input:
        {
            "historical_demand": [120, 135, 142, 158, 175, 165, 140, 125],
            "time_periods": ["2025-10-11 14:00", "2025-10-11 15:00", ...],
            "forecast_horizon_hours": 24,
            "location": "downtown_sf",
            "events": [
                {"event": "Giants Game", "datetime": "2025-10-18 19:00", "attendance": 40000},
                {"event": "Concert", "datetime": "2025-10-19 20:00", "attendance": 15000}
            ],
            "weather_forecast": [
                {"hour": 0, "condition": "clear", "temp_f": 65, "precipitation_chance": 0.1},
                {"hour": 1, "condition": "rain", "temp_f": 60, "precipitation_chance": 0.8}
            ],
            "day_of_week": "Friday",
            "is_holiday": false
        }
        """
        historical_demand = input_data.get("historical_demand", [])
        forecast_hours = input_data.get("forecast_horizon_hours", 24)
        events = input_data.get("events", [])
        weather = input_data.get("weather_forecast", [])
        day_of_week = input_data.get("day_of_week", "Monday")
        is_holiday = input_data.get("is_holiday", False)

        # Base forecast using time-series analysis
        base_forecast = self._forecast_base_demand(historical_demand, forecast_hours)

        # Detect and apply seasonal patterns
        seasonal_adjustment = self._apply_seasonal_patterns(base_forecast, day_of_week, is_holiday)

        # Apply event impact
        event_adjustment = self._apply_event_impact(seasonal_adjustment, events, forecast_hours)

        # Apply weather impact
        final_forecast = self._apply_weather_impact(event_adjustment, weather)

        # Calculate confidence intervals
        confidence_intervals = self._calculate_confidence(historical_demand, final_forecast)

        # Identify surge periods
        surge_periods = self._identify_surge_periods(final_forecast, historical_demand)

        # Generate capacity recommendations
        capacity_recommendations = self._generate_capacity_recommendations(
            final_forecast, surge_periods
        )

        return {
            "status": "completed",
            "apqc_process_id": self.APQC_PROCESS_ID,
            "timestamp": datetime.now().isoformat(),
            "output": {
                "demand_forecast": final_forecast,
                "confidence_intervals": confidence_intervals,
                "surge_periods": surge_periods,
                "capacity_recommendations": capacity_recommendations,
                "summary": {
                    "average_hourly_demand": round(np.mean(final_forecast["hourly_demand"]), 1),
                    "peak_demand": max(final_forecast["hourly_demand"]),
                    "peak_hour": final_forecast["hours"][
                        final_forecast["hourly_demand"].index(max(final_forecast["hourly_demand"]))
                    ],
                    "total_forecasted_rides": sum(final_forecast["hourly_demand"]),
                },
            },
        }

    def _forecast_base_demand(self, historical: List[float], hours: int) -> Dict[str, Any]:
        """Generate base forecast using exponential smoothing"""
        if not historical:
            return {"hourly_demand": [100] * hours, "hours": list(range(hours))}

        # Convert to numpy array
        data = np.array(historical)

        # Calculate trend
        if len(data) > 1:
            trend = (data[-1] - data[0]) / len(data)
        else:
            trend = 0

        # Exponential smoothing
        alpha = 0.3
        smoothed = data[0]
        for value in data[1:]:
            smoothed = alpha * value + (1 - alpha) * smoothed

        # Forecast future periods
        forecast = []
        for i in range(hours):
            predicted = smoothed + trend * (i + 1)
            forecast.append(max(0, round(predicted, 1)))

        return {
            "hourly_demand": forecast,
            "hours": list(range(hours)),
            "base_level": round(smoothed, 1),
            "trend": round(trend, 2),
        }

    def _apply_seasonal_patterns(
        self, base_forecast: Dict, day_of_week: str, is_holiday: bool
    ) -> Dict[str, Any]:
        """Apply day-of-week and time-of-day seasonality"""
        hourly_demand = base_forecast["hourly_demand"].copy()

        # Day of week factors
        dow_factors = {
            "Monday": 0.95,
            "Tuesday": 0.92,
            "Wednesday": 0.93,
            "Thursday": 0.98,
            "Friday": 1.15,
            "Saturday": 1.20,
            "Sunday": 1.05,
        }

        day_factor = dow_factors.get(day_of_week, 1.0)

        # Holiday factor
        holiday_factor = 1.25 if is_holiday else 1.0

        # Time of day patterns (hourly multipliers for 24 hours)
        time_of_day_pattern = [
            0.3,
            0.2,
            0.2,
            0.2,
            0.3,
            0.5,  # 0-5 AM: Very low
            0.8,
            1.2,
            1.4,
            1.3,
            1.1,
            1.0,  # 6-11 AM: Morning rise
            0.9,
            0.8,
            0.9,
            1.0,
            1.2,
            1.5,  # 12-5 PM: Afternoon
            1.8,
            1.9,
            1.7,
            1.4,
            1.0,
            0.6,  # 6-11 PM: Evening peak
        ]

        # Apply all factors
        adjusted_demand = []
        for i, demand in enumerate(hourly_demand):
            hour_of_day = i % 24
            time_factor = time_of_day_pattern[hour_of_day]

            adjusted = demand * day_factor * holiday_factor * time_factor
            adjusted_demand.append(round(adjusted, 1))

        return {
            "hourly_demand": adjusted_demand,
            "hours": base_forecast["hours"],
            "day_factor": day_factor,
            "holiday_factor": holiday_factor,
            "seasonal_adjustments_applied": True,
        }

    def _apply_event_impact(
        self, forecast: Dict, events: List[Dict], forecast_hours: int
    ) -> Dict[str, Any]:
        """Apply event-based demand surges"""
        hourly_demand = forecast["hourly_demand"].copy()

        event_impacts = []

        for event in events:
            event_datetime_str = event.get("datetime", "")
            attendance = event.get("attendance", 0)

            # Calculate event impact
            # Assume impact starts 2 hours before and extends 3 hours after
            impact_multiplier = 1 + (attendance / 10000) * 0.2  # 20% increase per 10k attendees

            # For simplification, assume event is within forecast window
            # In production, would parse datetime and calculate exact hours
            event_hour = len(hourly_demand) // 2  # Simplified: place in middle

            # Apply impact to surrounding hours
            for hour_offset in range(-2, 4):  # 2 hours before to 3 hours after
                impact_hour = event_hour + hour_offset
                if 0 <= impact_hour < len(hourly_demand):
                    # Gradual impact (peak at event time)
                    if hour_offset == 0:
                        multiplier = impact_multiplier
                    elif abs(hour_offset) == 1:
                        multiplier = 1 + (impact_multiplier - 1) * 0.7
                    else:
                        multiplier = 1 + (impact_multiplier - 1) * 0.4

                    hourly_demand[impact_hour] = round(hourly_demand[impact_hour] * multiplier, 1)

            event_impacts.append(
                {
                    "event": event.get("event"),
                    "impact_multiplier": round(impact_multiplier, 2),
                    "affected_hours": 6,
                }
            )

        return {
            "hourly_demand": hourly_demand,
            "hours": forecast["hours"],
            "event_impacts": event_impacts,
            "events_processed": len(events),
        }

    def _apply_weather_impact(self, forecast: Dict, weather_forecast: List[Dict]) -> Dict[str, Any]:
        """Apply weather impact on demand"""
        hourly_demand = forecast["hourly_demand"].copy()

        weather_impacts = []

        for i, weather in enumerate(weather_forecast[: len(hourly_demand)]):
            condition = weather.get("condition", "clear")
            precip_chance = weather.get("precipitation_chance", 0)
            temp = weather.get("temp_f", 70)

            # Weather impact factors
            condition_factors = {
                "clear": 1.0,
                "cloudy": 1.05,
                "rain": 1.25,
                "heavy_rain": 1.40,
                "snow": 1.30,
                "storm": 0.70,  # People avoid travel in storms
            }

            condition_factor = condition_factors.get(condition, 1.0)

            # Precipitation impact
            precip_factor = 1 + (precip_chance * 0.3)  # Up to 30% increase with high precip chance

            # Temperature impact (extreme temps increase demand)
            temp_factor = 1.0
            if temp < 40 or temp > 90:
                temp_factor = 1.15

            # Combined weather factor
            weather_factor = condition_factor * precip_factor * temp_factor

            hourly_demand[i] = round(hourly_demand[i] * weather_factor, 1)

            if weather_factor > 1.1:
                weather_impacts.append(
                    {"hour": i, "condition": condition, "impact_factor": round(weather_factor, 2)}
                )

        return {
            "hourly_demand": hourly_demand,
            "hours": forecast["hours"],
            "weather_impacts": weather_impacts,
            "weather_adjusted": True,
        }

    def _calculate_confidence(
        self, historical: List[float], forecast: Dict
    ) -> List[Dict[str, float]]:
        """Calculate confidence intervals for forecast"""
        if not historical:
            return []

        # Calculate standard deviation from historical data
        std_dev = np.std(historical) if len(historical) > 1 else 0

        # Confidence decreases with forecast horizon
        intervals = []
        for i, demand in enumerate(forecast["hourly_demand"]):
            # Increase uncertainty with time
            uncertainty_factor = 1 + (i * 0.02)  # 2% increase per hour
            adjusted_std = std_dev * uncertainty_factor

            # 95% confidence interval (1.96 standard deviations)
            lower_bound = max(0, demand - (1.96 * adjusted_std))
            upper_bound = demand + (1.96 * adjusted_std)

            intervals.append(
                {
                    "hour": i,
                    "forecast": demand,
                    "lower_95": round(lower_bound, 1),
                    "upper_95": round(upper_bound, 1),
                    "confidence_percentage": round(max(50, 95 - (i * 1)), 1),
                }
            )

        return intervals

    def _identify_surge_periods(
        self, forecast: Dict, historical: List[float]
    ) -> List[Dict[str, Any]]:
        """Identify periods requiring surge pricing"""
        if not historical:
            baseline = 100
        else:
            baseline = np.mean(historical)

        surge_threshold = baseline * 1.3  # 30% above baseline

        surge_periods = []
        in_surge = False
        surge_start = None

        for i, demand in enumerate(forecast["hourly_demand"]):
            if demand >= surge_threshold and not in_surge:
                # Surge period starts
                in_surge = True
                surge_start = i
            elif demand < surge_threshold and in_surge:
                # Surge period ends
                in_surge = False
                surge_periods.append(
                    {
                        "start_hour": surge_start,
                        "end_hour": i - 1,
                        "duration_hours": i - surge_start,
                        "peak_demand": round(max(forecast["hourly_demand"][surge_start:i]), 1),
                        "surge_multiplier_recommended": round(
                            1
                            + (
                                (max(forecast["hourly_demand"][surge_start:i]) - baseline)
                                / baseline
                            ),
                            2,
                        ),
                    }
                )

        # Handle case where surge extends to end
        if in_surge:
            surge_periods.append(
                {
                    "start_hour": surge_start,
                    "end_hour": len(forecast["hourly_demand"]) - 1,
                    "duration_hours": len(forecast["hourly_demand"]) - surge_start,
                    "peak_demand": round(max(forecast["hourly_demand"][surge_start:]), 1),
                    "surge_multiplier_recommended": round(
                        1 + ((max(forecast["hourly_demand"][surge_start:]) - baseline) / baseline),
                        2,
                    ),
                }
            )

        return surge_periods

    def _generate_capacity_recommendations(
        self, forecast: Dict, surge_periods: List[Dict]
    ) -> Dict[str, Any]:
        """Generate driver capacity recommendations"""
        hourly_demand = forecast["hourly_demand"]

        # Assume each driver can handle 2 rides per hour
        rides_per_driver_per_hour = 2

        # Calculate required drivers for each hour
        driver_requirements = []
        for i, demand in enumerate(hourly_demand):
            required_drivers = int(np.ceil(demand / rides_per_driver_per_hour))

            # Add buffer for surge periods
            is_surge = any(s["start_hour"] <= i <= s["end_hour"] for s in surge_periods)
            if is_surge:
                required_drivers = int(required_drivers * 1.2)  # 20% buffer

            driver_requirements.append(
                {
                    "hour": i,
                    "required_drivers": required_drivers,
                    "expected_rides": round(demand, 0),
                    "is_surge_period": is_surge,
                }
            )

        # Peak requirements
        peak_hour_data = max(driver_requirements, key=lambda x: x["required_drivers"])

        # Average requirements
        avg_drivers = int(np.mean([d["required_drivers"] for d in driver_requirements]))

        return {
            "hourly_driver_requirements": driver_requirements,
            "peak_requirement": {
                "hour": peak_hour_data["hour"],
                "drivers_needed": peak_hour_data["required_drivers"],
            },
            "average_drivers_needed": avg_drivers,
            "total_driver_hours_needed": sum(d["required_drivers"] for d in driver_requirements),
            "surge_periods_count": len(surge_periods),
            "recommendations": [
                f"Ensure {peak_hour_data['required_drivers']} drivers available during peak hour {peak_hour_data['hour']}",
                f"Average {avg_drivers} drivers needed throughout forecast period",
                f"Activate surge pricing during {len(surge_periods)} predicted surge periods",
            ],
        }

    def get_input_schema(self) -> Dict[str, Any]:
        """Return input schema"""
        return {
            "type": "object",
            "required": ["historical_demand"],
            "properties": {
                "historical_demand": {"type": "array"},
                "forecast_horizon_hours": {"type": "number"},
                "events": {"type": "array"},
                "weather_forecast": {"type": "array"},
                "day_of_week": {"type": "string"},
                "is_holiday": {"type": "boolean"},
            },
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """Return output schema"""
        return {
            "type": "object",
            "properties": {
                "demand_forecast": {"type": "object"},
                "confidence_intervals": {"type": "array"},
                "surge_periods": {"type": "array"},
                "capacity_recommendations": {"type": "object"},
            },
        }


def create_forecast_transportation_demand_logistics_agent() -> (
    ForecastTransportationDemandLogisticsAgent
):
    """Factory function to create ForecastTransportationDemandLogisticsAgent"""
    config = ForecastTransportationDemandLogisticsAgentConfig()
    return ForecastTransportationDemandLogisticsAgent(config)
