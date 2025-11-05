//! Opportunity Discovery System
//!
//! This module contains agents that work together to discover, analyze, and rank
//! market opportunities based on user preferences.

pub mod market_research_agent;
pub mod trend_analysis_agent;
pub mod competitor_analysis_agent;
pub mod opportunity_evaluation_agent;
pub mod discovery_manager;

pub use market_research_agent::MarketResearchAgent;
pub use trend_analysis_agent::TrendAnalysisAgent;
pub use competitor_analysis_agent::CompetitorAnalysisAgent;
pub use opportunity_evaluation_agent::OpportunityEvaluationAgent;
pub use discovery_manager::OpportunityDiscoveryManager;
