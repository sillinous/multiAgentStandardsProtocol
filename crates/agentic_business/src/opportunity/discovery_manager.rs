//! Opportunity Discovery Manager - Orchestrates the opportunity discovery process

use super::{
    MarketResearchAgent, TrendAnalysisAgent,
    CompetitorAnalysisAgent, OpportunityEvaluationAgent,
};
use crate::models::{Opportunity, UserPreferences};
use agentic_core::{Agent, AgentRole, Result, WorkflowId};
use agentic_meta::meta_agent::{MetaAgent, MetaAgentType, MetaAgentCapability, MetaAgentMetrics};
use agentic_runtime::llm::LlmClient;
use async_trait::async_trait;
use std::collections::HashMap;
use std::sync::Arc;
use tracing::{info, debug};

/// Opportunity Discovery Manager - Meta-agent for opportunity discovery
pub struct OpportunityDiscoveryManager {
    agent: Agent,
    workflow_id: WorkflowId,
    market_research: MarketResearchAgent,
    trend_analysis: TrendAnalysisAgent,
    competitor_analysis: CompetitorAnalysisAgent,
    evaluation: OpportunityEvaluationAgent,
    metrics: MetaAgentMetrics,
}

impl OpportunityDiscoveryManager {
    /// Create a new opportunity discovery manager
    pub fn new(llm_client: Arc<dyn LlmClient>) -> Self {
        let mut agent = Agent::new(
            "OpportunityDiscoveryManager",
            "Meta-agent that orchestrates market research, trend analysis, and opportunity evaluation",
            AgentRole::Supervisor,
            "claude-3-5-sonnet-20241022",
            "anthropic",
        );

        agent.add_tag("meta-agent");
        agent.add_tag("business");
        agent.add_tag("opportunity-discovery");

        // Configure agent to be standards-compliant (A2A, MCP protocols)
        crate::configure_standards_compliant_agent(&mut agent);

        Self {
            agent,
            workflow_id: WorkflowId::generate(),
            market_research: MarketResearchAgent::new(llm_client.clone()),
            trend_analysis: TrendAnalysisAgent::new(llm_client.clone()),
            competitor_analysis: CompetitorAnalysisAgent::new(llm_client.clone()),
            evaluation: OpportunityEvaluationAgent::new(llm_client),
            metrics: MetaAgentMetrics::default(),
        }
    }

    /// Discover and rank opportunities based on user preferences
    pub async fn discover(&mut self, preferences: UserPreferences) -> Result<Vec<Opportunity>> {
        info!("Starting opportunity discovery workflow");
        let start = std::time::Instant::now();

        // Step 1: Market Research - Discover raw opportunities
        debug!("Step 1: Market Research");
        let mut opportunities = self.market_research
            .discover_opportunities(&preferences)
            .await?;

        info!("Discovered {} raw opportunities", opportunities.len());

        // Step 2: Trend Analysis - Analyze growth patterns
        debug!("Step 2: Trend Analysis");
        for opportunity in &mut opportunities {
            if let Ok(trends) = self.trend_analysis.analyze_trends(opportunity).await {
                debug!("Analyzed {} trends for {}", trends.len(), opportunity.title);
            }
        }

        // Step 3: Competitor Analysis - Understand competitive landscape
        debug!("Step 3: Competitor Analysis");
        for opportunity in &mut opportunities {
            if let Ok(analysis) = self.competitor_analysis.analyze_competitors(opportunity).await {
                opportunity.competitive_analysis = analysis;
            }
        }

        // Step 4: Evaluation - Multi-dimensional scoring
        debug!("Step 4: Opportunity Evaluation");
        for opportunity in &mut opportunities {
            self.evaluation.evaluate_opportunity(opportunity).await?;
        }

        // Step 5: Ranking
        debug!("Step 5: Ranking opportunities");
        self.evaluation.rank_opportunities(&mut opportunities);

        // Update metrics
        let elapsed = start.elapsed();
        self.metrics.tasks_executed += 1;
        self.metrics.avg_execution_time_ms = elapsed.as_millis() as f64;

        info!(
            "Discovery workflow completed: {} opportunities in {:.2}s",
            opportunities.len(),
            elapsed.as_secs_f64()
        );

        Ok(opportunities)
    }

    /// Get workflow ID
    pub fn workflow_id(&self) -> WorkflowId {
        self.workflow_id
    }

    /// Get metrics
    pub fn metrics(&self) -> &MetaAgentMetrics {
        &self.metrics
    }
}

#[async_trait]
impl MetaAgent for OpportunityDiscoveryManager {
    fn meta_type(&self) -> MetaAgentType {
        MetaAgentType::Coordinator
    }

    fn base_agent(&self) -> &Agent {
        &self.agent
    }

    fn capabilities(&self) -> Vec<MetaAgentCapability> {
        vec![
            MetaAgentCapability {
                name: "discover_opportunities".to_string(),
                description: "Discover and rank market opportunities based on preferences".to_string(),
                inputs: vec!["user_preferences".to_string()],
                outputs: vec!["ranked_opportunities".to_string()],
                estimated_cost: Some(0.30),
            },
            MetaAgentCapability {
                name: "analyze_trends".to_string(),
                description: "Analyze market trends for opportunities".to_string(),
                inputs: vec!["opportunity".to_string()],
                outputs: vec!["trends".to_string()],
                estimated_cost: Some(0.05),
            },
            MetaAgentCapability {
                name: "evaluate_opportunity".to_string(),
                description: "Multi-dimensional evaluation of single opportunity".to_string(),
                inputs: vec!["opportunity".to_string()],
                outputs: vec!["score".to_string()],
                estimated_cost: Some(0.10),
            },
        ]
    }

    fn metrics(&self) -> &MetaAgentMetrics {
        &self.metrics
    }

    async fn execute_meta_task(
        &mut self,
        task_type: &str,
        params: HashMap<String, serde_json::Value>,
    ) -> Result<serde_json::Value> {
        match task_type {
            "discover_opportunities" => {
                let preferences: UserPreferences = serde_json::from_value(
                    params.get("preferences")
                        .ok_or_else(|| agentic_core::Error::InvalidArgument("Missing preferences".to_string()))?
                        .clone()
                )?;

                let opportunities = self.discover(preferences).await?;
                Ok(serde_json::to_value(opportunities)?)
            }
            _ => Err(agentic_core::Error::InvalidArgument(
                format!("Unknown task type: {}", task_type)
            )),
        }
    }

    async fn self_analyze(&self) -> Result<Vec<String>> {
        let mut insights = Vec::new();

        if self.metrics.tasks_executed == 0 {
            insights.push("No discovery workflows executed yet".to_string());
        } else {
            insights.push(format!(
                "Executed {} discovery workflows with avg time {:.2}s",
                self.metrics.tasks_executed,
                self.metrics.avg_execution_time_ms / 1000.0
            ));
        }

        Ok(insights)
    }

    async fn self_improve(&mut self, improvement: &str) -> Result<bool> {
        info!("Applying improvement: {}", improvement);
        // Could implement caching, parallel processing, etc.
        Ok(true)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use agentic_runtime::llm::MockLlmClient;

    #[tokio::test]
    async fn test_discovery_manager_creation() {
        let llm = Arc::new(MockLlmClient::new());
        let manager = OpportunityDiscoveryManager::new(llm);
        assert_eq!(manager.agent.name, "OpportunityDiscoveryManager");
    }

    #[tokio::test]
    async fn test_discover_opportunities() {
        let llm = Arc::new(MockLlmClient::new());
        let mut manager = OpportunityDiscoveryManager::new(llm);

        let preferences = UserPreferences {
            domain: Some("SaaS".to_string()),
            focus_minimal_investment: true,
            ..Default::default()
        };

        let result = manager.discover(preferences).await;
        assert!(result.is_ok());
    }
}
