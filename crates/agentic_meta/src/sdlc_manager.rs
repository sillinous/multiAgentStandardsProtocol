//! SDLC Manager - Orchestrates full software development lifecycle

use crate::{
    meta_agent::{MetaAgent, MetaAgentType, MetaAgentCapability, MetaAgentMetrics},
    requirements::{FeatureRequest, AgentRequirement, Priority},
    factory_agent::FactoryMetaAgent,
    code_generator::{CodeGeneratorAgent, CodeGenRequest, GeneratedCode},
    testing_agent::{TestingAgent, TestGenRequest, GeneratedTests, TestType},
};
use agentic_core::{Agent, AgentRole, AgentId, WorkflowId, Result, Error};
use agentic_runtime::llm::LlmClient;
use async_trait::async_trait;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::Arc;
use tracing::{info, debug, warn};

/// SDLC workflow stages
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum SDLCStage {
    Requirements,
    Design,
    Implementation,
    Testing,
    CodeReview,
    Documentation,
    Deployment,
    Completed,
}

impl SDLCStage {
    pub fn as_str(&self) -> &str {
        match self {
            SDLCStage::Requirements => "requirements",
            SDLCStage::Design => "design",
            SDLCStage::Implementation => "implementation",
            SDLCStage::Testing => "testing",
            SDLCStage::CodeReview => "code_review",
            SDLCStage::Documentation => "documentation",
            SDLCStage::Deployment => "deployment",
            SDLCStage::Completed => "completed",
        }
    }

    pub fn next(&self) -> Option<SDLCStage> {
        match self {
            SDLCStage::Requirements => Some(SDLCStage::Design),
            SDLCStage::Design => Some(SDLCStage::Implementation),
            SDLCStage::Implementation => Some(SDLCStage::Testing),
            SDLCStage::Testing => Some(SDLCStage::CodeReview),
            SDLCStage::CodeReview => Some(SDLCStage::Documentation),
            SDLCStage::Documentation => Some(SDLCStage::Deployment),
            SDLCStage::Deployment => Some(SDLCStage::Completed),
            SDLCStage::Completed => None,
        }
    }
}

/// Feature development workflow
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FeatureWorkflow {
    pub workflow_id: WorkflowId,
    pub feature: FeatureRequest,
    pub current_stage: SDLCStage,
    pub stage_outputs: HashMap<String, serde_json::Value>,
    pub assigned_agents: Vec<AgentId>,
    pub start_time: chrono::DateTime<chrono::Utc>,
    pub completion_time: Option<chrono::DateTime<chrono::Utc>>,
}

impl FeatureWorkflow {
    pub fn new(feature: FeatureRequest) -> Self {
        Self {
            workflow_id: WorkflowId::generate(),
            feature,
            current_stage: SDLCStage::Requirements,
            stage_outputs: HashMap::new(),
            assigned_agents: Vec::new(),
            start_time: chrono::Utc::now(),
            completion_time: None,
        }
    }

    pub fn advance_stage(&mut self) -> Result<SDLCStage> {
        if let Some(next_stage) = self.current_stage.next() {
            self.current_stage = next_stage;
            Ok(next_stage)
        } else {
            Err(Error::InvalidState("Workflow already completed".to_string()))
        }
    }

    pub fn is_completed(&self) -> bool {
        self.current_stage == SDLCStage::Completed
    }

    pub fn duration(&self) -> chrono::Duration {
        if let Some(completion) = self.completion_time {
            completion - self.start_time
        } else {
            chrono::Utc::now() - self.start_time
        }
    }
}

/// SDLC development result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DevelopmentResult {
    pub workflow_id: WorkflowId,
    pub feature_name: String,
    pub code: GeneratedCode,
    pub tests: GeneratedTests,
    pub documentation: String,
    pub review_notes: Option<String>,
    pub success: bool,
    pub stages_completed: Vec<SDLCStage>,
}

/// SDLC Manager orchestrates development workflows
pub struct SDLCManager {
    agent: Agent,
    llm_client: Arc<dyn LlmClient>,
    factory: Option<FactoryMetaAgent>,
    active_workflows: HashMap<WorkflowId, FeatureWorkflow>,
    metrics: MetaAgentMetrics,
}

impl SDLCManager {
    /// Create a new SDLC Manager
    pub fn new(llm_client: Arc<dyn LlmClient>) -> Self {
        let mut agent = Agent::new(
            "SDLCManager",
            "Orchestrates full software development lifecycle with specialist agents",
            AgentRole::Supervisor,
            "claude-3-5-sonnet-20241022",
            "anthropic",
        );

        agent.add_tag("meta-agent");
        agent.add_tag("sdlc");
        agent.add_tag("orchestrator");

        Self {
            agent,
            llm_client,
            factory: None,
            active_workflows: HashMap::new(),
            metrics: MetaAgentMetrics::default(),
        }
    }

    /// Set the agent factory for creating specialized agents
    pub fn with_factory(mut self, factory: FactoryMetaAgent) -> Self {
        self.factory = Some(factory);
        self
    }

    /// Get the base agent
    pub fn agent(&self) -> &Agent {
        &self.agent
    }

    /// Execute full SDLC workflow for a feature
    pub async fn develop_feature(&mut self, request: FeatureRequest) -> Result<DevelopmentResult> {
        info!("Starting SDLC workflow for feature: {}", request.description);

        // Create workflow
        let mut workflow = FeatureWorkflow::new(request.clone());
        self.active_workflows.insert(workflow.workflow_id, workflow.clone());

        // Execute each stage
        let mut stages_completed = Vec::new();

        // Stage 1: Requirements Analysis
        workflow.current_stage = SDLCStage::Requirements;
        let requirements = self.analyze_requirements(&request).await?;
        workflow.stage_outputs.insert("requirements".to_string(), serde_json::to_value(&requirements)?);
        stages_completed.push(SDLCStage::Requirements);
        debug!("Requirements analysis completed");

        // Stage 2: Design
        workflow.advance_stage()?;
        let design = self.create_design(&request, &requirements).await?;
        workflow.stage_outputs.insert("design".to_string(), serde_json::to_value(&design)?);
        stages_completed.push(SDLCStage::Design);
        debug!("Design phase completed");

        // Stage 3: Implementation
        workflow.advance_stage()?;
        let code = self.implement_feature(&request, &design).await?;
        workflow.stage_outputs.insert("code".to_string(), serde_json::to_value(&code)?);
        stages_completed.push(SDLCStage::Implementation);
        info!("Implementation completed: {} lines of code generated", code.code.lines().count());

        // Stage 4: Testing
        workflow.advance_stage()?;
        let tests = self.generate_tests(&code, &request).await?;
        workflow.stage_outputs.insert("tests".to_string(), serde_json::to_value(&tests)?);
        stages_completed.push(SDLCStage::Testing);
        info!("Testing completed: {} tests generated", tests.test_count);

        // Stage 5: Code Review
        workflow.advance_stage()?;
        let review_notes = self.review_code(&code, &tests).await?;
        workflow.stage_outputs.insert("review".to_string(), serde_json::json!(review_notes.clone()));
        stages_completed.push(SDLCStage::CodeReview);
        debug!("Code review completed");

        // Stage 6: Documentation
        workflow.advance_stage()?;
        let documentation = self.generate_documentation(&code, &request).await?;
        workflow.stage_outputs.insert("documentation".to_string(), serde_json::json!(documentation.clone()));
        stages_completed.push(SDLCStage::Documentation);
        debug!("Documentation generated");

        // Stage 7: Deployment preparation
        workflow.advance_stage()?;
        self.prepare_deployment(&workflow).await?;
        stages_completed.push(SDLCStage::Deployment);
        debug!("Deployment preparation completed");

        // Mark as completed
        workflow.advance_stage()?;
        workflow.completion_time = Some(chrono::Utc::now());

        // Update metrics
        self.metrics.tasks_executed += 1;
        self.metrics.avg_execution_time_ms = workflow.duration().num_milliseconds() as f64;

        let result = DevelopmentResult {
            workflow_id: workflow.workflow_id,
            feature_name: request.description.clone(),
            code,
            tests,
            documentation,
            review_notes,
            success: true,
            stages_completed,
        };

        info!(
            "SDLC workflow completed for '{}' in {:.2}s",
            request.description,
            workflow.duration().num_milliseconds() as f64 / 1000.0
        );

        // Update workflow
        self.active_workflows.insert(workflow.workflow_id, workflow);

        Ok(result)
    }

    /// Analyze feature requirements
    async fn analyze_requirements(&self, request: &FeatureRequest) -> Result<AgentRequirement> {
        debug!("Analyzing requirements for: {}", request.description);

        // Extract capabilities needed from feature description
        let capabilities = vec![
            "feature_implementation".to_string(),
            "error_handling".to_string(),
        ];

        // Create agent requirement from feature request
        let requirement = AgentRequirement::new(
            request.description.clone(),
            capabilities,
            vec!["production_ready".to_string()],
        );

        Ok(requirement)
    }

    /// Create design for the feature
    async fn create_design(&self, request: &FeatureRequest, _requirements: &AgentRequirement) -> Result<String> {
        debug!("Creating design for: {}", request.description);

        // Use LLM to create design
        use agentic_runtime::llm::{LlmRequest, LlmMessage, MessageRole};

        let llm_request = LlmRequest {
            model: self.agent.model.clone(),
            messages: vec![
                LlmMessage {
                    role: MessageRole::System,
                    content: "You are a software architect. Create a high-level design for the given feature.".to_string(),
                },
                LlmMessage {
                    role: MessageRole::User,
                    content: format!(
                        "Create a design for: {}\n\nPriority: {:?}\nAcceptance Criteria:\n{}",
                        request.description,
                        request.priority,
                        request.acceptance_criteria.join("\n- ")
                    ),
                },
            ],
            temperature: Some(0.4),
            max_tokens: Some(2048),
            tools: None,
        };

        let response = self.llm_client.complete(llm_request).await?;
        Ok(response.content)
    }

    /// Implement the feature
    async fn implement_feature(&self, request: &FeatureRequest, design: &str) -> Result<GeneratedCode> {
        info!("Implementing feature: {}", request.description);

        // Create code generator
        let code_gen = CodeGeneratorAgent::new(self.llm_client.clone());

        // Determine language (default to Rust for this project)
        let language = request.metadata
            .get("language")
            .and_then(|v| v.as_str())
            .unwrap_or("rust");

        // Create code generation request
        let code_request = CodeGenRequest::new(language, &request.description)
            .with_requirements(request.acceptance_criteria.clone())
            .with_context(design)
            .with_tests(false) // Tests generated separately
            .with_docs(false); // Documentation generated separately

        let code = code_gen.generate(code_request).await?;
        Ok(code)
    }

    /// Generate tests for the code
    async fn generate_tests(&self, code: &GeneratedCode, request: &FeatureRequest) -> Result<GeneratedTests> {
        info!("Generating tests for: {}", request.description);

        let test_agent = TestingAgent::new(self.llm_client.clone());

        let test_request = TestGenRequest::new(&code.code, &code.language)
            .with_test_types(vec![
                TestType::Unit,
                TestType::EdgeCase,
                TestType::ErrorHandling,
            ])
            .with_coverage_target(80.0);

        let tests = test_agent.generate_tests(test_request).await?;
        Ok(tests)
    }

    /// Review the generated code
    async fn review_code(&self, code: &GeneratedCode, tests: &GeneratedTests) -> Result<Option<String>> {
        debug!("Reviewing generated code");

        use agentic_runtime::llm::{LlmRequest, LlmMessage, MessageRole};

        let llm_request = LlmRequest {
            model: self.agent.model.clone(),
            messages: vec![
                LlmMessage {
                    role: MessageRole::System,
                    content: "You are an expert code reviewer. Review the code for quality, security, and best practices.".to_string(),
                },
                LlmMessage {
                    role: MessageRole::User,
                    content: format!(
                        "Review this {} code:\n\n```{}\n{}\n```\n\nTests generated: {}\nTest coverage: {:.1}%",
                        code.language,
                        code.language,
                        code.code,
                        tests.test_count,
                        tests.estimated_coverage
                    ),
                },
            ],
            temperature: Some(0.3),
            max_tokens: Some(2048),
            tools: None,
        };

        let response = self.llm_client.complete(llm_request).await?;
        Ok(Some(response.content))
    }

    /// Generate documentation
    async fn generate_documentation(&self, code: &GeneratedCode, request: &FeatureRequest) -> Result<String> {
        debug!("Generating documentation");

        if let Some(docs) = &code.documentation {
            return Ok(docs.clone());
        }

        use agentic_runtime::llm::{LlmRequest, LlmMessage, MessageRole};

        let llm_request = LlmRequest {
            model: self.agent.model.clone(),
            messages: vec![
                LlmMessage {
                    role: MessageRole::System,
                    content: "You are a technical documentation expert. Generate clear, comprehensive documentation.".to_string(),
                },
                LlmMessage {
                    role: MessageRole::User,
                    content: format!(
                        "Generate documentation for:\n\nFeature: {}\n\nCode:\n```{}\n{}\n```",
                        request.description,
                        code.language,
                        code.code
                    ),
                },
            ],
            temperature: Some(0.4),
            max_tokens: Some(2048),
            tools: None,
        };

        let response = self.llm_client.complete(llm_request).await?;
        Ok(response.content)
    }

    /// Prepare for deployment
    async fn prepare_deployment(&self, workflow: &FeatureWorkflow) -> Result<()> {
        debug!("Preparing deployment for workflow: {}", workflow.workflow_id);

        // In a real system, this would:
        // - Create deployment artifacts
        // - Run final integration tests
        // - Generate deployment scripts
        // - Create release notes

        Ok(())
    }

    /// Get active workflows
    pub fn active_workflows(&self) -> &HashMap<WorkflowId, FeatureWorkflow> {
        &self.active_workflows
    }

    /// Get workflow by ID
    pub fn get_workflow(&self, workflow_id: &WorkflowId) -> Option<&FeatureWorkflow> {
        self.active_workflows.get(workflow_id)
    }

    /// Cancel a workflow
    pub fn cancel_workflow(&mut self, workflow_id: &WorkflowId) -> Result<()> {
        if self.active_workflows.remove(workflow_id).is_some() {
            info!("Workflow {} cancelled", workflow_id);
            Ok(())
        } else {
            Err(Error::NotFound(format!("Workflow {} not found", workflow_id)))
        }
    }
}

#[async_trait]
impl MetaAgent for SDLCManager {
    fn meta_type(&self) -> MetaAgentType {
        MetaAgentType::SDLCManager
    }

    fn base_agent(&self) -> &Agent {
        &self.agent
    }

    fn capabilities(&self) -> Vec<MetaAgentCapability> {
        vec![
            MetaAgentCapability {
                name: "develop_feature".to_string(),
                description: "Execute full SDLC workflow for a feature".to_string(),
                inputs: vec!["feature_request".to_string()],
                outputs: vec!["development_result".to_string()],
                estimated_cost: Some(0.50),
            },
            MetaAgentCapability {
                name: "analyze_requirements".to_string(),
                description: "Analyze and refine feature requirements".to_string(),
                inputs: vec!["feature_request".to_string()],
                outputs: vec!["agent_requirement".to_string()],
                estimated_cost: Some(0.05),
            },
            MetaAgentCapability {
                name: "manage_workflow".to_string(),
                description: "Manage and monitor active development workflows".to_string(),
                inputs: vec!["workflow_id".to_string()],
                outputs: vec!["workflow_status".to_string()],
                estimated_cost: Some(0.01),
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
            "develop_feature" => {
                let request: FeatureRequest = serde_json::from_value(
                    params.get("feature_request")
                        .ok_or_else(|| Error::InvalidArgument("Missing feature_request".to_string()))?
                        .clone()
                ).map_err(|e| Error::SerializationError(e.to_string()))?;

                let result = self.develop_feature(request).await?;
                serde_json::to_value(result).map_err(|e| Error::SerializationError(e.to_string()))
            }
            _ => Err(Error::InvalidArgument(format!("Unknown task type: {}", task_type))),
        }
    }

    async fn self_analyze(&self) -> Result<Vec<String>> {
        let mut insights = Vec::new();

        let active_count = self.active_workflows.len();
        if active_count > 10 {
            insights.push(format!("High number of active workflows: {}", active_count));
        }

        if self.metrics.tasks_executed > 0 {
            insights.push(format!(
                "Average workflow duration: {:.2}s",
                self.metrics.avg_execution_time_ms / 1000.0
            ));
        }

        if insights.is_empty() {
            insights.push("SDLC Manager operating normally".to_string());
        }

        Ok(insights)
    }

    async fn self_improve(&mut self, improvement: &str) -> Result<bool> {
        info!("Applying SDLC improvement: {}", improvement);

        match improvement {
            "optimize_workflow" => {
                // Could implement parallel stage execution
                Ok(true)
            }
            "enhance_code_quality" => {
                // Could add more rigorous review criteria
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
    use agentic_runtime::llm::MockLlmClient;

    #[tokio::test]
    async fn test_sdlc_manager_creation() {
        let llm = Arc::new(MockLlmClient::new());
        let manager = SDLCManager::new(llm);
        assert_eq!(manager.agent().name, "SDLCManager");
        assert_eq!(manager.meta_type(), MetaAgentType::SDLCManager);
    }

    #[test]
    fn test_sdlc_stage_progression() {
        assert_eq!(SDLCStage::Requirements.next(), Some(SDLCStage::Design));
        assert_eq!(SDLCStage::Design.next(), Some(SDLCStage::Implementation));
        assert_eq!(SDLCStage::Completed.next(), None);
    }

    #[test]
    fn test_feature_workflow() {
        let feature = FeatureRequest {
            description: "Test feature".to_string(),
            priority: Priority::Normal,
            deadline: None,
            acceptance_criteria: vec![],
            metadata: HashMap::new(),
        };

        let mut workflow = FeatureWorkflow::new(feature);
        assert_eq!(workflow.current_stage, SDLCStage::Requirements);
        assert!(!workflow.is_completed());

        workflow.advance_stage().unwrap();
        assert_eq!(workflow.current_stage, SDLCStage::Design);
    }

    #[tokio::test]
    async fn test_full_sdlc_workflow() {
        let llm = Arc::new(MockLlmClient::new());
        let mut manager = SDLCManager::new(llm);

        let feature = FeatureRequest {
            description: "Add user authentication".to_string(),
            priority: Priority::High,
            deadline: None,
            acceptance_criteria: vec![
                "Support email/password login".to_string(),
                "Include JWT tokens".to_string(),
            ],
            metadata: HashMap::new(),
        };

        let result = manager.develop_feature(feature).await;
        assert!(result.is_ok());

        let dev_result = result.unwrap();
        assert!(dev_result.success);
        assert!(!dev_result.code.code.is_empty());
        assert!(dev_result.tests.test_count > 0);
    }
}
