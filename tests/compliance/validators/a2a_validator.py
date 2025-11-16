"""
Agent-to-Agent Protocol (A2A) v2.0 Validator
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import re
from datetime import datetime

from ..framework import ProtocolValidator, get_schema_path


class A2AValidator(ProtocolValidator):
    """Validator for A2A v2.0 protocol messages"""

    # Valid message types from A2A spec
    VALID_MESSAGE_TYPES = {
        "task_assignment",
        "task_completed",
        "status_update",
        "request",
        "response",
        "error",
        "negotiation",
        "acknowledgment",
        "event",
        "notification",
        "heartbeat",
        "discovery"
    }

    VALID_PRIORITIES = {"low", "normal", "high", "critical"}

    def __init__(self):
        super().__init__(get_schema_path("a2a"))

    def get_protocol_name(self) -> str:
        return "A2A"

    def get_protocol_version(self) -> str:
        return "2.0.0"

    def validate_envelope(self, message: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate A2A message envelope

        Args:
            message: A2A message to validate

        Returns:
            Tuple of (is_valid, error_list)
        """
        errors = []

        if 'envelope' not in message:
            return False, ["Missing 'envelope' field"]

        envelope = message['envelope']

        # Check protocol identifier
        if envelope.get('protocol') != 'A2A':
            errors.append("Protocol must be 'A2A'")

        # Check version format (semantic versioning)
        version = envelope.get('version', '')
        if not re.match(r'^\d+\.\d+\.\d+$', version):
            errors.append(f"Invalid version format: {version}")

        # Check message_id is UUID format
        message_id = envelope.get('message_id', '')
        if not self._is_valid_uuid(message_id):
            errors.append(f"Invalid message_id UUID: {message_id}")

        # Check timestamp is ISO 8601 format
        timestamp = envelope.get('timestamp', '')
        if not self._is_valid_iso8601(timestamp):
            errors.append(f"Invalid timestamp format: {timestamp}")

        # Check message_type is valid
        message_type = envelope.get('message_type', '')
        if message_type not in self.VALID_MESSAGE_TYPES:
            errors.append(f"Invalid message_type: {message_type}")

        # Check priority if present
        priority = envelope.get('priority')
        if priority and priority not in self.VALID_PRIORITIES:
            errors.append(f"Invalid priority: {priority}")

        # Validate agent info
        agent_errors = self._validate_agent_info(envelope.get('from_agent'), 'from_agent')
        errors.extend(agent_errors)

        agent_errors = self._validate_agent_info(envelope.get('to_agent'), 'to_agent')
        errors.extend(agent_errors)

        return len(errors) == 0, errors

    def validate_payload(self, message: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate A2A message payload

        Args:
            message: A2A message to validate

        Returns:
            Tuple of (is_valid, error_list)
        """
        errors = []

        if 'payload' not in message:
            return False, ["Missing 'payload' field"]

        payload = message['payload']

        # Check required 'content' field
        if 'content' not in payload:
            errors.append("Payload missing required 'content' field")

        return len(errors) == 0, errors

    def validate_security(self, message: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate security metadata if present

        Args:
            message: A2A message to validate

        Returns:
            Tuple of (is_valid, error_list)
        """
        errors = []

        if 'envelope' not in message:
            return True, []  # Already validated elsewhere

        security = message['envelope'].get('security')
        if not security:
            return True, []  # Security is optional

        # Validate authentication if present
        auth = security.get('authentication')
        if auth:
            method = auth.get('method')
            valid_methods = {'bearer', 'jwt', 'mtls', 'did', 'none'}
            if method and method not in valid_methods:
                errors.append(f"Invalid authentication method: {method}")

            # If DID method, validate DID format
            if method == 'did' and auth.get('did'):
                if not auth['did'].startswith('did:'):
                    errors.append(f"Invalid DID format: {auth['did']}")

        return len(errors) == 0, errors

    def _validate_agent_info(self, agent_info: Optional[Dict], field_name: str) -> List[str]:
        """Validate agent information structure"""
        errors = []

        if not agent_info:
            errors.append(f"Missing {field_name}")
            return errors

        if 'agent_id' not in agent_info:
            errors.append(f"{field_name} missing 'agent_id'")

        if 'agent_name' not in agent_info:
            errors.append(f"{field_name} missing 'agent_name'")

        # Validate version format if present
        version = agent_info.get('version')
        if version and not re.match(r'^\d+\.\d+\.\d+$', version):
            errors.append(f"{field_name} has invalid version format: {version}")

        return errors

    @staticmethod
    def _is_valid_uuid(uuid_str: str) -> bool:
        """Check if string is valid UUID format"""
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        return bool(re.match(uuid_pattern, uuid_str, re.IGNORECASE))

    @staticmethod
    def _is_valid_iso8601(timestamp: str) -> bool:
        """Check if string is valid ISO 8601 timestamp"""
        try:
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return True
        except (ValueError, AttributeError):
            return False

    def create_sample_message(self) -> Dict[str, Any]:
        """Create a valid sample A2A message for testing"""
        return {
            "envelope": {
                "protocol": "A2A",
                "version": "2.0.0",
                "message_id": "550e8400-e29b-41d4-a716-446655440000",
                "from_agent": {
                    "agent_id": "test_agent_1",
                    "agent_name": "Test Agent 1"
                },
                "to_agent": {
                    "agent_id": "test_agent_2",
                    "agent_name": "Test Agent 2"
                },
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "message_type": "request"
            },
            "payload": {
                "content": {
                    "test": "data"
                }
            }
        }
