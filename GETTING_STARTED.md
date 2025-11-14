# 🚀 Getting Started with Agentic Standards Protocol

Welcome! This guide will get you up and running with the Agentic Standards Protocol in **5 minutes**.

---

## 📋 Prerequisites

### Required
- **Python 3.8+** - [Download Python](https://www.python.org/downloads/)
- **pip** - Comes with Python
- **git** - [Download Git](https://git-scm.com/downloads)

### Optional (for enhanced features)
- **OpenAI API Key** - For LLM-powered intent parsing ([Get key](https://platform.openai.com/api-keys))
- **Production service API keys** - For real data sources (see [Service Setup](#production-service-api-keys))

---

## ⚡ Quick Install

### 1. Clone the Repository

```bash
git clone https://github.com/sillinous/multiAgentStandardsProtocol.git
cd multiAgentStandardsProtocol
```

### 2. Install Python Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

> **Note**: If `requirements.txt` doesn't exist yet, the system uses standard Python libraries. You may need to install: `pip install aiohttp pyyaml`

---

## 🎯 Your First Demo

Let's run your first demo to see the system in action!

### Option 1: Natural Language Chat (Easiest!)

The simplest way to experience the platform:

```bash
python src/superstandard/cli/chat.py
```

**What you'll see**:
```
================================================================================
🤖 Agentic Standards Protocol - Natural Language Interface
================================================================================

Talk to autonomous agents in plain English!

Examples:
  • Find me business opportunities in healthcare
  • Analyze competitors for stripe.com
  • What are the economic trends?
  • Show demographics for California
  • help

Type 'exit' or 'quit' to exit
================================================================================

You: _
```

**Try these queries**:
1. `Find me business opportunities in technology`
2. `What's the system status?`
3. `help`

### Option 2: A2A Autonomous Collaboration

Watch agents create and coordinate with each other:

```bash
python examples/a2a_autonomous_collaboration_demo.py
```

**What happens**:
- FactoryMetaAgent creates 4 specialized agents
- CoordinatorMetaAgent orchestrates a 4-phase workflow
- Agents communicate via A2A protocol
- Results displayed with complete statistics

**Duration**: ~15 seconds

### Option 3: Real-Time Dashboard

See the system working in real-time:

```bash
# Terminal 1: Run the demo
python examples/live_dashboard_demo.py

# Choose mode (1, 2, or 3)

# Dashboard will auto-open in browser
# Or manually open: dashboard.html
```

**What you'll see**:
- Live event stream as agents execute
- Real-time metrics updating
- Opportunity cards appearing
- Quality scores tracking

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Optional: For LLM-powered intent parsing (95%+ accuracy)
OPENAI_API_KEY=sk-...

# Optional: Production service API keys (for real data)
SIMILARWEB_API_KEY=your-key-here
QUALTRICS_API_KEY=your-key-here
FRED_API_KEY=your-key-here
CENSUS_API_KEY=your-key-here
```

### Production Service API Keys

#### Free Services (Recommended to start!)

**FRED (Federal Reserve Economic Data)**:
1. Visit https://fred.stlouisfed.org/docs/api/api_key.html
2. Sign up for free account
3. Get API key instantly
4. Add to `.env`: `FRED_API_KEY=your-key`

**US Census Bureau**:
1. Visit https://api.census.gov/data/key_signup.html
2. Request free API key
3. Receive key via email
4. Add to `.env`: `CENSUS_API_KEY=your-key`

#### Paid Services (Optional)

**SimilarWeb** - Competitive intelligence:
- Visit https://www.similarweb.com/api/
- Requires paid plan
- Add to `.env`: `SIMILARWEB_API_KEY=your-key`

**Qualtrics** - Market research:
- Visit https://www.qualtrics.com/
- Requires enterprise account
- Add to `.env`: `QUALTRICS_API_KEY=your-key`

> **Note**: System automatically falls back to mock data if API keys not provided!

---

## 📖 Understanding the System

### Architecture Overview

The platform has 6 main layers:

```
1. USER INTERFACES
   - Natural Language Chat
   - Real-Time Dashboard

2. ORCHESTRATION
   - Intent Parser & Agent Mapper
   - Opportunity Discovery Orchestrator
   - Dashboard Event Bus

3. META-AGENTS
   - FactoryMetaAgent (creates agents)
   - CoordinatorMetaAgent (orchestrates)

4. A2A MESSAGE BUS
   - Priority queues
   - Message routing
   - Pub/sub patterns

5. AGENTS & SERVICES
   - 4 production agents
   - 4 production services
   - Extensible architecture

6. DATA SOURCES
   - SimilarWeb, Qualtrics, FRED, Census
   - Automatic mock fallback
```

### Key Concepts

**Agents**: Specialized AI workers that perform specific tasks
- Example: `IdentifyCompetitorsAgent` analyzes competitive landscape

**Services**: Data source integrations
- Example: `FREDService` fetches economic data from Federal Reserve

**Orchestrators**: Coordinate multiple agents
- Example: `OpportunityDiscoveryOrchestrator` runs 4 agents in parallel

**Meta-Agents**: Agents that create/coordinate other agents
- Example: `FactoryMetaAgent` creates specialized agents on-demand

**A2A Protocol**: Standards-compliant agent communication
- Enables autonomous agent coordination

---

## 🎬 Complete Demo Walkthrough

### Demo 1: Natural Language Chat

**Step 1**: Start the chat
```bash
python src/superstandard/cli/chat.py
```

**Step 2**: Try a simple query
```
You: Find me business opportunities in technology
```

**What happens**:
1. Intent parser classifies: `discover_opportunities`
2. Parameter extractor gets: `industry=technology`
3. Agent mapper routes to: `OpportunityDiscoveryOrchestrator`
4. 4 agents execute in parallel
5. Results synthesized
6. Natural language response generated

**Step 3**: Try a complex query
```
You: Find me SaaS opportunities in healthcare with 85% confidence
```

**What happens**:
- Extracts: `industry=healthcare`, `category=SaaS`, `min_confidence=0.85`
- Runs same workflow with filters applied

**Step 4**: Check system status
```
You: What's the system status?
```

Returns: metrics, active agents, uptime

**Step 5**: Get help
```
You: help
```

Shows: all available commands

### Demo 2: A2A Collaboration

**Step 1**: Run the demo
```bash
python examples/a2a_autonomous_collaboration_demo.py
```

**What you'll see** (5 phases):

**Phase 1**: FactoryMetaAgent creates agents
```
🏭 FactoryMetaAgent creating 4 specialized agents...
   Creating: DataCollectorAgent...
   ✅ DataCollectorAgent created and registered
   [... 3 more agents ...]
```

**Phase 2**: Workflow defined
```
✅ Workflow defined: 4 phases
   1. Data Collection (2 tasks)
   2. Analysis (1 task)
   3. Synthesis (1 task)
   4. Validation (1 task)
```

**Phase 3**: CoordinatorMetaAgent orchestrates
```
▶️  Starting phase: Data Collection
📤 Task assigned to DataCollectorAgent
✅ Task completed: task-1-1
[... more tasks ...]
```

**Phase 4**: Results displayed
```
📊 Results by Phase:
   PHASE-1:
      ✅ task-1-1: {data_collected: true, records: 150}
      [... more results ...]
```

**Phase 5**: Statistics shown
```
🏭 FactoryMetaAgent Statistics:
   • Total Agents Created: 4
   • Active Agents: 4

📡 A2A Message Bus Statistics:
   • Total Messages: 15
   • Successful Deliveries: 15
```

### Demo 3: Real-Time Dashboard

**Step 1**: Run the demo
```bash
python examples/live_dashboard_demo.py
```

**Step 2**: Choose mode
```
Select demo mode:
1. Single Scenario (Technology in United States)
2. Multiple Scenarios (Technology, Healthcare, Financial Services)
3. Custom Scenario (Enter your own parameters)

Enter choice (1-3, default=1): 1
```

**Step 3**: Dashboard opens automatically
- Or manually open: `dashboard.html`

**What you'll see**:
- **Top metrics**: Updating in real-time
- **Event stream**: New events sliding in
- **Opportunity cards**: Appearing as discovered
- **Connection status**: Live indicator

**Step 4**: Explore the dashboard
- Scroll through event stream
- Click on opportunity cards
- Watch metrics update
- See quality scores

---

## 🧪 Testing the System

### Test Natural Language Understanding

```bash
python src/superstandard/cli/chat.py --query "Find me opportunities in healthcare"
```

Should return opportunities in healthcare industry.

### Test A2A Protocol

```bash
python examples/a2a_autonomous_collaboration_demo.py
```

Should show:
- 4 agents created
- 5 tasks completed
- 15+ A2A messages delivered
- 0 failures

### Test Dashboard Export

```bash
python examples/live_dashboard_demo.py
# Choose option 1
```

After completion, check for `dashboard_data.json`:
```bash
ls -lh dashboard_data.json
# Should exist with content
```

---

## 🔍 Exploring the Codebase

### Important Directories

```
multiAgentStandardsProtocol/
├── src/superstandard/
│   ├── agents/           # Production agents
│   ├── services/         # Data source services
│   ├── orchestration/    # Multi-agent orchestration
│   ├── nlp/              # Natural language processing
│   ├── a2a/              # A2A protocol implementation
│   ├── meta_agents/      # Factory & Coordinator
│   ├── monitoring/       # Dashboard state management
│   └── cli/              # Command-line interfaces
├── examples/             # Demo scripts
├── dashboard.html        # Real-time dashboard UI
└── docs/                 # Documentation
```

### Key Files to Explore

**Natural Language**:
- `src/superstandard/nlp/intent_parser.py` - Intent classification
- `src/superstandard/nlp/agent_mapper.py` - Intent-to-agent routing
- `src/superstandard/cli/chat.py` - Interactive chat interface

**A2A Protocol**:
- `src/superstandard/a2a/protocol.py` - A2A message format
- `src/superstandard/a2a/bus.py` - Message bus implementation
- `src/superstandard/meta_agents/factory.py` - Agent creation
- `src/superstandard/meta_agents/coordinator.py` - Workflow orchestration

**Dashboard**:
- `dashboard.html` - Frontend visualization
- `src/superstandard/monitoring/dashboard.py` - Event management
- `examples/live_dashboard_demo.py` - Demo script

**Agents**:
- `src/superstandard/agents/pcf/.../a_1_1_1_1_identify_competitors_PRODUCTION.py`
- `src/superstandard/agents/pcf/.../a_1_1_1_2_identify_economic_trends_PRODUCTION.py`
- `src/superstandard/agents/pcf/.../a_1_1_1_5_analyze_demographics_PRODUCTION.py`
- `src/superstandard/agents/pcf/.../a_1_1_2_1_conduct_research_PRODUCTION.py`

---

## 🚨 Troubleshooting

### Common Issues

#### Issue: "Module not found" errors

**Solution**: Install dependencies
```bash
pip install -r requirements.txt
# Or manually:
pip install aiohttp pyyaml
```

#### Issue: Natural language chat not understanding queries

**Solution 1**: Intent parser is in pattern mode (no API key)
- This is normal! Pattern mode works but with ~85% accuracy
- For 95%+ accuracy, add OpenAI API key

**Solution 2**: Query phrasing
- Try: "Find opportunities in healthcare"
- Instead of: "Can you help me find some opportunities?"

#### Issue: Dashboard shows "No data"

**Solution**: Run a demo first to generate data
```bash
python examples/live_dashboard_demo.py
# Then refresh dashboard
```

#### Issue: Agents return mock data

**This is normal!** System automatically falls back to mock data when:
- API keys not configured
- API calls fail
- Rate limits exceeded

To use real data, configure API keys (see [Configuration](#configuration))

#### Issue: Python version too old

```bash
python --version  # Should show 3.8+
```

If older, install Python 3.8+: https://www.python.org/downloads/

---

## 📚 Next Steps

### Learn More

1. **Read the Documentation**:
   - [Natural Language Interface](NATURAL_LANGUAGE_INTERFACE.md)
   - [A2A Protocol & Meta-Agents](A2A_PROTOCOL_META_AGENTS.md)
   - [Real-Time Dashboard](REAL_TIME_DASHBOARD.md)
   - [Autonomous Discovery](AUTONOMOUS_BUSINESS_OPPORTUNITY_DISCOVERY.md)

2. **Explore the Code**:
   - Start with `examples/` directory
   - Read agent implementations
   - Understand orchestration patterns

3. **Try Advanced Features**:
   - Add your own agents
   - Create custom workflows
   - Extend the natural language interface
   - Build integrations (Slack, Discord, etc.)

### Build Your First Feature

**Option 1: Add a New Intent**

See: [Adding Intents Guide](NATURAL_LANGUAGE_INTERFACE.md#advanced-usage)

**Option 2: Create a Custom Agent**

See: [Agent Development Guide](src/superstandard/agents/README.md)

**Option 3: Add a New Service**

See: [Service Integration Guide](src/superstandard/services/README.md)

---

## 💬 Get Help

- **Documentation**: Browse the docs in this repository
- **Examples**: Check `examples/` directory
- **Issues**: [GitHub Issues](https://github.com/sillinous/multiAgentStandardsProtocol/issues)
- **Discussions**: [GitHub Discussions](https://github.com/sillinous/multiAgentStandardsProtocol/discussions)

---

## 🎉 You're Ready!

You now have a working autonomous AI platform! Here's what you can do:

✅ **Talk to agents** in natural language
✅ **Watch autonomous coordination** via A2A protocol
✅ **Monitor everything** in real-time dashboard
✅ **Discover opportunities** autonomously
✅ **Extend the platform** with new agents/services

**Welcome to the future of autonomous AI!** 🚀

---

<p align="center">
  <strong>THE SYSTEM BUILDS ITSELF!</strong> 🤯
</p>

<p align="center">
  <a href="README.md">← Back to README</a> •
  <a href="ARCHITECTURE.md">Architecture Guide →</a>
</p>
