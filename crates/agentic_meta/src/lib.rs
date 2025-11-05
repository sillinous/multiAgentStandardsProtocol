//! Meta-Agent System - Agents that create and manage other agents
//!
//! This crate provides meta-agents with capabilities to:
//! - Create new agents based on requirements
//! - Manage full SDLC (Software Development Lifecycle)
//! - Evolve and improve existing agents
//! - Synthesize new capabilities
//! - Self-improve and self-maintain

pub mod meta_agent;
pub mod factory_agent;
pub mod sdlc_manager;
pub mod code_generator;
pub mod testing_agent;
pub mod specialist_agents;
pub mod requirements;

pub use meta_agent::{MetaAgent, MetaAgentType, MetaAgentCapability};
pub use factory_agent::FactoryMetaAgent;
pub use sdlc_manager::SDLCManager;
pub use code_generator::{CodeGeneratorAgent, CodeGenRequest, GeneratedCode};
pub use testing_agent::{TestingAgent, TestGenRequest, GeneratedTests, TestType};
pub use requirements::{AgentRequirement, FeatureRequest, CapabilitySpec};
