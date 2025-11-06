//! Optimization Agent - Continuous improvement and revenue optimization

use super::models::*;
use crate::models::Opportunity;
use agentic_core::{Agent, AgentRole, Result};
use agentic_runtime::llm::{LlmClient, LlmRequest};
use std::sync::Arc;
use tracing::{info, debug};
use uuid::Uuid;

pub struct OptimizationAgent {
    agent: Agent,
    llm_client: Arc<dyn LlmClient>,
}

impl OptimizationAgent {
    pub fn new(llm_client: Arc<dyn LlmClient>) -> Self {
        let mut agent = Agent::new(
            "OptimizationAgent",
            "Specialist in continuous improvement, A/B testing, and revenue optimization",
            AgentRole::Worker,
            "claude-3-5-sonnet-20241022",
            "anthropic",
        );

        agent.add_tag("business");
        agent.add_tag("revenue");
        agent.add_tag("optimization");
        agent.add_tag("improvement");

        crate::configure_standards_compliant_agent(&mut agent);

        Self { agent, llm_client }
    }

    pub async fn generate_optimizations(
        &self,
        opportunity: &Opportunity,
        analytics: &BusinessAnalytics,
    ) -> Result<Vec<OptimizationRecommendation>> {
        info!("🔧 Generating optimization recommendations");

        let mut recommendations = Vec::new();

        // Analyze current performance
        let prompt = format!(
            "You are an optimization expert. Analyze this business and suggest 3-5 specific improvements.\n\n\
            Product: {}\n\
            Revenue: ${:.2}\n\
            Customers: {}\n\
            Churn Rate: {:.1}%\n\
            ARPU: ${:.2}\n\n\
            Provide specific, actionable recommendations to:\n\
            - Increase revenue\n\
            - Reduce churn\n\
            - Improve conversion\n\
            - Reduce costs\n\n\
            Format: Number each recommendation 1-5.",
            opportunity.title,
            analytics.total_revenue,
            analytics.total_customers,
            analytics.churn_rate,
            analytics.arpu
        );

        let request = LlmRequest {
            messages: vec![("user".to_string(), prompt)],
            model: self.agent.model.clone(),
            max_tokens: Some(600),
            temperature: Some(0.7),
            ..Default::default()
        };

        let response = self.llm_client.complete(request).await?;

        // Parse recommendations
        let lines: Vec<String> = response.content
            .lines()
            .filter(|line| line.trim().starts_with(|c: char| c.is_numeric()))
            .map(|line| {
                line.trim()
                    .trim_start_matches(|c: char| c.is_numeric() || c == '.' || c == ')')
                    .trim()
                    .to_string()
            })
            .collect();

        for (idx, description) in lines.iter().enumerate() {
            let category = self.categorize_optimization(description);

            recommendations.push(OptimizationRecommendation {
                id: Uuid::new_v4(),
                opportunity_id: opportunity.id,
                category,
                title: format!("Optimization {}", idx + 1),
                description: description.clone(),
                expected_impact: 0.3 + (idx as f64 * 0.1),
                effort: if idx < 2 { EffortLevel::Low } else { EffortLevel::Medium },
                priority: if idx == 0 { Priority::High } else { Priority::Medium },
                status: OptimizationStatus::Identified,
                implemented_at: None,
            });
        }

        info!("✅ Generated {} optimization recommendations", recommendations.len());

        Ok(recommendations)
    }

    fn categorize_optimization(&self, description: &str) -> OptimizationCategory {
        let desc_lower = description.to_lowercase();

        if desc_lower.contains("price") || desc_lower.contains("pricing") {
            OptimizationCategory::Pricing
        } else if desc_lower.contains("market") || desc_lower.contains("campaign") {
            OptimizationCategory::Marketing
        } else if desc_lower.contains("feature") || desc_lower.contains("product") {
            OptimizationCategory::Product
        } else if desc_lower.contains("ux") || desc_lower.contains("user experience") {
            OptimizationCategory::UserExperience
        } else if desc_lower.contains("performance") || desc_lower.contains("speed") {
            OptimizationCategory::Performance
        } else if desc_lower.contains("cost") {
            OptimizationCategory::CostReduction
        } else if desc_lower.contains("retention") || desc_lower.contains("churn") {
            OptimizationCategory::Retention
        } else {
            OptimizationCategory::Conversion
        }
    }

    pub fn agent(&self) -> &Agent {
        &self.agent
    }
}
