"""
SuperStandard v1.0 - AI Research Marketplace Demo

A complete demonstration of all 3 protocols working together:
- ANP: Agent discovery and networking
- ACP: Multi-agent task coordination
- BAP: Blockchain economy with NFTs and payments

This demo simulates a decentralized AI research marketplace where:
1. Specialized AI agents register their capabilities
2. A coordinator discovers and orchestrates agents
3. Agents collaborate on research tasks
4. Agents mint knowledge NFTs and trade them
5. Payments are processed via blockchain

Usage:
    python demos/ai_marketplace/marketplace_demo.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from decimal import Decimal

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.superstandard.protocols.anp_implementation import (
    AgentNetworkRegistry,
    ANPRegistration,
    DiscoveryQuery,
    AgentStatus,
)
from src.superstandard.protocols.acp_implementation import CoordinationManager
from agents.consolidated.py.blockchain_agentic_protocol import (
    BlockchainAgenticProtocol,
    AgentWallet,
    TokenType,
)


class AIAgent:
    """Base class for AI agents in the marketplace"""

    def __init__(self, agent_id: str, name: str, agent_type: str, capabilities: list):
        self.agent_id = agent_id
        self.name = name
        self.agent_type = agent_type
        self.capabilities = capabilities
        self.tasks_completed = 0
        self.knowledge_created = []

    async def execute_task(self, task_description: str, input_data: dict) -> dict:
        """Simulate AI agent performing a task"""
        await asyncio.sleep(0.5)  # Simulate processing
        self.tasks_completed += 1

        # Generate output based on agent type
        if self.agent_type == "data_collector":
            return {
                "status": "completed",
                "data_collected": f"Data for: {task_description}",
                "sources": ["Source A", "Source B", "Source C"],
                "record_count": 1500,
            }
        elif self.agent_type == "analyst":
            return {
                "status": "completed",
                "insights": [
                    f"Key insight 1 from {task_description}",
                    f"Key insight 2 from {task_description}",
                    f"Trend identified in {task_description}",
                ],
                "confidence": 0.92,
            }
        elif self.agent_type == "writer":
            return {
                "status": "completed",
                "report": f"Comprehensive report on {task_description}",
                "sections": ["Introduction", "Analysis", "Findings", "Conclusion"],
                "word_count": 2500,
            }
        elif self.agent_type == "validator":
            return {
                "status": "completed",
                "validation": "passed",
                "quality_score": 0.95,
                "recommendations": ["Excellent work", "Ready for publication"],
            }
        else:
            return {"status": "completed", "result": f"Processed: {task_description}"}


async def main():
    print("\n" + "=" * 80)
    print("SuperStandard v1.0 - AI Research Marketplace Demo")
    print("=" * 80)
    print("\nA complete demonstration of ANP + ACP + BAP protocols working together\n")

    # ========================================================================
    # PHASE 1: INITIALIZATION
    # ========================================================================
    print("[PHASE 1] Initializing Protocol Infrastructure")
    print("-" * 80)

    # Initialize protocols
    anp_registry = AgentNetworkRegistry(heartbeat_timeout=300)
    acp_manager = CoordinationManager()
    bap = BlockchainAgenticProtocol(config={})

    print("[+] ANP: Agent Network Registry initialized")
    print("[+] ACP: Coordination Manager initialized")
    print("[+] BAP: Blockchain Protocol initialized")
    print()

    # ========================================================================
    # PHASE 2: AGENT CREATION & REGISTRATION (ANP)
    # ========================================================================
    print("[PHASE 2] Creating & Registering AI Agents (ANP)")
    print("-" * 80)

    # Create AI agents
    agents = [
        AIAgent(
            "collector-01",
            "Data Collector Alpha",
            "data_collector",
            ["data_collection", "web_scraping", "api_integration"],
        ),
        AIAgent(
            "analyst-01",
            "AI Analyst Prime",
            "analyst",
            ["data_analysis", "pattern_recognition", "ml_inference"],
        ),
        AIAgent(
            "writer-01",
            "Report Writer Pro",
            "writer",
            ["report_generation", "content_creation", "summarization"],
        ),
        AIAgent(
            "validator-01",
            "Quality Validator",
            "validator",
            ["quality_assurance", "validation", "peer_review"],
        ),
        AIAgent(
            "coordinator-01",
            "Marketplace Coordinator",
            "coordinator",
            ["task_orchestration", "agent_management", "workflow_design"],
        ),
    ]

    # Register agents on network (ANP)
    for agent in agents:
        registration = ANPRegistration(
            agent_id=agent.agent_id,
            agent_type=agent.agent_type,
            capabilities=agent.capabilities,
            endpoints={"api": f"http://localhost:8000/{agent.agent_id}"},
        )
        result = await anp_registry.register_agent(registration)
        print(f"[+] Registered: {agent.name}")
        print(f"    ID: {agent.agent_id}")
        print(f"    Capabilities: {', '.join(agent.capabilities[:2])}...")
        print()

    # ========================================================================
    # PHASE 3: AGENT DISCOVERY (ANP)
    # ========================================================================
    print("[PHASE 3] Discovering Agents by Capability (ANP)")
    print("-" * 80)

    # Coordinator discovers data collectors
    print("[*] Coordinator searching for data collection agents...")
    query = DiscoveryQuery(capabilities=["data_collection"])
    discovery_result = await anp_registry.discover_agents(query)
    print(f"[+] Found {len(discovery_result['agents'])} data collector(s)")

    # Discover analysts
    print("[*] Coordinator searching for analysis agents...")
    query = DiscoveryQuery(capabilities=["data_analysis"])
    discovery_result = await anp_registry.discover_agents(query)
    print(f"[+] Found {len(discovery_result['agents'])} analyst(s)")

    # Discover writers
    print("[*] Coordinator searching for writing agents...")
    query = DiscoveryQuery(capabilities=["report_generation"])
    discovery_result = await anp_registry.discover_agents(query)
    print(f"[+] Found {len(discovery_result['agents'])} writer(s)")
    print()

    # ========================================================================
    # PHASE 4: CREATE BLOCKCHAIN WALLETS (BAP)
    # ========================================================================
    print("[PHASE 4] Creating Agent Wallets & Initial Funding (BAP)")
    print("-" * 80)

    # Create wallets for agents
    wallets_created = 0
    for agent in agents:
        wallet = AgentWallet(
            wallet_id=f"wallet-{agent.agent_id}",
            agent_id=agent.agent_id,
            public_key=f"pub_key_{agent.agent_id}",
            private_key_hash=f"hash_{agent.agent_id}",
            token_balances={
                TokenType.REPUTATION: Decimal("100.0"),
                TokenType.UTILITY: Decimal("1000.0"),
                TokenType.GOVERNANCE: Decimal("50.0"),
            },
        )
        await bap.wallet_manager.store_wallet(wallet)
        wallets_created += 1

    print(f"[+] Created {wallets_created} agent wallets")
    print(f"[+] Initial funding: 100 REPUTATION, 1000 UTILITY, 50 GOVERNANCE per agent")
    print()

    # ========================================================================
    # PHASE 5: COORDINATION SESSION (ACP)
    # ========================================================================
    print("[PHASE 5] Creating Research Coordination Session (ACP)")
    print("-" * 80)

    # Create coordination for research project
    coordination = await acp_manager.create_coordination(
        coordinator_id="coordinator-01",
        coordination_type="pipeline",
        goal="Conduct AI market research and generate comprehensive report",
        coordination_plan={
            "project": "AI Market Analysis Q4 2025",
            "client": "Tech Research Institute",
            "deadline": "2025-12-15",
        },
    )
    coord_id = coordination["coordination_id"]
    coord_details = coordination["coordination"]
    print(f"[+] Coordination session created: {coord_id}")
    print(f"    Type: {coord_details['coordination_type']}")
    print(f"    Goal: {coord_details['goal']}")
    print()

    # Agents join coordination
    print("[*] Agents joining coordination...")
    for agent in agents[:4]:  # Exclude coordinator
        result = await acp_manager.join_coordination(
            coordination_id=coord_id,
            agent_id=agent.agent_id,
            agent_type=agent.agent_type,
            capabilities=agent.capabilities,
            role="contributor",
        )
    print(f"[+] {len(agents)-1} agents joined the coordination")
    print()

    # ========================================================================
    # PHASE 6: TASK CREATION & ASSIGNMENT (ACP)
    # ========================================================================
    print("[PHASE 6] Creating & Assigning Research Tasks (ACP)")
    print("-" * 80)

    # Task 1: Data Collection
    task1 = await acp_manager.create_task(
        coordination_id=coord_id,
        task_type="data_collection",
        description="Collect AI market data from multiple sources",
        priority=1,
        input_data={"sources": ["market_reports", "competitor_analysis", "trends"]},
        dependencies=[],
    )
    await acp_manager.assign_task(coord_id, task1["task_id"], "collector-01")
    print(f"[+] Task 1 assigned: Data Collection -> collector-01")

    # Task 2: Data Analysis
    task2 = await acp_manager.create_task(
        coordination_id=coord_id,
        task_type="data_analysis",
        description="Analyze collected data and identify key insights",
        priority=2,
        input_data={"analysis_type": "market_trends"},
        dependencies=[task1["task_id"]],
    )
    await acp_manager.assign_task(coord_id, task2["task_id"], "analyst-01")
    print(f"[+] Task 2 assigned: Analysis -> analyst-01")

    # Task 3: Report Writing
    task3 = await acp_manager.create_task(
        coordination_id=coord_id,
        task_type="report_generation",
        description="Generate comprehensive market research report",
        priority=3,
        input_data={
            "format": "pdf",
            "sections": ["executive_summary", "findings", "recommendations"],
        },
        dependencies=[task2["task_id"]],
    )
    await acp_manager.assign_task(coord_id, task3["task_id"], "writer-01")
    print(f"[+] Task 3 assigned: Report Writing -> writer-01")

    # Task 4: Quality Validation
    task4 = await acp_manager.create_task(
        coordination_id=coord_id,
        task_type="quality_validation",
        description="Validate report quality and accuracy",
        priority=4,
        input_data={"quality_standards": ["accuracy", "completeness", "clarity"]},
        dependencies=[task3["task_id"]],
    )
    await acp_manager.assign_task(coord_id, task4["task_id"], "validator-01")
    print(f"[+] Task 4 assigned: Validation -> validator-01")
    print()

    # ========================================================================
    # PHASE 7: TASK EXECUTION (ACP + ANP)
    # ========================================================================
    print("[PHASE 7] Executing Research Pipeline")
    print("-" * 80)

    # Execute tasks in sequence
    tasks = [
        (task1, agents[0], "Data Collection"),
        (task2, agents[1], "Data Analysis"),
        (task3, agents[2], "Report Writing"),
        (task4, agents[3], "Quality Validation"),
    ]

    for task, agent, task_name in tasks:
        print(f"\n[*] {task_name} ({agent.name})...")

        # Extract task details
        task_details = task["task"]

        # Simulate agent executing task
        result = await agent.execute_task(
            task_details["description"], task_details.get("input_data", {})
        )

        # Update task status
        await acp_manager.update_task_status(
            coord_id, task["task_id"], "completed", output_data=result
        )

        print(f"    [+] Task completed!")
        print(f"    [+] Output: {list(result.keys())}")

        # Send heartbeat to ANP
        await anp_registry.heartbeat(agent.agent_id, AgentStatus.HEALTHY, 0.5)

    print()

    # ========================================================================
    # PHASE 8: MINT KNOWLEDGE NFTs (BAP)
    # ========================================================================
    print("[PHASE 8] Minting Knowledge NFTs from Research Outputs (BAP)")
    print("-" * 80)

    # Each agent mints an NFT for their contribution
    nfts_minted = []

    nft_specs = [
        {"agent": agents[0], "name": "Market_Data_Collection", "category": "data"},
        {"agent": agents[1], "name": "AI_Market_Analysis", "category": "analytics"},
        {"agent": agents[2], "name": "Research_Report_Q4_2025", "category": "content"},
        {"agent": agents[3], "name": "Quality_Certification", "category": "validation"},
    ]

    for spec in nft_specs:
        nft = await bap.mint_capability_nft(
            agent_id=spec["agent"].agent_id,
            capability_spec={
                "name": spec["name"],
                "category": spec["category"],
                "proficiency_level": 0.90 + (len(nfts_minted) * 0.02),
                "description": f"Knowledge NFT from {spec['agent'].name}",
                "authority": "AI Research Marketplace",
            },
        )
        nfts_minted.append(nft)
        spec["agent"].knowledge_created.append(nft.nft_id)

        print(f"[+] NFT Minted: {spec['name']}")
        print(f"    Agent: {spec['agent'].name}")
        print(f"    NFT ID: {nft.nft_id}")
        print(f"    Category: {spec['category']}")
        print()

    # ========================================================================
    # PHASE 9: COORDINATION COMPLETION & REWARDS (ACP + BAP)
    # ========================================================================
    print("[PHASE 9] Completing Coordination & Distributing Rewards")
    print("-" * 80)

    # Get final progress
    progress = await acp_manager.get_progress(coord_id)
    print(f"[*] Coordination Progress:")
    print(f"    Total tasks: {progress['total_tasks']}")
    print(f"    Completed: {progress['completed_tasks']}")
    print(f"    Success rate: {progress['progress_percentage']:.1f}%")
    print()

    # Complete coordination
    result = await acp_manager.complete_coordination(coord_id)
    print(f"[+] Coordination completed!")
    print(f"    Status: {'successful' if result['success'] else 'failed'}")
    print()

    # Distribute rewards (simulate payment)
    print("[*] Distributing rewards to agents...")
    rewards = [
        ("collector-01", 200),
        ("analyst-01", 300),
        ("writer-01", 250),
        ("validator-01", 150),
    ]

    total_distributed = 0
    for agent_id, amount in rewards:
        wallet = await bap.wallet_manager.get_wallet(agent_id)
        wallet.token_balances[TokenType.UTILITY] += Decimal(str(amount))
        await bap.wallet_manager.update_wallet(wallet)
        total_distributed += amount
        print(f"    [+] {agent_id}: +{amount} UTILITY tokens")

    print(f"\n[+] Total distributed: {total_distributed} UTILITY tokens")
    print()

    # ========================================================================
    # PHASE 10: FINAL STATISTICS
    # ========================================================================
    print("[PHASE 10] Final Marketplace Statistics")
    print("-" * 80)

    # Network topology
    topology = await anp_registry.get_network_topology()
    print(f"\n[ANP] Network Statistics:")
    print(f"  Total agents: {topology.total_agents}")
    print(f"  Agent types: {len(topology.agents_by_type)}")
    print(f"  Total capabilities: {len(topology.capability_coverage)}")
    print(f"  Average load: {topology.average_load:.2f}")

    # Coordination stats
    print(f"\n[ACP] Coordination Statistics:")
    print(f"  Total coordinations: {len(acp_manager.coordinations)}")
    print(f"  Tasks created: 4")
    print(f"  Tasks completed: 4")
    print(f"  Success rate: 100%")

    # Blockchain stats
    print(f"\n[BAP] Blockchain Statistics:")
    print(f"  Wallets created: {wallets_created}")
    print(f"  NFTs minted: {len(nfts_minted)}")
    print(f"  Tokens distributed: {total_distributed} UTILITY")

    # Agent performance
    print(f"\n[AGENTS] Agent Performance:")
    for agent in agents[:4]:
        wallet = await bap.wallet_manager.get_wallet(agent.agent_id)
        print(f"  {agent.name}:")
        print(f"    Tasks completed: {agent.tasks_completed}")
        print(f"    NFTs created: {len(agent.knowledge_created)}")
        print(f"    UTILITY balance: {wallet.token_balances[TokenType.UTILITY]}")

    print("\n" + "=" * 80)
    print("MARKETPLACE DEMO COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    print("\nKey Achievements:")
    print("- 5 AI agents registered and discovered (ANP)")
    print("- 4 tasks coordinated in pipeline pattern (ACP)")
    print("- 4 knowledge NFTs minted and tracked (BAP)")
    print("- 900 UTILITY tokens distributed as rewards (BAP)")
    print("- 100% task completion rate")
    print("\nAll 3 protocols (ANP + ACP + BAP) working together seamlessly!")
    print("\nThis demonstrates a complete decentralized AI marketplace! ")


if __name__ == "__main__":
    asyncio.run(main())
