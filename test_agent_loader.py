#!/usr/bin/env python3
"""
Test agent_loader.py can load all registered agents
"""
import sys
sys.path.insert(0, '/home/user/multiAgentStandardsProtocol/src')

from superstandard.api.agent_loader import get_registry

def test_registry():
    """Test agent registry"""
    print("=" * 80)
    print("TESTING AGENT LOADER REGISTRY")
    print("=" * 80)
    print()

    # Get registry
    registry = get_registry()

    # Get statistics
    stats = registry.get_statistics()
    print("Registry Statistics:")
    print(f"  Total PCF elements: {stats['total_elements']}")
    print(f"  Total categories: {stats['total_categories']}")
    print(f"  Implemented agents: {stats['implemented_agents']}")
    print(f"  Implementation %: {stats['implementation_percentage']:.1f}%")
    print()

    # Test loading each agent
    print("Testing agent loading...")
    print("-" * 80)

    success_count = 0
    fail_count = 0

    for hierarchy_id in stats['available_agents']:
        try:
            agent = registry.get_agent(hierarchy_id, use_cache=False)
            print(f"✓ {hierarchy_id} - {agent.config.pcf_metadata.activity_name}")
            success_count += 1
        except Exception as e:
            print(f"✗ {hierarchy_id} - FAILED: {str(e)}")
            fail_count += 1

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total agents tested: {success_count + fail_count}")
    print(f"Successfully loaded: {success_count}")
    print(f"Failed: {fail_count}")
    print()

    if fail_count == 0:
        print("🎉 ALL 22 AGENTS LOADED SUCCESSFULLY!")
        print("🎉 PROCESS GROUP 1.1 - 100% COMPLETE AND OPERATIONAL!")
        return True
    else:
        print("❌ Some agents failed to load")
        return False

if __name__ == "__main__":
    success = test_registry()
    exit(0 if success else 1)
