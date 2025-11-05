//! Business API endpoints - Opportunity discovery, validation, and revenue generation

use axum::{
    extract::{Path, State},
    http::StatusCode,
    Json,
};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tokio::sync::Mutex;
use tracing::{info, error};

use agentic_business::{
    opportunity::OpportunityDiscoveryManager,
    models::{Opportunity, UserPreferences, OpportunityId},
};
use agentic_runtime::llm::LlmClient;

/// Shared state for business operations
pub struct BusinessState {
    pub llm_client: Arc<dyn LlmClient>,
    pub discovery_manager: Arc<Mutex<OpportunityDiscoveryManager>>,
    pub discovered_opportunities: Arc<Mutex<Vec<Opportunity>>>,
}

impl BusinessState {
    pub fn new(llm_client: Arc<dyn LlmClient>) -> Self {
        let discovery_manager = OpportunityDiscoveryManager::new(llm_client.clone());

        Self {
            llm_client,
            discovery_manager: Arc::new(Mutex::new(discovery_manager)),
            discovered_opportunities: Arc::new(Mutex::new(Vec::new())),
        }
    }
}

// ============================================================================
// Request/Response Types
// ============================================================================

#[derive(Debug, Serialize, Deserialize)]
pub struct DiscoverOpportunitiesRequest {
    pub preferences: UserPreferences,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct DiscoverOpportunitiesResponse {
    pub opportunities: Vec<Opportunity>,
    pub count: usize,
    pub workflow_id: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct OpportunityDetailsResponse {
    pub opportunity: Opportunity,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct OpportunityListResponse {
    pub opportunities: Vec<Opportunity>,
    pub total: usize,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct StartDevelopmentRequest {
    pub opportunity_id: OpportunityId,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct StartDevelopmentResponse {
    pub workflow_id: String,
    pub status: String,
    pub message: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct BusinessMetricsResponse {
    pub total_opportunities_discovered: usize,
    pub total_products_developed: usize,
    pub total_revenue_generated: f64,
    pub active_workflows: usize,
}

// ============================================================================
// API Handlers
// ============================================================================

/// POST /api/business/discover
/// Discover market opportunities based on user preferences
pub async fn api_discover_opportunities(
    State(state): State<Arc<BusinessState>>,
    Json(req): Json<DiscoverOpportunitiesRequest>,
) -> Result<Json<DiscoverOpportunitiesResponse>, (StatusCode, String)> {
    info!("API: Discovering opportunities with preferences: {:?}", req.preferences);

    let mut manager = state.discovery_manager.lock().await;

    match manager.discover(req.preferences).await {
        Ok(opportunities) => {
            let count = opportunities.len();
            let workflow_id = manager.workflow_id().to_string();

            // Store discovered opportunities
            let mut stored = state.discovered_opportunities.lock().await;
            stored.extend(opportunities.clone());

            info!("Successfully discovered {} opportunities", count);

            Ok(Json(DiscoverOpportunitiesResponse {
                opportunities,
                count,
                workflow_id,
            }))
        }
        Err(e) => {
            error!("Failed to discover opportunities: {}", e);
            Err((
                StatusCode::INTERNAL_SERVER_ERROR,
                format!("Discovery failed: {}", e),
            ))
        }
    }
}

/// GET /api/business/opportunities
/// List all discovered opportunities
pub async fn api_list_opportunities(
    State(state): State<Arc<BusinessState>>,
) -> Json<OpportunityListResponse> {
    let opportunities = state.discovered_opportunities.lock().await;

    Json(OpportunityListResponse {
        total: opportunities.len(),
        opportunities: opportunities.clone(),
    })
}

/// GET /api/business/opportunities/:id
/// Get details for a specific opportunity
pub async fn api_get_opportunity(
    State(state): State<Arc<BusinessState>>,
    Path(id): Path<String>,
) -> Result<Json<OpportunityDetailsResponse>, (StatusCode, String)> {
    let opportunities = state.discovered_opportunities.lock().await;

    // Parse ID
    let opportunity_id = id.parse::<OpportunityId>()
        .map_err(|_| (StatusCode::BAD_REQUEST, "Invalid opportunity ID".to_string()))?;

    // Find opportunity
    let opportunity = opportunities
        .iter()
        .find(|opp| opp.id == opportunity_id)
        .ok_or_else(|| (StatusCode::NOT_FOUND, "Opportunity not found".to_string()))?;

    Ok(Json(OpportunityDetailsResponse {
        opportunity: opportunity.clone(),
    }))
}

/// POST /api/business/opportunities/:id/develop
/// Start development workflow for an opportunity
pub async fn api_start_development(
    State(state): State<Arc<BusinessState>>,
    Path(id): Path<String>,
    Json(_req): Json<StartDevelopmentRequest>,
) -> Result<Json<StartDevelopmentResponse>, (StatusCode, String)> {
    info!("API: Starting development for opportunity {}", id);

    let opportunity_id = id.parse::<OpportunityId>()
        .map_err(|_| (StatusCode::BAD_REQUEST, "Invalid opportunity ID".to_string()))?;

    // Find opportunity
    let opportunities = state.discovered_opportunities.lock().await;
    let _opportunity = opportunities
        .iter()
        .find(|opp| opp.id == opportunity_id)
        .ok_or_else(|| (StatusCode::NOT_FOUND, "Opportunity not found".to_string()))?;

    // TODO: Integrate with ProductDevelopmentManager (Phase 3)

    Ok(Json(StartDevelopmentResponse {
        workflow_id: uuid::Uuid::new_v4().to_string(),
        status: "initiated".to_string(),
        message: "Development workflow started (Phase 3 - coming soon)".to_string(),
    }))
}

/// DELETE /api/business/opportunities/:id
/// Remove an opportunity from the list
pub async fn api_delete_opportunity(
    State(state): State<Arc<BusinessState>>,
    Path(id): Path<String>,
) -> Result<StatusCode, (StatusCode, String)> {
    let opportunity_id = id.parse::<OpportunityId>()
        .map_err(|_| (StatusCode::BAD_REQUEST, "Invalid opportunity ID".to_string()))?;

    let mut opportunities = state.discovered_opportunities.lock().await;

    let initial_len = opportunities.len();
    opportunities.retain(|opp| opp.id != opportunity_id);

    if opportunities.len() < initial_len {
        Ok(StatusCode::NO_CONTENT)
    } else {
        Err((StatusCode::NOT_FOUND, "Opportunity not found".to_string()))
    }
}

/// GET /api/business/metrics
/// Get business metrics and statistics
pub async fn api_business_metrics(
    State(state): State<Arc<BusinessState>>,
) -> Json<BusinessMetricsResponse> {
    let opportunities = state.discovered_opportunities.lock().await;

    Json(BusinessMetricsResponse {
        total_opportunities_discovered: opportunities.len(),
        total_products_developed: 0, // TODO: Track this
        total_revenue_generated: 0.0, // TODO: Track this
        active_workflows: 0, // TODO: Track this
    })
}

/// GET /api/business/discovery/status
/// Get status of the discovery manager
pub async fn api_discovery_status(
    State(state): State<Arc<BusinessState>>,
) -> Json<serde_json::Value> {
    let manager = state.discovery_manager.lock().await;
    let metrics = manager.metrics();

    serde_json::json!({
        "workflow_id": manager.workflow_id().to_string(),
        "tasks_executed": metrics.tasks_executed,
        "avg_execution_time_ms": metrics.avg_execution_time_ms,
        "status": "operational"
    })
}

// ============================================================================
// Route Registration
// ============================================================================

use axum::routing::{get, post, delete};
use axum::Router;

/// Create business routes
pub fn create_business_routes(state: Arc<BusinessState>) -> Router {
    Router::new()
        // Discovery
        .route("/business/discover", post(api_discover_opportunities))
        .route("/business/opportunities", get(api_list_opportunities))
        .route("/business/opportunities/:id", get(api_get_opportunity))
        .route("/business/opportunities/:id", delete(api_delete_opportunity))
        .route("/business/opportunities/:id/develop", post(api_start_development))

        // Metrics and status
        .route("/business/metrics", get(api_business_metrics))
        .route("/business/discovery/status", get(api_discovery_status))

        .with_state(state)
}

#[cfg(test)]
mod tests {
    use super::*;
    use agentic_runtime::llm::MockLlmClient;

    #[test]
    fn test_business_state_creation() {
        let llm = Arc::new(MockLlmClient::new());
        let state = BusinessState::new(llm);
        assert_eq!(state.discovered_opportunities.blocking_lock().len(), 0);
    }
}
