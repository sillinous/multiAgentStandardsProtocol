#!/usr/bin/env python3
"""
Test External Agent Registration
Verify that external systems can register agents
"""

import requests
import json

def test_external_agent_registration():
    """Test external agent registration in autonomous ecosystem"""
    print("TESTING EXTERNAL AGENT REGISTRATION")
    print("=" * 50)

    base_url = "http://localhost:8001"

    # Test 1: Check ecosystem is running
    print("1. Testing ecosystem availability...")
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            data = response.json()
            print(f"   SUCCESS: Ecosystem operational (v{data['version']})")
            print(f"   Mode: {data['mode']}")
        else:
            print(f"   FAILED: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"   ERROR: {e}")
        return False

    print()

    # Test 2: Register external agent
    print("2. Registering external agent...")
    agent_data = {
        "name": "External Test Agent",
        "description": "A test agent from an external system demonstrating integration",
        "capabilities": ["data_analysis", "automation"],
        "specializations": ["machine_learning", "process_automation"],
        "pricing_hourly_rate": 75.0
    }

    try:
        response = requests.post(f"{base_url}/agents/register", json=agent_data)
        if response.status_code == 200:
            result = response.json()
            print(f"   SUCCESS: Agent registered with ID {result['agent_id']}")
            print(f"   Message: {result['message']}")
            agent_id = result['agent_id']
        else:
            print(f"   FAILED: Status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"   ERROR: {e}")
        return False

    print()

    # Test 3: Verify agent appears in marketplace
    print("3. Verifying agent in marketplace...")
    try:
        response = requests.get(f"{base_url}/marketplace/agents")
        if response.status_code == 200:
            data = response.json()
            agents = data['agents']
            external_agent = next((a for a in agents if a['agent_id'] == agent_id), None)

            if external_agent:
                print(f"   SUCCESS: External agent found in marketplace")
                print(f"   Name: {external_agent['name']}")
                print(f"   Capabilities: {external_agent['capabilities']}")
            else:
                print(f"   FAILED: External agent not found in marketplace")
                return False
        else:
            print(f"   FAILED: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"   ERROR: {e}")
        return False

    print()

    # Test 4: Check marketplace insights
    print("4. Checking marketplace insights...")
    try:
        response = requests.get(f"{base_url}/marketplace/insights")
        if response.status_code == 200:
            data = response.json()
            total_agents = data.get('marketplace_stats', {}).get('total_agents', 0)
            print(f"   SUCCESS: Marketplace has {total_agents} total agents")
            print(f"   Ecosystem mode: {data.get('ecosystem_mode', 'unknown')}")
        else:
            print(f"   FAILED: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"   ERROR: {e}")
        return False

    print()

    # Test 5: Health check after registration
    print("5. Final health check...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"   SUCCESS: System health {data['overall_health']*100:.1f}%")
            print(f"   Active agents: {data['active_agents']}")
            print(f"   Marketplace volume: ${data['marketplace_volume']}")
        else:
            print(f"   FAILED: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"   ERROR: {e}")
        return False

    print()
    print("=" * 50)
    print("EXTERNAL AGENT INTEGRATION: SUCCESSFUL")
    print("The autonomous ecosystem is ready for external use!")
    print("=" * 50)
    return True

if __name__ == "__main__":
    success = test_external_agent_registration()
    if success:
        print("\nAUTONOMOUS ECOSYSTEM: EXTERNALLY ACCESSIBLE")
    else:
        print("\nISSUES DETECTED: Check ecosystem status")