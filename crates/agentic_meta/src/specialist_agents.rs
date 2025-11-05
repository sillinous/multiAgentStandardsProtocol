//! Specialist Agents - Domain-specific expert agents

use agentic_core::{Agent, AgentRole};

/// Type of specialist agent
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SpecialistType {
    /// Writes test code
    TestWriter,

    /// Generates documentation
    DocumentationWriter,

    /// Reviews code
    CodeReviewer,

    /// Debugs issues
    Debugger,

    /// Monitors performance
    PerformanceMonitor,

    /// Refactors code
    Refactorer,

    /// Deploys applications
    Deployer,
}

/// Specialist agent factory
pub struct SpecialistAgentFactory;

impl SpecialistAgentFactory {
    /// Create a specialist agent
    pub fn create(specialist_type: SpecialistType) -> Agent {
        let (name, description) = match specialist_type {
            SpecialistType::TestWriter => (
                "TestWriter",
                "Writes comprehensive unit and integration tests",
            ),
            SpecialistType::DocumentationWriter => (
                "DocWriter",
                "Generates clear and comprehensive documentation",
            ),
            SpecialistType::CodeReviewer => (
                "CodeReviewer",
                "Reviews code for quality, security, and best practices",
            ),
            SpecialistType::Debugger => (
                "Debugger",
                "Analyzes and fixes bugs",
            ),
            SpecialistType::PerformanceMonitor => (
                "PerfMonitor",
                "Monitors and optimizes performance",
            ),
            SpecialistType::Refactorer => (
                "Refactorer",
                "Refactors code for better quality and maintainability",
            ),
            SpecialistType::Deployer => (
                "Deployer",
                "Handles deployment and infrastructure",
            ),
        };

        let mut agent = Agent::new(
            name,
            description,
            AgentRole::Worker,
            "claude-3-5-sonnet-20241022",
            "anthropic",
        );

        agent.add_tag("specialist");
        agent.add_tag(&format!("{:?}", specialist_type).to_lowercase());

        agent
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_create_specialists() {
        let test_writer = SpecialistAgentFactory::create(SpecialistType::TestWriter);
        assert_eq!(test_writer.name, "TestWriter");

        let reviewer = SpecialistAgentFactory::create(SpecialistType::CodeReviewer);
        assert_eq!(reviewer.name, "CodeReviewer");
    }
}
