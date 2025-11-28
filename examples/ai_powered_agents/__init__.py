"""
AI-Powered Agent Examples

This package contains reference implementations demonstrating
the full capabilities of AI-powered APQC-compliant agents.

Examples:
    - IntelligentFinancialAnalyst: Financial analysis, risk assessment, forecasting
    - SmartRecruitmentAgent: Candidate screening, bias detection, interview prep
    - IntelligentCustomerRouter: Ticket classification, sentiment analysis, routing

Usage:
    from examples.ai_powered_agents import (
        IntelligentFinancialAnalyst,
        SmartRecruitmentAgent,
        IntelligentCustomerRouter
    )

    # Create and use agents
    analyst = IntelligentFinancialAnalyst()
    result = await analyst.analyze_portfolio(portfolio_data)

These examples showcase:
    - Integration with smart_processing domain processors
    - AI service abstraction for multi-provider support
    - APQC process compliance
    - Production-ready patterns and best practices
"""

from .intelligent_financial_analyst import (
    IntelligentFinancialAnalyst,
    FinancialAnalystConfig
)
from .smart_recruitment_agent import (
    SmartRecruitmentAgent,
    RecruitmentConfig
)
from .intelligent_customer_router import (
    IntelligentCustomerRouter,
    CustomerRouterConfig,
    Priority,
    Sentiment
)

__all__ = [
    "IntelligentFinancialAnalyst",
    "FinancialAnalystConfig",
    "SmartRecruitmentAgent",
    "RecruitmentConfig",
    "IntelligentCustomerRouter",
    "CustomerRouterConfig",
    "Priority",
    "Sentiment",
]
