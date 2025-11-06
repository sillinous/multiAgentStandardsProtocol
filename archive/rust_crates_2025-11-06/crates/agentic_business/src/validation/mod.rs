//! Business Validation System
//!
//! Comprehensive validation framework with 4 specialized agents coordinated by a meta-agent.
//!
//! # Architecture
//!
//! ```
//! BusinessValidationManager (Meta-Agent)
//! ├── FinancialAnalysisAgent
//! │   ├── Revenue projections
//! │   ├── ROI & cash flow analysis
//! │   ├── Break-even analysis
//! │   └── Funding requirements
//! ├── TechnicalFeasibilityAgent
//! │   ├── Tech stack recommendation
//! │   ├── Implementation complexity
//! │   ├── Technical risks
//! │   └── Scalability assessment
//! ├── MarketDemandAgent
//! │   ├── Target market (TAM/SAM/SOM)
//! │   ├── Customer segmentation
//! │   ├── Demand indicators
//! │   └── Adoption forecasting
//! └── RiskAssessmentAgent
//!     ├── Market risks
//!     ├── Financial risks
//!     ├── Operational risks
//!     ├── Technical risks
//!     ├── Competitive risks
//!     └── Regulatory risks
//! ```
//!
//! # Usage Example
//!
//! ```no_run
//! use agentic_business::validation::BusinessValidationManager;
//! use agentic_business::models::Opportunity;
//! use agentic_runtime::llm::MockLlmClient;
//! use std::sync::Arc;
//!
//! # async fn example() -> Result<(), Box<dyn std::error::Error>> {
//! let llm_client = Arc::new(MockLlmClient::new());
//! let mut manager = BusinessValidationManager::new(llm_client);
//!
//! let opportunity = Opportunity::new(
//!     "AI SaaS Platform".to_string(),
//!     "AI-powered business automation".to_string(),
//!     "SaaS".to_string(),
//!     agentic_business::models::ProductType::SaaS,
//! );
//!
//! // Perform comprehensive validation
//! let report = manager.validate(&opportunity).await?;
//!
//! println!("Overall Score: {:.1}/10", report.overall_validation_score);
//! println!("Recommendation: {:?}", report.recommendation);
//! println!("Confidence: {:.0}%", report.confidence_level * 100.0);
//! # Ok(())
//! # }
//! ```

pub mod financial_analysis_agent;
pub mod technical_feasibility_agent;
pub mod market_demand_agent;
pub mod risk_assessment_agent;
pub mod validation_manager;

// Re-export main types
pub use financial_analysis_agent::{
    FinancialAnalysisAgent,
    FinancialAnalysisReport,
    FinancialRecommendation,
    RevenueProjection,
    ROIAnalysis,
    CostBreakdown,
    CashFlowAnalysis,
    BreakEvenAnalysis,
    FundingRequirements,
};

pub use technical_feasibility_agent::{
    TechnicalFeasibilityAgent,
    TechnicalFeasibilityReport,
    TechnicalRecommendation,
    ImplementationComplexity,
    TechnicalRisk,
    RiskSeverity,
    ResourceRequirements,
    ScalabilityAssessment,
    SecurityConsideration,
};

pub use market_demand_agent::{
    MarketDemandAgent,
    MarketDemandReport,
    DemandRecommendation,
    TargetMarket,
    CustomerSegment,
    DemandIndicator,
    MarketTrendAnalysis,
    CompetitiveDemand,
    AdoptionForecast,
    TrendDirection,
    MarketMaturity,
};

pub use risk_assessment_agent::{
    RiskAssessmentAgent,
    RiskAssessmentReport,
    RiskRecommendation,
    RiskCategory,
    BusinessRisk,
    RiskLevel,
    MitigationStrategy,
    RiskMatrix,
    ContingencyPlan,
};

pub use validation_manager::{
    BusinessValidationManager,
    ComprehensiveValidationReport,
    ValidationRecommendation,
};
