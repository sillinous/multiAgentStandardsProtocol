"""
NEXUS Paper Trading API Routes

Exposes paper trading functionality for risk-free strategy testing.

Features:
- Create and manage virtual trading portfolios
- Place and execute simulated orders
- Track positions and P&L in real-time
- Order history and trade log
- Portfolio performance metrics

Endpoints:
- POST /api/paper/portfolios - Create portfolio
- GET /api/paper/portfolios/{id} - Get portfolio summary
- DELETE /api/paper/portfolios/{id} - Delete portfolio
- POST /api/paper/portfolios/{id}/orders - Place order
- POST /api/paper/portfolios/{id}/orders/{order_id}/execute - Execute order
- DELETE /api/paper/portfolios/{id}/orders/{order_id} - Cancel order
- GET /api/paper/portfolios/{id}/positions - Get positions
- GET /api/paper/portfolios/{id}/orders - Get order history
- POST /api/paper/portfolios/{id}/prices - Update market prices
- POST /api/paper/portfolios/{id}/reset - Reset portfolio
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional

# Import paper trading engine
try:
    from superstandard.trading.paper_trading import (
        PaperTradingEngine,
        OrderSide,
        get_or_create_portfolio,
        delete_portfolio
    )
    PAPER_TRADING_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Paper trading engine not available: {e}")
    PAPER_TRADING_AVAILABLE = False

router = APIRouter(prefix="/api/paper", tags=["paper_trading"])


# ============================================================================
# Pydantic Models
# ============================================================================

class PortfolioCreateRequest(BaseModel):
    """Request to create paper trading portfolio"""
    portfolio_id: str = Field(..., description="Unique portfolio identifier")
    initial_capital: float = Field(default=10000.0, gt=0, description="Starting virtual capital")

    class Config:
        json_schema_extra = {
            "example": {
                "portfolio_id": "trader_001",
                "initial_capital": 10000.0
            }
        }


class OrderPlaceRequest(BaseModel):
    """Request to place order"""
    symbol: str = Field(..., description="Trading symbol (e.g., SOL/USD)")
    side: str = Field(..., pattern="^(buy|sell)$", description="Order side: buy or sell")
    quantity: float = Field(..., gt=0, description="Order quantity")
    price: Optional[float] = Field(None, gt=0, description="Limit price (None for market order)")

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "SOL/USD",
                "side": "buy",
                "quantity": 10.0,
                "price": None
            }
        }


class OrderExecuteRequest(BaseModel):
    """Request to execute order"""
    market_price: float = Field(..., gt=0, description="Current market price")

    class Config:
        json_schema_extra = {
            "example": {
                "market_price": 125.50
            }
        }


class PriceUpdateRequest(BaseModel):
    """Request to update market prices"""
    prices: Dict[str, float] = Field(..., description="Symbol -> price mapping")

    class Config:
        json_schema_extra = {
            "example": {
                "prices": {
                    "SOL/USD": 125.50,
                    "BTC/USD": 45000.00
                }
            }
        }


# ============================================================================
# Portfolio Management Endpoints
# ============================================================================

@router.post("/portfolios")
async def create_portfolio(request: PortfolioCreateRequest) -> Dict[str, Any]:
    """
    Create a new paper trading portfolio

    Initializes a virtual portfolio with simulated capital for risk-free trading.
    """
    if not PAPER_TRADING_AVAILABLE:
        raise HTTPException(status_code=503, detail="Paper trading engine not available")

    engine = get_or_create_portfolio(request.portfolio_id, request.initial_capital)
    summary = engine.get_portfolio_summary()

    return {
        "status": "created",
        "message": "Paper trading portfolio created successfully",
        "portfolio": summary
    }


@router.get("/portfolios/{portfolio_id}")
async def get_portfolio(portfolio_id: str) -> Dict[str, Any]:
    """
    Get portfolio summary and performance metrics

    Returns current portfolio state including cash, equity, P&L, and positions.
    """
    if not PAPER_TRADING_AVAILABLE:
        raise HTTPException(status_code=503, detail="Paper trading engine not available")

    engine = get_or_create_portfolio(portfolio_id)
    summary = engine.get_portfolio_summary()

    return {
        "status": "success",
        "portfolio": summary
    }


@router.delete("/portfolios/{portfolio_id}")
async def delete_portfolio_endpoint(portfolio_id: str) -> Dict[str, str]:
    """Delete paper trading portfolio"""
    if not PAPER_TRADING_AVAILABLE:
        raise HTTPException(status_code=503, detail="Paper trading engine not available")

    deleted = delete_portfolio(portfolio_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    return {
        "status": "success",
        "message": f"Portfolio {portfolio_id} deleted"
    }


@router.post("/portfolios/{portfolio_id}/reset")
async def reset_portfolio(portfolio_id: str) -> Dict[str, Any]:
    """
    Reset portfolio to initial state

    Clears all positions, orders, and resets capital to initial amount.
    """
    if not PAPER_TRADING_AVAILABLE:
        raise HTTPException(status_code=503, detail="Paper trading engine not available")

    engine = get_or_create_portfolio(portfolio_id)
    engine.reset_portfolio()
    summary = engine.get_portfolio_summary()

    return {
        "status": "success",
        "message": "Portfolio reset to initial state",
        "portfolio": summary
    }


# ============================================================================
# Order Management Endpoints
# ============================================================================

@router.post("/portfolios/{portfolio_id}/orders")
async def place_order(portfolio_id: str, request: OrderPlaceRequest) -> Dict[str, Any]:
    """
    Place a trading order

    Creates a pending order that can be executed at market price.
    Supports both market orders (price=null) and limit orders.
    """
    if not PAPER_TRADING_AVAILABLE:
        raise HTTPException(status_code=503, detail="Paper trading engine not available")

    engine = get_or_create_portfolio(portfolio_id)

    # Map side string to enum
    side = OrderSide.BUY if request.side.lower() == "buy" else OrderSide.SELL

    order = engine.place_order(
        symbol=request.symbol,
        side=side,
        quantity=request.quantity,
        price=request.price
    )

    return {
        "status": "success",
        "message": "Order placed successfully",
        "order": {
            "order_id": order.order_id,
            "symbol": order.symbol,
            "side": order.side.value,
            "quantity": order.quantity,
            "price": order.price,
            "status": order.status.value,
            "created_at": order.created_at
        }
    }


@router.post("/portfolios/{portfolio_id}/orders/{order_id}/execute")
async def execute_order(
    portfolio_id: str,
    order_id: str,
    request: OrderExecuteRequest
) -> Dict[str, Any]:
    """
    Execute a pending order at market price

    Simulates order execution at the provided market price.
    Updates portfolio positions and cash accordingly.
    """
    if not PAPER_TRADING_AVAILABLE:
        raise HTTPException(status_code=503, detail="Paper trading engine not available")

    engine = get_or_create_portfolio(portfolio_id)

    executed = engine.execute_order(order_id, request.market_price)

    if not executed:
        raise HTTPException(
            status_code=400,
            detail="Order could not be executed (insufficient funds or price limits not met)"
        )

    # Get updated portfolio summary
    summary = engine.get_portfolio_summary()

    return {
        "status": "success",
        "message": "Order executed successfully",
        "order_id": order_id,
        "executed_price": request.market_price,
        "portfolio": summary
    }


@router.delete("/portfolios/{portfolio_id}/orders/{order_id}")
async def cancel_order(portfolio_id: str, order_id: str) -> Dict[str, str]:
    """
    Cancel a pending order

    Removes order from the order book before execution.
    """
    if not PAPER_TRADING_AVAILABLE:
        raise HTTPException(status_code=503, detail="Paper trading engine not available")

    engine = get_or_create_portfolio(portfolio_id)

    cancelled = engine.cancel_order(order_id)

    if not cancelled:
        raise HTTPException(status_code=404, detail="Order not found")

    return {
        "status": "success",
        "message": f"Order {order_id} cancelled"
    }


@router.get("/portfolios/{portfolio_id}/orders")
async def get_order_history(
    portfolio_id: str,
    limit: int = Query(100, ge=1, le=1000)
) -> List[Dict[str, Any]]:
    """
    Get order history

    Returns historical orders sorted by creation time (newest first).
    """
    if not PAPER_TRADING_AVAILABLE:
        raise HTTPException(status_code=503, detail="Paper trading engine not available")

    engine = get_or_create_portfolio(portfolio_id)
    orders = engine.get_order_history(limit=limit)

    return orders


# ============================================================================
# Position Management Endpoints
# ============================================================================

@router.get("/portfolios/{portfolio_id}/positions")
async def get_positions(portfolio_id: str) -> List[Dict[str, Any]]:
    """
    Get all open positions

    Returns current positions with unrealized P&L and performance metrics.
    """
    if not PAPER_TRADING_AVAILABLE:
        raise HTTPException(status_code=503, detail="Paper trading engine not available")

    engine = get_or_create_portfolio(portfolio_id)
    positions = engine.get_positions()

    return positions


@router.post("/portfolios/{portfolio_id}/prices")
async def update_prices(portfolio_id: str, request: PriceUpdateRequest) -> Dict[str, Any]:
    """
    Update market prices

    Updates current prices for all symbols and recalculates P&L.
    Use this endpoint to simulate real-time price updates.
    """
    if not PAPER_TRADING_AVAILABLE:
        raise HTTPException(status_code=503, detail="Paper trading engine not available")

    engine = get_or_create_portfolio(portfolio_id)
    engine.update_prices(request.prices)

    summary = engine.get_portfolio_summary()
    positions = engine.get_positions()

    return {
        "status": "success",
        "message": "Prices updated successfully",
        "portfolio": summary,
        "positions": positions
    }


# ============================================================================
# Health Check
# ============================================================================

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Check paper trading system health"""
    if not PAPER_TRADING_AVAILABLE:
        return {
            "status": "unavailable",
            "paper_trading_available": False
        }

    # Count active portfolios
    from superstandard.trading.paper_trading import _portfolios

    active_portfolios = len(_portfolios)
    total_equity = sum(p.portfolio.equity for p in _portfolios.values())
    total_trades = sum(len(p.portfolio.order_history) for p in _portfolios.values())

    return {
        "status": "healthy",
        "paper_trading_available": True,
        "active_portfolios": active_portfolios,
        "total_equity": total_equity,
        "total_trades": total_trades
    }


# ============================================================================
# Quick Trade Endpoint (Convenience)
# ============================================================================

@router.post("/portfolios/{portfolio_id}/quick-trade")
async def quick_trade(
    portfolio_id: str,
    symbol: str = Query(..., description="Trading symbol"),
    side: str = Query(..., pattern="^(buy|sell)$", description="Order side"),
    quantity: float = Query(..., gt=0, description="Order quantity"),
    market_price: float = Query(..., gt=0, description="Current market price")
) -> Dict[str, Any]:
    """
    Quick market order execution

    Convenience endpoint that places and immediately executes a market order.
    Useful for rapid testing and automated strategies.
    """
    if not PAPER_TRADING_AVAILABLE:
        raise HTTPException(status_code=503, detail="Paper trading engine not available")

    engine = get_or_create_portfolio(portfolio_id)

    # Map side
    order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL

    # Place order
    order = engine.place_order(
        symbol=symbol,
        side=order_side,
        quantity=quantity,
        price=None  # Market order
    )

    # Execute immediately
    executed = engine.execute_order(order.order_id, market_price)

    if not executed:
        raise HTTPException(
            status_code=400,
            detail="Quick trade failed (insufficient funds)"
        )

    summary = engine.get_portfolio_summary()

    return {
        "status": "success",
        "message": "Quick trade executed successfully",
        "order_id": order.order_id,
        "symbol": symbol,
        "side": side,
        "quantity": quantity,
        "executed_price": market_price,
        "portfolio": summary
    }
