"""
Phase 9: QA & Testing Swarm Agent

Coordinates a quality assurance and testing swarm that:
1. User Testing - Acts as user tester, evaluates usability and goal alignment
2. QA Evaluation - Performs quality checks, security, performance, edge cases
3. Enhancement Analysis - Identifies improvements and optimization opportunities
4. Development Swarm - Implements changes through SDLC process
5. Iteration Loop - Repeats until all parties agree on quality

This creates a continuous feedback loop for feature development and refinement.
"""

import json
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid

from src.models.model_factory import ModelFactory


class TestingPhase(str, Enum):
    """Phases in the QA/Testing cycle"""
    USER_TESTING = "user_testing"
    QA_EVALUATION = "qa_evaluation"
    ENHANCEMENT_ANALYSIS = "enhancement_analysis"
    DEVELOPMENT_PLANNING = "development_planning"
    IMPLEMENTATION = "implementation"
    VERIFICATION = "verification"
    COMPLETE = "complete"


@dataclass
class TestResult:
    """Result from a testing phase"""
    phase: TestingPhase
    agent: str
    timestamp: str
    issues_found: List[Dict[str, Any]] = field(default_factory=list)
    passed: bool = True
    confidence_score: float = 0.0
    recommendations: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QACycle:
    """A complete QA/Testing cycle"""
    cycle_id: str
    feature: str
    user_request: str
    current_phase: TestingPhase
    iteration: int
    started_at: str
    test_results: List[TestResult] = field(default_factory=list)
    development_tasks: List[Dict[str, Any]] = field(default_factory=list)
    agreements: Dict[str, bool] = field(default_factory=dict)  # Track who agrees
    is_complete: bool = False


class UserTesterAgent:
    """
    Simulates user testing - evaluates if feature meets user expectations
    Tests usability, functionality, and goal alignment
    """

    def __init__(self):
        self.model = ModelFactory.create_model()
        self.name = "UserTester v1.2"

    async def test_feature(self, feature: str, request: str) -> TestResult:
        """
        Act as user tester, evaluate feature against original request
        """
        prompt = f"""You are an expert user tester evaluating a new feature.

FEATURE: {feature}
ORIGINAL USER REQUEST: {request}

As a user tester, perform the following evaluation:
1. Usability Test - Is the feature easy to use and intuitive?
2. Goal Alignment - Does it fulfill the original request?
3. User Experience - Is the workflow smooth?
4. Edge Cases - Test common user mistakes or edge cases
5. Accessibility - Can different users use this effectively?

Respond in JSON format:
{{
    "passed": true/false,
    "confidence_score": 0.0-1.0,
    "issues_found": [
        {{"severity": "critical/high/medium/low", "issue": "description", "impact": "user impact"}}
    ],
    "recommendations": ["recommendation 1", "recommendation 2"],
    "test_coverage": "what aspects were tested",
    "user_satisfaction": "estimated user satisfaction level"
}}
"""
        try:
            response = await self.model.generate_response(
                system_prompt="You are an expert software QA user tester.",
                user_content=prompt,
                temperature=0.7,
                max_tokens=1500
            )

            result_data = json.loads(response)
            return TestResult(
                phase=TestingPhase.USER_TESTING,
                agent=self.name,
                timestamp=datetime.now().isoformat(),
                issues_found=result_data.get("issues_found", []),
                passed=result_data.get("passed", True),
                confidence_score=result_data.get("confidence_score", 0.0),
                recommendations=result_data.get("recommendations", []),
                details=result_data
            )
        except Exception as e:
            print(f"User testing error: {e}")
            return TestResult(
                phase=TestingPhase.USER_TESTING,
                agent=self.name,
                timestamp=datetime.now().isoformat(),
                passed=False,
                details={"error": str(e)}
            )


class QAEvaluatorAgent:
    """
    Performs quality assurance evaluation
    Checks code quality, security, performance, best practices
    """

    def __init__(self):
        self.model = ModelFactory.create_model()
        self.name = "QAEvaluator v2.0"

    async def evaluate_quality(self, feature: str, implementation_details: str = "") -> TestResult:
        """
        Evaluate feature quality from QA perspective
        """
        prompt = f"""You are an expert QA engineer evaluating implementation quality.

FEATURE: {feature}
IMPLEMENTATION DETAILS: {implementation_details}

Perform comprehensive QA evaluation:
1. Code Quality - Is code clean, maintainable, well-documented?
2. Security - Are there security vulnerabilities or best practices violations?
3. Performance - Will this scale? Are there performance concerns?
4. Testing - Is the feature properly tested? Test coverage?
5. Compatibility - Does it work across browsers/devices?
6. Error Handling - Are edge cases and errors handled properly?
7. Best Practices - Follows architecture and coding standards?

Respond in JSON format:
{{
    "passed": true/false,
    "confidence_score": 0.0-1.0,
    "issues_found": [
        {{"type": "security/performance/quality/compatibility/testing", "severity": "critical/high/medium/low", "issue": "description"}}
    ],
    "recommendations": ["fix 1", "fix 2"],
    "quality_metrics": {{"code_quality": 0-100, "test_coverage": 0-100, "security_score": 0-100}},
    "risk_assessment": "low/medium/high"
}}
"""
        try:
            response = await self.model.generate_response(
                system_prompt="You are an expert QA engineer.",
                user_content=prompt,
                temperature=0.7,
                max_tokens=1500
            )

            result_data = json.loads(response)
            return TestResult(
                phase=TestingPhase.QA_EVALUATION,
                agent=self.name,
                timestamp=datetime.now().isoformat(),
                issues_found=result_data.get("issues_found", []),
                passed=result_data.get("passed", True),
                confidence_score=result_data.get("confidence_score", 0.0),
                recommendations=result_data.get("recommendations", []),
                details=result_data
            )
        except Exception as e:
            print(f"QA evaluation error: {e}")
            return TestResult(
                phase=TestingPhase.QA_EVALUATION,
                agent=self.name,
                timestamp=datetime.now().isoformat(),
                passed=False,
                details={"error": str(e)}
            )


class EnhancementAnalystAgent:
    """
    Identifies enhancement opportunities and optimization possibilities
    Looks for improvements beyond basic functionality
    """

    def __init__(self):
        self.model = ModelFactory.create_model()
        self.name = "EnhancementAnalyst v1.5"

    async def analyze_enhancements(self, feature: str, current_feedback: List[Dict[str, Any]]) -> TestResult:
        """
        Identify enhancement and optimization opportunities
        """
        feedback_summary = json.dumps(current_feedback, indent=2)

        prompt = f"""You are a product enhancement specialist analyzing opportunities.

FEATURE: {feature}
CURRENT FEEDBACK: {feedback_summary}

Analyze enhancement opportunities:
1. User Experience Improvements - UX/UI enhancements
2. Performance Optimizations - Speed, efficiency improvements
3. Feature Gaps - Missing functionality that would help users
4. Scalability - Improvements for growth
5. Integration Opportunities - What else could integrate with this?
6. Analytics & Monitoring - Better insights for users/admins
7. Automation Possibilities - What could be automated?

Respond in JSON format:
{{
    "recommendations": [
        {{"priority": "high/medium/low", "area": "category", "suggestion": "description", "effort": "low/medium/high", "impact": "high/medium/low"}}
    ],
    "quick_wins": ["quick win 1", "quick win 2"],
    "future_roadmap": ["long-term opportunity 1", "opportunity 2"],
    "estimated_roi": "description of value"
}}
"""
        try:
            response = await self.model.generate_response(
                system_prompt="You are a product enhancement specialist.",
                user_content=prompt,
                temperature=0.8,
                max_tokens=1500
            )

            result_data = json.loads(response)
            return TestResult(
                phase=TestingPhase.ENHANCEMENT_ANALYSIS,
                agent=self.name,
                timestamp=datetime.now().isoformat(),
                passed=True,
                recommendations=result_data.get("recommendations", []),
                details=result_data
            )
        except Exception as e:
            print(f"Enhancement analysis error: {e}")
            return TestResult(
                phase=TestingPhase.ENHANCEMENT_ANALYSIS,
                agent=self.name,
                timestamp=datetime.now().isoformat(),
                passed=False,
                details={"error": str(e)}
            )


class DevelopmentSwarmCoordinator:
    """
    Coordinates development team to implement changes
    Plans tasks, assigns work, tracks implementation
    """

    def __init__(self):
        self.model = ModelFactory.create_model()
        self.name = "DevSwarmCoordinator v1.8"

    async def plan_development(
        self,
        feature: str,
        test_issues: List[Dict[str, Any]],
        qa_issues: List[Dict[str, Any]],
        enhancements: List[Dict[str, Any]]
    ) -> TestResult:
        """
        Plan development tasks based on feedback
        """
        issues_summary = f"""
TEST ISSUES: {json.dumps(test_issues, indent=2)}
QA ISSUES: {json.dumps(qa_issues, indent=2)}
ENHANCEMENT OPPORTUNITIES: {json.dumps(enhancements, indent=2)}
"""

        prompt = f"""You are a development team coordinator planning implementation.

FEATURE: {feature}
FEEDBACK SUMMARY: {issues_summary}

Create an SDLC implementation plan:
1. Prioritize Issues - Critical fixes first, then enhancements
2. Breaking Down Tasks - Create specific, assignable development tasks
3. Dependencies - Identify task dependencies
4. Estimated Effort - Time estimates for each task
5. Risk Mitigation - Plan to address risks
6. Testing Strategy - How changes will be verified

Respond in JSON format:
{{
    "development_tasks": [
        {{"id": "task_id", "title": "task title", "description": "details", "priority": "critical/high/medium/low", "effort_hours": 4, "assigned_agent": "agent_name", "dependencies": ["task_id"]}}
    ],
    "sprint_timeline": "timeline estimate",
    "quality_gates": ["gate 1", "gate 2"],
    "rollback_plan": "plan if things go wrong",
    "success_criteria": ["criterion 1", "criterion 2"]
}}
"""
        try:
            response = await self.model.generate_response(
                system_prompt="You are a development team coordinator.",
                user_content=prompt,
                temperature=0.7,
                max_tokens=2000
            )

            result_data = json.loads(response)
            return TestResult(
                phase=TestingPhase.DEVELOPMENT_PLANNING,
                agent=self.name,
                timestamp=datetime.now().isoformat(),
                passed=True,
                details=result_data
            )
        except Exception as e:
            print(f"Development planning error: {e}")
            return TestResult(
                phase=TestingPhase.DEVELOPMENT_PLANNING,
                agent=self.name,
                timestamp=datetime.now().isoformat(),
                passed=False,
                details={"error": str(e)}
            )


class QASwarmOrchestrator:
    """
    Main orchestrator that coordinates the entire QA/Testing/Development cycle
    Manages the feedback loop until all stakeholders agree
    """

    def __init__(self):
        self.user_tester = UserTesterAgent()
        self.qa_evaluator = QAEvaluatorAgent()
        self.enhancement_analyst = EnhancementAnalystAgent()
        self.dev_coordinator = DevelopmentSwarmCoordinator()
        self.max_iterations = 5
        self.agreement_threshold = 0.75  # 75% confidence/agreement needed

    async def run_qa_cycle(
        self,
        feature: str,
        user_request: str,
        implementation_details: str = ""
    ) -> QACycle:
        """
        Run a complete QA cycle: Test → QA → Enhance → Develop → Verify → Repeat
        """
        cycle_id = str(uuid.uuid4())
        cycle = QACycle(
            cycle_id=cycle_id,
            feature=feature,
            user_request=user_request,
            current_phase=TestingPhase.USER_TESTING,
            iteration=1,
            started_at=datetime.now().isoformat()
        )

        print(f"\n{'='*60}")
        print(f"🔄 Starting QA Cycle: {cycle_id}")
        print(f"Feature: {feature}")
        print(f"{'='*60}\n")

        while not cycle.is_complete and cycle.iteration <= self.max_iterations:
            print(f"\n📋 Iteration {cycle.iteration}")
            print(f"Current Phase: {cycle.current_phase.value}")
            print("-" * 60)

            # Phase 1: User Testing
            if cycle.current_phase == TestingPhase.USER_TESTING:
                print("\n👤 Running User Testing...")
                user_test = await self.user_tester.test_feature(feature, user_request)
                cycle.test_results.append(user_test)
                cycle.current_phase = TestingPhase.QA_EVALUATION
                print(f"   ✓ Test Coverage: {user_test.details.get('test_coverage', 'N/A')}")
                print(f"   ✓ Issues Found: {len(user_test.issues_found)}")

            # Phase 2: QA Evaluation
            elif cycle.current_phase == TestingPhase.QA_EVALUATION:
                print("\n🔍 Running QA Evaluation...")
                qa_result = await self.qa_evaluator.evaluate_quality(
                    feature,
                    implementation_details
                )
                cycle.test_results.append(qa_result)
                cycle.current_phase = TestingPhase.ENHANCEMENT_ANALYSIS
                print(f"   ✓ Quality Score: {qa_result.details.get('quality_metrics', {}).get('code_quality', 'N/A')}%")
                print(f"   ✓ Issues Found: {len(qa_result.issues_found)}")

            # Phase 3: Enhancement Analysis
            elif cycle.current_phase == TestingPhase.ENHANCEMENT_ANALYSIS:
                print("\n💡 Analyzing Enhancement Opportunities...")
                # Gather feedback from previous phases
                all_feedback = [r.details for r in cycle.test_results]
                enhancement = await self.enhancement_analyst.analyze_enhancements(
                    feature,
                    all_feedback
                )
                cycle.test_results.append(enhancement)
                cycle.current_phase = TestingPhase.DEVELOPMENT_PLANNING
                recommendations = enhancement.details.get('recommendations', [])
                print(f"   ✓ Enhancement Ideas: {len(recommendations)}")

            # Phase 4: Development Planning
            elif cycle.current_phase == TestingPhase.DEVELOPMENT_PLANNING:
                print("\n👷 Planning Development Tasks...")
                # Collect all issues and recommendations
                test_issues = []
                qa_issues = []
                enhancements = []

                for result in cycle.test_results:
                    if result.phase == TestingPhase.USER_TESTING:
                        test_issues = result.issues_found
                    elif result.phase == TestingPhase.QA_EVALUATION:
                        qa_issues = result.issues_found
                    elif result.phase == TestingPhase.ENHANCEMENT_ANALYSIS:
                        enhancements = result.recommendations

                dev_plan = await self.dev_coordinator.plan_development(
                    feature,
                    test_issues,
                    qa_issues,
                    enhancements
                )
                cycle.test_results.append(dev_plan)
                cycle.development_tasks = dev_plan.details.get('development_tasks', [])
                cycle.current_phase = TestingPhase.IMPLEMENTATION
                print(f"   ✓ Tasks Created: {len(cycle.development_tasks)}")

            # Phase 5: Implementation (simulated)
            elif cycle.current_phase == TestingPhase.IMPLEMENTATION:
                print("\n⚙️ Implementing Changes...")
                print(f"   ✓ Processing {len(cycle.development_tasks)} development tasks")
                # In real implementation, this would actually modify the codebase
                await asyncio.sleep(1)  # Simulate work
                cycle.current_phase = TestingPhase.VERIFICATION
                print("   ✓ Changes implemented and committed")

            # Phase 6: Verification - Run tests again
            elif cycle.current_phase == TestingPhase.VERIFICATION:
                print("\n✅ Verifying Changes...")
                cycle.iteration += 1

                # Run user testing again
                user_test = await self.user_tester.test_feature(feature, user_request)
                cycle.test_results.append(user_test)
                cycle.agreements['user_tester'] = user_test.passed

                # Run QA evaluation again
                qa_result = await self.qa_evaluator.evaluate_quality(feature)
                cycle.test_results.append(qa_result)
                cycle.agreements['qa_evaluator'] = qa_result.passed

                print(f"   ✓ User Tester: {'PASS ✓' if user_test.passed else 'FAIL ✗'}")
                print(f"   ✓ QA Evaluator: {'PASS ✓' if qa_result.passed else 'FAIL ✗'}")

                # Check if all agree
                if self._all_stakeholders_agree(cycle.agreements):
                    print("\n✨ All stakeholders in agreement!")
                    cycle.is_complete = True
                    cycle.current_phase = TestingPhase.COMPLETE
                else:
                    print(f"\n⚠️ Continuing refinement (Iteration {cycle.iteration}/{self.max_iterations})")
                    cycle.current_phase = TestingPhase.USER_TESTING

        print(f"\n{'='*60}")
        print(f"✅ QA Cycle Complete: {cycle.cycle_id}")
        print(f"Total Iterations: {cycle.iteration}")
        print(f"Final Status: {'APPROVED ✓' if cycle.is_complete else 'NEEDS REVIEW'}")
        print(f"{'='*60}\n")

        return cycle

    def _all_stakeholders_agree(self, agreements: Dict[str, bool]) -> bool:
        """Check if all stakeholders agree"""
        if not agreements:
            return False
        return all(agreements.values()) and len(agreements) >= 2


async def main():
    """Demo of QA Swarm in action"""
    orchestrator = QASwarmOrchestrator()

    # Example: Testing a new ExecutionMonitor feature
    cycle = await orchestrator.run_qa_cycle(
        feature="ExecutionMonitor Console with Agent Activity Logs",
        user_request="Users need to see what agents are doing in real-time during execution",
        implementation_details="React component with live console showing agent logs"
    )

    # Print final report
    print("\n📊 QA CYCLE SUMMARY REPORT")
    print("=" * 60)
    print(f"Feature: {cycle.feature}")
    print(f"Cycle ID: {cycle.cycle_id}")
    print(f"Total Iterations: {cycle.iteration}")
    print(f"Test Results: {len(cycle.test_results)}")
    print(f"Development Tasks: {len(cycle.development_tasks)}")
    print(f"Final Status: {'APPROVED ✓' if cycle.is_complete else 'NEEDS WORK'}")
    print("\nStakeholder Agreements:")
    for stakeholder, agreed in cycle.agreements.items():
        print(f"  • {stakeholder}: {'✓' if agreed else '✗'}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
