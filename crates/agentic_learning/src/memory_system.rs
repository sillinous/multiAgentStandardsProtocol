//! Memory system for agents (episodic, semantic, procedural)

use agentic_core::identity::AgentId;
use agentic_domain::learning::{Memory, MemoryType};
use chrono::Utc;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Memory system managing all memory types for an agent
#[derive(Clone, Debug, Default, Serialize, Deserialize)]
pub struct MemorySystem {
    /// Agent ID
    pub agent_id: AgentId,

    /// All memories organized by type
    pub memories_by_type: HashMap<String, Vec<Memory>>,

    /// All memories by ID for quick access
    pub memories_by_id: HashMap<String, Memory>,

    /// Statistics
    pub total_stored: u32,
    pub total_accessed: u32,
    pub avg_relevance: f64,
}

impl MemorySystem {
    /// Create a new memory system for an agent
    pub fn new(agent_id: AgentId) -> Self {
        Self {
            agent_id,
            memories_by_type: HashMap::new(),
            memories_by_id: HashMap::new(),
            total_stored: 0,
            total_accessed: 0,
            avg_relevance: 0.0,
        }
    }

    /// Store a memory
    pub fn store(&mut self, mut memory: Memory) {
        // Ensure memory belongs to this agent
        assert_eq!(memory.agent_id, self.agent_id);

        self.memories_by_id.insert(memory.id.clone(), memory.clone());

        let memory_type_str = match memory.memory_type {
            MemoryType::Episodic => "episodic",
            MemoryType::Semantic => "semantic",
            MemoryType::Procedural => "procedural",
        };

        self.memories_by_type
            .entry(memory_type_str.to_string())
            .or_insert_with(Vec::new)
            .push(memory);

        self.total_stored += 1;
        self.update_statistics();
    }

    /// Retrieve a memory by ID
    pub fn retrieve(&mut self, memory_id: &str) -> Option<&Memory> {
        if let Some(memory) = self.memories_by_id.get_mut(memory_id) {
            memory.access();
            self.total_accessed += 1;
            self.update_statistics();
            return Some(memory);
        }
        None
    }

    /// Get all memories of a specific type
    pub fn get_by_type(&self, memory_type: MemoryType) -> Vec<&Memory> {
        let type_str = match memory_type {
            MemoryType::Episodic => "episodic",
            MemoryType::Semantic => "semantic",
            MemoryType::Procedural => "procedural",
        };

        self.memories_by_type
            .get(type_str)
            .map(|memories| memories.iter().collect())
            .unwrap_or_default()
    }

    /// Get memories by tag
    pub fn get_by_tag(&self, tag: &str) -> Vec<&Memory> {
        self.memories_by_id
            .values()
            .filter(|m| m.tags.contains(&tag.to_string()))
            .collect()
    }

    /// Get most relevant memories
    pub fn get_most_relevant(&self, limit: usize) -> Vec<&Memory> {
        let mut memories: Vec<_> = self.memories_by_id.values().collect();
        memories.sort_by(|a, b| b.relevance.partial_cmp(&a.relevance).unwrap_or(std::cmp::Ordering::Equal));
        memories.into_iter().take(limit).collect()
    }

    /// Get recently accessed memories
    pub fn get_recently_accessed(&self, limit: usize) -> Vec<&Memory> {
        let mut memories: Vec<_> = self.memories_by_id.values().collect();
        memories.sort_by(|a, b| b.accessed_at.cmp(&a.accessed_at));
        memories.into_iter().take(limit).collect()
    }

    /// Forget a memory (remove)
    pub fn forget(&mut self, memory_id: &str) {
        if let Some(memory) = self.memories_by_id.remove(memory_id) {
            let type_str = match memory.memory_type {
                MemoryType::Episodic => "episodic",
                MemoryType::Semantic => "semantic",
                MemoryType::Procedural => "procedural",
            };

            if let Some(memories) = self.memories_by_type.get_mut(type_str) {
                memories.retain(|m| m.id != memory_id);
            }
        }
    }

    /// Consolidate memories (combine related ones)
    pub fn consolidate(&mut self, source_ids: Vec<String>, consolidated_memory: Memory) {
        // Remove source memories
        for id in source_ids {
            self.forget(&id);
        }

        // Store consolidated memory
        self.store(consolidated_memory);
    }

    /// Update relevance scores
    pub fn update_relevance(&mut self, memory_id: &str, new_relevance: f64) {
        if let Some(memory) = self.memories_by_id.get_mut(memory_id) {
            memory.relevance = new_relevance.clamp(0.0, 1.0);
            self.update_statistics();
        }
    }

    /// Decay memories that haven't been accessed (forgetting over time)
    pub fn decay_unused(&mut self, days: i64) {
        let cutoff = Utc::now() - chrono::Duration::days(days);

        let to_remove: Vec<String> = self
            .memories_by_id
            .iter()
            .filter(|(_, m)| m.accessed_at < cutoff && m.relevance < 0.3)
            .map(|(id, _)| id.clone())
            .collect();

        for id in to_remove {
            self.forget(&id);
        }
    }

    /// Update statistics
    fn update_statistics(&mut self) {
        if !self.memories_by_id.is_empty() {
            self.avg_relevance =
                self.memories_by_id.values().map(|m| m.relevance).sum::<f64>()
                    / self.memories_by_id.len() as f64;
        }
    }

    /// Get total memories
    pub fn total_memories(&self) -> usize {
        self.memories_by_id.len()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_memory_storage() {
        let agent_id = AgentId::generate();
        let mut memory_system = MemorySystem::new(agent_id);

        let memory = Memory::new(
            agent_id,
            MemoryType::Semantic,
            "Important fact",
        );

        memory_system.store(memory);
        assert_eq!(memory_system.total_memories(), 1);
    }

    #[test]
    fn test_memory_retrieval() {
        let agent_id = AgentId::generate();
        let mut memory_system = MemorySystem::new(agent_id);

        let memory = Memory::new(
            agent_id,
            MemoryType::Episodic,
            "A specific experience",
        );

        let memory_id = memory.id.clone();
        memory_system.store(memory);

        let retrieved = memory_system.retrieve(&memory_id);
        assert!(retrieved.is_some());
    }

    #[test]
    fn test_memory_by_type() {
        let agent_id = AgentId::generate();
        let mut memory_system = MemorySystem::new(agent_id);

        memory_system.store(Memory::new(agent_id, MemoryType::Episodic, "Event"));
        memory_system.store(Memory::new(agent_id, MemoryType::Semantic, "Fact"));

        let episodic = memory_system.get_by_type(MemoryType::Episodic);
        let semantic = memory_system.get_by_type(MemoryType::Semantic);

        assert_eq!(episodic.len(), 1);
        assert_eq!(semantic.len(), 1);
    }
}
