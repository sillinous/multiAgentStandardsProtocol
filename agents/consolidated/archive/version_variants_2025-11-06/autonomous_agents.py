"""
Database models for Autonomous Agent Management System
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.user import Base
import enum


class AgentStatus(str, enum.Enum):
    """Agent status enum"""
    IDLE = "idle"
    ACTIVE = "active"
    BUSY = "busy"
    ERROR = "error"
    TERMINATED = "terminated"


class TaskStatus(str, enum.Enum):
    """Task status enum"""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, enum.Enum):
    """Task priority enum"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AutonomousAgent(Base):
    """
    Autonomous Agent record
    Tracks agent instances, their status, and performance metrics
    """
    __tablename__ = "autonomous_agents"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String(100), unique=True, index=True, nullable=False)
    agent_type = Column(String(50), nullable=False, index=True)
    status = Column(Enum(AgentStatus), default=AgentStatus.IDLE, nullable=False, index=True)

    # Configuration
    capabilities = Column(JSON, default=list)  # List of AgentCapability values
    config = Column(JSON, default=dict)  # Agent-specific configuration
    workspace_path = Column(String(500), nullable=False)

    # Tracking
    current_iteration = Column(Integer, default=0)
    tasks_completed = Column(Integer, default=0)
    tasks_failed = Column(Integer, default=0)
    total_processing_time = Column(Float, default=0.0)  # Total seconds spent processing

    # Performance metrics
    success_rate = Column(Float, default=0.0)  # Percentage of successful tasks
    average_task_time = Column(Float, default=0.0)  # Average seconds per task
    quality_score = Column(Float, default=0.0)  # Quality assessment (0-1)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_active_at = Column(DateTime(timezone=True))
    terminated_at = Column(DateTime(timezone=True))

    # Additional info
    agent_metadata = Column(JSON, default=dict)  # Flexible metadata storage
    error_log = Column(Text)  # Error messages if status=ERROR

    # Relationships
    tasks = relationship("AgentTask", back_populates="agent", cascade="all, delete-orphan")
    messages = relationship("AgentMessage", back_populates="agent", cascade="all, delete-orphan")
    iterations = relationship("AgentIteration", back_populates="agent", cascade="all, delete-orphan")


class AgentTask(Base):
    """
    Agent Task record
    Tracks tasks assigned to agents and their execution
    """
    __tablename__ = "agent_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(100), unique=True, index=True, nullable=False)
    agent_id = Column(Integer, ForeignKey("autonomous_agents.id"), nullable=False, index=True)

    # Task details
    task_type = Column(String(100), nullable=False, index=True)
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False, index=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.QUEUED, nullable=False, index=True)

    # Task data
    task_data = Column(JSON, nullable=False)  # Input data for the task
    result = Column(JSON)  # Task execution result
    error_message = Column(Text)  # Error details if failed

    # Timing
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    processing_time = Column(Float)  # Seconds taken to complete

    # Relationships
    agent = relationship("AutonomousAgent", back_populates="tasks")


class AgentMessage(Base):
    """
    Agent Communication Messages
    Tracks messages sent/received by agents
    """
    __tablename__ = "agent_messages"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String(100), unique=True, index=True, nullable=False)
    agent_id = Column(Integer, ForeignKey("autonomous_agents.id"), nullable=False, index=True)

    # Message details
    message_type = Column(String(50), nullable=False, index=True)  # MessageType enum value
    content = Column(JSON, nullable=False)

    # Communication metadata
    sender_agent_id = Column(String(100))  # If from another agent
    recipient_agent_id = Column(String(100))  # If to another agent
    conversation_id = Column(String(100), index=True)  # Group related messages

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    agent = relationship("AutonomousAgent", back_populates="messages")


class AgentIteration(Base):
    """
    Agent Improvement Iterations
    Tracks self-improvement cycles and their results
    """
    __tablename__ = "agent_iterations"

    id = Column(Integer, primary_key=True, index=True)
    iteration_id = Column(String(100), unique=True, index=True, nullable=False)
    agent_id = Column(Integer, ForeignKey("autonomous_agents.id"), nullable=False, index=True)

    # Iteration details
    iteration_number = Column(Integer, nullable=False)
    cycle_type = Column(String(50))  # supervised, autonomous, manual

    # Results
    improvements_made = Column(JSON, default=list)  # List of improvements
    issues_found = Column(JSON, default=list)  # List of issues identified
    agents_generated = Column(Integer, default=0)  # Agents created in this cycle

    # Performance
    duration = Column(Float)  # Seconds
    success = Column(Integer, default=1)  # 1=success, 0=failure
    quality_delta = Column(Float)  # Change in quality score

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True))
    summary = Column(Text)  # Human-readable summary
    detailed_log = Column(JSON)  # Full iteration log

    # Relationships
    agent = relationship("AutonomousAgent", back_populates="iterations")


class AgentFactory(Base):
    """
    Agent Factory Generation Records
    Tracks agents generated by the agent factory
    """
    __tablename__ = "agent_factory_generations"

    id = Column(Integer, primary_key=True, index=True)
    generation_id = Column(String(100), unique=True, index=True, nullable=False)

    # Generation request
    requested_count = Column(Integer, nullable=False)
    priority_categories = Column(JSON)  # APQC categories
    requirements = Column(JSON)  # Requirements analysis input

    # Generation results
    agents_generated = Column(JSON, default=list)  # List of agent_ids generated
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)

    # Performance
    duration = Column(Float)  # Seconds taken
    cost_estimate = Column(Float)  # Estimated API cost

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True))
    created_by = Column(String(100))  # User or system that triggered

    # Results
    generation_log = Column(JSON)  # Detailed generation log
    error_log = Column(Text)  # Errors encountered


class OrchestratorCycle(Base):
    """
    Orchestrator Improvement Cycles
    Tracks autonomous improvement cycles run by orchestrator
    """
    __tablename__ = "orchestrator_cycles"

    id = Column(Integer, primary_key=True, index=True)
    cycle_id = Column(String(100), unique=True, index=True, nullable=False)

    # Cycle configuration
    mode = Column(String(20), nullable=False)  # supervised, autonomous
    max_cycles = Column(Integer, nullable=False)
    agents_per_cycle = Column(Integer, nullable=False)

    # Execution
    cycles_completed = Column(Integer, default=0)
    agents_generated = Column(Integer, default=0)
    improvements_made = Column(JSON, default=list)

    # Status
    status = Column(String(20), default="running", index=True)  # running, completed, stopped, error
    system_optimal = Column(Integer, default=0)  # 1=optimal, 0=not optimal

    # Performance
    duration = Column(Float)  # Total seconds
    total_cost = Column(Float)  # Total API cost

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    # Results
    summary = Column(Text)
    detailed_results = Column(JSON)
    cycle_history = Column(JSON)  # History of each cycle iteration
