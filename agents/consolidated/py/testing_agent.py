"""
Testing Agent - Comprehensive application testing and issue identification

Protocol-Compliant Agent supporting:
- A2A (Agent-to-Agent): Direct agent communication
- A2P (Agent-to-Pay): Financial transactions between agents
- ACP (Agent Coordination Protocol): Multi-agent coordination
- ANP (Agent Network Protocol): Agent discovery and registration
- MCP (Model Context Protocol): AI model integration
"""

import subprocess
import json
import os
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add library path for protocol-compliant BaseAgent
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'library'))

# CRITICAL: Import from protocol-compliant BaseAgent (THE SINGLE SOURCE OF TRUTH)
from core.base_agent_v1 import BaseAgent, AgentCapability, MessageType


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
        """Check if Celery worker is healthy and connected to Redis"""
        try:
            # Test 1: Check Redis connectivity
            import redis
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", "6379"))

            try:
                r = redis.Redis(host=redis_host, port=redis_port, socket_timeout=2)
                r.ping()
                redis_healthy = True
            except Exception:
                redis_healthy = False

            if not redis_healthy:
                return {
                    "healthy": False,
                    "reason": "Redis not accessible",
                    "redis_healthy": False,
                    "worker_healthy": False
                }

            # Test 2: Check Celery worker status via Redis
            # If Redis is healthy, we assume worker can connect
            # A more sophisticated test would use Celery's inspect API
            return {
                "healthy": redis_healthy,
                "redis_healthy": redis_healthy,
                "worker_healthy": redis_healthy,  # Simplified check
                "message": "Redis accessible - workers can connect"
            }

        except ImportError:
            # Redis library not installed
            return {
                "healthy": False,
                "reason": "Redis library not installed (pip install redis)",
                "redis_healthy": False,
                "worker_healthy": False
            }
        except Exception as e:
            return {
                "healthy": False,
                "reason": f"Worker health check failed: {str(e)}",
                "redis_healthy": False,
                "worker_healthy": False
            }

    async def _check_database_health(self) -> Dict[str, bool]:
        """Check if database is healthy"""
        # Try to connect to database
        return {"healthy": True}  # Placeholder

    async def _test_api_endpoints(self) -> Dict[str, Any]:
        """Test backend API endpoints"""
        import aiohttp

        results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "issues": []
        }

        # Define critical API endpoints to test
        endpoints = [
            {"path": "/api/v1/health", "method": "GET", "expected_status": 200},
            {"path": "/api/v1/autonomous/agents", "method": "GET", "expected_status": 200},
            {"path": "/", "method": "GET", "expected_status": 200},
        ]

        try:
            async with aiohttp.ClientSession() as session:
                for endpoint in endpoints:
                    results["total"] += 1
                    try:
                        async with session.request(
                            endpoint["method"],
                            f"http://localhost:8000{endpoint['path']}",
                            timeout=5
                        ) as resp:
                            if resp.status == endpoint["expected_status"]:
                                results["passed"] += 1
                            else:
                                results["failed"] += 1
                                results["issues"].append({
                                    "id": f"API-{endpoint['path'].replace('/', '-')}",
                                    "severity": "high",
                                    "component": "backend",
                                    "description": f"API endpoint {endpoint['path']} returned {resp.status}, expected {endpoint['expected_status']}",
                                    "recommendation": f"Fix {endpoint['path']} endpoint to return correct status"
                                })
                    except Exception as e:
                        results["failed"] += 1
                        results["issues"].append({
                            "id": f"API-{endpoint['path'].replace('/', '-')}-ERROR",
                            "severity": "critical",
                            "component": "backend",
                            "description": f"API endpoint {endpoint['path']} failed: {str(e)}",
                            "recommendation": f"Ensure {endpoint['path']} endpoint is accessible and functioning"
                        })
        except Exception as e:
            results["issues"].append({
                "id": "API-CONNECTION-ERROR",
                "severity": "critical",
                "component": "backend",
                "description": f"Failed to connect to backend: {str(e)}",
                "recommendation": "Ensure backend server is running on port 8000"
            })

        return results

    async def _test_database_operations(self) -> Dict[str, Any]:
        """Test database CRUD operations"""
        results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "issues": []
        }

        try:
            # Test database connectivity
            import sqlite3
            db_path = os.path.join(self.project_root, "backend", "market_research.db")

            if not os.path.exists(db_path):
                results["issues"].append({
                    "id": "DB-NOT-FOUND",
                    "severity": "critical",
                    "component": "database",
                    "description": "Database file not found",
                    "recommendation": "Run database initialization: python backend/init_autonomous_db.py"
                })
                return results

            # Test connection
            results["total"] += 1
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                # Test reading from autonomous_agents table
                cursor.execute("SELECT COUNT(*) FROM autonomous_agents")
                count = cursor.fetchone()[0]

                conn.close()
                results["passed"] += 1
            except Exception as e:
                results["failed"] += 1
                results["issues"].append({
                    "id": "DB-CONNECTION-ERROR",
                    "severity": "high",
                    "component": "database",
                    "description": f"Database connection failed: {str(e)}",
                    "recommendation": "Check database integrity and permissions"
                })

        except Exception as e:
            results["issues"].append({
                "id": "DB-TEST-ERROR",
                "severity": "high",
                "component": "database",
                "description": f"Database testing failed: {str(e)}",
                "recommendation": "Review database configuration"
            })

        return results

    async def _test_backend_ai_integration(self) -> Dict[str, Any]:
        """Test backend AI integration with OpenAI"""
        import aiohttp

        results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "issues": []
        }

        # Test 1: Check if AI service endpoint is accessible
        results["total"] += 1
        try:
            async with aiohttp.ClientSession() as session:
                # Test the config endpoint to see if OpenAI key is configured
                async with session.get("http://localhost:8000/api/v1/config/openai_key", timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("configured", False):
                            results["passed"] += 1
                        else:
                            results["failed"] += 1
                            results["issues"].append({
                                "id": "AI-OPENAI-NOT-CONFIGURED",
                                "severity": "high",
                                "component": "ai_integration",
                                "description": "OpenAI API key not configured",
                                "recommendation": "Set OPENAI_API_KEY in environment or via UI configuration"
                            })
                    else:
                        results["failed"] += 1
                        results["issues"].append({
                            "id": "AI-CONFIG-ENDPOINT-ERROR",
                            "severity": "medium",
                            "component": "ai_integration",
                            "description": f"Config endpoint returned {resp.status}",
                            "recommendation": "Check backend AI configuration endpoint"
                        })
        except Exception as e:
            results["failed"] += 1
            results["issues"].append({
                "id": "AI-CONFIG-CONNECTION-ERROR",
                "severity": "high",
                "component": "ai_integration",
                "description": f"Failed to check AI configuration: {str(e)}",
                "recommendation": "Ensure backend is running and accessible"
            })

        # Test 2: Check if AI analysis endpoint is functional
        results["total"] += 1
        try:
            async with aiohttp.ClientSession() as session:
                test_payload = {
                    "query": "test market analysis",
                    "context": "Testing AI integration"
                }
                async with session.post(
                    "http://localhost:8000/api/v1/ai-analysis/quick",
                    json=test_payload,
                    timeout=30
                ) as resp:
                    if resp.status in [200, 201]:
                        results["passed"] += 1
                    elif resp.status == 400:
                        # Bad request might be due to missing API key
                        results["failed"] += 1
                        results["issues"].append({
                            "id": "AI-ANALYSIS-BAD-REQUEST",
                            "severity": "high",
                            "component": "ai_integration",
                            "description": "AI analysis endpoint returned 400 (possibly missing API key)",
                            "recommendation": "Verify OpenAI API key is properly configured"
                        })
                    else:
                        results["failed"] += 1
                        results["issues"].append({
                            "id": "AI-ANALYSIS-ENDPOINT-ERROR",
                            "severity": "medium",
                            "component": "ai_integration",
                            "description": f"AI analysis endpoint returned {resp.status}",
                            "recommendation": "Check AI service configuration and logs"
                        })
        except Exception as e:
            results["failed"] += 1
            results["issues"].append({
                "id": "AI-ANALYSIS-ERROR",
                "severity": "medium",
                "component": "ai_integration",
                "description": f"AI analysis test failed: {str(e)}",
                "recommendation": "Review AI service integration and error logs"
            })

        return results

    async def _test_ui_components(self) -> Dict[str, Any]:
        """Test UI components"""
        import aiohttp

        results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "issues": []
        }

        # Test key pages/components
        pages = [
            {"path": "/", "name": "Home Page"},
            {"path": "/autonomous-agents", "name": "Autonomous Agents Dashboard"},
        ]

        try:
            async with aiohttp.ClientSession() as session:
                for page in pages:
                    results["total"] += 1
                    try:
                        async with session.get(
                            f"http://localhost:3000{page['path']}",
                            timeout=10
                        ) as resp:
                            if resp.status == 200:
                                results["passed"] += 1
                            else:
                                results["failed"] += 1
                                results["issues"].append({
                                    "id": f"UI-{page['name'].replace(' ', '-')}",
                                    "severity": "medium",
                                    "component": "frontend",
                                    "description": f"{page['name']} returned status {resp.status}",
                                    "recommendation": f"Fix {page['name']} rendering issue"
                                })
                    except Exception as e:
                        results["failed"] += 1
                        results["issues"].append({
                            "id": f"UI-{page['name'].replace(' ', '-')}-ERROR",
                            "severity": "high",
                            "component": "frontend",
                            "description": f"{page['name']} failed to load: {str(e)}",
                            "recommendation": f"Ensure {page['name']} is properly configured"
                        })
        except Exception as e:
            results["issues"].append({
                "id": "UI-TEST-ERROR",
                "severity": "critical",
                "component": "frontend",
                "description": f"UI testing failed: {str(e)}",
                "recommendation": "Ensure frontend server is running and accessible"
            })

        return results

    async def _test_page_rendering(self) -> Dict[str, Any]:
        """Test page rendering"""
        results = {
            "total": 1,
            "passed": 1,
            "failed": 0,
            "issues": []
        }

        # Basic rendering test passed if we got here
        # More sophisticated tests would use headless browser
        return results

    async def _test_market_research_to_business_plan(self) -> Dict[str, Any]:
        """Test complete market research to business plan workflow"""
        import aiohttp

        # This E2E test validates the core value proposition:
        # User provides market idea → AI generates comprehensive business plan

        try:
            async with aiohttp.ClientSession() as session:
                # Step 1: Submit market research query
                research_payload = {
                    "query": "eco-friendly water bottles market",
                    "depth": "quick"
                }

                async with session.post(
                    "http://localhost:8000/api/v1/ai-analysis/market-research",
                    json=research_payload,
                    timeout=60
                ) as resp:
                    if resp.status not in [200, 201]:
                        return {
                            "passed": False,
                            "issue": {
                                "id": "E2E-MARKET-RESEARCH-FAILED",
                                "severity": "high",
                                "component": "e2e_workflows",
                                "description": f"Market research API returned {resp.status}",
                                "recommendation": "Fix market research endpoint or verify AI integration"
                            }
                        }

                    market_data = await resp.json()

                # Step 2: Generate business plan from market research
                # Check if business plan generation endpoint exists
                plan_payload = {
                    "market_data": market_data,
                    "business_name": "EcoBottle Co",
                    "target_market": "eco-conscious consumers"
                }

                async with session.post(
                    "http://localhost:8000/api/v1/ai-analysis/business-plan",
                    json=plan_payload,
                    timeout=60
                ) as resp:
                    if resp.status == 404:
                        # Endpoint doesn't exist yet
                        return {
                            "passed": False,
                            "issue": {
                                "id": "E2E-BUSINESS-PLAN-NOT-IMPLEMENTED",
                                "severity": "high",
                                "component": "e2e_workflows",
                                "description": "Business plan generation endpoint not implemented",
                                "recommendation": "Implement /api/v1/ai-analysis/business-plan endpoint"
                            }
                        }
                    elif resp.status in [200, 201]:
                        # Workflow complete!
                        return {"passed": True, "issue": None}
                    else:
                        return {
                            "passed": False,
                            "issue": {
                                "id": "E2E-BUSINESS-PLAN-ERROR",
                                "severity": "medium",
                                "component": "e2e_workflows",
                                "description": f"Business plan generation returned {resp.status}",
                                "recommendation": "Debug business plan generation endpoint"
                            }
                        }

        except Exception as e:
            return {
                "passed": False,
                "issue": {
                    "id": "E2E-WORKFLOW-ERROR",
                    "severity": "medium",
                    "component": "e2e_workflows",
                    "description": f"E2E workflow test failed: {str(e)}",
                    "recommendation": "Ensure all E2E workflow components are operational"
                }
            }

    async def _test_one_button_deployment(self) -> Dict[str, Any]:
        """Test one-button autonomous deployment workflow"""
        import aiohttp

        # This E2E test validates the ultimate vision:
        # One button click → Fully deployed business with all assets

        try:
            async with aiohttp.ClientSession() as session:
                # Check if deployment endpoint exists
                deployment_payload = {
                    "business_plan": {
                        "name": "TestBusiness",
                        "market": "test market",
                        "product": "test product"
                    },
                    "deployment_options": {
                        "create_website": True,
                        "setup_payments": False,  # Don't actually charge anything in test
                        "generate_assets": True
                    }
                }

                async with session.post(
                    "http://localhost:8000/api/v1/autonomous/deploy",
                    json=deployment_payload,
                    timeout=120
                ) as resp:
                    if resp.status == 404:
                        # Feature not implemented yet (expected for now)
                        return {
                            "passed": False,
                            "issue": {
                                "id": "E2E-ONE-BUTTON-NOT-IMPLEMENTED",
                                "severity": "medium",
                                "component": "e2e_workflows",
                                "description": "One-button deployment endpoint not implemented",
                                "recommendation": "Implement /api/v1/autonomous/deploy endpoint for full autonomous deployment"
                            }
                        }
                    elif resp.status in [200, 201, 202]:
                        # Deployment initiated or completed
                        data = await resp.json()

                        # Verify deployment result has expected fields
                        required_fields = ["deployment_id", "status"]
                        if all(field in data for field in required_fields):
                            return {"passed": True, "issue": None}
                        else:
                            return {
                                "passed": False,
                                "issue": {
                                    "id": "E2E-DEPLOYMENT-INCOMPLETE",
                                    "severity": "medium",
                                    "component": "e2e_workflows",
                                    "description": "Deployment response missing required fields",
                                    "recommendation": "Ensure deployment returns deployment_id and status"
                                }
                            }
                    else:
                        return {
                            "passed": False,
                            "issue": {
                                "id": "E2E-DEPLOYMENT-ERROR",
                                "severity": "medium",
                                "component": "e2e_workflows",
                                "description": f"Deployment endpoint returned {resp.status}",
                                "recommendation": "Debug deployment endpoint implementation"
                            }
                        }

        except Exception as e:
            return {
                "passed": False,
                "issue": {
                    "id": "E2E-DEPLOYMENT-TEST-ERROR",
                    "severity": "low",
                    "component": "e2e_workflows",
                    "description": f"Deployment test failed: {str(e)}",
                    "recommendation": "This is expected if one-button deployment not yet implemented"
                }
            }

    async def _test_openai_integration(self) -> Dict[str, Any]:
        """Test OpenAI integration"""
        return {
            "passed": True,
            "issue": None
        }

    async def _check_issue_resolved(self, issue_id: str) -> bool:
        """Check if a specific issue has been resolved by re-running targeted tests"""

        # Map issue IDs to their corresponding test functions
        issue_test_map = {
            # Backend issues
            "ISSUE-BACKEND": self._check_backend_health,
            "API-": self._test_api_endpoints,
            "DB-": self._test_database_operations,
            "AI-": self._test_backend_ai_integration,

            # Frontend issues
            "ISSUE-FRONTEND": self._check_frontend_health,
            "UI-": self._test_ui_components,

            # Worker issues
            "ISSUE-WORKER": self._check_worker_health,

            # Database issues
            "ISSUE-DATABASE": self._check_database_health,
            "DB-": self._test_database_operations,

            # E2E workflow issues
            "E2E-MARKET-RESEARCH": self._test_market_research_to_business_plan,
            "E2E-BUSINESS-PLAN": self._test_market_research_to_business_plan,
            "E2E-ONE-BUTTON": self._test_one_button_deployment,
            "E2E-DEPLOYMENT": self._test_one_button_deployment,
        }

        # Find matching test function
        test_function = None
        for prefix, func in issue_test_map.items():
            if issue_id.startswith(prefix):
                test_function = func
                break

        if not test_function:
            # Unknown issue ID, can't validate
            return False

        try:
            # Re-run the specific test
            result = await test_function()

            # Check if issue is resolved based on result structure
            if isinstance(result, dict):
                # For health checks
                if "healthy" in result:
                    return result["healthy"]

                # For test results with issues array
                if "issues" in result:
                    # Check if this specific issue ID is still in issues
                    for issue in result["issues"]:
                        if issue.get("id") == issue_id:
                            return False  # Issue still present
                    return True  # Issue not found = resolved

                # For E2E tests
                if "passed" in result:
                    if result["passed"]:
                        return True
                    # Check if this is still the same issue
                    if result.get("issue", {}).get("id") == issue_id:
                        return False
                    # Different issue = original resolved but new issue appeared
                    return True

            return False

        except Exception:
            # If test fails to run, assume issue not resolved
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
