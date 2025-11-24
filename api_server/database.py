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
