"""
Unit Tests for Agent-to-Platform Protocol (A2P) v1.0

Comprehensive tests ensuring:
- Platform registration and authentication
- Service invocation with retry policies
- Rate limiting functionality
- Event subscriptions and webhooks
- Platform discovery
- Quota management
- Multiple authentication methods
"""

import pytest
import asyncio
from datetime import datetime
from superstandard.protocols.a2p_v1 import (
    # Enums
    Operation,
    RegistrationType,
    AuthMethod,
    BackoffStrategy,
    DeliveryGuarantee,
    CallbackMethod,
    WebhookAuthMethod,
    PlatformType,
    PricingModel,

    # Data Models
    RateLimits,
    Quota,
    Credentials,
    PlatformRegistration,
    Authentication,
    RetryPolicy,
    ServiceInvocation,
    SubscriptionRetryPolicy,
    WebhookAuthentication,
    Subscription,
    DiscoveryQuery,
    PricingInfo,
    SLA,
    PlatformInfo,
    PlatformDiscovery,
    A2PMessage,

    # Classes
    RateLimiter,
    A2PClient,
    PlatformRegistry,

    # Validation
    validate_a2p_message,
)


@pytest.mark.unit
class TestDataModels:
    """Test A2P data models."""

    def test_rate_limits_creation(self):
        """Test creating rate limits."""
        limits = RateLimits(
            requests_per_minute=60,
            requests_per_hour=3600,
            requests_per_day=100000,
            concurrent_requests=10
        )

        assert limits.requests_per_minute == 60
        assert limits.requests_per_hour == 3600
        assert limits.concurrent_requests == 10

    def test_rate_limits_to_dict(self):
        """Test rate limits serialization."""
        limits = RateLimits(
            requests_per_minute=100,
            concurrent_requests=5
        )

        data = limits.to_dict()
        assert data['requests_per_minute'] == 100
        assert data['concurrent_requests'] == 5
        assert 'requests_per_hour' not in data  # Not set

    def test_quota_creation(self):
        """Test creating quota."""
        quota = Quota(
            monthly_credits=1000000,
            daily_credits=50000,
            overage_allowed=True,
            overage_rate=1.5
        )

        assert quota.monthly_credits == 1000000
        assert quota.overage_allowed is True
        assert quota.overage_rate == 1.5

    def test_credentials_api_key(self):
        """Test API key credentials."""
        creds = Credentials(api_key="sk-test123")

        assert creds.api_key == "sk-test123"
        assert creds.client_id is None

    def test_credentials_oauth(self):
        """Test OAuth credentials."""
        creds = Credentials(
            client_id="client123",
            client_secret="secret456",
            access_token="token789",
            refresh_token="refresh_abc"
        )

        assert creds.client_id == "client123"
        assert creds.access_token == "token789"
        assert creds.refresh_token == "refresh_abc"

    def test_credentials_did(self):
        """Test DID credentials."""
        creds = Credentials(did="did:example:123456")

        assert creds.did == "did:example:123456"


@pytest.mark.unit
class TestPlatformRegistration:
    """Test platform registration."""

    def test_registration_creation(self):
        """Test creating a platform registration."""
        registration = PlatformRegistration(
            platform_id="openai",
            platform_name="OpenAI API",
            agent_id="agent_001",
            registration_type=RegistrationType.API_KEY.value,
            credentials=Credentials(api_key="sk-test"),
            allowed_operations=["completion", "embedding"]
        )

        assert registration.platform_id == "openai"
        assert registration.agent_id == "agent_001"
        assert registration.registration_type == "api_key"
        assert "completion" in registration.allowed_operations

    def test_registration_with_rate_limits(self):
        """Test registration with rate limits."""
        limits = RateLimits(
            requests_per_minute=60,
            requests_per_day=10000
        )

        registration = PlatformRegistration(
            platform_id="anthropic",
            agent_id="agent_002",
            registration_type=RegistrationType.API_KEY.value,
            rate_limits=limits
        )

        assert registration.rate_limits is not None
        assert registration.rate_limits.requests_per_minute == 60

    def test_registration_with_quota(self):
        """Test registration with quota."""
        quota = Quota(
            monthly_credits=500000,
            overage_allowed=True
        )

        registration = PlatformRegistration(
            platform_id="aws",
            agent_id="agent_003",
            registration_type=RegistrationType.OAUTH.value,
            quota=quota
        )

        assert registration.quota.monthly_credits == 500000
        assert registration.quota.overage_allowed is True

    def test_registration_timestamp(self):
        """Test registration timestamp auto-generation."""
        registration = PlatformRegistration(
            platform_id="gcp",
            agent_id="agent_004",
            registration_type=RegistrationType.SAML.value
        )

        assert registration.registered_at is not None

    def test_registration_serialization(self):
        """Test registration serialization."""
        registration = PlatformRegistration(
            platform_id="azure",
            agent_id="agent_005",
            registration_type=RegistrationType.MUTUAL_TLS.value,
            credentials=Credentials(certificate="cert_data")
        )

        data = registration.to_dict()
        assert data['platform_id'] == "azure"
        assert data['registration_type'] == "mutual_tls"


@pytest.mark.unit
class TestAuthentication:
    """Test authentication."""

    def test_auth_api_key(self):
        """Test API key authentication."""
        auth = Authentication(
            platform_id="openai",
            agent_id="agent_001",
            auth_method=AuthMethod.API_KEY.value,
            credentials={'api_key': 'sk-test'}
        )

        assert auth.auth_method == "api_key"
        assert auth.credentials['api_key'] == 'sk-test'

    def test_auth_oauth(self):
        """Test OAuth authentication."""
        auth = Authentication(
            platform_id="google",
            agent_id="agent_002",
            auth_method=AuthMethod.OAUTH.value,
            credentials={
                'client_id': 'client123',
                'client_secret': 'secret456'
            },
            scope=["read", "write"]
        )

        assert auth.auth_method == "oauth"
        assert "read" in auth.scope
        assert "write" in auth.scope

    def test_auth_jwt(self):
        """Test JWT authentication."""
        auth = Authentication(
            platform_id="custom",
            agent_id="agent_003",
            auth_method=AuthMethod.JWT.value,
            credentials={'token': 'jwt_token_here'}
        )

        assert auth.auth_method == "jwt"

    def test_auth_with_mfa(self):
        """Test authentication with MFA."""
        auth = Authentication(
            platform_id="secure_platform",
            agent_id="agent_004",
            auth_method=AuthMethod.API_KEY.value,
            credentials={'api_key': 'key123'},
            mfa_token="123456"
        )

        assert auth.mfa_token == "123456"


@pytest.mark.unit
class TestRetryPolicy:
    """Test retry policy."""

    def test_retry_policy_creation(self):
        """Test creating a retry policy."""
        policy = RetryPolicy(
            max_retries=5,
            backoff_strategy=BackoffStrategy.EXPONENTIAL.value,
            retry_on=["429", "500", "502"]
        )

        assert policy.max_retries == 5
        assert policy.backoff_strategy == "exponential"
        assert "429" in policy.retry_on

    def test_retry_linear_backoff(self):
        """Test linear backoff calculation."""
        policy = RetryPolicy(backoff_strategy=BackoffStrategy.LINEAR.value)

        assert policy.get_delay(0) == 1.0
        assert policy.get_delay(1) == 2.0
        assert policy.get_delay(2) == 3.0

    def test_retry_exponential_backoff(self):
        """Test exponential backoff calculation."""
        policy = RetryPolicy(backoff_strategy=BackoffStrategy.EXPONENTIAL.value)

        assert policy.get_delay(0) == 1
        assert policy.get_delay(1) == 2
        assert policy.get_delay(2) == 4
        assert policy.get_delay(3) == 8

    def test_retry_fibonacci_backoff(self):
        """Test Fibonacci backoff calculation."""
        policy = RetryPolicy(backoff_strategy=BackoffStrategy.FIBONACCI.value)

        assert policy.get_delay(0) == 1.0
        assert policy.get_delay(1) == 1.0
        assert policy.get_delay(2) == 2.0
        assert policy.get_delay(3) == 3.0
        assert policy.get_delay(4) == 5.0


@pytest.mark.unit
class TestServiceInvocation:
    """Test service invocation."""

    def test_invocation_creation(self):
        """Test creating a service invocation."""
        invocation = ServiceInvocation(
            platform_id="openai",
            service_name="completion",
            operation="create",
            parameters={
                'model': 'gpt-4',
                'messages': [{'role': 'user', 'content': 'Hello'}],
                'temperature': 0.7
            }
        )

        assert invocation.platform_id == "openai"
        assert invocation.service_name == "completion"
        assert invocation.parameters['model'] == 'gpt-4'

    def test_invocation_request_id(self):
        """Test request ID auto-generation."""
        invocation = ServiceInvocation(
            platform_id="test",
            service_name="test_service",
            operation="test_op"
        )

        assert invocation.request_id is not None
        assert invocation.request_id.startswith("req_")

    def test_invocation_with_retry(self):
        """Test invocation with custom retry policy."""
        retry = RetryPolicy(
            max_retries=5,
            backoff_strategy=BackoffStrategy.EXPONENTIAL.value
        )

        invocation = ServiceInvocation(
            platform_id="api",
            service_name="data",
            operation="fetch",
            retry_policy=retry
        )

        assert invocation.retry_policy.max_retries == 5

    def test_invocation_async_with_callback(self):
        """Test async invocation with callback."""
        invocation = ServiceInvocation(
            platform_id="async_platform",
            service_name="long_running",
            operation="process",
            async_operation=True,
            callback_url="https://agent.example.com/callback"
        )

        assert invocation.async_operation is True
        assert invocation.callback_url == "https://agent.example.com/callback"

    def test_invocation_with_metadata(self):
        """Test invocation with metadata."""
        invocation = ServiceInvocation(
            platform_id="platform",
            service_name="service",
            operation="op",
            metadata={
                'trace_id': 'trace_123',
                'agent_id': 'agent_001'
            }
        )

        assert invocation.metadata['trace_id'] == 'trace_123'


@pytest.mark.unit
class TestSubscription:
    """Test event subscriptions."""

    def test_subscription_creation(self):
        """Test creating a subscription."""
        subscription = Subscription(
            platform_id="aws_s3",
            event_types=["s3:ObjectCreated:*", "s3:ObjectRemoved:*"],
            callback_url="https://agent.example.com/webhooks/s3"
        )

        assert subscription.platform_id == "aws_s3"
        assert len(subscription.event_types) == 2
        assert subscription.callback_url == "https://agent.example.com/webhooks/s3"

    def test_subscription_id_generation(self):
        """Test subscription ID auto-generation."""
        subscription = Subscription(
            platform_id="platform",
            event_types=["event1"],
            callback_url="https://example.com"
        )

        assert subscription.subscription_id is not None
        assert subscription.subscription_id.startswith("sub_")

    def test_subscription_with_filter(self):
        """Test subscription with event filter."""
        subscription = Subscription(
            platform_id="aws_s3",
            event_types=["s3:ObjectCreated:*"],
            callback_url="https://example.com",
            filter={
                'bucket': 'my-bucket',
                'prefix': 'data/'
            }
        )

        assert subscription.filter['bucket'] == 'my-bucket'
        assert subscription.filter['prefix'] == 'data/'

    def test_subscription_delivery_guarantee(self):
        """Test subscription with delivery guarantee."""
        subscription = Subscription(
            platform_id="platform",
            event_types=["event1"],
            callback_url="https://example.com",
            delivery_guarantee=DeliveryGuarantee.EXACTLY_ONCE.value
        )

        assert subscription.delivery_guarantee == "exactly_once"

    def test_subscription_with_auth(self):
        """Test subscription with webhook authentication."""
        auth = WebhookAuthentication(
            method=WebhookAuthMethod.HMAC.value,
            secret="webhook_secret"
        )

        subscription = Subscription(
            platform_id="platform",
            event_types=["event1"],
            callback_url="https://example.com",
            authentication=auth
        )

        assert subscription.authentication.method == "hmac"
        assert subscription.authentication.secret == "webhook_secret"

    def test_subscription_callback_method(self):
        """Test subscription with custom callback method."""
        subscription = Subscription(
            platform_id="platform",
            event_types=["event1"],
            callback_url="https://example.com",
            callback_method=CallbackMethod.PUT.value
        )

        assert subscription.callback_method == "PUT"


@pytest.mark.unit
class TestPlatformDiscovery:
    """Test platform discovery."""

    def test_discovery_query_creation(self):
        """Test creating a discovery query."""
        query = DiscoveryQuery(
            capabilities=["llm", "embedding"],
            region="us-west-2",
            compliance=["GDPR", "SOC2"],
            max_cost=0.05,
            min_availability=0.999
        )

        assert "llm" in query.capabilities
        assert query.region == "us-west-2"
        assert "GDPR" in query.compliance
        assert query.min_availability == 0.999

    def test_platform_info_creation(self):
        """Test creating platform info."""
        pricing = PricingInfo(
            model=PricingModel.PAY_PER_USE.value,
            rates={'gpt-4': 0.03, 'gpt-3.5-turbo': 0.002}
        )

        sla = SLA(
            availability=0.999,
            latency_p99=2000.0,
            support_level="enterprise"
        )

        platform = PlatformInfo(
            platform_id="openai",
            platform_name="OpenAI API",
            platform_type=PlatformType.LLM_PROVIDER.value,
            capabilities=["llm", "completion", "embedding"],
            endpoints={'api': 'https://api.openai.com/v1'},
            pricing=pricing,
            sla=sla,
            compliance_certifications=["SOC2", "ISO27001"]
        )

        assert platform.platform_id == "openai"
        assert platform.platform_type == "llm_provider"
        assert "llm" in platform.capabilities
        assert platform.sla.availability == 0.999

    def test_platform_discovery_results(self):
        """Test platform discovery with results."""
        platform1 = PlatformInfo(
            platform_id="platform1",
            platform_name="Platform 1",
            platform_type=PlatformType.CLOUD_PROVIDER.value,
            capabilities=["compute", "storage"]
        )

        platform2 = PlatformInfo(
            platform_id="platform2",
            platform_name="Platform 2",
            platform_type=PlatformType.DATA_PLATFORM.value,
            capabilities=["analytics", "warehouse"]
        )

        discovery = PlatformDiscovery(
            results=[platform1, platform2]
        )

        assert len(discovery.results) == 2
        assert discovery.results[0].platform_id == "platform1"


@pytest.mark.unit
class TestA2PMessage:
    """Test A2P messages."""

    def test_message_creation(self):
        """Test creating an A2P message."""
        message = A2PMessage(
            operation=Operation.PLATFORM_REGISTER.value
        )

        assert message.protocol == "A2P"
        assert message.version == "1.0.0"
        assert message.operation == "platform_register"

    def test_message_with_registration(self):
        """Test message with registration."""
        registration = PlatformRegistration(
            platform_id="openai",
            agent_id="agent_001",
            registration_type=RegistrationType.API_KEY.value,
            credentials=Credentials(api_key="sk-test")
        )

        message = A2PMessage(
            operation=Operation.PLATFORM_REGISTER.value,
            platform_registration=registration
        )

        assert message.platform_registration.platform_id == "openai"

    def test_message_with_authentication(self):
        """Test message with authentication."""
        auth = Authentication(
            platform_id="platform",
            agent_id="agent_001",
            auth_method=AuthMethod.OAUTH.value,
            scope=["read", "write"]
        )

        message = A2PMessage(
            operation=Operation.AUTHENTICATE.value,
            authentication=auth
        )

        assert message.authentication.auth_method == "oauth"

    def test_message_with_service_invocation(self):
        """Test message with service invocation."""
        invocation = ServiceInvocation(
            platform_id="openai",
            service_name="completion",
            operation="create",
            parameters={'model': 'gpt-4'}
        )

        message = A2PMessage(
            operation=Operation.INVOKE_SERVICE.value,
            service_invocation=invocation
        )

        assert message.service_invocation.service_name == "completion"

    def test_message_serialization(self):
        """Test message serialization."""
        message = A2PMessage(
            operation=Operation.CAPABILITY_QUERY.value
        )

        json_str = message.to_json()
        assert isinstance(json_str, str)
        assert '"protocol": "A2P"' in json_str


@pytest.mark.asyncio
class TestRateLimiter:
    """Test rate limiter functionality."""

    async def test_rate_limiter_creation(self):
        """Test creating a rate limiter."""
        limits = RateLimits(requests_per_minute=60)
        limiter = RateLimiter(limits)

        assert limiter.limits.requests_per_minute == 60

    async def test_rate_limiter_acquire(self):
        """Test acquiring rate limit permission."""
        limits = RateLimits(requests_per_minute=100)
        limiter = RateLimiter(limits)

        # Should succeed
        allowed = await limiter.acquire()
        assert allowed is True

        limiter.release()

    async def test_rate_limiter_exceeded(self):
        """Test rate limit exceeded."""
        limits = RateLimits(requests_per_minute=2)
        limiter = RateLimiter(limits)

        # First two should succeed
        assert await limiter.acquire() is True
        assert await limiter.acquire() is True

        # Third should fail
        assert await limiter.acquire() is False

    async def test_rate_limiter_concurrent(self):
        """Test concurrent request limiting."""
        limits = RateLimits(concurrent_requests=3)
        limiter = RateLimiter(limits)

        # Acquire 3 slots
        assert await limiter.acquire() is True
        assert await limiter.acquire() is True
        assert await limiter.acquire() is True

        # Fourth should fail
        assert await limiter.acquire() is False

        # Release one and try again
        limiter.release()
        assert await limiter.acquire() is True

    async def test_rate_limiter_usage_stats(self):
        """Test rate limiter usage statistics."""
        limits = RateLimits(requests_per_minute=100)
        limiter = RateLimiter(limits)

        await limiter.acquire()
        await limiter.acquire()

        usage = limiter.get_usage()
        assert usage['requests_last_minute'] == 2
        assert usage['concurrent_requests'] == 2


@pytest.mark.asyncio
class TestA2PClient:
    """Test A2P client functionality."""

    async def test_client_creation(self):
        """Test creating an A2P client."""
        client = A2PClient(agent_id="agent_001")

        assert client.agent_id == "agent_001"

    async def test_client_register_platform(self):
        """Test registering a platform."""
        client = A2PClient(agent_id="agent_001")

        registration = PlatformRegistration(
            platform_id="openai",
            agent_id="agent_001",
            registration_type=RegistrationType.API_KEY.value,
            credentials=Credentials(api_key="sk-test")
        )

        result = await client.register_platform(registration)
        assert result is True
        assert "openai" in client._registrations

    async def test_client_register_with_rate_limits(self):
        """Test registering platform with rate limits."""
        client = A2PClient(agent_id="agent_001")

        limits = RateLimits(requests_per_minute=60)

        registration = PlatformRegistration(
            platform_id="anthropic",
            agent_id="agent_001",
            registration_type=RegistrationType.API_KEY.value,
            rate_limits=limits
        )

        await client.register_platform(registration)

        # Verify rate limiter was created
        assert "anthropic" in client._rate_limiters

    async def test_client_authenticate(self):
        """Test platform authentication."""
        client = A2PClient(agent_id="agent_001")

        # Register first
        registration = PlatformRegistration(
            platform_id="platform",
            agent_id="agent_001",
            registration_type=RegistrationType.API_KEY.value
        )
        await client.register_platform(registration)

        # Authenticate
        auth = Authentication(
            platform_id="platform",
            agent_id="agent_001",
            auth_method=AuthMethod.API_KEY.value
        )

        result = await client.authenticate(auth)
        assert result['success'] is True

    async def test_client_invoke_service(self):
        """Test service invocation."""
        client = A2PClient(agent_id="agent_001")

        # Register first
        registration = PlatformRegistration(
            platform_id="openai",
            agent_id="agent_001",
            registration_type=RegistrationType.API_KEY.value
        )
        await client.register_platform(registration)

        # Invoke service
        invocation = ServiceInvocation(
            platform_id="openai",
            service_name="completion",
            operation="create",
            parameters={'model': 'gpt-4'}
        )

        result = await client.invoke_service(invocation)
        assert result['success'] is True
        assert result['service_name'] == "completion"

    async def test_client_subscribe(self):
        """Test event subscription."""
        client = A2PClient(agent_id="agent_001")

        # Register first
        registration = PlatformRegistration(
            platform_id="aws_s3",
            agent_id="agent_001",
            registration_type=RegistrationType.API_KEY.value
        )
        await client.register_platform(registration)

        # Subscribe
        subscription = Subscription(
            platform_id="aws_s3",
            event_types=["s3:ObjectCreated:*"],
            callback_url="https://example.com/webhook"
        )

        sub_id = await client.subscribe(subscription)
        assert sub_id is not None
        assert sub_id in client._subscriptions

    async def test_client_unsubscribe(self):
        """Test unsubscribing."""
        client = A2PClient(agent_id="agent_001")

        # Register and subscribe first
        registration = PlatformRegistration(
            platform_id="platform",
            agent_id="agent_001",
            registration_type=RegistrationType.API_KEY.value
        )
        await client.register_platform(registration)

        subscription = Subscription(
            platform_id="platform",
            event_types=["event1"],
            callback_url="https://example.com"
        )

        sub_id = await client.subscribe(subscription)

        # Unsubscribe
        result = await client.unsubscribe(sub_id)
        assert result is True
        assert sub_id not in client._subscriptions

    async def test_client_discover_platforms(self):
        """Test platform discovery."""
        client = A2PClient(agent_id="agent_001")

        query = DiscoveryQuery(
            capabilities=["llm"],
            min_availability=0.99
        )

        results = await client.discover_platforms(query)
        assert isinstance(results, list)
        # Mock implementation returns at least one result
        assert len(results) > 0

    async def test_client_rate_limit_status(self):
        """Test getting rate limit status."""
        client = A2PClient(agent_id="agent_001")

        limits = RateLimits(requests_per_minute=100)
        registration = PlatformRegistration(
            platform_id="platform",
            agent_id="agent_001",
            registration_type=RegistrationType.API_KEY.value,
            rate_limits=limits
        )

        await client.register_platform(registration)

        status = client.get_rate_limit_status("platform")
        assert status is not None
        assert 'requests_last_minute' in status


@pytest.mark.asyncio
class TestPlatformRegistry:
    """Test platform registry functionality."""

    async def test_registry_creation(self):
        """Test creating a platform registry."""
        registry = PlatformRegistry()
        assert registry is not None

    async def test_registry_register_platform(self):
        """Test registering a platform."""
        registry = PlatformRegistry()

        platform = PlatformInfo(
            platform_id="openai",
            platform_name="OpenAI",
            platform_type=PlatformType.LLM_PROVIDER.value,
            capabilities=["llm", "completion"]
        )

        registry.register_platform(platform)

        # Verify registration
        retrieved = registry.get_platform("openai")
        assert retrieved is not None
        assert retrieved.platform_id == "openai"

    async def test_registry_discover_by_capabilities(self):
        """Test discovery by capabilities."""
        registry = PlatformRegistry()

        # Register platforms
        platform1 = PlatformInfo(
            platform_id="openai",
            platform_name="OpenAI",
            platform_type=PlatformType.LLM_PROVIDER.value,
            capabilities=["llm", "completion", "embedding"]
        )

        platform2 = PlatformInfo(
            platform_id="aws",
            platform_name="AWS",
            platform_type=PlatformType.CLOUD_PROVIDER.value,
            capabilities=["compute", "storage"]
        )

        registry.register_platform(platform1)
        registry.register_platform(platform2)

        # Discover LLM platforms
        query = DiscoveryQuery(capabilities=["llm"])
        results = registry.discover(query)

        assert len(results) == 1
        assert results[0].platform_id == "openai"

    async def test_registry_discover_by_availability(self):
        """Test discovery by availability SLA."""
        registry = PlatformRegistry()

        platform1 = PlatformInfo(
            platform_id="high_sla",
            platform_name="High SLA Platform",
            platform_type=PlatformType.API_SERVICE.value,
            capabilities=["api"],
            sla=SLA(availability=0.999)
        )

        platform2 = PlatformInfo(
            platform_id="low_sla",
            platform_name="Low SLA Platform",
            platform_type=PlatformType.API_SERVICE.value,
            capabilities=["api"],
            sla=SLA(availability=0.95)
        )

        registry.register_platform(platform1)
        registry.register_platform(platform2)

        # Discover high availability platforms
        query = DiscoveryQuery(min_availability=0.99)
        results = registry.discover(query)

        assert len(results) == 1
        assert results[0].platform_id == "high_sla"


@pytest.mark.unit
class TestValidation:
    """Test validation functions."""

    def test_validate_valid_message(self):
        """Test validation of valid message."""
        message = A2PMessage(
            operation=Operation.PLATFORM_REGISTER.value
        )

        assert validate_a2p_message(message)

    def test_validate_invalid_protocol(self):
        """Test validation with invalid protocol."""
        message = A2PMessage()
        message.protocol = "INVALID"

        assert not validate_a2p_message(message)

    def test_validate_invalid_version(self):
        """Test validation with invalid version."""
        message = A2PMessage()
        message.version = "invalid_version"

        assert not validate_a2p_message(message)
