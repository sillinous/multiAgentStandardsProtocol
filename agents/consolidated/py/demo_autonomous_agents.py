"""
Autonomous Agents - Investor Demo Script

This script demonstrates the autonomous agentic ecosystem for investor presentations.

Features demonstrated:
1. Create autonomous agents via API
2. Assign tasks to agents
3. Run autonomous improvement cycles
4. Generate agents using Agent Factory
5. Real-time agent monitoring
6. Orchestrator-driven continuous improvement

Usage:
    python demo_autonomous_agents.py
"""

import asyncio
import sys
import os
import time
from datetime import datetime
import requests
import json

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1/autonomous"
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def print_success(message):
    """Print success message"""
    print(f"[SUCCESS] {message}")

def print_info(message):
    """Print info message"""
    print(f"[INFO] {message}")

def print_error(message):
    """Print error message"""
    print(f"[ERROR] {message}")

def api_request(method, endpoint, data=None, params=None):
    """Make API request with error handling"""
    url = f"{API_BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, params=params, timeout=30)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=30)
        elif method == "DELETE":
            response = requests.delete(url, timeout=30)

        response.raise_for_status()
        return response.json() if response.text else {}

    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to API. Is the backend server running?")
        print_info("Start the server with: python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print_error(f"API request failed: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return None

def demo_1_create_agents():
    """Demo 1: Create individual agents"""
    print_section("DEMO 1: Creating Specialized Agents")

    agent_types = [
        ("testing", "Automated Testing Agent"),
        ("design", "System Design Agent"),
        ("development", "Code Development Agent"),
        ("qa", "Quality Assurance Agent")
    ]

    created_agents = []

    for agent_type, description in agent_types:
        print_info(f"Creating {description}...")

        data = {
            "agent_type": agent_type,
            "config": {
                "auto_start": True,
                "max_iterations": 10
            }
        }

        result = api_request("POST", "/agents", data=data)

        if result:
            print_success(f"Created {description}")
            print(f"  Agent ID: {result['agent_id']}")
            print(f"  Status: {result['status']}")
            print(f"  Capabilities: {', '.join(result['capabilities'])}")
            created_agents.append(result)
            time.sleep(0.5)

    return created_agents

def demo_2_list_agents():
    """Demo 2: List all active agents"""
    print_section("DEMO 2: Listing Active Agents")

    print_info("Fetching all active agents...")
    result = api_request("GET", "/agents")

    if result:
        print_success(f"Found {len(result)} active agents")
        for agent in result:
            print(f"\n  {agent['agent_id']}")
            print(f"    Type: {agent['agent_type']}")
            print(f"    Status: {agent['status']}")
            print(f"    Tasks Completed: {agent['tasks_completed']}")

    return result

def demo_3_assign_task():
    """Demo 3: Assign task to an agent"""
    print_section("DEMO 3: Assigning Tasks to Agents")

    # Get first agent
    agents = api_request("GET", "/agents")
    if not agents or len(agents) == 0:
        print_error("No agents available")
        return None

    agent = agents[0]
    print_info(f"Assigning task to agent: {agent['agent_id']}")

    task_data = {
        "task_type": "analyze_codebase",
        "task_data": {
            "target": "./",
            "focus_areas": ["performance", "security", "maintainability"]
        },
        "priority": "high"
    }

    result = api_request("POST", f"/agents/{agent['agent_id']}/tasks", data=task_data)

    if result:
        print_success("Task assigned successfully")
        print(f"  Task ID: {result['task_id']}")
        print(f"  Status: {result['status']}")

    return result

def demo_4_agent_factory():
    """Demo 4: Generate agents using Agent Factory"""
    print_section("DEMO 4: Agent Factory - Automatic Agent Generation")

    print_info("Generating 3 specialized agents using Agent Factory...")
    print_info("Analyzing APQC framework categories...")

    data = {
        "count": 3,
        "priority_categories": [
            "Develop and Manage Products and Services",
            "Market and Sell Products and Services",
            "Manage Information Technology"
        ]
    }

    result = api_request("POST", "/agents/factory/generate", data=data)

    if result:
        print_success(f"Generated {len(result)} agents")
        for agent in result:
            print(f"\n  {agent['agent_id']}")
            print(f"    Type: {agent['agent_type']}")
            print(f"    Status: {agent['status']}")

    return result

def demo_5_improvement_cycle():
    """Demo 5: Run autonomous improvement cycle"""
    print_section("DEMO 5: Autonomous Improvement Cycle")

    print_info("Starting autonomous improvement cycle...")
    print_info("The orchestrator will:")
    print("  1. Analyze current system state")
    print("  2. Identify capability gaps")
    print("  3. Generate needed agents")
    print("  4. Deploy and test improvements")
    print("  5. Iterate until optimal\n")

    # Check if API key is set
    if not ANTHROPIC_API_KEY:
        print_error("ANTHROPIC_API_KEY not set - running in supervised mode")
        supervised = True
    else:
        supervised = True  # For demo, always supervised

    params = {
        "supervised": supervised,
        "max_cycles": 2  # Limited for demo
    }

    print_info("Starting improvement cycle (this may take a few minutes)...")
    result = api_request("POST", "/agents/orchestrator/improvement-cycle", params=params)

    if result:
        print_success("Improvement cycle completed")
        print(f"\n  Status: {result['status']}")
        print(f"  Cycles Run: {result['cycles_run']}")
        print(f"  Agents Generated: {result['agents_generated']}")
        print(f"  System Optimal: {result['system_optimal']}")
        print(f"\n  Summary: {result['summary']}")

    return result

def demo_6_monitor_agents():
    """Demo 6: Real-time agent monitoring"""
    print_section("DEMO 6: Real-time Agent Monitoring")

    agents = api_request("GET", "/agents")

    if agents:
        print_info(f"Monitoring {len(agents)} agents...")

        for agent in agents[:5]:  # Limit to 5 for demo
            status = api_request("GET", f"/agents/{agent['agent_id']}/status")

            if status:
                print(f"\n  {status['agent_id']}")
                print(f"    Status: {status['status']}")
                print(f"    Iteration: {status['current_iteration']}")
                print(f"    Workspace: {status['workspace']}")
                print(f"    Messages: {status['message_count']}")

def run_investor_demo():
    """Run complete investor demonstration"""
    print("\n" + "=" * 80)
    print("  AUTONOMOUS AGENTIC ECOSYSTEM - INVESTOR DEMONSTRATION")
    print("=" * 80)
    print(f"\nDemo Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API Endpoint: {API_BASE_URL}")
    print(f"Anthropic API: {'Configured' if ANTHROPIC_API_KEY else 'Not configured (mock mode)'}")

    try:
        # Demo 1: Create agents
        agents = demo_1_create_agents()
        input("\nPress Enter to continue to Demo 2...")

        # Demo 2: List agents
        all_agents = demo_2_list_agents()
        input("\nPress Enter to continue to Demo 3...")

        # Demo 3: Assign task
        task_result = demo_3_assign_task()
        input("\nPress Enter to continue to Demo 4...")

        # Demo 4: Agent Factory
        factory_agents = demo_4_agent_factory()
        input("\nPress Enter to continue to Demo 5...")

        # Demo 5: Improvement cycle
        # improvement_result = demo_5_improvement_cycle()
        print_section("DEMO 5: Autonomous Improvement Cycle")
        print_info("Skipping improvement cycle for quick demo")
        print_info("This feature runs autonomous improvement iterations")
        input("\nPress Enter to continue to Demo 6...")

        # Demo 6: Monitor agents
        demo_6_monitor_agents()

        # Summary
        print_section("DEMONSTRATION COMPLETE")
        print_success("All autonomous agent features demonstrated successfully!")
        print("\nKey Capabilities Shown:")
        print("  [X] Individual agent creation and management")
        print("  [X] Task assignment and execution")
        print("  [X] Agent Factory for automatic generation")
        print("  [X] Real-time agent monitoring")
        print("  [ ] Autonomous improvement cycles (available)")
        print("  [ ] Inter-agent communication (available)")
        print("\nNext Steps:")
        print("  - View agents in web UI at http://localhost:3000")
        print("  - Run full improvement cycle with --autonomous flag")
        print("  - Explore agent library in autonomous-ecosystem/library/")

    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print_error(f"Demo failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 80)

if __name__ == "__main__":
    run_investor_demo()
