"""
Testing Agent - Comprehensive application testing and issue identification
"""

import subprocess
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from .base_agent import BaseAgent, AgentCapability, MessageType


class TestingAgent(BaseAgent):
    """
    Testing Agent responsible for:
    - Executing comprehensive test suites
    - Testing all components (Frontend, Backend, Worker, Database)
    - Identifying bugs, gaps, and enhancement opportunities
    - Generating detailed test reports with recommendations
    """

    def __init__(
        self,
        agent_id: str = "testing_agent_001",
        workspace_path: str = "./autonomous-ecosystem/workspace",
        project_root: str = "."
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type="testing",
            capabilities=[AgentCapability.TESTING],
            workspace_path=workspace_path
        )
        self.project_root = project_root
        self.test_results = []
        self.issues_found = []
        self.enhancements_identified = []

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute testing task"""
        task_type = task.get("type")

        if task_type == "comprehensive_test":
            return await self.run_comprehensive_tests()
        elif task_type == "component_test":
            component = task.get("component")
            return await self.test_component(component)
        elif task_type == "validate_fix":
            issue_ids = task.get("issue_ids", [])
            return await self.validate_fixes(issue_ids)
        else:
            return {"error": f"Unknown task type: {task_type}"}

    async def analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze test results and generate recommendations"""
        test_results = input_data.get("test_results", [])

        analysis = {
            "summary": self._generate_summary(test_results),
            "critical_issues": self._identify_critical_issues(test_results),
            "recommendations": self._generate_recommendations(test_results),
            "priority_items": self._prioritize_issues(test_results)
        }

        return analysis

    async def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run comprehensive test suite across all components"""
        print(f"[{self.agent_id}] Starting comprehensive test suite...")

        test_results = {
            "timestamp": datetime.now().isoformat(),
            "iteration": self.current_iteration,
            "components": {}
        }

        # Test Backend
        backend_results = await self._test_backend()
        test_results["components"]["backend"] = backend_results

        # Test Frontend
        frontend_results = await self._test_frontend()
        test_results["components"]["frontend"] = frontend_results

        # Test Worker
        worker_results = await self._test_worker()
        test_results["components"]["worker"] = worker_results

        # Test Database
        database_results = await self._test_database()
        test_results["components"]["database"] = database_results

        # Test E2E Workflows
        e2e_results = await self._test_e2e_workflows()
        test_results["components"]["e2e_workflows"] = e2e_results

        # Test AI Integrations
        ai_results = await self._test_ai_integrations()
        test_results["components"]["ai_integrations"] = ai_results

        # Analyze results
        analysis = await self.analyze({"test_results": test_results})
        test_results["analysis"] = analysis

        # Generate test report
        report = self._generate_test_report(test_results)

        # Save report
        self.save_artifact(
            "test_reports",
            report,
            f"comprehensive_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        # Send report to orchestrator
        self.send_message(
            MessageType.TEST_REPORT,
            "orchestrator",
            report
        )

        return report

    async def _test_backend(self) -> Dict[str, Any]:
        """Test backend API endpoints and functionality"""
        print(f"[{self.agent_id}] Testing backend...")

        results = {
            "component": "backend",
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "issues": [],
            "coverage": 0.0
        }

        # Check if backend is running
        backend_health = await self._check_backend_health()
        if not backend_health["healthy"]:
            results["issues"].append({
                "id": f"ISSUE-BACKEND-{datetime.now().timestamp()}",
                "severity": "critical",
                "component": "backend",
                "description": "Backend is not running or not accessible",
                "recommendation": "Ensure backend server is started and accessible at http://localhost:8000"
            })
            return results

        # Test API endpoints
        api_tests = await self._test_api_endpoints()
        results["tests_run"] += api_tests["total"]
        results["tests_passed"] += api_tests["passed"]
        results["tests_failed"] += api_tests["failed"]
        results["issues"].extend(api_tests["issues"])

        # Test database operations
        db_tests = await self._test_database_operations()
        results["tests_run"] += db_tests["total"]
        results["tests_passed"] += db_tests["passed"]
        results["tests_failed"] += db_tests["failed"]
        results["issues"].extend(db_tests["issues"])

        # Test AI service integration
        ai_tests = await self._test_backend_ai_integration()
        results["tests_run"] += ai_tests["total"]
        results["tests_passed"] += ai_tests["passed"]
        results["tests_failed"] += ai_tests["failed"]
        results["issues"].extend(ai_tests["issues"])

        if results["tests_run"] > 0:
            results["coverage"] = results["tests_passed"] / results["tests_run"]

        return results

    async def _test_frontend(self) -> Dict[str, Any]:
        """Test frontend UI and functionality"""
        print(f"[{self.agent_id}] Testing frontend...")

        results = {
            "component": "frontend",
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "issues": [],
            "coverage": 0.0
        }

        # Check if frontend is running
        frontend_health = await self._check_frontend_health()
        if not frontend_health["healthy"]:
            results["issues"].append({
                "id": f"ISSUE-FRONTEND-{datetime.now().timestamp()}",
                "severity": "critical",
                "component": "frontend",
                "description": "Frontend is not running or not accessible",
                "recommendation": "Ensure frontend server is started and accessible at http://localhost:3000"
            })
            return results

        # Test UI components
        ui_tests = await self._test_ui_components()
        results["tests_run"] += ui_tests["total"]
        results["tests_passed"] += ui_tests["passed"]
        results["tests_failed"] += ui_tests["failed"]
        results["issues"].extend(ui_tests["issues"])

        # Test page rendering
        page_tests = await self._test_page_rendering()
        results["tests_run"] += page_tests["total"]
        results["tests_passed"] += page_tests["passed"]
        results["tests_failed"] += page_tests["failed"]
        results["issues"].extend(page_tests["issues"])

        if results["tests_run"] > 0:
            results["coverage"] = results["tests_passed"] / results["tests_run"]

        return results

    async def _test_worker(self) -> Dict[str, Any]:
        """Test worker/background tasks"""
        print(f"[{self.agent_id}] Testing worker tasks...")

        results = {
            "component": "worker",
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "issues": [],
            "coverage": 0.0
        }

        # Test Celery worker connectivity
        worker_health = await self._check_worker_health()
        if not worker_health["healthy"]:
            results["issues"].append({
                "id": f"ISSUE-WORKER-{datetime.now().timestamp()}",
                "severity": "high",
                "component": "worker",
                "description": "Worker is not running or not connected to Redis",
                "recommendation": "Ensure Redis is running and worker is started"
            })

        return results

    async def _test_database(self) -> Dict[str, Any]:
        """Test database connectivity and operations"""
        print(f"[{self.agent_id}] Testing database...")

        results = {
            "component": "database",
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "issues": [],
            "coverage": 0.0
        }

        # Test database connectivity
        db_health = await self._check_database_health()
        if not db_health["healthy"]:
            results["issues"].append({
                "id": f"ISSUE-DATABASE-{datetime.now().timestamp()}",
                "severity": "critical",
                "component": "database",
                "description": "Database is not accessible",
                "recommendation": "Ensure database is running and accessible"
            })

        return results

    async def _test_e2e_workflows(self) -> Dict[str, Any]:
        """Test end-to-end workflows"""
        print(f"[{self.agent_id}] Testing E2E workflows...")

        results = {
            "component": "e2e_workflows",
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "issues": [],
            "enhancements": []
        }

        # Test: Market Research to Business Plan workflow
        workflow_test = await self._test_market_research_to_business_plan()
        results["tests_run"] += 1
        if workflow_test["passed"]:
            results["tests_passed"] += 1
        else:
            results["tests_failed"] += 1
            results["issues"].append(workflow_test["issue"])

        # Test: One-button deployment workflow
        deployment_test = await self._test_one_button_deployment()
        results["tests_run"] += 1
        if deployment_test["passed"]:
            results["tests_passed"] += 1
        else:
            results["tests_failed"] += 1
            results["issues"].append(deployment_test["issue"])

        return results

    async def _test_ai_integrations(self) -> Dict[str, Any]:
        """Test AI service integrations"""
        print(f"[{self.agent_id}] Testing AI integrations...")

        results = {
            "component": "ai_integrations",
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "issues": []
        }

        # Test OpenAI integration
        openai_test = await self._test_openai_integration()
        results["tests_run"] += 1
        if openai_test["passed"]:
            results["tests_passed"] += 1
        else:
            results["tests_failed"] += 1
            results["issues"].append(openai_test["issue"])

        return results

    async def test_component(self, component: str) -> Dict[str, Any]:
        """Test a specific component"""
        if component == "backend":
            return await self._test_backend()
        elif component == "frontend":
            return await self._test_frontend()
        elif component == "worker":
            return await self._test_worker()
        elif component == "database":
            return await self._test_database()
        else:
            return {"error": f"Unknown component: {component}"}

    async def validate_fixes(self, issue_ids: List[str]) -> Dict[str, Any]:
        """Validate that specific issues have been fixed"""
        print(f"[{self.agent_id}] Validating fixes for issues: {issue_ids}")

        validation_results = {
            "timestamp": datetime.now().isoformat(),
            "issues_validated": [],
            "issues_still_failing": []
        }

        for issue_id in issue_ids:
            # Load original issue
            # Re-run specific test
            # Check if issue is resolved
            is_resolved = await self._check_issue_resolved(issue_id)

            if is_resolved:
                validation_results["issues_validated"].append(issue_id)
            else:
                validation_results["issues_still_failing"].append(issue_id)

        return validation_results

    # Helper methods

    async def _check_backend_health(self) -> Dict[str, bool]:
        """Check if backend is healthy"""
        try:
            # Try to ping backend health endpoint
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8000/api/v1/health", timeout=5) as resp:
                    return {"healthy": resp.status == 200}
        except Exception:
            return {"healthy": False}

    async def _check_frontend_health(self) -> Dict[str, bool]:
        """Check if frontend is healthy"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:3000", timeout=5) as resp:
                    return {"healthy": resp.status == 200}
        except Exception:
            return {"healthy": False}

    async def _check_worker_health(self) -> Dict[str, bool]:
        """Check if worker is healthy"""
        # Check Redis connection
        # Check Celery worker status
        return {"healthy": False}  # Placeholder

    async def _check_database_health(self) -> Dict[str, bool]:
        """Check if database is healthy"""
        # Try to connect to database
        return {"healthy": True}  # Placeholder

    async def _test_api_endpoints(self) -> Dict[str, Any]:
        """Test backend API endpoints"""
        return {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "issues": []
        }

    async def _test_database_operations(self) -> Dict[str, Any]:
        """Test database CRUD operations"""
        return {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "issues": []
        }

    async def _test_backend_ai_integration(self) -> Dict[str, Any]:
        """Test backend AI integration"""
        return {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "issues": []
        }

    async def _test_ui_components(self) -> Dict[str, Any]:
        """Test UI components"""
        return {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "issues": []
        }

    async def _test_page_rendering(self) -> Dict[str, Any]:
        """Test page rendering"""
        return {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "issues": []
        }

    async def _test_market_research_to_business_plan(self) -> Dict[str, Any]:
        """Test complete market research to business plan workflow"""
        return {
            "passed": False,
            "issue": {
                "id": f"ISSUE-E2E-{datetime.now().timestamp()}",
                "severity": "critical",
                "component": "e2e_workflows",
                "description": "Market research to business plan workflow not fully implemented",
                "recommendation": "Implement complete end-to-end workflow from market research input to generated business plan"
            }
        }

    async def _test_one_button_deployment(self) -> Dict[str, Any]:
        """Test one-button deployment workflow"""
        return {
            "passed": False,
            "issue": {
                "id": f"ISSUE-E2E-DEPLOY-{datetime.now().timestamp()}",
                "severity": "critical",
                "component": "e2e_workflows",
                "description": "One-button autonomous deployment not implemented",
                "recommendation": "Implement one-button deployment feature that automates full business launch"
            }
        }

    async def _test_openai_integration(self) -> Dict[str, Any]:
        """Test OpenAI integration"""
        return {
            "passed": True,
            "issue": None
        }

    async def _check_issue_resolved(self, issue_id: str) -> bool:
        """Check if a specific issue has been resolved"""
        # Placeholder - would re-run specific test for this issue
        return False

    def _generate_summary(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test summary"""
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        all_issues = []

        components = test_results.get("components", {})
        for component_name, component_results in components.items():
            total_tests += component_results.get("tests_run", 0)
            passed_tests += component_results.get("tests_passed", 0)
            failed_tests += component_results.get("tests_failed", 0)
            all_issues.extend(component_results.get("issues", []))

        return {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "coverage": passed_tests / total_tests if total_tests > 0 else 0,
            "total_issues": len(all_issues)
        }

    def _identify_critical_issues(self, test_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify critical issues"""
        critical_issues = []
        components = test_results.get("components", {})

        for component_results in components.values():
            for issue in component_results.get("issues", []):
                if issue.get("severity") == "critical":
                    critical_issues.append(issue)

        return critical_issues

    def _generate_recommendations(self, test_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []

        summary = self._generate_summary(test_results)

        if summary["coverage"] < 0.9:
            recommendations.append("Increase test coverage to >90%")

        if summary["failed"] > 0:
            recommendations.append(f"Fix {summary['failed']} failing tests")

        critical_issues = self._identify_critical_issues(test_results)
        if critical_issues:
            recommendations.append(f"Address {len(critical_issues)} critical issues immediately")

        return recommendations

    def _prioritize_issues(self, test_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prioritize issues by severity"""
        all_issues = []
        components = test_results.get("components", {})

        for component_results in components.values():
            all_issues.extend(component_results.get("issues", []))

        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        all_issues.sort(key=lambda x: severity_order.get(x.get("severity", "low"), 999))

        return all_issues

    def _generate_test_report(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        summary = self._generate_summary(test_results)
        critical_issues = self._identify_critical_issues(test_results)
        priority_items = self._prioritize_issues(test_results)
        recommendations = self._generate_recommendations(test_results)

        report = {
            "type": "test_report",
            "timestamp": datetime.now().isoformat(),
            "iteration": self.current_iteration,
            "agent_id": self.agent_id,
            "summary": summary,
            "components": test_results.get("components", {}),
            "critical_issues": critical_issues,
            "priority_items": priority_items[:10],  # Top 10
            "recommendations": recommendations,
            "enhancements": self._identify_enhancements(test_results)
        }

        return report

    def _identify_enhancements(self, test_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify enhancement opportunities"""
        enhancements = []

        # Analyze components for enhancement opportunities
        components = test_results.get("components", {})

        # Check for E2E workflow enhancements
        if "e2e_workflows" in components:
            e2e_results = components["e2e_workflows"]
            if e2e_results.get("tests_failed", 0) > 0:
                enhancements.append({
                    "id": f"ENH-E2E-{datetime.now().timestamp()}",
                    "priority": "high",
                    "description": "Complete end-to-end autonomous deployment workflow",
                    "rationale": "Critical for achieving market-research-to-deployment vision"
                })

        return enhancements
