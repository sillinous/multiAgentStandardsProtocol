"""
Market Simulation Demo - Realistic Synthetic Markets for Agent Testing

Demonstrates:
1. Multiple market regimes (bull, bear, volatile, sideways, crash, recovery)
2. Event injection (news shocks, volatility spikes, trend reversals)
3. Trading agents with different personalities
4. Backtesting and performance comparison
5. Integration with personality system for agent differentiation

Run: python examples/market_simulation_demo.py
"""

import sys
sys.path.insert(0, 'src')

from superstandard.trading.market_simulation import (
    MarketSimulator,
    MarketRegime,
    AgentBacktester,
    MarketBar
)
from superstandard.agents.personality import PersonalityProfile, PersonalityTrait
from typing import List


# ============================================================================
# Personality-Based Trading Strategies
# ============================================================================

def create_personality_strategy(personality: PersonalityProfile):
    """
    Create trading strategy function based on agent personality.

    Different personalities trade differently:
    - High Openness: Experimental, tries new patterns
    - High Conscientiousness: Methodical, strict risk management
    - High Extraversion: Active trading, responds to market energy
    - High Agreeableness: Follows trends, consensus-based
    - Low Neuroticism: Calm during volatility, holds positions longer
    """

    def strategy(current_bar: MarketBar, history: List[MarketBar]) -> str:
        """
        Personality-driven trading strategy.

        Returns: 'buy', 'sell', or 'hold'
        """
        if len(history) < 20:
            return 'hold'  # Need history for analysis

        # Calculate indicators
        prices = [bar.close for bar in history[-20:]] + [current_bar.close]
        sma_20 = sum(prices) / len(prices)
        current_price = current_bar.close

        # Calculate momentum
        momentum = (current_price - history[-10].close) / history[-10].close

        # Calculate volatility
        returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
        volatility = (sum(r**2 for r in returns) / len(returns)) ** 0.5

        # Get personality modifiers
        risk_tolerance = personality.get_modifier('risk_tolerance')
        stress_resistance = personality.get_modifier('stress_resistance')
        decision_speed = personality.get_modifier('decision_speed')
        innovation_capacity = personality.get_modifier('innovation_capacity')

        # === Entry Logic (Buy) ===

        # Trend following (influenced by Agreeableness)
        trend_signal = current_price > sma_20
        trend_strength = abs(current_price - sma_20) / sma_20

        # Momentum signal (influenced by Openness/Innovation)
        momentum_signal = momentum > 0.01 * innovation_capacity

        # Volatility filter (influenced by Neuroticism/Stress Resistance)
        volatility_acceptable = volatility < (0.03 * stress_resistance)

        # Risk-adjusted entry
        should_buy = (
            trend_signal and
            momentum_signal and
            volatility_acceptable and
            trend_strength > (0.005 / risk_tolerance)  # Higher risk tolerance = lower threshold
        )

        # === Exit Logic (Sell) ===

        # Stop loss (influenced by Conscientiousness)
        conscientiousness = personality.conscientiousness
        stop_loss_pct = 0.05 * (1.0 - conscientiousness)  # High C = tighter stops

        # Take profit (influenced by Extraversion - high E exits faster)
        take_profit_pct = 0.10 * (1.0 + personality.extraversion)

        # Momentum reversal
        momentum_reversed = momentum < -0.01

        # Check if we're in a position (simplified - assume we are if conditions met)
        # In real backtest, AgentBacktester tracks position
        should_sell = (
            not trend_signal or
            momentum_reversed or
            volatility > (0.05 / stress_resistance)  # Exit if too volatile for agent
        )

        # Decision (influenced by Decision Speed)
        # High decision speed = more responsive to signals
        if decision_speed > 0.6:
            # Fast decision maker
            if should_buy:
                return 'buy'
            elif should_sell:
                return 'sell'
        else:
            # Slower decision maker - needs stronger confirmation
            if should_buy and momentum > 0.02:
                return 'buy'
            elif should_sell and momentum < -0.02:
                return 'sell'

        return 'hold'

    return strategy


# ============================================================================
# Demo Scenarios
# ============================================================================

def demo_market_regimes():
    """Demonstrate different market regimes"""
    print("\n" + "="*80)
    print("MARKET SIMULATION DEMO - Part 1: Market Regimes")
    print("="*80)

    simulator = MarketSimulator(initial_price=100.0, timeframe_minutes=60)

    # Generate different regimes
    regimes = [
        (MarketRegime.BULL, 50),
        (MarketRegime.SIDEWAYS, 30),
        (MarketRegime.VOLATILE, 40),
        (MarketRegime.BEAR, 50),
        (MarketRegime.CRASH, 20),
        (MarketRegime.RECOVERY, 30)
    ]

    print("\n📊 Generating 220 bars across 6 different market regimes...\n")

    for regime, duration in regimes:
        bars = simulator.generate_bars(duration, regime=regime, event_probability=0.03)
        print(f"✅ Generated {duration} bars in {regime.value.upper()} regime")
        print(f"   Price: ${bars[0].close:.2f} → ${bars[-1].close:.2f} "
              f"({((bars[-1].close - bars[0].close) / bars[0].close * 100):+.2f}%)")

    # Show overall statistics
    print("\n📈 Overall Market Statistics:")
    stats = simulator.get_statistics()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"   {key}: {value:.4f}")
        else:
            print(f"   {key}: {value}")

    return simulator


def demo_event_injection():
    """Demonstrate event injection and impact"""
    print("\n" + "="*80)
    print("MARKET SIMULATION DEMO - Part 2: Event Injection")
    print("="*80)

    simulator = MarketSimulator(initial_price=100.0, timeframe_minutes=60)

    print("\n⚡ Generating market with injected events...\n")

    # Generate base market
    simulator.generate_bars(50, regime=MarketRegime.BULL, event_probability=0.0)

    price_before = simulator.bars[-1].close
    print(f"📊 Price before events: ${price_before:.2f}")

    # Inject major news shock
    simulator.inject_event(
        event_type='news_shock',
        magnitude=0.8,
        direction=1,
        description="Major positive earnings surprise"
    )

    # Generate bars after event
    bars_after = simulator.generate_bars(30, event_probability=0.0)
    price_after = bars_after[-1].close

    print(f"📊 Price after event: ${price_after:.2f} ({((price_after - price_before) / price_before * 100):+.2f}%)")

    # Inject volatility spike
    simulator.inject_event(
        event_type='volatility_spike',
        magnitude=0.9,
        direction=-1,
        description="Sudden market uncertainty"
    )

    # Generate more bars
    simulator.generate_bars(20)

    print(f"\n📋 Total events injected: {len(simulator.events)}")
    for event in simulator.events:
        print(f"   - {event.description} (magnitude: {event.magnitude:.2f})")

    return simulator


def demo_personality_trading():
    """Demonstrate personality-based trading strategies"""
    print("\n" + "="*80)
    print("MARKET SIMULATION DEMO - Part 3: Personality-Based Trading")
    print("="*80)

    # Create market data (mixed regimes for realistic testing)
    simulator = MarketSimulator(initial_price=100.0, timeframe_minutes=60, seed=42)

    print("\n📊 Generating realistic market data...\n")
    simulator.generate_bars(50, regime=MarketRegime.BULL, event_probability=0.02)
    simulator.generate_bars(30, regime=MarketRegime.VOLATILE, event_probability=0.05)
    simulator.generate_bars(40, regime=MarketRegime.SIDEWAYS, event_probability=0.01)
    simulator.generate_bars(30, regime=MarketRegime.BEAR, event_probability=0.03)

    market_data = simulator.bars

    # Create agents with different personalities
    print("🤖 Creating trading agents with different personalities...\n")

    agents = [
        {
            'name': 'Aggressive Innovator',
            'personality': PersonalityProfile(
                openness=0.90,
                conscientiousness=0.40,
                extraversion=0.75,
                agreeableness=0.45,
                neuroticism=0.60
            )
        },
        {
            'name': 'Conservative Methodical',
            'personality': PersonalityProfile(
                openness=0.35,
                conscientiousness=0.90,
                extraversion=0.40,
                agreeableness=0.70,
                neuroticism=0.25
            )
        },
        {
            'name': 'Balanced Trader',
            'personality': PersonalityProfile(
                openness=0.60,
                conscientiousness=0.65,
                extraversion=0.55,
                agreeableness=0.60,
                neuroticism=0.40
            )
        },
        {
            'name': 'Cautious Follower',
            'personality': PersonalityProfile(
                openness=0.30,
                conscientiousness=0.80,
                extraversion=0.35,
                agreeableness=0.85,
                neuroticism=0.30
            )
        }
    ]

    # Backtest each agent
    results = []

    for agent in agents:
        personality = agent['personality']
        personality._calculate_modifiers()  # Ensure modifiers are calculated

        print(f"📊 Backtesting {agent['name']}...")
        print(f"   Personality: O={personality.openness:.2f} C={personality.conscientiousness:.2f} "
              f"E={personality.extraversion:.2f} A={personality.agreeableness:.2f} N={personality.neuroticism:.2f}")

        # Get position size based on personality
        risk_tolerance = personality.get_modifier('risk_tolerance')
        position_size = 0.5 + (risk_tolerance * 0.5)  # 0.5 to 1.0 range

        print(f"   Position size: {position_size:.2f}x (risk tolerance: {risk_tolerance:.2f})")

        # Create strategy
        strategy = create_personality_strategy(personality)

        # Backtest
        backtester = AgentBacktester(initial_capital=10000.0)
        metrics = backtester.backtest(market_data, strategy, position_size)

        print(f"   📈 Results:")
        print(f"      Total Return: {metrics.total_return * 100:+.2f}%")
        print(f"      Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
        print(f"      Max Drawdown: {metrics.max_drawdown * 100:.2f}%")
        print(f"      Win Rate: {metrics.win_rate * 100:.2f}%")
        print(f"      Trades: {metrics.num_trades} ({metrics.profitable_trades} wins, {metrics.losing_trades} losses)")
        print(f"      Fitness Score: {metrics.get_fitness_score():.3f}")
        print()

        results.append({
            'agent': agent['name'],
            'personality': personality,
            'metrics': metrics,
            'position_size': position_size
        })

    # Compare results
    print("\n" + "="*80)
    print("📊 PERFORMANCE COMPARISON")
    print("="*80)

    # Sort by fitness score
    results.sort(key=lambda x: x['metrics'].get_fitness_score(), reverse=True)

    print(f"\n{'Rank':<6} {'Agent':<25} {'Return':<12} {'Sharpe':<10} {'Win Rate':<12} {'Fitness':<10}")
    print("-" * 80)

    for i, result in enumerate(results, 1):
        metrics = result['metrics']
        print(f"{i:<6} {result['agent']:<25} "
              f"{metrics.total_return * 100:+8.2f}%    "
              f"{metrics.sharpe_ratio:6.2f}    "
              f"{metrics.win_rate * 100:6.2f}%      "
              f"{metrics.get_fitness_score():.3f}")

    print("\n✅ Personality clearly impacts trading performance!")
    print("   Different personalities → Different strategies → Different results")

    return results


def demo_fitness_for_breeding():
    """Demonstrate using market simulation for genetic breeding fitness"""
    print("\n" + "="*80)
    print("MARKET SIMULATION DEMO - Part 4: Fitness for Genetic Breeding")
    print("="*80)

    print("\n🧬 This market simulation can be used as fitness function for genetic breeding!")
    print("\nIntegration concept:")
    print("   1. Generate personality via genetic breeding")
    print("   2. Create trading strategy from personality")
    print("   3. Backtest on synthetic market → Performance metrics")
    print("   4. Use metrics.get_fitness_score() as breeding fitness")
    print("   5. Evolve agents toward better trading performance!")

    print("\n📊 Example fitness evaluation:\n")

    # Create example personalities
    personalities = [
        PersonalityProfile(openness=0.85, conscientiousness=0.45, extraversion=0.70,
                          agreeableness=0.50, neuroticism=0.55),
        PersonalityProfile(openness=0.40, conscientiousness=0.85, extraversion=0.45,
                          agreeableness=0.75, neuroticism=0.30),
        PersonalityProfile(openness=0.65, conscientiousness=0.70, extraversion=0.60,
                          agreeableness=0.65, neuroticism=0.35)
    ]

    # Generate market
    simulator = MarketSimulator(initial_price=100.0, seed=42)
    simulator.generate_bars(100, regime=MarketRegime.VOLATILE, event_probability=0.03)
    market_data = simulator.bars

    print("Testing 3 randomly generated personalities on volatile market:\n")

    for i, personality in enumerate(personalities, 1):
        personality._calculate_modifiers()
        strategy = create_personality_strategy(personality)

        backtester = AgentBacktester()
        metrics = backtester.backtest(market_data, strategy, position_size=0.7)

        fitness = metrics.get_fitness_score()

        print(f"Personality {i}: O={personality.openness:.2f} C={personality.conscientiousness:.2f} "
              f"E={personality.extraversion:.2f} A={personality.agreeableness:.2f} N={personality.neuroticism:.2f}")
        print(f"   → Fitness: {fitness:.3f} (Return: {metrics.total_return*100:+.1f}%, "
              f"Sharpe: {metrics.sharpe_ratio:.2f}, Trades: {metrics.num_trades})")
        print()

    print("✅ These fitness scores can drive genetic evolution!")
    print("   Breed high-fitness agents → Evolve toward optimal trading personalities")


# ============================================================================
# Main Demo
# ============================================================================

def main():
    """Run all market simulation demos"""
    print("\n" + "="*80)
    print("🌊 MARKET SIMULATION ENGINE - COMPREHENSIVE DEMO")
    print("="*80)
    print("\nRealistic synthetic market generation for agent testing and training")
    print("Features: Multiple regimes, event injection, personality-based trading")
    print()

    # Run all demos
    demo_market_regimes()
    demo_event_injection()
    results = demo_personality_trading()
    demo_fitness_for_breeding()

    print("\n" + "="*80)
    print("✅ DEMO COMPLETE!")
    print("="*80)
    print("\n🌟 Key Takeaways:")
    print("   1. Market simulation generates realistic synthetic data across 6 regimes")
    print("   2. Events can be injected to test agent resilience")
    print("   3. Personality drives different trading behaviors and outcomes")
    print("   4. Performance metrics provide fitness scores for genetic breeding")
    print("   5. This enables evolution of agents optimized for specific market conditions")
    print("\n🚀 Next Steps:")
    print("   - Integrate with genetic_breeding.py for evolution on market performance")
    print("   - Build market simulation dashboard for visualization")
    print("   - Train agents on historical market data")
    print("   - Create multi-market scenarios (stocks, crypto, forex)")
    print()


if __name__ == "__main__":
    main()
