# Quick Start Guide

Get up and running with the Agentic Forge multi-agent ecosystem in 5 minutes.

## Prerequisites

- Rust 1.70+ (install from https://rustup.rs/)
- Git
- 5+ GB free disk space

## Installation

```bash
# Clone the repository
git clone https://github.com/sillinous/multiAgentStandardsProtocol.git
cd multiAgentStandardsProtocol

# Build the project (first build takes ~2 minutes)
cargo build --release

# Run all tests
cargo test --all

# Generate documentation
cargo doc --open
```

## Project Structure

```
crates/
├── agentic_core/          # Types & traits (START HERE)
├── agentic_domain/        # Domain models (Agent Genome, Learning, etc.)
├── agentic_learning/      # Learning substrate
├── agentic_factory/       # Agent generation (Phase 2)
├── agentic_coordination/  # Orchestration (Phase 2)
├── agentic_protocols/     # A2A/MCP/ANS (Phase 2)
├── agentic_api/           # REST/WebSocket (Phase 3)
├── agentic_observability/ # OpenTelemetry (Phase 4)
├── agentic_standards/     # Standards tracking (Phase 4)
└── agentic_cli/           # CLI interface (Phase 3)
```

## Core Concepts

### 1. Agents
```rust
use agentic_core::agent::{Agent, AgentRole};

let mut agent = Agent::new(
    "DataAnalyzer",
    "Analyzes data",
    AgentRole::Worker,
    "claude-3-opus",
    "anthropic",
);
```

### 2. Agent Genome (Evolution)
```rust
use agentic_domain::agent_genome::{AgentGenome, Trait};

let mut genome = AgentGenome::new(agent.id, "data_analysis");
let trait_obj = Trait::new("reasoning_style", json!("analytical"));
genome.add_trait(trait_obj);
```

### 3. Learning Events
```rust
use agentic_learning::engine::LearningEngine;
use agentic_domain::learning::{LearningEvent, LearningType};

let event = LearningEvent::new(
    agent.id,
    LearningType::Success,
    "Found efficient pattern",
    "experimentation",
).with_confidence(0.95);
```

### 4. Knowledge Transfer
```rust
use agentic_learning::transfer::{KnowledgeTransfer, KnowledgeTransferManager};

let transfer = KnowledgeTransfer::new(agent1_id, agent2_id, learning_event);
let mut manager = KnowledgeTransferManager::new();
manager.record_transfer(transfer);
```

### 5. Workflows
```rust
use agentic_domain::workflow::{Workflow, Task};

let mut workflow = Workflow::new("DataPipeline", "Process data", "Extract insights");
workflow.add_task(Task::new("Extract", "Get data from source"));
workflow.add_task(Task::new("Transform", "Clean and transform"));
```

### 6. Experiments
```rust
use agentic_domain::experiment::Experiment;

let mut experiment = Experiment::new(
    agent.id,
    "mutation_test",
    "Test new reasoning approach",
    "Alternative strategy",
);
experiment.approve("system");
experiment.start();
```

### 7. Orchestration
```rust
use agentic_domain::orchestration::OrchestrationConfig;

// Supervisor pattern
let config = OrchestrationConfig::supervisor(workflow_id, supervisor_agent);

// Swarm pattern
let config = OrchestrationConfig::swarm(workflow_id, vec![agent1, agent2]);

// Emergent pattern
let config = OrchestrationConfig::emergent(workflow_id);
```

## Common Tasks

### Run Tests for a Specific Crate
```bash
cargo test -p agentic_core
cargo test -p agentic_domain
cargo test -p agentic_learning
```

### View Documentation
```bash
# Open docs in browser
cargo doc --open

# View specific crate docs
cargo doc -p agentic_core --open
cargo doc -p agentic_domain --open
```

### Build Release Binary
```bash
cargo build --release
ls target/release/
```

### Check Code Quality
```bash
cargo fmt --check
cargo clippy --all-targets --all-features
```

### Run Specific Test
```bash
cargo test --lib agentic_domain::agent_genome::tests::test_genome_creation
```

## Example: Create an Agent and Record Learning

```rust
use agentic_core::agent::{Agent, AgentRole};
use agentic_domain::agent_genome::AgentGenome;
use agentic_learning::engine::LearningEngine;
use agentic_domain::learning::{LearningEvent, LearningType};

fn main() {
    // 1. Create an agent
    let agent = Agent::new(
        "Analyst",
        "Data analysis agent",
        AgentRole::Worker,
        "claude-3-opus",
        "anthropic",
    );
    println!("Created agent: {}", agent.name);

    // 2. Create its genome
    let mut genome = AgentGenome::new(agent.id, "analysis");
    println!("Created genome version: {}", genome.version.version);

    // 3. Create learning engine
    let mut engine = LearningEngine::new();

    // 4. Record a learning event
    let event = LearningEvent::new(
        agent.id,
        LearningType::Success,
        "Discovered pattern in time-series data",
        "experimentation",
    ).with_confidence(0.92);

    engine.process_event(event).unwrap();
    println!("Learning events processed: {}", engine.total_events_processed);
    println!("Success rate: {:.1}%", engine.success_rate * 100.0);
}
```

## Troubleshooting

### Compilation Errors
```bash
# Update Rust
rustup update

# Clean and rebuild
cargo clean
cargo build
```

### Test Failures
```bash
# Run with verbose output
cargo test --all -- --nocapture

# Run specific test with backtrace
RUST_BACKTRACE=1 cargo test --lib agentic_core::identity::tests
```

### Performance Issues
```bash
# Build with optimizations
cargo build --release

# Run release tests
cargo test --release
```

## Next Steps

1. **Explore the Code**: Start with `agentic_core/src/lib.rs`
2. **Read Documentation**: View comprehensive README.md
3. **Run Examples**: See `PHASE1_SUMMARY.md` for code examples
4. **Join Development**: Check CONTRIBUTING.md for contribution guidelines
5. **Follow Roadmap**: Phase 2 begins with protocol integration

## Phase Progression

- **Phase 1 ✅**: Foundation (Agent Genome, Learning, Experiments)
- **Phase 2 🔄**: Protocol Integration (A2A, MCP, ANS)
- **Phase 3 📋**: Front-End (REST API, WebSocket, Dashboard)
- **Phase 4 📋**: Observability (OpenTelemetry, Tracing)
- **Phase 5 📋**: Advanced Features (Reflection, Marketplace)

## Resources

- **Full Documentation**: README.md (1100+ lines)
- **Phase 1 Summary**: PHASE1_SUMMARY.md
- **Code Examples**: Each module has unit tests as examples
- **Cargo Docs**: `cargo doc --open`

## Support

- **Issues**: GitHub Issues for bugs and feature requests
- **Discussions**: GitHub Discussions for questions
- **Documentation**: Inline code comments and external docs

## License

Apache License 2.0 - See LICENSE file

---

**Happy coding!** 🚀 Welcome to the future of autonomous multi-agent systems.
