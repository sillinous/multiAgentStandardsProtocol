

//! Revenue Generation Models
//!
//! Data structures for the revenue generation subsystem.

use serde::{Deserialize, Serialize};
use uuid::Uuid;
use chrono::{DateTime, Utc};

/// Payment provider types
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum PaymentProvider {
    Stripe,
    PayPal,
    Square,
    Paddle,
}

/// Pricing model types
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum PricingModel {
    /// One-time payment
    OneTime,
    /// Monthly subscription
    Subscription,
    /// Pay-per-use
    Usage,
    /// Freemium with premium features
    Freemium,
    /// Tiered pricing
    Tiered,
}

/// Monetization configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MonetizationConfig {
    pub opportunity_id: Uuid,
    pub payment_provider: PaymentProvider,
    pub pricing_model: PricingModel,
    pub price_point: f64,
    pub currency: String,
    pub billing_interval: Option<BillingInterval>,
    pub free_trial_days: Option<u32>,
    pub payment_link: Option<String>,
    pub webhook_url: Option<String>,
}

/// Billing interval for subscriptions
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum BillingInterval {
    Daily,
    Weekly,
    Monthly,
    Quarterly,
    Yearly,
}

/// Marketing campaign types
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum CampaignType {
    GoogleAds,
    FacebookAds,
    LinkedInAds,
    TwitterAds,
    SEO,
    ContentMarketing,
    EmailMarketing,
    SocialMedia,
}

/// Marketing campaign configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketingCampaign {
    pub id: Uuid,
    pub opportunity_id: Uuid,
    pub campaign_type: CampaignType,
    pub budget: f64,
    pub duration_days: u32,
    pub target_audience: String,
    pub key_messages: Vec<String>,
    pub call_to_action: String,
    pub landing_page_url: Option<String>,
    pub status: CampaignStatus,
    pub metrics: CampaignMetrics,
}

/// Campaign status
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum CampaignStatus {
    Draft,
    Active,
    Paused,
    Completed,
    Cancelled,
}

/// Campaign performance metrics
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct CampaignMetrics {
    pub impressions: u64,
    pub clicks: u64,
    pub conversions: u64,
    pub cost: f64,
    pub revenue: f64,
    pub roi: f64, // Return on Investment
    pub ctr: f64, // Click-through rate
    pub cpc: f64, // Cost per click
    pub cpa: f64, // Cost per acquisition
}

/// Deployment configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DeploymentConfig {
    pub opportunity_id: Uuid,
    pub hosting_provider: HostingProvider,
    pub domain: Option<String>,
    pub environment: DeploymentEnvironment,
    pub repository_url: Option<String>,
    pub deployment_url: Option<String>,
    pub ssl_enabled: bool,
    pub monitoring_enabled: bool,
    pub backup_enabled: bool,
}

/// Hosting provider options
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum HostingProvider {
    AWS,
    GoogleCloud,
    Azure,
    DigitalOcean,
    Heroku,
    Vercel,
    Netlify,
}

/// Deployment environment
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum DeploymentEnvironment {
    Development,
    Staging,
    Production,
}

/// Business analytics data
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct BusinessAnalytics {
    pub opportunity_id: Uuid,
    pub time_period: TimePeriod,

    // Revenue metrics
    pub total_revenue: f64,
    pub mrr: f64, // Monthly Recurring Revenue
    pub arr: f64, // Annual Recurring Revenue
    pub arpu: f64, // Average Revenue Per User

    // Customer metrics
    pub total_customers: u64,
    pub new_customers: u64,
    pub churned_customers: u64,
    pub churn_rate: f64,
    pub ltv: f64, // Lifetime Value
    pub cac: f64, // Customer Acquisition Cost

    // Engagement metrics
    pub active_users: u64,
    pub dau: u64, // Daily Active Users
    pub mau: u64, // Monthly Active Users
    pub engagement_rate: f64,

    // Conversion metrics
    pub conversion_rate: f64,
    pub trial_to_paid_rate: f64,
}

/// Time period for analytics
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum TimePeriod {
    Today,
    Week,
    Month,
    Quarter,
    Year,
    AllTime,
}

/// Optimization recommendation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OptimizationRecommendation {
    pub id: Uuid,
    pub opportunity_id: Uuid,
    pub category: OptimizationCategory,
    pub title: String,
    pub description: String,
    pub expected_impact: f64, // 0-1 scale
    pub effort: EffortLevel,
    pub priority: Priority,
    pub status: OptimizationStatus,
    pub implemented_at: Option<DateTime<Utc>>,
}

/// Optimization category
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum OptimizationCategory {
    Pricing,
    Marketing,
    Product,
    UserExperience,
    Performance,
    CostReduction,
    Retention,
    Conversion,
}

/// Effort level for implementation
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum EffortLevel {
    Low,
    Medium,
    High,
}

/// Priority level
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Priority {
    Low,
    Medium,
    High,
    Critical,
}

/// Optimization status
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum OptimizationStatus {
    Identified,
    Planned,
    InProgress,
    Implemented,
    Validated,
    Rejected,
}

/// Revenue generation result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RevenueGenerationResult {
    pub opportunity_id: Uuid,
    pub workflow_id: String,
    pub started_at: DateTime<Utc>,
    pub completed_at: Option<DateTime<Utc>>,

    // Configuration
    pub monetization_config: MonetizationConfig,
    pub deployment_config: DeploymentConfig,

    // Campaigns
    pub marketing_campaigns: Vec<MarketingCampaign>,

    // Analytics
    pub analytics: BusinessAnalytics,

    // Optimizations
    pub optimizations: Vec<OptimizationRecommendation>,

    // Status
    pub status: RevenueGenerationStatus,
    pub total_revenue_generated: f64,
    pub roi: f64,
}

/// Revenue generation status
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum RevenueGenerationStatus {
    Initializing,
    SettingUpMonetization,
    LaunchingMarketing,
    Deploying,
    Active,
    Optimizing,
    Paused,
    Completed,
    Failed,
}

impl MonetizationConfig {
    pub fn new(opportunity_id: Uuid, payment_provider: PaymentProvider, pricing_model: PricingModel) -> Self {
        Self {
            opportunity_id,
            payment_provider,
            pricing_model,
            price_point: 0.0,
            currency: "USD".to_string(),
            billing_interval: None,
            free_trial_days: None,
            payment_link: None,
            webhook_url: None,
        }
    }
}

impl MarketingCampaign {
    pub fn new(opportunity_id: Uuid, campaign_type: CampaignType) -> Self {
        Self {
            id: Uuid::new_v4(),
            opportunity_id,
            campaign_type,
            budget: 0.0,
            duration_days: 30,
            target_audience: String::new(),
            key_messages: Vec::new(),
            call_to_action: String::new(),
            landing_page_url: None,
            status: CampaignStatus::Draft,
            metrics: CampaignMetrics::default(),
        }
    }

    pub fn calculate_roi(&mut self) {
        if self.metrics.cost > 0.0 {
            self.metrics.roi = (self.metrics.revenue - self.metrics.cost) / self.metrics.cost;
        }
    }

    pub fn calculate_ctr(&mut self) {
        if self.metrics.impressions > 0 {
            self.metrics.ctr = (self.metrics.clicks as f64 / self.metrics.impressions as f64) * 100.0;
        }
    }

    pub fn calculate_cpc(&mut self) {
        if self.metrics.clicks > 0 {
            self.metrics.cpc = self.metrics.cost / self.metrics.clicks as f64;
        }
    }

    pub fn calculate_cpa(&mut self) {
        if self.metrics.conversions > 0 {
            self.metrics.cpa = self.metrics.cost / self.metrics.conversions as f64;
        }
    }
}

impl BusinessAnalytics {
    pub fn calculate_churn_rate(&mut self) {
        if self.total_customers > 0 {
            self.churn_rate = (self.churned_customers as f64 / self.total_customers as f64) * 100.0;
        }
    }

    pub fn calculate_engagement_rate(&mut self) {
        if self.total_customers > 0 {
            self.engagement_rate = (self.active_users as f64 / self.total_customers as f64) * 100.0;
        }
    }

    pub fn calculate_ltv_cac_ratio(&self) -> f64 {
        if self.cac > 0.0 {
            self.ltv / self.cac
        } else {
            0.0
        }
    }
}
