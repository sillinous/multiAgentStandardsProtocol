# Setup Guide - Agentic Forge Multi-Agent System

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Git

## Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd multiAgentStandardsProtocol
```

### 2. Install Core Requirements

```bash
pip install -r requirements.txt
```

**Core Dependencies Installed**:
- ✅ FastAPI - Web framework for API server
- ✅ Uvicorn - ASGI server for running the API
- ✅ Pydantic - Data validation
- ✅ WebSockets - Real-time communication
- ✅ Pandas & NumPy - Data manipulation
- ✅ HTTPx - Async HTTP client

### 3. Optional: Install Historical Data Support

For real market data validation (optional):

```bash
pip install yfinance
```

**Note**: If `yfinance` installation fails due to `multitasking` dependency issues, you can still use all other features. Historical data validation will be unavailable but all synthetic market simulation and genetic breeding features will work.

Alternative if yfinance fails:
```bash
# The system works perfectly without yfinance
# You can use synthetic market simulation instead
```

## Quick Start

### 1. Run the API Server

```bash
cd src
python -m superstandard.api.server
```

The server will start on `http://localhost:8080`

### 2. Access Dashboards

Open your browser to:
- **Main Hub**: http://localhost:8080/dashboard
- **Personality Dashboard**: http://localhost:8080/dashboard/personality
- **Evolution Dashboard**: http://localhost:8080/dashboard/evolution
- **Market Simulation**: http://localhost:8080/dashboard/market-simulation

### 3. Run Demos

**Personality System Demo**:
```bash
python examples/personality_demo.py
```

**Genetic Evolution Demo**:
```bash
python examples/genetic_evolution_demo.py
```

**Market Simulation Demo**:
```bash
python examples/market_simulation_demo.py
```

**Complete Pipeline Demo**:
```bash
python examples/genetic_evolution_on_market_performance.py
```

**Historical Data Validation** (requires yfinance):
```bash
python examples/validate_on_historical_data.py
```

## Verification

### Test Basic Functionality

```python
# Test personality system
from superstandard.agents.personality import PersonalityProfile

profile = PersonalityProfile.random()
profile._calculate_modifiers()
print(f"Risk Tolerance: {profile.get_modifier('risk_tolerance'):.2f}")
```

### Test Market Simulation

```python
from superstandard.trading import MarketSimulator, MarketRegime

simulator = MarketSimulator(initial_price=100.0)
bars = simulator.generate_bars(50, regime=MarketRegime.BULL)
print(f"Generated {len(bars)} market bars")
```

### Test API Server

```bash
# In one terminal:
cd src && python -m superstandard.api.server

# In another terminal:
curl http://localhost:8080/api/admin/stats
```

## Features Available

### ✅ Without Any Optional Dependencies

- Agent Personality System (5-Factor OCEAN model)
- Genetic Breeding Engine (4 crossover methods, 4 selection strategies)
- Synthetic Market Simulation (6 market regimes)
- Complete Backtesting Framework
- Agent Evolution Pipeline
- All Dashboards (Personality, Evolution, Market Simulation)
- API Server with WebSocket support

### ✅ With yfinance Installed

- Historical Market Data Fetching (Yahoo Finance)
- Real-World Validation on SPY, BTC, etc.
- Multi-Asset Support (stocks, crypto, forex, commodities)
- Market Regime Detection on Real Data
- Automated Caching System

## Troubleshooting

### yfinance Installation Fails

**Issue**: `multitasking` dependency fails to build

**Solution**: Skip yfinance installation. The core system works perfectly without it.

```bash
# Install everything except yfinance
pip install fastapi uvicorn pydantic websockets python-multipart aiofiles httpx pandas numpy
```

You can still:
- Run all demos except historical data validation
- Use synthetic market simulation
- Evolve agents on generated data
- Access all dashboards

### Import Errors

**Issue**: `ModuleNotFoundError: No module named 'superstandard'`

**Solution**: Run from project root or add to PYTHONPATH:

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

Or run examples with:
```bash
python -c "import sys; sys.path.insert(0, 'src'); exec(open('examples/personality_demo.py').read())"
```

### Port Already in Use

**Issue**: `Address already in use` when starting server

**Solution**: Change port or kill existing process:

```bash
# Use different port
cd src && python -m superstandard.api.server --port 8081

# Or kill existing process
lsof -ti:8080 | xargs kill -9
```

## Development Setup

### Install Development Dependencies

```bash
pip install pytest pytest-asyncio pytest-cov black mypy pylint
```

### Run Tests

```bash
pytest
```

### Format Code

```bash
black src/ examples/
```

### Type Checking

```bash
mypy src/
```

## Directory Structure

```
multiAgentStandardsProtocol/
├── src/
│   └── superstandard/
│       ├── agents/           # Personality & genetic breeding
│       ├── trading/          # Market simulation & historical data
│       ├── api/              # FastAPI server & dashboards
│       └── protocols/        # ANP, ACP, AConsP protocols
├── examples/                 # Demo scripts
├── requirements.txt          # Python dependencies
├── SETUP.md                  # This file
└── COMPLETE_SYSTEM_SUMMARY.md  # Full system documentation
```

## Next Steps

1. **Run Demos**: Try all example scripts to see the system in action
2. **Access Dashboards**: Explore the visualizations
3. **Read Documentation**: Check COMPLETE_SYSTEM_SUMMARY.md
4. **Experiment**: Create your own agents and evolve them!

## Support

- **Documentation**: See COMPLETE_SYSTEM_SUMMARY.md
- **Issues**: Open GitHub issue
- **Examples**: Check `/examples` directory

## Production Deployment

For production use:

1. Set up virtual environment
2. Configure environment variables
3. Use production ASGI server (e.g., gunicorn with uvicorn workers)
4. Set up monitoring and logging
5. Configure SSL/TLS for HTTPS
6. Implement rate limiting and authentication

See deployment guides for specific platforms (AWS, GCP, Azure, etc.)
