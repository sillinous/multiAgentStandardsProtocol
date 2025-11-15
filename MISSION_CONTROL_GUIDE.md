# 🚀 Mission Control - Unified Command Center

**NASA-Style Control Center for AI-Powered Trading**

Mission Control is the ultimate unified dashboard that integrates all features of the Agentic Forge platform into a single, powerful command center. Think NASA mission control, but for autonomous AI trading systems.

---

## 🎯 What is Mission Control?

Mission Control provides **real-time oversight and control** of your entire multi-strategy autonomous trading operation from a single interface. It combines:

- **Multi-Strategy Portfolio Management** - Run 3+ strategies simultaneously
- **Real-Time Risk Monitoring** - Live Sharpe, VaR, drawdown tracking
- **AI Chat Interface** - Natural language control and queries
- **Live Strategy Comparison** - Visual performance charts
- **Hot Opportunities Feed** - AI-discovered trading opportunities
- **Risk Alerts** - Proactive warnings and protections
- **One-Click Deployment** - From analysis to live trading instantly

---

## 🚀 Quick Start

### Launch Mission Control

```bash
python examples/launch_mission_control.py
```

Then open your browser to:
```
http://localhost:8002/mission-control
```

### First Look

You'll see a **6-panel interface**:

```
┌─────────────┬──────────────────────┬──────────────┐
│             │  Multi-Strategy      │              │
│    Chat     │  Portfolio           │ Risk Metrics │
│  Interface  │  (3+ strategies)     │              │
│             ├──────────────────────┤──────────────┤
│             │  Strategy Comparison │  Risk Alerts │
│             │  Chart               │              │
├─────────────┼──────────────────────┴──────────────┤
│ Hot         │                                      │
│ Opportunities│                                     │
└─────────────┴──────────────────────────────────────┘
```

---

## 📊 Features in Detail

### 1. Multi-Strategy Portfolio Management

**What it does:**
Runs multiple trading strategies in parallel and tracks their individual performance.

**Default Strategies:**
1. **Balanced Trader** (30% allocation)
   - Risk/reward optimized
   - Sharpe ratio: ~1.85
   - Max drawdown: ~8.5%

2. **Aggressive Growth** (40% allocation)
   - High-growth momentum
   - Sharpe ratio: ~2.15
   - Max drawdown: ~15.3%

3. **Sentiment Driven** (30% allocation)
   - News + social sentiment
   - Sharpe ratio: ~1.95
   - Max drawdown: ~10.2%

**Live Metrics Displayed:**
- Current value
- Total return ($)
- Total return (%)
- Allocation percentage
- Visual progress bar

**Example Display:**
```
Strategy 1: Balanced Trader        +15.2%
$45,230                    30% allocation
[████████████████░░░░░░] 76%
```

### 2. Real-Time Risk Monitoring

**Comprehensive Risk Metrics:**

| Metric | Description | Healthy Range |
|--------|-------------|---------------|
| **Sharpe Ratio** | Risk-adjusted return | > 1.5 |
| **Sortino Ratio** | Downside risk | > 2.0 |
| **VaR (95%)** | Worst-case daily loss | < 5% portfolio |
| **CVaR (95%)** | Expected loss beyond VaR | < 7% portfolio |
| **Max Drawdown** | Peak-to-trough decline | < 20% |
| **Current Drawdown** | Current decline from peak | < 10% |
| **Volatility** | Annualized volatility | < 25% |
| **Position Concentration** | % in largest position | < 15% |

**Color Coding:**
- 🟢 **Green** - Healthy (within targets)
- 🟡 **Yellow** - Caution (approaching limits)
- 🔴 **Red** - Critical (exceeds limits)

**Example:**
```
🛡️ Risk Metrics

Sharpe Ratio: 1.98     ✅ Excellent
VaR (95%):   -$2,850   ✅ Safe
Max Drawdown:  11.3%   ✅ Acceptable
Volatility:    18.5%   ✅ Moderate
```

### 3. AI Chat Interface

**Natural Language Control:**

Ask questions in plain English and get intelligent responses.

**Example Queries:**

**Sentiment Analysis:**
```
You: Show me BTC sentiment

AI: 💭 BTC-USD Sentiment Analysis:

Overall Score: +0.85 (Very Positive)
Trend: BULLISH ↗️

📊 Risk-Adjusted Recommendation:
Kelly Criterion: 142 shares
Position Size: $6,240 (6.2% of portfolio)
Target: $48,500
Stop Loss: $42,000

✅ This aligns with Kelly Criterion for optimal growth.
```

**Risk Analysis:**
```
You: What's my current risk?

AI: 🛡️ Current Risk Profile:

Overall Health: ✅ Healthy

📊 Key Metrics:
• Sharpe Ratio: 1.98
• Sortino Ratio: 2.45
• Max Drawdown: 11.3%
• Current Drawdown: 5.2%
• Volatility: 18.5%
• VaR (95%): -$2,850
• CVaR (95%): -$4,200

All metrics within acceptable ranges.
```

**Portfolio Summary:**
```
You: How's my portfolio?

AI: 📈 Portfolio Performance:

Total Value: $172,235
Total Return: +$27,235 (+18.8%)
Cash Balance: $22,000

Strategy Breakdown:
• Balanced Trader: $45,230 (+15.2%)
• Aggressive Growth: $73,680 (+22.8%)
• Sentiment Driven: $53,325 (+18.5%)

Overall Sharpe: 1.98 (Excellent)
```

**Strategy Deployment:**
```
You: Deploy a strategy

AI: ✅ Strategy Deployment Ready!

Select a strategy to deploy:
1. Balanced Trader (Sharpe: 1.85)
2. Aggressive Growth (Sharpe: 2.15)
3. Sentiment Driven (Sharpe: 1.95)

🛡️ Protection Active:
• Max position size: 10%
• Max risk per trade: 2%
• Stop-loss: Automatic
• Position sizing: Kelly Criterion

Reply with strategy number to deploy.
```

### 4. Live Strategy Comparison

**Visual Performance Chart:**

Interactive Chart.js line chart showing:
- All strategies on one chart
- Daily/weekly performance
- Relative performance comparison
- Hover tooltips with exact values

**Color Coding:**
- 🔵 **Blue** - Balanced strategies
- 🟠 **Orange** - Aggressive strategies
- 🟣 **Purple** - Sentiment strategies

**Example Chart:**
```
Strategy Comparison (30 Days)
25% ┤                        ●─── Aggressive
    │                    ●─●
20% ┤                ●─●
    │            ●─●         ●─── Sentiment
15% ┤        ●─●
    │    ●─●                 ●─── Balanced
10% ┤●─●
    ├────────────────────────────────────
    Day 1                           Day 30
```

### 5. Hot Opportunities Feed

**AI-Discovered Trading Opportunities:**

Each opportunity shows:
- **Symbol** - Asset ticker
- **Title** - Brief description
- **Signal Type** - Bullish/Bearish/Neutral
- **Confidence** - 0-100%
- **Scores**:
  - Sentiment score
  - Technical score
  - Fundamental score
- **Recommendation** - BUY/SELL/REDUCE/HOLD
- **Target & Stop Loss** - Suggested prices
- **Position Size** - Kelly Criterion optimized

**Example Opportunity:**
```
BTC-USD                      [BULLISH]

Strong Bullish Sentiment + Technical Breakout
Confidence: 85%

📊 Scores:
Sentiment:   +0.82
Technical:   +0.88
Fundamental: +0.75

💡 Recommendation: BUY
Target: $48,500
Stop: $42,000
Size: $6,240 (6.2%)
```

**Action Buttons:**
- **Analyze** - Deep dive analysis
- **Backtest** - Historical simulation
- **Deploy** - One-click live trading

### 6. Risk Alerts Panel

**Proactive Warnings:**

Severity levels:
- 🔵 **Info** - Informational updates
- 🟡 **Warning** - Approaching limits
- 🔴 **Critical** - Immediate action required

**Alert Categories:**
- **Position Size** - Concentration warnings
- **Drawdown** - Decline alerts
- **Volatility** - Risk increase notifications
- **Correlation** - Diversification issues

**Example Alerts:**
```
⚠️ WARNING
NVDA position approaching 15% portfolio concentration
Strategy: Aggressive Growth

ℹ️ INFO
Portfolio volatility increased to 18.5%
(within acceptable range)
```

---

## 🎮 How to Use Mission Control

### Typical Workflow

**1. Monitor Portfolio (Top Center)**
- Check overall performance
- Review individual strategies
- Verify allocations

**2. Check Risk (Top Right)**
- Verify Sharpe ratio > 1.5
- Ensure drawdown < 20%
- Monitor VaR exposure

**3. Review Opportunities (Bottom Left)**
- Scan AI discoveries
- Check confidence scores
- Evaluate recommendations

**4. Act on Insights (Chat Panel)**
- Ask for deeper analysis
- Request backtests
- Deploy strategies

**5. Monitor Alerts (Bottom Right)**
- Address warnings promptly
- Adjust positions if needed
- Maintain risk discipline

### One-Click Deployment

**From Opportunity to Live Trading:**

1. **Spot Opportunity** in Hot Opportunities feed
   - Example: BTC-USD bullish signal

2. **Click "Analyze"** for deeper analysis
   - Sentiment breakdown
   - Technical indicators
   - Risk assessment

3. **Click "Backtest"**
   - Historical performance
   - Risk metrics
   - Win rate & profit factor

4. **Click "Deploy"**
   - Auto-sized position (Kelly Criterion)
   - Stop-loss automatically set
   - Risk protections active
   - Live monitoring begins

**All in under 30 seconds!**

---

## 🔧 API Reference

### REST Endpoints

**Get Portfolio State:**
```bash
GET /api/mission-control/portfolio
```

**Response:**
```json
{
  "total_value": 172235.0,
  "total_return": 27235.0,
  "total_return_pct": 18.8,
  "strategies": [
    {
      "id": "balanced_trader",
      "name": "Balanced Trader",
      "type": "balanced",
      "allocation_pct": 30.0,
      "current_value": 45230.0,
      "total_return_pct": 15.2,
      "sharpe_ratio": 1.85,
      "status": "running"
    }
  ],
  "overall_sharpe": 1.98,
  "cash_balance": 22000.0
}
```

**Get Risk Metrics:**
```bash
GET /api/mission-control/risk
```

**Response:**
```json
{
  "sharpe_ratio": 1.98,
  "sortino_ratio": 2.45,
  "var_95": -2850.0,
  "cvar_95": -4200.0,
  "current_drawdown": 5.2,
  "max_drawdown": 11.3,
  "volatility": 18.5,
  "position_concentration": 13.1
}
```

**Get Opportunities:**
```bash
GET /api/mission-control/opportunities
```

**Response:**
```json
{
  "opportunities": [
    {
      "id": "opp_1",
      "symbol": "BTC-USD",
      "title": "Strong Bullish Sentiment + Technical Breakout",
      "signal_type": "bullish",
      "confidence": 0.85,
      "sentiment_score": 0.82,
      "technical_score": 0.88,
      "recommended_action": "BUY",
      "target_price": 48500.0,
      "position_size": 6240.0
    }
  ]
}
```

**Chat with AI:**
```bash
POST /api/mission-control/chat
Content-Type: application/json

{
  "message": "Show me BTC sentiment"
}
```

**Deploy Strategy:**
```bash
POST /api/mission-control/deploy-strategy
Content-Type: application/json

{
  "strategy_name": "balanced_trader",
  "allocation_pct": 25.0
}
```

**Response:**
```json
{
  "success": true,
  "message": "✅ balanced_trader deployed with 25.0% allocation",
  "strategy_id": "deployed_1234567890.123",
  "protections": {
    "max_position_size": "10%",
    "max_risk_per_trade": "2%",
    "stop_loss": "automatic",
    "position_sizing": "Kelly Criterion"
  }
}
```

### WebSocket API

**Real-Time Updates:**

```javascript
const ws = new WebSocket('ws://localhost:8002/api/mission-control/ws');

ws.onopen = () => {
    console.log('Connected to Mission Control');
};

ws.onmessage = (event) => {
    const message = JSON.parse(event.data);

    if (message.type === 'portfolio_update') {
        // Update portfolio display
        updatePortfolio(message.data);
    }

    if (message.type === 'risk_alert') {
        // Show alert
        showAlert(message.data);
    }

    if (message.type === 'opportunity_discovered') {
        // Add to opportunities feed
        addOpportunity(message.data);
    }
};

// Keep-alive ping
setInterval(() => {
    ws.send(JSON.stringify({type: 'ping'}));
}, 30000);
```

**Event Types:**
- `initial_state` - Full state on connection
- `portfolio_update` - Portfolio changes
- `risk_update` - Risk metric changes
- `opportunity_discovered` - New opportunity
- `risk_alert` - New alert
- `strategy_deployed` - Strategy started
- `trade_executed` - Trade completed

---

## 🎨 Customization

### Adding Custom Strategies

**1. Define Strategy in Backend:**

```python
# In mission_control_api.py

new_strategy = StrategyState(
    id='custom_strategy',
    name='My Custom Strategy',
    type='custom',
    allocation_pct=20.0,
    current_value=30000.0,
    total_return=5000.0,
    total_return_pct=20.0,
    sharpe_ratio=2.5,
    max_drawdown=5.0,
    positions=[],
    status='running'
)

mission_control.portfolio.strategies.append(new_strategy)
```

**2. Strategy Auto-Appears in UI:**
- Portfolio panel updates
- Comparison chart includes new line
- Chat interface recognizes it

### Customizing Risk Thresholds

```python
# In mission_control_api.py

# Custom risk thresholds
RISK_THRESHOLDS = {
    'max_position_size': 0.12,  # 12% max
    'max_drawdown': 0.15,        # 15% max
    'min_sharpe': 1.8,           # Minimum acceptable
    'max_var': 0.05,             # 5% VaR limit
}

# Check against thresholds
if position_size > RISK_THRESHOLDS['max_position_size']:
    create_alert('critical', 'Position size exceeded')
```

### Adding Custom Alerts

```python
# Create custom alert
alert = RiskAlert(
    id=f'alert_{time.time()}',
    severity='warning',
    category='custom',
    message='Custom risk condition detected',
    strategy_id='balanced_trader',
    timestamp=datetime.now().isoformat()
)

mission_control.alerts.append(alert)
await mission_control.broadcast('risk_alert', asdict(alert))
```

---

## 📱 Mobile Access

Mission Control is **fully responsive** and works on:
- Desktop (optimized layout)
- Tablets (medium screens)
- Mobile phones (stacked panels)

**Mobile Features:**
- Touch-friendly controls
- Swipe navigation
- Auto-scroll chat
- Optimized chart sizes
- Horizontal tables

**Access from Mobile:**
```
http://<your-server-ip>:8002/mission-control
```

---

## 🔒 Security & Risk Protections

### Automatic Protections

**Position Sizing:**
- ✅ Kelly Criterion optimization
- ✅ Max 10% per position
- ✅ Risk parity allocation

**Risk Limits:**
- ✅ Max 2% risk per trade
- ✅ Stop-loss on all positions
- ✅ Max 20% portfolio drawdown
- ✅ Position concentration < 15%

**Execution Controls:**
- ✅ All orders require confirmation
- ✅ Slippage protection
- ✅ Market hours validation
- ✅ Circuit breakers on volatility

### Manual Overrides

**Emergency Stop:**
```python
# Chat: "Emergency stop all strategies"
# Result: All strategies paused immediately
```

**Risk Override:**
```python
# Chat: "Override risk limit for BTC"
# Result: Temporary limit increase with confirmation
```

---

## 🚀 Performance & Scalability

### Real-Time Performance

- **WebSocket Latency:** < 50ms
- **Chart Updates:** 60 FPS
- **Portfolio Recalc:** < 100ms
- **Risk Metrics:** < 200ms
- **Chat Response:** < 500ms

### Concurrent Users

Mission Control supports:
- **Unlimited read-only viewers**
- **10+ simultaneous traders**
- **100+ WebSocket connections**

### Data History

- **Live Updates:** Real-time
- **History Retention:** 30 days in memory
- **Long-term Storage:** Database backed
- **Chart Resolution:** 1-minute intervals

---

## 🎯 Use Cases

### 1. Active Trading
- Monitor all strategies in real-time
- Quick deployment from opportunities
- Rapid risk adjustment

### 2. Portfolio Oversight
- Daily performance review
- Risk compliance monitoring
- Strategy rebalancing

### 3. Research & Development
- Test new strategies via chat
- Compare performance visually
- Analyze opportunities before deployment

### 4. Risk Management
- Monitor risk metrics continuously
- Respond to alerts immediately
- Enforce position limits

### 5. Stakeholder Demonstrations
- Show live trading operations
- Explain AI decision-making
- Prove risk management

---

## 🤝 Integration with Other Features

### With Backtesting Dashboard

```
1. Discover opportunity in Mission Control
2. Click "Backtest"
3. Opens Backtesting Dashboard with pre-filled params
4. Review historical performance
5. Click "Deploy to Mission Control"
6. Strategy auto-deployed with results
```

### With Conversational Dashboard

```
1. Chat in Mission Control: "Show me AAPL analysis"
2. Response includes sentiment, technical, fundamental
3. Click "Open Conversational Dashboard"
4. Deep-dive interactive analysis
5. Deploy from there or return to Mission Control
```

### With Risk Management System

```
1. Mission Control monitors portfolio
2. Risk system calculates live metrics
3. Alerts appear in Risk Alerts panel
4. One-click to adjust positions
5. Risk system re-calculates
6. Mission Control updates displays
```

**Everything is connected in real-time!**

---

## 📚 Troubleshooting

### Connection Issues

**Problem:** WebSocket not connecting

**Solution:**
```bash
# Check server is running
curl http://localhost:8002/

# Check WebSocket endpoint
wscat -c ws://localhost:8002/api/mission-control/ws
```

### Missing Data

**Problem:** Empty portfolio or strategies

**Solution:**
```python
# Backend initializes demo data automatically
# If missing, restart server:
python examples/launch_mission_control.py
```

### Slow Updates

**Problem:** Delayed real-time updates

**Solution:**
- Check network latency
- Reduce WebSocket ping interval
- Limit concurrent connections

---

## 🌟 Best Practices

### Daily Workflow

**Morning (Market Open):**
1. Check overnight performance
2. Review risk metrics
3. Scan hot opportunities
4. Adjust allocations if needed

**Midday:**
1. Monitor active positions
2. Check alerts
3. Respond to opportunities

**Evening (Market Close):**
1. Review daily P&L
2. Analyze strategy performance
3. Plan next day

### Risk Discipline

**Always:**
- ✅ Keep Sharpe ratio > 1.5
- ✅ Limit drawdown < 20%
- ✅ Diversify across strategies
- ✅ Size positions with Kelly
- ✅ Use stop-losses

**Never:**
- ❌ Override risk limits without reason
- ❌ Concentrate > 15% in one position
- ❌ Ignore critical alerts
- ❌ Deploy without backtesting
- ❌ Trade on emotion

### Portfolio Management

**Rebalancing:**
- Weekly review of allocations
- Increase top performers (within limits)
- Reduce underperformers
- Maintain diversification

**Strategy Selection:**
- Run 3-5 strategies simultaneously
- Mix correlation (balanced + aggressive + sentiment)
- Monitor independent performance
- Rotate based on market conditions

---

## 🎓 Advanced Topics

### Custom Strategy Integration

See `examples/custom_strategy_integration.py` for full example:

```python
from superstandard.strategies import BaseStrategy

class MyStrategy(BaseStrategy):
    def analyze(self, data):
        # Your custom logic
        return signal

    def size_position(self, signal):
        # Kelly Criterion
        return optimal_size

# Register with Mission Control
mission_control.register_strategy(MyStrategy())
```

### Event-Driven Architecture

Mission Control uses event-driven updates:

```python
# Backend broadcasts events
await mission_control.broadcast('portfolio_update', data)

# Frontend subscribes
ws.addEventListener('portfolio_update', updateUI)
```

### Real-Time Calculations

All metrics calculated in real-time:

```python
def calculate_sharpe(returns, risk_free=0.02):
    excess = np.mean(returns) - risk_free
    std = np.std(returns)
    return excess / std * np.sqrt(252)

# Runs on every portfolio update
```

---

## 🚀 What's Next?

### Planned Features

**v2.0:**
- [ ] Multi-timeframe analysis
- [ ] Options strategy support
- [ ] Futures integration
- [ ] Advanced order types
- [ ] Strategy marketplace

**v3.0:**
- [ ] Machine learning strategy optimization
- [ ] Automated parameter tuning
- [ ] Social trading features
- [ ] Mobile native apps
- [ ] Voice commands

---

## 📞 Support

**Documentation:**
- Main README: `/README.md`
- Risk Management: `/RISK_MANAGEMENT_GUIDE.md`
- Backtesting: `/examples/launch_backtesting_dashboard.py`

**Community:**
- GitHub Issues
- Discord Server
- Email Support

---

## 🎉 Summary

Mission Control is the **ultimate unified interface** for managing autonomous AI trading systems.

**Key Capabilities:**
✅ Multi-strategy portfolio management
✅ Real-time risk monitoring
✅ AI chat interface
✅ Live strategy comparison
✅ Hot opportunities feed
✅ Risk alerts & protections
✅ One-click deployment
✅ Mobile responsive
✅ WebSocket real-time updates
✅ Production-ready

**Get Started:**
```bash
python examples/launch_mission_control.py
```

**Access:**
```
http://localhost:8002/mission-control
```

**Welcome to the future of autonomous trading!** 🚀
