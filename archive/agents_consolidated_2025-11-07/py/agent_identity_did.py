"""
Agent Identity System using DID (Decentralized Identifiers)

Provides blockchain-based identity management for autonomous agents,
enabling verifiable credentials, portable reputation, and cross-platform
agent authentication.

Standards:
- W3C DID Core Specification
- W3C Verifiable Credentials
- DID Method: did:agent:
- Credential Types: AgentCapability, AgentReputation, AgentCertification

Features:
- Decentralized agent identity creation
- Verifiable credential issuance
- On-chain identity verification
- Portable reputation system
- Cross-platform agent authentication
- Privacy-preserving selective disclosure
"""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid


class DIDMethod(Enum):
    """DID method identifiers"""

    AGENT = "agent"  # did:agent:
    ETH = "eth"  # did:eth: (Ethereum-based)
    KEY = "key"  # did:key: (Key-based)


class CredentialType(Enum):
    """Types of verifiable credentials"""

    CAPABILITY = "AgentCapability"
    REPUTATION = "AgentReputation"
    CERTIFICATION = "AgentCertification"
    PROTOCOL_COMPLIANCE = "ProtocolCompliance"
    TRAINING = "TrainingCredential"


class VerificationStatus(Enum):
    """Credential verification status"""

    VALID = "valid"
    EXPIRED = "expired"
    REVOKED = "revoked"
    INVALID = "invalid"


@dataclass
class DIDDocument:
    """
    W3C DID Document

    Represents the complete identity information for an agent,
    stored on-chain or in a decentralized registry.
    """

    id: str  # DID identifier (e.g., did:agent:abc123)
    context: List[str] = field(
        default_factory=lambda: ["https://www.w3.org/ns/did/v1", "https://w3id.org/security/v1"]
    )

    # Controller (who manages this DID)
    controller: Optional[str] = None

    # Verification methods (public keys for signature verification)
    verification_method: List[Dict[str, Any]] = field(default_factory=list)

    # Authentication methods
    authentication: List[str] = field(default_factory=list)

    # Service endpoints
    service: List[Dict[str, Any]] = field(default_factory=list)

    # Metadata
    created: str = field(default_factory=lambda: datetime.now().isoformat())
    updated: str = field(default_factory=lambda: datetime.now().isoformat())

    # Agent-specific metadata
    agent_type: Optional[str] = None
    agent_version: Optional[str] = None
    capabilities: List[str] = field(default_factory=list)


@dataclass
class VerifiableCredential:
    """
    W3C Verifiable Credential

    A tamper-evident credential that can be cryptographically verified,
    issued to agents to prove capabilities, reputation, or certifications.
    """

    context: List[str] = field(default_factory=lambda: ["https://www.w3.org/2018/credentials/v1"])
    id: str = field(default_factory=lambda: f"urn:uuid:{uuid.uuid4()}")
    type: List[str] = field(default_factory=lambda: ["VerifiableCredential"])

    # Issuer (who issued this credential)
    issuer: str = ""

    # When issued
    issuance_date: str = field(default_factory=lambda: datetime.now().isoformat())

    # When it expires
    expiration_date: Optional[str] = None

    # The subject (agent) this credential is about
    credential_subject: Dict[str, Any] = field(default_factory=dict)

    # Cryptographic proof
    proof: Dict[str, Any] = field(default_factory=dict)

    # Status (for revocation)
    credential_status: Optional[Dict[str, Any]] = None


@dataclass
class AgentIdentity:
    """
    Complete agent identity package

    Combines DID, credentials, and reputation into a portable identity
    that agents can use across platforms and networks.
    """

    did: str
    did_document: DIDDocument
    credentials: List[VerifiableCredential] = field(default_factory=list)

    # Reputation metrics (verifiable on-chain)
    reputation_score: float = 100.0
    total_interactions: int = 0
    successful_interactions: int = 0
    endorsements: List[str] = field(default_factory=list)

    # Platform registrations
    registered_platforms: List[str] = field(default_factory=list)

    # Activity tracking
    last_active: str = field(default_factory=lambda: datetime.now().isoformat())
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class AgentIdentitySystem:
    """
    Decentralized Identity System for Autonomous Agents

    Manages DIDs, verifiable credentials, and cross-platform identity
    for the agent ecosystem.
    """

    def __init__(self):
        # Identity registry (in production, this would be on-chain)
        self.identities: Dict[str, AgentIdentity] = {}
        self.did_to_agent_id: Dict[str, str] = {}

        # Credential registry
        self.credentials: Dict[str, VerifiableCredential] = {}

        # Issuer registry (trusted credential issuers)
        self.trusted_issuers: Dict[str, str] = {}

        # Revocation registry
        self.revoked_credentials: set = set()

        # Statistics
        self.total_identities_created = 0
        self.total_credentials_issued = 0

    # =================================================================
    # DID Management
    # =================================================================

    def create_did(
        self,
        agent_id: str,
        agent_type: str,
        agent_version: str = "1.0.0",
        capabilities: Optional[List[str]] = None,
    ) -> AgentIdentity:
        """
        Create a new DID for an agent

        In production, this would:
        - Generate keypair
        - Register DID on blockchain
        - Create DID document
        - Store in distributed registry
        """

        # Generate DID
        did = self._generate_did(agent_id)

        # Create verification method (public key)
        verification_method_id = f"{did}#keys-1"
        public_key = self._generate_public_key(agent_id)

        verification_method = {
            "id": verification_method_id,
            "type": "Ed25519VerificationKey2020",
            "controller": did,
            "publicKeyMultibase": public_key,
        }

        # Create service endpoints
        service = [
            {
                "id": f"{did}#agent-endpoint",
                "type": "AgentService",
                "serviceEndpoint": f"https://agents.example.com/api/{agent_id}",
            }
        ]

        # Create DID document
        did_document = DIDDocument(
            id=did,
            controller=did,
            verification_method=[verification_method],
            authentication=[verification_method_id],
            service=service,
            agent_type=agent_type,
            agent_version=agent_version,
            capabilities=capabilities or [],
        )

        # Create identity
        identity = AgentIdentity(did=did, did_document=did_document)

        # Register
        self.identities[agent_id] = identity
        self.did_to_agent_id[did] = agent_id
        self.total_identities_created += 1

        return identity

    def get_identity(self, agent_id: str) -> Optional[AgentIdentity]:
        """Get agent's identity"""
        return self.identities.get(agent_id)

    def resolve_did(self, did: str) -> Optional[DIDDocument]:
        """
        Resolve a DID to its DID document

        In production, this would query the blockchain or
        distributed registry.
        """
        agent_id = self.did_to_agent_id.get(did)
        if not agent_id:
            return None

        identity = self.identities.get(agent_id)
        return identity.did_document if identity else None

    # =================================================================
    # Verifiable Credentials
    # =================================================================

    def issue_credential(
        self,
        agent_id: str,
        credential_type: CredentialType,
        claims: Dict[str, Any],
        issuer_did: str = "did:agent:system",
        valid_days: int = 365,
    ) -> VerifiableCredential:
        """
        Issue a verifiable credential to an agent

        Examples:
        - Capability credential: "This agent can perform traffic prediction"
        - Reputation credential: "This agent has 98% success rate"
        - Certification: "This agent is certified for healthcare data"
        """

        identity = self.get_identity(agent_id)
        if not identity:
            raise ValueError(f"Agent {agent_id} does not have a DID")

        # Create credential
        credential_id = f"urn:uuid:{uuid.uuid4()}"
        expiration = datetime.now() + timedelta(days=valid_days)

        credential = VerifiableCredential(
            id=credential_id,
            type=["VerifiableCredential", credential_type.value],
            issuer=issuer_did,
            expiration_date=expiration.isoformat(),
            credential_subject={"id": identity.did, "type": credential_type.value, **claims},
        )

        # Generate proof (cryptographic signature)
        credential.proof = self._generate_proof(credential, issuer_did)

        # Add revocation status
        credential.credential_status = {
            "id": f"https://agents.example.com/credentials/{credential_id}/status",
            "type": "CredentialStatusList2021",
        }

        # Register
        self.credentials[credential_id] = credential
        identity.credentials.append(credential)
        self.total_credentials_issued += 1

        return credential

    def verify_credential(self, credential: VerifiableCredential) -> VerificationStatus:
        """
        Verify a credential's authenticity and validity

        In production, this would:
        - Verify cryptographic signature
        - Check issuer's DID document
        - Validate against revocation registry
        - Check expiration
        """

        # Check if revoked
        if credential.id in self.revoked_credentials:
            return VerificationStatus.REVOKED

        # Check expiration
        if credential.expiration_date:
            expiration = datetime.fromisoformat(credential.expiration_date)
            if datetime.now() > expiration:
                return VerificationStatus.EXPIRED

        # In production, verify cryptographic signature here

        return VerificationStatus.VALID

    def revoke_credential(self, credential_id: str) -> bool:
        """Revoke a credential"""
        if credential_id in self.credentials:
            self.revoked_credentials.add(credential_id)
            return True
        return False

    # =================================================================
    # Reputation Management
    # =================================================================

    def update_reputation(
        self, agent_id: str, successful: bool, endorser_did: Optional[str] = None
    ):
        """
        Update agent's reputation based on interaction

        Reputation is calculated on-chain and becomes part of
        verifiable credentials.
        """
        identity = self.get_identity(agent_id)
        if not identity:
            return

        identity.total_interactions += 1
        if successful:
            identity.successful_interactions += 1

        # Calculate reputation score (0-100)
        if identity.total_interactions > 0:
            success_rate = identity.successful_interactions / identity.total_interactions
            # Weighted by total interactions (more data = more confidence)
            confidence_factor = min(identity.total_interactions / 100, 1.0)
            identity.reputation_score = (
                success_rate * 100 * confidence_factor + (1 - confidence_factor) * 100
            )

        # Add endorsement
        if endorser_did and endorser_did not in identity.endorsements:
            identity.endorsements.append(endorser_did)

    def get_reputation_credential(self, agent_id: str) -> Optional[VerifiableCredential]:
        """
        Generate a reputation credential for an agent

        This credential can be verified by other agents/platforms
        """
        identity = self.get_identity(agent_id)
        if not identity:
            return None

        claims = {
            "reputationScore": identity.reputation_score,
            "totalInteractions": identity.total_interactions,
            "successfulInteractions": identity.successful_interactions,
            "successRate": (
                identity.successful_interactions / identity.total_interactions
                if identity.total_interactions > 0
                else 0.0
            ),
            "endorsementCount": len(identity.endorsements),
        }

        return self.issue_credential(
            agent_id=agent_id,
            credential_type=CredentialType.REPUTATION,
            claims=claims,
            valid_days=30,  # Reputation credentials expire monthly
        )

    # =================================================================
    # Cross-Platform Identity
    # =================================================================

    def register_platform(self, agent_id: str, platform_name: str):
        """Register agent's identity on a platform"""
        identity = self.get_identity(agent_id)
        if identity and platform_name not in identity.registered_platforms:
            identity.registered_platforms.append(platform_name)

    def get_portable_identity(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Export agent's portable identity

        Can be imported to other platforms/networks
        """
        identity = self.get_identity(agent_id)
        if not identity:
            return None

        return {
            "did": identity.did,
            "did_document": asdict(identity.did_document),
            "credentials": [asdict(c) for c in identity.credentials],
            "reputation": {
                "score": identity.reputation_score,
                "total_interactions": identity.total_interactions,
                "successful_interactions": identity.successful_interactions,
                "endorsements": identity.endorsements,
            },
            "platforms": identity.registered_platforms,
            "created_at": identity.created_at,
            "exported_at": datetime.now().isoformat(),
        }

    # =================================================================
    # Statistics & Queries
    # =================================================================

    def get_system_statistics(self) -> Dict[str, Any]:
        """Get identity system statistics"""
        return {
            "total_identities": len(self.identities),
            "total_credentials": len(self.credentials),
            "total_revoked": len(self.revoked_credentials),
            "trusted_issuers": len(self.trusted_issuers),
            "identities_created": self.total_identities_created,
            "credentials_issued": self.total_credentials_issued,
        }

    # =================================================================
    # Utility Methods
    # =================================================================

    def _generate_did(self, agent_id: str) -> str:
        """Generate a DID identifier"""
        # did:agent:<hash>
        hash_input = f"{agent_id}:{datetime.now().isoformat()}".encode()
        hash_result = hashlib.sha256(hash_input).hexdigest()[:32]
        return f"did:agent:{hash_result}"

    def _generate_public_key(self, agent_id: str) -> str:
        """Generate a public key (multibase encoded)"""
        # In production, generate real keypair
        hash_input = f"pubkey:{agent_id}".encode()
        hash_result = hashlib.sha256(hash_input).hexdigest()
        return f"z{hash_result}"  # z prefix for multibase

    def _generate_proof(self, credential: VerifiableCredential, issuer_did: str) -> Dict[str, Any]:
        """Generate cryptographic proof for credential"""
        # In production, use real cryptographic signature

        # Create proof hash
        proof_input = json.dumps(
            {
                "credential_id": credential.id,
                "issuer": issuer_did,
                "subject": credential.credential_subject,
                "issued": credential.issuance_date,
            },
            sort_keys=True,
        ).encode()

        signature = hashlib.sha256(proof_input).hexdigest()

        return {
            "type": "Ed25519Signature2020",
            "created": datetime.now().isoformat(),
            "verificationMethod": f"{issuer_did}#keys-1",
            "proofPurpose": "assertionMethod",
            "proofValue": f"z{signature}",
        }


# =================================================================
# Global Service Instance
# =================================================================

_identity_system: Optional[AgentIdentitySystem] = None


def get_identity_system() -> AgentIdentitySystem:
    """Get or create the global identity system instance"""
    global _identity_system
    if _identity_system is None:
        _identity_system = AgentIdentitySystem()
    return _identity_system
