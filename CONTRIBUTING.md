# Contributing to SuperStandard

Thank you for your interest in contributing to SuperStandard! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)
- [Documentation Standards](#documentation-standards)
- [Pull Request Process](#pull-request-process)
- [Community](#community)

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors, regardless of experience level, background, or identity.

### Our Standards

**Positive behaviors:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Unacceptable behaviors:**
- Harassment, trolling, or discriminatory comments
- Personal attacks or inflammatory comments
- Publishing others' private information without permission
- Other conduct that could reasonably be considered inappropriate

---

## Getting Started

### Prerequisites

- **Rust 1.70+** (for Rust components): Install from https://rustup.rs/
- **Python 3.9+** (for protocol implementations): Install from https://python.org/
- **Git**: For version control
- **GitHub Account**: For submitting pull requests

### Fork and Clone

1. **Fork the repository** on GitHub
2. **Clone your fork locally**:

```bash
git clone https://github.com/YOUR_USERNAME/multiAgentStandardsProtocol.git
cd multiAgentStandardsProtocol
```

3. **Add upstream remote**:

```bash
git remote add upstream https://github.com/sillinous/multiAgentStandardsProtocol.git
```

4. **Install dependencies**:

```bash
# Python dependencies
pip install -r requirements.txt

# Rust dependencies (automatic via Cargo)
cargo build
```

---

## How to Contribute

### Types of Contributions

We welcome many types of contributions:

1. **Bug Reports**: Report issues you've encountered
2. **Feature Requests**: Propose new features or protocols
3. **Code Contributions**: Implement new features or fix bugs
4. **Documentation**: Improve docs, add examples, write tutorials
5. **Testing**: Add test coverage, improve test quality
6. **Protocol Specifications**: Design new protocols or improve existing ones
7. **Performance Improvements**: Optimize implementations
8. **Language Ports**: Implement protocols in other languages (Go, TypeScript, Java)

### Contribution Priority Areas

**High Priority:**
- Example applications showcasing protocol usage
- Integration guides for popular frameworks
- Test coverage expansion
- Performance benchmarks
- Security audits and improvements

**Phase 2 Protocols** (future contributions):
- SIP (Security & Identity Protocol) - CRITICAL
- DMP (Data Management Protocol)
- ALMP (Agent Lifecycle Management Protocol)
- See [PROTOCOL_ROADMAP.md](agents/consolidated/docs/PROTOCOL_ROADMAP.md) for full list

---

## Development Workflow

### 1. Create a Feature Branch

```bash
# Update your local main branch
git checkout main
git pull upstream main

# Create a feature branch
git checkout -b feature/your-feature-name
```

**Branch naming conventions:**
- `feature/` - New features (e.g., `feature/add-typescript-anp`)
- `fix/` - Bug fixes (e.g., `fix/anp-discovery-bug`)
- `docs/` - Documentation updates (e.g., `docs/improve-quickstart`)
- `test/` - Test additions (e.g., `test/add-acp-integration-tests`)
- `perf/` - Performance improvements (e.g., `perf/optimize-discovery`)

### 2. Make Your Changes

Follow the [Coding Standards](#coding-standards) and [Testing Requirements](#testing-requirements) sections below.

### 3. Commit Your Changes

```bash
git add .
git commit -m "Brief description of your changes

Longer description if needed:
- Bullet point 1
- Bullet point 2

Fixes #123 (if applicable)"
```

**Commit message guidelines:**
- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- Keep first line under 50 characters
- Reference issues and PRs when applicable
- Include "Breaking Change:" if the commit introduces breaking changes

### 4. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then open a Pull Request on GitHub.

---

## Coding Standards

### Rust Code

Follow standard Rust conventions:

```bash
# Use rustfmt for formatting
cargo fmt

# Check for common mistakes
cargo clippy

# Ensure code compiles
cargo build --all

# Run tests
cargo test --all
```

**Rust guidelines:**
- Follow the [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/)
- Use meaningful variable and function names
- Add rustdoc comments for public APIs
- Use `Result<T, E>` for error handling
- Prefer `impl Trait` over generic type parameters when appropriate
- Use `#[derive(...)]` for common traits when possible

### Python Code

Follow PEP 8 and modern Python best practices:

```bash
# Format code with black
black crates/agentic_protocols/python/

# Type checking with mypy
mypy crates/agentic_protocols/python/

# Linting with pylint
pylint crates/agentic_protocols/python/
```

**Python guidelines:**
- Follow [PEP 8](https://peps.python.org/pep-0008/)
- Use type hints for function signatures
- Use dataclasses for data structures
- Prefer async/await for I/O operations
- Use descriptive variable names
- Add docstrings for all public functions/classes

**Example Python function:**

```python
async def register_agent(
    self,
    registration: ANPRegistration
) -> Dict[str, Any]:
    """
    Register an agent in the network registry.

    Args:
        registration: Agent registration information

    Returns:
        Dict containing registration result with agent_id and status

    Raises:
        ValueError: If registration data is invalid
    """
    # Implementation here
    pass
```

### Documentation

- Use Markdown for documentation files
- Include code examples for all protocols
- Keep examples simple and self-contained
- Test all code examples to ensure they work

---

## Testing Requirements

### Minimum Test Coverage

All contributions with code changes **must** include tests:

- **New features**: Unit tests + integration tests
- **Bug fixes**: Regression test demonstrating the fix
- **Protocol implementations**: Full protocol test suite

### Running Tests

**Rust tests:**
```bash
# Run all Rust tests
cargo test --all

# Run specific crate tests
cargo test -p agentic_domain
cargo test -p agentic_learning

# Run tests with output
cargo test -- --nocapture
```

**Python tests:**
```bash
# Run protocol implementation tests
python crates/agentic_protocols/python/anp_implementation.py
python crates/agentic_protocols/python/acp_implementation.py

# Run with pytest (if configured)
pytest tests/
```

### Writing Good Tests

**Test structure:**
```python
async def test_agent_registration():
    """Test that agents can register successfully."""
    # Arrange - Set up test data
    registry = AgentNetworkRegistry()
    registration = ANPRegistration(
        agent_id="test-agent",
        name="TestAgent",
        agent_type="worker",
        capabilities=["testing"]
    )

    # Act - Perform the action
    result = await registry.register_agent(registration)

    # Assert - Verify expectations
    assert result["status"] == "registered"
    assert result["agent_id"] == "test-agent"
```

**Test naming:**
- Use descriptive names: `test_discovery_finds_agents_by_capability`
- Follow pattern: `test_<what>_<condition>_<expected_result>`

---

## Documentation Standards

### Protocol Documentation

When adding or modifying a protocol:

1. **Update README.md** with protocol overview
2. **Create protocol specification** in `agents/consolidated/docs/`
3. **Add usage examples** in README and protocol docs
4. **Document all APIs** with docstrings/rustdoc
5. **Include diagrams** for complex interactions (use Mermaid or ASCII art)

### Code Documentation

**Rust:**
```rust
/// Registers an agent in the network.
///
/// # Arguments
///
/// * `registration` - Agent registration information
///
/// # Returns
///
/// Returns a Result containing the registration status
///
/// # Examples
///
/// ```
/// let registration = ANPRegistration::new("agent-1", "Worker");
/// let result = registry.register_agent(registration).await?;
/// ```
pub async fn register_agent(&mut self, registration: ANPRegistration) -> Result<Status> {
    // Implementation
}
```

**Python:**
```python
async def register_agent(self, registration: ANPRegistration) -> Dict[str, Any]:
    """
    Register an agent in the network.

    Args:
        registration: Agent registration information including id, name,
                     type, capabilities, and endpoint

    Returns:
        Dictionary containing:
            - agent_id: The registered agent's ID
            - status: Registration status ("registered")
            - registry_size: Current number of registered agents

    Example:
        >>> registry = AgentNetworkRegistry()
        >>> registration = ANPRegistration(
        ...     agent_id="agent-1",
        ...     name="Worker",
        ...     agent_type="worker",
        ...     capabilities=["data_analysis"]
        ... )
        >>> result = await registry.register_agent(registration)
        >>> print(result["status"])
        registered
    """
```

---

## Pull Request Process

### Before Submitting

**Checklist:**
- [ ] Code follows project style guidelines
- [ ] All tests pass locally
- [ ] New tests added for new functionality
- [ ] Documentation updated (README, docstrings, etc.)
- [ ] Commit messages are clear and descriptive
- [ ] No merge conflicts with main branch
- [ ] Code has been formatted (rustfmt, black)
- [ ] No linter warnings (clippy, pylint)

### PR Description Template

```markdown
## Description
Brief description of the changes

## Type of Change
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing functionality to change)
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Test coverage improvement

## Testing
Describe the tests you ran and how to reproduce them

## Related Issues
Fixes #123
Related to #456

## Additional Context
Any additional information, screenshots, or context
```

### Review Process

1. **Automated Checks**: CI/CD runs tests and linters
2. **Code Review**: Maintainers review your code
3. **Feedback**: Address any requested changes
4. **Approval**: Once approved, your PR will be merged

**Review timeline:**
- Small PRs (< 100 lines): 1-3 days
- Medium PRs (100-500 lines): 3-7 days
- Large PRs (> 500 lines): 1-2 weeks

**Tips for faster reviews:**
- Keep PRs focused and small
- Respond to feedback promptly
- Be open to suggestions
- Test thoroughly before submitting

---

## Community

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions, ideas, and general discussion
- **Discord**: [Coming Soon] Real-time chat and collaboration
- **Email**: contact@sillinous.com (for sensitive issues)

### Getting Help

**Before asking for help:**
1. Check the [README.md](README.md)
2. Search existing [GitHub Issues](https://github.com/sillinous/multiAgentStandardsProtocol/issues)
3. Review the [documentation](agents/consolidated/docs/)

**When asking for help:**
- Be specific about your problem
- Include error messages and stack traces
- Describe what you've already tried
- Provide a minimal reproducible example

### Recognition

Contributors are recognized in:
- GitHub Contributors page
- Release notes for significant contributions
- Project documentation for major features

---

## Protocol Contribution Process

### Proposing New Protocols

For Phase 2+ protocols or new protocol ideas:

1. **Create an Issue**: Describe the protocol and its purpose
2. **Discussion**: Community discusses the proposal
3. **RFC (Request for Comments)**: Write detailed specification
4. **Approval**: Maintainers review and approve
5. **Implementation**: Implement according to spec
6. **Testing**: Comprehensive test coverage
7. **Documentation**: Complete usage guides
8. **Review**: Final review before merge

**Protocol specification template:**

```markdown
# Protocol Name (Acronym)

## Overview
Brief description of what the protocol does

## Motivation
Why is this protocol needed?

## Specification

### Data Structures
Define all data structures used by the protocol

### Operations
Define all operations/methods

### Message Formats
Define message formats if applicable

### Error Handling
How errors are handled

## Implementation Notes
Guidelines for implementing the protocol

## Security Considerations
Security implications and requirements

## Examples
Usage examples and common patterns
```

---

## License

By contributing to SuperStandard, you agree that your contributions will be licensed under the Apache License 2.0.

---

## Questions?

If you have questions about contributing, please:
- Open a [GitHub Discussion](https://github.com/sillinous/multiAgentStandardsProtocol/discussions)
- Check existing issues and discussions
- Reach out to maintainers

---

**Thank you for contributing to SuperStandard!**

Together, we're building THE industry standard for multi-agent systems.

---

**Last Updated**: 2025-11-05
