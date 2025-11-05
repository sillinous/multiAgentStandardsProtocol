//! Multi-Agent Workflow Example
//!
//! This example demonstrates:
//! 1. Creating a supervisor agent
//! 2. Creating multiple worker agents
//! 3. Coordinating a workflow across agents
//! 4. Task scheduling and execution
//!
//! Run with: cargo run --example multi_agent_workflow

use agentic_core::{Agent, AgentRole, WorkflowId};
use agentic_factory::{AgentFactory, AgentRegistry};
use agentic_runtime::{
    executor::{AgentExecutor, DefaultExecutor},
    context::ExecutionContext,
    scheduler::{TaskScheduler, Task, TaskPriority},
    llm::MockLlmClient,
};
use agentic_standards::StandardsAgent;
use std::sync::Arc;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("🤝 Agentic Ecosystem - Multi-Agent Workflow Example\n");

    // Setup
    println!("📋 Step 1: Creating agents...");
    let standards_agent = StandardsAgent::new();
    let factory = AgentFactory::from_registry(standards_agent.registry().clone());
    let mut registry = AgentRegistry::new();

    // Create supervisor
    let (mut supervisor, sup_genome) = factory.create_from_template(
        "tmpl.standard.worker",
        "Supervisor",
        "Coordinates workflow execution",
    )?;
    supervisor.role = AgentRole::Supervisor;
    println!("   ✓ Created supervisor: {}", supervisor.name);

    let supervisor_id = supervisor.id;
    registry.register(supervisor, sup_genome);

    // Create workers
    let worker_specs = vec![
        ("DataCollector", "Collects and validates data"),
        ("DataProcessor", "Processes and transforms data"),
        ("ReportGenerator", "Generates reports from processed data"),
    ];

    let mut worker_ids = Vec::new();
    for (name, desc) in worker_specs {
        let (mut worker, worker_genome) = factory.create_from_template(
            "tmpl.standard.worker",
            name,
            desc,
        )?;
        worker.role = AgentRole::Worker;
        println!("   ✓ Created worker: {}", worker.name);
        worker_ids.push(worker.id);
        registry.register(worker, worker_genome);
    }
    println!();

    // Create workflow
    println!("📝 Step 2: Setting up workflow...");
    let workflow_id = WorkflowId::generate();
    println!("   Workflow ID: {}", workflow_id);
    println!("   Supervisor: {}", registry.get_agent(&supervisor_id.to_string()).unwrap().name);
    println!("   Workers:");
    for id in &worker_ids {
        let agent = registry.get_agent(&id.to_string()).unwrap();
        println!("      - {} ({})", agent.name, agent.description);
    }
    println!();

    // Create task scheduler
    println!("⏱️  Step 3: Creating task scheduler...");
    let scheduler = TaskScheduler::new();
    println!("   ✓ Scheduler ready");
    println!();

    // Create tasks for the workflow
    println!("📋 Step 4: Submitting tasks...");
    let tasks_data = vec![
        (worker_ids[0], "Collect user activity data from last 7 days", TaskPriority::High),
        (worker_ids[0], "Validate data integrity and completeness", TaskPriority::High),
        (worker_ids[1], "Transform data into analysis format", TaskPriority::Normal),
        (worker_ids[1], "Calculate engagement metrics", TaskPriority::Normal),
        (worker_ids[2], "Generate weekly summary report", TaskPriority::Critical),
        (worker_ids[2], "Create visualization charts", TaskPriority::Normal),
    ];

    let mut task_ids = Vec::new();
    for (agent_id, description, priority) in tasks_data {
        let task = Task::new(agent_id, description)
            .with_priority(priority)
            .with_workflow(workflow_id);

        let task_id = scheduler.submit(task)?;
        task_ids.push(task_id.clone());

        let agent = registry.get_agent(&agent_id.to_string()).unwrap();
        println!("   ✓ Task submitted to {}: {}", agent.name, description);
    }
    println!();

    // Execute tasks
    println!("🚀 Step 5: Executing workflow tasks...\n");
    let llm_client = Arc::new(MockLlmClient::new("Task completed successfully"));
    let executor = DefaultExecutor::new(llm_client);

    let mut completed = 0;
    while let Some(mut task) = scheduler.next_task() {
        let agent = registry.get_agent(&task.agent_id.to_string()).unwrap();
        println!("   ⚡ Executing: {} -> {}", agent.name, task.input);

        // Get mutable agent for execution
        let mut agent_clone = agent.clone();
        let context = ExecutionContext::new(agent_clone.id)
            .with_workflow(workflow_id);

        match executor.execute(&mut agent_clone, &task.input, &context).await {
            Ok(result) => {
                if result.success {
                    scheduler.complete_task(&task.id, result.output.clone());
                    completed += 1;
                    println!("      ✓ Completed in {}ms ({} tokens)",
                        result.execution_time_ms, result.tokens_used);
                } else {
                    scheduler.fail_task(&task.id, result.error.unwrap_or_default());
                    println!("      ✗ Failed");
                }
            }
            Err(e) => {
                scheduler.fail_task(&task.id, e.to_string());
                println!("      ✗ Error: {}", e);
            }
        }
        println!();
    }

    // Display workflow statistics
    println!("📊 Step 6: Workflow Statistics");
    println!("   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    let stats = scheduler.stats();
    println!("   Total tasks: {}", stats.total);
    println!("   Completed: {}", stats.completed);
    println!("   Failed: {}", stats.failed);
    println!("   Success rate: {:.1}%",
        (stats.completed as f64 / stats.total as f64) * 100.0);
    println!("   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    println!();

    println!("✅ Workflow example completed!");
    println!();
    println!("💡 Key Concepts Demonstrated:");
    println!("   - Supervisor-worker pattern for coordination");
    println!("   - Priority-based task scheduling");
    println!("   - Workflow-scoped execution contexts");
    println!("   - Distributed task execution across multiple agents");
    println!("   - Centralized metrics and monitoring");

    Ok(())
}
