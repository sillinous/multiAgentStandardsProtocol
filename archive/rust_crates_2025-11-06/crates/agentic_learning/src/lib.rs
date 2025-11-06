//! Learning substrate for the multi-agent ecosystem
//!
//! Provides:
//! - Learning event recording and processing
//! - Multi-agent knowledge sharing
//! - Episodic, semantic, and procedural memory
//! - Knowledge graph management
//! - Learning-driven evolution

pub mod engine;
pub mod knowledge_graph;
pub mod memory_system;
pub mod transfer;

pub use engine::LearningEngine;
pub use knowledge_graph::KnowledgeGraph;
pub use memory_system::MemorySystem;
pub use transfer::KnowledgeTransfer;
