//! Meta-Agent Factory Example
//!
//! This example demonstrates the meta-agent system where agents create and manage other agents.
//! It shows the self-hosting capability - the system using itself to create new functionality.

use agentic_meta::{
    meta_agent::{MetaAgent, MetaAgentType},
    factory_agent::FactoryMetaAgent,
    requirements::{AgentRequirement, QualityRequirements, WorkloadSpec, Priority},
};
use agentic_standards::StandardsAgent;
use agentic_runtime::{
    executor::{AgentExecutor, DefaultExecutor, ExecutionContext},
    llm::{MockLlmClient, LlmClient},
};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Initialize tracing
    tracing_subscriber::fmt()
        .with_max_level(tracing::Level::INFO)
        .init();

    println!("🏭 Meta-Agent Factory Demo");
    println!("==========================\n");

    // 1. Initialize the standards registry
    println!("📋 Step 1: Initializing Standards Registry...");
    let standards = StandardsAgent::new();
    println!("   ✓ Standards registry ready with {} standards\n",
        standards.registry().standards().len());

    // 2. Create the factory meta-agent
    println!("🤖 Step 2: Creating Factory Meta-Agent...");
    let mut factory = FactoryMetaAgent::new(standards.registry().clone());
    println!("   ✓ Factory meta-agent created");
    println!("   • Type: {:?}", factory.meta_type());
    println!("   • Base Agent: {}", factory.base_agent().name);
    println!("   • Capabilities: {}", factory.capabilities().len());
    println!();

    // 3. Display factory capabilities
    println!("💡 Step 3: Factory Capabilities:");
    for (i, cap) in factory.capabilities().iter().enumerate() {
        println!("   {}. {} - {}", i + 1, cap.name, cap.description);
        if let Some(cost) = cap.estimated_cost {
            println!("      Cost: ${:.3} per operation", cost);
        }
    }
    println!();

    // 4. Define requirements for different types of agents
    println!("📝 Step 4: Defining Agent Requirements...\n");

    // 4a. Data Analysis Agent
    println!("   Creating requirement for Data Analysis Agent...");
    let data_analyst_req = AgentRequirement::new(
        "Analyze financial data and generate insights",
        vec![
            "data_analysis".to_string(),
            "statistics".to_string(),
            "visualization".to_string(),
        ],
        vec![
            "max_memory:4GB".to_string(),
            "timeout:300s".to_string(),
        ],
    )
    .with_quality(QualityRequirements {
        min_accuracy: Some(0.95),
        max_latency_ms: Some(5000),
        max_cost_per_task: Some(0.10),
        min_success_rate: Some(0.98),
    })
    .with_workload(WorkloadSpec {
        estimated_tasks_per_hour: 50,
        peak_tasks_per_hour: Some(100),
        avg_task_duration_ms: 2000,
        concurrency_level: 5,
    });

    // 4b. Code Review Agent
    println!("   Creating requirement for Code Review Agent...");
    let code_reviewer_req = AgentRequirement::new(
        "Review code for quality, security, and best practices",
        vec![
            "code_review".to_string(),
            "security_analysis".to_string(),
            "style_checking".to_string(),
        ],
        vec![
            "languages:rust,python,javascript".to_string(),
            "max_file_size:1MB".to_string(),
        ],
    )
    .with_quality(QualityRequirements {
        min_accuracy: Some(0.90),
        max_latency_ms: Some(10000),
        max_cost_per_task: Some(0.25),
        min_success_rate: Some(0.95),
    })
    .with_model("claude-3-5-sonnet-20241022");

    // 4c. Testing Agent
    println!("   Creating requirement for Testing Agent...");
    let tester_req = AgentRequirement::new(
        "Write comprehensive unit and integration tests",
        vec![
            "test_generation".to_string(),
            "coverage_analysis".to_string(),
            "test_execution".to_string(),
        ],
        vec![
            "frameworks:pytest,jest,cargo-test".to_string(),
            "min_coverage:80%".to_string(),
        ],
    )
    .with_quality(QualityRequirements {
        min_accuracy: Some(0.85),
        max_latency_ms: Some(15000),
        max_cost_per_task: Some(0.15),
        min_success_rate: Some(0.90),
    })
    .with_model("claude-3-5-haiku-20241022"); // Use cost-effective model

    // 4d. Documentation Agent
    println!("   Creating requirement for Documentation Agent...");
    let doc_writer_req = AgentRequirement::simple(
        "Generate clear and comprehensive documentation",
        vec![
            "documentation".to_string(),
            "markdown_generation".to_string(),
            "api_docs".to_string(),
        ],
    );

    println!("   ✓ All requirements defined\n");

    // 5. Create agents using the factory
    println!("🔨 Step 5: Creating Agents from Requirements...\n");

    // Create Data Analyst
    println!("   Creating Data Analysis Agent...");
    let (data_analyst, analyst_genome) = factory
        .create_from_requirements(&data_analyst_req)
        .await?;
    println!("   ✓ Created: {} (ID: {})", data_analyst.name, data_analyst.id);
    println!("     • Model: {} / {}", data_analyst.model, data_analyst.provider);
    println!("     • Role: {:?}", data_analyst.role);
    println!("     • Genome Traits: {}", analyst_genome.traits.len());
    println!("     • Genome Specialization: {}", analyst_genome.specialization);
    println!();

    // Create Code Reviewer
    println!("   Creating Code Review Agent...");
    let (code_reviewer, reviewer_genome) = factory
        .create_from_requirements(&code_reviewer_req)
        .await?;
    println!("   ✓ Created: {} (ID: {})", code_reviewer.name, code_reviewer.id);
    println!("     • Model: {} / {}", code_reviewer.model, code_reviewer.provider);
    println!("     • Role: {:?}", code_reviewer.role);
    println!("     • Genome Traits: {}", reviewer_genome.traits.len());
    println!();

    // Create Tester
    println!("   Creating Testing Agent...");
    let (tester, tester_genome) = factory
        .create_from_requirements(&tester_req)
        .await?;
    println!("   ✓ Created: {} (ID: {})", tester.name, tester.id);
    println!("     • Model: {} / {}", tester.model, tester.provider);
    println!("     • Genome Traits: {}", tester_genome.traits.len());
    println!();

    // Create Documentation Writer
    println!("   Creating Documentation Agent...");
    let (doc_writer, doc_genome) = factory
        .create_from_requirements(&doc_writer_req)
        .await?;
    println!("   ✓ Created: {} (ID: {})", doc_writer.name, doc_writer.id);
    println!("     • Genome Traits: {}", doc_genome.traits.len());
    println!();

    // 6. Display factory metrics
    println!("📊 Step 6: Factory Performance Metrics:");
    let metrics = factory.metrics();
    println!("   • Agents Created: {}", metrics.agents_created);
    println!("   • Avg Creation Time: {:.2}ms", metrics.avg_creation_time_ms);
    println!("   • Success Rate: {:.1}%", metrics.creation_success_rate * 100.0);
    println!("   • Tasks Executed: {}", metrics.tasks_executed);
    println!();

    // 7. Display list of created agents
    println!("📋 Step 7: Created Agents Registry:");
    let created_ids = factory.created_agents();
    println!("   Total agents created by this factory: {}", created_ids.len());
    for (i, agent_id) in created_ids.iter().enumerate() {
        println!("   {}. {}", i + 1, agent_id);
    }
    println!();

    // 8. Self-analysis - Factory reflects on its performance
    println!("🔍 Step 8: Factory Self-Analysis...");
    let insights = factory.self_analyze().await?;
    println!("   Factory insights:");
    for (i, insight) in insights.iter().enumerate() {
        println!("   {}. {}", i + 1, insight);
    }
    println!();

    // 9. Demonstrate agent execution with the created agents
    println!("🚀 Step 9: Executing Created Agents...\n");

    // Setup executor with mock LLM for demo
    let llm_client = MockLlmClient::new();
    let executor = DefaultExecutor::new(Box::new(llm_client));

    // Execute data analyst
    println!("   Executing Data Analysis Agent...");
    let mut data_analyst_mut = data_analyst;
    let context = ExecutionContext::new()
        .with_metadata("source", "demo")
        .with_metadata("environment", "development");

    let result = executor
        .execute(
            &mut data_analyst_mut,
            "Analyze the quarterly revenue data and identify trends",
            &context,
        )
        .await?;

    println!("   ✓ Data Analyst Result:");
    println!("     • Status: {:?}", result.status);
    println!("     • Duration: {}ms", result.duration.as_millis());
    println!("     • Token Usage: {} tokens", result.tokens_used);
    println!("     • Output: {}", result.output);
    println!();

    // Execute code reviewer
    println!("   Executing Code Review Agent...");
    let mut reviewer_mut = code_reviewer;
    let review_result = executor
        .execute(
            &mut reviewer_mut,
            "Review this function for potential security vulnerabilities",
            &context,
        )
        .await?;

    println!("   ✓ Code Reviewer Result:");
    println!("     • Status: {:?}", review_result.status);
    println!("     • Duration: {}ms", review_result.duration.as_millis());
    println!("     • Output: {}", review_result.output);
    println!();

    // 10. Demonstrate meta-task execution
    println!("🎯 Step 10: Executing Meta-Tasks...\n");

    let mut params = std::collections::HashMap::new();
    params.insert(
        "requirement".to_string(),
        serde_json::to_value(&AgentRequirement::simple(
            "Monitor system performance",
            vec!["monitoring".to_string(), "alerting".to_string()],
        ))?,
    );

    println!("   Executing meta-task: create_agent");
    let meta_result = factory
        .execute_meta_task("create_agent", params)
        .await?;

    println!("   ✓ Meta-task Result:");
    println!("{}", serde_json::to_string_pretty(&meta_result)?);
    println!();

    // 11. Final summary
    println!("📈 Step 11: Final Summary");
    println!("========================");
    println!();
    println!("The Meta-Agent Factory has successfully demonstrated:");
    println!("  ✓ Self-hosting capability - System creating its own agents");
    println!("  ✓ Requirement-driven agent creation");
    println!("  ✓ Intelligent model selection based on cost/performance");
    println!("  ✓ Genome generation with specialized traits");
    println!("  ✓ Quality-aware configuration");
    println!("  ✓ Performance tracking and metrics");
    println!("  ✓ Self-analysis and introspection");
    println!("  ✓ Agent execution and task completion");
    println!();
    println!("Total agents created: {}", factory.created_agents().len());
    println!("Factory success rate: {:.1}%", factory.metrics().creation_success_rate * 100.0);
    println!();
    println!("🎉 Meta-Agent Factory Demo Complete!");

    Ok(())
}
