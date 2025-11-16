"""
Temporal Agent Protocol (TAP) v1.0 Validator
"""

from typing import Any, Dict, List
import re
from ..framework import ProtocolValidator, get_schema_path


class TAPValidator(ProtocolValidator):
    """Validator for TAP v1.0 protocol messages"""

    VALID_QUERY_TYPES = {
        "point_in_time",
        "time_range",
        "event_sequence",
        "temporal_pattern",
        "what_if_scenario"
    }

    def __init__(self):
        super().__init__(get_schema_path("tap"))

    def get_protocol_name(self) -> str:
        return "TAP"

    def get_protocol_version(self) -> str:
        return "1.0.0"

    def validate_temporal_query(self, message: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate TAP temporal query

        Args:
            message: TAP message to validate

        Returns:
            Tuple of (is_valid, error_list)
        """
        errors = []

        if 'temporal_query' not in message:
            return False, ["Missing 'temporal_query' field"]

        query = message['temporal_query']

        # Check query_type
        query_type = query.get('query_type')
        if not query_type:
            errors.append("temporal_query missing 'query_type'")
        elif query_type not in self.VALID_QUERY_TYPES:
            errors.append(f"Invalid query_type: {query_type}")

        # Check temporal_scope
        if 'temporal_scope' not in query:
            errors.append("temporal_query missing 'temporal_scope'")

        return len(errors) == 0, errors

    def validate_temporal_scope(self, temporal_scope: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate temporal scope structure

        Args:
            temporal_scope: Temporal scope object

        Returns:
            Tuple of (is_valid, error_list)
        """
        errors = []

        # Check for at least one temporal constraint
        has_constraint = any(k in temporal_scope for k in ['point_in_time', 'start_time', 'end_time', 'time_range'])

        if not has_constraint:
            errors.append("temporal_scope must specify at least one temporal constraint")

        return len(errors) == 0, errors

    def create_sample_message(self) -> Dict[str, Any]:
        """Create a valid sample TAP message for testing"""
        return {
            "protocol": "TAP",
            "version": "1.0.0",
            "temporal_query": {
                "query_type": "point_in_time",
                "temporal_scope": {
                    "point_in_time": "2025-01-01T00:00:00Z"
                },
                "query": {
                    "entity": "company_revenue",
                    "attributes": ["total_revenue", "profit_margin"]
                }
            }
        }
