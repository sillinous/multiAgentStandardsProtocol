//! Agent Genome - DNA-like representation of agent capabilities and personality
//!
//! The genome is the heritable blueprint for an agent. It can be:
//! - Mutated to create new variants
//! - Evolved based on fitness scores
//! - Shared with other agents for collective learning
//! - Versioned and checkpointed for rollback

use agentic_core::identity::AgentId;
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::HashMap;

/// A trait represents a heritable characteristic that can be mutated
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Trait {
    /// Name of the trait (e.g., "reasoning_style", "tool_preference")
    pub name: String,

    /// Current value (can be anything from string to complex JSON)
    pub value: Value,

    /// Confidence level in this trait (0.0 to 1.0)
    pub confidence: f64,

    /// Whether this trait is evolvable
    pub evolvable: bool,

    /// Version when this trait was introduced
    pub introduced_in_version: String,

    /// Mutation count
    pub mutation_count: u32,

    /// Successful mutations that led to improvement
    pub successful_mutations: u32,
}

impl Trait {
    /// Create a new trait
    pub fn new(name: impl Into<String>, value: Value) -> Self {
        Self {
            name: name.into(),
            value,
            confidence: 0.5,
            evolvable: true,
            introduced_in_version: "1.0.0".to_string(),
            mutation_count: 0,
            successful_mutations: 0,
        }
    }

    /// Set confidence level
    pub fn with_confidence(mut self, confidence: f64) -> Self {
        self.confidence = confidence.clamp(0.0, 1.0);
        self
    }

    /// Mark as not evolvable
    pub fn not_evolvable(mut self) -> Self {
        self.evolvable = false;
        self
    }
}

/// Represents a mutation applied to a trait
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct TraitMutation {
    /// Name of the trait being mutated
    pub trait_name: String,

    /// Original value before mutation
    pub original_value: Value,

    /// New value after mutation
    pub new_value: Value,

    /// Reason/description of the mutation
    pub reason: String,

    /// Fitness improvement from this mutation (positive or negative)
    pub fitness_delta: f64,

    /// Whether this mutation was accepted into the genome
    pub accepted: bool,

    /// When this mutation was applied
    pub timestamp: DateTime<Utc>,
}

impl TraitMutation {
    /// Create a new trait mutation
    pub fn new(
        trait_name: impl Into<String>,
        original_value: Value,
        new_value: Value,
        reason: impl Into<String>,
    ) -> Self {
        Self {
            trait_name: trait_name.into(),
            original_value,
            new_value,
            reason: reason.into(),
            fitness_delta: 0.0,
            accepted: false,
            timestamp: Utc::now(),
        }
    }

    /// Set fitness improvement
    pub fn with_fitness_delta(mut self, delta: f64) -> Self {
        self.fitness_delta = delta;
        self
    }

    /// Mark as accepted
    pub fn accept(mut self) -> Self {
        self.accepted = true;
        self
    }
}

/// Version information for a genome
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct GenomeVersion {
    /// Semantic version (e.g., "1.2.3")
    pub version: String,

    /// Parent genome version (for tracking evolution lineage)
    pub parent_version: Option<String>,

    /// Hash of the genome content for integrity checking
    pub content_hash: String,

    /// Fitness score at time of versioning
    pub fitness_at_version: f64,

    /// When this version was created
    pub created_at: DateTime<Utc>,

    /// Description of changes in this version
    pub changelog: String,
}

/// Agent Genome - the DNA-like blueprint for agent capabilities and behavior
///
/// An agent genome encodes all the evolvable aspects of an agent:
/// - Behavioral traits
/// - Personality characteristics
/// - Tool preferences
/// - Reasoning styles
/// - Learned patterns
///
/// Genomes can be mutated, evolved, and shared between agents for collective learning.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct AgentGenome {
    /// Agent ID this genome belongs to
    pub agent_id: AgentId,

    /// Current version
    pub version: GenomeVersion,

    /// All traits (the actual genome data)
    pub traits: HashMap<String, Trait>,

    /// Evolution history
    pub evolution_history: Vec<TraitMutation>,

    /// Mutation attempts (successful and failed)
    pub mutation_attempts: u32,

    /// Successful mutations
    pub successful_mutations: u32,

    /// Overall fitness score
    pub fitness_score: f64,

    /// Specialization (e.g., "data_analysis", "code_generation")
    pub specialization: String,

    /// Whether this genome is locked (no mutations allowed)
    pub locked: bool,

    /// Metadata
    pub metadata: HashMap<String, Value>,
}

impl AgentGenome {
    /// Create a new genome for an agent
    pub fn new(agent_id: AgentId, specialization: impl Into<String>) -> Self {
        let now = Utc::now();
        let version = GenomeVersion {
            version: "1.0.0".to_string(),
            parent_version: None,
            content_hash: Self::compute_hash(&HashMap::new()),
            fitness_at_version: 0.5,
            created_at: now,
            changelog: "Initial genome creation".to_string(),
        };

        Self {
            agent_id,
            version,
            traits: HashMap::new(),
            evolution_history: Vec::new(),
            mutation_attempts: 0,
            successful_mutations: 0,
            fitness_score: 0.5,
            specialization: specialization.into(),
            locked: false,
            metadata: HashMap::new(),
        }
    }

    /// Add a trait to the genome
    pub fn add_trait(&mut self, trait_obj: Trait) {
        self.traits.insert(trait_obj.name.clone(), trait_obj);
    }

    /// Get a trait by name
    pub fn get_trait(&self, name: &str) -> Option<&Trait> {
        self.traits.get(name)
    }

    /// Apply a mutation to the genome
    pub fn apply_mutation(&mut self, mutation: TraitMutation) -> crate::agentic_core::Result<()> {
        if self.locked {
            return Err(agentic_core::Error::InvalidState(
                "Cannot mutate locked genome".to_string(),
            ));
        }

        let trait_name = &mutation.trait_name;

        // Check if trait exists and is evolvable
        if let Some(trait_obj) = self.traits.get_mut(trait_name) {
            if !trait_obj.evolvable {
                return Err(agentic_core::Error::InvalidState(
                    format!("Trait {} is not evolvable", trait_name),
                ));
            }

            // Apply mutation
            trait_obj.value = mutation.new_value.clone();
            trait_obj.mutation_count += 1;

            if mutation.accepted {
                trait_obj.successful_mutations += 1;
            }
        }

        self.mutation_attempts += 1;
        if mutation.accepted {
            self.successful_mutations += 1;
            self.fitness_score += mutation.fitness_delta;
        }

        self.evolution_history.push(mutation);
        Ok(())
    }

    /// Create a new version checkpoint
    pub fn checkpoint(&mut self, changelog: impl Into<String>) {
        let current_version = &self.version;
        let old_version = current_version.version.clone();

        // Increment semantic version
        let new_version = Self::bump_version(&old_version);

        self.version = GenomeVersion {
            version: new_version,
            parent_version: Some(old_version),
            content_hash: Self::compute_hash(&self.traits),
            fitness_at_version: self.fitness_score,
            created_at: Utc::now(),
            changelog: changelog.into(),
        };
    }

    /// Get mutation success rate
    pub fn mutation_success_rate(&self) -> f64 {
        if self.mutation_attempts == 0 {
            0.0
        } else {
            self.successful_mutations as f64 / self.mutation_attempts as f64
        }
    }

    /// Lock the genome (prevent mutations)
    pub fn lock(&mut self) {
        self.locked = true;
    }

    /// Unlock the genome (allow mutations)
    pub fn unlock(&mut self) {
        self.locked = false;
    }

    /// Compute hash of genome traits
    fn compute_hash(traits: &HashMap<String, Trait>) -> String {
        use std::collections::hash_map::DefaultHasher;
        use std::hash::{Hash, Hasher};

        let json_str = serde_json::to_string(&traits).unwrap_or_default();
        let mut hasher = DefaultHasher::new();
        json_str.hash(&mut hasher);
        format!("{:x}", hasher.finish())
    }

    /// Bump semantic version
    fn bump_version(current: &str) -> String {
        let parts: Vec<&str> = current.split('.').collect();
        if let [major, minor, patch] = parts.as_slice() {
            if let Ok(p) = patch.parse::<u32>() {
                return format!("{}.{}.{}", major, minor, p + 1);
            }
        }
        format!("{}.patch", current)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_trait_creation() {
        let trait_obj = Trait::new("reasoning_style", serde_json::json!("analytical"));
        assert_eq!(trait_obj.name, "reasoning_style");
        assert!(trait_obj.evolvable);
    }

    #[test]
    fn test_genome_creation() {
        let agent_id = AgentId::generate();
        let genome = AgentGenome::new(agent_id, "data_analysis");

        assert_eq!(genome.agent_id, agent_id);
        assert_eq!(genome.specialization, "data_analysis");
        assert!(!genome.locked);
    }

    #[test]
    fn test_genome_mutations() {
        let agent_id = AgentId::generate();
        let mut genome = AgentGenome::new(agent_id, "data_analysis");

        let trait_obj = Trait::new("reasoning_style", serde_json::json!("analytical"));
        genome.add_trait(trait_obj);

        let mutation = TraitMutation::new(
            "reasoning_style",
            serde_json::json!("analytical"),
            serde_json::json!("creative"),
            "Improve creativity",
        )
        .with_fitness_delta(0.1)
        .accept();

        genome.apply_mutation(mutation).unwrap();

        assert_eq!(genome.mutation_attempts, 1);
        assert_eq!(genome.successful_mutations, 1);
        assert!(genome.mutation_success_rate() > 0.0);
    }

    #[test]
    fn test_genome_checkpoint() {
        let agent_id = AgentId::generate();
        let mut genome = AgentGenome::new(agent_id, "data_analysis");

        let old_version = genome.version.version.clone();
        genome.checkpoint("Added new capability");

        assert_ne!(genome.version.version, old_version);
        assert_eq!(genome.version.parent_version, Some(old_version));
    }

    #[test]
    fn test_genome_locking() {
        let agent_id = AgentId::generate();
        let mut genome = AgentGenome::new(agent_id, "data_analysis");

        genome.lock();
        assert!(genome.locked);

        genome.unlock();
        assert!(!genome.locked);
    }
}
