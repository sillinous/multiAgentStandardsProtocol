//! Revenue Generation System
//!
//! Complete autonomous revenue generation from monetization to optimization.
//!
//! # Architecture
//!
//! The revenue generation system consists of 5 specialist agents orchestrated by a meta-agent:
//!
//! ## Agents
//!
//! 1. **MonetizationAgent**: Payment setup, pricing strategy, billing configuration
//! 2. **MarketingAgent**: Campaigns, SEO, content generation, growth hacking
//! 3. **DeploymentAgent**: Production deployment, infrastructure, monitoring
//! 4. **AnalyticsAgent**: Business metrics tracking, performance monitoring
//! 5. **OptimizationAgent**: Continuous improvement, A/B testing, revenue optimization
//!
//! ## Meta-Agent
//!
//! **RevenueGenerationManager**: Orchestrates all 5 agents to execute the complete
//! revenue generation workflow from monetization setup to continuous optimization.
//!
//! # Workflow
//!
//! The complete revenue generation workflow:
//!
//! ```text
//! 1. Monetization Setup (20%)
//!    └── Payment provider selection
//!    └── Pricing model determination
//!    └── Price point calculation
//!    └── Billing configuration
//!
//! 2. Marketing Launch (30%)
//!    └── Channel selection
//!    └── Campaign creation
//!    └── Content generation
//!    └── SEO optimization
//!
//! 3. Production Deployment (20%)
//!    └── Hosting provider selection
//!    └── Infrastructure provisioning
//!    └── SSL/domain setup
//!    └── Monitoring configuration
//!
//! 4. Analytics Tracking (15%)
//!    └── Metrics setup
//!    └── Performance tracking
//!    └── Customer analytics
//!    └── Revenue monitoring
//!
//! 5. Continuous Optimization (15%)
//!    └── Performance analysis
//!    └── Optimization recommendations
//!    └── A/B testing
//!    └── Revenue maximization
//! ```
//!
//! # Example Usage
//!
//! ```rust,no_run
//! use agentic_business::revenue::RevenueGenerationManager;
//! use agentic_business::models::Opportunity;
//! use agentic_runtime::llm::LlmClient;
//! use std::sync::Arc;
//!
//! #[tokio::main]
//! async fn main() -> Result<(), Box<dyn std::error::Error>> {
//!     // Create LLM client
//!     let llm_client: Arc<dyn LlmClient> = /* ... */;
//!
//!     // Create revenue manager
//!     let mut manager = RevenueGenerationManager::new(llm_client);
//!
//!     // Opportunity (from discovery + validation + development)
//!     let opportunity = /* ... */;
//!     let validation_report = /* ... */;
//!     let development_result = /* ... */;
//!
//!     // Generate revenue
//!     let result = manager.generate_revenue(
//!         &opportunity,
//!         &validation_report,
//!         &development_result,
//!         1000.0, // Marketing budget
//!     ).await?;
//!
//!     println!("💰 Expected Monthly Revenue: ${:.2}", result.analytics.mrr);
//!     println!("📈 Expected Annual Revenue: ${:.2}", result.analytics.arr);
//!     println!("📊 ROI: {:.1}%", result.roi * 100.0);
//!
//!     // Track actual revenue over time
//!     manager.track_revenue(&mut result, 5000.0, 100).await?;
//!
//!     Ok(())
//! }
//! ```
//!
//! # Features
//!
//! - **Multi-Provider Payment Support**: Stripe, PayPal, Square, Paddle
//! - **Flexible Pricing Models**: Subscription, one-time, usage, freemium, tiered
//! - **Multi-Channel Marketing**: Google Ads, Facebook, LinkedIn, SEO, content
//! - **Cloud Deployment**: AWS, Google Cloud, Azure, Vercel, Netlify, etc.
//! - **Comprehensive Analytics**: Revenue, customers, churn, engagement, conversion
//! - **AI-Driven Optimization**: Continuous improvement recommendations
//!
//! # Standards Compliance
//!
//! All agents are configured to be standards-compliant:
//! - **A2A Protocol** (Agent-to-Agent communication)
//! - **MCP Protocol** (Model Context Protocol)
//! - Standards-compliant capabilities and protocols
//!
//! # Performance
//!
//! - **Parallel Execution**: Agents run concurrently where possible
//! - **Fast Workflow**: Complete revenue setup in seconds
//! - **Scalable**: Handles multiple opportunities simultaneously
//! - **Observable**: Comprehensive metrics and logging

pub mod models;
pub mod monetization_agent;
pub mod marketing_agent;
pub mod deployment_agent;
pub mod analytics_agent;
pub mod optimization_agent;
pub mod revenue_manager;

// Re-export main types
pub use models::*;
pub use monetization_agent::MonetizationAgent;
pub use marketing_agent::MarketingAgent;
pub use deployment_agent::DeploymentAgent;
pub use analytics_agent::AnalyticsAgent;
pub use optimization_agent::OptimizationAgent;
pub use revenue_manager::RevenueGenerationManager;

/// Quick-start helper to create a complete revenue generation manager
pub fn create_revenue_manager(llm_client: std::sync::Arc<dyn agentic_runtime::llm::LlmClient>) -> RevenueGenerationManager {
    RevenueGenerationManager::new(llm_client)
}
