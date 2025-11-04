//! Core abstractions and traits for the autonomous multi-agent ecosystem
//!
//! This crate provides fundamental types, traits, and interfaces that form the foundation
//! of the agentic ecosystem, including:
//!
//! - Agent identity and lifecycle management
//! - Communication protocols and message types
//! - Tool and capability definitions
//! - Error handling and result types
//!
//! # Architecture
//!
//! The core layer provides trait-based abstractions to allow different implementations
//! of agents, learning systems, and coordination patterns while maintaining a consistent
//! interface across the ecosystem.

pub mod agent;
pub mod capability;
pub mod communication;
pub mod error;
pub mod identity;
pub mod message;
pub mod tool;

pub use agent::{Agent, AgentRole, AgentStatus};
pub use capability::{Capability, CapabilityCard};
pub use communication::{Protocol, ProtocolVersion};
pub use error::{Error, Result};
pub use identity::{AgentId, WorkflowId};
pub use message::{Message, MessageContent};
pub use tool::{Tool, ToolCall, ToolResult};
