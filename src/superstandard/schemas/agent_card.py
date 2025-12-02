"""
Agent Card Schema Definition
============================

Defines the structure for APQC Agent Cards - executable specifications
that make BPMN tasks implementable with real integrations.

Based on:
- Google A2A Protocol Agent Card specification
- APQC Process Classification Framework
- BPMN 2.0 Service Task extensions

Version: 1.0.0
Date: 2025-11-25
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import json


class IntegrationType(Enum):
    """Types of integrations an agent can use"""
    REST_API = "rest_api"
    GRAPHQL = "graphql"
    DATABASE = "database"
    FILE_SYSTEM = "file_system"
    MESSAGE_QUEUE = "message_queue"
    WEBHOOK = "webhook"
    AI_MODEL = "ai_model"
    OCR = "ocr"
    EMAIL = "email"
    HUMAN_IN_LOOP = "human_in_loop"


class DataType(Enum):
    """Standard data types for input/output schemas"""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"
    DATE = "date"
    DATETIME = "datetime"
    CURRENCY = "currency"
    FILE = "file"
    BINARY = "binary"


@dataclass
class SchemaField:
    """Defines a field in input/output schema"""
    name: str
    data_type: DataType
    description: str
    required: bool = True
    default: Any = None
    validation: Optional[Dict[str, Any]] = None  # e.g., {"min": 0, "max": 100}
    example: Any = None


@dataclass
class Integration:
    """Defines an external integration"""
    id: str
    name: str
    type: IntegrationType
    description: str
    endpoint_template: Optional[str] = None  # e.g., "https://api.quickbooks.com/v3/company/{company_id}/invoice"
    auth_type: str = "oauth2"  # oauth2, api_key, basic, none
    required_credentials: List[str] = field(default_factory=list)  # e.g., ["client_id", "client_secret", "refresh_token"]
    rate_limit: Optional[Dict[str, int]] = None  # e.g., {"requests_per_minute": 100}
    documentation_url: Optional[str] = None
    category: str = "general"  # finance, hr, crm, documents, communication, etc.


@dataclass
class DecisionRule:
    """Defines a business rule for decision making"""
    id: str
    name: str
    description: str
    condition: str  # Expression like "variance_percent > 5"
    action_if_true: str
    action_if_false: str
    configurable: bool = True  # Can user modify this rule?
    default_threshold: Optional[Any] = None


@dataclass
class ErrorHandler:
    """Defines error handling behavior"""
    error_type: str  # e.g., "validation_error", "integration_timeout", "auth_failure"
    description: str
    action: str  # "retry", "escalate", "manual_review", "skip", "abort"
    max_retries: int = 3
    retry_delay_seconds: int = 60
    escalation_target: Optional[str] = None  # e.g., "supervisor_queue", "ap_manager"
    notification_channels: List[str] = field(default_factory=list)  # ["email", "slack"]


@dataclass
class AgentCard:
    """
    Complete Agent Card specification for an APQC task

    This is the executable specification that makes a BPMN task
    actually implementable with real integrations.
    """
    # Identity
    id: str  # e.g., "agent_9_2_1_1_step1"
    apqc_id: str  # e.g., "9.2.1.1"
    apqc_name: str  # e.g., "Process invoices and track accounts payable"
    step_number: int
    step_name: str  # e.g., "Invoice Receipt and Validation"

    # Description
    description: str
    purpose: str  # Why this step exists in the process
    business_value: str  # What value it provides

    # Capabilities
    capabilities: List[str]  # What this agent can do

    # Input/Output Schemas
    input_schema: List[SchemaField]
    output_schema: List[SchemaField]

    # Integrations
    required_integrations: List[str]  # Integration IDs
    optional_integrations: List[str] = field(default_factory=list)

    # Decision Logic
    decision_rules: List[DecisionRule] = field(default_factory=list)

    # AI/LLM Configuration (if applicable)
    ai_config: Optional[Dict[str, Any]] = None  # model, prompt_template, tools, etc.

    # Error Handling
    error_handlers: List[ErrorHandler] = field(default_factory=list)

    # Handoff Configuration
    next_step_on_success: Optional[str] = None  # Next agent ID
    next_step_on_failure: Optional[str] = None  # Fallback agent ID
    parallel_steps: List[str] = field(default_factory=list)  # Steps that can run in parallel

    # SLA and Performance
    expected_duration_seconds: int = 60
    timeout_seconds: int = 300
    sla_target_seconds: Optional[int] = None

    # Audit and Compliance
    requires_audit_log: bool = True
    compliance_frameworks: List[str] = field(default_factory=list)  # ["SOX", "GDPR", "HIPAA"]
    data_retention_days: int = 2555  # 7 years for financial

    # User Configuration
    user_configurable_fields: List[str] = field(default_factory=list)  # Fields users can modify

    # Metadata
    version: str = "1.0.0"
    status: str = "draft"  # draft, active, deprecated
    created_date: str = ""
    last_modified: str = ""

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "apqc_id": self.apqc_id,
            "apqc_name": self.apqc_name,
            "step_number": self.step_number,
            "step_name": self.step_name,
            "description": self.description,
            "purpose": self.purpose,
            "business_value": self.business_value,
            "capabilities": self.capabilities,
            "input_schema": [
                {
                    "name": f.name,
                    "type": f.data_type.value,
                    "description": f.description,
                    "required": f.required,
                    "default": f.default,
                    "validation": f.validation,
                    "example": f.example
                }
                for f in self.input_schema
            ],
            "output_schema": [
                {
                    "name": f.name,
                    "type": f.data_type.value,
                    "description": f.description,
                    "required": f.required,
                    "example": f.example
                }
                for f in self.output_schema
            ],
            "required_integrations": self.required_integrations,
            "optional_integrations": self.optional_integrations,
            "decision_rules": [
                {
                    "id": r.id,
                    "name": r.name,
                    "description": r.description,
                    "condition": r.condition,
                    "action_if_true": r.action_if_true,
                    "action_if_false": r.action_if_false,
                    "configurable": r.configurable,
                    "default_threshold": r.default_threshold
                }
                for r in self.decision_rules
            ],
            "ai_config": self.ai_config,
            "error_handlers": [
                {
                    "error_type": h.error_type,
                    "description": h.description,
                    "action": h.action,
                    "max_retries": h.max_retries,
                    "escalation_target": h.escalation_target
                }
                for h in self.error_handlers
            ],
            "next_step_on_success": self.next_step_on_success,
            "next_step_on_failure": self.next_step_on_failure,
            "parallel_steps": self.parallel_steps,
            "expected_duration_seconds": self.expected_duration_seconds,
            "timeout_seconds": self.timeout_seconds,
            "sla_target_seconds": self.sla_target_seconds,
            "requires_audit_log": self.requires_audit_log,
            "compliance_frameworks": self.compliance_frameworks,
            "data_retention_days": self.data_retention_days,
            "user_configurable_fields": self.user_configurable_fields,
            "version": self.version,
            "status": self.status
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=indent)


@dataclass
class ProcessAgentCards:
    """Collection of Agent Cards for a complete APQC process"""
    apqc_id: str
    apqc_name: str
    category: str
    description: str
    agent_cards: List[AgentCard]

    # Process-level configuration
    orchestration_pattern: str = "sequential"  # sequential, parallel, conditional
    total_steps: int = 0
    estimated_duration_seconds: int = 0

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "apqc_id": self.apqc_id,
            "apqc_name": self.apqc_name,
            "category": self.category,
            "description": self.description,
            "orchestration_pattern": self.orchestration_pattern,
            "total_steps": len(self.agent_cards),
            "estimated_duration_seconds": sum(a.expected_duration_seconds for a in self.agent_cards),
            "agent_cards": [a.to_dict() for a in self.agent_cards]
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=indent)
