"""
APQC Agent Testing Framework

Comprehensive testing infrastructure for 118 APQC agents implementing
the APQC Process Classification Framework v7.0.1 across 13 categories.

Test Organization:
- test_apqc_framework.py: Base testing framework and utilities
- conftest.py: Pytest fixtures and configuration
- test_apqc_category_1_vision_strategy.py: Category 1.0 tests (22 agents)
- test_apqc_category_2_products_services.py: Category 2.0 tests (4 agents)
- test_apqc_category_3_market_sell.py: Category 3.0 tests (13 agents)
- test_apqc_categories_4_13_template.py: Template for remaining categories (79 agents)

Usage:
    # Run all APQC tests
    pytest tests/apqc/ -v

    # Run specific category
    pytest tests/apqc/ -m apqc_category_1 -v

    # Run integration tests
    pytest tests/apqc/ -m apqc_integration -v

    # Run with coverage
    pytest tests/apqc/ --cov=src/superstandard/agents --cov-report=html

Version: 1.0.0
Framework: APQC 7.0.1
"""

from .test_apqc_framework import (
    APQCAgentTestCase,
    MockDataGenerator,
    APQCTestUtilities
)

__all__ = [
    'APQCAgentTestCase',
    'MockDataGenerator',
    'APQCTestUtilities'
]

__version__ = '1.0.0'
__apqc_framework_version__ = '7.0.1'
