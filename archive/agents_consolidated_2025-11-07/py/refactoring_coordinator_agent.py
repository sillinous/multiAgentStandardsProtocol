"""
Refactoring Coordinator Agent
APQC Process Classification Framework: 11.1.2 - Manage Software Development

Specialized agent for prioritizing, scheduling, and coordinating technical debt remediation
and refactoring activities aligned with enterprise development processes.
"""

import asyncio
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple, Union
from enum import Enum
from dataclasses import dataclass, asdict, field
from pathlib import Path
import heapq
from collections import defaultdict

from .technical_debt_tracking_agent import (
    TechnicalDebtItem,
    TechnicalDebtSeverity,
    TechnicalDebtCategory,
)
from .architecture_review_agent import ArchitecturalViolation, ArchitecturalViolationType

logger = logging.getLogger(__name__)


class RefactoringPriority(Enum):
    """Refactoring priority levels following APQC development process prioritization"""

    CRITICAL = "critical"  # Immediate action required (security, production blockers)
    HIGH = "high"  # Next sprint planning cycle
    MEDIUM = "medium"  # Planned refactoring initiatives
    LOW = "low"  # Continuous improvement backlog
    DEFERRED = "deferred"  # Future consideration


class RefactoringComplexity(Enum):
    """Complexity assessment for refactoring efforts"""

    TRIVIAL = "trivial"  # < 2 hours, single file
    SIMPLE = "simple"  # 2-8 hours, few files
    MODERATE = "moderate"  # 1-3 days, multiple components
    COMPLEX = "complex"  # 1-2 weeks, architectural changes
    EPIC = "epic"  # > 2 weeks, major refactoring


class RefactoringImpact(Enum):
    """Impact assessment following APQC risk classification"""

    MINIMAL = "minimal"  # Isolated changes, low risk
    MODERATE = "moderate"  # Some dependency changes, medium risk
    SIGNIFICANT = "significant"  # Cross-component changes, high risk
    MAJOR = "major"  # Architectural changes, very high risk


@dataclass
class RefactoringDependency:
    """Dependency relationship between refactoring tasks"""

    task_id: str
    dependency_id: str
    dependency_type: str  # blocks, requires, enhances
    description: str


@dataclass
class RefactoringTask:
    """Individual refactoring task with comprehensive planning details"""

    id: str
    title: str
    description: str
    priority: RefactoringPriority
    complexity: RefactoringComplexity
    impact: RefactoringImpact

    # Source references
    debt_items: List[str]  # Related technical debt item IDs
    architectural_violations: List[str]  # Related architectural violation IDs

    # Effort estimation
    estimated_hours: float
    confidence_level: float  # 0.0 - 1.0
    complexity_factors: List[str]

    # Business context
    business_value: str
    business_justification: str
    risk_assessment: str
    success_criteria: List[str]

    # Implementation details
    affected_files: List[str]
    test_requirements: List[str]
    documentation_updates: List[str]
    deployment_considerations: List[str]

    # Scheduling
    target_start_date: Optional[datetime]
    target_completion_date: Optional[datetime]
    assigned_to: Optional[str]
    team: Optional[str]
    sprint: Optional[str]

    # Dependencies and relationships
    dependencies: List[RefactoringDependency] = field(default_factory=list)
    blocks: List[str] = field(default_factory=list)  # Task IDs this task blocks

    # Progress tracking
    status: str = "planned"  # planned, in_progress, testing, completed, cancelled
    progress_percentage: float = 0.0
    actual_hours: float = 0.0
    completion_date: Optional[datetime] = None

    # Quality assurance
    code_review_required: bool = True
    testing_requirements: List[str] = field(default_factory=list)
    rollback_plan: str = ""

    # Metadata
    created_date: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    apqc_process_reference: str = "11.1.2"

    # Tags and categorization
    tags: List[str] = field(default_factory=list)
    technical_context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RefactoringInitiative:
    """Collection of related refactoring tasks forming a cohesive initiative"""

    id: str
    name: str
    description: str
    objective: str
    tasks: List[str]  # Task IDs
    total_estimated_hours: float
    target_completion_date: datetime
    initiative_lead: str
    stakeholders: List[str]
    success_metrics: List[str]
    status: str = "planned"
    progress_percentage: float = 0.0


class RefactoringCoordinatorAgent:
    """
    Enterprise-grade refactoring coordination agent

    Implements APQC Process 11.1.2 - Manage Software Development
    Provides systematic prioritization, planning, and coordination of refactoring efforts
    """

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.refactoring_tasks: Dict[str, RefactoringTask] = {}
        self.initiatives: Dict[str, RefactoringInitiative] = {}
        self.priority_queue = []  # Heap-based priority queue
        self.scheduling_constraints = self._initialize_scheduling_constraints()
        self.business_priorities = self._initialize_business_priorities()
        self.team_capacity = self._initialize_team_capacity()

    def _initialize_scheduling_constraints(self) -> Dict[str, Any]:
        """Initialize scheduling constraints and rules"""
        return {
            "max_concurrent_tasks": 3,
            "max_epic_tasks_per_sprint": 1,
            "min_team_capacity_percentage": 70,  # Reserve 30% for feature development
            "critical_task_sla": timedelta(days=1),
            "high_task_sla": timedelta(days=7),
            "sprint_duration": timedelta(weeks=2),
            "planning_buffer": timedelta(days=2),
            "code_freeze_periods": [],  # List of (start, end) datetime tuples
            "holiday_calendar": [],  # List of holiday dates
        }

    def _initialize_business_priorities(self) -> Dict[str, float]:
        """Initialize business priority weights for different categories"""
        return {
            "security": 1.0,
            "performance": 0.8,
            "maintainability": 0.6,
            "architecture": 0.7,
            "compliance": 0.9,
            "scalability": 0.8,
            "usability": 0.5,
            "documentation": 0.4,
        }

    def _initialize_team_capacity(self) -> Dict[str, Dict]:
        """Initialize team capacity and skills matrix"""
        return {
            "backend_team": {
                "capacity_hours_per_sprint": 120,
                "current_allocation": 0.0,
                "skills": ["python", "architecture", "database", "api"],
                "availability": 1.0,
            },
            "frontend_team": {
                "capacity_hours_per_sprint": 80,
                "current_allocation": 0.0,
                "skills": ["javascript", "react", "ui", "css"],
                "availability": 1.0,
            },
            "devops_team": {
                "capacity_hours_per_sprint": 40,
                "current_allocation": 0.0,
                "skills": ["infrastructure", "deployment", "monitoring"],
                "availability": 1.0,
            },
            "qa_team": {
                "capacity_hours_per_sprint": 60,
                "current_allocation": 0.0,
                "skills": ["testing", "automation", "quality"],
                "availability": 1.0,
            },
        }

    async def analyze_and_prioritize_debt(
        self,
        debt_items: List[TechnicalDebtItem],
        architectural_violations: List[ArchitecturalViolation],
    ) -> Dict[str, Any]:
        """
        Analyze technical debt and architectural violations to create prioritized refactoring plan

        Args:
            debt_items: List of technical debt items
            architectural_violations: List of architectural violations

        Returns:
            Comprehensive refactoring plan with prioritized tasks
        """
        logger.info("🎯 Starting technical debt analysis and refactoring prioritization...")

        # Clear existing tasks to start fresh
        self.refactoring_tasks.clear()
        self.priority_queue.clear()

        # Step 1: Create refactoring tasks from debt items
        debt_tasks = await self._create_tasks_from_debt_items(debt_items)

        # Step 2: Create refactoring tasks from architectural violations
        architecture_tasks = await self._create_tasks_from_violations(architectural_violations)

        # Step 3: Identify consolidation opportunities
        consolidated_tasks = await self._consolidate_related_tasks(debt_tasks + architecture_tasks)

        # Step 4: Calculate comprehensive priority scores
        await self._calculate_priority_scores(consolidated_tasks)

        # Step 5: Analyze dependencies and constraints
        await self._analyze_task_dependencies(consolidated_tasks)

        # Step 6: Create scheduling plan
        scheduling_plan = await self._create_scheduling_plan()

        # Step 7: Generate initiatives
        initiatives = await self._generate_initiatives()

        # Step 8: Create comprehensive report
        analysis_report = {
            "analysis_timestamp": datetime.now().isoformat(),
            "summary": await self._generate_summary(),
            "prioritized_tasks": [
                asdict(task)
                for task in sorted(
                    self.refactoring_tasks.values(),
                    key=lambda t: self._get_priority_score(t),
                    reverse=True,
                )
            ],
            "scheduling_plan": scheduling_plan,
            "initiatives": [asdict(initiative) for initiative in self.initiatives.values()],
            "resource_allocation": await self._analyze_resource_allocation(),
            "risk_assessment": await self._assess_refactoring_risks(),
            "recommendations": await self._generate_recommendations(),
            "metrics": await self._calculate_planning_metrics(),
        }

        logger.info(
            f"✅ Refactoring analysis completed: {len(consolidated_tasks)} tasks prioritized"
        )

        return analysis_report

    async def _create_tasks_from_debt_items(
        self, debt_items: List[TechnicalDebtItem]
    ) -> List[RefactoringTask]:
        """Create refactoring tasks from technical debt items"""
        tasks = []

        for debt_item in debt_items:
            task = RefactoringTask(
                id=f"debt_{debt_item.id}",
                title=f"Resolve: {debt_item.title}",
                description=debt_item.description,
                priority=self._map_debt_severity_to_priority(debt_item.severity),
                complexity=self._estimate_debt_complexity(debt_item),
                impact=self._assess_debt_impact(debt_item),
                debt_items=[debt_item.id],
                architectural_violations=[],
                estimated_hours=self._parse_effort_estimation(debt_item.remediation_effort),
                confidence_level=self._calculate_confidence_level(debt_item),
                complexity_factors=self._identify_complexity_factors(debt_item),
                business_value=debt_item.business_impact,
                business_justification=debt_item.business_impact,
                risk_assessment=debt_item.security_implications,
                success_criteria=self._generate_success_criteria(debt_item),
                affected_files=[debt_item.file_path],
                test_requirements=self._determine_test_requirements(debt_item),
                documentation_updates=self._identify_documentation_updates(debt_item),
                deployment_considerations=self._assess_deployment_considerations(debt_item),
                tags=debt_item.tags + [debt_item.category.value],
                technical_context=debt_item.technical_context,
                apqc_process_reference=debt_item.apqc_process_reference,
            )

            tasks.append(task)

        return tasks

    async def _create_tasks_from_violations(
        self, violations: List[ArchitecturalViolation]
    ) -> List[RefactoringTask]:
        """Create refactoring tasks from architectural violations"""
        tasks = []

        for violation in violations:
            task = RefactoringTask(
                id=f"arch_{violation.id}",
                title=f"Fix: {violation.title}",
                description=violation.description,
                priority=self._map_violation_severity_to_priority(violation.severity),
                complexity=self._estimate_violation_complexity(violation),
                impact=self._assess_violation_impact(violation),
                debt_items=[],
                architectural_violations=[violation.id],
                estimated_hours=self._parse_effort_estimation(violation.effort_estimation),
                confidence_level=0.7,  # Default confidence for architectural tasks
                complexity_factors=self._identify_violation_complexity_factors(violation),
                business_value=violation.business_justification,
                business_justification=violation.business_justification,
                risk_assessment=violation.impact_assessment,
                success_criteria=self._generate_violation_success_criteria(violation),
                affected_files=violation.affected_components,
                test_requirements=self._determine_violation_test_requirements(violation),
                documentation_updates=["Architecture documentation update"],
                deployment_considerations=self._assess_violation_deployment_considerations(
                    violation
                ),
                tags=[violation.violation_type.value, "architecture"],
                technical_context=violation.violation_details,
                apqc_process_reference=violation.apqc_process_reference,
            )

            tasks.append(task)

        return tasks

    async def _consolidate_related_tasks(
        self, tasks: List[RefactoringTask]
    ) -> List[RefactoringTask]:
        """Identify and consolidate related refactoring tasks"""
        consolidated_tasks = []
        task_groups = defaultdict(list)

        # Group tasks by file and similarity
        for task in tasks:
            # Group by primary affected file
            primary_file = task.affected_files[0] if task.affected_files else "unknown"
            task_groups[primary_file].append(task)

        for file_path, file_tasks in task_groups.items():
            if len(file_tasks) > 1:
                # Create consolidated task for multiple issues in same file
                consolidated_task = await self._merge_tasks(file_tasks, file_path)
                consolidated_tasks.append(consolidated_task)

                # Store original tasks for reference
                for task in file_tasks:
                    self.refactoring_tasks[task.id] = task
            else:
                # Single task for this file
                task = file_tasks[0]
                consolidated_tasks.append(task)
                self.refactoring_tasks[task.id] = task

        return consolidated_tasks

    async def _merge_tasks(self, tasks: List[RefactoringTask], file_path: str) -> RefactoringTask:
        """Merge multiple related tasks into a consolidated refactoring task"""
        # Use the highest priority task as the base
        base_task = max(tasks, key=lambda t: self._get_priority_numeric_value(t.priority))

        merged_task = RefactoringTask(
            id=f"consolidated_{hash(file_path + str(len(tasks)))}",
            title=f"Comprehensive refactoring: {Path(file_path).name}",
            description=f"Consolidated refactoring addressing {len(tasks)} issues in {file_path}",
            priority=base_task.priority,
            complexity=self._calculate_merged_complexity(tasks),
            impact=self._calculate_merged_impact(tasks),
            debt_items=[item for task in tasks for item in task.debt_items],
            architectural_violations=[
                violation for task in tasks for violation in task.architectural_violations
            ],
            estimated_hours=sum(task.estimated_hours for task in tasks)
            * 0.8,  # 20% efficiency gain
            confidence_level=min(task.confidence_level for task in tasks),
            complexity_factors=list(
                set(factor for task in tasks for factor in task.complexity_factors)
            ),
            business_value=f"Combined business value from {len(tasks)} improvements",
            business_justification=base_task.business_justification,
            risk_assessment=self._consolidate_risk_assessments(tasks),
            success_criteria=[criterion for task in tasks for criterion in task.success_criteria],
            affected_files=list(set(file for task in tasks for file in task.affected_files)),
            test_requirements=list(set(req for task in tasks for req in task.test_requirements)),
            documentation_updates=list(
                set(update for task in tasks for update in task.documentation_updates)
            ),
            deployment_considerations=list(
                set(
                    consideration
                    for task in tasks
                    for consideration in task.deployment_considerations
                )
            ),
            tags=list(set(tag for task in tasks for tag in task.tags)) + ["consolidated"],
            technical_context={"merged_from": [task.id for task in tasks]},
        )

        return merged_task

    def _map_debt_severity_to_priority(
        self, severity: TechnicalDebtSeverity
    ) -> RefactoringPriority:
        """Map technical debt severity to refactoring priority"""
        mapping = {
            TechnicalDebtSeverity.CRITICAL: RefactoringPriority.CRITICAL,
            TechnicalDebtSeverity.HIGH: RefactoringPriority.HIGH,
            TechnicalDebtSeverity.MEDIUM: RefactoringPriority.MEDIUM,
            TechnicalDebtSeverity.LOW: RefactoringPriority.LOW,
        }
        return mapping.get(severity, RefactoringPriority.MEDIUM)

    def _map_violation_severity_to_priority(self, severity: str) -> RefactoringPriority:
        """Map architectural violation severity to refactoring priority"""
        mapping = {
            "critical": RefactoringPriority.CRITICAL,
            "high": RefactoringPriority.HIGH,
            "medium": RefactoringPriority.MEDIUM,
            "low": RefactoringPriority.LOW,
        }
        return mapping.get(severity, RefactoringPriority.MEDIUM)

    def _estimate_debt_complexity(self, debt_item: TechnicalDebtItem) -> RefactoringComplexity:
        """Estimate complexity for technical debt resolution"""
        effort_hours = self._parse_effort_estimation(debt_item.remediation_effort)

        if effort_hours <= 2:
            return RefactoringComplexity.TRIVIAL
        elif effort_hours <= 8:
            return RefactoringComplexity.SIMPLE
        elif effort_hours <= 24:
            return RefactoringComplexity.MODERATE
        elif effort_hours <= 80:
            return RefactoringComplexity.COMPLEX
        else:
            return RefactoringComplexity.EPIC

    def _estimate_violation_complexity(
        self, violation: ArchitecturalViolation
    ) -> RefactoringComplexity:
        """Estimate complexity for architectural violation resolution"""
        effort_hours = self._parse_effort_estimation(violation.effort_estimation)

        # Architectural violations tend to be more complex
        if effort_hours <= 4:
            return RefactoringComplexity.SIMPLE
        elif effort_hours <= 16:
            return RefactoringComplexity.MODERATE
        elif effort_hours <= 40:
            return RefactoringComplexity.COMPLEX
        else:
            return RefactoringComplexity.EPIC

    def _assess_debt_impact(self, debt_item: TechnicalDebtItem) -> RefactoringImpact:
        """Assess impact of technical debt resolution"""
        if debt_item.category in [
            TechnicalDebtCategory.SECURITY,
            TechnicalDebtCategory.ARCHITECTURE,
        ]:
            return RefactoringImpact.SIGNIFICANT
        elif debt_item.category in [
            TechnicalDebtCategory.PERFORMANCE,
            TechnicalDebtCategory.CONFIGURATION,
        ]:
            return RefactoringImpact.MODERATE
        else:
            return RefactoringImpact.MINIMAL

    def _assess_violation_impact(self, violation: ArchitecturalViolation) -> RefactoringImpact:
        """Assess impact of architectural violation resolution"""
        if violation.violation_type in [
            ArchitecturalViolationType.CIRCULAR_DEPENDENCY,
            ArchitecturalViolationType.LAYERING_VIOLATION,
        ]:
            return RefactoringImpact.SIGNIFICANT
        elif violation.violation_type in [
            ArchitecturalViolationType.TIGHT_COUPLING,
            ArchitecturalViolationType.SINGLE_RESPONSIBILITY,
        ]:
            return RefactoringImpact.MODERATE
        else:
            return RefactoringImpact.MINIMAL

    def _parse_effort_estimation(self, effort_str: str) -> float:
        """Parse effort estimation string to hours"""
        import re

        # Extract numbers from effort estimation
        numbers = re.findall(r"\d+", effort_str.lower())
        if not numbers:
            return 4.0  # Default

        base_hours = float(numbers[0])

        if "week" in effort_str.lower():
            return base_hours * 40  # 40 hours per week
        elif "day" in effort_str.lower():
            return base_hours * 8  # 8 hours per day
        else:
            return base_hours  # Assume hours

    def _calculate_confidence_level(self, debt_item: TechnicalDebtItem) -> float:
        """Calculate confidence level for effort estimation"""
        # Base confidence
        confidence = 0.7

        # Adjust based on category familiarity
        if debt_item.category in [
            TechnicalDebtCategory.CODE_QUALITY,
            TechnicalDebtCategory.DOCUMENTATION,
        ]:
            confidence += 0.2
        elif debt_item.category in [
            TechnicalDebtCategory.ARCHITECTURE,
            TechnicalDebtCategory.SECURITY,
        ]:
            confidence -= 0.1

        return min(1.0, max(0.3, confidence))

    def _identify_complexity_factors(self, debt_item: TechnicalDebtItem) -> List[str]:
        """Identify factors that contribute to task complexity"""
        factors = []

        if debt_item.category == TechnicalDebtCategory.SECURITY:
            factors.append("security_testing_required")
        if debt_item.category == TechnicalDebtCategory.PERFORMANCE:
            factors.append("performance_testing_required")
        if debt_item.category == TechnicalDebtCategory.ARCHITECTURE:
            factors.append("cross_component_impact")
        if len(debt_item.dependencies) > 0:
            factors.append("external_dependencies")
        if debt_item.severity in [TechnicalDebtSeverity.CRITICAL, TechnicalDebtSeverity.HIGH]:
            factors.append("high_risk_changes")

        return factors

    def _identify_violation_complexity_factors(
        self, violation: ArchitecturalViolation
    ) -> List[str]:
        """Identify complexity factors for architectural violations"""
        factors = []

        if len(violation.affected_components) > 1:
            factors.append("multiple_components")
        if violation.violation_type == ArchitecturalViolationType.CIRCULAR_DEPENDENCY:
            factors.append("dependency_restructuring")
        if violation.violation_type == ArchitecturalViolationType.LAYERING_VIOLATION:
            factors.append("architectural_refactoring")
        if violation.severity in ["critical", "high"]:
            factors.append("high_priority_fix")

        return factors

    def _generate_success_criteria(self, debt_item: TechnicalDebtItem) -> List[str]:
        """Generate success criteria for debt resolution"""
        criteria = [
            f"Technical debt item {debt_item.id} resolved",
            "Code quality metrics improved",
            "No regression in existing functionality",
        ]

        if debt_item.category == TechnicalDebtCategory.SECURITY:
            criteria.append("Security vulnerability eliminated")
        if debt_item.category == TechnicalDebtCategory.PERFORMANCE:
            criteria.append("Performance benchmarks improved")
        if debt_item.category == TechnicalDebtCategory.TESTING:
            criteria.append("Test coverage increased")

        return criteria

    def _generate_violation_success_criteria(self, violation: ArchitecturalViolation) -> List[str]:
        """Generate success criteria for architectural violation resolution"""
        criteria = [
            f"Architectural violation {violation.id} resolved",
            "Architecture review passed",
            "Documentation updated",
        ]

        if violation.violation_type == ArchitecturalViolationType.CIRCULAR_DEPENDENCY:
            criteria.append("Dependency cycle eliminated")
        if violation.violation_type == ArchitecturalViolationType.LAYERING_VIOLATION:
            criteria.append("Layer boundaries respected")
        if violation.violation_type == ArchitecturalViolationType.TIGHT_COUPLING:
            criteria.append("Coupling metrics improved")

        return criteria

    def _determine_test_requirements(self, debt_item: TechnicalDebtItem) -> List[str]:
        """Determine testing requirements for debt resolution"""
        requirements = ["Unit tests updated", "Integration tests verified"]

        if debt_item.category == TechnicalDebtCategory.SECURITY:
            requirements.extend(["Security tests added", "Penetration testing"])
        if debt_item.category == TechnicalDebtCategory.PERFORMANCE:
            requirements.extend(["Performance tests added", "Load testing"])
        if debt_item.category == TechnicalDebtCategory.API:
            requirements.append("API contract tests")

        return requirements

    def _determine_violation_test_requirements(
        self, violation: ArchitecturalViolation
    ) -> List[str]:
        """Determine testing requirements for violation resolution"""
        requirements = ["Architecture tests added", "Dependency tests updated"]

        if violation.violation_type == ArchitecturalViolationType.SECURITY_ARCHITECTURE:
            requirements.append("Security architecture validation")
        if violation.violation_type == ArchitecturalViolationType.PERFORMANCE_ARCHITECTURE:
            requirements.append("Performance architecture validation")

        return requirements

    def _identify_documentation_updates(self, debt_item: TechnicalDebtItem) -> List[str]:
        """Identify required documentation updates"""
        updates = []

        if debt_item.category == TechnicalDebtCategory.ARCHITECTURE:
            updates.append("Architecture documentation")
        if debt_item.category == TechnicalDebtCategory.CONFIGURATION:
            updates.append("Configuration guide")
        if debt_item.category == TechnicalDebtCategory.SECURITY:
            updates.append("Security documentation")

        updates.append("Code comments and docstrings")
        return updates

    def _assess_deployment_considerations(self, debt_item: TechnicalDebtItem) -> List[str]:
        """Assess deployment considerations for debt resolution"""
        considerations = []

        if debt_item.category == TechnicalDebtCategory.CONFIGURATION:
            considerations.append("Environment configuration updates")
        if debt_item.category == TechnicalDebtCategory.SECURITY:
            considerations.append("Security deployment checklist")
        if debt_item.category == TechnicalDebtCategory.PERFORMANCE:
            considerations.append("Performance monitoring setup")
        if debt_item.category == TechnicalDebtCategory.DEPENDENCIES:
            considerations.append("Dependency update coordination")

        return considerations

    def _assess_violation_deployment_considerations(
        self, violation: ArchitecturalViolation
    ) -> List[str]:
        """Assess deployment considerations for violation resolution"""
        considerations = ["Architecture validation", "Backward compatibility check"]

        if len(violation.affected_components) > 3:
            considerations.append("Phased deployment strategy")
        if violation.severity == "critical":
            considerations.append("Emergency deployment procedures")

        return considerations

    def _calculate_merged_complexity(self, tasks: List[RefactoringTask]) -> RefactoringComplexity:
        """Calculate complexity for merged tasks"""
        complexity_values = {
            RefactoringComplexity.TRIVIAL: 1,
            RefactoringComplexity.SIMPLE: 2,
            RefactoringComplexity.MODERATE: 3,
            RefactoringComplexity.COMPLEX: 4,
            RefactoringComplexity.EPIC: 5,
        }

        total_complexity = sum(complexity_values[task.complexity] for task in tasks)
        avg_complexity = total_complexity / len(tasks)

        # Map back to complexity enum
        if avg_complexity <= 1.5:
            return RefactoringComplexity.TRIVIAL
        elif avg_complexity <= 2.5:
            return RefactoringComplexity.SIMPLE
        elif avg_complexity <= 3.5:
            return RefactoringComplexity.MODERATE
        elif avg_complexity <= 4.5:
            return RefactoringComplexity.COMPLEX
        else:
            return RefactoringComplexity.EPIC

    def _calculate_merged_impact(self, tasks: List[RefactoringTask]) -> RefactoringImpact:
        """Calculate impact for merged tasks"""
        impact_values = {
            RefactoringImpact.MINIMAL: 1,
            RefactoringImpact.MODERATE: 2,
            RefactoringImpact.SIGNIFICANT: 3,
            RefactoringImpact.MAJOR: 4,
        }

        max_impact = max(impact_values[task.impact] for task in tasks)

        # Map back to impact enum
        if max_impact <= 1:
            return RefactoringImpact.MINIMAL
        elif max_impact <= 2:
            return RefactoringImpact.MODERATE
        elif max_impact <= 3:
            return RefactoringImpact.SIGNIFICANT
        else:
            return RefactoringImpact.MAJOR

    def _consolidate_risk_assessments(self, tasks: List[RefactoringTask]) -> str:
        """Consolidate risk assessments from multiple tasks"""
        risk_keywords = set()
        for task in tasks:
            risk_keywords.update(task.risk_assessment.lower().split())

        high_risk_keywords = ["critical", "security", "breaking", "data", "production"]
        has_high_risk = any(keyword in risk_keywords for keyword in high_risk_keywords)

        if has_high_risk:
            return f"High risk consolidation of {len(tasks)} improvements with potential security/data implications"
        else:
            return f"Moderate risk consolidation of {len(tasks)} improvements"

    async def _calculate_priority_scores(self, tasks: List[RefactoringTask]):
        """Calculate comprehensive priority scores for all tasks"""
        for task in tasks:
            score = await self._calculate_task_priority_score(task)
            # Add to priority queue (negative score for max-heap behavior)
            heapq.heappush(self.priority_queue, (-score, task.id))

    async def _calculate_task_priority_score(self, task: RefactoringTask) -> float:
        """Calculate priority score for a single task"""
        # Base priority score
        priority_scores = {
            RefactoringPriority.CRITICAL: 100,
            RefactoringPriority.HIGH: 75,
            RefactoringPriority.MEDIUM: 50,
            RefactoringPriority.LOW: 25,
            RefactoringPriority.DEFERRED: 10,
        }

        base_score = priority_scores[task.priority]

        # Business value multiplier
        business_multiplier = 1.0
        for category, weight in self.business_priorities.items():
            if category in [tag.lower() for tag in task.tags]:
                business_multiplier = max(business_multiplier, weight)

        # Complexity factor (higher complexity = lower immediate priority)
        complexity_factors = {
            RefactoringComplexity.TRIVIAL: 1.2,
            RefactoringComplexity.SIMPLE: 1.1,
            RefactoringComplexity.MODERATE: 1.0,
            RefactoringComplexity.COMPLEX: 0.9,
            RefactoringComplexity.EPIC: 0.8,
        }

        complexity_factor = complexity_factors[task.complexity]

        # Impact multiplier
        impact_multipliers = {
            RefactoringImpact.MINIMAL: 0.8,
            RefactoringImpact.MODERATE: 1.0,
            RefactoringImpact.SIGNIFICANT: 1.2,
            RefactoringImpact.MAJOR: 1.5,
        }

        impact_multiplier = impact_multipliers[task.impact]

        # Confidence factor
        confidence_factor = task.confidence_level

        # ROI factor (business value / effort)
        roi_factor = business_multiplier / (task.estimated_hours / 8)  # Convert to days

        # Final score calculation
        final_score = (
            base_score
            * business_multiplier
            * complexity_factor
            * impact_multiplier
            * confidence_factor
            * roi_factor
        )

        return final_score

    def _get_priority_score(self, task: RefactoringTask) -> float:
        """Get cached priority score for a task"""
        # Find the score in the priority queue
        for neg_score, task_id in self.priority_queue:
            if task_id == task.id:
                return -neg_score
        return 0.0

    def _get_priority_numeric_value(self, priority: RefactoringPriority) -> int:
        """Get numeric value for priority comparison"""
        values = {
            RefactoringPriority.CRITICAL: 5,
            RefactoringPriority.HIGH: 4,
            RefactoringPriority.MEDIUM: 3,
            RefactoringPriority.LOW: 2,
            RefactoringPriority.DEFERRED: 1,
        }
        return values.get(priority, 3)

    async def _analyze_task_dependencies(self, tasks: List[RefactoringTask]):
        """Analyze and establish dependencies between tasks"""
        # Simple dependency analysis based on file overlap and related issues
        for i, task1 in enumerate(tasks):
            for j, task2 in enumerate(tasks):
                if i != j:
                    # Check for file overlap
                    if set(task1.affected_files) & set(task2.affected_files):
                        # Tasks affecting same files should have dependency
                        if task1.priority.value in [
                            "critical",
                            "high",
                        ] and task2.priority.value in ["medium", "low"]:
                            dependency = RefactoringDependency(
                                task_id=task2.id,
                                dependency_id=task1.id,
                                dependency_type="blocks",
                                description=f"High priority task {task1.id} blocks {task2.id}",
                            )
                            task2.dependencies.append(dependency)
                            task1.blocks.append(task2.id)

    async def _create_scheduling_plan(self) -> Dict[str, Any]:
        """Create comprehensive scheduling plan for refactoring tasks"""
        current_date = datetime.now()
        sprint_start = current_date + timedelta(days=1)

        scheduled_tasks = []
        team_allocations = {team: 0.0 for team in self.team_capacity.keys()}

        # Sort tasks by priority score
        sorted_tasks = sorted(
            self.refactoring_tasks.values(), key=self._get_priority_score, reverse=True
        )

        current_sprint_start = sprint_start
        current_sprint_tasks = []
        current_sprint_hours = 0

        for task in sorted_tasks:
            # Determine required team
            required_team = self._determine_required_team(task)
            team_capacity = self.team_capacity[required_team]["capacity_hours_per_sprint"]

            # Check if task fits in current sprint
            if (
                current_sprint_hours + task.estimated_hours <= team_capacity
                and len(current_sprint_tasks) < self.scheduling_constraints["max_concurrent_tasks"]
            ):

                # Add to current sprint
                task.target_start_date = current_sprint_start
                task.target_completion_date = current_sprint_start + timedelta(
                    days=min(14, max(1, task.estimated_hours / 8))
                )
                task.team = required_team
                task.sprint = f"Sprint {(current_sprint_start - sprint_start).days // 14 + 1}"

                current_sprint_tasks.append(task)
                current_sprint_hours += task.estimated_hours
                team_allocations[required_team] += task.estimated_hours

            else:
                # Move to next sprint
                scheduled_tasks.extend(current_sprint_tasks)
                current_sprint_start += self.scheduling_constraints["sprint_duration"]
                current_sprint_tasks = [task]
                current_sprint_hours = task.estimated_hours

                # Update task scheduling
                task.target_start_date = current_sprint_start
                task.target_completion_date = current_sprint_start + timedelta(
                    days=min(14, max(1, task.estimated_hours / 8))
                )
                task.team = required_team
                task.sprint = f"Sprint {(current_sprint_start - sprint_start).days // 14 + 1}"

        # Add remaining tasks
        scheduled_tasks.extend(current_sprint_tasks)

        return {
            "total_tasks": len(scheduled_tasks),
            "total_sprints": max(1, (current_sprint_start - sprint_start).days // 14 + 1),
            "total_estimated_hours": sum(task.estimated_hours for task in scheduled_tasks),
            "team_allocations": team_allocations,
            "sprint_breakdown": self._create_sprint_breakdown(scheduled_tasks),
            "critical_path": await self._identify_critical_path(scheduled_tasks),
            "resource_constraints": await self._identify_resource_constraints(),
        }

    def _determine_required_team(self, task: RefactoringTask) -> str:
        """Determine which team should handle the task"""
        # Simple team assignment based on tags and file types
        task_tags = [tag.lower() for tag in task.tags]

        if any(tag in task_tags for tag in ["api", "backend", "database", "architecture"]):
            return "backend_team"
        elif any(tag in task_tags for tag in ["frontend", "ui", "javascript", "react"]):
            return "frontend_team"
        elif any(tag in task_tags for tag in ["deployment", "infrastructure", "configuration"]):
            return "devops_team"
        elif any(tag in task_tags for tag in ["testing", "quality", "automation"]):
            return "qa_team"
        else:
            return "backend_team"  # Default

    def _create_sprint_breakdown(self, tasks: List[RefactoringTask]) -> Dict[str, List[Dict]]:
        """Create breakdown of tasks by sprint"""
        sprint_breakdown = defaultdict(list)

        for task in tasks:
            if task.sprint:
                sprint_breakdown[task.sprint].append(
                    {
                        "task_id": task.id,
                        "title": task.title,
                        "priority": task.priority.value,
                        "estimated_hours": task.estimated_hours,
                        "team": task.team,
                        "complexity": task.complexity.value,
                    }
                )

        return dict(sprint_breakdown)

    async def _identify_critical_path(self, tasks: List[RefactoringTask]) -> List[str]:
        """Identify critical path of task dependencies"""
        # Simplified critical path analysis
        critical_tasks = [task for task in tasks if task.priority == RefactoringPriority.CRITICAL]
        return [task.id for task in critical_tasks]

    async def _identify_resource_constraints(self) -> List[str]:
        """Identify resource constraints and bottlenecks"""
        constraints = []

        for team, capacity_info in self.team_capacity.items():
            if (
                capacity_info["current_allocation"]
                > capacity_info["capacity_hours_per_sprint"] * 0.8
            ):
                constraints.append(f"{team} is over 80% capacity")

        return constraints

    async def _generate_initiatives(self) -> List[RefactoringInitiative]:
        """Generate refactoring initiatives from related tasks"""
        initiatives = []

        # Group tasks by common themes
        theme_groups = defaultdict(list)

        for task in self.refactoring_tasks.values():
            # Group by primary tag
            primary_tag = task.tags[0] if task.tags else "general"
            theme_groups[primary_tag].append(task.id)

        # Create initiatives for groups with multiple tasks
        for theme, task_ids in theme_groups.items():
            if len(task_ids) >= 3:  # Minimum 3 tasks for an initiative
                total_hours = sum(
                    self.refactoring_tasks[task_id].estimated_hours for task_id in task_ids
                )

                initiative = RefactoringInitiative(
                    id=f"initiative_{theme}_{len(initiatives)}",
                    name=f"{theme.title()} Improvement Initiative",
                    description=f"Comprehensive improvement of {theme} aspects across the platform",
                    objective=f"Address all {theme}-related technical debt and architectural issues",
                    tasks=task_ids,
                    total_estimated_hours=total_hours,
                    target_completion_date=datetime.now() + timedelta(weeks=8),
                    initiative_lead="TBD",
                    stakeholders=["Development Team", "Architecture Team"],
                    success_metrics=[
                        f"All {len(task_ids)} {theme} tasks completed",
                        f"{theme} quality metrics improved by 25%",
                        "No regression in functionality",
                    ],
                )

                initiatives.append(initiative)
                self.initiatives[initiative.id] = initiative

        return initiatives

    async def _generate_summary(self) -> Dict[str, Any]:
        """Generate executive summary of refactoring plan"""
        total_tasks = len(self.refactoring_tasks)
        total_hours = sum(task.estimated_hours for task in self.refactoring_tasks.values())

        priority_breakdown = defaultdict(int)
        complexity_breakdown = defaultdict(int)

        for task in self.refactoring_tasks.values():
            priority_breakdown[task.priority.value] += 1
            complexity_breakdown[task.complexity.value] += 1

        return {
            "total_refactoring_tasks": total_tasks,
            "total_estimated_hours": total_hours,
            "estimated_weeks": total_hours / 40,  # 40 hours per week
            "priority_breakdown": dict(priority_breakdown),
            "complexity_breakdown": dict(complexity_breakdown),
            "total_initiatives": len(self.initiatives),
            "immediate_actions_required": priority_breakdown.get("critical", 0),
            "key_recommendation": await self._get_key_recommendation(),
        }

    async def _get_key_recommendation(self) -> str:
        """Get key recommendation based on analysis"""
        critical_count = len(
            [
                t
                for t in self.refactoring_tasks.values()
                if t.priority == RefactoringPriority.CRITICAL
            ]
        )

        if critical_count > 0:
            return f"Immediate action required: {critical_count} critical issues must be addressed before next release"

        high_count = len(
            [t for t in self.refactoring_tasks.values() if t.priority == RefactoringPriority.HIGH]
        )

        if high_count > 5:
            return f"Consider dedicated refactoring sprint: {high_count} high priority items identified"

        return "Manageable technical debt load - incorporate into regular sprint planning"

    async def _analyze_resource_allocation(self) -> Dict[str, Any]:
        """Analyze resource allocation and capacity planning"""
        team_workload = defaultdict(float)
        skill_requirements = defaultdict(int)

        for task in self.refactoring_tasks.values():
            if task.team:
                team_workload[task.team] += task.estimated_hours

            # Count skill requirements
            for tag in task.tags:
                skill_requirements[tag] += 1

        return {
            "team_workload_hours": dict(team_workload),
            "skill_requirements": dict(skill_requirements),
            "capacity_utilization": {
                team: (workload / self.team_capacity[team]["capacity_hours_per_sprint"]) * 100
                for team, workload in team_workload.items()
                if team in self.team_capacity
            },
            "recommendations": await self._get_resource_recommendations(team_workload),
        }

    async def _get_resource_recommendations(self, team_workload: Dict[str, float]) -> List[str]:
        """Get resource allocation recommendations"""
        recommendations = []

        for team, workload in team_workload.items():
            if team in self.team_capacity:
                capacity = self.team_capacity[team]["capacity_hours_per_sprint"]
                utilization = workload / capacity

                if utilization > 1.2:
                    recommendations.append(
                        f"⚠️  {team} is overallocated by {(utilization-1)*100:.0f}% - consider additional resources"
                    )
                elif utilization > 0.9:
                    recommendations.append(
                        f"📊 {team} is near capacity - monitor workload carefully"
                    )

        return recommendations

    async def _assess_refactoring_risks(self) -> Dict[str, Any]:
        """Assess risks associated with refactoring plan"""
        risks = []
        risk_score = 0

        # High impact tasks
        high_impact_tasks = [
            t
            for t in self.refactoring_tasks.values()
            if t.impact in [RefactoringImpact.SIGNIFICANT, RefactoringImpact.MAJOR]
        ]

        if high_impact_tasks:
            risks.append(
                f"High impact changes: {len(high_impact_tasks)} tasks may affect multiple components"
            )
            risk_score += len(high_impact_tasks) * 2

        # Complex tasks
        complex_tasks = [
            t
            for t in self.refactoring_tasks.values()
            if t.complexity in [RefactoringComplexity.COMPLEX, RefactoringComplexity.EPIC]
        ]

        if complex_tasks:
            risks.append(
                f"Complex refactoring: {len(complex_tasks)} tasks require significant effort"
            )
            risk_score += len(complex_tasks)

        # Resource constraints
        overallocated_teams = 0
        for team, capacity_info in self.team_capacity.items():
            if capacity_info["current_allocation"] > capacity_info["capacity_hours_per_sprint"]:
                overallocated_teams += 1

        if overallocated_teams > 0:
            risks.append(f"Resource constraints: {overallocated_teams} teams are overallocated")
            risk_score += overallocated_teams * 3

        # Dependencies
        tasks_with_dependencies = len(
            [t for t in self.refactoring_tasks.values() if t.dependencies]
        )
        if tasks_with_dependencies > len(self.refactoring_tasks) * 0.3:
            risks.append("High dependency complexity may cause scheduling delays")
            risk_score += 2

        return {
            "identified_risks": risks,
            "risk_score": risk_score,
            "risk_level": ("High" if risk_score > 15 else "Medium" if risk_score > 8 else "Low"),
            "mitigation_strategies": await self._generate_risk_mitigation_strategies(risks),
        }

    async def _generate_risk_mitigation_strategies(self, risks: List[str]) -> List[str]:
        """Generate strategies to mitigate identified risks"""
        strategies = [
            "🔒 Implement comprehensive testing strategy for all refactoring tasks",
            "📋 Create detailed rollback plans for high-impact changes",
            "🔄 Use feature flags for gradual rollout of architectural changes",
            "👥 Conduct peer reviews for all complex refactoring tasks",
            "📊 Monitor key metrics throughout refactoring implementation",
            "⏱️  Implement time-boxed refactoring sessions to control scope creep",
        ]

        # Add specific strategies based on identified risks
        if any("High impact" in risk for risk in risks):
            strategies.append("🎯 Phase high-impact changes across multiple sprints")

        if any("Resource constraints" in risk for risk in risks):
            strategies.append("📈 Consider external consulting for specialized refactoring tasks")

        if any("dependency" in risk.lower() for risk in risks):
            strategies.append("🗂️  Implement dependency management tools and practices")

        return strategies

    async def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations for refactoring execution"""
        recommendations = []

        # Critical tasks
        critical_tasks = [
            t for t in self.refactoring_tasks.values() if t.priority == RefactoringPriority.CRITICAL
        ]
        if critical_tasks:
            recommendations.append(
                f"🚨 IMMEDIATE ACTION: Address {len(critical_tasks)} critical refactoring tasks within 1 week"
            )

        # Quick wins
        quick_wins = [
            t
            for t in self.refactoring_tasks.values()
            if t.complexity == RefactoringComplexity.TRIVIAL and t.estimated_hours <= 2
        ]
        if quick_wins:
            recommendations.append(
                f"⚡ Quick wins available: {len(quick_wins)} trivial tasks can be completed in next sprint"
            )

        # Consolidation opportunities
        consolidated_tasks = [
            t for t in self.refactoring_tasks.values() if "consolidated" in t.tags
        ]
        if consolidated_tasks:
            recommendations.append(
                f"🔄 Efficiency gain: {len(consolidated_tasks)} consolidated tasks identified for batch processing"
            )

        # Team balancing
        team_utilization = {}
        for task in self.refactoring_tasks.values():
            if task.team:
                team_utilization[task.team] = (
                    team_utilization.get(task.team, 0) + task.estimated_hours
                )

        max_utilized_team = (
            max(team_utilization.items(), key=lambda x: x[1]) if team_utilization else None
        )
        if max_utilized_team and max_utilized_team[1] > 80:
            recommendations.append(
                f"⚖️  Load balancing needed: {max_utilized_team[0]} has {max_utilized_team[1]} hours allocated"
            )

        # Initiative opportunities
        if len(self.initiatives) > 0:
            recommendations.append(
                f"🎯 Strategic initiatives: {len(self.initiatives)} thematic refactoring initiatives identified"
            )

        return recommendations

    async def _calculate_planning_metrics(self) -> Dict[str, float]:
        """Calculate key planning and efficiency metrics"""
        if not self.refactoring_tasks:
            return {}

        total_tasks = len(self.refactoring_tasks)
        total_hours = sum(task.estimated_hours for task in self.refactoring_tasks.values())

        # Calculate various metrics
        avg_task_size = total_hours / total_tasks

        confidence_scores = [task.confidence_level for task in self.refactoring_tasks.values()]
        avg_confidence = sum(confidence_scores) / len(confidence_scores)

        priority_scores = [
            self._get_priority_score(task) for task in self.refactoring_tasks.values()
        ]
        avg_priority_score = sum(priority_scores) / len(priority_scores)

        # Calculate efficiency metrics
        consolidated_tasks = len(
            [t for t in self.refactoring_tasks.values() if "consolidated" in t.tags]
        )
        consolidation_ratio = consolidated_tasks / total_tasks

        return {
            "average_task_size_hours": avg_task_size,
            "average_confidence_level": avg_confidence,
            "average_priority_score": avg_priority_score,
            "consolidation_ratio": consolidation_ratio,
            "estimated_completion_weeks": total_hours / 40,
            "tasks_per_week": total_tasks / max(1, total_hours / 40),
            "high_priority_percentage": len(
                [
                    t
                    for t in self.refactoring_tasks.values()
                    if t.priority in [RefactoringPriority.CRITICAL, RefactoringPriority.HIGH]
                ]
            )
            / total_tasks
            * 100,
        }

    async def export_refactoring_plan(self, output_path: str) -> str:
        """Export comprehensive refactoring plan to file"""
        # This would be called after analyze_and_prioritize_debt()
        plan_data = {
            "export_timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "tasks": {task_id: asdict(task) for task_id, task in self.refactoring_tasks.items()},
            "initiatives": {
                init_id: asdict(initiative) for init_id, initiative in self.initiatives.items()
            },
            "scheduling_constraints": self.scheduling_constraints,
            "team_capacity": self.team_capacity,
            "business_priorities": self.business_priorities,
        }

        # Convert datetime objects for JSON serialization
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, timedelta):
                return str(obj)
            elif isinstance(obj, (RefactoringPriority, RefactoringComplexity, RefactoringImpact)):
                return obj.value
            return str(obj)

        with open(output_path, "w") as f:
            json.dump(plan_data, f, indent=2, default=json_serializer)

        logger.info(f"📋 Refactoring plan exported to {output_path}")
        return output_path


# Initialize the refactoring coordinator agent
refactoring_coordinator = RefactoringCoordinatorAgent(
    project_root=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
)
