//! Agent Runtime - Execution engine for autonomous agents
//!
//! This crate provides the runtime infrastructure for executing agents:
//! - LLM API integration (Anthropic, OpenAI)
//! - Task scheduling and execution
//! - Message routing between agents
//! - Resource management and rate limiting
//! - Execution context and state management

pub mod llm;
pub mod executor;
pub mod scheduler;
pub mod context;
pub mod config;

pub use llm::{LlmClient, LlmProvider, LlmRequest, LlmResponse};
pub use executor::{AgentExecutor, ExecutionResult};
pub use scheduler::{TaskScheduler, Task, TaskPriority};
pub use context::{ExecutionContext, ContextData};
pub use config::{RuntimeConfig, LlmConfig, ExecutionConfig, PerformanceConfig};
