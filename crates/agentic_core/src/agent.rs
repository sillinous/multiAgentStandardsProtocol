//! Agent types and traits

use crate::identity::AgentId;
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Represents the role an agent plays in the system
#[derive(Clone, Debug, Eq, PartialEq, Serialize, Deserialize)]
pub enum AgentRole {
    /// Supervisory agent that coordinates other agents
    Supervisor,

    /// Worker agent that performs specific tasks
    Worker,

    /// Peer agent in a swarm configuration
    Peer,

    /// Meta-agent that creates and manages other agents (AgentFactory)
    Factory,

    /// Standardization agent that monitors and updates standards
    Standardizer,

    /// Learning agent that processes and shares knowledge
    Learner,

    /// Custom role defined by user
    Custom(String),
}

impl std::fmt::Display for AgentRole {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            AgentRole::Supervisor => write!(f, "supervisor"),
            AgentRole::Worker => write!(f, "worker"),
            AgentRole::Peer => write!(f, "peer"),
            AgentRole::Factory => write!(f, "factory"),
            AgentRole::Standardizer => write!(f, "standardizer"),
            AgentRole::Learner => write!(f, "learner"),
            AgentRole::Custom(name) => write!(f, "custom:{}", name),
        }
    }
}

/// Agent lifecycle status
#[derive(Clone, Debug, Eq, PartialEq, Serialize, Deserialize)]
pub enum AgentStatus {
    /// Agent initialized but not yet started
    Initialized,

    /// Agent is actively running
    Running,

    /// Agent is paused/idle
    Idle,

    /// Agent is learning or evolving
    Learning,

    /// Agent is executing a task
    Busy,

    /// Agent encountered an error
    Error(String),

    /// Agent has been retired
    Retired,
}

impl std::fmt::Display for AgentStatus {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            AgentStatus::Initialized => write!(f, "initialized"),
            AgentStatus::Running => write!(f, "running"),
            AgentStatus::Idle => write!(f, "idle"),
            AgentStatus::Learning => write!(f, "learning"),
            AgentStatus::Busy => write!(f, "busy"),
            AgentStatus::Error(msg) => write!(f, "error: {}", msg),
            AgentStatus::Retired => write!(f, "retired"),
        }
    }
}

/// Metadata about an agent's performance
#[derive(Clone, Debug, Default, Serialize, Deserialize)]
pub struct AgentMetrics {
    /// Number of tasks completed
    pub tasks_completed: u64,

    /// Number of tasks failed
    pub tasks_failed: u64,

    /// Average task completion time in milliseconds
    pub avg_completion_time_ms: f64,

    /// Agent's current success rate (0.0 to 1.0)
    pub success_rate: f64,

    /// Number of successful tool calls
    pub tool_calls_successful: u64,

    /// Number of failed tool calls
    pub tool_calls_failed: u64,

    /// Knowledge items learned
    pub knowledge_items: u64,

    /// Experiences from interactions
    pub experiences_collected: u64,
}

/// Core agent data structure
///
/// This represents the fundamental agent entity in the ecosystem.
/// Agents can be initialized, evolved, coordinated, and can learn over time.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Agent {
    /// Unique identifier for this agent
    pub id: AgentId,

    /// Human-readable name
    pub name: String,

    /// Detailed description of what this agent does
    pub description: String,

    /// The role this agent plays in the system
    pub role: AgentRole,

    /// Current status of the agent
    pub status: AgentStatus,

    /// Model identifier (e.g., "claude-3-opus", "gpt-4")
    pub model: String,

    /// Provider (e.g., "anthropic", "openai")
    pub provider: String,

    /// Tags for categorization and discovery
    pub tags: Vec<String>,

    /// Version of the agent's genome/behavior
    pub version: String,

    /// Metadata about performance
    pub metrics: AgentMetrics,

    /// Configuration parameters
    pub config: HashMap<String, serde_json::Value>,

    /// When this agent was created
    pub created_at: DateTime<Utc>,

    /// When this agent was last modified
    pub updated_at: DateTime<Utc>,

    /// Fitness score (0.0 to 1.0) for evolution
    pub fitness_score: f64,

    /// Whether this agent is currently available for use
    pub is_available: bool,
}

impl Agent {
    /// Create a new agent with default values
    pub fn new(
        name: impl Into<String>,
        description: impl Into<String>,
        role: AgentRole,
        model: impl Into<String>,
        provider: impl Into<String>,
    ) -> Self {
        let now = Utc::now();

        Self {
            id: AgentId::generate(),
            name: name.into(),
            description: description.into(),
            role,
            status: AgentStatus::Initialized,
            model: model.into(),
            provider: provider.into(),
            tags: Vec::new(),
            version: "1.0.0".to_string(),
            metrics: AgentMetrics::default(),
            config: HashMap::new(),
            created_at: now,
            updated_at: now,
            fitness_score: 0.5,
            is_available: true,
        }
    }

    /// Update the agent's status
    pub fn set_status(&mut self, status: AgentStatus) {
        self.status = status;
        self.updated_at = Utc::now();
    }

    /// Record a successful task completion
    pub fn record_task_success(&mut self, completion_time_ms: f64) {
        self.metrics.tasks_completed += 1;
        let old_avg = self.metrics.avg_completion_time_ms;
        let total_tasks = self.metrics.tasks_completed + self.metrics.tasks_failed;
        let completed = self.metrics.tasks_completed as f64;

        // Calculate running average
        self.metrics.avg_completion_time_ms =
            (old_avg * (completed - 1.0) + completion_time_ms) / completed;

        // Update success rate
        self.metrics.success_rate = completed / total_tasks as f64;
        self.updated_at = Utc::now();
    }

    /// Record a failed task
    pub fn record_task_failure(&mut self) {
        self.metrics.tasks_failed += 1;
        let total_tasks = self.metrics.tasks_completed + self.metrics.tasks_failed;
        self.metrics.success_rate = self.metrics.tasks_completed as f64 / total_tasks as f64;
        self.updated_at = Utc::now();
    }

    /// Update the agent's fitness score for evolution
    pub fn set_fitness_score(&mut self, score: f64) {
        self.fitness_score = score.clamp(0.0, 1.0);
        self.updated_at = Utc::now();
    }

    /// Add a tag for categorization
    pub fn add_tag(&mut self, tag: impl Into<String>) {
        let tag = tag.into();
        if !self.tags.contains(&tag) {
            self.tags.push(tag);
            self.updated_at = Utc::now();
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_agent_creation() {
        let agent = Agent::new(
            "Test Agent",
            "A test agent",
            AgentRole::Worker,
            "claude-3-opus",
            "anthropic",
        );

        assert_eq!(agent.name, "Test Agent");
        assert_eq!(agent.status, AgentStatus::Initialized);
        assert_eq!(agent.role, AgentRole::Worker);
    }

    #[test]
    fn test_agent_metrics_tracking() {
        let mut agent = Agent::new(
            "Test Agent",
            "A test agent",
            AgentRole::Worker,
            "claude-3-opus",
            "anthropic",
        );

        agent.record_task_success(100.0);
        assert_eq!(agent.metrics.tasks_completed, 1);
        assert_eq!(agent.metrics.avg_completion_time_ms, 100.0);

        agent.record_task_success(200.0);
        assert_eq!(agent.metrics.tasks_completed, 2);
        assert_eq!(agent.metrics.avg_completion_time_ms, 150.0);

        agent.record_task_failure();
        assert_eq!(agent.metrics.tasks_failed, 1);
        assert!(agent.metrics.success_rate < 1.0);
    }

    #[test]
    fn test_agent_status_update() {
        let mut agent = Agent::new(
            "Test Agent",
            "A test agent",
            AgentRole::Worker,
            "claude-3-opus",
            "anthropic",
        );

        assert_eq!(agent.status, AgentStatus::Initialized);

        agent.set_status(AgentStatus::Running);
        assert_eq!(agent.status, AgentStatus::Running);
    }
}
