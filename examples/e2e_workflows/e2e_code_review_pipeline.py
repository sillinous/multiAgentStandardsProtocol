"""
🔍 E2E Workflow: Automated Code Review Pipeline
================================================

Complete end-to-end demonstration of an automated code review pipeline using:
- ACP: Pipeline Coordination Pattern
- CAP: Code Analysis Protocol
- CAIP: Compliance and Audit Protocol
- CIP: Collective Intelligence for Final Decision
- A2A: Agent Communication
- TAP: Temporal Event Tracking

Scenario:
A code submission goes through a multi-stage review pipeline with static analysis,
compliance checking, collective intelligence decision-making, and full audit trail.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

# Protocol imports
from superstandard.protocols.acp_implementation import (
    CoordinationManager,
    CoordinationType,
    TaskStatus,
    Task,
    Participant,
)

# Simple mock classes for workflow demonstration
@dataclass
class WorkflowNode:
    """Workflow node for demonstration."""
    node_id: str
    node_type: str
    agent_id: str
    task_definition: Dict[str, Any]

@dataclass
class WorkflowEdge:
    """Workflow edge for demonstration."""
    from_node: str
    to_node: str

class CoordinationEngine:
    """Simplified coordination engine for demonstration."""
    def __init__(self):
        self.sessions = {}
        self.workflows = {}

    async def create_session(self, session_id: str, pattern: CoordinationType,
                            participants: List[str], metadata: Dict[str, Any] = None):
        """Create a coordination session."""
        self.sessions[session_id] = {
            "session_id": session_id,
            "pattern": pattern.value if hasattr(pattern, 'value') else str(pattern),
            "participants": participants,
            "metadata": metadata or {},
            "status": "active"
        }

    async def define_workflow(self, session_id: str, nodes: List[WorkflowNode], edges: List[WorkflowEdge]):
        """Define workflow for session."""
        self.workflows[session_id] = {
            "nodes": nodes,
            "edges": edges
        }

CoordinationPattern = CoordinationType
TaskState = TaskStatus
from superstandard.protocols.cip_v1 import (
    CollectiveDecision,
    Vote,
    VotingOption,
    DecisionMethod,
    ConsensusBuilder,
)
from superstandard.protocols.tap_v1 import (
    TemporalEngine,
    TemporalEvent,
    TimeRange,
    TemporalResolution,
    OperationType,
)
from superstandard.agents.base.protocols import A2AMessage, MessageType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Helper Classes
# ============================================================================

class ReviewDecision(Enum):
    """Code review decision options."""
    APPROVE = "approve"
    APPROVE_WITH_SUGGESTIONS = "approve_with_suggestions"
    REQUEST_CHANGES = "request_changes"
    REJECT = "reject"


@dataclass
class CodeSubmission:
    """Code submission for review."""
    submission_id: str
    commit_hash: str
    author: str
    files_changed: List[str]
    lines_added: int
    lines_deleted: int
    description: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class CodeAnalysisResult:
    """Result from code analysis."""
    analyzer_id: str
    analysis_type: str
    passed: bool
    score: float
    issues: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    recommendations: List[str]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class ComplianceCheckResult:
    """Result from compliance checking."""
    checker_id: str
    check_type: str
    compliant: bool
    violations: List[Dict[str, Any]]
    policies_checked: List[str]
    audit_entry: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class ReviewAgent:
    """Agent participating in code review."""
    agent_id: str
    role: str
    expertise: List[str]
    messages: List[A2AMessage] = field(default_factory=list)
    analysis_results: List[Any] = field(default_factory=list)

    async def send_message(self, to_agent: str, message_type: str, content: Dict[str, Any]) -> A2AMessage:
        """Send message."""
        msg = A2AMessage(
            from_agent=self.agent_id,
            to_agent=to_agent,
            message_type=message_type,
            content=content
        )
        logger.info(f"📤 {self.agent_id} → {to_agent}: {message_type}")
        return msg

    async def receive_message(self, message: A2AMessage) -> None:
        """Receive message."""
        self.messages.append(message)
        logger.info(f"📥 {self.agent_id} received: {message.message_type}")


@dataclass
class AuditLog:
    """Audit log for CAIP compliance."""
    log_id: str
    entries: List[Dict[str, Any]] = field(default_factory=list)

    def log_event(
        self,
        event_type: str,
        agent_id: str,
        operation: str,
        details: Dict[str, Any]
    ) -> None:
        """Log an audit event."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "agent_id": agent_id,
            "operation": operation,
            "details": details,
            "entry_id": f"audit_{len(self.entries) + 1}"
        }
        self.entries.append(entry)
        logger.info(f"📝 Audit logged: {event_type} by {agent_id}")

    def generate_report(self) -> Dict[str, Any]:
        """Generate compliance report."""
        return {
            "log_id": self.log_id,
            "total_entries": len(self.entries),
            "entries_by_type": self._count_by_type(),
            "entries_by_agent": self._count_by_agent(),
            "timeline": self.entries,
            "generated_at": datetime.utcnow().isoformat()
        }

    def _count_by_type(self) -> Dict[str, int]:
        """Count entries by type."""
        counts = {}
        for entry in self.entries:
            event_type = entry["event_type"]
            counts[event_type] = counts.get(event_type, 0) + 1
        return counts

    def _count_by_agent(self) -> Dict[str, int]:
        """Count entries by agent."""
        counts = {}
        for entry in self.entries:
            agent_id = entry["agent_id"]
            counts[agent_id] = counts.get(agent_id, 0) + 1
        return counts


# ============================================================================
# Simulated Analysis Functions
# ============================================================================

async def perform_static_analysis(code_submission: CodeSubmission) -> CodeAnalysisResult:
    """Simulate static code analysis (CAP)."""
    logger.info("🔬 Performing static code analysis...")
    await asyncio.sleep(0.1)

    # Simulate analysis
    issues = []
    if code_submission.lines_added > 500:
        issues.append({
            "severity": "medium",
            "type": "code_smell",
            "message": "Large code change, consider breaking into smaller commits",
            "file": code_submission.files_changed[0] if code_submission.files_changed else "unknown"
        })

    passed = len(issues) == 0 or all(i["severity"] != "high" for i in issues)

    return CodeAnalysisResult(
        analyzer_id="static_analyzer_001",
        analysis_type="static_analysis",
        passed=passed,
        score=0.92 if passed else 0.75,
        issues=issues,
        metrics={
            "cyclomatic_complexity": 8,
            "cognitive_complexity": 6,
            "maintainability_index": 78.5,
            "code_coverage": 87.3,
            "duplication_percentage": 3.2
        },
        recommendations=[
            "Add unit tests for new functions",
            "Consider extracting helper methods"
        ]
    )


async def perform_security_scan(code_submission: CodeSubmission) -> CodeAnalysisResult:
    """Simulate security scanning (CAP)."""
    logger.info("🔒 Performing security scan...")
    await asyncio.sleep(0.1)

    issues = []

    return CodeAnalysisResult(
        analyzer_id="security_scanner_001",
        analysis_type="security_scan",
        passed=True,
        score=0.95,
        issues=issues,
        metrics={
            "vulnerabilities_found": 0,
            "high_severity": 0,
            "medium_severity": 0,
            "low_severity": 0
        },
        recommendations=[
            "Security scan passed",
            "No vulnerabilities detected"
        ]
    )


async def perform_quality_check(code_submission: CodeSubmission) -> CodeAnalysisResult:
    """Simulate code quality checking (CAP)."""
    logger.info("✨ Performing quality check...")
    await asyncio.sleep(0.1)

    return CodeAnalysisResult(
        analyzer_id="quality_checker_001",
        analysis_type="quality_check",
        passed=True,
        score=0.88,
        issues=[],
        metrics={
            "code_style_compliance": 95.0,
            "documentation_coverage": 82.0,
            "test_coverage": 87.3,
            "type_safety_score": 92.0
        },
        recommendations=[
            "Increase documentation for complex functions",
            "Add type hints to remaining functions"
        ]
    )


async def check_compliance(
    code_submission: CodeSubmission,
    analysis_results: List[CodeAnalysisResult],
    audit_log: AuditLog
) -> ComplianceCheckResult:
    """Check compliance with policies (CAIP)."""
    logger.info("⚖️ Checking compliance with policies...")
    await asyncio.sleep(0.1)

    violations = []

    # Check minimum code coverage policy
    quality_result = next(
        (r for r in analysis_results if r.analysis_type == "quality_check"),
        None
    )

    if quality_result and quality_result.metrics.get("test_coverage", 0) < 80:
        violations.append({
            "policy": "minimum_test_coverage_80",
            "severity": "medium",
            "message": f"Test coverage {quality_result.metrics['test_coverage']}% below required 80%"
        })

    # Check security vulnerabilities policy
    security_result = next(
        (r for r in analysis_results if r.analysis_type == "security_scan"),
        None
    )

    if security_result and security_result.metrics.get("high_severity", 0) > 0:
        violations.append({
            "policy": "zero_high_severity_vulnerabilities",
            "severity": "high",
            "message": "High severity vulnerabilities detected"
        })

    compliant = len(violations) == 0

    # Log compliance check
    audit_entry = {
        "submission_id": code_submission.submission_id,
        "compliant": compliant,
        "violations_count": len(violations),
        "policies_checked": [
            "minimum_test_coverage_80",
            "zero_high_severity_vulnerabilities",
            "code_style_compliance",
            "license_compliance"
        ]
    }

    audit_log.log_event(
        event_type="compliance_check",
        agent_id="compliance_checker_001",
        operation="check_submission_compliance",
        details=audit_entry
    )

    return ComplianceCheckResult(
        checker_id="compliance_checker_001",
        check_type="policy_compliance",
        compliant=compliant,
        violations=violations,
        policies_checked=audit_entry["policies_checked"],
        audit_entry=audit_entry
    )


# ============================================================================
# Main Workflow
# ============================================================================

async def run_code_review_pipeline():
    """Execute complete code review pipeline workflow."""

    print("\n" + "="*80)
    print("🔍 AUTOMATED CODE REVIEW PIPELINE - E2E WORKFLOW")
    print("="*80 + "\n")

    # ========================================================================
    # PHASE 1: Initialize Systems
    # ========================================================================

    print("\n" + "-"*80)
    print("PHASE 1: Initialize Review Pipeline Systems")
    print("-"*80 + "\n")

    coordinator = CoordinationEngine()
    temporal_engine = TemporalEngine(
        timeline_id="code_review_timeline",
        resolution=TemporalResolution.MILLISECOND
    )
    audit_log = AuditLog(log_id="code_review_audit_001")

    logger.info("✓ Coordination engine initialized (ACP)")
    logger.info("✓ Temporal engine initialized (TAP)")
    logger.info("✓ Audit log initialized (CAIP)")

    # ========================================================================
    # PHASE 2: Create Code Submission
    # ========================================================================

    print("\n" + "-"*80)
    print("PHASE 2: Code Submission")
    print("-"*80 + "\n")

    submission = CodeSubmission(
        submission_id="PR-12345",
        commit_hash="abc123def456",
        author="developer@company.com",
        files_changed=[
            "src/services/payment_processor.py",
            "src/models/transaction.py",
            "tests/test_payment_processor.py"
        ],
        lines_added=245,
        lines_deleted=87,
        description="Add support for international payment processing"
    )

    # Log submission
    audit_log.log_event(
        event_type="submission_received",
        agent_id="system",
        operation="code_submission",
        details={
            "submission_id": submission.submission_id,
            "author": submission.author,
            "files_changed": len(submission.files_changed),
            "lines_added": submission.lines_added,
            "lines_deleted": submission.lines_deleted
        }
    )

    # Record temporal event
    await temporal_engine.record_event(TemporalEvent(
        event_id="evt_submission",
        timestamp=datetime.utcnow().isoformat(),
        agent_id="system",
        operation_type=OperationType.STATE_CHANGE.value,
        operation_data={"action": "code_submitted", "submission_id": submission.submission_id},
        state_snapshot={"status": "submitted"}
    ))

    logger.info(f"✓ Code submission received: {submission.submission_id}")
    logger.info(f"  Files changed: {len(submission.files_changed)}")
    logger.info(f"  Lines: +{submission.lines_added} -{submission.lines_deleted}")

    # ========================================================================
    # PHASE 3: Create Review Team (ACP)
    # ========================================================================

    print("\n" + "-"*80)
    print("PHASE 3: Assemble Review Team")
    print("-"*80 + "\n")

    # Create review agents
    review_agents = {
        "static_analyzer": ReviewAgent(
            agent_id="static_analyzer_001",
            role="Static Code Analyzer",
            expertise=["code_quality", "complexity_analysis", "best_practices"]
        ),
        "security_scanner": ReviewAgent(
            agent_id="security_scanner_001",
            role="Security Scanner",
            expertise=["vulnerability_detection", "security_patterns", "owasp"]
        ),
        "quality_checker": ReviewAgent(
            agent_id="quality_checker_001",
            role="Quality Checker",
            expertise=["code_style", "documentation", "testing"]
        ),
        "compliance_checker": ReviewAgent(
            agent_id="compliance_checker_001",
            role="Compliance Checker",
            expertise=["policy_enforcement", "regulatory_compliance"]
        ),
        "senior_reviewer_1": ReviewAgent(
            agent_id="senior_reviewer_001",
            role="Senior Code Reviewer",
            expertise=["architecture", "design_patterns", "performance"]
        ),
        "senior_reviewer_2": ReviewAgent(
            agent_id="senior_reviewer_002",
            role="Senior Code Reviewer",
            expertise=["api_design", "maintainability", "scalability"]
        )
    }

    # Create coordination session with pipeline pattern
    session_id = "code_review_session_PR12345"

    await coordinator.create_session(
        session_id=session_id,
        pattern=CoordinationPattern.PIPELINE,
        participants=[agent.agent_id for agent in review_agents.values()],
        metadata={
            "submission_id": submission.submission_id,
            "review_type": "automated_pipeline",
            "deadline": (datetime.utcnow() + timedelta(hours=2)).isoformat()
        }
    )

    logger.info(f"✓ Review team assembled: {len(review_agents)} agents")
    logger.info(f"✓ Coordination session created: {session_id}")

    # Define pipeline workflow
    workflow_nodes = [
        WorkflowNode(
            node_id="static_analysis",
            node_type="task",
            agent_id=review_agents["static_analyzer"].agent_id,
            task_definition={"analysis_type": "static_analysis"}
        ),
        WorkflowNode(
            node_id="security_scan",
            node_type="task",
            agent_id=review_agents["security_scanner"].agent_id,
            task_definition={"analysis_type": "security_scan"}
        ),
        WorkflowNode(
            node_id="quality_check",
            node_type="task",
            agent_id=review_agents["quality_checker"].agent_id,
            task_definition={"analysis_type": "quality_check"}
        ),
        WorkflowNode(
            node_id="compliance_check",
            node_type="task",
            agent_id=review_agents["compliance_checker"].agent_id,
            task_definition={"analysis_type": "compliance"}
        ),
        WorkflowNode(
            node_id="collective_decision",
            node_type="task",
            agent_id="coordinator",
            task_definition={"analysis_type": "collective_review"}
        )
    ]

    workflow_edges = [
        WorkflowEdge(from_node="static_analysis", to_node="compliance_check"),
        WorkflowEdge(from_node="security_scan", to_node="compliance_check"),
        WorkflowEdge(from_node="quality_check", to_node="compliance_check"),
        WorkflowEdge(from_node="compliance_check", to_node="collective_decision"),
    ]

    await coordinator.define_workflow(
        session_id=session_id,
        nodes=workflow_nodes,
        edges=workflow_edges
    )

    logger.info(f"✓ Pipeline workflow defined: {len(workflow_nodes)} stages")

    # ========================================================================
    # PHASE 4: Execute Automated Analysis (CAP + A2A + TAP)
    # ========================================================================

    print("\n" + "-"*80)
    print("PHASE 4: Execute Automated Code Analysis")
    print("-"*80 + "\n")

    analysis_results = []

    # Stage 1: Static Analysis
    start_time = datetime.utcnow()
    await temporal_engine.record_event(TemporalEvent(
        event_id="evt_static_start",
        timestamp=start_time.isoformat(),
        agent_id=review_agents["static_analyzer"].agent_id,
        operation_type=OperationType.STATE_CHANGE.value,
        operation_data={"action": "analysis_started", "type": "static"},
        state_snapshot={"status": "analyzing"}
    ))

    static_result = await perform_static_analysis(submission)
    analysis_results.append(static_result)
    review_agents["static_analyzer"].analysis_results.append(static_result)

    audit_log.log_event(
        event_type="analysis_completed",
        agent_id=static_result.analyzer_id,
        operation="static_analysis",
        details={
            "passed": static_result.passed,
            "score": static_result.score,
            "issues_count": len(static_result.issues)
        }
    )

    await temporal_engine.record_event(TemporalEvent(
        event_id="evt_static_complete",
        timestamp=datetime.utcnow().isoformat(),
        agent_id=review_agents["static_analyzer"].agent_id,
        operation_type=OperationType.STATE_CHANGE.value,
        operation_data={"action": "analysis_completed", "result": "passed" if static_result.passed else "failed"},
        state_snapshot={"status": "completed", "score": static_result.score}
    ))

    logger.info(f"✓ Static analysis: {'PASSED' if static_result.passed else 'FAILED'} (Score: {static_result.score:.2f})")

    # Stage 2: Security Scan
    await temporal_engine.record_event(TemporalEvent(
        event_id="evt_security_start",
        timestamp=datetime.utcnow().isoformat(),
        agent_id=review_agents["security_scanner"].agent_id,
        operation_type=OperationType.STATE_CHANGE.value,
        operation_data={"action": "scan_started"},
        state_snapshot={"status": "scanning"}
    ))

    security_result = await perform_security_scan(submission)
    analysis_results.append(security_result)
    review_agents["security_scanner"].analysis_results.append(security_result)

    audit_log.log_event(
        event_type="analysis_completed",
        agent_id=security_result.analyzer_id,
        operation="security_scan",
        details={
            "passed": security_result.passed,
            "vulnerabilities": security_result.metrics["vulnerabilities_found"]
        }
    )

    await temporal_engine.record_event(TemporalEvent(
        event_id="evt_security_complete",
        timestamp=datetime.utcnow().isoformat(),
        agent_id=review_agents["security_scanner"].agent_id,
        operation_type=OperationType.STATE_CHANGE.value,
        operation_data={"action": "scan_completed"},
        state_snapshot={"status": "completed", "vulnerabilities": 0}
    ))

    logger.info(f"✓ Security scan: {'PASSED' if security_result.passed else 'FAILED'} (Score: {security_result.score:.2f})")

    # Stage 3: Quality Check
    quality_result = await perform_quality_check(submission)
    analysis_results.append(quality_result)
    review_agents["quality_checker"].analysis_results.append(quality_result)

    audit_log.log_event(
        event_type="analysis_completed",
        agent_id=quality_result.analyzer_id,
        operation="quality_check",
        details={
            "passed": quality_result.passed,
            "test_coverage": quality_result.metrics["test_coverage"]
        }
    )

    logger.info(f"✓ Quality check: {'PASSED' if quality_result.passed else 'FAILED'} (Score: {quality_result.score:.2f})")

    # ========================================================================
    # PHASE 5: Compliance Checking (CAIP)
    # ========================================================================

    print("\n" + "-"*80)
    print("PHASE 5: Compliance Policy Checking")
    print("-"*80 + "\n")

    compliance_result = await check_compliance(submission, analysis_results, audit_log)

    logger.info(f"✓ Compliance check: {'COMPLIANT' if compliance_result.compliant else 'NON-COMPLIANT'}")
    if compliance_result.violations:
        logger.info(f"  Violations: {len(compliance_result.violations)}")
        for violation in compliance_result.violations:
            logger.info(f"    - {violation['policy']}: {violation['message']}")

    # ========================================================================
    # PHASE 6: Collective Intelligence Decision (CIP + A2A)
    # ========================================================================

    print("\n" + "-"*80)
    print("PHASE 6: Collective Intelligence Review Decision")
    print("-"*80 + "\n")

    # Define voting options
    voting_options = [
        VotingOption(
            option_id=ReviewDecision.APPROVE.value,
            option_value="Approve - Code meets all standards",
            metadata={"action": "merge"}
        ),
        VotingOption(
            option_id=ReviewDecision.APPROVE_WITH_SUGGESTIONS.value,
            option_value="Approve with suggestions for improvement",
            metadata={"action": "merge_with_notes"}
        ),
        VotingOption(
            option_id=ReviewDecision.REQUEST_CHANGES.value,
            option_value="Request changes before approval",
            metadata={"action": "request_revision"}
        ),
        VotingOption(
            option_id=ReviewDecision.REJECT.value,
            option_value="Reject - Significant issues found",
            metadata={"action": "reject"}
        )
    ]

    # Create collective decision
    collective_decision = CollectiveDecision(
        decision_id=f"review_decision_{submission.submission_id}",
        options=voting_options,
        method=DecisionMethod.WEIGHTED_VOTING
    )

    # Senior reviewers vote (A2A communication)
    senior_reviewers = [
        review_agents["senior_reviewer_1"],
        review_agents["senior_reviewer_2"]
    ]

    # Calculate votes based on analysis results
    overall_score = sum(r.score for r in analysis_results) / len(analysis_results)
    all_passed = all(r.passed for r in analysis_results)
    compliant = compliance_result.compliant

    # Senior reviewer 1 votes
    if all_passed and compliant and overall_score > 0.90:
        vote_option = ReviewDecision.APPROVE.value
    elif all_passed and overall_score > 0.85:
        vote_option = ReviewDecision.APPROVE_WITH_SUGGESTIONS.value
    else:
        vote_option = ReviewDecision.REQUEST_CHANGES.value

    vote1 = Vote(
        agent_id=senior_reviewers[0].agent_id,
        option_id=vote_option,
        vote_value=1.0,
        confidence=0.85,
        reasoning=f"Overall quality score: {overall_score:.2f}. All automated checks passed."
    )
    collective_decision.add_vote(vote1)

    # Send vote via A2A
    vote_msg1 = await senior_reviewers[0].send_message(
        to_agent="coordinator",
        message_type="vote_cast",
        content={
            "decision_id": collective_decision.decision_id,
            "vote": vote_option,
            "confidence": 0.85
        }
    )

    # Senior reviewer 2 votes
    vote2 = Vote(
        agent_id=senior_reviewers[1].agent_id,
        option_id=vote_option,
        vote_value=1.0,
        confidence=0.88,
        reasoning=f"Code quality is good. Recommendations for improvement noted."
    )
    collective_decision.add_vote(vote2)

    vote_msg2 = await senior_reviewers[1].send_message(
        to_agent="coordinator",
        message_type="vote_cast",
        content={
            "decision_id": collective_decision.decision_id,
            "vote": vote_option,
            "confidence": 0.88
        }
    )

    # Calculate collective decision
    decision_result = collective_decision.calculate_result()

    logger.info(f"✓ Collective decision reached: {decision_result.winning_option.upper()}")
    logger.info(f"  Confidence: {decision_result.confidence:.2f}")
    logger.info(f"  Consensus level: {decision_result.consensus_level:.2f}")

    # Log decision
    audit_log.log_event(
        event_type="review_decision",
        agent_id="collective_intelligence",
        operation="final_review_decision",
        details={
            "submission_id": submission.submission_id,
            "decision": decision_result.winning_option,
            "confidence": decision_result.confidence,
            "votes": len(decision_result.vote_distribution)
        }
    )

    # ========================================================================
    # PHASE 7: Generate Audit Trail (CAIP + TAP)
    # ========================================================================

    print("\n" + "-"*80)
    print("PHASE 7: Generate Complete Audit Trail")
    print("-"*80 + "\n")

    # Generate compliance report
    compliance_report = audit_log.generate_report()

    logger.info(f"✓ Audit report generated:")
    logger.info(f"  Total audit entries: {compliance_report['total_entries']}")
    logger.info(f"  Events by type: {compliance_report['entries_by_type']}")

    # Query temporal timeline
    time_range = TimeRange(
        start_time=start_time.isoformat(),
        end_time=datetime.utcnow().isoformat()
    )

    temporal_events = await temporal_engine.query_events(time_range=time_range)

    logger.info(f"✓ Temporal timeline captured: {len(temporal_events)} events")

    # ========================================================================
    # PHASE 8: Final Results Summary
    # ========================================================================

    print("\n" + "="*80)
    print("CODE REVIEW PIPELINE RESULTS")
    print("="*80 + "\n")

    print(f"Submission: {submission.submission_id}")
    print(f"  Author: {submission.author}")
    print(f"  Files: {len(submission.files_changed)}")
    print(f"  Changes: +{submission.lines_added} -{submission.lines_deleted}")

    print("\nAutomated Analysis Results:")
    for result in analysis_results:
        status = "✓ PASSED" if result.passed else "✗ FAILED"
        print(f"  {result.analysis_type}: {status} (Score: {result.score:.2f})")

    print(f"\nCompliance: {'✓ COMPLIANT' if compliance_result.compliant else '✗ NON-COMPLIANT'}")
    print(f"  Policies checked: {len(compliance_result.policies_checked)}")
    print(f"  Violations: {len(compliance_result.violations)}")

    print(f"\nCollective Decision: {decision_result.winning_option.upper()}")
    print(f"  Confidence: {decision_result.confidence:.2%}")
    print(f"  Consensus: {decision_result.consensus_level:.2%}")

    print("\nRecommendations:")
    for result in analysis_results:
        for rec in result.recommendations:
            print(f"  • {rec}")

    print("\nAudit Trail:")
    print(f"  ✓ {compliance_report['total_entries']} audit entries")
    print(f"  ✓ {len(temporal_events)} temporal events")
    print(f"  ✓ Complete compliance report generated")

    print("\nProtocol Integration:")
    print(f"  ✓ ACP: Pipeline coordination with {len(workflow_nodes)} stages")
    print(f"  ✓ CAP: {len(analysis_results)} code analysis operations")
    print(f"  ✓ CAIP: {len(compliance_result.policies_checked)} compliance checks")
    print(f"  ✓ CIP: Collective decision with {len(decision_result.vote_distribution)} votes")
    print(f"  ✓ A2A: Review team communication")
    print(f"  ✓ TAP: {len(temporal_events)} temporal events tracked")

    print("\n" + "="*80)
    print("✅ CODE REVIEW PIPELINE COMPLETED SUCCESSFULLY")
    print("="*80 + "\n")

    return {
        "submission_id": submission.submission_id,
        "decision": decision_result.winning_option,
        "confidence": decision_result.confidence,
        "analysis_results": len(analysis_results),
        "audit_entries": compliance_report['total_entries'],
        "temporal_events": len(temporal_events)
    }


# ============================================================================
# Main Entry Point
# ============================================================================

async def main():
    """Main entry point."""
    try:
        result = await run_code_review_pipeline()
        print(f"\n✅ Code review pipeline completed!")
        print(f"Decision: {result['decision']}")
        print(f"Confidence: {result['confidence']:.2%}")
    except Exception as e:
        logger.error(f"❌ Pipeline failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
