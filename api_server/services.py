"""
Real Implementation Services
============================

Actual business logic implementations for the platform.
These replace the in-memory mock stores with real database operations
and external service integrations.
"""

import os
import hashlib
import hmac
import secrets
import httpx
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from api_server.database import (
    Organization, User, Team, TeamMember,
    APIKey, Webhook, WebhookDelivery,
    AIConversation, AIMessage,
    SessionLocal
)


# ============================================================================
# Password Hashing (using hashlib for simplicity, use bcrypt in production)
# ============================================================================

def hash_password(password: str) -> str:
    """Hash a password using SHA-256 with salt"""
    salt = secrets.token_hex(16)
    hash_obj = hashlib.sha256((salt + password).encode())
    return f"{salt}${hash_obj.hexdigest()}"


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash"""
    try:
        salt, hash_value = password_hash.split("$")
        hash_obj = hashlib.sha256((salt + password).encode())
        return hash_obj.hexdigest() == hash_value
    except:
        return False


# ============================================================================
# Organization Service
# ============================================================================

class OrganizationService:
    """Real database operations for organizations"""

    @staticmethod
    def create(db: Session, name: str, slug: str, plan: str = "free") -> Organization:
        """Create a new organization"""
        org = Organization(
            org_id=f"org_{secrets.token_hex(8)}",
            name=name,
            slug=slug.lower().replace(" ", "-"),
            plan=plan,
            status="active"
        )
        db.add(org)
        db.commit()
        db.refresh(org)
        return org

    @staticmethod
    def get_by_id(db: Session, org_id: str) -> Optional[Organization]:
        """Get organization by ID"""
        return db.query(Organization).filter(Organization.org_id == org_id).first()

    @staticmethod
    def get_by_slug(db: Session, slug: str) -> Optional[Organization]:
        """Get organization by slug"""
        return db.query(Organization).filter(Organization.slug == slug).first()

    @staticmethod
    def list_all(db: Session, skip: int = 0, limit: int = 100) -> List[Organization]:
        """List all organizations"""
        return db.query(Organization).offset(skip).limit(limit).all()

    @staticmethod
    def update(db: Session, org: Organization, **kwargs) -> Organization:
        """Update organization"""
        for key, value in kwargs.items():
            if hasattr(org, key):
                setattr(org, key, value)
        org.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(org)
        return org

    @staticmethod
    def increment_api_calls(db: Session, org: Organization) -> None:
        """Increment API call counter"""
        org.current_api_calls += 1
        db.commit()


# ============================================================================
# User Service
# ============================================================================

class UserService:
    """Real database operations for users"""

    @staticmethod
    def create(db: Session, email: str, password: str, organization_id: int = None,
               first_name: str = None, last_name: str = None, role: str = "member") -> User:
        """Create a new user"""
        user = User(
            user_id=f"user_{secrets.token_hex(8)}",
            email=email.lower(),
            username=email.split("@")[0],
            password_hash=hash_password(password),
            first_name=first_name,
            last_name=last_name,
            display_name=f"{first_name or ''} {last_name or ''}".strip() or email.split("@")[0],
            organization_id=organization_id,
            role=role,
            status="active"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def get_by_id(db: Session, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.user_id == user_id).first()

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return db.query(User).filter(User.email == email.lower()).first()

    @staticmethod
    def authenticate(db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate user by email and password"""
        user = UserService.get_by_email(db, email)
        if user and verify_password(password, user.password_hash):
            user.last_login = datetime.utcnow()
            db.commit()
            return user
        return None

    @staticmethod
    def list_by_organization(db: Session, organization_id: int) -> List[User]:
        """List users in an organization"""
        return db.query(User).filter(User.organization_id == organization_id).all()

    @staticmethod
    def list_all(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """List all users"""
        return db.query(User).offset(skip).limit(limit).all()

    @staticmethod
    def update(db: Session, user: User, **kwargs) -> User:
        """Update user"""
        # Don't allow updating password_hash directly
        kwargs.pop('password_hash', None)
        kwargs.pop('password', None)

        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_password(db: Session, user: User, new_password: str) -> User:
        """Update user password"""
        user.password_hash = hash_password(new_password)
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def delete(db: Session, user_id: str) -> bool:
        """Delete user (soft delete by setting status to deleted)"""
        user = UserService.get_by_id(db, user_id)
        if user:
            user.status = "deleted"
            user.updated_at = datetime.utcnow()
            db.commit()
            return True
        return False


# ============================================================================
# Organization Service Extensions
# ============================================================================

class OrganizationServiceExtensions:
    """Additional organization operations"""

    @staticmethod
    def delete(db: Session, org_id: str) -> bool:
        """Delete organization (soft delete)"""
        org = OrganizationService.get_by_id(db, org_id)
        if org:
            org.status = "deleted"
            org.updated_at = datetime.utcnow()
            db.commit()
            return True
        return False


# ============================================================================
# Team Service
# ============================================================================

class TeamService:
    """Real database operations for teams"""

    @staticmethod
    def create(db: Session, organization_id: int, name: str, description: str = None) -> Team:
        """Create a new team"""
        team = Team(
            team_id=f"team_{secrets.token_hex(8)}",
            name=name,
            description=description,
            organization_id=organization_id,
            status="active"
        )
        db.add(team)
        db.commit()
        db.refresh(team)
        return team

    @staticmethod
    def get_by_id(db: Session, team_id: str) -> Optional[Team]:
        """Get team by ID"""
        return db.query(Team).filter(Team.team_id == team_id).first()

    @staticmethod
    def list_by_organization(db: Session, organization_id: int) -> List[Team]:
        """List teams in an organization"""
        return db.query(Team).filter(Team.organization_id == organization_id).all()

    @staticmethod
    def update(db: Session, team: Team, **kwargs) -> Team:
        """Update team"""
        for key, value in kwargs.items():
            if hasattr(team, key):
                setattr(team, key, value)
        team.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(team)
        return team

    @staticmethod
    def delete(db: Session, team_id: str) -> bool:
        """Delete team (soft delete)"""
        team = TeamService.get_by_id(db, team_id)
        if team:
            team.status = "deleted"
            team.updated_at = datetime.utcnow()
            db.commit()
            return True
        return False

    @staticmethod
    def add_member(db: Session, team_id: int, user_id: int, role: str = "member") -> TeamMember:
        """Add a member to a team"""
        member = TeamMember(
            team_id=team_id,
            user_id=user_id,
            role=role
        )
        db.add(member)
        db.commit()
        db.refresh(member)
        return member

    @staticmethod
    def remove_member(db: Session, team_id: int, user_id: int) -> bool:
        """Remove a member from a team"""
        member = db.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id
        ).first()
        if member:
            db.delete(member)
            db.commit()
            return True
        return False


# ============================================================================
# API Key Service
# ============================================================================

class APIKeyService:
    """Real API key management with secure hashing"""

    @staticmethod
    def create(db: Session, organization_id: int, name: str,
               scopes: List[str] = None, created_by_user_id: int = None) -> tuple[APIKey, str]:
        """Create a new API key. Returns (APIKey, raw_key)"""
        # Generate secure random key
        raw_key = f"sk_{secrets.token_hex(32)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        api_key = APIKey(
            key_id=f"key_{secrets.token_hex(8)}",
            key_hash=key_hash,
            key_prefix=raw_key[:12],
            name=name,
            organization_id=organization_id,
            created_by_user_id=created_by_user_id,
            scopes=scopes or ["read"],
            status="active"
        )
        db.add(api_key)
        db.commit()
        db.refresh(api_key)

        # Return both the model and the raw key (only time it's available)
        return api_key, raw_key

    @staticmethod
    def validate(db: Session, raw_key: str) -> Optional[APIKey]:
        """Validate an API key and return the APIKey if valid"""
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        api_key = db.query(APIKey).filter(
            APIKey.key_hash == key_hash,
            APIKey.status == "active"
        ).first()

        if api_key:
            # Check expiration
            if api_key.expires_at and api_key.expires_at < datetime.utcnow():
                return None

            # Update usage stats
            api_key.total_requests += 1
            api_key.last_used_at = datetime.utcnow()
            db.commit()

        return api_key

    @staticmethod
    def revoke(db: Session, key_id: str) -> bool:
        """Revoke an API key"""
        api_key = db.query(APIKey).filter(APIKey.key_id == key_id).first()
        if api_key:
            api_key.status = "revoked"
            api_key.revoked_at = datetime.utcnow()
            db.commit()
            return True
        return False

    @staticmethod
    def list_by_organization(db: Session, organization_id: int) -> List[APIKey]:
        """List API keys for an organization"""
        return db.query(APIKey).filter(APIKey.organization_id == organization_id).all()


# ============================================================================
# Webhook Service (Real HTTP Delivery)
# ============================================================================

class WebhookService:
    """Real webhook delivery with HTTP requests"""

    @staticmethod
    def create(db: Session, organization_id: int, name: str, url: str,
               events: List[str], secret: str = None) -> Webhook:
        """Create a new webhook"""
        webhook = Webhook(
            webhook_id=f"wh_{secrets.token_hex(8)}",
            name=name,
            url=url,
            secret=secret or secrets.token_hex(32),
            organization_id=organization_id,
            events=events,
            status="active"
        )
        db.add(webhook)
        db.commit()
        db.refresh(webhook)
        return webhook

    @staticmethod
    def get_by_event(db: Session, organization_id: int, event_type: str) -> List[Webhook]:
        """Get all webhooks subscribed to an event type"""
        webhooks = db.query(Webhook).filter(
            Webhook.organization_id == organization_id,
            Webhook.status == "active"
        ).all()
        return [w for w in webhooks if event_type in (w.events or [])]

    @staticmethod
    def generate_signature(payload: str, secret: str) -> str:
        """Generate HMAC signature for webhook payload"""
        return hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

    @staticmethod
    async def deliver(db: Session, webhook: Webhook, event_type: str,
                     event_id: str, payload: Dict[str, Any]) -> WebhookDelivery:
        """Actually deliver a webhook via HTTP POST"""
        import json

        delivery = WebhookDelivery(
            delivery_id=f"del_{secrets.token_hex(8)}",
            webhook_id=webhook.id,
            event_type=event_type,
            event_id=event_id,
            payload=payload,
            status="pending",
            scheduled_at=datetime.utcnow()
        )
        db.add(delivery)
        db.commit()

        # Prepare request
        payload_json = json.dumps(payload)
        signature = WebhookService.generate_signature(payload_json, webhook.secret)

        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": f"sha256={signature}",
            "X-Webhook-Event": event_type,
            "X-Webhook-Delivery-ID": delivery.delivery_id,
            **(webhook.headers or {})
        }

        # Send HTTP request
        start_time = datetime.utcnow()
        try:
            async with httpx.AsyncClient(timeout=webhook.timeout_seconds) as client:
                response = await client.post(
                    webhook.url,
                    content=payload_json,
                    headers=headers
                )

            delivery.response_status_code = response.status_code
            delivery.response_body = response.text[:1000]  # Truncate
            delivery.response_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

            if 200 <= response.status_code < 300:
                delivery.status = "success"
                webhook.successful_deliveries += 1
                webhook.last_success_at = datetime.utcnow()
            else:
                delivery.status = "failed"
                delivery.error_message = f"HTTP {response.status_code}"
                webhook.failed_deliveries += 1
                webhook.last_failure_at = datetime.utcnow()
                webhook.last_failure_reason = delivery.error_message

        except Exception as e:
            delivery.status = "failed"
            delivery.error_message = str(e)
            delivery.response_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            webhook.failed_deliveries += 1
            webhook.last_failure_at = datetime.utcnow()
            webhook.last_failure_reason = str(e)

        delivery.delivered_at = datetime.utcnow()
        webhook.total_deliveries += 1
        webhook.last_triggered_at = datetime.utcnow()
        db.commit()
        db.refresh(delivery)

        return delivery

    @staticmethod
    async def trigger_event(db: Session, organization_id: int, event_type: str,
                           payload: Dict[str, Any]) -> List[WebhookDelivery]:
        """Trigger an event and deliver to all subscribed webhooks"""
        webhooks = WebhookService.get_by_event(db, organization_id, event_type)
        event_id = f"evt_{secrets.token_hex(8)}"

        deliveries = []
        for webhook in webhooks:
            delivery = await WebhookService.deliver(db, webhook, event_type, event_id, payload)
            deliveries.append(delivery)

        return deliveries


# ============================================================================
# AI Provider Service (Real API Calls)
# ============================================================================

class AIProviderService:
    """Real AI provider integrations"""

    PROVIDERS = {
        "openai": {
            "base_url": "https://api.openai.com/v1",
            "models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "gpt-4o", "gpt-4o-mini"]
        },
        "anthropic": {
            "base_url": "https://api.anthropic.com/v1",
            "models": ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307", "claude-sonnet-4-20250514"]
        },
        "ollama": {
            "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            "models": ["llama3", "llama3:70b", "mixtral", "codellama", "mistral"]
        }
    }

    @staticmethod
    def get_api_key(provider: str) -> Optional[str]:
        """Get API key from environment"""
        keys = {
            "openai": os.getenv("OPENAI_API_KEY"),
            "anthropic": os.getenv("ANTHROPIC_API_KEY")
        }
        return keys.get(provider)

    @staticmethod
    async def chat_completion_openai(messages: List[Dict], model: str = "gpt-4",
                                     temperature: float = 0.7) -> Dict[str, Any]:
        """Call OpenAI chat completion API"""
        api_key = AIProviderService.get_api_key("openai")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature
                },
                timeout=60.0
            )
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def chat_completion_anthropic(messages: List[Dict], model: str = "claude-3-sonnet-20240229",
                                        system: str = None, max_tokens: int = 4096) -> Dict[str, Any]:
        """Call Anthropic chat completion API"""
        api_key = AIProviderService.get_api_key("anthropic")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")

        # Convert messages to Anthropic format
        anthropic_messages = []
        for msg in messages:
            if msg["role"] != "system":
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01"
                },
                json={
                    "model": model,
                    "messages": anthropic_messages,
                    "system": system or "You are a helpful assistant.",
                    "max_tokens": max_tokens
                },
                timeout=60.0
            )
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def chat_completion_ollama(messages: List[Dict], model: str = "llama3",
                                     system: str = None) -> Dict[str, Any]:
        """Call Ollama local API for chat completion"""
        base_url = AIProviderService.PROVIDERS["ollama"]["base_url"]

        # Build the prompt from messages
        ollama_messages = []
        if system:
            ollama_messages.append({"role": "system", "content": system})
        ollama_messages.extend(messages)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/api/chat",
                json={
                    "model": model,
                    "messages": ollama_messages,
                    "stream": False
                },
                timeout=120.0  # Local models can be slower
            )
            response.raise_for_status()
            result = response.json()
            return {
                "content": result.get("message", {}).get("content", ""),
                "model": model,
                "tokens_used": result.get("eval_count", 0) + result.get("prompt_eval_count", 0)
            }

    @staticmethod
    async def chat(db: Session, conversation_id: int, user_message: str) -> AIMessage:
        """Send a message in a conversation and get AI response"""
        conversation = db.query(AIConversation).filter(
            AIConversation.id == conversation_id
        ).first()

        if not conversation:
            raise ValueError("Conversation not found")

        # Save user message
        user_msg = AIMessage(
            message_id=f"msg_{secrets.token_hex(8)}",
            conversation_id=conversation_id,
            role="user",
            content=user_message
        )
        db.add(user_msg)
        db.commit()

        # Get conversation history
        history = db.query(AIMessage).filter(
            AIMessage.conversation_id == conversation_id
        ).order_by(AIMessage.created_at).all()

        messages = [{"role": m.role, "content": m.content} for m in history]

        # Call appropriate provider
        try:
            if conversation.provider == "openai":
                if conversation.system_prompt:
                    messages.insert(0, {"role": "system", "content": conversation.system_prompt})
                result = await AIProviderService.chat_completion_openai(
                    messages, model=conversation.model
                )
                assistant_content = result["choices"][0]["message"]["content"]
                tokens_used = result.get("usage", {}).get("total_tokens", 0)

            elif conversation.provider == "anthropic":
                result = await AIProviderService.chat_completion_anthropic(
                    messages, model=conversation.model, system=conversation.system_prompt
                )
                assistant_content = result["content"][0]["text"]
                tokens_used = result.get("usage", {}).get("input_tokens", 0) + \
                             result.get("usage", {}).get("output_tokens", 0)

            elif conversation.provider == "ollama":
                result = await AIProviderService.chat_completion_ollama(
                    messages, model=conversation.model, system=conversation.system_prompt
                )
                assistant_content = result["content"]
                tokens_used = result.get("tokens_used", 0)

            else:
                # Unsupported provider - return helpful error instead of mock
                supported = list(AIProviderService.PROVIDERS.keys())
                raise ValueError(f"Unsupported AI provider: '{conversation.provider}'. Supported providers: {supported}")

        except Exception as e:
            assistant_content = f"Error calling {conversation.provider}: {str(e)}"
            tokens_used = 0

        # Save assistant response
        assistant_msg = AIMessage(
            message_id=f"msg_{secrets.token_hex(8)}",
            conversation_id=conversation_id,
            role="assistant",
            content=assistant_content,
            model=conversation.model,
            tokens_used=tokens_used
        )
        db.add(assistant_msg)

        # Update conversation stats
        conversation.message_count += 2
        conversation.total_tokens += tokens_used
        conversation.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(assistant_msg)

        return assistant_msg


# ============================================================================
# Rate Limiter (Real Implementation)
# ============================================================================

class RateLimiter:
    """Real rate limiting using sliding window"""

    # In-memory store for rate limits (use Redis in production)
    _requests: Dict[str, List[datetime]] = {}

    @classmethod
    def check(cls, key: str, limit: int, window_seconds: int = 60) -> tuple[bool, int]:
        """
        Check if request is allowed.
        Returns (allowed, remaining_requests)
        """
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window_seconds)

        if key not in cls._requests:
            cls._requests[key] = []

        # Remove old requests outside window
        cls._requests[key] = [t for t in cls._requests[key] if t > window_start]

        current_count = len(cls._requests[key])

        if current_count >= limit:
            return False, 0

        # Record this request
        cls._requests[key].append(now)
        return True, limit - current_count - 1

    @classmethod
    def reset(cls, key: str) -> None:
        """Reset rate limit for a key"""
        if key in cls._requests:
            del cls._requests[key]


# ============================================================================
# Secrets Encryption Service (Fernet)
# ============================================================================

class SecretsService:
    """
    Secure secrets encryption/decryption using Fernet (AES-128-CBC).

    Key Management:
    - Primary key is loaded from SECRETS_ENCRYPTION_KEY env var
    - If not set, a development key is generated (NOT for production!)
    - The key should be a 32-byte URL-safe base64-encoded string

    Usage:
        SecretsService.encrypt("my-secret-value") -> encrypted string
        SecretsService.decrypt(encrypted_string) -> "my-secret-value"
    """

    _fernet = None
    _key = None
    _is_dev_key = False

    @classmethod
    def _ensure_initialized(cls):
        """Initialize the Fernet cipher if not already done"""
        if cls._fernet is not None:
            return

        try:
            from cryptography.fernet import Fernet
        except ImportError:
            # cryptography not installed - use fallback
            import logging
            logging.warning("cryptography package not installed. Using base64 fallback (NOT SECURE!).")
            cls._fernet = "fallback"
            return

        # Try to get key from environment
        key = os.getenv("SECRETS_ENCRYPTION_KEY")

        if key:
            cls._key = key.encode() if isinstance(key, str) else key
            cls._is_dev_key = False
        else:
            # Generate a development key - NOT for production
            import logging
            cls._key = Fernet.generate_key()
            cls._is_dev_key = True
            logging.warning(
                f"No SECRETS_ENCRYPTION_KEY set. Using generated dev key. "
                f"Set SECRETS_ENCRYPTION_KEY for production!"
            )

        cls._fernet = Fernet(cls._key)

    @classmethod
    def encrypt(cls, plaintext: str) -> str:
        """
        Encrypt a plaintext string.

        Returns: URL-safe base64-encoded encrypted string
        """
        cls._ensure_initialized()

        if cls._fernet == "fallback":
            # Fallback to base64 when cryptography is not installed
            import base64
            return "b64:" + base64.urlsafe_b64encode(plaintext.encode()).decode()

        encrypted = cls._fernet.encrypt(plaintext.encode())
        return "fernet:" + encrypted.decode()

    @classmethod
    def decrypt(cls, encrypted: str) -> str:
        """
        Decrypt an encrypted string.

        Raises:
            ValueError: If decryption fails (wrong key, corrupted data, etc.)
        """
        cls._ensure_initialized()

        # Handle legacy base64-only encryption
        if encrypted.startswith("b64:"):
            import base64
            return base64.urlsafe_b64decode(encrypted[4:].encode()).decode()

        # Handle fernet encryption
        if encrypted.startswith("fernet:"):
            if cls._fernet == "fallback":
                raise ValueError("Cannot decrypt fernet-encrypted data without cryptography package")

            try:
                decrypted = cls._fernet.decrypt(encrypted[7:].encode())
                return decrypted.decode()
            except Exception as e:
                raise ValueError(f"Decryption failed: {e}")

        # Legacy: try base64 for old untagged data
        try:
            import base64
            return base64.b64decode(encrypted.encode()).decode()
        except:
            raise ValueError("Unknown encryption format")

    @classmethod
    def rotate_key(cls, old_key: str, new_key: str, encrypted_value: str) -> str:
        """
        Re-encrypt a value with a new key.

        Args:
            old_key: The previous encryption key
            new_key: The new encryption key
            encrypted_value: Value encrypted with old key

        Returns:
            Value encrypted with new key
        """
        try:
            from cryptography.fernet import Fernet
        except ImportError:
            raise ValueError("cryptography package required for key rotation")

        # Decrypt with old key
        old_fernet = Fernet(old_key.encode() if isinstance(old_key, str) else old_key)

        if encrypted_value.startswith("fernet:"):
            encrypted_value = encrypted_value[7:]

        plaintext = old_fernet.decrypt(encrypted_value.encode()).decode()

        # Encrypt with new key
        new_fernet = Fernet(new_key.encode() if isinstance(new_key, str) else new_key)
        new_encrypted = new_fernet.encrypt(plaintext.encode())

        return "fernet:" + new_encrypted.decode()

    @classmethod
    def generate_key(cls) -> str:
        """
        Generate a new Fernet key.

        Returns:
            URL-safe base64-encoded 32-byte key
        """
        try:
            from cryptography.fernet import Fernet
            return Fernet.generate_key().decode()
        except ImportError:
            # Fallback - generate a random key
            import base64
            return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()

    @classmethod
    def is_using_dev_key(cls) -> bool:
        """Check if using a generated development key (insecure)"""
        cls._ensure_initialized()
        return cls._is_dev_key

    @classmethod
    def get_encryption_version(cls) -> int:
        """Get the current encryption version for audit purposes"""
        cls._ensure_initialized()
        if cls._fernet == "fallback":
            return 0  # Base64 fallback
        return 1  # Fernet v1
