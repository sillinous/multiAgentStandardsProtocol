//! Agent executor - runs agents and manages their lifecycle

use crate::context::ExecutionContext;
use crate::llm::{LlmClient, LlmRequest, LlmResponse, Message};
use agentic_core::{Agent, AgentStatus, Result, Error};
use agentic_domain::learning::{LearningEvent, LearningType};
use agentic_learning::LearningEngine;
use async_trait::async_trait;
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use std::time::Instant;
use tracing::{info, warn, error, instrument};

/// Result of agent execution
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExecutionResult {
    pub success: bool,
    pub output: String,
    pub error: Option<String>,
    pub tokens_used: usize,
    pub execution_time_ms: u64,
    pub learning_events: Vec<LearningEvent>,
}

impl ExecutionResult {
    pub fn success(output: String, tokens: usize, time_ms: u64) -> Self {
        Self {
            success: true,
            output,
            error: None,
            tokens_used: tokens,
            execution_time_ms: time_ms,
            learning_events: Vec::new(),
        }
    }

    pub fn failure(error: String, time_ms: u64) -> Self {
        Self {
            success: false,
            output: String::new(),
            error: Some(error),
            tokens_used: 0,
            execution_time_ms: time_ms,
            learning_events: Vec::new(),
        }
    }

    pub fn with_learning_event(mut self, event: LearningEvent) -> Self {
        self.learning_events.push(event);
        self
    }
}

/// Trait for executing agents
#[async_trait]
pub trait AgentExecutor: Send + Sync {
    /// Execute an agent with given input
    async fn execute(
        &self,
        agent: &mut Agent,
        input: &str,
        context: &ExecutionContext,
    ) -> Result<ExecutionResult>;

    /// Execute agent and update its state
    async fn execute_with_learning(
        &self,
        agent: &mut Agent,
        input: &str,
        context: &ExecutionContext,
        learning_engine: &mut LearningEngine,
    ) -> Result<ExecutionResult>;
}

/// Default executor implementation using LLM clients
pub struct DefaultExecutor {
    llm_client: Arc<dyn LlmClient>,
}

impl DefaultExecutor {
    pub fn new(llm_client: Arc<dyn LlmClient>) -> Self {
        Self { llm_client }
    }

    fn build_system_prompt(&self, agent: &Agent) -> String {
        format!(
            "You are {}, an AI agent with the following characteristics:\n\n\
            Description: {}\n\
            Role: {}\n\
            Specialization: {:?}\n\n\
            Your task is to provide helpful, accurate, and thoughtful responses.",
            agent.name,
            agent.description,
            agent.role,
            agent.tags,
        )
    }

    fn create_learning_event(
        &self,
        agent: &Agent,
        success: bool,
        error: Option<&str>,
    ) -> LearningEvent {
        let learning_type = if success {
            LearningType::Success
        } else {
            LearningType::Failure
        };

        let description = match (success, error) {
            (true, _) => format!("Successfully executed task"),
            (false, Some(err)) => format!("Failed to execute task: {}", err),
            (false, None) => "Failed to execute task".to_string(),
        };

        LearningEvent::new(
            agent.id,
            learning_type,
            description,
            "task_execution",
        )
    }
}

#[async_trait]
impl AgentExecutor for DefaultExecutor {
    #[instrument(skip(self, agent, context), fields(agent_id = %agent.id, agent_name = %agent.name))]
    async fn execute(
        &self,
        agent: &mut Agent,
        input: &str,
        context: &ExecutionContext,
    ) -> Result<ExecutionResult> {
        info!("Executing agent {} with input: {}", agent.name, input);
        let start = Instant::now();

        // Update agent status
        agent.set_status(AgentStatus::Busy);

        // Build LLM request
        let system_prompt = self.build_system_prompt(agent);
        let request = LlmRequest::new(&agent.model)
            .with_system(system_prompt)
            .add_message(Message::user(input));

        // Execute LLM request
        match self.llm_client.complete(request).await {
            Ok(response) => {
                let execution_time = start.elapsed().as_millis() as u64;

                info!(
                    "Agent {} completed execution in {}ms, used {} tokens",
                    agent.name,
                    execution_time,
                    response.usage.total_tokens
                );

                // Update agent metrics
                agent.record_task_success(execution_time as f64);
                agent.set_status(AgentStatus::Idle);

                Ok(ExecutionResult::success(
                    response.content,
                    response.usage.total_tokens,
                    execution_time,
                ))
            }
            Err(e) => {
                let execution_time = start.elapsed().as_millis() as u64;
                error!("Agent {} execution failed: {}", agent.name, e);

                agent.record_task_failure();
                agent.set_status(AgentStatus::Error(e.to_string()));

                Ok(ExecutionResult::failure(e.to_string(), execution_time))
            }
        }
    }

    #[instrument(skip(self, agent, context, learning_engine), fields(agent_id = %agent.id))]
    async fn execute_with_learning(
        &self,
        agent: &mut Agent,
        input: &str,
        context: &ExecutionContext,
        learning_engine: &mut LearningEngine,
    ) -> Result<ExecutionResult> {
        let result = self.execute(agent, input, context).await?;

        // Create learning event
        let learning_event = self.create_learning_event(
            agent,
            result.success,
            result.error.as_deref(),
        );

        // Process learning event
        if let Err(e) = learning_engine.process_event(learning_event.clone()) {
            warn!("Failed to process learning event: {}", e);
        } else {
            info!("Learning event processed for agent {}", agent.id);
        }

        Ok(result.with_learning_event(learning_event))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::llm::MockLlmClient;
    use agentic_core::AgentRole;

    #[tokio::test]
    async fn test_executor_success() {
        let llm_client = Arc::new(MockLlmClient::new("Test response"));
        let executor = DefaultExecutor::new(llm_client);

        let mut agent = Agent::new(
            "Test Agent",
            "A test agent",
            AgentRole::Worker,
            "mock-model",
            "mock",
        );

        let context = ExecutionContext::new(agent.id);
        let result = executor.execute(&mut agent, "Test input", &context).await.unwrap();

        assert!(result.success);
        assert_eq!(result.output, "Test response");
        assert_eq!(agent.metrics.tasks_completed, 1);
    }
}
