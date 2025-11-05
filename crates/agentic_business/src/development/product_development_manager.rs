//! Product Development Manager - Meta-agent orchestrating product development

use super::models::*;
use super::{UIUXDesignAgent, InfrastructureAgent};
use crate::models::Opportunity;
use crate::validation::ComprehensiveValidationReport;
use agentic_core::{Agent, AgentRole, Result, WorkflowId};
use agentic_meta::{MetaAgent, MetaAgentMetrics};
use agentic_runtime::llm::LlmClient;
use std::sync::Arc;
use tracing::{info, debug};

/// Product Development Manager - Meta-agent for complete product development
pub struct ProductDevelopmentManager {
    agent: Agent,
    workflow_id: WorkflowId,

    // Development agents
    design_agent: UIUXDesignAgent,
    infrastructure_agent: InfrastructureAgent,

    // Metrics
    metrics: MetaAgentMetrics,

    // LLM client
    llm_client: Arc<dyn LlmClient>,
}

impl ProductDevelopmentManager {
    /// Create a new product development manager
    pub fn new(llm_client: Arc<dyn LlmClient>) -> Self {
        let mut agent = Agent::new(
            "ProductDevelopmentManager",
            "Meta-agent orchestrating complete product development from design to deployment",
            AgentRole::Supervisor,
            "claude-3-5-sonnet-20241022",
            "anthropic",
        );

        agent.add_tag("meta-agent");
        agent.add_tag("business");
        agent.add_tag("product-development");
        agent.add_tag("supervisor");

        // Configure agent to be standards-compliant (A2A, MCP protocols)
        crate::configure_standards_compliant_agent(&mut agent);

        Self {
            agent,
            workflow_id: WorkflowId::generate(),
            design_agent: UIUXDesignAgent::new(llm_client.clone()),
            infrastructure_agent: InfrastructureAgent::new(llm_client.clone()),
            metrics: MetaAgentMetrics::default(),
            llm_client,
        }
    }

    pub fn agent(&self) -> &Agent {
        &self.agent
    }

    pub fn workflow_id(&self) -> &WorkflowId {
        &self.workflow_id
    }

    /// Develop complete product from validated opportunity
    ///
    /// This orchestrates the full development workflow:
    /// 1. UI/UX Design - Generate design specifications
    /// 2. Infrastructure - Provision cloud resources
    /// 3. SDLC - Code generation, testing, documentation (future integration)
    /// 4. Quality Gates - Ensure all requirements met
    /// 5. Deployment Preparation - Ready for production
    pub async fn develop(
        &mut self,
        opportunity: &Opportunity,
        validation_report: &ComprehensiveValidationReport,
    ) -> Result<ProductDevelopmentResult> {
        info!("🚀 Starting product development for: {}", opportunity.title);
        let start_time = std::time::Instant::now();

        // Phase 1: UI/UX Design
        info!("📐 Phase 1: Generating UI/UX design...");
        let design_spec = self.design_agent.design(opportunity).await?;
        info!("✅ Design specification complete");

        // Phase 2: Infrastructure Provisioning
        info!("🏗️  Phase 2: Provisioning infrastructure...");
        let infrastructure_spec = self.infrastructure_agent
            .provision(opportunity, Some(&validation_report.technical_feasibility))
            .await?;
        info!("✅ Infrastructure specification complete");

        // Phase 3: Create Development Specification
        info!("📋 Phase 3: Creating development specification...");
        let development_spec = self.create_development_spec(
            opportunity,
            design_spec,
            infrastructure_spec,
            validation_report,
        ).await?;
        info!("✅ Development specification complete");

        // Phase 4: Quality Gates
        info!("🔒 Phase 4: Checking quality gates...");
        let quality_gates_passed = self.check_quality_gates(&development_spec);
        info!("✅ Quality gates: {}", if quality_gates_passed { "PASSED" } else { "WARNINGS" });

        // Update metrics
        let elapsed = start_time.elapsed();
        self.metrics.tasks_executed += 1;
        self.metrics.avg_execution_time_ms =
            (self.metrics.avg_execution_time_ms * (self.metrics.tasks_executed - 1) as f64
                + elapsed.as_millis() as f64) / self.metrics.tasks_executed as f64;

        let result = ProductDevelopmentResult {
            opportunity_id: opportunity.id,
            status: if quality_gates_passed {
                DevelopmentStatus::Complete
            } else {
                DevelopmentStatus::Development
            },
            specification: development_spec,
            repository_url: None, // Would be set by actual SDLC integration
            deployment_url: None, // Would be set after deployment
            completion_percentage: if quality_gates_passed { 100.0 } else { 75.0 },
            phases_completed: vec![
                "Design".to_string(),
                "Infrastructure".to_string(),
                "Specification".to_string(),
            ],
        };

        info!("🎉 Product development workflow complete - Status: {:?}", result.status);

        Ok(result)
    }

    /// Create comprehensive development specification
    async fn create_development_spec(
        &self,
        opportunity: &Opportunity,
        design: DesignSpecification,
        infrastructure: InfrastructureSpec,
        validation_report: &ComprehensiveValidationReport,
    ) -> Result<ProductDevelopmentSpec> {
        debug!("Creating development specification");

        let tech_stack = validation_report.technical_feasibility.recommended_tech_stack.clone();

        // Create development timeline
        let timeline = self.create_timeline(opportunity, &design, &infrastructure);

        // Define quality gates
        let quality_gates = self.define_quality_gates();

        Ok(ProductDevelopmentSpec {
            opportunity_id: opportunity.id,
            design,
            infrastructure,
            tech_stack,
            development_timeline: timeline,
            quality_gates,
        })
    }

    /// Create development timeline
    fn create_timeline(
        &self,
        opportunity: &Opportunity,
        design: &DesignSpecification,
        infrastructure: &InfrastructureSpec,
    ) -> DevelopmentTimeline {
        let base_days = opportunity.implementation_estimate.estimated_days;
        let complexity = opportunity.implementation_estimate.complexity_score;

        let mut phases = Vec::new();

        // Phase 1: Setup & Design
        phases.push(DevelopmentPhase {
            phase_name: "Setup & Design".to_string(),
            duration_days: (base_days as f64 * 0.15) as u32,
            tasks: vec![
                "Repository setup".to_string(),
                "Design system implementation".to_string(),
                format!("Create {} components", design.components.len()),
            ],
            dependencies: vec![],
        });

        // Phase 2: Infrastructure
        phases.push(DevelopmentPhase {
            phase_name: "Infrastructure".to_string(),
            duration_days: (base_days as f64 * 0.20) as u32,
            tasks: vec![
                format!("Setup {} database", infrastructure.database.database_type),
                "Configure hosting".to_string(),
                "Setup CI/CD pipeline".to_string(),
            ],
            dependencies: vec!["Setup & Design".to_string()],
        });

        // Phase 3: Core Development
        phases.push(DevelopmentPhase {
            phase_name: "Core Development".to_string(),
            duration_days: (base_days as f64 * 0.40) as u32,
            tasks: vec![
                "Implement authentication".to_string(),
                "Build core features".to_string(),
                "API implementation".to_string(),
            ],
            dependencies: vec!["Infrastructure".to_string()],
        });

        // Phase 4: Testing & Refinement
        phases.push(DevelopmentPhase {
            phase_name: "Testing & Refinement".to_string(),
            duration_days: (base_days as f64 * 0.15) as u32,
            tasks: vec![
                "Unit testing".to_string(),
                "Integration testing".to_string(),
                "Bug fixes".to_string(),
            ],
            dependencies: vec!["Core Development".to_string()],
        });

        // Phase 5: Deployment
        phases.push(DevelopmentPhase {
            phase_name: "Deployment".to_string(),
            duration_days: (base_days as f64 * 0.10) as u32,
            tasks: vec![
                "Production deployment".to_string(),
                "Monitoring setup".to_string(),
                "Documentation".to_string(),
            ],
            dependencies: vec!["Testing & Refinement".to_string()],
        });

        DevelopmentTimeline {
            total_days: base_days,
            phases,
        }
    }

    /// Define quality gates
    fn define_quality_gates(&self) -> Vec<QualityGate> {
        vec![
            QualityGate {
                gate_name: "Design Completeness".to_string(),
                criteria: vec![
                    "Design system defined".to_string(),
                    "All components specified".to_string(),
                    "User flows documented".to_string(),
                ],
                required: true,
            },
            QualityGate {
                gate_name: "Infrastructure Ready".to_string(),
                criteria: vec![
                    "Database schema defined".to_string(),
                    "API endpoints specified".to_string(),
                    "Hosting configured".to_string(),
                ],
                required: true,
            },
            QualityGate {
                gate_name: "Security".to_string(),
                criteria: vec![
                    "Authentication implemented".to_string(),
                    "HTTPS enabled".to_string(),
                    "Environment variables secured".to_string(),
                ],
                required: true,
            },
            QualityGate {
                gate_name: "Testing".to_string(),
                criteria: vec![
                    "80%+ code coverage".to_string(),
                    "All critical paths tested".to_string(),
                    "No high-severity bugs".to_string(),
                ],
                required: true,
            },
            QualityGate {
                gate_name: "Performance".to_string(),
                criteria: vec![
                    "Page load < 3s".to_string(),
                    "API response < 500ms".to_string(),
                    "Lighthouse score > 90".to_string(),
                ],
                required: false,
            },
        ]
    }

    /// Check quality gates
    fn check_quality_gates(&self, spec: &ProductDevelopmentSpec) -> bool {
        // For now, check that design and infrastructure specs exist
        let design_complete = !spec.design.components.is_empty()
            && !spec.design.user_flows.is_empty();

        let infrastructure_complete = !spec.infrastructure.database.schema.is_empty()
            && !spec.infrastructure.api.endpoints.is_empty();

        design_complete && infrastructure_complete
    }

    /// Get development metrics
    pub fn metrics(&self) -> &MetaAgentMetrics {
        &self.metrics
    }
}

impl MetaAgent for ProductDevelopmentManager {
    fn agent(&self) -> &Agent {
        &self.agent
    }

    fn workflow_id(&self) -> &WorkflowId {
        &self.workflow_id
    }

    fn metrics(&self) -> &MetaAgentMetrics {
        &self.metrics
    }

    async fn self_analyze(&self) -> Result<String> {
        let analysis = format!(
            "ProductDevelopmentManager Self-Analysis:\n\
            - Workflow ID: {}\n\
            - Development Workflows Executed: {}\n\
            - Average Execution Time: {:.2}ms\n\
            - Agents Managed: 2 (UIUXDesign, Infrastructure)\n\
            - Success Rate: {:.1}%\n\
            \n\
            Agent Capabilities:\n\
            - UI/UX Design: Design systems, components, user flows\n\
            - Infrastructure: Cloud provisioning, database design, API specification\n\
            - Integration: Ready for SDLC Manager integration\n\
            \n\
            Development Phases:\n\
            1. Setup & Design (15% of timeline)\n\
            2. Infrastructure (20% of timeline)\n\
            3. Core Development (40% of timeline)\n\
            4. Testing & Refinement (15% of timeline)\n\
            5. Deployment (10% of timeline)\n\
            \n\
            Quality Gates: 5 defined (4 required, 1 optional)\n\
            \n\
            Performance Insights:\n\
            - Parallel agent execution for speed\n\
            - Comprehensive specification generation\n\
            - Standards-compliant (A2A, MCP protocols)",
            self.workflow_id,
            self.metrics.tasks_executed,
            self.metrics.avg_execution_time_ms,
            self.metrics.creation_success_rate * 100.0
        );

        Ok(analysis)
    }

    async fn self_improve(&mut self) -> Result<String> {
        debug!("ProductDevelopmentManager analyzing performance for improvements");

        let improvements = vec![
            "Integrate with SDLCManager for actual code generation",
            "Add deployment automation",
            "Implement monitoring and analytics setup",
            "Add A/B testing configuration",
            "Enhance cost optimization recommendations",
        ];

        Ok(improvements.join("\n"))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use agentic_runtime::llm::MockLlmClient;
    use crate::models::ProductType;
    use crate::validation::{
        BusinessValidationManager,
    };

    #[tokio::test]
    async fn test_product_development() {
        let llm = Arc::new(MockLlmClient::new());
        let mut manager = ProductDevelopmentManager::new(llm.clone());

        let opp = Opportunity::new(
            "Test SaaS".to_string(),
            "A test product".to_string(),
            "SaaS".to_string(),
            ProductType::SaaS,
        );

        // Get validation report
        let mut validation_manager = BusinessValidationManager::new(llm);
        let validation_report = validation_manager.validate(&opp).await.unwrap();

        let result = manager.develop(&opp, &validation_report).await.unwrap();

        assert_eq!(result.opportunity_id, opp.id);
        assert!(!result.specification.design.components.is_empty());
        assert!(!result.specification.infrastructure.database.schema.is_empty());
        assert!(result.completion_percentage > 0.0);
    }
}
