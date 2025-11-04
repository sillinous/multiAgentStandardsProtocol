//! Autonomous experimentation framework
//!
//! Allows agents to safely propose and run experiments to test hypotheses
//! and discover new behaviors in a sandboxed environment.

use agentic_core::identity::AgentId;
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use serde_json::Value;

/// Status of an experiment
#[derive(Clone, Debug, Eq, PartialEq, Serialize, Deserialize)]
pub enum ExperimentStatus {
    /// Proposed but not yet approved
    Proposed,

    /// Approved and ready to run
    Approved,

    /// Currently executing
    Running,

    /// Successfully completed
    Completed,

    /// Failed during execution
    Failed(String),

    /// Rolled back (results discarded)
    RolledBack,

    /// Cancelled by user/system
    Cancelled,
}

impl std::fmt::Display for ExperimentStatus {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ExperimentStatus::Proposed => write!(f, "proposed"),
            ExperimentStatus::Approved => write!(f, "approved"),
            ExperimentStatus::Running => write!(f, "running"),
            ExperimentStatus::Completed => write!(f, "completed"),
            ExperimentStatus::Failed(msg) => write!(f, "failed: {}", msg),
            ExperimentStatus::RolledBack => write!(f, "rolled_back"),
            ExperimentStatus::Cancelled => write!(f, "cancelled"),
        }
    }
}

/// Result of an experiment
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ExperimentResult {
    /// Whether the hypothesis was confirmed
    pub hypothesis_confirmed: bool,

    /// Fitness improvement from this experiment
    pub fitness_delta: f64,

    /// Detailed findings
    pub findings: String,

    /// Structured results
    pub data: Option<Value>,

    /// Execution time in seconds
    pub execution_time_secs: f64,

    /// Resource usage (CPU, memory, tokens, etc.)
    pub resource_usage: Option<Value>,

    /// Success rate of the experiment (0.0 to 1.0)
    pub success_rate: f64,

    /// Whether this result should be applied to the agent
    pub should_apply: bool,
}

impl ExperimentResult {
    /// Create a new experiment result
    pub fn new() -> Self {
        Self {
            hypothesis_confirmed: false,
            fitness_delta: 0.0,
            findings: String::new(),
            data: None,
            execution_time_secs: 0.0,
            resource_usage: None,
            success_rate: 0.0,
            should_apply: false,
        }
    }

    /// Mark hypothesis as confirmed
    pub fn confirm_hypothesis(mut self) -> Self {
        self.hypothesis_confirmed = true;
        self
    }

    /// Set fitness delta
    pub fn with_fitness_delta(mut self, delta: f64) -> Self {
        self.fitness_delta = delta;
        self
    }

    /// Mark for application
    pub fn should_apply_result(mut self) -> Self {
        self.should_apply = true;
        self
    }
}

impl Default for ExperimentResult {
    fn default() -> Self {
        Self::new()
    }
}

/// An experiment proposal - agents propose hypotheses to test
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Experiment {
    /// Unique identifier
    pub id: String,

    /// Proposing agent
    pub proposer_id: AgentId,

    /// Type of experiment (e.g., "mutation_test", "behavior_exploration", "tool_evaluation")
    pub experiment_type: String,

    /// What hypothesis is being tested
    pub hypothesis: String,

    /// Detailed description of the experiment
    pub description: String,

    /// Expected outcome
    pub expected_outcome: String,

    /// Resources allowed for this experiment (tokens, time, memory)
    pub resource_budget: ExperimentBudget,

    /// Safety constraints
    pub safety_constraints: Vec<String>,

    /// Current status
    pub status: ExperimentStatus,

    /// When this was created
    pub created_at: DateTime<Utc>,

    /// When this was started
    pub started_at: Option<DateTime<Utc>>,

    /// When this was completed
    pub completed_at: Option<DateTime<Utc>>,

    /// Results (if experiment completed)
    pub result: Option<ExperimentResult>,

    /// Approval required from user/system
    pub requires_approval: bool,

    /// Whether this was approved
    pub approved: bool,

    /// Approver ID (if applicable)
    pub approved_by: Option<String>,

    /// Structured parameters
    pub parameters: Value,

    /// Related learning events
    pub learning_outcomes: Vec<String>,
}

/// Budget constraints for an experiment
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ExperimentBudget {
    /// Maximum API tokens allowed
    pub max_tokens: Option<u32>,

    /// Maximum execution time in seconds
    pub max_time_secs: Option<u32>,

    /// Maximum memory in MB
    pub max_memory_mb: Option<u32>,

    /// Maximum cost in USD
    pub max_cost_usd: Option<f64>,

    /// Whether to allow tool calls
    pub allow_tool_calls: bool,

    /// Whether to allow file writes
    pub allow_file_writes: bool,
}

impl Default for ExperimentBudget {
    fn default() -> Self {
        Self {
            max_tokens: Some(50000),
            max_time_secs: Some(300), // 5 minutes
            max_memory_mb: Some(512),
            max_cost_usd: Some(1.0),
            allow_tool_calls: true,
            allow_file_writes: false,
        }
    }
}

impl Experiment {
    /// Create a new experiment
    pub fn new(
        proposer_id: AgentId,
        experiment_type: impl Into<String>,
        hypothesis: impl Into<String>,
        description: impl Into<String>,
    ) -> Self {
        Self {
            id: nanoid::nanoid!(),
            proposer_id,
            experiment_type: experiment_type.into(),
            hypothesis: hypothesis.into(),
            description: description.into(),
            expected_outcome: String::new(),
            resource_budget: ExperimentBudget::default(),
            safety_constraints: vec![
                "No production data access".to_string(),
                "No permanent state changes without approval".to_string(),
            ],
            status: ExperimentStatus::Proposed,
            created_at: Utc::now(),
            started_at: None,
            completed_at: None,
            result: None,
            requires_approval: true,
            approved: false,
            approved_by: None,
            parameters: serde_json::json!({}),
            learning_outcomes: Vec::new(),
        }
    }

    /// Set expected outcome
    pub fn with_expected_outcome(mut self, outcome: impl Into<String>) -> Self {
        self.expected_outcome = outcome.into();
        self
    }

    /// Set resource budget
    pub fn with_budget(mut self, budget: ExperimentBudget) -> Self {
        self.resource_budget = budget;
        self
    }

    /// Mark as not requiring approval (for low-risk experiments)
    pub fn no_approval_required(mut self) -> Self {
        self.requires_approval = false;
        self
    }

    /// Approve the experiment
    pub fn approve(&mut self, approver: impl Into<String>) {
        self.approved = true;
        self.approved_by = Some(approver.into());
        self.status = ExperimentStatus::Approved;
    }

    /// Start execution
    pub fn start(&mut self) {
        self.started_at = Some(Utc::now());
        self.status = ExperimentStatus::Running;
    }

    /// Complete with result
    pub fn complete(&mut self, result: ExperimentResult) {
        self.completed_at = Some(Utc::now());
        self.status = ExperimentStatus::Completed;
        self.result = Some(result);
    }

    /// Fail the experiment
    pub fn fail(&mut self, reason: impl Into<String>) {
        self.completed_at = Some(Utc::now());
        self.status = ExperimentStatus::Failed(reason.into());
    }

    /// Rollback the experiment
    pub fn rollback(&mut self) {
        self.status = ExperimentStatus::RolledBack;
    }

    /// Record learning outcome
    pub fn add_learning_outcome(&mut self, learning_id: String) {
        self.learning_outcomes.push(learning_id);
    }

    /// Get execution time if completed
    pub fn execution_time_secs(&self) -> Option<f64> {
        match (self.started_at, self.completed_at) {
            (Some(start), Some(end)) => Some((end - start).num_seconds() as f64),
            _ => None,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_experiment_creation() {
        let proposer = AgentId::generate();
        let experiment = Experiment::new(
            proposer,
            "mutation_test",
            "Test new reasoning approach",
            "Try alternative reasoning strategy",
        );

        assert_eq!(experiment.proposer_id, proposer);
        assert_eq!(experiment.status, ExperimentStatus::Proposed);
        assert!(experiment.requires_approval);
    }

    #[test]
    fn test_experiment_lifecycle() {
        let proposer = AgentId::generate();
        let mut experiment = Experiment::new(
            proposer,
            "mutation_test",
            "Test new reasoning approach",
            "Try alternative reasoning strategy",
        );

        assert_eq!(experiment.status, ExperimentStatus::Proposed);

        experiment.approve("system");
        assert_eq!(experiment.status, ExperimentStatus::Approved);

        experiment.start();
        assert_eq!(experiment.status, ExperimentStatus::Running);

        let result = ExperimentResult::new()
            .confirm_hypothesis()
            .with_fitness_delta(0.05);

        experiment.complete(result);
        assert_eq!(experiment.status, ExperimentStatus::Completed);
    }

    #[test]
    fn test_experiment_budget() {
        let budget = ExperimentBudget {
            max_tokens: Some(10000),
            max_time_secs: Some(60),
            max_cost_usd: Some(0.5),
            ..Default::default()
        };

        assert_eq!(budget.max_tokens, Some(10000));
        assert!(budget.allow_tool_calls);
        assert!(!budget.allow_file_writes);
    }
}
