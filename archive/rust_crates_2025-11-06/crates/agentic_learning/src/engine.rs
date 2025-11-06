//! Core learning engine for processing and applying learnings

use agentic_core::identity::AgentId;
use agentic_domain::learning::{Learning, LearningEvent, LearningType, Memory, MemoryType};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// The Learning Engine processes learning events and applies them
/// to agent genomes for continuous improvement
#[derive(Clone, Debug, Default, Serialize, Deserialize)]
pub struct LearningEngine {
    /// All learning events by agent
    pub learning_by_agent: HashMap<AgentId, Vec<LearningEvent>>,

    /// Global learning statistics
    pub total_events_processed: u32,

    /// Learning events successfully acted upon
    pub learning_events_applied: u32,

    /// Average insight confidence
    pub avg_confidence: f64,

    /// Learning success rate
    pub success_rate: f64,
}

impl LearningEngine {
    /// Create a new learning engine
    pub fn new() -> Self {
        Self::default()
    }

    /// Process a learning event
    pub fn process_event(&mut self, event: LearningEvent) -> crate::agentic_core::Result<()> {
        let agent_id = event.learner_id;

        // Store the event
        self.learning_by_agent
            .entry(agent_id)
            .or_insert_with(Vec::new)
            .push(event.clone());

        // Update statistics
        self.total_events_processed += 1;

        if event.acted_upon {
            self.learning_events_applied += 1;
        }

        // Update success rate
        if self.total_events_processed > 0 {
            self.success_rate =
                self.learning_events_applied as f64 / self.total_events_processed as f64;
        }

        Ok(())
    }

    /// Get all learning events for an agent
    pub fn get_agent_learnings(&self, agent_id: &AgentId) -> Option<&Vec<LearningEvent>> {
        self.learning_by_agent.get(agent_id)
    }

    /// Get recent learnings for an agent
    pub fn get_recent_learnings(&self, agent_id: &AgentId, count: usize) -> Vec<&LearningEvent> {
        self.learning_by_agent
            .get(agent_id)
            .map(|learnings| learnings.iter().rev().take(count).collect())
            .unwrap_or_default()
    }

    /// Find high-confidence learnings that should be applied
    pub fn get_actionable_learnings(
        &self,
        agent_id: &AgentId,
        confidence_threshold: f64,
    ) -> Vec<&LearningEvent> {
        self.learning_by_agent
            .get(agent_id)
            .map(|learnings| {
                learnings
                    .iter()
                    .filter(|e| e.confidence >= confidence_threshold && !e.acted_upon)
                    .collect()
            })
            .unwrap_or_default()
    }

    /// Get learning statistics for an agent
    pub fn get_agent_stats(&self, agent_id: &AgentId) -> LearningStats {
        if let Some(learnings) = self.learning_by_agent.get(agent_id) {
            let total = learnings.len();
            let successful = learnings.iter().filter(|e| e.learning_type == LearningType::Success).count();
            let peer_learnings = learnings.iter().filter(|e| e.learning_type == LearningType::PeerLearning).count();
            let avg_confidence = learnings.iter().map(|e| e.confidence).sum::<f64>() / total as f64;

            LearningStats {
                total_learnings: total as u32,
                successful_learnings: successful as u32,
                peer_learnings: peer_learnings as u32,
                avg_confidence,
                success_rate: successful as f64 / total as f64,
            }
        } else {
            LearningStats::default()
        }
    }

    /// Apply a learning event to an agent genome (mutation)
    /// Returns whether the mutation should be accepted
    pub fn apply_learning(&mut self, event: &mut LearningEvent) -> bool {
        // Mark as acted upon
        event.mark_acted_upon();

        // Update statistics
        self.learning_events_applied += 1;
        if self.total_events_processed > 0 {
            self.success_rate =
                self.learning_events_applied as f64 / self.total_events_processed as f64;
        }

        // High-confidence learnings should be applied
        event.confidence >= 0.7
    }
}

/// Statistics about learning for an agent
#[derive(Clone, Debug, Default, Serialize, Deserialize)]
pub struct LearningStats {
    pub total_learnings: u32,
    pub successful_learnings: u32,
    pub peer_learnings: u32,
    pub avg_confidence: f64,
    pub success_rate: f64,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_learning_engine_creation() {
        let engine = LearningEngine::new();
        assert_eq!(engine.total_events_processed, 0);
    }

    #[test]
    fn test_process_event() {
        let mut engine = LearningEngine::new();
        let agent_id = AgentId::generate();

        let event = LearningEvent::new(
            agent_id,
            LearningType::Success,
            "Learned something useful",
            "test",
        );

        engine.process_event(event).unwrap();
        assert_eq!(engine.total_events_processed, 1);
    }

    #[test]
    fn test_agent_stats() {
        let mut engine = LearningEngine::new();
        let agent_id = AgentId::generate();

        for _ in 0..3 {
            let event = LearningEvent::new(
                agent_id,
                LearningType::Success,
                "Learning",
                "test",
            );
            engine.process_event(event).unwrap();
        }

        let stats = engine.get_agent_stats(&agent_id);
        assert_eq!(stats.total_learnings, 3);
        assert_eq!(stats.successful_learnings, 3);
    }
}
