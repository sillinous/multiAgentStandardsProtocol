//! Agentic Business - Autonomous Business-to-Revenue Agent System
//!
//! This crate provides a complete ecosystem of specialized agents that work together to:
//! - Discover market opportunities from multiple sources
//! - Analyze and validate business ideas
//! - Develop complete products/services/apps
//! - Generate revenue through autonomous deployment and marketing
//!
//! # Architecture
//!
//! The system is organized into four main subsystems, each managed by a meta-agent:
//!
//! ## 1. Opportunity Discovery
//! - `MarketResearchAgent`: Discovers opportunities from APIs, web scraping, trends
//! - `TrendAnalysisAgent`: Analyzes market trends and growth patterns
//! - `CompetitorAnalysisAgent`: Studies competitive landscape
//! - `OpportunityEvaluationAgent`: Multi-dimensional scoring
//! - `OpportunityDiscoveryManager`: Orchestrates the discovery process
//!
//! ## 2. Business Validation
//! - `FinancialAnalysisAgent`: ROI calculations, revenue projections
//! - `TechnicalFeasibilityAgent`: Implementation complexity assessment
//! - `MarketDemandAgent`: Demand validation
//! - `RiskAssessmentAgent`: Risk identification and mitigation
//! - `BusinessValidationManager`: Orchestrates validation
//!
//! ## 3. Product Development
//! - `UIUXDesignAgent`: Generates UI/UX designs
//! - `InfrastructureAgent`: Cloud provisioning
//! - Integrates with existing `SDLCManager` for code generation
//! - `ProductDevelopmentManager`: End-to-end product creation
//!
//! ## 4. Revenue Generation
//! - `MonetizationAgent`: Payment setup, pricing strategy
//! - `MarketingAgent`: Campaigns, SEO, content
//! - `DeploymentAgent`: Production deployment
//! - `AnalyticsAgent`: Business metrics tracking
//! - `OptimizationAgent`: Continuous improvement
//! - `RevenueGenerationManager`: Orchestrates revenue generation
//!
//! # Example Usage
//!
//! ```rust,no_run
//! use agentic_business::opportunity::OpportunityDiscoveryManager;
//! use agentic_business::models::UserPreferences;
//!
//! #[tokio::main]
//! async fn main() -> Result<(), Box<dyn std::error::Error>> {
//!     // User configures preferences
//!     let preferences = UserPreferences {
//!         domain: Some("SaaS".to_string()),
//!         min_investment: Some(1000.0),
//!         max_time_to_market_days: Some(30),
//!         revenue_type: vec!["subscription".to_string(), "passive".to_string()],
//!         ..Default::default()
//!     };
//!
//!     // Discover opportunities
//!     let manager = OpportunityDiscoveryManager::new(llm_client);
//!     let opportunities = manager.discover(preferences).await?;
//!
//!     // User selects opportunity
//!     let selected = &opportunities[0];
//!
//!     // Full autonomous development and revenue generation happens here...
//!
//!     Ok(())
//! }
//! ```

pub mod models;
pub mod opportunity;
pub mod validation;
pub mod development;
pub mod revenue;

// Re-export main types
pub use models::{
    Opportunity, MultiDimensionalScore, UserPreferences,
    FinancialProjection, CompetitiveAnalysis,
};
pub use opportunity::{
    OpportunityDiscoveryManager,
    MarketResearchAgent,
    TrendAnalysisAgent,
};
pub use revenue::{
    RevenueGenerationManager,
    MonetizationAgent,
    MarketingAgent,
    DeploymentAgent,
    AnalyticsAgent,
    OptimizationAgent,
};

/// Configure an agent to be standards-compliant according to agentic_standards
///
/// This function sets up the required protocol and capability flags in the agent's
/// config HashMap to comply with the standard worker template:
/// - Protocol: A2A (Agent-to-Agent communication) - Recommended
/// - Protocol: MCP (Model Context Protocol) - Required
/// - Capability: mcp.tools - Required
/// - Capability: a2a.messaging - Recommended
///
/// # Example
///
/// ```rust,no_run
/// use agentic_core::{Agent, AgentRole};
/// use agentic_business::configure_standards_compliant_agent;
///
/// let mut agent = Agent::new(
///     "MyAgent",
///     "Description",
///     AgentRole::Worker,
///     "claude-3-5-sonnet-20241022",
///     "anthropic",
/// );
///
/// // Make agent standards-compliant
/// configure_standards_compliant_agent(&mut agent);
/// ```
pub fn configure_standards_compliant_agent(agent: &mut agentic_core::Agent) {
    // A2A Protocol (Agent-to-Agent communication)
    // Level: Recommended
    // Enables agent-to-agent messaging via A2A protocol
    agent.config.insert(
        "protocol:a2a".to_string(),
        serde_json::json!("1.0")
    );

    // MCP Protocol (Model Context Protocol)
    // Level: Required
    // Enables model context protocol for tool exposure
    agent.config.insert(
        "protocol:mcp".to_string(),
        serde_json::json!("1.0")
    );

    // Capability: MCP Tools
    // Level: Required
    // Indicates agent can expose and use MCP tools
    agent.config.insert(
        "cap:mcp.tools".to_string(),
        serde_json::json!("1.0.0")
    );

    // Capability: A2A Messaging
    // Level: Recommended
    // Indicates agent can send/receive A2A messages
    agent.config.insert(
        "cap:a2a.messaging".to_string(),
        serde_json::json!("1.0.0")
    );

    // Capability: Business Domain
    // Custom capability for business agents
    agent.config.insert(
        "cap:business.analysis".to_string(),
        serde_json::json!("1.0.0")
    );
}
