//! Data models for the business-to-revenue system

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use uuid::Uuid;

/// Unique identifier for an opportunity
pub type OpportunityId = Uuid;

/// User preferences for opportunity discovery
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserPreferences {
    /// Preferred domain (e.g., "SaaS", "E-commerce", "Mobile Apps")
    pub domain: Option<String>,

    /// Product type preference
    pub product_type: Option<ProductType>,

    /// Minimum investment willing to make (USD)
    pub min_investment: Option<f64>,

    /// Maximum investment willing to make (USD)
    pub max_investment: Option<f64>,

    /// Maximum time to market (days)
    pub max_time_to_market_days: Option<u32>,

    /// Revenue type preferences
    pub revenue_type: Vec<String>, // "subscription", "one-time", "passive", "affiliate"

    /// Focus on minimal investment opportunities
    pub focus_minimal_investment: bool,

    /// Focus on passive revenue streams
    pub focus_passive_revenue: bool,

    /// Focus on quick wins
    pub focus_quick_wins: bool,

    /// Custom criteria
    pub custom_criteria: HashMap<String, serde_json::Value>,
}

impl Default for UserPreferences {
    fn default() -> Self {
        Self {
            domain: None,
            product_type: None,
            min_investment: Some(0.0),
            max_investment: None,
            max_time_to_market_days: None,
            revenue_type: vec![],
            focus_minimal_investment: false,
            focus_passive_revenue: false,
            focus_quick_wins: false,
            custom_criteria: HashMap::new(),
        }
    }
}

/// Product type classification
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ProductType {
    SaaS,
    MobileApp,
    WebApp,
    API,
    ECommerce,
    Marketplace,
    ContentPlatform,
    Tool,
    Service,
    Other,
}

/// Market opportunity
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Opportunity {
    pub id: OpportunityId,
    pub domain: String,
    pub product_type: ProductType,
    pub title: String,
    pub description: String,
    pub scores: MultiDimensionalScore,
    pub financial_projection: FinancialProjection,
    pub competitive_analysis: CompetitiveAnalysis,
    pub implementation_estimate: ImplementationEstimate,
    pub sources: Vec<DataSource>,
    pub discovered_at: chrono::DateTime<chrono::Utc>,
    pub validation_status: Option<ValidationStatus>,
}

impl Opportunity {
    pub fn new(title: String, description: String, domain: String, product_type: ProductType) -> Self {
        Self {
            id: Uuid::new_v4(),
            title,
            description,
            domain,
            product_type,
            scores: MultiDimensionalScore::default(),
            financial_projection: FinancialProjection::default(),
            competitive_analysis: CompetitiveAnalysis::default(),
            implementation_estimate: ImplementationEstimate::default(),
            sources: Vec::new(),
            discovered_at: chrono::Utc::now(),
            validation_status: None,
        }
    }

    /// Check if opportunity matches user preferences
    pub fn matches_preferences(&self, prefs: &UserPreferences) -> bool {
        // Domain match
        if let Some(domain) = &prefs.domain {
            if !self.domain.to_lowercase().contains(&domain.to_lowercase()) {
                return false;
            }
        }

        // Product type match
        if let Some(ptype) = prefs.product_type {
            if self.product_type != ptype {
                return false;
            }
        }

        // Investment range
        if let Some(max_inv) = prefs.max_investment {
            if self.financial_projection.initial_investment > max_inv {
                return false;
            }
        }

        // Time to market
        if let Some(max_days) = prefs.max_time_to_market_days {
            if self.implementation_estimate.estimated_days > max_days {
                return false;
            }
        }

        // Minimal investment focus
        if prefs.focus_minimal_investment && self.financial_projection.initial_investment > 5000.0 {
            return false;
        }

        // Passive revenue focus
        if prefs.focus_passive_revenue && self.scores.passive_income < 7.0 {
            return false;
        }

        true
    }

    /// Calculate overall attractiveness score
    pub fn attractiveness_score(&self) -> f64 {
        self.scores.overall
    }
}

/// Multi-dimensional opportunity scoring
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MultiDimensionalScore {
    /// Market size potential (0-10)
    pub market_size: f64,

    /// Competition level (0-10, lower is better)
    pub competition: f64,

    /// Implementation complexity (0-10, lower is easier)
    pub complexity: f64,

    /// Revenue potential (0-10)
    pub revenue_potential: f64,

    /// Time to market (0-10, higher is faster)
    pub time_to_market: f64,

    /// Investment required (0-10, lower is less investment)
    pub investment_required: f64,

    /// Passive income potential (0-10)
    pub passive_income: f64,

    /// Overall weighted score (0-10)
    pub overall: f64,
}

impl Default for MultiDimensionalScore {
    fn default() -> Self {
        Self {
            market_size: 5.0,
            competition: 5.0,
            complexity: 5.0,
            revenue_potential: 5.0,
            time_to_market: 5.0,
            investment_required: 5.0,
            passive_income: 5.0,
            overall: 5.0,
        }
    }
}

impl MultiDimensionalScore {
    /// Calculate weighted overall score
    pub fn calculate_overall(&mut self) {
        // Weights can be customized based on user preferences
        let weights = [
            (self.market_size, 0.2),
            (10.0 - self.competition, 0.15), // Invert competition (lower is better)
            (10.0 - self.complexity, 0.10),   // Invert complexity
            (self.revenue_potential, 0.25),
            (self.time_to_market, 0.10),
            (10.0 - self.investment_required, 0.10), // Invert investment
            (self.passive_income, 0.10),
        ];

        let total_weight: f64 = weights.iter().map(|(_, w)| w).sum();
        self.overall = weights.iter().map(|(score, weight)| score * weight).sum::<f64>() / total_weight;
    }
}

/// Financial projections
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FinancialProjection {
    /// Initial investment required (USD)
    pub initial_investment: f64,

    /// Monthly operating costs (USD)
    pub monthly_costs: f64,

    /// Projected monthly revenue (USD) - pessimistic
    pub monthly_revenue_low: f64,

    /// Projected monthly revenue (USD) - realistic
    pub monthly_revenue_mid: f64,

    /// Projected monthly revenue (USD) - optimistic
    pub monthly_revenue_high: f64,

    /// Break-even time (months)
    pub break_even_months: f64,

    /// Projected ROI at 12 months (percentage)
    pub roi_12_months: f64,

    /// Revenue model
    pub revenue_model: String,
}

impl Default for FinancialProjection {
    fn default() -> Self {
        Self {
            initial_investment: 0.0,
            monthly_costs: 0.0,
            monthly_revenue_low: 0.0,
            monthly_revenue_mid: 0.0,
            monthly_revenue_high: 0.0,
            break_even_months: 0.0,
            roi_12_months: 0.0,
            revenue_model: "Unknown".to_string(),
        }
    }
}

/// Competitive analysis
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CompetitiveAnalysis {
    /// Number of direct competitors
    pub direct_competitors: usize,

    /// Number of indirect competitors
    pub indirect_competitors: usize,

    /// Market leader information
    pub market_leader: Option<Competitor>,

    /// Top 3-5 competitors
    pub top_competitors: Vec<Competitor>,

    /// Our competitive advantages
    pub advantages: Vec<String>,

    /// Competitive threats
    pub threats: Vec<String>,

    /// Market saturation level (0-10)
    pub saturation_level: f64,
}

impl Default for CompetitiveAnalysis {
    fn default() -> Self {
        Self {
            direct_competitors: 0,
            indirect_competitors: 0,
            market_leader: None,
            top_competitors: Vec::new(),
            advantages: Vec::new(),
            threats: Vec::new(),
            saturation_level: 5.0,
        }
    }
}

/// Competitor information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Competitor {
    pub name: String,
    pub website: Option<String>,
    pub pricing: Option<String>,
    pub market_share: Option<f64>,
    pub strengths: Vec<String>,
    pub weaknesses: Vec<String>,
}

/// Implementation estimate
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ImplementationEstimate {
    /// Estimated development time (days)
    pub estimated_days: u32,

    /// Estimated development cost (USD)
    pub estimated_cost: f64,

    /// Recommended tech stack
    pub tech_stack: TechStack,

    /// Core features to implement
    pub core_features: Vec<Feature>,

    /// Nice-to-have features
    pub optional_features: Vec<Feature>,

    /// Implementation complexity (0-10)
    pub complexity_score: f64,
}

impl Default for ImplementationEstimate {
    fn default() -> Self {
        Self {
            estimated_days: 0,
            estimated_cost: 0.0,
            tech_stack: TechStack::default(),
            core_features: Vec::new(),
            optional_features: Vec::new(),
            complexity_score: 5.0,
        }
    }
}

/// Technology stack recommendation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TechStack {
    pub frontend: Option<String>,
    pub backend: Option<String>,
    pub database: Option<String>,
    pub hosting: Option<String>,
    pub additional: Vec<String>,
}

impl Default for TechStack {
    fn default() -> Self {
        Self {
            frontend: None,
            backend: None,
            database: None,
            hosting: None,
            additional: Vec::new(),
        }
    }
}

/// Feature specification
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Feature {
    pub name: String,
    pub description: String,
    pub priority: FeaturePriority,
    pub estimated_hours: u32,
}

/// Feature priority
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum FeaturePriority {
    Critical,
    High,
    Medium,
    Low,
}

/// Data source for opportunity discovery
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DataSource {
    pub name: String,
    pub source_type: SourceType,
    pub url: Option<String>,
    pub confidence: f64,
}

/// Source type classification
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum SourceType {
    API,
    WebScraping,
    TrendAnalysis,
    LLMAnalysis,
    UserInput,
}

/// Validation status
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ValidationStatus {
    pub validated_at: chrono::DateTime<chrono::Utc>,
    pub financial_validated: bool,
    pub technical_validated: bool,
    pub demand_validated: bool,
    pub risk_validated: bool,
    pub overall_recommendation: ValidationRecommendation,
}

/// Validation recommendation
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ValidationRecommendation {
    StronglyRecommended,
    Recommended,
    Conditional,
    NotRecommended,
}

/// Analysis report (generic)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AnalysisReport {
    pub opportunity_id: OpportunityId,
    pub report_type: String,
    pub agent_id: String,
    pub summary: String,
    pub details: serde_json::Value,
    pub confidence: f64,
    pub generated_at: chrono::DateTime<chrono::Utc>,
}

/// Market trend data
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketTrend {
    pub keyword: String,
    pub trend_direction: TrendDirection,
    pub growth_rate: f64, // Percentage
    pub search_volume: Option<u64>,
    pub period: String,
}

/// Trend direction
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum TrendDirection {
    Rising,
    Stable,
    Declining,
}
