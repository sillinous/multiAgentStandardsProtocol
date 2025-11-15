"""
Dashboard WebSocket Server
FastAPI server with WebSocket support for real-time dashboard
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .realtime_dashboard import get_dashboard, get_event_bus, DashboardEvent

# Create FastAPI app
app = FastAPI(title="Agentic Platform Dashboard", version="1.0.0")

# Get dashboard instance
dashboard = get_dashboard()
event_bus = get_event_bus()

# Active WebSocket connections
active_connections: Set[WebSocket] = set()


# Serve dashboard HTML
@app.get("/", response_class=HTMLResponse)
async def get_dashboard_page():
    """Serve the dashboard HTML page"""
    dashboard_path = Path(__file__).parent / "dashboard.html"
    with open(dashboard_path, "r") as f:
        return f.read()


# WebSocket endpoint for real-time updates
@app.websocket("/ws/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for dashboard updates"""
    await websocket.accept()
    active_connections.add(websocket)

    # Send initial state
    try:
        state = dashboard.get_dashboard_state()
        await websocket.send_json({
            "type": "state",
            "state": state
        })
    except Exception as e:
        print(f"Error sending initial state: {e}")

    # Subscribe to event bus
    event_queue = event_bus.subscribe()

    try:
        # Start background task to send events
        async def send_events():
            while True:
                try:
                    event = await event_queue.get()
                    await websocket.send_json({
                        "type": "event",
                        "event": event.to_dict()
                    })
                except Exception as e:
                    print(f"Error sending event: {e}")
                    break

        # Start background task to send metrics updates
        async def send_metrics():
            while True:
                await asyncio.sleep(2)  # Update every 2 seconds
                try:
                    metrics = event_bus.get_metrics()
                    await websocket.send_json({
                        "type": "metrics",
                        "metrics": metrics
                    })
                except Exception as e:
                    print(f"Error sending metrics: {e}")
                    break

        # Start both tasks
        event_task = asyncio.create_task(send_events())
        metrics_task = asyncio.create_task(send_metrics())

        # Wait for client messages (for control commands)
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)

                # Handle different message types
                if message.get("type") == "get_state":
                    state = dashboard.get_dashboard_state()
                    await websocket.send_json({
                        "type": "state",
                        "state": state
                    })

            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"Error handling message: {e}")
                break

    finally:
        # Cleanup
        event_bus.unsubscribe(event_queue)
        active_connections.discard(websocket)

        # Cancel background tasks
        event_task.cancel()
        metrics_task.cancel()


# API endpoints
@app.get("/api/metrics")
async def get_metrics():
    """Get current dashboard metrics"""
    return event_bus.get_metrics()


@app.get("/api/events/recent")
async def get_recent_events(count: int = 50):
    """Get recent events"""
    return event_bus.get_recent_events(count)


@app.get("/api/state")
async def get_state():
    """Get complete dashboard state"""
    return dashboard.get_dashboard_state()


@app.post("/api/events/test")
async def create_test_event(event_type: str = "agent_completed"):
    """Create a test event for dashboard testing"""
    import random

    if event_type == "agent_started":
        event = DashboardEvent.agent_started(
            agent_id=f"test-{random.randint(1000, 9999)}",
            agent_name="Test Agent",
            task="Test task execution"
        )
    elif event_type == "agent_completed":
        event = DashboardEvent.agent_completed(
            agent_id=f"test-{random.randint(1000, 9999)}",
            agent_name="Test Agent",
            task="Test task execution",
            duration_ms=random.uniform(500, 2000),
            success=random.choice([True, True, True, False])  # 75% success rate
        )
    elif event_type == "workflow_started":
        event = DashboardEvent.workflow_started(
            workflow_id=f"workflow-{random.randint(1000, 9999)}",
            workflow_name="Test Workflow",
            total_tasks=random.randint(5, 15)
        )
    elif event_type == "workflow_completed":
        total_tasks = random.randint(5, 15)
        failed = random.randint(0, 2)
        event = DashboardEvent.workflow_completed(
            workflow_id=f"workflow-{random.randint(1000, 9999)}",
            workflow_name="Test Workflow",
            duration_seconds=random.uniform(5, 30),
            tasks_completed=total_tasks - failed,
            tasks_failed=failed,
            total_cost=random.uniform(20, 150)
        )
    else:
        event = DashboardEvent.metric_update(
            metric_name="test_metric",
            value=random.uniform(0, 100),
            unit="units"
        )

    await event_bus.publish(event)
    return {"status": "success", "event": event.to_dict()}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "active_connections": len(active_connections),
        "metrics": event_bus.get_metrics()
    }


if __name__ == "__main__":
    import uvicorn

    print("\n" + "=" * 80)
    print("🚀 AGENTIC PLATFORM - REAL-TIME MONITORING DASHBOARD")
    print("=" * 80)
    print("\n📊 Dashboard URL: http://localhost:8000")
    print("🔌 WebSocket URL: ws://localhost:8000/ws/dashboard")
    print("📡 API URL: http://localhost:8000/api")
    print("\n💡 Test the dashboard:")
    print("   curl -X POST http://localhost:8000/api/events/test?event_type=agent_completed")
    print("\n" + "=" * 80 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
