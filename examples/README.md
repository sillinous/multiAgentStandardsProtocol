# SuperStandard v1.0 - Example Applications

This directory contains comprehensive example applications demonstrating the SuperStandard protocol suite.

## Table of Contents

- [Quick Start](#quick-start)
- [Examples Overview](#examples-overview)
- [Installation](#installation)
- [Running the Examples](#running-the-examples)
- [Example Details](#example-details)

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run COMPLETE PLATFORM DEMO (Recommended - Shows ALL features!)
python examples/complete_platform_demo.py

# Or run individual protocol examples:

# Run ANP (Agent Network Protocol) example
python examples/anp_discovery/agent_network_demo.py

# Run ACP (Agent Coordination Protocol) example
python examples/acp_coordination/multi_agent_pipeline.py

# Run BAP (Blockchain Agent Protocol) example
python examples/bap_marketplace/agent_marketplace_demo.py
```

---

## Examples Overview

| Example | Protocol/System | What It Demonstrates | Complexity |
|---------|-----------------|---------------------|------------|
| **🚀 Complete Platform Demo** | Agentic Forge | **Template deployment, analytics, backtesting, Pareto evolution** | **Beginner (RECOMMENDED)** |
| **Agent Network Discovery** | ANP v1.0 | Agent registration, capability-based discovery, health monitoring | Beginner |
| **Multi-Agent Pipeline** | ACP v1.0 | Coordination patterns, task management, shared state sync | Intermediate |
| **Agent Marketplace** | BAP v1.0 | Blockchain economy, NFTs, smart contracts, DAO governance | Advanced |

---

## Installation

### Prerequisites

- **Python 3.9+**
- **pip** (Python package manager)

### Install Dependencies

```bash
# Navigate to project root
cd multiAgentStandardsProtocol

# Install Python dependencies
pip install -r requirements.txt
```

---

## Running the Examples

### 0. 🚀 Complete Platform Demo (RECOMMENDED START HERE!)

**What you'll learn:**
- How to deploy pre-configured agent ensembles with one command
- How to view real-time analytics (4 interactive charts)
- How to run historical backtests with equity curves and trade logs
- How to run multi-objective Pareto evolution (NSGA-II algorithm)
- How to explore the Pareto frontier for optimal trade-offs
- **The COMPLETE power of the Agentic Forge platform!**

**Prerequisites:**
```bash
# Start the API server first (in a separate terminal)
cd src
python -m superstandard.api.server
```

**Run the demo:**
```bash
python examples/complete_platform_demo.py
```

**What happens:**
1. **Template Deployment** - Instantly creates "Balanced Trader" ensemble with 3 specialists
2. **Analytics Display** - Shows performance metrics, regime distribution, and specialist effectiveness
3. **Backtest Execution** - Runs 7-day historical validation with complete metrics
4. **Pareto Evolution** (optional) - Evolves 20 agents over 10 generations optimizing return vs risk
5. **Complete Summary** - Resource IDs and dashboard links for visual exploration

**Expected output:**
```
🚀 AGENTIC FORGE - COMPLETE PLATFORM DEMO 🚀

================================================================================
  STEP 1: Deploy Ensemble Template
================================================================================

✅ Template deployed successfully!
   Ensemble ID: abc-123-456-789
   Ensemble Name: Balanced Trader
   Specialists Added: 3

================================================================================
  STEP 3: Run Strategy Backtest
================================================================================

✅ Backtest completed!
   Total Return: 25.34%
   Win Rate: 62.50%
   Sharpe Ratio: 1.85
   Max Drawdown: -12.45%

🧬 Run Pareto Evolution? (takes ~1-2 min) [y/N]: y

================================================================================
  STEP 4: Run Multi-Objective Pareto Evolution
================================================================================

✅ Pareto evolution completed!
   Pareto Frontier Size: 12 agents
   Total Fronts: 5
```

**Duration:** 2-3 minutes (including optional Pareto evolution)

**Next Steps:**
- Open dashboard at `http://localhost:8080/dashboard`
- View analytics charts with real-time updates
- Explore backtest equity curve and trade log
- Analyze Pareto frontier scatter plot
- Compare frontier agents with different trade-offs

**Pro Tip:** This demo showcases features NO other multi-agent platform offers - research-grade NSGA-II optimization with zero-code visual interface!

---

### 1. Agent Network Discovery (ANP)

**What you'll learn:**
- How to create an agent network registry
- How to register agents with capabilities
- How to discover agents by capability, type, and region
- How to monitor agent health with heartbeats
- How to inspect network topology

**Run the example:**
```bash
python examples/anp_discovery/agent_network_demo.py
```

**Expected output:**
- 5 agents registered with various capabilities
- Capability-based discovery queries
- Type and region-based filtering
- Health status monitoring
- Network topology statistics

**Duration:** ~10 seconds

---

### 2. Multi-Agent Pipeline Coordination (ACP)

**What you'll learn:**
- How to create a coordination session
- How agents join a coordination
- How to create tasks with dependencies
- How to assign tasks to agents
- How to manage shared state across agents
- How to monitor coordination progress

**Run the example:**
```bash
python examples/acp_coordination/multi_agent_pipeline.py
```

**Expected output:**
- Pipeline coordination with 3 agents
- 3 tasks created and assigned
- Sequential task execution with dependencies
- Shared state updates
- Progress tracking and completion

**Duration:** ~15 seconds

---

### 3. Agent Marketplace (BAP)

**What you'll learn:**
- How to create agent wallets with multiple token types
- How to mint and trade capability NFTs
- How to stake reputation for collaborations
- How to create smart contracts with milestones
- How to process milestone payments
- How to propose and vote on DAO governance

**Run the example:**
```bash
python examples/bap_marketplace/agent_marketplace_demo.py
```

**Expected output:**
- 3 agent wallets with multi-token balances
- 3 capability NFTs minted
- Reputation staking demonstration
- Smart contract with 3 milestones
- 450 UTILITY tokens distributed
- DAO governance proposal and voting

**Duration:** ~20 seconds

---

## Example Details

### ANP: Agent Network Discovery

**File:** `examples/anp_discovery/agent_network_demo.py`

**Scenario:**
A distributed network of agents needs to discover each other based on capabilities and collaborate on tasks.

**Key Concepts:**
- **Agent Registry**: Central directory for agent discovery
- **Capability Indexing**: O(1) lookups for capability-based search
- **Health Monitoring**: Automatic offline detection with heartbeat timeout
- **Network Topology**: Real-time statistics on agent distribution

**Example Agents:**
1. **Data Collector** - Capabilities: api_fetch, web_scraping, data_extraction
2. **Data Analyzer** (×2) - Capabilities: data_analysis, reporting, machine_learning
3. **Report Generator** - Capabilities: reporting, pdf_generation, email_delivery
4. **Master Orchestrator** - Capabilities: task_coordination, workflow_management

**Code Highlights:**
```python
# Register an agent
registration = ANPRegistration(
    agent_id="data-analyzer-1",
    name="Analyzer Prime",
    agent_type="analyzer",
    capabilities=["data_analysis", "reporting"],
    endpoint="http://localhost:8002"
)
result = await registry.register_agent(registration)

# Discover agents by capability
query = DiscoveryQuery(capabilities=["data_analysis"])
agents = await registry.discover_agents(query)

# Send heartbeat
result = await registry.heartbeat(
    "data-analyzer-1",
    HealthStatus.HEALTHY,
    load_score=0.3
)
```

---

### ACP: Multi-Agent Pipeline Coordination

**File:** `examples/acp_coordination/multi_agent_pipeline.py`

**Scenario:**
Three specialized agents collaborate on a customer data processing pipeline: collection → analysis → reporting.

**Key Concepts:**
- **Coordination Patterns**: Pipeline execution with task dependencies
- **Task Management**: Create, assign, and track tasks
- **Shared State**: Synchronized state across all coordinating agents
- **Progress Monitoring**: Real-time coordination status

**Pipeline Stages:**
1. **Data Collection** - Fetch customer data from CRM API (data-collector-1)
2. **Data Analysis** - Analyze behavior patterns with ML (data-analyzer-1)
3. **Report Generation** - Generate executive summary PDF (report-generator-1)

**Code Highlights:**
```python
# Create coordination session
coordination = await manager.create_coordination(
    coordinator_id="supervisor-main",
    coordination_type="pipeline",
    goal="Process customer data pipeline"
)

# Create task with dependencies
task2 = await manager.create_task(
    coordination_id=coord_id,
    task_type="data_analysis",
    description="Analyze customer behavior patterns",
    dependencies=[task1['task_id']]  # Depends on Task 1
)

# Update shared state
await manager.update_shared_state(
    coordination_id=coord_id,
    agent_id="data-analyzer-1",
    updates={"analysis_complete": True, "insights_count": 25}
)
```

---

### BAP: Agent Marketplace & Blockchain Economy

**File:** `examples/bap_marketplace/agent_marketplace_demo.py`

**Scenario:**
A decentralized marketplace where agents trade capabilities, collaborate on contracts, and participate in DAO governance.

**Key Concepts:**
- **Multi-Token Economy**: 9 token types (Reputation, Utility, Governance, etc.)
- **Capability NFTs**: Tradable skill certificates with proficiency levels
- **Smart Contracts**: Milestone-based collaboration agreements
- **Reputation Staking**: Risk/reward mechanism for collaborations
- **DAO Governance**: Community proposals and weighted voting

**Marketplace Participants:**
1. **Data Provider** - NFT: API Integration (85% proficiency)
2. **AI Analyst** - NFT: Data Analysis (92% proficiency)
3. **Report Generator** - NFT: Report Generation (88% proficiency)

**Token Types Used:**
- **REPUTATION**: Trust score, stakeable for collaborations
- **UTILITY**: Payment currency for services
- **GOVERNANCE**: Voting power in DAO decisions
- **CAPABILITY**: NFT ownership representation
- **PERFORMANCE**: Quality metrics

**Smart Contract Flow:**
1. Contract created with 3 milestones
2. Milestone 1: Data delivery → 100 UTILITY to data-provider-1
3. Milestone 2: Analysis complete → 200 UTILITY to ai-analyst-1
4. Milestone 3: Report delivered → 150 UTILITY to report-gen-1
5. Reputation returned with bonus after successful completion

**Code Highlights:**
```python
# Mint capability NFT
nft = await bap.mint_capability_nft(
    agent_id="ai-analyst-1",
    capability_type="data_analysis",
    proficiency_level=0.92,
    metadata={"verified": True, "certifications": ["ML Engineer"]}
)

# Stake reputation for collaboration
wallet.reputation_staked += 50.0
wallet.token_balances[TokenType.REPUTATION] -= 50.0

# Create smart contract
contract = await bap.create_collaboration_contract(
    participants=["data-provider-1", "ai-analyst-1", "report-gen-1"],
    payment_schedule={
        "ai-analyst-1": {
            "amount": 200,
            "token_type": TokenType.UTILITY,
            "milestone": "analysis_complete"
        }
    }
)

# Create governance proposal
proposal = await bap.create_governance_proposal(
    proposer_id="ai-analyst-1",
    title="Increase minimum reputation requirement",
    voting_period_days=7
)

# Vote on proposal
vote = await bap.vote_on_proposal(
    proposal_id=proposal['proposal_id'],
    voter_id="ai-analyst-1",
    vote=VoteType.APPROVE,
    voting_power=100
)
```

---

## Next Steps

### Build Your Own

After running these examples, try:

1. **Extend ANP**: Add authentication, encryption, or load balancing
2. **Extend ACP**: Implement other coordination patterns (swarm, hierarchical, consensus)
3. **Extend BAP**: Add auction mechanisms, royalty systems, or cross-chain bridges

### Integration

Integrate SuperStandard protocols into your own projects:

```python
# In your agent application
from crates.agentic_protocols.python.anp_implementation import AgentNetworkRegistry
from crates.agentic_protocols.python.acp_implementation import CoordinationManager
from agents.consolidated.py.blockchain_agentic_protocol import BlockchainAgenticProtocol

# Initialize protocols
anp_registry = AgentNetworkRegistry()
acp_manager = CoordinationManager()
bap = BlockchainAgenticProtocol()

# Use protocols in your agent logic
# ...
```

---

## Troubleshooting

### ImportError: No module named 'crates'

**Solution**: Ensure you're running from the project root directory:
```bash
cd /path/to/multiAgentStandardsProtocol
python examples/anp_discovery/agent_network_demo.py
```

### ModuleNotFoundError for dataclasses or typing_extensions

**Solution**: Install requirements:
```bash
pip install -r requirements.txt
```

### Protocol Implementation Not Found

**Solution**: Verify file paths exist:
```bash
ls crates/agentic_protocols/python/anp_implementation.py
ls crates/agentic_protocols/python/acp_implementation.py
ls agents/consolidated/py/blockchain_agentic_protocol.py
```

---

## Additional Resources

- **Main README**: `../README.md` - Complete project overview
- **Contributing Guide**: `../CONTRIBUTING.md` - How to contribute
- **Protocol Roadmap**: `../agents/consolidated/docs/PROTOCOL_ROADMAP.md` - Future plans
- **API Documentation**: Run `python -m pydoc <module>` for detailed API docs

---

## Community

- **GitHub Issues**: Report bugs or request features
- **GitHub Discussions**: Ask questions and share ideas
- **Discord**: [Coming Soon] Join the community

---

**Built with SuperStandard v1.0 - THE industry standard for multi-agent systems**

*Let's change the world together!*
