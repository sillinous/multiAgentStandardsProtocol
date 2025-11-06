"""
🌙 Moon Dev's Autonomous Risk Management Agent
Built with love by Moon Dev 🚀

AUTONOMOUS FEATURES:
- Real-time risk monitoring (< 1 second response)
- Collaborative consensus-based limit overrides
- Protocol-compliant (A2A, A2Pay, MCP, FIPA)
- Event-driven architecture
- Tool registration for other agents
- Shared knowledge via distributed memory
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
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
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


class AutonomousRiskAgent(AutonomousAgent):
    """
    Autonomous Risk Management Agent

    Monitors portfolio risk in real-time and collaborates with other agents
    for critical risk decisions using consensus voting.

    Capabilities:
    - Real-time risk score calculation
    - Exposure monitoring
    - Position risk analysis
    - Collaborative limit override decisions
    - Risk alerts to other agents
    """

    def __init__(
        self, agent_id: str, message_bus, shared_memory, consensus_manager, config_dict=None
    ):
        """Initialize Autonomous Risk Agent"""
        super().__init__(agent_id, message_bus, shared_memory, consensus_manager, config_dict)

        # Initialize AI model
        self.model = ModelFactory.create_model("anthropic")

        # Risk parameters
        self.max_loss_usd = config.MAX_LOSS_USD
        self.max_gain_usd = config.MAX_GAIN_USD
        self.min_balance_usd = config.MINIMUM_BALANCE_USD
        self.max_position_pct = config.MAX_POSITION_PERCENTAGE
        self.cash_pct = config.CASH_PERCENTAGE

        # Risk state
        self.start_balance = 0.0
        self.current_balance = 0.0
        self.override_active = False
        self.last_risk_check = None

        # Performance tracking
        self.risk_checks_performed = 0
        self.alerts_sent = 0
        self.limits_breached = 0
        self.overrides_proposed = 0

        print(f"[{self.agent_id}] 🛡️ Autonomous Risk Agent initialized")

    def on_start(self):
        """Initialize agent when started"""
        print(f"[{self.agent_id}] 🚀 Starting autonomous risk monitoring...")

        # Register capabilities
        self.register_capability(
            capability_type="risk_management",
            description="Real-time portfolio risk monitoring and exposure management",
            input_types=["position_data", "market_data", "trade_request"],
            output_types=["risk_score", "risk_alert", "limit_override_decision"],
            cost_model={"risk_check": 0.0001, "limit_override_analysis": 0.001, "currency": "SOL"},
        )

        # Register MCP tools for other agents
        self.register_tool(
            tool_name="calculate_risk_score",
            description="Calculate current portfolio risk score (0.0-1.0)",
            parameters={
                "type": "object",
                "properties": {
                    "include_pending": {
                        "type": "boolean",
                        "description": "Include pending trades in calculation",
                    }
                },
            },
            cost=0.0001,
        )

        self.register_tool(
            tool_name="check_position_risk",
            description="Check risk for a specific position or proposed trade",
            parameters={
                "type": "object",
                "properties": {
                    "token": {"type": "string", "description": "Token address"},
                    "size_usd": {"type": "number", "description": "Position size in USD"},
                    "action": {
                        "type": "string",
                        "enum": ["BUY", "SELL"],
                        "description": "Trade action",
                    },
                },
                "required": ["token", "size_usd", "action"],
            },
            cost=0.0001,
        )

        self.register_tool(
            tool_name="request_limit_override",
            description="Request consensus vote for risk limit override",
            parameters={
                "type": "object",
                "properties": {
                    "limit_type": {
                        "type": "string",
                        "enum": ["max_loss", "max_gain", "min_balance"],
                    },
                    "reason": {"type": "string", "description": "Justification for override"},
                },
                "required": ["limit_type", "reason"],
            },
            cost=0.001,
        )

        # Subscribe to events
        self.subscribe("market.price_update", self._handle_price_update)
        self.subscribe("trade.request", self._handle_trade_request)
        self.subscribe("trade.executed", self._handle_trade_executed)
        self.subscribe("agent.risk_agent.*", self._handle_direct_message)

        # Initialize portfolio state
        self._initialize_portfolio()

        # Register with monitoring dashboard
        register_agent(self.agent_id, self.get_stats())

        print(f"[{self.agent_id}] ✅ Risk monitoring active!")
        print(f"[{self.agent_id}] 📊 Start Balance: ${self.start_balance:.2f}")
        print(f"[{self.agent_id}] 🛡️ Max Loss: ${self.max_loss_usd:.2f}")
        print(f"[{self.agent_id}] 🎯 Max Gain: ${self.max_gain_usd:.2f}")

    def _initialize_portfolio(self):
        """Initialize portfolio balance and state"""
        try:
            # Get current portfolio value
            self.start_balance = self._calculate_portfolio_value()
            self.current_balance = self.start_balance

            # Store in shared memory
            self.set_memory("portfolio:start_balance", self.start_balance, ttl=86400)
            self.set_memory("portfolio:current_balance", self.current_balance, ttl=300)

            # Publish event
            self.publish_event(
                "portfolio_initialized",
                {"start_balance": self.start_balance, "timestamp": datetime.now().isoformat()},
            )

        except Exception as e:
            print(f"[{self.agent_id}] ⚠️ Error initializing portfolio: {e}")
            self.start_balance = 10000.0  # Fallback
            self.current_balance = 10000.0

    def _calculate_portfolio_value(self) -> float:
        """Calculate total portfolio value"""
        try:
            total = 0.0

            # Get USDC balance
            usdc_value = n.get_token_balance_usd(config.USDC_ADDRESS)
            total += usdc_value

            # Get monitored token balances
            for token in config.MONITORED_TOKENS:
                if token != config.USDC_ADDRESS:
                    token_value = n.get_token_balance_usd(token)
                    total += token_value

            return total

        except Exception as e:
            print(f"[{self.agent_id}] ⚠️ Error calculating portfolio: {e}")
            # Return cached value
            return self.get_memory("portfolio:current_balance", default=10000.0)

    def _handle_price_update(self, message):
        """Handle market price updates"""
        token = message.data.get("token")
        price = message.data.get("price")

        # Update cached price
        self.set_memory(f"price:{token}", price, ttl=60)

        # Check if we need to update risk assessment
        if self._should_check_risk():
            self._perform_risk_check()

    def _handle_trade_request(self, message):
        """Handle trade requests from other agents"""
        token = message.data.get("token")
        action = message.data.get("action")
        size_usd = message.data.get("size_usd")
        requester = message.sender

        print(
            f"[{self.agent_id}] 📋 Trade request from {requester}: {action} {size_usd} USD of {token[:8]}..."
        )

        # Calculate risk for this trade
        risk_assessment = self._assess_trade_risk(token, action, size_usd)

        # Respond with assessment
        self.send_a2a_message(
            receiver=requester,
            performative=A2APerformative.INFORM,
            content={
                "request_id": message.data.get("request_id"),
                "approved": risk_assessment["approved"],
                "risk_score": risk_assessment["risk_score"],
                "reasoning": risk_assessment["reasoning"],
            },
        )

        # Alert if high risk
        if risk_assessment["risk_score"] > 0.7:
            self.broadcast(
                "risk_alert",
                {
                    "type": "high_risk_trade",
                    "token": token,
                    "risk_score": risk_assessment["risk_score"],
                    "reasoning": risk_assessment["reasoning"],
                },
                priority=MessagePriority.HIGH,
            )

            self.alerts_sent += 1

    def _handle_trade_executed(self, message):
        """Handle executed trade events"""
        # Update portfolio value
        self._update_portfolio_value()

        # Check limits
        self._check_limits()

    def _handle_direct_message(self, message):
        """Handle direct messages to risk agent"""
        action = message.data.get("action")

        if action == "calculate_risk_score":
            risk_score = self._calculate_risk_score()
            self.send_a2a_message(
                receiver=message.sender,
                performative=A2APerformative.INFORM,
                content={"risk_score": risk_score},
            )

        elif action == "check_position_risk":
            token = message.data.get("token")
            size_usd = message.data.get("size_usd")
            trade_action = message.data.get("trade_action")

            assessment = self._assess_trade_risk(token, trade_action, size_usd)

            self.send_a2a_message(
                receiver=message.sender, performative=A2APerformative.INFORM, content=assessment
            )

    def _assess_trade_risk(self, token: str, action: str, size_usd: float) -> Dict[str, Any]:
        """Assess risk for a proposed trade"""
        try:
            # Get current portfolio state
            current_balance = self._calculate_portfolio_value()

            # Calculate position size as percentage
            position_pct = (size_usd / current_balance) * 100 if current_balance > 0 else 0

            # Get current price and volatility
            price = self.get_memory(f"price:{token}", default=0)

            # Calculate risk score (0.0 - 1.0)
            risk_score = 0.0

            # Factor 1: Position size (0-40% of risk)
            if position_pct > self.max_position_pct:
                risk_score += 0.4
            else:
                risk_score += (position_pct / self.max_position_pct) * 0.4

            # Factor 2: Current exposure (0-30% of risk)
            total_exposure = self._calculate_total_exposure()
            risk_score += min(total_exposure, 1.0) * 0.3

            # Factor 3: Recent performance (0-30% of risk)
            pnl_pct = ((current_balance - self.start_balance) / self.start_balance) * 100
            if pnl_pct < -5:  # Down more than 5%
                risk_score += 0.3
            elif pnl_pct < 0:
                risk_score += 0.15

            # Approve if risk is acceptable
            approved = risk_score < 0.6

            reasoning = f"Position: {position_pct:.1f}% of portfolio, "
            reasoning += f"Total exposure: {total_exposure:.1%}, "
            reasoning += f"PnL: {pnl_pct:+.1f}%, "
            reasoning += f"Risk Score: {risk_score:.2f}"

            if not approved:
                reasoning += " - REJECTED: Risk too high"

            return {
                "approved": approved,
                "risk_score": risk_score,
                "position_pct": position_pct,
                "total_exposure": total_exposure,
                "reasoning": reasoning,
            }

        except Exception as e:
            print(f"[{self.agent_id}] ⚠️ Error assessing trade risk: {e}")
            return {
                "approved": False,
                "risk_score": 1.0,
                "reasoning": f"Error calculating risk: {str(e)}",
            }

    def _should_check_risk(self) -> bool:
        """Determine if risk check is needed"""
        if self.last_risk_check is None:
            return True

        # Check every 30 seconds
        return (time.time() - self.last_risk_check) > 30

    def _perform_risk_check(self):
        """Perform comprehensive risk assessment"""
        self.last_risk_check = time.time()
        self.risk_checks_performed += 1

        try:
            # Update portfolio value
            self._update_portfolio_value()

            # Calculate risk metrics
            risk_score = self._calculate_risk_score()
            exposure = self._calculate_total_exposure()

            # Store in memory
            self.set_memory("risk:current_score", risk_score, ttl=60)
            self.set_memory("risk:total_exposure", exposure, ttl=60)

            # Check limits
            self._check_limits()

            # Broadcast status
            if risk_score > 0.7:
                self.broadcast(
                    "risk_status_update",
                    {"risk_score": risk_score, "exposure": exposure, "level": "high"},
                    priority=MessagePriority.HIGH,
                )

        except Exception as e:
            print(f"[{self.agent_id}] ⚠️ Error in risk check: {e}")

    def _calculate_risk_score(self) -> float:
        """Calculate overall portfolio risk score (0.0 - 1.0)"""
        try:
            # Get current state
            current_balance = self._calculate_portfolio_value()
            pnl = current_balance - self.start_balance
            pnl_pct = (pnl / self.start_balance) * 100 if self.start_balance > 0 else 0

            # Calculate components
            exposure = self._calculate_total_exposure()
            drawdown = max(0, -pnl_pct) / 10  # 10% down = 1.0 risk

            # Weighted risk score
            risk_score = (exposure * 0.6) + (drawdown * 0.4)

            return min(risk_score, 1.0)

        except:
            return 0.5  # Default moderate risk

    def _calculate_total_exposure(self) -> float:
        """Calculate total portfolio exposure (0.0 - 1.0)"""
        try:
            current_balance = self._calculate_portfolio_value()
            usdc_balance = n.get_token_balance_usd(config.USDC_ADDRESS)

            if current_balance == 0:
                return 0.0

            exposed = current_balance - usdc_balance
            exposure = exposed / current_balance

            return max(0.0, min(1.0, exposure))

        except:
            return 0.5  # Default moderate exposure

    def _update_portfolio_value(self):
        """Update current portfolio value"""
        try:
            self.current_balance = self._calculate_portfolio_value()
            self.set_memory("portfolio:current_balance", self.current_balance, ttl=300)

        except Exception as e:
            print(f"[{self.agent_id}] ⚠️ Error updating portfolio: {e}")

    def _check_limits(self):
        """Check if any risk limits are breached"""
        current_balance = self.current_balance
        pnl = current_balance - self.start_balance

        # Check max loss
        if pnl <= -self.max_loss_usd:
            self._handle_limit_breach("max_loss", pnl)

        # Check max gain
        elif pnl >= self.max_gain_usd:
            self._handle_limit_breach("max_gain", pnl)

        # Check minimum balance
        if current_balance <= self.min_balance_usd:
            self._handle_limit_breach("min_balance", current_balance)

    def _handle_limit_breach(self, limit_type: str, value: float):
        """Handle risk limit breach"""
        self.limits_breached += 1

        print(f"[{self.agent_id}] 🚨 LIMIT BREACH: {limit_type} = {value:.2f}")

        # Broadcast critical alert
        self.broadcast(
            "risk_limit_breach",
            {"limit_type": limit_type, "value": value, "timestamp": datetime.now().isoformat()},
            priority=MessagePriority.CRITICAL,
        )

        # Propose consensus vote for override
        if not self.override_active:
            self._propose_limit_override(limit_type)

    def _propose_limit_override(self, limit_type: str):
        """Propose limit override via consensus"""
        self.overrides_proposed += 1

        print(f"[{self.agent_id}] 🗳️ Proposing limit override: {limit_type}")

        # Propose consensus
        proposal_id = self.propose_consensus(
            action="override_risk_limit",
            data={
                "limit_type": limit_type,
                "current_balance": self.current_balance,
                "start_balance": self.start_balance,
                "pnl": self.current_balance - self.start_balance,
                "risk_score": self._calculate_risk_score(),
            },
            min_votes=2,
            threshold=0.7,  # Need 70% approval
            timeout_seconds=30,
        )

        print(f"[{self.agent_id}] 📋 Override proposal: {proposal_id[:8]}...")

    def _on_vote_request(self, proposal_data: Dict[str, Any]):
        """Vote on consensus proposals"""
        action = proposal_data.get("action")
        proposal_id = proposal_data.get("proposal_id")

        # Vote on limit overrides
        if action == "override_risk_limit":
            limit_type = proposal_data["data"].get("limit_type")
            risk_score = proposal_data["data"].get("risk_score", 0.5)

            # Be conservative - only approve low risk overrides
            approve = risk_score < 0.5

            self.vote(
                proposal_id=proposal_id,
                approve=approve,
                confidence=0.8,
                reasoning=f"Risk score {risk_score:.2f} - {'acceptable' if approve else 'too high'}",
            )

    def _on_proposal_approved(self, decision_data: Dict[str, Any]):
        """Handle approved proposals"""
        action = decision_data.get("action")

        if action == "override_risk_limit":
            if decision_data.get("proposer") == self.agent_id:
                print(f"[{self.agent_id}] ✅ Override APPROVED by consensus")
                self.override_active = True

                # Store override state
                self.set_memory("risk:override_active", True, ttl=3600)

    def _on_proposal_rejected(self, decision_data: Dict[str, Any]):
        """Handle rejected proposals"""
        action = decision_data.get("action")

        if action == "override_risk_limit":
            if decision_data.get("proposer") == self.agent_id:
                print(f"[{self.agent_id}] ❌ Override REJECTED by consensus")

                # Halt trading
                self.broadcast(
                    "trading_halt",
                    {
                        "reason": "Risk limit breach - override rejected",
                        "timestamp": datetime.now().isoformat(),
                    },
                    priority=MessagePriority.CRITICAL,
                )

    def _periodic_task(self):
        """Periodic autonomous behavior"""
        # Throttle to every 10 seconds
        if not hasattr(self, "_last_periodic"):
            self._last_periodic = time.time()

        if time.time() - self._last_periodic < 10:
            return

        self._last_periodic = time.time()

        # Perform risk check
        if self._should_check_risk():
            self._perform_risk_check()

        # Update monitoring dashboard
        register_agent(
            self.agent_id,
            {
                **self.get_stats(),
                "risk_checks": self.risk_checks_performed,
                "alerts_sent": self.alerts_sent,
                "limits_breached": self.limits_breached,
                "overrides_proposed": self.overrides_proposed,
                "current_balance": self.current_balance,
                "risk_score": self._calculate_risk_score(),
            },
        )

    def on_stop(self):
        """Cleanup when agent stops"""
        print(f"[{self.agent_id}] 🛑 Stopping risk monitoring...")

        # Store final state
        self.set_memory("risk:final_balance", self.current_balance, ttl=86400)

        # Publish event
        self.publish_event(
            "agent_stopped",
            {
                "final_balance": self.current_balance,
                "risk_checks": self.risk_checks_performed,
                "alerts_sent": self.alerts_sent,
            },
        )


def main():
    """Run Autonomous Risk Agent standalone"""
    print("=" * 70)
    print("🛡️ AUTONOMOUS RISK AGENT")
    print("=" * 70)

    # Initialize infrastructure
    print("\nInitializing autonomous infrastructure...")
    bus = get_message_bus(use_redis=False)
    memory = get_shared_memory(use_redis=False)
    consensus = ConsensusManager(bus, memory)

    # Create agent
    print("Creating Autonomous Risk Agent...")
    agent = AutonomousRiskAgent(
        agent_id="autonomous_risk_agent",
        message_bus=bus,
        shared_memory=memory,
        consensus_manager=consensus,
    )

    # Start agent
    print("Starting agent...")
    agent.start()

    print("\n" + "=" * 70)
    print("AUTONOMOUS RISK AGENT RUNNING")
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
