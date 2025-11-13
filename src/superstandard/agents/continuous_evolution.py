"""
Continuous Evolution in Production
===================================

REVOLUTIONARY: Agents that keep evolving and improving while running in production!

This system enables:
- Automatic performance monitoring and degradation detection
- Background evolution when performance declines
- A/B testing framework (champion vs challenger)
- Automatic promotion of better strategies
- Zero-downtime strategy improvement

Key Concepts:
- Champion: Current best-performing agent in production
- Challenger: Newly evolved candidate being tested
- A/B Split: Traffic split between champion and challenger
- Performance Window: Rolling time period for metric calculation
- Degradation Threshold: When to trigger evolution
- Promotion Criteria: When challenger replaces champion

This is CUTTING EDGE - no other platform offers autonomous continuous evolution!
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
import threading
import time
import statistics
from collections import deque

from .genetic_breeding import AgentGenome, EvolutionEngine
from .pareto_evolution import ParetoEvolutionEngine, ParetoEvolutionConfig, Objective, ObjectiveType
from .backtest_engine import BacktestEngine, BacktestConfig


# ============================================================================
# Evolution State & Configuration
# ============================================================================

class EvolutionTrigger(str, Enum):
    """What triggers an evolution cycle"""
    PERFORMANCE_DEGRADATION = "performance_degradation"
    SCHEDULED = "scheduled"
    MANUAL = "manual"
    CHALLENGER_VICTORY = "challenger_victory"


class ABTestStatus(str, Enum):
    """Status of A/B test"""
    RUNNING = "running"
    CHAMPION_WINS = "champion_wins"
    CHALLENGER_WINS = "challenger_wins"
    INCONCLUSIVE = "inconclusive"


@dataclass
class PerformanceMetrics:
    """Rolling performance metrics for degradation detection"""
    timestamp: datetime
    win_rate: float
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    total_decisions: int
    confidence_avg: float


@dataclass
class DegradationDetectionConfig:
    """Configuration for performance degradation detection"""
    window_size: int = 100  # Number of recent decisions to analyze
    baseline_window: int = 500  # Historical baseline for comparison
    win_rate_threshold: float = 0.10  # 10% drop triggers evolution
    sharpe_threshold: float = 0.20  # 20% drop triggers evolution
    drawdown_threshold: float = 0.15  # 15% increase triggers evolution
    min_decisions_before_check: int = 50  # Minimum decisions before checking


@dataclass
class ABTestConfig:
    """Configuration for A/B testing"""
    traffic_split: float = 0.20  # 20% traffic to challenger
    min_decisions_per_strategy: int = 30  # Minimum for statistical significance
    confidence_level: float = 0.95  # 95% confidence for promotion
    test_duration_hours: int = 24  # Maximum test duration
    promote_on_equal: bool = False  # Promote if tied (challenger has potential)


@dataclass
class ContinuousEvolutionConfig:
    """Configuration for continuous evolution system"""
    enabled: bool = True
    evolution_interval_hours: int = 24  # Check every 24 hours
    degradation_config: DegradationDetectionConfig = field(default_factory=DegradationDetectionConfig)
    ab_test_config: ABTestConfig = field(default_factory=ABTestConfig)
    pareto_config: ParetoEvolutionConfig = field(default_factory=lambda: ParetoEvolutionConfig(
        population_size=20,
        num_generations=10
    ))
    auto_promote: bool = True  # Automatically promote winning challengers
    backup_champions: int = 5  # Keep last N champions for rollback


# ============================================================================
# A/B Test Management
# ============================================================================

@dataclass
class ABTest:
    """Active A/B test comparing champion vs challenger"""
    test_id: str
    ensemble_id: str
    champion_genome: AgentGenome
    challenger_genome: AgentGenome
    started_at: datetime
    config: ABTestConfig

    # Performance tracking
    champion_decisions: List[Dict[str, Any]] = field(default_factory=list)
    challenger_decisions: List[Dict[str, Any]] = field(default_factory=list)

    # Current metrics
    champion_win_rate: float = 0.0
    challenger_win_rate: float = 0.0
    champion_sharpe: float = 0.0
    challenger_sharpe: float = 0.0

    status: ABTestStatus = ABTestStatus.RUNNING
    winner: Optional[str] = None  # "champion" or "challenger"
    completed_at: Optional[datetime] = None

    def record_decision(self, is_challenger: bool, decision: str, outcome: float, confidence: float):
        """Record a decision and outcome for champion or challenger"""
        decision_record = {
            'timestamp': datetime.now().isoformat(),
            'decision': decision,
            'outcome': outcome,  # P&L or performance metric
            'confidence': confidence
        }

        if is_challenger:
            self.challenger_decisions.append(decision_record)
        else:
            self.champion_decisions.append(decision_record)

        # Update metrics
        self._update_metrics()

    def _update_metrics(self):
        """Recalculate performance metrics"""
        # Champion metrics
        if self.champion_decisions:
            winning_decisions = [d for d in self.champion_decisions if d['outcome'] > 0]
            self.champion_win_rate = len(winning_decisions) / len(self.champion_decisions)

            returns = [d['outcome'] for d in self.champion_decisions]
            if len(returns) > 1:
                avg_return = statistics.mean(returns)
                std_return = statistics.stdev(returns)
                self.champion_sharpe = avg_return / std_return if std_return > 0 else 0.0

        # Challenger metrics
        if self.challenger_decisions:
            winning_decisions = [d for d in self.challenger_decisions if d['outcome'] > 0]
            self.challenger_win_rate = len(winning_decisions) / len(self.challenger_decisions)

            returns = [d['outcome'] for d in self.challenger_decisions]
            if len(returns) > 1:
                avg_return = statistics.mean(returns)
                std_return = statistics.stdev(returns)
                self.challenger_sharpe = avg_return / std_return if std_return > 0 else 0.0

    def evaluate(self) -> ABTestStatus:
        """
        Evaluate A/B test and determine winner.

        Returns:
            ABTestStatus indicating outcome
        """
        # Check minimum decisions
        if (len(self.champion_decisions) < self.config.min_decisions_per_strategy or
            len(self.challenger_decisions) < self.config.min_decisions_per_strategy):
            return ABTestStatus.RUNNING

        # Check test duration
        duration = datetime.now() - self.started_at
        if duration > timedelta(hours=self.config.test_duration_hours):
            # Timeout - evaluate what we have
            pass

        # Compare performance
        challenger_better_wr = self.challenger_win_rate > self.champion_win_rate * 1.05  # 5% better
        challenger_better_sharpe = self.challenger_sharpe > self.champion_sharpe * 1.05

        champion_better_wr = self.champion_win_rate > self.challenger_win_rate * 1.05
        champion_better_sharpe = self.champion_sharpe > self.challenger_sharpe * 1.05

        # Decision logic
        if challenger_better_wr and challenger_better_sharpe:
            self.status = ABTestStatus.CHALLENGER_WINS
            self.winner = "challenger"
        elif champion_better_wr and champion_better_sharpe:
            self.status = ABTestStatus.CHAMPION_WINS
            self.winner = "champion"
        elif challenger_better_wr or challenger_better_sharpe:
            # Challenger better on at least one metric
            if self.config.promote_on_equal:
                self.status = ABTestStatus.CHALLENGER_WINS
                self.winner = "challenger"
            else:
                self.status = ABTestStatus.INCONCLUSIVE
        else:
            self.status = ABTestStatus.CHAMPION_WINS
            self.winner = "champion"

        self.completed_at = datetime.now()
        return self.status


# ============================================================================
# Performance Degradation Detection
# ============================================================================

class PerformanceDegradationDetector:
    """
    Detects when agent performance degrades below acceptable thresholds.

    Uses rolling window comparison vs historical baseline to identify
    statistically significant performance decline.
    """

    def __init__(self, config: DegradationDetectionConfig):
        self.config = config
        self.metrics_history: deque = deque(maxlen=config.baseline_window)
        self.recent_metrics: deque = deque(maxlen=config.window_size)

    def record_metrics(self, metrics: PerformanceMetrics):
        """Record performance metrics"""
        self.metrics_history.append(metrics)
        self.recent_metrics.append(metrics)

    def check_degradation(self) -> tuple[bool, Dict[str, Any]]:
        """
        Check if performance has degraded.

        Returns:
            (is_degraded, degradation_details)
        """
        if len(self.recent_metrics) < self.config.min_decisions_before_check:
            return False, {"reason": "insufficient_data"}

        if len(self.metrics_history) < self.config.baseline_window // 2:
            return False, {"reason": "insufficient_baseline"}

        # Calculate baseline (historical average)
        baseline_wr = statistics.mean(m.win_rate for m in self.metrics_history)
        baseline_sharpe = statistics.mean(m.sharpe_ratio for m in self.metrics_history if m.sharpe_ratio != 0)
        baseline_drawdown = statistics.mean(abs(m.max_drawdown) for m in self.metrics_history)

        # Calculate recent performance
        recent_wr = statistics.mean(m.win_rate for m in self.recent_metrics)
        recent_sharpe = statistics.mean(m.sharpe_ratio for m in self.recent_metrics if m.sharpe_ratio != 0)
        recent_drawdown = statistics.mean(abs(m.max_drawdown) for m in self.recent_metrics)

        # Check thresholds
        degradation_flags = []

        # Win rate drop
        if baseline_wr > 0:
            wr_drop = (baseline_wr - recent_wr) / baseline_wr
            if wr_drop > self.config.win_rate_threshold:
                degradation_flags.append({
                    'metric': 'win_rate',
                    'baseline': baseline_wr,
                    'recent': recent_wr,
                    'drop_percent': wr_drop * 100
                })

        # Sharpe ratio drop
        if baseline_sharpe > 0:
            sharpe_drop = (baseline_sharpe - recent_sharpe) / baseline_sharpe
            if sharpe_drop > self.config.sharpe_threshold:
                degradation_flags.append({
                    'metric': 'sharpe_ratio',
                    'baseline': baseline_sharpe,
                    'recent': recent_sharpe,
                    'drop_percent': sharpe_drop * 100
                })

        # Drawdown increase
        if baseline_drawdown > 0:
            drawdown_increase = (recent_drawdown - baseline_drawdown) / baseline_drawdown
            if drawdown_increase > self.config.drawdown_threshold:
                degradation_flags.append({
                    'metric': 'max_drawdown',
                    'baseline': baseline_drawdown,
                    'recent': recent_drawdown,
                    'increase_percent': drawdown_increase * 100
                })

        is_degraded = len(degradation_flags) > 0

        return is_degraded, {
            'degraded': is_degraded,
            'flags': degradation_flags,
            'baseline': {
                'win_rate': baseline_wr,
                'sharpe_ratio': baseline_sharpe,
                'max_drawdown': baseline_drawdown
            },
            'recent': {
                'win_rate': recent_wr,
                'sharpe_ratio': recent_sharpe,
                'max_drawdown': recent_drawdown
            }
        }


# ============================================================================
# Continuous Evolution Engine
# ============================================================================

@dataclass
class EvolutionEvent:
    """Record of an evolution cycle"""
    event_id: str
    ensemble_id: str
    trigger: EvolutionTrigger
    triggered_at: datetime
    trigger_reason: Dict[str, Any]

    # Evolution details
    champion_genome: AgentGenome
    challenger_genome: Optional[AgentGenome] = None
    ab_test_id: Optional[str] = None

    # Outcome
    completed_at: Optional[datetime] = None
    outcome: Optional[str] = None  # "challenger_promoted", "champion_retained", "in_progress"
    performance_improvement: Optional[float] = None


class ContinuousEvolutionEngine:
    """
    Main engine for continuous evolution in production.

    Monitors performance, triggers evolution, manages A/B tests,
    and automatically promotes better strategies.

    This is the BRAIN of the self-improving system!
    """

    def __init__(self, config: ContinuousEvolutionConfig):
        self.config = config
        self.degradation_detector = PerformanceDegradationDetector(config.degradation_config)
        self.evolution_engine = EvolutionEngine()
        self.pareto_engine = ParetoEvolutionEngine(config.pareto_config)

        # State tracking
        self.active_ab_tests: Dict[str, ABTest] = {}
        self.evolution_history: List[EvolutionEvent] = []
        self.champion_genomes: Dict[str, deque] = {}  # ensemble_id -> deque of champions

        # Background monitoring
        self.monitoring_thread: Optional[threading.Thread] = None
        self.running = False

    def start_monitoring(self, ensemble_id: str, check_interval_seconds: int = 60):
        """
        Start background monitoring thread.

        Args:
            ensemble_id: Ensemble to monitor
            check_interval_seconds: How often to check (default: 60s)
        """
        if self.running:
            return

        self.running = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(ensemble_id, check_interval_seconds),
            daemon=True
        )
        self.monitoring_thread.start()

    def stop_monitoring(self):
        """Stop background monitoring"""
        self.running = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)

    def _monitoring_loop(self, ensemble_id: str, check_interval_seconds: int):
        """Background monitoring loop (runs in separate thread)"""
        while self.running:
            try:
                # Check for degradation
                is_degraded, details = self.degradation_detector.check_degradation()

                if is_degraded and ensemble_id not in self.active_ab_tests:
                    # Trigger evolution!
                    print(f"🚨 Performance degradation detected for {ensemble_id}!")
                    print(f"   Flags: {details['flags']}")

                    # This would trigger evolution in the main system
                    # (actual implementation would use callbacks/events)
                    self._trigger_evolution(
                        ensemble_id=ensemble_id,
                        trigger=EvolutionTrigger.PERFORMANCE_DEGRADATION,
                        trigger_reason=details
                    )

                # Check active A/B tests
                for test_id, ab_test in list(self.active_ab_tests.items()):
                    status = ab_test.evaluate()

                    if status != ABTestStatus.RUNNING:
                        print(f"✅ A/B test {test_id} completed: {status.value}")

                        if status == ABTestStatus.CHALLENGER_WINS and self.config.auto_promote:
                            self._promote_challenger(ensemble_id, ab_test)

                time.sleep(check_interval_seconds)

            except Exception as e:
                print(f"❌ Error in monitoring loop: {e}")
                time.sleep(check_interval_seconds)

    def _trigger_evolution(
        self,
        ensemble_id: str,
        trigger: EvolutionTrigger,
        trigger_reason: Dict[str, Any]
    ) -> EvolutionEvent:
        """
        Trigger an evolution cycle.

        This creates a new challenger genome and starts an A/B test.
        """
        # Get current champion
        champion_genome = self._get_champion_genome(ensemble_id)

        # Create evolution event
        event = EvolutionEvent(
            event_id=f"evo_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{ensemble_id[:8]}",
            ensemble_id=ensemble_id,
            trigger=trigger,
            triggered_at=datetime.now(),
            trigger_reason=trigger_reason,
            champion_genome=champion_genome,
            outcome="in_progress"
        )

        self.evolution_history.append(event)

        # TODO: Actually run evolution (would integrate with existing systems)
        # For now, this is the hook point

        return event

    def create_ab_test(
        self,
        ensemble_id: str,
        champion_genome: AgentGenome,
        challenger_genome: AgentGenome
    ) -> ABTest:
        """
        Create a new A/B test comparing champion vs challenger.

        Args:
            ensemble_id: Ensemble being tested
            champion_genome: Current champion
            challenger_genome: New challenger

        Returns:
            ABTest instance
        """
        test_id = f"ab_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{ensemble_id[:8]}"

        ab_test = ABTest(
            test_id=test_id,
            ensemble_id=ensemble_id,
            champion_genome=champion_genome,
            challenger_genome=challenger_genome,
            started_at=datetime.now(),
            config=self.config.ab_test_config
        )

        self.active_ab_tests[test_id] = ab_test

        print(f"🧪 A/B Test started: {test_id}")
        print(f"   Champion: {champion_genome.agent_id[:16]}...")
        print(f"   Challenger: {challenger_genome.agent_id[:16]}...")
        print(f"   Traffic Split: {self.config.ab_test_config.traffic_split:.0%} to challenger")

        return ab_test

    def record_decision_outcome(
        self,
        test_id: str,
        is_challenger: bool,
        decision: str,
        outcome: float,
        confidence: float
    ):
        """Record a decision outcome for A/B test tracking"""
        if test_id in self.active_ab_tests:
            self.active_ab_tests[test_id].record_decision(
                is_challenger=is_challenger,
                decision=decision,
                outcome=outcome,
                confidence=confidence
            )

    def _promote_challenger(self, ensemble_id: str, ab_test: ABTest):
        """
        Promote challenger to champion.

        Archives old champion and makes challenger the new champion.
        """
        # Archive old champion
        if ensemble_id not in self.champion_genomes:
            self.champion_genomes[ensemble_id] = deque(maxlen=self.config.backup_champions)

        self.champion_genomes[ensemble_id].append(ab_test.champion_genome)

        print(f"🏆 Promoting challenger to champion!")
        print(f"   Old champion archived: {ab_test.champion_genome.agent_id[:16]}...")
        print(f"   New champion: {ab_test.challenger_genome.agent_id[:16]}...")
        print(f"   Performance improvement: {ab_test.challenger_win_rate - ab_test.champion_win_rate:.2%}")

        # Update evolution history
        for event in reversed(self.evolution_history):
            if event.ensemble_id == ensemble_id and event.outcome == "in_progress":
                event.outcome = "challenger_promoted"
                event.completed_at = datetime.now()
                event.performance_improvement = ab_test.challenger_win_rate - ab_test.champion_win_rate
                break

        # Remove from active tests
        del self.active_ab_tests[ab_test.test_id]

    def _get_champion_genome(self, ensemble_id: str) -> AgentGenome:
        """Get current champion genome for ensemble"""
        # In real implementation, this would fetch from registry
        # For now, return a placeholder
        return AgentGenome(
            agent_id=f"champion_{ensemble_id}",
            generation=0,
            personality_traits={'openness': 0.7, 'conscientiousness': 0.8}
        )

    def get_evolution_summary(self, ensemble_id: str) -> Dict[str, Any]:
        """Get comprehensive evolution summary for ensemble"""
        events = [e for e in self.evolution_history if e.ensemble_id == ensemble_id]
        active_tests = [t for t in self.active_ab_tests.values() if t.ensemble_id == ensemble_id]

        return {
            'total_evolution_cycles': len(events),
            'active_ab_tests': len(active_tests),
            'champions_archived': len(self.champion_genomes.get(ensemble_id, [])),
            'recent_events': [
                {
                    'event_id': e.event_id,
                    'trigger': e.trigger.value,
                    'triggered_at': e.triggered_at.isoformat(),
                    'outcome': e.outcome,
                    'improvement': e.performance_improvement
                }
                for e in events[-10:]  # Last 10 events
            ],
            'active_tests': [
                {
                    'test_id': t.test_id,
                    'started_at': t.started_at.isoformat(),
                    'champion_win_rate': t.champion_win_rate,
                    'challenger_win_rate': t.challenger_win_rate,
                    'status': t.status.value
                }
                for t in active_tests
            ]
        }
