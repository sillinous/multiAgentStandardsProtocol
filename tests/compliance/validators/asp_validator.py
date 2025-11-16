"""
Agent Semantic Protocol (ASP) v1.0 Validator
"""

from typing import Any, Dict, List
from ..framework import ProtocolValidator, get_schema_path


class ASPValidator(ProtocolValidator):
    """Validator for ASP v1.0 protocol messages"""

    VALID_QUERY_TYPES = {
        "capability_match",
        "schema_alignment",
        "ontology_mapping",
        "concept_resolution"
    }

    def __init__(self):
        super().__init__(get_schema_path("asp"))

    def get_protocol_name(self) -> str:
        return "ASP"

    def get_protocol_version(self) -> str:
        return "1.0.0"

    def validate_semantic_declaration(self, message: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate ASP semantic declaration

        Args:
            message: ASP message to validate

        Returns:
            Tuple of (is_valid, error_list)
        """
        errors = []

        if 'semantic_declaration' not in message:
            # Semantic declaration is required
            return False, ["Missing 'semantic_declaration' field"]

        declaration = message['semantic_declaration']

        # Check required fields
        if 'agent_id' not in declaration:
            errors.append("semantic_declaration missing 'agent_id'")

        if 'ontologies' not in declaration:
            errors.append("semantic_declaration missing 'ontologies'")
        elif not isinstance(declaration['ontologies'], list):
            errors.append("'ontologies' must be an array")

        if 'capabilities' not in declaration:
            errors.append("semantic_declaration missing 'capabilities'")
        elif not isinstance(declaration['capabilities'], list):
            errors.append("'capabilities' must be an array")

        return len(errors) == 0, errors

    def validate_semantic_query(self, message: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate ASP semantic query

        Args:
            message: ASP message to validate

        Returns:
            Tuple of (is_valid, error_list)
        """
        errors = []

        if 'semantic_query' not in message:
            return True, []  # Query is optional

        query = message['semantic_query']

        # Validate query_type if present
        query_type = query.get('query_type')
        if query_type and query_type not in self.VALID_QUERY_TYPES:
            errors.append(f"Invalid query_type: {query_type}")

        return len(errors) == 0, errors

    def create_sample_message(self) -> Dict[str, Any]:
        """Create a valid sample ASP message for testing"""
        return {
            "protocol": "ASP",
            "version": "1.0.0",
            "semantic_declaration": {
                "agent_id": "test_agent_1",
                "ontologies": [
                    {
                        "ontology_id": "apqc:7.0.1",
                        "namespace": "http://apqc.org/ontology/7.0.1"
                    }
                ],
                "capabilities": [
                    {
                        "capability_id": "strategic_planning",
                        "name": "Strategic Planning",
                        "description": "Develop business strategies"
                    }
                ]
            }
        }
