from __future__ import annotations

from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.schemas.agent_schemas import (
    AgentCreate,
    AgentUpdate,
    AgentOut,
    AgentStatus,
    AgentLogOut,
    AgentRunOut,
)
from app.models.agent_models import Agent, AgentLog, AgentRun, Base
from app.services.scheduler import global_scheduler


router = APIRouter()

# NOTE: For a minimal, self-contained iteration we create a local SQLite engine.
# If the project already has a shared engine/session, swap to that here.
engine = create_engine("sqlite:///./agents.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


@router.get("/", response_model=List[AgentOut])
def list_agents() -> List[AgentOut]:
    db = SessionLocal()
    try:
        items = db.query(Agent).all()
        return [
            AgentOut(
                id=a.id,
                name=a.name,
                status=a.status,  # type: ignore[arg-type]
                config=a.config,
                created_at=a.created_at,
                updated_at=a.updated_at,
                schedule_interval_sec=a.schedule_interval_sec,
            )
            for a in items
        ]
    finally:
        db.close()


@router.post("/", response_model=AgentOut)
def create_agent(payload: AgentCreate) -> AgentOut:
    db = SessionLocal()
    try:
        a = Agent(name=payload.name, config=payload.config, schedule_interval_sec=payload.schedule_interval_sec)
        db.add(a)
        db.commit()
        db.refresh(a)
        # set up scheduled task if any
        if a.schedule_interval_sec and a.schedule_interval_sec > 0:
            global_scheduler.add_task(
                name=f"agent:{a.id}", interval_sec=a.schedule_interval_sec, fn=lambda: None
            )
            global_scheduler.start()
        return AgentOut(
            id=a.id,
            name=a.name,
            status=a.status,  # type: ignore[arg-type]
            config=a.config,
            created_at=a.created_at,
            updated_at=a.updated_at,
            schedule_interval_sec=a.schedule_interval_sec,
        )
    finally:
        db.close()


@router.get("/{agent_id}", response_model=AgentOut)
def get_agent(agent_id: str) -> AgentOut:
    db = SessionLocal()
    try:
        a = db.query(Agent).get(agent_id)
        if not a:
            raise HTTPException(status_code=404, detail="Agent not found")
        return AgentOut(
            id=a.id,
            name=a.name,
            status=a.status,  # type: ignore[arg-type]
            config=a.config,
            created_at=a.created_at,
            updated_at=a.updated_at,
            schedule_interval_sec=a.schedule_interval_sec,
        )
    finally:
        db.close()


@router.patch("/{agent_id}", response_model=AgentOut)
def update_agent(agent_id: str, payload: AgentUpdate) -> AgentOut:
    db = SessionLocal()
    try:
        a = db.query(Agent).get(agent_id)
        if not a:
            raise HTTPException(status_code=404, detail="Agent not found")
        if payload.name is not None:
            a.name = payload.name
        if payload.config is not None:
            a.config = payload.config
        if payload.status is not None:
            a.status = payload.status
        if payload.schedule_interval_sec is not None:
            a.schedule_interval_sec = payload.schedule_interval_sec
        a.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(a)
        return AgentOut(
            id=a.id,
            name=a.name,
            status=a.status,  # type: ignore[arg-type]
            config=a.config,
            created_at=a.created_at,
            updated_at=a.updated_at,
            schedule_interval_sec=a.schedule_interval_sec,
        )
    finally:
        db.close()


@router.delete("/{agent_id}")
def delete_agent(agent_id: str) -> dict:
    db = SessionLocal()
    try:
        a = db.query(Agent).get(agent_id)
        if not a:
            raise HTTPException(status_code=404, detail="Agent not found")
        db.delete(a)
        db.commit()
        global_scheduler.remove_task(f"agent:{agent_id}")
        return {"ok": True}
    finally:
        db.close()


@router.post("/{agent_id}/start")
def start_agent(agent_id: str) -> dict:
    db = SessionLocal()
    try:
        a = db.query(Agent).get(agent_id)
        if not a:
            raise HTTPException(status_code=404, detail="Agent not found")
        a.status = "running"
        a.updated_at = datetime.utcnow()
        db.commit()
        return {"status": a.status}
    finally:
        db.close()


@router.post("/{agent_id}/stop")
def stop_agent(agent_id: str) -> dict:
    db = SessionLocal()
    try:
        a = db.query(Agent).get(agent_id)
        if not a:
            raise HTTPException(status_code=404, detail="Agent not found")
        a.status = "stopped"
        a.updated_at = datetime.utcnow()
        db.commit()
        return {"status": a.status}
    finally:
        db.close()


@router.post("/{agent_id}/trigger", response_model=AgentRunOut)
def trigger_run(agent_id: str) -> AgentRunOut:
    db = SessionLocal()
    try:
        a = db.query(Agent).get(agent_id)
        if not a:
            raise HTTPException(status_code=404, detail="Agent not found")
        run = AgentRun(agent_id=a.id, status="running")
        db.add(run)
        db.commit()
        db.refresh(run)
        # Immediately finish with a stub result for this iteration
        run.status = "success"
        run.finished_at = datetime.utcnow()
        run.result = {"ok": True}
        db.commit()
        db.refresh(run)
        # Log entry
        log = AgentLog(agent_id=a.id, level="info", message="Run completed", meta={"run_id": run.id})
        db.add(log)
        db.commit()
        return AgentRunOut(
            id=run.id,
            agent_id=a.id,
            started_at=run.started_at,
            finished_at=run.finished_at,
            status="success",
            result=run.result,
        )
    finally:
        db.close()


@router.get("/{agent_id}/status", response_model=AgentStatus)
def get_status(agent_id: str) -> AgentStatus:
    db = SessionLocal()
    try:
        a = db.query(Agent).get(agent_id)
        if not a:
            raise HTTPException(status_code=404, detail="Agent not found")
        return AgentStatus(id=a.id, status=a.status, last_heartbeat=None)
    finally:
        db.close()


@router.get("/{agent_id}/logs", response_model=List[AgentLogOut])
def get_logs(agent_id: str) -> List[AgentLogOut]:
    db = SessionLocal()
    try:
        logs = db.query(AgentLog).filter(AgentLog.agent_id == agent_id).order_by(AgentLog.timestamp.desc()).limit(200).all()
        return [
            AgentLogOut(
                id=l.id,
                agent_id=l.agent_id,
                timestamp=l.timestamp,
                level=l.level,  # type: ignore[arg-type]
                message=l.message,
                meta=l.meta,
            )
            for l in logs
        ]
    finally:
        db.close()

