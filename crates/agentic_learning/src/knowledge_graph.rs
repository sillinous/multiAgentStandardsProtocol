//! Knowledge graph management for shared knowledge across agents

use agentic_core::identity::AgentId;
use agentic_domain::learning::KnowledgeNode;
use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet};

/// Edge connecting two nodes in the knowledge graph
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct KnowledgeEdge {
    /// Source node ID
    pub from: String,

    /// Target node ID
    pub to: String,

    /// Relationship type
    pub relationship: String,

    /// Strength of relationship (0.0 to 1.0)
    pub strength: f64,
}

/// Knowledge graph representing shared understanding
#[derive(Clone, Debug, Default, Serialize, Deserialize)]
pub struct KnowledgeGraph {
    /// All knowledge nodes
    pub nodes: HashMap<String, KnowledgeNode>,

    /// All edges/relationships
    pub edges: Vec<KnowledgeEdge>,

    /// Agents that have accessed each node
    pub access_log: HashMap<String, Vec<AgentId>>,
}

impl KnowledgeGraph {
    /// Create a new knowledge graph
    pub fn new() -> Self {
        Self::default()
    }

    /// Add a knowledge node
    pub fn add_node(&mut self, node: KnowledgeNode) {
        self.nodes.insert(node.id.clone(), node);
    }

    /// Get a knowledge node
    pub fn get_node(&self, node_id: &str) -> Option<&KnowledgeNode> {
        self.nodes.get(node_id)
    }

    /// Update a knowledge node
    pub fn update_node(&mut self, node: KnowledgeNode) {
        self.nodes.insert(node.id.clone(), node);
    }

    /// Add an edge/relationship
    pub fn add_edge(
        &mut self,
        from: impl Into<String>,
        to: impl Into<String>,
        relationship: impl Into<String>,
        strength: f64,
    ) {
        self.edges.push(KnowledgeEdge {
            from: from.into(),
            to: to.into(),
            relationship: relationship.into(),
            strength: strength.clamp(0.0, 1.0),
        });
    }

    /// Get edges from a node
    pub fn get_outgoing_edges(&self, node_id: &str) -> Vec<&KnowledgeEdge> {
        self.edges.iter().filter(|e| e.from == node_id).collect()
    }

    /// Get edges to a node
    pub fn get_incoming_edges(&self, node_id: &str) -> Vec<&KnowledgeEdge> {
        self.edges.iter().filter(|e| e.to == node_id).collect()
    }

    /// Record agent access to a node
    pub fn record_access(&mut self, node_id: &str, agent_id: AgentId) {
        self.access_log
            .entry(node_id.to_string())
            .or_insert_with(Vec::new)
            .push(agent_id);
    }

    /// Find nodes by knowledge type
    pub fn find_by_type(&self, knowledge_type: &str) -> Vec<&KnowledgeNode> {
        self.nodes
            .values()
            .filter(|n| n.knowledge_type == knowledge_type)
            .collect()
    }

    /// Get most accessed nodes
    pub fn most_accessed_nodes(&self, limit: usize) -> Vec<(&str, usize)> {
        let mut accesses: Vec<_> = self
            .access_log
            .iter()
            .map(|(node_id, agents)| (node_id.as_str(), agents.len()))
            .collect();
        accesses.sort_by(|a, b| b.1.cmp(&a.1));
        accesses.into_iter().take(limit).collect()
    }

    /// Get nodes shared by specific agents
    pub fn nodes_shared_by_agents(&self, agent_ids: &[AgentId]) -> Vec<&KnowledgeNode> {
        let agent_set: HashSet<_> = agent_ids.iter().copied().collect();
        self.nodes
            .values()
            .filter(|node| {
                node.contributors.iter().all(|contributor| agent_set.contains(contributor))
            })
            .collect()
    }

    /// Get total number of nodes
    pub fn node_count(&self) -> usize {
        self.nodes.len()
    }

    /// Get total number of edges
    pub fn edge_count(&self) -> usize {
        self.edges.len()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_knowledge_graph() {
        let mut graph = KnowledgeGraph::new();

        let node = KnowledgeNode::new(
            "concept1",
            "A knowledge concept",
            "pattern",
        );

        graph.add_node(node);
        assert_eq!(graph.node_count(), 1);
    }

    #[test]
    fn test_knowledge_edges() {
        let mut graph = KnowledgeGraph::new();

        let node1 = KnowledgeNode::new("node1", "First", "fact");
        let node2 = KnowledgeNode::new("node2", "Second", "fact");

        graph.add_node(node1);
        graph.add_node(node2);
        graph.add_edge("node1", "node2", "relates_to", 0.8);

        assert_eq!(graph.edge_count(), 1);
        let edges = graph.get_outgoing_edges("node1");
        assert_eq!(edges.len(), 1);
    }
}
