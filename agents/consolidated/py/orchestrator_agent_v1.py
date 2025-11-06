"""
Orchestrator Agent - Coordinates the autonomous improvement loop
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from superstandard.agents.base.base_agent import BaseAgent, AgentCapability, MessageType
from .testing_agent import TestingAgent
from .design_agent import DesignAgent
from .development_agent import DevelopmentAgent
from .qa_agent import QAAgent
import asyncio


class OrchestratorAgent(BaseAgent):
    """
    Orchestrator Agent responsible for:
    - Managing workflow between teams
    - Routing tasks and reports
    - Tracking progress and metrics
    - Facilitating inter-team communication
    - Driving consensus on readiness
    - Maintaining knowledge base
    - Ensuring continuous improvement
    """

    def __init__(
        self,
        agent_id: str = "orchestrator_001",
        workspace_path: str = "./autonomous-ecosystem/workspace",
        project_root: str = "."
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type="orchestrator",
            capabilities=[AgentCapability.ORCHESTRATION],
            workspace_path=workspace_path
        )
        self.project_root = project_root

        # Initialize agent teams
        self.testing_team = TestingAgent(
            workspace_path=workspace_path,
            project_root=project_root
        )
        self.design_team = DesignAgent(
            workspace_path=workspace_path,
            project_root=project_root
        )
        self.development_team = DevelopmentAgent(
            workspace_path=workspace_path,
            project_root=project_root
        )
        self.qa_team = QAAgent(
            workspace_path=workspace_path,
            project_root=project_root
        )

        # Loop state
        self.loop_running = False
        self.max_iterations = 10
        self.consensus_reached = False
        self.iteration_history = []

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute orchestrator task"""
        task_type = task.get("type")

        if task_type == "start_improvement_loop":
            return await self.start_improvement_loop()
        elif task_type == "check_consensus":
            return await self.check_consensus()
        elif task_type == "get_status":
            return await self.get_loop_status()
        else:
            return {"error": f"Unknown task type: {task_type}"}

    async def analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze loop progress and metrics"""
        return await self.analyze_progress()

    async def start_improvement_loop(self) -> Dict[str, Any]:
        """Start the continuous improvement loop"""
        print(f"\n{'='*80}")
        print(f"[{self.agent_id}] STARTING AUTONOMOUS IMPROVEMENT LOOP")
        print(f"{'='*80}\n")

        self.loop_running = True
        self.consensus_reached = False

        loop_result = {
            "started_at": datetime.now().isoformat(),
            "iterations": [],
            "final_status": "unknown"
        }

        # Run improvement iterations
        while (
            self.current_iteration <= self.max_iterations and
            not self.consensus_reached and
            self.loop_running
        ):
            print(f"\n{'='*80}")
            print(f"ITERATION {self.current_iteration}")
            print(f"{'='*80}\n")

            iteration_result = await self._run_iteration()
            loop_result["iterations"].append(iteration_result)
            self.iteration_history.append(iteration_result)

            # Check for consensus
            consensus = await self.check_consensus()
            if consensus["consensus_reached"]:
                self.consensus_reached = True
                loop_result["final_status"] = "consensus_reached"
                print(f"\n{'='*80}")
                print(f"✓ CONSENSUS REACHED - APPLICATION READY FOR DEPLOYMENT")
                print(f"{'='*80}\n")
                break

            # Move to next iteration
            self.current_iteration += 1
            self._update_team_iterations()

        if not self.consensus_reached:
            loop_result["final_status"] = "max_iterations_reached"
            print(f"\n{'='*80}")
            print(f"⚠ MAX ITERATIONS REACHED - NO CONSENSUS YET")
            print(f"{'='*80}\n")

        loop_result["completed_at"] = datetime.now().isoformat()
        loop_result["total_iterations"] = len(loop_result["iterations"])
        loop_result["consensus_reached"] = self.consensus_reached

        # Save final report
        self.save_artifact(
            ".",
            loop_result,
            f"improvement_loop_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        return loop_result

    async def _run_iteration(self) -> Dict[str, Any]:
        """Run a single improvement iteration"""
        iteration_result = {
            "iteration": self.current_iteration,
            "started_at": datetime.now().isoformat(),
            "phases": {}
        }

        # Phase 1: Testing
        print(f"\n--- PHASE 1: COMPREHENSIVE TESTING ---\n")
        test_report = await self._phase_testing()
        iteration_result["phases"]["testing"] = test_report

        # Check if any issues found
        if test_report["summary"]["total_issues"] == 0:
            print("\n✓ No issues found - checking final validation")
            iteration_result["completed_at"] = datetime.now().isoformat()
            return iteration_result

        # Phase 2: Design
        print(f"\n--- PHASE 2: DESIGN ANALYSIS ---\n")
        design_specs = await self._phase_design(test_report)
        iteration_result["phases"]["design"] = design_specs

        # Phase 3: Development
        print(f"\n--- PHASE 3: IMPLEMENTATION ---\n")
        implementations = await self._phase_development(design_specs)
        iteration_result["phases"]["development"] = implementations

        # Phase 4: QA Review
        print(f"\n--- PHASE 4: QA REVIEW ---\n")
        qa_reviews = await self._phase_qa(implementations, design_specs)
        iteration_result["phases"]["qa"] = qa_reviews

        # Phase 5: Validation
        print(f"\n--- PHASE 5: VALIDATION ---\n")
        validation = await self._phase_validation(qa_reviews)
        iteration_result["phases"]["validation"] = validation

        iteration_result["completed_at"] = datetime.now().isoformat()

        return iteration_result

    async def _phase_testing(self) -> Dict[str, Any]:
        """Phase 1: Comprehensive Testing"""
        test_report = await self.testing_team.run_comprehensive_tests()

        print(f"\n📊 Test Results:")
        print(f"  Total Tests: {test_report['summary']['total_tests']}")
        print(f"  Passed: {test_report['summary']['passed']}")
        print(f"  Failed: {test_report['summary']['failed']}")
        print(f"  Coverage: {test_report['summary']['coverage']:.1%}")
        print(f"  Issues Found: {test_report['summary']['total_issues']}")

        if test_report["critical_issues"]:
            print(f"\n  🚨 Critical Issues:")
            for issue in test_report["critical_issues"][:5]:
                print(f"    - {issue['id']}: {issue['description']}")

        return test_report

    async def _phase_design(self, test_report: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 2: Design Analysis and Specification"""

        # Analyze test report
        analysis = await self.design_team.analyze_test_report(test_report)

        print(f"\n📐 Design Analysis:")
        print(f"  Insights: {len(analysis['insights'])}")
        print(f"  Recommendations: {len(analysis['design_recommendations'])}")
        print(f"  Architectural Concerns: {len(analysis['architectural_concerns'])}")

        # Create specifications for priority issues
        priority_issues = test_report.get("priority_items", [])[:5]  # Top 5

        if not priority_issues:
            print(f"\n  ℹ No priority issues to address")
            return {"specifications": []}

        design_specs = await self.design_team.create_specifications(priority_issues)

        print(f"\n📋 Design Specifications:")
        for spec in design_specs.get("specifications", []):
            print(f"  - {spec['id']}: {spec['title']}")

        return design_specs

    async def _phase_development(self, design_specs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Phase 3: Implementation"""

        specifications = design_specs.get("specifications", [])

        if not specifications:
            print(f"\n  ℹ No specifications to implement")
            return []

        implementations = []

        for spec in specifications:
            print(f"\n🔨 Implementing: {spec['id']}")

            implementation = await self.development_team.implement_specification(spec)
            implementations.append(implementation)

            print(f"  Status: {implementation['status']}")
            print(f"  Changes: {len(implementation['changes'])}")
            print(f"  Tests Added: {len(implementation['tests_added'])}")

        return implementations

    async def _phase_qa(
        self,
        implementations: List[Dict[str, Any]],
        design_specs: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Phase 4: QA Review"""

        if not implementations:
            print(f"\n  ℹ No implementations to review")
            return []

        reviews = []
        specifications = design_specs.get("specifications", [])

        for implementation in implementations:
            # Find corresponding spec
            spec_id = implementation.get("implements_spec")
            spec = next((s for s in specifications if s["id"] == spec_id), {})

            print(f"\n🔍 Reviewing: {spec_id}")

            review = await self.qa_team.review_implementation(implementation, spec)
            reviews.append(review)

            print(f"  Status: {review['status']}")
            print(f"  Findings: {len(review['findings'])}")
            print(f"  Alignment Score: {review['alignment_score']:.2f}")

            if review["status"] == "rejected":
                print(f"  ❌ REJECTED: {review['recommendations']}")
            else:
                print(f"  ✓ APPROVED: {review['recommendations']}")

        return reviews

    async def _phase_validation(self, qa_reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Phase 5: Validation"""

        validation = {
            "reviews_evaluated": len(qa_reviews),
            "approved": 0,
            "rejected": 0,
            "needs_rework": []
        }

        for review in qa_reviews:
            if review["status"] == "approved":
                validation["approved"] += 1
            else:
                validation["rejected"] += 1
                validation["needs_rework"].append(review["reviews_implementation"])

        print(f"\n📈 Validation Results:")
        print(f"  Approved: {validation['approved']}")
        print(f"  Rejected: {validation['rejected']}")

        if validation["needs_rework"]:
            print(f"  Needs Rework: {', '.join(validation['needs_rework'])}")

        return validation

    async def check_consensus(self) -> Dict[str, Any]:
        """Check if all teams agree application is ready"""
        print(f"\n🔍 Checking consensus...")

        consensus = {
            "timestamp": datetime.now().isoformat(),
            "iteration": self.current_iteration,
            "team_votes": {},
            "consensus_reached": False,
            "readiness_criteria": {}
        }

        # Get votes from each team
        # Testing team: Check latest test results
        test_vote = await self._get_testing_vote()
        consensus["team_votes"]["testing"] = test_vote

        # Design team: Check if all critical issues have specs
        design_vote = await self._get_design_vote()
        consensus["team_votes"]["design"] = design_vote

        # Development team: Check if all specs implemented
        dev_vote = await self._get_development_vote()
        consensus["team_votes"]["development"] = dev_vote

        # QA team: Check readiness assessment
        qa_assessment = await self.qa_team.assess_overall_readiness()
        consensus["team_votes"]["qa"] = qa_assessment["vote"]
        consensus["readiness_criteria"] = qa_assessment["readiness_criteria"]

        # Check overall consensus
        all_ready = all(
            vote == "ready"
            for vote in consensus["team_votes"].values()
        )

        consensus["consensus_reached"] = all_ready

        # Save consensus check
        self.save_artifact(
            ".",
            consensus,
            f"consensus_check_iter_{self.current_iteration}.json"
        )

        print(f"\n  Team Votes:")
        for team, vote in consensus["team_votes"].items():
            status_icon = "✓" if vote == "ready" else "✗"
            print(f"    {status_icon} {team}: {vote}")

        print(f"\n  Overall Consensus: {'✓ REACHED' if all_ready else '✗ NOT YET'}")

        return consensus

    async def _get_testing_vote(self) -> str:
        """Get testing team vote"""
        # Check if latest test report shows acceptable results
        # For now, simplified check
        return "not_ready"  # Would check actual test results

    async def _get_design_vote(self) -> str:
        """Get design team vote"""
        # Check if all critical issues have been addressed with specs
        return "not_ready"  # Would check actual design status

    async def _get_development_vote(self) -> str:
        """Get development team vote"""
        # Check if all specs have been implemented
        return "not_ready"  # Would check actual implementation status

    async def get_loop_status(self) -> Dict[str, Any]:
        """Get current status of improvement loop"""
        return {
            "loop_running": self.loop_running,
            "current_iteration": self.current_iteration,
            "max_iterations": self.max_iterations,
            "consensus_reached": self.consensus_reached,
            "iterations_completed": len(self.iteration_history),
            "team_status": {
                "testing": self.testing_team.get_status(),
                "design": self.design_team.get_status(),
                "development": self.development_team.get_status(),
                "qa": self.qa_team.get_status()
            }
        }

    async def analyze_progress(self) -> Dict[str, Any]:
        """Analyze progress across iterations"""
        if not self.iteration_history:
            return {"message": "No iterations completed yet"}

        analysis = {
            "total_iterations": len(self.iteration_history),
            "issues_found": [],
            "issues_resolved": [],
            "trend": "unknown"
        }

        # Analyze issue trends
        for iteration in self.iteration_history:
            test_phase = iteration.get("phases", {}).get("testing", {})
            issues = test_phase.get("summary", {}).get("total_issues", 0)
            analysis["issues_found"].append(issues)

        # Determine trend
        if len(analysis["issues_found"]) >= 2:
            if analysis["issues_found"][-1] < analysis["issues_found"][0]:
                analysis["trend"] = "improving"
            elif analysis["issues_found"][-1] > analysis["issues_found"][0]:
                analysis["trend"] = "degrading"
            else:
                analysis["trend"] = "stable"

        return analysis

    def _update_team_iterations(self):
        """Update iteration number for all teams"""
        self.testing_team.current_iteration = self.current_iteration
        self.design_team.current_iteration = self.current_iteration
        self.development_team.current_iteration = self.current_iteration
        self.qa_team.current_iteration = self.current_iteration

    async def stop_loop(self):
        """Stop the improvement loop"""
        print(f"\n[{self.agent_id}] Stopping improvement loop...")
        self.loop_running = False
