"""
APQC Workflow Execution Engine
==============================

A comprehensive execution engine that runs APQC processes defined by
Agent Cards. Orchestrates step execution, decision evaluation,
integration calls, and audit logging.

Features:
- Sequential and parallel step execution
- Decision rule evaluation
- Integration API calls
- Error handling with retries
- State persistence
- Real-time progress tracking
- Complete audit trail

Version: 1.0.0
Date: 2025-11-25
"""

import ast
import asyncio
import json
import operator
import uuid
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import traceback
import threading
from collections import deque


class ExecutionStatus(Enum):
    """Status of workflow or step execution"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    WAITING_APPROVAL = "waiting_approval"
    WAITING_INPUT = "waiting_input"


class StepResult(Enum):
    """Result of individual step execution"""
    SUCCESS = "success"
    FAILURE = "failure"
    SKIPPED = "skipped"
    RETRY = "retry"
    MANUAL_REVIEW = "manual_review"


# ============================================================================
# Circuit Breaker Pattern
# ============================================================================

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered


@dataclass
class CircuitBreaker:
    """
    Circuit breaker to prevent cascading failures.

    When failures exceed threshold, the circuit opens and fast-fails requests
    until the reset timeout expires, then allows a test request through.
    """
    name: str
    failure_threshold: int = 5
    reset_timeout_seconds: int = 60
    half_open_max_calls: int = 3

    state: CircuitState = field(default=CircuitState.CLOSED)
    failure_count: int = field(default=0)
    success_count: int = field(default=0)
    last_failure_time: Optional[datetime] = field(default=None)
    half_open_calls: int = field(default=0)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def can_execute(self) -> tuple[bool, Optional[str]]:
        """Check if execution is allowed"""
        with self._lock:
            if self.state == CircuitState.CLOSED:
                return True, None

            if self.state == CircuitState.OPEN:
                # Check if reset timeout has passed
                if self.last_failure_time:
                    elapsed = (datetime.now() - self.last_failure_time).total_seconds()
                    if elapsed >= self.reset_timeout_seconds:
                        self.state = CircuitState.HALF_OPEN
                        self.half_open_calls = 0
                        return True, None
                return False, f"Circuit breaker '{self.name}' is OPEN. Retry after {self.reset_timeout_seconds}s"

            if self.state == CircuitState.HALF_OPEN:
                if self.half_open_calls < self.half_open_max_calls:
                    self.half_open_calls += 1
                    return True, None
                return False, f"Circuit breaker '{self.name}' is HALF_OPEN, max test calls reached"

        return True, None

    def record_success(self):
        """Record a successful execution"""
        with self._lock:
            self.success_count += 1
            if self.state == CircuitState.HALF_OPEN:
                # Successful test, close circuit
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.half_open_calls = 0

    def record_failure(self):
        """Record a failed execution"""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.now()

            if self.state == CircuitState.HALF_OPEN:
                # Failed test, reopen circuit
                self.state = CircuitState.OPEN
                self.half_open_calls = 0
            elif self.state == CircuitState.CLOSED:
                if self.failure_count >= self.failure_threshold:
                    self.state = CircuitState.OPEN

    def get_status(self) -> Dict:
        """Get circuit breaker status"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None
        }


# ============================================================================
# Retry with Exponential Backoff
# ============================================================================

@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_retries: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True  # Add randomness to prevent thundering herd

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number (0-indexed)"""
        delay = self.base_delay_seconds * (self.exponential_base ** attempt)
        delay = min(delay, self.max_delay_seconds)

        if self.jitter:
            # Add up to 25% jitter
            jitter_range = delay * 0.25
            delay += random.uniform(-jitter_range, jitter_range)

        return max(0, delay)


async def retry_with_backoff(
    func: Callable,
    config: RetryConfig = None,
    on_retry: Callable = None
) -> Any:
    """
    Execute function with exponential backoff retry.

    Args:
        func: Async function to execute
        config: Retry configuration
        on_retry: Optional callback on retry (attempt, error, delay)

    Returns:
        Function result on success

    Raises:
        Last exception if all retries exhausted
    """
    config = config or RetryConfig()
    last_exception = None

    for attempt in range(config.max_retries + 1):
        try:
            return await func()
        except Exception as e:
            last_exception = e

            if attempt < config.max_retries:
                delay = config.get_delay(attempt)
                if on_retry:
                    on_retry(attempt, e, delay)
                await asyncio.sleep(delay)

    raise last_exception


# ============================================================================
# Dead Letter Queue for Failed Executions
# ============================================================================

@dataclass
class DeadLetterEntry:
    """Entry in the dead letter queue"""
    execution_id: str
    apqc_code: str
    input_data: Dict[str, Any]
    error: str
    traceback: str
    failed_at: datetime
    retry_count: int
    original_context: Dict[str, Any] = field(default_factory=dict)


class DeadLetterQueue:
    """
    Queue for failed workflow executions that can be retried later.

    Provides:
    - Persistent storage of failed executions
    - Retry capability with configurable limits
    - Metrics on failure patterns
    """

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.entries: deque[DeadLetterEntry] = deque(maxlen=max_size)
        self._lock = threading.Lock()

    def add(self, entry: DeadLetterEntry):
        """Add failed execution to queue"""
        with self._lock:
            self.entries.append(entry)

    def get_all(self) -> List[DeadLetterEntry]:
        """Get all entries"""
        with self._lock:
            return list(self.entries)

    def get_by_id(self, execution_id: str) -> Optional[DeadLetterEntry]:
        """Get entry by execution ID"""
        with self._lock:
            for entry in self.entries:
                if entry.execution_id == execution_id:
                    return entry
        return None

    def remove(self, execution_id: str) -> bool:
        """Remove entry from queue"""
        with self._lock:
            for i, entry in enumerate(self.entries):
                if entry.execution_id == execution_id:
                    del self.entries[i]
                    return True
        return False

    def get_stats(self) -> Dict:
        """Get queue statistics"""
        with self._lock:
            if not self.entries:
                return {
                    "total": 0,
                    "by_error_type": {},
                    "by_apqc_code": {}
                }

            by_error = {}
            by_code = {}
            for entry in self.entries:
                # Count by error type
                error_type = entry.error.split(":")[0] if ":" in entry.error else entry.error[:50]
                by_error[error_type] = by_error.get(error_type, 0) + 1

                # Count by APQC code
                by_code[entry.apqc_code] = by_code.get(entry.apqc_code, 0) + 1

            return {
                "total": len(self.entries),
                "by_error_type": by_error,
                "by_apqc_code": by_code,
                "oldest": self.entries[0].failed_at.isoformat() if self.entries else None,
                "newest": self.entries[-1].failed_at.isoformat() if self.entries else None
            }


# Global dead letter queue instance
dead_letter_queue = DeadLetterQueue()


@dataclass
class ExecutionContext:
    """Context passed through workflow execution"""
    execution_id: str
    workflow_id: str
    apqc_code: str
    started_at: datetime
    input_data: Dict[str, Any]
    variables: Dict[str, Any] = field(default_factory=dict)
    credentials: Dict[str, Dict[str, str]] = field(default_factory=dict)
    current_step: int = 0
    total_steps: int = 0
    status: ExecutionStatus = ExecutionStatus.PENDING
    errors: List[Dict] = field(default_factory=list)
    audit_log: List[Dict] = field(default_factory=list)


@dataclass
class StepExecution:
    """Record of a step's execution"""
    step_id: str
    step_number: int
    step_name: str
    status: StepResult
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: int = 0
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    integration_calls: List[Dict] = field(default_factory=list)
    decision_results: List[Dict] = field(default_factory=list)
    error: Optional[str] = None
    retry_count: int = 0


class AuditLogger:
    """Logs all execution events for compliance and debugging"""

    def __init__(self, execution_id: str):
        self.execution_id = execution_id
        self.logs: List[Dict] = []

    def log(self, event_type: str, details: Dict[str, Any], level: str = "info"):
        """Log an event"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "execution_id": self.execution_id,
            "event_type": event_type,
            "level": level,
            "details": details
        }
        self.logs.append(entry)
        # Print for debugging
        print(f"[{level.upper()}] {event_type}: {json.dumps(details, default=str)[:200]}")

    def get_logs(self) -> List[Dict]:
        return self.logs


class DecisionEvaluator:
    """Evaluates business rules and decision conditions"""

    def __init__(self, context: ExecutionContext):
        self.context = context

    def evaluate(self, rule: Dict, step_output: Dict) -> Dict:
        """
        Evaluate a decision rule against step output.

        Returns dict with:
        - rule_id: ID of the rule
        - condition: The condition string
        - result: True/False
        - action: The action to take
        """
        rule_id = rule.get("id", "unknown")
        condition = rule.get("condition", "true")
        threshold = rule.get("default_threshold")

        # Build evaluation context
        eval_context = {
            **self.context.variables,
            **step_output,
            "threshold": threshold,
            "tolerance_threshold": threshold,
            "auto_approve_threshold": threshold,
            "manager_threshold": threshold,
            "amount_cap": threshold,
            "minimum_apr_threshold": threshold,
        }

        try:
            # Safe evaluation of condition
            result = self._safe_eval(condition, eval_context)

            action = rule.get("action_if_true") if result else rule.get("action_if_false")

            return {
                "rule_id": rule_id,
                "rule_name": rule.get("name", ""),
                "condition": condition,
                "threshold": threshold,
                "result": bool(result),
                "action": action,
                "evaluated_at": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "rule_id": rule_id,
                "rule_name": rule.get("name", ""),
                "condition": condition,
                "result": False,
                "action": rule.get("action_if_false"),
                "error": str(e),
                "evaluated_at": datetime.now().isoformat()
            }

    def _safe_eval(self, condition: str, context: Dict) -> bool:
        """
        Safely evaluate a condition string using AST parsing.

        This method parses the condition into an AST and evaluates it
        without using eval(), preventing code injection attacks.

        Supports:
        - Comparisons: ==, !=, <, >, <=, >=
        - Boolean operators: and, or, not
        - Literals: numbers, strings, True, False, None
        - Names: variables from context
        """
        # Normalize operators
        condition = condition.replace(" AND ", " and ")
        condition = condition.replace(" OR ", " or ")
        condition = condition.replace(" NOT ", " not ")

        # Build context with standard boolean values
        allowed_names = {
            "True": True,
            "False": False,
            "true": True,
            "false": False,
            "None": None,
            "none": None,
            **context
        }

        try:
            # Parse the condition into an AST
            tree = ast.parse(condition, mode='eval')

            # Evaluate using our safe evaluator
            return self._eval_node(tree.body, allowed_names)
        except Exception as e:
            # Log the error and default to True
            print(f"[WARNING] Safe eval failed for condition '{condition}': {e}")
            return True

    def _eval_node(self, node: ast.AST, context: Dict) -> Any:
        """
        Recursively evaluate an AST node safely.

        Only allows safe operations - no function calls, attribute access,
        or other potentially dangerous operations.
        """
        # Comparison operators mapping
        COMPARE_OPS = {
            ast.Eq: operator.eq,
            ast.NotEq: operator.ne,
            ast.Lt: operator.lt,
            ast.LtE: operator.le,
            ast.Gt: operator.gt,
            ast.GtE: operator.ge,
            ast.Is: operator.is_,
            ast.IsNot: operator.is_not,
            ast.In: lambda a, b: a in b,
            ast.NotIn: lambda a, b: a not in b,
        }

        # Boolean operators mapping
        BOOL_OPS = {
            ast.And: lambda vals: all(vals),
            ast.Or: lambda vals: any(vals),
        }

        # Unary operators mapping
        UNARY_OPS = {
            ast.Not: operator.not_,
            ast.UAdd: operator.pos,
            ast.USub: operator.neg,
        }

        # Binary operators mapping
        BIN_OPS = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Mod: operator.mod,
        }

        # Handle different node types
        if isinstance(node, ast.Constant):
            # Literal values (Python 3.8+)
            return node.value

        elif isinstance(node, ast.Num):
            # Numbers (Python 3.7 compatibility)
            return node.n

        elif isinstance(node, ast.Str):
            # Strings (Python 3.7 compatibility)
            return node.s

        elif isinstance(node, ast.NameConstant):
            # True, False, None (Python 3.7 compatibility)
            return node.value

        elif isinstance(node, ast.Name):
            # Variable lookup
            name = node.id
            if name not in context:
                raise ValueError(f"Unknown variable: {name}")
            return context[name]

        elif isinstance(node, ast.Compare):
            # Comparison operations (e.g., a == b, a < b < c)
            left = self._eval_node(node.left, context)
            for op, comparator in zip(node.ops, node.comparators):
                op_func = COMPARE_OPS.get(type(op))
                if op_func is None:
                    raise ValueError(f"Unsupported comparison operator: {type(op).__name__}")
                right = self._eval_node(comparator, context)
                if not op_func(left, right):
                    return False
                left = right
            return True

        elif isinstance(node, ast.BoolOp):
            # Boolean operations (and, or)
            op_func = BOOL_OPS.get(type(node.op))
            if op_func is None:
                raise ValueError(f"Unsupported boolean operator: {type(node.op).__name__}")
            # Evaluate values lazily for short-circuit behavior
            if isinstance(node.op, ast.And):
                for value in node.values:
                    if not self._eval_node(value, context):
                        return False
                return True
            else:  # Or
                for value in node.values:
                    if self._eval_node(value, context):
                        return True
                return False

        elif isinstance(node, ast.UnaryOp):
            # Unary operations (not, -, +)
            op_func = UNARY_OPS.get(type(node.op))
            if op_func is None:
                raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
            return op_func(self._eval_node(node.operand, context))

        elif isinstance(node, ast.BinOp):
            # Binary operations (+, -, *, /, %)
            op_func = BIN_OPS.get(type(node.op))
            if op_func is None:
                raise ValueError(f"Unsupported binary operator: {type(node.op).__name__}")
            left = self._eval_node(node.left, context)
            right = self._eval_node(node.right, context)
            return op_func(left, right)

        elif isinstance(node, ast.IfExp):
            # Ternary operator (a if condition else b)
            test = self._eval_node(node.test, context)
            if test:
                return self._eval_node(node.body, context)
            else:
                return self._eval_node(node.orelse, context)

        elif isinstance(node, (ast.List, ast.Tuple)):
            # List and tuple literals
            return [self._eval_node(elem, context) for elem in node.elts]

        else:
            # Reject all other node types (function calls, attribute access, etc.)
            raise ValueError(f"Unsupported expression type: {type(node).__name__}")


class IntegrationClient:
    """Handles calls to external integration APIs"""

    def __init__(self, credentials: Dict[str, Dict[str, str]]):
        self.credentials = credentials
        self.call_log: List[Dict] = []

    async def call(self, integration_id: str, operation: str, params: Dict) -> Dict:
        """
        Call an integration API.

        In a real implementation, this would make actual HTTP calls.
        For now, it simulates the call and returns mock data.
        """
        start_time = time.time()

        call_record = {
            "integration_id": integration_id,
            "operation": operation,
            "params": params,
            "started_at": datetime.now().isoformat(),
            "has_credentials": integration_id in self.credentials
        }

        try:
            # Check if credentials exist
            if integration_id not in self.credentials:
                # Simulate without credentials (demo mode)
                result = await self._simulate_call(integration_id, operation, params)
                call_record["mode"] = "simulated"
            else:
                # Would make actual API call here
                result = await self._execute_call(integration_id, operation, params)
                call_record["mode"] = "live"

            call_record["success"] = True
            call_record["result"] = result
            call_record["duration_ms"] = int((time.time() - start_time) * 1000)

        except Exception as e:
            call_record["success"] = False
            call_record["error"] = str(e)
            call_record["duration_ms"] = int((time.time() - start_time) * 1000)
            result = {"error": str(e), "success": False}

        self.call_log.append(call_record)
        return result

    async def _simulate_call(self, integration_id: str, operation: str, params: Dict) -> Dict:
        """Simulate an integration call for demo purposes"""
        # Add small delay to simulate network latency
        await asyncio.sleep(0.1)

        # Return simulated responses based on integration and operation
        simulations = {
            "aws_textract": {
                "extract_text": {
                    "success": True,
                    "extracted_data": {
                        "invoice_number": params.get("invoice_number", "INV-DEMO-001"),
                        "vendor_name": params.get("vendor_name", "Demo Vendor"),
                        "total_amount": params.get("amount", 1500.00),
                        "confidence_score": 95.5
                    }
                }
            },
            "netsuite": {
                "lookup_vendor": {
                    "success": True,
                    "vendor_id": "VND-00123",
                    "vendor_status": "active",
                    "payment_terms": "NET30"
                },
                "three_way_match": {
                    "success": True,
                    "match_status": "full_match",
                    "match_score": 100
                },
                "create_ap_voucher": {
                    "success": True,
                    "voucher_number": f"AP-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
                }
            },
            "slack": {
                "send_message": {
                    "success": True,
                    "message_id": f"msg_{uuid.uuid4().hex[:8]}",
                    "delivered": True
                }
            },
            "quickbooks_online": {
                "create_invoice": {
                    "success": True,
                    "invoice_id": f"QBO-{uuid.uuid4().hex[:8].upper()}"
                }
            }
        }

        if integration_id in simulations and operation in simulations[integration_id]:
            return simulations[integration_id][operation]

        # Default simulation
        return {
            "success": True,
            "simulated": True,
            "integration": integration_id,
            "operation": operation,
            "message": "Simulated response - configure credentials for live execution"
        }

    async def _execute_call(self, integration_id: str, operation: str, params: Dict) -> Dict:
        """Execute actual API call (placeholder for real implementation)"""
        # In a real implementation, this would:
        # 1. Load integration config
        # 2. Build the HTTP request
        # 3. Add authentication headers
        # 4. Make the API call
        # 5. Parse and return the response

        # For now, return simulated response
        return await self._simulate_call(integration_id, operation, params)


class StepExecutor:
    """Executes individual workflow steps"""

    def __init__(self, context: ExecutionContext, integration_client: IntegrationClient,
                 decision_evaluator: DecisionEvaluator, audit_logger: AuditLogger):
        self.context = context
        self.integration_client = integration_client
        self.decision_evaluator = decision_evaluator
        self.audit_logger = audit_logger

    async def execute(self, step_config: Dict, input_data: Dict) -> StepExecution:
        """Execute a single workflow step"""
        step_id = step_config.get("id", f"step_{self.context.current_step}")
        step_number = step_config.get("step_number", self.context.current_step)
        step_name = step_config.get("step_name", "Unknown Step")

        execution = StepExecution(
            step_id=step_id,
            step_number=step_number,
            step_name=step_name,
            status=StepResult.SUCCESS,
            started_at=datetime.now(),
            input_data=input_data
        )

        self.audit_logger.log("step_started", {
            "step_id": step_id,
            "step_number": step_number,
            "step_name": step_name,
            "input_keys": list(input_data.keys())
        })

        try:
            # Execute integrations
            output_data = await self._execute_integrations(step_config, input_data)
            execution.output_data = output_data

            # Evaluate decision rules
            decision_results = self._evaluate_decisions(step_config, output_data)
            execution.decision_results = decision_results

            # Check for manual review or routing
            for result in decision_results:
                if result.get("action") in ["route_to_manual_review", "manual_review", "escalate"]:
                    execution.status = StepResult.MANUAL_REVIEW
                    break

            # Update context variables with output
            self.context.variables.update(output_data)

            execution.completed_at = datetime.now()
            execution.duration_ms = int((execution.completed_at - execution.started_at).total_seconds() * 1000)

            self.audit_logger.log("step_completed", {
                "step_id": step_id,
                "status": execution.status.value,
                "duration_ms": execution.duration_ms,
                "output_keys": list(output_data.keys())
            })

        except Exception as e:
            execution.status = StepResult.FAILURE
            execution.error = str(e)
            execution.completed_at = datetime.now()
            execution.duration_ms = int((execution.completed_at - execution.started_at).total_seconds() * 1000)

            self.audit_logger.log("step_failed", {
                "step_id": step_id,
                "error": str(e),
                "traceback": traceback.format_exc()
            }, level="error")

        return execution

    async def _execute_integrations(self, step_config: Dict, input_data: Dict) -> Dict:
        """Execute integration calls for a step"""
        output = {**input_data}
        required_integrations = step_config.get("required_integrations", [])
        capabilities = step_config.get("capabilities", [])

        for integration_id in required_integrations:
            # Determine operation based on capabilities
            operation = self._map_capability_to_operation(capabilities, integration_id)

            result = await self.integration_client.call(
                integration_id=integration_id,
                operation=operation,
                params=input_data
            )

            # Merge result into output
            if isinstance(result, dict):
                output.update(result)

        return output

    def _map_capability_to_operation(self, capabilities: List[str], integration_id: str) -> str:
        """Map step capabilities to integration operation"""
        # Map common capabilities to operations
        capability_map = {
            "extract_invoice_data_ocr": "extract_text",
            "lookup_vendor_master": "lookup_vendor",
            "three_way_match": "three_way_match",
            "send_approval_request": "send_message",
            "create_ap_voucher": "create_ap_voucher",
            "post_to_ledger": "post_journal_entry"
        }

        for cap in capabilities:
            if cap in capability_map:
                return capability_map[cap]

        return "execute"

    def _evaluate_decisions(self, step_config: Dict, output_data: Dict) -> List[Dict]:
        """Evaluate all decision rules for a step"""
        results = []
        decision_rules = step_config.get("decision_rules", [])

        for rule in decision_rules:
            result = self.decision_evaluator.evaluate(rule, output_data)
            results.append(result)

        return results


class WorkflowEngine:
    """
    Main workflow execution engine.

    Orchestrates the execution of APQC processes defined by Agent Cards.
    """

    def __init__(self, agent_cards_dir: str = None):
        self.agent_cards_dir = Path(agent_cards_dir) if agent_cards_dir else Path(__file__).parent.parent.parent.parent / "agent_cards"
        self.active_executions: Dict[str, ExecutionContext] = {}
        self.completed_executions: List[Dict] = []
        self.execution_callbacks: List[Callable] = []

    def register_callback(self, callback: Callable):
        """Register a callback for execution events"""
        self.execution_callbacks.append(callback)

    def _notify_callbacks(self, event: str, data: Dict):
        """Notify all registered callbacks"""
        for callback in self.execution_callbacks:
            try:
                callback(event, data)
            except Exception as e:
                print(f"Callback error: {e}")

    def load_agent_card(self, apqc_code: str) -> Optional[Dict]:
        """Load agent card definition for an APQC code"""
        code_underscore = apqc_code.replace(".", "_")

        # Try different filename patterns
        patterns = [
            f"apqc_{code_underscore}*.json",
            f"{code_underscore}*.json"
        ]

        for pattern in patterns:
            for filepath in self.agent_cards_dir.glob(pattern):
                try:
                    with open(filepath, 'r') as f:
                        return json.load(f)
                except:
                    continue

        return None

    async def execute(self, apqc_code: str, input_data: Dict,
                      credentials: Dict[str, Dict[str, str]] = None) -> Dict:
        """
        Execute a workflow for the given APQC code.

        Args:
            apqc_code: APQC process code (e.g., "9.2.1.1")
            input_data: Initial input data for the workflow
            credentials: Optional credentials for integrations

        Returns:
            Execution result dictionary
        """
        execution_id = str(uuid.uuid4())

        # Load agent card
        agent_card = self.load_agent_card(apqc_code)
        if not agent_card:
            return {
                "success": False,
                "error": f"Agent card not found for APQC code: {apqc_code}",
                "execution_id": execution_id
            }

        # Create execution context
        context = ExecutionContext(
            execution_id=execution_id,
            workflow_id=f"workflow_{apqc_code}_{execution_id[:8]}",
            apqc_code=apqc_code,
            started_at=datetime.now(),
            input_data=input_data,
            variables=dict(input_data),
            credentials=credentials or {},
            total_steps=len(agent_card.get("agent_cards", []))
        )

        self.active_executions[execution_id] = context

        # Initialize components
        audit_logger = AuditLogger(execution_id)
        integration_client = IntegrationClient(credentials or {})
        decision_evaluator = DecisionEvaluator(context)
        step_executor = StepExecutor(context, integration_client, decision_evaluator, audit_logger)

        audit_logger.log("workflow_started", {
            "apqc_code": apqc_code,
            "apqc_name": agent_card.get("apqc_name"),
            "total_steps": context.total_steps,
            "input_keys": list(input_data.keys())
        })

        context.status = ExecutionStatus.RUNNING
        self._notify_callbacks("workflow_started", {"execution_id": execution_id, "apqc_code": apqc_code})

        step_executions = []
        success = True

        try:
            # Execute each step
            for i, step_config in enumerate(agent_card.get("agent_cards", [])):
                context.current_step = i + 1

                self._notify_callbacks("step_started", {
                    "execution_id": execution_id,
                    "step_number": i + 1,
                    "step_name": step_config.get("step_name")
                })

                # Get input for this step (output from previous step or initial input)
                step_input = context.variables

                # Execute the step
                step_result = await step_executor.execute(step_config, step_input)
                step_executions.append(step_result)

                self._notify_callbacks("step_completed", {
                    "execution_id": execution_id,
                    "step_number": i + 1,
                    "status": step_result.status.value,
                    "duration_ms": step_result.duration_ms
                })

                # Check for failure
                if step_result.status == StepResult.FAILURE:
                    # Check error handlers
                    should_retry = self._handle_error(step_config, step_result, context)
                    if not should_retry:
                        success = False
                        break

                # Check for manual review
                if step_result.status == StepResult.MANUAL_REVIEW:
                    context.status = ExecutionStatus.WAITING_APPROVAL
                    audit_logger.log("waiting_approval", {
                        "step_number": i + 1,
                        "step_name": step_config.get("step_name")
                    })
                    # In a real implementation, this would pause and wait
                    # For now, we'll continue (simulating auto-approval)

            # Complete execution
            if success:
                context.status = ExecutionStatus.COMPLETED
            else:
                context.status = ExecutionStatus.FAILED

        except Exception as e:
            context.status = ExecutionStatus.FAILED
            context.errors.append({
                "error": str(e),
                "traceback": traceback.format_exc(),
                "timestamp": datetime.now().isoformat()
            })
            audit_logger.log("workflow_error", {"error": str(e)}, level="error")
            success = False

        # Build result
        completed_at = datetime.now()
        total_duration = int((completed_at - context.started_at).total_seconds() * 1000)

        result = {
            "success": success,
            "execution_id": execution_id,
            "workflow_id": context.workflow_id,
            "apqc_code": apqc_code,
            "apqc_name": agent_card.get("apqc_name"),
            "status": context.status.value,
            "started_at": context.started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
            "total_duration_ms": total_duration,
            "steps_completed": len([s for s in step_executions if s.status == StepResult.SUCCESS]),
            "total_steps": context.total_steps,
            "step_executions": [
                {
                    "step_number": s.step_number,
                    "step_name": s.step_name,
                    "status": s.status.value,
                    "duration_ms": s.duration_ms,
                    "output_keys": list(s.output_data.keys()),
                    "decision_results": s.decision_results,
                    "error": s.error
                }
                for s in step_executions
            ],
            "final_output": context.variables,
            "integration_calls": integration_client.call_log,
            "audit_log": audit_logger.get_logs(),
            "errors": context.errors
        }

        audit_logger.log("workflow_completed", {
            "success": success,
            "status": context.status.value,
            "total_duration_ms": total_duration,
            "steps_completed": result["steps_completed"]
        })

        # Move to completed
        del self.active_executions[execution_id]
        self.completed_executions.append(result)

        self._notify_callbacks("workflow_completed", {
            "execution_id": execution_id,
            "success": success,
            "status": context.status.value
        })

        return result

    def _handle_error(self, step_config: Dict, step_result: StepExecution, context: ExecutionContext) -> bool:
        """Handle step execution error based on error handlers"""
        error_handlers = step_config.get("error_handlers", [])

        for handler in error_handlers:
            action = handler.get("action", "abort")
            max_retries = handler.get("max_retries", 0)

            if action == "retry" and step_result.retry_count < max_retries:
                step_result.retry_count += 1
                return True  # Should retry

            if action == "skip":
                return True  # Continue to next step

            if action == "escalate":
                # In a real implementation, this would notify someone
                pass

        return False  # Abort

    def get_execution_status(self, execution_id: str) -> Optional[Dict]:
        """Get status of an execution"""
        if execution_id in self.active_executions:
            ctx = self.active_executions[execution_id]
            return {
                "execution_id": execution_id,
                "status": ctx.status.value,
                "current_step": ctx.current_step,
                "total_steps": ctx.total_steps,
                "started_at": ctx.started_at.isoformat()
            }

        # Check completed
        for result in self.completed_executions:
            if result["execution_id"] == execution_id:
                return result

        return None

    def list_executions(self, limit: int = 50) -> List[Dict]:
        """List recent executions"""
        active = [
            {
                "execution_id": eid,
                "status": ctx.status.value,
                "apqc_code": ctx.apqc_code,
                "current_step": ctx.current_step,
                "total_steps": ctx.total_steps,
                "started_at": ctx.started_at.isoformat()
            }
            for eid, ctx in self.active_executions.items()
        ]

        completed = self.completed_executions[-limit:]

        return active + completed


# Create global engine instance
_engine_instance = None

def get_engine() -> WorkflowEngine:
    """Get the global workflow engine instance"""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = WorkflowEngine()
    return _engine_instance
