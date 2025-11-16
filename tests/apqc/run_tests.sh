#!/bin/bash
# APQC Agent Test Runner
#
# This script provides convenient commands for running APQC agent tests
# with various options and filters.
#
# Usage: ./run_tests.sh [option]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print header
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  APQC Agent Testing Framework${NC}"
    echo -e "${BLUE}  Framework: APQC 7.0.1${NC}"
    echo -e "${BLUE}  Agents: 118 (39 tested, 79 template)${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

# Print usage
print_usage() {
    echo "Usage: ./run_tests.sh [option]"
    echo ""
    echo "Options:"
    echo "  all              Run all APQC tests"
    echo "  cat1             Run Category 1 tests (Vision & Strategy - 22 agents)"
    echo "  cat2             Run Category 2 tests (Products & Services - 4 agents)"
    echo "  cat3             Run Category 3 tests (Market & Sell - 13 agents)"
    echo "  integration      Run integration tests only"
    echo "  coverage         Run with coverage report"
    echo "  fast             Run fast tests only (exclude slow tests)"
    echo "  parallel         Run tests in parallel"
    echo "  verbose          Run with verbose output"
    echo "  help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./run_tests.sh all"
    echo "  ./run_tests.sh cat1"
    echo "  ./run_tests.sh coverage"
}

# Change to tests/apqc directory
cd "$(dirname "$0")"

print_header

case "${1:-all}" in
    all)
        echo -e "${GREEN}Running all APQC tests...${NC}"
        pytest . -v
        ;;

    cat1)
        echo -e "${GREEN}Running Category 1 tests (Vision & Strategy)...${NC}"
        pytest . -v -m apqc_category_1
        ;;

    cat2)
        echo -e "${GREEN}Running Category 2 tests (Products & Services)...${NC}"
        pytest . -v -m apqc_category_2
        ;;

    cat3)
        echo -e "${GREEN}Running Category 3 tests (Market & Sell)...${NC}"
        pytest . -v -m apqc_category_3
        ;;

    integration)
        echo -e "${GREEN}Running integration tests...${NC}"
        pytest . -v -m apqc_integration
        ;;

    coverage)
        echo -e "${GREEN}Running tests with coverage report...${NC}"
        pytest . -v --cov=../../src/superstandard/agents --cov-report=html --cov-report=term
        echo ""
        echo -e "${YELLOW}Coverage report generated in htmlcov/index.html${NC}"
        ;;

    fast)
        echo -e "${GREEN}Running fast tests only...${NC}"
        pytest . -v -m "not slow"
        ;;

    parallel)
        echo -e "${GREEN}Running tests in parallel...${NC}"
        if command -v pytest-xdist &> /dev/null; then
            pytest . -v -n auto
        else
            echo -e "${RED}pytest-xdist not installed. Install with: pip install pytest-xdist${NC}"
            exit 1
        fi
        ;;

    verbose)
        echo -e "${GREEN}Running tests with verbose output...${NC}"
        pytest . -vv --tb=long --showlocals
        ;;

    help|--help|-h)
        print_usage
        ;;

    *)
        echo -e "${RED}Unknown option: $1${NC}"
        echo ""
        print_usage
        exit 1
        ;;
esac

# Print summary
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Test run complete!${NC}"
echo -e "${BLUE}========================================${NC}"
