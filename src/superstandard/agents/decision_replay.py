"""
Decision Replay System - Time-Travel Through Agent Decisions

Allows users to replay and analyze agent decisions over time,
understanding how decisions evolved and what outcomes resulted.

Features:
- Timeline view of all decisions
- Step-by-step replay of decision-making process
- Outcome tracking and analysis
- Pattern recognition across decisions
- Learning insights extraction
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict
import statistics

from .explainable_ai import DecisionExplanation


@dataclass
class DecisionTimeline:
    """Timeline of decisions for a symbol"""

    symbol: str
    decisions: List[DecisionExplanation] = field(default_factory=list)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    def add_decision(self, decision: DecisionExplanation):
        """Add decision to timeline"""
        self.decisions.append(decision)
        self.decisions.sort(key=lambda d: d.timestamp)

        if not self.start_date or decision.timestamp < self.start_date:
            self.start_date = decision.timestamp
        if not self.end_date or decision.timestamp > self.end_date:
            self.end_date = decision.timestamp

    def get_decisions_in_range(
        self,
        start: datetime,
        end: datetime
    ) -> List[DecisionExplanation]:
        """Get decisions within date range"""
        return [
            d for d in self.decisions
            if start <= d.timestamp <= end
        ]

    def get_decision_sequence(self) -> List[str]:
        """Get sequence of decisions (buy, sell, hold)"""
        return [d.decision for d in self.decisions]


@dataclass
class ReplayFrame:
    """Single frame in decision replay"""

    timestamp: datetime
    decision: DecisionExplanation
    frame_number: int
    total_frames: int
    context: Dict[str, Any] = field(default_factory=dict)


class DecisionReplayEngine:
    """
    Engine for replaying agent decisions over time

    Allows users to:
    - View decision history chronologically
    - Replay decision-making process step-by-step
    - Analyze patterns and outcomes
    - Learn from historical decisions

    Example:
        engine = DecisionReplayEngine()

        # Add decisions
        engine.record_decision(decision1)
        engine.record_decision(decision2)

        # Create replay
        replay = engine.create_replay(symbol="AAPL")

        # Step through frames
        for frame in replay:
            print(f"Frame {frame.frame_number}/{frame.total_frames}")
            print(frame.decision.natural_language_summary)
    """

    def __init__(self):
        self.timelines: Dict[str, DecisionTimeline] = {}
        self.all_decisions: List[DecisionExplanation] = []

    def record_decision(self, decision: DecisionExplanation):
        """Record a decision in the replay system"""
        self.all_decisions.append(decision)

        # Add to symbol timeline
        if decision.symbol not in self.timelines:
            self.timelines[decision.symbol] = DecisionTimeline(symbol=decision.symbol)

        self.timelines[decision.symbol].add_decision(decision)

    def create_replay(
        self,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[ReplayFrame]:
        """
        Create a replay of decisions

        Args:
            symbol: Optional symbol filter
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            List of ReplayFrame objects
        """
        # Get decisions to replay
        if symbol and symbol in self.timelines:
            decisions = self.timelines[symbol].decisions
        else:
            decisions = self.all_decisions

        # Filter by date range
        if start_date or end_date:
            decisions = [
                d for d in decisions
                if (not start_date or d.timestamp >= start_date) and
                   (not end_date or d.timestamp <= end_date)
            ]

        # Create frames
        frames = []
        total_frames = len(decisions)

        for i, decision in enumerate(decisions, 1):
            frame = ReplayFrame(
                timestamp=decision.timestamp,
                decision=decision,
                frame_number=i,
                total_frames=total_frames
            )
            frames.append(frame)

        return frames

    def analyze_decision_pattern(
        self,
        symbol: str,
        time_window: timedelta = timedelta(days=30)
    ) -> Dict[str, Any]:
        """
        Analyze decision patterns for a symbol

        Args:
            symbol: Stock symbol
            time_window: Time window to analyze

        Returns:
            Dictionary with pattern analysis
        """
        if symbol not in self.timelines:
            return {'error': f'No decisions found for {symbol}'}

        timeline = self.timelines[symbol]

        # Get recent decisions
        end_date = datetime.now()
        start_date = end_date - time_window
        recent_decisions = timeline.get_decisions_in_range(start_date, end_date)

        if not recent_decisions:
            return {'error': 'No recent decisions in time window'}

        # Analyze patterns
        decision_counts = defaultdict(int)
        total_confidence = 0.0
        outcomes = {'success': 0, 'failure': 0, 'pending': 0}

        for decision in recent_decisions:
            decision_counts[decision.decision] += 1
            total_confidence += decision.confidence

            if decision.outcome:
                outcomes[decision.outcome] += 1
            else:
                outcomes['pending'] += 1

        # Calculate statistics
        avg_confidence = total_confidence / len(recent_decisions)

        # Success rate (only for executed decisions)
        total_completed = outcomes['success'] + outcomes['failure']
        success_rate = outcomes['success'] / total_completed if total_completed > 0 else 0.0

        return {
            'symbol': symbol,
            'time_window_days': time_window.days,
            'total_decisions': len(recent_decisions),
            'decision_distribution': dict(decision_counts),
            'average_confidence': avg_confidence,
            'outcomes': dict(outcomes),
            'success_rate': success_rate,
            'most_common_decision': max(decision_counts.items(), key=lambda x: x[1])[0]
        }

    def get_learning_insights(
        self,
        symbol: str,
        min_decisions: int = 10
    ) -> List[str]:
        """
        Extract learning insights from decision history

        Args:
            symbol: Stock symbol
            min_decisions: Minimum decisions required for insights

        Returns:
            List of insight strings
        """
        if symbol not in self.timelines:
            return [f"No decision history for {symbol}"]

        timeline = self.timelines[symbol]

        if len(timeline.decisions) < min_decisions:
            return [f"Need at least {min_decisions} decisions for insights (have {len(timeline.decisions)})"]

        insights = []

        # Analyze confidence vs outcome
        successful = [d for d in timeline.decisions if d.outcome == 'success']
        failed = [d for d in timeline.decisions if d.outcome == 'failure']

        if successful and failed:
            avg_success_conf = statistics.mean(d.confidence for d in successful)
            avg_fail_conf = statistics.mean(d.confidence for d in failed)

            if avg_success_conf > avg_fail_conf + 0.1:
                insights.append(
                    f"✅ Higher confidence decisions ({avg_success_conf * 100:.1f}%) "
                    f"are more likely to succeed than lower confidence ones ({avg_fail_conf * 100:.1f}%)"
                )
            elif avg_fail_conf > avg_success_conf + 0.1:
                insights.append(
                    f"⚠️ Warning: Higher confidence doesn't guarantee success. "
                    f"Failed decisions had {avg_fail_conf * 100:.1f}% avg confidence vs "
                    f"{avg_success_conf * 100:.1f}% for successful ones."
                )

        # Analyze decision sequences
        sequence = timeline.get_decision_sequence()
        if len(sequence) >= 5:
            # Look for patterns
            buy_streaks = self._find_streaks(sequence, 'buy')
            sell_streaks = self._find_streaks(sequence, 'sell')

            if buy_streaks:
                max_buy_streak = max(buy_streaks)
                if max_buy_streak >= 3:
                    insights.append(
                        f"📊 Observed {max_buy_streak} consecutive BUY decisions - "
                        "agent identified sustained bullish trend"
                    )

            if sell_streaks:
                max_sell_streak = max(sell_streaks)
                if max_sell_streak >= 3:
                    insights.append(
                        f"📊 Observed {max_sell_streak} consecutive SELL decisions - "
                        "agent identified sustained bearish trend"
                    )

        # Analyze outcome improvement over time
        if len(timeline.decisions) >= 20:
            first_half = timeline.decisions[:len(timeline.decisions)//2]
            second_half = timeline.decisions[len(timeline.decisions)//2:]

            first_success_rate = self._calculate_success_rate(first_half)
            second_success_rate = self._calculate_success_rate(second_half)

            if second_success_rate > first_success_rate + 0.1:
                insights.append(
                    f"📈 Agent is improving! Success rate increased from "
                    f"{first_success_rate * 100:.1f}% to {second_success_rate * 100:.1f}%"
                )
            elif first_success_rate > second_success_rate + 0.1:
                insights.append(
                    f"⚠️ Agent performance declining. Success rate dropped from "
                    f"{first_success_rate * 100:.1f}% to {second_success_rate * 100:.1f}%"
                )

        return insights if insights else ["Not enough data for meaningful insights yet"]

    def _find_streaks(self, sequence: List[str], value: str) -> List[int]:
        """Find streaks of a specific value in sequence"""
        streaks = []
        current_streak = 0

        for item in sequence:
            if item == value:
                current_streak += 1
            else:
                if current_streak > 0:
                    streaks.append(current_streak)
                current_streak = 0

        if current_streak > 0:
            streaks.append(current_streak)

        return streaks

    def _calculate_success_rate(self, decisions: List[DecisionExplanation]) -> float:
        """Calculate success rate for a list of decisions"""
        completed = [d for d in decisions if d.outcome in ('success', 'failure')]
        if not completed:
            return 0.0

        successful = [d for d in completed if d.outcome == 'success']
        return len(successful) / len(completed)

    def export_replay_data(
        self,
        symbol: str,
        format: str = 'json'
    ) -> str:
        """
        Export replay data for external analysis

        Args:
            symbol: Stock symbol
            format: Export format ('json', 'csv')

        Returns:
            Formatted string data
        """
        if symbol not in self.timelines:
            return ''

        timeline = self.timelines[symbol]

        if format == 'json':
            import json
            data = {
                'symbol': symbol,
                'total_decisions': len(timeline.decisions),
                'start_date': timeline.start_date.isoformat() if timeline.start_date else None,
                'end_date': timeline.end_date.isoformat() if timeline.end_date else None,
                'decisions': [d.to_dict() for d in timeline.decisions]
            }
            return json.dumps(data, indent=2)

        elif format == 'csv':
            lines = ['timestamp,symbol,decision,confidence,outcome,return']
            for d in timeline.decisions:
                lines.append(
                    f"{d.timestamp.isoformat()},"
                    f"{d.symbol},"
                    f"{d.decision},"
                    f"{d.confidence:.4f},"
                    f"{d.outcome or 'pending'},"
                    f"{d.actual_return or ''}"
                )
            return '\n'.join(lines)

        return ''

    def get_timeline_summary(self, symbol: str) -> Dict[str, Any]:
        """Get summary of decision timeline for symbol"""
        if symbol not in self.timelines:
            return {'error': f'No timeline for {symbol}'}

        timeline = self.timelines[symbol]

        return {
            'symbol': symbol,
            'total_decisions': len(timeline.decisions),
            'start_date': timeline.start_date.isoformat() if timeline.start_date else None,
            'end_date': timeline.end_date.isoformat() if timeline.end_date else None,
            'time_span_days': (timeline.end_date - timeline.start_date).days if timeline.start_date and timeline.end_date else 0,
            'decision_sequence': timeline.get_decision_sequence()
        }
