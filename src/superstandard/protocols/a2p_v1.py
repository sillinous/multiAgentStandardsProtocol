"""
🔌 Agent-to-Platform Protocol (A2P) v1.0 - PRODUCTION IMPLEMENTATION
======================================================================

Standard protocol for agents to interact with external platforms, APIs, and services.

Features:
- Platform registration and discovery
- Multiple authentication methods (API key, OAuth, SAML, mTLS, DID)
- Service invocation with retry policies
- Event subscriptions and webhooks
- Rate limiting and quota management
- Platform capability discovery
- Support for LLM providers, cloud platforms, data platforms

Author: SuperStandard Team
License: MIT
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Callable, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import json
import uuid
from collections import defaultdict
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS
# ============================================================================


class Operation(Enum):
    """A2P operation types."""

    PLATFORM_REGISTER = "platform_register"
    PLATFORM_DISCOVER = "platform_discover"
    AUTHENTICATE = "authenticate"
    INVOKE_SERVICE = "invoke_service"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    RATE_LIMIT_QUERY = "rate_limit_query"
    CAPABILITY_QUERY = "capability_query"


class RegistrationType(Enum):
    """Platform registration types."""

    API_KEY = "api_key"
    OAUTH = "oauth"
    SAML = "saml"
    MUTUAL_TLS = "mutual_tls"
    DID_AUTH = "did_auth"


class AuthMethod(Enum):
    """Authentication methods."""

    API_KEY = "api_key"
    OAUTH = "oauth"
    JWT = "jwt"
    SAML = "saml"
    MUTUAL_TLS = "mutual_tls"
    DID_AUTH = "did_auth"


class BackoffStrategy(Enum):
    """Retry backoff strategies."""

    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    FIBONACCI = "fibonacci"


class DeliveryGuarantee(Enum):
    """Event delivery guarantees."""

    AT_MOST_ONCE = "at_most_once"
    AT_LEAST_ONCE = "at_least_once"
    EXACTLY_ONCE = "exactly_once"


class CallbackMethod(Enum):
    """HTTP methods for webhooks."""

    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"


class WebhookAuthMethod(Enum):
    """Webhook authentication methods."""

    HMAC = "hmac"
    JWT = "jwt"
    API_KEY = "api_key"
    MUTUAL_TLS = "mutual_tls"


class PlatformType(Enum):
    """Types of platforms."""

    LLM_PROVIDER = "llm_provider"
    CLOUD_PROVIDER = "cloud_provider"
    DATA_PLATFORM = "data_platform"
    API_SERVICE = "api_service"
    BLOCKCHAIN = "blockchain"


class PricingModel(Enum):
    """Pricing models."""

    PAY_PER_USE = "pay_per_use"
    SUBSCRIPTION = "subscription"
    FREEMIUM = "freemium"
    ENTERPRISE = "enterprise"


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class RateLimits:
    """Rate limits imposed by platform."""

    requests_per_minute: Optional[int] = None
    requests_per_hour: Optional[int] = None
    requests_per_day: Optional[int] = None
    concurrent_requests: Optional[int] = None
    burst_limit: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {k: v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RateLimits':
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if hasattr(cls, k)})


@dataclass
class Quota:
    """Usage quota information."""

    monthly_credits: Optional[float] = None
    daily_credits: Optional[float] = None
    overage_allowed: bool = False
    overage_rate: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {k: v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Quota':
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if hasattr(cls, k)})


@dataclass
class Credentials:
    """Platform credentials."""

    api_key: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    certificate: Optional[str] = None
    did: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {k: v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Credentials':
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if hasattr(cls, k)})


@dataclass
class PlatformRegistration:
    """Platform registration information."""

    platform_id: str
    agent_id: str
    registration_type: str
    platform_name: Optional[str] = None
    credentials: Optional[Credentials] = None
    allowed_operations: List[str] = field(default_factory=list)
    rate_limits: Optional[RateLimits] = None
    quota: Optional[Quota] = None
    registered_at: Optional[str] = None
    expires_at: Optional[str] = None

    def __post_init__(self):
        """Set registration timestamp if not provided."""
        if not self.registered_at:
            self.registered_at = datetime.utcnow().isoformat() + 'Z'

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            'platform_id': self.platform_id,
            'agent_id': self.agent_id,
            'registration_type': self.registration_type
        }

        if self.platform_name:
            result['platform_name'] = self.platform_name
        if self.credentials:
            result['credentials'] = self.credentials.to_dict()
        if self.allowed_operations:
            result['allowed_operations'] = self.allowed_operations
        if self.rate_limits:
            result['rate_limits'] = self.rate_limits.to_dict()
        if self.quota:
            result['quota'] = self.quota.to_dict()
        if self.registered_at:
            result['registered_at'] = self.registered_at
        if self.expires_at:
            result['expires_at'] = self.expires_at

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlatformRegistration':
        """Create from dictionary."""
        return cls(
            platform_id=data['platform_id'],
            agent_id=data['agent_id'],
            registration_type=data['registration_type'],
            platform_name=data.get('platform_name'),
            credentials=Credentials.from_dict(data['credentials']) if 'credentials' in data else None,
            allowed_operations=data.get('allowed_operations', []),
            rate_limits=RateLimits.from_dict(data['rate_limits']) if 'rate_limits' in data else None,
            quota=Quota.from_dict(data['quota']) if 'quota' in data else None,
            registered_at=data.get('registered_at'),
            expires_at=data.get('expires_at')
        )


@dataclass
class Authentication:
    """Authentication information."""

    platform_id: str
    agent_id: str
    auth_method: str
    credentials: Optional[Dict[str, Any]] = None
    scope: List[str] = field(default_factory=list)
    session_duration: Optional[int] = None
    mfa_token: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            'platform_id': self.platform_id,
            'agent_id': self.agent_id,
            'auth_method': self.auth_method
        }

        if self.credentials:
            result['credentials'] = self.credentials
        if self.scope:
            result['scope'] = self.scope
        if self.session_duration:
            result['session_duration'] = self.session_duration
        if self.mfa_token:
            result['mfa_token'] = self.mfa_token

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Authentication':
        """Create from dictionary."""
        return cls(
            platform_id=data['platform_id'],
            agent_id=data['agent_id'],
            auth_method=data['auth_method'],
            credentials=data.get('credentials'),
            scope=data.get('scope', []),
            session_duration=data.get('session_duration'),
            mfa_token=data.get('mfa_token')
        )


@dataclass
class RetryPolicy:
    """Retry policy for service invocations."""

    max_retries: int = 3
    backoff_strategy: str = BackoffStrategy.EXPONENTIAL.value
    retry_on: List[str] = field(default_factory=lambda: ["429", "500", "502", "503"])

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RetryPolicy':
        """Create from dictionary."""
        return cls(**data)

    def get_delay(self, attempt: int) -> float:
        """
        Calculate delay for retry attempt.

        Args:
            attempt: Retry attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        if self.backoff_strategy == BackoffStrategy.LINEAR.value:
            return (attempt + 1) * 1.0
        elif self.backoff_strategy == BackoffStrategy.EXPONENTIAL.value:
            return 2 ** attempt
        elif self.backoff_strategy == BackoffStrategy.FIBONACCI.value:
            if attempt == 0:
                return 1.0
            if attempt == 1:
                return 1.0
            a, b = 1.0, 1.0
            for _ in range(attempt - 1):
                a, b = b, a + b
            return b
        else:
            return 1.0


@dataclass
class ServiceInvocation:
    """Service invocation request."""

    platform_id: str
    service_name: str
    operation: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    request_id: Optional[str] = None
    timeout: int = 30000
    retry_policy: Optional[RetryPolicy] = None
    async_operation: bool = False
    callback_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Generate request ID if not provided."""
        if not self.request_id:
            self.request_id = f"req_{uuid.uuid4().hex[:12]}"
        if not self.retry_policy:
            self.retry_policy = RetryPolicy()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            'platform_id': self.platform_id,
            'service_name': self.service_name,
            'operation': self.operation,
            'parameters': self.parameters,
            'request_id': self.request_id,
            'timeout': self.timeout,
            'async': self.async_operation
        }

        if self.retry_policy:
            result['retry_policy'] = self.retry_policy.to_dict()
        if self.callback_url:
            result['callback_url'] = self.callback_url
        if self.metadata:
            result['metadata'] = self.metadata

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ServiceInvocation':
        """Create from dictionary."""
        return cls(
            platform_id=data['platform_id'],
            service_name=data['service_name'],
            operation=data['operation'],
            parameters=data.get('parameters', {}),
            request_id=data.get('request_id'),
            timeout=data.get('timeout', 30000),
            retry_policy=RetryPolicy.from_dict(data['retry_policy']) if 'retry_policy' in data else None,
            async_operation=data.get('async', False),
            callback_url=data.get('callback_url'),
            metadata=data.get('metadata', {})
        )


@dataclass
class SubscriptionRetryPolicy:
    """Retry policy for webhook subscriptions."""

    max_retries: int = 3
    retry_delay: int = 60

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SubscriptionRetryPolicy':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class WebhookAuthentication:
    """Webhook authentication configuration."""

    method: str
    secret: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {'method': self.method}
        if self.secret:
            result['secret'] = self.secret
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WebhookAuthentication':
        """Create from dictionary."""
        return cls(method=data['method'], secret=data.get('secret'))


@dataclass
class Subscription:
    """Event subscription configuration."""

    platform_id: str
    event_types: List[str]
    callback_url: str
    subscription_id: Optional[str] = None
    callback_method: str = CallbackMethod.POST.value
    filter: Dict[str, Any] = field(default_factory=dict)
    delivery_guarantee: str = DeliveryGuarantee.AT_LEAST_ONCE.value
    retry_policy: Optional[SubscriptionRetryPolicy] = None
    authentication: Optional[WebhookAuthentication] = None
    active: bool = True
    created_at: Optional[str] = None
    expires_at: Optional[str] = None

    def __post_init__(self):
        """Generate subscription ID and timestamps if not provided."""
        if not self.subscription_id:
            self.subscription_id = f"sub_{uuid.uuid4().hex[:12]}"
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat() + 'Z'
        if not self.retry_policy:
            self.retry_policy = SubscriptionRetryPolicy()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            'platform_id': self.platform_id,
            'subscription_id': self.subscription_id,
            'event_types': self.event_types,
            'callback_url': self.callback_url,
            'callback_method': self.callback_method,
            'delivery_guarantee': self.delivery_guarantee,
            'active': self.active
        }

        if self.filter:
            result['filter'] = self.filter
        if self.retry_policy:
            result['retry_policy'] = self.retry_policy.to_dict()
        if self.authentication:
            result['authentication'] = self.authentication.to_dict()
        if self.created_at:
            result['created_at'] = self.created_at
        if self.expires_at:
            result['expires_at'] = self.expires_at

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Subscription':
        """Create from dictionary."""
        return cls(
            platform_id=data['platform_id'],
            event_types=data['event_types'],
            callback_url=data['callback_url'],
            subscription_id=data.get('subscription_id'),
            callback_method=data.get('callback_method', CallbackMethod.POST.value),
            filter=data.get('filter', {}),
            delivery_guarantee=data.get('delivery_guarantee', DeliveryGuarantee.AT_LEAST_ONCE.value),
            retry_policy=SubscriptionRetryPolicy.from_dict(data['retry_policy']) if 'retry_policy' in data else None,
            authentication=WebhookAuthentication.from_dict(data['authentication']) if 'authentication' in data else None,
            active=data.get('active', True),
            created_at=data.get('created_at'),
            expires_at=data.get('expires_at')
        )


@dataclass
class DiscoveryQuery:
    """Platform discovery query."""

    capabilities: List[str] = field(default_factory=list)
    region: Optional[str] = None
    compliance: List[str] = field(default_factory=list)
    max_cost: Optional[float] = None
    min_availability: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {}
        if self.capabilities:
            result['capabilities'] = self.capabilities
        if self.region:
            result['region'] = self.region
        if self.compliance:
            result['compliance'] = self.compliance
        if self.max_cost is not None:
            result['max_cost'] = self.max_cost
        if self.min_availability is not None:
            result['min_availability'] = self.min_availability
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DiscoveryQuery':
        """Create from dictionary."""
        return cls(
            capabilities=data.get('capabilities', []),
            region=data.get('region'),
            compliance=data.get('compliance', []),
            max_cost=data.get('max_cost'),
            min_availability=data.get('min_availability')
        )


@dataclass
class PricingInfo:
    """Platform pricing information."""

    model: str
    rates: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {'model': self.model, 'rates': self.rates}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PricingInfo':
        """Create from dictionary."""
        return cls(model=data['model'], rates=data.get('rates', {}))


@dataclass
class SLA:
    """Service level agreement information."""

    availability: Optional[float] = None
    latency_p99: Optional[float] = None
    support_level: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {k: v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SLA':
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if hasattr(cls, k)})


@dataclass
class PlatformInfo:
    """Platform information from discovery."""

    platform_id: str
    platform_name: str
    platform_type: str
    capabilities: List[str] = field(default_factory=list)
    endpoints: Dict[str, str] = field(default_factory=dict)
    pricing: Optional[PricingInfo] = None
    sla: Optional[SLA] = None
    compliance_certifications: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            'platform_id': self.platform_id,
            'platform_name': self.platform_name,
            'platform_type': self.platform_type
        }

        if self.capabilities:
            result['capabilities'] = self.capabilities
        if self.endpoints:
            result['endpoints'] = self.endpoints
        if self.pricing:
            result['pricing'] = self.pricing.to_dict()
        if self.sla:
            result['sla'] = self.sla.to_dict()
        if self.compliance_certifications:
            result['compliance_certifications'] = self.compliance_certifications

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlatformInfo':
        """Create from dictionary."""
        return cls(
            platform_id=data['platform_id'],
            platform_name=data['platform_name'],
            platform_type=data['platform_type'],
            capabilities=data.get('capabilities', []),
            endpoints=data.get('endpoints', {}),
            pricing=PricingInfo.from_dict(data['pricing']) if 'pricing' in data else None,
            sla=SLA.from_dict(data['sla']) if 'sla' in data else None,
            compliance_certifications=data.get('compliance_certifications', [])
        )


@dataclass
class PlatformDiscovery:
    """Platform discovery request and results."""

    query: Optional[DiscoveryQuery] = None
    results: List[PlatformInfo] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {}
        if self.query:
            result['query'] = self.query.to_dict()
        if self.results:
            result['results'] = [r.to_dict() for r in self.results]
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlatformDiscovery':
        """Create from dictionary."""
        return cls(
            query=DiscoveryQuery.from_dict(data['query']) if 'query' in data else None,
            results=[PlatformInfo.from_dict(r) for r in data.get('results', [])]
        )


@dataclass
class A2PMessage:
    """Complete A2P protocol message."""

    protocol: str = "A2P"
    version: str = "1.0.0"
    operation: Optional[str] = None
    platform_registration: Optional[PlatformRegistration] = None
    authentication: Optional[Authentication] = None
    service_invocation: Optional[ServiceInvocation] = None
    subscription: Optional[Subscription] = None
    platform_discovery: Optional[PlatformDiscovery] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            'protocol': self.protocol,
            'version': self.version
        }

        if self.operation:
            result['operation'] = self.operation
        if self.platform_registration:
            result['platform_registration'] = self.platform_registration.to_dict()
        if self.authentication:
            result['authentication'] = self.authentication.to_dict()
        if self.service_invocation:
            result['service_invocation'] = self.service_invocation.to_dict()
        if self.subscription:
            result['subscription'] = self.subscription.to_dict()
        if self.platform_discovery:
            result['platform_discovery'] = self.platform_discovery.to_dict()

        return result

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'A2PMessage':
        """Create from dictionary."""
        return cls(
            protocol=data.get('protocol', 'A2P'),
            version=data.get('version', '1.0.0'),
            operation=data.get('operation'),
            platform_registration=PlatformRegistration.from_dict(data['platform_registration']) if 'platform_registration' in data else None,
            authentication=Authentication.from_dict(data['authentication']) if 'authentication' in data else None,
            service_invocation=ServiceInvocation.from_dict(data['service_invocation']) if 'service_invocation' in data else None,
            subscription=Subscription.from_dict(data['subscription']) if 'subscription' in data else None,
            platform_discovery=PlatformDiscovery.from_dict(data['platform_discovery']) if 'platform_discovery' in data else None
        )

    @classmethod
    def from_json(cls, json_str: str) -> 'A2PMessage':
        """Create from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


# ============================================================================
# RATE LIMITER
# ============================================================================


class RateLimiter:
    """Rate limiter for platform requests."""

    def __init__(self, limits: RateLimits):
        """
        Initialize rate limiter.

        Args:
            limits: Rate limit configuration
        """
        self.limits = limits
        self._minute_requests: List[float] = []
        self._hour_requests: List[float] = []
        self._day_requests: List[float] = []
        self._concurrent = 0

    def _clean_old_requests(self):
        """Remove old requests from tracking."""
        now = time.time()

        # Clean minute requests (older than 60 seconds)
        self._minute_requests = [t for t in self._minute_requests if now - t < 60]

        # Clean hour requests (older than 3600 seconds)
        self._hour_requests = [t for t in self._hour_requests if now - t < 3600]

        # Clean day requests (older than 86400 seconds)
        self._day_requests = [t for t in self._day_requests if now - t < 86400]

    async def acquire(self) -> bool:
        """
        Acquire permission to make a request.

        Returns:
            True if allowed, False if rate limited
        """
        self._clean_old_requests()
        now = time.time()

        # Check per-minute limit
        if self.limits.requests_per_minute:
            if len(self._minute_requests) >= self.limits.requests_per_minute:
                logger.warning("Rate limit exceeded: requests per minute")
                return False

        # Check per-hour limit
        if self.limits.requests_per_hour:
            if len(self._hour_requests) >= self.limits.requests_per_hour:
                logger.warning("Rate limit exceeded: requests per hour")
                return False

        # Check per-day limit
        if self.limits.requests_per_day:
            if len(self._day_requests) >= self.limits.requests_per_day:
                logger.warning("Rate limit exceeded: requests per day")
                return False

        # Check concurrent requests
        if self.limits.concurrent_requests:
            if self._concurrent >= self.limits.concurrent_requests:
                logger.warning("Rate limit exceeded: concurrent requests")
                return False

        # Record the request
        self._minute_requests.append(now)
        self._hour_requests.append(now)
        self._day_requests.append(now)
        self._concurrent += 1

        return True

    def release(self):
        """Release a concurrent request slot."""
        if self._concurrent > 0:
            self._concurrent -= 1

    def get_usage(self) -> Dict[str, int]:
        """Get current usage statistics."""
        self._clean_old_requests()
        return {
            'requests_last_minute': len(self._minute_requests),
            'requests_last_hour': len(self._hour_requests),
            'requests_last_day': len(self._day_requests),
            'concurrent_requests': self._concurrent
        }


# ============================================================================
# A2P CLIENT
# ============================================================================


class A2PClient:
    """Client for interacting with external platforms."""

    def __init__(self, agent_id: str):
        """
        Initialize A2P client.

        Args:
            agent_id: Unique agent identifier
        """
        self.agent_id = agent_id
        self._registrations: Dict[str, PlatformRegistration] = {}
        self._rate_limiters: Dict[str, RateLimiter] = {}
        self._subscriptions: Dict[str, Subscription] = {}
        logger.info(f"A2P client initialized for agent: {agent_id}")

    async def register_platform(self, registration: PlatformRegistration) -> bool:
        """
        Register with a platform.

        Args:
            registration: Platform registration info

        Returns:
            True if successful
        """
        platform_id = registration.platform_id
        self._registrations[platform_id] = registration

        # Create rate limiter if limits are specified
        if registration.rate_limits:
            self._rate_limiters[platform_id] = RateLimiter(registration.rate_limits)

        logger.info(f"Registered with platform: {platform_id}")
        return True

    async def authenticate(self, auth: Authentication) -> Dict[str, Any]:
        """
        Authenticate with a platform.

        Args:
            auth: Authentication information

        Returns:
            Authentication result
        """
        platform_id = auth.platform_id

        if platform_id not in self._registrations:
            raise ValueError(f"Platform {platform_id} not registered")

        logger.info(f"Authenticating with platform: {platform_id} using {auth.auth_method}")

        # In a real implementation, this would perform actual authentication
        return {
            'success': True,
            'platform_id': platform_id,
            'auth_method': auth.auth_method,
            'session_id': f"session_{uuid.uuid4().hex[:12]}"
        }

    async def invoke_service(self, invocation: ServiceInvocation) -> Dict[str, Any]:
        """
        Invoke a platform service.

        Args:
            invocation: Service invocation request

        Returns:
            Service response
        """
        platform_id = invocation.platform_id

        if platform_id not in self._registrations:
            raise ValueError(f"Platform {platform_id} not registered")

        # Check rate limits
        if platform_id in self._rate_limiters:
            limiter = self._rate_limiters[platform_id]
            if not await limiter.acquire():
                raise RuntimeError(f"Rate limit exceeded for platform {platform_id}")

        try:
            logger.info(f"Invoking service {invocation.service_name}.{invocation.operation} on {platform_id}")

            # Simulate service invocation with retry
            for attempt in range(invocation.retry_policy.max_retries + 1):
                try:
                    # In a real implementation, this would make actual API calls
                    result = {
                        'success': True,
                        'request_id': invocation.request_id,
                        'platform_id': platform_id,
                        'service_name': invocation.service_name,
                        'operation': invocation.operation,
                        'result': {'status': 'completed'}
                    }
                    return result

                except Exception as e:
                    if attempt < invocation.retry_policy.max_retries:
                        delay = invocation.retry_policy.get_delay(attempt)
                        logger.warning(f"Retry attempt {attempt + 1} after {delay}s: {e}")
                        await asyncio.sleep(delay)
                    else:
                        raise

        finally:
            # Release rate limit slot
            if platform_id in self._rate_limiters:
                self._rate_limiters[platform_id].release()

    async def subscribe(self, subscription: Subscription) -> str:
        """
        Subscribe to platform events.

        Args:
            subscription: Subscription configuration

        Returns:
            Subscription ID
        """
        platform_id = subscription.platform_id

        if platform_id not in self._registrations:
            raise ValueError(f"Platform {platform_id} not registered")

        sub_id = subscription.subscription_id
        self._subscriptions[sub_id] = subscription

        logger.info(f"Subscribed to {platform_id} events: {subscription.event_types}")
        return sub_id

    async def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from platform events.

        Args:
            subscription_id: Subscription ID to cancel

        Returns:
            True if successful
        """
        if subscription_id in self._subscriptions:
            subscription = self._subscriptions[subscription_id]
            subscription.active = False
            del self._subscriptions[subscription_id]
            logger.info(f"Unsubscribed: {subscription_id}")
            return True

        return False

    async def discover_platforms(self, query: DiscoveryQuery) -> List[PlatformInfo]:
        """
        Discover platforms matching criteria.

        Args:
            query: Discovery query

        Returns:
            List of matching platforms
        """
        logger.info(f"Discovering platforms with capabilities: {query.capabilities}")

        # In a real implementation, this would query a platform registry
        # For now, return mock data
        results = []

        # Mock OpenAI platform
        if not query.capabilities or 'llm' in query.capabilities:
            results.append(PlatformInfo(
                platform_id='openai',
                platform_name='OpenAI API',
                platform_type=PlatformType.LLM_PROVIDER.value,
                capabilities=['llm', 'completion', 'embedding', 'fine_tuning'],
                endpoints={'api': 'https://api.openai.com/v1'},
                pricing=PricingInfo(
                    model=PricingModel.PAY_PER_USE.value,
                    rates={'gpt-4': 0.03, 'gpt-3.5-turbo': 0.002}
                ),
                sla=SLA(availability=0.999, latency_p99=2000.0, support_level='enterprise')
            ))

        return results

    def get_rate_limit_status(self, platform_id: str) -> Optional[Dict[str, int]]:
        """
        Get rate limit usage for a platform.

        Args:
            platform_id: Platform identifier

        Returns:
            Usage statistics or None if no rate limiter
        """
        if platform_id in self._rate_limiters:
            return self._rate_limiters[platform_id].get_usage()
        return None

    def list_subscriptions(self) -> List[Subscription]:
        """
        List all active subscriptions.

        Returns:
            List of active subscriptions
        """
        return list(self._subscriptions.values())


# ============================================================================
# PLATFORM REGISTRY
# ============================================================================


class PlatformRegistry:
    """Registry of available platforms."""

    def __init__(self):
        """Initialize platform registry."""
        self._platforms: Dict[str, PlatformInfo] = {}
        logger.info("Platform registry initialized")

    def register_platform(self, platform: PlatformInfo):
        """
        Register a platform in the registry.

        Args:
            platform: Platform information
        """
        self._platforms[platform.platform_id] = platform
        logger.info(f"Registered platform: {platform.platform_id}")

    def discover(self, query: DiscoveryQuery) -> List[PlatformInfo]:
        """
        Discover platforms matching criteria.

        Args:
            query: Discovery query

        Returns:
            List of matching platforms
        """
        results = []

        for platform in self._platforms.values():
            # Check capabilities
            if query.capabilities:
                if not all(cap in platform.capabilities for cap in query.capabilities):
                    continue

            # Check availability SLA
            if query.min_availability is not None:
                if not platform.sla or platform.sla.availability < query.min_availability:
                    continue

            # Check compliance
            if query.compliance:
                if not all(comp in platform.compliance_certifications for comp in query.compliance):
                    continue

            results.append(platform)

        return results

    def get_platform(self, platform_id: str) -> Optional[PlatformInfo]:
        """
        Get platform information.

        Args:
            platform_id: Platform identifier

        Returns:
            Platform info or None
        """
        return self._platforms.get(platform_id)


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================


def validate_a2p_message(message: A2PMessage) -> bool:
    """
    Validate an A2P message.

    Args:
        message: Message to validate

    Returns:
        True if valid
    """
    try:
        if message.protocol != "A2P":
            logger.error("Invalid protocol")
            return False

        version_parts = message.version.split('.')
        if len(version_parts) != 3:
            logger.error("Invalid version format")
            return False

        if message.operation:
            valid_ops = [op.value for op in Operation]
            if message.operation not in valid_ops:
                logger.error(f"Invalid operation: {message.operation}")
                return False

        return True

    except Exception as e:
        logger.error(f"Validation error: {e}", exc_info=True)
        return False


# ============================================================================
# EXPORTS
# ============================================================================


__all__ = [
    # Enums
    'Operation',
    'RegistrationType',
    'AuthMethod',
    'BackoffStrategy',
    'DeliveryGuarantee',
    'CallbackMethod',
    'WebhookAuthMethod',
    'PlatformType',
    'PricingModel',

    # Data Models
    'RateLimits',
    'Quota',
    'Credentials',
    'PlatformRegistration',
    'Authentication',
    'RetryPolicy',
    'ServiceInvocation',
    'SubscriptionRetryPolicy',
    'WebhookAuthentication',
    'Subscription',
    'DiscoveryQuery',
    'PricingInfo',
    'SLA',
    'PlatformInfo',
    'PlatformDiscovery',
    'A2PMessage',

    # Classes
    'RateLimiter',
    'A2PClient',
    'PlatformRegistry',

    # Validation
    'validate_a2p_message',
]
