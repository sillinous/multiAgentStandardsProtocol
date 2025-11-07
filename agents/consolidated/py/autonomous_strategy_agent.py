"""
🌙 Moon Dev's Autonomous Strategy Agent
Built with love by Moon Dev 🚀

AUTONOMOUS FEATURES:
- Real-time market analysis and signal generation
- Collaborative strategy development with other agents
- AI-powered multi-model consensus
- Protocol-compliant (A2A, A2Pay, MCP, FIPA)
- Event-driven architecture
- Tool registration for analysis services
- Emergent strategy intelligence
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from autonomous import (
    AutonomousAgent,
    get_message_bus,
    get_shared_memory,
    ConsensusManager,
    A2APerformative,
    FIPAPerformative,
    MessagePriority,
    VoteType,
    PaymentType,
)
from autonomous.monitoring_dashboard import register_agent

import json
import time
import random
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Import existing utilities
try:
    from src import config
    from src import nice_funcs as n
    from src.config import *
    from src.models.model_factory import ModelFactory
except ImportError:
    import config
    import nice_funcs as n
    from config import *
    from models.model_factory import ModelFactory

load_dotenv()


class AutonomousStrategyAgent(AutonomousAgent):
    """
    Autonomous Strategy Agent

    Generates trading signals through AI analysis and collaborates
    with other agents for emergent strategy development.

    Capabilities:
    - Real-time market analysis
    - AI-powered signal generation
    - Multi-agent strategy collaboration
    - Technical indicator analysis
    - Sentiment analysis integration
    - Pattern recognition
    """

    def __init__(
        self, agent_id: str, message_bus, shared_memory, consensus_manager, config_dict=None
    ):
        """Initialize Autonomous Strategy Agent"""
        super().__init__(agent_id, message_bus, shared_memory, consensus_manager, config_dict)

        # Initialize AI model
        self.model = ModelFactory.create_model("anthropic")

        # Strategy parameters
        self.monitored_tokens = config.MONITORED_TOKENS
        self.analysis_interval = 60  # Analyze every 60 seconds
        self.signal_threshold = 0.6  # Minimum confidence for signals

        # Strategy state
        self.active_analyses = {}
        self.signal_history = []
        self.strategy_patterns = {}

        # Performance tracking
        self.analyses_performed = 0
        self.signals_generated = 0
        self.correct_signals = 0
        self.collaboration_sessions = 0

        print(f"[{self.agent_id}] 🧠 Autonomous Strategy Agent initialized")
        print(f"[{self.agent_id}] 📊 Monitoring {len(self.monitored_tokens)} tokens")

    def on_start(self):
        """Initialize agent when started"""
        print(f"[{self.agent_id}] 🚀 Starting autonomous strategy generation...")

        # Register capabilities
        self.register_capability(
            capability_type="market_analysis",
            description="AI-powered market analysis and trading signal generation",
            input_types=["market_data", "price_data", "volume_data"],
            output_types=["trading_signal", "market_analysis", "strategy_recommendation"],
            cost_model={
                "analysis": 0.0005,
                "signal_generation": 0.001,
                "strategy_consultation": 0.002,
                "currency": "SOL",
            },
        )

        # Register MCP tools
        self.register_tool(
            tool_name="analyze_token",
            description="Perform comprehensive technical analysis on a token",
            parameters={
                "type": "object",
                "properties": {
                    "token": {"type": "string", "description": "Token address"},
                    "timeframe": {"type": "string", "description": "Analysis timeframe"},
                    "include_sentiment": {
                        "type": "boolean",
                        "description": "Include sentiment analysis",
                    },
                },
                "required": ["token"],
            },
            cost=0.0005,
        )

        self.register_tool(
            tool_name="generate_signal",
            description="Generate trading signal for a token",
            parameters={
                "type": "object",
                "properties": {
                    "token": {"type": "string", "description": "Token address"},
                    "analysis_type": {
                        "type": "string",
                        "enum": ["technical", "sentiment", "combined"],
                    },
                },
                "required": ["token"],
            },
            cost=0.001,
        )

        self.register_tool(
            tool_name="collaborate_strategy",
            description="Collaborate on strategy development with other agents",
            parameters={
                "type": "object",
                "properties": {
                    "strategy_type": {"type": "string", "description": "Type of strategy"},
                    "market_conditions": {
                        "type": "object",
                        "description": "Current market conditions",
                    },
                },
                "required": ["strategy_type"],
            },
            cost=0.002,
        )

        # Subscribe to events
        self.subscribe("market.price_update", self._handle_price_update)
        self.subscribe("market.volume_spike", self._handle_volume_spike)
        self.subscribe("sentiment.update", self._handle_sentiment_update)
        self.subscribe("agent.strategy_agent.*", self._handle_direct_message)

        # Register with monitoring dashboard
        register_agent(self.agent_id, self.get_stats())

        print(f"[{self.agent_id}] ✅ Strategy generation active!")

    def _handle_price_update(self, message):
        """Handle market price updates"""
        token = message.data.get("token")
        price = message.data.get("price")
        volume = message.data.get("volume", 0)

        # Update cached data
        self.set_memory(f"price:{token}", price, ttl=60)
        self.set_memory(f"volume:{token}", volume, ttl=60)

        # Check if analysis needed
        if self._should_analyze(token):
            self._analyze_token(token)

    def _handle_volume_spike(self, message):
        """Handle volume spike events"""
        token = message.data.get("token")
        volume_increase = message.data.get("volume_increase_pct", 0)

        print(
            f"[{self.agent_id}] 📊 Volume spike detected: {token[:8]}... (+{volume_increase:.1f}%)"
        )

        # Immediate analysis on volume spikes
        self._analyze_token(token, priority="high")

    def _handle_sentiment_update(self, message):
        """Handle sentiment analysis updates"""
        token = message.data.get("token")
        sentiment = message.data.get("sentiment")  # positive, negative, neutral
        score = message.data.get("score", 0.5)

        # Store sentiment
        self.set_memory(f"sentiment:{token}", {"sentiment": sentiment, "score": score}, ttl=300)

        # Re-analyze if strong sentiment
        if abs(score - 0.5) > 0.3:
            self._analyze_token(token)

    def _handle_direct_message(self, message):
        """Handle direct messages"""
        action = message.data.get("action")

        if action == "analyze_token":
            token = message.data.get("token")
            analysis = self._analyze_token(token)

            self.send_a2a_message(
                receiver=message.sender,
                performative=A2APerformative.INFORM,
                content={"token": token, "analysis": analysis},
            )

        elif action == "generate_signal":
            token = message.data.get("token")
            signal = self._generate_trading_signal(token)

            self.send_a2a_message(
                receiver=message.sender,
                performative=A2APerformative.INFORM,
                content={"token": token, "signal": signal},
            )

        elif action == "collaborate_strategy":
            strategy_type = message.data.get("strategy_type")
            self._collaborate_on_strategy(strategy_type, message.sender)

    def _should_analyze(self, token: str) -> bool:
        """Determine if token should be analyzed"""
        last_analysis = self.active_analyses.get(token, 0)
        return (time.time() - last_analysis) > self.analysis_interval

    def _analyze_token(self, token: str, priority: str = "normal") -> Dict[str, Any]:
        """Perform comprehensive token analysis"""
        self.analyses_performed += 1
        self.active_analyses[token] = time.time()

        try:
            print(f"[{self.agent_id}] 🔍 Analyzing {token[:8]}...")

            # Get current data
            price = self.get_memory(f"price:{token}", default=0)
            volume = self.get_memory(f"volume:{token}", default=0)
            sentiment_data = self.get_memory(f"sentiment:{token}", default={})

            # Calculate technical indicators
            indicators = self._calculate_indicators(token, price)

            # Determine trend
            trend = self._determine_trend(indicators)

            # Calculate strength
            strength = self._calculate_strength(indicators, sentiment_data)

            # Generate analysis
            analysis = {
                "token": token,
                "price": price,
                "volume": volume,
                "trend": trend,
                "strength": strength,
                "indicators": indicators,
                "sentiment": sentiment_data.get("sentiment", "neutral"),
                "timestamp": datetime.now().isoformat(),
            }

            # Store analysis
            self.set_memory(f"analysis:{token}", analysis, ttl=120)

            # Generate signal if strong trend
            if strength > self.signal_threshold:
                self._generate_trading_signal(token, analysis)

            return analysis

        except Exception as e:
            print(f"[{self.agent_id}] ⚠️ Analysis error: {e}")
            return {"error": str(e)}

    def _calculate_indicators(self, token: str, current_price: float) -> Dict[str, Any]:
        """Calculate technical indicators"""
        # Simplified indicators for demo
        # In production, would use pandas_ta or talib

        indicators = {}

        try:
            # Get price history
            price_history = self.get_memory(f"price_history:{token}", default=[])

            if len(price_history) > 0:
                prices = [p for p in price_history[-20:]]  # Last 20 prices

                # Simple moving average
                sma_20 = sum(prices) / len(prices) if prices else current_price

                # Momentum
                if len(prices) >= 10:
                    momentum = ((prices[-1] - prices[-10]) / prices[-10]) * 100
                else:
                    momentum = 0

                indicators = {
                    "sma_20": sma_20,
                    "momentum": momentum,
                    "above_sma": current_price > sma_20,
                    "price_change_pct": (
                        ((current_price - prices[0]) / prices[0] * 100) if prices else 0
                    ),
                }

            return indicators

        except Exception as e:
            print(f"[{self.agent_id}] ⚠️ Indicator calculation error: {e}")
            return {}

    def _determine_trend(self, indicators: Dict[str, Any]) -> str:
        """Determine market trend"""
        if not indicators:
            return "neutral"

        above_sma = indicators.get("above_sma", False)
        momentum = indicators.get("momentum", 0)

        if above_sma and momentum > 2:
            return "bullish"
        elif not above_sma and momentum < -2:
            return "bearish"
        else:
            return "neutral"

    def _calculate_strength(
        self, indicators: Dict[str, Any], sentiment_data: Dict[str, Any]
    ) -> float:
        """Calculate signal strength (0.0 - 1.0)"""
        strength = 0.5  # Start neutral

        # Technical strength (60% weight)
        if indicators:
            momentum = indicators.get("momentum", 0)
            strength += (momentum / 10) * 0.6  # Normalize momentum contribution

        # Sentiment strength (40% weight)
        if sentiment_data:
            sentiment_score = sentiment_data.get("score", 0.5)
            strength += (sentiment_score - 0.5) * 0.4

        return max(0.0, min(1.0, strength))

    def _generate_trading_signal(
        self, token: str, analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate trading signal"""
        if analysis is None:
            analysis = self.get_memory(f"analysis:{token}", default={})

        if not analysis:
            return {"action": "HOLD", "confidence": 0.0}

        trend = analysis.get("trend", "neutral")
        strength = analysis.get("strength", 0.5)

        # Determine action
        if trend == "bullish" and strength > self.signal_threshold:
            action = "BUY"
        elif trend == "bearish" and strength > self.signal_threshold:
            action = "SELL"
        else:
            action = "HOLD"

        signal = {
            "token": token,
            "action": action,
            "confidence": strength,
            "trend": trend,
            "reasoning": f"{trend.capitalize()} trend with {strength:.2f} confidence",
            "timestamp": datetime.now().isoformat(),
        }

        # Store signal
        self.signal_history.append(signal)
        if len(self.signal_history) > 100:
            self.signal_history = self.signal_history[-100:]

        # Broadcast signal if actionable
        if action in ["BUY", "SELL"]:
            self.signals_generated += 1

            print(
                f"[{self.agent_id}] 📡 Signal: {action} {token[:8]}... (confidence: {strength:.2f})"
            )

            self.broadcast(
                "market.signal",
                {
                    "token": token,
                    "action": action,
                    "confidence": strength,
                    "reasoning": signal["reasoning"],
                },
                priority=MessagePriority.HIGH if strength > 0.8 else MessagePriority.NORMAL,
            )

        return signal

    def _collaborate_on_strategy(self, strategy_type: str, requester: str):
        """Collaborate on strategy development"""
        self.collaboration_sessions += 1

        print(f"[{self.agent_id}] 🤝 Strategy collaboration with {requester}: {strategy_type}")

        # Propose strategy discussion
        proposal_id = self.propose_consensus(
            action="develop_strategy",
            data={
                "strategy_type": strategy_type,
                "requester": requester,
                "market_conditions": self._get_market_summary(),
            },
            min_votes=2,
            threshold=0.6,
            timeout_seconds=30,
        )

        print(f"[{self.agent_id}] 📋 Strategy collaboration proposal: {proposal_id[:8]}...")

    def _get_market_summary(self) -> Dict[str, Any]:
        """Get current market conditions summary"""
        try:
            # Aggregate recent analyses
            bullish_count = 0
            bearish_count = 0
            neutral_count = 0

            for token in self.monitored_tokens[:5]:  # Sample 5 tokens
                analysis = self.get_memory(f"analysis:{token}", default={})
                trend = analysis.get("trend", "neutral")

                if trend == "bullish":
                    bullish_count += 1
                elif trend == "bearish":
                    bearish_count += 1
                else:
                    neutral_count += 1

            total = bullish_count + bearish_count + neutral_count
            if total == 0:
                return {"overall_sentiment": "unknown"}

            return {
                "overall_sentiment": (
                    "bullish"
                    if bullish_count > bearish_count
                    else "bearish" if bearish_count > bullish_count else "neutral"
                ),
                "bullish_pct": (bullish_count / total) * 100,
                "bearish_pct": (bearish_count / total) * 100,
                "neutral_pct": (neutral_count / total) * 100,
            }

        except:
            return {"overall_sentiment": "unknown"}

    def _on_vote_request(self, proposal_data: Dict[str, Any]):
        """Vote on consensus proposals"""
        action = proposal_data.get("action")
        proposal_id = proposal_data.get("proposal_id")

        # Vote on strategy development
        if action == "develop_strategy":
            # Always support strategy collaboration
            self.vote(
                proposal_id=proposal_id,
                approve=True,
                confidence=0.8,
                reasoning="Strategy collaboration benefits all agents",
            )

        # Vote on trade decisions based on analysis
        elif action == "close_position":
            token = proposal_data["data"].get("token")
            analysis = self.get_memory(f"analysis:{token}", default={})

            trend = analysis.get("trend", "neutral")
            strength = analysis.get("strength", 0.5)

            # Approve closes in bearish trends
            approve = trend == "bearish" or strength < 0.4

            self.vote(
                proposal_id=proposal_id,
                approve=approve,
                confidence=strength if approve else 1.0 - strength,
                reasoning=f"Analysis shows {trend} trend",
            )

    def _on_proposal_approved(self, decision_data: Dict[str, Any]):
        """Handle approved proposals"""
        action = decision_data.get("action")

        if action == "develop_strategy":
            if decision_data.get("proposer") == self.agent_id:
                print(f"[{self.agent_id}] ✅ Strategy collaboration APPROVED")
                # Would implement actual strategy development here

    def _periodic_task(self):
        """Periodic autonomous behavior"""
        # Throttle to every 20 seconds
        if not hasattr(self, "_last_periodic"):
            self._last_periodic = time.time()
            self._analysis_cycle = 0

        if time.time() - self._last_periodic < 20:
            return

        self._last_periodic = time.time()
        self._analysis_cycle += 1

        # Analyze tokens on rotation
        if len(self.monitored_tokens) > 0:
            token_index = self._analysis_cycle % len(self.monitored_tokens)
            token = self.monitored_tokens[token_index]

            # Simulate price update for demo
            current_price = self.get_memory(f"price:{token}", default=100.0)
            # Add some randomness
            new_price = current_price * (1 + random.uniform(-0.02, 0.02))

            # Update price
            self.set_memory(f"price:{token}", new_price, ttl=60)

            # Update price history
            price_history = self.get_memory(f"price_history:{token}", default=[])
            price_history.append(new_price)
            if len(price_history) > 100:
                price_history = price_history[-100:]
            self.set_memory(f"price_history:{token}", price_history, ttl=600)

            # Broadcast price update
            self.broadcast(
                "market_price_update",
                {
                    "token": token,
                    "price": new_price,
                    "volume": random.randint(500000, 2000000),
                    "timestamp": time.time(),
                },
            )

            # Analyze
            self._analyze_token(token)

        # Update monitoring dashboard
        register_agent(
            self.agent_id,
            {
                **self.get_stats(),
                "analyses_performed": self.analyses_performed,
                "signals_generated": self.signals_generated,
                "collaboration_sessions": self.collaboration_sessions,
                "signal_accuracy": (
                    (self.correct_signals / self.signals_generated * 100)
                    if self.signals_generated > 0
                    else 0
                ),
            },
        )

    def on_stop(self):
        """Cleanup when agent stops"""
        print(f"[{self.agent_id}] 🛑 Stopping strategy agent...")

        # Store final state
        self.set_memory("strategy:final_signals", len(self.signal_history), ttl=86400)

        # Publish event
        self.publish_event(
            "agent_stopped",
            {
                "analyses_performed": self.analyses_performed,
                "signals_generated": self.signals_generated,
            },
        )


def main():
    """Run Autonomous Strategy Agent standalone"""
    print("=" * 70)
    print("🧠 AUTONOMOUS STRATEGY AGENT")
    print("=" * 70)

    # Initialize infrastructure
    print("\nInitializing autonomous infrastructure...")
    bus = get_message_bus(use_redis=False)
    memory = get_shared_memory(use_redis=False)
    consensus = ConsensusManager(bus, memory)

    # Create agent
    print("Creating Autonomous Strategy Agent...")
    agent = AutonomousStrategyAgent(
        agent_id="autonomous_strategy_agent",
        message_bus=bus,
        shared_memory=memory,
        consensus_manager=consensus,
    )

    # Start agent
    print("Starting agent...")
    agent.start()

    print("\n" + "=" * 70)
    print("AUTONOMOUS STRATEGY AGENT RUNNING")
    print("=" * 70)
    print("\nPress Ctrl+C to stop...")

    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\nStopping agent...")
        agent.stop()
        bus.stop()

        print("\n" + "=" * 70)
        print("AGENT STOPPED")
        print("=" * 70)


if __name__ == "__main__":
    main()
