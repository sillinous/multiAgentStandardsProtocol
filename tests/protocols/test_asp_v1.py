"""
Unit Tests for Agent Semantic Protocol (ASP) v1.0

Comprehensive tests ensuring:
- Data model creation and validation
- Semantic matching functionality
- Ontology alignment
- Schema mapping
- Query operations
"""

import pytest
from superstandard.protocols.asp_v1 import (
    # Data models
    OntologyReference,
    SemanticParameter,
    QualityOfService,
    SemanticCapability,
    SchemaReference,
    DomainKnowledge,
    SemanticDeclaration,
    SemanticMatch,
    SemanticAlignment,
    SemanticQuery,
    SemanticResponse,
    ASPMessage,
    Transformation,

    # Enums
    Proficiency,
    MatchType,
    AlignmentType,
    TransformationType,
    QueryType,

    # Core classes
    SemanticMatcher,
    SemanticAligner,
    SemanticRegistry,

    # Validation
    validate_semantic_type,
    validate_asp_message,
)


@pytest.mark.unit
class TestDataModels:
    """Test ASP data models."""

    def test_ontology_reference_creation(self):
        """Test creating an ontology reference."""
        ontology = OntologyReference(
            ontology_id="apqc:7.0.1",
            namespace="https://apqc.org/ontology/7.0.1",
            version="7.0.1",
            coverage=["FinancialAnalysis", "BudgetPlanning"]
        )

        assert ontology.ontology_id == "apqc:7.0.1"
        assert ontology.namespace == "https://apqc.org/ontology/7.0.1"
        assert len(ontology.coverage) == 2
        assert "FinancialAnalysis" in ontology.coverage

    def test_ontology_reference_to_dict(self):
        """Test ontology reference serialization."""
        ontology = OntologyReference(
            ontology_id="schema.org:latest",
            namespace="https://schema.org/"
        )

        data = ontology.to_dict()
        assert data['ontology_id'] == "schema.org:latest"
        assert data['namespace'] == "https://schema.org/"

    def test_semantic_parameter_creation(self):
        """Test creating a semantic parameter."""
        param = SemanticParameter(
            name="total_budget",
            semantic_type="schema.org:MonetaryAmount",
            unit="USD",
            constraints={"range": {"min": 0}}
        )

        assert param.name == "total_budget"
        assert param.semantic_type == "schema.org:MonetaryAmount"
        assert param.unit == "USD"
        assert not param.optional

    def test_quality_of_service(self):
        """Test QoS model."""
        qos = QualityOfService(
            accuracy=0.95,
            latency_ms=5000,
            reliability=0.99
        )

        assert qos.accuracy == 0.95
        assert qos.latency_ms == 5000
        assert qos.reliability == 0.99

    def test_semantic_capability_creation(self):
        """Test creating a semantic capability."""
        capability = SemanticCapability(
            capability_id="perform_budgeting",
            semantic_type="apqc:BudgetPlanning",
            capability_name="Perform Budget Planning",
            inputs=[
                SemanticParameter(
                    name="timeframe",
                    semantic_type="schema.org:DateTime"
                )
            ],
            outputs=[
                SemanticParameter(
                    name="budget_allocation",
                    semantic_type="fibo:BudgetAllocation"
                )
            ]
        )

        assert capability.capability_id == "perform_budgeting"
        assert capability.semantic_type == "apqc:BudgetPlanning"
        assert len(capability.inputs) == 1
        assert len(capability.outputs) == 1

    def test_schema_reference_creation(self):
        """Test creating a schema reference."""
        schema = SchemaReference(
            schema_id="budget_allocation_v1",
            schema_uri="https://schemas.superstandard.org/budget_allocation/v1.json",
            schema_type="json-schema",
            semantic_mapping={
                "total_amount": "schema.org:totalPrice",
                "currency": "schema.org:priceCurrency"
            }
        )

        assert schema.schema_id == "budget_allocation_v1"
        assert len(schema.semantic_mapping) == 2

    def test_domain_knowledge_creation(self):
        """Test creating domain knowledge."""
        domain = DomainKnowledge(
            domain="finance",
            subdomain="budgeting",
            proficiency=Proficiency.EXPERT.value,
            standards=["GAAP", "IFRS"],
            regulations=["SOX"]
        )

        assert domain.domain == "finance"
        assert domain.proficiency == "expert"
        assert len(domain.standards) == 2

    def test_semantic_declaration_creation(self):
        """Test creating a complete semantic declaration."""
        declaration = SemanticDeclaration(
            agent_id="apqc_9_2_xyz123",
            ontologies=[
                OntologyReference(
                    ontology_id="apqc:7.0.1",
                    namespace="https://apqc.org/ontology/7.0.1"
                )
            ],
            capabilities=[
                SemanticCapability(
                    capability_id="perform_budgeting",
                    semantic_type="apqc:BudgetPlanning"
                )
            ],
            domain_knowledge=[
                DomainKnowledge(
                    domain="finance",
                    proficiency="expert"
                )
            ]
        )

        assert declaration.agent_id == "apqc_9_2_xyz123"
        assert len(declaration.ontologies) == 1
        assert len(declaration.capabilities) == 1
        assert len(declaration.domain_knowledge) == 1


@pytest.mark.unit
class TestSemanticMatcher:
    """Test semantic matching functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.matcher = SemanticMatcher()

    def test_matcher_initialization(self):
        """Test matcher initialization."""
        assert self.matcher is not None
        assert len(self.matcher.agent_declarations) == 0

    def test_register_agent(self):
        """Test registering an agent."""
        declaration = SemanticDeclaration(
            agent_id="test_agent_1",
            ontologies=[],
            capabilities=[
                SemanticCapability(
                    capability_id="analyze_data",
                    semantic_type="apqc:FinancialAnalysis"
                )
            ]
        )

        self.matcher.register_agent(declaration)

        assert "test_agent_1" in self.matcher.agent_declarations
        assert len(self.matcher.agent_declarations["test_agent_1"].capabilities) == 1

    def test_exact_capability_match(self):
        """Test exact semantic type matching."""
        # Register an agent
        declaration = SemanticDeclaration(
            agent_id="financial_agent",
            ontologies=[],
            capabilities=[
                SemanticCapability(
                    capability_id="budget_planning",
                    semantic_type="apqc:BudgetPlanning"
                )
            ]
        )
        self.matcher.register_agent(declaration)

        # Search for exact match
        required = SemanticCapability(
            capability_id="need_budgeting",
            semantic_type="apqc:BudgetPlanning"
        )

        matches = self.matcher.find_capability_matches(required, min_score=0.5)

        assert len(matches) == 1
        assert matches[0].agent_id == "financial_agent"
        assert matches[0].match_score == 1.0
        assert matches[0].match_type == MatchType.EXACT.value

    def test_partial_capability_match(self):
        """Test partial semantic matching."""
        # Register agents with similar but not exact capabilities
        declaration1 = SemanticDeclaration(
            agent_id="agent_1",
            ontologies=[],
            capabilities=[
                SemanticCapability(
                    capability_id="cap_1",
                    semantic_type="apqc:FinancialAnalysis"
                )
            ]
        )
        declaration2 = SemanticDeclaration(
            agent_id="agent_2",
            ontologies=[],
            capabilities=[
                SemanticCapability(
                    capability_id="cap_2",
                    semantic_type="apqc:FinancialPlanning"
                )
            ]
        )

        self.matcher.register_agent(declaration1)
        self.matcher.register_agent(declaration2)

        # Search for Financial*
        required = SemanticCapability(
            capability_id="need_financial",
            semantic_type="apqc:Financial"
        )

        matches = self.matcher.find_capability_matches(required, min_score=0.3)

        # Both should match with subsumption
        assert len(matches) >= 1

    def test_no_match_below_threshold(self):
        """Test that low-scoring matches are filtered out."""
        declaration = SemanticDeclaration(
            agent_id="marketing_agent",
            ontologies=[],
            capabilities=[
                SemanticCapability(
                    capability_id="marketing",
                    semantic_type="apqc:Marketing"
                )
            ]
        )
        self.matcher.register_agent(declaration)

        # Search for completely different capability
        required = SemanticCapability(
            capability_id="need_finance",
            semantic_type="apqc:Finance"
        )

        matches = self.matcher.find_capability_matches(required, min_score=0.8)

        # Should not match
        assert len(matches) == 0

    def test_semantic_similarity_same_namespace(self):
        """Test semantic similarity calculation."""
        score = self.matcher._semantic_similarity(
            "apqc:BudgetPlanning",
            "apqc:BudgetAnalysis"
        )

        # Same namespace + similar concept = high score
        assert score > 0.5

    def test_semantic_similarity_different_namespace(self):
        """Test semantic similarity with different namespaces."""
        score = self.matcher._semantic_similarity(
            "apqc:BudgetPlanning",
            "schema.org:BudgetPlanning"
        )

        # Different namespace but same concept = moderate score
        assert score > 0.5


@pytest.mark.unit
class TestSemanticAligner:
    """Test semantic alignment functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.aligner = SemanticAligner()

    def test_aligner_initialization(self):
        """Test aligner initialization."""
        assert self.aligner is not None

    def test_exact_concept_alignment(self):
        """Test exact concept matching."""
        alignment = self.aligner.align_concepts(
            "schema.org:MonetaryAmount",
            "schema.org:MonetaryAmount",
            confidence_threshold=0.7
        )

        assert alignment is not None
        assert alignment.alignment_type == AlignmentType.EQUIVALENCE.value
        assert alignment.confidence == 1.0
        assert alignment.transformation is not None
        assert alignment.transformation.transformation_type == TransformationType.IDENTITY.value

    def test_subsumption_alignment(self):
        """Test subsumption relationship."""
        alignment = self.aligner.align_concepts(
            "apqc:Financial",
            "apqc:FinancialAnalysis",
            confidence_threshold=0.7
        )

        assert alignment is not None
        assert alignment.alignment_type == AlignmentType.SUBSUMPTION.value
        assert alignment.confidence >= 0.7

    def test_no_alignment_below_threshold(self):
        """Test that weak alignments are rejected."""
        alignment = self.aligner.align_concepts(
            "apqc:Marketing",
            "schema.org:Finance",
            confidence_threshold=0.9
        )

        # Should not align
        assert alignment is None

    def test_schema_alignment(self):
        """Test aligning two schemas."""
        schema1 = SchemaReference(
            schema_id="schema_1",
            schema_uri="https://example.com/schema1",
            semantic_mapping={
                "revenue": "schema.org:totalRevenue",
                "expenses": "schema.org:operatingExpense"
            }
        )

        schema2 = SchemaReference(
            schema_id="schema_2",
            schema_uri="https://example.com/schema2",
            semantic_mapping={
                "total_revenue": "schema.org:totalRevenue",
                "costs": "schema.org:operatingExpense"
            }
        )

        alignments = self.aligner.align_schemas(schema1, schema2)

        # Should find alignments for matching fields
        assert len(alignments) >= 1


@pytest.mark.unit
class TestSemanticRegistry:
    """Test semantic registry."""

    def setup_method(self):
        """Set up test fixtures."""
        self.registry = SemanticRegistry()

    def test_registry_initialization(self):
        """Test registry initialization."""
        assert self.registry is not None
        assert self.registry.matcher is not None
        assert self.registry.aligner is not None

    def test_register_and_discover(self):
        """Test full registration and discovery flow."""
        # Register agents
        declaration1 = SemanticDeclaration(
            agent_id="budget_agent",
            ontologies=[],
            capabilities=[
                SemanticCapability(
                    capability_id="budget_planning",
                    semantic_type="apqc:BudgetPlanning"
                )
            ]
        )

        declaration2 = SemanticDeclaration(
            agent_id="finance_agent",
            ontologies=[],
            capabilities=[
                SemanticCapability(
                    capability_id="financial_analysis",
                    semantic_type="apqc:FinancialAnalysis"
                )
            ]
        )

        self.registry.register(declaration1)
        self.registry.register(declaration2)

        # Discover budget planning capability
        required = SemanticCapability(
            capability_id="need_budget",
            semantic_type="apqc:BudgetPlanning"
        )

        response = self.registry.discover_capabilities(required, min_score=0.5)

        assert len(response.matches) >= 1
        assert any(m.agent_id == "budget_agent" for m in response.matches)

    def test_capability_match_query(self):
        """Test capability match query."""
        # Register agent
        declaration = SemanticDeclaration(
            agent_id="test_agent",
            ontologies=[],
            capabilities=[
                SemanticCapability(
                    capability_id="test_cap",
                    semantic_type="apqc:Testing"
                )
            ]
        )
        self.registry.register(declaration)

        # Query
        query = SemanticQuery(
            query_type=QueryType.CAPABILITY_MATCH.value,
            query={
                'capability': {
                    'capability_id': 'need_test',
                    'semantic_type': 'apqc:Testing'
                },
                'min_score': 0.5
            }
        )

        response = self.registry.query(query)

        assert len(response.matches) >= 1

    def test_ontology_mapping_query(self):
        """Test ontology mapping query."""
        query = SemanticQuery(
            query_type=QueryType.ONTOLOGY_MAPPING.value,
            query={
                'source_concept': 'schema.org:MonetaryAmount',
                'target_concept': 'schema.org:MonetaryAmount'
            }
        )

        response = self.registry.query(query)

        assert len(response.alignments) >= 1
        assert response.alignments[0].alignment_type == AlignmentType.EQUIVALENCE.value


@pytest.mark.unit
class TestValidation:
    """Test validation functions."""

    def test_validate_semantic_type_valid(self):
        """Test validating valid semantic types."""
        assert validate_semantic_type("apqc:BudgetPlanning")
        assert validate_semantic_type("schema.org:MonetaryAmount")
        assert validate_semantic_type("fibo:FinancialStatement")

    def test_validate_semantic_type_invalid(self):
        """Test rejecting invalid semantic types."""
        assert not validate_semantic_type("invalid")
        assert not validate_semantic_type("no-colon")
        assert not validate_semantic_type(":missing-namespace")
        assert not validate_semantic_type("missing-concept:")

    def test_validate_asp_message_valid(self):
        """Test validating valid ASP messages."""
        message = ASPMessage(
            protocol="ASP",
            version="1.0.0",
            semantic_declaration=SemanticDeclaration(
                agent_id="test",
                ontologies=[],
                capabilities=[]
            )
        )

        is_valid, error = validate_asp_message(message)

        assert is_valid
        assert error is None

    def test_validate_asp_message_invalid_protocol(self):
        """Test rejecting invalid protocol."""
        message = ASPMessage(
            protocol="WRONG",
            version="1.0.0"
        )

        is_valid, error = validate_asp_message(message)

        assert not is_valid
        assert "Protocol" in error

    def test_validate_asp_message_invalid_version(self):
        """Test rejecting invalid version."""
        message = ASPMessage(
            protocol="ASP",
            version="1.0"  # Should be X.Y.Z
        )

        is_valid, error = validate_asp_message(message)

        assert not is_valid
        assert "Version" in error

    def test_validate_asp_message_empty(self):
        """Test rejecting empty message."""
        message = ASPMessage(
            protocol="ASP",
            version="1.0.0"
            # No declaration, query, or response
        )

        is_valid, error = validate_asp_message(message)

        assert not is_valid


@pytest.mark.unit
class TestASPIntegration:
    """Integration tests for ASP."""

    def test_full_semantic_discovery_workflow(self):
        """Test complete semantic discovery workflow."""
        registry = SemanticRegistry()

        # Register multiple agents with different capabilities
        agents = [
            SemanticDeclaration(
                agent_id="finance_agent_1",
                ontologies=[
                    OntologyReference(
                        ontology_id="apqc:7.0.1",
                        namespace="https://apqc.org/ontology/7.0.1"
                    )
                ],
                capabilities=[
                    SemanticCapability(
                        capability_id="budget_planning",
                        semantic_type="apqc:BudgetPlanning",
                        capability_name="Budget Planning",
                        quality_of_service=QualityOfService(
                            accuracy=0.95,
                            latency_ms=5000
                        )
                    )
                ],
                domain_knowledge=[
                    DomainKnowledge(
                        domain="finance",
                        subdomain="budgeting",
                        proficiency="expert",
                        standards=["GAAP", "IFRS"]
                    )
                ]
            ),
            SemanticDeclaration(
                agent_id="finance_agent_2",
                ontologies=[
                    OntologyReference(
                        ontology_id="schema.org:latest",
                        namespace="https://schema.org/"
                    )
                ],
                capabilities=[
                    SemanticCapability(
                        capability_id="financial_analysis",
                        semantic_type="schema.org:AnalyzeAction",
                        capability_name="Financial Analysis"
                    )
                ],
                domain_knowledge=[
                    DomainKnowledge(
                        domain="finance",
                        proficiency="advanced"
                    )
                ]
            )
        ]

        for agent in agents:
            registry.register(agent)

        # Discover agents with budget planning capability
        required = SemanticCapability(
            capability_id="need_budget_planning",
            semantic_type="apqc:BudgetPlanning"
        )

        response = registry.discover_capabilities(required, min_score=0.5)

        # Should find finance_agent_1
        assert len(response.matches) >= 1
        budget_matches = [m for m in response.matches if m.capability_id == "budget_planning"]
        assert len(budget_matches) == 1
        assert budget_matches[0].agent_id == "finance_agent_1"

    def test_asp_message_roundtrip(self):
        """Test ASP message serialization/deserialization."""
        # Create message
        declaration = SemanticDeclaration(
            agent_id="test_agent",
            ontologies=[
                OntologyReference(
                    ontology_id="apqc:7.0.1",
                    namespace="https://apqc.org/ontology/7.0.1"
                )
            ],
            capabilities=[
                SemanticCapability(
                    capability_id="test_cap",
                    semantic_type="apqc:Testing"
                )
            ]
        )

        message = ASPMessage(
            protocol="ASP",
            version="1.0.0",
            semantic_declaration=declaration
        )

        # Convert to dict
        data = message.to_dict()

        assert data['protocol'] == "ASP"
        assert data['version'] == "1.0.0"
        assert 'semantic_declaration' in data
        assert data['semantic_declaration']['agent_id'] == "test_agent"
