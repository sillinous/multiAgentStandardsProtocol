//! Protocol adapters (A2A, MCP, ANS) - MVP trait definitions

use agentic_core::{Protocol, ProtocolVersion};

pub trait ProtocolAdapter {
    fn protocol(&self) -> Protocol;
    fn version(&self) -> ProtocolVersion;
    // Extend with encode/decode, handshake, discovery as needed
}

#[derive(Clone, Debug)]
pub struct MockMcpAdapter;

impl MockMcpAdapter {
    pub fn list_tools(&self) -> Vec<McpTool> {
        vec![
            McpTool { name: "echo".into(), description: "Echo back input".into() },
            McpTool { name: "reverse".into(), description: "Reverse input string".into() },
        ]
    }

    pub fn invoke(&self, tool: &str, input: &str) -> String {
        match tool {
            "echo" => input.to_string(),
            "reverse" => input.chars().rev().collect(),
            _ => format!("unknown tool: {}", tool),
        }
    }
}

impl ProtocolAdapter for MockMcpAdapter {
    fn protocol(&self) -> Protocol { Protocol::MCP }
    fn version(&self) -> ProtocolVersion { ProtocolVersion { protocol: Protocol::MCP, major: 1, minor: 0, patch: 0, prerelease: None } }
}

#[derive(Clone, Debug, serde::Serialize, serde::Deserialize)]
pub struct McpTool { pub name: String, pub description: String }

#[derive(Clone, Debug)]
pub struct MockA2aAdapter;

impl MockA2aAdapter {
    pub fn envelope(&self, from: &str, to: &str, content: &str) -> A2aEnvelope {
        A2aEnvelope { from: from.into(), to: to.into(), content: content.into() }
    }
}

impl ProtocolAdapter for MockA2aAdapter {
    fn protocol(&self) -> Protocol { Protocol::A2A }
    fn version(&self) -> ProtocolVersion { ProtocolVersion { protocol: Protocol::A2A, major: 1, minor: 0, patch: 0, prerelease: None } }
}

#[derive(Clone, Debug, serde::Serialize, serde::Deserialize)]
pub struct A2aEnvelope { pub from: String, pub to: String, pub content: String }
