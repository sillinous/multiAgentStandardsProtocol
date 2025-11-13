"""
Historical Market Data Integration - Real Market Data for Agent Validation

This module fetches real historical market data from various sources and converts
it to our MarketBar format for backtesting evolved agents on actual market history.

Data Sources:
- Yahoo Finance (stocks, ETFs, crypto, forex)
- Supports daily, hourly, and minute-level data
- Caching to avoid redundant API calls

Author: Agentic Forge
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from pathlib import Path
import json
import time

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("Warning: yfinance not installed. Install with: pip install yfinance")

from .market_simulation import MarketBar


# ============================================================================
# Historical Data Fetcher
# ============================================================================

@dataclass
class DataSource:
    """Market data source configuration"""
    symbol: str           # Ticker symbol (e.g., 'SPY', 'BTC-USD')
    source: str = 'yahoo' # Data source ('yahoo')
    interval: str = '1d'  # Time interval ('1d', '1h', '1m', '5m', '15m', '30m', '60m')

    def __str__(self):
        return f"{self.symbol}_{self.interval}"


class HistoricalDataFetcher:
    """
    Fetch and cache real historical market data.

    Uses Yahoo Finance API to download OHLCV data for stocks, crypto, forex, etc.
    Implements local caching to avoid redundant API calls.
    """

    def __init__(self, cache_dir: str = ".market_data_cache"):
        """
        Initialize the fetcher.

        Args:
            cache_dir: Directory to cache downloaded data
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        if not YFINANCE_AVAILABLE:
            raise ImportError(
                "yfinance is required for historical data. "
                "Install with: pip install yfinance"
            )

    def fetch(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        interval: str = '1d',
        use_cache: bool = True
    ) -> List[MarketBar]:
        """
        Fetch historical market data.

        Args:
            symbol: Ticker symbol (e.g., 'SPY', 'AAPL', 'BTC-USD', 'EURUSD=X')
            start_date: Start date 'YYYY-MM-DD' (default: 1 year ago)
            end_date: End date 'YYYY-MM-DD' (default: today)
            interval: Data interval ('1d', '1h', '5m', etc.)
            use_cache: Use cached data if available

        Returns:
            List of MarketBar objects

        Examples:
            # Fetch daily SPY data for last year
            bars = fetcher.fetch('SPY')

            # Fetch hourly Bitcoin data
            bars = fetcher.fetch('BTC-USD', interval='1h')

            # Fetch specific date range
            bars = fetcher.fetch('AAPL', start_date='2023-01-01', end_date='2023-12-31')
        """
        # Set default dates
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')

        if start_date is None:
            start_datetime = datetime.now() - timedelta(days=365)
            start_date = start_datetime.strftime('%Y-%m-%d')

        # Check cache
        cache_key = f"{symbol}_{interval}_{start_date}_{end_date}"
        cache_file = self.cache_dir / f"{cache_key}.json"

        if use_cache and cache_file.exists():
            print(f"📦 Loading cached data for {symbol} ({interval})")
            return self._load_from_cache(cache_file)

        # Fetch from Yahoo Finance
        print(f"📥 Downloading {symbol} data from Yahoo Finance...")
        print(f"   Period: {start_date} to {end_date}")
        print(f"   Interval: {interval}")

        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date, interval=interval)

            if df.empty:
                raise ValueError(f"No data returned for {symbol}")

            # Convert to MarketBar format
            bars = self._dataframe_to_bars(df, symbol)

            print(f"✅ Downloaded {len(bars)} bars")

            # Cache the data
            if use_cache:
                self._save_to_cache(cache_file, bars)

            return bars

        except Exception as e:
            raise RuntimeError(f"Failed to fetch data for {symbol}: {e}")

    def fetch_multiple(
        self,
        symbols: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        interval: str = '1d',
        use_cache: bool = True
    ) -> Dict[str, List[MarketBar]]:
        """
        Fetch data for multiple symbols.

        Args:
            symbols: List of ticker symbols
            start_date: Start date
            end_date: End date
            interval: Data interval
            use_cache: Use cached data

        Returns:
            Dictionary mapping symbol to list of MarketBars
        """
        results = {}

        for symbol in symbols:
            try:
                bars = self.fetch(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    interval=interval,
                    use_cache=use_cache
                )
                results[symbol] = bars
                time.sleep(0.5)  # Rate limiting - be nice to Yahoo Finance
            except Exception as e:
                print(f"⚠️  Failed to fetch {symbol}: {e}")
                results[symbol] = []

        return results

    def get_popular_symbols(self) -> Dict[str, List[str]]:
        """
        Get dictionary of popular trading symbols by category.

        Returns:
            Dictionary with categories and symbols
        """
        return {
            'stocks': [
                'SPY',    # S&P 500 ETF
                'QQQ',    # NASDAQ 100 ETF
                'DIA',    # Dow Jones ETF
                'AAPL',   # Apple
                'MSFT',   # Microsoft
                'GOOGL',  # Google
                'AMZN',   # Amazon
                'TSLA',   # Tesla
                'NVDA',   # NVIDIA
                'META'    # Meta
            ],
            'crypto': [
                'BTC-USD',  # Bitcoin
                'ETH-USD',  # Ethereum
                'BNB-USD',  # Binance Coin
                'ADA-USD',  # Cardano
                'SOL-USD'   # Solana
            ],
            'forex': [
                'EURUSD=X',  # Euro/USD
                'GBPUSD=X',  # Pound/USD
                'JPYUSD=X',  # Yen/USD
                'AUDUSD=X'   # Aussie/USD
            ],
            'commodities': [
                'GC=F',  # Gold Futures
                'SI=F',  # Silver Futures
                'CL=F'   # Crude Oil Futures
            ]
        }

    def _dataframe_to_bars(self, df, symbol: str) -> List[MarketBar]:
        """Convert pandas DataFrame to list of MarketBars"""
        bars = []

        for index, row in df.iterrows():
            # Handle timezone-aware and timezone-naive datetimes
            if hasattr(index, 'to_pydatetime'):
                timestamp = index.to_pydatetime()
            else:
                timestamp = index

            # Remove timezone info if present for consistency
            if hasattr(timestamp, 'replace'):
                timestamp = timestamp.replace(tzinfo=None)

            bar = MarketBar(
                timestamp=timestamp,
                open=float(row['Open']),
                high=float(row['High']),
                low=float(row['Low']),
                close=float(row['Close']),
                volume=float(row['Volume'])
            )
            bars.append(bar)

        return bars

    def _save_to_cache(self, cache_file: Path, bars: List[MarketBar]):
        """Save bars to cache file"""
        data = [bar.to_dict() for bar in bars]

        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _load_from_cache(self, cache_file: Path) -> List[MarketBar]:
        """Load bars from cache file"""
        with open(cache_file, 'r') as f:
            data = json.load(f)

        bars = []
        for item in data:
            bar = MarketBar(
                timestamp=datetime.fromisoformat(item['timestamp']),
                open=item['open'],
                high=item['high'],
                low=item['low'],
                close=item['close'],
                volume=item['volume']
            )
            bars.append(bar)

        return bars

    def clear_cache(self, symbol: Optional[str] = None):
        """
        Clear cached data.

        Args:
            symbol: If specified, clear only this symbol. Otherwise clear all.
        """
        if symbol:
            pattern = f"{symbol}_*.json"
            files = list(self.cache_dir.glob(pattern))
            count = len(files)
            for f in files:
                f.unlink()
            print(f"🗑️  Cleared {count} cache files for {symbol}")
        else:
            files = list(self.cache_dir.glob("*.json"))
            count = len(files)
            for f in files:
                f.unlink()
            print(f"🗑️  Cleared {count} cache files")


# ============================================================================
# Market Regime Detector
# ============================================================================

class MarketRegimeDetector:
    """
    Detect market regimes in historical data.

    Analyzes real market data to classify into regimes (bull, bear, volatile, etc.)
    based on statistical properties.
    """

    @staticmethod
    def detect_regime(bars: List[MarketBar], window: int = 20) -> str:
        """
        Detect current market regime based on recent bars.

        Args:
            bars: List of market bars
            window: Number of bars to analyze

        Returns:
            Regime name ('bull', 'bear', 'volatile', 'sideways', 'crash')
        """
        if len(bars) < window:
            return 'unknown'

        recent_bars = bars[-window:]
        prices = [bar.close for bar in recent_bars]

        # Calculate metrics
        total_return = (prices[-1] - prices[0]) / prices[0]
        returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
        volatility = (sum(r**2 for r in returns) / len(returns)) ** 0.5

        # Classify regime
        if volatility > 0.04:  # High volatility
            if total_return < -0.10:  # Large drop
                return 'crash'
            else:
                return 'volatile'
        elif abs(total_return) < 0.02:  # Low movement
            return 'sideways'
        elif total_return > 0.05:  # Strong uptrend
            return 'bull'
        elif total_return < -0.05:  # Strong downtrend
            return 'bear'
        else:
            return 'sideways'

    @staticmethod
    def segment_by_regime(
        bars: List[MarketBar],
        window: int = 20
    ) -> List[Dict]:
        """
        Segment historical data into regime periods.

        Args:
            bars: List of market bars
            window: Window for regime detection

        Returns:
            List of regime segments with start/end indices and regime type
        """
        if len(bars) < window:
            return []

        segments = []
        current_regime = None
        segment_start = 0

        for i in range(window, len(bars)):
            regime = MarketRegimeDetector.detect_regime(bars[:i+1], window)

            if regime != current_regime:
                if current_regime is not None:
                    segments.append({
                        'regime': current_regime,
                        'start_idx': segment_start,
                        'end_idx': i - 1,
                        'bars': i - segment_start,
                        'start_date': bars[segment_start].timestamp,
                        'end_date': bars[i-1].timestamp
                    })

                current_regime = regime
                segment_start = i

        # Add final segment
        if current_regime is not None:
            segments.append({
                'regime': current_regime,
                'start_idx': segment_start,
                'end_idx': len(bars) - 1,
                'bars': len(bars) - segment_start,
                'start_date': bars[segment_start].timestamp,
                'end_date': bars[-1].timestamp
            })

        return segments
