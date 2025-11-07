#!/usr/bin/env python3
"""
End-to-End Test: Agent Factory System
Tests the complete flow from API request to agent generation
"""

import requests
import json
import time
from pathlib import Path
import zipfile
import io

# Configuration
BASE_URL = "http://localhost:8000"
FACTORY_URL = f"{BASE_URL}/api/v1/factory"


def test_health_check():
    """Test 1: Verify API is healthy"""
    print("\n🧪 Test 1: Health Check")
    print("=" * 60)

    response = requests.get(f"{FACTORY_URL}/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    print("✅ PASSED: API is healthy")
    return True


def test_list_templates():
    """Test 2: List all available templates"""
    print("\n🧪 Test 2: List Templates")
    print("=" * 60)

    response = requests.get(f"{FACTORY_URL}/templates")
    print(f"Status Code: {response.status_code}")

    templates = response.json()
    print(f"Found {len(templates)} templates:")
    for template in templates[:3]:  # Show first 3
        print(f"  - {template['name']} (APQC {template['apqc_process']})")

    assert response.status_code == 200
    assert len(templates) == 10
    print(f"✅ PASSED: Retrieved {len(templates)} templates")
    return templates


def test_get_template_details(template_id):
    """Test 3: Get details for a specific template"""
    print(f"\n🧪 Test 3: Get Template Details ({template_id})")
    print("=" * 60)

    response = requests.get(f"{FACTORY_URL}/templates/{template_id}")
    print(f"Status Code: {response.status_code}")

    template = response.json()
    print(f"Template: {template['name']}")
    print(f"Description: {template['description']}")
    print(f"Business Value: {template['business_value']}")
    print(f"Capabilities: {len(template['capabilities'])} defined")

    assert response.status_code == 200
    assert template["template_id"] == template_id
    print("✅ PASSED: Template details retrieved")
    return template


def test_get_recommendations():
    """Test 4: Get AI-powered template recommendations"""
    print("\n🧪 Test 4: Get Template Recommendations")
    print("=" * 60)

    request_data = {
        "business_objective": "Improve customer service response time by 60% and increase satisfaction by 35%",
        "industry": "technology",
        "organization_size": "smb",
    }

    print(f"Request: {json.dumps(request_data, indent=2)}")

    response = requests.post(f"{FACTORY_URL}/templates/recommend", json=request_data)
    print(f"Status Code: {response.status_code}")

    recommendations = response.json()
    print(f"\nRecommendations response type: {type(recommendations)}")

    # Handle different response formats
    if isinstance(recommendations, dict):
        recs_list = recommendations.get("recommendations", [recommendations])
    elif isinstance(recommendations, list):
        recs_list = recommendations
    else:
        recs_list = []

    print(f"\nTop Recommendations ({len(recs_list)} total):")
    for rec in recs_list[:3]:
        if isinstance(rec, dict):
            score = rec.get("score", rec.get("match_score", 0))
            template = rec.get("template", rec)
            template_name = (
                template.get("name", "Unknown") if isinstance(template, dict) else "Unknown"
            )
            reasoning = rec.get("reasoning", "N/A")
            print(f"  {score:.1f}% - {template_name}")
            print(f"        Reason: {reasoning}")

    assert response.status_code == 200
    print("✅ PASSED: Recommendations generated")
    return recommendations


def test_get_statistics():
    """Test 5: Get factory statistics"""
    print("\n🧪 Test 5: Get Factory Statistics")
    print("=" * 60)

    response = requests.get(f"{FACTORY_URL}/statistics")
    print(f"Status Code: {response.status_code}")

    stats = response.json()
    print(f"Statistics:")
    print(f"  Templates: {stats['templates']['total_templates']}")
    print(f"  Total Usage: {stats['templates']['total_usage']}")
    print(f"  Agents Generated: {stats['generation']['total_agents_generated']}")
    print(f"  Avg Code Quality: {stats['generation']['average_code_quality']}")

    assert response.status_code == 200
    print("✅ PASSED: Statistics retrieved")
    return stats


def test_create_agent():
    """Test 6: Create a complete agent (THE BIG ONE!)"""
    print("\n🧪 Test 6: Create Agent (End-to-End)")
    print("=" * 60)

    agent_spec = {
        "agent_name": "E2E_Test_Customer_Service_Bot",
        "description": "Automated customer service agent for handling inquiries and support tickets",
        "business_objective": "Reduce response time by 60% while improving customer satisfaction by 35%",
        # Template selection
        "template_id": "apqc-5.1-customer-service-optimizer",
        "apqc_process": "5.1",
        # Customization
        "custom_capabilities": ["sentiment_analysis", "ticket_routing"],
        "integration_targets": ["slack", "zendesk"],
        # Compliance
        "compliance_frameworks": ["gdpr", "soc2"],
        "data_residency": "EU",
        "encryption_required": True,
        # Performance
        "performance_tier": "optimized",
        "max_response_time_ms": 500,
        "concurrent_users": 200,
        # Deployment
        "deployment_format": "docker",
        "cloud_provider": "aws",
        # Additional
        "industry": "technology",
        "organization_size": "smb",
    }

    print("Creating agent with specification:")
    print(
        json.dumps(
            {
                k: v
                for k, v in agent_spec.items()
                if k in ["agent_name", "template_id", "compliance_frameworks"]
            },
            indent=2,
        )
    )

    start_time = time.time()

    response = requests.post(
        f"{FACTORY_URL}/create-agent",
        json=agent_spec,
        timeout=60,  # Allow up to 60 seconds for generation
    )

    elapsed_time = time.time() - start_time

    print(f"\nStatus Code: {response.status_code}")
    print(f"Generation Time: {elapsed_time:.2f} seconds")

    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ Agent Created Successfully!")
        print(f"Agent ID: {result['agent_id']}")
        print(f"Agent Name: {result['agent_name']}")
        print(f"Code Quality Score: {result['code_quality_score']}/100")
        print(f"Lines of Code: {result['lines_of_code']}")
        print(f"Template Used: {result.get('template_id', 'N/A')}")
        if "generated_files" in result:
            print(f"\nGenerated Files:")
            for file_info in result["generated_files"]:
                print(f"  - {file_info['filename']} ({file_info['size_bytes']} bytes)")

        assert (
            result["code_quality_score"] >= 85
        ), f"Quality score {result['code_quality_score']} below threshold"
        assert elapsed_time < 30, f"Generation took {elapsed_time}s, expected <30s"

        print(
            f"\n✅ PASSED: Agent generated in {elapsed_time:.2f}s with quality {result['code_quality_score']}/100"
        )
        return result
    else:
        print(f"\n❌ FAILED: {response.status_code}")
        print(f"Error: {response.text}")
        raise AssertionError(f"Agent creation failed: {response.text}")


def test_get_agent_details(agent_id):
    """Test 7: Get details of generated agent"""
    print(f"\n🧪 Test 7: Get Agent Details ({agent_id})")
    print("=" * 60)

    response = requests.get(f"{FACTORY_URL}/agents/{agent_id}")
    print(f"Status Code: {response.status_code}")

    agent = response.json()
    print(f"Agent: {agent.get('agent_name', 'Unknown')}")
    print(f"Created: {agent.get('generated_date', agent.get('created_at', 'Unknown'))}")
    print(f"Quality: {agent.get('code_quality_score', 0)}/100")
    print(f"Status: {agent.get('status', 'Unknown')}")

    assert response.status_code == 200
    print("✅ PASSED: Agent details retrieved")
    return agent


def test_download_agent(agent_id):
    """Test 8: Download agent package"""
    print(f"\n🧪 Test 8: Download Agent Package ({agent_id})")
    print("=" * 60)

    response = requests.get(f"{FACTORY_URL}/agents/{agent_id}/download")
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    print(f"Content-Length: {len(response.content)} bytes")

    assert response.status_code == 200
    assert response.headers.get("content-type") == "application/zip"

    # Verify ZIP contents
    zip_file = zipfile.ZipFile(io.BytesIO(response.content))
    files = zip_file.namelist()

    print(f"\nZIP Contents ({len(files)} files):")
    for filename in files:
        file_info = zip_file.getinfo(filename)
        print(f"  - {filename} ({file_info.file_size} bytes)")

    # Verify expected files exist
    expected_files = ["requirements.txt", "Dockerfile", "README.md"]

    for expected in expected_files:
        matching = [f for f in files if expected in f]
        assert len(matching) > 0, f"Missing expected file: {expected}"

    print(f"\n✅ PASSED: Agent package downloaded with {len(files)} files")
    return response.content


def test_statistics_after_creation():
    """Test 9: Verify statistics updated after creation"""
    print("\n🧪 Test 9: Verify Statistics Updated")
    print("=" * 60)

    response = requests.get(f"{FACTORY_URL}/statistics")
    stats = response.json()

    agents_generated = stats["generation"]["total_agents_generated"]
    avg_quality = stats["generation"]["average_code_quality"]

    print(f"Updated Statistics:")
    print(f"  Total Agents Generated: {agents_generated}")
    print(f"  Average Code Quality: {avg_quality}")

    assert agents_generated >= 1, "Statistics should show at least 1 agent generated"

    print("✅ PASSED: Statistics updated correctly")
    return stats


def run_all_tests():
    """Run complete end-to-end test suite"""
    print("\n" + "=" * 60)
    print("🚀 AGENT FACTORY END-TO-END TEST SUITE")
    print("=" * 60)

    try:
        # Phase 1: API Verification
        print("\n📋 PHASE 1: API VERIFICATION")
        test_health_check()
        templates = test_list_templates()
        test_get_template_details(templates[4]["template_id"])  # Customer Service template
        test_get_recommendations()
        initial_stats = test_get_statistics()

        # Phase 2: Agent Generation (Critical Test)
        print("\n📋 PHASE 2: AGENT GENERATION")
        agent_result = test_create_agent()
        agent_id = agent_result["agent_id"]

        # Phase 3: Agent Retrieval
        print("\n📋 PHASE 3: AGENT RETRIEVAL")
        test_get_agent_details(agent_id)
        zip_content = test_download_agent(agent_id)

        # Phase 4: Verification
        print("\n📋 PHASE 4: VERIFICATION")
        final_stats = test_statistics_after_creation()

        # Summary
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 60)
        print("\n📊 Test Summary:")
        print(f"  ✅ 9/9 tests passed")
        print(f"  ✅ Agent generated successfully")
        print(f"  ✅ Quality score: {agent_result['code_quality_score']}/100")
        print(f"  ✅ Package size: {len(zip_content):,} bytes")
        print(
            f"  ✅ Statistics updated: {final_stats['generation']['total_agents_generated']} agents"
        )
        print("\n🚀 The Agent Factory is FULLY OPERATIONAL!")

        return True

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        return False
    except requests.exceptions.ConnectionError:
        print("\n❌ CONNECTION ERROR: Backend not running on http://localhost:8000")
        print("   Start backend with: python3 -m uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
