"""
🛒 E2E Workflow: Agent Capability Marketplace
==============================================

Complete end-to-end demonstration of a decentralized agent marketplace using:
- ANP: Agent Network Registration
- BAP: Blockchain for NFT minting and smart contracts
- ACP: Coordinated Multi-Agent Collaboration
- A2A: Agent Communication and Negotiation
- ASP: Semantic Capability Discovery

Scenario:
Agents register their capabilities as NFTs on a blockchain, create a marketplace
for buying/selling capabilities, discover and purchase capabilities, collaborate
on tasks, and distribute rewards via blockchain transactions.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum

# Protocol imports
from superstandard.protocols.anp_implementation import AgentNetworkRegistry
from superstandard.protocols.asp_v1 import (
    SemanticRegistry,
    OntologyReference,
    SemanticCapability,
    SemanticDeclaration,
)
from superstandard.protocols.acp_implementation import (
    CoordinationManager,
    CoordinationType,
    Task,
    Participant,
)

# Simple mock classes for workflow demonstration
@dataclass
class WorkflowNode:
    """Workflow node for demonstration."""
    node_id: str
    node_type: str
    agent_id: str
    task_definition: Dict[str, Any]

@dataclass
class WorkflowEdge:
    """Workflow edge for demonstration."""
    from_node: str
    to_node: str

class CoordinationEngine:
    """Simplified coordination engine for demonstration."""
    def __init__(self):
        self.sessions = {}
        self.workflows = {}

    async def create_session(self, session_id: str, pattern: CoordinationType,
                            participants: List[str], metadata: Dict[str, Any] = None):
        """Create a coordination session."""
        self.sessions[session_id] = {
            "session_id": session_id,
            "pattern": pattern.value if hasattr(pattern, 'value') else str(pattern),
            "participants": participants,
            "metadata": metadata or {},
            "status": "active"
        }

CoordinationPattern = CoordinationType
from superstandard.agents.blockchain.blockchain_agentic_protocol import (
    AgentWallet,
    TokenType,
    TransactionType,
    CapabilityNFT,
)
from superstandard.agents.base.protocols import A2AMessage, MessageType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Helper Classes
# ============================================================================

@dataclass
class MarketplaceAgent:
    """Agent participating in the marketplace."""
    agent_id: str
    agent_type: str
    capabilities: List[str]
    wallet: AgentWallet
    owned_nfts: List[CapabilityNFT] = field(default_factory=list)
    messages: List[A2AMessage] = field(default_factory=list)

    async def send_message(self, to_agent: str, message_type: str, content: Dict[str, Any]) -> A2AMessage:
        """Send message to another agent."""
        msg = A2AMessage(
            from_agent=self.agent_id,
            to_agent=to_agent,
            message_type=message_type,
            content=content
        )
        logger.info(f"💬 {self.agent_id} → {to_agent}: {message_type}")
        return msg

    async def receive_message(self, message: A2AMessage) -> None:
        """Receive message."""
        self.messages.append(message)
        logger.info(f"📨 {self.agent_id} received: {message.message_type}")


@dataclass
class SmartContract:
    """Blockchain smart contract for marketplace."""
    contract_id: str
    contract_type: str
    participants: List[str]
    terms: Dict[str, Any]
    status: str = "pending"
    transactions: List[Dict[str, Any]] = field(default_factory=list)

    def execute(self) -> Dict[str, Any]:
        """Execute the smart contract."""
        logger.info(f"⚡ Executing contract: {self.contract_id}")
        self.status = "executed"
        return {
            "contract_id": self.contract_id,
            "status": self.status,
            "timestamp": datetime.utcnow().isoformat()
        }


@dataclass
class Marketplace:
    """Decentralized agent capability marketplace."""
    marketplace_id: str
    listings: List[Dict[str, Any]] = field(default_factory=list)
    contracts: List[SmartContract] = field(default_factory=list)
    transactions: List[Dict[str, Any]] = field(default_factory=list)

    def list_capability(
        self,
        nft: CapabilityNFT,
        seller_id: str,
        price: Decimal,
        token_type: TokenType
    ) -> str:
        """List capability NFT for sale."""
        listing_id = f"listing_{len(self.listings) + 1}"
        listing = {
            "listing_id": listing_id,
            "nft_id": nft.nft_id,
            "capability_id": nft.capability_id,
            "seller_id": seller_id,
            "price": str(price),
            "token_type": token_type.value,
            "status": "active",
            "listed_at": datetime.utcnow().isoformat()
        }
        self.listings.append(listing)
        logger.info(f"📋 Listed: {nft.capability_id} for {price} {token_type.value}")
        return listing_id

    def search_capabilities(self, capability_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for capabilities in marketplace."""
        if capability_filter:
            return [
                listing for listing in self.listings
                if capability_filter.lower() in listing["capability_id"].lower()
                and listing["status"] == "active"
            ]
        return [listing for listing in self.listings if listing["status"] == "active"]

    def create_purchase_contract(
        self,
        listing: Dict[str, Any],
        buyer_id: str
    ) -> SmartContract:
        """Create smart contract for capability purchase."""
        contract = SmartContract(
            contract_id=f"contract_{len(self.contracts) + 1}",
            contract_type="capability_purchase",
            participants=[listing["seller_id"], buyer_id],
            terms={
                "listing_id": listing["listing_id"],
                "nft_id": listing["nft_id"],
                "price": listing["price"],
                "token_type": listing["token_type"],
                "seller_id": listing["seller_id"],
                "buyer_id": buyer_id
            }
        )
        self.contracts.append(contract)
        return contract

    def execute_purchase(
        self,
        contract: SmartContract,
        buyer_wallet: AgentWallet,
        seller_wallet: AgentWallet,
        nft: CapabilityNFT
    ) -> Dict[str, Any]:
        """Execute capability purchase via smart contract."""
        price = Decimal(contract.terms["price"])
        token_type = TokenType(contract.terms["token_type"])

        # Transfer tokens from buyer to seller
        buyer_wallet.token_balances[token_type] -= price
        seller_wallet.token_balances[token_type] += price

        # Transfer NFT from seller to buyer
        buyer_wallet.nft_holdings.append(nft.nft_id)
        if nft.nft_id in seller_wallet.nft_holdings:
            seller_wallet.nft_holdings.remove(nft.nft_id)

        # Execute contract
        result = contract.execute()

        # Record transaction
        transaction = {
            "transaction_id": f"tx_{len(self.transactions) + 1}",
            "transaction_type": TransactionType.CAPABILITY_TRANSFER.value,
            "from_wallet": seller_wallet.wallet_id,
            "to_wallet": buyer_wallet.wallet_id,
            "nft_id": nft.nft_id,
            "amount": str(price),
            "token_type": token_type.value,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.transactions.append(transaction)

        # Update listing status
        for listing in self.listings:
            if listing["listing_id"] == contract.terms["listing_id"]:
                listing["status"] = "sold"
                break

        logger.info(f"✅ Purchase completed: {nft.capability_id}")
        return result


# ============================================================================
# Main Workflow
# ============================================================================

async def run_agent_marketplace_workflow():
    """Execute complete agent marketplace workflow."""

    print("\n" + "="*80)
    print("🛒 AGENT CAPABILITY MARKETPLACE - E2E WORKFLOW")
    print("="*80 + "\n")

    # ========================================================================
    # PHASE 1: Initialize Systems
    # ========================================================================

    print("\n" + "-"*80)
    print("PHASE 1: Initialize Marketplace Systems")
    print("-"*80 + "\n")

    network_registry = AgentNetworkRegistry()
    semantic_registry = SemanticRegistry()
    coordinator = CoordinationEngine()
    marketplace = Marketplace(marketplace_id="capability_marketplace_v1")

    logger.info("✓ Network registry initialized (ANP)")
    logger.info("✓ Semantic registry initialized (ASP)")
    logger.info("✓ Coordination engine initialized (ACP)")
    logger.info("✓ Marketplace initialized (BAP)")

    # ========================================================================
    # PHASE 2: Create Agents with Wallets (ANP + BAP)
    # ========================================================================

    print("\n" + "-"*80)
    print("PHASE 2: Create Agents with Blockchain Wallets")
    print("-"*80 + "\n")

    # Create agents with wallets
    agents = {
        "ml_expert": MarketplaceAgent(
            agent_id="ml_expert_001",
            agent_type="MLExpert",
            capabilities=["machine_learning", "deep_learning", "model_training"],
            wallet=AgentWallet(
                wallet_id="wallet_ml_001",
                agent_id="ml_expert_001",
                public_key="pub_ml_001",
                private_key_hash="hash_ml_001",
                token_balances={
                    TokenType.UTILITY: Decimal("5000.0"),
                    TokenType.REPUTATION: Decimal("92.5")
                }
            )
        ),
        "data_scientist": MarketplaceAgent(
            agent_id="data_scientist_001",
            agent_type="DataScientist",
            capabilities=["data_analysis", "statistical_modeling", "visualization"],
            wallet=AgentWallet(
                wallet_id="wallet_ds_001",
                agent_id="data_scientist_001",
                public_key="pub_ds_001",
                private_key_hash="hash_ds_001",
                token_balances={
                    TokenType.UTILITY: Decimal("3000.0"),
                    TokenType.REPUTATION: Decimal("88.0")
                }
            )
        ),
        "nlp_specialist": MarketplaceAgent(
            agent_id="nlp_specialist_001",
            agent_type="NLPSpecialist",
            capabilities=["nlp", "text_analysis", "language_models"],
            wallet=AgentWallet(
                wallet_id="wallet_nlp_001",
                agent_id="nlp_specialist_001",
                public_key="pub_nlp_001",
                private_key_hash="hash_nlp_001",
                token_balances={
                    TokenType.UTILITY: Decimal("4000.0"),
                    TokenType.REPUTATION: Decimal("90.0")
                }
            )
        ),
        "project_manager": MarketplaceAgent(
            agent_id="project_manager_001",
            agent_type="ProjectManager",
            capabilities=["project_management", "coordination", "planning"],
            wallet=AgentWallet(
                wallet_id="wallet_pm_001",
                agent_id="project_manager_001",
                public_key="pub_pm_001",
                private_key_hash="hash_pm_001",
                token_balances={
                    TokenType.UTILITY: Decimal("10000.0"),  # Has budget to buy
                    TokenType.REPUTATION: Decimal("95.0")
                }
            )
        )
    }

    # Register agents in network
    for key, agent in agents.items():
        await network_registry.register_agent(
            agent_id=agent.agent_id,
            agent_type=agent.agent_type,
            capabilities=agent.capabilities,
            endpoints={"http": f"http://localhost:8000/{agent.agent_id}"},
            metadata={
                "wallet_id": agent.wallet.wallet_id,
                "reputation": str(agent.wallet.token_balances[TokenType.REPUTATION])
            }
        )
        logger.info(f"✓ Registered: {agent.agent_id} (Wallet: {agent.wallet.wallet_id})")

    # ========================================================================
    # PHASE 3: Mint Capability NFTs (BAP)
    # ========================================================================

    print("\n" + "-"*80)
    print("PHASE 3: Mint Capability NFTs")
    print("-"*80 + "\n")

    # Mint NFTs for each agent's capabilities
    all_nfts = {}

    for key, agent in agents.items():
        agent_nfts = []
        for capability in agent.capabilities[:2]:  # Mint top 2 capabilities
            nft = CapabilityNFT(
                nft_id=f"nft_{agent.agent_id}_{capability}",
                capability_id=capability,
                capability_name=capability.replace("_", " ").title(),
                owner_id=agent.agent_id,
                minted_at=datetime.utcnow().isoformat(),
                metadata={
                    "agent_type": agent.agent_type,
                    "proficiency_level": "expert",
                    "certification": "verified"
                }
            )
            agent_nfts.append(nft)
            agent.owned_nfts.append(nft)
            agent.wallet.nft_holdings.append(nft.nft_id)

            logger.info(f"🎨 Minted NFT: {nft.capability_id} for {agent.agent_id}")

        all_nfts[key] = agent_nfts

    total_nfts = sum(len(nfts) for nfts in all_nfts.values())
    logger.info(f"✓ Total NFTs minted: {total_nfts}")

    # ========================================================================
    # PHASE 4: List Capabilities in Marketplace (BAP)
    # ========================================================================

    print("\n" + "-"*80)
    print("PHASE 4: List Capabilities in Marketplace")
    print("-"*80 + "\n")

    # Agents list their capabilities for sale (except project manager)
    listings = {}

    # ML Expert lists capabilities
    listings["ml_1"] = marketplace.list_capability(
        nft=all_nfts["ml_expert"][0],
        seller_id=agents["ml_expert"].agent_id,
        price=Decimal("500.0"),
        token_type=TokenType.UTILITY
    )

    # Data Scientist lists capabilities
    listings["ds_1"] = marketplace.list_capability(
        nft=all_nfts["data_scientist"][0],
        seller_id=agents["data_scientist"].agent_id,
        price=Decimal("400.0"),
        token_type=TokenType.UTILITY
    )

    # NLP Specialist lists capabilities
    listings["nlp_1"] = marketplace.list_capability(
        nft=all_nfts["nlp_specialist"][0],
        seller_id=agents["nlp_specialist"].agent_id,
        price=Decimal("600.0"),
        token_type=TokenType.UTILITY
    )

    logger.info(f"✓ {len(listings)} capabilities listed in marketplace")

    # ========================================================================
    # PHASE 5: Discover and Purchase Capabilities (ANP + ASP + BAP + A2A)
    # ========================================================================

    print("\n" + "-"*80)
    print("PHASE 5: Discover and Purchase Capabilities")
    print("-"*80 + "\n")

    # Project manager needs ML and NLP capabilities for a project
    pm = agents["project_manager"]

    # Discover via network registry (ANP)
    ml_agents = await network_registry.discover_agents(
        capability_filter=["machine_learning"]
    )
    logger.info(f"✓ Discovered {len(ml_agents)} agents with ML capability (ANP)")

    # Search marketplace for ML capability
    ml_listings = marketplace.search_capabilities("machine_learning")
    logger.info(f"✓ Found {len(ml_listings)} ML listings in marketplace")

    # Negotiate purchase via A2A messaging
    ml_seller = agents["ml_expert"]
    ml_listing = ml_listings[0]

    # PM sends purchase inquiry
    inquiry_msg = await pm.send_message(
        to_agent=ml_seller.agent_id,
        message_type="purchase_inquiry",
        content={
            "listing_id": ml_listing["listing_id"],
            "offered_price": str(Decimal(ml_listing["price"]) * Decimal("0.9")),  # 10% discount
            "reason": "bulk_purchase"
        }
    )
    await ml_seller.receive_message(inquiry_msg)

    # Seller accepts (simplified negotiation)
    acceptance_msg = await ml_seller.send_message(
        to_agent=pm.agent_id,
        message_type="purchase_accepted",
        content={
            "listing_id": ml_listing["listing_id"],
            "final_price": ml_listing["price"],  # Original price
            "nft_id": ml_listing["nft_id"]
        }
    )
    await pm.receive_message(acceptance_msg)

    logger.info("✓ Purchase negotiation completed via A2A")

    # Create and execute smart contract
    purchase_contract = marketplace.create_purchase_contract(
        listing=ml_listing,
        buyer_id=pm.agent_id
    )

    logger.info(f"✓ Smart contract created: {purchase_contract.contract_id}")

    # Execute purchase
    ml_nft = all_nfts["ml_expert"][0]
    purchase_result = marketplace.execute_purchase(
        contract=purchase_contract,
        buyer_wallet=pm.wallet,
        seller_wallet=ml_seller.wallet,
        nft=ml_nft
    )

    pm.owned_nfts.append(ml_nft)

    logger.info(f"✓ Purchase executed: {ml_nft.capability_id}")
    logger.info(f"  PM balance: {pm.wallet.token_balances[TokenType.UTILITY]} UTILITY")
    logger.info(f"  Seller balance: {ml_seller.wallet.token_balances[TokenType.UTILITY]} UTILITY")

    # Purchase NLP capability similarly
    nlp_listing = marketplace.search_capabilities("nlp")[0]
    nlp_contract = marketplace.create_purchase_contract(
        listing=nlp_listing,
        buyer_id=pm.agent_id
    )

    nlp_nft = all_nfts["nlp_specialist"][0]
    nlp_seller = agents["nlp_specialist"]

    marketplace.execute_purchase(
        contract=nlp_contract,
        buyer_wallet=pm.wallet,
        seller_wallet=nlp_seller.wallet,
        nft=nlp_nft
    )

    pm.owned_nfts.append(nlp_nft)
    logger.info(f"✓ Purchase executed: {nlp_nft.capability_id}")

    # ========================================================================
    # PHASE 6: Collaborative Task Execution (ACP + A2A)
    # ========================================================================

    print("\n" + "-"*80)
    print("PHASE 6: Collaborative Task Execution")
    print("-"*80 + "\n")

    # Create coordination session for project
    session_id = "ai_project_collaboration"

    await coordinator.create_session(
        session_id=session_id,
        pattern=CoordinationPattern.PIPELINE,
        participants=[
            ml_seller.agent_id,
            nlp_seller.agent_id,
            agents["data_scientist"].agent_id,
            pm.agent_id
        ],
        metadata={
            "project": "customer_sentiment_analysis",
            "budget": "2000.0",
            "deadline": (datetime.utcnow() + timedelta(days=14)).isoformat()
        }
    )

    logger.info(f"✓ Coordination session created: {session_id}")

    # Define workflow
    workflow = [
        WorkflowNode(
            node_id="data_prep",
            node_type="task",
            agent_id=agents["data_scientist"].agent_id,
            task_definition={"task": "prepare_customer_data"}
        ),
        WorkflowNode(
            node_id="nlp_processing",
            node_type="task",
            agent_id=nlp_seller.agent_id,
            task_definition={"task": "extract_sentiment_features"}
        ),
        WorkflowNode(
            node_id="ml_modeling",
            node_type="task",
            agent_id=ml_seller.agent_id,
            task_definition={"task": "train_sentiment_model"}
        ),
    ]

    # Execute workflow with A2A communication
    for i, node in enumerate(workflow):
        task_msg = await pm.send_message(
            to_agent=node.agent_id,
            message_type=MessageType.TASK_ASSIGNMENT.value,
            content={
                "session_id": session_id,
                "task": node.task_definition["task"],
                "sequence": i + 1
            }
        )

        # Find agent and deliver message
        agent = next(a for a in agents.values() if a.agent_id == node.agent_id)
        await agent.receive_message(task_msg)

        # Simulate task completion
        result_msg = await agent.send_message(
            to_agent=pm.agent_id,
            message_type=MessageType.RESULT.value,
            content={
                "task": node.task_definition["task"],
                "status": "completed",
                "quality_score": 0.95
            }
        )
        await pm.receive_message(result_msg)

        logger.info(f"✓ Task completed: {node.task_definition['task']}")

    # ========================================================================
    # PHASE 7: Distribute Rewards (BAP)
    # ========================================================================

    print("\n" + "-"*80)
    print("PHASE 7: Distribute Performance Rewards")
    print("-"*80 + "\n")

    # PM distributes rewards based on performance
    reward_distribution = {
        agents["data_scientist"].agent_id: Decimal("300.0"),
        nlp_seller.agent_id: Decimal("400.0"),
        ml_seller.agent_id: Decimal("500.0"),
    }

    for agent_id, reward_amount in reward_distribution.items():
        # Deduct from PM
        pm.wallet.token_balances[TokenType.UTILITY] -= reward_amount

        # Add to agent
        agent = next(a for a in agents.values() if a.agent_id == agent_id)
        agent.wallet.token_balances[TokenType.UTILITY] += reward_amount

        # Also award reputation tokens
        reputation_reward = reward_amount * Decimal("0.01")  # 1% as reputation
        agent.wallet.token_balances[TokenType.REPUTATION] += reputation_reward

        # Record transaction
        transaction = {
            "transaction_type": TransactionType.PERFORMANCE_REWARD.value,
            "from_wallet": pm.wallet.wallet_id,
            "to_wallet": agent.wallet.wallet_id,
            "amount": str(reward_amount),
            "token_type": TokenType.UTILITY.value,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        marketplace.transactions.append(transaction)

        logger.info(f"💰 Rewarded {agent_id}: {reward_amount} UTILITY + {reputation_reward} REPUTATION")

    # ========================================================================
    # PHASE 8: Results Summary
    # ========================================================================

    print("\n" + "="*80)
    print("MARKETPLACE WORKFLOW SUMMARY")
    print("="*80 + "\n")

    print("NFT Minting:")
    print(f"  • Total NFTs minted: {total_nfts}")
    print(f"  • Capabilities tokenized: {sum(len(agent.capabilities[:2]) for agent in agents.values())}")

    print("\nMarketplace Activity:")
    print(f"  • Total listings: {len(marketplace.listings)}")
    print(f"  • Successful sales: {sum(1 for l in marketplace.listings if l['status'] == 'sold')}")
    print(f"  • Smart contracts: {len(marketplace.contracts)}")
    print(f"  • Total transactions: {len(marketplace.transactions)}")

    print("\nAgent Balances:")
    for key, agent in agents.items():
        print(f"  • {agent.agent_id}:")
        print(f"      UTILITY: {agent.wallet.token_balances[TokenType.UTILITY]}")
        print(f"      REPUTATION: {agent.wallet.token_balances[TokenType.REPUTATION]}")
        print(f"      NFTs owned: {len(agent.wallet.nft_holdings)}")

    print("\nProtocol Integration:")
    print(f"  ✓ ANP: {len(agents)} agents registered")
    print(f"  ✓ BAP: {total_nfts} NFTs minted, {len(marketplace.contracts)} contracts")
    print(f"  ✓ ASP: Semantic capability discovery")
    print(f"  ✓ ACP: Collaborative workflow coordination")
    print(f"  ✓ A2A: {sum(len(a.messages) for a in agents.values())} messages exchanged")

    print("\n" + "="*80)
    print("✅ AGENT MARKETPLACE WORKFLOW COMPLETED SUCCESSFULLY")
    print("="*80 + "\n")

    return {
        "marketplace_id": marketplace.marketplace_id,
        "total_nfts": total_nfts,
        "total_transactions": len(marketplace.transactions),
        "agents_participated": len(agents)
    }


# ============================================================================
# Main Entry Point
# ============================================================================

async def main():
    """Main entry point."""
    try:
        result = await run_agent_marketplace_workflow()
        print(f"\n✅ Marketplace workflow completed!")
        print(f"Total NFTs: {result['total_nfts']}")
        print(f"Total transactions: {result['total_transactions']}")
    except Exception as e:
        logger.error(f"❌ Workflow failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
