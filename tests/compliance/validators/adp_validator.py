"""
Agent Discovery Protocol (ADP) v1.0 Validator
"""

from typing import Any, Dict, List
from ..framework import ProtocolValidator, get_schema_path


class ADPValidator(ProtocolValidator):
    """Validator for ADP v1.0 protocol messages"""

    VALID_DISCOVERY_TYPES = {
        "capability_search",
        "agent_lookup",
        "service_discovery",
        "network_topology"
    }

    VALID_AGENT_STATUS = {
        "online",
        "offline",
        "busy",
        "maintenance"
    }

    def __init__(self):
        super().__init__(get_schema_path("adp"))

    def get_protocol_name(self) -> str:
        return "ADP"

    def get_protocol_version(self) -> str:
        return "1.0.0"

    def validate_discovery_request(self, message: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate ADP discovery request

        Args:
            message: ADP message to validate

        Returns:
            Tuple of (is_valid, error_list)
        """
        errors = []

        if 'discovery_request' not in message:
            return True, []  # Request is optional if response is present

        request = message['discovery_request']

        # Check discovery_type
        discovery_type = request.get('discovery_type')
        if discovery_type and discovery_type not in self.VALID_DISCOVERY_TYPES:
            errors.append(f"Invalid discovery_type: {discovery_type}")

        return len(errors) == 0, errors

    def validate_discovery_response(self, message: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate ADP discovery response

        Args:
            message: ADP message to validate

        Returns:
            Tuple of (is_valid, error_list)
        """
        errors = []

        if 'discovery_response' not in message:
            return True, []  # Response is optional if request is present

        response = message['discovery_response']

        # Check agents array
        if 'agents' in response:
            if not isinstance(response['agents'], list):
                errors.append("'agents' must be an array")
            else:
                # Validate each agent entry
                for i, agent in enumerate(response['agents']):
                    if 'agent_id' not in agent:
                        errors.append(f"Agent {i} missing 'agent_id'")

                    status = agent.get('status')
                    if status and status not in self.VALID_AGENT_STATUS:
                        errors.append(f"Agent {i} has invalid status: {status}")

        return len(errors) == 0, errors

    def create_sample_message(self) -> Dict[str, Any]:
        """Create a valid sample ADP message for testing"""
        return {
            "protocol": "ADP",
            "version": "1.0.0",
            "discovery_request": {
                "discovery_type": "capability_search",
                "criteria": {
                    "capabilities": ["strategic_planning"]
                }
            }
        }
