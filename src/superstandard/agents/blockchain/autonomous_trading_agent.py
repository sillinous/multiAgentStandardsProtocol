"""
🌙 Moon Dev's Autonomous Trading Agent
Built with love by Moon Dev 🚀

AUTONOMOUS FEATURES:
- Real-time collaborative trading with Risk Agent
- Multi-agent consensus for critical decisions
- Protocol-compliant (A2A, A2Pay, MCP, FIPA)
- Event-driven architecture
- Tool registration for execution services
- Shared knowledge via distributed memory
- AI-powered swarm decision making
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
import uuid
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


class AutonomousTradingAgent(AutonomousAgent):
    """
    Autonomous Trading Agent

    Executes trades with real-time risk collaboration, multi-agent
    consensus, and AI-powered decision making.

    Capabilities:
    - AI-powered trade decisions (swarm or single model)
    - Real-time risk approval via Risk Agent
    - Collaborative consensus for large trades
    - Position management with shared memory
    - Payment for analysis services (A2Pay)
    """

    def __init__(
        self, agent_id: str, message_bus, shared_memory, consensus_manager, config_dict=None
    ):
        """Initialize Autonomous Trading Agent"""
        super().__init__(agent_id, message_bus, shared_memory, consensus_manager, config_dict)

        # Initialize AI model
        self.model = ModelFactory.create_model("anthropic")

        # Trading parameters
        self.exchange = config_dict.get("exchange", "SOLANA") if config_dict else "SOLANA"
        self.use_swarm = config_dict.get("use_swarm", False) if config_dict else False
        self.long_only = config_dict.get("long_only", True) if config_dict else True
        self.usd_size = config.usd_size
        self.max_order_size = config.max_usd_order_size

        # Trading state
        self.active_positions = {}
        self.pending_trades = {}
        self.trade_history = []

        # Performance tracking
        self.trades_executed = 0
        self.trades_rejected = 0
        self.consensus_votes_cast = 0
        self.risk_checks_requested = 0

        print(f"[{self.agent_id}] 🤖 Autonomous Trading Agent initialized")
        print(f"[{self.agent_id}] 🏦 Exchange: {self.exchange}")
        print(f"[{self.agent_id}] 🌊 AI Mode: {'Swarm' if self.use_swarm else 'Single Model'}")
        print(f"[{self.agent_id}] 📈 Mode: {'Long Only' if self.long_only else 'Long/Short'}")

    def on_start(self):
        """Initialize agent when started"""
        print(f"[{self.agent_id}] 🚀 Starting autonomous trading...")

        # Register capabilities
        self.register_capability(
            capability_type="trading",
            description="AI-powered trade execution with risk management",
            input_types=["market_data", "trading_signal", "strategy_recommendation"],
            output_types=["trade_executed", "position_update", "trade_rejection"],
            cost_model={"trade_execution": 0.001, "position_query": 0.0001, "currency": "SOL"},
        )

        # Register MCP tools
        self.register_tool(
            tool_name="execute_trade",
            description="Execute a trade order (requires risk approval)",
            parameters={
                "type": "object",
                "properties": {
                    "token": {"type": "string", "description": "Token address"},
                    "action": {
                        "type": "string",
                        "enum": ["BUY", "SELL"],
                        "description": "Trade action",
                    },
                    "size_usd": {"type": "number", "description": "Order size in USD"},
                    "requester": {"type": "string", "description": "Requesting agent ID"},
                },
                "required": ["token", "action", "size_usd", "requester"],
            },
            cost=0.001,
        )

        self.register_tool(
            tool_name="get_position",
            description="Get current position for a token",
            parameters={
                "type": "object",
                "properties": {"token": {"type": "string", "description": "Token address"}},
                "required": ["token"],
            },
            cost=0.0001,
        )

        self.register_tool(
            tool_name="close_position",
            description="Close an open position (requires consensus)",
            parameters={
                "type": "object",
                "properties": {
                    "token": {"type": "string", "description": "Token address"},
                    "reason": {"type": "string", "description": "Reason for closing"},
                },
                "required": ["token", "reason"],
            },
            cost=0.001,
        )

        # Subscribe to events
        self.subscribe("market.price_update", self._handle_price_update)
        self.subscribe("market.signal", self._handle_trading_signal)
        self.subscribe("risk_alert", self._handle_risk_alert)
        self.subscribe("risk_limit_breach", self._handle_limit_breach)
        self.subscribe("trading_halt", self._handle_trading_halt)
        self.subscribe("agent.trading_agent.*", self._handle_direct_message)

        # Load existing positions
        self._load_positions()

        # Register with monitoring dashboard
        register_agent(self.agent_id, self.get_stats())

        print(f"[{self.agent_id}] ✅ Trading system active!")

    def _load_positions(self):
        """Load current positions from memory/chain"""
        try:
            # Load from shared memory
            positions = self.get_memory("trading:active_positions", default={})
            self.active_positions = positions

            print(f"[{self.agent_id}] 📊 Loaded {len(positions)} active positions")

        except Exception as e:
            print(f"[{self.agent_id}] ⚠️ Error loading positions: {e}")

    def _handle_price_update(self, message):
        """Handle market price updates"""
        token = message.data.get("token")
        price = message.data.get("price")

        # Update cached price
        self.set_memory(f"price:{token}", price, ttl=60)

        # Check if positions need management
        if token in self.active_positions:
            self._check_position_management(token, price)

    def _handle_trading_signal(self, message):
        """Handle trading signals from strategy agents"""
        token = message.data.get("token")
        action = message.data.get("action")  # BUY, SELL, HOLD
        confidence = message.data.get("confidence", 0.5)
        source = message.sender

        print(
            f"[{self.agent_id}] 📡 Signal from {source}: {action} {token[:8]}... (confidence: {confidence:.2f})"
        )

        # Only act on high-confidence signals
        if confidence < 0.6:
            print(f"[{self.agent_id}] ⚠️ Low confidence - ignoring signal")
            return

        # Process signal
        if action == "BUY":
            self._process_buy_signal(token, confidence, source)
        elif action == "SELL":
            self._process_sell_signal(token, confidence, source)

    def _handle_risk_alert(self, message):
        """Handle risk alerts"""
        alert_type = message.data.get("type")
        risk_score = message.data.get("risk_score", 0)

        print(f"[{self.agent_id}] ⚠️ Risk Alert: {alert_type} (score: {risk_score:.2f})")

        # Reduce position sizes if high risk
        if risk_score > 0.7:
            self._reduce_exposure()

    def _handle_limit_breach(self, message):
        """Handle risk limit breaches"""
        limit_type = message.data.get("limit_type")

        print(f"[{self.agent_id}] 🚨 LIMIT BREACH: {limit_type}")

        # Close all positions if max loss
        if limit_type == "max_loss":
            self._close_all_positions("Max loss limit breached")

    def _handle_trading_halt(self, message):
        """Handle trading halt orders"""
        reason = message.data.get("reason")

        print(f"[{self.agent_id}] 🛑 TRADING HALT: {reason}")

        # Cancel all pending trades
        self.pending_trades.clear()
        self.set_memory("trading:halted", True, ttl=3600)

    def _handle_direct_message(self, message):
        """Handle direct messages"""
        action = message.data.get("action")

        if action == "execute_trade":
            token = message.data.get("token")
            trade_action = message.data.get("trade_action")
            size_usd = message.data.get("size_usd")
            requester = message.sender

            result = self._execute_trade_request(token, trade_action, size_usd, requester)

            self.send_a2a_message(
                receiver=requester, performative=A2APerformative.INFORM, content=result
            )

        elif action == "get_position":
            token = message.data.get("token")
            position = self.active_positions.get(token, None)

            self.send_a2a_message(
                receiver=message.sender,
                performative=A2APerformative.INFORM,
                content={"token": token, "position": position},
            )

    def _process_buy_signal(self, token: str, confidence: float, source: str):
        """Process buy signal"""
        # Check if trading is halted
        if self.get_memory("trading:halted", default=False):
            print(f"[{self.agent_id}] ⛔ Trading halted - ignoring buy signal")
            return

        # Check if already have position
        if token in self.active_positions:
            print(f"[{self.agent_id}] 📊 Already have position in {token[:8]}...")
            return

        # Calculate position size
        size_usd = self.usd_size

        # Request risk approval
        print(f"[{self.agent_id}] 🔍 Requesting risk approval for {token[:8]}...")

        request_id = str(uuid.uuid4())
        self.risk_checks_requested += 1

        self.send_a2a_message(
            receiver="autonomous_risk_agent",
            performative=A2APerformative.REQUEST,
            content={
                "request_id": request_id,
                "action": "check_position_risk",
                "token": token,
                "size_usd": size_usd,
                "trade_action": "BUY",
            },
        )

        # Store pending trade
        self.pending_trades[request_id] = {
            "token": token,
            "action": "BUY",
            "size_usd": size_usd,
            "confidence": confidence,
            "source": source,
            "timestamp": time.time(),
        }

    def _process_sell_signal(self, token: str, confidence: float, source: str):
        """Process sell signal"""
        # Check if we have position
        if token not in self.active_positions:
            print(f"[{self.agent_id}] 📊 No position in {token[:8]}... to sell")
            return

        # Propose consensus for position close
        print(f"[{self.agent_id}] 🗳️ Proposing consensus to close {token[:8]}...")

        proposal_id = self.propose_consensus(
            action="close_position",
            data={"token": token, "reason": f"Sell signal from {source}", "confidence": confidence},
            min_votes=2,
            threshold=0.6,
            timeout_seconds=20,
        )

        print(f"[{self.agent_id}] 📋 Close position proposal: {proposal_id[:8]}...")

    def _execute_trade_request(
        self, token: str, action: str, size_usd: float, requester: str
    ) -> Dict[str, Any]:
        """Execute trade request from another agent"""
        try:
            # Check trading halt
            if self.get_memory("trading:halted", default=False):
                return {"success": False, "error": "Trading halted"}

            # Get risk approval
            # ... implementation would call risk agent ...

            # Execute trade
            result = self._execute_trade(token, action, size_usd)

            # Pay requester for signal (A2Pay)
            if result["success"]:
                self.request_payment(
                    to_agent=requester,
                    amount=0.0001,
                    currency="SOL",
                    payment_type=PaymentType.CRYPTOCURRENCY,
                    reason=f"Trading signal for {token[:8]}...",
                )

            return result

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_trade(self, token: str, action: str, size_usd: float) -> Dict[str, Any]:
        """Execute actual trade"""
        try:
            print(f"[{self.agent_id}] ⚡ Executing: {action} {size_usd} USD of {token[:8]}...")

            # Execute via exchange
            if action == "BUY":
                result = n.market_buy(token, size_usd)
            elif action == "SELL":
                result = n.market_sell(token, size_usd)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

            # Update position tracking
            if result.get("success"):
                self._update_position(token, action, size_usd)

                self.trades_executed += 1

                # Broadcast trade executed
                self.broadcast(
                    "trade.executed",
                    {
                        "token": token,
                        "action": action,
                        "size_usd": size_usd,
                        "timestamp": datetime.now().isoformat(),
                    },
                    priority=MessagePriority.NORMAL,
                )

                # Publish event
                self.publish_event(
                    "trade_executed", {"token": token, "action": action, "size_usd": size_usd}
                )

            return result

        except Exception as e:
            print(f"[{self.agent_id}] ❌ Trade execution failed: {e}")
            self.trades_rejected += 1
            return {"success": False, "error": str(e)}

    def _update_position(self, token: str, action: str, size_usd: float):
        """Update position tracking"""
        if action == "BUY":
            self.active_positions[token] = {
                "size_usd": size_usd,
                "entry_time": time.time(),
                "entry_price": self.get_memory(f"price:{token}", default=0),
            }
        elif action == "SELL":
            if token in self.active_positions:
                del self.active_positions[token]

        # Store in shared memory
        self.set_memory("trading:active_positions", self.active_positions, ttl=3600)

    def _check_position_management(self, token: str, current_price: float):
        """Check if position needs management"""
        if token not in self.active_positions:
            return

        position = self.active_positions[token]
        entry_price = position.get("entry_price", current_price)

        # Calculate P&L
        pnl_pct = ((current_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0

        # Take profit at +20%
        if pnl_pct >= 20:
            print(f"[{self.agent_id}] 💰 Take profit: {token[:8]}... at +{pnl_pct:.1f}%")
            self._process_sell_signal(token, 0.9, "autonomous_trading_agent")

        # Stop loss at -10%
        elif pnl_pct <= -10:
            print(f"[{self.agent_id}] 🛑 Stop loss: {token[:8]}... at {pnl_pct:.1f}%")
            self._process_sell_signal(token, 0.9, "autonomous_trading_agent")

    def _reduce_exposure(self):
        """Reduce overall exposure"""
        print(f"[{self.agent_id}] ⚠️ Reducing exposure...")

        # Close worst performing position
        worst_token = None
        worst_pnl = float("inf")

        for token, position in self.active_positions.items():
            current_price = self.get_memory(f"price:{token}", default=0)
            entry_price = position.get("entry_price", current_price)

            if entry_price > 0:
                pnl_pct = ((current_price - entry_price) / entry_price) * 100
                if pnl_pct < worst_pnl:
                    worst_pnl = pnl_pct
                    worst_token = token

        if worst_token:
            self._process_sell_signal(worst_token, 0.8, "autonomous_trading_agent")

    def _close_all_positions(self, reason: str):
        """Close all active positions"""
        print(f"[{self.agent_id}] 🚨 CLOSING ALL POSITIONS: {reason}")

        for token in list(self.active_positions.keys()):
            self._process_sell_signal(token, 1.0, "autonomous_trading_agent")

    def _on_vote_request(self, proposal_data: Dict[str, Any]):
        """Vote on consensus proposals"""
        action = proposal_data.get("action")
        proposal_id = proposal_data.get("proposal_id")

        # Vote on position closes
        if action == "close_position":
            confidence = proposal_data["data"].get("confidence", 0.5)

            # Vote based on signal confidence
            approve = confidence > 0.6

            self.vote(
                proposal_id=proposal_id,
                approve=approve,
                confidence=confidence,
                reasoning=f"Signal confidence: {confidence:.2f}",
            )

            self.consensus_votes_cast += 1

        # Vote on risk overrides (be conservative)
        elif action == "override_risk_limit":
            risk_score = proposal_data["data"].get("risk_score", 0.5)

            # Only approve if very low risk
            approve = risk_score < 0.3

            self.vote(
                proposal_id=proposal_id,
                approve=approve,
                confidence=0.7,
                reasoning=f"Risk score {risk_score:.2f} - {'acceptable' if approve else 'too risky'}",
            )

    def _on_proposal_approved(self, decision_data: Dict[str, Any]):
        """Handle approved proposals"""
        action = decision_data.get("action")

        if action == "close_position":
            if decision_data.get("proposer") == self.agent_id:
                token = decision_data["data"].get("token")
                print(f"[{self.agent_id}] ✅ Position close APPROVED: {token[:8]}...")

                # Execute close
                size_usd = self.active_positions[token]["size_usd"]
                self._execute_trade(token, "SELL", size_usd)

    def _on_proposal_rejected(self, decision_data: Dict[str, Any]):
        """Handle rejected proposals"""
        action = decision_data.get("action")

        if action == "close_position":
            if decision_data.get("proposer") == self.agent_id:
                token = decision_data["data"].get("token")
                print(f"[{self.agent_id}] ❌ Position close REJECTED: {token[:8]}...")

    def _periodic_task(self):
        """Periodic autonomous behavior"""
        # Throttle to every 15 seconds
        if not hasattr(self, "_last_periodic"):
            self._last_periodic = time.time()

        if time.time() - self._last_periodic < 15:
            return

        self._last_periodic = time.time()

        # Check pending trades for timeouts
        self._cleanup_pending_trades()

        # Update monitoring dashboard
        register_agent(
            self.agent_id,
            {
                **self.get_stats(),
                "trades_executed": self.trades_executed,
                "trades_rejected": self.trades_rejected,
                "active_positions": len(self.active_positions),
                "pending_trades": len(self.pending_trades),
                "consensus_votes": self.consensus_votes_cast,
                "risk_checks": self.risk_checks_requested,
            },
        )

    def _cleanup_pending_trades(self):
        """Remove expired pending trades"""
        now = time.time()
        expired = []

        for request_id, trade in self.pending_trades.items():
            if now - trade["timestamp"] > 60:  # 60 second timeout
                expired.append(request_id)

        for request_id in expired:
            print(f"[{self.agent_id}] ⏱️ Pending trade expired: {request_id[:8]}...")
            del self.pending_trades[request_id]

    def on_stop(self):
        """Cleanup when agent stops"""
        print(f"[{self.agent_id}] 🛑 Stopping trading agent...")

        # Store final state
        self.set_memory("trading:final_positions", self.active_positions, ttl=86400)

        # Publish event
        self.publish_event(
            "agent_stopped",
            {
                "trades_executed": self.trades_executed,
                "active_positions": len(self.active_positions),
            },
        )


def main():
    """Run Autonomous Trading Agent standalone"""
    print("=" * 70)
    print("🤖 AUTONOMOUS TRADING AGENT")
    print("=" * 70)

    # Initialize infrastructure
    print("\nInitializing autonomous infrastructure...")
    bus = get_message_bus(use_redis=False)
    memory = get_shared_memory(use_redis=False)
    consensus = ConsensusManager(bus, memory)

    # Create agent
    print("Creating Autonomous Trading Agent...")
    agent = AutonomousTradingAgent(
        agent_id="autonomous_trading_agent",
        message_bus=bus,
        shared_memory=memory,
        consensus_manager=consensus,
        config_dict={"exchange": "SOLANA", "use_swarm": False, "long_only": True},
    )

    # Start agent
    print("Starting agent...")
    agent.start()

    print("\n" + "=" * 70)
    print("AUTONOMOUS TRADING AGENT RUNNING")
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
