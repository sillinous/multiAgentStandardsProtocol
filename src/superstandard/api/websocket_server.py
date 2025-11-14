"""
Production WebSocket Server for Real-Time Dashboard

This module provides a production-grade WebSocket server that:
- Serves the HTML dashboard
- Broadcasts real-time events to connected clients
- Integrates with DashboardState for event streaming
- Handles client connections/disconnections
- Provides health check endpoint

Usage:
    python src/superstandard/api/websocket_server.py

Or integrate into your application:
    from src.superstandard.api.websocket_server import DashboardWebSocketServer

    server = DashboardWebSocketServer(host='0.0.0.0', port=8000)
    await server.start()
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Set, Optional
from datetime import datetime
import uuid

try:
    from aiohttp import web, WSMsgType
except ImportError:
    print("⚠️  aiohttp not installed. Install with: pip install aiohttp")
    print("   Required for WebSocket server functionality.")
    raise

from ..monitoring.dashboard import get_dashboard, DashboardEvent


logger = logging.getLogger(__name__)


class DashboardWebSocketServer:
    """
    Production WebSocket Server for Real-Time Dashboard

    Features:
    - WebSocket endpoint for real-time event streaming
    - HTTP endpoint for serving dashboard HTML
    - Health check endpoint
    - Client connection management
    - Automatic event broadcasting
    - Graceful shutdown handling
    """

    def __init__(
        self,
        host: str = '0.0.0.0',
        port: int = 8000,
        dashboard_html_path: Optional[str] = None
    ):
        """
        Initialize WebSocket server

        Args:
            host: Host to bind to (default: 0.0.0.0)
            port: Port to bind to (default: 8000)
            dashboard_html_path: Path to dashboard HTML file (auto-detected if None)
        """
        self.host = host
        self.port = port

        # Auto-detect dashboard HTML path
        if dashboard_html_path is None:
            # Try to find dashboard.html in project root
            current_dir = Path(__file__).parent
            project_root = current_dir.parent.parent.parent
            self.dashboard_html_path = project_root / "dashboard.html"
        else:
            self.dashboard_html_path = Path(dashboard_html_path)

        # WebSocket clients
        self.clients: Set[web.WebSocketResponse] = set()

        # Dashboard state integration
        self.dashboard = get_dashboard()

        # Web application
        self.app = web.Application()
        self._setup_routes()

        # Server state
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None

        logger.info(f"✅ DashboardWebSocketServer initialized")
        logger.info(f"   Host: {self.host}")
        logger.info(f"   Port: {self.port}")
        logger.info(f"   Dashboard HTML: {self.dashboard_html_path}")

    def _setup_routes(self):
        """Setup HTTP and WebSocket routes"""
        self.app.router.add_get('/', self.handle_dashboard)
        self.app.router.add_get('/dashboard', self.handle_dashboard)
        self.app.router.add_get('/ws', self.handle_websocket)
        self.app.router.add_get('/health', self.handle_health)
        self.app.router.add_get('/stats', self.handle_stats)

    async def handle_dashboard(self, request: web.Request) -> web.Response:
        """Serve dashboard HTML"""
        try:
            if not self.dashboard_html_path.exists():
                return web.Response(
                    text=f"Dashboard HTML not found at: {self.dashboard_html_path}",
                    status=404
                )

            html_content = self.dashboard_html_path.read_text()

            # Update WebSocket endpoint in HTML to point to this server
            # Replace placeholder WebSocket URL with actual endpoint
            html_content = html_content.replace(
                "config.simulateEvents: true,",
                "config.simulateEvents: false,"
            )
            html_content = html_content.replace(
                "// const ws = new WebSocket('ws://localhost:8000/ws/dashboard');",
                f"const ws = new WebSocket('ws://{request.host}/ws');"
            )

            return web.Response(
                text=html_content,
                content_type='text/html'
            )

        except Exception as e:
            logger.error(f"Error serving dashboard: {e}")
            return web.Response(
                text=f"Error loading dashboard: {str(e)}",
                status=500
            )

    async def handle_websocket(self, request: web.Request) -> web.WebSocketResponse:
        """Handle WebSocket connections"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        client_id = str(uuid.uuid4())[:8]
        logger.info(f"🔌 WebSocket client connected: {client_id}")

        # Add to clients set
        self.clients.add(ws)

        try:
            # Send connection confirmation
            await ws.send_json({
                'event_type': 'connection_established',
                'client_id': client_id,
                'timestamp': datetime.utcnow().isoformat(),
                'message': 'Connected to Agentic Standards Protocol Dashboard'
            })

            # Send recent events to new client
            recent_events = self.dashboard.get_recent_events(limit=50)
            for event in reversed(recent_events):
                await ws.send_json(event)

            # Send current stats
            stats = self.dashboard.get_dashboard_stats()
            await ws.send_json({
                'event_type': 'metrics_updated',
                'timestamp': datetime.utcnow().isoformat(),
                'data': stats,
                'severity': 'info'
            })

            # Listen for client messages (for future interactivity)
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        logger.debug(f"Received from {client_id}: {data}")
                        # Handle client commands if needed
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON from {client_id}: {msg.data}")

                elif msg.type == WSMsgType.ERROR:
                    logger.error(f"WebSocket error from {client_id}: {ws.exception()}")

        except Exception as e:
            logger.error(f"Error in WebSocket handler for {client_id}: {e}")

        finally:
            # Remove from clients set
            self.clients.discard(ws)
            logger.info(f"🔌 WebSocket client disconnected: {client_id}")

        return ws

    async def handle_health(self, request: web.Request) -> web.Response:
        """Health check endpoint"""
        return web.json_response({
            'status': 'healthy',
            'service': 'DashboardWebSocketServer',
            'timestamp': datetime.utcnow().isoformat(),
            'connected_clients': len(self.clients),
            'uptime_seconds': (datetime.utcnow() - self.dashboard.start_time).total_seconds()
        })

    async def handle_stats(self, request: web.Request) -> web.Response:
        """Dashboard statistics endpoint"""
        stats = self.dashboard.get_dashboard_stats()
        stats['connected_clients'] = len(self.clients)
        return web.json_response(stats)

    async def broadcast_event(self, event: DashboardEvent):
        """
        Broadcast event to all connected WebSocket clients

        Args:
            event: Dashboard event to broadcast
        """
        if not self.clients:
            return

        event_dict = event.to_dict()

        # Broadcast to all connected clients
        disconnected = set()
        for ws in self.clients:
            try:
                await ws.send_json(event_dict)
            except Exception as e:
                logger.error(f"Failed to send event to client: {e}")
                disconnected.add(ws)

        # Remove disconnected clients
        for ws in disconnected:
            self.clients.discard(ws)

    async def start(self):
        """Start the WebSocket server"""
        try:
            # Setup the application
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()

            # Start the server
            self.site = web.TCPSite(self.runner, self.host, self.port)
            await self.site.start()

            logger.info("=" * 80)
            logger.info("🚀 Dashboard WebSocket Server STARTED")
            logger.info("=" * 80)
            logger.info(f"   📡 WebSocket Endpoint: ws://{self.host}:{self.port}/ws")
            logger.info(f"   🌐 Dashboard URL: http://{self.host}:{self.port}/dashboard")
            logger.info(f"   ❤️  Health Check: http://{self.host}:{self.port}/health")
            logger.info(f"   📊 Statistics: http://{self.host}:{self.port}/stats")
            logger.info("=" * 80)
            logger.info("")

            # Integrate with DashboardState for automatic event broadcasting
            self._integrate_with_dashboard()

            logger.info("✅ Server ready to accept connections!")
            logger.info(f"   Open http://localhost:{self.port}/dashboard in your browser")
            logger.info("")

        except Exception as e:
            logger.error(f"❌ Failed to start server: {e}")
            raise

    def _integrate_with_dashboard(self):
        """Integrate with DashboardState to automatically broadcast events"""
        # Override the dashboard's broadcast_event method to also send via WebSocket
        original_broadcast = self.dashboard.broadcast_event

        async def enhanced_broadcast(event: DashboardEvent):
            # Call original broadcast (adds to history, logs, etc.)
            await original_broadcast(event)
            # Also broadcast via WebSocket
            await self.broadcast_event(event)

        # Replace the method
        self.dashboard.broadcast_event = enhanced_broadcast
        logger.info("✅ Dashboard event broadcasting integrated with WebSocket server")

    async def stop(self):
        """Stop the WebSocket server"""
        logger.info("🛑 Stopping Dashboard WebSocket Server...")

        # Close all WebSocket connections
        for ws in list(self.clients):
            await ws.close()
        self.clients.clear()

        # Cleanup server
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()

        logger.info("✅ Server stopped")

    async def run_forever(self):
        """Start server and run forever"""
        await self.start()

        try:
            # Run forever
            while True:
                await asyncio.sleep(3600)
        except KeyboardInterrupt:
            logger.info("\n⚠️  Received shutdown signal")
        finally:
            await self.stop()


async def main():
    """Main entry point for standalone server"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create and run server
    server = DashboardWebSocketServer(
        host='0.0.0.0',
        port=8000
    )

    await server.run_forever()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
