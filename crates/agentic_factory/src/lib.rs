//! AgentFactory - creates agents from standardized templates

use agentic_core::{Agent, AgentRole, Result};
use agentic_domain::agent_genome::AgentGenome;
use agentic_standards::{StandardsRegistry, StandardizedAgentTemplate};
use std::collections::HashMap;

pub struct AgentFactory {
    registry: StandardsRegistry,
}

impl AgentFactory {
    pub fn from_registry(registry: StandardsRegistry) -> Self {
        Self { registry }
    }

    pub fn create_from_template(
        &self,
        template_id: &str,
        name: &str,
        description: &str,
    ) -> Result<(Agent, AgentGenome)> {
        let tmpl: &StandardizedAgentTemplate = self
            .registry
            .get_template(template_id)
            .ok_or_else(|| agentic_core::Error::InvalidArgument(format!("unknown template: {}", template_id)))?;

        let mut agent = Agent::new(
            name,
            description,
            AgentRole::Worker,
            tmpl.default_model.clone(),
            tmpl.default_provider.clone(),
        );

        for t in &tmpl.default_tags {
            agent.add_tag(t.clone());
        }
        for cap_name in &tmpl.default_capabilities {
            agent.config.insert(format!("cap:{}", cap_name), serde_json::json!("1.0.0"));
        }

        // Set protocol flags to satisfy compliance for required protocols in template
        for std in &tmpl.standards {
            for p in &std.required_protocols {
                let (key, val) = match p {
                    agentic_core::Protocol::A2A => ("protocol:a2a", "1.0"),
                    agentic_core::Protocol::MCP => ("protocol:mcp", "1.0"),
                    agentic_core::Protocol::ANS => ("protocol:ans", "1.0"),
                    agentic_core::Protocol::HTTP => ("protocol:http", "1.1"),
                    agentic_core::Protocol::WebSocket => ("protocol:websocket", "1.0"),
                    agentic_core::Protocol::Internal => ("protocol:internal", "1.0"),
                };
                agent.config.insert(key.to_string(), serde_json::json!(val));
            }
        }

        let genome = AgentGenome::new(agent.id, tmpl.display_name.clone());

        Ok((agent, genome))
    }
}

#[derive(Default)]
pub struct AgentRegistry {
    agents: HashMap<String, Agent>,
    genomes: HashMap<String, AgentGenome>,
}

impl AgentRegistry {
    pub fn new() -> Self { Self { agents: HashMap::new(), genomes: HashMap::new() } }

    pub fn register(&mut self, agent: Agent, genome: AgentGenome) {
        let id = agent.id.to_string();
        self.genomes.insert(id.clone(), genome);
        self.agents.insert(id, agent);
    }

    pub fn list_agents(&self) -> Vec<&Agent> {
        self.agents.values().collect()
    }

    pub fn get_agent(&self, id: &str) -> Option<&Agent> {
        self.agents.get(id)
    }

    pub fn get_genome(&self, id: &str) -> Option<&AgentGenome> {
        self.genomes.get(id)
    }

    pub fn remove(&mut self, id: &str) -> bool {
        self.genomes.remove(id);
        self.agents.remove(id).is_some()
    }
}
