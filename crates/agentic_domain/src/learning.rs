//! Learning and knowledge models for agents
//!
//! Supports:
//! - Episodic memory (specific experiences)
//! - Semantic memory (generalized knowledge)
//! - Procedural memory (learned skills/patterns)
//! - Knowledge transfer between agents

use agentic_core::identity::AgentId;
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use serde_json::Value;

/// Types of learning events
#[derive(Clone, Debug, Eq, PartialEq, Serialize, Deserialize)]
pub enum LearningType {
    /// Learning from successful task completion
    Success,

    /// Learning from failure
    Failure,

    /// Learning from peer agents
    PeerLearning,

    /// Learning from experimentation
    Experimental,

    /// Learning from feedback
    Feedback,

    /// Pattern recognition
    Pattern,

    /// Emergent behavior discovery
    Emergence,
}

/// A single learning event - something learned from experience
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct LearningEvent {
    /// Unique identifier
    pub id: String,

    /// Agent that learned this
    pub learner_id: AgentId,

    /// Type of learning
    pub learning_type: LearningType,

    /// What was learned (natural language or structured)
    pub insight: String,

    /// Structured data about the learning
    pub data: Option<Value>,

    /// Confidence level (0.0 to 1.0)
    pub confidence: f64,

    /// Source of the learning (task, experiment, observation, etc.)
    pub source: String,

    /// Related task ID or experiment ID
    pub related_id: Option<String>,

    /// When this was learned
    pub timestamp: DateTime<Utc>,

    /// Relevant context
    pub context: Option<Value>,

    /// Impact on fitness (positive or negative)
    pub fitness_impact: f64,

    /// Whether this learning has been acted upon (incorporated into genome)
    pub acted_upon: bool,

    /// Agents that have learned from this learning (collective learning)
    pub shared_with: Vec<AgentId>,
}

impl LearningEvent {
    /// Create a new learning event
    pub fn new(
        learner_id: AgentId,
        learning_type: LearningType,
        insight: impl Into<String>,
        source: impl Into<String>,
    ) -> Self {
        Self {
            id: nanoid::nanoid!(),
            learner_id,
            learning_type,
            insight: insight.into(),
            data: None,
            confidence: 0.5,
            source: source.into(),
            related_id: None,
            timestamp: Utc::now(),
            context: None,
            fitness_impact: 0.0,
            acted_upon: false,
            shared_with: Vec::new(),
        }
    }

    /// Set confidence level
    pub fn with_confidence(mut self, confidence: f64) -> Self {
        self.confidence = confidence.clamp(0.0, 1.0);
        self
    }

    /// Set structured data
    pub fn with_data(mut self, data: Value) -> Self {
        self.data = Some(data);
        self
    }

    /// Set fitness impact
    pub fn with_fitness_impact(mut self, impact: f64) -> Self {
        self.fitness_impact = impact;
        self
    }

    /// Mark as acted upon
    pub fn mark_acted_upon(&mut self) {
        self.acted_upon = true;
    }

    /// Share this learning with another agent
    pub fn share_with(&mut self, agent_id: AgentId) {
        if !self.shared_with.contains(&agent_id) {
            self.shared_with.push(agent_id);
        }
    }
}

/// Memory type for storage and retrieval
#[derive(Clone, Debug, Serialize, Deserialize)]
pub enum MemoryType {
    /// Episodic: specific experiences (task execution, outcomes)
    Episodic,

    /// Semantic: generalized knowledge (facts, patterns, rules)
    Semantic,

    /// Procedural: learned skills and patterns (how to do things)
    Procedural,
}

/// A memory entry in the agent's knowledge system
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Memory {
    /// Unique identifier
    pub id: String,

    /// Agent that owns this memory
    pub agent_id: AgentId,

    /// Type of memory
    pub memory_type: MemoryType,

    /// Content of the memory
    pub content: String,

    /// Structured data
    pub data: Option<Value>,

    /// Relevance score (0.0 to 1.0) - how relevant is this for current tasks
    pub relevance: f64,

    /// Frequency of use
    pub usage_count: u32,

    /// When this memory was created
    pub created_at: DateTime<Utc>,

    /// When this memory was last accessed
    pub accessed_at: DateTime<Utc>,

    /// When this memory should expire (optional)
    pub expires_at: Option<DateTime<Utc>>,

    /// Tags for categorization
    pub tags: Vec<String>,

    /// Related learning events
    pub related_learnings: Vec<String>,
}

impl Memory {
    /// Create a new memory
    pub fn new(
        agent_id: AgentId,
        memory_type: MemoryType,
        content: impl Into<String>,
    ) -> Self {
        let now = Utc::now();
        Self {
            id: nanoid::nanoid!(),
            agent_id,
            memory_type,
            content: content.into(),
            data: None,
            relevance: 0.5,
            usage_count: 0,
            created_at: now,
            accessed_at: now,
            expires_at: None,
            tags: Vec::new(),
            related_learnings: Vec::new(),
        }
    }

    /// Access this memory (updates timestamp and usage count)
    pub fn access(&mut self) {
        self.accessed_at = Utc::now();
        self.usage_count += 1;
    }

    /// Add a tag
    pub fn with_tag(mut self, tag: impl Into<String>) -> Self {
        self.tags.push(tag.into());
        self
    }

    /// Set relevance score
    pub fn with_relevance(mut self, relevance: f64) -> Self {
        self.relevance = relevance.clamp(0.0, 1.0);
        self
    }
}

/// Knowledge graph node representing a concept or pattern
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct KnowledgeNode {
    /// Unique identifier
    pub id: String,

    /// Name/label of the concept
    pub name: String,

    /// Description
    pub description: String,

    /// Type of knowledge (fact, rule, pattern, etc.)
    pub knowledge_type: String,

    /// Structured representation
    pub data: Value,

    /// Agents that contributed to this knowledge
    pub contributors: Vec<AgentId>,

    /// Confidence level
    pub confidence: f64,

    /// When this was created
    pub created_at: DateTime<Utc>,

    /// When this was last updated
    pub updated_at: DateTime<Utc>,
}

impl KnowledgeNode {
    /// Create a new knowledge node
    pub fn new(
        name: impl Into<String>,
        description: impl Into<String>,
        knowledge_type: impl Into<String>,
    ) -> Self {
        let now = Utc::now();
        Self {
            id: nanoid::nanoid!(),
            name: name.into(),
            description: description.into(),
            knowledge_type: knowledge_type.into(),
            data: serde_json::json!({}),
            contributors: Vec::new(),
            confidence: 0.5,
            created_at: now,
            updated_at: now,
        }
    }

    /// Add a contributor
    pub fn add_contributor(&mut self, agent_id: AgentId) {
        if !self.contributors.contains(&agent_id) {
            self.contributors.push(agent_id);
        }
    }
}

/// Learning substrate - manages all learning and knowledge
#[derive(Clone, Debug, Default, Serialize, Deserialize)]
pub struct Learning {
    /// All learning events
    pub events: Vec<LearningEvent>,

    /// All memories
    pub memories: Vec<Memory>,

    /// Knowledge graph nodes
    pub knowledge_nodes: Vec<KnowledgeNode>,

    /// Statistics about learning
    pub total_events: u32,
    pub successful_learnings: u32,
    pub shared_learnings: u32,
}

impl Learning {
    /// Create a new learning substrate
    pub fn new() -> Self {
        Self::default()
    }

    /// Record a learning event
    pub fn record_event(&mut self, event: LearningEvent) {
        self.total_events += 1;
        if event.learning_type == LearningType::Success {
            self.successful_learnings += 1;
        }
        if !event.shared_with.is_empty() {
            self.shared_learnings += 1;
        }
        self.events.push(event);
    }

    /// Store a memory
    pub fn store_memory(&mut self, memory: Memory) {
        self.memories.push(memory);
    }

    /// Add knowledge node
    pub fn add_knowledge(&mut self, node: KnowledgeNode) {
        self.knowledge_nodes.push(node);
    }

    /// Get learning success rate
    pub fn success_rate(&self) -> f64 {
        if self.total_events == 0 {
            0.0
        } else {
            self.successful_learnings as f64 / self.total_events as f64
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_learning_event_creation() {
        let agent_id = AgentId::generate();
        let event = LearningEvent::new(
            agent_id,
            LearningType::Success,
            "Discovered efficient pattern",
            "task_execution",
        )
        .with_confidence(0.9);

        assert_eq!(event.learner_id, agent_id);
        assert_eq!(event.confidence, 0.9);
    }

    #[test]
    fn test_memory_creation() {
        let agent_id = AgentId::generate();
        let memory = Memory::new(
            agent_id,
            MemoryType::Semantic,
            "Semantic fact about the world",
        )
        .with_tag("important");

        assert_eq!(memory.agent_id, agent_id);
        assert!(memory.tags.contains(&"important".to_string()));
    }

    #[test]
    fn test_learning_substrate() {
        let mut learning = Learning::new();
        let agent_id = AgentId::generate();

        let event = LearningEvent::new(
            agent_id,
            LearningType::Success,
            "Test learning",
            "test",
        );

        learning.record_event(event);
        assert_eq!(learning.total_events, 1);
        assert_eq!(learning.successful_learnings, 1);
    }
}
