"""
NEXUS Real-Time Market Data WebSocket

Provides WebSocket streaming for real-time market data and trading events.

Features:
- Real-time price updates
- Trade event notifications
- Portfolio value streaming
- Order execution events
- Multi-client broadcasting

Use Cases:
- Live paper trading price updates
- Real-time dashboard updates
- Trading UI price feeds
- Event notifications
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set, Any, Optional
import asyncio
import json
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class MarketDataUpdate:
    """Market data update message"""
    type: str  # price_update, trade_event, portfolio_update, order_event
    symbol: Optional[str] = None
    price: Optional[float] = None
    timestamp: str = ""
    data: Dict[str, Any] = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()
        if self.data is None:
            self.data = {}


class MarketDataWebSocketManager:
    """
    WebSocket manager for real-time market data streaming

    Manages WebSocket connections and broadcasts market data updates to subscribers.
    """

    def __init__(self):
        # Active connections: symbol -> set of WebSocket connections
        self.price_subscriptions: Dict[str, Set[WebSocket]] = {}

        # All active connections
        self.active_connections: Set[WebSocket] = set()

        # Event subscribers (trading events, orders, etc.)
        self.event_subscribers: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        """Accept WebSocket connection"""
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        self.active_connections.discard(websocket)
        self.event_subscribers.discard(websocket)

        # Remove from all price subscriptions
        for symbol_subs in self.price_subscriptions.values():
            symbol_subs.discard(websocket)

    async def subscribe_prices(self, websocket: WebSocket, symbols: list):
        """Subscribe to price updates for specific symbols"""
        for symbol in symbols:
            if symbol not in self.price_subscriptions:
                self.price_subscriptions[symbol] = set()
            self.price_subscriptions[symbol].add(websocket)

    async def subscribe_events(self, websocket: WebSocket):
        """Subscribe to trading events"""
        self.event_subscribers.add(websocket)

    async def broadcast_price_update(self, symbol: str, price: float, data: Dict[str, Any] = None):
        """
        Broadcast price update to subscribers

        Args:
            symbol: Trading symbol
            price: Current price
            data: Additional data (volume, bid/ask, etc.)
        """
        if symbol not in self.price_subscriptions:
            return

        update = MarketDataUpdate(
            type="price_update",
            symbol=symbol,
            price=price,
            data=data or {}
        )

        message = json.dumps(asdict(update))

        # Send to all subscribers of this symbol
        disconnected = set()
        for websocket in self.price_subscriptions[symbol]:
            try:
                await websocket.send_text(message)
            except:
                disconnected.add(websocket)

        # Clean up disconnected clients
        for ws in disconnected:
            self.disconnect(ws)

    async def broadcast_event(self, event_type: str, data: Dict[str, Any]):
        """
        Broadcast trading event to all event subscribers

        Args:
            event_type: Event type (trade_executed, order_placed, portfolio_update, etc.)
            data: Event data
        """
        update = MarketDataUpdate(
            type=event_type,
            data=data
        )

        message = json.dumps(asdict(update))

        # Send to all event subscribers
        disconnected = set()
        for websocket in self.event_subscribers:
            try:
                await websocket.send_text(message)
            except:
                disconnected.add(websocket)

        # Clean up disconnected clients
        for ws in disconnected:
            self.disconnect(ws)

    async def handle_client_message(self, websocket: WebSocket, message: str):
        """
        Handle incoming message from client

        Supported messages:
        - {"action": "subscribe_prices", "symbols": ["BTC/USD", "ETH/USD"]}
        - {"action": "subscribe_events"}
        - {"action": "unsubscribe_prices", "symbols": ["BTC/USD"]}
        """
        try:
            data = json.loads(message)
            action = data.get("action")

            if action == "subscribe_prices":
                symbols = data.get("symbols", [])
                await self.subscribe_prices(websocket, symbols)
                await websocket.send_text(json.dumps({
                    "type": "subscription_confirmed",
                    "action": "price_subscription",
                    "symbols": symbols
                }))

            elif action == "subscribe_events":
                await self.subscribe_events(websocket)
                await websocket.send_text(json.dumps({
                    "type": "subscription_confirmed",
                    "action": "event_subscription"
                }))

            elif action == "unsubscribe_prices":
                symbols = data.get("symbols", [])
                for symbol in symbols:
                    if symbol in self.price_subscriptions:
                        self.price_subscriptions[symbol].discard(websocket)

        except json.JSONDecodeError:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Invalid JSON message"
            }))

    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket statistics"""
        return {
            "active_connections": len(self.active_connections),
            "event_subscribers": len(self.event_subscribers),
            "price_subscriptions": {
                symbol: len(subs) for symbol, subs in self.price_subscriptions.items()
            }
        }


# Global WebSocket manager instance
ws_manager = MarketDataWebSocketManager()
