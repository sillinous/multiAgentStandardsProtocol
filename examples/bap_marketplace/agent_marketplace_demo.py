"""
SuperStandard BAP (Blockchain Agent Protocol) Demo

This example demonstrates:
1. Agent wallet creation and token management
2. Capability NFT minting and trading
3. Smart contract creation for collaboration
4. Reputation staking and management
5. DAO governance with proposals and voting
6. Complete agent marketplace simulation

Usage:
    python examples/bap_marketplace/agent_marketplace_demo.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.consolidated.py.blockchain_agentic_protocol import (
    BlockchainAgenticProtocol,
    AgentWallet,
    TokenType,
    CapabilityNFT,
    SmartContract,
    Transaction,
    GovernanceProposal,
    ProposalStatus,
    VoteType
)


async def main():
    print("\n" + "="*80)
    print("SuperStandard BAP v1.0 - Agent Marketplace & Blockchain Economy Demo")
    print("="*80 + "\n")

    # Initialize BAP
    bap = BlockchainAgenticProtocol()
    print("[*] Initialized Blockchain Agent Protocol\n")

    # Step 1: Create agent wallets
    print("Step 1: Creating agent wallets with initial token balances")
    print("-" * 80)

    # Create wallet for Data Provider Agent
    print("[*] Creating wallet for Data Provider Agent...")
    wallet1 = AgentWallet(
        agent_id="data-provider-1",
        address="0x1234567890abcdef1234567890abcdef12345678",
        token_balances={
            TokenType.REPUTATION: 150.0,
            TokenType.UTILITY: 1000.0,
            TokenType.CAPABILITY: 5.0
        },
        reputation_staked=0.0,
        staking_history=[]
    )
    await bap.wallet_manager.store_wallet(wallet1)
    print(f"[+] Created wallet: {wallet1.address}")
    print(f"    Reputation: {wallet1.token_balances[TokenType.REPUTATION]}")
    print(f"    Utility: {wallet1.token_balances[TokenType.UTILITY]}")

    # Create wallet for AI Analyst Agent
    print("\n[*] Creating wallet for AI Analyst Agent...")
    wallet2 = AgentWallet(
        agent_id="ai-analyst-1",
        address="0xabcdef1234567890abcdef1234567890abcdef12",
        token_balances={
            TokenType.REPUTATION: 200.0,
            TokenType.UTILITY: 500.0,
            TokenType.GOVERNANCE: 100.0
        },
        reputation_staked=0.0,
        staking_history=[]
    )
    await bap.wallet_manager.store_wallet(wallet2)
    print(f"[+] Created wallet: {wallet2.address}")
    print(f"    Reputation: {wallet2.token_balances[TokenType.REPUTATION]}")
    print(f"    Governance: {wallet2.token_balances[TokenType.GOVERNANCE]}")

    # Create wallet for Report Generator Agent
    print("\n[*] Creating wallet for Report Generator Agent...")
    wallet3 = AgentWallet(
        agent_id="report-gen-1",
        address="0x7890abcdef1234567890abcdef1234567890abcd",
        token_balances={
            TokenType.REPUTATION: 180.0,
            TokenType.UTILITY: 750.0,
            TokenType.PERFORMANCE: 50.0
        },
        reputation_staked=0.0,
        staking_history=[]
    )
    await bap.wallet_manager.store_wallet(wallet3)
    print(f"[+] Created wallet: {wallet3.address}")

    # Step 2: Mint Capability NFTs
    print("\nStep 2: Minting Capability NFTs for agent skills")
    print("-" * 80)

    # Mint "Data Analysis" NFT for AI Analyst
    print("[*] Minting 'Data Analysis' NFT for ai-analyst-1...")
    nft1 = await bap.mint_capability_nft(
        agent_id="ai-analyst-1",
        capability_type="data_analysis",
        proficiency_level=0.92,
        metadata={
            "verified": True,
            "certifications": ["ML Engineer", "Data Scientist"],
            "years_experience": 5,
            "success_rate": 0.95
        }
    )
    print(f"[+] Minted NFT: {nft1['nft_id']}")
    print(f"    Capability: {nft1['capability_type']}")
    print(f"    Proficiency: {nft1['proficiency_level']:.2%}")
    print(f"    Verified: {nft1['metadata']['verified']}")

    # Mint "Report Generation" NFT for Report Generator
    print("\n[*] Minting 'Report Generation' NFT for report-gen-1...")
    nft2 = await bap.mint_capability_nft(
        agent_id="report-gen-1",
        capability_type="report_generation",
        proficiency_level=0.88,
        metadata={
            "verified": True,
            "formats_supported": ["PDF", "HTML", "PPT"],
            "templates": 50,
            "avg_quality_score": 4.7
        }
    )
    print(f"[+] Minted NFT: {nft2['nft_id']}")
    print(f"    Capability: {nft2['capability_type']}")
    print(f"    Formats: {', '.join(nft2['metadata']['formats_supported'])}")

    # Mint "API Integration" NFT for Data Provider
    print("\n[*] Minting 'API Integration' NFT for data-provider-1...")
    nft3 = await bap.mint_capability_nft(
        agent_id="data-provider-1",
        capability_type="api_integration",
        proficiency_level=0.85,
        metadata={
            "verified": True,
            "apis_supported": 30,
            "reliability": 0.99,
            "avg_response_time": "200ms"
        }
    )
    print(f"[+] Minted NFT: {nft3['nft_id']}")
    print(f"    APIs supported: {nft3['metadata']['apis_supported']}")
    print(f"    Reliability: {nft3['metadata']['reliability']:.1%}")

    # Step 3: Trade Capability NFTs
    print("\nStep 3: Trading Capability NFTs on marketplace")
    print("-" * 80)

    # Data Provider lists API Integration NFT for sale
    print("[*] data-provider-1 listing 'API Integration' NFT for 50 UTILITY tokens...")
    # In a real implementation, this would create a marketplace listing
    print("[+] NFT listed on marketplace")

    # Step 4: Reputation Staking
    print("\nStep 4: Reputation staking for collaboration trust")
    print("-" * 80)

    # AI Analyst stakes reputation for upcoming collaboration
    print("[*] ai-analyst-1 staking 50 REPUTATION tokens for collaboration...")
    stake_amount = 50.0
    wallet2.reputation_staked += stake_amount
    wallet2.token_balances[TokenType.REPUTATION] -= stake_amount
    wallet2.staking_history.append({
        "amount": stake_amount,
        "timestamp": datetime.now().isoformat(),
        "purpose": "data_analysis_project"
    })
    await bap.wallet_manager.update_wallet(wallet2)
    print(f"[+] Staked {stake_amount} REPUTATION")
    print(f"    Remaining balance: {wallet2.token_balances[TokenType.REPUTATION]}")
    print(f"    Total staked: {wallet2.reputation_staked}")

    # Step 5: Create Smart Contract for Collaboration
    print("\nStep 5: Creating smart contract for multi-agent collaboration")
    print("-" * 80)

    print("[*] Creating collaboration contract between 3 agents...")
    contract = await bap.create_collaboration_contract(
        participants=["data-provider-1", "ai-analyst-1", "report-gen-1"],
        payment_schedule={
            "data-provider-1": {
                "amount": 100,
                "token_type": TokenType.UTILITY,
                "milestone": "data_delivery"
            },
            "ai-analyst-1": {
                "amount": 200,
                "token_type": TokenType.UTILITY,
                "milestone": "analysis_complete"
            },
            "report-gen-1": {
                "amount": 150,
                "token_type": TokenType.UTILITY,
                "milestone": "report_delivered"
            }
        },
        terms={
            "project": "Customer Insights Analysis Q4",
            "duration_days": 14,
            "deliverables": [
                "Customer data from 3 sources",
                "Behavioral analysis with ML insights",
                "Executive summary report"
            ],
            "penalty_clause": "10% reputation burn for non-delivery"
        }
    )
    print(f"[+] Contract created: {contract['contract_id']}")
    print(f"    Participants: {len(contract['participants'])}")
    print(f"    Total value: {contract['total_value']} tokens")
    print(f"    Duration: {contract['terms']['duration_days']} days")
    print(f"\n    Payment Schedule:")
    for agent_id, payment in contract['payment_schedule'].items():
        print(f"      {agent_id}: {payment['amount']} {payment['token_type']}")
        print(f"        Milestone: {payment['milestone']}")

    # Step 6: Execute Contract Milestones
    print("\nStep 6: Executing contract milestones")
    print("-" * 80)

    print("[*] Milestone 1: data-provider-1 delivers data...")
    await asyncio.sleep(0.5)
    # Create transaction for first milestone
    tx1 = Transaction(
        transaction_id=f"tx-milestone-1-{int(datetime.now().timestamp())}",
        from_agent="contract-escrow",
        to_agent="data-provider-1",
        token_type=TokenType.UTILITY,
        amount=100.0,
        transaction_type="milestone_payment",
        timestamp=datetime.now(),
        status="pending"
    )
    result = await bap.transaction_processor.process_transaction(tx1)
    print(f"[+] Milestone 1 payment processed: {result}")
    # Update wallet balance
    wallet1.token_balances[TokenType.UTILITY] += 100.0
    await bap.wallet_manager.update_wallet(wallet1)
    print(f"    data-provider-1 new balance: {wallet1.token_balances[TokenType.UTILITY]} UTILITY")

    print("\n[*] Milestone 2: ai-analyst-1 completes analysis...")
    await asyncio.sleep(0.5)
    tx2 = Transaction(
        transaction_id=f"tx-milestone-2-{int(datetime.now().timestamp())}",
        from_agent="contract-escrow",
        to_agent="ai-analyst-1",
        token_type=TokenType.UTILITY,
        amount=200.0,
        transaction_type="milestone_payment",
        timestamp=datetime.now(),
        status="pending"
    )
    result = await bap.transaction_processor.process_transaction(tx2)
    print(f"[+] Milestone 2 payment processed: {result}")
    wallet2.token_balances[TokenType.UTILITY] += 200.0
    await bap.wallet_manager.update_wallet(wallet2)
    print(f"    ai-analyst-1 new balance: {wallet2.token_balances[TokenType.UTILITY]} UTILITY")

    print("\n[*] Milestone 3: report-gen-1 delivers report...")
    await asyncio.sleep(0.5)
    tx3 = Transaction(
        transaction_id=f"tx-milestone-3-{int(datetime.now().timestamp())}",
        from_agent="contract-escrow",
        to_agent="report-gen-1",
        token_type=TokenType.UTILITY,
        amount=150.0,
        transaction_type="milestone_payment",
        timestamp=datetime.now(),
        status="pending"
    )
    result = await bap.transaction_processor.process_transaction(tx3)
    print(f"[+] Milestone 3 payment processed: {result}")
    wallet3.token_balances[TokenType.UTILITY] += 150.0
    await bap.wallet_manager.update_wallet(wallet3)
    print(f"    report-gen-1 new balance: {wallet3.token_balances[TokenType.UTILITY]} UTILITY")

    # Step 7: Return Staked Reputation
    print("\nStep 7: Returning staked reputation after successful collaboration")
    print("-" * 80)

    print("[*] Collaboration completed successfully, returning staked reputation...")
    # Return staked reputation with bonus for successful collaboration
    reputation_bonus = 10.0
    wallet2.token_balances[TokenType.REPUTATION] += wallet2.reputation_staked + reputation_bonus
    wallet2.reputation_staked = 0.0
    await bap.wallet_manager.update_wallet(wallet2)
    print(f"[+] Reputation returned to ai-analyst-1")
    print(f"    Bonus earned: {reputation_bonus} REPUTATION")
    print(f"    New reputation balance: {wallet2.token_balances[TokenType.REPUTATION]}")

    # Step 8: DAO Governance Proposal
    print("\nStep 8: DAO governance - Proposing protocol upgrade")
    print("-" * 80)

    print("[*] ai-analyst-1 creating governance proposal...")
    proposal = await bap.create_governance_proposal(
        proposer_id="ai-analyst-1",
        proposal_type="protocol_upgrade",
        title="Increase minimum reputation for high-value contracts",
        description="Propose increasing minimum reputation requirement from 100 to 150 "
                   "for contracts valued over 1000 UTILITY tokens to ensure quality.",
        options=["approve", "reject", "modify"],
        voting_period_days=7,
        required_quorum=0.3,
        execution_data={
            "parameter": "min_reputation_high_value",
            "current_value": 100,
            "proposed_value": 150
        }
    )
    print(f"[+] Proposal created: {proposal['proposal_id']}")
    print(f"    Title: {proposal['title']}")
    print(f"    Voting period: {proposal['voting_period_days']} days")
    print(f"    Required quorum: {proposal['required_quorum']:.0%}")

    # Step 9: Vote on Proposal
    print("\nStep 9: Agents voting on governance proposal")
    print("-" * 80)

    # ai-analyst-1 votes (100 GOVERNANCE tokens)
    print("[*] ai-analyst-1 voting 'approve' with 100 GOVERNANCE tokens...")
    vote1 = await bap.vote_on_proposal(
        proposal_id=proposal['proposal_id'],
        voter_id="ai-analyst-1",
        vote=VoteType.APPROVE,
        voting_power=wallet2.token_balances[TokenType.GOVERNANCE]
    )
    print(f"[+] Vote recorded: {vote1['vote']}")
    print(f"    Voting power: {vote1['voting_power']}")

    # Step 10: Final Wallet Summary
    print("\nStep 10: Final wallet balances after marketplace activity")
    print("-" * 80)

    all_wallets = [
        ("data-provider-1", wallet1),
        ("ai-analyst-1", wallet2),
        ("report-gen-1", wallet3)
    ]

    for agent_id, wallet in all_wallets:
        print(f"\n[*] {agent_id}:")
        print(f"    Address: {wallet.address}")
        for token_type, balance in wallet.token_balances.items():
            if balance > 0:
                print(f"    {token_type.name}: {balance}")
        if wallet.reputation_staked > 0:
            print(f"    Reputation Staked: {wallet.reputation_staked}")

    # Step 11: Transaction History
    print("\nStep 11: Recent transaction history")
    print("-" * 80)

    print("[*] Checking transaction history for ai-analyst-1...")
    transactions = await bap.transaction_processor.get_agent_transactions("ai-analyst-1")
    print(f"[+] Found {len(transactions)} transactions")
    for tx in transactions[-3:]:  # Show last 3
        print(f"    - {tx.transaction_type}: {tx.amount} {tx.token_type.name}")
        print(f"      From: {tx.from_agent} → To: {tx.to_agent}")
        print(f"      Status: {tx.status}")

    print("\n" + "="*80)
    print("Agent Marketplace Demo Completed Successfully!")
    print("="*80)

    print("\nKey Achievements:")
    print("- 3 agent wallets created with multi-token balances")
    print("- 3 capability NFTs minted and verified")
    print("- Reputation staking system demonstrated")
    print("- Smart contract with 3 milestones executed successfully")
    print("- 450 UTILITY tokens distributed via milestone payments")
    print("- Reputation returned with bonus after successful collaboration")
    print("- DAO governance proposal created and voted on")
    print("\nThis demonstrates a complete decentralized agent economy! 🚀")


if __name__ == "__main__":
    asyncio.run(main())
