"""
🧠 Agent Semantic Protocol (ASP) v1.0 - PRODUCTION IMPLEMENTATION
==================================================================

Complete implementation of ASP for semantic interoperability between agents.

Features:
- Semantic capability declaration and discovery
- Ontology-based semantic matching
- Schema alignment and mapping
- Domain knowledge representation
- Semantic similarity scoring
- Concept resolution and mapping

Author: SuperStandard Team
License: MIT
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
import json
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class OntologyReference:
    """Reference to an ontology that an agent understands."""

    ontology_id: str
    namespace: str
    version: Optional[str] = None
    coverage: List[str] = field(default_factory=list)
    extensions: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def __repr__(self) -> str:
        return f"OntologyReference(ontology_id='{self.ontology_id}', namespace='{self.namespace}')"


@dataclass
class SemanticParameter:
    """Semantic description of a parameter."""

    name: str
    semantic_type: str
    schema_ref: Optional[str] = None
    unit: Optional[str] = None
    constraints: Dict[str, Any] = field(default_factory=dict)
    optional: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def __repr__(self) -> str:
        return f"SemanticParameter(name='{self.name}', type='{self.semantic_type}')"


@dataclass
class QualityOfService:
    """Quality of service characteristics."""

    accuracy: Optional[float] = None
    latency_ms: Optional[int] = None
    throughput: Optional[float] = None
    reliability: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class SemanticCapability:
    """Semantic description of an agent capability."""

    capability_id: str
    semantic_type: str
    capability_name: Optional[str] = None
    inputs: List[SemanticParameter] = field(default_factory=list)
    outputs: List[SemanticParameter] = field(default_factory=list)
    preconditions: List[str] = field(default_factory=list)
    postconditions: List[str] = field(default_factory=list)
    quality_of_service: Optional[QualityOfService] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        if self.quality_of_service:
            result['quality_of_service'] = self.quality_of_service.to_dict()
        return result

    def __repr__(self) -> str:
        return f"SemanticCapability(id='{self.capability_id}', type='{self.semantic_type}')"


@dataclass
class SchemaReference:
    """Reference to a data schema."""

    schema_id: str
    schema_uri: str
    schema_type: str = "json-schema"
    semantic_mapping: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def __repr__(self) -> str:
        return f"SchemaReference(id='{self.schema_id}', uri='{self.schema_uri}')"


class Proficiency(Enum):
    """Domain knowledge proficiency levels."""

    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


@dataclass
class DomainKnowledge:
    """Domain-specific knowledge declaration."""

    domain: str
    proficiency: str
    subdomain: Optional[str] = None
    standards: List[str] = field(default_factory=list)
    regulations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def __repr__(self) -> str:
        return f"DomainKnowledge(domain='{self.domain}', proficiency='{self.proficiency}')"


@dataclass
class SemanticDeclaration:
    """Complete semantic declaration for an agent."""

    agent_id: str
    ontologies: List[OntologyReference]
    capabilities: List[SemanticCapability]
    schemas: List[SchemaReference] = field(default_factory=list)
    domain_knowledge: List[DomainKnowledge] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'agent_id': self.agent_id,
            'ontologies': [o.to_dict() for o in self.ontologies],
            'capabilities': [c.to_dict() for c in self.capabilities],
            'schemas': [s.to_dict() for s in self.schemas],
            'domain_knowledge': [d.to_dict() for d in self.domain_knowledge]
        }


class MatchType(Enum):
    """Types of semantic matches."""

    EXACT = "exact"
    SUBSUMPTION = "subsumption"
    PARTIAL = "partial"
    ANALOGOUS = "analogous"


@dataclass
class SemanticMatch:
    """Result of semantic matching."""

    agent_id: str
    capability_id: str
    match_score: float
    match_type: str
    confidence: float
    explanation: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def __repr__(self) -> str:
        return f"SemanticMatch(agent='{self.agent_id}', score={self.match_score:.2f}, type='{self.match_type}')"


class AlignmentType(Enum):
    """Types of semantic alignment."""

    EQUIVALENCE = "equivalence"
    SUBSUMPTION = "subsumption"
    OVERLAP = "overlap"
    DISJOINT = "disjoint"


class TransformationType(Enum):
    """Types of data transformation."""

    IDENTITY = "identity"
    UNIT_CONVERSION = "unit_conversion"
    SCHEMA_MAPPING = "schema_mapping"
    CUSTOM = "custom"


@dataclass
class Transformation:
    """Data transformation specification."""

    transformation_type: str
    transformation_spec: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class SemanticAlignment:
    """Alignment between semantic representations."""

    source_concept: str
    target_concept: str
    alignment_type: str
    confidence: float
    transformation: Optional[Transformation] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        if self.transformation:
            result['transformation'] = self.transformation.to_dict()
        return result

    def __repr__(self) -> str:
        return f"SemanticAlignment('{self.source_concept}' -> '{self.target_concept}', type='{self.alignment_type}')"


class QueryType(Enum):
    """Types of semantic queries."""

    CAPABILITY_MATCH = "capability_match"
    SCHEMA_ALIGNMENT = "schema_alignment"
    ONTOLOGY_MAPPING = "ontology_mapping"
    CONCEPT_RESOLUTION = "concept_resolution"


@dataclass
class SemanticQuery:
    """Query for semantic alignment or discovery."""

    query_type: str
    query: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class SemanticResponse:
    """Response to semantic query."""

    matches: List[SemanticMatch] = field(default_factory=list)
    alignments: List[SemanticAlignment] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'matches': [m.to_dict() for m in self.matches],
            'alignments': [a.to_dict() for a in self.alignments]
        }


@dataclass
class ASPMessage:
    """Agent Semantic Protocol message."""

    protocol: str = "ASP"
    version: str = "1.0.0"
    semantic_declaration: Optional[SemanticDeclaration] = None
    semantic_query: Optional[SemanticQuery] = None
    semantic_response: Optional[SemanticResponse] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            'protocol': self.protocol,
            'version': self.version
        }
        if self.semantic_declaration:
            result['semantic_declaration'] = self.semantic_declaration.to_dict()
        if self.semantic_query:
            result['semantic_query'] = self.semantic_query.to_dict()
        if self.semantic_response:
            result['semantic_response'] = self.semantic_response.to_dict()
        return result


# ============================================================================
# SEMANTIC MATCHER
# ============================================================================


class SemanticMatcher:
    """
    Semantic matching engine for discovering compatible agents.

    Handles:
    - Capability matching based on semantic types
    - Similarity scoring using ontology concepts
    - Match type classification
    """

    def __init__(self):
        """Initialize the semantic matcher."""
        self.agent_declarations: Dict[str, SemanticDeclaration] = {}
        self.ontology_cache: Dict[str, Set[str]] = {}

    def register_agent(self, declaration: SemanticDeclaration) -> None:
        """
        Register an agent's semantic declaration.

        Args:
            declaration: The agent's semantic declaration
        """
        self.agent_declarations[declaration.agent_id] = declaration
        logger.info(f"Registered agent {declaration.agent_id} with {len(declaration.capabilities)} capabilities")

    def find_capability_matches(
        self,
        required_capability: SemanticCapability,
        min_score: float = 0.5
    ) -> List[SemanticMatch]:
        """
        Find agents with matching capabilities.

        Args:
            required_capability: The capability to match
            min_score: Minimum match score (0-1)

        Returns:
            List of semantic matches sorted by score (descending)
        """
        matches = []

        for agent_id, declaration in self.agent_declarations.items():
            for capability in declaration.capabilities:
                score, match_type = self._compute_match_score(
                    required_capability,
                    capability
                )

                if score >= min_score:
                    matches.append(SemanticMatch(
                        agent_id=agent_id,
                        capability_id=capability.capability_id,
                        match_score=score,
                        match_type=match_type,
                        confidence=score,
                        explanation=f"Semantic type match: {capability.semantic_type}"
                    ))

        # Sort by score descending
        matches.sort(key=lambda m: m.match_score, reverse=True)
        return matches

    def _compute_match_score(
        self,
        required: SemanticCapability,
        candidate: SemanticCapability
    ) -> tuple[float, str]:
        """
        Compute match score between two capabilities.

        Args:
            required: Required capability
            candidate: Candidate capability

        Returns:
            Tuple of (score, match_type)
        """
        # Exact semantic type match
        if required.semantic_type == candidate.semantic_type:
            return (1.0, MatchType.EXACT.value)

        # Check for subsumption (one type contains the other)
        if self._is_subsumption(required.semantic_type, candidate.semantic_type):
            return (0.9, MatchType.SUBSUMPTION.value)

        # Check for overlap based on semantic similarity
        similarity = self._semantic_similarity(
            required.semantic_type,
            candidate.semantic_type
        )

        if similarity >= 0.7:
            return (similarity, MatchType.PARTIAL.value)
        elif similarity >= 0.5:
            return (similarity, MatchType.ANALOGOUS.value)
        else:
            return (similarity, MatchType.PARTIAL.value)

    def _is_subsumption(self, type1: str, type2: str) -> bool:
        """
        Check if one semantic type subsumes another.

        Args:
            type1: First semantic type
            type2: Second semantic type

        Returns:
            True if there's a subsumption relationship
        """
        # Extract namespace and concept
        parts1 = type1.split(':')
        parts2 = type2.split(':')

        if len(parts1) == 2 and len(parts2) == 2:
            namespace1, concept1 = parts1
            namespace2, concept2 = parts2

            # Same namespace
            if namespace1 == namespace2:
                # Check if one concept is contained in the other
                return concept1.lower() in concept2.lower() or concept2.lower() in concept1.lower()

        return False

    def _semantic_similarity(self, type1: str, type2: str) -> float:
        """
        Compute semantic similarity between two types.

        Uses simple heuristics for v1.0:
        - Namespace match: +0.3
        - Concept similarity: up to +0.7

        Args:
            type1: First semantic type
            type2: Second semantic type

        Returns:
            Similarity score (0-1)
        """
        score = 0.0

        # Parse types
        parts1 = type1.split(':')
        parts2 = type2.split(':')

        if len(parts1) == 2 and len(parts2) == 2:
            namespace1, concept1 = parts1
            namespace2, concept2 = parts2

            # Namespace match
            if namespace1 == namespace2:
                score += 0.3

            # Concept similarity (simple string matching)
            concept1_lower = concept1.lower()
            concept2_lower = concept2.lower()

            # Exact match
            if concept1_lower == concept2_lower:
                score += 0.7
            # Substring match
            elif concept1_lower in concept2_lower or concept2_lower in concept1_lower:
                score += 0.5
            # Word overlap
            else:
                words1 = set(re.findall(r'[A-Z][a-z]*', concept1))
                words2 = set(re.findall(r'[A-Z][a-z]*', concept2))

                if words1 and words2:
                    overlap = len(words1 & words2)
                    total = len(words1 | words2)
                    score += 0.7 * (overlap / total)

        return min(score, 1.0)


# ============================================================================
# SEMANTIC ALIGNER
# ============================================================================


class SemanticAligner:
    """
    Semantic alignment engine for mapping between ontologies and schemas.

    Handles:
    - Ontology concept mapping
    - Schema field alignment
    - Data transformation specification
    """

    def __init__(self):
        """Initialize the semantic aligner."""
        self.alignment_cache: Dict[tuple[str, str], SemanticAlignment] = {}

    def align_concepts(
        self,
        source_concept: str,
        target_concept: str,
        confidence_threshold: float = 0.7
    ) -> Optional[SemanticAlignment]:
        """
        Align two ontology concepts.

        Args:
            source_concept: Source concept URI
            target_concept: Target concept URI
            confidence_threshold: Minimum confidence for alignment

        Returns:
            SemanticAlignment if concepts can be aligned, None otherwise
        """
        # Check cache
        cache_key = (source_concept, target_concept)
        if cache_key in self.alignment_cache:
            return self.alignment_cache[cache_key]

        # Compute alignment
        alignment_type, confidence = self._compute_alignment_type(
            source_concept,
            target_concept
        )

        if confidence < confidence_threshold:
            return None

        # Determine transformation
        transformation = self._determine_transformation(
            source_concept,
            target_concept,
            alignment_type
        )

        alignment = SemanticAlignment(
            source_concept=source_concept,
            target_concept=target_concept,
            alignment_type=alignment_type,
            confidence=confidence,
            transformation=transformation
        )

        # Cache result
        self.alignment_cache[cache_key] = alignment

        return alignment

    def _compute_alignment_type(
        self,
        source: str,
        target: str
    ) -> tuple[str, float]:
        """
        Compute alignment type and confidence.

        Args:
            source: Source concept
            target: Target concept

        Returns:
            Tuple of (alignment_type, confidence)
        """
        # Exact match
        if source == target:
            return (AlignmentType.EQUIVALENCE.value, 1.0)

        # Parse concepts
        source_parts = source.split(':')
        target_parts = target.split(':')

        if len(source_parts) == 2 and len(target_parts) == 2:
            source_ns, source_concept = source_parts
            target_ns, target_concept = target_parts

            source_lower = source_concept.lower()
            target_lower = target_concept.lower()

            # Subsumption (one contains the other)
            if source_lower in target_lower:
                return (AlignmentType.SUBSUMPTION.value, 0.85)
            elif target_lower in source_lower:
                return (AlignmentType.SUBSUMPTION.value, 0.85)

            # Word overlap
            words_source = set(re.findall(r'[A-Z][a-z]*', source_concept))
            words_target = set(re.findall(r'[A-Z][a-z]*', target_concept))

            if words_source and words_target:
                overlap = len(words_source & words_target)
                total = len(words_source | words_target)
                overlap_ratio = overlap / total

                if overlap_ratio > 0.5:
                    return (AlignmentType.OVERLAP.value, 0.6 + overlap_ratio * 0.3)

        # No significant alignment
        return (AlignmentType.DISJOINT.value, 0.0)

    def _determine_transformation(
        self,
        source: str,
        target: str,
        alignment_type: str
    ) -> Optional[Transformation]:
        """
        Determine required data transformation.

        Args:
            source: Source concept
            target: Target concept
            alignment_type: Type of alignment

        Returns:
            Transformation specification or None
        """
        # Identity transformation for equivalence
        if alignment_type == AlignmentType.EQUIVALENCE.value:
            return Transformation(
                transformation_type=TransformationType.IDENTITY.value,
                transformation_spec={}
            )

        # Check for unit conversions
        if 'amount' in source.lower() or 'amount' in target.lower():
            return Transformation(
                transformation_type=TransformationType.UNIT_CONVERSION.value,
                transformation_spec={
                    'note': 'May require currency or unit conversion'
                }
            )

        # Schema mapping for subsumption/overlap
        if alignment_type in [AlignmentType.SUBSUMPTION.value, AlignmentType.OVERLAP.value]:
            return Transformation(
                transformation_type=TransformationType.SCHEMA_MAPPING.value,
                transformation_spec={
                    'source_field': source,
                    'target_field': target,
                    'mapping_type': 'direct'
                }
            )

        return None

    def align_schemas(
        self,
        source_schema: SchemaReference,
        target_schema: SchemaReference
    ) -> List[SemanticAlignment]:
        """
        Align two data schemas based on semantic mappings.

        Args:
            source_schema: Source schema
            target_schema: Target schema

        Returns:
            List of field alignments
        """
        alignments = []

        # Align based on semantic mappings
        for source_field, source_concept in source_schema.semantic_mapping.items():
            for target_field, target_concept in target_schema.semantic_mapping.items():
                alignment = self.align_concepts(source_concept, target_concept)

                if alignment and alignment.confidence >= 0.5:
                    # Add field information to transformation
                    if alignment.transformation:
                        alignment.transformation.transformation_spec.update({
                            'source_field': source_field,
                            'target_field': target_field
                        })

                    alignments.append(alignment)

        return alignments


# ============================================================================
# SEMANTIC REGISTRY
# ============================================================================


class SemanticRegistry:
    """
    Central registry for semantic declarations and discovery.

    Handles:
    - Agent registration
    - Capability discovery
    - Schema alignment
    - Concept resolution
    """

    def __init__(self):
        """Initialize the semantic registry."""
        self.matcher = SemanticMatcher()
        self.aligner = SemanticAligner()

    def register(self, declaration: SemanticDeclaration) -> None:
        """
        Register an agent's semantic declaration.

        Args:
            declaration: Agent's semantic declaration
        """
        self.matcher.register_agent(declaration)
        logger.info(f"Registered agent {declaration.agent_id} in semantic registry")

    def discover_capabilities(
        self,
        required_capability: SemanticCapability,
        min_score: float = 0.5
    ) -> SemanticResponse:
        """
        Discover agents with matching capabilities.

        Args:
            required_capability: Required capability
            min_score: Minimum match score

        Returns:
            SemanticResponse with matches
        """
        matches = self.matcher.find_capability_matches(required_capability, min_score)

        return SemanticResponse(matches=matches)

    def align_ontologies(
        self,
        source_concept: str,
        target_concept: str
    ) -> SemanticResponse:
        """
        Align two ontology concepts.

        Args:
            source_concept: Source concept URI
            target_concept: Target concept URI

        Returns:
            SemanticResponse with alignment
        """
        alignment = self.aligner.align_concepts(source_concept, target_concept)

        alignments = [alignment] if alignment else []
        return SemanticResponse(alignments=alignments)

    def query(self, query: SemanticQuery) -> SemanticResponse:
        """
        Execute a semantic query.

        Args:
            query: Semantic query

        Returns:
            SemanticResponse with results
        """
        if query.query_type == QueryType.CAPABILITY_MATCH.value:
            # Extract required capability from query
            capability_data = query.query.get('capability', {})
            required_capability = SemanticCapability(
                capability_id=capability_data.get('capability_id', 'query'),
                semantic_type=capability_data.get('semantic_type', ''),
                inputs=[],
                outputs=[]
            )
            min_score = query.query.get('min_score', 0.5)

            return self.discover_capabilities(required_capability, min_score)

        elif query.query_type == QueryType.ONTOLOGY_MAPPING.value:
            source = query.query.get('source_concept', '')
            target = query.query.get('target_concept', '')

            return self.align_ontologies(source, target)

        else:
            return SemanticResponse()


# ============================================================================
# VALIDATION
# ============================================================================


def validate_semantic_type(semantic_type: str) -> bool:
    """
    Validate a semantic type URI.

    Args:
        semantic_type: Semantic type to validate

    Returns:
        True if valid
    """
    # Should be in format namespace:concept
    pattern = r'^[a-zA-Z0-9._-]+:[a-zA-Z0-9._-]+$'
    return bool(re.match(pattern, semantic_type))


def validate_asp_message(message: ASPMessage) -> tuple[bool, Optional[str]]:
    """
    Validate an ASP message.

    Args:
        message: Message to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if message.protocol != "ASP":
        return (False, "Protocol must be 'ASP'")

    if not re.match(r'^\d+\.\d+\.\d+$', message.version):
        return (False, "Version must match pattern X.Y.Z")

    # Must have at least one of: declaration, query, or response
    if not any([message.semantic_declaration, message.semantic_query, message.semantic_response]):
        return (False, "Message must contain declaration, query, or response")

    return (True, None)


# ============================================================================
# EXPORTS
# ============================================================================


__all__ = [
    # Data models
    'OntologyReference',
    'SemanticParameter',
    'QualityOfService',
    'SemanticCapability',
    'SchemaReference',
    'DomainKnowledge',
    'SemanticDeclaration',
    'SemanticMatch',
    'SemanticAlignment',
    'SemanticQuery',
    'SemanticResponse',
    'ASPMessage',
    'Transformation',

    # Enums
    'Proficiency',
    'MatchType',
    'AlignmentType',
    'TransformationType',
    'QueryType',

    # Core classes
    'SemanticMatcher',
    'SemanticAligner',
    'SemanticRegistry',

    # Validation
    'validate_semantic_type',
    'validate_asp_message',
]
