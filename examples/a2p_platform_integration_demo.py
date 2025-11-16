"""
🔌 Agent-to-Platform Protocol (A2P) v1.0 - Platform Integration Demo
======================================================================

Demonstrates A2P capabilities for platform integration:
- Platform registration with multiple auth methods
- Service invocation with retry policies
- Rate limiting and quota management
- Event subscriptions (webhooks)
- Platform discovery
- Multiple platform types (LLM, cloud, data)

This example shows realistic scenarios where an agent integrates with
OpenAI for LLM capabilities, AWS for storage, and other platforms.
"""

import asyncio
import json
from datetime import datetime
from superstandard.protocols.a2p_v1 import (
    # Core functionality
    A2PClient,
    PlatformRegistry,

    # Data models
    PlatformRegistration,
    Authentication,
    ServiceInvocation,
    Subscription,
    DiscoveryQuery,
    PlatformInfo,
    A2PMessage,

    # Supporting models
    Credentials,
    RateLimits,
    Quota,
    RetryPolicy,
    WebhookAuthentication,
    PricingInfo,
    SLA,

    # Enums
    Operation,
    RegistrationType,
    AuthMethod,
    BackoffStrategy,
    DeliveryGuarantee,
    WebhookAuthMethod,
    PlatformType,
    PricingModel,
)


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def print_json(data: dict, title: str = None):
    """Pretty print JSON data."""
    if title:
        print(f"\n{title}:")
    print(json.dumps(data, indent=2))


async def main():
    """Run the platform integration demo."""

    print_section("A2P v1.0: Platform Integration Demo")

    # ========================================================================
    # STEP 1: Initialize A2P Client
    # ========================================================================

    print_section("STEP 1: Initialize A2P Client for Agent")

    client = A2PClient(agent_id="apqc_1_0_strategic_agent_001")
    print(f"✓ A2P client initialized for agent: {client.agent_id}")
    print()

    # ========================================================================
    # STEP 2: Register with OpenAI Platform (LLM Provider)
    # ========================================================================

    print_section("STEP 2: Register with OpenAI Platform")

    openai_registration = PlatformRegistration(
        platform_id="openai",
        platform_name="OpenAI API",
        agent_id=client.agent_id,
        registration_type=RegistrationType.API_KEY.value,
        credentials=Credentials(
            api_key="sk-proj-mock_api_key_for_demo"
        ),
        allowed_operations=["completion", "embedding", "fine_tuning"],
        rate_limits=RateLimits(
            requests_per_minute=60,
            requests_per_hour=3600,
            requests_per_day=100000,
            concurrent_requests=10
        ),
        quota=Quota(
            monthly_credits=1000000,
            daily_credits=50000,
            overage_allowed=True,
            overage_rate=1.2
        )
    )

    await client.register_platform(openai_registration)
    print("✓ Registered with OpenAI")
    print(f"  Platform ID: {openai_registration.platform_id}")
    print(f"  Auth Method: {openai_registration.registration_type}")
    print(f"  Rate Limits: {openai_registration.rate_limits.requests_per_minute} req/min")
    print(f"  Monthly Credits: {openai_registration.quota.monthly_credits}")
    print()

    # ========================================================================
    # STEP 3: Authenticate with OpenAI
    # ========================================================================

    print_section("STEP 3: Authenticate with OpenAI Platform")

    openai_auth = Authentication(
        platform_id="openai",
        agent_id=client.agent_id,
        auth_method=AuthMethod.API_KEY.value,
        credentials={'api_key': 'sk-proj-mock_api_key_for_demo'},
        scope=["completion", "embedding"]
    )

    auth_result = await client.authenticate(openai_auth)
    print("✓ Authentication successful")
    print_json(auth_result, "Authentication Result")

    # ========================================================================
    # STEP 4: Invoke LLM Service (OpenAI Completion)
    # ========================================================================

    print_section("STEP 4: Invoke OpenAI Completion Service")

    completion_invocation = ServiceInvocation(
        platform_id="openai",
        service_name="completion",
        operation="create",
        parameters={
            'model': 'gpt-4',
            'messages': [
                {
                    'role': 'system',
                    'content': 'You are a strategic planning assistant for APQC process framework.'
                },
                {
                    'role': 'user',
                    'content': 'Analyze market trends for digital transformation in 2026'
                }
            ],
            'temperature': 0.7,
            'max_tokens': 2000
        },
        timeout=30000,
        retry_policy=RetryPolicy(
            max_retries=3,
            backoff_strategy=BackoffStrategy.EXPONENTIAL.value,
            retry_on=["429", "500", "502", "503"]
        ),
        metadata={
            'trace_id': 'trace_strategic_analysis_001',
            'agent_id': client.agent_id,
            'task_id': 'task_market_analysis_2026'
        }
    )

    print(f"📤 Invoking service: {completion_invocation.service_name}")
    print(f"  Platform: {completion_invocation.platform_id}")
    print(f"  Model: {completion_invocation.parameters['model']}")
    print(f"  Request ID: {completion_invocation.request_id}")
    print(f"  Retry Policy: {completion_invocation.retry_policy.backoff_strategy}")
    print()

    service_result = await client.invoke_service(completion_invocation)
    print("✓ Service invocation successful")
    print_json(service_result, "Service Result")

    # ========================================================================
    # STEP 5: Register with AWS Platform (Cloud Provider)
    # ========================================================================

    print_section("STEP 5: Register with AWS Platform")

    aws_registration = PlatformRegistration(
        platform_id="aws",
        platform_name="Amazon Web Services",
        agent_id=client.agent_id,
        registration_type=RegistrationType.OAUTH.value,
        credentials=Credentials(
            client_id="aws_client_id_demo",
            client_secret="aws_client_secret_demo",
            access_token="aws_access_token_demo"
        ),
        allowed_operations=["s3_storage", "lambda_invoke", "dynamodb_query"],
        rate_limits=RateLimits(
            requests_per_minute=1000,
            concurrent_requests=50
        )
    )

    await client.register_platform(aws_registration)
    print("✓ Registered with AWS")
    print(f"  Platform ID: {aws_registration.platform_id}")
    print(f"  Auth Method: {aws_registration.registration_type}")
    print()

    # ========================================================================
    # STEP 6: Subscribe to AWS S3 Events
    # ========================================================================

    print_section("STEP 6: Subscribe to AWS S3 Events")

    s3_subscription = Subscription(
        platform_id="aws",
        event_types=[
            "s3:ObjectCreated:*",
            "s3:ObjectRemoved:*"
        ],
        callback_url="https://agent.superstandard.org/webhooks/s3",
        callback_method="POST",
        filter={
            'bucket': 'strategic-agent-data',
            'prefix': 'reports/2026/'
        },
        delivery_guarantee=DeliveryGuarantee.AT_LEAST_ONCE.value,
        authentication=WebhookAuthentication(
            method=WebhookAuthMethod.HMAC.value,
            secret="webhook_secret_key_demo"
        )
    )

    subscription_id = await client.subscribe(s3_subscription)
    print("✓ Subscription created")
    print(f"  Subscription ID: {subscription_id}")
    print(f"  Platform: {s3_subscription.platform_id}")
    print(f"  Event Types: {', '.join(s3_subscription.event_types)}")
    print(f"  Callback URL: {s3_subscription.callback_url}")
    print(f"  Delivery Guarantee: {s3_subscription.delivery_guarantee}")
    print(f"  Authentication: {s3_subscription.authentication.method}")
    print()

    # ========================================================================
    # STEP 7: Rate Limit Management
    # ========================================================================

    print_section("STEP 7: Rate Limit Monitoring")

    # Check OpenAI rate limit status
    openai_status = client.get_rate_limit_status("openai")
    if openai_status:
        print("OpenAI Rate Limit Status:")
        print(f"  Requests (last minute): {openai_status['requests_last_minute']}")
        print(f"  Requests (last hour): {openai_status['requests_last_hour']}")
        print(f"  Requests (last day): {openai_status['requests_last_day']}")
        print(f"  Concurrent requests: {openai_status['concurrent_requests']}")
    print()

    # ========================================================================
    # STEP 8: Platform Discovery
    # ========================================================================

    print_section("STEP 8: Platform Discovery")

    # Initialize platform registry
    registry = PlatformRegistry()

    # Register some platforms in the registry
    openai_platform = PlatformInfo(
        platform_id="openai",
        platform_name="OpenAI API",
        platform_type=PlatformType.LLM_PROVIDER.value,
        capabilities=["llm", "completion", "embedding", "fine_tuning"],
        endpoints={
            'api': 'https://api.openai.com/v1',
            'docs': 'https://platform.openai.com/docs'
        },
        pricing=PricingInfo(
            model=PricingModel.PAY_PER_USE.value,
            rates={
                'gpt-4': 0.03,
                'gpt-3.5-turbo': 0.002,
                'embedding': 0.0001
            }
        ),
        sla=SLA(
            availability=0.999,
            latency_p99=2000.0,
            support_level="enterprise"
        ),
        compliance_certifications=["SOC2", "ISO27001", "GDPR"]
    )

    anthropic_platform = PlatformInfo(
        platform_id="anthropic",
        platform_name="Anthropic Claude",
        platform_type=PlatformType.LLM_PROVIDER.value,
        capabilities=["llm", "completion", "analysis"],
        endpoints={
            'api': 'https://api.anthropic.com/v1'
        },
        pricing=PricingInfo(
            model=PricingModel.PAY_PER_USE.value,
            rates={
                'claude-3-opus': 0.015,
                'claude-3-sonnet': 0.003
            }
        ),
        sla=SLA(
            availability=0.999,
            latency_p99=1500.0,
            support_level="enterprise"
        ),
        compliance_certifications=["SOC2", "ISO27001"]
    )

    aws_platform = PlatformInfo(
        platform_id="aws",
        platform_name="Amazon Web Services",
        platform_type=PlatformType.CLOUD_PROVIDER.value,
        capabilities=["compute", "storage", "database", "serverless"],
        endpoints={
            'console': 'https://console.aws.amazon.com',
            'api': 'https://aws.amazon.com'
        },
        pricing=PricingInfo(
            model=PricingModel.PAY_PER_USE.value,
            rates={'s3_storage': 0.023, 'lambda_invocation': 0.0000002}
        ),
        sla=SLA(
            availability=0.9999,
            support_level="enterprise"
        ),
        compliance_certifications=["SOC2", "ISO27001", "HIPAA", "GDPR"]
    )

    registry.register_platform(openai_platform)
    registry.register_platform(anthropic_platform)
    registry.register_platform(aws_platform)

    print("✓ Platform registry populated with 3 platforms")
    print()

    # Discover LLM providers
    print("Discovering LLM Providers:")
    llm_query = DiscoveryQuery(
        capabilities=["llm", "completion"],
        min_availability=0.99
    )

    llm_platforms = registry.discover(llm_query)
    print(f"  Found {len(llm_platforms)} platforms:")
    for platform in llm_platforms:
        print(f"  • {platform.platform_name} ({platform.platform_id})")
        print(f"    Type: {platform.platform_type}")
        print(f"    SLA: {platform.sla.availability if platform.sla else 'N/A'}")
    print()

    # Discover platforms with specific compliance
    print("Discovering GDPR-Compliant Platforms:")
    compliance_query = DiscoveryQuery(
        compliance=["GDPR"]
    )

    compliant_platforms = registry.discover(compliance_query)
    print(f"  Found {len(compliant_platforms)} platforms:")
    for platform in compliant_platforms:
        print(f"  • {platform.platform_name}")
        print(f"    Certifications: {', '.join(platform.compliance_certifications)}")
    print()

    # ========================================================================
    # STEP 9: Async Service Invocation with Callback
    # ========================================================================

    print_section("STEP 9: Async Service Invocation with Callback")

    async_invocation = ServiceInvocation(
        platform_id="openai",
        service_name="fine_tuning",
        operation="create",
        parameters={
            'model': 'gpt-3.5-turbo',
            'training_file': 'file-abc123',
            'validation_file': 'file-def456'
        },
        async_operation=True,
        callback_url="https://agent.superstandard.org/callbacks/fine_tuning",
        metadata={
            'agent_id': client.agent_id,
            'job_type': 'model_fine_tuning'
        }
    )

    print(f"📤 Starting async service invocation")
    print(f"  Service: {async_invocation.service_name}")
    print(f"  Async: {async_invocation.async_operation}")
    print(f"  Callback URL: {async_invocation.callback_url}")
    print()

    # ========================================================================
    # STEP 10: List Active Subscriptions
    # ========================================================================

    print_section("STEP 10: Active Subscriptions")

    subscriptions = client.list_subscriptions()
    print(f"Active Subscriptions: {len(subscriptions)}")
    for sub in subscriptions:
        print(f"\n  Subscription ID: {sub.subscription_id}")
        print(f"  Platform: {sub.platform_id}")
        print(f"  Event Types: {', '.join(sub.event_types)}")
        print(f"  Callback: {sub.callback_url}")
        print(f"  Status: {'Active' if sub.active else 'Inactive'}")
    print()

    # ========================================================================
    # STEP 11: Create A2P Protocol Messages
    # ========================================================================

    print_section("STEP 11: A2P Protocol Messages")

    # Platform registration message
    register_message = A2PMessage(
        operation=Operation.PLATFORM_REGISTER.value,
        platform_registration=openai_registration
    )

    print("Platform Registration Message:")
    print(register_message.to_json())
    print()

    # Service invocation message
    invoke_message = A2PMessage(
        operation=Operation.INVOKE_SERVICE.value,
        service_invocation=completion_invocation
    )

    print("\nService Invocation Message (first 500 chars):")
    json_str = invoke_message.to_json()
    print(json_str[:500] + "..." if len(json_str) > 500 else json_str)
    print()

    # ========================================================================
    # STEP 12: Multi-Platform Workflow
    # ========================================================================

    print_section("STEP 12: Multi-Platform Workflow Example")

    print("Workflow: Strategic Analysis with Multiple Platforms")
    print()

    # Step 1: Query OpenAI for analysis
    print("1. Query OpenAI for market trend analysis")
    print("   ✓ Service: completion")
    print("   ✓ Model: gpt-4")
    print()

    # Step 2: Store results in AWS S3
    print("2. Store analysis results in AWS S3")
    print("   ✓ Service: s3_storage")
    print("   ✓ Bucket: strategic-agent-data")
    print()

    # Step 3: Trigger processing via AWS Lambda
    print("3. Trigger data processing via AWS Lambda")
    print("   ✓ Service: lambda_invoke")
    print("   ✓ Function: process_strategic_analysis")
    print()

    # Step 4: Receive webhook notification
    print("4. Receive webhook notification when complete")
    print("   ✓ Event: s3:ObjectCreated")
    print("   ✓ Callback: agent webhook endpoint")
    print()

    # ========================================================================
    # STEP 13: Summary Statistics
    # ========================================================================

    print_section("STEP 13: Demo Summary")

    print("Platforms Registered:")
    print(f"  • OpenAI (LLM Provider)")
    print(f"  • AWS (Cloud Provider)")
    print()

    print("Operations Demonstrated:")
    print(f"  ✓ Platform registration (API key, OAuth)")
    print(f"  ✓ Authentication")
    print(f"  ✓ Service invocation (sync and async)")
    print(f"  ✓ Event subscriptions (webhooks)")
    print(f"  ✓ Platform discovery")
    print(f"  ✓ Rate limit monitoring")
    print(f"  ✓ Retry policies")
    print()

    print("Features Showcased:")
    print(f"  ✓ Multiple authentication methods (API key, OAuth)")
    print(f"  ✓ Rate limiting and quota management")
    print(f"  ✓ Retry policies with backoff strategies")
    print(f"  ✓ Webhook subscriptions with HMAC authentication")
    print(f"  ✓ Platform discovery with filtering")
    print(f"  ✓ Async operations with callbacks")
    print(f"  ✓ Compliance-aware platform selection")
    print()

    print("Platform Types Covered:")
    print(f"  • LLM Providers (OpenAI, Anthropic)")
    print(f"  • Cloud Providers (AWS)")
    print(f"  • Service discovery and selection")
    print()

    print("\n" + "="*80)
    print("  Demo completed successfully!")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
