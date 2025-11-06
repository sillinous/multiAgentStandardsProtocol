//! Shared state management for workflows and agents

use agentic_core::identity::{AgentId, WorkflowId};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::HashMap;

/// Shared state context for a workflow
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct SharedState {
    /// Workflow ID this state belongs to
    pub workflow_id: WorkflowId,

    /// Current state data
    pub data: HashMap<String, Value>,

    /// State version for consistency
    pub version: u32,

    /// When this state was created
    pub created_at: DateTime<Utc>,

    /// When this state was last modified
    pub modified_at: DateTime<Utc>,

    /// Last agent to modify this state
    pub last_modified_by: Option<AgentId>,

    /// Whether state is locked (read-only)
    pub locked: bool,

    /// Checkpoints for rollback
    pub checkpoints: Vec<StateCheckpoint>,
}

/// A checkpoint of state at a point in time
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct StateCheckpoint {
    /// Checkpoint ID
    pub id: String,

    /// Snapshot of state at this point
    pub snapshot: HashMap<String, Value>,

    /// When this checkpoint was created
    pub timestamp: DateTime<Utc>,

    /// Description of what changed
    pub description: String,

    /// Whether this checkpoint was successful and should be maintained
    pub valid: bool,
}

impl StateCheckpoint {
    /// Create a new checkpoint
    pub fn new(
        snapshot: HashMap<String, Value>,
        description: impl Into<String>,
    ) -> Self {
        Self {
            id: nanoid::nanoid!(),
            snapshot,
            timestamp: Utc::now(),
            description: description.into(),
            valid: true,
        }
    }
}

impl SharedState {
    /// Create new shared state for a workflow
    pub fn new(workflow_id: WorkflowId) -> Self {
        let now = Utc::now();
        Self {
            workflow_id,
            data: HashMap::new(),
            version: 0,
            created_at: now,
            modified_at: now,
            last_modified_by: None,
            locked: false,
            checkpoints: Vec::new(),
        }
    }

    /// Set a value in the state
    pub fn set(&mut self, key: impl Into<String>, value: Value, agent_id: AgentId) {
        if self.locked {
            return; // Silently ignore writes to locked state
        }

        self.data.insert(key.into(), value);
        self.version += 1;
        self.modified_at = Utc::now();
        self.last_modified_by = Some(agent_id);
    }

    /// Get a value from the state
    pub fn get(&self, key: &str) -> Option<&Value> {
        self.data.get(key)
    }

    /// Remove a value from the state
    pub fn remove(&mut self, key: &str, agent_id: AgentId) {
        if self.locked {
            return;
        }

        self.data.remove(key);
        self.version += 1;
        self.modified_at = Utc::now();
        self.last_modified_by = Some(agent_id);
    }

    /// Check if a key exists
    pub fn has(&self, key: &str) -> bool {
        self.data.contains_key(key)
    }

    /// Get all keys
    pub fn keys(&self) -> Vec<String> {
        self.data.keys().cloned().collect()
    }

    /// Create a checkpoint
    pub fn checkpoint(&mut self, description: impl Into<String>) {
        let checkpoint = StateCheckpoint::new(self.data.clone(), description);
        self.checkpoints.push(checkpoint);
    }

    /// Restore from a checkpoint
    pub fn restore_checkpoint(&mut self, checkpoint_id: &str) -> bool {
        if let Some(checkpoint) = self.checkpoints.iter().find(|c| c.id == checkpoint_id) {
            if checkpoint.valid {
                self.data = checkpoint.snapshot.clone();
                self.version += 1;
                self.modified_at = Utc::now();
                return true;
            }
        }
        false
    }

    /// Lock state (make read-only)
    pub fn lock(&mut self) {
        self.locked = true;
    }

    /// Unlock state
    pub fn unlock(&mut self) {
        self.locked = false;
    }

    /// Get latest checkpoint
    pub fn latest_checkpoint(&self) -> Option<&StateCheckpoint> {
        self.checkpoints.iter().max_by_key(|c| c.timestamp)
    }
}

/// Agent-local state (not shared)
#[derive(Clone, Debug, Default, Serialize, Deserialize)]
pub struct AgentLocalState {
    /// Agent ID
    pub agent_id: AgentId,

    /// Local state data
    pub data: HashMap<String, Value>,

    /// When created
    pub created_at: DateTime<Utc>,

    /// When modified
    pub modified_at: DateTime<Utc>,
}

impl AgentLocalState {
    /// Create new local state for an agent
    pub fn new(agent_id: AgentId) -> Self {
        let now = Utc::now();
        Self {
            agent_id,
            data: HashMap::new(),
            created_at: now,
            modified_at: now,
        }
    }

    /// Set a value
    pub fn set(&mut self, key: impl Into<String>, value: Value) {
        self.data.insert(key.into(), value);
        self.modified_at = Utc::now();
    }

    /// Get a value
    pub fn get(&self, key: &str) -> Option<&Value> {
        self.data.get(key)
    }

    /// Clear all state
    pub fn clear(&mut self) {
        self.data.clear();
        self.modified_at = Utc::now();
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_shared_state() {
        let workflow_id = WorkflowId::generate();
        let agent_id = AgentId::generate();
        let mut state = SharedState::new(workflow_id);

        state.set("key1", serde_json::json!("value1"), agent_id);
        assert_eq!(state.get("key1"), Some(&serde_json::json!("value1")));
        assert_eq!(state.version, 1);
    }

    #[test]
    fn test_state_checkpoint() {
        let workflow_id = WorkflowId::generate();
        let agent_id = AgentId::generate();
        let mut state = SharedState::new(workflow_id);

        state.set("key1", serde_json::json!("value1"), agent_id);
        state.checkpoint("Initial state");

        state.set("key1", serde_json::json!("value2"), agent_id);

        // Restore
        if let Some(checkpoint) = state.latest_checkpoint() {
            assert!(state.restore_checkpoint(&checkpoint.id));
            assert_eq!(state.get("key1"), Some(&serde_json::json!("value1")));
        }
    }

    #[test]
    fn test_agent_local_state() {
        let agent_id = AgentId::generate();
        let mut local_state = AgentLocalState::new(agent_id);

        local_state.set("memory", serde_json::json!("important info"));
        assert!(local_state.has("memory") if { local_state.data.contains_key("memory") } else { false });
    }
}
