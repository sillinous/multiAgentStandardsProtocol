//! Requirements and specifications for meta-agent operations

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Specification for an agent to be created
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentRequirement {
    /// Purpose of the agent
    pub purpose: String,

    /// Required capabilities
    pub capabilities: Vec<String>,

    /// Performance constraints
    pub constraints: Vec<String>,

    /// Preferred model
    pub preferred_model: Option<String>,

    /// Expected workload
    pub expected_workload: Option<WorkloadSpec>,

    /// Quality requirements
    pub quality_requirements: QualityRequirements,
}

/// Workload specification
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkloadSpec {
    /// Tasks per day
    pub tasks_per_day: u32,

    /// Average task complexity (1-10)
    pub avg_complexity: u8,

    /// Peak concurrency needed
    pub peak_concurrency: u32,
}

/// Quality requirements
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QualityRequirements {
    /// Minimum success rate (0.0 - 1.0)
    pub min_success_rate: f64,

    /// Maximum response time in ms
    pub max_response_time_ms: u64,

    /// Maximum cost per task
    pub max_cost_per_task: Option<f64>,

    /// Accuracy requirements
    pub min_accuracy: Option<f64>,
}

impl Default for QualityRequirements {
    fn default() -> Self {
        Self {
            min_success_rate: 0.9,
            max_response_time_ms: 30000,
            max_cost_per_task: Some(1.0),
            min_accuracy: Some(0.95),
        }
    }
}

/// Feature request for SDLC workflow
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FeatureRequest {
    /// Feature description
    pub description: String,

    /// Priority level
    pub priority: Priority,

    /// Optional deadline
    pub deadline: Option<chrono::DateTime<chrono::Utc>>,

    /// Acceptance criteria
    pub acceptance_criteria: Vec<String>,

    /// Related features or dependencies
    pub dependencies: Vec<String>,

    /// Target users
    pub target_users: Vec<String>,

    /// Additional context
    pub context: HashMap<String, String>,
}

/// Priority levels
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Priority {
    Low,
    Medium,
    High,
    Critical,
}

/// Capability specification
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CapabilitySpec {
    /// Name of the capability
    pub name: String,

    /// Description
    pub description: String,

    /// Input schema
    pub input_schema: serde_json::Value,

    /// Output schema
    pub output_schema: serde_json::Value,

    /// Example usage
    pub examples: Vec<CapabilityExample>,

    /// Required sub-capabilities
    pub requires: Vec<String>,
}

/// Example of capability usage
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CapabilityExample {
    pub name: String,
    pub input: serde_json::Value,
    pub expected_output: serde_json::Value,
    pub description: String,
}

/// Bug report for autonomous fixing
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BugReport {
    /// Bug description
    pub description: String,

    /// Steps to reproduce
    pub reproduction_steps: Vec<String>,

    /// Severity level
    pub severity: Severity,

    /// Affected components
    pub affected_components: Vec<String>,

    /// Error messages
    pub error_messages: Vec<String>,

    /// Expected behavior
    pub expected_behavior: String,

    /// Actual behavior
    pub actual_behavior: String,
}

/// Severity levels
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Severity {
    Low,
    Medium,
    High,
    Critical,
}

/// Task breakdown for complex operations
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TaskBreakdown {
    /// Main task description
    pub main_task: String,

    /// Sub-tasks required
    pub sub_tasks: Vec<SubTask>,

    /// Dependencies between tasks
    pub dependencies: HashMap<String, Vec<String>>,

    /// Estimated total time
    pub estimated_duration_minutes: u32,
}

/// A sub-task in a breakdown
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SubTask {
    pub id: String,
    pub description: String,
    pub assigned_agent_type: Option<String>,
    pub estimated_duration_minutes: u32,
    pub priority: Priority,
}

impl AgentRequirement {
    /// Create a simple agent requirement
    pub fn simple(purpose: impl Into<String>, capabilities: Vec<String>) -> Self {
        Self {
            purpose: purpose.into(),
            capabilities,
            constraints: Vec::new(),
            preferred_model: None,
            expected_workload: None,
            quality_requirements: QualityRequirements::default(),
        }
    }

    /// Add a constraint
    pub fn with_constraint(mut self, constraint: impl Into<String>) -> Self {
        self.constraints.push(constraint.into());
        self
    }

    /// Set preferred model
    pub fn with_model(mut self, model: impl Into<String>) -> Self {
        self.preferred_model = Some(model.into());
        self
    }

    /// Set quality requirements
    pub fn with_quality(mut self, quality: QualityRequirements) -> Self {
        self.quality_requirements = quality;
        self
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_agent_requirement_builder() {
        let req = AgentRequirement::simple(
            "Analyze financial data",
            vec!["data_analysis".to_string(), "reporting".to_string()],
        )
        .with_constraint("max_cost_per_run: $0.50")
        .with_model("claude-3-5-sonnet-20241022");

        assert_eq!(req.purpose, "Analyze financial data");
        assert_eq!(req.capabilities.len(), 2);
        assert_eq!(req.constraints.len(), 1);
        assert_eq!(req.preferred_model, Some("claude-3-5-sonnet-20241022".to_string()));
    }

    #[test]
    fn test_quality_requirements_defaults() {
        let quality = QualityRequirements::default();

        assert_eq!(quality.min_success_rate, 0.9);
        assert_eq!(quality.max_response_time_ms, 30000);
        assert_eq!(quality.max_cost_per_task, Some(1.0));
    }
}
