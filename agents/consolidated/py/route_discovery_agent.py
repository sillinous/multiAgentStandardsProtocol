"""
Route Discovery Agent for Mobility Routing Swarm

Calculates optimal routes using nearest-neighbor and greedy optimization algorithms.
"""

import math
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from agents.base_agent import BaseAgent, AgentCapability


@dataclass
class RouteSegment:
    """A segment of a route"""
    from_location: Tuple[float, float]
    to_location: Tuple[float, float]
    distance_km: float
    duration_minutes: float
    cost_estimate: float


class RouteDiscoveryAgent(BaseAgent):
    """
    Agent responsible for discovering and optimizing routes.
    Uses nearest-neighbor and greedy optimization algorithms.
    """

    def __init__(self, agent_id: str = "route_discovery_agent", workspace_path: str = "./autonomous-ecosystem/workspace"):
        super().__init__(
            agent_id=agent_id,
            agent_type="route_discovery",
            capabilities=[AgentCapability.ORCHESTRATION],
            workspace_path=workspace_path
        )

        # Configuration
        self.avg_speed_kmh = 40.0
        self.cost_per_km = 1.5
        self.max_stops = 10

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute route discovery task

        Args:
            task: Task with 'action' and parameters

        Returns:
            Task execution result
        """
        action = task.get("action")

        if action == "calculate_route":
            return await self._handle_route_calculation(task)
        elif action == "estimate_time":
            return await self._handle_time_estimation(task)
        elif action == "find_alternatives":
            return await self._handle_alternative_routes(task)
        else:
            return {
                "success": False,
                "error": f"Unknown action: {action}"
            }

    async def analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze route options and provide insights

        Args:
            input_data: Route data to analyze

        Returns:
            Analysis results with recommendations
        """
        route = input_data.get("route", [])

        if not route:
            return {
                "timestamp": datetime.now().isoformat(),
                "total_stops": 0,
                "total_distance_km": 0.0,
                "recommendations": ["No route to analyze"]
            }

        # Calculate route metrics
        total_distance = 0.0
        for i in range(len(route) - 1):
            distance = self._calculate_distance(
                tuple(route[i]),
                tuple(route[i + 1])
            )
            total_distance += distance

        total_time = (total_distance / self.avg_speed_kmh) * 60
        efficiency_score = self._calculate_efficiency_score(route, total_distance)

        analysis = {
            "timestamp": datetime.now().isoformat(),
            "total_stops": len(route),
            "total_distance_km": round(total_distance, 2),
            "estimated_time_minutes": round(total_time, 2),
            "efficiency_score": round(efficiency_score, 3),
            "recommendations": self._generate_route_recommendations(route, efficiency_score)
        }

        return analysis

    def calculate_optimal_route(
        self,
        stops: List[Tuple[float, float]],
        start_location: Optional[Tuple[float, float]] = None
    ) -> Dict[str, Any]:
        """
        Calculate optimal route through multiple stops using nearest-neighbor algorithm

        Args:
            stops: List of (lat, lon) waypoints to visit
            start_location: Starting point (if None, use first stop)

        Returns:
            Optimized route with sequence and metrics
        """
        if not stops:
            return {
                "route": [],
                "sequence": [],
                "total_distance_km": 0.0,
                "total_time_minutes": 0.0
            }

        # Start from specified location or first stop
        current = start_location if start_location else stops[0]
        remaining = stops.copy()

        if start_location:
            route = [start_location]
            sequence = []
        else:
            route = [stops[0]]
            remaining.remove(stops[0])
            sequence = [0]

        total_distance = 0.0

        # Nearest-neighbor algorithm
        while remaining:
            # Find nearest unvisited stop
            nearest = min(
                remaining,
                key=lambda stop: self._calculate_distance(current, stop)
            )

            distance = self._calculate_distance(current, nearest)
            total_distance += distance

            route.append(nearest)
            sequence.append(stops.index(nearest))
            remaining.remove(nearest)
            current = nearest

        # Calculate total time
        total_time = (total_distance / self.avg_speed_kmh) * 60

        return {
            "route": route,
            "sequence": sequence,
            "total_distance_km": round(total_distance, 2),
            "total_time_minutes": round(total_time, 2),
            "stops": len(stops),
            "algorithm": "nearest_neighbor"
        }

    def estimate_total_time(
        self,
        route: List[Tuple[float, float]],
        traffic_multiplier: float = 1.0
    ) -> Dict[str, Any]:
        """
        Estimate total travel time for a route

        Args:
            route: List of (lat, lon) waypoints
            traffic_multiplier: Traffic delay factor (1.0 = normal, 2.0 = double time)

        Returns:
            Time estimation with breakdown
        """
        if len(route) < 2:
            return {
                "total_time_minutes": 0.0,
                "segments": [],
                "traffic_adjusted": False
            }

        segments = []
        total_distance = 0.0

        for i in range(len(route) - 1):
            distance = self._calculate_distance(route[i], route[i + 1])
            base_time = (distance / self.avg_speed_kmh) * 60
            adjusted_time = base_time * traffic_multiplier

            segments.append({
                "from": route[i],
                "to": route[i + 1],
                "distance_km": round(distance, 2),
                "base_time_minutes": round(base_time, 2),
                "adjusted_time_minutes": round(adjusted_time, 2)
            })

            total_distance += distance

        total_base_time = (total_distance / self.avg_speed_kmh) * 60
        total_adjusted_time = total_base_time * traffic_multiplier

        return {
            "total_time_minutes": round(total_adjusted_time, 2),
            "base_time_minutes": round(total_base_time, 2),
            "total_distance_km": round(total_distance, 2),
            "traffic_multiplier": traffic_multiplier,
            "segments": segments,
            "traffic_adjusted": traffic_multiplier != 1.0
        }

    def get_alternative_routes(
        self,
        route: List[Tuple[float, float]],
        num_alternatives: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Generate alternative routes by varying the stop order

        Args:
            route: Original route waypoints
            num_alternatives: Number of alternatives to generate

        Returns:
            List of alternative route options
        """
        if len(route) < 3:
            return []

        alternatives = []

        # Try different optimization strategies
        # Alternative 1: Reverse some segments
        if len(route) >= 4:
            alt_route = route.copy()
            mid = len(alt_route) // 2
            alt_route[1:mid] = reversed(alt_route[1:mid])
            alt_metrics = self.estimate_total_time(alt_route)
            alternatives.append({
                "route": alt_route,
                "strategy": "segment_reversal",
                "metrics": alt_metrics
            })

        # Alternative 2: 2-opt improvement (swap edges)
        if len(route) >= 4:
            alt_route = self._two_opt_improvement(route)
            alt_metrics = self.estimate_total_time(alt_route)
            alternatives.append({
                "route": alt_route,
                "strategy": "2opt_optimization",
                "metrics": alt_metrics
            })

        # Alternative 3: Different starting point
        if len(route) >= 4:
            start_idx = len(route) // 3
            alt_route = route[start_idx:] + route[:start_idx]
            alt_metrics = self.estimate_total_time(alt_route)
            alternatives.append({
                "route": alt_route,
                "strategy": "alternate_start",
                "metrics": alt_metrics
            })

        return alternatives[:num_alternatives]

    async def _handle_route_calculation(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle route calculation task"""
        stops = task.get("stops", [])
        start_location = task.get("start_location")

        route_result = self.calculate_optimal_route(stops, start_location)

        return {
            "success": True,
            "route": route_result,
            "agent_id": self.agent_id
        }

    async def _handle_time_estimation(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle time estimation task"""
        route = task.get("route", [])
        traffic_multiplier = task.get("traffic_multiplier", 1.0)

        estimation = self.estimate_total_time(route, traffic_multiplier)

        return {
            "success": True,
            "estimation": estimation,
            "agent_id": self.agent_id
        }

    async def _handle_alternative_routes(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle alternative route finding task"""
        route = task.get("route", [])
        num_alternatives = task.get("num_alternatives", 3)

        alternatives = self.get_alternative_routes(route, num_alternatives)

        return {
            "success": True,
            "alternatives": alternatives,
            "count": len(alternatives),
            "agent_id": self.agent_id
        }

    def _calculate_distance(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """Calculate distance using Haversine formula"""
        lat1, lon1 = point1
        lat2, lon2 = point2

        R = 6371  # Earth radius in km

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) ** 2)

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def _two_opt_improvement(self, route: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """
        Apply 2-opt improvement to route
        Swaps edges to reduce total distance
        """
        improved_route = route.copy()
        improved = True

        while improved:
            improved = False
            for i in range(1, len(improved_route) - 2):
                for j in range(i + 1, len(improved_route) - 1):
                    # Calculate current distance
                    current_dist = (
                        self._calculate_distance(improved_route[i - 1], improved_route[i]) +
                        self._calculate_distance(improved_route[j], improved_route[j + 1])
                    )

                    # Calculate distance after swap
                    new_dist = (
                        self._calculate_distance(improved_route[i - 1], improved_route[j]) +
                        self._calculate_distance(improved_route[i], improved_route[j + 1])
                    )

                    # If improvement found, apply swap
                    if new_dist < current_dist:
                        improved_route[i:j + 1] = reversed(improved_route[i:j + 1])
                        improved = True
                        break

                if improved:
                    break

        return improved_route

    def _calculate_efficiency_score(self, route: List[Tuple[float, float]], total_distance: float) -> float:
        """
        Calculate route efficiency score (0-1, higher is better)
        Based on straightness and number of stops
        """
        if len(route) < 2:
            return 0.0

        # Calculate direct distance from start to end
        direct_distance = self._calculate_distance(route[0], route[-1])

        # Straightness factor: how close is the route to a straight line
        if total_distance > 0:
            straightness = direct_distance / total_distance
        else:
            straightness = 0.0

        # Stops penalty: fewer stops is better
        stops_factor = 1.0 - (len(route) / self.max_stops)
        stops_factor = max(0.0, stops_factor)

        # Combined score
        efficiency = 0.6 * straightness + 0.4 * stops_factor

        return min(1.0, efficiency)

    def _generate_route_recommendations(self, route: List[Tuple[float, float]], efficiency_score: float) -> List[str]:
        """Generate route recommendations"""
        recommendations = []

        if efficiency_score < 0.5:
            recommendations.append("Route has many detours - consider direct alternatives")

        if len(route) > 8:
            recommendations.append("Route has many stops - consider splitting into multiple trips")

        if efficiency_score >= 0.75:
            recommendations.append("Route is well optimized")

        if len(route) >= 3:
            recommendations.append("Consider using 2-opt optimization to reduce distance")

        return recommendations
