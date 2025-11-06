//! Domain models for the autonomous multi-agent ecosystem
//!
//! This crate contains the core domain models that enable agents to:
//! - Evolve their capabilities (AgentGenome)
//! - Learn from experiences (Learning substrate)
//! - Experiment autonomously (Experiment framework)
//! - Self-organize and coordinate (Orchestration)
//! - Create new agents (AgentFactory)

pub mod agent_genome;
pub mod learning;
pub mod experiment;
pub mod orchestration;
pub mod workflow;
pub mod state;

pub use agent_genome::{AgentGenome, GenomeVersion, Trait, TraitMutation};
pub use learning::{Learning, LearningEvent, LearningType};
pub use experiment::{Experiment, ExperimentStatus};
pub use orchestration::{OrchestrationType, Handoff};
pub use workflow::{Workflow, WorkflowStatus};
