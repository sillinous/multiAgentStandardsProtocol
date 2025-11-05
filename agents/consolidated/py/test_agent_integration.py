#!/usr/bin/env python3
"""
Test Agent Integration
Verifies that market research agents are properly integrated into the API
"""

import asyncio
import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_agent_initialization():
    """Test that agents can be initialized"""
    print("🧪 Testing Agent Initialization...")

    try:
        from app.market_research_agents import initialize_market_research_agents, get_market_research_orchestrator
        from app.ai_service import market_ai
        from app.blockchain_agentic_protocol import BlockchainAgenticProtocol

        # Initialize blockchain protocol
        blockchain_protocol = BlockchainAgenticProtocol()
        print("  ✅ Blockchain protocol initialized")

        # Initialize agents
        orchestrator = await initialize_market_research_agents(market_ai, blockchain_protocol)
        print(f"  ✅ Agent orchestrator initialized: {orchestrator is not None}")

        # Get orchestrator
        retrieved_orchestrator = await get_market_research_orchestrator()
        print(f"  ✅ Can retrieve orchestrator: {retrieved_orchestrator is not None}")

        # Check agent status
        if orchestrator:
            status = orchestrator.get_agent_status()
            print(f"  ✅ Agent status retrieved: {len(status)} agents")
            for agent_id, agent_info in status.items():
                print(f"     - {agent_id}: {agent_info.get('status', 'unknown')}")

        return True
    except Exception as e:
        print(f"  ❌ Agent initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_agent_analysis():
    """Test that agents can perform analysis"""
    print("\n🧪 Testing Agent Analysis...")

    try:
        from app.market_research_agents import get_market_research_orchestrator

        orchestrator = await get_market_research_orchestrator()
        if not orchestrator:
            print("  ⚠️  Orchestrator not available (needs initialization first)")
            return False

        # Test market opportunity analysis
        market_data = {
            "search_terms": ["smart home devices"],
            "analysis_type": "basic",
            "keywords": ["smart home"],
            "user_id": "test_user",
            "timestamp": 1234567890
        }

        print("  📊 Running market opportunity analysis...")
        result = await orchestrator.analyze_market_opportunity(market_data)

        print(f"  ✅ Analysis completed!")
        print(f"     - Analysis ID: {result.get('analysis_id', 'N/A')}")
        print(f"     - Insights: {len(result.get('insights', []))}")
        print(f"     - Opportunities: {len(result.get('opportunities', []))}")

        return True
    except Exception as e:
        print(f"  ❌ Agent analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_learning_integration():
    """Test that learning framework is available"""
    print("\n🧪 Testing Learning Framework Integration...")

    try:
        from app.agent_learning_integration import (
            enable_agent_learning,
            get_learning_ecosystem_stats,
            LearningAgentWrapper
        )

        print("  ✅ Learning framework imports successful")

        # Try to get ecosystem stats (may be empty if no agents registered)
        stats = get_learning_ecosystem_stats()
        print(f"  ✅ Learning ecosystem stats retrieved")
        print(f"     - Learning agents: {stats.get('total_learning_agents', 0)}")

        return True
    except Exception as e:
        print(f"  ❌ Learning framework test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("=" * 60)
    print("🚀 Agent Integration Test Suite")
    print("=" * 60)

    results = []

    # Test 1: Agent Initialization
    results.append(await test_agent_initialization())

    # Test 2: Agent Analysis
    results.append(await test_agent_analysis())

    # Test 3: Learning Integration
    results.append(await test_learning_integration())

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Tests Passed: {passed}/{total}")

    if passed == total:
        print("✅ All tests passed! Agent integration is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the output above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
