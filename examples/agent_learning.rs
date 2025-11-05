//! Agent Learning Example
//!
//! This example demonstrates:
//! 1. Creating an agent with learning capabilities
//! 2. Executing tasks and recording learning events
//! 3. Processing learning events to improve agent performance
//! 4. Viewing learning statistics and insights
//!
//! Run with: cargo run --example agent_learning

use agentic_core::{Agent, AgentRole};
use agentic_domain::learning::{LearningEvent, LearningType};
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
    println!("🧠 Agentic Ecosystem - Agent Learning Example\n");

    // Setup
    println!("📋 Setting up environment...");
    let standards_agent = StandardsAgent::new();
    let factory = AgentFactory::from_registry(standards_agent.registry().clone());
    let mut learning_engine = LearningEngine::new();

    // Create agent
    let (mut agent, genome) = factory.create_from_template(
        "tmpl.standard.worker",
        "LearningAgent",
        "An agent that learns from experience",
    )?;

    println!("   ✓ Created agent: {}", agent.name);
    println!();

    // Create executor
    let llm_client = Arc::new(MockLlmClient::new("Task completed successfully!"));
    let executor = DefaultExecutor::new(llm_client);
    let context = ExecutionContext::new(agent.id);

    // Execute multiple tasks with learning
    println!("🚀 Executing tasks and recording learning events...\n");

    let tasks = vec![
        ("Analyze user behavior patterns", true),
        ("Generate monthly report", true),
        ("Process invalid data", false),
        ("Optimize database queries", true),
        ("Handle malformed JSON", false),
        ("Create data visualization", true),
    ];

    for (i, (task_description, should_succeed)) in tasks.iter().enumerate() {
        println!("   Task {}: {}", i + 1, task_description);

        let result = executor
            .execute_with_learning(&mut agent, task_description, &context, &mut learning_engine)
            .await?;

        if *should_succeed {
            println!("      ✓ Success - {}ms, {} tokens",
                result.execution_time_ms, result.tokens_used);
        } else {
            println!("      ✗ Failed (simulated) - {}ms", result.execution_time_ms);

            // Record a failure learning event
            let failure_event = LearningEvent::new(
                agent.id,
                LearningType::Failure,
                format!("Failed to handle: {}", task_description),
                "error_handling",
            );
            learning_engine.process_event(failure_event)?;
        }
        println!();
    }

    // Display learning statistics
    println!("📊 Learning Statistics");
    println!("   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    println!("   Total events: {}", learning_engine.total_events_processed);
    println!("   Success rate: {:.1}%", learning_engine.success_rate * 100.0);

    if let Some(agent_learnings) = learning_engine.learning_by_agent.get(&agent.id) {
        println!("   Agent-specific learnings: {}", agent_learnings.len());
        println!();
        println!("   Recent learning events:");
        for (i, event) in agent_learnings.iter().take(3).enumerate() {
            println!("      {}. [{}] {} (confidence: {:.2})",
                i + 1,
                match event.learning_type {
                    LearningType::Success => "SUCCESS",
                    LearningType::Failure => "FAILURE",
                    LearningType::Pattern => "PATTERN",
                    LearningType::Insight => "INSIGHT",
                },
                event.description,
                event.confidence,
            );
        }
    }
    println!("   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    println!();

    // Display agent metrics
    println!("📈 Agent Performance Metrics");
    println!("   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    println!("   Tasks completed: {}", agent.metrics.tasks_completed);
    println!("   Tasks failed: {}", agent.metrics.tasks_failed);
    println!("   Success rate: {:.1}%", agent.metrics.success_rate * 100.0);
    println!("   Avg completion time: {:.2}ms", agent.metrics.avg_completion_time_ms);
    println!("   Fitness score: {:.3}", agent.fitness_score);
    println!("   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    println!();

    println!("✅ Learning example completed!");
    println!();
    println!("💡 Key Insights:");
    println!("   - Agents automatically record learning events during execution");
    println!("   - Learning engine aggregates and analyzes patterns");
    println!("   - Success rates and metrics inform future improvements");
    println!("   - Learning can be shared across agents (knowledge transfer)");

    Ok(())
}
