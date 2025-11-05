"""
Test script for Agent Factory

Generates a single test agent to validate the factory works
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.agent_factory import AgentFactory


async def test_single_agent():
    """Test generating a single agent"""

    print("=" * 60)
    print("AGENT FACTORY TEST - Single Agent Generation")
    print("=" * 60)

    # Initialize factory
    factory = AgentFactory()

    # Load registry and get first agent
    registry = await factory._load_apqc_registry()

    print(f"\nRegistry loaded: {registry['total_agents']} agents available")

    # Get first agent from category 3.0 (Market and Sell)
    test_agent_spec = None
    for agent in registry.get("agents", []):
        if agent.get("metadata", {}).get("category_id") == "3.0":
            test_agent_spec = agent
            break

    if not test_agent_spec:
        print("ERROR: No agent found in category 3.0")
        return

    print(f"\nTest Agent Selected:")
    print(f"  ID: {test_agent_spec.get('agent_id')}")
    print(f"  Category: {test_agent_spec.get('metadata', {}).get('category_name')}")
    print(f"  Process: {test_agent_spec.get('metadata', {}).get('process_name')}")

    # Generate the agent
    print("\nStarting generation...\n")
    result = await factory.generate_agent(test_agent_spec)

    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    print(f"Status: {result['status']}")
    print(f"Files Created: {len(result['files_created'])}")
    for file_path in result['files_created']:
        print(f"  - {file_path}")

    if result['errors']:
        print(f"\nErrors:")
        for error in result['errors']:
            print(f"  - {error}")

    print("=" * 60)

    return result


async def test_batch_generation():
    """Test generating multiple agents in parallel"""

    print("\n\n" + "=" * 60)
    print("AGENT FACTORY TEST - Batch Generation (3 agents)")
    print("=" * 60)

    factory = AgentFactory()

    # Load registry
    registry = await factory._load_apqc_registry()

    # Get first 3 agents from category 3.0
    agent_ids = []
    for agent in registry.get("agents", []):
        if agent.get("metadata", {}).get("category_id") == "3.0":
            agent_ids.append(agent.get("agent_id"))
            if len(agent_ids) >= 3:
                break

    print(f"\nGenerating {len(agent_ids)} agents in parallel...")

    # Generate batch
    result = await factory.generate_batch(agent_ids)

    print("\n" + "=" * 60)
    print("BATCH RESULTS")
    print("=" * 60)
    print(f"Total: {result['total_agents']}")
    print(f"Completed: {result['completed']}")
    print(f"Failed: {result['failed']}")
    print(f"Success Rate: {(result['completed']/result['total_agents']*100 if result['total_agents'] > 0 else 0):.1f}%")
    print("=" * 60)

    return result


async def main():
    """Run all tests"""

    print("\n" + "=" * 70)
    print("AGENT FACTORY - Comprehensive Test Suite")
    print("=" * 70)

    # Check API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        print("\nANTHROPIC_API_KEY: Found")
        print("Mode: REAL CODE GENERATION")
    else:
        print("\nANTHROPIC_API_KEY: Not found")
        print("Mode: MOCK MODE (will generate placeholder code)")
        print("\nTo enable real generation:")
        print("  1. Set ANTHROPIC_API_KEY environment variable")
        print("  2. Re-run this test")

    input("\nPress Enter to continue with test...")

    # Test 1: Single agent generation
    single_result = await test_single_agent()

    # Test 2: Batch generation (if single succeeded)
    if single_result.get("status") == "completed":
        user_choice = input("\nSingle agent test passed! Run batch test (3 agents)? (y/n): ")
        if user_choice.lower() == 'y':
            await test_batch_generation()
        else:
            print("\nSkipping batch test.")
    else:
        print("\nSkipping batch test due to single agent test failure.")

    print("\n" + "=" * 70)
    print("TEST SUITE COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
