//! Analytics Agent - Tracks business metrics, user behavior, and performance

use super::models::*;
use crate::models::Opportunity;
use agentic_core::{Agent, AgentRole, Result};
use std::sync::Arc;
use agentic_runtime::llm::LlmClient;
use tracing::info;

pub struct AnalyticsAgent {
    agent: Agent,
    llm_client: Arc<dyn LlmClient>,
}

impl AnalyticsAgent {
    pub fn new(llm_client: Arc<dyn LlmClient>) -> Self {
        let mut agent = Agent::new(
            "AnalyticsAgent",
            "Specialist in business analytics, metrics tracking, and performance monitoring",
            AgentRole::Worker,
            "claude-3-5-sonnet-20241022",
            "anthropic",
        );

        agent.add_tag("business");
        agent.add_tag("revenue");
        agent.add_tag("analytics");
        agent.add_tag("metrics");

        crate::configure_standards_compliant_agent(&mut agent);

        Self { agent, llm_client }
    }

    pub async fn create_analytics_setup(
        &self,
        opportunity: &Opportunity,
    ) -> Result<BusinessAnalytics> {
        info!("📊 Setting up analytics for: {}", opportunity.title);

        let mut analytics = BusinessAnalytics {
            opportunity_id: opportunity.id,
            time_period: TimePeriod::Month,
            ..Default::default()
        };

        // Initialize with baseline expectations
        analytics.total_customers = 0;
        analytics.new_customers = 0;
        analytics.churned_customers = 0;
        analytics.churn_rate = 0.0;

        info!("✅ Analytics configured");

        Ok(analytics)
    }

    pub async fn track_metrics(
        &self,
        analytics: &mut BusinessAnalytics,
        revenue: f64,
        customers: u64,
    ) -> Result<()> {
        info!("📈 Tracking metrics - Revenue: ${:.2}, Customers: {}", revenue, customers);

        analytics.total_revenue = revenue;
        analytics.total_customers = customers;

        if customers > 0 {
            analytics.arpu = revenue / customers as f64;
        }

        analytics.calculate_churn_rate();
        analytics.calculate_engagement_rate();

        Ok(())
    }

    pub fn agent(&self) -> &Agent {
        &self.agent
    }
}
