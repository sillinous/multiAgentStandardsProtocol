"""
🤖 RuntimeAgent - Autonomous Agent Runtime Wrapper
===================================================

Wraps any BaseAgent implementation with:
- Autonomous behavior loop
- Task queue for receiving work
- State machine (idle, working, paused, stopped)
- Lifecycle management
- Health monitoring

This transforms static agent classes into living, breathing autonomous entities!

Usage:
    from superstandard.agents.analysis.analytics_agent_v1 import AnalyticsAgent
    from superstandard.agents.runtime import RuntimeAgent

    agent = AnalyticsAgent()
    runtime = RuntimeAgent(agent)
    await runtime.start()  # Agent now runs autonomously!

    # Assign work
    await runtime.submit_task({"type": "analyze", "data": {...}})

    # Control lifecycle
    await runtime.pause()
    await runtime.resume()
    await runtime.stop()
"""

import asyncio
import logging
from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
import uuid

logger = logging.getLogger(__name__)


class AgentState(Enum):
    """Agent runtime states"""
    CREATED = "created"      # Just instantiated
    STARTING = "starting"    # Starting up
    IDLE = "idle"            # Running, waiting for tasks
    WORKING = "working"      # Executing a task
    PAUSED = "paused"        # Paused by operator
    STOPPING = "stopping"    # Shutting down
    STOPPED = "stopped"      # Fully stopped
    ERROR = "error"          # Error state


@dataclass
class TaskQueueItem:
    """Item in agent's task queue"""
    task_id: str
    task: Dict[str, Any]
    submitted_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class RuntimeAgent:
    """
    Runtime wrapper that gives agents autonomous behavior.

    Wraps any BaseAgent subclass and provides:
    - Continuous execution loop
    - Task queue processing
    - State management
    - Health monitoring
    - Lifecycle control
    """

    def __init__(self, agent_instance, max_queue_size: int = 100):
        """
        Initialize runtime wrapper around an agent instance.

        Args:
            agent_instance: Instance of BaseAgent subclass
            max_queue_size: Maximum tasks in queue
        """
        self.agent = agent_instance
        self.agent_id = agent_instance.agent_id
        self.agent_type = agent_instance.agent_type

        # Runtime state
        self.state = AgentState.CREATED
        self.task_queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self.current_task: Optional[TaskQueueItem] = None
        self.completed_tasks: list[TaskQueueItem] = []

        # Lifecycle management
        self.behavior_loop_task: Optional[asyncio.Task] = None
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.should_run = False

        # Statistics
        self.stats = {
            "created_at": datetime.utcnow(),
            "started_at": None,
            "stopped_at": None,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "total_execution_time": 0.0,
            "heartbeats_sent": 0
        }

        logger.info(f"[{self.agent_id}] RuntimeAgent created (state: {self.state.value})")

    async def start(self):
        """Start the agent's autonomous behavior loop"""
        if self.state != AgentState.CREATED and self.state != AgentState.STOPPED:
            logger.warning(f"[{self.agent_id}] Cannot start from state {self.state.value}")
            return

        self.state = AgentState.STARTING
        logger.info(f"[{self.agent_id}] Starting autonomous behavior loop...")

        # Initialize agent if it has initialization method
        if hasattr(self.agent, 'initialize_agent'):
            try:
                await self.agent.initialize_agent()
            except Exception as e:
                logger.error(f"[{self.agent_id}] Initialization failed: {e}")
                self.state = AgentState.ERROR
                return

        # Start behavior loop
        self.should_run = True
        self.behavior_loop_task = asyncio.create_task(self._behavior_loop())
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        self.state = AgentState.IDLE
        self.stats["started_at"] = datetime.utcnow()

        logger.info(f"[{self.agent_id}] ✅ Running autonomously (state: {self.state.value})")

    async def stop(self):
        """Stop the agent gracefully"""
        if self.state == AgentState.STOPPED:
            return

        logger.info(f"[{self.agent_id}] Stopping...")
        self.state = AgentState.STOPPING
        self.should_run = False

        # Cancel behavior loop
        if self.behavior_loop_task:
            self.behavior_loop_task.cancel()
            try:
                await self.behavior_loop_task
            except asyncio.CancelledError:
                pass

        # Cancel heartbeat
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass

        self.state = AgentState.STOPPED
        self.stats["stopped_at"] = datetime.utcnow()

        logger.info(f"[{self.agent_id}] ⭕ Stopped")

    async def pause(self):
        """Pause the agent (stops processing new tasks)"""
        if self.state != AgentState.IDLE and self.state != AgentState.WORKING:
            logger.warning(f"[{self.agent_id}] Cannot pause from state {self.state.value}")
            return

        self.state = AgentState.PAUSED
        logger.info(f"[{self.agent_id}] ⏸️ Paused")

    async def resume(self):
        """Resume the agent from paused state"""
        if self.state != AgentState.PAUSED:
            logger.warning(f"[{self.agent_id}] Cannot resume from state {self.state.value}")
            return

        self.state = AgentState.IDLE
        logger.info(f"[{self.agent_id}] ▶️ Resumed")

    async def submit_task(self, task: Dict[str, Any]) -> str:
        """
        Submit a task for the agent to execute.

        Args:
            task: Task specification

        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())
        task_item = TaskQueueItem(task_id=task_id, task=task)

        try:
            await self.task_queue.put(task_item)
            logger.info(f"[{self.agent_id}] Task {task_id} queued (queue size: {self.task_queue.qsize()})")
            return task_id
        except asyncio.QueueFull:
            logger.error(f"[{self.agent_id}] Task queue full! Cannot accept task.")
            raise Exception("Agent task queue is full")

    async def _behavior_loop(self):
        """
        Main autonomous behavior loop.

        Continuously processes tasks from queue.
        """
        logger.info(f"[{self.agent_id}] 🔄 Behavior loop started")

        while self.should_run:
            try:
                # Skip if paused
                if self.state == AgentState.PAUSED:
                    await asyncio.sleep(1)
                    continue

                # Wait for next task (with timeout to check should_run)
                try:
                    task_item = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                # Execute task
                self.state = AgentState.WORKING
                self.current_task = task_item
                task_item.started_at = datetime.utcnow()

                logger.info(f"[{self.agent_id}] 🔨 Executing task {task_item.task_id}")

                try:
                    # Call agent's execute_task method
                    result = await self.agent.execute_task(task_item.task)
                    task_item.result = result
                    task_item.completed_at = datetime.utcnow()

                    # Calculate execution time
                    exec_time = (task_item.completed_at - task_item.started_at).total_seconds()
                    self.stats["tasks_completed"] += 1
                    self.stats["total_execution_time"] += exec_time

                    logger.info(f"[{self.agent_id}] ✅ Task {task_item.task_id} completed ({exec_time:.2f}s)")

                except Exception as e:
                    task_item.error = str(e)
                    task_item.completed_at = datetime.utcnow()
                    self.stats["tasks_failed"] += 1

                    logger.error(f"[{self.agent_id}] ❌ Task {task_item.task_id} failed: {e}")

                # Store completed task
                self.completed_tasks.append(task_item)
                if len(self.completed_tasks) > 100:  # Keep last 100
                    self.completed_tasks.pop(0)

                self.current_task = None
                self.state = AgentState.IDLE if self.should_run else AgentState.STOPPING

            except Exception as e:
                logger.error(f"[{self.agent_id}] Behavior loop error: {e}")
                self.state = AgentState.ERROR
                await asyncio.sleep(5)  # Wait before retrying
                if self.should_run:
                    self.state = AgentState.IDLE

        logger.info(f"[{self.agent_id}] 🔄 Behavior loop stopped")

    async def _heartbeat_loop(self):
        """Send periodic heartbeats"""
        while self.should_run:
            try:
                # Send heartbeat if agent has the method
                if hasattr(self.agent, 'send_heartbeat'):
                    await self.agent.send_heartbeat()

                self.stats["heartbeats_sent"] += 1
                await asyncio.sleep(30)  # Heartbeat every 30 seconds

            except Exception as e:
                logger.error(f"[{self.agent_id}] Heartbeat error: {e}")
                await asyncio.sleep(30)

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive agent status"""
        uptime = None
        if self.stats["started_at"]:
            uptime = (datetime.utcnow() - self.stats["started_at"]).total_seconds()

        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "state": self.state.value,
            "instantiated": True,  # ← KEY: This agent is REAL
            "queue_size": self.task_queue.qsize(),
            "current_task": self.current_task.task_id if self.current_task else None,
            "stats": {
                **self.stats,
                "started_at": self.stats["started_at"].isoformat() if self.stats["started_at"] else None,
                "stopped_at": self.stats["stopped_at"].isoformat() if self.stats["stopped_at"] else None,
                "uptime_seconds": uptime,
                "avg_task_time": (
                    self.stats["total_execution_time"] / self.stats["tasks_completed"]
                    if self.stats["tasks_completed"] > 0
                    else 0
                )
            }
        }

    def get_task_history(self, limit: int = 10) -> list[Dict[str, Any]]:
        """Get recent task history"""
        recent_tasks = self.completed_tasks[-limit:]
        return [
            {
                "task_id": t.task_id,
                "task": t.task,
                "submitted_at": t.submitted_at.isoformat(),
                "started_at": t.started_at.isoformat() if t.started_at else None,
                "completed_at": t.completed_at.isoformat() if t.completed_at else None,
                "result": t.result,
                "error": t.error,
                "duration_seconds": (
                    (t.completed_at - t.started_at).total_seconds()
                    if t.completed_at and t.started_at
                    else None
                )
            }
            for t in recent_tasks
        ]
