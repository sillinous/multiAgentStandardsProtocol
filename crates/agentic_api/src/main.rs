//! Main entry point for the Agentic API server

use agentic_api::{AppState, router};
use tower_http::cors::{Any, CorsLayer};
use std::net::SocketAddr;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

#[tokio::main]
async fn main() {
    // Initialize tracing
    tracing_subscriber::registry()
        .with(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "agentic_api=info,tower_http=debug".into()),
        )
        .with(tracing_subscriber::fmt::layer())
        .init();

    // Create application state
    let state = AppState::new();

    // Configure CORS
    let cors = CorsLayer::new()
        .allow_origin(Any)
        .allow_methods(Any)
        .allow_headers(Any);

    // Build router with middleware
    let app = router(state).layer(cors);

    // Start server
    let addr: SocketAddr = "127.0.0.1:8080".parse().unwrap();
    tracing::info!("🚀 Agentic API server starting on http://{}", addr);
    tracing::info!("📊 Dashboard available at http://{}", addr);
    tracing::info!("📖 API endpoints:");
    tracing::info!("   GET  /api/health - Health check");
    tracing::info!("   GET  /api/agents - List all agents");
    tracing::info!("   POST /api/agents - Create new agent");
    tracing::info!("   POST /api/workflows - Create workflow");

    let listener = tokio::net::TcpListener::bind(addr)
        .await
        .expect("Failed to bind to address");

    axum::serve(listener, app)
        .await
        .expect("Server error");
}


