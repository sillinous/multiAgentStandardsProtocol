"""
Real Market Data Adapter for BacktestEngine

Seamlessly integrates real market data from Alpaca into the existing
backtesting framework.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional
import logging

from .alpaca_client import AlpacaClient, AlpacaConfig, MarketDataBar
from ..backtest_engine import MarketBar


logger = logging.getLogger(__name__)


@dataclass
class RealDataConfig:
    """Configuration for real data fetching"""

    alpaca_config: AlpacaConfig
    cache_enabled: bool = True
    cache_ttl_seconds: int = 300  # 5 minutes


class RealMarketDataAdapter:
    """
    Adapter to fetch real market data for backtesting

    Replaces synthetic data with real historical data from Alpaca,
    while maintaining compatibility with BacktestEngine.

    Example:
        config = RealDataConfig(alpaca_config=AlpacaConfig())
        adapter = RealMarketDataAdapter(config)

        # Fetch real data for backtesting
        bars = adapter.fetch_backtest_data(
            symbol="AAPL",
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now(),
            timeframe="1Day"
        )

        # Use with BacktestEngine
        backtest_engine = BacktestEngine(backtest_config)
        result = backtest_engine.run(ensemble, bars)
    """

    def __init__(self, config: RealDataConfig):
        """Initialize adapter with configuration"""
        self.config = config
        self.client = AlpacaClient(config.alpaca_config)
        self._cache: dict = {}

        logger.info("Real market data adapter initialized")

    def fetch_backtest_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1Day"
    ) -> List[MarketBar]:
        """
        Fetch real market data for backtesting

        Args:
            symbol: Stock symbol (e.g., "AAPL")
            start_date: Start date for historical data
            end_date: End date for historical data
            timeframe: Bar timeframe ("1Min", "5Min", "1Hour", "1Day")

        Returns:
            List of MarketBar objects compatible with BacktestEngine
        """
        # Check cache
        cache_key = f"{symbol}:{start_date.date()}:{end_date.date()}:{timeframe}"
        if self.config.cache_enabled and cache_key in self._cache:
            logger.info(f"Using cached data for {symbol}")
            return self._cache[cache_key]

        # Calculate number of days
        days = (end_date - start_date).days

        # Fetch data from Alpaca
        logger.info(
            f"Fetching real market data: {symbol} "
            f"from {start_date.date()} to {end_date.date()} ({timeframe})"
        )

        market_data_bars = self.client.get_historical_bars(
            symbol=symbol,
            days=days,
            timeframe=timeframe
        )

        # Convert to BacktestEngine format
        backtest_bars = [bar.to_backtest_bar() for bar in market_data_bars]

        # Filter by date range (Alpaca might return extra data)
        backtest_bars = [
            bar for bar in backtest_bars
            if start_date <= bar.timestamp <= end_date
        ]

        # Cache the result
        if self.config.cache_enabled:
            self._cache[cache_key] = backtest_bars

        logger.info(f"Fetched {len(backtest_bars)} bars for {symbol}")

        return backtest_bars

    def fetch_multiple_symbols(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1Day"
    ) -> dict[str, List[MarketBar]]:
        """
        Fetch data for multiple symbols

        Args:
            symbols: List of stock symbols
            start_date: Start date
            end_date: End date
            timeframe: Bar timeframe

        Returns:
            Dictionary mapping symbol to list of bars
        """
        result = {}

        for symbol in symbols:
            try:
                bars = self.fetch_backtest_data(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    timeframe=timeframe
                )
                result[symbol] = bars
            except Exception as e:
                logger.error(f"Error fetching data for {symbol}: {e}")
                result[symbol] = []

        return result

    def get_latest_price(self, symbol: str) -> float:
        """
        Get latest price for a symbol

        Args:
            symbol: Stock symbol

        Returns:
            Latest price
        """
        return self.client.get_current_price(symbol)

    def clear_cache(self):
        """Clear the data cache"""
        self._cache.clear()
        logger.info("Data cache cleared")


# ============================================================================
# Convenience Functions
# ============================================================================

def create_real_data_adapter(
    api_key: Optional[str] = None,
    api_secret: Optional[str] = None,
    paper_trading: bool = True
) -> RealMarketDataAdapter:
    """
    Create a real market data adapter with sensible defaults

    Args:
        api_key: Alpaca API key (defaults to ALPACA_API_KEY env var)
        api_secret: Alpaca API secret (defaults to ALPACA_API_SECRET env var)
        paper_trading: Use paper trading endpoint (default True)

    Returns:
        Configured RealMarketDataAdapter
    """
    import os

    alpaca_config = AlpacaConfig(
        api_key=api_key or os.getenv('ALPACA_API_KEY', ''),
        api_secret=api_secret or os.getenv('ALPACA_API_SECRET', ''),
        paper_trading=paper_trading
    )

    real_data_config = RealDataConfig(alpaca_config=alpaca_config)

    return RealMarketDataAdapter(real_data_config)
