//! Knowledge transfer between agents
//!
//! Enables agents to share learnings and knowledge with each other

use agentic_core::identity::AgentId;
use agentic_domain::learning::LearningEvent;
use serde::{Deserialize, Serialize};

/// Represents a knowledge transfer from one agent to another
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct KnowledgeTransfer {
    /// Unique identifier
    pub id: String,

    /// Source agent (sharing knowledge)
    pub from_agent: AgentId,

    /// Destination agent (receiving knowledge)
    pub to_agent: AgentId,

    /// Learning event being shared
    pub learning: LearningEvent,

    /// Whether the transfer was accepted
    pub accepted: bool,

    /// Effectiveness of transfer (how much it helped the receiving agent)
    pub effectiveness: f64,

    /// When this transfer occurred
    pub timestamp: chrono::DateTime<chrono::Utc>,
}

impl KnowledgeTransfer {
    /// Create a new knowledge transfer
    pub fn new(
        from_agent: AgentId,
        to_agent: AgentId,
        learning: LearningEvent,
    ) -> Self {
        Self {
            id: nanoid::nanoid!(),
            from_agent,
            to_agent,
            learning,
            accepted: false,
            effectiveness: 0.0,
            timestamp: chrono::Utc::now(),
        }
    }

    /// Mark transfer as accepted
    pub fn accept(mut self) -> Self {
        self.accepted = true;
        self
    }

    /// Set effectiveness
    pub fn with_effectiveness(mut self, effectiveness: f64) -> Self {
        self.effectiveness = effectiveness.clamp(0.0, 1.0);
        self
    }
}

/// Manages knowledge sharing between agents
#[derive(Clone, Debug, Default, Serialize, Deserialize)]
pub struct KnowledgeTransferManager {
    /// All transfers
    pub transfers: Vec<KnowledgeTransfer>,

    /// Transfers by recipient
    pub transfers_by_recipient: std::collections::HashMap<AgentId, Vec<String>>,

    /// Transfers by source
    pub transfers_by_source: std::collections::HashMap<AgentId, Vec<String>>,

    /// Statistics
    pub total_transfers: u32,
    pub successful_transfers: u32,
}

impl KnowledgeTransferManager {
    /// Create a new knowledge transfer manager
    pub fn new() -> Self {
        Self::default()
    }

    /// Record a knowledge transfer
    pub fn record_transfer(&mut self, transfer: KnowledgeTransfer) {
        let transfer_id = transfer.id.clone();
        let from = transfer.from_agent;
        let to = transfer.to_agent;
        let accepted = transfer.accepted;

        self.transfers.push(transfer);
        self.total_transfers += 1;

        if accepted {
            self.successful_transfers += 1;
        }

        self.transfers_by_recipient
            .entry(to)
            .or_insert_with(Vec::new)
            .push(transfer_id.clone());

        self.transfers_by_source
            .entry(from)
            .or_insert_with(Vec::new)
            .push(transfer_id);
    }

    /// Get all transfers received by an agent
    pub fn get_received_transfers(&self, agent_id: &AgentId) -> Vec<&KnowledgeTransfer> {
        if let Some(transfer_ids) = self.transfers_by_recipient.get(agent_id) {
            self.transfers
                .iter()
                .filter(|t| transfer_ids.contains(&t.id))
                .collect()
        } else {
            Vec::new()
        }
    }

    /// Get all transfers sent by an agent
    pub fn get_sent_transfers(&self, agent_id: &AgentId) -> Vec<&KnowledgeTransfer> {
        if let Some(transfer_ids) = self.transfers_by_source.get(agent_id) {
            self.transfers
                .iter()
                .filter(|t| transfer_ids.contains(&t.id))
                .collect()
        } else {
            Vec::new()
        }
    }

    /// Get agents that an agent has learned from
    pub fn get_knowledge_sources(&self, agent_id: &AgentId) -> Vec<AgentId> {
        self.get_received_transfers(agent_id)
            .iter()
            .map(|t| t.from_agent)
            .collect::<std::collections::HashSet<_>>()
            .into_iter()
            .collect()
    }

    /// Get agents that have learned from an agent
    pub fn get_knowledge_recipients(&self, agent_id: &AgentId) -> Vec<AgentId> {
        self.get_sent_transfers(agent_id)
            .iter()
            .map(|t| t.to_agent)
            .collect::<std::collections::HashSet<_>>()
            .into_iter()
            .collect()
    }

    /// Calculate knowledge transfer effectiveness for an agent
    pub fn get_effectiveness_score(&self, agent_id: &AgentId) -> f64 {
        let received = self.get_received_transfers(agent_id);
        if received.is_empty() {
            return 0.0;
        }

        let total_effectiveness: f64 = received.iter().map(|t| t.effectiveness).sum();
        total_effectiveness / received.len() as f64
    }

    /// Get transfer success rate
    pub fn success_rate(&self) -> f64 {
        if self.total_transfers == 0 {
            0.0
        } else {
            self.successful_transfers as f64 / self.total_transfers as f64
        }
    }

    /// Build a learning network graph
    pub fn get_learning_network(&self) -> LearningNetwork {
        let mut nodes = std::collections::HashSet::new();
        let mut edges = Vec::new();

        for transfer in &self.transfers {
            nodes.insert(transfer.from_agent);
            nodes.insert(transfer.to_agent);

            if transfer.accepted {
                edges.push(LearningNetworkEdge {
                    from: transfer.from_agent,
                    to: transfer.to_agent,
                    strength: transfer.effectiveness,
                });
            }
        }

        LearningNetwork {
            agents: nodes.into_iter().collect(),
            connections: edges,
        }
    }
}

/// Represents the network of learning relationships between agents
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct LearningNetwork {
    /// Agents in the network
    pub agents: Vec<AgentId>,

    /// Connections (who learned from whom)
    pub connections: Vec<LearningNetworkEdge>,
}

/// Edge in the learning network
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct LearningNetworkEdge {
    /// Source agent
    pub from: AgentId,

    /// Target agent
    pub to: AgentId,

    /// Strength of the learning relationship
    pub strength: f64,
}

#[cfg(test)]
mod tests {
    use super::*;
    use agentic_domain::learning::LearningType;

    #[test]
    fn test_knowledge_transfer() {
        let from = AgentId::generate();
        let to = AgentId::generate();

        let event = LearningEvent::new(
            from,
            LearningType::Success,
            "Discovered pattern",
            "test",
        );

        let transfer = KnowledgeTransfer::new(from, to, event);
        assert_eq!(transfer.from_agent, from);
        assert_eq!(transfer.to_agent, to);
        assert!(!transfer.accepted);
    }

    #[test]
    fn test_knowledge_transfer_manager() {
        let mut manager = KnowledgeTransferManager::new();

        let from = AgentId::generate();
        let to = AgentId::generate();

        let event = LearningEvent::new(
            from,
            LearningType::Success,
            "Test learning",
            "test",
        );

        let transfer = KnowledgeTransfer::new(from, to, event).accept();
        manager.record_transfer(transfer);

        assert_eq!(manager.total_transfers, 1);
        assert_eq!(manager.successful_transfers, 1);
    }
}
