//! Task scheduler for managing agent execution queue

use agentic_core::{AgentId, WorkflowId};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::cmp::Ordering;
use std::collections::{BinaryHeap, HashMap};
use std::sync::{Arc, Mutex};
use tokio::sync::mpsc;
use uuid::Uuid;

/// Task priority levels
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum TaskPriority {
    Low = 1,
    Normal = 2,
    High = 3,
    Critical = 4,
}

/// Status of a task
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum TaskStatus {
    Pending,
    Running,
    Completed,
    Failed,
    Cancelled,
}

/// A task to be executed by an agent
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Task {
    pub id: String,
    pub agent_id: AgentId,
    pub workflow_id: Option<WorkflowId>,
    pub input: String,
    pub priority: TaskPriority,
    pub status: TaskStatus,
    pub created_at: DateTime<Utc>,
    pub started_at: Option<DateTime<Utc>>,
    pub completed_at: Option<DateTime<Utc>>,
    pub result: Option<String>,
    pub error: Option<String>,
    pub retry_count: u32,
    pub max_retries: u32,
}

impl Task {
    pub fn new(agent_id: AgentId, input: impl Into<String>) -> Self {
        Self {
            id: Uuid::new_v4().to_string(),
            agent_id,
            workflow_id: None,
            input: input.into(),
            priority: TaskPriority::Normal,
            status: TaskStatus::Pending,
            created_at: Utc::now(),
            started_at: None,
            completed_at: None,
            result: None,
            error: None,
            retry_count: 0,
            max_retries: 3,
        }
    }

    pub fn with_priority(mut self, priority: TaskPriority) -> Self {
        self.priority = priority;
        self
    }

    pub fn with_workflow(mut self, workflow_id: WorkflowId) -> Self {
        self.workflow_id = Some(workflow_id);
        self
    }

    pub fn with_max_retries(mut self, max: u32) -> Self {
        self.max_retries = max;
        self
    }

    pub fn mark_running(&mut self) {
        self.status = TaskStatus::Running;
        self.started_at = Some(Utc::now());
    }

    pub fn mark_completed(&mut self, result: String) {
        self.status = TaskStatus::Completed;
        self.completed_at = Some(Utc::now());
        self.result = Some(result);
    }

    pub fn mark_failed(&mut self, error: String) {
        self.status = TaskStatus::Failed;
        self.completed_at = Some(Utc::now());
        self.error = Some(error);
    }

    pub fn can_retry(&self) -> bool {
        self.retry_count < self.max_retries
    }

    pub fn increment_retry(&mut self) {
        self.retry_count += 1;
    }
}

/// Wrapper for priority queue ordering
#[derive(Clone)]
struct PrioritizedTask {
    task: Task,
}

impl PartialEq for PrioritizedTask {
    fn eq(&self, other: &Self) -> bool {
        self.task.priority == other.task.priority
    }
}

impl Eq for PrioritizedTask {}

impl PartialOrd for PrioritizedTask {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

impl Ord for PrioritizedTask {
    fn cmp(&self, other: &Self) -> Ordering {
        // Higher priority first
        self.task.priority.cmp(&other.task.priority)
            .then_with(|| other.task.created_at.cmp(&self.task.created_at)) // Earlier tasks first if same priority
    }
}

/// Task scheduler manages the execution queue
pub struct TaskScheduler {
    queue: Arc<Mutex<BinaryHeap<PrioritizedTask>>>,
    tasks: Arc<Mutex<HashMap<String, Task>>>,
    task_tx: mpsc::UnboundedSender<Task>,
    task_rx: Arc<Mutex<mpsc::UnboundedReceiver<Task>>>,
}

impl TaskScheduler {
    pub fn new() -> Self {
        let (task_tx, task_rx) = mpsc::unbounded_channel();

        Self {
            queue: Arc::new(Mutex::new(BinaryHeap::new())),
            tasks: Arc::new(Mutex::new(HashMap::new())),
            task_tx,
            task_rx: Arc::new(Mutex::new(task_rx)),
        }
    }

    /// Submit a new task to the scheduler
    pub fn submit(&self, mut task: Task) -> Result<String, String> {
        task.status = TaskStatus::Pending;
        let task_id = task.id.clone();

        // Store task
        self.tasks.lock().unwrap().insert(task_id.clone(), task.clone());

        // Add to priority queue
        self.queue.lock().unwrap().push(PrioritizedTask { task: task.clone() });

        // Send notification
        if let Err(e) = self.task_tx.send(task) {
            return Err(format!("Failed to submit task: {}", e));
        }

        Ok(task_id)
    }

    /// Get the next task from the queue
    pub fn next_task(&self) -> Option<Task> {
        let mut queue = self.queue.lock().unwrap();
        queue.pop().map(|pt| {
            let mut task = pt.task;
            task.mark_running();

            // Update task in storage
            self.tasks.lock().unwrap().insert(task.id.clone(), task.clone());

            task
        })
    }

    /// Get a task by ID
    pub fn get_task(&self, task_id: &str) -> Option<Task> {
        self.tasks.lock().unwrap().get(task_id).cloned()
    }

    /// Update a task's status
    pub fn update_task(&self, task_id: &str, update_fn: impl FnOnce(&mut Task)) {
        if let Some(task) = self.tasks.lock().unwrap().get_mut(task_id) {
            update_fn(task);
        }
    }

    /// Complete a task
    pub fn complete_task(&self, task_id: &str, result: String) {
        self.update_task(task_id, |task| {
            task.mark_completed(result);
        });
    }

    /// Fail a task
    pub fn fail_task(&self, task_id: &str, error: String) {
        self.update_task(task_id, |task| {
            task.mark_failed(error);
        });
    }

    /// Retry a task if possible
    pub fn retry_task(&self, task_id: &str) -> Result<(), String> {
        let task = self.get_task(task_id)
            .ok_or_else(|| format!("Task {} not found", task_id))?;

        if !task.can_retry() {
            return Err(format!("Task {} has exceeded max retries", task_id));
        }

        let mut new_task = task.clone();
        new_task.increment_retry();
        new_task.status = TaskStatus::Pending;
        new_task.started_at = None;
        new_task.completed_at = None;
        new_task.result = None;
        new_task.error = None;

        self.queue.lock().unwrap().push(PrioritizedTask { task: new_task.clone() });
        self.tasks.lock().unwrap().insert(task_id.to_string(), new_task);

        Ok(())
    }

    /// Get all tasks for an agent
    pub fn get_agent_tasks(&self, agent_id: &AgentId) -> Vec<Task> {
        self.tasks.lock().unwrap()
            .values()
            .filter(|t| t.agent_id == *agent_id)
            .cloned()
            .collect()
    }

    /// Get all tasks in a workflow
    pub fn get_workflow_tasks(&self, workflow_id: &WorkflowId) -> Vec<Task> {
        self.tasks.lock().unwrap()
            .values()
            .filter(|t| t.workflow_id.as_ref() == Some(workflow_id))
            .cloned()
            .collect()
    }

    /// Get queue statistics
    pub fn stats(&self) -> SchedulerStats {
        let tasks = self.tasks.lock().unwrap();
        let pending = tasks.values().filter(|t| t.status == TaskStatus::Pending).count();
        let running = tasks.values().filter(|t| t.status == TaskStatus::Running).count();
        let completed = tasks.values().filter(|t| t.status == TaskStatus::Completed).count();
        let failed = tasks.values().filter(|t| t.status == TaskStatus::Failed).count();

        SchedulerStats {
            total: tasks.len(),
            pending,
            running,
            completed,
            failed,
            queue_size: self.queue.lock().unwrap().len(),
        }
    }
}

impl Default for TaskScheduler {
    fn default() -> Self {
        Self::new()
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SchedulerStats {
    pub total: usize,
    pub pending: usize,
    pub running: usize,
    pub completed: usize,
    pub failed: usize,
    pub queue_size: usize,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_task_creation() {
        let agent_id = AgentId::generate();
        let task = Task::new(agent_id, "Test input")
            .with_priority(TaskPriority::High);

        assert_eq!(task.agent_id, agent_id);
        assert_eq!(task.priority, TaskPriority::High);
        assert_eq!(task.status, TaskStatus::Pending);
    }

    #[test]
    fn test_scheduler_submit() {
        let scheduler = TaskScheduler::new();
        let agent_id = AgentId::generate();
        let task = Task::new(agent_id, "Test input");

        let task_id = scheduler.submit(task).unwrap();
        assert!(!task_id.is_empty());

        let retrieved = scheduler.get_task(&task_id);
        assert!(retrieved.is_some());
    }

    #[test]
    fn test_priority_ordering() {
        let scheduler = TaskScheduler::new();
        let agent_id = AgentId::generate();

        // Submit tasks in reverse priority order
        let low_task = Task::new(agent_id, "Low").with_priority(TaskPriority::Low);
        let high_task = Task::new(agent_id, "High").with_priority(TaskPriority::High);
        let normal_task = Task::new(agent_id, "Normal").with_priority(TaskPriority::Normal);

        scheduler.submit(low_task).unwrap();
        scheduler.submit(high_task).unwrap();
        scheduler.submit(normal_task).unwrap();

        // High priority should come first
        let task1 = scheduler.next_task().unwrap();
        assert_eq!(task1.priority, TaskPriority::High);

        let task2 = scheduler.next_task().unwrap();
        assert_eq!(task2.priority, TaskPriority::Normal);

        let task3 = scheduler.next_task().unwrap();
        assert_eq!(task3.priority, TaskPriority::Low);
    }
}
