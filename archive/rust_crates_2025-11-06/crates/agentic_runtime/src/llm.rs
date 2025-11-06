//! LLM Client abstraction and implementations for multiple providers

use async_trait::async_trait;
use serde::{Deserialize, Serialize};
use std::time::Duration;
use thiserror::Error;

#[derive(Debug, Error)]
pub enum LlmError {
    #[error("API request failed: {0}")]
    ApiError(String),

    #[error("Rate limit exceeded: {0}")]
    RateLimitExceeded(String),

    #[error("Invalid API key")]
    InvalidApiKey,

    #[error("Unsupported model: {0}")]
    UnsupportedModel(String),

    #[error("Serialization error: {0}")]
    SerializationError(String),

    #[error("Network error: {0}")]
    NetworkError(String),

    #[error("Token limit exceeded: max {max}, requested {requested}")]
    TokenLimitExceeded { max: usize, requested: usize },
}

pub type Result<T> = std::result::Result<T, LlmError>;

/// Supported LLM providers
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum LlmProvider {
    Anthropic,
    OpenAI,
    Mock, // For testing
}

/// Message role in conversation
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum MessageRole {
    System,
    User,
    Assistant,
}

/// A single message in the conversation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Message {
    pub role: MessageRole,
    pub content: String,
}

impl Message {
    pub fn system(content: impl Into<String>) -> Self {
        Self { role: MessageRole::System, content: content.into() }
    }

    pub fn user(content: impl Into<String>) -> Self {
        Self { role: MessageRole::User, content: content.into() }
    }

    pub fn assistant(content: impl Into<String>) -> Self {
        Self { role: MessageRole::Assistant, content: content.into() }
    }
}

/// Request parameters for LLM completion
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LlmRequest {
    pub model: String,
    pub messages: Vec<Message>,
    pub max_tokens: Option<usize>,
    pub temperature: Option<f32>,
    pub top_p: Option<f32>,
    pub stop_sequences: Vec<String>,
}

impl LlmRequest {
    pub fn new(model: impl Into<String>) -> Self {
        Self {
            model: model.into(),
            messages: Vec::new(),
            max_tokens: Some(4096),
            temperature: Some(0.7),
            top_p: Some(1.0),
            stop_sequences: Vec::new(),
        }
    }

    pub fn with_system(mut self, content: impl Into<String>) -> Self {
        self.messages.insert(0, Message::system(content));
        self
    }

    pub fn add_message(mut self, message: Message) -> Self {
        self.messages.push(message);
        self
    }

    pub fn with_temperature(mut self, temp: f32) -> Self {
        self.temperature = Some(temp);
        self
    }

    pub fn with_max_tokens(mut self, max: usize) -> Self {
        self.max_tokens = Some(max);
        self
    }
}

/// Response from LLM
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LlmResponse {
    pub content: String,
    pub model: String,
    pub usage: TokenUsage,
    pub finish_reason: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokenUsage {
    pub prompt_tokens: usize,
    pub completion_tokens: usize,
    pub total_tokens: usize,
}

/// Trait for LLM client implementations
#[async_trait]
pub trait LlmClient: Send + Sync {
    /// Get the provider this client is for
    fn provider(&self) -> LlmProvider;

    /// Send a completion request
    async fn complete(&self, request: LlmRequest) -> Result<LlmResponse>;

    /// Check if a model is supported
    fn supports_model(&self, model: &str) -> bool;

    /// Get available models
    fn available_models(&self) -> Vec<String>;
}

/// Anthropic Claude client
pub struct AnthropicClient {
    api_key: String,
    base_url: String,
    client: reqwest::Client,
}

impl AnthropicClient {
    pub fn new(api_key: impl Into<String>) -> Self {
        Self {
            api_key: api_key.into(),
            base_url: "https://api.anthropic.com/v1".to_string(),
            client: reqwest::Client::builder()
                .timeout(Duration::from_secs(120))
                .build()
                .expect("Failed to create HTTP client"),
        }
    }

    pub fn with_base_url(mut self, url: impl Into<String>) -> Self {
        self.base_url = url.into();
        self
    }
}

#[async_trait]
impl LlmClient for AnthropicClient {
    fn provider(&self) -> LlmProvider {
        LlmProvider::Anthropic
    }

    async fn complete(&self, request: LlmRequest) -> Result<LlmResponse> {
        // Build Anthropic-specific request format
        let mut anthropic_messages = Vec::new();
        let mut system_prompt = None;

        for msg in &request.messages {
            match msg.role {
                MessageRole::System => {
                    system_prompt = Some(msg.content.clone());
                }
                MessageRole::User | MessageRole::Assistant => {
                    anthropic_messages.push(serde_json::json!({
                        "role": match msg.role {
                            MessageRole::User => "user",
                            MessageRole::Assistant => "assistant",
                            _ => unreachable!(),
                        },
                        "content": msg.content,
                    }));
                }
            }
        }

        let mut body = serde_json::json!({
            "model": request.model,
            "messages": anthropic_messages,
            "max_tokens": request.max_tokens.unwrap_or(4096),
        });

        if let Some(system) = system_prompt {
            body["system"] = serde_json::json!(system);
        }

        if let Some(temp) = request.temperature {
            body["temperature"] = serde_json::json!(temp);
        }

        if let Some(top_p) = request.top_p {
            body["top_p"] = serde_json::json!(top_p);
        }

        if !request.stop_sequences.is_empty() {
            body["stop_sequences"] = serde_json::json!(request.stop_sequences);
        }

        let response = self.client
            .post(format!("{}/messages", self.base_url))
            .header("x-api-key", &self.api_key)
            .header("anthropic-version", "2023-06-01")
            .header("content-type", "application/json")
            .json(&body)
            .send()
            .await
            .map_err(|e| LlmError::NetworkError(e.to_string()))?;

        if !response.status().is_success() {
            let status = response.status();
            let error_text = response.text().await.unwrap_or_default();
            return Err(LlmError::ApiError(format!("HTTP {}: {}", status, error_text)));
        }

        let response_json: serde_json::Value = response.json().await
            .map_err(|e| LlmError::SerializationError(e.to_string()))?;

        // Parse Anthropic response
        let content = response_json["content"][0]["text"]
            .as_str()
            .ok_or_else(|| LlmError::ApiError("No content in response".to_string()))?
            .to_string();

        let usage = TokenUsage {
            prompt_tokens: response_json["usage"]["input_tokens"].as_u64().unwrap_or(0) as usize,
            completion_tokens: response_json["usage"]["output_tokens"].as_u64().unwrap_or(0) as usize,
            total_tokens: 0,
        };

        Ok(LlmResponse {
            content,
            model: request.model,
            usage: TokenUsage {
                total_tokens: usage.prompt_tokens + usage.completion_tokens,
                ..usage
            },
            finish_reason: response_json["stop_reason"].as_str().unwrap_or("unknown").to_string(),
        })
    }

    fn supports_model(&self, model: &str) -> bool {
        model.starts_with("claude-")
    }

    fn available_models(&self) -> Vec<String> {
        vec![
            "claude-3-5-sonnet-20241022".to_string(),
            "claude-3-5-haiku-20241022".to_string(),
            "claude-3-opus-20240229".to_string(),
            "claude-3-sonnet-20240229".to_string(),
            "claude-3-haiku-20240307".to_string(),
        ]
    }
}

/// OpenAI client
pub struct OpenAIClient {
    api_key: String,
    base_url: String,
    client: reqwest::Client,
}

impl OpenAIClient {
    pub fn new(api_key: impl Into<String>) -> Self {
        Self {
            api_key: api_key.into(),
            base_url: "https://api.openai.com/v1".to_string(),
            client: reqwest::Client::builder()
                .timeout(Duration::from_secs(120))
                .build()
                .expect("Failed to create HTTP client"),
        }
    }
}

#[async_trait]
impl LlmClient for OpenAIClient {
    fn provider(&self) -> LlmProvider {
        LlmProvider::OpenAI
    }

    async fn complete(&self, request: LlmRequest) -> Result<LlmResponse> {
        let messages: Vec<serde_json::Value> = request.messages.iter().map(|msg| {
            serde_json::json!({
                "role": match msg.role {
                    MessageRole::System => "system",
                    MessageRole::User => "user",
                    MessageRole::Assistant => "assistant",
                },
                "content": msg.content,
            })
        }).collect();

        let mut body = serde_json::json!({
            "model": request.model,
            "messages": messages,
        });

        if let Some(max_tokens) = request.max_tokens {
            body["max_tokens"] = serde_json::json!(max_tokens);
        }

        if let Some(temp) = request.temperature {
            body["temperature"] = serde_json::json!(temp);
        }

        if let Some(top_p) = request.top_p {
            body["top_p"] = serde_json::json!(top_p);
        }

        if !request.stop_sequences.is_empty() {
            body["stop"] = serde_json::json!(request.stop_sequences);
        }

        let response = self.client
            .post(format!("{}/chat/completions", self.base_url))
            .header("Authorization", format!("Bearer {}", self.api_key))
            .header("content-type", "application/json")
            .json(&body)
            .send()
            .await
            .map_err(|e| LlmError::NetworkError(e.to_string()))?;

        if !response.status().is_success() {
            let status = response.status();
            let error_text = response.text().await.unwrap_or_default();
            return Err(LlmError::ApiError(format!("HTTP {}: {}", status, error_text)));
        }

        let response_json: serde_json::Value = response.json().await
            .map_err(|e| LlmError::SerializationError(e.to_string()))?;

        let content = response_json["choices"][0]["message"]["content"]
            .as_str()
            .ok_or_else(|| LlmError::ApiError("No content in response".to_string()))?
            .to_string();

        let usage = TokenUsage {
            prompt_tokens: response_json["usage"]["prompt_tokens"].as_u64().unwrap_or(0) as usize,
            completion_tokens: response_json["usage"]["completion_tokens"].as_u64().unwrap_or(0) as usize,
            total_tokens: response_json["usage"]["total_tokens"].as_u64().unwrap_or(0) as usize,
        };

        Ok(LlmResponse {
            content,
            model: request.model,
            usage,
            finish_reason: response_json["choices"][0]["finish_reason"]
                .as_str()
                .unwrap_or("unknown")
                .to_string(),
        })
    }

    fn supports_model(&self, model: &str) -> bool {
        model.starts_with("gpt-") || model.starts_with("o1-")
    }

    fn available_models(&self) -> Vec<String> {
        vec![
            "gpt-4o".to_string(),
            "gpt-4o-mini".to_string(),
            "gpt-4-turbo".to_string(),
            "gpt-4".to_string(),
            "gpt-3.5-turbo".to_string(),
            "o1-preview".to_string(),
            "o1-mini".to_string(),
        ]
    }
}

/// Mock client for testing
pub struct MockLlmClient {
    pub response: String,
}

impl MockLlmClient {
    pub fn new(response: impl Into<String>) -> Self {
        Self {
            response: response.into(),
        }
    }
}

impl Default for MockLlmClient {
    fn default() -> Self {
        Self::new("Mock LLM response")
    }
}

#[async_trait]
impl LlmClient for MockLlmClient {
    fn provider(&self) -> LlmProvider {
        LlmProvider::Mock
    }

    async fn complete(&self, request: LlmRequest) -> Result<LlmResponse> {
        Ok(LlmResponse {
            content: self.response.clone(),
            model: request.model,
            usage: TokenUsage {
                prompt_tokens: 10,
                completion_tokens: 20,
                total_tokens: 30,
            },
            finish_reason: "stop".to_string(),
        })
    }

    fn supports_model(&self, _model: &str) -> bool {
        true
    }

    fn available_models(&self) -> Vec<String> {
        vec!["mock-model".to_string()]
    }
}
