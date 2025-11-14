"""
Parameter Extractor - Extract and Validate Parameters from Natural Language

Enhances parameter extraction with validation, normalization, and defaults.
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from .intent_parser import IntentType


@dataclass
class ParameterSchema:
    """Schema for a parameter."""

    name: str
    type: type
    required: bool = False
    default: Any = None
    choices: Optional[List[Any]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    description: str = ""


class ParameterExtractor:
    """
    Parameter Extractor and Validator.

    Takes raw parameters from intent parsing and validates/normalizes them
    according to agent requirements.
    """

    def __init__(self):
        """Initialize parameter extractor."""
        self.logger = logging.getLogger(__name__)

        # Define parameter schemas for each intent
        self.schemas = self._build_schemas()

    def _build_schemas(self) -> Dict[IntentType, List[ParameterSchema]]:
        """Build parameter schemas for each intent type."""
        return {
            IntentType.DISCOVER_OPPORTUNITIES: [
                ParameterSchema(
                    name="industry",
                    type=str,
                    required=True,
                    default="technology",
                    description="Target industry sector"
                ),
                ParameterSchema(
                    name="geography",
                    type=str,
                    required=True,
                    default="United States",
                    description="Geographic region"
                ),
                ParameterSchema(
                    name="min_confidence",
                    type=float,
                    required=False,
                    default=0.75,
                    min_value=0.0,
                    max_value=1.0,
                    description="Minimum confidence threshold"
                ),
                ParameterSchema(
                    name="category",
                    type=str,
                    required=False,
                    choices=["SaaS", "Product", "Service", "Platform"],
                    description="Opportunity category filter"
                ),
                ParameterSchema(
                    name="min_revenue",
                    type=int,
                    required=False,
                    min_value=0,
                    description="Minimum revenue threshold"
                )
            ],
            IntentType.ANALYZE_COMPETITORS: [
                ParameterSchema(
                    name="domain",
                    type=str,
                    required=True,
                    description="Target domain to analyze"
                ),
                ParameterSchema(
                    name="limit",
                    type=int,
                    required=False,
                    default=10,
                    min_value=1,
                    max_value=50,
                    description="Number of competitors to return"
                )
            ],
            IntentType.GET_ECONOMIC_TRENDS: [
                ParameterSchema(
                    name="geography",
                    type=str,
                    required=False,
                    default="United States",
                    description="Geographic region"
                ),
                ParameterSchema(
                    name="indicators",
                    type=list,
                    required=False,
                    default=["gdp", "unemployment", "inflation"],
                    description="Economic indicators to fetch"
                ),
                ParameterSchema(
                    name="years",
                    type=int,
                    required=False,
                    default=5,
                    min_value=1,
                    max_value=20,
                    description="Number of years of historical data"
                )
            ],
            IntentType.ANALYZE_DEMOGRAPHICS: [
                ParameterSchema(
                    name="geography",
                    type=str,
                    required=True,
                    default="United States",
                    description="Geographic region (state or county)"
                ),
                ParameterSchema(
                    name="year",
                    type=int,
                    required=False,
                    default=2020,
                    description="Census year"
                )
            ],
            IntentType.CONDUCT_RESEARCH: [
                ParameterSchema(
                    name="survey_id",
                    type=str,
                    required=True,
                    description="Qualtrics survey ID"
                ),
                ParameterSchema(
                    name="industry",
                    type=str,
                    required=False,
                    description="Industry context"
                )
            ]
        }

    def extract_and_validate(
        self,
        intent_type: IntentType,
        raw_parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract and validate parameters for given intent.

        Args:
            intent_type: Type of intent
            raw_parameters: Raw parameters from intent parsing

        Returns:
            Validated and normalized parameters

        Raises:
            ValueError: If required parameters are missing or invalid
        """
        schema = self.schemas.get(intent_type, [])
        if not schema:
            # No schema for this intent, return as-is
            return raw_parameters

        validated = {}
        errors = []

        for param_schema in schema:
            param_name = param_schema.name
            raw_value = raw_parameters.get(param_name)

            # Handle missing parameters
            if raw_value is None:
                if param_schema.required:
                    if param_schema.default is not None:
                        validated[param_name] = param_schema.default
                        self.logger.info(
                            f"Using default for {param_name}: {param_schema.default}"
                        )
                    else:
                        errors.append(f"Required parameter missing: {param_name}")
                        continue
                else:
                    if param_schema.default is not None:
                        validated[param_name] = param_schema.default
                    continue

            # Type validation and conversion
            try:
                validated_value = self._validate_and_convert(
                    raw_value,
                    param_schema
                )
                validated[param_name] = validated_value
            except ValueError as e:
                errors.append(f"Invalid {param_name}: {e}")

        if errors:
            raise ValueError(f"Parameter validation errors: {'; '.join(errors)}")

        return validated

    def _validate_and_convert(
        self,
        value: Any,
        schema: ParameterSchema
    ) -> Any:
        """Validate and convert a single parameter."""
        # Type conversion
        try:
            if schema.type == int:
                converted = int(value)
            elif schema.type == float:
                converted = float(value)
            elif schema.type == str:
                converted = str(value)
            elif schema.type == list:
                if isinstance(value, str):
                    converted = [v.strip() for v in value.split(',')]
                elif isinstance(value, list):
                    converted = value
                else:
                    converted = [value]
            else:
                converted = value
        except (ValueError, TypeError) as e:
            raise ValueError(f"Cannot convert to {schema.type.__name__}: {e}")

        # Choices validation
        if schema.choices is not None:
            if converted not in schema.choices:
                raise ValueError(
                    f"Must be one of {schema.choices}, got: {converted}"
                )

        # Range validation
        if schema.min_value is not None and converted < schema.min_value:
            raise ValueError(
                f"Must be >= {schema.min_value}, got: {converted}"
            )

        if schema.max_value is not None and converted > schema.max_value:
            raise ValueError(
                f"Must be <= {schema.max_value}, got: {converted}"
            )

        return converted

    def get_schema(self, intent_type: IntentType) -> List[ParameterSchema]:
        """Get parameter schema for an intent type."""
        return self.schemas.get(intent_type, [])

    def get_required_parameters(self, intent_type: IntentType) -> List[str]:
        """Get list of required parameter names for an intent."""
        schema = self.get_schema(intent_type)
        return [p.name for p in schema if p.required]

    def get_parameter_help(self, intent_type: IntentType) -> str:
        """Get human-readable help text for parameters."""
        schema = self.get_schema(intent_type)
        if not schema:
            return "No parameters required."

        lines = ["Parameters:"]
        for param in schema:
            required = " (required)" if param.required else " (optional)"
            default = f" [default: {param.default}]" if param.default is not None else ""
            choices = f" [choices: {', '.join(str(c) for c in param.choices)}]" if param.choices else ""
            range_info = ""
            if param.min_value is not None or param.max_value is not None:
                if param.min_value is not None and param.max_value is not None:
                    range_info = f" [range: {param.min_value}-{param.max_value}]"
                elif param.min_value is not None:
                    range_info = f" [min: {param.min_value}]"
                else:
                    range_info = f" [max: {param.max_value}]"

            lines.append(
                f"  - {param.name}{required}{default}{choices}{range_info}"
            )
            if param.description:
                lines.append(f"    {param.description}")

        return "\n".join(lines)
