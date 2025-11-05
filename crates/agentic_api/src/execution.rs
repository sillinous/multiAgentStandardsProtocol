//! Agent execution endpoints

use crate::AppState;
use axum::{extract::{Path, State}, Json};
use serde::{Deserialize, Serialize};
use tracing::{info, error};
use agentic_runtime::{
    executor::AgentExecutor,
    context::ExecutionContext,
    scheduler::{Task, TaskPriority},
};

#[derive(Deserialize)]
pub struct ExecuteAgentReq {
    pub input: String,
    #[serde(default)]
    pub with_learning: bool,
}

#[derive(Serialize)]
pub struct ExecuteAgentRes {
    pub success: bool,
    pub output: String,
    pub error: Option<String>,
    pub tokens_used: usize,
    pub execution_time_ms: u64,
    pub learning_events_count: usize,
}

/// Execute an agent directly
pub async fn api_agent_execute(
    State(state): State<AppState>,
    Path(id): Path<String>,
    Json(req): Json<ExecuteAgentReq>,
) -> Json<ExecuteAgentRes> {
    info!("Executing agent {} with input: {}", id, req.input);

    // Get agent from registry
    let agent_opt = state.registry.lock().unwrap().get_agent(&id).cloned();

    let Some(mut agent) = agent_opt else {
        error!("Agent {} not found", id);
        return Json(ExecuteAgentRes {
            success: false,
            output: String::new(),
            error: Some(format!("Agent {} not found", id)),
            tokens_used: 0,
            execution_time_ms: 0,
            learning_events_count: 0,
        });
    };

    // Create execution context
    let context = ExecutionContext::new(agent.id);

    // Execute agent
    let result = if req.with_learning {
        let mut learning_engine = state.learning_engine.lock().unwrap();
        state.executor
            .execute_with_learning(&mut agent, &req.input, &context, &mut learning_engine)
            .await
    } else {
        state.executor
            .execute(&mut agent, &req.input, &context)
            .await
    };

    match result {
        Ok(exec_result) => {
            // Update agent in registry
            state.registry.lock().unwrap().register(agent,
                state.registry.lock().unwrap().get_genome(&id).unwrap().clone()
            );

            Json(ExecuteAgentRes {
                success: exec_result.success,
                output: exec_result.output,
                error: exec_result.error,
                tokens_used: exec_result.tokens_used,
                execution_time_ms: exec_result.execution_time_ms,
                learning_events_count: exec_result.learning_events.len(),
            })
        }
        Err(e) => {
            error!("Execution error: {}", e);
            Json(ExecuteAgentRes {
                success: false,
                output: String::new(),
                error: Some(e.to_string()),
                tokens_used: 0,
                execution_time_ms: 0,
                learning_events_count: 0,
            })
        }
    }
}

#[derive(Deserialize)]
pub struct CreateTaskReq {
    pub agent_id: String,
    pub input: String,
    #[serde(default)]
    pub priority: String, // "low", "normal", "high", "critical"
    pub workflow_id: Option<String>,
}

#[derive(Serialize)]
pub struct CreateTaskRes {
    pub task_id: String,
}

/// Create a new task
pub async fn api_tasks_create(
    State(state): State<AppState>,
    Json(req): Json<CreateTaskReq>,
) -> Json<Result<CreateTaskRes, String>> {
    let agent_id = match req.agent_id.parse() {
        Ok(id) => id,
        Err(_) => return Json(Err("Invalid agent ID".to_string())),
    };

    let priority = match req.priority.as_str() {
        "low" => TaskPriority::Low,
        "normal" => TaskPriority::Normal,
        "high" => TaskPriority::High,
        "critical" => TaskPriority::Critical,
        _ => TaskPriority::Normal,
    };

    let mut task = Task::new(agent_id, req.input).with_priority(priority);

    if let Some(wf_id) = req.workflow_id {
        if let Ok(workflow_id) = wf_id.parse() {
            task = task.with_workflow(workflow_id);
        }
    }

    match state.scheduler.submit(task) {
        Ok(task_id) => {
            info!("Task {} created for agent {}", task_id, req.agent_id);
            Json(Ok(CreateTaskRes { task_id }))
        }
        Err(e) => {
            error!("Failed to create task: {}", e);
            Json(Err(e))
        }
    }
}

/// List all tasks
pub async fn api_tasks_list(
    State(state): State<AppState>,
) -> Json<Vec<serde_json::Value>> {
    let stats = state.scheduler.stats();
    Json(vec![serde_json::json!({
        "total": stats.total,
        "pending": stats.pending,
        "running": stats.running,
        "completed": stats.completed,
        "failed": stats.failed,
    })])
}

/// Get task by ID
pub async fn api_task_get(
    State(state): State<AppState>,
    Path(id): Path<String>,
) -> Json<Option<serde_json::Value>> {
    if let Some(task) = state.scheduler.get_task(&id) {
        Json(Some(serde_json::json!({
            "id": task.id,
            "agent_id": task.agent_id.to_string(),
            "input": task.input,
            "priority": format!("{:?}", task.priority),
            "status": format!("{:?}", task.status),
            "created_at": task.created_at,
            "started_at": task.started_at,
            "completed_at": task.completed_at,
            "result": task.result,
            "error": task.error,
        })))
    } else {
        Json(None)
    }
}

/// Get task status
pub async fn api_task_status(
    State(state): State<AppState>,
    Path(id): Path<String>,
) -> Json<Option<String>> {
    state.scheduler.get_task(&id).map(|task| format!("{:?}", task.status)).into()
}

/// Get learning statistics
pub async fn api_learning_stats(
    State(state): State<AppState>,
) -> Json<serde_json::Value> {
    let engine = state.learning_engine.lock().unwrap();
    Json(serde_json::json!({
        "total_events": engine.total_events_processed,
        "success_rate": engine.success_rate,
        "agents_count": engine.learning_by_agent.len(),
    }))
}

/// Get learning events for an agent
pub async fn api_learning_events(
    State(state): State<AppState>,
    Path(agent_id): Path<String>,
) -> Json<Vec<serde_json::Value>> {
    let engine = state.learning_engine.lock().unwrap();

    if let Ok(agent_id_parsed) = agent_id.parse() {
        if let Some(events) = engine.learning_by_agent.get(&agent_id_parsed) {
            let events_json: Vec<serde_json::Value> = events.iter().map(|e| {
                serde_json::json!({
                    "agent_id": e.agent_id.to_string(),
                    "learning_type": format!("{:?}", e.learning_type),
                    "description": e.description,
                    "domain": e.domain,
                    "confidence": e.confidence,
                    "timestamp": e.timestamp,
                })
            }).collect();
            return Json(events_json);
        }
    }

    Json(vec![])
}
