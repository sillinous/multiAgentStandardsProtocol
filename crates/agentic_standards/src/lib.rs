//! Standards registry, templates, and a standards agent for compliance checks

use agentic_core::{Agent, Protocol, ProtocolVersion};
use agentic_core::identity::AgentId;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Clone, Debug, Eq, PartialEq, Hash, Serialize, Deserialize)]
pub struct StandardId(pub String);

#[derive(Clone, Debug, Serialize, Deserialize)]
pub enum ComplianceLevel {
    Draft,
    Recommended,
    Required,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct StandardSpec {
    pub id: StandardId,
    pub name: String,
    pub version: ProtocolVersion,
    pub level: ComplianceLevel,
    pub description: String,
    pub required_protocols: Vec<Protocol>,
    /// MVP: required capabilities by name. Real system should reference structured capabilities.
    pub required_capabilities: Vec<String>,
    pub metadata: HashMap<String, String>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ComplianceReport {
    pub standard: StandardId,
    pub compliant: bool,
    pub missing_protocols: Vec<Protocol>,
    pub missing_capabilities: Vec<String>,
    pub notes: Vec<String>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct StandardizedAgentTemplate {
    pub template_id: String,
    pub display_name: String,
    pub description: String,
    pub default_model: String,
    pub default_provider: String,
    pub standards: Vec<StandardSpec>,
    /// Default capability flags (by name), set into `Agent.config` under keys `cap:<name>`
    pub default_capabilities: Vec<String>,
    pub default_tags: Vec<String>,
}

impl StandardizedAgentTemplate {
    pub fn compliance_for(&self, agent: &Agent) -> ComplianceReport {
        let mut missing_protocols = vec![];
        let mut missing_caps = vec![];

        for std in &self.standards {
            for p in &std.required_protocols {
                // MVP: consider protocol present if agent.config has key protocol:<name>
                let key = match p {
                    Protocol::A2A => "protocol:a2a",
                    Protocol::MCP => "protocol:mcp",
                    Protocol::ANS => "protocol:ans",
                    Protocol::HTTP => "protocol:http",
                    Protocol::WebSocket => "protocol:websocket",
                    Protocol::Internal => "protocol:internal",
                };
                if !agent.config.contains_key(key) {
                    missing_protocols.push(*p);
                }
            }

            for cap_name in &std.required_capabilities {
                let key = format!("cap:{}", cap_name);
                if !agent.config.contains_key(&key) {
                    missing_caps.push(cap_name.clone());
                }
            }
        }

        ComplianceReport {
            standard: self
                .standards
                .get(0)
                .map(|s| s.id.clone())
                .unwrap_or(StandardId("none".into())),
            compliant: missing_protocols.is_empty() && missing_caps.is_empty(),
            missing_protocols,
            missing_capabilities: missing_caps,
            notes: vec![],
        }
    }
}

#[derive(Default, Clone)]
pub struct StandardsRegistry {
    templates: HashMap<String, StandardizedAgentTemplate>,
}

impl StandardsRegistry {
    pub fn new() -> Self { Self { templates: HashMap::new() } }

    pub fn register_template(&mut self, tmpl: StandardizedAgentTemplate) {
        self.templates.insert(tmpl.template_id.clone(), tmpl);
    }

    pub fn get_template(&self, id: &str) -> Option<&StandardizedAgentTemplate> {
        self.templates.get(id)
    }
}

// Convenience helpers: canned standards
pub fn standard_mcp_required() -> StandardSpec {
    StandardSpec {
        id: StandardId("std.mcp.v1".into()),
        name: "Model Context Protocol".into(),
        version: ProtocolVersion { protocol: Protocol::MCP, major: 1, minor: 0, patch: 0, prerelease: None },
        level: ComplianceLevel::Required,
        description: "Agents must expose MCP tools and resource access per spec".into(),
        required_protocols: vec![Protocol::MCP],
        required_capabilities: vec!["mcp.tools".into()],
        metadata: HashMap::new(),
    }
}

pub fn standard_a2a_recommended() -> StandardSpec {
    StandardSpec {
        id: StandardId("std.a2a.v1".into()),
        name: "Agent-to-Agent".into(),
        version: ProtocolVersion { protocol: Protocol::A2A, major: 1, minor: 0, patch: 0, prerelease: None },
        level: ComplianceLevel::Recommended,
        description: "Agents should support A2A messaging".into(),
        required_protocols: vec![Protocol::A2A],
        required_capabilities: vec![],
        metadata: HashMap::new(),
    }
}

pub fn template_standard_worker() -> StandardizedAgentTemplate {
    StandardizedAgentTemplate {
        template_id: "tmpl.standard.worker".into(),
        display_name: "Standard Worker".into(),
        description: "Worker agent compliant with MCP and A2A (recommended)".into(),
        default_model: "claude-3-opus".into(),
        default_provider: "anthropic".into(),
        standards: vec![standard_mcp_required(), standard_a2a_recommended()],
        default_capabilities: vec!["mcp.tools".into()],
        default_tags: vec!["standard".into(), "worker".into()],
    }
}

pub struct StandardsAgent {
    pub id: AgentId,
    pub registry: StandardsRegistry,
}

impl StandardsAgent {
    pub fn new() -> Self {
        let mut registry = StandardsRegistry::new();
        registry.register_template(template_standard_worker());
        Self { id: AgentId::generate(), registry }
    }

    pub fn register_template(&mut self, tmpl: StandardizedAgentTemplate) {
        self.registry.register_template(tmpl);
    }

    pub fn compliance_for_template(&self, template_id: &str, agent: &agentic_core::Agent) -> Option<ComplianceReport> {
        self.registry.get_template(template_id).map(|t| t.compliance_for(agent))
    }

    pub fn registry(&self) -> &StandardsRegistry { &self.registry }
}
