#!/usr/bin/env python3
"""
Test Script for SuperStandard PCF Agent API

Tests all major API endpoints to verify functionality.

Usage:
    # Start the API server first:
    python scripts/run_api.py

    # Then in another terminal:
    python scripts/test_api.py
"""

import sys
import asyncio
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

try:
    import httpx
except ImportError:
    print("Error: httpx not installed")
    print("Install with: pip install httpx")
    sys.exit(1)


async def test_api():
    """Test all API endpoints"""
    base_url = "http://localhost:8000"

    print("=" * 80)
    print("SuperStandard PCF Agent API Test Suite")
    print("=" * 80)
    print()

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test 1: Health Check
        print("Test 1: Health Check")
        print("-" * 40)
        try:
            response = await client.get(f"{base_url}/api/health")
            response.raise_for_status()
            data = response.json()
            print(f"✓ Status: {data['status']}")
            print(f"✓ Version: {data['version']}")
            print(f"✓ Agents Available: {data['agents_available']}")
            print(f"✓ Uptime: {data['uptime_seconds']}s")
            print()
        except Exception as e:
            print(f"✗ Failed: {e}")
            print()

        # Test 2: Get Agent Metadata
        print("Test 2: Get Agent Metadata (1.1.1.1)")
        print("-" * 40)
        try:
            response = await client.get(f"{base_url}/api/pcf/1.1.1.1")
            response.raise_for_status()
            data = response.json()
            print(f"✓ Hierarchy ID: {data['hierarchy_id']}")
            print(f"✓ PCF Element ID: {data['pcf_element_id']}")
            print(f"✓ Name: {data['name']}")
            print(f"✓ Level: {data['level']} ({data['level_name']})")
            print(f"✓ Inputs: {len(data['inputs'])} defined")
            print(f"✓ Outputs: {len(data['outputs'])} defined")
            print(f"✓ KPIs: {len(data['kpis'])} defined")
            print()
        except Exception as e:
            print(f"✗ Failed: {e}")
            print()

        # Test 3: Execute Agent
        print("Test 3: Execute Agent (1.1.1.1 Identify Competitors)")
        print("-" * 40)
        try:
            request_body = {
                "input_data": {
                    "market_segment": "Cloud Infrastructure",
                    "geographic_scope": "North America",
                    "industry_focus": ["Technology", "SaaS"],
                    "company_size_filter": "enterprise"
                },
                "delegate_to_children": False,
                "track_kpis": True,
                "correlation_id": "test-correlation-123"
            }

            response = await client.post(
                f"{base_url}/api/pcf/1.1.1.1/execute",
                json=request_body
            )
            response.raise_for_status()
            data = response.json()

            print(f"✓ Execution ID: {data['execution_id']}")
            print(f"✓ Status: {data['status']}")
            print(f"✓ Success: {data['success']}")
            print(f"✓ Agent: {data['agent_name']}")
            print(f"✓ Execution Time: {data['execution_time_ms']}ms")

            # Check result
            if data['result']:
                result = data['result']
                print(f"\nResult Details:")
                print(f"  - Competitors Found: {result.get('competitors_count', 'N/A')}")

                if 'competitive_landscape' in result:
                    landscape = result['competitive_landscape']
                    print(f"  - Market Structure: {landscape.get('market_structure', 'N/A')}")
                    print(f"  - HHI: {landscape.get('hhi', 'N/A')}")
                    print(f"  - CR4: {landscape.get('cr4', 'N/A')}")

                if 'threat_assessment' in result:
                    threat = result['threat_assessment']
                    print(f"  - Threat Level: {threat.get('overall_threat_level', 'N/A')}")

            # Check KPIs
            if data['kpis']:
                print(f"\nKPIs Tracked:")
                for kpi in data['kpis']:
                    print(f"  - {kpi['name']}: {kpi['value']}")

            print()
        except Exception as e:
            print(f"✗ Failed: {e}")
            if hasattr(e, 'response'):
                print(f"   Response: {e.response.text}")
            print()

        # Test 4: Search Agents
        print("Test 4: Search Agents (query='competitor')")
        print("-" * 40)
        try:
            search_request = {
                "query": "competitor",
                "limit": 10
            }

            response = await client.post(
                f"{base_url}/api/pcf/search",
                json=search_request
            )
            response.raise_for_status()
            data = response.json()

            print(f"✓ Total Results: {data['total']}")
            print(f"✓ Returned: {data['count']}")

            if data['results']:
                print(f"\nTop Results:")
                for result in data['results'][:3]:
                    print(f"  - {result['hierarchy_id']}: {result['name']}")
                    print(f"    Level: {result['level_name']}, Relevance: {result.get('relevance_score', 'N/A'):.2f}")

            print()
        except Exception as e:
            print(f"✗ Failed: {e}")
            print()

        # Test 5: Test Non-existent Agent
        print("Test 5: Error Handling (non-existent agent 9.9.9.9)")
        print("-" * 40)
        try:
            response = await client.get(f"{base_url}/api/pcf/9.9.9.9")
            if response.status_code == 404:
                print(f"✓ Correctly returned 404 Not Found")
                error_data = response.json()
                print(f"✓ Error Message: {error_data.get('detail', 'N/A')}")
            else:
                print(f"✗ Expected 404, got {response.status_code}")
            print()
        except Exception as e:
            print(f"✗ Failed: {e}")
            print()

    print("=" * 80)
    print("API Test Suite Complete!")
    print("=" * 80)


def main():
    """Main entry point"""
    print("\nChecking if API server is running...")
    print("(Make sure to run: python scripts/run_api.py)\n")

    try:
        asyncio.run(test_api())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nTest suite failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
