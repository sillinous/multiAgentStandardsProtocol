"""
Database Models for Agent Platform
====================================

SQLAlchemy models for storing agent executions, workflows, and results.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
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
