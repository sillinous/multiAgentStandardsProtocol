"""
DispatchManagementLogisticsAgent - APQC 4.5.1
Manage Transportation Dispatch and Driver Assignment
APQC ID: apqc_4_5_d1s2p3a4

Real-time dispatch optimization for ride-sharing platforms with intelligent
driver assignment, load balancing, and surge pricing triggers.
"""

import os
import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import heapq

from library.core.base_agent import BaseAgent
from library.core.protocols import ProtocolMixin


@dataclass
class DispatchManagementLogisticsAgentConfig:
    apqc_agent_id: str = "apqc_4_5_d1s2p3a4"
    apqc_process_id: str = "4.5.1"
    agent_name: str = "dispatch_management_logistics_agent"
    agent_type: str = "operational"
    version: str = "1.0.0"


class DispatchManagementLogisticsAgent(BaseAgent, ProtocolMixin):
    """
    APQC 4.5.1 - Manage Transportation Dispatch

    Skills:
    - assignment_optimization: 0.94 (optimal driver-rider matching)
    - capacity_management: 0.91 (fleet utilization)
    - demand_matching: 0.89 (supply-demand balancing)
    - surge_detection: 0.87 (dynamic pricing triggers)

    Use Cases:
    - Real-time driver assignment
    - Load balancing across fleet
    - Surge pricing activation
    - Wait time minimization
    """

    VERSION = "1.0.0"
    APQC_PROCESS_ID = "4.5.1"

    def __init__(self, config: DispatchManagementLogisticsAgentConfig):
        super().__init__(agent_id=config.apqc_agent_id, agent_type=config.agent_type, version=config.version)
        self.config = config
        self.skills = {
            'assignment_optimization': 0.94,
            'capacity_management': 0.91,
            'demand_matching': 0.89,
            'surge_detection': 0.87
        }

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize dispatch operations

        Input:
        {
            "ride_requests": [
                {
                    "request_id": "REQ001",
                    "rider_location": {"lat": 37.7749, "lng": -122.4194},
                    "destination": {"lat": 37.3352, "lng": -121.8811},
                    "requested_at": "2025-10-18T14:30:00",
                    "priority": "standard",
                    "passenger_count": 2
                }
            ],
            "available_drivers": [
                {
                    "driver_id": "DRV001",
                    "location": {"lat": 37.7849, "lng": -122.4094},
                    "status": "available",
                    "rating": 4.8,
                    "vehicle_capacity": 4,
                    "acceptance_rate": 0.95
                }
            ],
            "market_conditions": {
                "active_requests": 50,
                "available_drivers": 30,
                "average_wait_time_minutes": 8
            }
        }
        """
        ride_requests = input_data.get('ride_requests', [])
        available_drivers = input_data.get('available_drivers', [])
        market_conditions = input_data.get('market_conditions', {})

        # Perform driver assignment
        assignments = self._optimize_driver_assignment(ride_requests, available_drivers)

        # Analyze capacity and utilization
        capacity_analysis = self._analyze_capacity(available_drivers, ride_requests, market_conditions)

        # Detect surge pricing needs
        surge_analysis = self._analyze_surge_conditions(market_conditions, assignments)

        # Calculate dispatch metrics
        metrics = self._calculate_dispatch_metrics(assignments, capacity_analysis, surge_analysis)

        return {
            "status": "completed",
            "apqc_process_id": self.APQC_PROCESS_ID,
            "timestamp": datetime.now().isoformat(),
            "output": {
                "driver_assignments": assignments,
                "capacity_analysis": capacity_analysis,
                "surge_analysis": surge_analysis,
                "dispatch_metrics": metrics,
                "recommendations": self._generate_recommendations(capacity_analysis, surge_analysis)
            }
        }

    def _optimize_driver_assignment(
        self,
        requests: List[Dict],
        drivers: List[Dict]
    ) -> List[Dict[str, Any]]:
        """
        Assign drivers to ride requests using Hungarian algorithm approximation
        """
        assignments = []

        # Create cost matrix (distance + wait time)
        for request in requests:
            best_driver = None
            min_cost = float('inf')

            for driver in drivers:
                if driver['status'] != 'available':
                    continue

                # Calculate assignment cost
                cost = self._calculate_assignment_cost(request, driver)

                if cost < min_cost:
                    min_cost = cost
                    best_driver = driver

            if best_driver:
                # Calculate ETA to pickup
                pickup_distance = self._calculate_distance(
                    driver['location']['lat'], driver['location']['lng'],
                    request['rider_location']['lat'], request['rider_location']['lng']
                )
                pickup_time_minutes = (pickup_distance / 40) * 60  # 40 km/h urban average

                assignment = {
                    'request_id': request['request_id'],
                    'driver_id': best_driver['driver_id'],
                    'assignment_cost': round(min_cost, 2),
                    'pickup_distance_km': round(pickup_distance, 2),
                    'estimated_pickup_minutes': round(pickup_time_minutes, 1),
                    'driver_rating': best_driver['rating'],
                    'match_quality': self._calculate_match_quality(request, best_driver, pickup_distance),
                    'assigned_at': datetime.now().isoformat()
                }

                assignments.append(assignment)

                # Mark driver as assigned (in practice, would update database)
                best_driver['status'] = 'assigned'

        # Handle unassigned requests
        assigned_ids = {a['request_id'] for a in assignments}
        for request in requests:
            if request['request_id'] not in assigned_ids:
                assignments.append({
                    'request_id': request['request_id'],
                    'driver_id': None,
                    'status': 'unassigned',
                    'reason': 'no_available_drivers',
                    'wait_queue_position': len(assignments) + 1
                })

        return assignments

    def _calculate_assignment_cost(self, request: Dict, driver: Dict) -> float:
        """
        Calculate cost of assigning driver to request
        Lower is better
        """
        # Distance to pickup
        distance = self._calculate_distance(
            driver['location']['lat'], driver['location']['lng'],
            request['rider_location']['lat'], request['rider_location']['lng']
        )

        # Time component
        time_cost = distance / 40  # Normalize by speed

        # Quality penalties
        rating_penalty = (5.0 - driver['rating']) * 0.5  # Penalize lower ratings
        acceptance_penalty = (1.0 - driver.get('acceptance_rate', 0.9)) * 2  # Penalize low acceptance

        # Priority adjustment
        priority_multiplier = {
            'urgent': 0.5,
            'standard': 1.0,
            'economy': 1.5
        }.get(request.get('priority', 'standard'), 1.0)

        total_cost = (time_cost + rating_penalty + acceptance_penalty) * priority_multiplier

        return total_cost

    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Haversine distance in km"""
        from math import radians, sin, cos, sqrt, atan2

        R = 6371
        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        delta_lat = radians(lat2 - lat1)
        delta_lon = radians(lon2 - lon1)

        a = sin(delta_lat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))

        return R * c

    def _calculate_match_quality(self, request: Dict, driver: Dict, distance: float) -> str:
        """
        Calculate match quality score
        """
        score = 100

        # Distance penalty (prefer closer drivers)
        if distance > 5:
            score -= (distance - 5) * 5

        # Rating bonus
        score += (driver['rating'] - 4.0) * 10

        # Acceptance rate bonus
        score += (driver.get('acceptance_rate', 0.9) - 0.8) * 20

        # Capacity check
        if driver['vehicle_capacity'] < request.get('passenger_count', 1):
            score -= 50

        score = max(0, min(100, score))

        if score >= 85:
            return 'excellent'
        elif score >= 70:
            return 'good'
        elif score >= 50:
            return 'fair'
        else:
            return 'poor'

    def _analyze_capacity(
        self,
        drivers: List[Dict],
        requests: List[Dict],
        market: Dict
    ) -> Dict[str, Any]:
        """
        Analyze fleet capacity and utilization
        """
        total_drivers = len(drivers)
        available_drivers = sum(1 for d in drivers if d['status'] == 'available')
        total_requests = len(requests)

        # Supply-demand ratio
        supply_demand_ratio = available_drivers / total_requests if total_requests > 0 else float('inf')

        # Utilization rate
        utilization_rate = (total_drivers - available_drivers) / total_drivers if total_drivers > 0 else 0

        # Capacity status
        if supply_demand_ratio < 0.6:
            capacity_status = 'constrained'
            capacity_health = 'critical'
        elif supply_demand_ratio < 1.0:
            capacity_status = 'tight'
            capacity_health = 'warning'
        elif supply_demand_ratio < 1.5:
            capacity_status = 'balanced'
            capacity_health = 'healthy'
        else:
            capacity_status = 'surplus'
            capacity_health = 'optimal'

        return {
            'total_drivers': total_drivers,
            'available_drivers': available_drivers,
            'total_requests': total_requests,
            'supply_demand_ratio': round(supply_demand_ratio, 2),
            'utilization_rate': round(utilization_rate, 2),
            'capacity_status': capacity_status,
            'capacity_health': capacity_health,
            'estimated_wait_time_minutes': market.get('average_wait_time_minutes', 0)
        }

    def _analyze_surge_conditions(
        self,
        market: Dict,
        assignments: List[Dict]
    ) -> Dict[str, Any]:
        """
        Analyze if surge pricing should be activated
        """
        active_requests = market.get('active_requests', 0)
        available_drivers = market.get('available_drivers', 0)
        avg_wait_time = market.get('average_wait_time_minutes', 0)

        # Calculate surge multiplier
        if available_drivers == 0:
            surge_multiplier = 2.5
        else:
            demand_supply_ratio = active_requests / available_drivers

            if demand_supply_ratio > 2.0:
                surge_multiplier = 2.0
            elif demand_supply_ratio > 1.5:
                surge_multiplier = 1.5
            elif demand_supply_ratio > 1.2:
                surge_multiplier = 1.25
            else:
                surge_multiplier = 1.0

        # Wait time factor
        if avg_wait_time > 15:
            surge_multiplier = max(surge_multiplier, 1.5)
        elif avg_wait_time > 10:
            surge_multiplier = max(surge_multiplier, 1.25)

        surge_active = surge_multiplier > 1.0

        # Unassigned requests
        unassigned_count = sum(1 for a in assignments if a.get('driver_id') is None)

        return {
            'surge_active': surge_active,
            'surge_multiplier': round(surge_multiplier, 2),
            'demand_supply_ratio': round(active_requests / available_drivers, 2) if available_drivers > 0 else 999,
            'average_wait_time_minutes': avg_wait_time,
            'unassigned_requests': unassigned_count,
            'surge_reason': self._get_surge_reason(surge_multiplier, avg_wait_time, unassigned_count)
        }

    def _get_surge_reason(self, multiplier: float, wait_time: float, unassigned: int) -> str:
        """Determine primary reason for surge"""
        if multiplier <= 1.0:
            return 'normal_operations'
        elif unassigned > 5:
            return 'high_unassigned_requests'
        elif wait_time > 15:
            return 'extended_wait_times'
        else:
            return 'high_demand'

    def _calculate_dispatch_metrics(
        self,
        assignments: List[Dict],
        capacity: Dict,
        surge: Dict
    ) -> Dict[str, Any]:
        """
        Calculate key dispatch performance metrics
        """
        total_assignments = len([a for a in assignments if a.get('driver_id')])
        total_requests = len(assignments)

        assignment_rate = total_assignments / total_requests if total_requests > 0 else 0

        # Average pickup time
        pickup_times = [a['estimated_pickup_minutes'] for a in assignments if 'estimated_pickup_minutes' in a]
        avg_pickup_time = np.mean(pickup_times) if pickup_times else 0

        # Match quality distribution
        quality_counts = {}
        for a in assignments:
            quality = a.get('match_quality', 'unknown')
            quality_counts[quality] = quality_counts.get(quality, 0) + 1

        return {
            'assignment_rate': round(assignment_rate, 2),
            'total_assignments': total_assignments,
            'total_requests': total_requests,
            'average_pickup_time_minutes': round(avg_pickup_time, 1),
            'match_quality_distribution': quality_counts,
            'surge_multiplier': surge['surge_multiplier'],
            'utilization_rate': capacity['utilization_rate']
        }

    def _generate_recommendations(self, capacity: Dict, surge: Dict) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        if capacity['capacity_health'] == 'critical':
            recommendations.append("URGENT: Activate driver incentives to increase supply")
            recommendations.append("Consider increasing surge multiplier to reduce demand")

        if surge['surge_active']:
            recommendations.append(f"Surge pricing active at {surge['surge_multiplier']}x - monitor closely")
            recommendations.append("Send notifications to offline drivers in high-demand areas")

        if capacity['supply_demand_ratio'] > 2.0:
            recommendations.append("Surplus capacity detected - consider promotional discounts")
            recommendations.append("Reduce driver idle time with proactive positioning")

        if surge['average_wait_time_minutes'] > 10:
            recommendations.append("Average wait time elevated - optimize driver positioning")

        if not recommendations:
            recommendations.append("Operations running smoothly - maintain current strategy")

        return recommendations

    def get_input_schema(self) -> Dict[str, Any]:
        """Return input schema"""
        return {
            "type": "object",
            "required": ["ride_requests", "available_drivers"],
            "properties": {
                "ride_requests": {"type": "array"},
                "available_drivers": {"type": "array"},
                "market_conditions": {"type": "object"}
            }
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """Return output schema"""
        return {
            "type": "object",
            "properties": {
                "driver_assignments": {"type": "array"},
                "capacity_analysis": {"type": "object"},
                "surge_analysis": {"type": "object"},
                "dispatch_metrics": {"type": "object"}
            }
        }


def create_dispatch_management_logistics_agent() -> DispatchManagementLogisticsAgent:
    """Factory function"""
    config = DispatchManagementLogisticsAgentConfig()
    return DispatchManagementLogisticsAgent(config)
