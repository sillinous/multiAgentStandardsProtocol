# Contributing to Agentic Forge

Thank you for your interest in contributing to the Agentic Forge! This document provides guidelines and instructions for contributing.

## 🌟 Ways to Contribute

- **Code**: Bug fixes, new features, optimizations
- **Documentation**: Improvements, tutorials, examples
- **Testing**: Writing tests, reporting bugs
- **Design**: UI/UX improvements, architecture proposals
- **Community**: Answering questions, helping others

## 🚀 Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/multiAgentStandardsProtocol.git
cd multiAgentStandardsProtocol
```

### 2. Set Up Development Environment

```bash
# Install Rust (if not already installed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install development tools
rustup component add rustfmt clippy

# Build the project
cargo build

# Run tests
cargo test --all
```

### 3. Create a Branch

```bash
# Create a feature branch
git checkout -b feature/your-feature-name

# Or a bugfix branch
git checkout -b fix/bug-description
```

## 📝 Development Workflow

### Before Making Changes

1. **Check existing issues** - See if someone is already working on it
2. **Create an issue** - Discuss major changes before implementing
3. **Read the architecture docs** - Understand the codebase structure

### Making Changes

1. **Write clean code** - Follow Rust conventions
2. **Add tests** - Cover new functionality
3. **Update docs** - Document public APIs
4. **Run checks** - Ensure code quality

```bash
# Format code
cargo fmt --all

# Run clippy for linting
cargo clippy --all -- -D warnings

# Run tests
cargo test --all

# Build in release mode
cargo build --release
```

### Commit Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples**:
```bash
git commit -m "feat(runtime): add OpenAI client support"
git commit -m "fix(api): handle null values in agent config"
git commit -m "docs(quickstart): update installation instructions"
```

### Opening a Pull Request

1. **Push your branch**
```bash
git push origin feature/your-feature-name
```

2. **Create Pull Request** on GitHub

3. **Fill out the PR template** with:
   - Description of changes
   - Related issues
   - Testing performed
   - Breaking changes (if any)

4. **Wait for review** - Address feedback promptly

## 🏗️ Project Structure

```
multiAgentStandardsProtocol/
├── crates/
│   ├── agentic_core/          # Core types and traits
│   ├── agentic_domain/         # Domain models
│   ├── agentic_learning/       # Learning system
│   ├── agentic_runtime/        # Execution runtime
│   ├── agentic_factory/        # Agent factory
│   ├── agentic_protocols/      # Protocol implementations
│   ├── agentic_standards/      # Standards tracking
│   ├── agentic_api/            # REST API
│   ├── agentic_cli/            # CLI tools
│   ├── agentic_coordination/   # Orchestration
│   └── agentic_observability/  # Telemetry
├── examples/                   # Example applications
├── docs/                       # Documentation
└── tests/                      # Integration tests
```

## 🧪 Testing

### Unit Tests

```bash
# Run all tests
cargo test --all

# Run specific crate tests
cargo test -p agentic_runtime

# Run with output
cargo test -- --nocapture
```

### Integration Tests

```bash
# Run integration tests
cargo test --test '*'
```

### Examples

```bash
# Test examples work
cargo run --example basic_agent
cargo run --example agent_learning
cargo run --example multi_agent_workflow
```

## 📚 Documentation

### Code Documentation

```rust
/// Brief description
///
/// Longer description with details.
///
/// # Examples
///
/// ```
/// use agentic_core::Agent;
///
/// let agent = Agent::new("MyAgent", "Description", ...);
/// ```
///
/// # Errors
///
/// Returns `Error::InvalidArgument` if...
pub fn my_function() -> Result<()> {
    // ...
}
```

### Generate Docs

```bash
# Generate and open documentation
cargo doc --open --no-deps
```

## 🎨 Code Style

### Rust Style Guide

We follow the official [Rust Style Guide](https://doc.rust-lang.org/style-guide/):

- Use `snake_case` for functions and variables
- Use `PascalCase` for types and traits
- Use `SCREAMING_SNAKE_CASE` for constants
- Maximum line length: 100 characters
- Use 4 spaces for indentation

### Code Organization

```rust
// 1. Module imports
use std::collections::HashMap;
use serde::{Serialize, Deserialize};

// 2. Type definitions
pub struct MyStruct {
    // Public fields first
    pub field1: String,
    // Then private fields
    field2: i32,
}

// 3. Implementation blocks
impl MyStruct {
    // Constructor/associated functions first
    pub fn new() -> Self { /* ... */ }

    // Then public methods
    pub fn public_method(&self) { /* ... */ }

    // Then private methods
    fn private_method(&self) { /* ... */ }
}

// 4. Trait implementations
impl SomeTrait for MyStruct {
    // ...
}

// 5. Tests
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_something() {
        // ...
    }
}
```

## 🐛 Reporting Bugs

### Before Reporting

1. **Check existing issues** - Avoid duplicates
2. **Update to latest** - Bug might be fixed
3. **Minimal reproduction** - Simplify the problem

### Bug Report Template

```markdown
**Describe the bug**
Clear description of the bug.

**To Reproduce**
Steps to reproduce:
1. Run command '...'
2. Call function '...'
3. See error

**Expected behavior**
What you expected to happen.

**Actual behavior**
What actually happened.

**Environment**
- OS: [e.g., Ubuntu 22.04]
- Rust version: [e.g., 1.75.0]
- Agentic Forge version: [e.g., 0.1.0]

**Additional context**
Logs, stack traces, etc.
```

## 💡 Feature Requests

### Feature Request Template

```markdown
**Is your feature request related to a problem?**
Clear description of the problem.

**Describe the solution you'd like**
What you want to happen.

**Describe alternatives you've considered**
Other solutions you've thought about.

**Additional context**
Mockups, examples, etc.
```

## 🏆 Recognition

Contributors are recognized in:
- **CONTRIBUTORS.md** - List of all contributors
- **Release notes** - Credited for their contributions
- **README.md** - Major contributors highlighted

## 📋 Checklist Before Submitting PR

- [ ] Code compiles without warnings
- [ ] All tests pass
- [ ] New tests added for new functionality
- [ ] Code formatted with `cargo fmt`
- [ ] No clippy warnings (`cargo clippy`)
- [ ] Documentation updated
- [ ] Examples updated (if relevant)
- [ ] Commit messages follow conventions
- [ ] PR description filled out
- [ ] Breaking changes noted

## 🤝 Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone.

### Our Standards

**Positive behavior**:
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community

**Unacceptable behavior**:
- Trolling, insulting, or derogatory comments
- Public or private harassment
- Publishing others' private information
- Other conduct inappropriate in a professional setting

### Enforcement

Instances of abusive behavior may be reported to the project team. All complaints will be reviewed and investigated promptly and fairly.

## 📞 Getting Help

- **Discord**: [Join our server](#) (coming soon)
- **GitHub Discussions**: [Ask questions](https://github.com/sillinous/multiAgentStandardsProtocol/discussions)
- **Email**: support@sillinous.com

## 📄 License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.

---

**Thank you for contributing to Agentic Forge! 🎉**
