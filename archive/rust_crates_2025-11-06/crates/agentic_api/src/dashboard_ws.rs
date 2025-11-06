//! Real-Time Monitoring Dashboard with WebSocket support
//!
//! Provides real-time updates for:
//! - Agent execution monitoring
//! - Business opportunity pipeline
//! - Revenue metrics
//! - System health

use axum::{
    extract::{
        ws::{Message, WebSocket},
        WebSocketUpgrade,
        State,
    },
    response::IntoResponse,
    routing::get,
    Router,
};
use futures::{sink::SinkExt, stream::StreamExt};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tokio::sync::{broadcast, RwLock};
use std::collections::HashMap;
use uuid::Uuid;
use tracing::{info, warn, error};

/// Dashboard event types that are broadcast to connected clients
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum DashboardEvent {
    /// Agent execution started
    AgentExecutionStarted {
        agent_id: String,
        agent_name: String,
        task: String,
        timestamp: String,
    },

    /// Agent execution completed
    AgentExecutionCompleted {
        agent_id: String,
        agent_name: String,
        task: String,
        duration_ms: u64,
        success: bool,
        timestamp: String,
    },

    /// Business opportunity discovered
    OpportunityDiscovered {
        opportunity_id: String,
        title: String,
        description: String,
        score: f64,
        category: String,
        estimated_revenue: f64,
        timestamp: String,
    },

    /// Opportunity validation completed
    ValidationCompleted {
        opportunity_id: String,
        title: String,
        overall_score: f64,
        financial_viability: f64,
        technical_feasibility: f64,
        market_demand: f64,
        risk_level: String,
        recommendation: String,
        timestamp: String,
    },

    /// Product development started
    DevelopmentStarted {
        opportunity_id: String,
        title: String,
        features_count: usize,
        timestamp: String,
    },

    /// Product development completed
    DevelopmentCompleted {
        opportunity_id: String,
        title: String,
        deliverables_count: usize,
        duration_ms: u64,
        timestamp: String,
    },

    /// Revenue generated
    RevenueGenerated {
        opportunity_id: String,
        amount: f64,
        currency: String,
        source: String,
        timestamp: String,
    },

    /// System health update
    SystemHealth {
        agents_active: usize,
        agents_total: usize,
        opportunities_active: usize,
        cpu_usage: f64,
        memory_usage: f64,
        timestamp: String,
    },

    /// A2A message sent between agents
    A2aMessageSent {
        from_agent: String,
        to_agent: String,
        message_type: String,
        timestamp: String,
    },

    /// Workflow phase transition
    WorkflowPhaseTransition {
        workflow_id: String,
        from_phase: String,
        to_phase: String,
        timestamp: String,
    },
}

impl DashboardEvent {
    /// Create a new agent execution started event
    pub fn agent_started(agent_id: impl Into<String>, agent_name: impl Into<String>, task: impl Into<String>) -> Self {
        Self::AgentExecutionStarted {
            agent_id: agent_id.into(),
            agent_name: agent_name.into(),
            task: task.into(),
            timestamp: chrono::Utc::now().to_rfc3339(),
        }
    }

    /// Create a new agent execution completed event
    pub fn agent_completed(agent_id: impl Into<String>, agent_name: impl Into<String>, task: impl Into<String>, duration_ms: u64, success: bool) -> Self {
        Self::AgentExecutionCompleted {
            agent_id: agent_id.into(),
            agent_name: agent_name.into(),
            task: task.into(),
            duration_ms,
            success,
            timestamp: chrono::Utc::now().to_rfc3339(),
        }
    }

    /// Create a new opportunity discovered event
    pub fn opportunity_discovered(
        opportunity_id: impl Into<String>,
        title: impl Into<String>,
        description: impl Into<String>,
        score: f64,
        category: impl Into<String>,
        estimated_revenue: f64,
    ) -> Self {
        Self::OpportunityDiscovered {
            opportunity_id: opportunity_id.into(),
            title: title.into(),
            description: description.into(),
            score,
            category: category.into(),
            estimated_revenue,
            timestamp: chrono::Utc::now().to_rfc3339(),
        }
    }

    /// Create a new system health event
    pub fn system_health(agents_active: usize, agents_total: usize, opportunities_active: usize, cpu_usage: f64, memory_usage: f64) -> Self {
        Self::SystemHealth {
            agents_active,
            agents_total,
            opportunities_active,
            cpu_usage,
            memory_usage,
            timestamp: chrono::Utc::now().to_rfc3339(),
        }
    }
}

/// Dashboard state managing WebSocket connections and event broadcast
#[derive(Clone)]
pub struct DashboardState {
    /// Broadcast channel for sending events to all connected clients
    event_tx: broadcast::Sender<DashboardEvent>,

    /// Connected clients
    clients: Arc<RwLock<HashMap<Uuid, ClientInfo>>>,

    /// Event history (last 100 events)
    history: Arc<RwLock<Vec<DashboardEvent>>>,
}

#[derive(Debug, Clone)]
struct ClientInfo {
    id: Uuid,
    connected_at: chrono::DateTime<chrono::Utc>,
}

impl DashboardState {
    /// Create a new dashboard state
    pub fn new() -> Self {
        let (event_tx, _) = broadcast::channel(1000);

        Self {
            event_tx,
            clients: Arc::new(RwLock::new(HashMap::new())),
            history: Arc::new(RwLock::new(Vec::new())),
        }
    }

    /// Broadcast an event to all connected clients
    pub async fn broadcast(&self, event: DashboardEvent) {
        // Add to history
        let mut history = self.history.write().await;
        history.push(event.clone());

        // Keep only last 100 events
        if history.len() > 100 {
            history.remove(0);
        }
        drop(history);

        // Broadcast to all clients
        if let Err(e) = self.event_tx.send(event) {
            warn!("Failed to broadcast event: {}", e);
        }
    }

    /// Get recent event history
    pub async fn get_history(&self) -> Vec<DashboardEvent> {
        self.history.read().await.clone()
    }

    /// Get connected clients count
    pub async fn client_count(&self) -> usize {
        self.clients.read().await.len()
    }

    /// Register a new client
    async fn register_client(&self) -> Uuid {
        let id = Uuid::new_v4();
        let mut clients = self.clients.write().await;
        clients.insert(
            id,
            ClientInfo {
                id,
                connected_at: chrono::Utc::now(),
            },
        );
        info!("Dashboard client connected: {} (total: {})", id, clients.len());
        id
    }

    /// Unregister a client
    async fn unregister_client(&self, id: Uuid) {
        let mut clients = self.clients.write().await;
        clients.remove(&id);
        info!("Dashboard client disconnected: {} (remaining: {})", id, clients.len());
    }
}

impl Default for DashboardState {
    fn default() -> Self {
        Self::new()
    }
}

/// WebSocket handler for dashboard real-time updates
pub async fn dashboard_websocket_handler(
    ws: WebSocketUpgrade,
    State(state): State<DashboardState>,
) -> impl IntoResponse {
    ws.on_upgrade(move |socket| handle_socket(socket, state))
}

/// Handle individual WebSocket connection
async fn handle_socket(socket: WebSocket, state: DashboardState) {
    let client_id = state.register_client().await;

    let (mut sender, mut receiver) = socket.split();

    // Subscribe to event broadcast
    let mut event_rx = state.event_tx.subscribe();

    // Send recent history to newly connected client
    let history = state.get_history().await;
    for event in history {
        if let Ok(json) = serde_json::to_string(&event) {
            if sender.send(Message::Text(json)).await.is_err() {
                break;
            }
        }
    }

    // Spawn task to forward broadcast events to this client
    let mut send_task = tokio::spawn(async move {
        while let Ok(event) = event_rx.recv().await {
            if let Ok(json) = serde_json::to_string(&event) {
                if sender.send(Message::Text(json)).await.is_err() {
                    break;
                }
            }
        }
    });

    // Spawn task to handle incoming messages from client (heartbeat, etc.)
    let mut recv_task = tokio::spawn(async move {
        while let Some(Ok(msg)) = receiver.next().await {
            match msg {
                Message::Text(text) => {
                    info!("Received message from client: {}", text);
                    // Handle client commands if needed
                }
                Message::Close(_) => {
                    break;
                }
                _ => {}
            }
        }
    });

    // Wait for either task to complete
    tokio::select! {
        _ = (&mut send_task) => recv_task.abort(),
        _ = (&mut recv_task) => send_task.abort(),
    }

    // Cleanup
    state.unregister_client(client_id).await;
}

/// Get dashboard statistics
#[derive(Serialize)]
pub struct DashboardStats {
    pub connected_clients: usize,
    pub total_events: usize,
    pub recent_events: Vec<DashboardEvent>,
}

pub async fn get_dashboard_stats(
    State(state): State<DashboardState>,
) -> axum::Json<DashboardStats> {
    let stats = DashboardStats {
        connected_clients: state.client_count().await,
        total_events: state.history.read().await.len(),
        recent_events: state.get_history().await.into_iter().rev().take(10).collect(),
    };
    axum::Json(stats)
}

/// Broadcast a system health update
pub async fn broadcast_system_health(
    State(state): State<DashboardState>,
    Json(health): Json<SystemHealthData>,
) -> axum::Json<bool> {
    let event = DashboardEvent::system_health(
        health.agents_active,
        health.agents_total,
        health.opportunities_active,
        health.cpu_usage,
        health.memory_usage,
    );
    state.broadcast(event).await;
    axum::Json(true)
}

#[derive(serde::Deserialize, serde::Serialize)]
pub struct SystemHealthData {
    pub agents_active: usize,
    pub agents_total: usize,
    pub opportunities_active: usize,
    pub cpu_usage: f64,
    pub memory_usage: f64,
}

/// Create dashboard routes
pub fn create_dashboard_routes(state: DashboardState) -> Router {
    Router::new()
        .route("/ws", get(dashboard_websocket_handler))
        .route("/stats", get(get_dashboard_stats))
        .route("/health", axum::routing::post(broadcast_system_health))
        .with_state(state)
}

/// Helper function to broadcast events from anywhere in the application
pub async fn broadcast_event(state: &DashboardState, event: DashboardEvent) {
    state.broadcast(event).await;
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_dashboard_state_creation() {
        let state = DashboardState::new();
        assert_eq!(state.client_count().await, 0);
        assert_eq!(state.get_history().await.len(), 0);
    }

    #[tokio::test]
    async fn test_event_broadcast() {
        let state = DashboardState::new();

        let event = DashboardEvent::agent_started("agent-1", "Test Agent", "Test Task");
        state.broadcast(event).await;

        let history = state.get_history().await;
        assert_eq!(history.len(), 1);
    }

    #[tokio::test]
    async fn test_history_limit() {
        let state = DashboardState::new();

        // Add 150 events
        for i in 0..150 {
            let event = DashboardEvent::agent_started(
                format!("agent-{}", i),
                "Test Agent",
                "Test Task"
            );
            state.broadcast(event).await;
        }

        // Should keep only last 100
        let history = state.get_history().await;
        assert_eq!(history.len(), 100);
    }
}
