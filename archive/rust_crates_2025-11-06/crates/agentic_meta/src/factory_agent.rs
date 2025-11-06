//! Factory Meta-Agent - Creates and configures new agents

use crate::meta_agent::{MetaAgent, MetaAgentType, MetaAgentCapability, MetaAgentMetrics, MetaAgentResult, MetaAgentConfig};
use crate::requirements::AgentRequirement;
use agentic_core::{Agent, AgentRole, AgentId, Result, Error};
use agentic_domain::agent_genome::AgentGenome;
use agentic_factory::AgentFactory;
use agentic_standards::StandardsRegistry;
use async_trait::async_trait;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::time::Instant;
use tracing::{info, debug, warn};

/// Factory Meta-Agent - Creates new agents based on requirements
pub struct FactoryMetaAgent {
    /// Base agent
    agent: Agent,

    /// Underlying agent factory
    factory: AgentFactory,

    /// Configuration
    config: MetaAgentConfig,

    /// Performance metrics
    metrics: MetaAgentMetrics,

    /// Agents created by this factory
    created_agents: Vec<AgentId>,
}

impl FactoryMetaAgent {
    /// Create a new factory meta-agent
    pub fn new(registry: StandardsRegistry) -> Self {
        let mut agent = Agent::new(
            "AgentFactory",
            "Meta-agent that creates and configures other agents based on requirements",
            AgentRole::Factory,
            "claude-3-5-sonnet-20241022",
            "anthropic",
        );

        agent.add_tag("meta-agent");
        agent.add_tag("factory");
        agent.add_tag("creator");

        Self {
            agent,
            factory: AgentFactory::from_registry(registry),
            config: MetaAgentConfig::default(),
            metrics: MetaAgentMetrics::default(),
            created_agents: Vec::new(),
        }
    }

    /// Create an agent from requirements
    pub async fn create_from_requirements(
        &mut self,
        requirement: &AgentRequirement,
    ) -> Result<(Agent, AgentGenome)> {
        info!("Creating agent from requirements: {}", requirement.purpose);
        let start = Instant::now();

        // Check if we've hit creation limit
        if let Some(max) = self.config.max_agents_created {
            if self.created_agents.len() >= max {
                return Err(Error::InvalidState(
                    format!("Maximum agent creation limit reached: {}", max)
                ));
            }
        }

        // Analyze requirements to determine best template
        let template_id = self.select_template(requirement)?;
        debug!("Selected template: {}", template_id);

        // Create agent name from purpose
        let name = self.generate_agent_name(&requirement.purpose);

        // Select model based on requirements
        let model = requirement.preferred_model.clone()
            .unwrap_or_else(|| self.select_model(requirement));

        // Create agent from template
        let (mut agent, mut genome) = self.factory.create_from_template(
            &template_id,
            &name,
            &requirement.purpose,
        )?;

        // Configure agent with required capabilities
        for capability in &requirement.capabilities {
            agent.config.insert(
                format!("capability:{}", capability),
                serde_json::json!({"enabled": true}),
            );
        }

        // Apply constraints
        for constraint in &requirement.constraints {
            agent.config.insert(
                format!("constraint:{}", self.constraint_key(constraint)),
                serde_json::json!(constraint),
            );
        }

        // Set quality requirements
        agent.config.insert(
            "quality_requirements".to_string(),
            serde_json::to_value(&requirement.quality_requirements)
                .map_err(|e| Error::SerializationError(e.to_string()))?,
        );

        // Add genome traits based on requirements
        for capability in &requirement.capabilities {
            let trait_obj = agentic_domain::agent_genome::Trait::new(
                format!("capability:{}", capability),
                serde_json::json!({
                    "name": capability,
                    "proficiency": 0.7,
                    "learning_rate": 0.1,
                }),
            ).with_confidence(0.8);

            genome.add_trait(trait_obj);
        }

        genome.specialization = requirement.purpose.clone();

        // Update metrics
        let elapsed = start.elapsed().as_millis() as f64;
        self.metrics.agents_created += 1;
        self.metrics.avg_creation_time_ms =
            (self.metrics.avg_creation_time_ms * (self.metrics.agents_created - 1) as f64
                + elapsed) / self.metrics.agents_created as f64;

        self.metrics.creation_success_rate = self.metrics.agents_created as f64
            / (self.metrics.agents_created as f64 + 1.0); // Simplified

        self.created_agents.push(agent.id);

        info!("Successfully created agent '{}' (ID: {}) in {:.2}ms",
            agent.name, agent.id, elapsed);

        Ok((agent, genome))
    }

    /// Select appropriate template based on requirements
    fn select_template(&self, requirement: &AgentRequirement) -> Result<String> {
        // Simple selection logic - can be enhanced with ML
        if requirement.capabilities.contains(&"data_analysis".to_string()) {
            Ok("tmpl.standard.worker".to_string())
        } else if requirement.capabilities.contains(&"coordination".to_string()) {
            Ok("tmpl.standard.worker".to_string()) // Would have supervisor template
        } else {
            Ok("tmpl.standard.worker".to_string())
        }
    }

    /// Select appropriate model based on requirements
    fn select_model(&self, requirement: &AgentRequirement) -> String {
        // Select model based on cost/performance tradeoff
        if let Some(max_cost) = requirement.quality_requirements.max_cost_per_task {
            if max_cost < 0.10 {
                "claude-3-5-haiku-20241022".to_string()
            } else if max_cost < 0.50 {
                "claude-3-5-sonnet-20241022".to_string()
            } else {
                "claude-3-opus-20240229".to_string()
            }
        } else {
            "claude-3-5-sonnet-20241022".to_string()
        }
    }

    /// Generate agent name from purpose
    fn generate_agent_name(&self, purpose: &str) -> String {
        // Simple name generation - can be enhanced
        let words: Vec<&str> = purpose.split_whitespace().collect();
        if words.len() >= 2 {
            format!("{}{}Agent",
                words[0].chars().next().unwrap().to_uppercase(),
                &words[0][1..],
            )
        } else {
            format!("{}Agent", purpose.replace(" ", ""))
        }
    }

    /// Extract key from constraint string
    fn constraint_key(&self, constraint: &str) -> String {
        constraint.split(':').next().unwrap_or(constraint).to_string()
    }

    /// Get agents created by this factory
    pub fn created_agents(&self) -> &[AgentId] {
        &self.created_agents
    }

    /// Get configuration
    pub fn config(&self) -> &MetaAgentConfig {
        &self.config
    }

    /// Update configuration
    pub fn set_config(&mut self, config: MetaAgentConfig) {
        self.config = config;
    }
}

#[async_trait]
impl MetaAgent for FactoryMetaAgent {
    fn meta_type(&self) -> MetaAgentType {
        MetaAgentType::Factory
    }

    fn base_agent(&self) -> &Agent {
        &self.agent
    }

    fn capabilities(&self) -> Vec<MetaAgentCapability> {
        vec![
            MetaAgentCapability {
                name: "create_agent".to_string(),
                description: "Create a new agent based on requirements".to_string(),
                inputs: vec!["agent_requirement".to_string()],
                outputs: vec!["agent".to_string(), "genome".to_string()],
                estimated_cost: Some(0.05),
            },
            MetaAgentCapability {
                name: "analyze_requirements".to_string(),
                description: "Analyze requirements to determine best agent configuration".to_string(),
                inputs: vec!["requirements".to_string()],
                outputs: vec!["analysis".to_string()],
                estimated_cost: Some(0.01),
            },
            MetaAgentCapability {
                name: "optimize_configuration".to_string(),
                description: "Optimize agent configuration for performance".to_string(),
                inputs: vec!["agent_id".to_string()],
                outputs: vec!["optimized_config".to_string()],
                estimated_cost: Some(0.02),
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
            "create_agent" => {
                let requirement: AgentRequirement = serde_json::from_value(
                    params.get("requirement")
                        .ok_or_else(|| Error::InvalidArgument("Missing requirement".to_string()))?
                        .clone()
                ).map_err(|e| Error::SerializationError(e.to_string()))?;

                let (agent, genome) = self.create_from_requirements(&requirement).await?;

                Ok(serde_json::json!({
                    "agent_id": agent.id.to_string(),
                    "agent_name": agent.name,
                    "genome_version": genome.version.version,
                }))
            }
            _ => Err(Error::InvalidArgument(format!("Unknown task type: {}", task_type))),
        }
    }

    async fn self_analyze(&self) -> Result<Vec<String>> {
        let mut insights = Vec::new();

        if self.metrics.creation_success_rate < 0.9 {
            insights.push("Creation success rate below target (90%)".to_string());
        }

        if self.metrics.avg_creation_time_ms > 1000.0 {
            insights.push("Average creation time above target (1000ms)".to_string());
        }

        if self.created_agents.len() > 100 {
            insights.push("Consider implementing agent cleanup/archival".to_string());
        }

        if insights.is_empty() {
            insights.push("Performance within acceptable parameters".to_string());
        }

        Ok(insights)
    }

    async fn self_improve(&mut self, improvement: &str) -> Result<bool> {
        info!("Applying self-improvement: {}", improvement);

        match improvement {
            "reduce_creation_time" => {
                // Could implement caching, optimization, etc.
                Ok(true)
            }
            "improve_template_selection" => {
                // Could implement ML-based selection
                Ok(true)
            }
            _ => {
                warn!("Unknown improvement: {}", improvement);
                Ok(false)
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use agentic_standards::StandardsAgent;

    #[test]
    fn test_factory_meta_agent_creation() {
        let standards = StandardsAgent::new();
        let factory = FactoryMetaAgent::new(standards.registry().clone());

        assert_eq!(factory.meta_type(), MetaAgentType::Factory);
        assert_eq!(factory.base_agent().name, "AgentFactory");
        assert_eq!(factory.created_agents().len(), 0);
    }

    #[tokio::test]
    async fn test_create_agent_from_requirements() {
        let standards = StandardsAgent::new();
        let mut factory = FactoryMetaAgent::new(standards.registry().clone());

        let requirement = AgentRequirement::simple(
            "Analyze financial data",
            vec!["data_analysis".to_string(), "reporting".to_string()],
        );

        let result = factory.create_from_requirements(&requirement).await;
        assert!(result.is_ok());

        let (agent, genome) = result.unwrap();
        assert!(!agent.name.is_empty());
        assert_eq!(genome.specialization, "Analyze financial data");
        assert_eq!(factory.created_agents().len(), 1);
    }

    #[test]
    fn test_model_selection() {
        let standards = StandardsAgent::new();
        let factory = FactoryMetaAgent::new(standards.registry().clone());

        let low_cost_req = AgentRequirement::simple("Test", vec![])
            .with_quality(QualityRequirements {
                max_cost_per_task: Some(0.05),
                ..Default::default()
            });

        let model = factory.select_model(&low_cost_req);
        assert_eq!(model, "claude-3-5-haiku-20241022");

        let high_quality_req = AgentRequirement::simple("Test", vec![])
            .with_quality(QualityRequirements {
                max_cost_per_task: Some(1.0),
                ..Default::default()
            });

        let model = factory.select_model(&high_quality_req);
        assert_eq!(model, "claude-3-opus-20240229");
    }
}
