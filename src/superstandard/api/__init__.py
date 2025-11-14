"""
API Module - Production HTTP and WebSocket Servers

This module provides production-grade server infrastructure for the
Agentic Standards Protocol platform.

Components:
- WebSocket Server: Real-time event broadcasting for dashboard
- REST API: HTTP endpoints for stats, health checks, etc.

Usage:
    from src.superstandard.api.websocket_server import DashboardWebSocketServer

    server = DashboardWebSocketServer(host='0.0.0.0', port=8000)
    await server.start()
"""

from .websocket_server import DashboardWebSocketServer

__all__ = ['DashboardWebSocketServer']
