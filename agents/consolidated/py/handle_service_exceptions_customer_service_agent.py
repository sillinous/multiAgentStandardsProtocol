"""
HandleServiceExceptionsCustomerServiceAgent - APQC 6.2.3
Handle Service Exceptions and Customer Complaints
APQC ID: apqc_6_2_h1s2e3x4

This agent automates handling of service exceptions including cancellations,
complaints, refunds, and escalations with sentiment analysis and resolution automation.
"""

import os
import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

from library.core.base_agent import BaseAgent
from library.core.protocols import ProtocolMixin


@dataclass
class HandleServiceExceptionsCustomerServiceAgentConfig:
    apqc_agent_id: str = "apqc_6_2_h1s2e3x4"
    apqc_process_id: str = "6.2.3"
    agent_name: str = "handle_service_exceptions_customer_service_agent"
    agent_type: str = "operational"
    version: str = "1.0.0"


class HandleServiceExceptionsCustomerServiceAgent(BaseAgent, ProtocolMixin):
    """
    APQC 6.2.3 - Handle Service Exceptions

    Skills:
    - exception_handling: 0.91 (automated exception processing)
    - resolution_automation: 0.88 (auto-resolution rules)
    - sentiment_analysis: 0.85 (complaint severity detection)
    - escalation_management: 0.83 (intelligent escalation)

    Use Cases:
    - Process ride cancellations
    - Handle customer complaints
    - Automate refund decisions
    - Manage escalations
    """

    VERSION = "1.0.0"
    APQC_PROCESS_ID = "6.2.3"

    def __init__(self, config: HandleServiceExceptionsCustomerServiceAgentConfig):
        super().__init__(agent_id=config.apqc_agent_id, agent_type=config.agent_type, version=config.version)
        self.config = config
        self.skills = {
            'exception_handling': 0.91,
            'resolution_automation': 0.88,
            'sentiment_analysis': 0.85,
            'escalation_management': 0.83
        }

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle service exceptions and customer issues

        Input:
        {
            "exception": {
                "exception_id": "EXC12345",
                "type": "cancellation",  # or "complaint", "refund_request", "service_issue"
                "ride_id": "RIDE67890",
                "customer_id": "CUST001",
                "driver_id": "DRV001",
                "created_at": "2025-10-18T14:30:00",
                "description": "Driver cancelled after 10 minutes of waiting",
                "customer_sentiment": "frustrated"
            },
            "ride_details": {
                "fare_amount": 35.50,
                "distance_km": 15.2,
                "wait_time_minutes": 10,
                "ride_status": "cancelled_by_driver"
            },
            "customer_history": {
                "total_rides": 145,
                "lifetime_value": 4250,
                "average_rating_given": 4.6,
                "previous_exceptions": 2,
                "account_age_days": 365
            },
            "driver_history": {
                "total_rides": 892,
                "cancellation_rate": 0.03,
                "average_rating": 4.7,
                "recent_exceptions": 1
            }
        }
        """
        exception = input_data.get('exception', {})
        ride_details = input_data.get('ride_details', {})
        customer_history = input_data.get('customer_history', {})
        driver_history = input_data.get('driver_history', {})

        # Analyze exception severity
        severity_analysis = self._analyze_severity(exception, customer_history, ride_details)

        # Determine resolution strategy
        resolution_strategy = self._determine_resolution(exception, severity_analysis, ride_details, customer_history)

        # Calculate compensation
        compensation = self._calculate_compensation(exception, ride_details, customer_history, severity_analysis)

        # Determine if escalation is needed
        escalation_decision = self._evaluate_escalation(exception, severity_analysis, resolution_strategy)

        # Generate customer communication
        communication = self._generate_communication(exception, resolution_strategy, compensation)

        # Generate follow-up actions
        follow_up_actions = self._generate_follow_up_actions(exception, driver_history, resolution_strategy)

        return {
            "status": "completed",
            "apqc_process_id": self.APQC_PROCESS_ID,
            "timestamp": datetime.now().isoformat(),
            "output": {
                "exception_id": exception.get('exception_id'),
                "severity_analysis": severity_analysis,
                "resolution_strategy": resolution_strategy,
                "compensation": compensation,
                "escalation_decision": escalation_decision,
                "customer_communication": communication,
                "follow_up_actions": follow_up_actions,
                "summary": {
                    "resolution_type": resolution_strategy['resolution_type'],
                    "auto_resolved": resolution_strategy['auto_resolvable'],
                    "compensation_amount": compensation.get('total_amount', 0),
                    "requires_escalation": escalation_decision['escalate']
                }
            }
        }

    def _analyze_severity(
        self,
        exception: Dict[str, Any],
        customer_history: Dict[str, Any],
        ride_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze the severity of the service exception
        """
        exception_type = exception.get('type')
        sentiment = exception.get('customer_sentiment', 'neutral')
        previous_exceptions = customer_history.get('previous_exceptions', 0)
        lifetime_value = customer_history.get('lifetime_value', 0)

        # Base severity score (0-100)
        severity_score = 30  # Base

        # Exception type impact
        type_severity = {
            'complaint': 40,
            'cancellation': 30,
            'refund_request': 35,
            'service_issue': 45,
            'safety_concern': 90,
            'payment_dispute': 50
        }
        severity_score += type_severity.get(exception_type, 30)

        # Sentiment impact
        sentiment_impact = {
            'very_frustrated': 20,
            'frustrated': 15,
            'disappointed': 10,
            'neutral': 0,
            'satisfied': -10
        }
        severity_score += sentiment_impact.get(sentiment, 0)

        # Customer history impact
        if previous_exceptions > 3:
            severity_score += 15  # Frequent issues
        elif previous_exceptions > 1:
            severity_score += 5

        # High-value customer adjustment
        if lifetime_value > 5000:
            severity_score += 10
        elif lifetime_value > 2000:
            severity_score += 5

        # Ride details impact
        fare = ride_details.get('fare_amount', 0)
        if fare > 50:
            severity_score += 5

        wait_time = ride_details.get('wait_time_minutes', 0)
        if wait_time > 15:
            severity_score += 10
        elif wait_time > 10:
            severity_score += 5

        severity_score = min(100, max(0, severity_score))

        # Determine severity level
        if severity_score >= 80:
            severity_level = 'critical'
        elif severity_score >= 60:
            severity_level = 'high'
        elif severity_score >= 40:
            severity_level = 'medium'
        else:
            severity_level = 'low'

        return {
            'severity_score': round(severity_score, 1),
            'severity_level': severity_level,
            'exception_type': exception_type,
            'customer_sentiment': sentiment,
            'high_value_customer': lifetime_value > 2000,
            'repeat_issue': previous_exceptions > 1,
            'urgent': severity_score >= 70
        }

    def _determine_resolution(
        self,
        exception: Dict[str, Any],
        severity: Dict[str, Any],
        ride_details: Dict[str, Any],
        customer_history: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Determine the appropriate resolution strategy
        """
        exception_type = exception.get('type')
        severity_level = severity['severity_level']

        # Resolution rules based on exception type and severity
        if exception_type == 'cancellation':
            if ride_details.get('ride_status') == 'cancelled_by_driver':
                resolution_type = 'full_refund_credit'
                auto_resolvable = True
                reason = 'Driver cancellation - automatic full credit'
            elif ride_details.get('wait_time_minutes', 0) > 10:
                resolution_type = 'partial_credit'
                auto_resolvable = True
                reason = 'Extended wait time - partial credit'
            else:
                resolution_type = 'no_compensation'
                auto_resolvable = True
                reason = 'Customer cancellation within normal parameters'

        elif exception_type == 'complaint':
            if severity_level in ['critical', 'high']:
                resolution_type = 'credit_and_investigation'
                auto_resolvable = False
                reason = 'Serious complaint requiring investigation'
            else:
                resolution_type = 'apology_credit'
                auto_resolvable = True
                reason = 'Standard complaint - goodwill credit'

        elif exception_type == 'refund_request':
            if severity_level in ['critical', 'high']:
                resolution_type = 'full_refund'
                auto_resolvable = severity_level != 'critical'
                reason = 'High severity - full refund warranted'
            else:
                resolution_type = 'partial_refund'
                auto_resolvable = True
                reason = 'Partial refund for minor issue'

        elif exception_type == 'service_issue':
            resolution_type = 'credit_and_apology'
            auto_resolvable = severity_level in ['low', 'medium']
            reason = 'Service quality issue - credit offered'

        elif exception_type == 'safety_concern':
            resolution_type = 'full_refund_and_investigation'
            auto_resolvable = False
            reason = 'Safety concern requires immediate escalation'

        else:
            resolution_type = 'manual_review'
            auto_resolvable = False
            reason = 'Unknown exception type - manual review required'

        # Adjust based on customer value
        if customer_history.get('lifetime_value', 0) > 5000 and resolution_type in ['no_compensation', 'partial_credit']:
            resolution_type = 'credit_and_apology'
            reason += ' (upgraded for VIP customer)'

        return {
            'resolution_type': resolution_type,
            'auto_resolvable': auto_resolvable,
            'reason': reason,
            'requires_manager_approval': severity_level == 'critical' or not auto_resolvable,
            'estimated_resolution_time_hours': 0.5 if auto_resolvable else 4
        }

    def _calculate_compensation(
        self,
        exception: Dict[str, Any],
        ride_details: Dict[str, Any],
        customer_history: Dict[str, Any],
        severity: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate appropriate compensation amount
        """
        fare_amount = ride_details.get('fare_amount', 0)
        exception_type = exception.get('type')
        severity_level = severity['severity_level']

        compensation_amount = 0
        compensation_type = 'none'
        compensation_items = []

        # Base compensation rules
        if exception_type == 'cancellation' and ride_details.get('ride_status') == 'cancelled_by_driver':
            # Full fare as credit
            compensation_amount = fare_amount
            compensation_type = 'account_credit'
            compensation_items.append({
                'item': 'Full ride credit',
                'amount': fare_amount,
                'reason': 'Driver cancellation'
            })

        elif exception_type in ['complaint', 'service_issue']:
            # Goodwill credit based on severity
            if severity_level == 'critical':
                compensation_amount = max(fare_amount * 1.5, 50)
                compensation_type = 'account_credit'
            elif severity_level == 'high':
                compensation_amount = max(fare_amount, 25)
                compensation_type = 'account_credit'
            elif severity_level == 'medium':
                compensation_amount = max(fare_amount * 0.5, 10)
                compensation_type = 'account_credit'
            else:
                compensation_amount = 5
                compensation_type = 'account_credit'

            compensation_items.append({
                'item': 'Goodwill credit',
                'amount': compensation_amount,
                'reason': f'{severity_level} severity {exception_type}'
            })

        elif exception_type == 'refund_request':
            if severity_level in ['critical', 'high']:
                compensation_amount = fare_amount
                compensation_type = 'refund'
            else:
                compensation_amount = fare_amount * 0.5
                compensation_type = 'partial_refund'

            compensation_items.append({
                'item': 'Refund' if compensation_type == 'refund' else 'Partial refund',
                'amount': compensation_amount,
                'reason': 'Refund request approved'
            })

        # Add bonus for high-value customers
        if customer_history.get('lifetime_value', 0) > 5000 and compensation_amount > 0:
            bonus = 10
            compensation_amount += bonus
            compensation_items.append({
                'item': 'VIP customer bonus',
                'amount': bonus,
                'reason': 'Valued customer appreciation'
            })

        # Add promo code for future rides
        promo_code = None
        if severity_level in ['high', 'critical'] or customer_history.get('previous_exceptions', 0) > 2:
            promo_code = {
                'code': f"SORRY{exception.get('exception_id', '12345')[-5:]}",
                'discount_percentage': 20 if severity_level == 'critical' else 15,
                'max_discount_amount': 15 if severity_level == 'critical' else 10,
                'expires_days': 30
            }
            compensation_items.append({
                'item': 'Future ride discount',
                'amount': promo_code['max_discount_amount'],
                'reason': 'Apology discount for next ride'
            })

        return {
            'total_amount': round(compensation_amount, 2),
            'compensation_type': compensation_type,
            'compensation_items': compensation_items,
            'promo_code': promo_code,
            'requires_approval': compensation_amount > 100,
            'approved': compensation_amount <= 100
        }

    def _evaluate_escalation(
        self,
        exception: Dict[str, Any],
        severity: Dict[str, Any],
        resolution: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Determine if the exception requires escalation
        """
        escalate = False
        escalation_level = 'none'
        escalation_reasons = []

        # Critical severity always escalates
        if severity['severity_level'] == 'critical':
            escalate = True
            escalation_level = 'manager'
            escalation_reasons.append('Critical severity level')

        # Safety concerns always escalate
        if exception.get('type') == 'safety_concern':
            escalate = True
            escalation_level = 'safety_team'
            escalation_reasons.append('Safety concern reported')

        # Cannot auto-resolve
        if not resolution['auto_resolvable']:
            escalate = True
            escalation_level = 'support_supervisor'
            escalation_reasons.append('Manual review required')

        # High-value customer with repeat issues
        if severity.get('high_value_customer') and severity.get('repeat_issue'):
            escalate = True
            escalation_level = 'customer_success_manager'
            escalation_reasons.append('VIP customer with repeat issues')

        # Compensation requires approval
        if resolution.get('requires_manager_approval'):
            escalate = True
            escalation_level = 'manager'
            escalation_reasons.append('High-value compensation requires approval')

        return {
            'escalate': escalate,
            'escalation_level': escalation_level,
            'escalation_reasons': escalation_reasons,
            'priority': 'urgent' if severity['severity_level'] == 'critical' else 'normal',
            'sla_hours': 1 if severity['severity_level'] == 'critical' else 4
        }

    def _generate_communication(
        self,
        exception: Dict[str, Any],
        resolution: Dict[str, Any],
        compensation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate customer communication templates
        """
        exception_type = exception.get('type')
        resolution_type = resolution['resolution_type']

        # Subject line
        subjects = {
            'cancellation': 'Regarding Your Recent Ride Cancellation',
            'complaint': 'We\'re Sorry About Your Recent Experience',
            'refund_request': 'Your Refund Request',
            'service_issue': 'Apology for Service Issue',
            'safety_concern': 'URGENT: Safety Concern Follow-up'
        }
        subject = subjects.get(exception_type, 'Regarding Your Recent Ride')

        # Message body
        message_parts = []

        # Greeting
        message_parts.append("Dear Valued Customer,")
        message_parts.append("")

        # Acknowledgment
        if exception_type == 'cancellation':
            message_parts.append("We sincerely apologize for the cancellation of your recent ride.")
        elif exception_type in ['complaint', 'service_issue']:
            message_parts.append("Thank you for bringing this matter to our attention. We sincerely apologize for the inconvenience you experienced.")
        elif exception_type == 'safety_concern':
            message_parts.append("We take safety concerns very seriously and apologize for any distress this incident may have caused.")

        message_parts.append("")

        # Resolution
        if 'refund' in resolution_type:
            if resolution_type == 'full_refund':
                message_parts.append(f"We have issued a full refund of ${compensation['total_amount']:.2f} to your original payment method.")
            else:
                message_parts.append(f"We have issued a partial refund of ${compensation['total_amount']:.2f} to your original payment method.")
        elif 'credit' in resolution_type:
            message_parts.append(f"We have added ${compensation['total_amount']:.2f} in credit to your account for future rides.")

        # Promo code
        if compensation.get('promo_code'):
            promo = compensation['promo_code']
            message_parts.append("")
            message_parts.append(f"Additionally, please use promo code {promo['code']} for {promo['discount_percentage']}% off your next ride (up to ${promo['max_discount_amount']}).")

        message_parts.append("")
        message_parts.append("We value your business and appreciate your patience and understanding.")
        message_parts.append("")
        message_parts.append("Best regards,")
        message_parts.append("Customer Support Team")

        return {
            'channel': 'email',
            'subject': subject,
            'message_body': "\n".join(message_parts),
            'send_immediately': resolution['auto_resolvable'],
            'requires_review': not resolution['auto_resolvable'],
            'follow_up_in_days': 3 if exception_type in ['complaint', 'safety_concern'] else None
        }

    def _generate_follow_up_actions(
        self,
        exception: Dict[str, Any],
        driver_history: Dict[str, Any],
        resolution: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate follow-up actions for the exception
        """
        actions = []

        exception_type = exception.get('type')

        # Driver-related actions
        if exception.get('driver_id'):
            driver_cancellation_rate = driver_history.get('cancellation_rate', 0)

            if exception_type == 'cancellation' and driver_cancellation_rate > 0.05:
                actions.append({
                    'action': 'Review driver cancellation pattern',
                    'assignee': 'driver_quality_team',
                    'priority': 'high',
                    'due_hours': 24,
                    'details': f"Driver has {driver_cancellation_rate:.1%} cancellation rate"
                })

            if exception_type in ['complaint', 'service_issue']:
                actions.append({
                    'action': 'Send coaching notification to driver',
                    'assignee': 'driver_operations',
                    'priority': 'medium',
                    'due_hours': 12,
                    'details': 'Customer complaint - coaching required'
                })

            if exception_type == 'safety_concern':
                actions.append({
                    'action': 'Suspend driver pending investigation',
                    'assignee': 'safety_team',
                    'priority': 'urgent',
                    'due_hours': 1,
                    'details': 'Safety concern reported - immediate action required'
                })

        # Customer follow-up
        if exception.get('customer_sentiment') in ['very_frustrated', 'frustrated']:
            actions.append({
                'action': 'Proactive customer follow-up call',
                'assignee': 'customer_success',
                'priority': 'medium',
                'due_hours': 48,
                'details': 'Check customer satisfaction after resolution'
            })

        # Quality improvement
        if exception_type == 'service_issue':
            actions.append({
                'action': 'Log service quality issue for analysis',
                'assignee': 'quality_team',
                'priority': 'low',
                'due_hours': 168,
                'details': 'Trend analysis for continuous improvement'
            })

        return actions

    def get_input_schema(self) -> Dict[str, Any]:
        """Return input schema for exception handling"""
        return {
            "type": "object",
            "required": ["exception", "ride_details"],
            "properties": {
                "exception": {"type": "object"},
                "ride_details": {"type": "object"},
                "customer_history": {"type": "object"},
                "driver_history": {"type": "object"}
            }
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """Return output schema"""
        return {
            "type": "object",
            "properties": {
                "severity_analysis": {"type": "object"},
                "resolution_strategy": {"type": "object"},
                "compensation": {"type": "object"},
                "escalation_decision": {"type": "object"},
                "customer_communication": {"type": "object"},
                "follow_up_actions": {"type": "array"}
            }
        }


def create_handle_service_exceptions_customer_service_agent() -> HandleServiceExceptionsCustomerServiceAgent:
    """Factory function to create HandleServiceExceptionsCustomerServiceAgent"""
    config = HandleServiceExceptionsCustomerServiceAgentConfig()
    return HandleServiceExceptionsCustomerServiceAgent(config)
