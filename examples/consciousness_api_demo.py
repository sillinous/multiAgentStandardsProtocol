"""
Consciousness API Demo - Full End-to-End Example

This demo shows how to use the Consciousness API to:
1. Create a collective consciousness via REST API
2. Register agents using API endpoints
3. Contribute thoughts through HTTP POST
4. Trigger consciousness collapses
5. Monitor real-time events via WebSocket

Prerequisites:
    pip install fastapi uvicorn websockets aiohttp

Usage:
    # Terminal 1: Start API server
    python -m uvicorn superstandard.api.consciousness_api:app --reload --port 8000

    # Terminal 2: Run this demo
    python examples/consciousness_api_demo.py

    # Browser: Open dashboard
    http://localhost:8000/dashboard

This demonstrates the complete API workflow!
"""

import asyncio
import aiohttp
import json
from datetime import datetime


API_BASE = "http://localhost:8000"
WS_BASE = "ws://localhost:8000"


async def demo_rest_api():
    """Demonstrate REST API endpoints."""
    print("=" * 80)
    print("CONSCIOUSNESS API DEMO - REST Endpoints")
    print("=" * 80)
    print()

    async with aiohttp.ClientSession() as session:
        # 1. Check API status
        print("1. Checking API status...")
        async with session.get(f"{API_BASE}/") as resp:
            data = await resp.json()
            print(f"   Service: {data['service']}")
            print(f"   Version: {data['version']}")
            print(f"   Status: {data['status']}")
            print()

        # 2. Create collective consciousness
        print("2. Creating collective consciousness...")
        collective_data = {
            "consciousness_id": "api_demo_collective",
            "persistent": False,
            "auto_save": False
        }
        async with session.post(f"{API_BASE}/api/consciousness/", json=collective_data) as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"   Created: {data['consciousness_id']}")
                print(f"   Status: {data['status']}")
            else:
                print(f"   Error: {resp.status}")
                return
        print()

        # 3. Register agents
        print("3. Registering 3 agents...")
        agents = [
            {"agent_id": "analyst_001", "initial_state": "awakening"},
            {"agent_id": "strategist_001", "initial_state": "awakening"},
            {"agent_id": "optimizer_001", "initial_state": "awakening"}
        ]

        for agent in agents:
            async with session.post(
                f"{API_BASE}/api/consciousness/api_demo_collective/agents",
                json=agent
            ) as resp:
                data = await resp.json()
                print(f"   {data['agent_id']}: {data['state']}")

        print()

        # 4. Get collective state
        print("4. Getting collective state...")
        async with session.get(f"{API_BASE}/api/consciousness/api_demo_collective") as resp:
            state = await resp.json()
            print(f"   Total Agents: {state['total_agents']}")
            print(f"   Collective Awareness: {state['collective_awareness']:.0%}")
        print()

        # 5. Contribute thoughts
        print("5. Contributing thoughts from agents...")
        thoughts = [
            {
                "agent_id": "analyst_001",
                "thought_type": "observation",
                "content": "Market shows 23% volatility in Q4",
                "confidence": 0.92
            },
            {
                "agent_id": "strategist_001",
                "thought_type": "question",
                "content": "What are the key risk factors?",
                "confidence": 0.75
            },
            {
                "agent_id": "optimizer_001",
                "thought_type": "insight",
                "content": "Portfolio rebalancing can reduce risk by 35%",
                "confidence": 0.88,
                "emotional_valence": 0.6
            },
            {
                "agent_id": "analyst_001",
                "thought_type": "inference",
                "content": "Volatility correlates with sector concentration",
                "confidence": 0.85
            },
            {
                "agent_id": "strategist_001",
                "thought_type": "intention",
                "content": "Should diversify across 5 key sectors",
                "confidence": 0.80
            }
        ]

        for thought in thoughts:
            async with session.post(
                f"{API_BASE}/api/consciousness/api_demo_collective/thoughts",
                json=thought
            ) as resp:
                data = await resp.json()
                print(f"   {data['agent_id']}: {data['thought_type']} "
                      f"({data['entangled_with']} entanglements)")

        print()

        # 6. Get updated metrics
        print("6. Getting consciousness metrics...")
        async with session.get(f"{API_BASE}/api/consciousness/api_demo_collective/metrics") as resp:
            metrics = await resp.json()
            m = metrics['metrics']
            print(f"   Total Thoughts: {m['total_thoughts']}")
            print(f"   In Superposition: {m['thoughts_in_superposition']}")
            print(f"   Entanglement Density: {m['entanglement_density']:.2f}")
            print(f"   Collective Awareness: {m['collective_awareness']:.0%}")
        print()

        # 7. Trigger consciousness collapse
        print("7. Triggering consciousness collapse...")
        collapse_data = {
            "query": "How can we optimize portfolio risk?",
            "min_coherence": 0.4
        }
        async with session.post(
            f"{API_BASE}/api/consciousness/api_demo_collective/collapse",
            json=collapse_data
        ) as resp:
            data = await resp.json()
            print(f"   Query: {data['query']}")
            print(f"   Patterns Discovered: {data['patterns_discovered']}")
            print()

            if data['patterns_discovered'] > 0:
                print("   Emergent Patterns:")
                for i, pattern in enumerate(data['patterns'], 1):
                    print(f"   {i}. {pattern['pattern_type'].upper()}")
                    print(f"      Coherence: {pattern['coherence_score']:.0%}")
                    print(f"      Novelty: {pattern['novelty_score']:.0%}")
                    print(f"      Impact: {pattern['impact_potential']:.0%}")
                    print(f"      Agents: {', '.join(pattern['contributing_agents'])}")
                    print()

        # 8. Check health
        print("8. Checking consciousness health...")
        async with session.get(f"{API_BASE}/api/consciousness/api_demo_collective/health") as resp:
            health = await resp.json()
            print(f"   Health Status: {health['health'].upper()}")
            if health['issues']:
                print(f"   Issues: {', '.join(health['issues'])}")
            else:
                print("   No issues detected")
        print()

        # 9. List all collectives
        print("9. Listing all collectives...")
        async with session.get(f"{API_BASE}/api/consciousness/") as resp:
            data = await resp.json()
            print(f"   Total Collectives: {len(data['collectives'])}")
            for collective in data['collectives']:
                print(f"   - {collective['consciousness_id']}: "
                      f"{collective['total_agents']} agents, "
                      f"{collective['emergent_patterns']} patterns")
        print()


async def demo_websocket():
    """Demonstrate WebSocket real-time event stream."""
    print("=" * 80)
    print("CONSCIOUSNESS API DEMO - WebSocket Real-Time Stream")
    print("=" * 80)
    print()

    import websockets

    print("Connecting to WebSocket stream...")
    print("(This will show real-time events for 10 seconds)")
    print()

    try:
        async with websockets.connect(f"{WS_BASE}/api/consciousness/api_demo_collective/stream") as websocket:
            print("Connected! Listening for events...")
            print("-" * 80)

            # Listen for 10 seconds
            try:
                async with asyncio.timeout(10):
                    async for message in websocket:
                        data = json.loads(message)
                        event_type = data.get('event_type', 'unknown')
                        timestamp = datetime.now().strftime("%H:%M:%S")

                        if event_type == 'connected':
                            print(f"[{timestamp}] CONNECTED to collective")
                            state = data.get('data', {})
                            print(f"            Initial state: {state.get('total_agents', 0)} agents, "
                                  f"{state.get('total_thoughts', 0)} thoughts")
                        elif event_type == 'agent_registered':
                            event_data = data.get('data', {})
                            print(f"[{timestamp}] AGENT REGISTERED: {event_data.get('agent_id')} "
                                  f"({event_data.get('state')})")
                        elif event_type == 'thought_contributed':
                            event_data = data.get('data', {})
                            print(f"[{timestamp}] THOUGHT: {event_data.get('agent_id')} -> "
                                  f"{event_data.get('thought_type')}")
                        elif event_type == 'consciousness_collapsed':
                            event_data = data.get('data', {})
                            print(f"[{timestamp}] COLLAPSE: {event_data.get('patterns_discovered')} "
                                  f"patterns discovered")
                        elif event_type == 'pattern_discovered':
                            event_data = data.get('data', {})
                            print(f"[{timestamp}] PATTERN: {event_data.get('pattern_type')} "
                                  f"(coherence: {event_data.get('coherence', 0):.0%})")
                        else:
                            print(f"[{timestamp}] {event_type}: {data.get('data', {})}")

            except asyncio.TimeoutError:
                print("-" * 80)
                print("Demo timeout - 10 seconds elapsed")

    except Exception as e:
        print(f"WebSocket error: {e}")
        print("Make sure the API server is running!")

    print()


async def cleanup():
    """Cleanup demo collective."""
    print("Cleaning up...")
    async with aiohttp.ClientSession() as session:
        async with session.delete(f"{API_BASE}/api/consciousness/api_demo_collective") as resp:
            if resp.status == 200:
                print("Demo collective deleted")


async def main():
    """Run complete demo."""
    print()
    print("*" * 80)
    print("CONSCIOUSNESS API - COMPLETE DEMONSTRATION")
    print("*" * 80)
    print()
    print("This demo demonstrates:")
    print("1. REST API for consciousness management")
    print("2. Agent registration and thought contribution")
    print("3. Consciousness collapse and pattern discovery")
    print("4. Real-time WebSocket event streaming")
    print()
    print("Make sure the API server is running:")
    print("  python -m uvicorn superstandard.api.consciousness_api:app --port 8000")
    print()
    print("Also open the dashboard in your browser:")
    print("  http://localhost:8000/dashboard")
    print()
    input("Press Enter to continue...")
    print()

    try:
        # Run REST API demo
        await demo_rest_api()

        # Run WebSocket demo
        print("Now demonstrating real-time WebSocket events...")
        print("(Any future events in the collective will appear here)")
        print()
        await demo_websocket()

    except aiohttp.ClientConnectorError:
        print()
        print("=" * 80)
        print("ERROR: Cannot connect to API server!")
        print("=" * 80)
        print()
        print("Please start the API server first:")
        print("  python -m uvicorn superstandard.api.consciousness_api:app --port 8000")
        print()
        return
    except Exception as e:
        print(f"Demo error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await cleanup()

    print()
    print("=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)
    print()
    print("Next steps:")
    print("1. Open dashboard: http://localhost:8000/dashboard")
    print("2. Explore API docs: http://localhost:8000/docs")
    print("3. Try the API interactively!")
    print()


if __name__ == "__main__":
    asyncio.run(main())
