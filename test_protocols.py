#!/usr/bin/env python3
"""
SuperStandard v1.0 - Protocol Testing Suite

Quick test to verify all protocols are working correctly.

Usage:
    python test_protocols.py
"""
import asyncio
import sys

async def main():
    print("\n" + "="*70)
    print("SuperStandard v1.0 - Protocol Testing Suite")
    print("="*70 + "\n")

    all_passed = True

    # Test 1: ANP (Agent Network Protocol)
    print("Test 1: ANP (Agent Network Protocol)")
    print("-" * 70)
    try:
        from crates.agentic_protocols.python.anp_implementation import example_usage
        await example_usage()
        print("[PASS] ANP Test PASSED\n")
    except Exception as e:
        print(f"[FAIL] ANP Test FAILED: {e}\n")
        all_passed = False

    # Test 2: ACP (Agent Coordination Protocol)
    print("\nTest 2: ACP (Agent Coordination Protocol)")
    print("-" * 70)
    try:
        from crates.agentic_protocols.python.acp_implementation import example_usage as acp_example
        await acp_example()
        print("[PASS] ACP Test PASSED\n")
    except Exception as e:
        print(f"[FAIL] ACP Test FAILED: {e}\n")
        all_passed = False

    # Test 3: BAP (Blockchain Agent Protocol)
    print("\nTest 3: BAP (Blockchain Agent Protocol)")
    print("-" * 70)
    try:
        from agents.consolidated.py.blockchain_agentic_protocol import (
            BlockchainAgenticProtocol,
            AgentWallet,
            TokenType
        )

        bap = BlockchainAgenticProtocol(config={})

        # Test wallet creation
        wallet = AgentWallet(
            agent_id="test-agent",
            address="0x1234567890abcdef",
            token_balances={
                TokenType.REPUTATION: 100.0,
                TokenType.UTILITY: 500.0,
                TokenType.GOVERNANCE: 50.0
            }
        )
        await bap.wallet_manager.store_wallet(wallet)
        print(f"[+] Wallet created: {wallet.agent_id}")
        print(f"    Reputation: {wallet.token_balances[TokenType.REPUTATION]}")
        print(f"    Utility: {wallet.token_balances[TokenType.UTILITY]}")

        # Test NFT minting
        nft = await bap.mint_capability_nft(
            agent_id="test-agent",
            capability_type="data_analysis",
            proficiency_level=0.92,
            metadata={"verified": True, "certifications": ["ML Engineer"]}
        )
        print(f"[+] NFT minted: {nft['nft_id']}")
        print(f"    Capability: {nft['capability_type']}")
        print(f"    Proficiency: {nft['proficiency_level']:.0%}")

        print("[PASS] BAP Test PASSED\n")
    except Exception as e:
        print(f"[FAIL] BAP Test FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        all_passed = False

    # Summary
    print("="*70)
    if all_passed:
        print("[SUCCESS] ALL TESTS PASSED! SuperStandard v1.0 is ready!")
        print("="*70)
        print("\nYou can now:")
        print("- Run the built-in examples")
        print("- Integrate protocols into your applications")
        print("- Build amazing multi-agent systems")
        print("\nLet's change the world!")
        return 0
    else:
        print("[FAIL] SOME TESTS FAILED - Please check the errors above")
        print("="*70)
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
