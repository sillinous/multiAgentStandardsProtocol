"""
QA/Evaluation Agent - Validates changes and assesses readiness
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from .base_agent import BaseAgent, AgentCapability, MessageType


class QAAgent(BaseAgent):
    """
    QA/Evaluation Agent responsible for:
    - Reviewing implemented changes
    - Validating against design specifications
    - Assessing code quality and test coverage
    - Evaluating alignment with autonomous deployment vision
    - Approving or rejecting changes
    - Determining overall application readiness
    """

    def __init__(
        self,
        agent_id: str = "qa_agent_001",
        workspace_path: str = "./autonomous-ecosystem/workspace",
        project_root: str = "."
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type="qa_evaluation",
            capabilities=[AgentCapability.QA_EVALUATION],
            workspace_path=workspace_path
        )
        self.project_root = project_root
        self.reviews_completed = []
        self.approvals_given = 0
        self.rejections_given = 0

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute QA task"""
        task_type = task.get("type")

        if task_type == "review_implementation":
            implementation = task.get("implementation")
            spec = task.get("specification")
            return await self.review_implementation(implementation, spec)
        elif task_type == "assess_readiness":
            return await self.assess_overall_readiness()
        elif task_type == "validate_changes":
            changes = task.get("changes")
            return await self.validate_changes(changes)
        else:
            return {"error": f"Unknown task type: {task_type}"}

    async def analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze and provide quality assessment"""
        analysis_type = input_data.get("type")

        if analysis_type == "implementation":
            return await self.analyze_implementation(input_data.get("implementation"))
        elif analysis_type == "readiness":
            return await self.analyze_readiness(input_data.get("test_results"))
        else:
            return {"error": f"Unknown analysis type: {analysis_type}"}

    async def review_implementation(
        self,
        implementation: Dict[str, Any],
        specification: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Review implementation against specification"""
        print(f"[{self.agent_id}] Reviewing implementation: {implementation.get('implements_spec')}")

        review = {
            "type": "qa_review",
            "timestamp": datetime.now().isoformat(),
            "iteration": self.current_iteration,
            "agent_id": self.agent_id,
            "reviews_implementation": implementation.get("implements_spec"),
            "status": "pending",
            "findings": [],
            "alignment_score": 0.0,
            "recommendations": ""
        }

        # Check if implementation addresses spec requirements
        completeness = await self._check_completeness(implementation, specification)
        review["findings"].extend(completeness["findings"])

        # Check code quality
        quality = await self._check_code_quality(implementation)
        review["findings"].extend(quality["findings"])

        # Check test coverage
        test_coverage = await self._check_test_coverage(implementation)
        review["findings"].extend(test_coverage["findings"])

        # Check alignment with vision
        alignment = await self._check_vision_alignment(implementation)
        review["alignment_score"] = alignment["score"]
        review["findings"].extend(alignment["findings"])

        # Determine status
        critical_issues = [f for f in review["findings"] if f.get("severity") == "critical"]
        high_issues = [f for f in review["findings"] if f.get("severity") == "high"]

        if len(critical_issues) > 0:
            review["status"] = "rejected"
            review["recommendations"] = f"Fix {len(critical_issues)} critical issues before re-submission"
            self.rejections_given += 1
        elif len(high_issues) > 3:
            review["status"] = "rejected"
            review["recommendations"] = f"Address {len(high_issues)} high-severity issues"
            self.rejections_given += 1
        elif review["alignment_score"] < 0.7:
            review["status"] = "rejected"
            review["recommendations"] = "Implementation does not align well with autonomous deployment vision"
            self.rejections_given += 1
        else:
            review["status"] = "approved"
            review["recommendations"] = "Implementation meets quality standards and can proceed to testing"
            self.approvals_given += 1

        # Save review
        self.save_artifact(
            "qa_reviews",
            review,
            f"qa_review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        # Send to orchestrator
        self.send_message(
            MessageType.QA_REVIEW,
            "orchestrator",
            review
        )

        return review

    async def assess_overall_readiness(self) -> Dict[str, Any]:
        """Assess overall application readiness for deployment"""
        print(f"[{self.agent_id}] Assessing overall application readiness...")

        assessment = {
            "timestamp": datetime.now().isoformat(),
            "iteration": self.current_iteration,
            "agent_id": self.agent_id,
            "readiness_criteria": {},
            "overall_ready": False,
            "vote": "not_ready",
            "blockers": [],
            "recommendations": []
        }

        # Check each readiness criterion
        criteria = await self._evaluate_readiness_criteria()
        assessment["readiness_criteria"] = criteria

        # Check for blockers
        for criterion, result in criteria.items():
            if not result["met"] and result["critical"]:
                assessment["blockers"].append({
                    "criterion": criterion,
                    "description": result["description"]
                })

        # Determine overall readiness
        if len(assessment["blockers"]) == 0:
            all_met = all(c["met"] for c in criteria.values())
            if all_met:
                assessment["overall_ready"] = True
                assessment["vote"] = "ready"
                assessment["recommendations"].append("Application meets all readiness criteria")
            else:
                assessment["vote"] = "not_ready"
                unmet = [k for k, v in criteria.items() if not v["met"]]
                assessment["recommendations"].append(f"Address remaining criteria: {', '.join(unmet)}")
        else:
            assessment["vote"] = "not_ready"
            assessment["recommendations"].append(f"Fix {len(assessment['blockers'])} critical blockers")

        return assessment

    async def validate_changes(self, changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate specific changes"""
        print(f"[{self.agent_id}] Validating {len(changes)} changes...")

        validation = {
            "changes_validated": [],
            "issues_found": []
        }

        for change in changes:
            is_valid = await self._validate_change(change)
            if is_valid["valid"]:
                validation["changes_validated"].append(change)
            else:
                validation["issues_found"].append({
                    "change": change,
                    "issues": is_valid["issues"]
                })

        return validation

    # Review helper methods

    async def _check_completeness(
        self,
        implementation: Dict[str, Any],
        specification: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check if implementation is complete according to spec"""
        findings = []

        spec_requirements = specification.get("requirements", [])
        impl_changes = implementation.get("changes", [])

        if len(impl_changes) == 0:
            findings.append({
                "type": "issue",
                "severity": "critical",
                "description": "No changes implemented",
                "action_required": "Implement the required changes"
            })
        elif len(impl_changes) < len(spec_requirements):
            findings.append({
                "type": "concern",
                "severity": "medium",
                "description": "Implementation may not address all requirements",
                "action_required": "Verify all requirements are addressed"
            })

        # Check for tests
        tests_added = implementation.get("tests_added", [])
        if len(tests_added) == 0:
            findings.append({
                "type": "issue",
                "severity": "high",
                "description": "No tests added for implementation",
                "action_required": "Add comprehensive tests"
            })

        return {"findings": findings}

    async def _check_code_quality(self, implementation: Dict[str, Any]) -> Dict[str, Any]:
        """Check code quality"""
        findings = []

        # In a real implementation, would run linters, formatters, etc.
        # For now, just check if changes have descriptions

        changes = implementation.get("changes", [])
        for change in changes:
            if not change.get("description"):
                findings.append({
                    "type": "issue",
                    "severity": "low",
                    "description": f"Change missing description: {change.get('file')}",
                    "action_required": "Add clear description of changes"
                })

        return {"findings": findings}

    async def _check_test_coverage(self, implementation: Dict[str, Any]) -> Dict[str, Any]:
        """Check test coverage"""
        findings = []

        tests_added = implementation.get("tests_added", [])
        changes = implementation.get("changes", [])

        # Expect at least one test per change
        if len(tests_added) < len(changes) * 0.5:
            findings.append({
                "type": "concern",
                "severity": "medium",
                "description": "Test coverage may be insufficient",
                "action_required": "Add more tests to cover implementation"
            })

        return {"findings": findings}

    async def _check_vision_alignment(self, implementation: Dict[str, Any]) -> Dict[str, Any]:
        """Check alignment with autonomous deployment vision"""
        findings = []
        score = 0.5  # Default medium alignment

        component = implementation.get("component")

        if component == "e2e_workflows":
            # E2E workflows are critical to vision
            changes = implementation.get("changes", [])

            # Check for key workflow components
            has_orchestration = any("orchestration" in c.get("file", "").lower() for c in changes)
            has_deployment = any("deployment" in c.get("file", "").lower() for c in changes)
            has_workflow = any("workflow" in c.get("file", "").lower() for c in changes)

            if has_orchestration and has_deployment and has_workflow:
                score = 0.9
                findings.append({
                    "type": "success",
                    "severity": "low",
                    "description": "Implementation strongly aligns with autonomous deployment vision",
                    "action_required": "None - excellent alignment"
                })
            elif has_orchestration or has_deployment:
                score = 0.7
                findings.append({
                    "type": "suggestion",
                    "severity": "low",
                    "description": "Implementation partially aligns with vision",
                    "action_required": "Consider adding more autonomous workflow components"
                })
            else:
                score = 0.4
                findings.append({
                    "type": "concern",
                    "severity": "high",
                    "description": "Implementation does not clearly support autonomous deployment vision",
                    "action_required": "Add workflow orchestration and deployment automation"
                })
        else:
            # Other components support but don't directly enable vision
            score = 0.6
            findings.append({
                "type": "suggestion",
                "severity": "low",
                "description": f"Component {component} provides supporting functionality",
                "action_required": "Ensure integration with E2E workflows"
            })

        return {"score": score, "findings": findings}

    async def _evaluate_readiness_criteria(self) -> Dict[str, Any]:
        """Evaluate all readiness criteria"""
        criteria = {}

        # 1. Critical Issues Resolved
        criteria["critical_issues_resolved"] = {
            "met": False,  # Would check latest test report
            "critical": True,
            "description": "All critical and high-severity bugs resolved"
        }

        # 2. Test Coverage
        criteria["test_coverage"] = {
            "met": False,  # Would check coverage reports
            "critical": True,
            "description": ">90% code coverage across all components"
        }

        # 3. E2E Workflow Functional
        criteria["e2e_workflow_functional"] = {
            "met": False,  # Would check E2E test results
            "critical": True,
            "description": "Complete market-research-to-deployment flow functional"
        }

        # 4. Autonomous Operations
        criteria["autonomous_operations"] = {
            "met": False,  # Would check autonomous features
            "critical": True,
            "description": "All autonomous features working without manual intervention"
        }

        # 5. Performance
        criteria["performance"] = {
            "met": True,  # Would check performance benchmarks
            "critical": False,
            "description": "Meets performance benchmarks"
        }

        # 6. Documentation
        criteria["documentation"] = {
            "met": True,  # Would check docs
            "critical": False,
            "description": "Adequate documentation provided"
        }

        return criteria

    async def _validate_change(self, change: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a specific change"""
        validation = {
            "valid": True,
            "issues": []
        }

        # Check change has required fields
        if not change.get("file"):
            validation["valid"] = False
            validation["issues"].append("Change missing file path")

        if not change.get("type"):
            validation["valid"] = False
            validation["issues"].append("Change missing type")

        if not change.get("description"):
            validation["valid"] = False
            validation["issues"].append("Change missing description")

        return validation

    async def analyze_implementation(self, implementation: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze implementation quality"""
        return {
            "quality_score": 0.7,
            "completeness_score": 0.8,
            "test_coverage_score": 0.6,
            "overall_assessment": "Good"
        }

    async def analyze_readiness(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze readiness from test results"""
        summary = test_results.get("summary", {})

        readiness_score = 0.0
        if summary.get("total_tests", 0) > 0:
            pass_rate = summary["passed"] / summary["total_tests"]
            coverage = summary.get("coverage", 0)
            readiness_score = (pass_rate * 0.6) + (coverage * 0.4)

        return {
            "readiness_score": readiness_score,
            "ready_for_deployment": readiness_score > 0.9,
            "areas_needing_work": self._identify_weak_areas(test_results)
        }

    def _identify_weak_areas(self, test_results: Dict[str, Any]) -> List[str]:
        """Identify areas that need work"""
        weak_areas = []

        components = test_results.get("components", {})
        for component_name, component_results in components.items():
            if component_results.get("tests_failed", 0) > 0:
                weak_areas.append(component_name)

        return weak_areas
