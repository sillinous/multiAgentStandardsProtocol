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
    """Seed database with agent definitions"""
    db = SessionLocal()

    # Check if agents already exist
    if db.query(Agent).count() > 0:
        print("Agents already seeded")
        db.close()
        return

    # Seed the 4 invoice agents we built
    agents = [
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

    db.add_all(agents)
    db.commit()
    print(f"✅ Seeded {len(agents)} agents")
    db.close()


if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    seed_agents()
    print("✅ Database setup complete!")
