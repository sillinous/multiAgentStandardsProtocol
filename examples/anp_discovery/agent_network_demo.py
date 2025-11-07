"""
SuperStandard ANP (Agent Network Protocol) Demo

This example demonstrates:
1. Agent registration in a network registry
2. Capability-based agent discovery
3. Health monitoring with heartbeats
4. Network topology inspection

Usage:
    python examples/anp_discovery/agent_network_demo.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.superstandard.protocols.anp_implementation import (
    AgentNetworkRegistry,
    ANPRegistration,
    DiscoveryQuery,
    AgentStatus,
)


async def main():
    print("\n" + "=" * 60)
    print("SuperStandard ANP v1.0 - Agent Network Discovery Demo")
    print("=" * 60 + "\n")

    # Create network registry
    registry = AgentNetworkRegistry(heartbeat_timeout=30)
    print("[*] Created Agent Network Registry (30s heartbeat timeout)\n")

    # Step 1: Register multiple agents with different capabilities
    print("Step 1: Registering agents with various capabilities")
    print("-" * 60)

    agents = [
        {
            "agent_id": "data-collector-1",
            "name": "Data Collector Alpha",
            "agent_type": "collector",
            "capabilities": ["api_fetch", "web_scraping", "data_extraction"],
            "endpoint": "http://localhost:8001",
            "region": "us-east",
        },
        {
            "agent_id": "data-analyzer-1",
            "name": "Analyzer Prime",
            "agent_type": "analyzer",
            "capabilities": ["data_analysis", "reporting", "visualization"],
            "endpoint": "http://localhost:8002",
            "region": "us-east",
        },
        {
            "agent_id": "data-analyzer-2",
            "name": "Analyzer Beta",
            "agent_type": "analyzer",
            "capabilities": ["data_analysis", "machine_learning", "prediction"],
            "endpoint": "http://localhost:8003",
            "region": "eu-west",
        },
        {
            "agent_id": "report-generator-1",
            "name": "Report Generator",
            "agent_type": "generator",
            "capabilities": ["reporting", "pdf_generation", "email_delivery"],
            "endpoint": "http://localhost:8004",
            "region": "us-west",
        },
        {
            "agent_id": "orchestrator-1",
            "name": "Master Orchestrator",
            "agent_type": "orchestrator",
            "capabilities": ["task_coordination", "workflow_management"],
            "endpoint": "http://localhost:8005",
            "region": "us-east",
        },
    ]

    for agent_data in agents:
        registration = ANPRegistration(
            agent_id=agent_data["agent_id"],
            name=agent_data["name"],
            agent_type=agent_data["agent_type"],
            capabilities=agent_data["capabilities"],
            endpoint=agent_data["endpoint"],
            region=agent_data.get("region"),
        )
        result = await registry.register_agent(registration)
        print(f"[+] Registered: {agent_data['name']}")
        print(f"    ID: {result['agent_id']}")
        print(f"    Capabilities: {', '.join(agent_data['capabilities'])}")
        print(f"    Status: {result['status']}")
        print()

    # Step 2: Discover agents by capability
    print("\nStep 2: Discovering agents by capability")
    print("-" * 60)

    # Find all data analysis agents
    print("[*] Searching for agents with 'data_analysis' capability...")
    query = DiscoveryQuery(capabilities=["data_analysis"])
    result = await registry.discover_agents(query)
    print(f"[+] Found {len(result['agents'])} agents:")
    for agent in result["agents"]:
        print(f"    - {agent['name']} ({agent['agent_id']})")
        print(f"      Endpoint: {agent['endpoint']}")
        print(f"      Region: {agent.get('region', 'N/A')}")
        print(f"      All capabilities: {', '.join(agent['capabilities'])}")
        print()

    # Find reporting agents
    print("[*] Searching for agents with 'reporting' capability...")
    query = DiscoveryQuery(capabilities=["reporting"])
    result = await registry.discover_agents(query)
    print(f"[+] Found {len(result['agents'])} agents:")
    for agent in result["agents"]:
        print(f"    - {agent['name']} ({agent['agent_id']})")
        print(f"      Capabilities: {', '.join(agent['capabilities'])}")
        print()

    # Step 3: Filter by agent type
    print("\nStep 3: Discovering agents by type")
    print("-" * 60)

    print("[*] Searching for all 'analyzer' type agents...")
    query = DiscoveryQuery(agent_type="analyzer")
    result = await registry.discover_agents(query)
    print(f"[+] Found {len(result['agents'])} analyzer agents:")
    for agent in result["agents"]:
        print(f"    - {agent['name']} ({agent['agent_id']})")
        print(f"      Region: {agent.get('region', 'N/A')}")
        print()

    # Step 4: Filter by region
    print("\nStep 4: Discovering agents by region")
    print("-" * 60)

    print("[*] Searching for agents in 'us-east' region...")
    query = DiscoveryQuery(region="us-east")
    result = await registry.discover_agents(query)
    print(f"[+] Found {len(result['agents'])} agents in us-east:")
    for agent in result["agents"]:
        print(f"    - {agent['name']} ({agent['agent_type']})")
        print(f"      Capabilities: {', '.join(agent['capabilities'])}")
        print()

    # Step 5: Combined query
    print("\nStep 5: Complex discovery query")
    print("-" * 60)

    print("[*] Searching for 'analyzer' type with 'machine_learning' in 'eu-west'...")
    query = DiscoveryQuery(
        agent_type="analyzer", capabilities=["machine_learning"], region="eu-west"
    )
    result = await registry.discover_agents(query)
    print(f"[+] Found {len(result['agents'])} matching agents:")
    for agent in result["agents"]:
        print(f"    - {agent['name']}")
        print(f"      ID: {agent['agent_id']}")
        print(f"      All capabilities: {', '.join(agent['capabilities'])}")
        print()

    # Step 6: Health monitoring with heartbeats
    print("\nStep 6: Health monitoring")
    print("-" * 60)

    print("[*] Sending heartbeats from agents...")
    # Simulate healthy agent
    result = await registry.heartbeat("data-collector-1", AgentStatus.HEALTHY, load_score=0.3)
    print(f"[+] data-collector-1: {result['status']} (load: {result['current_load']})")

    # Simulate degraded agent
    result = await registry.heartbeat("data-analyzer-1", AgentStatus.DEGRADED, load_score=0.85)
    print(f"[+] data-analyzer-1: {result['status']} (load: {result['current_load']})")

    # Check agent status
    print("\n[*] Checking agent status after heartbeats...")
    query = DiscoveryQuery(capabilities=["data_analysis"])
    result = await registry.discover_agents(query)
    for agent in result["agents"]:
        print(f"    - {agent['name']}: {agent['status']} (load: {agent['load_score']:.2f})")

    # Step 7: Network topology
    print("\nStep 7: Network Topology")
    print("-" * 60)

    topology = await registry.get_network_topology()
    print(f"[*] Network Statistics:")
    print(f"    Total agents: {topology.total_agents}")
    print(f"    Online agents: {topology.online_agents}")
    print(f"    Offline agents: {topology.offline_agents}")
    print(f"    Average load: {topology.average_load:.2f}")
    print()

    print(f"[*] Agents by Type:")
    for agent_type, count in topology.agents_by_type.items():
        print(f"    {agent_type}: {count}")
    print()

    print(f"[*] Agents by Region:")
    for region, count in topology.agents_by_region.items():
        print(f"    {region}: {count}")
    print()

    print(f"[*] Top Capabilities:")
    for capability, count in sorted(
        topology.capabilities.items(), key=lambda x: x[1], reverse=True
    )[:5]:
        print(f"    {capability}: {count} agents")

    # Step 8: Deregister an agent
    print("\nStep 8: Agent deregistration")
    print("-" * 60)

    print("[*] Deregistering 'report-generator-1'...")
    result = await registry.deregister_agent("report-generator-1")
    print(f"[+] Deregistration result: {result}")

    # Check updated topology
    topology = await registry.get_network_topology()
    print(f"\n[*] Updated Network Statistics:")
    print(f"    Total agents: {topology.total_agents}")
    print(f"    Online agents: {topology.online_agents}")

    print("\n" + "=" * 60)
    print("Demo completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
