"""
Integration Tests for AI-Powered API Endpoints

Tests the smart processing and AI service endpoints.

Run with: pytest tests/test_ai_endpoints.py -v
Or standalone: python tests/test_ai_endpoints.py
"""

import asyncio
import sys
from pathlib import Path

# Add project paths
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from httpx import AsyncClient, ASGITransport
from datetime import datetime


class TestAIEndpoints:
    """Test suite for AI-powered API endpoints"""

    @pytest.fixture
    def app(self):
        """Get FastAPI app instance"""
        from api_server.main import app
        return app

    @pytest.mark.asyncio
    async def test_ai_status(self, app):
        """Test AI status endpoint"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/ai/status")
            assert response.status_code == 200
            data = response.json()
            assert "available" in data
            assert "domains" in data
            assert "capabilities" in data
            print(f"AI Status: available={data['available']}, domains={len(data['domains'])}")

    @pytest.mark.asyncio
    async def test_ai_domains(self, app):
        """Test AI domains listing endpoint"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/ai/domains")

            if response.status_code == 503:
                pytest.skip("AI services not available")

            assert response.status_code == 200
            data = response.json()
            assert "domains" in data
            assert "finance" in data["domains"]
            assert "hr" in data["domains"]
            assert "operations" in data["domains"]
            print(f"Available domains: {list(data['domains'].keys())}")

    @pytest.mark.asyncio
    async def test_ai_process_finance(self, app):
        """Test AI processing for finance domain"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/ai/process", json={
                "domain": "finance",
                "task_type": "risk_assessment",
                "data": {
                    "portfolio_value": 100000,
                    "holdings": [
                        {"symbol": "AAPL", "allocation": 0.5},
                        {"symbol": "MSFT", "allocation": 0.5}
                    ]
                },
                "context": {"risk_tolerance": "moderate"}
            })

            if response.status_code == 503:
                pytest.skip("AI services not available")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"
            assert data["domain"] == "finance"
            assert data["ai_powered"] == True
            assert "result" in data
            print(f"Finance processing result: {data['result'].get('status', 'N/A')}")

    @pytest.mark.asyncio
    async def test_ai_process_hr(self, app):
        """Test AI processing for HR domain"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/ai/process", json={
                "domain": "hr",
                "task_type": "recruitment",
                "data": {
                    "position": "Software Engineer",
                    "candidates": 10,
                    "requirements": ["Python", "SQL"]
                },
                "context": {"urgency": "medium"}
            })

            if response.status_code == 503:
                pytest.skip("AI services not available")

            assert response.status_code == 200
            data = response.json()
            assert data["domain"] == "hr"
            assert data["ai_powered"] == True
            print(f"HR processing result: {data['result'].get('status', 'N/A')}")

    @pytest.mark.asyncio
    async def test_ai_process_operations(self, app):
        """Test AI processing for operations domain"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/ai/process", json={
                "domain": "operations",
                "task_type": "supply_chain",
                "data": {
                    "inventory_level": 500,
                    "demand_forecast": 1000
                },
                "context": {}
            })

            if response.status_code == 503:
                pytest.skip("AI services not available")

            assert response.status_code == 200
            data = response.json()
            assert data["domain"] == "operations"
            print(f"Operations processing result: {data['result'].get('status', 'N/A')}")

    @pytest.mark.asyncio
    async def test_ai_process_customer_service(self, app):
        """Test AI processing for customer service domain"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/ai/process", json={
                "domain": "customer_service",
                "task_type": "ticket_routing",
                "data": {
                    "ticket_subject": "Login issue",
                    "ticket_content": "Cannot access my account"
                },
                "context": {"channel": "email"}
            })

            if response.status_code == 503:
                pytest.skip("AI services not available")

            assert response.status_code == 200
            data = response.json()
            assert data["domain"] == "customer_service"
            print(f"Customer service result: {data['result'].get('status', 'N/A')}")

    @pytest.mark.asyncio
    async def test_ai_process_it(self, app):
        """Test AI processing for IT domain"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/ai/process", json={
                "domain": "it",
                "task_type": "incident",
                "data": {
                    "incident_type": "service_down",
                    "affected_systems": ["api-gateway"]
                },
                "context": {"severity": "high"}
            })

            if response.status_code == 503:
                pytest.skip("AI services not available")

            assert response.status_code == 200
            data = response.json()
            assert data["domain"] == "it"
            print(f"IT processing result: {data['result'].get('status', 'N/A')}")

    @pytest.mark.asyncio
    async def test_ai_analyze(self, app):
        """Test AI analysis endpoint"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/ai/analyze", json={
                "prompt": "Analyze this sales data for trends",
                "data": {
                    "sales": [
                        {"month": "Jan", "amount": 10000},
                        {"month": "Feb", "amount": 12000},
                        {"month": "Mar", "amount": 15000}
                    ]
                }
            })

            if response.status_code == 503:
                pytest.skip("AI services not available")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"
            assert data["ai_powered"] == True
            assert "analysis" in data
            print(f"Analysis result type: {type(data['analysis'])}")

    @pytest.mark.asyncio
    async def test_ai_recommend(self, app):
        """Test AI recommendations endpoint"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/ai/recommend", json={
                "context": {
                    "issue": "high customer churn",
                    "segment": "enterprise"
                },
                "constraints": ["budget under $50k"],
                "max_recommendations": 3
            })

            if response.status_code == 503:
                pytest.skip("AI services not available")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"
            assert "recommendations" in data
            assert len(data["recommendations"]) <= 3
            print(f"Recommendations count: {len(data['recommendations'])}")

    @pytest.mark.asyncio
    async def test_ai_agents_list(self, app):
        """Test AI agents listing endpoint"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/ai/agents")
            assert response.status_code == 200
            data = response.json()
            assert "total" in data
            assert "ai_powered_agents" in data
            print(f"AI-powered agents found: {data['total']}")

    @pytest.mark.asyncio
    async def test_ai_demo_finance(self, app):
        """Test AI demo endpoint for finance"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/ai/demo/finance")

            if response.status_code == 503:
                pytest.skip("AI services not available")

            assert response.status_code == 200
            data = response.json()
            assert data["domain"] == "finance"
            assert data["demo_scenario"] == "risk_assessment"
            assert data["ai_powered"] == True
            print(f"Finance demo completed: {data['status']}")

    @pytest.mark.asyncio
    async def test_ai_demo_invalid_domain(self, app):
        """Test AI demo endpoint with invalid domain"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/ai/demo/invalid_domain")

            if response.status_code == 503:
                pytest.skip("AI services not available")

            assert response.status_code == 400
            data = response.json()
            assert "Unknown domain" in data["detail"]


async def run_quick_test():
    """Run a quick standalone test"""
    print("=" * 60)
    print("AI Endpoints Quick Test")
    print("=" * 60)

    try:
        from api_server.main import app
        from httpx import AsyncClient, ASGITransport

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Test status
            print("\n1. Testing /api/ai/status...")
            response = await client.get("/api/ai/status")
            data = response.json()
            print(f"   Status: {response.status_code}")
            print(f"   AI Available: {data.get('available', 'N/A')}")
            print(f"   Domains: {data.get('domains', [])}")

            # Test domains
            print("\n2. Testing /api/ai/domains...")
            response = await client.get("/api/ai/domains")
            if response.status_code == 200:
                data = response.json()
                print(f"   Status: {response.status_code}")
                print(f"   Total domains: {data.get('total', 0)}")
            else:
                print(f"   Status: {response.status_code} (AI services may not be available)")

            # Test AI agents list
            print("\n3. Testing /api/ai/agents...")
            response = await client.get("/api/ai/agents")
            data = response.json()
            print(f"   Status: {response.status_code}")
            print(f"   AI-powered agents: {data.get('total', 0)}")

            # Test demo
            print("\n4. Testing /api/ai/demo/finance...")
            response = await client.post("/api/ai/demo/finance")
            if response.status_code == 200:
                data = response.json()
                print(f"   Status: {response.status_code}")
                print(f"   Demo result: {data.get('status', 'N/A')}")
                print(f"   AI-powered: {data.get('ai_powered', False)}")
            else:
                print(f"   Status: {response.status_code} (Demo may require AI services)")

        print("\n" + "=" * 60)
        print("Quick test completed!")
        print("=" * 60)

    except ImportError as e:
        print(f"\nError: Could not import required modules: {e}")
        print("Make sure you're running from the project root directory.")
    except Exception as e:
        print(f"\nError during test: {e}")


if __name__ == "__main__":
    # Run quick test when executed directly
    asyncio.run(run_quick_test())
