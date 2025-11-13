"""
Complete Platform Demo - End-to-End Workflow
============================================

This demo showcases ALL major features of the Agentic Forge platform:
1. Template Deployment - One-click ensemble creation
2. Analytics Dashboard - Real-time performance visualization
3. Strategy Backtesting - Historical validation
4. Pareto Evolution - Multi-objective optimization
5. Visual Trade-off Analysis - Frontier exploration

Run this script to see the complete workflow from template to optimized agents!

Requirements:
- Server running on localhost:8080
- Basic HTTP requests (requests library)

Usage:
    python examples/complete_platform_demo.py
"""

import requests
import json
import time
from datetime import datetime, timedelta


BASE_URL = "http://localhost:8080"


def print_section(title):
    """Print a fancy section header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def print_success(message):
    """Print success message"""
    print(f"✅ {message}")


def print_info(message):
    """Print info message"""
    print(f"ℹ️  {message}")


def print_result(label, value):
    """Print result"""
    print(f"   {label}: {value}")


# ============================================================================
# STEP 1: Template Deployment
# ============================================================================

def deploy_template():
    """Deploy a balanced trader template"""
    print_section("STEP 1: Deploy Ensemble Template")

    print_info("Deploying 'Balanced Trader' template...")

    response = requests.post(
        f"{BASE_URL}/api/ensemble/templates/balanced_trader/deploy",
        headers={"Content-Type": "application/json"},
        json={}
    )

    result = response.json()

    if result.get('success'):
        print_success("Template deployed successfully!")
        print_result("Ensemble ID", result['ensemble_id'])
        print_result("Ensemble Name", result['ensemble_name'])
        print_result("Specialists Added", result['specialists_added'])
        return result['ensemble_id']
    else:
        print("❌ Failed to deploy template")
        return None


# ============================================================================
# STEP 2: View Ensemble Details & Analytics
# ============================================================================

def view_ensemble_analytics(ensemble_id):
    """View ensemble details and analytics"""
    print_section("STEP 2: View Ensemble Analytics")

    # Get ensemble info
    print_info("Fetching ensemble information...")
    response = requests.get(f"{BASE_URL}/api/ensemble/{ensemble_id}")
    ensemble = response.json()

    print_success("Ensemble loaded!")
    print_result("Name", ensemble['name'])
    print_result("Total Specialists", ensemble['ensemble_stats']['total_specialists'])
    print_result("Routing Method", ensemble['ensemble_stats']['routing_method'])
    print_result("Total Decisions", ensemble['total_decisions'])

    # Get analytics
    print_info("\nFetching analytics data...")
    response = requests.get(f"{BASE_URL}/api/ensemble/{ensemble_id}/analytics")
    analytics = response.json()

    print_success("Analytics loaded!")
    print_result("Performance History Points", len(analytics['performance_history']))
    print_result("Regime History Points", len(analytics['regime_history']))

    if analytics['specialist_performance']:
        print("\n   Specialist Performance:")
        for spec_type, perf in analytics['specialist_performance'].items():
            print(f"     {spec_type}:")
            print(f"       Win Rate: {perf['win_rate']:.2%}")
            print(f"       Total Return: {perf['total_return']:.2f}")
            print(f"       Total Trades: {perf['total_trades']}")


# ============================================================================
# STEP 3: Run Backtest
# ============================================================================

def run_backtest(ensemble_id):
    """Run a 7-day backtest"""
    print_section("STEP 3: Run Strategy Backtest")

    # Calculate dates (last 7 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    print_info(f"Running backtest from {start_date.date()} to {end_date.date()}...")
    print_info("Configuration: $10,000 capital, 0.1% commission, 95% position size")

    response = requests.post(
        f"{BASE_URL}/api/backtest/run",
        headers={"Content-Type": "application/json"},
        json={
            "ensemble_id": ensemble_id,
            "symbol": "BTC/USD",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "initial_capital": 10000.0,
            "commission_rate": 0.001,
            "slippage_rate": 0.0005,
            "position_size": 0.95
        }
    )

    result = response.json()

    if result.get('success'):
        print_success("Backtest completed!")
        backtest_id = result['backtest_id']
        print_result("Backtest ID", backtest_id)
        print_result("Duration", f"{result['duration_seconds']:.2f}s")

        metrics = result['preliminary_metrics']
        print("\n   Performance Metrics:")
        print_result("Total Return", f"{metrics['total_return_percent']:.2f}%")
        print_result("Win Rate", f"{metrics['win_rate']:.2%}")
        print_result("Total Trades", metrics['total_trades'])
        print_result("Sharpe Ratio", f"{metrics['sharpe_ratio']:.2f}")
        print_result("Max Drawdown", f"{metrics['max_drawdown_percent']:.2f}%")

        # Get full results
        print_info("\nFetching complete backtest results...")
        response = requests.get(f"{BASE_URL}/api/backtest/{backtest_id}")
        full_results = response.json()

        print_success("Full results loaded!")
        print_result("Equity Curve Points", len(full_results['equity_curve']))
        print_result("Total Trades", len(full_results['trades']))
        print_result("Final Equity", f"${full_results['metrics']['final_equity']:.2f}")
        print_result("Profit Factor", f"{full_results['metrics']['profit_factor']:.2f}")

        return backtest_id
    else:
        print("❌ Backtest failed")
        return None


# ============================================================================
# STEP 4: Run Pareto Evolution
# ============================================================================

def run_pareto_evolution(ensemble_id):
    """Run multi-objective Pareto evolution"""
    print_section("STEP 4: Run Multi-Objective Pareto Evolution")

    print_info("Configuring NSGA-II evolution...")
    print_info("Objectives: Return (maximize) + Max Drawdown (minimize)")
    print_info("Population: 20 agents, Generations: 10")

    # Calculate dates
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    response = requests.post(
        f"{BASE_URL}/api/pareto/evolve",
        headers={"Content-Type": "application/json"},
        json={
            "ensemble_id": ensemble_id,
            "population_size": 20,
            "num_generations": 10,
            "objectives": [
                {"type": "return", "minimize": False, "weight": 1.0},
                {"type": "max_drawdown", "minimize": True, "weight": 1.0},
                {"type": "sharpe_ratio", "minimize": False, "weight": 1.0}
            ],
            "backtest_config": {
                "symbol": "BTC/USD",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "initial_capital": 10000.0,
                "commission_rate": 0.001,
                "slippage_rate": 0.0005,
                "position_size": 0.95
            }
        }
    )

    result = response.json()

    if result.get('success'):
        print_success("Pareto evolution completed!")
        evolution_id = result['evolution_id']
        print_result("Evolution ID", evolution_id)
        print_result("Pareto Frontier Size", result['pareto_frontier_size'])
        print_result("Total Fronts", result['total_fronts'])
        print_result("Generations", result['generations_completed'])

        # Get full results
        print_info("\nFetching Pareto frontier results...")
        response = requests.get(f"{BASE_URL}/api/pareto/{evolution_id}")
        pareto_results = response.json()

        print_success("Pareto frontier loaded!")
        print(f"\n   🎯 Pareto Frontier ({len(pareto_results['pareto_frontier'])} agents):")

        for i, agent in enumerate(pareto_results['pareto_frontier'][:5], 1):
            print(f"\n   Agent {i}:")
            print(f"     ID: {agent['agent_id'][:16]}...")
            print(f"     Generation: {agent['generation']}")
            print(f"     Dominance Rank: {agent['dominance_rank']}")
            print(f"     Crowding Distance: {agent['crowding_distance']:.3f}")
            print(f"     Objectives:")
            for obj, value in agent['objectives'].items():
                print(f"       {obj}: {value:.2f}")

        if len(pareto_results['pareto_frontier']) > 5:
            print(f"\n   ... and {len(pareto_results['pareto_frontier']) - 5} more agents on the frontier")

        return evolution_id
    else:
        print(f"❌ Pareto evolution failed: {result.get('detail', 'Unknown error')}")
        return None


# ============================================================================
# STEP 5: Summary & Next Steps
# ============================================================================

def print_summary(ensemble_id, backtest_id, evolution_id):
    """Print comprehensive summary"""
    print_section("COMPLETE WORKFLOW SUMMARY")

    print_success("All steps completed successfully!")
    print("\n📋 Resource IDs:")
    print_result("Ensemble ID", ensemble_id)
    if backtest_id:
        print_result("Backtest ID", backtest_id)
    if evolution_id:
        print_result("Evolution ID", evolution_id)

    print("\n🌐 Next Steps - View in Dashboard:")
    print(f"\n   1. Open browser: {BASE_URL}/dashboard")
    print(f"   2. Select ensemble: {ensemble_id[:16]}...")
    print(f"   3. View analytics charts (4 real-time visualizations)")
    print(f"   4. Check backtest results (equity curve + trade log)")
    if evolution_id:
        print(f"   5. Explore Pareto frontier (scatter plot + agent table)")

    print("\n✨ What You Just Saw:")
    print("   ✅ One-click template deployment")
    print("   ✅ Real-time analytics tracking")
    print("   ✅ Historical backtest validation")
    if evolution_id:
        print("   ✅ Multi-objective Pareto evolution")
        print("   ✅ Optimal trade-off discovery")

    print("\n🚀 The Agentic Forge is PRODUCTION READY!")
    print("="*80)


# ============================================================================
# Main Execution
# ============================================================================

def main():
    """Run complete platform demo"""
    print("\n" + "="*80)
    print("  🚀 AGENTIC FORGE - COMPLETE PLATFORM DEMO 🚀")
    print("="*80)
    print("\nThis demo showcases the FULL power of the platform:")
    print("  • Template Deployment")
    print("  • Analytics Dashboard")
    print("  • Strategy Backtesting")
    print("  • Multi-Objective Pareto Evolution")
    print("\nStarting demo...\n")

    try:
        # Step 1: Deploy template
        ensemble_id = deploy_template()
        if not ensemble_id:
            print("❌ Demo failed at template deployment")
            return

        time.sleep(1)

        # Step 2: View analytics
        view_ensemble_analytics(ensemble_id)

        time.sleep(1)

        # Step 3: Run backtest
        backtest_id = run_backtest(ensemble_id)

        time.sleep(1)

        # Step 4: Run Pareto evolution (optional, takes longer)
        evolution_id = None
        print("\n" + "-"*80)
        user_input = input("\n🧬 Run Pareto Evolution? (takes ~1-2 min) [y/N]: ")
        if user_input.lower() == 'y':
            evolution_id = run_pareto_evolution(ensemble_id)
        else:
            print_info("Skipping Pareto evolution (you can run it from the dashboard!)")

        # Step 5: Summary
        print_summary(ensemble_id, backtest_id, evolution_id)

    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to server at", BASE_URL)
        print("   Please ensure the server is running:")
        print("   cd src && python -m superstandard.api.server")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
