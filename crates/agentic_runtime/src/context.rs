//! Execution context for agent runs

use agentic_core::{AgentId, WorkflowId};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Context data that can be passed to agent execution
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContextData {
    data: HashMap<String, serde_json::Value>,
}

impl ContextData {
    pub fn new() -> Self {
        Self {
            data: HashMap::new(),
        }
    }

    pub fn insert(&mut self, key: impl Into<String>, value: serde_json::Value) {
        self.data.insert(key.into(), value);
    }

    pub fn get(&self, key: &str) -> Option<&serde_json::Value> {
        self.data.get(key)
    }

    pub fn get_str(&self, key: &str) -> Option<String> {
        self.data.get(key)?.as_str().map(|s| s.to_string())
    }

    pub fn get_i64(&self, key: &str) -> Option<i64> {
        self.data.get(key)?.as_i64()
    }

    pub fn get_bool(&self, key: &str) -> Option<bool> {
        self.data.get(key)?.as_bool()
    }
}

impl Default for ContextData {
    fn default() -> Self {
        Self::new()
    }
}

/// Execution context for an agent run
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExecutionContext {
    pub agent_id: AgentId,
    pub workflow_id: Option<WorkflowId>,
    pub parent_agent_id: Option<AgentId>,
    pub data: ContextData,
    pub metadata: HashMap<String, String>,
}

impl ExecutionContext {
    pub fn new(agent_id: AgentId) -> Self {
        Self {
            agent_id,
            workflow_id: None,
            parent_agent_id: None,
            data: ContextData::new(),
            metadata: HashMap::new(),
        }
    }

    pub fn with_workflow(mut self, workflow_id: WorkflowId) -> Self {
        self.workflow_id = Some(workflow_id);
        self
    }

    pub fn with_parent(mut self, parent_id: AgentId) -> Self {
        self.parent_agent_id = Some(parent_id);
        self
    }

    pub fn add_metadata(&mut self, key: impl Into<String>, value: impl Into<String>) {
        self.metadata.insert(key.into(), value.into());
    }
}
