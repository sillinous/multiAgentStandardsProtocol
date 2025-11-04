//! Agent and workflow identity types

use serde::{Deserialize, Serialize};
use std::fmt;
use uuid::Uuid;

/// Unique identifier for an agent
#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq, Serialize, Deserialize)]
pub struct AgentId(Uuid);

impl AgentId {
    /// Generate a new unique agent ID
    pub fn generate() -> Self {
        Self(Uuid::new_v4())
    }

    /// Create from string (for parsing from external sources)
    pub fn from_string(s: &str) -> crate::Result<Self> {
        Uuid::parse_str(s)
            .map(Self)
            .map_err(|e| crate::Error::InvalidAgentId(e.to_string()))
    }

    /// Get the string representation
    pub fn as_str(&self) -> String {
        self.0.to_string()
    }
}

impl fmt::Display for AgentId {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.0)
    }
}

impl Default for AgentId {
    fn default() -> Self {
        Self::generate()
    }
}

/// Unique identifier for a workflow or multi-agent execution
#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq, Serialize, Deserialize)]
pub struct WorkflowId(Uuid);

impl WorkflowId {
    /// Generate a new unique workflow ID
    pub fn generate() -> Self {
        Self(Uuid::new_v4())
    }

    /// Create from string (for parsing from external sources)
    pub fn from_string(s: &str) -> crate::Result<Self> {
        Uuid::parse_str(s)
            .map(Self)
            .map_err(|e| crate::Error::InvalidWorkflowId(e.to_string()))
    }

    /// Get the string representation
    pub fn as_str(&self) -> String {
        self.0.to_string()
    }
}

impl fmt::Display for WorkflowId {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.0)
    }
}

impl Default for WorkflowId {
    fn default() -> Self {
        Self::generate()
    }
}

/// Task ID for tracking individual work items
#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq, Serialize, Deserialize)]
pub struct TaskId(Uuid);

impl TaskId {
    /// Generate a new unique task ID
    pub fn generate() -> Self {
        Self(Uuid::new_v4())
    }

    /// Create from string
    pub fn from_string(s: &str) -> crate::Result<Self> {
        Uuid::parse_str(s)
            .map(Self)
            .map_err(|e| crate::Error::InvalidTaskId(e.to_string()))
    }

    pub fn as_str(&self) -> String {
        self.0.to_string()
    }
}

impl fmt::Display for TaskId {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.0)
    }
}

impl Default for TaskId {
    fn default() -> Self {
        Self::generate()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_agent_id_generation() {
        let id1 = AgentId::generate();
        let id2 = AgentId::generate();
        assert_ne!(id1, id2);
    }

    #[test]
    fn test_agent_id_from_string() {
        let id = AgentId::generate();
        let id_str = id.as_str();
        let parsed = AgentId::from_string(&id_str).unwrap();
        assert_eq!(id, parsed);
    }

    #[test]
    fn test_workflow_id_generation() {
        let id1 = WorkflowId::generate();
        let id2 = WorkflowId::generate();
        assert_ne!(id1, id2);
    }
}
