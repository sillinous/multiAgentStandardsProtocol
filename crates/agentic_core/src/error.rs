//! Error types for the agentic ecosystem

use thiserror::Error;

/// Result type for agentic operations
pub type Result<T> = std::result::Result<T, Error>;

/// Errors that can occur in the agentic ecosystem
#[derive(Error, Debug)]
pub enum Error {
    #[error("Invalid agent ID: {0}")]
    InvalidAgentId(String),

    #[error("Invalid workflow ID: {0}")]
    InvalidWorkflowId(String),

    #[error("Invalid task ID: {0}")]
    InvalidTaskId(String),

    #[error("Agent not found: {0}")]
    AgentNotFound(String),

    #[error("Workflow not found: {0}")]
    WorkflowNotFound(String),

    #[error("Task not found: {0}")]
    TaskNotFound(String),

    #[error("Tool not found: {0}")]
    ToolNotFound(String),

    #[error("Capability not supported: {0}")]
    CapabilityNotSupported(String),

    #[error("Agent initialization failed: {0}")]
    InitializationFailed(String),

    #[error("Message processing failed: {0}")]
    MessageProcessingFailed(String),

    #[error("Tool execution failed: {0}")]
    ToolExecutionFailed(String),

    #[error("Protocol error: {0}")]
    ProtocolError(String),

    #[error("Serialization error: {0}")]
    SerializationError(#[from] serde_json::Error),

    #[error("Internal error: {0}")]
    InternalError(String),

    #[error("Authorization failed: {0}")]
    AuthorizationFailed(String),

    #[error("Invalid state: {0}")]
    InvalidState(String),

    #[error("Timeout: {0}")]
    Timeout(String),

    #[error("Learning error: {0}")]
    LearningError(String),

    #[error("Experimentation error: {0}")]
    ExperimentationError(String),

    #[error("Agent factory error: {0}")]
    FactoryError(String),

    #[error("Coordination error: {0}")]
    CoordinationError(String),

    #[error("Policy violation: {0}")]
    PolicyViolation(String),

    #[error("Unknown error: {0}")]
    Unknown(String),
}

impl From<String> for Error {
    fn from(s: String) -> Self {
        Error::Unknown(s)
    }
}

impl From<&str> for Error {
    fn from(s: &str) -> Self {
        Error::Unknown(s.to_string())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_error_display() {
        let err = Error::AgentNotFound("agent-123".to_string());
        assert!(err.to_string().contains("agent-123"));
    }
}
