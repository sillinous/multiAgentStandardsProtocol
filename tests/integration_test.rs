//! Integration tests for the Agentic Forge

use agentic_core::{Agent, AgentRole};
use agentic_domain::{
    agent_genome::{AgentGenome, Trait},
    learning::{LearningEvent, LearningType},
};
use agentic_factory::{AgentFactory, AgentRegistry};
use agentic_learning::LearningEngine;
use agentic_runtime::{
    executor::{AgentExecutor, DefaultExecutor},
    context::ExecutionContext,
    scheduler::{TaskScheduler, Task, TaskPriority},
    llm::MockLlmClient,
};
use agentic_standards::StandardsAgent;
use std::sync::Arc;

#[tokio::test]
async fn test_agent_creation_and_execution() {
    // Setup
    let standards_agent = StandardsAgent::new();
    let factory = AgentFactory::from_registry(standards_agent.registry().clone());

    // Create agent
    let (mut agent, genome) = factory
        .create_from_template(
            "tmpl.standard.worker",
            "TestAgent",
            "A test agent",
        )
        .expect("Failed to create agent");

    assert_eq!(agent.name, "TestAgent");
    assert_eq!(agent.role, AgentRole::Worker);
    assert_eq!(genome.specialization, "Standard Worker");

    // Create executor
    let llm_client = Arc::new(MockLlmClient::new("Test response"));
    let executor = DefaultExecutor::new(llm_client);

    // Execute
    let context = ExecutionContext::new(agent.id);
    let result = executor
        .execute(&mut agent, "Test input", &context)
        .await
        .expect("Execution failed");

    assert!(result.success);
    assert_eq!(result.output, "Test response");
    assert_eq!(agent.metrics.tasks_completed, 1);
}

#[tokio::test]
async fn test_learning_system() {
    // Setup
    let standards_agent = StandardsAgent::new();
    let factory = AgentFactory::from_registry(standards_agent.registry().clone());
    let mut learning_engine = LearningEngine::new();

    let (agent, _genome) = factory
        .create_from_template(
            "tmpl.standard.worker",
            "LearningAgent",
            "An agent that learns",
        )
        .expect("Failed to create agent");

    // Record learning events
    let event1 = LearningEvent::new(
        agent.id,
        LearningType::Success,
        "Successfully completed task",
        "task_execution",
    );

    let event2 = LearningEvent::new(
        agent.id,
        LearningType::Failure,
        "Failed to parse input",
        "error_handling",
    );

    learning_engine.process_event(event1).expect("Failed to process event");
    learning_engine.process_event(event2).expect("Failed to process event");

    // Verify
    assert_eq!(learning_engine.total_events_processed, 2);
    assert!(learning_engine.success_rate > 0.0);
    assert!(learning_engine.learning_by_agent.contains_key(&agent.id));
}

#[tokio::test]
async fn test_agent_genome_mutation() {
    let agent_id = agentic_core::AgentId::generate();
    let mut genome = AgentGenome::new(agent_id, "test_specialization");

    // Add trait
    let trait_obj = Trait::new("reasoning_style", serde_json::json!("analytical"));
    genome.add_trait(trait_obj);

    // Verify trait
    assert!(genome.get_trait("reasoning_style").is_some());

    // Create mutation
    let mutation = agentic_domain::agent_genome::TraitMutation::new(
        "reasoning_style",
        serde_json::json!("analytical"),
        serde_json::json!("creative"),
        "Improve creativity",
    )
    .with_fitness_delta(0.1)
    .accept();

    // Apply mutation
    genome.apply_mutation(mutation).expect("Failed to apply mutation");

    // Verify
    assert_eq!(genome.mutation_attempts, 1);
    assert_eq!(genome.successful_mutations, 1);
    assert!(genome.fitness_score > 0.5);
}

#[tokio::test]
async fn test_task_scheduler() {
    let scheduler = TaskScheduler::new();
    let agent_id = agentic_core::AgentId::generate();

    // Create tasks with different priorities
    let task1 = Task::new(agent_id, "Low priority task")
        .with_priority(TaskPriority::Low);
    let task2 = Task::new(agent_id, "High priority task")
        .with_priority(TaskPriority::High);
    let task3 = Task::new(agent_id, "Critical task")
        .with_priority(TaskPriority::Critical);

    // Submit tasks
    scheduler.submit(task1).expect("Failed to submit task1");
    scheduler.submit(task2).expect("Failed to submit task2");
    scheduler.submit(task3).expect("Failed to submit task3");

    // Verify order (critical should come first)
    let next1 = scheduler.next_task().expect("No task available");
    assert_eq!(next1.priority, TaskPriority::Critical);

    let next2 = scheduler.next_task().expect("No task available");
    assert_eq!(next2.priority, TaskPriority::High);

    let next3 = scheduler.next_task().expect("No task available");
    assert_eq!(next3.priority, TaskPriority::Low);
}

#[tokio::test]
async fn test_multi_agent_workflow() {
    // Setup
    let standards_agent = StandardsAgent::new();
    let factory = AgentFactory::from_registry(standards_agent.registry().clone());
    let mut registry = AgentRegistry::new();

    // Create supervisor
    let (mut supervisor, sup_genome) = factory
        .create_from_template(
            "tmpl.standard.worker",
            "Supervisor",
            "Coordinates workflow",
        )
        .expect("Failed to create supervisor");
    supervisor.role = AgentRole::Supervisor;
    let supervisor_id = supervisor.id;
    registry.register(supervisor, sup_genome);

    // Create workers
    let mut worker_ids = Vec::new();
    for i in 0..3 {
        let (mut worker, worker_genome) = factory
            .create_from_template(
                "tmpl.standard.worker",
                &format!("Worker-{}", i + 1),
                "Worker agent",
            )
            .expect("Failed to create worker");
        worker.role = AgentRole::Worker;
        worker_ids.push(worker.id);
        registry.register(worker, worker_genome);
    }

    // Verify
    assert!(registry.get_agent(&supervisor_id.to_string()).is_some());
    assert_eq!(worker_ids.len(), 3);

    for worker_id in &worker_ids {
        assert!(registry.get_agent(&worker_id.to_string()).is_some());
    }
}

#[tokio::test]
async fn test_execution_with_learning() {
    // Setup
    let standards_agent = StandardsAgent::new();
    let factory = AgentFactory::from_registry(standards_agent.registry().clone());
    let mut learning_engine = LearningEngine::new();

    let (mut agent, _genome) = factory
        .create_from_template(
            "tmpl.standard.worker",
            "TestAgent",
            "A test agent",
        )
        .expect("Failed to create agent");

    let llm_client = Arc::new(MockLlmClient::new("Success response"));
    let executor = DefaultExecutor::new(llm_client);
    let context = ExecutionContext::new(agent.id);

    // Execute with learning
    let result = executor
        .execute_with_learning(&mut agent, "Test input", &context, &mut learning_engine)
        .await
        .expect("Execution failed");

    // Verify
    assert!(result.success);
    assert!(!result.learning_events.is_empty());
    assert_eq!(learning_engine.total_events_processed, 1);
    assert_eq!(agent.metrics.tasks_completed, 1);
}

#[tokio::test]
async fn test_agent_metrics() {
    let mut agent = Agent::new(
        "MetricsAgent",
        "Testing metrics",
        AgentRole::Worker,
        "mock-model",
        "mock",
    );

    // Record successful tasks
    agent.record_task_success(100.0);
    agent.record_task_success(200.0);
    agent.record_task_success(300.0);

    // Record failure
    agent.record_task_failure();

    // Verify metrics
    assert_eq!(agent.metrics.tasks_completed, 3);
    assert_eq!(agent.metrics.tasks_failed, 1);
    assert_eq!(agent.metrics.avg_completion_time_ms, 200.0);
    assert_eq!(agent.metrics.success_rate, 0.75);
}

#[tokio::test]
async fn test_genome_versioning() {
    let agent_id = agentic_core::AgentId::generate();
    let mut genome = AgentGenome::new(agent_id, "test_spec");

    let initial_version = genome.version.version.clone();
    assert_eq!(initial_version, "1.0.0");

    // Checkpoint
    genome.checkpoint("Added new capability");

    // Verify version bumped
    assert_ne!(genome.version.version, initial_version);
    assert_eq!(genome.version.parent_version, Some(initial_version));
}

#[test]
fn test_standards_compliance() {
    let standards_agent = StandardsAgent::new();
    let factory = AgentFactory::from_registry(standards_agent.registry().clone());

    let (agent, _genome) = factory
        .create_from_template(
            "tmpl.standard.worker",
            "ComplianceAgent",
            "Testing compliance",
        )
        .expect("Failed to create agent");

    let report = standards_agent
        .compliance_for_template("tmpl.standard.worker", &agent)
        .expect("Failed to get compliance report");

    // Should be compliant as it was created from template
    assert!(report.compliant, "Agent should be compliant with standards");
    assert!(report.missing_protocols.is_empty());
}

#[test]
fn test_agent_registry_operations() {
    let mut registry = AgentRegistry::new();

    let agent = Agent::new(
        "RegistryAgent",
        "Testing registry",
        AgentRole::Worker,
        "mock-model",
        "mock",
    );

    let agent_id = agent.id;
    let genome = AgentGenome::new(agent_id, "test");

    // Register
    registry.register(agent.clone(), genome.clone());

    // Retrieve
    let retrieved = registry.get_agent(&agent_id.to_string());
    assert!(retrieved.is_some());
    assert_eq!(retrieved.unwrap().name, "RegistryAgent");

    // Get genome
    let retrieved_genome = registry.get_genome(&agent_id.to_string());
    assert!(retrieved_genome.is_some());

    // List
    let agents = registry.list_agents();
    assert_eq!(agents.len(), 1);

    // Remove
    assert!(registry.remove(&agent_id.to_string()));
    assert!(registry.get_agent(&agent_id.to_string()).is_none());
}
