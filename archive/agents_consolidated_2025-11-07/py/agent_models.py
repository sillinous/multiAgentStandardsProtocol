from __future__ import annotations

from sqlalchemy import Column, String, DateTime, JSON, Float, ForeignKey
from sqlalchemy.orm import declarative_base
from datetime import datetime
import uuid


Base = declarative_base()


def _uuid() -> str:
    return str(uuid.uuid4())


class Agent(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=False)
    status = Column(String, nullable=False, default="idle")
    config = Column(JSON, nullable=False, default=dict)
    schedule_interval_sec = Column(Float, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(String, primary_key=True, default=_uuid)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    status = Column(String, nullable=False, default="queued")
    result = Column(JSON, nullable=False, default=dict)


class AgentLog(Base):
    __tablename__ = "agent_logs"

    id = Column(String, primary_key=True, default=_uuid)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    level = Column(String, nullable=False, default="info")
    message = Column(String, nullable=False, default="")
    meta = Column(JSON, nullable=False, default=dict)
