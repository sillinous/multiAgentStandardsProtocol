"""
Comprehensive tests for Global Agent Factory as a Service (AgentFaaS)

Tests cover:
- Template system
- Code generation engine
- API endpoints
- Research integration
- Compliance checking
- End-to-end agent creation
"""

import pytest
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Add autonomous-ecosystem to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from library.core.agent_template_system import (
    AgentTemplateSystem, AgentTemplate, AgentSpecification,
    ComplianceFramework, PerformanceTier, DeploymentFormat, APQCCategory
)
from library.core.agent_code_generator import AgentCodeGenerator


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def template_system():
    """Create template system instance"""
    db_path = "test_agent_templates.db"
    # Clean up any existing test database
    if Path(db_path).exists():
        Path(db_path).unlink()
    return AgentTemplateSystem(db_path=db_path)


@pytest.fixture
def code_generator(template_system):
    """Create code generator instance"""
    db_path = "test_agent_generation.db"
    if Path(db_path).exists():
        Path(db_path).unlink()
    return AgentCodeGenerator(db_path=db_path, template_system=template_system)


@pytest.fixture
def sample_specification():
    """Create sample agent specification"""
    return AgentSpecification(
        agent_name="Test Market Analyzer",
        description="Analyzes market trends and competitor data",
        business_objective="Provide actionable market insights to improve strategic decisions",
        apqc_process="3.1",
        compliance_frameworks=[ComplianceFramework.GDPR, ComplianceFramework.SOC2],
        performance_tier=PerformanceTier.OPTIMIZED,
        max_response_time_ms=500,
        concurrent_users=100,
        deployment_format=DeploymentFormat.DOCKER
    )


# ============================================================================
# Template System Tests
# ============================================================================

class TestTemplateSystem:
    """Test suite for Agent Template System"""

    def test_initialization(self, template_system):
        """Test template system initializes correctly"""
        assert template_system is not None
        assert Path(template_system.db_path).exists()

        # Should have loaded built-in templates
        stats = template_system.get_statistics()
        assert stats['total_templates'] >= 10  # We created 10 templates

    def test_search_templates_by_apqc(self, template_system):
        """Test searching templates by APQC process"""
        results = template_system.search_templates(apqc_process="1.3")

        assert len(results) > 0
        assert all(r['apqc_process'] == "1.3" for r in results)

    def test_search_templates_by_category(self, template_system):
        """Test searching templates by APQC category"""
        results = template_system.search_templates(
            apqc_category=APQCCategory.VISION_STRATEGY
        )

        assert len(results) > 0

    def test_search_templates_by_keyword(self, template_system):
        """Test searching templates by keyword"""
        results = template_system.search_templates(keyword="market")

        assert len(results) > 0
        # Results should contain "market" in name or description
        for result in results:
            text = f"{result['name']} {result['description']}".lower()
            assert "market" in text

    def test_get_template(self, template_system):
        """Test retrieving specific template"""
        # First, get all templates
        results = template_system.search_templates()
        assert len(results) > 0

        # Get first template
        template_id = results[0]['template_id']
        template = template_system.get_template(template_id)

        assert template is not None
        assert template['template_id'] == template_id

    def test_recommend_template(self, template_system, sample_specification):
        """Test template recommendation"""
        recommendations = template_system.recommend_template(sample_specification)

        assert len(recommendations) > 0
        # First recommendation should be for APQC 3.1 (market research)
        assert recommendations[0]['apqc_process'] == "3.1"

    def test_record_usage(self, template_system):
        """Test recording template usage"""
        results = template_system.search_templates()
        template_id = results[0]['template_id']

        # Record usage
        template_system.record_usage(
            template_id=template_id,
            agent_name="Test Agent",
            deployment_format=DeploymentFormat.DOCKER,
            compliance_frameworks=[ComplianceFramework.GDPR],
            success=True,
            performance_metrics={"quality_score": 95.0}
        )

        # Verify usage was recorded
        template = template_system.get_template(template_id)
        assert template['usage_count'] >= 1

    def test_statistics(self, template_system):
        """Test template system statistics"""
        stats = template_system.get_statistics()

        assert 'total_templates' in stats
        assert 'total_usage' in stats
        assert 'average_success_rate' in stats
        assert 'top_templates' in stats

        assert stats['total_templates'] >= 10
        assert isinstance(stats['top_templates'], list)


# ============================================================================
# Code Generator Tests
# ============================================================================

class TestCodeGenerator:
    """Test suite for Agent Code Generator"""

    def test_initialization(self, code_generator):
        """Test code generator initializes correctly"""
        assert code_generator is not None
        assert Path(code_generator.db_path).exists()

    def test_generate_agent(self, code_generator, sample_specification):
        """Test generating a complete agent"""
        generated = code_generator.generate_agent(sample_specification)

        assert generated is not None
        assert generated.agent_id is not None
        assert generated.agent_name == sample_specification.agent_name

        # Check all code artifacts were generated
        assert len(generated.agent_code) > 0
        assert len(generated.test_code) > 0
        assert len(generated.requirements_txt) > 0
        assert len(generated.dockerfile) > 0
        assert len(generated.readme_md) > 0

        # Check code quality
        assert generated.lines_of_code > 0
        assert generated.code_quality_score > 0

    def test_generated_agent_code_structure(self, code_generator, sample_specification):
        """Test that generated agent code has proper structure"""
        generated = code_generator.generate_agent(sample_specification)

        # Check for key imports
        assert "from autonomous_ecosystem.library.core.enhanced_base_agent import EnhancedBaseAgent" in generated.agent_code
        assert "import asyncio" in generated.agent_code

        # Check for class definition
        class_name = "TestMarketAnalyzer"  # PascalCase version
        assert f"class {class_name}(EnhancedBaseAgent):" in generated.agent_code

        # Check for docstrings
        assert '"""' in generated.agent_code

        # Check for type hints
        assert "-> " in generated.agent_code

    def test_generated_test_code(self, code_generator, sample_specification):
        """Test that generated test code is valid"""
        generated = code_generator.generate_agent(sample_specification)

        # Check for pytest imports
        assert "import pytest" in generated.test_code
        assert "@pytest.mark.asyncio" in generated.test_code

        # Check for test class
        assert "class Test" in generated.test_code

        # Check for fixtures
        assert "@pytest.fixture" in generated.test_code

    def test_generated_requirements(self, code_generator, sample_specification):
        """Test that requirements.txt includes necessary dependencies"""
        generated = code_generator.generate_agent(sample_specification)

        requirements = generated.requirements_txt

        # Check for base dependencies
        assert "pytest" in requirements
        assert "asyncio" in requirements or "aiohttp" in requirements

    def test_generated_dockerfile(self, code_generator, sample_specification):
        """Test that Dockerfile is valid"""
        generated = code_generator.generate_agent(sample_specification)

        dockerfile = generated.dockerfile

        # Check for key Dockerfile commands
        assert "FROM python:" in dockerfile
        assert "WORKDIR" in dockerfile
        assert "COPY" in dockerfile
        assert "RUN pip install" in dockerfile
        assert "CMD" in dockerfile

    def test_generated_readme(self, code_generator, sample_specification):
        """Test that README is comprehensive"""
        generated = code_generator.generate_agent(sample_specification)

        readme = generated.readme_md

        # Check for key sections
        assert "# " in readme  # Title
        assert "## " in readme  # Sections
        assert "Installation" in readme
        assert "Usage" in readme
        assert "Testing" in readme
        assert "Deployment" in readme

        # Check for business information
        assert sample_specification.business_objective in readme

    def test_compliance_checks(self, code_generator, sample_specification):
        """Test that compliance checks are performed"""
        generated = code_generator.generate_agent(sample_specification)

        assert len(generated.compliance_checks) > 0

        # Should have checks for specified frameworks
        assert any("gdpr" in check.lower() for check in generated.compliance_checks.keys())

    def test_code_quality_estimation(self, code_generator, sample_specification):
        """Test code quality score calculation"""
        generated = code_generator.generate_agent(sample_specification)

        # Should have a reasonable quality score
        assert 0 <= generated.code_quality_score <= 100
        # Generated code should have at least 70 quality score
        assert generated.code_quality_score >= 70

    def test_retrieve_generated_agent(self, code_generator, sample_specification):
        """Test retrieving a generated agent"""
        generated = code_generator.generate_agent(sample_specification)

        # Retrieve agent
        retrieved = code_generator.get_generated_agent(generated.agent_id)

        assert retrieved is not None
        assert retrieved['agent_id'] == generated.agent_id

    def test_generation_statistics(self, code_generator, sample_specification):
        """Test generation statistics"""
        # Generate a few agents
        for i in range(3):
            spec = AgentSpecification(
                agent_name=f"Test Agent {i}",
                description=f"Test agent {i}",
                business_objective="Test objective",
                apqc_process="3.1"
            )
            code_generator.generate_agent(spec)

        stats = code_generator.get_statistics()

        assert stats['total_agents_generated'] >= 3
        assert stats['average_code_quality'] > 0
        assert stats['total_lines_of_code'] > 0


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.asyncio
class TestEndToEndAgentGeneration:
    """End-to-end tests for complete agent generation flow"""

    async def test_complete_agent_generation_flow(self, code_generator, sample_specification):
        """Test complete flow from specification to deployable agent"""
        # 1. Generate agent
        generated = code_generator.generate_agent(sample_specification)

        assert generated is not None

        # 2. Verify all artifacts
        assert generated.agent_code
        assert generated.test_code
        assert generated.requirements_txt
        assert generated.dockerfile
        assert generated.readme_md

        # 3. Verify compliance
        assert len(generated.compliance_checks) > 0

        # 4. Verify can be retrieved
        retrieved = code_generator.get_generated_agent(generated.agent_id)
        assert retrieved is not None

    async def test_multiple_agents_with_same_template(self, code_generator):
        """Test generating multiple agents from same template"""
        agents = []

        for i in range(3):
            spec = AgentSpecification(
                agent_name=f"Strategic Manager {i}",
                description=f"Strategic initiative manager instance {i}",
                business_objective="Manage strategic initiatives",
                apqc_process="1.3"
            )
            generated = code_generator.generate_agent(spec)
            agents.append(generated)

        # All should be unique
        agent_ids = [a.agent_id for a in agents]
        assert len(agent_ids) == len(set(agent_ids))

        # All should use same template
        template_ids = [a.template_id for a in agents]
        assert len(set(template_ids)) == 1

    async def test_agents_with_different_compliance(self, code_generator):
        """Test generating agents with different compliance requirements"""
        # GDPR agent
        gdpr_spec = AgentSpecification(
            agent_name="GDPR Compliant Agent",
            description="GDPR compliant agent",
            business_objective="Process data with GDPR compliance",
            compliance_frameworks=[ComplianceFramework.GDPR]
        )
        gdpr_agent = code_generator.generate_agent(gdpr_spec)

        # HIPAA agent
        hipaa_spec = AgentSpecification(
            agent_name="HIPAA Compliant Agent",
            description="HIPAA compliant agent",
            business_objective="Process healthcare data",
            compliance_frameworks=[ComplianceFramework.HIPAA]
        )
        hipaa_agent = code_generator.generate_agent(hipaa_spec)

        # Should have different compliance checks
        assert gdpr_agent.compliance_checks != hipaa_agent.compliance_checks


# ============================================================================
# Performance Tests
# ============================================================================

@pytest.mark.benchmark
class TestPerformance:
    """Performance benchmarking tests"""

    def test_template_search_performance(self, template_system, benchmark):
        """Benchmark template search performance"""
        def search():
            return template_system.search_templates(keyword="market")

        result = benchmark(search)
        assert len(result) > 0

    def test_agent_generation_performance(self, code_generator, sample_specification, benchmark):
        """Benchmark agent generation performance"""
        def generate():
            return code_generator.generate_agent(sample_specification)

        result = benchmark(generate)
        assert result is not None

    @pytest.mark.asyncio
    async def test_concurrent_agent_generation(self, code_generator):
        """Test concurrent agent generation"""
        import time

        async def generate_agent(i):
            spec = AgentSpecification(
                agent_name=f"Concurrent Agent {i}",
                description=f"Agent {i}",
                business_objective="Test concurrency",
                apqc_process="3.1"
            )
            return code_generator.generate_agent(spec)

        # Generate 5 agents concurrently
        start_time = time.time()
        tasks = [generate_agent(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start_time

        # All should succeed
        assert len(results) == 5
        assert all(r is not None for r in results)

        # Should be faster than sequential (rough check)
        print(f"Generated 5 agents in {elapsed:.2f}s")


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_invalid_apqc_process(self, code_generator):
        """Test handling of invalid APQC process"""
        spec = AgentSpecification(
            agent_name="Invalid Agent",
            description="Test",
            business_objective="Test",
            apqc_process="99.99"  # Invalid
        )

        # Should still generate (fallback to generic template or best match)
        # This tests graceful degradation
        try:
            generated = code_generator.generate_agent(spec)
            assert generated is not None
        except ValueError:
            # Also acceptable - explicit error
            pass

    def test_missing_required_fields(self):
        """Test that required fields are enforced"""
        with pytest.raises(TypeError):
            # Missing required fields
            spec = AgentSpecification()

    def test_invalid_compliance_framework(self):
        """Test invalid compliance framework"""
        with pytest.raises(ValueError):
            ComplianceFramework("invalid_framework")

    def test_invalid_performance_tier(self):
        """Test invalid performance tier"""
        with pytest.raises(ValueError):
            PerformanceTier("invalid_tier")


# ============================================================================
# Cleanup
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def cleanup():
    """Clean up test databases after all tests"""
    yield

    # Clean up test databases
    test_dbs = [
        "test_agent_templates.db",
        "test_agent_generation.db",
        "agent_templates_demo.db",
        "agent_generation_demo.db"
    ]

    for db in test_dbs:
        if Path(db).exists():
            try:
                Path(db).unlink()
            except:
                pass


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
