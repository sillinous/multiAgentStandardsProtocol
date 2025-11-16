"""BAP Agent Economy Demo.

Demonstrates the Blockchain Agent Protocol (BAP) v1.0 with:
- Agent wallet creation
- Token transfers and staking
- Capability NFT minting
- Smart contract collaboration
- DAO governance voting
- Complete agent economic ecosystem
"""

import asyncio
from decimal import Decimal
from datetime import datetime

from src.superstandard.protocols.bap_v1 import (
    create_bap_client,
    TokenType,
    TransactionType,
)


async def main():
    """Run BAP agent economy demonstration."""
    print("=" * 80)
    print("BLOCKCHAIN AGENT PROTOCOL (BAP) v1.0 DEMONSTRATION")
    print("WORLD-FIRST: Decentralized Agent Economy")
    print("=" * 80)
    print()

    # Initialize BAP client
    print("1. Initializing BAP Client...")
    client = create_bap_client({
        "network": "consortium",
        "consensus": "proof_of_capability",
    })
    print(f"   ✓ BAP Client v{client.version} initialized")
    print()

    # =========================================================================
    # STEP 1: Create Agent Wallets
    # =========================================================================
    print("2. Creating Agent Wallets...")
    print("-" * 80)

    # Create strategic planning agent
    strategic_wallet = await client.create_wallet(
        agent_id="apqc_1_0_strategic_001",
        security_level="consortium",
    )
    print(f"   ✓ Strategic Agent Wallet: {strategic_wallet.wallet_id[:8]}...")
    print(f"     - Agent ID: {strategic_wallet.agent_id}")
    print(f"     - Public Key: {strategic_wallet.public_key[:20]}...")
    print(f"     - Security: {strategic_wallet.security_level}")
    print(f"     - Initial Utility Tokens: {strategic_wallet.token_balances[TokenType.UTILITY.value]}")
    print(f"     - Initial Reputation: {strategic_wallet.token_balances[TokenType.REPUTATION.value]}")
    print()

    # Create financial agent
    financial_wallet = await client.create_wallet(
        agent_id="apqc_9_2_financial_001",
        security_level="quantum_secure",
    )
    print(f"   ✓ Financial Agent Wallet: {financial_wallet.wallet_id[:8]}...")
    print(f"     - Agent ID: {financial_wallet.agent_id}")
    print(f"     - Security: {financial_wallet.security_level}")
    print()

    # Create marketing agent
    marketing_wallet = await client.create_wallet(
        agent_id="apqc_3_0_marketing_001",
        security_level="consortium",
    )
    print(f"   ✓ Marketing Agent Wallet: {marketing_wallet.wallet_id[:8]}...")
    print(f"     - Agent ID: {marketing_wallet.agent_id}")
    print()

    # Create multi-sig DAO wallet
    dao_wallet = await client.create_wallet(
        agent_id="dao_governance_001",
        security_level="consortium",
        multi_sig_threshold=2,
        authorized_signers=[
            "apqc_1_0_strategic_001",
            "apqc_9_2_financial_001",
            "apqc_3_0_marketing_001"
        ],
    )
    print(f"   ✓ DAO Multi-Sig Wallet: {dao_wallet.wallet_id[:8]}...")
    print(f"     - Multi-Sig Threshold: {dao_wallet.multi_sig_threshold}")
    print(f"     - Authorized Signers: {len(dao_wallet.authorized_signers)}")
    print()

    # =========================================================================
    # STEP 2: Mint Capability NFTs
    # =========================================================================
    print("3. Minting Capability NFTs...")
    print("-" * 80)

    # Strategic planning NFT
    strategic_nft = await client.mint_capability_nft(
        agent_id="apqc_1_0_strategic_001",
        capability_name="Strategic Planning Expert",
        capability_category="apqc:1.0",
        proficiency_level=0.95,
        description="Expert-level strategic planning and business strategy development",
        prerequisites=["strategic_planning_intermediate", "business_analysis"],
        performance_proof={
            "tasks_completed": 500,
            "success_rate": 0.96,
            "peer_rating": 4.8,
            "certifications": ["Strategic Management", "Business Strategy"],
        },
    )
    print(f"   ✓ Strategic Planning NFT: {strategic_nft.nft_id[:8]}...")
    print(f"     - Capability: {strategic_nft.capability_name}")
    print(f"     - Proficiency: {strategic_nft.proficiency_level * 100}%")
    print(f"     - Mint Cost: {strategic_nft.mint_cost} tokens")
    print(f"     - Validation Score: {strategic_nft.validation_score}")
    print()

    # Financial analysis NFT
    financial_nft = await client.mint_capability_nft(
        agent_id="apqc_9_2_financial_001",
        capability_name="Financial Analysis Expert",
        capability_category="apqc:9.2",
        proficiency_level=0.92,
        description="Advanced financial analysis and reporting",
        prerequisites=["accounting_basics", "financial_modeling"],
        performance_proof={
            "tasks_completed": 450,
            "success_rate": 0.94,
            "peer_rating": 4.7,
        },
    )
    print(f"   ✓ Financial Analysis NFT: {financial_nft.nft_id[:8]}...")
    print(f"     - Capability: {financial_nft.capability_name}")
    print(f"     - Proficiency: {financial_nft.proficiency_level * 100}%")
    print()

    # Marketing campaign NFT
    marketing_nft = await client.mint_capability_nft(
        agent_id="apqc_3_0_marketing_001",
        capability_name="Marketing Campaign Management",
        capability_category="apqc:3.0",
        proficiency_level=0.88,
        description="Digital marketing and campaign management expertise",
        performance_proof={
            "campaigns_managed": 200,
            "avg_roi": 3.5,
            "success_rate": 0.91,
        },
    )
    print(f"   ✓ Marketing Campaign NFT: {marketing_nft.nft_id[:8]}...")
    print(f"     - Capability: {marketing_nft.capability_name}")
    print(f"     - Proficiency: {marketing_nft.proficiency_level * 100}%")
    print()

    # =========================================================================
    # STEP 3: Token Transfers
    # =========================================================================
    print("4. Executing Token Transfers...")
    print("-" * 80)

    # Transfer utility tokens
    transfer_tx = await client.transfer_tokens(
        from_agent="apqc_1_0_strategic_001",
        to_agent="apqc_9_2_financial_001",
        token_type=TokenType.UTILITY.value,
        amount=Decimal("100"),
    )
    print(f"   ✓ Token Transfer: {transfer_tx.transaction_id[:8]}...")
    print(f"     - From: {transfer_tx.from_agent}")
    print(f"     - To: {transfer_tx.to_agent}")
    print(f"     - Amount: {transfer_tx.amount} {transfer_tx.token_type}")
    print(f"     - Fee: {transfer_tx.transaction_fee}")
    print(f"     - Status: {transfer_tx.status}")
    print(f"     - Block: {transfer_tx.block_number}")
    print()

    # Check balances
    strategic_balance = await client.get_balance(
        "apqc_1_0_strategic_001",
        TokenType.UTILITY.value
    )
    financial_balance = await client.get_balance(
        "apqc_9_2_financial_001",
        TokenType.UTILITY.value
    )
    print(f"   Balances after transfer:")
    print(f"     - Strategic Agent: {strategic_balance} UTILITY")
    print(f"     - Financial Agent: {financial_balance} UTILITY")
    print()

    # =========================================================================
    # STEP 4: Create Collaboration Smart Contract
    # =========================================================================
    print("5. Creating Collaboration Smart Contract...")
    print("-" * 80)

    collaboration_contract = await client.create_smart_contract(
        contract_type="multi_agent_collaboration",
        contract_name="FY2026 Strategic Planning Project",
        participating_agents=[
            "apqc_1_0_strategic_001",
            "apqc_9_2_financial_001",
            "apqc_3_0_marketing_001",
        ],
        creator_agent_id="apqc_1_0_strategic_001",
        execution_conditions=[
            "all_agents_signed",
            "tokens_staked",
            "capabilities_verified",
        ],
        success_criteria=[
            "deliverables_approved",
            "deadline_met",
            "quality_score_above_0.8",
        ],
        token_allocations={
            "apqc_1_0_strategic_001": Decimal("500"),
            "apqc_9_2_financial_001": Decimal("300"),
            "apqc_3_0_marketing_001": Decimal("200"),
        },
        expiration_days=60,
    )

    print(f"   ✓ Smart Contract: {collaboration_contract.contract_id[:8]}...")
    print(f"     - Name: {collaboration_contract.contract_name}")
    print(f"     - Type: {collaboration_contract.contract_type}")
    print(f"     - Participants: {len(collaboration_contract.participating_agents)}")
    print(f"     - Creator: {collaboration_contract.contract_creator}")
    print(f"     - State: {collaboration_contract.contract_state}")
    print(f"     - Execution Conditions:")
    for condition in collaboration_contract.execution_conditions:
        print(f"       • {condition}")
    print(f"     - Token Allocations:")
    for agent, amount in collaboration_contract.token_allocations.items():
        print(f"       • {agent}: {amount} tokens")
    print()

    # =========================================================================
    # STEP 5: Stake Reputation Tokens
    # =========================================================================
    print("6. Staking Reputation Tokens for Collaboration...")
    print("-" * 80)

    # Each agent stakes reputation
    stake_amounts = {
        "apqc_1_0_strategic_001": Decimal("50"),
        "apqc_9_2_financial_001": Decimal("40"),
        "apqc_3_0_marketing_001": Decimal("30"),
    }

    for agent_id, stake_amount in stake_amounts.items():
        success = await client.stake_tokens(
            agent_id=agent_id,
            token_type=TokenType.REPUTATION.value,
            amount=stake_amount,
            stake_id=collaboration_contract.contract_id,
        )
        print(f"   ✓ {agent_id} staked {stake_amount} REPUTATION")

        # Check staked balance
        wallet = await client.get_wallet(agent_id)
        staked = wallet.staked_tokens.get(collaboration_contract.contract_id, Decimal("0"))
        print(f"     - Total Staked: {staked}")

    print()

    # =========================================================================
    # STEP 6: Execute Smart Contract
    # =========================================================================
    print("7. Executing Collaboration Smart Contract...")
    print("-" * 80)

    execution_result = await client.execute_contract(
        contract_id=collaboration_contract.contract_id,
        execution_data={
            "phase": "completion",
            "deliverables": [
                "Strategic Plan Document",
                "Financial Projections",
                "Marketing Strategy",
            ],
            "quality_score": 0.92,
        }
    )

    print(f"   ✓ Contract Execution: {execution_result['contract_id'][:8]}...")
    print(f"     - Success: {execution_result['success']}")
    print(f"     - State: {collaboration_contract.contract_state}")
    print(f"     - Execution History Entries: {len(collaboration_contract.execution_history)}")
    print()

    # =========================================================================
    # STEP 7: NFT Transfer (Secondary Market)
    # =========================================================================
    print("8. Transferring NFT on Secondary Market...")
    print("-" * 80)

    # Transfer marketing NFT to strategic agent
    nft_transfer_success = await client.transfer_nft(
        nft_id=marketing_nft.nft_id,
        from_agent="apqc_3_0_marketing_001",
        to_agent="apqc_1_0_strategic_001",
    )

    print(f"   ✓ NFT Transfer: {marketing_nft.nft_id[:8]}...")
    print(f"     - From: apqc_3_0_marketing_001")
    print(f"     - To: apqc_1_0_strategic_001")
    print(f"     - Capability: {marketing_nft.capability_name}")
    print(f"     - Transfer Fee: {marketing_nft.transfer_fee}")
    print(f"     - Success: {nft_transfer_success}")
    print()

    # Check NFT ownership
    strategic_nfts = await client.get_nfts("apqc_1_0_strategic_001")
    print(f"   Strategic Agent now owns {len(strategic_nfts)} NFTs:")
    for nft in strategic_nfts:
        print(f"     • {nft.capability_name} (proficiency: {nft.proficiency_level})")
    print()

    # =========================================================================
    # STEP 8: DAO Governance Voting
    # =========================================================================
    print("9. DAO Governance Voting...")
    print("-" * 80)

    # Give governance tokens to agents
    for agent_id in ["apqc_1_0_strategic_001", "apqc_9_2_financial_001", "apqc_3_0_marketing_001"]:
        wallet = await client.get_wallet(agent_id)
        wallet.token_balances[TokenType.GOVERNANCE.value] = Decimal("100")

    # Vote on governance proposal
    proposal_id = "proposal_expand_token_economy"
    print(f"   Proposal: {proposal_id}")
    print(f"   Topic: Expand token economy with new innovation rewards")
    print()

    votes = [
        ("apqc_1_0_strategic_001", "yes", "Will incentivize creative solutions"),
        ("apqc_9_2_financial_001", "yes", "Good ROI for ecosystem growth"),
        ("apqc_3_0_marketing_001", "no", "Need more analysis first"),
    ]

    for agent_id, vote, rationale in votes:
        success = await client.vote_on_proposal(
            agent_id=agent_id,
            proposal_id=proposal_id,
            vote=vote,
            rationale=rationale,
        )
        wallet = await client.get_wallet(agent_id)
        voting_power = wallet.token_balances[TokenType.GOVERNANCE.value]
        print(f"   ✓ {agent_id}")
        print(f"     - Vote: {vote.upper()}")
        print(f"     - Voting Power: {voting_power}")
        print(f"     - Rationale: {rationale}")
        print()

    # =========================================================================
    # STEP 9: Protocol Statistics
    # =========================================================================
    print("10. Protocol Statistics & Summary...")
    print("-" * 80)

    stats = await client.get_statistics()
    print(f"   BAP Protocol Statistics:")
    print(f"     - Version: {stats['version']}")
    print(f"     - Current Block: {stats['current_block']}")
    print(f"     - Total Wallets: {stats['total_wallets']}")
    print(f"     - Total NFTs: {stats['total_nfts']}")
    print(f"     - Total Contracts: {stats['total_contracts']}")
    print(f"     - Total Transactions: {stats['total_transactions']}")
    print(f"     - Governance Votes: {stats['total_governance_votes']}")
    print()

    # =========================================================================
    # STEP 10: Agent Economic Profiles
    # =========================================================================
    print("11. Agent Economic Profiles...")
    print("-" * 80)

    for agent_id in ["apqc_1_0_strategic_001", "apqc_9_2_financial_001", "apqc_3_0_marketing_001"]:
        wallet = await client.get_wallet(agent_id)
        nfts = await client.get_nfts(agent_id)
        transactions = await client.get_transactions(agent_id)

        print(f"   {agent_id}:")
        print(f"     Token Balances:")
        print(f"       • UTILITY: {wallet.token_balances[TokenType.UTILITY.value]}")
        print(f"       • REPUTATION: {wallet.token_balances[TokenType.REPUTATION.value]}")
        print(f"       • GOVERNANCE: {wallet.token_balances[TokenType.GOVERNANCE.value]}")
        print(f"     NFTs Owned: {len(nfts)}")
        for nft in nfts:
            print(f"       • {nft.capability_name}")
        print(f"     Transactions: {len(transactions)}")
        print(f"     Staked Tokens: {len(wallet.staked_tokens)} stakes")
        print()

    # =========================================================================
    # DEMO COMPLETE
    # =========================================================================
    print("=" * 80)
    print("DEMONSTRATION COMPLETE!")
    print("=" * 80)
    print()
    print("Key Features Demonstrated:")
    print("  ✓ Multi-level agent wallets with security levels")
    print("  ✓ Multi-signature DAO governance wallet")
    print("  ✓ Capability NFT minting with proficiency levels")
    print("  ✓ Token transfers with transaction fees")
    print("  ✓ Reputation staking for collaborations")
    print("  ✓ Smart contract creation and execution")
    print("  ✓ NFT secondary market transfers")
    print("  ✓ DAO governance voting with voting power")
    print("  ✓ Complete blockchain transaction processing")
    print("  ✓ Agent economic profiles and statistics")
    print()
    print("The Blockchain Agent Protocol enables:")
    print("  • Decentralized agent economies")
    print("  • Capability-based certification (NFTs)")
    print("  • Autonomous collaboration contracts")
    print("  • Democratic DAO governance")
    print("  • Multi-token economic models")
    print("  • Cryptographic security and verification")
    print()
    print("This is the WORLD-FIRST blockchain economics protocol")
    print("specifically designed for autonomous agent ecosystems!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
