"""
Database Models for Agent Platform
====================================

SQLAlchemy models for storing agent executions, workflows, and results.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, BigInteger, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./agent_platform.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ============================================================================
# Database Models
# ============================================================================

class Agent(Base):
    """Agent registry - all available agents"""
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    apqc_id = Column(String(50), index=True)
    apqc_category = Column(String(200))
    agent_type = Column(String(50))  # atomic, composite
    version = Column(String(20), default="1.0.0")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    executions = relationship("AgentExecution", back_populates="agent")


class Workflow(Base):
    """Workflow definitions and executions"""
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(String(100), unique=True, index=True, nullable=False)
    workflow_name = Column(String(200), nullable=False)
    workflow_type = Column(String(50))  # invoice_processing, employee_onboarding, etc.
    status = Column(String(50), default="pending")  # pending, running, completed, failed

    # Input/Output
    input_data = Column(JSON)
    output_data = Column(JSON)

    # Execution metadata
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    execution_time_ms = Column(Float)

    # Results
    success = Column(Boolean)
    error_message = Column(Text)

    # Metrics
    total_agents = Column(Integer, default=0)
    agents_succeeded = Column(Integer, default=0)
    agents_failed = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    executions = relationship("AgentExecution", back_populates="workflow")


class AgentExecution(Base):
    """Individual agent execution records"""
    __tablename__ = "agent_executions"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(String(100), unique=True, index=True, nullable=False)

    # Foreign keys
    agent_id = Column(Integer, ForeignKey("agents.id"))
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=True)

    # Execution details
    task_id = Column(String(100), index=True)
    status = Column(String(50))  # success, failed, pending

    # Input/Output
    input_data = Column(JSON)
    output_data = Column(JSON)
    result_data = Column(JSON)

    # Timing
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    execution_time_ms = Column(Float)

    # Results
    success = Column(Boolean)
    error_message = Column(Text)

    # Metadata
    retry_count = Column(Integer, default=0)
    priority = Column(Integer, default=5)
    execution_metadata = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    agent = relationship("Agent", back_populates="executions")
    workflow = relationship("Workflow", back_populates="executions")


class WorkflowStage(Base):
    """Individual stages within a workflow"""
    __tablename__ = "workflow_stages"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"))
    stage_number = Column(Integer)  # 1, 2, 3, 4...
    stage_name = Column(String(100))  # extract, validate, calculate, approve
    agent_execution_id = Column(Integer, ForeignKey("agent_executions.id"))

    status = Column(String(50))  # pending, running, completed, failed
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    execution_time_ms = Column(Float)

    success = Column(Boolean)
    error_message = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)


class WorkflowDefinition(Base):
    """Reusable workflow definitions/templates"""
    __tablename__ = "workflow_definitions"

    id = Column(Integer, primary_key=True, index=True)
    definition_id = Column(String(100), unique=True, index=True, nullable=False)

    # Basic info
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # Workflow configuration (JSON)
    steps = Column(JSON)  # Array of step definitions
    triggers = Column(JSON)  # Array of trigger configurations
    variables = Column(JSON)  # Variable definitions
    error_handling = Column(JSON)  # Error handling configuration

    # Metadata
    tags = Column(JSON)  # Array of tags
    version = Column(Integer, default=1)

    # Ownership
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    created_by = Column(Integer, ForeignKey("users.id"))

    # Status
    status = Column(String(50), default="active")  # active, draft, archived

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================================
# Core Entity Models (Users, Teams, Organizations)
# ============================================================================

class Organization(Base):
    """Organizations/Tenants"""
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    slug = Column(String(100), unique=True, index=True)
    description = Column(Text)

    # Settings
    plan = Column(String(50), default="free")  # free, starter, professional, enterprise
    settings = Column(JSON, default={})

    # Limits
    max_users = Column(Integer, default=5)
    max_teams = Column(Integer, default=3)
    max_api_calls_per_month = Column(Integer, default=10000)
    current_api_calls = Column(Integer, default=0)

    # Status
    status = Column(String(50), default="active")  # active, suspended, deleted

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    users = relationship("User", back_populates="organization")
    teams = relationship("Team", back_populates="organization")
    api_keys = relationship("APIKey", back_populates="organization")
    webhooks = relationship("Webhook", back_populates="organization")


class User(Base):
    """Platform users"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True)
    password_hash = Column(String(255))  # bcrypt hashed

    # Profile
    first_name = Column(String(100))
    last_name = Column(String(100))
    display_name = Column(String(200))
    avatar_url = Column(String(500))

    # Organization
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    role = Column(String(50), default="member")  # owner, admin, member, viewer

    # Auth
    email_verified = Column(Boolean, default=False)
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String(100))

    # Status
    status = Column(String(50), default="active")  # active, invited, suspended, deleted
    last_login = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    organization = relationship("Organization", back_populates="users")
    team_memberships = relationship("TeamMember", back_populates="user")


class Team(Base):
    """Teams within organizations"""
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # Organization
    organization_id = Column(Integer, ForeignKey("organizations.id"))

    # Settings
    settings = Column(JSON, default={})

    # Status
    status = Column(String(50), default="active")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    organization = relationship("Organization", back_populates="teams")
    members = relationship("TeamMember", back_populates="team")


class TeamMember(Base):
    """Team membership junction table"""
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String(50), default="member")  # lead, member
    joined_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    team = relationship("Team", back_populates="members")
    user = relationship("User", back_populates="team_memberships")


# ============================================================================
# API Keys & Authentication
# ============================================================================

class APIKey(Base):
    """API Keys for authentication"""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key_id = Column(String(50), unique=True, index=True, nullable=False)
    key_hash = Column(String(255), nullable=False)  # SHA-256 hash of actual key
    key_prefix = Column(String(20))  # First 8 chars for identification

    name = Column(String(200))
    description = Column(Text)

    # Organization & Permissions
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    created_by_user_id = Column(Integer, ForeignKey("users.id"))
    scopes = Column(JSON, default=["read"])  # read, write, admin, etc.

    # Rate Limits
    rate_limit_per_minute = Column(Integer, default=60)
    rate_limit_per_day = Column(Integer, default=10000)

    # Usage tracking
    total_requests = Column(Integer, default=0)
    last_used_at = Column(DateTime)

    # Status
    status = Column(String(50), default="active")  # active, revoked, expired
    expires_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    revoked_at = Column(DateTime)

    # Relationships
    organization = relationship("Organization", back_populates="api_keys")


# ============================================================================
# Webhooks
# ============================================================================

class Webhook(Base):
    """Webhook configurations"""
    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True, index=True)
    webhook_id = Column(String(50), unique=True, index=True, nullable=False)

    name = Column(String(200))
    url = Column(String(500), nullable=False)
    secret = Column(String(255))  # For signature verification

    # Organization
    organization_id = Column(Integer, ForeignKey("organizations.id"))

    # Configuration
    events = Column(JSON, default=[])  # workflow.completed, agent.executed, etc.
    headers = Column(JSON, default={})  # Custom headers to include

    # Status
    status = Column(String(50), default="active")  # active, paused, failed

    # Reliability
    retry_count = Column(Integer, default=3)
    timeout_seconds = Column(Integer, default=30)

    # Stats
    total_deliveries = Column(Integer, default=0)
    successful_deliveries = Column(Integer, default=0)
    failed_deliveries = Column(Integer, default=0)
    last_triggered_at = Column(DateTime)
    last_success_at = Column(DateTime)
    last_failure_at = Column(DateTime)
    last_failure_reason = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    organization = relationship("Organization", back_populates="webhooks")
    deliveries = relationship("WebhookDelivery", back_populates="webhook")


class WebhookDelivery(Base):
    """Webhook delivery attempts"""
    __tablename__ = "webhook_deliveries"

    id = Column(Integer, primary_key=True, index=True)
    delivery_id = Column(String(50), unique=True, index=True, nullable=False)
    webhook_id = Column(Integer, ForeignKey("webhooks.id"))

    # Event
    event_type = Column(String(100))
    event_id = Column(String(100))
    payload = Column(JSON)

    # Delivery attempt
    attempt_number = Column(Integer, default=1)
    status = Column(String(50))  # pending, success, failed

    # Response
    response_status_code = Column(Integer)
    response_body = Column(Text)
    response_time_ms = Column(Float)

    # Error
    error_message = Column(Text)

    # Timestamps
    scheduled_at = Column(DateTime)
    delivered_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    webhook = relationship("Webhook", back_populates="deliveries")


# ============================================================================
# AI Conversations & Messages
# ============================================================================

class AIConversation(Base):
    """AI chat conversations"""
    __tablename__ = "ai_conversations"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String(50), unique=True, index=True, nullable=False)

    # Owner
    user_id = Column(Integer, ForeignKey("users.id"))
    organization_id = Column(Integer, ForeignKey("organizations.id"))

    # Configuration
    title = Column(String(500))
    model = Column(String(100), default="gpt-4")
    provider = Column(String(50), default="openai")  # openai, anthropic, ollama
    system_prompt = Column(Text)

    # Context
    context = Column(JSON, default={})

    # Stats
    message_count = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)

    # Status
    status = Column(String(50), default="active")  # active, archived

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    messages = relationship("AIMessage", back_populates="conversation")


class AIMessage(Base):
    """Individual messages in AI conversations"""
    __tablename__ = "ai_messages"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String(50), unique=True, index=True, nullable=False)
    conversation_id = Column(Integer, ForeignKey("ai_conversations.id"))

    # Content
    role = Column(String(50))  # user, assistant, system
    content = Column(Text)

    # Metadata
    model = Column(String(100))
    tokens_used = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    conversation = relationship("AIConversation", back_populates="messages")


class AIUsageLog(Base):
    """AI provider usage logging for analytics and billing"""
    __tablename__ = "ai_usage_logs"

    id = Column(Integer, primary_key=True, index=True)
    log_id = Column(String(50), unique=True, index=True, nullable=False)

    # Association
    user_id = Column(Integer, ForeignKey("users.id"))
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    conversation_id = Column(Integer, ForeignKey("ai_conversations.id"))

    # Provider details
    provider = Column(String(50), index=True)  # openai, anthropic, ollama
    model = Column(String(100), index=True)

    # Token usage
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)

    # Cost tracking (in cents)
    cost_cents = Column(Integer, default=0)

    # Request metadata
    request_type = Column(String(50))  # chat, completion, embedding
    latency_ms = Column(Integer)
    success = Column(Boolean, default=True)
    error_message = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class AIProviderConfig(Base):
    """AI provider configurations (stored credentials and settings)"""
    __tablename__ = "ai_provider_configs"

    id = Column(Integer, primary_key=True, index=True)
    config_id = Column(String(50), unique=True, index=True, nullable=False)

    # Provider identity
    provider = Column(String(50), unique=True, nullable=False)  # openai, anthropic, ollama
    display_name = Column(String(200))

    # Configuration
    base_url = Column(String(500))
    api_key_encrypted = Column(Text)  # Encrypted API key
    default_model = Column(String(100))
    available_models = Column(JSON, default=[])  # List of available models

    # Settings
    max_tokens = Column(Integer, default=4096)
    temperature = Column(Float, default=0.7)
    rate_limit_rpm = Column(Integer)  # Requests per minute
    timeout_seconds = Column(Integer, default=60)

    # Status
    enabled = Column(Boolean, default=True)
    last_health_check = Column(DateTime)
    health_status = Column(String(50), default="unknown")  # healthy, degraded, down, unknown

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================================
# Enterprise Features - Billing & Quotas
# ============================================================================

class BillingAccount(Base):
    """Billing accounts for organizations"""
    __tablename__ = "billing_accounts"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(String(50), unique=True, index=True, nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"))

    # Plan details
    plan_type = Column(String(50), default="free")  # free, starter, professional, enterprise
    billing_email = Column(String(200))
    billing_address = Column(JSON)

    # Payment
    payment_method = Column(String(50))  # card, invoice, wire
    payment_status = Column(String(50), default="active")  # active, past_due, cancelled

    # Limits
    monthly_budget = Column(Float)
    current_month_spend = Column(Float, default=0.0)

    # Timestamps
    billing_cycle_start = Column(DateTime)
    next_billing_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CostRecord(Base):
    """Cost tracking records"""
    __tablename__ = "cost_records"

    id = Column(Integer, primary_key=True, index=True)
    record_id = Column(String(50), unique=True, index=True, nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    billing_account_id = Column(Integer, ForeignKey("billing_accounts.id"))

    # Cost details
    cost_type = Column(String(50))  # agent_execution, workflow, ai_call, storage, api_request
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="USD")

    # Reference
    resource_id = Column(String(100))
    resource_type = Column(String(50))
    description = Column(Text)

    # Timestamps
    incurred_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class UsageQuota(Base):
    """Usage quotas for organizations"""
    __tablename__ = "usage_quotas"

    id = Column(Integer, primary_key=True, index=True)
    quota_id = Column(String(50), unique=True, index=True, nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"))

    # Quota type
    quota_type = Column(String(50))  # executions, api_calls, storage_gb, ai_tokens
    limit_value = Column(Integer, nullable=False)
    current_usage = Column(Integer, default=0)
    period = Column(String(20), default="monthly")  # daily, monthly, yearly

    # Enforcement
    hard_limit = Column(Boolean, default=False)  # True = block when exceeded
    alert_threshold = Column(Float, default=0.8)  # Alert at 80%

    # Reset
    reset_at = Column(DateTime)
    last_reset = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================================
# Enterprise Features - Backup & Disaster Recovery
# ============================================================================

class Backup(Base):
    """Backup records"""
    __tablename__ = "backups"

    id = Column(Integer, primary_key=True, index=True)
    backup_id = Column(String(50), unique=True, index=True, nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"))

    # Backup details
    backup_type = Column(String(50))  # full, incremental, differential
    backup_name = Column(String(200))
    description = Column(Text)

    # Storage
    storage_location = Column(String(500))  # S3 path, file path, etc.
    size_bytes = Column(BigInteger)
    checksum = Column(String(100))

    # Status
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    error_message = Column(Text)

    # Timing
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    expires_at = Column(DateTime)
    retention_days = Column(Integer, default=30)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)


class RestoreJob(Base):
    """Restore job records"""
    __tablename__ = "restore_jobs"

    id = Column(Integer, primary_key=True, index=True)
    restore_id = Column(String(50), unique=True, index=True, nullable=False)
    backup_id = Column(Integer, ForeignKey("backups.id"))
    organization_id = Column(Integer, ForeignKey("organizations.id"))

    # Restore details
    restore_type = Column(String(50))  # full, partial
    target_environment = Column(String(100))

    # Status
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    progress_percent = Column(Integer, default=0)
    error_message = Column(Text)

    # Timing
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================================
# Enterprise Features - SSO & MFA
# ============================================================================

class SSOProvider(Base):
    """SSO provider configurations"""
    __tablename__ = "sso_providers"

    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(String(50), unique=True, index=True, nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"))

    # Provider details
    name = Column(String(200), nullable=False)
    provider_type = Column(String(50))  # saml, oidc
    is_enabled = Column(Boolean, default=True)

    # SAML config
    entity_id = Column(String(500))
    sso_url = Column(String(500))
    certificate = Column(Text)

    # OIDC config
    client_id = Column(String(200))
    client_secret_encrypted = Column(String(500))  # Encrypted
    authorization_url = Column(String(500))
    token_url = Column(String(500))
    userinfo_url = Column(String(500))

    # Attribute mapping
    attribute_mapping = Column(JSON)

    # Status
    status = Column(String(50), default="active")
    last_used_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MFADevice(Base):
    """MFA device registrations"""
    __tablename__ = "mfa_devices"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(50), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))

    # Device details
    device_type = Column(String(50))  # totp, sms, email, hardware_key
    device_name = Column(String(200))

    # TOTP
    secret_encrypted = Column(String(500))  # Encrypted TOTP secret
    backup_codes_encrypted = Column(Text)  # Encrypted backup codes

    # Status
    is_verified = Column(Boolean, default=False)
    is_primary = Column(Boolean, default=False)
    status = Column(String(50), default="pending")  # pending, active, disabled

    # Usage
    last_used_at = Column(DateTime)
    use_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    verified_at = Column(DateTime)


# ============================================================================
# Enterprise Features - Security Policies
# ============================================================================

class SecurityPolicy(Base):
    """Security policies"""
    __tablename__ = "security_policies"

    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(String(50), unique=True, index=True, nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"))

    # Policy details
    name = Column(String(200), nullable=False)
    description = Column(Text)
    policy_type = Column(String(50))  # access, data, network, compliance

    # Rules
    rules = Column(JSON)  # Array of rule definitions
    scope = Column(String(50), default="organization")  # organization, team, user

    # Enforcement
    enforcement_mode = Column(String(50), default="audit")  # audit, enforce, disabled
    priority = Column(Integer, default=5)

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PolicyViolation(Base):
    """Policy violation records"""
    __tablename__ = "policy_violations"

    id = Column(Integer, primary_key=True, index=True)
    violation_id = Column(String(50), unique=True, index=True, nullable=False)
    policy_id = Column(Integer, ForeignKey("security_policies.id"))
    organization_id = Column(Integer, ForeignKey("organizations.id"))

    # Violation details
    severity = Column(String(20))  # low, medium, high, critical
    description = Column(Text)
    resource_type = Column(String(100))
    resource_id = Column(String(100))

    # Actor
    user_id = Column(Integer, ForeignKey("users.id"))
    ip_address = Column(String(50))
    user_agent = Column(Text)

    # Resolution
    status = Column(String(50), default="open")  # open, acknowledged, resolved, false_positive
    resolved_by = Column(Integer, ForeignKey("users.id"))
    resolved_at = Column(DateTime)
    resolution_notes = Column(Text)

    # Timestamps
    occurred_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================================
# Enterprise Features - Marketplace
# ============================================================================

class MarketplaceListing(Base):
    """Marketplace listings"""
    __tablename__ = "marketplace_listings"

    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(String(50), unique=True, index=True, nullable=False)
    publisher_org_id = Column(Integer, ForeignKey("organizations.id"))

    # Listing details
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    tags = Column(JSON)

    # Type
    listing_type = Column(String(50))  # agent, workflow, integration, template
    resource_id = Column(String(100))

    # Pricing
    pricing_model = Column(String(50), default="free")  # free, one_time, subscription
    price = Column(Float, default=0.0)
    currency = Column(String(10), default="USD")

    # Stats
    downloads = Column(Integer, default=0)
    rating_average = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)

    # Status
    status = Column(String(50), default="draft")  # draft, pending_review, published, rejected
    published_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MarketplaceReview(Base):
    """Marketplace reviews"""
    __tablename__ = "marketplace_reviews"

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(String(50), unique=True, index=True, nullable=False)
    listing_id = Column(Integer, ForeignKey("marketplace_listings.id"))
    user_id = Column(Integer, ForeignKey("users.id"))

    # Review content
    rating = Column(Integer)  # 1-5
    title = Column(String(200))
    content = Column(Text)

    # Status
    status = Column(String(50), default="published")  # published, hidden, flagged

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================================
# Enterprise Features - Subscriptions
# ============================================================================

class SubscriptionPlan(Base):
    """Subscription plans"""
    __tablename__ = "subscription_plans"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(String(50), unique=True, index=True, nullable=False)

    # Plan details
    name = Column(String(200), nullable=False)
    description = Column(Text)
    tier = Column(String(50))  # free, starter, professional, enterprise

    # Pricing
    price_monthly = Column(Float, default=0.0)
    price_yearly = Column(Float, default=0.0)
    currency = Column(String(10), default="USD")

    # Limits
    limits = Column(JSON)  # {agents: 10, workflows: 5, api_calls: 1000}

    # Features
    features = Column(JSON)  # ["feature1", "feature2"]

    # Status
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Subscription(Base):
    """User/Organization subscriptions"""
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(String(50), unique=True, index=True, nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"))

    # Subscription details
    billing_cycle = Column(String(20), default="monthly")  # monthly, yearly
    status = Column(String(50), default="active")  # active, cancelled, past_due, trialing

    # Trial
    trial_ends_at = Column(DateTime)

    # Billing
    current_period_start = Column(DateTime)
    current_period_end = Column(DateTime)
    cancelled_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================================
# Enterprise Features - Deployments
# ============================================================================

class Deployment(Base):
    """Deployment records"""
    __tablename__ = "deployments"

    id = Column(Integer, primary_key=True, index=True)
    deployment_id = Column(String(50), unique=True, index=True, nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"))

    # Deployment details
    name = Column(String(200))
    description = Column(Text)
    environment = Column(String(50))  # development, staging, production
    version = Column(String(50))

    # Strategy
    strategy = Column(String(50), default="rolling")  # rolling, canary, blue_green
    rollout_config = Column(JSON)

    # Status
    status = Column(String(50), default="pending")  # pending, running, completed, failed, rolled_back
    progress_percent = Column(Integer, default=0)
    error_message = Column(Text)

    # Resources
    resources_deployed = Column(JSON)  # List of deployed resources

    # Timing
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================================
# Enterprise Features - SLAs
# ============================================================================

class SLADefinition(Base):
    """SLA definitions"""
    __tablename__ = "sla_definitions"

    id = Column(Integer, primary_key=True, index=True)
    sla_id = Column(String(50), unique=True, index=True, nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"))

    # SLA details
    name = Column(String(200), nullable=False)
    description = Column(Text)
    service_type = Column(String(100))

    # Targets
    uptime_target = Column(Float)  # 99.9
    response_time_target_ms = Column(Integer)
    error_rate_target = Column(Float)  # 0.1

    # Measurement
    measurement_window = Column(String(20), default="monthly")  # daily, weekly, monthly

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SLAMetric(Base):
    """SLA metrics records"""
    __tablename__ = "sla_metrics"

    id = Column(Integer, primary_key=True, index=True)
    metric_id = Column(String(50), unique=True, index=True, nullable=False)
    sla_id = Column(Integer, ForeignKey("sla_definitions.id"))

    # Metric details
    metric_type = Column(String(50))  # uptime, response_time, error_rate
    value = Column(Float)
    period_start = Column(DateTime)
    period_end = Column(DateTime)

    # Status
    target_met = Column(Boolean)

    # Timestamps
    recorded_at = Column(DateTime, default=datetime.utcnow)


class SLAViolation(Base):
    """SLA violation records"""
    __tablename__ = "sla_violations"

    id = Column(Integer, primary_key=True, index=True)
    violation_id = Column(String(50), unique=True, index=True, nullable=False)
    sla_id = Column(Integer, ForeignKey("sla_definitions.id"))

    # Violation details
    metric_type = Column(String(50))
    target_value = Column(Float)
    actual_value = Column(Float)
    duration_minutes = Column(Integer)

    # Impact
    severity = Column(String(20))  # minor, major, critical

    # Resolution
    status = Column(String(50), default="open")  # open, acknowledged, resolved
    resolution_notes = Column(Text)

    # Timestamps
    occurred_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================================
# Enterprise Features - Knowledge Base
# ============================================================================

class KBCategory(Base):
    """Knowledge base categories"""
    __tablename__ = "kb_categories"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(String(50), unique=True, index=True, nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"))

    # Category details
    name = Column(String(200), nullable=False)
    description = Column(Text)
    slug = Column(String(200))
    parent_id = Column(Integer, ForeignKey("kb_categories.id"))

    # Display
    icon = Column(String(50))
    sort_order = Column(Integer, default=0)

    # Status
    is_public = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class KBArticle(Base):
    """Knowledge base articles"""
    __tablename__ = "kb_articles"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(String(50), unique=True, index=True, nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    category_id = Column(Integer, ForeignKey("kb_categories.id"))
    author_id = Column(Integer, ForeignKey("users.id"))

    # Article content
    title = Column(String(300), nullable=False)
    slug = Column(String(300))
    content = Column(Text)
    content_format = Column(String(20), default="markdown")  # markdown, html

    # Metadata
    tags = Column(JSON)
    keywords = Column(JSON)

    # Stats
    views = Column(Integer, default=0)
    helpful_votes = Column(Integer, default=0)
    not_helpful_votes = Column(Integer, default=0)

    # Status
    status = Column(String(50), default="draft")  # draft, published, archived
    published_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================================
# Data Retention & Compliance
# ============================================================================

class DataRetentionPolicy(Base):
    """Data retention policies"""
    __tablename__ = "data_retention_policies"

    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(String(50), unique=True, index=True, nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"))

    # Policy details
    name = Column(String(200), nullable=False)
    description = Column(Text)
    data_type = Column(String(100))  # logs, executions, messages, etc.

    # Retention
    retention_days = Column(Integer, nullable=False)
    action = Column(String(50), default="delete")  # delete, archive, anonymize

    # Schedule
    is_active = Column(Boolean, default=True)
    last_run = Column(DateTime)
    next_run = Column(DateTime)

    # Stats
    records_affected = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================================
# Job Scheduling & Execution Queue
# ============================================================================

class ScheduledJob(Base):
    """Scheduled jobs for recurring or delayed execution"""
    __tablename__ = "scheduled_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # Job configuration
    job_type = Column(String(50))  # agent_execution, workflow, backup, cleanup
    target_id = Column(String(100))  # agent_id or workflow_id
    target_type = Column(String(50))  # agent, workflow

    # Schedule
    schedule_type = Column(String(50))  # cron, interval, once
    cron_expression = Column(String(100))  # "0 0 * * *" for daily
    interval_seconds = Column(Integer)
    next_run_at = Column(DateTime)
    last_run_at = Column(DateTime)

    # Status
    status = Column(String(50), default="active")  # active, paused, disabled
    run_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    max_failures = Column(Integer, default=3)  # disable after this many failures

    # Input data
    input_data = Column(JSON)

    # Ownership
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    created_by = Column(Integer, ForeignKey("users.id"))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class JobExecution(Base):
    """Individual job execution records"""
    __tablename__ = "job_executions"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(String(50), unique=True, index=True, nullable=False)
    job_id = Column(Integer, ForeignKey("scheduled_jobs.id"), index=True)

    # Execution details
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    execution_time_ms = Column(Float)

    # Results
    output_data = Column(JSON)
    error_message = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)


class ExecutionQueueItem(Base):
    """Execution queue for agents and workflows"""
    __tablename__ = "execution_queue"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(String(50), unique=True, index=True, nullable=False)

    # Target
    agent_id = Column(String(100), index=True)
    workflow_id = Column(String(100), index=True)

    # Input
    input_data = Column(JSON)

    # Queue management
    priority = Column(Integer, default=5)  # 1=highest, 10=lowest
    status = Column(String(50), default="queued", index=True)  # queued, running, completed, failed, cancelled
    progress = Column(Float, default=0.0)
    current_step = Column(String(200))

    # Scheduling
    scheduled_at = Column(DateTime)
    callback_url = Column(String(500))
    timeout_seconds = Column(Integer, default=300)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    tags = Column(JSON)

    # Execution timing
    queued_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    execution_time_ms = Column(Float)

    # Results
    result_data = Column(JSON)
    error_message = Column(Text)

    # Ownership
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    user_id = Column(Integer, ForeignKey("users.id"))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ExecutionHistory(Base):
    """Historical record of all executions"""
    __tablename__ = "execution_history"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(String(50), index=True, nullable=False)

    # What was executed
    execution_type = Column(String(50))  # agent, workflow
    agent_id = Column(String(100), index=True)
    workflow_id = Column(String(100), index=True)

    # Input/Output
    input_data = Column(JSON)
    output_data = Column(JSON)

    # Execution details
    status = Column(String(50))  # completed, failed, cancelled
    error_message = Column(Text)
    execution_time_ms = Column(Float)

    # Metadata
    tags = Column(JSON)
    priority = Column(Integer)

    # Timing
    queued_at = Column(DateTime)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Ownership
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    user_id = Column(Integer, ForeignKey("users.id"))

    # Archive timestamp
    archived_at = Column(DateTime, default=datetime.utcnow)


# ============================================================================
# Event System
# ============================================================================

class EventLog(Base):
    """System event log for audit and tracking"""
    __tablename__ = "event_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(50), unique=True, index=True, nullable=False)

    # Event details
    event_type = Column(String(100), index=True, nullable=False)  # agent.executed, workflow.completed, etc.
    severity = Column(String(20), default="info")  # debug, info, warning, error, critical
    source = Column(String(100))  # component that generated the event

    # Context
    entity_type = Column(String(50))  # agent, workflow, user, etc.
    entity_id = Column(String(100))  # ID of the related entity
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    user_id = Column(Integer, ForeignKey("users.id"))

    # Event data
    data = Column(JSON)
    message = Column(Text)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class EventSubscription(Base):
    """Subscriptions to events for webhooks/notifications"""
    __tablename__ = "event_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(String(50), unique=True, index=True, nullable=False)

    # Subscriber
    subscriber_type = Column(String(50))  # webhook, notification_channel, integration
    subscriber_id = Column(String(100))

    # Event filter
    event_types = Column(JSON)  # List of event types to subscribe to
    entity_filter = Column(JSON)  # Optional filter by entity type/id

    # Status
    status = Column(String(50), default="active")  # active, paused, disabled

    # Ownership
    organization_id = Column(Integer, ForeignKey("organizations.id"))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================================
# Notifications
# ============================================================================

class NotificationChannel(Base):
    """Notification channels (email, slack, teams, etc.)"""
    __tablename__ = "notification_channels"

    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)

    # Channel type
    channel_type = Column(String(50))  # email, slack, teams, webhook, sms
    configuration = Column(JSON)  # Channel-specific config (api keys, endpoints, etc.)

    # Status
    status = Column(String(50), default="active")  # active, disabled, failed
    last_error = Column(Text)
    last_used_at = Column(DateTime)

    # Ownership
    organization_id = Column(Integer, ForeignKey("organizations.id"))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Notification(Base):
    """Individual notifications"""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    notification_id = Column(String(50), unique=True, index=True, nullable=False)

    # Notification details
    title = Column(String(300))
    message = Column(Text)
    notification_type = Column(String(50))  # info, success, warning, error, alert

    # Delivery
    channel_id = Column(Integer, ForeignKey("notification_channels.id"))
    recipient_type = Column(String(50))  # user, team, broadcast
    recipient_id = Column(String(100))

    # Status
    status = Column(String(50), default="pending")  # pending, sent, delivered, failed
    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)
    read_at = Column(DateTime)
    error_message = Column(Text)

    # Context
    entity_type = Column(String(50))
    entity_id = Column(String(100))
    action_url = Column(String(500))

    # Ownership
    organization_id = Column(Integer, ForeignKey("organizations.id"))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)


class NotificationPreference(Base):
    """User notification preferences"""
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)

    # Preferences by type
    notification_type = Column(String(50))  # email, in_app, slack, etc.
    event_types = Column(JSON)  # List of event types to receive
    enabled = Column(Boolean, default=True)

    # Schedule
    quiet_hours_start = Column(String(10))  # "22:00"
    quiet_hours_end = Column(String(10))  # "08:00"
    timezone = Column(String(50), default="UTC")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================================
# Secrets Management
# ============================================================================

class Secret(Base):
    """Secure secrets storage"""
    __tablename__ = "secrets"

    id = Column(Integer, primary_key=True, index=True)
    secret_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # Secret data (encrypted)
    secret_type = Column(String(50))  # api_key, password, certificate, token
    encrypted_value = Column(Text, nullable=False)  # Encrypted using app secret
    encryption_version = Column(Integer, default=1)

    # Metadata
    tags = Column(JSON)
    expires_at = Column(DateTime)
    last_rotated_at = Column(DateTime)
    rotation_policy = Column(JSON)  # Auto-rotation config

    # Access control
    allowed_agents = Column(JSON)  # List of agent IDs that can access
    allowed_workflows = Column(JSON)  # List of workflow IDs that can access

    # Ownership
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    created_by = Column(Integer, ForeignKey("users.id"))

    # Status
    status = Column(String(50), default="active")  # active, expired, revoked

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SecretVersion(Base):
    """Secret version history"""
    __tablename__ = "secret_versions"

    id = Column(Integer, primary_key=True, index=True)
    secret_id = Column(Integer, ForeignKey("secrets.id"), index=True, nullable=False)
    version = Column(Integer, nullable=False)

    # Encrypted value at this version
    encrypted_value = Column(Text, nullable=False)

    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"))
    change_reason = Column(Text)

    # Status
    status = Column(String(50), default="current")  # current, deprecated, revoked

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================================
# Audit Logs
# ============================================================================

class AuditLog(Base):
    """Comprehensive audit log for compliance"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    audit_id = Column(String(50), unique=True, index=True, nullable=False)

    # Action details
    action = Column(String(100), nullable=False)  # create, update, delete, execute, login, etc.
    action_category = Column(String(50))  # user_management, data_access, system_config, etc.

    # Actor
    actor_type = Column(String(50))  # user, system, agent, api_key
    actor_id = Column(String(100))
    actor_name = Column(String(200))
    ip_address = Column(String(50))
    user_agent = Column(String(500))

    # Target
    target_type = Column(String(50))  # agent, workflow, user, organization, etc.
    target_id = Column(String(100))
    target_name = Column(String(200))

    # Change details
    old_value = Column(JSON)
    new_value = Column(JSON)
    change_summary = Column(Text)

    # Context
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    request_id = Column(String(50))  # For correlating related operations

    # Status
    status = Column(String(50))  # success, failure
    error_message = Column(Text)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


# ============================================================================
# Feature Flags & A/B Testing
# ============================================================================

class FeatureFlag(Base):
    """Feature flags for gradual rollouts"""
    __tablename__ = "feature_flags"

    id = Column(Integer, primary_key=True, index=True)
    flag_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # Flag configuration
    enabled = Column(Boolean, default=False)
    rollout_percentage = Column(Integer, default=0)  # 0-100
    targeting_rules = Column(JSON)  # Rules for who gets the flag

    # Default value
    default_value = Column(JSON)
    variants = Column(JSON)  # For multivariate flags

    # Ownership
    organization_id = Column(Integer, ForeignKey("organizations.id"))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FeatureFlagOverride(Base):
    """Per-user or per-team feature flag overrides"""
    __tablename__ = "feature_flag_overrides"

    id = Column(Integer, primary_key=True, index=True)
    flag_id = Column(Integer, ForeignKey("feature_flags.id"), index=True)

    # Override target
    target_type = Column(String(50))  # user, team, organization
    target_id = Column(String(100))

    # Override value
    enabled = Column(Boolean)
    value = Column(JSON)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ABExperiment(Base):
    """A/B experiments"""
    __tablename__ = "ab_experiments"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    hypothesis = Column(Text)

    # Experiment configuration
    status = Column(String(50), default="draft")  # draft, running, paused, completed
    variants = Column(JSON)  # [{"name": "control", "weight": 50}, {"name": "treatment", "weight": 50}]
    target_metric = Column(String(100))  # Primary metric to measure

    # Targeting
    audience_filter = Column(JSON)  # Rules for who is included
    traffic_allocation = Column(Integer, default=100)  # % of traffic in experiment

    # Duration
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    min_sample_size = Column(Integer)

    # Results
    results = Column(JSON)
    winner_variant = Column(String(50))
    statistical_significance = Column(Float)

    # Ownership
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    created_by = Column(Integer, ForeignKey("users.id"))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ABAssignment(Base):
    """User assignments to A/B experiment variants"""
    __tablename__ = "ab_assignments"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("ab_experiments.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)

    # Assignment
    variant = Column(String(50), nullable=False)
    assigned_at = Column(DateTime, default=datetime.utcnow)

    # Tracking
    exposure_logged = Column(Boolean, default=False)
    conversion_logged = Column(Boolean, default=False)
    conversion_at = Column(DateTime)


# ============================================================================
# Testing & Quality Assurance
# ============================================================================

class TestSuite(Base):
    """Test suites for agents and workflows"""
    __tablename__ = "test_suites"

    id = Column(Integer, primary_key=True, index=True)
    suite_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # Target configuration
    target_type = Column(String(50))  # agent, workflow, api
    target_id = Column(String(100))  # ID of the agent/workflow being tested

    # Test cases (JSON array)
    test_cases = Column(JSON)  # [{name, description, input, expected_output, timeout_ms}]
    total_tests = Column(Integer, default=0)

    # Configuration
    config = Column(JSON)  # Suite-level configuration
    tags = Column(JSON)

    # Ownership
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    created_by = Column(Integer, ForeignKey("users.id"))

    # Status
    status = Column(String(50), default="active")  # active, archived

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TestRun(Base):
    """Individual test run executions"""
    __tablename__ = "test_runs"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(50), unique=True, index=True, nullable=False)
    suite_id = Column(Integer, ForeignKey("test_suites.id"), index=True)

    # Execution details
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    environment = Column(String(50))  # development, staging, production

    # Results
    total_tests = Column(Integer, default=0)
    passed = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    skipped = Column(Integer, default=0)
    duration_ms = Column(Float)

    # Detailed results (JSON)
    test_results = Column(JSON)  # [{test_name, status, duration_ms, output, error}]
    summary = Column(Text)

    # Timing
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Who triggered
    triggered_by = Column(Integer, ForeignKey("users.id"))
    trigger_type = Column(String(50))  # manual, scheduled, ci_cd

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================================
# Connectors & Integrations
# ============================================================================

class Connector(Base):
    """Integration connector definitions"""
    __tablename__ = "connectors"

    id = Column(Integer, primary_key=True, index=True)
    connector_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # Connector type
    connector_type = Column(String(50))  # database, api, file, messaging
    provider = Column(String(100))  # postgres, mysql, salesforce, s3, etc.

    # Configuration schema
    config_schema = Column(JSON)  # JSON schema for configuration
    auth_type = Column(String(50))  # oauth, api_key, basic, none

    # Status
    status = Column(String(50), default="available")  # available, deprecated, coming_soon

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ConnectorInstance(Base):
    """Configured connector instances"""
    __tablename__ = "connector_instances"

    id = Column(Integer, primary_key=True, index=True)
    instance_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    connector_id = Column(Integer, ForeignKey("connectors.id"))

    # Configuration (encrypted credentials)
    configuration = Column(JSON)  # Non-sensitive config
    credentials_secret_id = Column(Integer, ForeignKey("secrets.id"))  # Reference to encrypted credentials

    # Connection status
    status = Column(String(50), default="configured")  # configured, connected, failed, disconnected
    last_connected_at = Column(DateTime)
    last_error = Column(Text)

    # Health check
    health_check_enabled = Column(Boolean, default=True)
    last_health_check_at = Column(DateTime)
    health_status = Column(String(50))  # healthy, degraded, unhealthy

    # Ownership
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    created_by = Column(Integer, ForeignKey("users.id"))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class IntegrationProvider(Base):
    """Pre-built external service providers (GitHub, Slack, Jira, etc.)"""
    __tablename__ = "integration_providers"

    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(String(50), unique=True, index=True, nullable=False)

    # Provider identity
    name = Column(String(200), nullable=False)
    display_name = Column(String(200))
    description = Column(Text)
    category = Column(String(50))  # communication, dev_tools, productivity, crm, analytics
    icon_url = Column(String(500))

    # OAuth configuration
    oauth_enabled = Column(Boolean, default=False)
    oauth_authorization_url = Column(String(500))
    oauth_token_url = Column(String(500))
    oauth_scopes = Column(JSON)  # Available OAuth scopes

    # API configuration
    api_base_url = Column(String(500))
    api_version = Column(String(50))
    rate_limit_requests = Column(Integer)
    rate_limit_period_seconds = Column(Integer)

    # Webhook configuration
    webhook_support = Column(Boolean, default=False)
    webhook_events = Column(JSON)  # Available webhook event types

    # Capabilities
    capabilities = Column(JSON)  # List of supported operations
    required_scopes = Column(JSON)  # Scopes needed for each capability

    # Documentation
    docs_url = Column(String(500))
    setup_guide = Column(Text)

    # Status
    status = Column(String(50), default="active")  # active, beta, deprecated, maintenance

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class IntegrationConnection(Base):
    """OAuth/API connections to external services"""
    __tablename__ = "integration_connections"

    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(String(50), unique=True, index=True, nullable=False)

    # Provider reference
    provider_id = Column(Integer, ForeignKey("integration_providers.id"), index=True)

    # Connection identity
    name = Column(String(200))
    external_account_id = Column(String(200))  # Account ID from external service
    external_account_name = Column(String(200))  # Display name from external service

    # OAuth tokens (stored securely)
    access_token_secret_id = Column(Integer, ForeignKey("secrets.id"))
    refresh_token_secret_id = Column(Integer, ForeignKey("secrets.id"))
    token_expires_at = Column(DateTime)
    granted_scopes = Column(JSON)  # Scopes granted during OAuth

    # API Key auth (alternative to OAuth)
    api_key_secret_id = Column(Integer, ForeignKey("secrets.id"))

    # Connection status
    status = Column(String(50), default="active")  # pending, active, expired, revoked, failed
    last_used_at = Column(DateTime)
    last_error = Column(Text)
    error_count = Column(Integer, default=0)

    # Rate limiting state
    rate_limit_remaining = Column(Integer)
    rate_limit_reset_at = Column(DateTime)

    # Ownership
    organization_id = Column(Integer, ForeignKey("organizations.id"), index=True)
    created_by = Column(Integer, ForeignKey("users.id"))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class IntegrationWebhook(Base):
    """Inbound/outbound webhooks for integrations"""
    __tablename__ = "integration_webhooks"

    id = Column(Integer, primary_key=True, index=True)
    webhook_id = Column(String(50), unique=True, index=True, nullable=False)

    # Association
    connection_id = Column(Integer, ForeignKey("integration_connections.id"), index=True)
    provider_id = Column(Integer, ForeignKey("integration_providers.id"), index=True)

    # Webhook identity
    name = Column(String(200))
    description = Column(Text)
    direction = Column(String(20))  # inbound, outbound

    # Configuration
    endpoint_url = Column(String(500))  # For outbound: target URL; For inbound: our generated URL
    secret_key = Column(String(200))  # Webhook signature verification key
    events = Column(JSON)  # List of event types to trigger/receive

    # Filtering
    filters = Column(JSON)  # Event filtering rules
    transform_template = Column(Text)  # Payload transformation template

    # Retry policy (for outbound)
    retry_enabled = Column(Boolean, default=True)
    max_retries = Column(Integer, default=3)
    retry_delay_seconds = Column(Integer, default=60)

    # Statistics
    total_deliveries = Column(Integer, default=0)
    successful_deliveries = Column(Integer, default=0)
    failed_deliveries = Column(Integer, default=0)
    last_triggered_at = Column(DateTime)

    # Status
    status = Column(String(50), default="active")  # active, paused, disabled

    # Ownership
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    created_by = Column(Integer, ForeignKey("users.id"))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class IntegrationWebhookDelivery(Base):
    """Webhook delivery history and status"""
    __tablename__ = "integration_webhook_deliveries"

    id = Column(Integer, primary_key=True, index=True)
    delivery_id = Column(String(50), unique=True, index=True, nullable=False)
    webhook_id = Column(Integer, ForeignKey("integration_webhooks.id"), index=True)

    # Delivery details
    event_type = Column(String(100))
    payload = Column(JSON)

    # Request details (for outbound)
    request_url = Column(String(500))
    request_headers = Column(JSON)
    request_body = Column(Text)

    # Response details
    response_status_code = Column(Integer)
    response_headers = Column(JSON)
    response_body = Column(Text)
    response_time_ms = Column(Integer)

    # Status
    status = Column(String(50))  # pending, success, failed, retrying
    attempt_count = Column(Integer, default=1)
    error_message = Column(Text)
    next_retry_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime)


class IntegrationSyncJob(Base):
    """Scheduled sync jobs between systems"""
    __tablename__ = "integration_sync_jobs"

    id = Column(Integer, primary_key=True, index=True)
    sync_job_id = Column(String(50), unique=True, index=True, nullable=False)

    # Association
    connection_id = Column(Integer, ForeignKey("integration_connections.id"), index=True)

    # Job identity
    name = Column(String(200))
    description = Column(Text)

    # Sync configuration
    sync_type = Column(String(50))  # full, incremental, bidirectional
    source_entity = Column(String(100))  # Entity type in source (e.g., "issues", "contacts")
    target_entity = Column(String(100))  # Entity type in target
    field_mapping = Column(JSON)  # Field mapping configuration
    filters = Column(JSON)  # Data filtering rules

    # Schedule
    schedule_type = Column(String(50))  # manual, cron, interval, realtime
    schedule_cron = Column(String(100))  # Cron expression if cron type
    schedule_interval_minutes = Column(Integer)  # Interval in minutes

    # State tracking
    last_sync_at = Column(DateTime)
    last_sync_status = Column(String(50))  # success, partial, failed
    last_sync_records_processed = Column(Integer)
    last_sync_records_created = Column(Integer)
    last_sync_records_updated = Column(Integer)
    last_sync_records_failed = Column(Integer)
    last_sync_cursor = Column(String(500))  # Cursor for incremental sync

    # Error handling
    error_handling_mode = Column(String(50))  # skip, fail, retry
    last_error = Column(Text)
    consecutive_failures = Column(Integer, default=0)

    # Status
    status = Column(String(50), default="active")  # active, paused, disabled, running
    next_run_at = Column(DateTime)

    # Ownership
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    created_by = Column(Integer, ForeignKey("users.id"))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class IntegrationSyncRun(Base):
    """History of sync job executions"""
    __tablename__ = "integration_sync_runs"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(50), unique=True, index=True, nullable=False)
    sync_job_id = Column(Integer, ForeignKey("integration_sync_jobs.id"), index=True)

    # Run details
    trigger_type = Column(String(50))  # scheduled, manual, webhook
    triggered_by = Column(Integer, ForeignKey("users.id"))

    # Progress tracking
    status = Column(String(50))  # running, completed, failed, cancelled
    progress_percent = Column(Integer, default=0)
    current_phase = Column(String(100))

    # Statistics
    records_processed = Column(Integer, default=0)
    records_created = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_deleted = Column(Integer, default=0)
    records_skipped = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)

    # Error details
    errors = Column(JSON)  # Array of error records

    # Timing
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer)


class IntegrationEventLog(Base):
    """Activity logs for integration events"""
    __tablename__ = "integration_event_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(50), unique=True, index=True, nullable=False)

    # Event source
    provider_id = Column(Integer, ForeignKey("integration_providers.id"), index=True)
    connection_id = Column(Integer, ForeignKey("integration_connections.id"), index=True)
    webhook_id = Column(Integer, ForeignKey("integration_webhooks.id"))
    sync_job_id = Column(Integer, ForeignKey("integration_sync_jobs.id"))

    # Event details
    event_type = Column(String(100), index=True)  # oauth.connected, webhook.received, sync.completed, etc.
    event_category = Column(String(50))  # auth, webhook, sync, error, rate_limit
    severity = Column(String(20))  # info, warning, error

    # Event data
    message = Column(Text)
    details = Column(JSON)

    # Actor
    actor_type = Column(String(50))  # user, system, webhook
    actor_id = Column(String(100))

    # Request context
    request_id = Column(String(100))
    ip_address = Column(String(50))

    # Organization
    organization_id = Column(Integer, ForeignKey("organizations.id"), index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class IntegrationDataMapping(Base):
    """Reusable data mapping configurations"""
    __tablename__ = "integration_data_mappings"

    id = Column(Integer, primary_key=True, index=True)
    mapping_id = Column(String(50), unique=True, index=True, nullable=False)

    # Mapping identity
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # Source/Target
    source_provider_id = Column(Integer, ForeignKey("integration_providers.id"))
    source_entity = Column(String(100))
    target_entity = Column(String(100))

    # Mapping configuration
    field_mappings = Column(JSON)  # Array of {source_field, target_field, transform}
    default_values = Column(JSON)  # Default values for target fields
    computed_fields = Column(JSON)  # Dynamically computed fields

    # Validation
    validation_rules = Column(JSON)  # Data validation rules

    # Status
    status = Column(String(50), default="active")

    # Ownership
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    created_by = Column(Integer, ForeignKey("users.id"))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================================
# Agent Memory & Context
# ============================================================================

class AgentMemory(Base):
    """Persistent memory for agents"""
    __tablename__ = "agent_memories"

    id = Column(Integer, primary_key=True, index=True)
    memory_id = Column(String(50), unique=True, index=True, nullable=False)
    agent_id = Column(Integer, ForeignKey("agents.id"), index=True)

    # Memory type
    memory_type = Column(String(50))  # short_term, long_term, episodic, semantic
    scope = Column(String(50))  # session, user, global

    # Content
    key = Column(String(200))
    value = Column(JSON)
    embedding = Column(JSON)  # Vector embedding for semantic search

    # Context
    session_id = Column(String(100))
    user_id = Column(Integer, ForeignKey("users.id"))

    # Metadata
    importance = Column(Float, default=1.0)
    access_count = Column(Integer, default=0)
    last_accessed_at = Column(DateTime)
    expires_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ConversationContext(Base):
    """Conversation context and state"""
    __tablename__ = "conversation_contexts"

    id = Column(Integer, primary_key=True, index=True)
    context_id = Column(String(50), unique=True, index=True, nullable=False)
    conversation_id = Column(Integer, ForeignKey("ai_conversations.id"), index=True)

    # Context data
    context_type = Column(String(50))  # user_info, task_state, preferences
    data = Column(JSON)

    # TTL
    expires_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================================
# Batch Processing
# ============================================================================

class BatchJob(Base):
    """Batch processing jobs"""
    __tablename__ = "batch_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # Job type
    job_type = Column(String(50))  # agent_batch, data_import, data_export, analysis

    # Input
    input_source = Column(String(100))  # file, api, database
    input_location = Column(String(500))  # path or URL
    input_format = Column(String(50))  # json, csv, jsonl
    total_items = Column(Integer)

    # Processing
    agent_id = Column(Integer, ForeignKey("agents.id"))
    workflow_id = Column(Integer, ForeignKey("workflows.id"))
    batch_size = Column(Integer, default=100)
    concurrency = Column(Integer, default=5)

    # Progress
    status = Column(String(50), default="pending")  # pending, running, paused, completed, failed
    processed_items = Column(Integer, default=0)
    successful_items = Column(Integer, default=0)
    failed_items = Column(Integer, default=0)
    progress_percentage = Column(Float, default=0.0)

    # Timing
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    estimated_completion = Column(DateTime)

    # Output
    output_location = Column(String(500))
    error_log_location = Column(String(500))

    # Ownership
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    created_by = Column(Integer, ForeignKey("users.id"))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class BatchResult(Base):
    """Individual batch job results"""
    __tablename__ = "batch_results"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("batch_jobs.id"), index=True)
    item_index = Column(Integer)

    # Result
    status = Column(String(50))  # success, failed, skipped
    input_data = Column(JSON)
    output_data = Column(JSON)
    error_message = Column(Text)

    # Timing
    processed_at = Column(DateTime, default=datetime.utcnow)
    processing_time_ms = Column(Float)


# ============================================================================
# Database Utilities
# ============================================================================

def init_db():
    """Initialize database - create all tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully")


def get_db():
    """Get database session (for FastAPI dependency injection)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def seed_agents():
    """Seed database with all APQC agent definitions from generated_agents_v2"""
    import os
    import re
    from pathlib import Path

    db = SessionLocal()

    # Check if agents already exist
    if db.query(Agent).count() > 0:
        print(f"✅ Agents already seeded ({db.query(Agent).count()} agents)")
        db.close()
        return

    # Path to generated agents
    agents_dir = Path(__file__).parent.parent / "generated_agents_v2"
    if not agents_dir.exists():
        print("⚠️  generated_agents_v2 directory not found, seeding minimal agents")
        agents = get_minimal_agents()
    else:
        agents = scan_and_load_agents(agents_dir)

    if agents:
        db.add_all(agents)
        db.commit()
        print(f"✅ Seeded {len(agents)} agents")

    db.close()


def scan_and_load_agents(agents_dir):
    """Scan the generated_agents_v2 directory and create Agent objects"""
    from pathlib import Path
    import re

    agents = []
    category_map = {
        "asset_management": "Manage Assets",
        "business_capabilities": "Develop Business Capabilities",
        "customer_service": "Serve Customers",
        "external_relations": "Manage External Relations",
        "finance": "Manage Financial Resources",
        "human_resources": "Manage Human Capital",
        "information_technology": "Manage Information Technology",
        "product_management": "Manage Product Development",
        "risk_compliance": "Manage Risk & Compliance",
        "sales_marketing": "Manage Sales and Marketing",
        "service_delivery": "Deliver Service",
        "strategy": "Develop Strategy & Manage Enterprise Transformation",
        "supply_chain": "Manage Supply Chain"
    }

    # Scan all subdirectories (categories)
    for category_dir in sorted(agents_dir.iterdir()):
        if not category_dir.is_dir():
            continue

        category_name = category_dir.name
        category_label = category_map.get(category_name, category_name.replace("_", " ").title())
        agent_counter = {}  # Track ID suffix for functional names

        # Scan all Python files in category
        for agent_file in sorted(category_dir.glob("*.py")):
            if agent_file.name.startswith("__"):
                continue

            filename = agent_file.stem

            # Try to extract APQC ID first
            # Format: "9_1_2_3_agent.py" or similar
            match = re.match(r"^(\d+)_(\d+)_(\d+)_(\d+)", filename)

            if match:
                # Standard APQC ID format
                apqc_id = f"{match.group(1)}.{match.group(2)}.{match.group(3)}.{match.group(4)}"
                agent_name = f"APQC {apqc_id} - {category_label} Agent"
                agent_id = f"{category_name}_{apqc_id.replace('.', '_')}"
            else:
                # Functional name format: "allocate_costs_manage_agent.py"
                # Extract the functional part (remove "_manage_agent" suffix if present)
                functional_name = filename
                if functional_name.endswith("_manage_agent"):
                    functional_name = functional_name[:-13]  # Remove "_manage_agent"
                elif functional_name.endswith("_agent"):
                    functional_name = functional_name[:-6]   # Remove "_agent"

                # Convert to readable name
                readable_name = functional_name.replace("_", " ").title()
                agent_name = f"{readable_name} - {category_label}"

                # Generate a unique agent ID
                base_id = f"{category_name}_{functional_name}"
                agent_counter[base_id] = agent_counter.get(base_id, 0) + 1
                agent_id = f"{base_id}_{agent_counter[base_id]}" if agent_counter[base_id] > 1 else base_id

                apqc_id = None  # No APQC ID for functional agents

            # Create agent
            agent = Agent(
                agent_id=agent_id,
                name=agent_name,
                description=f"Autonomous agent for {category_label.lower()}",
                apqc_id=apqc_id,
                apqc_category=category_label,
                agent_type="atomic",
                version="1.0.0",
                is_active=True
            )
            agents.append(agent)

    return agents


def get_minimal_agents():
    """Fallback: Seed the 4 base invoice agents"""
    return [
        Agent(
            agent_id="9.1.1.6",
            name="Extract Invoice Data",
            description="Gather financial data from invoice sources",
            apqc_id="9.1.1.6",
            apqc_category="Manage Financial Resources",
            agent_type="atomic",
            version="1.0.0"
        ),
        Agent(
            agent_id="9.1.1.7",
            name="Validate Invoice Data",
            description="Validate invoice data accuracy",
            apqc_id="9.1.1.7",
            apqc_category="Manage Financial Resources",
            agent_type="atomic",
            version="1.0.0"
        ),
        Agent(
            agent_id="9.1.1.8",
            name="Calculate Invoice Totals",
            description="Perform invoice calculations",
            apqc_id="9.1.1.8",
            apqc_category="Manage Financial Resources",
            agent_type="atomic",
            version="1.0.0"
        ),
        Agent(
            agent_id="9.1.1.9",
            name="Generate Approval Recommendation",
            description="Plan reporting and approval recommendations",
            apqc_id="9.1.1.9",
            apqc_category="Manage Financial Resources",
            agent_type="atomic",
            version="1.0.0"
        )
    ]


if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    seed_agents()
    print("✅ Database setup complete!")
