//! Configuration management for the runtime

use serde::{Deserialize, Serialize};
use std::env;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RuntimeConfig {
    pub llm: LlmConfig,
    pub execution: ExecutionConfig,
    pub performance: PerformanceConfig,
}

impl RuntimeConfig {
    /// Load configuration from environment variables
    pub fn from_env() -> Self {
        Self {
            llm: LlmConfig::from_env(),
            execution: ExecutionConfig::from_env(),
            performance: PerformanceConfig::from_env(),
        }
    }

    /// Load with defaults
    pub fn default() -> Self {
        Self {
            llm: LlmConfig::default(),
            execution: ExecutionConfig::default(),
            performance: PerformanceConfig::default(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LlmConfig {
    pub anthropic_api_key: Option<String>,
    pub openai_api_key: Option<String>,
    pub default_provider: String,
    pub default_model: String,
    pub max_tokens: usize,
    pub temperature: f32,
}

impl LlmConfig {
    pub fn from_env() -> Self {
        Self {
            anthropic_api_key: env::var("ANTHROPIC_API_KEY").ok(),
            openai_api_key: env::var("OPENAI_API_KEY").ok(),
            default_provider: env::var("DEFAULT_LLM_PROVIDER")
                .unwrap_or_else(|_| "mock".to_string()),
            default_model: env::var("DEFAULT_MODEL")
                .unwrap_or_else(|_| "claude-3-5-sonnet-20241022".to_string()),
            max_tokens: env::var("MAX_TOKENS")
                .unwrap_or_else(|_| "4096".to_string())
                .parse()
                .unwrap_or(4096),
            temperature: env::var("DEFAULT_TEMPERATURE")
                .unwrap_or_else(|_| "0.7".to_string())
                .parse()
                .unwrap_or(0.7),
        }
    }
}

impl Default for LlmConfig {
    fn default() -> Self {
        Self {
            anthropic_api_key: None,
            openai_api_key: None,
            default_provider: "mock".to_string(),
            default_model: "claude-3-5-sonnet-20241022".to_string(),
            max_tokens: 4096,
            temperature: 0.7,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExecutionConfig {
    pub agent_timeout_seconds: u64,
    pub max_retries: u32,
    pub enable_learning: bool,
}

impl ExecutionConfig {
    pub fn from_env() -> Self {
        Self {
            agent_timeout_seconds: env::var("AGENT_TIMEOUT")
                .unwrap_or_else(|_| "120".to_string())
                .parse()
                .unwrap_or(120),
            max_retries: env::var("MAX_RETRIES")
                .unwrap_or_else(|_| "3".to_string())
                .parse()
                .unwrap_or(3),
            enable_learning: env::var("ENABLE_LEARNING")
                .unwrap_or_else(|_| "true".to_string())
                .parse()
                .unwrap_or(true),
        }
    }
}

impl Default for ExecutionConfig {
    fn default() -> Self {
        Self {
            agent_timeout_seconds: 120,
            max_retries: 3,
            enable_learning: true,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PerformanceConfig {
    pub max_concurrent_executions: usize,
    pub task_queue_size: usize,
    pub rate_limit_per_minute: u32,
}

impl PerformanceConfig {
    pub fn from_env() -> Self {
        Self {
            max_concurrent_executions: env::var("MAX_CONCURRENT_EXECUTIONS")
                .unwrap_or_else(|_| "10".to_string())
                .parse()
                .unwrap_or(10),
            task_queue_size: env::var("TASK_QUEUE_SIZE")
                .unwrap_or_else(|_| "1000".to_string())
                .parse()
                .unwrap_or(1000),
            rate_limit_per_minute: env::var("RATE_LIMIT_PER_MINUTE")
                .unwrap_or_else(|_| "100".to_string())
                .parse()
                .unwrap_or(100),
        }
    }
}

impl Default for PerformanceConfig {
    fn default() -> Self {
        Self {
            max_concurrent_executions: 10,
            task_queue_size: 1000,
            rate_limit_per_minute: 100,
        }
    }
}
