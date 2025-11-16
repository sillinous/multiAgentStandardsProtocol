"""Comprehensive tests for Blockchain Agent Protocol (BAP) v1.0.

Tests cover:
- Wallet creation and management
- Token transfers and staking
- NFT minting and transfers
- Smart contract creation and execution
- DAO governance voting
- Transaction processing
- Security features
"""

import asyncio
import pytest
from decimal import Decimal
from datetime import datetime, timedelta

from src.superstandard.protocols.bap_v1 import (
    BAPClient,
    AgentWallet,
    CapabilityNFT,
    SmartContract,
    Transaction,
    TokenType,
    TransactionType,
    SecurityLevel,
    create_bap_client,
)


class TestBAPClient:
    """Test BAP client initialization and basic operations."""

    @pytest.mark.asyncio
    async def test_client_creation(self):
        """Test creating BAP client."""
        client = create_bap_client()
        assert client is not None
        assert client.version == "1.0.0"
        assert client.stats["total_wallets"] == 0

    @pytest.mark.asyncio
    async def test_client_with_config(self):
        """Test creating BAP client with config."""
        config = {"network": "testnet"}
        client = create_bap_client(config)
        assert client.config == config


class TestWalletOperations:
    """Test wallet creation and management."""

    @pytest.mark.asyncio
    async def test_create_wallet(self):
        """Test creating an agent wallet."""
        client = create_bap_client()
        wallet = await client.create_wallet("agent_001")

        assert wallet is not None
        assert wallet.agent_id == "agent_001"
        assert wallet.wallet_id is not None
        assert wallet.public_key.startswith("0x")
        assert len(wallet.private_key_hash) == 64  # SHA256 hash
        assert wallet.security_level == "consortium"

    @pytest.mark.asyncio
    async def test_wallet_initial_balances(self):
        """Test wallet receives initial token allocation."""
        client = create_bap_client()
        wallet = await client.create_wallet("agent_002")

        # Should have initial allocation
        assert wallet.token_balances[TokenType.UTILITY.value] == Decimal("1000")
        assert wallet.token_balances[TokenType.REPUTATION.value] == Decimal("100")

    @pytest.mark.asyncio
    async def test_wallet_security_levels(self):
        """Test creating wallets with different security levels."""
        client = create_bap_client()

        wallet_public = await client.create_wallet("agent_003", security_level="public")
        assert wallet_public.security_level == "public"

        wallet_quantum = await client.create_wallet("agent_004", security_level="quantum_secure")
        assert wallet_quantum.security_level == "quantum_secure"

    @pytest.mark.asyncio
    async def test_multi_sig_wallet(self):
        """Test creating multi-signature wallet."""
        client = create_bap_client()
        wallet = await client.create_wallet(
            "agent_005",
            multi_sig_threshold=2,
            authorized_signers=["agent_005", "agent_006", "agent_007"]
        )

        assert wallet.multi_sig_threshold == 2
        assert len(wallet.authorized_signers) == 3
        assert "agent_005" in wallet.authorized_signers

    @pytest.mark.asyncio
    async def test_get_wallet(self):
        """Test retrieving wallet by agent ID."""
        client = create_bap_client()
        created_wallet = await client.create_wallet("agent_008")
        retrieved_wallet = await client.get_wallet("agent_008")

        assert retrieved_wallet is not None
        assert retrieved_wallet.wallet_id == created_wallet.wallet_id
        assert retrieved_wallet.agent_id == "agent_008"

    @pytest.mark.asyncio
    async def test_duplicate_wallet_fails(self):
        """Test that creating duplicate wallet fails."""
        client = create_bap_client()
        await client.create_wallet("agent_009")

        with pytest.raises(ValueError, match="already exists"):
            await client.create_wallet("agent_009")

    @pytest.mark.asyncio
    async def test_wallet_to_dict(self):
        """Test converting wallet to dictionary."""
        client = create_bap_client()
        wallet = await client.create_wallet("agent_010")
        wallet_dict = wallet.to_dict()

        assert isinstance(wallet_dict, dict)
        assert wallet_dict["agent_id"] == "agent_010"
        assert "wallet_id" in wallet_dict
        assert "token_balances" in wallet_dict


class TestTokenOperations:
    """Test token transfers and management."""

    @pytest.mark.asyncio
    async def test_token_transfer(self):
        """Test transferring tokens between wallets."""
        client = create_bap_client()
        await client.create_wallet("agent_011")
        await client.create_wallet("agent_012")

        # Transfer tokens
        transaction = await client.transfer_tokens(
            from_agent="agent_011",
            to_agent="agent_012",
            token_type=TokenType.UTILITY.value,
            amount=Decimal("100")
        )

        assert transaction is not None
        assert transaction.status == "confirmed"

        # Check balances
        from_balance = await client.get_balance("agent_011", TokenType.UTILITY.value)
        to_balance = await client.get_balance("agent_012", TokenType.UTILITY.value)

        assert from_balance == Decimal("900")  # 1000 - 100
        assert to_balance == Decimal("1100")   # 1000 + 100

    @pytest.mark.asyncio
    async def test_insufficient_balance_fails(self):
        """Test that transfer fails with insufficient balance."""
        client = create_bap_client()
        await client.create_wallet("agent_013")
        await client.create_wallet("agent_014")

        with pytest.raises(ValueError):
            await client.transfer_tokens(
                from_agent="agent_013",
                to_agent="agent_014",
                token_type=TokenType.UTILITY.value,
                amount=Decimal("10000")  # More than initial balance
            )

    @pytest.mark.asyncio
    async def test_stake_tokens(self):
        """Test staking tokens."""
        client = create_bap_client()
        await client.create_wallet("agent_015")

        # Stake tokens
        success = await client.stake_tokens(
            agent_id="agent_015",
            token_type=TokenType.REPUTATION.value,
            amount=Decimal("50"),
            stake_id="collaboration_001"
        )

        assert success is True

        # Check balances
        wallet = await client.get_wallet("agent_015")
        assert wallet.token_balances[TokenType.REPUTATION.value] == Decimal("50")  # 100 - 50
        assert wallet.staked_tokens["collaboration_001"] == Decimal("50")

    @pytest.mark.asyncio
    async def test_unstake_tokens(self):
        """Test unstaking tokens."""
        client = create_bap_client()
        await client.create_wallet("agent_016")

        # Stake then unstake
        await client.stake_tokens(
            agent_id="agent_016",
            token_type=TokenType.REPUTATION.value,
            amount=Decimal("50"),
            stake_id="collaboration_002"
        )

        success = await client.unstake_tokens(
            agent_id="agent_016",
            stake_id="collaboration_002",
            amount=Decimal("30"),
            token_type=TokenType.REPUTATION.value
        )

        assert success is True

        wallet = await client.get_wallet("agent_016")
        assert wallet.token_balances[TokenType.REPUTATION.value] == Decimal("80")  # 100 - 50 + 30
        assert wallet.staked_tokens["collaboration_002"] == Decimal("20")  # 50 - 30

    @pytest.mark.asyncio
    async def test_all_token_types(self):
        """Test that all 9 token types are supported."""
        client = create_bap_client()
        wallet = await client.create_wallet("agent_017")

        # Check all token types are initialized
        expected_tokens = [
            TokenType.REPUTATION,
            TokenType.CAPABILITY,
            TokenType.PERFORMANCE,
            TokenType.COLLABORATION,
            TokenType.INNOVATION,
            TokenType.KNOWLEDGE,
            TokenType.COMPUTE,
            TokenType.GOVERNANCE,
            TokenType.UTILITY,
        ]

        for token_type in expected_tokens:
            assert token_type.value in wallet.token_balances

    @pytest.mark.asyncio
    async def test_get_balance(self):
        """Test getting token balance."""
        client = create_bap_client()
        await client.create_wallet("agent_018")

        balance = await client.get_balance("agent_018", TokenType.UTILITY.value)
        assert balance == Decimal("1000")

        # Non-existent agent
        balance = await client.get_balance("agent_999", TokenType.UTILITY.value)
        assert balance == Decimal("0")


class TestNFTOperations:
    """Test NFT minting and transfers."""

    @pytest.mark.asyncio
    async def test_mint_capability_nft(self):
        """Test minting a capability NFT."""
        client = create_bap_client()
        await client.create_wallet("agent_019")

        nft = await client.mint_capability_nft(
            agent_id="agent_019",
            capability_name="Strategic Planning Expert",
            capability_category="apqc:1.0",
            proficiency_level=0.95,
            description="Expert-level strategic planning",
        )

        assert nft is not None
        assert nft.capability_name == "Strategic Planning Expert"
        assert nft.proficiency_level == 0.95
        assert nft.current_owner == "agent_019"
        assert nft.certification_authority == "SuperStandard Consortium"

    @pytest.mark.asyncio
    async def test_nft_mint_cost(self):
        """Test that NFT minting costs are calculated correctly."""
        client = create_bap_client()
        await client.create_wallet("agent_020")

        # Higher proficiency = higher cost
        nft_expert = await client.mint_capability_nft(
            agent_id="agent_020",
            capability_name="Expert Skill",
            capability_category="apqc:1.0",
            proficiency_level=0.95,
        )

        # Cost should be 10 + (0.95 * 90) = 95.5
        assert nft_expert.mint_cost >= Decimal("90")
        assert nft_expert.mint_cost <= Decimal("100")

    @pytest.mark.asyncio
    async def test_nft_insufficient_balance_fails(self):
        """Test that NFT minting fails with insufficient balance."""
        client = create_bap_client()
        wallet = await client.create_wallet("agent_021")

        # Drain wallet
        wallet.token_balances[TokenType.UTILITY.value] = Decimal("5")

        with pytest.raises(ValueError, match="Insufficient tokens"):
            await client.mint_capability_nft(
                agent_id="agent_021",
                capability_name="Expensive Skill",
                capability_category="apqc:1.0",
                proficiency_level=0.99,
            )

    @pytest.mark.asyncio
    async def test_transfer_nft(self):
        """Test transferring NFT between agents."""
        client = create_bap_client()
        await client.create_wallet("agent_022")
        await client.create_wallet("agent_023")

        # Mint NFT
        nft = await client.mint_capability_nft(
            agent_id="agent_022",
            capability_name="Test Skill",
            capability_category="apqc:1.0",
            proficiency_level=0.5,
        )

        # Transfer NFT
        success = await client.transfer_nft(
            nft_id=nft.nft_id,
            from_agent="agent_022",
            to_agent="agent_023"
        )

        assert success is True

        # Check ownership
        updated_nft = client.nfts[nft.nft_id]
        assert updated_nft.current_owner == "agent_023"
        assert "agent_022" in updated_nft.previous_owners

    @pytest.mark.asyncio
    async def test_transfer_nft_not_owner_fails(self):
        """Test that NFT transfer fails if not owner."""
        client = create_bap_client()
        await client.create_wallet("agent_024")
        await client.create_wallet("agent_025")
        await client.create_wallet("agent_026")

        nft = await client.mint_capability_nft(
            agent_id="agent_024",
            capability_name="Test Skill",
            capability_category="apqc:1.0",
            proficiency_level=0.5,
        )

        with pytest.raises(ValueError, match="does not own"):
            await client.transfer_nft(
                nft_id=nft.nft_id,
                from_agent="agent_025",  # Not the owner
                to_agent="agent_026"
            )

    @pytest.mark.asyncio
    async def test_get_agent_nfts(self):
        """Test getting all NFTs for an agent."""
        client = create_bap_client()
        await client.create_wallet("agent_027")

        # Mint multiple NFTs
        nft1 = await client.mint_capability_nft(
            agent_id="agent_027",
            capability_name="Skill 1",
            capability_category="apqc:1.0",
            proficiency_level=0.5,
        )

        nft2 = await client.mint_capability_nft(
            agent_id="agent_027",
            capability_name="Skill 2",
            capability_category="apqc:2.0",
            proficiency_level=0.7,
        )

        nfts = await client.get_nfts("agent_027")
        assert len(nfts) == 2
        assert nft1 in nfts
        assert nft2 in nfts

    @pytest.mark.asyncio
    async def test_nft_with_prerequisites(self):
        """Test NFT with prerequisites."""
        client = create_bap_client()
        await client.create_wallet("agent_028")

        nft = await client.mint_capability_nft(
            agent_id="agent_028",
            capability_name="Advanced Skill",
            capability_category="apqc:1.0",
            proficiency_level=0.8,
            prerequisites=["basic_skill", "intermediate_skill"],
        )

        assert len(nft.prerequisites) == 2
        assert "basic_skill" in nft.prerequisites

    @pytest.mark.asyncio
    async def test_nft_with_performance_proof(self):
        """Test NFT with performance proof."""
        client = create_bap_client()
        await client.create_wallet("agent_029")

        performance_proof = {
            "tasks_completed": 500,
            "success_rate": 0.96,
            "peer_rating": 4.8,
        }

        nft = await client.mint_capability_nft(
            agent_id="agent_029",
            capability_name="Proven Skill",
            capability_category="apqc:1.0",
            proficiency_level=0.9,
            performance_proof=performance_proof,
        )

        assert nft.performance_proof["tasks_completed"] == 500
        assert nft.performance_proof["success_rate"] == 0.96

    @pytest.mark.asyncio
    async def test_nft_to_dict(self):
        """Test converting NFT to dictionary."""
        client = create_bap_client()
        await client.create_wallet("agent_030")

        nft = await client.mint_capability_nft(
            agent_id="agent_030",
            capability_name="Test Skill",
            capability_category="apqc:1.0",
            proficiency_level=0.5,
        )

        nft_dict = nft.to_dict()
        assert isinstance(nft_dict, dict)
        assert nft_dict["capability_name"] == "Test Skill"
        assert "nft_id" in nft_dict


class TestSmartContracts:
    """Test smart contract creation and execution."""

    @pytest.mark.asyncio
    async def test_create_contract(self):
        """Test creating a smart contract."""
        client = create_bap_client()
        await client.create_wallet("agent_031")
        await client.create_wallet("agent_032")

        contract = await client.create_smart_contract(
            contract_type="collaboration",
            contract_name="Test Collaboration",
            participating_agents=["agent_031", "agent_032"],
            creator_agent_id="agent_031",
        )

        assert contract is not None
        assert contract.contract_name == "Test Collaboration"
        assert len(contract.participating_agents) == 2
        assert contract.contract_creator == "agent_031"
        assert contract.contract_state == "created"

    @pytest.mark.asyncio
    async def test_contract_with_conditions(self):
        """Test creating contract with execution conditions."""
        client = create_bap_client()
        await client.create_wallet("agent_033")

        contract = await client.create_smart_contract(
            contract_type="collaboration",
            contract_name="Conditional Contract",
            participating_agents=["agent_033"],
            creator_agent_id="agent_033",
            execution_conditions=["all_agents_signed", "tokens_staked"],
            success_criteria=["deliverables_approved", "deadline_met"],
        )

        assert len(contract.execution_conditions) == 2
        assert "all_agents_signed" in contract.execution_conditions
        assert len(contract.success_criteria) == 2

    @pytest.mark.asyncio
    async def test_contract_with_token_allocations(self):
        """Test contract with token allocations."""
        client = create_bap_client()
        await client.create_wallet("agent_034")
        await client.create_wallet("agent_035")

        allocations = {
            "agent_034": Decimal("500"),
            "agent_035": Decimal("300"),
        }

        contract = await client.create_smart_contract(
            contract_type="collaboration",
            contract_name="Funded Contract",
            participating_agents=["agent_034", "agent_035"],
            creator_agent_id="agent_034",
            token_allocations=allocations,
        )

        assert contract.token_allocations["agent_034"] == Decimal("500")
        assert contract.token_allocations["agent_035"] == Decimal("300")

    @pytest.mark.asyncio
    async def test_execute_contract(self):
        """Test executing a smart contract."""
        client = create_bap_client()
        await client.create_wallet("agent_036")

        contract = await client.create_smart_contract(
            contract_type="collaboration",
            contract_name="Executable Contract",
            participating_agents=["agent_036"],
            creator_agent_id="agent_036",
        )

        result = await client.execute_contract(
            contract_id=contract.contract_id,
            execution_data={"phase": "completion"}
        )

        assert result["success"] is True
        assert contract.contract_state == "completed"
        assert len(contract.execution_history) == 2  # Started and completed

    @pytest.mark.asyncio
    async def test_contract_expiration(self):
        """Test contract with expiration date."""
        client = create_bap_client()
        await client.create_wallet("agent_037")

        contract = await client.create_smart_contract(
            contract_type="collaboration",
            contract_name="Expiring Contract",
            participating_agents=["agent_037"],
            creator_agent_id="agent_037",
            expiration_days=7,
        )

        assert contract.expiration_date is not None
        expiration = datetime.fromisoformat(contract.expiration_date)
        created = datetime.fromisoformat(contract.created_at)
        delta = expiration - created
        # Allow for slight timing differences (6-7 days)
        assert delta.days >= 6 and delta.days <= 7

    @pytest.mark.asyncio
    async def test_contract_to_dict(self):
        """Test converting contract to dictionary."""
        client = create_bap_client()
        await client.create_wallet("agent_038")

        contract = await client.create_smart_contract(
            contract_type="collaboration",
            contract_name="Test Contract",
            participating_agents=["agent_038"],
            creator_agent_id="agent_038",
        )

        contract_dict = contract.to_dict()
        assert isinstance(contract_dict, dict)
        assert contract_dict["contract_name"] == "Test Contract"
        assert "contract_id" in contract_dict


class TestGovernance:
    """Test DAO governance and voting."""

    @pytest.mark.asyncio
    async def test_vote_on_proposal(self):
        """Test voting on governance proposal."""
        client = create_bap_client()
        wallet = await client.create_wallet("agent_039")

        # Give governance tokens
        wallet.token_balances[TokenType.GOVERNANCE.value] = Decimal("100")

        success = await client.vote_on_proposal(
            agent_id="agent_039",
            proposal_id="proposal_001",
            vote="yes",
            rationale="This proposal benefits the ecosystem"
        )

        assert success is True
        assert client.stats["total_governance_votes"] == 1

    @pytest.mark.asyncio
    async def test_vote_with_voting_power(self):
        """Test that voting power is based on governance tokens."""
        client = create_bap_client()
        wallet = await client.create_wallet("agent_040")

        # Set governance tokens
        wallet.token_balances[TokenType.GOVERNANCE.value] = Decimal("50")

        await client.vote_on_proposal(
            agent_id="agent_040",
            proposal_id="proposal_002",
            vote="no"
        )

        # Check transaction recorded voting power
        transactions = await client.get_transactions("agent_040")
        vote_tx = [tx for tx in transactions if tx.transaction_type == TransactionType.GOVERNANCE_VOTE.value]
        assert len(vote_tx) > 0
        assert vote_tx[0].transaction_data["voting_power"] == "50"

    @pytest.mark.asyncio
    async def test_vote_choices(self):
        """Test different vote choices."""
        client = create_bap_client()
        await client.create_wallet("agent_041")
        await client.create_wallet("agent_042")
        await client.create_wallet("agent_043")

        # Yes vote
        success = await client.vote_on_proposal("agent_041", "proposal_003", "yes")
        assert success is True

        # No vote
        success = await client.vote_on_proposal("agent_042", "proposal_003", "no")
        assert success is True

        # Abstain vote
        success = await client.vote_on_proposal("agent_043", "proposal_003", "abstain")
        assert success is True

    @pytest.mark.asyncio
    async def test_invalid_vote_fails(self):
        """Test that invalid vote choice fails."""
        client = create_bap_client()
        await client.create_wallet("agent_044")

        with pytest.raises(ValueError, match="Invalid vote"):
            await client.vote_on_proposal("agent_044", "proposal_004", "maybe")


class TestTransactions:
    """Test transaction processing."""

    @pytest.mark.asyncio
    async def test_transaction_signing(self):
        """Test that transactions are signed."""
        client = create_bap_client()
        await client.create_wallet("agent_045")
        await client.create_wallet("agent_046")

        transaction = await client.transfer_tokens(
            from_agent="agent_045",
            to_agent="agent_046",
            token_type=TokenType.UTILITY.value,
            amount=Decimal("10")
        )

        assert transaction.signature is not None
        assert len(transaction.signature) > 0

    @pytest.mark.asyncio
    async def test_transaction_confirmation(self):
        """Test transaction confirmation."""
        client = create_bap_client()
        await client.create_wallet("agent_047")
        await client.create_wallet("agent_048")

        transaction = await client.transfer_tokens(
            from_agent="agent_047",
            to_agent="agent_048",
            token_type=TokenType.UTILITY.value,
            amount=Decimal("10")
        )

        assert transaction.status == "confirmed"
        assert transaction.confirmation_count >= 1

    @pytest.mark.asyncio
    async def test_transaction_block_info(self):
        """Test transaction includes block information."""
        client = create_bap_client()
        await client.create_wallet("agent_049")
        await client.create_wallet("agent_050")

        transaction = await client.transfer_tokens(
            from_agent="agent_049",
            to_agent="agent_050",
            token_type=TokenType.UTILITY.value,
            amount=Decimal("10")
        )

        assert transaction.block_number is not None
        assert transaction.block_number > 0
        assert transaction.block_hash is not None

    @pytest.mark.asyncio
    async def test_get_agent_transactions(self):
        """Test getting all transactions for an agent."""
        client = create_bap_client()
        await client.create_wallet("agent_051")
        await client.create_wallet("agent_052")

        # Create multiple transactions
        await client.transfer_tokens(
            from_agent="agent_051",
            to_agent="agent_052",
            token_type=TokenType.UTILITY.value,
            amount=Decimal("10")
        )

        await client.transfer_tokens(
            from_agent="agent_052",
            to_agent="agent_051",
            token_type=TokenType.UTILITY.value,
            amount=Decimal("5")
        )

        transactions = await client.get_transactions("agent_051")
        assert len(transactions) >= 2

    @pytest.mark.asyncio
    async def test_transaction_to_dict(self):
        """Test converting transaction to dictionary."""
        client = create_bap_client()
        await client.create_wallet("agent_053")
        await client.create_wallet("agent_054")

        transaction = await client.transfer_tokens(
            from_agent="agent_053",
            to_agent="agent_054",
            token_type=TokenType.UTILITY.value,
            amount=Decimal("10")
        )

        tx_dict = transaction.to_dict()
        assert isinstance(tx_dict, dict)
        assert tx_dict["from_agent"] == "agent_053"
        assert tx_dict["to_agent"] == "agent_054"


class TestStatistics:
    """Test protocol statistics."""

    @pytest.mark.asyncio
    async def test_get_statistics(self):
        """Test getting protocol statistics."""
        client = create_bap_client()
        stats = await client.get_statistics()

        assert "version" in stats
        assert stats["version"] == "1.0.0"
        assert "total_wallets" in stats
        assert "total_nfts" in stats
        assert "total_contracts" in stats
        assert "total_transactions" in stats

    @pytest.mark.asyncio
    async def test_statistics_update(self):
        """Test that statistics update correctly."""
        client = create_bap_client()

        # Create wallet
        await client.create_wallet("agent_055")
        stats = await client.get_statistics()
        assert stats["total_wallets"] == 1

        # Mint NFT
        await client.mint_capability_nft(
            agent_id="agent_055",
            capability_name="Test",
            capability_category="test",
            proficiency_level=0.5,
        )
        stats = await client.get_statistics()
        assert stats["total_nfts"] == 1

        # Create contract
        await client.create_smart_contract(
            contract_type="test",
            contract_name="Test",
            participating_agents=["agent_055"],
            creator_agent_id="agent_055",
        )
        stats = await client.get_statistics()
        assert stats["total_contracts"] == 1


class TestIntegration:
    """Integration tests for complex workflows."""

    @pytest.mark.asyncio
    async def test_full_collaboration_workflow(self):
        """Test complete collaboration workflow with contract, tokens, and NFTs."""
        client = create_bap_client()

        # Create agents
        agent1 = await client.create_wallet("collaborator_1")
        agent2 = await client.create_wallet("collaborator_2")

        # Mint capability NFTs
        nft1 = await client.mint_capability_nft(
            agent_id="collaborator_1",
            capability_name="Strategic Planning",
            capability_category="apqc:1.0",
            proficiency_level=0.9,
        )

        nft2 = await client.mint_capability_nft(
            agent_id="collaborator_2",
            capability_name="Financial Analysis",
            capability_category="apqc:9.2",
            proficiency_level=0.85,
        )

        # Create collaboration contract
        contract = await client.create_smart_contract(
            contract_type="multi_agent_collaboration",
            contract_name="FY2026 Strategic Planning",
            participating_agents=["collaborator_1", "collaborator_2"],
            creator_agent_id="collaborator_1",
            token_allocations={
                "collaborator_1": Decimal("500"),
                "collaborator_2": Decimal("300"),
            },
        )

        # Stake reputation
        await client.stake_tokens(
            agent_id="collaborator_1",
            token_type=TokenType.REPUTATION.value,
            amount=Decimal("50"),
            stake_id=contract.contract_id,
        )

        # Execute contract
        result = await client.execute_contract(contract.contract_id)
        assert result["success"] is True

        # Verify states
        assert len(agent1.nft_holdings) == 1
        assert len(agent2.nft_holdings) == 1
        assert contract.contract_state == "completed"

    @pytest.mark.asyncio
    async def test_marketplace_workflow(self):
        """Test NFT marketplace workflow."""
        client = create_bap_client()

        # Seller creates and mints NFT
        seller = await client.create_wallet("seller_agent")
        nft = await client.mint_capability_nft(
            agent_id="seller_agent",
            capability_name="Rare Skill",
            capability_category="apqc:3.0",
            proficiency_level=0.95,
        )

        # Buyer creates wallet
        buyer = await client.create_wallet("buyer_agent")

        # Give buyer enough tokens
        buyer.token_balances[TokenType.UTILITY.value] = Decimal("5000")

        # Transfer NFT
        success = await client.transfer_nft(
            nft_id=nft.nft_id,
            from_agent="seller_agent",
            to_agent="buyer_agent"
        )

        assert success is True
        assert nft.current_owner == "buyer_agent"
        assert "seller_agent" in nft.previous_owners

    @pytest.mark.asyncio
    async def test_dao_governance_workflow(self):
        """Test DAO governance workflow."""
        client = create_bap_client()

        # Create multiple voters
        voters = []
        for i in range(5):
            wallet = await client.create_wallet(f"voter_{i}")
            wallet.token_balances[TokenType.GOVERNANCE.value] = Decimal(str(100 * (i + 1)))
            voters.append(f"voter_{i}")

        # Vote on proposal
        votes = ["yes", "yes", "no", "yes", "abstain"]
        for i, vote in enumerate(votes):
            await client.vote_on_proposal(
                agent_id=voters[i],
                proposal_id="governance_proposal_001",
                vote=vote
            )

        # Check all votes recorded
        assert client.stats["total_governance_votes"] == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
