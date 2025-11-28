"""
NEXUS Strategy Storage System

Manages storage, versioning, and performance tracking of AI-generated trading strategies.

Features:
- SQLite database for strategy persistence
- Version control and history tracking
- Performance metrics and backtest result linkage
- Strategy comparison and ranking
- AI-assisted profitability analysis

Database Schema:
- strategies: Core strategy information
- strategy_versions: Version history
- strategy_backtests: Backtest results linkage
- strategy_metrics: Performance metrics aggregation
"""

import sqlite3
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib


@dataclass
class Strategy:
    """Trading strategy model"""
    id: Optional[str] = None
    name: str = ""
    description: str = ""
    strategy_type: str = "ai_generated"  # ai_generated, manual, evolved
    code: str = ""  # Strategy code (Python function)
    parameters: Dict[str, Any] = None

    # Metadata
    created_by: str = "autonomous_strategy_agent"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    version: int = 1
    parent_strategy_id: Optional[str] = None  # For evolved strategies

    # Performance tracking
    total_backtests: int = 0
    best_sharpe_ratio: Optional[float] = None
    best_total_return_pct: Optional[float] = None
    avg_win_rate: Optional[float] = None

    # Status
    is_active: bool = True
    is_favorite: bool = False
    tags: List[str] = None

    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}
        if self.tags is None:
            self.tags = []
        if self.id is None:
            # Generate ID from name + timestamp
            hash_input = f"{self.name}_{datetime.utcnow().isoformat()}"
            self.id = hashlib.md5(hash_input.encode()).hexdigest()[:12]
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()
        if self.updated_at is None:
            self.updated_at = self.created_at


@dataclass
class BacktestResult:
    """Backtest result linked to a strategy"""
    id: str
    strategy_id: str
    strategy_version: int

    # Backtest configuration
    symbol: str
    start_date: str
    end_date: str
    timeframe: str
    initial_capital: float

    # Performance metrics
    total_return_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown_pct: float
    win_rate: float
    total_trades: int
    profit_factor: float

    # Metadata
    created_at: str
    duration_seconds: Optional[float] = None


class StrategyStorage:
    """
    Strategy storage and management system

    Provides persistence, versioning, and performance tracking for trading strategies.
    """

    def __init__(self, db_path: str = "data/strategies.db"):
        """Initialize strategy storage"""
        self.db_path = db_path

        # Ensure data directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_database()

    def _init_database(self):
        """Create database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Strategies table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS strategies (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                strategy_type TEXT NOT NULL,
                code TEXT NOT NULL,
                parameters TEXT,  -- JSON
                created_by TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                version INTEGER DEFAULT 1,
                parent_strategy_id TEXT,
                total_backtests INTEGER DEFAULT 0,
                best_sharpe_ratio REAL,
                best_total_return_pct REAL,
                avg_win_rate REAL,
                is_active BOOLEAN DEFAULT 1,
                is_favorite BOOLEAN DEFAULT 0,
                tags TEXT  -- JSON array
            )
        """)

        # Strategy versions (full history)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS strategy_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                code TEXT NOT NULL,
                parameters TEXT,
                created_at TEXT NOT NULL,
                change_description TEXT,
                FOREIGN KEY (strategy_id) REFERENCES strategies(id) ON DELETE CASCADE,
                UNIQUE(strategy_id, version)
            )
        """)

        # Backtest results
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS strategy_backtests (
                id TEXT PRIMARY KEY,
                strategy_id TEXT NOT NULL,
                strategy_version INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                initial_capital REAL NOT NULL,
                total_return_pct REAL NOT NULL,
                sharpe_ratio REAL,
                sortino_ratio REAL,
                max_drawdown_pct REAL,
                win_rate REAL,
                total_trades INTEGER,
                profit_factor REAL,
                created_at TEXT NOT NULL,
                duration_seconds REAL,
                FOREIGN KEY (strategy_id) REFERENCES strategies(id) ON DELETE CASCADE
            )
        """)

        # Create indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_strategies_sharpe
            ON strategies(best_sharpe_ratio DESC)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_strategies_return
            ON strategies(best_total_return_pct DESC)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_backtests_strategy
            ON strategy_backtests(strategy_id, created_at DESC)
        """)

        conn.commit()
        conn.close()

    def save_strategy(self, strategy: Strategy) -> str:
        """
        Save a new strategy or update existing one

        Returns:
            strategy_id
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Check if strategy exists
            cursor.execute("SELECT id, version FROM strategies WHERE id = ?", (strategy.id,))
            existing = cursor.fetchone()

            if existing:
                # Update existing strategy
                strategy.version = existing[1] + 1
                strategy.updated_at = datetime.utcnow().isoformat()

                # Save version history
                cursor.execute("""
                    INSERT INTO strategy_versions
                    (strategy_id, version, code, parameters, created_at, change_description)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    strategy.id,
                    strategy.version,
                    strategy.code,
                    json.dumps(strategy.parameters),
                    strategy.updated_at,
                    "Strategy updated"
                ))

                # Update main strategy record
                cursor.execute("""
                    UPDATE strategies SET
                        name = ?, description = ?, code = ?, parameters = ?,
                        updated_at = ?, version = ?, tags = ?
                    WHERE id = ?
                """, (
                    strategy.name, strategy.description, strategy.code,
                    json.dumps(strategy.parameters), strategy.updated_at,
                    strategy.version, json.dumps(strategy.tags), strategy.id
                ))
            else:
                # Insert new strategy
                cursor.execute("""
                    INSERT INTO strategies (
                        id, name, description, strategy_type, code, parameters,
                        created_by, created_at, updated_at, version, parent_strategy_id,
                        is_active, is_favorite, tags
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    strategy.id, strategy.name, strategy.description, strategy.strategy_type,
                    strategy.code, json.dumps(strategy.parameters), strategy.created_by,
                    strategy.created_at, strategy.updated_at, strategy.version,
                    strategy.parent_strategy_id, strategy.is_active, strategy.is_favorite,
                    json.dumps(strategy.tags)
                ))

                # Save initial version
                cursor.execute("""
                    INSERT INTO strategy_versions
                    (strategy_id, version, code, parameters, created_at, change_description)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    strategy.id, 1, strategy.code, json.dumps(strategy.parameters),
                    strategy.created_at, "Initial version"
                ))

            conn.commit()
            return strategy.id

        finally:
            conn.close()

    def get_strategy(self, strategy_id: str, version: Optional[int] = None) -> Optional[Strategy]:
        """
        Get strategy by ID

        Args:
            strategy_id: Strategy identifier
            version: Specific version to retrieve (default: latest)

        Returns:
            Strategy object or None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            if version is None:
                # Get latest version
                cursor.execute("SELECT * FROM strategies WHERE id = ?", (strategy_id,))
            else:
                # Get specific version from history
                cursor.execute("""
                    SELECT s.*, v.code, v.parameters
                    FROM strategies s
                    JOIN strategy_versions v ON s.id = v.strategy_id
                    WHERE s.id = ? AND v.version = ?
                """, (strategy_id, version))

            row = cursor.fetchone()
            if not row:
                return None

            # Parse row into Strategy object
            return self._row_to_strategy(row)

        finally:
            conn.close()

    def list_strategies(
        self,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "created_at",  # created_at, best_sharpe_ratio, best_total_return_pct
        filter_type: Optional[str] = None,
        filter_tags: Optional[List[str]] = None,
        active_only: bool = True
    ) -> List[Strategy]:
        """
        List strategies with filtering and sorting

        Args:
            limit: Maximum number of strategies to return
            offset: Offset for pagination
            sort_by: Field to sort by
            filter_type: Filter by strategy_type
            filter_tags: Filter by tags (any match)
            active_only: Only return active strategies

        Returns:
            List of Strategy objects
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Build query
            query = "SELECT * FROM strategies WHERE 1=1"
            params = []

            if active_only:
                query += " AND is_active = 1"

            if filter_type:
                query += " AND strategy_type = ?"
                params.append(filter_type)

            if filter_tags:
                # Check if any tag matches
                tag_conditions = " OR ".join(["tags LIKE ?" for _ in filter_tags])
                query += f" AND ({tag_conditions})"
                params.extend([f"%{tag}%" for tag in filter_tags])

            # Sort
            sort_mapping = {
                "created_at": "created_at DESC",
                "best_sharpe_ratio": "best_sharpe_ratio DESC",
                "best_total_return_pct": "best_total_return_pct DESC",
                "name": "name ASC"
            }
            query += f" ORDER BY {sort_mapping.get(sort_by, 'created_at DESC')}"

            # Pagination
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [self._row_to_strategy(row) for row in rows]

        finally:
            conn.close()

    def save_backtest_result(self, result: BacktestResult):
        """
        Save backtest result and update strategy metrics

        Args:
            result: BacktestResult object
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Insert backtest result
            cursor.execute("""
                INSERT INTO strategy_backtests (
                    id, strategy_id, strategy_version, symbol, start_date, end_date,
                    timeframe, initial_capital, total_return_pct, sharpe_ratio,
                    sortino_ratio, max_drawdown_pct, win_rate, total_trades,
                    profit_factor, created_at, duration_seconds
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.id, result.strategy_id, result.strategy_version,
                result.symbol, result.start_date, result.end_date, result.timeframe,
                result.initial_capital, result.total_return_pct, result.sharpe_ratio,
                result.sortino_ratio, result.max_drawdown_pct, result.win_rate,
                result.total_trades, result.profit_factor, result.created_at,
                result.duration_seconds
            ))

            # Update strategy aggregated metrics
            cursor.execute("""
                UPDATE strategies SET
                    total_backtests = total_backtests + 1,
                    best_sharpe_ratio = MAX(best_sharpe_ratio, ?),
                    best_total_return_pct = MAX(best_total_return_pct, ?),
                    avg_win_rate = (
                        SELECT AVG(win_rate) FROM strategy_backtests
                        WHERE strategy_id = ?
                    )
                WHERE id = ?
            """, (
                result.sharpe_ratio, result.total_return_pct,
                result.strategy_id, result.strategy_id
            ))

            conn.commit()

        finally:
            conn.close()

    def get_strategy_backtests(
        self,
        strategy_id: str,
        limit: int = 20
    ) -> List[BacktestResult]:
        """
        Get all backtest results for a strategy

        Args:
            strategy_id: Strategy identifier
            limit: Maximum number of results to return

        Returns:
            List of BacktestResult objects
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT * FROM strategy_backtests
                WHERE strategy_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (strategy_id, limit))

            rows = cursor.fetchall()
            return [self._row_to_backtest(row) for row in rows]

        finally:
            conn.close()

    def get_top_strategies(
        self,
        metric: str = "sharpe_ratio",  # sharpe_ratio, total_return_pct, win_rate
        limit: int = 10
    ) -> List[Tuple[Strategy, Dict[str, float]]]:
        """
        Get top-performing strategies by metric

        Args:
            metric: Performance metric to rank by
            limit: Number of strategies to return

        Returns:
            List of (Strategy, metrics) tuples
        """
        metric_mapping = {
            "sharpe_ratio": "best_sharpe_ratio",
            "total_return_pct": "best_total_return_pct",
            "win_rate": "avg_win_rate"
        }

        sort_column = metric_mapping.get(metric, "best_sharpe_ratio")

        strategies = self.list_strategies(
            limit=limit,
            sort_by=sort_column,
            active_only=True
        )

        # Build metrics dict for each strategy
        results = []
        for strategy in strategies:
            metrics = {
                "sharpe_ratio": strategy.best_sharpe_ratio,
                "total_return_pct": strategy.best_total_return_pct,
                "win_rate": strategy.avg_win_rate,
                "total_backtests": strategy.total_backtests
            }
            results.append((strategy, metrics))

        return results

    def compare_strategies(
        self,
        strategy_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Compare multiple strategies side-by-side

        Args:
            strategy_ids: List of strategy IDs to compare

        Returns:
            Comparison data with metrics for each strategy
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            comparison = {
                "strategies": [],
                "winner_by_metric": {}
            }

            for strategy_id in strategy_ids:
                strategy = self.get_strategy(strategy_id)
                if not strategy:
                    continue

                # Get all backtests for this strategy
                backtests = self.get_strategy_backtests(strategy_id, limit=100)

                # Calculate aggregate metrics
                if backtests:
                    avg_sharpe = sum(b.sharpe_ratio for b in backtests if b.sharpe_ratio) / len(backtests)
                    avg_return = sum(b.total_return_pct for b in backtests) / len(backtests)
                    avg_win_rate = sum(b.win_rate for b in backtests) / len(backtests)
                    max_drawdown = min(b.max_drawdown_pct for b in backtests)
                else:
                    avg_sharpe = avg_return = avg_win_rate = max_drawdown = None

                comparison["strategies"].append({
                    "id": strategy.id,
                    "name": strategy.name,
                    "type": strategy.strategy_type,
                    "total_backtests": len(backtests),
                    "best_sharpe_ratio": strategy.best_sharpe_ratio,
                    "best_return_pct": strategy.best_total_return_pct,
                    "avg_sharpe_ratio": avg_sharpe,
                    "avg_return_pct": avg_return,
                    "avg_win_rate": avg_win_rate,
                    "worst_drawdown_pct": max_drawdown
                })

            # Determine winners by each metric
            if comparison["strategies"]:
                comparison["winner_by_metric"] = {
                    "best_sharpe": max(comparison["strategies"], key=lambda s: s["best_sharpe_ratio"] or -999)["id"],
                    "best_return": max(comparison["strategies"], key=lambda s: s["best_return_pct"] or -999)["id"],
                    "best_win_rate": max(comparison["strategies"], key=lambda s: s["avg_win_rate"] or 0)["id"],
                    "lowest_drawdown": max(comparison["strategies"], key=lambda s: s["worst_drawdown_pct"] or -999)["id"]
                }

            return comparison

        finally:
            conn.close()

    def delete_strategy(self, strategy_id: str):
        """
        Delete strategy and all associated data (cascade)

        Args:
            strategy_id: Strategy to delete
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM strategies WHERE id = ?", (strategy_id,))
            conn.commit()

        finally:
            conn.close()

    def _row_to_strategy(self, row) -> Strategy:
        """Convert database row to Strategy object"""
        return Strategy(
            id=row[0],
            name=row[1],
            description=row[2],
            strategy_type=row[3],
            code=row[4],
            parameters=json.loads(row[5]) if row[5] else {},
            created_by=row[6],
            created_at=row[7],
            updated_at=row[8],
            version=row[9],
            parent_strategy_id=row[10],
            total_backtests=row[11],
            best_sharpe_ratio=row[12],
            best_total_return_pct=row[13],
            avg_win_rate=row[14],
            is_active=bool(row[15]),
            is_favorite=bool(row[16]),
            tags=json.loads(row[17]) if row[17] else []
        )

    def _row_to_backtest(self, row) -> BacktestResult:
        """Convert database row to BacktestResult object"""
        return BacktestResult(
            id=row[0],
            strategy_id=row[1],
            strategy_version=row[2],
            symbol=row[3],
            start_date=row[4],
            end_date=row[5],
            timeframe=row[6],
            initial_capital=row[7],
            total_return_pct=row[8],
            sharpe_ratio=row[9],
            sortino_ratio=row[10],
            max_drawdown_pct=row[11],
            win_rate=row[12],
            total_trades=row[13],
            profit_factor=row[14],
            created_at=row[15],
            duration_seconds=row[16]
        )


# Singleton instance
_storage_instance = None

def get_storage() -> StrategyStorage:
    """Get singleton storage instance"""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = StrategyStorage()
    return _storage_instance
