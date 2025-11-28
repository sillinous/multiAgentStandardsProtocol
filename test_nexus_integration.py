"""
NEXUS Trading Platform Integration Test

Tests all newly integrated trading endpoints:
- Strategy generation
- Trade execution
- Risk management
- Arbitrage detection
- Swarm intelligence

This verifies that existing production-ready agents are properly exposed via API.
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8080"

def print_section(title):
    """Print formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def test_health():
    """Test trading platform health check"""
    print_section("1. HEALTH CHECK - Trading Platform")

    try:
        response = requests.get(f"{BASE_URL}/api/trading/health", timeout=5)
        print(f"Status: {response.status_code}")
        data = response.json()
        print(json.dumps(data, indent=2))
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_agents_status():
    """Test detailed agent status"""
    print_section("2. AGENT STATUS - All Trading Agents")

    try:
        response = requests.get(f"{BASE_URL}/api/trading/agents/status", timeout=5)
        print(f"Status: {response.status_code}")
        data = response.json()
        print(json.dumps(data, indent=2))
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Agent status failed: {e}")
        return False

def test_strategy_generation():
    """Test AI strategy generation"""
    print_section("3. STRATEGY GENERATION - Autonomous Strategy Agent")

    payload = {
        "token_address": "SOL-USD",
        "analysis_type": "comprehensive",
        "use_swarm": False
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/trading/strategy/generate",
            json=payload,
            timeout=30
        )
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("\n✅ Strategy Generated Successfully!")
            print(f"Strategy ID: {data.get('strategy_id')}")
            print(f"Agent: {data.get('agent')}")
            print(f"Timestamp: {data.get('timestamp')}")

            if 'signal' in data:
                print(f"\nSignal: {json.dumps(data['signal'], indent=2)}")

            return True
        else:
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Strategy generation failed: {e}")
        return False

def test_risk_check():
    """Test risk management system"""
    print_section("4. RISK MANAGEMENT - Risk Agent")

    payload = {
        "portfolio_value": 10000.0,
        "position_size": 1000.0,
        "leverage": 5
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/trading/risk/check",
            json=payload,
            timeout=10
        )
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("\n✅ Risk Check Complete!")
            print(f"Risk Approved: {data.get('risk_approved')}")
            print(f"Portfolio Value: ${data.get('portfolio_value')}")
            print(f"Risk Percentage: {data.get('risk_percentage')}%")
            print(f"Agent: {data.get('agent')}")
            return True
        else:
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Risk check failed: {e}")
        return False

def test_funding_arbitrage():
    """Test funding rate arbitrage detection"""
    print_section("5. ARBITRAGE DETECTION - Funding Rate (Hyperliquid)")

    try:
        response = requests.get(
            f"{BASE_URL}/api/trading/arbitrage/funding",
            timeout=15
        )
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("\n✅ Funding Arbitrage Scan Complete!")
            print(f"Opportunities Found: {data.get('count', 0)}")
            print(f"Agent: {data.get('agent')}")

            if data.get('opportunities'):
                print("\nTop Opportunities:")
                for opp in data['opportunities'][:3]:
                    print(f"  - {opp}")

            return True
        else:
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Funding arb scan failed: {e}")
        return False

def test_all_arbitrage():
    """Test all arbitrage opportunities scan"""
    print_section("6. COMPREHENSIVE ARBITRAGE - All Types")

    try:
        response = requests.get(
            f"{BASE_URL}/api/trading/arbitrage/all",
            timeout=30
        )
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("\n✅ All Arbitrage Scans Complete!")

            opps = data.get('opportunities', {})
            print(f"\nFunding Rate Opportunities: {len(opps.get('funding', []))}")
            print(f"Pre-Listing Opportunities: {len(opps.get('listing', []))}")
            print(f"Whale Activity Alerts: {len(opps.get('whale', []))}")

            return True
        else:
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Comprehensive arb scan failed: {e}")
        return False

def test_swarm_query():
    """Test 6-model swarm intelligence"""
    print_section("7. SWARM INTELLIGENCE - 6 AI Models")

    payload = {
        "prompt": "Is SOL/USD bullish or bearish right now?"
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/trading/swarm/query",
            params=payload,
            timeout=60
        )
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("\n✅ Swarm Query Complete!")
            print(f"Models Queried: {data.get('models_queried', 0)}")
            print(f"Agent: {data.get('agent')}")

            if 'consensus' in data:
                print(f"\nConsensus: {json.dumps(data['consensus'], indent=2)}")

            return True
        else:
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Swarm query failed: {e}")
        return False

def run_all_tests():
    """Run all integration tests"""
    print("\n" + "#" * 80)
    print("#  NEXUS TRADING PLATFORM - INTEGRATION TEST SUITE")
    print("#  Testing existing production-ready agents via new API")
    print("#" * 80)
    print(f"\nTest Time: {datetime.now().isoformat()}")
    print(f"Base URL: {BASE_URL}")

    results = []

    # Run tests
    results.append(("Health Check", test_health()))
    results.append(("Agent Status", test_agents_status()))
    results.append(("Strategy Generation", test_strategy_generation()))
    results.append(("Risk Management", test_risk_check()))
    results.append(("Funding Arbitrage", test_funding_arbitrage()))
    results.append(("All Arbitrage", test_all_arbitrage()))
    results.append(("Swarm Intelligence", test_swarm_query()))

    # Summary
    print_section("TEST SUMMARY")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%\n")

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {test_name}")

    print("\n" + "=" * 80)

    if passed == total:
        print("🎉 ALL TESTS PASSED! NEXUS Trading Platform integration successful.")
    else:
        print("⚠️ Some tests failed. Check logs above for details.")

    print("=" * 80 + "\n")

    return passed == total

if __name__ == "__main__":
    try:
        success = run_all_tests()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        exit(1)
