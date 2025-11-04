//! Workflow definitions and management

use agentic_core::identity::{AgentId, WorkflowId};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use serde_json::Value;

/// Status of a workflow
#[derive(Clone, Debug, Eq, PartialEq, Serialize, Deserialize)]
pub enum WorkflowStatus {
    /// Workflow created but not started
    Created,

    /// Workflow is running
    Running,

    /// Workflow is paused
    Paused,

    /// Workflow completed successfully
    Completed,

    /// Workflow failed
    Failed(String),

    /// Workflow was cancelled
    Cancelled,

    /// Waiting for input/approval
    Waiting,
}

impl std::fmt::Display for WorkflowStatus {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            WorkflowStatus::Created => write!(f, "created"),
            WorkflowStatus::Running => write!(f, "running"),
            WorkflowStatus::Paused => write!(f, "paused"),
            WorkflowStatus::Completed => write!(f, "completed"),
            WorkflowStatus::Failed(msg) => write!(f, "failed: {}", msg),
            WorkflowStatus::Cancelled => write!(f, "cancelled"),
            WorkflowStatus::Waiting => write!(f, "waiting"),
        }
    }
}

/// A task within a workflow
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Task {
    /// Unique identifier
    pub id: String,

    /// Task name
    pub name: String,

    /// Task description
    pub description: String,

    /// Assigned agent (if any)
    pub assigned_agent: Option<AgentId>,

    /// Status
    pub status: TaskStatus,

    /// When created
    pub created_at: DateTime<Utc>,

    /// When started
    pub started_at: Option<DateTime<Utc>>,

    /// When completed
    pub completed_at: Option<DateTime<Utc>>,

    /// Task output
    pub output: Option<Value>,

    /// Error message (if failed)
    pub error: Option<String>,
}

/// Task status
#[derive(Clone, Debug, Eq, PartialEq, Serialize, Deserialize)]
pub enum TaskStatus {
    Pending,
    Running,
    Completed,
    Failed,
    Skipped,
}

impl Task {
    /// Create a new task
    pub fn new(name: impl Into<String>, description: impl Into<String>) -> Self {
        Self {
            id: nanoid::nanoid!(),
            name: name.into(),
            description: description.into(),
            assigned_agent: None,
            status: TaskStatus::Pending,
            created_at: Utc::now(),
            started_at: None,
            completed_at: None,
            output: None,
            error: None,
        }
    }

    /// Assign task to agent
    pub fn assign_to(mut self, agent_id: AgentId) -> Self {
        self.assigned_agent = Some(agent_id);
        self
    }

    /// Mark as started
    pub fn start(&mut self) {
        self.status = TaskStatus::Running;
        self.started_at = Some(Utc::now());
    }

    /// Mark as completed
    pub fn complete(&mut self, output: Value) {
        self.status = TaskStatus::Completed;
        self.completed_at = Some(Utc::now());
        self.output = Some(output);
    }

    /// Mark as failed
    pub fn fail(&mut self, error: impl Into<String>) {
        self.status = TaskStatus::Failed;
        self.completed_at = Some(Utc::now());
        self.error = Some(error.into());
    }
}

/// A multi-agent workflow
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Workflow {
    /// Unique identifier
    pub id: WorkflowId,

    /// Workflow name
    pub name: String,

    /// Description
    pub description: String,

    /// Status
    pub status: WorkflowStatus,

    /// Goal of the workflow
    pub goal: String,

    /// Tasks in the workflow
    pub tasks: Vec<Task>,

    /// Participating agents
    pub agents: Vec<AgentId>,

    /// When created
    pub created_at: DateTime<Utc>,

    /// When started
    pub started_at: Option<DateTime<Utc>>,

    /// When completed
    pub completed_at: Option<DateTime<Utc>>,

    /// Final result
    pub result: Option<Value>,

    /// Total tokens used
    pub tokens_used: u32,

    /// Total cost in USD
    pub total_cost_usd: f64,

    /// Metrics
    pub metrics: WorkflowMetrics,
}

/// Workflow metrics
#[derive(Clone, Debug, Default, Serialize, Deserialize)]
pub struct WorkflowMetrics {
    pub total_tasks: u32,
    pub completed_tasks: u32,
    pub failed_tasks: u32,
    pub total_agents: u32,
    pub total_duration_secs: f64,
}

impl Workflow {
    /// Create a new workflow
    pub fn new(
        name: impl Into<String>,
        description: impl Into<String>,
        goal: impl Into<String>,
    ) -> Self {
        Self {
            id: WorkflowId::generate(),
            name: name.into(),
            description: description.into(),
            status: WorkflowStatus::Created,
            goal: goal.into(),
            tasks: Vec::new(),
            agents: Vec::new(),
            created_at: Utc::now(),
            started_at: None,
            completed_at: None,
            result: None,
            tokens_used: 0,
            total_cost_usd: 0.0,
            metrics: WorkflowMetrics::default(),
        }
    }

    /// Add a task to the workflow
    pub fn add_task(&mut self, task: Task) {
        self.tasks.push(task);
    }

    /// Add an agent to the workflow
    pub fn add_agent(&mut self, agent_id: AgentId) {
        if !self.agents.contains(&agent_id) {
            self.agents.push(agent_id);
        }
    }

    /// Start the workflow
    pub fn start(&mut self) {
        self.status = WorkflowStatus::Running;
        self.started_at = Some(Utc::now());
    }

    /// Complete the workflow
    pub fn complete(&mut self, result: Value) {
        self.status = WorkflowStatus::Completed;
        self.completed_at = Some(Utc::now());
        self.result = Some(result);
        self.update_metrics();
    }

    /// Fail the workflow
    pub fn fail(&mut self, reason: impl Into<String>) {
        self.status = WorkflowStatus::Failed(reason.into());
        self.completed_at = Some(Utc::now());
        self.update_metrics();
    }

    /// Update metrics
    fn update_metrics(&mut self) {
        self.metrics.total_tasks = self.tasks.len() as u32;
        self.metrics.completed_tasks =
            self.tasks.iter().filter(|t| t.status == TaskStatus::Completed).count() as u32;
        self.metrics.failed_tasks =
            self.tasks.iter().filter(|t| t.status == TaskStatus::Failed).count() as u32;
        self.metrics.total_agents = self.agents.len() as u32;

        if let (Some(start), Some(end)) = (self.started_at, self.completed_at) {
            self.metrics.total_duration_secs = (end - start).num_seconds() as f64;
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_task_creation() {
        let task = Task::new("Analyze data", "Analyze the data set");
        assert_eq!(task.status, TaskStatus::Pending);
    }

    #[test]
    fn test_workflow_creation() {
        let workflow = Workflow::new(
            "Data Pipeline",
            "Process and analyze data",
            "Extract insights from data",
        );

        assert_eq!(workflow.status, WorkflowStatus::Created);
        assert!(workflow.tasks.is_empty());
    }

    #[test]
    fn test_workflow_with_tasks() {
        let mut workflow = Workflow::new(
            "Data Pipeline",
            "Process and analyze data",
            "Extract insights from data",
        );

        let task1 = Task::new("Extract", "Extract data from source");
        let task2 = Task::new("Transform", "Transform the data");

        workflow.add_task(task1);
        workflow.add_task(task2);

        assert_eq!(workflow.tasks.len(), 2);
    }
}
