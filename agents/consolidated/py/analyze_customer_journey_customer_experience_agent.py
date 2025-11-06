"""
AnalyzeCustomerJourneyCustomerExperienceAgent - APQC 6.1.3
Analyze Customer Journey and Experience Metrics
APQC ID: apqc_6_1_a1c2j3u4

This agent analyzes the complete customer journey from app open to ride completion,
identifying friction points, satisfaction drivers, churn risk, and optimization opportunities.
"""

import os
import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

from superstandard.agents.base.base_agent import BaseAgent
from library.core.protocols import ProtocolMixin


@dataclass
class AnalyzeCustomerJourneyCustomerExperienceAgentConfig:
    apqc_agent_id: str = "apqc_6_1_a1c2j3u4"
    apqc_process_id: str = "6.1.3"
    agent_name: str = "analyze_customer_journey_customer_experience_agent"
    agent_type: str = "analytical"
    version: str = "1.0.0"


class AnalyzeCustomerJourneyCustomerExperienceAgent(BaseAgent, ProtocolMixin):
    """
    APQC 6.1.3 - Analyze Customer Journey

    Skills:
    - journey_mapping: 0.90 (touchpoint analysis)
    - satisfaction_modeling: 0.88 (NPS and CSAT prediction)
    - churn_prediction: 0.86 (customer retention forecasting)
    - touchpoint_analysis: 0.84 (friction point identification)

    Use Cases:
    - Map complete customer journey
    - Identify experience friction points
    - Predict customer churn
    - Optimize touchpoint experiences
    """

    VERSION = "1.0.0"
    APQC_PROCESS_ID = "6.1.3"

    def __init__(self, config: AnalyzeCustomerJourneyCustomerExperienceAgentConfig):
        super().__init__(agent_id=config.apqc_agent_id, agent_type=config.agent_type, version=config.version)
        self.config = config
        self.skills = {
            'journey_mapping': 0.90,
            'satisfaction_modeling': 0.88,
            'churn_prediction': 0.86,
            'touchpoint_analysis': 0.84
        }

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze customer journey and experience

        Input:
        {
            "customer_id": "CUST12345",
            "journey_data": {
                "app_opens_last_30_days": 25,
                "searches_last_30_days": 20,
                "completed_rides_last_30_days": 15,
                "cancellations_last_30_days": 2,
                "average_wait_time_minutes": 6.5,
                "average_ride_rating": 4.6,
                "payment_failures": 1,
                "support_contacts": 1
            },
            "touchpoint_performance": {
                "app_load_time_seconds": 2.1,
                "search_to_match_seconds": 45,
                "driver_arrival_accuracy": 0.88,
                "ride_completion_success_rate": 0.94,
                "payment_success_rate": 0.97
            },
            "satisfaction_metrics": {
                "nps_score": 8,
                "overall_satisfaction": 4.5,
                "likelihood_to_recommend": 0.85,
                "last_feedback_sentiment": "positive"
            },
            "customer_profile": {
                "account_age_days": 450,
                "lifetime_rides": 145,
                "lifetime_value": 4250,
                "preferred_payment_method": "credit_card",
                "last_ride_days_ago": 3
            }
        }
        """
        customer_id = input_data.get('customer_id')
        journey_data = input_data.get('journey_data', {})
        touchpoint_perf = input_data.get('touchpoint_performance', {})
        satisfaction = input_data.get('satisfaction_metrics', {})
        profile = input_data.get('customer_profile', {})

        # Map customer journey stages
        journey_map = self._map_customer_journey(journey_data, touchpoint_perf)

        # Analyze satisfaction drivers
        satisfaction_analysis = self._analyze_satisfaction_drivers(satisfaction, journey_data, profile)

        # Predict churn risk
        churn_prediction = self._predict_churn_risk(journey_data, satisfaction, profile)

        # Identify friction points
        friction_points = self._identify_friction_points(journey_map, touchpoint_perf, journey_data)

        # Generate optimization recommendations
        recommendations = self._generate_journey_recommendations(friction_points, churn_prediction, journey_map)

        # Calculate customer health score
        health_score = self._calculate_customer_health(journey_data, satisfaction, profile, churn_prediction)

        return {
            "status": "completed",
            "apqc_process_id": self.APQC_PROCESS_ID,
            "timestamp": datetime.now().isoformat(),
            "output": {
                "customer_id": customer_id,
                "journey_map": journey_map,
                "satisfaction_analysis": satisfaction_analysis,
                "churn_prediction": churn_prediction,
                "friction_points": friction_points,
                "recommendations": recommendations,
                "customer_health_score": health_score,
                "summary": {
                    "health_status": health_score['status'],
                    "churn_risk": churn_prediction['risk_level'],
                    "primary_friction_point": friction_points[0]['stage'] if friction_points else 'none',
                    "nps_score": satisfaction.get('nps_score', 0)
                }
            }
        }

    def _map_customer_journey(
        self,
        journey_data: Dict[str, Any],
        touchpoint_perf: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Map the complete customer journey with performance metrics
        """
        # Define journey stages
        stages = []

        # Stage 1: App Discovery & Download (not tracked in this data)
        # Stage 2: Account Creation & Onboarding (historical)

        # Stage 3: Search & Request
        app_opens = journey_data.get('app_opens_last_30_days', 0)
        searches = journey_data.get('searches_last_30_days', 0)
        search_to_request_rate = (searches / app_opens) if app_opens > 0 else 0

        stages.append({
            'stage_number': 1,
            'stage_name': 'Search & Request',
            'touchpoints': ['app_open', 'location_entry', 'destination_entry', 'ride_request'],
            'performance_metrics': {
                'app_load_time_seconds': touchpoint_perf.get('app_load_time_seconds', 0),
                'search_to_match_seconds': touchpoint_perf.get('search_to_match_seconds', 0),
                'search_to_request_conversion': round(search_to_request_rate, 2)
            },
            'completion_rate': round(search_to_request_rate, 2),
            'avg_duration_seconds': touchpoint_perf.get('search_to_match_seconds', 0),
            'friction_indicators': {
                'slow_app_load': touchpoint_perf.get('app_load_time_seconds', 0) > 3,
                'long_matching_time': touchpoint_perf.get('search_to_match_seconds', 0) > 60
            }
        })

        # Stage 4: Driver Match & Acceptance
        completed_rides = journey_data.get('completed_rides_last_30_days', 0)
        match_to_ride_rate = (completed_rides / searches) if searches > 0 else 0

        stages.append({
            'stage_number': 2,
            'stage_name': 'Driver Match & Acceptance',
            'touchpoints': ['driver_match', 'driver_acceptance', 'pickup_notification'],
            'performance_metrics': {
                'match_success_rate': round(match_to_ride_rate, 2),
                'average_wait_time_minutes': journey_data.get('average_wait_time_minutes', 0)
            },
            'completion_rate': round(match_to_ride_rate, 2),
            'avg_duration_seconds': journey_data.get('average_wait_time_minutes', 0) * 60,
            'friction_indicators': {
                'high_wait_time': journey_data.get('average_wait_time_minutes', 0) > 8,
                'low_match_rate': match_to_ride_rate < 0.8
            }
        })

        # Stage 5: Pickup & Ride
        cancellations = journey_data.get('cancellations_last_30_days', 0)
        total_attempts = completed_rides + cancellations
        ride_completion_rate = (completed_rides / total_attempts) if total_attempts > 0 else 0

        stages.append({
            'stage_number': 3,
            'stage_name': 'Pickup & Ride Experience',
            'touchpoints': ['driver_arrival', 'ride_start', 'in_ride_experience', 'destination_arrival'],
            'performance_metrics': {
                'driver_arrival_accuracy': touchpoint_perf.get('driver_arrival_accuracy', 0),
                'ride_completion_rate': round(ride_completion_rate, 2),
                'average_rating': journey_data.get('average_ride_rating', 0)
            },
            'completion_rate': round(ride_completion_rate, 2),
            'avg_duration_seconds': 1800,  # Estimated 30 min average
            'friction_indicators': {
                'poor_arrival_accuracy': touchpoint_perf.get('driver_arrival_accuracy', 0) < 0.85,
                'low_ratings': journey_data.get('average_ride_rating', 0) < 4.5
            }
        })

        # Stage 6: Payment & Post-Ride
        payment_success = touchpoint_perf.get('payment_success_rate', 0)
        payment_failures = journey_data.get('payment_failures', 0)

        stages.append({
            'stage_number': 4,
            'stage_name': 'Payment & Post-Ride',
            'touchpoints': ['payment_processing', 'receipt', 'rating', 'tip'],
            'performance_metrics': {
                'payment_success_rate': payment_success,
                'payment_failures_count': payment_failures
            },
            'completion_rate': payment_success,
            'avg_duration_seconds': 30,
            'friction_indicators': {
                'payment_issues': payment_failures > 0 or payment_success < 0.95
            }
        })

        # Calculate overall journey metrics
        overall_completion = (
            stages[0]['completion_rate'] *
            stages[1]['completion_rate'] *
            stages[2]['completion_rate'] *
            stages[3]['completion_rate']
        )

        return {
            'stages': stages,
            'total_stages': len(stages),
            'overall_completion_rate': round(overall_completion, 3),
            'total_journey_duration_minutes': sum(s['avg_duration_seconds'] for s in stages) / 60,
            'stages_with_friction': sum(1 for s in stages if any(s['friction_indicators'].values()))
        }

    def _analyze_satisfaction_drivers(
        self,
        satisfaction: Dict[str, Any],
        journey_data: Dict[str, Any],
        profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze key drivers of customer satisfaction
        """
        nps_score = satisfaction.get('nps_score', 7)
        overall_sat = satisfaction.get('overall_satisfaction', 4.0)
        recommend_likelihood = satisfaction.get('likelihood_to_recommend', 0.7)

        # Categorize NPS
        if nps_score >= 9:
            nps_category = 'promoter'
        elif nps_score >= 7:
            nps_category = 'passive'
        else:
            nps_category = 'detractor'

        # Identify satisfaction drivers
        drivers = []

        # Wait time driver
        avg_wait = journey_data.get('average_wait_time_minutes', 0)
        if avg_wait <= 5:
            drivers.append({
                'driver': 'Short wait times',
                'impact': 'positive',
                'importance': 0.25,
                'current_performance': 'excellent'
            })
        elif avg_wait > 10:
            drivers.append({
                'driver': 'Long wait times',
                'impact': 'negative',
                'importance': 0.25,
                'current_performance': 'poor'
            })

        # Rating driver
        avg_rating = journey_data.get('average_ride_rating', 0)
        if avg_rating >= 4.7:
            drivers.append({
                'driver': 'High-quality drivers',
                'impact': 'positive',
                'importance': 0.30,
                'current_performance': 'excellent'
            })
        elif avg_rating < 4.3:
            drivers.append({
                'driver': 'Driver quality concerns',
                'impact': 'negative',
                'importance': 0.30,
                'current_performance': 'poor'
            })

        # Reliability driver
        cancellations = journey_data.get('cancellations_last_30_days', 0)
        if cancellations > 3:
            drivers.append({
                'driver': 'High cancellation rate',
                'impact': 'negative',
                'importance': 0.20,
                'current_performance': 'poor'
            })

        # Payment experience
        payment_failures = journey_data.get('payment_failures', 0)
        if payment_failures == 0:
            drivers.append({
                'driver': 'Smooth payment experience',
                'impact': 'positive',
                'importance': 0.15,
                'current_performance': 'excellent'
            })
        elif payment_failures > 0:
            drivers.append({
                'driver': 'Payment difficulties',
                'impact': 'negative',
                'importance': 0.15,
                'current_performance': 'poor'
            })

        # Support experience
        support_contacts = journey_data.get('support_contacts', 0)
        if support_contacts > 2:
            drivers.append({
                'driver': 'Frequent support needs',
                'impact': 'negative',
                'importance': 0.10,
                'current_performance': 'concerning'
            })

        return {
            'nps_score': nps_score,
            'nps_category': nps_category,
            'overall_satisfaction': overall_sat,
            'recommendation_likelihood': recommend_likelihood,
            'satisfaction_drivers': drivers,
            'primary_positive_driver': next((d for d in drivers if d['impact'] == 'positive'), None),
            'primary_negative_driver': next((d for d in drivers if d['impact'] == 'negative'), None),
            'satisfaction_trend': satisfaction.get('last_feedback_sentiment', 'neutral')
        }

    def _predict_churn_risk(
        self,
        journey_data: Dict[str, Any],
        satisfaction: Dict[str, Any],
        profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Predict customer churn risk using behavioral signals
        """
        churn_score = 0  # 0-100, higher = higher churn risk

        # Recent activity decline
        rides_last_30 = journey_data.get('completed_rides_last_30_days', 0)
        lifetime_rides = profile.get('lifetime_rides', 1)
        account_age_days = profile.get('account_age_days', 365)

        expected_rides_30_days = (lifetime_rides / account_age_days) * 30
        activity_ratio = rides_last_30 / expected_rides_30_days if expected_rides_30_days > 0 else 1

        if activity_ratio < 0.5:
            churn_score += 30  # Significant decline
        elif activity_ratio < 0.7:
            churn_score += 15  # Moderate decline

        # Days since last ride
        days_since_last_ride = profile.get('last_ride_days_ago', 0)
        if days_since_last_ride > 30:
            churn_score += 25
        elif days_since_last_ride > 14:
            churn_score += 10

        # Satisfaction indicators
        nps_score = satisfaction.get('nps_score', 7)
        if nps_score < 7:
            churn_score += 20  # Detractor
        elif nps_score < 9:
            churn_score += 5  # Passive

        # Negative experiences
        cancellations = journey_data.get('cancellations_last_30_days', 0)
        if cancellations > 3:
            churn_score += 15

        payment_failures = journey_data.get('payment_failures', 0)
        if payment_failures > 1:
            churn_score += 10

        support_contacts = journey_data.get('support_contacts', 0)
        if support_contacts > 2:
            churn_score += 10

        # Determine risk level
        if churn_score >= 60:
            risk_level = 'high'
        elif churn_score >= 40:
            risk_level = 'medium'
        elif churn_score >= 20:
            risk_level = 'low'
        else:
            risk_level = 'very_low'

        # Calculate churn probability
        churn_probability = min(0.9, churn_score / 100)

        # Days to potential churn
        if risk_level == 'high':
            days_to_churn = 14
        elif risk_level == 'medium':
            days_to_churn = 30
        else:
            days_to_churn = None

        return {
            'churn_risk_score': round(churn_score, 1),
            'churn_probability': round(churn_probability, 3),
            'risk_level': risk_level,
            'days_to_potential_churn': days_to_churn,
            'primary_churn_indicators': self._identify_churn_indicators(
                activity_ratio, days_since_last_ride, nps_score, cancellations
            ),
            'intervention_urgency': 'immediate' if risk_level == 'high' else 'monitor'
        }

    def _identify_churn_indicators(
        self,
        activity_ratio: float,
        days_since_last: int,
        nps: int,
        cancellations: int
    ) -> List[str]:
        """Identify specific churn indicators"""
        indicators = []

        if activity_ratio < 0.5:
            indicators.append('Significant usage decline')
        if days_since_last > 14:
            indicators.append(f'Inactive for {days_since_last} days')
        if nps < 7:
            indicators.append('Low satisfaction (detractor)')
        if cancellations > 2:
            indicators.append('High cancellation rate')

        return indicators

    def _identify_friction_points(
        self,
        journey_map: Dict[str, Any],
        touchpoint_perf: Dict[str, Any],
        journey_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Identify specific friction points in the customer journey
        """
        friction_points = []

        # Analyze each stage for friction
        for stage in journey_map['stages']:
            stage_frictions = stage.get('friction_indicators', {})

            for friction_type, has_friction in stage_frictions.items():
                if has_friction:
                    # Calculate impact
                    impact_score = self._calculate_friction_impact(
                        stage['stage_name'],
                        friction_type,
                        stage['performance_metrics']
                    )

                    friction_points.append({
                        'stage': stage['stage_name'],
                        'friction_type': friction_type,
                        'impact_score': impact_score,
                        'severity': 'high' if impact_score > 70 else 'medium' if impact_score > 40 else 'low',
                        'affected_metric': self._get_affected_metric(friction_type),
                        'current_performance': stage['performance_metrics']
                    })

        # Sort by impact score
        friction_points.sort(key=lambda x: x['impact_score'], reverse=True)

        return friction_points

    def _calculate_friction_impact(
        self,
        stage_name: str,
        friction_type: str,
        metrics: Dict
    ) -> float:
        """Calculate impact score for a friction point"""
        # Impact varies by stage and type
        base_impacts = {
            'slow_app_load': 40,
            'long_matching_time': 60,
            'high_wait_time': 70,
            'low_match_rate': 80,
            'poor_arrival_accuracy': 50,
            'low_ratings': 65,
            'payment_issues': 55
        }

        return base_impacts.get(friction_type, 30)

    def _get_affected_metric(self, friction_type: str) -> str:
        """Map friction type to affected metric"""
        metric_map = {
            'slow_app_load': 'app_load_time',
            'long_matching_time': 'match_duration',
            'high_wait_time': 'wait_time',
            'low_match_rate': 'match_success_rate',
            'poor_arrival_accuracy': 'arrival_accuracy',
            'low_ratings': 'customer_rating',
            'payment_issues': 'payment_success_rate'
        }
        return metric_map.get(friction_type, 'unknown')

    def _generate_journey_recommendations(
        self,
        friction_points: List[Dict],
        churn_prediction: Dict,
        journey_map: Dict
    ) -> List[Dict[str, Any]]:
        """
        Generate recommendations to improve customer journey
        """
        recommendations = []

        # Address top friction points
        for friction in friction_points[:3]:  # Top 3 friction points
            recommendation = {
                'category': 'friction_reduction',
                'priority': 'high' if friction['severity'] == 'high' else 'medium',
                'issue': f"{friction['friction_type']} in {friction['stage']}",
                'recommendation': self._get_friction_recommendation(friction['friction_type']),
                'expected_impact': f"Improve {friction['affected_metric']} by 15-25%"
            }
            recommendations.append(recommendation)

        # Churn prevention if needed
        if churn_prediction['risk_level'] in ['high', 'medium']:
            recommendations.append({
                'category': 'churn_prevention',
                'priority': 'urgent' if churn_prediction['risk_level'] == 'high' else 'high',
                'issue': f"High churn risk: {', '.join(churn_prediction['primary_churn_indicators'])}",
                'recommendation': 'Send personalized re-engagement offer and survey',
                'expected_impact': 'Reduce churn probability by 30-40%'
            })

        # Journey optimization
        if journey_map['overall_completion_rate'] < 0.8:
            recommendations.append({
                'category': 'journey_optimization',
                'priority': 'medium',
                'issue': f"Low overall journey completion rate: {journey_map['overall_completion_rate']:.0%}",
                'recommendation': 'Optimize conversion funnel at low-performing stages',
                'expected_impact': 'Increase completion rate to 85%+'
            })

        return recommendations

    def _get_friction_recommendation(self, friction_type: str) -> str:
        """Get specific recommendation for friction type"""
        recommendations = {
            'slow_app_load': 'Optimize app performance and implement lazy loading',
            'long_matching_time': 'Improve matching algorithm and driver availability',
            'high_wait_time': 'Increase driver supply in high-demand areas',
            'low_match_rate': 'Expand driver network and adjust pricing',
            'poor_arrival_accuracy': 'Improve GPS tracking and driver navigation',
            'low_ratings': 'Implement driver quality improvement program',
            'payment_issues': 'Simplify payment flow and add alternative payment methods'
        }
        return recommendations.get(friction_type, 'Investigate and resolve issue')

    def _calculate_customer_health(
        self,
        journey_data: Dict,
        satisfaction: Dict,
        profile: Dict,
        churn_pred: Dict
    ) -> Dict[str, Any]:
        """
        Calculate overall customer health score
        """
        # Component scores
        activity_score = min(100, (journey_data.get('completed_rides_last_30_days', 0) / 20) * 100)
        satisfaction_score = (satisfaction.get('overall_satisfaction', 0) / 5) * 100
        engagement_score = min(100, (journey_data.get('app_opens_last_30_days', 0) / 30) * 100)
        retention_score = 100 - churn_pred['churn_risk_score']

        # Weighted health score
        health_score = (
            activity_score * 0.30 +
            satisfaction_score * 0.30 +
            engagement_score * 0.20 +
            retention_score * 0.20
        )

        # Determine status
        if health_score >= 80:
            status = 'excellent'
        elif health_score >= 60:
            status = 'good'
        elif health_score >= 40:
            status = 'at_risk'
        else:
            status = 'critical'

        return {
            'overall_health_score': round(health_score, 1),
            'status': status,
            'component_scores': {
                'activity': round(activity_score, 1),
                'satisfaction': round(satisfaction_score, 1),
                'engagement': round(engagement_score, 1),
                'retention': round(retention_score, 1)
            },
            'requires_intervention': status in ['at_risk', 'critical']
        }

    def get_input_schema(self) -> Dict[str, Any]:
        """Return input schema"""
        return {
            "type": "object",
            "required": ["customer_id", "journey_data"],
            "properties": {
                "customer_id": {"type": "string"},
                "journey_data": {"type": "object"},
                "touchpoint_performance": {"type": "object"},
                "satisfaction_metrics": {"type": "object"},
                "customer_profile": {"type": "object"}
            }
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """Return output schema"""
        return {
            "type": "object",
            "properties": {
                "journey_map": {"type": "object"},
                "satisfaction_analysis": {"type": "object"},
                "churn_prediction": {"type": "object"},
                "friction_points": {"type": "array"},
                "recommendations": {"type": "array"},
                "customer_health_score": {"type": "object"}
            }
        }


def create_analyze_customer_journey_customer_experience_agent() -> AnalyzeCustomerJourneyCustomerExperienceAgent:
    """Factory function to create AnalyzeCustomerJourneyCustomerExperienceAgent"""
    config = AnalyzeCustomerJourneyCustomerExperienceAgentConfig()
    return AnalyzeCustomerJourneyCustomerExperienceAgent(config)
