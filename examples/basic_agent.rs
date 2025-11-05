//! Basic example: Creating and executing an agent
//!
//! This example demonstrates:
//! 1. Creating an agent from a template
//! 2. Setting up an LLM client (using mock for demo)
//! 3. Executing the agent with an input
//! 4. Viewing execution results and metrics
//!
//! Run with: cargo run --example basic_agent

use agentic_core::{Agent, AgentRole};
use agentic_factory::{AgentFactory, AgentRegistry};
use agentic_learning::LearningEngine;
use agentic_runtime::{
    executor::{AgentExecutor, DefaultExecutor},
    context::ExecutionContext,
    llm::MockLlmClient,
};
use agentic_standards::StandardsAgent;
use std::sync::Arc;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("🤖 Agentic Ecosystem - Basic Agent Example\n");

    // Step 1: Create a standards agent and factory
    println!("📋 Step 1: Setting up standards and factory...");
    let standards_agent = StandardsAgent::new();
    let factory = AgentFactory::from_registry(standards_agent.registry().clone());

    // Step 2: Create an agent from template
    println!("🔨 Step 2: Creating agent from template...");
    let (mut agent, genome) = factory.create_from_template(
        "tmpl.standard.worker",
        "DataAnalyzer",
        "An agent that analyzes data and provides insights",
    )?;

    println!("   ✓ Created agent: {} (ID: {})", agent.name, agent.id);
    println!("   ✓ Genome version: {}", genome.version.version);
    println!("   ✓ Specialization: {}", genome.specialization);
    println!("   ✓ Fitness score: {:.2}", genome.fitness_score);
    println!();

    // Step 3: Create executor with mock LLM client
    println!("⚙️  Step 3: Setting up executor with mock LLM...");
    let llm_client = Arc::new(MockLlmClient::new(
        "Based on the provided data, I can see a clear upward trend in user engagement. \
        The key metrics show a 25% increase over the past quarter, with particularly strong \
        growth in the mobile segment."
    ));
    let executor = DefaultExecutor::new(llm_client);
    println!("   ✓ Executor ready");
    println!();

    // Step 4: Create execution context
    println!("📝 Step 4: Creating execution context...");
    let context = ExecutionContext::new(agent.id);
    println!("   ✓ Context created for agent {}", agent.id);
    println!();

    // Step 5: Execute agent
    println!("🚀 Step 5: Executing agent with input...");
    let input = "Please analyze the following data: Q1: 1000 users, Q2: 1150 users, Q3: 1300 users, Q4: 1250 users";
    println!("   Input: {}", input);
    println!();

    let result = executor.execute(&mut agent, input, &context).await?;

    // Step 6: Display results
    println!("📊 Step 6: Execution Results");
    println!("   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    println!("   Success: {}", if result.success { "✓ Yes" } else { "✗ No" });
    println!("   Tokens used: {}", result.tokens_used);
    println!("   Execution time: {}ms", result.execution_time_ms);
    println!();
    println!("   Output:");
    println!("   {}", result.output);
    println!("   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    println!();

    // Step 7: Check agent metrics
    println!("📈 Step 7: Agent Metrics");
    println!("   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    println!("   Tasks completed: {}", agent.metrics.tasks_completed);
    println!("   Tasks failed: {}", agent.metrics.tasks_failed);
    println!("   Success rate: {:.2}%", agent.metrics.success_rate * 100.0);
    println!("   Avg completion time: {:.2}ms", agent.metrics.avg_completion_time_ms);
    println!("   Agent status: {}", agent.status);
    println!("   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    println!();

    println!("✅ Example completed successfully!");
    println!();
    println!("💡 Next steps:");
    println!("   - Try the learning example: cargo run --example agent_learning");
    println!("   - Try the workflow example: cargo run --example multi_agent_workflow");
    println!("   - Start the API server: cargo run -p agentic_api");

    Ok(())
}
