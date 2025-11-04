//! Agent capability definitions and cards

use serde::{Deserialize, Serialize};

/// Represents a single capability an agent has
#[derive(Clone, Debug, Serialize, Deserialize, Eq, PartialEq)]
pub struct Capability {
    /// Name of the capability
    pub name: String,

    /// Human-readable description
    pub description: String,

    /// Category (e.g., "analysis", "generation", "planning", "learning")
    pub category: String,

    /// Whether this capability can be evolved/improved
    pub evolvable: bool,

    /// Current proficiency level (0.0 to 1.0)
    pub proficiency: f64,

    /// Tags for discoverability
    pub tags: Vec<String>,
}

impl Capability {
    /// Create a new capability
    pub fn new(
        name: impl Into<String>,
        description: impl Into<String>,
        category: impl Into<String>,
    ) -> Self {
        Self {
            name: name.into(),
            description: description.into(),
            category: category.into(),
            evolvable: true,
            proficiency: 0.5,
            tags: Vec::new(),
        }
    }

    /// Mark capability as not evolvable
    pub fn not_evolvable(mut self) -> Self {
        self.evolvable = false;
        self
    }

    /// Set proficiency level
    pub fn with_proficiency(mut self, proficiency: f64) -> Self {
        self.proficiency = proficiency.clamp(0.0, 1.0);
        self
    }

    /// Add a tag
    pub fn with_tag(mut self, tag: impl Into<String>) -> Self {
        self.tags.push(tag.into());
        self
    }
}

/// A card that advertises an agent's capabilities (for A2A protocol)
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct CapabilityCard {
    /// Agent ID
    pub agent_id: String,

    /// Agent name
    pub name: String,

    /// Agent description
    pub description: String,

    /// List of capabilities
    pub capabilities: Vec<Capability>,

    /// Supported protocols
    pub protocols: Vec<String>,

    /// Authentication methods supported
    pub auth_methods: Vec<String>,

    /// API endpoints
    pub endpoints: Vec<Endpoint>,

    /// Version of the agent
    pub version: String,
}

/// API endpoint information
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Endpoint {
    /// Endpoint path (e.g., "/api/v1/tasks")
    pub path: String,

    /// HTTP method
    pub method: String,

    /// Description of what this endpoint does
    pub description: String,

    /// Required authentication
    pub requires_auth: bool,
}

impl CapabilityCard {
    /// Create a new capability card
    pub fn new(
        agent_id: impl Into<String>,
        name: impl Into<String>,
        description: impl Into<String>,
        version: impl Into<String>,
    ) -> Self {
        Self {
            agent_id: agent_id.into(),
            name: name.into(),
            description: description.into(),
            capabilities: Vec::new(),
            protocols: vec!["a2a/1.0".to_string(), "mcp/1.0".to_string()],
            auth_methods: vec!["oauth2".to_string(), "api_key".to_string()],
            endpoints: Vec::new(),
            version: version.into(),
        }
    }

    /// Add a capability
    pub fn with_capability(mut self, capability: Capability) -> Self {
        self.capabilities.push(capability);
        self
    }

    /// Add an endpoint
    pub fn with_endpoint(
        mut self,
        path: impl Into<String>,
        method: impl Into<String>,
        description: impl Into<String>,
    ) -> Self {
        self.endpoints.push(Endpoint {
            path: path.into(),
            method: method.into(),
            description: description.into(),
            requires_auth: true,
        });
        self
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_capability_creation() {
        let cap = Capability::new(
            "analysis",
            "Can analyze text",
            "analysis",
        )
        .with_proficiency(0.8);

        assert_eq!(cap.name, "analysis");
        assert_eq!(cap.proficiency, 0.8);
    }

    #[test]
    fn test_capability_card() {
        let card = CapabilityCard::new(
            "agent-123",
            "Analytics Agent",
            "Analyzes data and generates insights",
            "1.0.0",
        )
        .with_capability(
            Capability::new(
                "analysis",
                "Can analyze text",
                "analysis",
            )
        );

        assert_eq!(card.capabilities.len(), 1);
        assert!(card.protocols.contains(&"a2a/1.0".to_string()));
    }
}
