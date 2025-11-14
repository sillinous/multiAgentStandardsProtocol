#!/usr/bin/env python3
"""
Natural Language Interface Demo

Demonstrates the revolutionary natural language interface for invoking
autonomous agents using plain English.

This demo shows:
1. Intent classification from natural language
2. Automatic parameter extraction
3. Agent selection and execution
4. Natural language response generation

Usage:
    python examples/natural_language_demo.py
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.superstandard.cli.chat import NaturalLanguageChatInterface

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(message)s'
)


async def demo_single_queries():
    """Demo mode: Run several example queries to showcase capabilities."""
    print("\n" + "=" * 80)
    print("🎯 NATURAL LANGUAGE INTERFACE DEMO")
    print("=" * 80)
    print("\nThis demo shows how you can talk to autonomous agents in plain English!")
    print()

    chat = NaturalLanguageChatInterface(use_llm=False)

    # Example queries to demonstrate
    example_queries = [
        {
            "query": "Find me business opportunities in technology",
            "description": "Opportunity Discovery in Tech Sector"
        },
        {
            "query": "Show me economic trends",
            "description": "Economic Trends Analysis"
        },
        {
            "query": "What's the system status?",
            "description": "System Health Check"
        },
        {
            "query": "help",
            "description": "Get Available Commands"
        }
    ]

    for i, example in enumerate(example_queries, 1):
        print(f"\n{'='*80}")
        print(f"Example {i}/{len(example_queries)}: {example['description']}")
        print(f"{'='*80}")
        print(f"\n💬 User Query: \"{example['query']}\"")
        print()

        try:
            response = await chat.process_query(example['query'])

            print("\n🤖 Agent Response:")
            print("-" * 80)
            print(response)
            print("-" * 80)

        except Exception as e:
            print(f"\n❌ Error: {e}")

        if i < len(example_queries):
            print("\n⏸️  Press Enter to continue to next example...")
            input()

    print("\n" + "=" * 80)
    print("✅ Demo Complete!")
    print("=" * 80)
    print("\nTo try it interactively:")
    print("  python src/superstandard/cli/chat.py")
    print()


async def demo_interactive():
    """Run interactive demo mode."""
    print("\n" + "=" * 80)
    print("🎯 INTERACTIVE NATURAL LANGUAGE INTERFACE")
    print("=" * 80)
    print()

    chat = NaturalLanguageChatInterface(use_llm=False)
    await chat.run_interactive()


async def demo_advanced_queries():
    """Demo advanced query capabilities."""
    print("\n" + "=" * 80)
    print("🚀 ADVANCED NATURAL LANGUAGE QUERIES DEMO")
    print("=" * 80)
    print("\nThis demo shows advanced parameter extraction from natural language")
    print()

    chat = NaturalLanguageChatInterface(use_llm=False)

    advanced_queries = [
        {
            "query": "Find me SaaS opportunities in healthcare with at least 80% confidence",
            "description": "Complex Opportunity Query with Filters"
        },
        {
            "query": "Analyze competitors for openai.com",
            "description": "Competitor Analysis with Domain"
        },
        {
            "query": "Show me demographics for California",
            "description": "Demographics with Geographic Filter"
        }
    ]

    for i, example in enumerate(advanced_queries, 1):
        print(f"\n{'='*80}")
        print(f"Advanced Example {i}/{len(advanced_queries)}: {example['description']}")
        print(f"{'='*80}")
        print(f"\n💬 User Query: \"{example['query']}\"")
        print()

        try:
            response = await chat.process_query(example['query'])

            print("\n🤖 Agent Response:")
            print("-" * 80)
            print(response)
            print("-" * 80)

        except Exception as e:
            print(f"\n❌ Error: {e}")

        if i < len(advanced_queries):
            print("\n⏸️  Press Enter to continue...")
            input()

    print("\n" + "=" * 80)
    print("✅ Advanced Demo Complete!")
    print("=" * 80)
    print()


async def main():
    """Main entry point."""
    print("\n🤖 Natural Language Interface Demo\n")
    print("Select demo mode:")
    print("1. Simple Examples (4 basic queries)")
    print("2. Advanced Examples (complex parameter extraction)")
    print("3. Interactive Mode (try your own queries)")
    print()

    try:
        choice = input("Enter choice (1-3, default=1): ").strip() or "1"

        if choice == "1":
            await demo_single_queries()
        elif choice == "2":
            await demo_advanced_queries()
        elif choice == "3":
            await demo_interactive()
        else:
            print("Invalid choice. Running simple examples...")
            await demo_single_queries()

    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
