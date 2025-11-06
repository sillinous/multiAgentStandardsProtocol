"""
MatchRidersToDriversLogisticsAgent - APQC 4.5.2
Intelligent Rider-Driver Matching Algorithm
APQC ID: apqc_4_5_m1a2t3c4

This agent implements intelligent matching algorithms considering preferences,
fairness, wait time optimization, and driver-rider compatibility.
"""

import os
import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2

from superstandard.agents.base.base_agent import BaseAgent
from library.core.protocols import ProtocolMixin


@dataclass
class MatchRidersToDriversLogisticsAgentConfig:
    apqc_agent_id: str = "apqc_4_5_m1a2t3c4"
    apqc_process_id: str = "4.5.2"
    agent_name: str = "match_riders_to_drivers_logistics_agent"
    agent_type: str = "operational"
    version: str = "1.0.0"


class MatchRidersToDriversLogisticsAgent(BaseAgent, ProtocolMixin):
    """
    APQC 4.5.2 - Match Riders to Drivers

    Skills:
    - matching_algorithm: 0.94 (optimal matching engine)
    - preference_learning: 0.90 (personalization)
    - fairness_optimization: 0.87 (equitable distribution)
    - wait_time_minimization: 0.85 (ETA optimization)

    Use Cases:
    - Match riders to optimal drivers
    - Balance driver earnings fairness
    - Minimize rider wait times
    - Handle rider preferences
    """

    VERSION = "1.0.0"
    APQC_PROCESS_ID = "4.5.2"

    def __init__(self, config: MatchRidersToDriversLogisticsAgentConfig):
        super().__init__(agent_id=config.apqc_agent_id, agent_type=config.agent_type, version=config.version)
        self.config = config
        self.skills = {
            'matching_algorithm': 0.94,
            'preference_learning': 0.90,
            'fairness_optimization': 0.87,
            'wait_time_minimization': 0.85
        }

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Match riders to optimal drivers

        Input:
        {
            "rider": {
                "rider_id": "RIDER001",
                "location": {"lat": 37.7749, "lng": -122.4194},
                "destination": {"lat": 37.3352, "lng": -121.8811},
                "preferences": {
                    "min_rating": 4.5,
                    "preferred_vehicle_type": "sedan",
                    "quiet_ride": false,
                    "accessibility_needs": []
                },
                "priority_level": "standard",
                "max_wait_time_minutes": 10
            },
            "available_drivers": [
                {
                    "driver_id": "DRV001",
                    "location": {"lat": 37.7849, "lng": -122.4094},
                    "rating": 4.8,
                    "completed_rides_today": 12,
                    "earnings_today": 350,
                    "vehicle_type": "sedan",
                    "acceptance_rate": 0.95,
                    "idle_time_minutes": 15
                }
            ],
            "fairness_settings": {
                "balance_earnings": true,
                "balance_ride_distribution": true,
                "prioritize_idle_drivers": true
            }
        }
        """
        rider = input_data.get('rider', {})
        available_drivers = input_data.get('available_drivers', [])
        fairness_settings = input_data.get('fairness_settings', {})

        # Calculate match scores for all drivers
        match_candidates = self._calculate_match_scores(rider, available_drivers, fairness_settings)

        # Select optimal match
        optimal_match = self._select_optimal_match(match_candidates, rider, fairness_settings)

        # Calculate alternative matches
        alternatives = self._calculate_alternatives(match_candidates, optimal_match)

        # Calculate fairness metrics
        fairness_metrics = self._calculate_fairness_metrics(match_candidates, optimal_match, available_drivers)

        # Generate match explanation
        explanation = self._generate_match_explanation(optimal_match, rider)

        return {
            "status": "completed",
            "apqc_process_id": self.APQC_PROCESS_ID,
            "timestamp": datetime.now().isoformat(),
            "output": {
                "optimal_match": optimal_match,
                "alternatives": alternatives,
                "fairness_metrics": fairness_metrics,
                "match_explanation": explanation,
                "summary": {
                    "matched_driver_id": optimal_match.get('driver_id'),
                    "match_quality_score": optimal_match.get('overall_score'),
                    "estimated_pickup_minutes": optimal_match.get('estimated_pickup_minutes'),
                    "confidence": optimal_match.get('confidence')
                }
            }
        }

    def _calculate_match_scores(
        self,
        rider: Dict[str, Any],
        drivers: List[Dict],
        fairness: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Calculate comprehensive match scores for all available drivers
        """
        rider_location = rider.get('location', {})
        preferences = rider.get('preferences', {})
        max_wait = rider.get('max_wait_time_minutes', 10)

        matches = []

        for driver in drivers:
            driver_location = driver.get('location', {})

            # 1. Distance Score (0-100, higher is better)
            distance_km = self._haversine_distance(
                rider_location['lat'], rider_location['lng'],
                driver_location['lat'], driver_location['lng']
            )

            # Convert distance to time (assume 40 km/h urban speed)
            eta_minutes = (distance_km / 40) * 60

            # Distance score: 100 at 0km, 0 at max_wait equivalent distance
            max_distance = (max_wait / 60) * 40
            distance_score = max(0, 100 - (distance_km / max_distance * 100))

            # 2. Rating Score (0-100)
            driver_rating = driver.get('rating', 4.0)
            min_rating = preferences.get('min_rating', 4.0)

            if driver_rating < min_rating:
                rating_score = 0  # Does not meet minimum
            else:
                rating_score = (driver_rating / 5.0) * 100

            # 3. Preference Match Score (0-100)
            vehicle_type = driver.get('vehicle_type', 'sedan')
            preferred_type = preferences.get('preferred_vehicle_type', 'any')

            if preferred_type == 'any' or vehicle_type == preferred_type:
                preference_score = 100
            else:
                preference_score = 60  # Partial match

            # 4. Fairness Score (0-100)
            fairness_score = self._calculate_fairness_score(driver, drivers, fairness)

            # 5. Reliability Score (0-100)
            acceptance_rate = driver.get('acceptance_rate', 0.9)
            reliability_score = acceptance_rate * 100

            # 6. Availability Score (0-100)
            # Prioritize drivers who have been idle longer
            idle_minutes = driver.get('idle_time_minutes', 0)
            availability_score = min(100, idle_minutes * 2)  # Max at 50 minutes idle

            # Calculate weighted overall score
            weights = {
                'distance': 0.35,
                'rating': 0.20,
                'preference': 0.15,
                'fairness': 0.15,
                'reliability': 0.10,
                'availability': 0.05
            }

            overall_score = (
                distance_score * weights['distance'] +
                rating_score * weights['rating'] +
                preference_score * weights['preference'] +
                fairness_score * weights['fairness'] +
                reliability_score * weights['reliability'] +
                availability_score * weights['availability']
            )

            # Calculate confidence based on data completeness
            confidence = 0.85  # Base confidence
            if driver_rating >= 4.5:
                confidence += 0.05
            if driver.get('completed_rides_today', 0) >= 10:
                confidence += 0.05
            if acceptance_rate >= 0.90:
                confidence += 0.05

            matches.append({
                'driver_id': driver['driver_id'],
                'overall_score': round(overall_score, 2),
                'component_scores': {
                    'distance': round(distance_score, 2),
                    'rating': round(rating_score, 2),
                    'preference': round(preference_score, 2),
                    'fairness': round(fairness_score, 2),
                    'reliability': round(reliability_score, 2),
                    'availability': round(availability_score, 2)
                },
                'distance_km': round(distance_km, 2),
                'estimated_pickup_minutes': round(eta_minutes, 1),
                'driver_rating': driver_rating,
                'vehicle_type': vehicle_type,
                'acceptance_rate': acceptance_rate,
                'confidence': round(confidence, 2),
                'meets_preferences': rating_score > 0 and preference_score >= 60,
                'within_wait_time': eta_minutes <= max_wait
            })

        # Sort by overall score
        matches.sort(key=lambda x: x['overall_score'], reverse=True)

        return matches

    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate great-circle distance between two points"""
        R = 6371  # Earth's radius in kilometers

        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        delta_lat = radians(lat2 - lat1)
        delta_lon = radians(lon2 - lon1)

        a = sin(delta_lat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))

        return R * c

    def _calculate_fairness_score(
        self,
        driver: Dict[str, Any],
        all_drivers: List[Dict],
        fairness_settings: Dict[str, Any]
    ) -> float:
        """
        Calculate fairness score to balance earnings and ride distribution
        """
        score = 50  # Base score

        if not fairness_settings:
            return score

        # Balance earnings
        if fairness_settings.get('balance_earnings', True):
            earnings_today = driver.get('earnings_today', 0)
            avg_earnings = np.mean([d.get('earnings_today', 0) for d in all_drivers])

            if earnings_today < avg_earnings:
                # Give boost to drivers with below-average earnings
                earnings_ratio = earnings_today / avg_earnings if avg_earnings > 0 else 1
                score += (1 - earnings_ratio) * 30  # Up to +30 points

        # Balance ride distribution
        if fairness_settings.get('balance_ride_distribution', True):
            rides_today = driver.get('completed_rides_today', 0)
            avg_rides = np.mean([d.get('completed_rides_today', 0) for d in all_drivers])

            if rides_today < avg_rides:
                rides_ratio = rides_today / avg_rides if avg_rides > 0 else 1
                score += (1 - rides_ratio) * 20  # Up to +20 points

        # Prioritize idle drivers
        if fairness_settings.get('prioritize_idle_drivers', True):
            idle_minutes = driver.get('idle_time_minutes', 0)
            if idle_minutes > 15:
                score += min(30, idle_minutes / 2)  # Up to +30 points

        return min(100, score)

    def _select_optimal_match(
        self,
        candidates: List[Dict],
        rider: Dict,
        fairness_settings: Dict
    ) -> Dict[str, Any]:
        """
        Select the optimal driver match from candidates
        """
        if not candidates:
            return {
                'driver_id': None,
                'status': 'no_match_found',
                'reason': 'no_available_drivers'
            }

        # Filter candidates that meet minimum requirements
        eligible = [
            c for c in candidates
            if c['meets_preferences'] and c['within_wait_time']
        ]

        if not eligible:
            # Relax constraints if no perfect match
            eligible = [c for c in candidates if c['within_wait_time']]

        if not eligible:
            # Still no match
            return {
                'driver_id': None,
                'status': 'no_match_found',
                'reason': 'no_drivers_within_wait_time'
            }

        # Select highest scoring eligible driver
        optimal = eligible[0]
        optimal['status'] = 'matched'
        optimal['match_timestamp'] = datetime.now().isoformat()

        return optimal

    def _calculate_alternatives(
        self,
        candidates: List[Dict],
        optimal_match: Dict
    ) -> List[Dict[str, Any]]:
        """
        Calculate alternative driver options
        """
        if not optimal_match.get('driver_id'):
            return []

        # Return top 3 alternatives (excluding optimal match)
        alternatives = [
            c for c in candidates
            if c['driver_id'] != optimal_match.get('driver_id')
        ][:3]

        return alternatives

    def _calculate_fairness_metrics(
        self,
        candidates: List[Dict],
        optimal_match: Dict,
        all_drivers: List[Dict]
    ) -> Dict[str, Any]:
        """
        Calculate fairness metrics for the matching decision
        """
        if not optimal_match.get('driver_id'):
            return {
                'fairness_score': 0,
                'earnings_balance_score': 0,
                'ride_distribution_score': 0
            }

        matched_driver_id = optimal_match['driver_id']
        matched_driver = next((d for d in all_drivers if d['driver_id'] == matched_driver_id), None)

        if not matched_driver:
            return {'fairness_score': 0}

        # Analyze earnings distribution
        earnings_list = [d.get('earnings_today', 0) for d in all_drivers]
        avg_earnings = np.mean(earnings_list)
        earnings_std = np.std(earnings_list)

        matched_earnings = matched_driver.get('earnings_today', 0)
        earnings_percentile = sum(1 for e in earnings_list if e <= matched_earnings) / len(earnings_list) * 100

        # Analyze ride distribution
        rides_list = [d.get('completed_rides_today', 0) for d in all_drivers]
        avg_rides = np.mean(rides_list)
        rides_std = np.std(rides_list)

        matched_rides = matched_driver.get('completed_rides_today', 0)
        rides_percentile = sum(1 for r in rides_list if r <= matched_rides) / len(rides_list) * 100

        # Overall fairness score (prefer matching drivers in lower percentiles)
        earnings_balance_score = (100 - earnings_percentile)
        ride_distribution_score = (100 - rides_percentile)

        fairness_score = (earnings_balance_score + ride_distribution_score) / 2

        return {
            'fairness_score': round(fairness_score, 1),
            'earnings_balance_score': round(earnings_balance_score, 1),
            'ride_distribution_score': round(ride_distribution_score, 1),
            'matched_driver_earnings_percentile': round(earnings_percentile, 1),
            'matched_driver_rides_percentile': round(rides_percentile, 1),
            'promotes_equity': earnings_percentile < 60 or rides_percentile < 60
        }

    def _generate_match_explanation(
        self,
        optimal_match: Dict,
        rider: Dict
    ) -> Dict[str, Any]:
        """
        Generate human-readable explanation for the match
        """
        if not optimal_match.get('driver_id'):
            return {
                'summary': 'No suitable drivers available',
                'reasons': ['All drivers are either too far or do not meet requirements']
            }

        reasons = []

        # Distance reason
        if optimal_match['component_scores']['distance'] >= 80:
            reasons.append(f"Driver is very close ({optimal_match['distance_km']:.1f} km away)")
        elif optimal_match['component_scores']['distance'] >= 60:
            reasons.append(f"Driver is reasonably close ({optimal_match['distance_km']:.1f} km away)")

        # Rating reason
        if optimal_match['component_scores']['rating'] >= 90:
            reasons.append(f"Highly rated driver ({optimal_match['driver_rating']:.1f}/5.0)")

        # Preference reason
        if optimal_match['component_scores']['preference'] >= 90:
            reasons.append(f"Matches your preferred vehicle type ({optimal_match['vehicle_type']})")

        # Fairness reason
        if optimal_match['component_scores']['fairness'] >= 80:
            reasons.append("Driver has been waiting for a ride (fair distribution)")

        # Reliability reason
        if optimal_match['component_scores']['reliability'] >= 90:
            reasons.append(f"High acceptance rate ({optimal_match['acceptance_rate']:.0%})")

        summary = f"Best match: {optimal_match['overall_score']:.0f}/100 score, {optimal_match['estimated_pickup_minutes']:.0f} min ETA"

        return {
            'summary': summary,
            'reasons': reasons,
            'match_quality': 'excellent' if optimal_match['overall_score'] >= 85 else \
                           'good' if optimal_match['overall_score'] >= 70 else 'fair',
            'confidence': optimal_match['confidence']
        }

    def get_input_schema(self) -> Dict[str, Any]:
        """Return input schema for rider-driver matching"""
        return {
            "type": "object",
            "required": ["rider", "available_drivers"],
            "properties": {
                "rider": {"type": "object"},
                "available_drivers": {"type": "array"},
                "fairness_settings": {"type": "object"}
            }
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """Return output schema"""
        return {
            "type": "object",
            "properties": {
                "optimal_match": {"type": "object"},
                "alternatives": {"type": "array"},
                "fairness_metrics": {"type": "object"},
                "match_explanation": {"type": "object"}
            }
        }


def create_match_riders_to_drivers_logistics_agent() -> MatchRidersToDriversLogisticsAgent:
    """Factory function to create MatchRidersToDriversLogisticsAgent"""
    config = MatchRidersToDriversLogisticsAgentConfig()
    return MatchRidersToDriversLogisticsAgent(config)
