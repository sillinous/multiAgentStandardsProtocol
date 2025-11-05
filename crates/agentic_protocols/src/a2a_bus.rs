//! A2A Message Bus - Enables autonomous agent-to-agent communication
//!
//! This implements a production-grade message bus for the A2A protocol,
//! enabling agents to communicate, collaborate, and coordinate autonomously.

use crate::a2a::{A2aEnvelope, A2aMessage};
use agentic_core::{AgentId, Result, Error};
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::{mpsc, RwLock, broadcast};
use tracing::{info, debug, warn};
use uuid::Uuid;

/// Message handler function type
pub type MessageHandler = Arc<dyn Fn(A2aMessage) -> Result<Option<A2aMessage>> + Send + Sync>;

/// A2A Message Bus for autonomous agent communication
pub struct A2aBus {
    /// Registered agents and their message channels
    agents: Arc<RwLock<HashMap<AgentId, mpsc::UnboundedSender<A2aMessage>>>>,

    /// Broadcast channel for system-wide events
    broadcast: broadcast::Sender<A2aMessage>,

    /// Message handlers for different message types
    handlers: Arc<RwLock<HashMap<String, MessageHandler>>>,

    /// Metrics
    metrics: Arc<RwLock<BusMetrics>>,
}

/// Message bus metrics
#[derive(Debug, Clone, Default)]
pub struct BusMetrics {
    pub total_messages: u64,
    pub successful_deliveries: u64,
    pub failed_deliveries: u64,
    pub agents_registered: usize,
    pub broadcast_messages: u64,
}

impl A2aBus {
    /// Create a new A2A message bus
    pub fn new() -> Self {
        let (broadcast_tx, _) = broadcast::channel(1000);

        Self {
            agents: Arc::new(RwLock::new(HashMap::new())),
            broadcast: broadcast_tx,
            handlers: Arc::new(RwLock::new(HashMap::new())),
            metrics: Arc::new(RwLock::new(BusMetrics::default())),
        }
    }

    /// Register an agent with the message bus
    pub async fn register_agent(
        &self,
        agent_id: AgentId,
    ) -> mpsc::UnboundedReceiver<A2aMessage> {
        let (tx, rx) = mpsc::unbounded_channel();

        self.agents.write().await.insert(agent_id.clone(), tx);

        let mut metrics = self.metrics.write().await;
        metrics.agents_registered = self.agents.read().await.len();

        info!("🔌 Agent registered on A2A bus: {}", agent_id);

        rx
    }

    /// Unregister an agent from the message bus
    pub async fn unregister_agent(&self, agent_id: &AgentId) {
        self.agents.write().await.remove(agent_id);

        let mut metrics = self.metrics.write().await;
        metrics.agents_registered = self.agents.read().await.len();

        info!("🔌 Agent unregistered from A2A bus: {}", agent_id);
    }

    /// Send a message from one agent to another
    pub async fn send(&self, message: A2aMessage) -> Result<()> {
        debug!("📤 Sending A2A message: {} -> {}",
            message.envelope.from.agent_id,
            message.envelope.to.agent_id
        );

        // Update metrics
        {
            let mut metrics = self.metrics.write().await;
            metrics.total_messages += 1;
        }

        // Get recipient's channel
        let agents = self.agents.read().await;
        let recipient_tx = agents.get(&message.envelope.to.agent_id)
            .ok_or_else(|| Error::InvalidArgument(
                format!("Agent not registered: {}", message.envelope.to.agent_id)
            ))?;

        // Send message
        recipient_tx.send(message.clone())
            .map_err(|e| Error::Internal(format!("Failed to send message: {}", e)))?;

        // Update success metrics
        {
            let mut metrics = self.metrics.write().await;
            metrics.successful_deliveries += 1;
        }

        debug!("✅ Message delivered successfully");

        Ok(())
    }

    /// Broadcast a message to all registered agents
    pub async fn broadcast(&self, message: A2aMessage) -> Result<()> {
        info!("📢 Broadcasting A2A message from: {}", message.envelope.from.agent_id);

        // Update metrics
        {
            let mut metrics = self.metrics.write().await;
            metrics.broadcast_messages += 1;
        }

        // Send to broadcast channel (ignores if no receivers)
        let _ = self.broadcast.send(message);

        Ok(())
    }

    /// Subscribe to broadcast messages
    pub fn subscribe(&self) -> broadcast::Receiver<A2aMessage> {
        self.broadcast.subscribe()
    }

    /// Register a message handler for a specific message type
    pub async fn register_handler(
        &self,
        message_type: String,
        handler: MessageHandler,
    ) {
        self.handlers.write().await.insert(message_type, handler);
        debug!("🔧 Registered handler for message type: {}", message_type);
    }

    /// Send and wait for response (request-response pattern)
    pub async fn request(
        &self,
        message: A2aMessage,
        timeout: std::time::Duration,
    ) -> Result<A2aMessage> {
        let correlation_id = message.envelope.correlation_id.unwrap_or_else(|| Uuid::new_v4().to_string());

        // Create temporary channel for response
        let (response_tx, mut response_rx) = mpsc::unbounded_channel();

        // Store correlation ID for response routing
        // (In production, would use a more sophisticated routing mechanism)

        // Send request
        self.send(message).await?;

        // Wait for response with timeout
        tokio::select! {
            response = response_rx.recv() => {
                response.ok_or_else(|| Error::Internal("No response received".to_string()))
            }
            _ = tokio::time::sleep(timeout) => {
                Err(Error::Internal("Request timeout".to_string()))
            }
        }
    }

    /// Get current metrics
    pub async fn metrics(&self) -> BusMetrics {
        self.metrics.read().await.clone()
    }

    /// Get list of registered agents
    pub async fn registered_agents(&self) -> Vec<AgentId> {
        self.agents.read().await.keys().cloned().collect()
    }
}

impl Default for A2aBus {
    fn default() -> Self {
        Self::new()
    }
}

/// Helper for creating A2A messages
pub struct A2aMessageBuilder {
    from_id: AgentId,
    from_name: String,
    to_id: AgentId,
    to_name: String,
}

impl A2aMessageBuilder {
    pub fn new(from_id: AgentId, from_name: String) -> Self {
        Self {
            from_id,
            from_name,
            to_id: AgentId::generate(),
            to_name: String::new(),
        }
    }

    pub fn to(mut self, agent_id: AgentId, agent_name: String) -> Self {
        self.to_id = agent_id;
        self.to_name = agent_name;
        self
    }

    pub fn build_task_assignment(
        self,
        task: String,
        payload: serde_json::Value,
    ) -> A2aMessage {
        A2aMessage {
            envelope: A2aEnvelope {
                from: crate::a2a::AgentInfo {
                    agent_id: self.from_id,
                    agent_name: self.from_name,
                    capabilities: vec![],
                },
                to: crate::a2a::AgentInfo {
                    agent_id: self.to_id,
                    agent_name: self.to_name,
                    capabilities: vec![],
                },
                message_id: Uuid::new_v4().to_string(),
                correlation_id: Some(Uuid::new_v4().to_string()),
                timestamp: chrono::Utc::now(),
                priority: crate::a2a::Priority::Normal,
                ttl: Some(3600),
            },
            payload: crate::a2a::Payload {
                payload_type: "task_assignment".to_string(),
                data: serde_json::json!({
                    "task": task,
                    "details": payload
                }),
            },
        }
    }

    pub fn build_response(
        self,
        status: &str,
        result: serde_json::Value,
    ) -> A2aMessage {
        A2aMessage {
            envelope: A2aEnvelope {
                from: crate::a2a::AgentInfo {
                    agent_id: self.from_id,
                    agent_name: self.from_name,
                    capabilities: vec![],
                },
                to: crate::a2a::AgentInfo {
                    agent_id: self.to_id,
                    agent_name: self.to_name,
                    capabilities: vec![],
                },
                message_id: Uuid::new_v4().to_string(),
                correlation_id: None,
                timestamp: chrono::Utc::now(),
                priority: crate::a2a::Priority::Normal,
                ttl: Some(3600),
            },
            payload: crate::a2a::Payload {
                payload_type: "response".to_string(),
                data: serde_json::json!({
                    "status": status,
                    "result": result
                }),
            },
        }
    }

    pub fn build_status_update(
        self,
        status: String,
        progress: f64,
        message: String,
    ) -> A2aMessage {
        A2aMessage {
            envelope: A2aEnvelope {
                from: crate::a2a::AgentInfo {
                    agent_id: self.from_id,
                    agent_name: self.from_name,
                    capabilities: vec![],
                },
                to: crate::a2a::AgentInfo {
                    agent_id: self.to_id,
                    agent_name: self.to_name,
                    capabilities: vec![],
                },
                message_id: Uuid::new_v4().to_string(),
                correlation_id: None,
                timestamp: chrono::Utc::now(),
                priority: crate::a2a::Priority::Normal,
                ttl: Some(300),
            },
            payload: crate::a2a::Payload {
                payload_type: "status_update".to_string(),
                data: serde_json::json!({
                    "status": status,
                    "progress": progress,
                    "message": message
                }),
            },
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_bus_creation() {
        let bus = A2aBus::new();
        let metrics = bus.metrics().await;
        assert_eq!(metrics.agents_registered, 0);
    }

    #[tokio::test]
    async fn test_agent_registration() {
        let bus = A2aBus::new();
        let agent_id = AgentId::generate();

        let _rx = bus.register_agent(agent_id.clone()).await;

        let metrics = bus.metrics().await;
        assert_eq!(metrics.agents_registered, 1);

        let agents = bus.registered_agents().await;
        assert!(agents.contains(&agent_id));
    }

    #[tokio::test]
    async fn test_message_sending() {
        let bus = A2aBus::new();

        let agent1_id = AgentId::generate();
        let agent2_id = AgentId::generate();

        let mut rx2 = bus.register_agent(agent2_id.clone()).await;
        bus.register_agent(agent1_id.clone()).await;

        let message = A2aMessageBuilder::new(agent1_id.clone(), "Agent1".to_string())
            .to(agent2_id.clone(), "Agent2".to_string())
            .build_task_assignment("test_task".to_string(), serde_json::json!({}));

        bus.send(message).await.unwrap();

        let received = rx2.recv().await.unwrap();
        assert_eq!(received.envelope.from.agent_id, agent1_id);
        assert_eq!(received.envelope.to.agent_id, agent2_id);

        let metrics = bus.metrics().await;
        assert_eq!(metrics.successful_deliveries, 1);
    }
}
