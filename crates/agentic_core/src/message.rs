//! Message types for agent communication

use crate::identity::{AgentId, WorkflowId};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use serde_json::Value;

/// Content that can be included in a message
#[derive(Clone, Debug, Serialize, Deserialize)]
pub enum MessageContent {
    /// Plain text content
    Text(String),

    /// Structured JSON data
    Json(Value),

    /// Task or instruction
    Task {
        title: String,
        description: String,
        context: Option<Value>,
    },

    /// Result of a completed task
    TaskResult {
        task_id: String,
        success: bool,
        result: String,
        data: Option<Value>,
    },

    /// Error or exception
    Error {
        code: String,
        message: String,
        details: Option<Value>,
    },

    /// Learning event (for learning agents)
    Learning {
        event_type: String,
        insight: String,
        confidence: f64,
    },

    /// Emergent behavior discovered
    EmergentBehavior {
        description: String,
        impact: String,
    },

    /// Multi-content message
    Multiple(Vec<MessageContent>),
}

/// Direction of message flow
#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize, Deserialize)]
pub enum MessageDirection {
    /// Message is being sent
    Sent,

    /// Message was received
    Received,
}

/// Message between agents or systems
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Message {
    /// Unique identifier for this message
    pub id: String,

    /// Agent sending this message
    pub from: AgentId,

    /// Agent receiving this message (None for broadcast)
    pub to: Option<AgentId>,

    /// Workflow this message is part of (if any)
    pub workflow_id: Option<WorkflowId>,

    /// Content of the message
    pub content: MessageContent,

    /// Direction of the message
    pub direction: MessageDirection,

    /// When this message was created
    pub timestamp: DateTime<Utc>,

    /// Optional correlation ID for tracing related messages
    pub correlation_id: Option<String>,

    /// Priority level (0-100)
    pub priority: u8,

    /// Whether this message requires acknowledgment
    pub requires_ack: bool,

    /// Acknowledgment status
    pub acknowledged: bool,

    /// Optional metadata
    pub metadata: Value,
}

impl Message {
    /// Create a new message from one agent to another
    pub fn new(
        from: AgentId,
        to: Option<AgentId>,
        content: MessageContent,
    ) -> Self {
        Self {
            id: nanoid::nanoid!(),
            from,
            to,
            workflow_id: None,
            content,
            direction: MessageDirection::Sent,
            timestamp: Utc::now(),
            correlation_id: None,
            priority: 50,
            requires_ack: false,
            acknowledged: false,
            metadata: serde_json::json!({}),
        }
    }

    /// Create a text message
    pub fn text(from: AgentId, to: Option<AgentId>, text: impl Into<String>) -> Self {
        Self::new(from, to, MessageContent::Text(text.into()))
    }

    /// Create a task message
    pub fn task(
        from: AgentId,
        to: Option<AgentId>,
        title: impl Into<String>,
        description: impl Into<String>,
    ) -> Self {
        Self::new(
            from,
            to,
            MessageContent::Task {
                title: title.into(),
                description: description.into(),
                context: None,
            },
        )
    }

    /// Create an error message
    pub fn error(
        from: AgentId,
        to: Option<AgentId>,
        code: impl Into<String>,
        message: impl Into<String>,
    ) -> Self {
        Self::new(
            from,
            to,
            MessageContent::Error {
                code: code.into(),
                message: message.into(),
                details: None,
            },
        )
    }

    /// Create a learning message
    pub fn learning(
        from: AgentId,
        insight: impl Into<String>,
        confidence: f64,
    ) -> Self {
        Self::new(
            from,
            None, // Learning messages are broadcast
            MessageContent::Learning {
                event_type: "insight".to_string(),
                insight: insight.into(),
                confidence: confidence.clamp(0.0, 1.0),
            },
        )
    }

    /// Set the workflow ID
    pub fn with_workflow(mut self, workflow_id: WorkflowId) -> Self {
        self.workflow_id = Some(workflow_id);
        self
    }

    /// Set correlation ID for tracing
    pub fn with_correlation_id(mut self, id: impl Into<String>) -> Self {
        self.correlation_id = Some(id.into());
        self
    }

    /// Set priority
    pub fn with_priority(mut self, priority: u8) -> Self {
        self.priority = priority.min(100);
        self
    }

    /// Mark as requiring acknowledgment
    pub fn requires_acknowledgment(mut self) -> Self {
        self.requires_ack = true;
        self
    }

    /// Acknowledge this message
    pub fn acknowledge(&mut self) {
        self.acknowledged = true;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_message_creation() {
        let from = AgentId::generate();
        let to = AgentId::generate();

        let msg = Message::text(from, Some(to), "Hello!");

        assert_eq!(msg.from, from);
        assert_eq!(msg.to, Some(to));
        assert!(!msg.id.is_empty());
    }

    #[test]
    fn test_message_with_workflow() {
        let from = AgentId::generate();
        let workflow_id = WorkflowId::generate();

        let msg = Message::text(from, None, "Test")
            .with_workflow(workflow_id);

        assert_eq!(msg.workflow_id, Some(workflow_id));
    }

    #[test]
    fn test_learning_message() {
        let from = AgentId::generate();
        let msg = Message::learning(from, "Discovered pattern X", 0.95);

        match msg.content {
            MessageContent::Learning {
                insight,
                confidence,
                ..
            } => {
                assert_eq!(insight, "Discovered pattern X");
                assert_eq!(confidence, 0.95);
            }
            _ => panic!("Expected learning content"),
        }
    }
}
