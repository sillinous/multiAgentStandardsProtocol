//! A2A (Agent-to-Agent) Protocol Implementation
//!
//! Standards-compliant A2A protocol for autonomous agent communication

use agentic_core::AgentId;
use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};

/// A2A Message - Complete message structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct A2aMessage {
    pub envelope: A2aEnvelope,
    pub payload: Payload,
}

/// A2A Envelope - Message routing and metadata
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct A2aEnvelope {
    pub from: AgentInfo,
    pub to: AgentInfo,
    pub message_id: String,
    pub correlation_id: Option<String>,
    pub timestamp: DateTime<Utc>,
    pub priority: Priority,
    pub ttl: Option<u64>, // Time to live in seconds
}

/// Agent information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentInfo {
    pub agent_id: AgentId,
    pub agent_name: String,
    pub capabilities: Vec<String>,
}

/// Message priority
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Priority {
    Low,
    Normal,
    High,
    Critical,
}

/// Message payload
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Payload {
    #[serde(rename = "type")]
    pub payload_type: String,
    pub data: serde_json::Value,
}

/// Message types
pub mod message_types {
    pub const TASK_ASSIGNMENT: &str = "task_assignment";
    pub const TASK_COMPLETED: &str = "task_completed";
    pub const STATUS_UPDATE: &str = "status_update";
    pub const REQUEST: &str = "request";
    pub const RESPONSE: &str = "response";
    pub const ERROR: &str = "error";
    pub const NEGOTIATION: &str = "negotiation";
    pub const ACKNOWLEDGMENT: &str = "acknowledgment";
}

impl A2aMessage {
    /// Create a new A2A message
    pub fn new(
        from_id: AgentId,
        from_name: String,
        to_id: AgentId,
        to_name: String,
        payload_type: String,
        data: serde_json::Value,
    ) -> Self {
        Self {
            envelope: A2aEnvelope {
                from: AgentInfo {
                    agent_id: from_id,
                    agent_name: from_name,
                    capabilities: vec![],
                },
                to: AgentInfo {
                    agent_id: to_id,
                    agent_name: to_name,
                    capabilities: vec![],
                },
                message_id: uuid::Uuid::new_v4().to_string(),
                correlation_id: None,
                timestamp: Utc::now(),
                priority: Priority::Normal,
                ttl: Some(3600),
            },
            payload: Payload {
                payload_type,
                data,
            },
        }
    }

    /// Check if message has expired
    pub fn is_expired(&self) -> bool {
        if let Some(ttl) = self.envelope.ttl {
            let elapsed = Utc::now().signed_duration_since(self.envelope.timestamp);
            elapsed.num_seconds() as u64 > ttl
        } else {
            false
        }
    }
}
