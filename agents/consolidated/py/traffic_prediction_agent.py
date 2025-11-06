"""
Traffic Prediction Agent for Mobility Routing Swarm

Predicts travel times and congestion patterns using time-based heuristics
and distance calculations.
"""

import math
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, time
from enum import Enum

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from superstandard.agents.base.base_agent import BaseAgent, AgentCapability


class CongestionLevel(Enum):
    """Traffic congestion levels"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    SEVERE = "severe"


class TrafficPredictionAgent(BaseAgent):
    """
    Agent responsible for predicting traffic patterns and travel times.
    Uses time-of-day heuristics and distance-based calculations.
    """

    def __init__(self, agent_id: str = "traffic_prediction_agent", workspace_path: str = "./autonomous-ecosystem/workspace"):
        super().__init__(
            agent_id=agent_id,
            agent_type="traffic_prediction",
            capabilities=[AgentCapability.ORCHESTRATION],
            workspace_path=workspace_path
        )

        # Traffic patterns by hour (multiplier on base speed)
        self.traffic_patterns = {
            # Early morning (12 AM - 6 AM): Light traffic
            0: 1.0, 1: 1.0, 2: 1.0, 3: 1.0, 4: 1.1, 5: 1.2,
            # Morning rush (6 AM - 10 AM): Heavy traffic
            6: 1.5, 7: 2.0, 8: 2.5, 9: 2.0, 10: 1.5,
            # Midday (10 AM - 3 PM): Moderate traffic
            11: 1.3, 12: 1.4, 13: 1.4, 14: 1.3, 15: 1.3,
            # Evening rush (3 PM - 7 PM): Heavy traffic
            16: 1.8, 17: 2.5, 18: 2.3, 19: 1.8,
            # Evening (7 PM - 12 AM): Moderate to light
            20: 1.4, 21: 1.2, 22: 1.1, 23: 1.0
        }

        # Base speed in km/h
        self.base_speed = 40.0

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute traffic prediction task

        Args:
            task: Task with 'action' and parameters

        Returns:
            Task execution result
        """
        action = task.get("action")

        if action == "predict_travel_time":
            return await self._handle_travel_time_prediction(task)
        elif action == "get_hotspots":
            return await self._handle_hotspot_detection(task)
        elif action == "suggest_alternates":
            return await self._handle_alternate_routes(task)
        else:
            return {
                "success": False,
                "error": f"Unknown action: {action}"
            }

    async def analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze traffic conditions and provide insights

        Args:
            input_data: Traffic data to analyze

        Returns:
            Analysis results with predictions and recommendations
        """
        current_time = input_data.get("time", datetime.now())
        if isinstance(current_time, str):
            current_time = datetime.fromisoformat(current_time)

        hour = current_time.hour
        congestion = self._get_congestion_level(hour)

        analysis = {
            "timestamp": datetime.now().isoformat(),
            "current_hour": hour,
            "congestion_level": congestion.value,
            "traffic_multiplier": self.traffic_patterns[hour],
            "recommendations": self._generate_recommendations(hour, congestion),
            "confidence": 0.85
        }

        return analysis

    def predict_travel_time(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        departure_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Predict travel time between two points

        Args:
            origin: (lat, lon) tuple for origin
            destination: (lat, lon) tuple for destination
            departure_time: Planned departure time

        Returns:
            Prediction with time estimates and confidence
        """
        if departure_time is None:
            departure_time = datetime.now()

        # Calculate distance using haversine formula
        distance_km = self._calculate_distance(origin, destination)

        # Get traffic multiplier for the hour
        hour = departure_time.hour
        traffic_multiplier = self.traffic_patterns[hour]

        # Calculate base travel time
        base_time_minutes = (distance_km / self.base_speed) * 60

        # Adjust for traffic
        predicted_time_minutes = base_time_minutes * traffic_multiplier

        # Add some randomness for realism (±10%)
        import random
        variance = random.uniform(0.9, 1.1)
        predicted_time_minutes *= variance

        congestion = self._get_congestion_level(hour)

        return {
            "distance_km": round(distance_km, 2),
            "base_time_minutes": round(base_time_minutes, 2),
            "predicted_time_minutes": round(predicted_time_minutes, 2),
            "departure_time": departure_time.isoformat(),
            "arrival_time": self._add_minutes(departure_time, predicted_time_minutes).isoformat(),
            "congestion_level": congestion.value,
            "traffic_multiplier": traffic_multiplier,
            "confidence": 0.82
        }

    def get_congestion_hotspots(self, area_bounds: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify congestion hotspots in an area

        Args:
            area_bounds: Dictionary with 'north', 'south', 'east', 'west' bounds

        Returns:
            List of hotspot locations with severity
        """
        current_hour = datetime.now().hour
        traffic_mult = self.traffic_patterns[current_hour]

        # Simulate hotspots based on traffic level
        hotspots = []

        if traffic_mult >= 2.0:  # Heavy traffic
            # Generate 3-5 hotspots
            import random
            num_hotspots = random.randint(3, 5)

            for i in range(num_hotspots):
                lat = random.uniform(area_bounds['south'], area_bounds['north'])
                lon = random.uniform(area_bounds['west'], area_bounds['east'])

                hotspots.append({
                    "location": {"lat": lat, "lon": lon},
                    "severity": "high" if traffic_mult > 2.3 else "moderate",
                    "delay_minutes": round(random.uniform(5, 15), 1),
                    "affected_radius_km": round(random.uniform(0.5, 2.0), 2)
                })

        return hotspots

    def suggest_alternate_routes(
        self,
        route: List[Tuple[float, float]],
        current_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Suggest alternate routes based on traffic conditions

        Args:
            route: List of (lat, lon) waypoints
            current_time: Time for traffic prediction

        Returns:
            List of alternate route suggestions
        """
        if current_time is None:
            current_time = datetime.now()

        hour = current_time.hour
        congestion = self._get_congestion_level(hour)

        alternates = []

        if congestion in [CongestionLevel.HIGH, CongestionLevel.SEVERE]:
            # Suggest time-shifted routes
            alternates.append({
                "type": "time_shift",
                "recommendation": "Depart 30 minutes earlier",
                "time_adjustment": -30,
                "expected_savings_minutes": 15,
                "confidence": 0.80
            })

            alternates.append({
                "type": "time_shift",
                "recommendation": "Depart 60 minutes later",
                "time_adjustment": 60,
                "expected_savings_minutes": 20,
                "confidence": 0.75
            })

        return alternates

    async def _handle_travel_time_prediction(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle travel time prediction task"""
        origin = tuple(task.get("origin", [0, 0]))
        destination = tuple(task.get("destination", [0, 0]))
        departure_time = task.get("departure_time")

        if isinstance(departure_time, str):
            departure_time = datetime.fromisoformat(departure_time)

        prediction = self.predict_travel_time(origin, destination, departure_time)

        return {
            "success": True,
            "prediction": prediction,
            "agent_id": self.agent_id
        }

    async def _handle_hotspot_detection(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle hotspot detection task"""
        area_bounds = task.get("area_bounds", {
            "north": 37.8, "south": 37.7,
            "east": -122.3, "west": -122.5
        })

        hotspots = self.get_congestion_hotspots(area_bounds)

        return {
            "success": True,
            "hotspots": hotspots,
            "count": len(hotspots),
            "agent_id": self.agent_id
        }

    async def _handle_alternate_routes(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle alternate route suggestion task"""
        route = task.get("route", [])
        current_time = task.get("current_time")

        if isinstance(current_time, str):
            current_time = datetime.fromisoformat(current_time)

        alternates = self.suggest_alternate_routes(route, current_time)

        return {
            "success": True,
            "alternates": alternates,
            "agent_id": self.agent_id
        }

    def _calculate_distance(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """Calculate distance between two lat/lon points using Haversine formula"""
        lat1, lon1 = point1
        lat2, lon2 = point2

        R = 6371  # Earth radius in km

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) ** 2)

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c

        return distance

    def _get_congestion_level(self, hour: int) -> CongestionLevel:
        """Get congestion level for a given hour"""
        multiplier = self.traffic_patterns[hour]

        if multiplier >= 2.3:
            return CongestionLevel.SEVERE
        elif multiplier >= 1.7:
            return CongestionLevel.HIGH
        elif multiplier >= 1.3:
            return CongestionLevel.MODERATE
        else:
            return CongestionLevel.LOW

    def _add_minutes(self, dt: datetime, minutes: float) -> datetime:
        """Add minutes to a datetime"""
        from datetime import timedelta
        return dt + timedelta(minutes=minutes)

    def _generate_recommendations(self, hour: int, congestion: CongestionLevel) -> List[str]:
        """Generate traffic recommendations"""
        recommendations = []

        if congestion == CongestionLevel.SEVERE:
            recommendations.append("Consider delaying travel by 1-2 hours if possible")
            recommendations.append("Use public transportation for better reliability")
        elif congestion == CongestionLevel.HIGH:
            recommendations.append("Allow extra time for delays")
            recommendations.append("Consider alternate routes")
        elif congestion == CongestionLevel.MODERATE:
            recommendations.append("Normal traffic expected")
        else:
            recommendations.append("Optimal travel conditions")

        return recommendations
