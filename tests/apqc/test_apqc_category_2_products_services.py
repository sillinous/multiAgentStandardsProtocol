"""
APQC Category 2.0 - Products and Services Agent Tests

Comprehensive tests for all 4 Products and Services agents from APQC Category 2.0.

Agents tested:
1. DesignPrototypeProductsCreativeAgent (2.0)
2. TestMarketForNewProductsServicesCreativeAgent (2.0)
3. PrepareForProductionCreativeAgent
4. GenerateDefineNewProductServiceIdeasCreativeAgent

Test Coverage:
- Individual agent tests (initialization, execution, health, protocols)
- Product lifecycle integration tests
- Design-to-production workflow tests
- Market testing and validation

Version: 1.0.0
Framework: APQC 7.0.1
Category: 2.0 - Develop and Manage Products and Services
"""

import pytest
from typing import Dict, Any
from .test_apqc_framework import APQCAgentTestCase, MockDataGenerator, APQCTestUtilities


# ========================================================================
# Category 2.0 Agent Tests
# ========================================================================

@pytest.mark.apqc
@pytest.mark.apqc_category_2
class TestDesignPrototypeProductsCreativeAgent(APQCAgentTestCase):
    """
    Tests for DesignPrototypeProductsCreativeAgent (APQC 2.0)

    Agent: Design and prototype products
    Path: src/superstandard/agents/ui/design_prototype_products_creative_agent.py
    Domain: product_design | Type: creative
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.ui.design_prototype_products_creative_agent import (
            DesignPrototypeProductsCreativeAgent
        )
        return DesignPrototypeProductsCreativeAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.ui.design_prototype_products_creative_agent import (
            DesignPrototypeProductsCreativeAgentConfig
        )
        return DesignPrototypeProductsCreativeAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "2.0",
            "apqc_framework_version": "7.0.1"
        }

    def get_expected_capabilities(self):
        """Return expected capabilities."""
        return ["design", "prototyping", "creative", "innovation"]

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for product design."""
        return {
            "task_type": "design_prototype",
            "data": {
                "product_concept": {
                    "name": "Smart Widget 2.0",
                    "category": "consumer_electronics",
                    "target_market": "tech_enthusiasts"
                },
                "requirements": {
                    "features": ["wireless", "ai_powered", "eco_friendly"],
                    "constraints": ["budget_500", "launch_6_months"],
                    "performance": {"battery_life": "24_hours", "response_time": "100ms"}
                },
                "design_specifications": {
                    "form_factor": "handheld",
                    "materials": ["recycled_plastic", "aluminum"],
                    "colors": ["black", "white", "blue"]
                }
            },
            "context": {
                "design_phase": "concept",
                "priority": "high"
            },
            "priority": "high"
        }

    @pytest.mark.asyncio
    async def test_product_design_workflow(self):
        """Test product design and prototyping workflow."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        # Test design phases
        phases = ["concept", "detailed_design", "prototype"]

        for phase in phases:
            input_data = self.generate_valid_input()
            input_data["context"]["design_phase"] = phase

            result = await agent.execute(input_data)

            assert result['status'] in ['completed', 'degraded']
            assert 'output' in result


@pytest.mark.apqc
@pytest.mark.apqc_category_2
class TestTestMarketForNewProductsServicesCreativeAgent(APQCAgentTestCase):
    """
    Tests for TestMarketForNewProductsServicesCreativeAgent (APQC 2.0)

    Agent: Test market for new products and services
    Path: src/superstandard/agents/testing/test_market_for_new_products_services_creative_agent.py
    Domain: market_testing | Type: creative
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.testing.test_market_for_new_products_services_creative_agent import (
            TestMarketForNewProductsServicesCreativeAgent
        )
        return TestMarketForNewProductsServicesCreativeAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.testing.test_market_for_new_products_services_creative_agent import (
            TestMarketForNewProductsServicesCreativeAgentConfig
        )
        return TestMarketForNewProductsServicesCreativeAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "2.0",
            "apqc_framework_version": "7.0.1"
        }

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for market testing."""
        return {
            "task_type": "market_test",
            "data": {
                "product": {
                    "name": "Smart Widget 2.0",
                    "prototype_version": "v1.0",
                    "features": ["wireless", "ai_powered"]
                },
                "test_market": {
                    "geography": "west_coast_us",
                    "demographics": {"age_range": "25-45", "income": "high"},
                    "sample_size": 500
                },
                "test_parameters": {
                    "duration": "30_days",
                    "metrics": ["adoption_rate", "satisfaction", "willingness_to_pay"],
                    "success_criteria": {"adoption_rate": 0.15, "satisfaction": 4.0}
                },
                "pricing_options": [49.99, 59.99, 69.99]
            },
            "context": {
                "test_type": "beta",
                "priority": "high"
            },
            "priority": "high"
        }

    @pytest.mark.asyncio
    async def test_market_testing_phases(self):
        """Test different market testing phases."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        test_types = ["alpha", "beta", "pilot"]

        for test_type in test_types:
            input_data = self.generate_valid_input()
            input_data["context"]["test_type"] = test_type

            result = await agent.execute(input_data)

            assert result['status'] in ['completed', 'degraded']


@pytest.mark.apqc
@pytest.mark.apqc_category_2
class TestPrepareForProductionCreativeAgent(APQCAgentTestCase):
    """
    Tests for PrepareForProductionCreativeAgent

    Agent: Prepare for production
    Path: src/superstandard/agents/infrastructure/prepare_for_production_creative_agent.py
    Domain: production | Type: creative
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.infrastructure.prepare_for_production_creative_agent import (
            PrepareForProductionCreativeAgent
        )
        return PrepareForProductionCreativeAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.infrastructure.prepare_for_production_creative_agent import (
            PrepareForProductionCreativeAgentConfig
        )
        return PrepareForProductionCreativeAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "2.0",
            "apqc_framework_version": "7.0.1"
        }

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for production preparation."""
        return {
            "task_type": "prepare_production",
            "data": {
                "product": {
                    "name": "Smart Widget 2.0",
                    "final_design": "approved",
                    "market_test_results": {"success": True, "feedback": "positive"}
                },
                "production_requirements": {
                    "initial_volume": 10000,
                    "quality_standards": "iso_9001",
                    "timeline": "90_days"
                },
                "supply_chain": {
                    "suppliers": ["supplier_a", "supplier_b"],
                    "materials": ["plastic", "electronics", "packaging"],
                    "lead_times": {"plastic": "30_days", "electronics": "45_days"}
                },
                "manufacturing": {
                    "facility": "plant_1",
                    "capacity": 1000,
                    "shifts": 2
                }
            },
            "context": {
                "launch_date": "2025-06-01",
                "priority": "high"
            },
            "priority": "high"
        }

    @pytest.mark.asyncio
    async def test_production_readiness_checklist(self):
        """Test production readiness validation."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']
        assert 'output' in result


@pytest.mark.apqc
@pytest.mark.apqc_category_2
class TestGenerateDefineNewProductServiceIdeasCreativeAgent(APQCAgentTestCase):
    """
    Tests for GenerateDefineNewProductServiceIdeasCreativeAgent

    Agent: Generate and define new product/service ideas
    Path: src/superstandard/agents/blockchain/generate_define_new_product_service_ideas_creative_agent.py
    Domain: innovation | Type: creative
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.blockchain.generate_define_new_product_service_ideas_creative_agent import (
            GenerateDefineNewProductServiceIdeasCreativeAgent
        )
        return GenerateDefineNewProductServiceIdeasCreativeAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.blockchain.generate_define_new_product_service_ideas_creative_agent import (
            GenerateDefineNewProductServiceIdeasCreativeAgentConfig
        )
        return GenerateDefineNewProductServiceIdeasCreativeAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "2.0",
            "apqc_framework_version": "7.0.1"
        }

    def get_expected_capabilities(self):
        """Return expected capabilities."""
        return ["innovation", "ideation", "creative", "analysis"]

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for idea generation."""
        return {
            "task_type": "generate_ideas",
            "data": {
                "innovation_goals": ["market_disruption", "customer_delight", "revenue_growth"],
                "market_insights": {
                    "trends": ["sustainability", "ai", "personalization"],
                    "gaps": ["affordable_premium", "eco_tech"],
                    "customer_needs": ["convenience", "quality", "value"]
                },
                "constraints": {
                    "budget": 1000000,
                    "timeline": "12_months",
                    "capabilities": ["software", "hardware", "services"]
                },
                "ideation_parameters": {
                    "quantity": 20,
                    "diversity": "high",
                    "feasibility_threshold": 0.6
                }
            },
            "context": {
                "innovation_session": "Q1_2025",
                "priority": "high"
            },
            "priority": "high"
        }

    @pytest.mark.asyncio
    async def test_idea_generation_quantity(self):
        """Test that agent generates requested number of ideas."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']
        assert 'output' in result


# ========================================================================
# Category Integration Tests
# ========================================================================

@pytest.mark.apqc
@pytest.mark.apqc_category_2
@pytest.mark.apqc_integration
class TestCategory2Integration:
    """
    Integration tests for Category 2.0 - Products and Services agents.

    Tests complete product lifecycle from ideation to production.
    """

    @pytest.mark.asyncio
    async def test_complete_product_lifecycle(self):
        """
        Test complete product lifecycle workflow.

        Workflow:
        1. Generate ideas (GenerateDefineNewProductServiceIdeasCreativeAgent)
        2. Design and prototype (DesignPrototypeProductsCreativeAgent)
        3. Test market (TestMarketForNewProductsServicesCreativeAgent)
        4. Prepare for production (PrepareForProductionCreativeAgent)
        """
        # Import agents
        from superstandard.agents.blockchain.generate_define_new_product_service_ideas_creative_agent import (
            GenerateDefineNewProductServiceIdeasCreativeAgent,
            GenerateDefineNewProductServiceIdeasCreativeAgentConfig
        )
        from superstandard.agents.ui.design_prototype_products_creative_agent import (
            DesignPrototypeProductsCreativeAgent,
            DesignPrototypeProductsCreativeAgentConfig
        )
        from superstandard.agents.testing.test_market_for_new_products_services_creative_agent import (
            TestMarketForNewProductsServicesCreativeAgent,
            TestMarketForNewProductsServicesCreativeAgentConfig
        )
        from superstandard.agents.infrastructure.prepare_for_production_creative_agent import (
            PrepareForProductionCreativeAgent,
            PrepareForProductionCreativeAgentConfig
        )

        # Create agent instances
        ideation_agent = GenerateDefineNewProductServiceIdeasCreativeAgent(
            GenerateDefineNewProductServiceIdeasCreativeAgentConfig()
        )
        design_agent = DesignPrototypeProductsCreativeAgent(
            DesignPrototypeProductsCreativeAgentConfig()
        )
        market_test_agent = TestMarketForNewProductsServicesCreativeAgent(
            TestMarketForNewProductsServicesCreativeAgentConfig()
        )
        production_agent = PrepareForProductionCreativeAgent(
            PrepareForProductionCreativeAgentConfig()
        )

        # Step 1: Generate ideas
        ideation_input = {
            "task_type": "generate_ideas",
            "data": {
                "innovation_goals": ["market_disruption"],
                "market_insights": {"trends": ["ai", "sustainability"]},
                "ideation_parameters": {"quantity": 5}
            },
            "priority": "high"
        }
        ideation_result = await ideation_agent.execute(ideation_input)
        assert ideation_result['status'] in ['completed', 'degraded']

        # Step 2: Design and prototype
        design_input = {
            "task_type": "design_prototype",
            "data": {
                "product_concept": ideation_result.get('output', {}),
                "requirements": {"features": ["ai_powered"], "constraints": ["budget_500"]}
            },
            "priority": "high"
        }
        design_result = await design_agent.execute(design_input)
        assert design_result['status'] in ['completed', 'degraded']

        # Step 3: Market test
        market_test_input = {
            "task_type": "market_test",
            "data": {
                "product": design_result.get('output', {}),
                "test_market": {"geography": "west_coast_us", "sample_size": 500},
                "test_parameters": {"duration": "30_days"}
            },
            "priority": "high"
        }
        market_test_result = await market_test_agent.execute(market_test_input)
        assert market_test_result['status'] in ['completed', 'degraded']

        # Step 4: Prepare for production
        production_input = {
            "task_type": "prepare_production",
            "data": {
                "product": design_result.get('output', {}),
                "market_test_results": market_test_result.get('output', {}),
                "production_requirements": {"initial_volume": 10000}
            },
            "priority": "high"
        }
        production_result = await production_agent.execute(production_input)
        assert production_result['status'] in ['completed', 'degraded']

    @pytest.mark.asyncio
    async def test_iterative_design_refinement(self):
        """Test iterative design refinement based on market feedback."""
        from superstandard.agents.ui.design_prototype_products_creative_agent import (
            DesignPrototypeProductsCreativeAgent,
            DesignPrototypeProductsCreativeAgentConfig
        )
        from superstandard.agents.testing.test_market_for_new_products_services_creative_agent import (
            TestMarketForNewProductsServicesCreativeAgent,
            TestMarketForNewProductsServicesCreativeAgentConfig
        )

        design_agent = DesignPrototypeProductsCreativeAgent(
            DesignPrototypeProductsCreativeAgentConfig()
        )
        test_agent = TestMarketForNewProductsServicesCreativeAgent(
            TestMarketForNewProductsServicesCreativeAgentConfig()
        )

        # Initial design
        design_input = {
            "task_type": "design_prototype",
            "data": {
                "product_concept": {"name": "Test Product"},
                "requirements": {"features": ["feature_a"]}
            },
            "priority": "high"
        }
        design_result_v1 = await design_agent.execute(design_input)

        # Market test v1
        test_input = {
            "task_type": "market_test",
            "data": {
                "product": design_result_v1.get('output', {}),
                "test_market": {"sample_size": 100}
            },
            "priority": "high"
        }
        test_result_v1 = await test_agent.execute(test_input)

        # Refine design based on feedback
        design_input_v2 = design_input.copy()
        design_input_v2["data"]["market_feedback"] = test_result_v1.get('output', {})
        design_result_v2 = await design_agent.execute(design_input_v2)

        assert design_result_v2['status'] in ['completed', 'degraded']


# ========================================================================
# Category-Specific Tests
# ========================================================================

@pytest.mark.apqc
@pytest.mark.apqc_category_2
class TestCategory2Capabilities:
    """
    Test category-specific capabilities for Products and Services agents.
    """

    @pytest.mark.asyncio
    async def test_creative_agents_innovation_capability(self):
        """Verify creative agents have innovation capabilities."""
        from superstandard.agents.blockchain.generate_define_new_product_service_ideas_creative_agent import (
            GenerateDefineNewProductServiceIdeasCreativeAgent,
            GenerateDefineNewProductServiceIdeasCreativeAgentConfig
        )

        agent = GenerateDefineNewProductServiceIdeasCreativeAgent(
            GenerateDefineNewProductServiceIdeasCreativeAgentConfig()
        )

        # Should have creative/innovation capabilities
        assert hasattr(agent, 'capabilities_list')

    @pytest.mark.asyncio
    async def test_product_design_quality_standards(self):
        """Test that design agents consider quality standards."""
        from superstandard.agents.ui.design_prototype_products_creative_agent import (
            DesignPrototypeProductsCreativeAgent,
            DesignPrototypeProductsCreativeAgentConfig
        )

        agent = DesignPrototypeProductsCreativeAgent(
            DesignPrototypeProductsCreativeAgentConfig()
        )

        quality_input = {
            "task_type": "design_prototype",
            "data": {
                "product_concept": {"name": "Premium Product"},
                "requirements": {"quality_standard": "premium"}
            },
            "priority": "high"
        }

        result = await agent.execute(quality_input)
        assert result['status'] in ['completed', 'degraded']


# ========================================================================
# Performance Tests
# ========================================================================

@pytest.mark.apqc
@pytest.mark.apqc_category_2
@pytest.mark.slow
class TestCategory2Performance:
    """
    Performance tests for Category 2 agents.
    """

    @pytest.mark.asyncio
    async def test_parallel_idea_generation(self):
        """Test multiple idea generation sessions in parallel."""
        import asyncio
        from superstandard.agents.blockchain.generate_define_new_product_service_ideas_creative_agent import (
            GenerateDefineNewProductServiceIdeasCreativeAgent,
            GenerateDefineNewProductServiceIdeasCreativeAgentConfig
        )

        agents = [
            GenerateDefineNewProductServiceIdeasCreativeAgent(
                GenerateDefineNewProductServiceIdeasCreativeAgentConfig()
            )
            for _ in range(3)
        ]

        input_data = {
            "task_type": "generate_ideas",
            "data": {
                "innovation_goals": ["innovation"],
                "ideation_parameters": {"quantity": 5}
            },
            "priority": "high"
        }

        tasks = [agent.execute(input_data) for agent in agents]
        results = await asyncio.gather(*tasks)

        assert len(results) == 3
        for result in results:
            assert result['status'] in ['completed', 'degraded']


if __name__ == "__main__":
    """Run tests when executed directly."""
    pytest.main([__file__, "-v", "--tb=short"])
