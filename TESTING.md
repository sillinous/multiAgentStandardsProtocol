# 🧪 Testing Guide

Comprehensive testing guide for the Agentic Forge.

## Table of Contents

- [Overview](#overview)
- [Running Tests](#running-tests)
- [Test Categories](#test-categories)
- [Writing Tests](#writing-tests)
- [CI/CD Testing](#cicd-testing)
- [Manual Testing](#manual-testing)

---

## Overview

The Agentic Forge has multiple levels of testing:

1. **Unit Tests** - Test individual components
2. **Integration Tests** - Test component interactions
3. **Example Tests** - Verify examples compile and run
4. **API Tests** - Test HTTP endpoints
5. **End-to-End Tests** - Full system testing

---

## Running Tests

### Run All Tests

```bash
cargo test --all
```

### Run Specific Test Suite

```bash
# Unit tests only
cargo test --lib

# Integration tests only
cargo test --test '*'

# Specific crate tests
cargo test -p agentic_runtime
cargo test -p agentic_core
cargo test -p agentic_learning

# Doc tests
cargo test --doc
```

### Run With Output

```bash
# Show println! output
cargo test -- --nocapture

# Show test names
cargo test -- --show-output

# Run specific test
cargo test test_agent_creation -- --exact
```

### Run Examples

```bash
# Verify examples compile
cargo build --examples

# Run specific example
cargo run --example basic_agent
cargo run --example agent_learning
cargo run --example multi_agent_workflow
```

---

## Test Categories

### 1. Unit Tests

Located in each crate's source files:

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_something() {
        // Test code
    }
}
```

**Example crates with unit tests**:
- `agentic_core/src/agent.rs` - Agent creation and metrics
- `agentic_domain/src/agent_genome.rs` - Genome mutations
- `agentic_runtime/src/scheduler.rs` - Task scheduling

### 2. Integration Tests

Located in `tests/` directory:

```bash
tests/
├── integration_test.rs    # Core integration tests
└── api_integration_test.rs # API integration tests
```

**Run integration tests**:
```bash
cargo test --test integration_test
```

### 3. Doc Tests

Tests in documentation:

```rust
/// Example usage:
/// ```
/// use agentic_core::Agent;
/// let agent = Agent::new(...);
/// ```
```

**Run doc tests**:
```bash
cargo test --doc
```

---

## Writing Tests

### Unit Test Template

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_feature_name() {
        // Arrange
        let input = setup_test_data();

        // Act
        let result = function_under_test(input);

        // Assert
        assert_eq!(result, expected_value);
        assert!(result.is_ok());
    }
}
```

### Async Test Template

```rust
#[tokio::test]
async fn test_async_feature() {
    // Setup
    let client = create_test_client();

    // Execute
    let result = client.async_operation().await;

    // Verify
    assert!(result.is_ok());
}
```

### Integration Test Template

```rust
// tests/my_integration_test.rs

use agentic_core::Agent;
use agentic_runtime::executor::DefaultExecutor;

#[tokio::test]
async fn test_end_to_end_flow() {
    // Setup multiple components
    let agent = create_agent();
    let executor = create_executor();

    // Test interaction
    let result = executor.execute(&agent, "input").await;

    // Verify
    assert!(result.is_ok());
}
```

---

## CI/CD Testing

### GitHub Actions

Tests run automatically on:
- Push to `main` or `develop`
- Pull requests
- Tag creation (releases)

**CI Pipeline includes**:
1. Build on multiple platforms (Linux, Windows, macOS)
2. Run all tests
3. Check formatting (`cargo fmt`)
4. Run clippy linting
5. Build examples
6. Security audit
7. Code coverage

### Local CI Simulation

```bash
# Run the same checks as CI
./scripts/ci-check.sh

# Or manually:
cargo fmt --all -- --check
cargo clippy --all -- -D warnings
cargo test --all
cargo build --examples
```

---

## Manual Testing

### 1. Test Agent Creation

```bash
cargo run --example basic_agent
```

**Expected output**:
```
🤖 Agentic Ecosystem - Basic Agent Example
...
✓ Created agent: DataAnalyzer (ID: agent_...)
✓ Executor ready
📊 Execution Results
   Success: ✓ Yes
   ...
✅ Example completed successfully!
```

### 2. Test API Server

```bash
# Terminal 1: Start server
cargo run -p agentic_api

# Terminal 2: Test endpoints
curl http://localhost:8080/api/health
curl http://localhost:8080/api/agents
```

### 3. Test With Real LLM

```bash
# Set API key
export ANTHROPIC_API_KEY="your-key"

# Run example
cargo run --example basic_agent

# Should use real Claude API
```

### 4. Test Docker Build

```bash
# Build image
docker build -t agentic-forge:test .

# Run container
docker run -p 8080:8080 agentic-forge:test

# Test
curl http://localhost:8080/api/health
```

---

## Test Coverage

### Generate Coverage Report

```bash
# Install tarpaulin
cargo install cargo-tarpaulin

# Generate coverage
cargo tarpaulin --out Html --output-dir coverage

# Open report
open coverage/index.html
```

### Current Coverage Status

| Crate | Coverage | Status |
|-------|----------|--------|
| agentic_core | ~80% | ✅ Good |
| agentic_domain | ~75% | ✅ Good |
| agentic_runtime | ~70% | ✅ Good |
| agentic_learning | ~75% | ✅ Good |
| agentic_api | ~40% | 🟡 Needs improvement |

---

## Test Data

### Mock LLM Responses

```rust
use agentic_runtime::llm::MockLlmClient;

let mock = MockLlmClient::new("Test response");
// Mock will always return "Test response"
```

### Test Agents

```rust
let agent = Agent::new(
    "TestAgent",
    "For testing only",
    AgentRole::Worker,
    "mock-model",
    "mock",
);
```

### Test Fixtures

Located in `tests/fixtures/` (if created):
- Sample agent configurations
- Test workflows
- Learning event data

---

## Debugging Tests

### Enable Logging

```bash
# Set log level
RUST_LOG=debug cargo test -- --nocapture

# Specific module
RUST_LOG=agentic_runtime=trace cargo test
```

### Debug Specific Test

```bash
# Run with debugger
rust-lldb target/debug/deps/integration_test-<hash>
# or
rust-gdb target/debug/deps/integration_test-<hash>

# Set breakpoint and run
(lldb) breakpoint set --name test_agent_creation
(lldb) run
```

### Common Issues

**Problem**: Tests fail with "connection refused"
```bash
# Solution: Start the API server first
cargo run -p agentic_api &
cargo test --test api_integration_test
```

**Problem**: Async tests hang
```bash
# Solution: Increase timeout or check for deadlocks
RUST_TEST_TIME_UNIT=60000 cargo test
```

**Problem**: Flaky tests
```bash
# Solution: Run multiple times
for i in {1..10}; do cargo test || break; done
```

---

## Performance Testing

### Benchmark Tests

```bash
# Install criterion (if using benchmarks)
cargo install cargo-criterion

# Run benchmarks
cargo criterion
```

### Load Testing

```bash
# Use Apache Bench
ab -n 1000 -c 10 http://localhost:8080/api/health

# Use wrk
wrk -t4 -c100 -d30s http://localhost:8080/api/agents
```

---

## Test Checklist

Before submitting PR:

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Examples compile and run
- [ ] No clippy warnings
- [ ] Code is formatted
- [ ] New features have tests
- [ ] Documentation is updated
- [ ] No failing CI checks

---

## Resources

- **Rust Testing Book**: https://doc.rust-lang.org/book/ch11-00-testing.html
- **Tokio Testing**: https://tokio.rs/tokio/topics/testing
- **Axum Testing**: https://docs.rs/axum/latest/axum/testing/index.html

---

**Happy Testing! 🧪**

*Quality code starts with quality tests*
