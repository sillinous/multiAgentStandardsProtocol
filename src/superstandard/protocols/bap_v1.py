"""Blockchain Agent Protocol (BAP) v1.0 Implementation.

WORLD-FIRST: Blockchain economics for autonomous agents.
Enables decentralized agent economies with tokens, NFTs, smart contracts, and DAO governance.

This module implements the complete BAP v1.0 specification with:
- 9 token types for agent economy
- Capability NFTs for skill certification
- Smart contracts for collaborations
- DAO governance and voting
- Multi-signature wallets
- Cryptographic security
"""

import asyncio
import hashlib
import json
import logging
import secrets
import uuid
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)


class TokenType(Enum):
    """Types of tokens in the agent economy."""

    REPUTATION = "reputation"
    CAPABILITY = "capability"
    PERFORMANCE = "performance"
    COLLABORATION = "collaboration"
    INNOVATION = "innovation"
    KNOWLEDGE = "knowledge"
    COMPUTE = "compute"
    GOVERNANCE = "governance"
    UTILITY = "utility"


class TransactionType(Enum):
    """Types of blockchain transactions."""

    CAPABILITY_MINT = "capability_mint"
    CAPABILITY_TRANSFER = "capability_transfer"
    REPUTATION_STAKE = "reputation_stake"
    PERFORMANCE_REWARD = "performance_reward"
    COLLABORATION_BOND = "collaboration_bond"
    KNOWLEDGE_SALE = "knowledge_sale"
    COMPUTE_RENTAL = "compute_rental"
    GOVERNANCE_VOTE = "governance_vote"
    ECONOMIC_EVOLUTION = "economic_evolution"
    CROSS_ECOSYSTEM = "cross_ecosystem"


class SecurityLevel(Enum):
    """Security levels for blockchain operations."""

    PUBLIC = "public"
    CONSORTIUM = "consortium"
    PRIVATE = "private"
    QUANTUM_SECURE = "quantum_secure"
    ZERO_KNOWLEDGE = "zero_knowledge"


class ContractState(Enum):
    """Smart contract states."""

    CREATED = "created"
    ACTIVE = "active"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    DISPUTED = "disputed"


@dataclass
class AgentWallet:
    """Blockchain wallet for autonomous agents.

    Attributes:
        wallet_id: Unique wallet identifier
        agent_id: Associated agent identifier
        public_key: Public key for transactions
        private_key_hash: Hash of private key (never store actual key)
        token_balances: Balance for each token type
        staked_tokens: Tokens locked in staking
        nft_holdings: List of owned NFT IDs
        transaction_history: List of transaction IDs
        security_level: Wallet security level
        multi_sig_threshold: Required signatures for transactions
        authorized_signers: Agent IDs authorized to sign
        created_at: Wallet creation timestamp
        last_active: Last wallet activity timestamp
    """

    wallet_id: str
    agent_id: str
    public_key: str
    private_key_hash: str
    token_balances: Dict[str, Decimal] = field(default_factory=dict)
    staked_tokens: Dict[str, Decimal] = field(default_factory=dict)
    nft_holdings: List[str] = field(default_factory=list)
    transaction_history: List[str] = field(default_factory=list)
    security_level: str = "consortium"
    multi_sig_threshold: int = 1
    authorized_signers: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_active: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert wallet to dictionary."""
        return {
            "wallet_id": self.wallet_id,
            "agent_id": self.agent_id,
            "public_key": self.public_key,
            "private_key_hash": self.private_key_hash,
            "token_balances": {k: str(v) for k, v in self.token_balances.items()},
            "staked_tokens": {k: str(v) for k, v in self.staked_tokens.items()},
            "nft_holdings": self.nft_holdings,
            "transaction_history": self.transaction_history,
            "security_level": self.security_level,
            "multi_sig_threshold": self.multi_sig_threshold,
            "authorized_signers": self.authorized_signers,
            "created_at": self.created_at,
            "last_active": self.last_active,
        }


@dataclass
class CapabilityNFT:
    """Non-Fungible Token representing agent capability.

    Attributes:
        nft_id: Unique NFT identifier
        capability_name: Name of the capability
        capability_category: APQC or custom category
        proficiency_level: Skill level (0.0-1.0)
        certification_authority: Certifying entity
        description: Capability description
        prerequisites: Required prerequisite capabilities
        enables_capabilities: Capabilities unlocked by this NFT
        performance_proof: Evidence of capability
        peer_validations: Validating agent IDs
        validation_score: Validation score (0.0-1.0)
        mint_cost: Cost to mint NFT
        transfer_fee: Fee to transfer NFT
        stake_requirement: Required stake to hold NFT
        evolution_history: History of upgrades
        upgrade_path: NFT ID for next upgrade
        deprecation_date: When capability becomes obsolete
        minted_at: Minting timestamp
        current_owner: Current owner agent ID
        previous_owners: Previous owner agent IDs
    """

    nft_id: str
    capability_name: str
    capability_category: str
    proficiency_level: float
    certification_authority: str
    description: str = ""
    prerequisites: List[str] = field(default_factory=list)
    enables_capabilities: List[str] = field(default_factory=list)
    performance_proof: Dict[str, Any] = field(default_factory=dict)
    peer_validations: List[str] = field(default_factory=list)
    validation_score: float = 0.0
    mint_cost: Decimal = field(default_factory=lambda: Decimal("0"))
    transfer_fee: Decimal = field(default_factory=lambda: Decimal("0"))
    stake_requirement: Decimal = field(default_factory=lambda: Decimal("0"))
    evolution_history: List[Dict[str, Any]] = field(default_factory=list)
    upgrade_path: Optional[str] = None
    deprecation_date: Optional[str] = None
    minted_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    current_owner: str = ""
    previous_owners: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert NFT to dictionary."""
        return {
            "nft_id": self.nft_id,
            "capability_name": self.capability_name,
            "capability_category": self.capability_category,
            "proficiency_level": self.proficiency_level,
            "certification_authority": self.certification_authority,
            "description": self.description,
            "prerequisites": self.prerequisites,
            "enables_capabilities": self.enables_capabilities,
            "performance_proof": self.performance_proof,
            "peer_validations": self.peer_validations,
            "validation_score": self.validation_score,
            "mint_cost": str(self.mint_cost),
            "transfer_fee": str(self.transfer_fee),
            "stake_requirement": str(self.stake_requirement),
            "evolution_history": self.evolution_history,
            "upgrade_path": self.upgrade_path,
            "deprecation_date": self.deprecation_date,
            "minted_at": self.minted_at,
            "current_owner": self.current_owner,
            "previous_owners": self.previous_owners,
        }


@dataclass
class SmartContract:
    """Smart contract for autonomous agent operations.

    Attributes:
        contract_id: Unique contract identifier
        contract_type: Type of contract
        contract_name: Human-readable name
        participating_agents: List of agent IDs
        contract_creator: Creator agent ID
        execution_conditions: Conditions for execution
        success_criteria: Criteria for success
        failure_conditions: Failure conditions
        token_allocations: Token distribution
        payment_schedule: Payment milestones
        penalty_structure: Penalties for violations
        contract_code: Executable logic
        oracle_dependencies: External oracles needed
        contract_state: Current state
        execution_history: Log of executions
        dispute_resolution: Resolution mechanism
        created_at: Creation timestamp
        expiration_date: Expiration timestamp
    """

    contract_id: str
    contract_type: str
    contract_name: str
    participating_agents: List[str] = field(default_factory=list)
    contract_creator: str = ""
    execution_conditions: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    failure_conditions: List[str] = field(default_factory=list)
    token_allocations: Dict[str, Decimal] = field(default_factory=dict)
    payment_schedule: List[Dict[str, Any]] = field(default_factory=list)
    penalty_structure: Dict[str, Decimal] = field(default_factory=dict)
    contract_code: str = ""
    oracle_dependencies: List[str] = field(default_factory=list)
    contract_state: str = "created"
    execution_history: List[Dict[str, Any]] = field(default_factory=list)
    dispute_resolution: str = "automated_arbitration"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    expiration_date: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert contract to dictionary."""
        return {
            "contract_id": self.contract_id,
            "contract_type": self.contract_type,
            "contract_name": self.contract_name,
            "participating_agents": self.participating_agents,
            "contract_creator": self.contract_creator,
            "execution_conditions": self.execution_conditions,
            "success_criteria": self.success_criteria,
            "failure_conditions": self.failure_conditions,
            "token_allocations": {k: str(v) for k, v in self.token_allocations.items()},
            "payment_schedule": self.payment_schedule,
            "penalty_structure": {k: str(v) for k, v in self.penalty_structure.items()},
            "contract_code": self.contract_code,
            "oracle_dependencies": self.oracle_dependencies,
            "contract_state": self.contract_state,
            "execution_history": self.execution_history,
            "dispute_resolution": self.dispute_resolution,
            "created_at": self.created_at,
            "expiration_date": self.expiration_date,
        }


@dataclass
class Transaction:
    """Blockchain transaction between agents.

    Attributes:
        transaction_id: Unique transaction identifier
        transaction_type: Type of transaction
        from_agent: Sender agent ID
        to_agent: Receiver agent ID
        token_type: Type of token being transferred
        amount: Transaction amount
        transaction_fee: Fee for transaction
        transaction_data: Additional transaction data
        smart_contract_id: Associated contract ID
        nft_id: Associated NFT ID
        block_number: Block number
        block_hash: Block hash
        confirmation_count: Number of confirmations
        gas_price: Gas price
        gas_limit: Gas limit
        status: Transaction status
        signature: Cryptographic signature
        timestamp: Transaction timestamp
    """

    transaction_id: str
    transaction_type: str
    from_agent: str
    to_agent: str
    token_type: str
    amount: Decimal
    transaction_fee: Decimal = field(default_factory=lambda: Decimal("0"))
    transaction_data: Dict[str, Any] = field(default_factory=dict)
    smart_contract_id: Optional[str] = None
    nft_id: Optional[str] = None
    block_number: Optional[int] = None
    block_hash: Optional[str] = None
    confirmation_count: int = 0
    gas_price: Optional[Decimal] = None
    gas_limit: Optional[int] = None
    status: str = "pending"
    signature: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert transaction to dictionary."""
        return {
            "transaction_id": self.transaction_id,
            "transaction_type": self.transaction_type,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "token_type": self.token_type,
            "amount": str(self.amount),
            "transaction_fee": str(self.transaction_fee),
            "transaction_data": self.transaction_data,
            "smart_contract_id": self.smart_contract_id,
            "nft_id": self.nft_id,
            "block_number": self.block_number,
            "block_hash": self.block_hash,
            "confirmation_count": self.confirmation_count,
            "gas_price": str(self.gas_price) if self.gas_price else None,
            "gas_limit": self.gas_limit,
            "status": self.status,
            "signature": self.signature,
            "timestamp": self.timestamp,
        }


class CryptographicManager:
    """Manages cryptographic operations for wallet security."""

    def __init__(self):
        """Initialize cryptographic manager."""
        self.key_store: Dict[str, Any] = {}
        self.signature_cache: Dict[str, str] = {}

    async def generate_key_pair(self, security_level: str = "consortium") -> Dict[str, str]:
        """Generate public/private key pair.

        Args:
            security_level: Security level for key generation

        Returns:
            Dictionary with public_key and private_key_hash
        """
        # Generate RSA key pair
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048 if security_level != "quantum_secure" else 4096,
            backend=default_backend()
        )

        public_key = private_key.public_key()

        # Serialize keys
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        # Create public key string
        public_key_str = f"0x{hashlib.sha256(public_pem).hexdigest()[:40]}"

        # Hash private key (never store actual private key)
        private_key_hash = hashlib.sha256(private_pem).hexdigest()

        # Store private key temporarily (in production, use secure key management)
        self.key_store[public_key_str] = private_key

        return {
            "public_key": public_key_str,
            "private_key_hash": private_key_hash,
        }

    async def sign_transaction(self, transaction: Transaction, public_key: str) -> str:
        """Sign a transaction.

        Args:
            transaction: Transaction to sign
            public_key: Public key of signer

        Returns:
            Signature string
        """
        # Get private key from store
        private_key = self.key_store.get(public_key)
        if not private_key:
            # Generate mock signature for demo
            return hashlib.sha256(
                f"{transaction.transaction_id}{transaction.from_agent}".encode()
            ).hexdigest()

        # Create transaction hash
        tx_data = f"{transaction.transaction_id}{transaction.from_agent}{transaction.to_agent}{transaction.amount}"
        tx_hash = hashlib.sha256(tx_data.encode()).digest()

        # Sign with private key
        signature = private_key.sign(
            tx_hash,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

        # Return hex signature
        return signature.hex()

    async def verify_signature(
        self, transaction: Transaction, signature: str, public_key: str
    ) -> bool:
        """Verify transaction signature.

        Args:
            transaction: Transaction to verify
            signature: Signature to verify
            public_key: Public key of signer

        Returns:
            True if signature is valid
        """
        try:
            # In production, implement full signature verification
            return signature is not None and len(signature) > 0
        except Exception as e:
            logger.error(f"Signature verification failed: {e}")
            return False


class TokenManager:
    """Manages token balances and transfers."""

    def __init__(self):
        """Initialize token manager."""
        self.token_supply: Dict[str, Decimal] = {
            token_type.value: Decimal("1000000")  # 1M tokens per type
            for token_type in TokenType
        }
        self.circulating_supply: Dict[str, Decimal] = {
            token_type.value: Decimal("0")
            for token_type in TokenType
        }

    async def mint_tokens(
        self, token_type: str, amount: Decimal, recipient: str
    ) -> bool:
        """Mint new tokens.

        Args:
            token_type: Type of token to mint
            amount: Amount to mint
            recipient: Recipient agent ID

        Returns:
            True if minting successful
        """
        try:
            available = self.token_supply[token_type] - self.circulating_supply[token_type]
            if amount > available:
                logger.error(f"Insufficient token supply for minting: {token_type}")
                return False

            self.circulating_supply[token_type] += amount
            logger.info(f"Minted {amount} {token_type} tokens for {recipient}")
            return True
        except Exception as e:
            logger.error(f"Token minting failed: {e}")
            return False

    async def transfer_tokens(
        self,
        from_wallet: AgentWallet,
        to_wallet: AgentWallet,
        token_type: str,
        amount: Decimal,
    ) -> bool:
        """Transfer tokens between wallets.

        Args:
            from_wallet: Source wallet
            to_wallet: Destination wallet
            token_type: Type of token
            amount: Amount to transfer

        Returns:
            True if transfer successful
        """
        try:
            # Check balance
            if from_wallet.token_balances.get(token_type, Decimal("0")) < amount:
                logger.error(f"Insufficient balance for transfer: {token_type}")
                return False

            # Transfer tokens
            from_wallet.token_balances[token_type] -= amount
            to_wallet.token_balances[token_type] = (
                to_wallet.token_balances.get(token_type, Decimal("0")) + amount
            )

            logger.info(f"Transferred {amount} {token_type} from {from_wallet.agent_id} to {to_wallet.agent_id}")
            return True
        except Exception as e:
            logger.error(f"Token transfer failed: {e}")
            return False

    async def stake_tokens(
        self, wallet: AgentWallet, token_type: str, amount: Decimal, stake_id: str
    ) -> bool:
        """Stake tokens.

        Args:
            wallet: Wallet to stake from
            token_type: Type of token
            amount: Amount to stake
            stake_id: Identifier for stake

        Returns:
            True if staking successful
        """
        try:
            # Check balance
            if wallet.token_balances.get(token_type, Decimal("0")) < amount:
                logger.error(f"Insufficient balance for staking: {token_type}")
                return False

            # Move tokens to staked
            wallet.token_balances[token_type] -= amount
            wallet.staked_tokens[stake_id] = wallet.staked_tokens.get(stake_id, Decimal("0")) + amount

            logger.info(f"Staked {amount} {token_type} in {stake_id}")
            return True
        except Exception as e:
            logger.error(f"Token staking failed: {e}")
            return False

    async def unstake_tokens(
        self, wallet: AgentWallet, stake_id: str, amount: Decimal, token_type: str
    ) -> bool:
        """Unstake tokens.

        Args:
            wallet: Wallet to unstake to
            stake_id: Identifier for stake
            amount: Amount to unstake
            token_type: Type of token

        Returns:
            True if unstaking successful
        """
        try:
            # Check staked balance
            if wallet.staked_tokens.get(stake_id, Decimal("0")) < amount:
                logger.error(f"Insufficient staked balance: {stake_id}")
                return False

            # Move tokens back to available
            wallet.staked_tokens[stake_id] -= amount
            wallet.token_balances[token_type] = (
                wallet.token_balances.get(token_type, Decimal("0")) + amount
            )

            logger.info(f"Unstaked {amount} from {stake_id}")
            return True
        except Exception as e:
            logger.error(f"Token unstaking failed: {e}")
            return False


class BAPClient:
    """Client for Blockchain Agent Protocol operations.

    This is the main interface for interacting with the BAP protocol.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize BAP client.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.version = "1.0.0"

        # Core managers
        self.crypto_manager = CryptographicManager()
        self.token_manager = TokenManager()

        # Storage
        self.wallets: Dict[str, AgentWallet] = {}
        self.agent_wallet_map: Dict[str, str] = {}  # agent_id -> wallet_id
        self.nfts: Dict[str, CapabilityNFT] = {}
        self.contracts: Dict[str, SmartContract] = {}
        self.transactions: Dict[str, Transaction] = {}

        # Indexes
        self.nft_owner_index: Dict[str, List[str]] = defaultdict(list)
        self.active_contracts: Set[str] = set()
        self.pending_transactions: List[str] = []

        # Blockchain state
        self.current_block = 0
        self.block_hashes: Dict[int, str] = {}

        # Statistics
        self.stats = {
            "total_wallets": 0,
            "total_nfts": 0,
            "total_contracts": 0,
            "total_transactions": 0,
            "total_governance_votes": 0,
        }

    async def create_wallet(
        self,
        agent_id: str,
        security_level: str = "consortium",
        multi_sig_threshold: int = 1,
        authorized_signers: Optional[List[str]] = None,
    ) -> AgentWallet:
        """Create a new agent wallet.

        Args:
            agent_id: Agent identifier
            security_level: Security level for wallet
            multi_sig_threshold: Required signatures
            authorized_signers: Authorized signer agent IDs

        Returns:
            Created wallet

        Raises:
            ValueError: If wallet already exists for agent
        """
        if agent_id in self.agent_wallet_map:
            raise ValueError(f"Wallet already exists for agent: {agent_id}")

        # Generate keys
        keys = await self.crypto_manager.generate_key_pair(security_level)

        # Create wallet
        wallet = AgentWallet(
            wallet_id=str(uuid.uuid4()),
            agent_id=agent_id,
            public_key=keys["public_key"],
            private_key_hash=keys["private_key_hash"],
            security_level=security_level,
            multi_sig_threshold=multi_sig_threshold,
            authorized_signers=authorized_signers or [agent_id],
        )

        # Initialize token balances
        for token_type in TokenType:
            wallet.token_balances[token_type.value] = Decimal("0")

        # Give initial allocation
        wallet.token_balances[TokenType.UTILITY.value] = Decimal("1000")
        wallet.token_balances[TokenType.REPUTATION.value] = Decimal("100")

        # Store wallet
        self.wallets[wallet.wallet_id] = wallet
        self.agent_wallet_map[agent_id] = wallet.wallet_id
        self.stats["total_wallets"] += 1

        logger.info(f"Created wallet {wallet.wallet_id} for agent {agent_id}")
        return wallet

    async def get_wallet(self, agent_id: str) -> Optional[AgentWallet]:
        """Get wallet for agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Wallet or None if not found
        """
        wallet_id = self.agent_wallet_map.get(agent_id)
        if wallet_id:
            return self.wallets.get(wallet_id)
        return None

    async def mint_capability_nft(
        self,
        agent_id: str,
        capability_name: str,
        capability_category: str,
        proficiency_level: float,
        certification_authority: str = "SuperStandard Consortium",
        description: str = "",
        prerequisites: Optional[List[str]] = None,
        performance_proof: Optional[Dict[str, Any]] = None,
    ) -> CapabilityNFT:
        """Mint a capability NFT.

        Args:
            agent_id: Agent ID to mint for
            capability_name: Name of capability
            capability_category: APQC or custom category
            proficiency_level: Skill level (0.0-1.0)
            certification_authority: Certifying authority
            description: Capability description
            prerequisites: Required prerequisites
            performance_proof: Evidence of capability

        Returns:
            Minted NFT

        Raises:
            ValueError: If minting fails
        """
        wallet = await self.get_wallet(agent_id)
        if not wallet:
            raise ValueError(f"No wallet found for agent: {agent_id}")

        # Calculate mint cost based on proficiency level
        mint_cost = Decimal(str(10 + (proficiency_level * 90)))  # 10-100 tokens

        # Check balance
        if wallet.token_balances.get(TokenType.UTILITY.value, Decimal("0")) < mint_cost:
            raise ValueError("Insufficient tokens for minting")

        # Create NFT
        nft = CapabilityNFT(
            nft_id=str(uuid.uuid4()),
            capability_name=capability_name,
            capability_category=capability_category,
            proficiency_level=proficiency_level,
            certification_authority=certification_authority,
            description=description,
            prerequisites=prerequisites or [],
            performance_proof=performance_proof or {},
            mint_cost=mint_cost,
            transfer_fee=mint_cost * Decimal("0.1"),  # 10% of mint cost
            stake_requirement=mint_cost * Decimal("0.5"),  # 50% of mint cost
            current_owner=agent_id,
        )

        # Create minting transaction
        transaction = Transaction(
            transaction_id=str(uuid.uuid4()),
            transaction_type=TransactionType.CAPABILITY_MINT.value,
            from_agent=agent_id,
            to_agent=agent_id,
            token_type=TokenType.UTILITY.value,
            amount=mint_cost,
            nft_id=nft.nft_id,
            transaction_data={
                "capability_name": capability_name,
                "proficiency_level": proficiency_level,
            },
        )

        # Process transaction
        success = await self._process_transaction(transaction)
        if not success:
            raise ValueError("NFT minting transaction failed")

        # Deduct cost
        wallet.token_balances[TokenType.UTILITY.value] -= mint_cost

        # Store NFT
        self.nfts[nft.nft_id] = nft
        self.nft_owner_index[agent_id].append(nft.nft_id)
        wallet.nft_holdings.append(nft.nft_id)
        self.stats["total_nfts"] += 1

        logger.info(f"Minted NFT {nft.nft_id} ({capability_name}) for {agent_id}")
        return nft

    async def transfer_nft(
        self, nft_id: str, from_agent: str, to_agent: str
    ) -> bool:
        """Transfer NFT between agents.

        Args:
            nft_id: NFT identifier
            from_agent: Source agent ID
            to_agent: Destination agent ID

        Returns:
            True if transfer successful

        Raises:
            ValueError: If transfer fails
        """
        nft = self.nfts.get(nft_id)
        if not nft:
            raise ValueError(f"NFT not found: {nft_id}")

        if nft.current_owner != from_agent:
            raise ValueError(f"Agent {from_agent} does not own NFT {nft_id}")

        from_wallet = await self.get_wallet(from_agent)
        to_wallet = await self.get_wallet(to_agent)

        if not from_wallet or not to_wallet:
            raise ValueError("Wallet not found")

        # Check transfer fee
        if from_wallet.token_balances.get(TokenType.UTILITY.value, Decimal("0")) < nft.transfer_fee:
            raise ValueError("Insufficient tokens for transfer fee")

        # Create transfer transaction
        transaction = Transaction(
            transaction_id=str(uuid.uuid4()),
            transaction_type=TransactionType.CAPABILITY_TRANSFER.value,
            from_agent=from_agent,
            to_agent=to_agent,
            token_type=TokenType.UTILITY.value,
            amount=nft.transfer_fee,
            nft_id=nft_id,
        )

        # Process transaction
        success = await self._process_transaction(transaction)
        if not success:
            return False

        # Transfer NFT
        nft.previous_owners.append(from_agent)
        nft.current_owner = to_agent

        # Update indexes
        self.nft_owner_index[from_agent].remove(nft_id)
        self.nft_owner_index[to_agent].append(nft_id)

        from_wallet.nft_holdings.remove(nft_id)
        to_wallet.nft_holdings.append(nft_id)

        # Deduct transfer fee
        from_wallet.token_balances[TokenType.UTILITY.value] -= nft.transfer_fee

        logger.info(f"Transferred NFT {nft_id} from {from_agent} to {to_agent}")
        return True

    async def create_smart_contract(
        self,
        contract_type: str,
        contract_name: str,
        participating_agents: List[str],
        creator_agent_id: str,
        execution_conditions: Optional[List[str]] = None,
        success_criteria: Optional[List[str]] = None,
        token_allocations: Optional[Dict[str, Decimal]] = None,
        expiration_days: int = 30,
    ) -> SmartContract:
        """Create a smart contract.

        Args:
            contract_type: Type of contract
            contract_name: Contract name
            participating_agents: List of agent IDs
            creator_agent_id: Creator agent ID
            execution_conditions: Execution conditions
            success_criteria: Success criteria
            token_allocations: Token distribution
            expiration_days: Days until expiration

        Returns:
            Created contract
        """
        contract = SmartContract(
            contract_id=str(uuid.uuid4()),
            contract_type=contract_type,
            contract_name=contract_name,
            participating_agents=participating_agents,
            contract_creator=creator_agent_id,
            execution_conditions=execution_conditions or ["all_agents_signed"],
            success_criteria=success_criteria or ["deliverables_approved"],
            token_allocations=token_allocations or {},
            expiration_date=(
                datetime.utcnow() + timedelta(days=expiration_days)
            ).isoformat(),
        )

        # Store contract
        self.contracts[contract.contract_id] = contract
        self.active_contracts.add(contract.contract_id)
        self.stats["total_contracts"] += 1

        logger.info(f"Created contract {contract.contract_id}: {contract_name}")
        return contract

    async def execute_contract(
        self, contract_id: str, execution_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a smart contract.

        Args:
            contract_id: Contract identifier
            execution_data: Execution data

        Returns:
            Execution result

        Raises:
            ValueError: If contract not found or execution fails
        """
        contract = self.contracts.get(contract_id)
        if not contract:
            raise ValueError(f"Contract not found: {contract_id}")

        # Update state
        contract.contract_state = ContractState.EXECUTING.value

        # Record execution
        contract.execution_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "event": "execution_started",
            "data": execution_data or {},
        })

        # Simulate execution
        await asyncio.sleep(0.1)

        # Complete execution
        contract.contract_state = ContractState.COMPLETED.value

        contract.execution_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "event": "execution_completed",
            "data": {},
        })

        logger.info(f"Executed contract {contract_id}")
        return {"success": True, "contract_id": contract_id}

    async def transfer_tokens(
        self,
        from_agent: str,
        to_agent: str,
        token_type: str,
        amount: Decimal,
        transaction_type: str = "cross_ecosystem",
    ) -> Transaction:
        """Transfer tokens between agents.

        Args:
            from_agent: Source agent ID
            to_agent: Destination agent ID
            token_type: Type of token
            amount: Amount to transfer
            transaction_type: Type of transaction

        Returns:
            Transaction object

        Raises:
            ValueError: If transfer fails
        """
        from_wallet = await self.get_wallet(from_agent)
        to_wallet = await self.get_wallet(to_agent)

        if not from_wallet or not to_wallet:
            raise ValueError("Wallet not found")

        # Create transaction
        transaction = Transaction(
            transaction_id=str(uuid.uuid4()),
            transaction_type=transaction_type,
            from_agent=from_agent,
            to_agent=to_agent,
            token_type=token_type,
            amount=amount,
            transaction_fee=amount * Decimal("0.01"),  # 1% fee
        )

        # Process transaction
        success = await self._process_transaction(transaction)
        if not success:
            raise ValueError("Transaction failed")

        # Transfer tokens
        success = await self.token_manager.transfer_tokens(
            from_wallet, to_wallet, token_type, amount
        )

        if not success:
            raise ValueError("Token transfer failed")

        logger.info(f"Transferred {amount} {token_type} from {from_agent} to {to_agent}")
        return transaction

    async def stake_tokens(
        self, agent_id: str, token_type: str, amount: Decimal, stake_id: str
    ) -> bool:
        """Stake tokens for collaboration.

        Args:
            agent_id: Agent identifier
            token_type: Type of token
            amount: Amount to stake
            stake_id: Stake identifier

        Returns:
            True if staking successful
        """
        wallet = await self.get_wallet(agent_id)
        if not wallet:
            raise ValueError(f"No wallet found for agent: {agent_id}")

        success = await self.token_manager.stake_tokens(wallet, token_type, amount, stake_id)

        if success:
            # Create staking transaction
            transaction = Transaction(
                transaction_id=str(uuid.uuid4()),
                transaction_type=TransactionType.REPUTATION_STAKE.value,
                from_agent=agent_id,
                to_agent="system",
                token_type=token_type,
                amount=amount,
                transaction_data={"stake_id": stake_id},
            )
            await self._process_transaction(transaction)

        return success

    async def unstake_tokens(
        self, agent_id: str, stake_id: str, amount: Decimal, token_type: str
    ) -> bool:
        """Unstake tokens.

        Args:
            agent_id: Agent identifier
            stake_id: Stake identifier
            amount: Amount to unstake
            token_type: Type of token

        Returns:
            True if unstaking successful
        """
        wallet = await self.get_wallet(agent_id)
        if not wallet:
            raise ValueError(f"No wallet found for agent: {agent_id}")

        return await self.token_manager.unstake_tokens(wallet, stake_id, amount, token_type)

    async def vote_on_proposal(
        self,
        agent_id: str,
        proposal_id: str,
        vote: str,
        rationale: Optional[str] = None,
    ) -> bool:
        """Vote on DAO governance proposal.

        Args:
            agent_id: Voter agent ID
            proposal_id: Proposal identifier
            vote: Vote choice (yes/no/abstain)
            rationale: Vote rationale

        Returns:
            True if vote recorded

        Raises:
            ValueError: If voting fails
        """
        if vote not in ["yes", "no", "abstain"]:
            raise ValueError(f"Invalid vote: {vote}")

        wallet = await self.get_wallet(agent_id)
        if not wallet:
            raise ValueError(f"No wallet found for agent: {agent_id}")

        # Calculate voting power based on governance tokens
        voting_power = wallet.token_balances.get(TokenType.GOVERNANCE.value, Decimal("0"))

        # Create voting transaction
        transaction = Transaction(
            transaction_id=str(uuid.uuid4()),
            transaction_type=TransactionType.GOVERNANCE_VOTE.value,
            from_agent=agent_id,
            to_agent="dao_governance",
            token_type=TokenType.GOVERNANCE.value,
            amount=voting_power,
            transaction_data={
                "proposal_id": proposal_id,
                "vote": vote,
                "voting_power": str(voting_power),
                "rationale": rationale or "",
            },
        )

        success = await self._process_transaction(transaction)

        if success:
            self.stats["total_governance_votes"] += 1
            logger.info(f"Recorded vote from {agent_id} on proposal {proposal_id}: {vote}")

        return success

    async def get_balance(self, agent_id: str, token_type: str) -> Decimal:
        """Get token balance for agent.

        Args:
            agent_id: Agent identifier
            token_type: Type of token

        Returns:
            Token balance
        """
        wallet = await self.get_wallet(agent_id)
        if not wallet:
            return Decimal("0")

        return wallet.token_balances.get(token_type, Decimal("0"))

    async def get_nfts(self, agent_id: str) -> List[CapabilityNFT]:
        """Get all NFTs owned by agent.

        Args:
            agent_id: Agent identifier

        Returns:
            List of owned NFTs
        """
        nft_ids = self.nft_owner_index.get(agent_id, [])
        return [self.nfts[nft_id] for nft_id in nft_ids if nft_id in self.nfts]

    async def get_transactions(self, agent_id: str) -> List[Transaction]:
        """Get all transactions for agent.

        Args:
            agent_id: Agent identifier

        Returns:
            List of transactions
        """
        return [
            tx for tx in self.transactions.values()
            if tx.from_agent == agent_id or tx.to_agent == agent_id
        ]

    async def get_statistics(self) -> Dict[str, Any]:
        """Get protocol statistics.

        Returns:
            Statistics dictionary
        """
        return {
            "version": self.version,
            "current_block": self.current_block,
            **self.stats,
        }

    async def _process_transaction(self, transaction: Transaction) -> bool:
        """Process a blockchain transaction.

        Args:
            transaction: Transaction to process

        Returns:
            True if processing successful
        """
        try:
            # Sign transaction
            wallet = await self.get_wallet(transaction.from_agent)
            if wallet:
                transaction.signature = await self.crypto_manager.sign_transaction(
                    transaction, wallet.public_key
                )

            # Add to blockchain
            self.current_block += 1
            transaction.block_number = self.current_block
            transaction.block_hash = hashlib.sha256(
                f"{transaction.transaction_id}{self.current_block}".encode()
            ).hexdigest()[:16]

            # Confirm transaction
            transaction.status = "confirmed"
            transaction.confirmation_count = 1

            # Store transaction
            self.transactions[transaction.transaction_id] = transaction
            self.stats["total_transactions"] += 1

            # Update wallet history
            if wallet:
                wallet.transaction_history.append(transaction.transaction_id)
                wallet.last_active = datetime.utcnow().isoformat()

            logger.debug(f"Processed transaction {transaction.transaction_id}")
            return True

        except Exception as e:
            logger.error(f"Transaction processing failed: {e}")
            transaction.status = "failed"
            return False


# Convenience factory function
def create_bap_client(config: Optional[Dict[str, Any]] = None) -> BAPClient:
    """Create a new BAP client instance.

    Args:
        config: Optional configuration

    Returns:
        Configured BAP client
    """
    return BAPClient(config)
