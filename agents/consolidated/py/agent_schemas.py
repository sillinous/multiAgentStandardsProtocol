from __future__ import annotations

from typing import Any, Dict, Optional, Literal, List
from pydantic import BaseModel, Field
from datetime import datetime


AgentStatusType = Literal["idle", "running", "stopped", "error"]


class AgentCreate(BaseModel):
    name: str
    config: Dict[str, Any] = Field(default_factory=dict)
    schedule_interval_sec: Optional[float] = None


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    status: Optional[AgentStatusType] = None
    schedule_interval_sec: Optional[float] = None


class AgentOut(BaseModel):
    id: str
    name: str
    status: AgentStatusType
    config: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    schedule_interval_sec: Optional[float] = None


class AgentStatus(BaseModel):
    id: str
    status: AgentStatusType
    last_heartbeat: Optional[datetime] = None


class AgentLogOut(BaseModel):
    id: str
    agent_id: str
    timestamp: datetime
    level: Literal["debug", "info", "warning", "error"]
    message: str
    meta: Dict[str, Any] = Field(default_factory=dict)


class AgentRunOut(BaseModel):
    id: str
    agent_id: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    status: Literal["queued", "running", "success", "failed"]
    result: Dict[str, Any] = Field(default_factory=dict)

