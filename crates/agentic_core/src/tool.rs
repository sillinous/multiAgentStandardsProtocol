//! Tool definitions and execution results

use crate::identity::AgentId;
use serde::{Deserialize, Serialize};
use serde_json::Value;

/// Represents a tool/function that an agent can call
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Tool {
    /// Unique identifier for this tool
    pub id: String,

    /// Human-readable name
    pub name: String,

    /// Detailed description of what the tool does
    pub description: String,

    /// Input schema (JSON Schema format)
    pub input_schema: Value,

    /// The agent that owns/provides this tool
    pub provider_agent_id: Option<AgentId>,

    /// Category (e.g., "data_access", "computation", "communication")
    pub category: String,

    /// Whether this tool is available for use
    pub is_available: bool,

    /// Cost of using this tool (for budgeting)
    pub cost_estimate: Option<f64>,
}

impl Tool {
    /// Create a new tool
    pub fn new(
        id: impl Into<String>,
        name: impl Into<String>,
        description: impl Into<String>,
        category: impl Into<String>,
    ) -> Self {
        Self {
            id: id.into(),
            name: name.into(),
            description: description.into(),
            input_schema: serde_json::json!({}),
            provider_agent_id: None,
            category: category.into(),
            is_available: true,
            cost_estimate: None,
        }
    }

    /// Set the input schema
    pub fn with_schema(mut self, schema: Value) -> Self {
        self.input_schema = schema;
        self
    }

    /// Set the provider agent
    pub fn with_provider(mut self, provider: AgentId) -> Self {
        self.provider_agent_id = Some(provider);
        self
    }
}

/// Unique identifier for a tool call
#[derive(Clone, Debug, Eq, PartialEq, Serialize, Deserialize)]
pub struct ToolCallId(String);

impl ToolCallId {
    /// Create a new tool call ID
    pub fn new(id: impl Into<String>) -> Self {
        Self(id.into())
    }

    /// Generate a unique tool call ID
    pub fn generate() -> Self {
        Self(nanoid::nanoid!())
    }
}

/// A request to execute a tool
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ToolCall {
    /// Unique identifier for this tool call
    pub id: ToolCallId,

    /// Name of the tool to call
    pub tool_name: String,

    /// Arguments to pass to the tool
    pub arguments: Value,

    /// Optional timeout in seconds
    pub timeout_secs: Option<u64>,
}

impl ToolCall {
    /// Create a new tool call
    pub fn new(tool_name: impl Into<String>, arguments: Value) -> Self {
        Self {
            id: ToolCallId::generate(),
            tool_name: tool_name.into(),
            arguments,
            timeout_secs: None,
        }
    }

    /// Set a timeout
    pub fn with_timeout(mut self, secs: u64) -> Self {
        self.timeout_secs = Some(secs);
        self
    }
}

/// Result of executing a tool
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ToolResult {
    /// The tool call that this result corresponds to
    pub tool_call_id: ToolCallId,

    /// Tool name
    pub tool_name: String,

    /// Whether the tool call succeeded
    pub success: bool,

    /// Result content
    pub content: String,

    /// Any error message (if success is false)
    pub error: Option<String>,

    /// Structured result data
    pub data: Option<Value>,

    /// Execution time in milliseconds
    pub execution_time_ms: u64,
}

impl ToolResult {
    /// Create a successful tool result
    pub fn success(
        tool_call_id: ToolCallId,
        tool_name: impl Into<String>,
        content: impl Into<String>,
    ) -> Self {
        Self {
            tool_call_id,
            tool_name: tool_name.into(),
            success: true,
            content: content.into(),
            error: None,
            data: None,
            execution_time_ms: 0,
        }
    }

    /// Create a failed tool result
    pub fn error(
        tool_call_id: ToolCallId,
        tool_name: impl Into<String>,
        error: impl Into<String>,
    ) -> Self {
        Self {
            tool_call_id,
            tool_name: tool_name.into(),
            success: false,
            content: String::new(),
            error: Some(error.into()),
            data: None,
            execution_time_ms: 0,
        }
    }

    /// Add structured data to the result
    pub fn with_data(mut self, data: Value) -> Self {
        self.data = Some(data);
        self
    }

    /// Set execution time
    pub fn with_execution_time(mut self, ms: u64) -> Self {
        self.execution_time_ms = ms;
        self
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_tool_creation() {
        let tool = Tool::new(
            "web_search",
            "Web Search",
            "Search the web for information",
            "data_access",
        );

        assert_eq!(tool.name, "Web Search");
        assert_eq!(tool.category, "data_access");
    }

    #[test]
    fn test_tool_call() {
        let args = serde_json::json!({ "query": "rust programming" });
        let call = ToolCall::new("web_search", args);

        assert_eq!(call.tool_name, "web_search");
        assert!(!call.id.0.is_empty());
    }

    #[test]
    fn test_tool_result() {
        let call_id = ToolCallId::generate();
        let result = ToolResult::success(call_id.clone(), "web_search", "Found 5 results");

        assert!(result.success);
        assert_eq!(result.tool_name, "web_search");

        let error_result = ToolResult::error(call_id, "web_search", "Network error");
        assert!(!error_result.success);
        assert!(error_result.error.is_some());
    }
}
