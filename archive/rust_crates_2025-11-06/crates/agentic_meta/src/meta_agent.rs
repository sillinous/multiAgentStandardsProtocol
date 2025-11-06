//! Core meta-agent trait and types

use agentic_core::{Agent, AgentId, Result};
use agentic_domain::agent_genome::AgentGenome;
use async_trait::async_trait;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Type of meta-agent
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum MetaAgentType {
    /// Creates and configures new agents
    Factory,

    /// Manages full software development lifecycle
    SDLCManager,

    /// Improves agents through evolution
    EvolutionManager,

    /// Synthesizes new capabilities
    CapabilitySynthesizer,

    /// Coordinates multiple agents
    Coordinator,

    /// Monitors and optimizes performance
    PerformanceOptimizer,
}

/// Meta-agent capability
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MetaAgentCapability {
    /// Name of the capability
    pub name: String,

    /// Description of what it does
    pub description: String,

    /// Input requirements
    pub inputs: Vec<String>,

    /// Expected outputs
    pub outputs: Vec<String>,

    /// Resource cost estimate
    pub estimated_cost: Option<f64>,
}

/// Performance metrics for meta-agents
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct MetaAgentMetrics {
    /// Number of agents created
    pub agents_created: u64,

    /// Creation success rate
    pub creation_success_rate: f64,

    /// Average creation time in milliseconds
    pub avg_creation_time_ms: f64,

    /// Number of improvements made
    pub improvements_applied: u64,

    /// Number of experiments run
    pub experiments_run: u64,

    /// Successful experiment rate
    pub experiment_success_rate: f64,
}

/// Core meta-agent trait
#[async_trait]
pub trait MetaAgent: Send + Sync {
    /// Get the meta-agent type
    fn meta_type(&self) -> MetaAgentType;

    /// Get the underlying agent
    fn base_agent(&self) -> &Agent;

    /// Get meta-agent capabilities
    fn capabilities(&self) -> Vec<MetaAgentCapability>;

    /// Get performance metrics
    fn metrics(&self) -> &MetaAgentMetrics;

    /// Execute meta-agent specific task
    async fn execute_meta_task(
        &mut self,
        task_type: &str,
        params: HashMap<String, serde_json::Value>,
    ) -> Result<serde_json::Value>;

    /// Self-analyze performance and identify improvements
    async fn self_analyze(&self) -> Result<Vec<String>>;

    /// Apply an improvement to itself
    async fn self_improve(&mut self, improvement: &str) -> Result<bool>;
}

/// Result of meta-agent operation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MetaAgentResult {
    pub success: bool,
    pub output: serde_json::Value,
    pub agents_created: Vec<AgentId>,
    pub agents_modified: Vec<AgentId>,
    pub execution_time_ms: u64,
    pub cost: f64,
    pub notes: Vec<String>,
}

impl MetaAgentResult {
    pub fn success(output: serde_json::Value) -> Self {
        Self {
            success: true,
            output,
            agents_created: Vec::new(),
            agents_modified: Vec::new(),
            execution_time_ms: 0,
            cost: 0.0,
            notes: Vec::new(),
        }
    }

    pub fn failure(error: String) -> Self {
        Self {
            success: false,
            output: serde_json::json!({ "error": error }),
            agents_created: Vec::new(),
            agents_modified: Vec::new(),
            execution_time_ms: 0,
            cost: 0.0,
            notes: Vec::new(),
        }
    }

    pub fn with_agents(mut self, created: Vec<AgentId>) -> Self {
        self.agents_created = created;
        self
    }

    pub fn with_cost(mut self, cost: f64) -> Self {
        self.cost = cost;
        self
    }

    pub fn with_timing(mut self, ms: u64) -> Self {
        self.execution_time_ms = ms;
        self
    }
}

/// Configuration for meta-agent behavior
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MetaAgentConfig {
    /// Maximum agents this meta-agent can create
    pub max_agents_created: Option<usize>,

    /// Maximum cost per operation
    pub max_cost_per_operation: Option<f64>,

    /// Whether this meta-agent can self-modify
    pub allow_self_modification: bool,

    /// Whether to require human approval for critical operations
    pub require_human_approval: bool,

    /// Sandbox mode - agents created in sandbox first
    pub sandbox_mode: bool,

    /// Auto-deploy created agents
    pub auto_deploy: bool,
}

impl Default for MetaAgentConfig {
    fn default() -> Self {
        Self {
            max_agents_created: Some(10),
            max_cost_per_operation: Some(10.0),
            allow_self_modification: false,
            require_human_approval: true,
            sandbox_mode: true,
            auto_deploy: false,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_meta_agent_result() {
        let result = MetaAgentResult::success(serde_json::json!({"status": "ok"}))
            .with_cost(0.15)
            .with_timing(1500);

        assert!(result.success);
        assert_eq!(result.cost, 0.15);
        assert_eq!(result.execution_time_ms, 1500);
    }

    #[test]
    fn test_meta_agent_config_defaults() {
        let config = MetaAgentConfig::default();

        assert_eq!(config.max_agents_created, Some(10));
        assert_eq!(config.max_cost_per_operation, Some(10.0));
        assert!(!config.allow_self_modification);
        assert!(config.require_human_approval);
        assert!(config.sandbox_mode);
        assert!(!config.auto_deploy);
    }
}
