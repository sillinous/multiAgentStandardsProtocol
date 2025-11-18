"""
NEXUS Market Data Simulator

Generates realistic market data for testing and demonstration purposes.
Simulates price movements for common crypto pairs.
"""

import asyncio
import random
from datetime import datetime
from typing import Dict

class MarketDataSimulator:
    """Simulates realistic market data using random walk model"""

    def __init__(self):
        # Initial prices for crypto pairs
        self.prices: Dict[str, float] = {
            "BTC/USD": 45000.0,
            "ETH/USD": 2500.0,
            "SOL/USD": 120.0,
        }

        # Price volatility per symbol (%)
        self.volatility: Dict[str, float] = {
            "BTC/USD": 0.5,
            "ETH/USD": 0.6,
            "SOL/USD": 0.8,
        }

        # Trend direction per symbol (-1, 0, 1)
        self.trends: Dict[str, float] = {
            "BTC/USD": 0.0,
            "ETH/USD": 0.0,
            "SOL/USD": 0.0,
        }

        self.is_running = False

    def get_price(self, symbol: str) -> float:
        """Get current price for symbol"""
        return self.prices.get(symbol, 0.0)

    async def generate_price_update(self, symbol: str) -> Dict:
        """Generate next price update for symbol using random walk"""
        if symbol not in self.prices:
            return None

        current_price = self.prices[symbol]
        volatility = self.volatility.get(symbol, 0.5)

        # Random walk with drift
        # 70% chance to continue trend, 30% to reverse
        if random.random() < 0.7:
            self.trends[symbol] = self.trends[symbol] * 0.95  # Decay trend
        else:
            self.trends[symbol] = random.uniform(-0.1, 0.1)  # New trend

        # Generate price change
        random_change = random.gauss(0, volatility)  # Normal distribution
        trend_component = self.trends[symbol] * 0.05
        price_change_pct = random_change + trend_component

        new_price = current_price * (1 + price_change_pct / 100)

        # Prevent unrealistic prices
        min_price = current_price * 0.5  # Don't drop more than 50%
        max_price = current_price * 1.5  # Don't jump more than 50%
        new_price = max(min_price, min(max_price, new_price))

        self.prices[symbol] = new_price

        # Generate realistic market data
        return {
            "symbol": symbol,
            "price": round(new_price, 2),
            "change_pct": round(price_change_pct, 2),
            "timestamp": datetime.utcnow().isoformat(),
            "bid": round(new_price * 0.9999, 2),
            "ask": round(new_price * 1.0001, 2),
            "volume": round(random.uniform(100, 10000), 2),
        }

    async def run(self, ws_manager, update_interval: float = 1.0):
        """
        Run market data simulator

        Args:
            ws_manager: WebSocket manager to broadcast updates
            update_interval: Seconds between price updates
        """
        self.is_running = True
        symbols = list(self.prices.keys())

        try:
            while self.is_running:
                # Generate updates for all symbols
                for symbol in symbols:
                    update = await self.generate_price_update(symbol)
                    if update and ws_manager:
                        await ws_manager.broadcast_price_update(
                            symbol,
                            update["price"],
                            data=update
                        )

                await asyncio.sleep(update_interval)
        except asyncio.CancelledError:
            self.is_running = False

    def stop(self):
        """Stop the simulator"""
        self.is_running = False


# Global simulator instance
market_simulator = MarketDataSimulator()
