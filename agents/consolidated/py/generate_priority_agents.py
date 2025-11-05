"""
Generate Priority Agents Script

Generates the 10 highest-priority agents for the market research platform
in parallel using the Agent Factory.

Usage:
    python generate_priority_agents.py [count]

Examples:
    python generate_priority_agents.py         # Generate default 10 agents
    python generate_priority_agents.py 5       # Generate 5 agents
    python generate_priority_agents.py 20      # Generate 20 agents
"""

import asyncio
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.agent_factory import AgentFactory


async def generate_priority_agents(count: int = 10):
    """
    Generate priority agents

    Args:
        count: Number of agents to generate
    """

    print("=" * 80)
    print(f"PRIORITY AGENT GENERATION - {count} Agents")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Check API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("WARNING: ANTHROPIC_API_KEY not found!")
        print("Generation will run in MOCK MODE (placeholder code only)")
        print()
        print("To enable real code generation:")
        print("  1. Set ANTHROPIC_API_KEY environment variable")
        print("  2. Re-run this script")
        print()
        choice = input("Continue in mock mode? (y/n): ")
        if choice.lower() != 'y':
            print("Aborted.")
            return
        print()
    else:
        print("ANTHROPIC_API_KEY: Found")
        print("Mode: REAL CODE GENERATION with Claude API")
        print()

    # Initialize Agent Factory
    print("Initializing Agent Factory...")
    factory = AgentFactory()
    print()

    # Start generation
    start_time = datetime.now()

    print(f"Launching parallel generation of {count} agents...")
    print("This may take 5-10 minutes depending on API response times...")
    print()

    result = await factory.generate_priority_agents(count=count)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # Display results
    print()
    print("=" * 80)
    print("GENERATION COMPLETE")
    print("=" * 80)
    print(f"Total Agents: {result['total_agents']}")
    print(f"Completed: {result['completed']}")
    print(f"Failed: {result['failed']}")
    print(f"Success Rate: {(result['completed']/result['total_agents']*100 if result['total_agents'] > 0 else 0):.1f}%")
    print(f"Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
    print(f"Avg Time per Agent: {duration/result['total_agents']:.1f} seconds")
    print()

    # Show successful generations
    if result['completed'] > 0:
        print("Successfully Generated Agents:")
        for agent_result in result['results']:
            if agent_result.get('status') == 'completed':
                print(f"  - {agent_result.get('agent_id')}")
                for file_path in agent_result.get('files_created', []):
                    print(f"      {file_path}")
        print()

    # Show failures
    if result['failed'] > 0:
        print("Failed Generations:")
        for agent_result in result['results']:
            if agent_result.get('status') != 'completed':
                print(f"  - {agent_result.get('agent_id', 'unknown')}: {agent_result.get('errors', ['Unknown error'])[0] if agent_result.get('errors') else 'Unknown error'}")
        print()

    print("=" * 80)
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # Next steps
    print()
    print("Next Steps:")
    print("  1. Review generated agents in autonomous-ecosystem/library/")
    print("  2. Run tests: pytest autonomous-ecosystem/workspace/tests/generated_agents/")
    print("  3. Integrate with orchestrator")
    print("  4. Deploy to production")
    print()

    return result


async def generate_by_category(category_id: str):
    """
    Generate all agents in a specific category

    Args:
        category_id: APQC category ID (e.g., "3.0")
    """

    print("=" * 80)
    print(f"CATEGORY AGENT GENERATION - Category {category_id}")
    print("=" * 80)
    print()

    factory = AgentFactory()

    start_time = datetime.now()

    result = await factory.generate_category_agents(category_id)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print()
    print("=" * 80)
    print("GENERATION COMPLETE")
    print("=" * 80)
    print(f"Total Agents: {result['total_agents']}")
    print(f"Completed: {result['completed']}")
    print(f"Failed: {result['failed']}")
    print(f"Duration: {duration:.1f} seconds")
    print("=" * 80)

    return result


def main():
    """Main entry point"""

    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1].startswith("--category="):
            # Category mode
            category_id = sys.argv[1].split("=")[1]
            asyncio.run(generate_by_category(category_id))
        else:
            # Count mode
            try:
                count = int(sys.argv[1])
                asyncio.run(generate_priority_agents(count))
            except ValueError:
                print(f"Error: Invalid count '{sys.argv[1]}'")
                print("Usage: python generate_priority_agents.py [count]")
                print("   or: python generate_priority_agents.py --category=3.0")
                sys.exit(1)
    else:
        # Default: 10 agents
        asyncio.run(generate_priority_agents(10))


if __name__ == "__main__":
    main()
