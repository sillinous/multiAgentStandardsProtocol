"""
Command Interpreter for Natural Language Trading

Interprets user commands and executes trading actions.
Converts natural language intent into concrete trading operations.

Features:
- Buy/Sell order execution
- Risk adjustment
- Portfolio management
- Trading control (start/stop)
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime

from .query_processor import ProcessedQuery, QueryIntent


# ============================================================================
# Command Models
# ============================================================================

class CommandType(str, Enum):
    """Type of trading command"""
    BUY = "buy"
    SELL = "sell"
    ADJUST_RISK = "adjust_risk"
    STOP_TRADING = "stop_trading"
    START_TRADING = "start_trading"
    SET_ALLOCATION = "set_allocation"
    REBALANCE = "rebalance"
    CANCEL_ORDER = "cancel_order"


class CommandStatus(str, Enum):
    """Status of command execution"""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    PENDING = "pending"
    CANCELLED = "cancelled"


@dataclass
class TradingCommand:
    """Structured trading command"""

    command_type: CommandType
    symbol: Optional[str] = None
    quantity: Optional[float] = None
    amount: Optional[float] = None  # Dollar amount

    # Risk adjustment
    risk_level: Optional[str] = None  # "conservative", "balanced", "aggressive"

    # Additional parameters
    parameters: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    original_query: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'command_type': self.command_type.value,
            'symbol': self.symbol,
            'quantity': self.quantity,
            'amount': self.amount,
            'risk_level': self.risk_level,
            'parameters': self.parameters,
            'original_query': self.original_query,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class CommandResult:
    """Result of command execution"""

    status: CommandStatus
    command: TradingCommand
    message: str

    # Execution details
    executed_quantity: Optional[float] = None
    executed_price: Optional[float] = None
    order_id: Optional[str] = None

    # Additional data
    data: Dict[str, Any] = field(default_factory=dict)

    # Errors
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'status': self.status.value,
            'command': self.command.to_dict(),
            'message': self.message,
            'executed_quantity': self.executed_quantity,
            'executed_price': self.executed_price,
            'order_id': self.order_id,
            'data': self.data,
            'error': self.error
        }


# ============================================================================
# Command Interpreter
# ============================================================================

class CommandInterpreter:
    """
    Interprets and executes trading commands from natural language

    Converts ProcessedQuery objects into executable TradingCommand objects
    and coordinates execution through the trading engine.

    Example:
        interpreter = CommandInterpreter(paper_trading_engine)

        # User says: "Buy 100 shares of AAPL"
        query = query_processor.process("Buy 100 shares of AAPL")
        command = interpreter.interpret(query)
        result = interpreter.execute(command)

        print(result.message)  # "✅ Bought 100 shares of AAPL at $175.50"
    """

    def __init__(
        self,
        paper_trading_engine=None,
        default_quantity: float = 10.0,
        default_amount: float = 1000.0,
        max_position_size: float = 10000.0
    ):
        """
        Initialize command interpreter

        Args:
            paper_trading_engine: Optional PaperTradingEngine for execution
            default_quantity: Default number of shares if not specified
            default_amount: Default dollar amount if not specified
            max_position_size: Maximum position size limit
        """
        self.paper_trading_engine = paper_trading_engine
        self.default_quantity = default_quantity
        self.default_amount = default_amount
        self.max_position_size = max_position_size

        # Trading state
        self.trading_enabled = True
        self.current_risk_level = "balanced"

        # Command history
        self.command_history: List[CommandResult] = []

    def interpret(self, query: ProcessedQuery) -> Optional[TradingCommand]:
        """
        Interpret a processed query into a trading command

        Args:
            query: ProcessedQuery from QueryProcessor

        Returns:
            TradingCommand if query is a command, None otherwise
        """
        # Map intent to command
        intent_to_command = {
            QueryIntent.BUY: self._interpret_buy,
            QueryIntent.SELL: self._interpret_sell,
            QueryIntent.ADJUST_RISK: self._interpret_adjust_risk,
            QueryIntent.STOP_TRADING: self._interpret_stop_trading,
        }

        interpreter_func = intent_to_command.get(query.intent)

        if interpreter_func:
            return interpreter_func(query)

        return None

    def execute(self, command: TradingCommand) -> CommandResult:
        """
        Execute a trading command

        Args:
            command: TradingCommand to execute

        Returns:
            CommandResult with execution details
        """
        # Check if trading is enabled
        if not self.trading_enabled and command.command_type not in [
            CommandType.START_TRADING
        ]:
            result = CommandResult(
                status=CommandStatus.FAILED,
                command=command,
                message="❌ Trading is currently disabled",
                error="Trading disabled"
            )
            self.command_history.append(result)
            return result

        # Route to appropriate executor
        executors = {
            CommandType.BUY: self._execute_buy,
            CommandType.SELL: self._execute_sell,
            CommandType.ADJUST_RISK: self._execute_adjust_risk,
            CommandType.STOP_TRADING: self._execute_stop_trading,
            CommandType.START_TRADING: self._execute_start_trading,
        }

        executor_func = executors.get(command.command_type)

        if executor_func:
            result = executor_func(command)
            self.command_history.append(result)
            return result

        # Unknown command
        result = CommandResult(
            status=CommandStatus.FAILED,
            command=command,
            message=f"❌ Unknown command type: {command.command_type}",
            error="Unknown command type"
        )
        self.command_history.append(result)
        return result

    def interpret_and_execute(self, query: ProcessedQuery) -> CommandResult:
        """
        Interpret and execute in one step

        Args:
            query: ProcessedQuery from QueryProcessor

        Returns:
            CommandResult with execution details
        """
        command = self.interpret(query)

        if not command:
            return CommandResult(
                status=CommandStatus.FAILED,
                command=TradingCommand(
                    command_type=CommandType.BUY,
                    original_query=query.original_text
                ),
                message="❌ Could not interpret command",
                error="Interpretation failed"
            )

        return self.execute(command)

    # ========================================================================
    # Interpretation Methods
    # ========================================================================

    def _interpret_buy(self, query: ProcessedQuery) -> TradingCommand:
        """Interpret a buy command"""
        symbol = query.symbols[0] if query.symbols else None

        return TradingCommand(
            command_type=CommandType.BUY,
            symbol=symbol,
            quantity=query.amount or self.default_quantity,
            original_query=query.original_text
        )

    def _interpret_sell(self, query: ProcessedQuery) -> TradingCommand:
        """Interpret a sell command"""
        symbol = query.symbols[0] if query.symbols else None

        # Check for "sell all" or "sell everything"
        sell_all = any(word in query.original_text.lower()
                      for word in ['all', 'everything', 'entire'])

        return TradingCommand(
            command_type=CommandType.SELL,
            symbol=symbol,
            quantity=query.amount if not sell_all else None,
            parameters={'sell_all': sell_all},
            original_query=query.original_text
        )

    def _interpret_adjust_risk(self, query: ProcessedQuery) -> TradingCommand:
        """Interpret a risk adjustment command"""
        text = query.original_text.lower()

        # Determine risk level
        risk_level = None
        if any(word in text for word in ['conservative', 'safe', 'careful', 'cautious']):
            risk_level = "conservative"
        elif any(word in text for word in ['aggressive', 'risky', 'bold']):
            risk_level = "aggressive"
        elif any(word in text for word in ['balanced', 'moderate', 'normal']):
            risk_level = "balanced"

        return TradingCommand(
            command_type=CommandType.ADJUST_RISK,
            risk_level=risk_level,
            original_query=query.original_text
        )

    def _interpret_stop_trading(self, query: ProcessedQuery) -> TradingCommand:
        """Interpret a stop trading command"""
        return TradingCommand(
            command_type=CommandType.STOP_TRADING,
            original_query=query.original_text
        )

    # ========================================================================
    # Execution Methods
    # ========================================================================

    def _execute_buy(self, command: TradingCommand) -> CommandResult:
        """Execute a buy order"""
        if not command.symbol:
            return CommandResult(
                status=CommandStatus.FAILED,
                command=command,
                message="❌ No symbol specified for buy order",
                error="Missing symbol"
            )

        quantity = command.quantity or self.default_quantity

        # If paper trading engine is available, use it
        if self.paper_trading_engine:
            try:
                # Execute through paper trading engine
                execution_result = self.paper_trading_engine.execute_decision(
                    symbol=command.symbol,
                    decision={
                        'action': 'buy',
                        'confidence': 0.8,  # Default confidence
                        'quantity': quantity
                    }
                )

                if execution_result.get('status') == 'executed':
                    return CommandResult(
                        status=CommandStatus.SUCCESS,
                        command=command,
                        message=f"✅ Bought {quantity} shares of {command.symbol} at ${execution_result.get('price', 0):.2f}",
                        executed_quantity=quantity,
                        executed_price=execution_result.get('price'),
                        order_id=execution_result.get('order_id'),
                        data=execution_result
                    )
                else:
                    return CommandResult(
                        status=CommandStatus.FAILED,
                        command=command,
                        message=f"❌ Buy order failed: {execution_result.get('error', 'Unknown error')}",
                        error=execution_result.get('error')
                    )

            except Exception as e:
                return CommandResult(
                    status=CommandStatus.FAILED,
                    command=command,
                    message=f"❌ Buy order failed: {str(e)}",
                    error=str(e)
                )

        # Simulated execution without paper trading engine
        return CommandResult(
            status=CommandStatus.SUCCESS,
            command=command,
            message=f"✅ [SIMULATED] Would buy {quantity} shares of {command.symbol}",
            executed_quantity=quantity,
            data={'simulated': True}
        )

    def _execute_sell(self, command: TradingCommand) -> CommandResult:
        """Execute a sell order"""
        if not command.symbol:
            return CommandResult(
                status=CommandStatus.FAILED,
                command=command,
                message="❌ No symbol specified for sell order",
                error="Missing symbol"
            )

        sell_all = command.parameters.get('sell_all', False)

        if sell_all:
            quantity_str = "all shares"
        else:
            quantity = command.quantity or self.default_quantity
            quantity_str = f"{quantity} shares"

        # If paper trading engine is available, use it
        if self.paper_trading_engine:
            try:
                execution_result = self.paper_trading_engine.execute_decision(
                    symbol=command.symbol,
                    decision={
                        'action': 'sell',
                        'confidence': 0.8,
                        'quantity': command.quantity if not sell_all else None
                    }
                )

                if execution_result.get('status') == 'executed':
                    return CommandResult(
                        status=CommandStatus.SUCCESS,
                        command=command,
                        message=f"✅ Sold {quantity_str} of {command.symbol} at ${execution_result.get('price', 0):.2f}",
                        executed_quantity=execution_result.get('quantity'),
                        executed_price=execution_result.get('price'),
                        order_id=execution_result.get('order_id'),
                        data=execution_result
                    )
                else:
                    return CommandResult(
                        status=CommandStatus.FAILED,
                        command=command,
                        message=f"❌ Sell order failed: {execution_result.get('error', 'Unknown error')}",
                        error=execution_result.get('error')
                    )

            except Exception as e:
                return CommandResult(
                    status=CommandStatus.FAILED,
                    command=command,
                    message=f"❌ Sell order failed: {str(e)}",
                    error=str(e)
                )

        # Simulated execution
        return CommandResult(
            status=CommandStatus.SUCCESS,
            command=command,
            message=f"✅ [SIMULATED] Would sell {quantity_str} of {command.symbol}",
            data={'simulated': True}
        )

    def _execute_adjust_risk(self, command: TradingCommand) -> CommandResult:
        """Execute risk adjustment"""
        if not command.risk_level:
            return CommandResult(
                status=CommandStatus.FAILED,
                command=command,
                message="❌ No risk level specified",
                error="Missing risk level"
            )

        old_level = self.current_risk_level
        self.current_risk_level = command.risk_level

        return CommandResult(
            status=CommandStatus.SUCCESS,
            command=command,
            message=f"✅ Risk level adjusted from {old_level} to {command.risk_level}",
            data={
                'old_level': old_level,
                'new_level': command.risk_level
            }
        )

    def _execute_stop_trading(self, command: TradingCommand) -> CommandResult:
        """Execute stop trading"""
        self.trading_enabled = False

        return CommandResult(
            status=CommandStatus.SUCCESS,
            command=command,
            message="⏸️  Trading stopped. Use 'start trading' to resume.",
            data={'trading_enabled': False}
        )

    def _execute_start_trading(self, command: TradingCommand) -> CommandResult:
        """Execute start trading"""
        self.trading_enabled = True

        return CommandResult(
            status=CommandStatus.SUCCESS,
            command=command,
            message="▶️  Trading started. Ready to execute commands.",
            data={'trading_enabled': True}
        )

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def get_command_history(self, limit: int = 10) -> List[CommandResult]:
        """Get recent command history"""
        return self.command_history[-limit:]

    def get_last_command(self) -> Optional[CommandResult]:
        """Get the last executed command"""
        return self.command_history[-1] if self.command_history else None

    def clear_history(self):
        """Clear command history"""
        self.command_history.clear()

    def get_trading_status(self) -> Dict[str, Any]:
        """Get current trading status"""
        return {
            'trading_enabled': self.trading_enabled,
            'risk_level': self.current_risk_level,
            'commands_executed': len(self.command_history),
            'last_command': self.get_last_command().to_dict() if self.get_last_command() else None
        }


# ============================================================================
# Utility Functions
# ============================================================================

def quick_execute(query_text: str, paper_trading_engine=None) -> CommandResult:
    """
    Quick execute a natural language command

    Args:
        query_text: Natural language command
        paper_trading_engine: Optional paper trading engine

    Returns:
        CommandResult
    """
    from .query_processor import QueryProcessor

    processor = QueryProcessor()
    interpreter = CommandInterpreter(paper_trading_engine)

    query = processor.process(query_text)
    return interpreter.interpret_and_execute(query)
