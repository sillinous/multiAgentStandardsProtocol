"""
APQC Category 3.0 - Market and Sell Agent Tests

Comprehensive tests for all 13 Market and Sell agents from APQC Category 3.0.

Agents tested:
1. UnderstandMarketsCustomersCapabilitiesSalesMarketingAgent (3.1)
2. DevelopMarketingStrategySalesMarketingAgent (3.2)
3. DevelopManageMarketingPlansSalesMarketingAgent (3.3)
4. DevelopSalesStrategySalesMarketingAgent (3.4)
5. DevelopManageSalesPlansSalesMarketingAgent (3.5)
6. SegmentCustomersSalesMarketingAgent
7. ManageProductPortfolioSalesMarketingAgent
8. ManageSalesChannelsSalesMarketingAgent
9. ManageCampaignEffectivenessSalesMarketingAgent
10. ManagePricingSalesMarketingAgent
11. ManageProductLifecycleSalesMarketingAgent
12. ConductCustomerResearchSalesMarketingAgent
13. AnalyzeMarketTrendsSalesMarketingAgent

Test Coverage:
- Individual agent tests (initialization, execution, health, protocols)
- Sales and marketing workflow integration
- Campaign management tests
- Customer segmentation and targeting

Version: 1.0.0
Framework: APQC 7.0.1
Category: 3.0 - Market and Sell Products and Services
"""

import pytest
from typing import Dict, Any
from .test_apqc_framework import APQCAgentTestCase, MockDataGenerator, APQCTestUtilities


# ========================================================================
# Category 3.0 Agent Tests
# ========================================================================

@pytest.mark.apqc
@pytest.mark.apqc_category_3
class TestUnderstandMarketsCustomersCapabilitiesSalesMarketingAgent(APQCAgentTestCase):
    """
    Tests for UnderstandMarketsCustomersCapabilitiesSalesMarketingAgent (APQC 3.1)

    Agent: Understand markets, customers, and capabilities
    Path: src/superstandard/agents/trading/understand_markets_customers_capabilities_sales_marketing_agent.py
    Domain: sales_marketing | Type: sales_marketing
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.trading.understand_markets_customers_capabilities_sales_marketing_agent import (
            UnderstandMarketsCustomersCapabilitiesSalesMarketingAgent
        )
        return UnderstandMarketsCustomersCapabilitiesSalesMarketingAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.trading.understand_markets_customers_capabilities_sales_marketing_agent import (
            UnderstandMarketsCustomersCapabilitiesSalesMarketingAgentConfig
        )
        return UnderstandMarketsCustomersCapabilitiesSalesMarketingAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "3.0",
            "apqc_process_id": "3.1",
            "apqc_framework_version": "7.0.1"
        }

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for market understanding."""
        return {
            "task_type": "understand_market",
            "data": {
                "market_scope": {
                    "geographies": ["north_america", "europe"],
                    "segments": ["enterprise", "mid_market", "smb"],
                    "industries": ["technology", "finance", "healthcare"]
                },
                "customer_analysis": {
                    "needs": ["efficiency", "cost_reduction", "innovation"],
                    "pain_points": ["complexity", "integration", "cost"],
                    "buying_behavior": {"decision_makers": ["cto", "cfo"], "cycle": "6_months"}
                },
                "capabilities_assessment": {
                    "current": ["product_a", "service_b"],
                    "gaps": ["international_support", "industry_specific"],
                    "competitive_advantages": ["innovation", "customer_service"]
                }
            },
            "context": {
                "analysis_period": "Q1_2025",
                "priority": "high"
            },
            "priority": "high"
        }


@pytest.mark.apqc
@pytest.mark.apqc_category_3
class TestDevelopMarketingStrategySalesMarketingAgent(APQCAgentTestCase):
    """
    Tests for DevelopMarketingStrategySalesMarketingAgent (APQC 3.2)

    Agent: Develop marketing strategy
    Path: src/superstandard/agents/trading/develop_marketing_strategy_sales_marketing_agent.py
    Domain: sales_marketing | Type: sales_marketing
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.trading.develop_marketing_strategy_sales_marketing_agent import (
            DevelopMarketingStrategySalesMarketingAgent
        )
        return DevelopMarketingStrategySalesMarketingAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.trading.develop_marketing_strategy_sales_marketing_agent import (
            DevelopMarketingStrategySalesMarketingAgentConfig
        )
        return DevelopMarketingStrategySalesMarketingAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "3.0",
            "apqc_process_id": "3.2",
            "apqc_framework_version": "7.0.1"
        }

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for marketing strategy."""
        return {
            "task_type": "develop_marketing_strategy",
            "data": {
                "business_objectives": {
                    "revenue_target": 10000000,
                    "market_share_target": 0.20,
                    "brand_awareness": "increase_50_percent"
                },
                "target_markets": {
                    "primary": ["enterprise_tech"],
                    "secondary": ["mid_market_finance"],
                    "emerging": ["healthcare_smb"]
                },
                "positioning": {
                    "value_proposition": "innovation_leader",
                    "differentiation": ["ai_powered", "customer_centric", "cost_effective"],
                    "competitive_positioning": "premium_value"
                },
                "marketing_mix": {
                    "product_strategy": "portfolio_expansion",
                    "pricing_strategy": "value_based",
                    "distribution_strategy": "multi_channel",
                    "promotion_strategy": "integrated_marketing"
                }
            },
            "context": {
                "planning_horizon": "1_year",
                "priority": "high"
            },
            "priority": "high"
        }


@pytest.mark.apqc
@pytest.mark.apqc_category_3
class TestDevelopManageMarketingPlansSalesMarketingAgent(APQCAgentTestCase):
    """
    Tests for DevelopManageMarketingPlansSalesMarketingAgent (APQC 3.3)

    Agent: Develop and manage marketing plans
    Path: src/superstandard/agents/trading/develop_manage_marketing_plans_sales_marketing_agent.py
    Domain: sales_marketing | Type: sales_marketing
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.trading.develop_manage_marketing_plans_sales_marketing_agent import (
            DevelopManageMarketingPlansSalesMarketingAgent
        )
        return DevelopManageMarketingPlansSalesMarketingAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.trading.develop_manage_marketing_plans_sales_marketing_agent import (
            DevelopManageMarketingPlansSalesMarketingAgentConfig
        )
        return DevelopManageMarketingPlansSalesMarketingAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "3.0",
            "apqc_process_id": "3.3",
            "apqc_framework_version": "7.0.1"
        }

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for marketing plans."""
        return {
            "task_type": "develop_marketing_plan",
            "data": {
                "campaign": {
                    "name": "Q1_Product_Launch",
                    "objectives": ["awareness", "lead_generation", "sales"],
                    "budget": 500000,
                    "duration": "90_days"
                },
                "tactics": {
                    "digital": ["sem", "social_media", "content_marketing"],
                    "traditional": ["events", "pr"],
                    "channels": ["website", "linkedin", "google_ads"]
                },
                "kpis": {
                    "leads": 1000,
                    "conversion_rate": 0.05,
                    "roi": 3.0,
                    "brand_lift": 0.15
                },
                "timeline": [
                    {"phase": "planning", "weeks": 2},
                    {"phase": "execution", "weeks": 10},
                    {"phase": "optimization", "weeks": 2}
                ]
            },
            "context": {
                "quarter": "Q1_2025",
                "priority": "high"
            },
            "priority": "high"
        }


@pytest.mark.apqc
@pytest.mark.apqc_category_3
class TestDevelopSalesStrategySalesMarketingAgent(APQCAgentTestCase):
    """
    Tests for DevelopSalesStrategySalesMarketingAgent (APQC 3.4)

    Agent: Develop sales strategy
    Path: src/superstandard/agents/trading/develop_sales_strategy_sales_marketing_agent.py
    Domain: sales_marketing | Type: sales_marketing
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.trading.develop_sales_strategy_sales_marketing_agent import (
            DevelopSalesStrategySalesMarketingAgent
        )
        return DevelopSalesStrategySalesMarketingAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.trading.develop_sales_strategy_sales_marketing_agent import (
            DevelopSalesStrategySalesMarketingAgentConfig
        )
        return DevelopSalesStrategySalesMarketingAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "3.0",
            "apqc_process_id": "3.4",
            "apqc_framework_version": "7.0.1"
        }

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for sales strategy."""
        return {
            "task_type": "develop_sales_strategy",
            "data": {
                "revenue_targets": {
                    "annual": 10000000,
                    "quarterly": [2000000, 2500000, 2500000, 3000000],
                    "growth_rate": 0.25
                },
                "sales_model": {
                    "approach": "consultative",
                    "channels": ["direct", "partners", "online"],
                    "segments": ["enterprise", "mid_market"]
                },
                "sales_organization": {
                    "structure": "geographic_vertical",
                    "team_size": 20,
                    "specializations": ["industry", "product"]
                },
                "enablement": {
                    "tools": ["crm", "sales_intelligence"],
                    "training": ["product", "consultative_selling"],
                    "compensation": "quota_based"
                }
            },
            "context": {
                "fiscal_year": "2025",
                "priority": "high"
            },
            "priority": "high"
        }


@pytest.mark.apqc
@pytest.mark.apqc_category_3
class TestDevelopManageSalesPlansSalesMarketingAgent(APQCAgentTestCase):
    """
    Tests for DevelopManageSalesPlansSalesMarketingAgent (APQC 3.5)

    Agent: Develop and manage sales plans
    Path: src/superstandard/agents/trading/develop_manage_sales_plans_sales_marketing_agent.py
    Domain: sales_marketing | Type: sales_marketing
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.trading.develop_manage_sales_plans_sales_marketing_agent import (
            DevelopManageSalesPlansSalesMarketingAgent
        )
        return DevelopManageSalesPlansSalesMarketingAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.trading.develop_manage_sales_plans_sales_marketing_agent import (
            DevelopManageSalesPlansSalesMarketingAgentConfig
        )
        return DevelopManageSalesPlansSalesMarketingAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "3.0",
            "apqc_process_id": "3.5",
            "apqc_framework_version": "7.0.1"
        }

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for sales plans."""
        return {
            "task_type": "develop_sales_plan",
            "data": {
                "territory": {
                    "region": "west_coast",
                    "accounts": 50,
                    "potential": 5000000
                },
                "quotas": {
                    "annual": 2000000,
                    "monthly": [150000, 150000, 180000, 180000, 180000, 180000,
                                200000, 200000, 200000, 200000, 200000, 180000]
                },
                "pipeline": {
                    "target_coverage": 3.0,
                    "stages": ["prospect", "qualify", "propose", "negotiate", "close"],
                    "conversion_rates": [0.5, 0.4, 0.6, 0.7, 0.8]
                },
                "activities": {
                    "calls_per_week": 20,
                    "meetings_per_week": 10,
                    "proposals_per_month": 5
                }
            },
            "context": {
                "quarter": "Q1_2025",
                "priority": "high"
            },
            "priority": "high"
        }


@pytest.mark.apqc
@pytest.mark.apqc_category_3
class TestSegmentCustomersSalesMarketingAgent(APQCAgentTestCase):
    """
    Tests for SegmentCustomersSalesMarketingAgent

    Agent: Segment customers
    Path: src/superstandard/agents/trading/segment_customers_sales_marketing_agent.py
    Domain: sales_marketing | Type: sales_marketing
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.trading.segment_customers_sales_marketing_agent import (
            SegmentCustomersSalesMarketingAgent
        )
        return SegmentCustomersSalesMarketingAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.trading.segment_customers_sales_marketing_agent import (
            SegmentCustomersSalesMarketingAgentConfig
        )
        return SegmentCustomersSalesMarketingAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "3.0",
            "apqc_framework_version": "7.0.1"
        }

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for customer segmentation."""
        return {
            "task_type": "segment_customers",
            "data": {
                "customer_base": {
                    "total_customers": 10000,
                    "attributes": ["revenue", "industry", "size", "geography", "product_usage"]
                },
                "segmentation_criteria": {
                    "method": "behavioral_demographic",
                    "dimensions": ["value", "potential", "engagement"],
                    "target_segments": 5
                },
                "business_objectives": {
                    "personalization": True,
                    "resource_allocation": True,
                    "retention_focus": True
                }
            },
            "context": {
                "analysis_period": "annual",
                "priority": "high"
            },
            "priority": "high"
        }

    @pytest.mark.asyncio
    async def test_segmentation_methods(self):
        """Test different segmentation methods."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        methods = ["demographic", "behavioral", "psychographic", "value_based"]

        for method in methods:
            input_data = self.generate_valid_input()
            input_data["data"]["segmentation_criteria"]["method"] = method

            result = await agent.execute(input_data)
            assert result['status'] in ['completed', 'degraded']


@pytest.mark.apqc
@pytest.mark.apqc_category_3
class TestManageProductPortfolioSalesMarketingAgent(APQCAgentTestCase):
    """
    Tests for ManageProductPortfolioSalesMarketingAgent

    Agent: Manage product portfolio
    Path: src/superstandard/agents/trading/manage_product_portfolio_sales_marketing_agent.py
    Domain: sales_marketing | Type: sales_marketing
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.trading.manage_product_portfolio_sales_marketing_agent import (
            ManageProductPortfolioSalesMarketingAgent
        )
        return ManageProductPortfolioSalesMarketingAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.trading.manage_product_portfolio_sales_marketing_agent import (
            ManageProductPortfolioSalesMarketingAgentConfig
        )
        return ManageProductPortfolioSalesMarketingAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "3.0",
            "apqc_framework_version": "7.0.1"
        }

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for portfolio management."""
        return {
            "task_type": "manage_portfolio",
            "data": {
                "products": [
                    {"name": "Product_A", "revenue": 5000000, "growth": 0.15, "margin": 0.40},
                    {"name": "Product_B", "revenue": 3000000, "growth": 0.05, "margin": 0.30},
                    {"name": "Product_C", "revenue": 1000000, "growth": 0.25, "margin": 0.50}
                ],
                "portfolio_analysis": {
                    "framework": "bcg_matrix",
                    "metrics": ["revenue", "growth", "margin", "market_share"],
                    "time_period": "annual"
                },
                "optimization_goals": {
                    "revenue_growth": 0.20,
                    "margin_improvement": 0.05,
                    "portfolio_balance": True
                }
            },
            "context": {
                "review_cycle": "quarterly",
                "priority": "high"
            },
            "priority": "high"
        }


@pytest.mark.apqc
@pytest.mark.apqc_category_3
class TestManageSalesChannelsSalesMarketingAgent(APQCAgentTestCase):
    """
    Tests for ManageSalesChannelsSalesMarketingAgent

    Agent: Manage sales channels
    Path: src/superstandard/agents/trading/manage_sales_channels_sales_marketing_agent.py
    Domain: sales_marketing | Type: sales_marketing
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.trading.manage_sales_channels_sales_marketing_agent import (
            ManageSalesChannelsSalesMarketingAgent
        )
        return ManageSalesChannelsSalesMarketingAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.trading.manage_sales_channels_sales_marketing_agent import (
            ManageSalesChannelsSalesMarketingAgentConfig
        )
        return ManageSalesChannelsSalesMarketingAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "3.0",
            "apqc_framework_version": "7.0.1"
        }

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for channel management."""
        return {
            "task_type": "manage_channels",
            "data": {
                "channels": [
                    {"name": "direct_sales", "revenue_contribution": 0.60, "cost": 0.25},
                    {"name": "partners", "revenue_contribution": 0.30, "cost": 0.15},
                    {"name": "online", "revenue_contribution": 0.10, "cost": 0.05}
                ],
                "channel_strategy": {
                    "objectives": ["revenue_growth", "cost_efficiency", "market_coverage"],
                    "optimization": ["partner_enablement", "digital_transformation"]
                },
                "performance_metrics": {
                    "revenue": True,
                    "conversion": True,
                    "customer_acquisition_cost": True,
                    "customer_lifetime_value": True
                }
            },
            "context": {
                "review_period": "quarterly",
                "priority": "medium"
            },
            "priority": "medium"
        }


@pytest.mark.apqc
@pytest.mark.apqc_category_3
class TestManageCampaignEffectivenessSalesMarketingAgent(APQCAgentTestCase):
    """
    Tests for ManageCampaignEffectivenessSalesMarketingAgent

    Agent: Manage campaign effectiveness
    Path: src/superstandard/agents/trading/manage_campaign_effectiveness_sales_marketing_agent.py
    Domain: sales_marketing | Type: sales_marketing
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.trading.manage_campaign_effectiveness_sales_marketing_agent import (
            ManageCampaignEffectivenessSalesMarketingAgent
        )
        return ManageCampaignEffectivenessSalesMarketingAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.trading.manage_campaign_effectiveness_sales_marketing_agent import (
            ManageCampaignEffectivenessSalesMarketingAgentConfig
        )
        return ManageCampaignEffectivenessSalesMarketingAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "3.0",
            "apqc_framework_version": "7.0.1"
        }

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for campaign effectiveness."""
        return {
            "task_type": "analyze_campaign_effectiveness",
            "data": {
                "campaign": {
                    "name": "Q1_Launch",
                    "budget": 500000,
                    "duration_days": 90,
                    "channels": ["digital", "events", "pr"]
                },
                "metrics": {
                    "impressions": 1000000,
                    "clicks": 50000,
                    "leads": 5000,
                    "conversions": 250,
                    "revenue": 2500000
                },
                "analysis_dimensions": ["channel", "audience", "message", "timing"],
                "benchmarks": {
                    "ctr": 0.05,
                    "conversion_rate": 0.05,
                    "roi": 4.0
                }
            },
            "context": {
                "reporting_period": "campaign_completion",
                "priority": "high"
            },
            "priority": "high"
        }


@pytest.mark.apqc
@pytest.mark.apqc_category_3
class TestManagePricingSalesMarketingAgent(APQCAgentTestCase):
    """
    Tests for ManagePricingSalesMarketingAgent

    Agent: Manage pricing
    Path: src/superstandard/agents/trading/manage_pricing_sales_marketing_agent.py
    Domain: sales_marketing | Type: sales_marketing
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.trading.manage_pricing_sales_marketing_agent import (
            ManagePricingSalesMarketingAgent
        )
        return ManagePricingSalesMarketingAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.trading.manage_pricing_sales_marketing_agent import (
            ManagePricingSalesMarketingAgentConfig
        )
        return ManagePricingSalesMarketingAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "3.0",
            "apqc_framework_version": "7.0.1"
        }

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for pricing management."""
        return {
            "task_type": "optimize_pricing",
            "data": {
                "product": {
                    "name": "Enterprise_Solution",
                    "cost": 100,
                    "current_price": 200,
                    "competitor_prices": [180, 220, 250]
                },
                "pricing_strategy": {
                    "method": "value_based",
                    "objectives": ["margin_optimization", "market_share", "competitive_positioning"],
                    "constraints": ["minimum_margin_40", "market_competitiveness"]
                },
                "market_data": {
                    "demand_elasticity": -1.5,
                    "customer_willingness_to_pay": 250,
                    "price_sensitivity": "medium"
                }
            },
            "context": {
                "pricing_review": "quarterly",
                "priority": "high"
            },
            "priority": "high"
        }


@pytest.mark.apqc
@pytest.mark.apqc_category_3
class TestManageProductLifecycleSalesMarketingAgent(APQCAgentTestCase):
    """
    Tests for ManageProductLifecycleSalesMarketingAgent

    Agent: Manage product lifecycle
    Path: src/superstandard/agents/trading/manage_product_lifecycle_sales_marketing_agent.py
    Domain: sales_marketing | Type: sales_marketing
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.trading.manage_product_lifecycle_sales_marketing_agent import (
            ManageProductLifecycleSalesMarketingAgent
        )
        return ManageProductLifecycleSalesMarketingAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.trading.manage_product_lifecycle_sales_marketing_agent import (
            ManageProductLifecycleSalesMarketingAgentConfig
        )
        return ManageProductLifecycleSalesMarketingAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "3.0",
            "apqc_framework_version": "7.0.1"
        }

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for lifecycle management."""
        return {
            "task_type": "manage_lifecycle",
            "data": {
                "product": {
                    "name": "Product_X",
                    "current_stage": "growth",
                    "time_in_market": "18_months"
                },
                "lifecycle_stages": {
                    "introduction": {"duration": "6_months", "investment": 1000000},
                    "growth": {"duration": "24_months", "revenue_target": 5000000},
                    "maturity": {"duration": "36_months", "margin_target": 0.45},
                    "decline": {"actions": ["harvest", "divest"]}
                },
                "stage_transition_criteria": {
                    "growth_rate": True,
                    "market_share": True,
                    "profitability": True
                }
            },
            "context": {
                "review_frequency": "quarterly",
                "priority": "medium"
            },
            "priority": "medium"
        }


@pytest.mark.apqc
@pytest.mark.apqc_category_3
class TestConductCustomerResearchSalesMarketingAgent(APQCAgentTestCase):
    """
    Tests for ConductCustomerResearchSalesMarketingAgent

    Agent: Conduct customer research
    Path: src/superstandard/agents/trading/conduct_customer_research_sales_marketing_agent.py
    Domain: sales_marketing | Type: sales_marketing
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.trading.conduct_customer_research_sales_marketing_agent import (
            ConductCustomerResearchSalesMarketingAgent
        )
        return ConductCustomerResearchSalesMarketingAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.trading.conduct_customer_research_sales_marketing_agent import (
            ConductCustomerResearchSalesMarketingAgentConfig
        )
        return ConductCustomerResearchSalesMarketingAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "3.0",
            "apqc_framework_version": "7.0.1"
        }

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for customer research."""
        return {
            "task_type": "conduct_research",
            "data": {
                "research_objectives": [
                    "understand_needs",
                    "identify_pain_points",
                    "validate_product_concepts"
                ],
                "methodology": {
                    "type": "mixed_methods",
                    "qualitative": ["interviews", "focus_groups"],
                    "quantitative": ["surveys", "usage_analytics"]
                },
                "target_audience": {
                    "segments": ["current_customers", "prospects", "lost_customers"],
                    "sample_size": 500,
                    "demographics": {"industries": ["tech", "finance"], "sizes": ["enterprise"]}
                },
                "timeline": {
                    "design": "2_weeks",
                    "fieldwork": "4_weeks",
                    "analysis": "2_weeks"
                }
            },
            "context": {
                "research_purpose": "product_development",
                "priority": "high"
            },
            "priority": "high"
        }


@pytest.mark.apqc
@pytest.mark.apqc_category_3
class TestAnalyzeMarketTrendsSalesMarketingAgent(APQCAgentTestCase):
    """
    Tests for AnalyzeMarketTrendsSalesMarketingAgent

    Agent: Analyze market trends
    Path: src/superstandard/agents/trading/analyze_market_trends_sales_marketing_agent.py
    Domain: sales_marketing | Type: sales_marketing
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.trading.analyze_market_trends_sales_marketing_agent import (
            AnalyzeMarketTrendsSalesMarketingAgent
        )
        return AnalyzeMarketTrendsSalesMarketingAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.trading.analyze_market_trends_sales_marketing_agent import (
            AnalyzeMarketTrendsSalesMarketingAgentConfig
        )
        return AnalyzeMarketTrendsSalesMarketingAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "3.0",
            "apqc_framework_version": "7.0.1"
        }

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for trend analysis."""
        return {
            "task_type": "analyze_trends",
            "data": {
                "market_scope": {
                    "industry": "technology",
                    "geography": "global",
                    "time_horizon": "3_years"
                },
                "trend_categories": [
                    "technology_trends",
                    "customer_behavior",
                    "competitive_dynamics",
                    "regulatory_changes",
                    "economic_factors"
                ],
                "data_sources": [
                    "market_research_reports",
                    "industry_publications",
                    "customer_data",
                    "competitive_intelligence"
                ],
                "analysis_framework": {
                    "methods": ["pestel", "porter_five_forces", "trend_analysis"],
                    "outputs": ["trend_report", "implications", "recommendations"]
                }
            },
            "context": {
                "analysis_frequency": "quarterly",
                "priority": "high"
            },
            "priority": "high"
        }


# ========================================================================
# Category Integration Tests
# ========================================================================

@pytest.mark.apqc
@pytest.mark.apqc_category_3
@pytest.mark.apqc_integration
class TestCategory3Integration:
    """
    Integration tests for Category 3.0 - Market and Sell agents.

    Tests complete sales and marketing workflows.
    """

    @pytest.mark.asyncio
    async def test_complete_marketing_campaign_workflow(self):
        """
        Test complete marketing campaign workflow.

        Workflow:
        1. Understand markets and customers
        2. Develop marketing strategy
        3. Develop marketing plans
        4. Execute campaign
        5. Measure effectiveness
        """
        # Import agents
        from superstandard.agents.trading.understand_markets_customers_capabilities_sales_marketing_agent import (
            UnderstandMarketsCustomersCapabilitiesSalesMarketingAgent,
            UnderstandMarketsCustomersCapabilitiesSalesMarketingAgentConfig
        )
        from superstandard.agents.trading.develop_marketing_strategy_sales_marketing_agent import (
            DevelopMarketingStrategySalesMarketingAgent,
            DevelopMarketingStrategySalesMarketingAgentConfig
        )
        from superstandard.agents.trading.develop_manage_marketing_plans_sales_marketing_agent import (
            DevelopManageMarketingPlansSalesMarketingAgent,
            DevelopManageMarketingPlansSalesMarketingAgentConfig
        )
        from superstandard.agents.trading.manage_campaign_effectiveness_sales_marketing_agent import (
            ManageCampaignEffectivenessSalesMarketingAgent,
            ManageCampaignEffectivenessSalesMarketingAgentConfig
        )

        # Create agents
        market_agent = UnderstandMarketsCustomersCapabilitiesSalesMarketingAgent(
            UnderstandMarketsCustomersCapabilitiesSalesMarketingAgentConfig()
        )
        strategy_agent = DevelopMarketingStrategySalesMarketingAgent(
            DevelopMarketingStrategySalesMarketingAgentConfig()
        )
        plans_agent = DevelopManageMarketingPlansSalesMarketingAgent(
            DevelopManageMarketingPlansSalesMarketingAgentConfig()
        )
        effectiveness_agent = ManageCampaignEffectivenessSalesMarketingAgent(
            ManageCampaignEffectivenessSalesMarketingAgentConfig()
        )

        # Execute workflow
        market_result = await market_agent.execute(MockDataGenerator.generate_strategic_input())
        assert market_result['status'] in ['completed', 'degraded']

        strategy_result = await strategy_agent.execute(MockDataGenerator.generate_strategic_input())
        assert strategy_result['status'] in ['completed', 'degraded']

        plans_result = await plans_agent.execute(MockDataGenerator.generate_strategic_input())
        assert plans_result['status'] in ['completed', 'degraded']

        effectiveness_result = await effectiveness_agent.execute(MockDataGenerator.generate_strategic_input())
        assert effectiveness_result['status'] in ['completed', 'degraded']

    @pytest.mark.asyncio
    async def test_sales_and_marketing_alignment(self):
        """Test alignment between sales and marketing strategies."""
        from superstandard.agents.trading.develop_marketing_strategy_sales_marketing_agent import (
            DevelopMarketingStrategySalesMarketingAgent,
            DevelopMarketingStrategySalesMarketingAgentConfig
        )
        from superstandard.agents.trading.develop_sales_strategy_sales_marketing_agent import (
            DevelopSalesStrategySalesMarketingAgent,
            DevelopSalesStrategySalesMarketingAgentConfig
        )

        marketing_agent = DevelopMarketingStrategySalesMarketingAgent(
            DevelopMarketingStrategySalesMarketingAgentConfig()
        )
        sales_agent = DevelopSalesStrategySalesMarketingAgent(
            DevelopSalesStrategySalesMarketingAgentConfig()
        )

        marketing_result = await marketing_agent.execute(MockDataGenerator.generate_strategic_input())
        sales_result = await sales_agent.execute(MockDataGenerator.generate_strategic_input())

        assert marketing_result['status'] in ['completed', 'degraded']
        assert sales_result['status'] in ['completed', 'degraded']


if __name__ == "__main__":
    """Run tests when executed directly."""
    pytest.main([__file__, "-v", "--tb=short"])
