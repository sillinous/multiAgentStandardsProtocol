"""
Position Sizing Algorithms

Dynamic position sizing strategies for optimal capital allocation.

Algorithms Included:
- Kelly Criterion - Optimal bet sizing based on edge and odds
- Risk Parity - Equal risk contribution across positions
- Volatility-Based - Size inversely proportional to volatility
- Fixed Fractional - Fixed percentage of capital
- Maximum Position Size - Hard limits for risk control
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from enum import Enum
import math


# ============================================================================
# Position Sizing Models
# ============================================================================

class PositionSizingMethod(str, Enum):
    """Position sizing methods"""
    KELLY = "kelly"
    RISK_PARITY = "risk_parity"
    VOLATILITY_BASED = "volatility_based"
    FIXED_FRACTIONAL = "fixed_fractional"
    EQUAL_WEIGHT = "equal_weight"


@dataclass
class PositionSize:
    """Recommended position size"""

    method: PositionSizingMethod
    recommended_shares: float
    recommended_dollars: float
    recommended_pct_portfolio: float

    # Rationale
    rationale: str
    risk_level: str  # "low", "moderate", "high"

    # Constraints applied
    max_position_applied: bool = False
    min_position_applied: bool = False

    # Metadata
    calculation_details: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'method': self.method.value,
            'recommended_shares': self.recommended_shares,
            'recommended_dollars': self.recommended_dollars,
            'recommended_pct_portfolio': self.recommended_pct_portfolio,
            'rationale': self.rationale,
            'risk_level': self.risk_level,
            'max_position_applied': self.max_position_applied,
            'min_position_applied': self.min_position_applied,
            'calculation_details': self.calculation_details or {}
        }


# ============================================================================
# Position Sizing Calculator
# ============================================================================

class PositionSizingCalculator:
    """
    Calculate optimal position sizes using various algorithms

    Example:
        calculator = PositionSizingCalculator(
            portfolio_value=100000,
            max_position_pct=0.10,  # 10% max per position
            max_risk_per_trade_pct=0.02  # 2% max risk per trade
        )

        # Kelly Criterion
        size = calculator.kelly_criterion(
            win_rate=0.55,
            avg_win=1.5,
            avg_loss=1.0,
            current_price=175.50
        )

        print(f"Buy {size.recommended_shares} shares")
        print(f"Rationale: {size.rationale}")
    """

    def __init__(
        self,
        portfolio_value: float,
        max_position_pct: float = 0.10,
        min_position_pct: float = 0.01,
        max_risk_per_trade_pct: float = 0.02
    ):
        """
        Initialize position sizing calculator

        Args:
            portfolio_value: Total portfolio value
            max_position_pct: Maximum position size as % of portfolio (e.g., 0.10 for 10%)
            min_position_pct: Minimum position size as % of portfolio (e.g., 0.01 for 1%)
            max_risk_per_trade_pct: Maximum risk per trade as % (e.g., 0.02 for 2%)
        """
        self.portfolio_value = portfolio_value
        self.max_position_pct = max_position_pct
        self.min_position_pct = min_position_pct
        self.max_risk_per_trade_pct = max_risk_per_trade_pct

    def kelly_criterion(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        current_price: float
    ) -> PositionSize:
        """
        Calculate position size using Kelly Criterion

        Kelly % = (Win Rate * Avg Win - Loss Rate * Avg Loss) / Avg Win

        Args:
            win_rate: Historical win rate (0 to 1, e.g., 0.55 for 55%)
            avg_win: Average win percentage (e.g., 1.5 for 1.5%)
            avg_loss: Average loss percentage (e.g., 1.0 for 1.0%)
            current_price: Current price per share

        Returns:
            PositionSize with Kelly-optimal sizing
        """
        # Ensure valid inputs
        win_rate = max(0.0, min(1.0, win_rate))
        loss_rate = 1.0 - win_rate

        # Kelly formula
        if avg_win <= 0:
            kelly_pct = 0.0
        else:
            kelly_pct = (win_rate * avg_win - loss_rate * avg_loss) / avg_win

        # Kelly can be aggressive, use fractional Kelly (50%)
        fractional_kelly = kelly_pct * 0.5

        # Ensure positive
        fractional_kelly = max(0.0, fractional_kelly)

        # Apply max position constraint
        constrained_pct = min(fractional_kelly, self.max_position_pct)
        max_applied = constrained_pct < fractional_kelly

        # Apply min position constraint
        if constrained_pct < self.min_position_pct and fractional_kelly > 0:
            constrained_pct = self.min_position_pct
            min_applied = True
        else:
            min_applied = False

        # Calculate shares
        position_dollars = self.portfolio_value * constrained_pct
        shares = position_dollars / current_price if current_price > 0 else 0

        # Determine risk level
        if constrained_pct < 0.03:
            risk = "low"
        elif constrained_pct < 0.07:
            risk = "moderate"
        else:
            risk = "high"

        # Rationale
        rationale = f"Kelly Criterion: {fractional_kelly * 100:.1f}% of portfolio (fractional Kelly at 50%). "
        if max_applied:
            rationale += f"Capped at {self.max_position_pct * 100:.1f}% max position."

        return PositionSize(
            method=PositionSizingMethod.KELLY,
            recommended_shares=shares,
            recommended_dollars=position_dollars,
            recommended_pct_portfolio=constrained_pct,
            rationale=rationale,
            risk_level=risk,
            max_position_applied=max_applied,
            min_position_applied=min_applied,
            calculation_details={
                'kelly_pct': kelly_pct,
                'fractional_kelly': fractional_kelly,
                'win_rate': win_rate,
                'avg_win': avg_win,
                'avg_loss': avg_loss
            }
        )

    def risk_parity(
        self,
        current_price: float,
        volatility: float,
        num_positions: int
    ) -> PositionSize:
        """
        Calculate position size using Risk Parity

        Each position contributes equal risk to the portfolio.

        Args:
            current_price: Current price per share
            volatility: Annualized volatility (e.g., 0.25 for 25%)
            num_positions: Number of positions in portfolio

        Returns:
            PositionSize with risk parity sizing
        """
        if num_positions <= 0 or volatility <= 0:
            return self._zero_position("risk_parity")

        # Target risk per position (equal risk contribution)
        target_risk_pct = 1.0 / num_positions

        # Position size = Target Risk / Volatility
        position_pct = target_risk_pct / volatility

        # Apply constraints
        constrained_pct = min(position_pct, self.max_position_pct)
        constrained_pct = max(constrained_pct, self.min_position_pct)

        max_applied = constrained_pct < position_pct
        min_applied = constrained_pct > position_pct

        # Calculate shares
        position_dollars = self.portfolio_value * constrained_pct
        shares = position_dollars / current_price if current_price > 0 else 0

        # Risk level
        risk = "moderate"  # Risk parity aims for balanced risk

        rationale = f"Risk Parity: {constrained_pct * 100:.1f}% for equal risk contribution across {num_positions} positions."

        return PositionSize(
            method=PositionSizingMethod.RISK_PARITY,
            recommended_shares=shares,
            recommended_dollars=position_dollars,
            recommended_pct_portfolio=constrained_pct,
            rationale=rationale,
            risk_level=risk,
            max_position_applied=max_applied,
            min_position_applied=min_applied,
            calculation_details={
                'volatility': volatility,
                'num_positions': num_positions,
                'target_risk_pct': target_risk_pct
            }
        )

    def volatility_based(
        self,
        current_price: float,
        volatility: float,
        target_portfolio_volatility: float = 0.15
    ) -> PositionSize:
        """
        Calculate position size based on volatility

        Size inversely proportional to volatility.

        Args:
            current_price: Current price per share
            volatility: Annualized volatility (e.g., 0.25 for 25%)
            target_portfolio_volatility: Target portfolio volatility (e.g., 0.15 for 15%)

        Returns:
            PositionSize with volatility-based sizing
        """
        if volatility <= 0:
            return self._zero_position("volatility_based")

        # Position size inversely proportional to volatility
        position_pct = target_portfolio_volatility / volatility

        # Apply constraints
        constrained_pct = min(position_pct, self.max_position_pct)
        constrained_pct = max(constrained_pct, self.min_position_pct)

        max_applied = constrained_pct < position_pct
        min_applied = constrained_pct > position_pct

        # Calculate shares
        position_dollars = self.portfolio_value * constrained_pct
        shares = position_dollars / current_price if current_price > 0 else 0

        # Risk level based on volatility
        if volatility < 0.15:
            risk = "low"
        elif volatility < 0.30:
            risk = "moderate"
        else:
            risk = "high"

        rationale = f"Volatility-Based: {constrained_pct * 100:.1f}% (inversely proportional to {volatility * 100:.1f}% volatility)."

        return PositionSize(
            method=PositionSizingMethod.VOLATILITY_BASED,
            recommended_shares=shares,
            recommended_dollars=position_dollars,
            recommended_pct_portfolio=constrained_pct,
            rationale=rationale,
            risk_level=risk,
            max_position_applied=max_applied,
            min_position_applied=min_applied,
            calculation_details={
                'volatility': volatility,
                'target_portfolio_volatility': target_portfolio_volatility
            }
        )

    def fixed_fractional(
        self,
        current_price: float,
        fraction: float = 0.05
    ) -> PositionSize:
        """
        Calculate position size as fixed fraction of portfolio

        Args:
            current_price: Current price per share
            fraction: Fixed fraction of portfolio (e.g., 0.05 for 5%)

        Returns:
            PositionSize with fixed fractional sizing
        """
        # Apply constraints
        constrained_pct = min(fraction, self.max_position_pct)
        constrained_pct = max(constrained_pct, self.min_position_pct)

        max_applied = constrained_pct < fraction
        min_applied = constrained_pct > fraction

        # Calculate shares
        position_dollars = self.portfolio_value * constrained_pct
        shares = position_dollars / current_price if current_price > 0 else 0

        # Risk level
        if constrained_pct < 0.03:
            risk = "low"
        elif constrained_pct < 0.07:
            risk = "moderate"
        else:
            risk = "high"

        rationale = f"Fixed Fractional: {constrained_pct * 100:.1f}% of portfolio."

        return PositionSize(
            method=PositionSizingMethod.FIXED_FRACTIONAL,
            recommended_shares=shares,
            recommended_dollars=position_dollars,
            recommended_pct_portfolio=constrained_pct,
            rationale=rationale,
            risk_level=risk,
            max_position_applied=max_applied,
            min_position_applied=min_applied,
            calculation_details={'fraction': fraction}
        )

    def equal_weight(
        self,
        current_price: float,
        num_positions: int
    ) -> PositionSize:
        """
        Calculate equal-weighted position size

        Args:
            current_price: Current price per share
            num_positions: Number of positions in portfolio

        Returns:
            PositionSize with equal weighting
        """
        if num_positions <= 0:
            return self._zero_position("equal_weight")

        # Equal weight
        position_pct = 1.0 / num_positions

        # Apply constraints
        constrained_pct = min(position_pct, self.max_position_pct)
        constrained_pct = max(constrained_pct, self.min_position_pct)

        max_applied = constrained_pct < position_pct
        min_applied = constrained_pct > position_pct

        # Calculate shares
        position_dollars = self.portfolio_value * constrained_pct
        shares = position_dollars / current_price if current_price > 0 else 0

        risk = "moderate"

        rationale = f"Equal Weight: {constrained_pct * 100:.1f}% (1/{num_positions} positions)."

        return PositionSize(
            method=PositionSizingMethod.EQUAL_WEIGHT,
            recommended_shares=shares,
            recommended_dollars=position_dollars,
            recommended_pct_portfolio=constrained_pct,
            rationale=rationale,
            risk_level=risk,
            max_position_applied=max_applied,
            min_position_applied=min_applied,
            calculation_details={'num_positions': num_positions}
        )

    def risk_adjusted_sizing(
        self,
        current_price: float,
        stop_loss_pct: float,
        max_loss_dollars: Optional[float] = None
    ) -> PositionSize:
        """
        Calculate position size based on maximum acceptable loss

        Position Size = Max Loss / (Price * Stop Loss %)

        Args:
            current_price: Current price per share
            stop_loss_pct: Stop loss percentage (e.g., 0.05 for 5%)
            max_loss_dollars: Maximum acceptable loss in dollars
                            (defaults to max_risk_per_trade_pct * portfolio_value)

        Returns:
            PositionSize with risk-adjusted sizing
        """
        if stop_loss_pct <= 0 or current_price <= 0:
            return self._zero_position("risk_adjusted")

        # Default max loss
        if max_loss_dollars is None:
            max_loss_dollars = self.portfolio_value * self.max_risk_per_trade_pct

        # Calculate shares
        shares = max_loss_dollars / (current_price * stop_loss_pct)

        # Calculate position value
        position_dollars = shares * current_price
        position_pct = position_dollars / self.portfolio_value

        # Apply constraints
        if position_pct > self.max_position_pct:
            position_pct = self.max_position_pct
            position_dollars = self.portfolio_value * position_pct
            shares = position_dollars / current_price
            max_applied = True
        else:
            max_applied = False

        if position_pct < self.min_position_pct:
            position_pct = self.min_position_pct
            position_dollars = self.portfolio_value * position_pct
            shares = position_dollars / current_price
            min_applied = True
        else:
            min_applied = False

        # Risk level
        if position_pct < 0.03:
            risk = "low"
        elif position_pct < 0.07:
            risk = "moderate"
        else:
            risk = "high"

        rationale = f"Risk-Adjusted: {shares:.0f} shares with {stop_loss_pct * 100:.1f}% stop-loss (max loss: ${max_loss_dollars:.2f})."

        return PositionSize(
            method=PositionSizingMethod.FIXED_FRACTIONAL,  # Closest enum value
            recommended_shares=shares,
            recommended_dollars=position_dollars,
            recommended_pct_portfolio=position_pct,
            rationale=rationale,
            risk_level=risk,
            max_position_applied=max_applied,
            min_position_applied=min_applied,
            calculation_details={
                'stop_loss_pct': stop_loss_pct,
                'max_loss_dollars': max_loss_dollars
            }
        )

    def _zero_position(self, method: str) -> PositionSize:
        """Return zero position size"""
        return PositionSize(
            method=PositionSizingMethod.FIXED_FRACTIONAL,
            recommended_shares=0,
            recommended_dollars=0,
            recommended_pct_portfolio=0,
            rationale=f"{method}: Invalid parameters, no position recommended.",
            risk_level="none"
        )


# ============================================================================
# Utility Functions
# ============================================================================

def calculate_optimal_position(
    portfolio_value: float,
    current_price: float,
    method: str = "kelly",
    **kwargs
) -> PositionSize:
    """
    Calculate optimal position size using specified method

    Args:
        portfolio_value: Total portfolio value
        current_price: Current price per share
        method: Sizing method ("kelly", "risk_parity", "volatility_based", "fixed_fractional")
        **kwargs: Method-specific parameters

    Returns:
        PositionSize
    """
    calculator = PositionSizingCalculator(portfolio_value=portfolio_value)

    if method == "kelly":
        return calculator.kelly_criterion(current_price=current_price, **kwargs)
    elif method == "risk_parity":
        return calculator.risk_parity(current_price=current_price, **kwargs)
    elif method == "volatility_based":
        return calculator.volatility_based(current_price=current_price, **kwargs)
    elif method == "fixed_fractional":
        return calculator.fixed_fractional(current_price=current_price, **kwargs)
    elif method == "equal_weight":
        return calculator.equal_weight(current_price=current_price, **kwargs)
    else:
        return calculator.fixed_fractional(current_price=current_price)
