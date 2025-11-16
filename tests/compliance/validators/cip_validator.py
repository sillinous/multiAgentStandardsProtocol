"""
Cognitive Interoperability Protocol (CIP) v1.0 Validator
"""

from typing import Any, Dict, List
from ..framework import ProtocolValidator, get_schema_path


class CIPValidator(ProtocolValidator):
    """Validator for CIP v1.0 protocol messages"""

    VALID_REASONING_TYPES = {
        "deductive",
        "inductive",
        "abductive",
        "analogical",
        "causal"
    }

    VALID_CONFIDENCE_LEVELS = {
        "very_low",
        "low",
        "medium",
        "high",
        "very_high"
    }

    def __init__(self):
        super().__init__(get_schema_path("cip"))

    def get_protocol_name(self) -> str:
        return "CIP"

    def get_protocol_version(self) -> str:
        return "1.0.0"

    def validate_reasoning_request(self, message: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate CIP reasoning request

        Args:
            message: CIP message to validate

        Returns:
            Tuple of (is_valid, error_list)
        """
        errors = []

        if 'reasoning_request' not in message:
            return True, []  # Request is optional if response is present

        request = message['reasoning_request']

        # Check reasoning_type
        reasoning_type = request.get('reasoning_type')
        if reasoning_type and reasoning_type not in self.VALID_REASONING_TYPES:
            errors.append(f"Invalid reasoning_type: {reasoning_type}")

        # Check for premises or context
        if 'premises' not in request and 'context' not in request:
            errors.append("reasoning_request must have either 'premises' or 'context'")

        return len(errors) == 0, errors

    def validate_reasoning_response(self, message: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate CIP reasoning response

        Args:
            message: CIP message to validate

        Returns:
            Tuple of (is_valid, error_list)
        """
        errors = []

        if 'reasoning_response' not in message:
            return True, []  # Response is optional if request is present

        response = message['reasoning_response']

        # Check confidence if present
        confidence = response.get('confidence')
        if confidence:
            if isinstance(confidence, dict):
                level = confidence.get('level')
                if level and level not in self.VALID_CONFIDENCE_LEVELS:
                    errors.append(f"Invalid confidence level: {level}")

                score = confidence.get('score')
                if score is not None and (score < 0 or score > 1):
                    errors.append(f"Confidence score must be between 0 and 1, got: {score}")

        return len(errors) == 0, errors

    def create_sample_message(self) -> Dict[str, Any]:
        """Create a valid sample CIP message for testing"""
        return {
            "protocol": "CIP",
            "version": "1.0.0",
            "reasoning_request": {
                "reasoning_type": "deductive",
                "premises": [
                    "All strategic plans require market analysis",
                    "We are creating a strategic plan"
                ],
                "goal": "Determine if market analysis is required"
            }
        }
