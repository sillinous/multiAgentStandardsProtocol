//! Multi-agent orchestration patterns
//!
//! Supports:
//! - Supervisor (hierarchical) orchestration
//! - Swarm (peer-to-peer) orchestration
//! - Emergent (self-organizing) orchestration
//! - Hybrid patterns

use agentic_core::identity::{AgentId, WorkflowId};
use serde::{Deserialize, Serialize};
use serde_json::Value;

/// Type of orchestration pattern
#[derive(Clone, Debug, Eq, PartialEq, Serialize, Deserialize)]
pub enum OrchestrationType {
    /// Hierarchical: supervisor agent delegates to workers
    Supervisor,

    /// Peer-to-peer: agents hand off to each other
    Swarm,

    /// Self-organizing: agents coordinate based on needs
    Emergent,

    /// Mixed approach
    Hybrid,

    /// Custom user-defined pattern
    Custom(String),
}

impl std::fmt::Display for OrchestrationType {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            OrchestrationType::Supervisor => write!(f, "supervisor"),
            OrchestrationType::Swarm => write!(f, "swarm"),
            OrchestrationType::Emergent => write!(f, "emergent"),
            OrchestrationType::Hybrid => write!(f, "hybrid"),
            OrchestrationType::Custom(name) => write!(f, "custom:{}", name),
        }
    }
}

/// Represents a handoff from one agent to another
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Handoff {
    /// Current agent (doing the handing off)
    pub from_agent: AgentId,

    /// Next agent (receiving the work)
    pub to_agent: AgentId,

    /// Reason for the handoff
    pub reason: String,

    /// Work/context to pass
    pub context: Value,

    /// Priority of the work
    pub priority: u8,

    /// Whether the handoff is required or suggested
    pub required: bool,

    /// Conditions for successful completion
    pub completion_criteria: Option<String>,
}

impl Handoff {
    /// Create a new handoff
    pub fn new(
        from_agent: AgentId,
        to_agent: AgentId,
        reason: impl Into<String>,
        context: Value,
    ) -> Self {
        Self {
            from_agent,
            to_agent,
            reason: reason.into(),
            context,
            priority: 50,
            required: false,
            completion_criteria: None,
        }
    }

    /// Mark as required
    pub fn required(mut self) -> Self {
        self.required = true;
        self
    }

    /// Set priority
    pub fn with_priority(mut self, priority: u8) -> Self {
        self.priority = priority.min(100);
        self
    }

    /// Set completion criteria
    pub fn with_criteria(mut self, criteria: impl Into<String>) -> Self {
        self.completion_criteria = Some(criteria.into());
        self
    }
}

/// Role in a workflow
#[derive(Clone, Debug, Eq, PartialEq, Serialize, Deserialize)]
pub enum WorkflowRole {
    /// Orchestrator/coordinator
    Orchestrator,

    /// Individual contributor
    Contributor,

    /// Observer/monitor
    Observer,

    /// Specialist in specific domain
    Specialist(String),
}

/// Assignment of an agent to a workflow role
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct AgentAssignment {
    /// Agent being assigned
    pub agent_id: AgentId,

    /// Role in the workflow
    pub role: WorkflowRole,

    /// Whether this assignment is fixed or can change
    pub is_fixed: bool,

    /// Specialties/capabilities for this role
    pub specialties: Vec<String>,
}

impl AgentAssignment {
    /// Create new assignment
    pub fn new(agent_id: AgentId, role: WorkflowRole) -> Self {
        Self {
            agent_id,
            role,
            is_fixed: false,
            specialties: Vec::new(),
        }
    }

    /// Mark as fixed (cannot change during workflow)
    pub fn fixed(mut self) -> Self {
        self.is_fixed = true;
        self
    }

    /// Add specialty
    pub fn with_specialty(mut self, specialty: impl Into<String>) -> Self {
        self.specialties.push(specialty.into());
        self
    }
}

/// Dependency between workflow tasks
#[derive(Clone, Debug, Serialize, Deserialize)]
pub enum TaskDependency {
    /// Task B depends on successful completion of Task A
    DependsOn(String),

    /// Task B cannot start until Task A is complete
    BlockedBy(String),

    /// Parallel execution OK
    Parallel,

    /// Optional dependency (nice to have)
    Soft(String),
}

/// Orchestration configuration for a workflow
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct OrchestrationConfig {
    /// Workflow ID
    pub workflow_id: WorkflowId,

    /// Pattern to use
    pub pattern: OrchestrationType,

    /// Agents and their roles
    pub assignments: Vec<AgentAssignment>,

    /// Primary orchestrator (if supervisor pattern)
    pub orchestrator: Option<AgentId>,

    /// Maximum number of agents in workflow
    pub max_agents: Option<usize>,

    /// Maximum execution time in seconds
    pub timeout_secs: Option<u64>,

    /// Whether to allow dynamic agent addition
    pub allow_dynamic_agents: bool,

    /// Policy for agent selection
    pub selection_policy: String,

    /// Whether to enable automatic handoffs
    pub auto_handoff: bool,

    /// Config parameters
    pub params: Value,
}

impl OrchestrationConfig {
    /// Create supervisor orchestration config
    pub fn supervisor(workflow_id: WorkflowId, orchestrator: AgentId) -> Self {
        Self {
            workflow_id,
            pattern: OrchestrationType::Supervisor,
            assignments: vec![AgentAssignment::new(orchestrator, WorkflowRole::Orchestrator).fixed()],
            orchestrator: Some(orchestrator),
            max_agents: Some(10),
            timeout_secs: Some(3600),
            allow_dynamic_agents: true,
            selection_policy: "capability_match".to_string(),
            auto_handoff: false,
            params: serde_json::json!({}),
        }
    }

    /// Create swarm orchestration config
    pub fn swarm(workflow_id: WorkflowId, agents: Vec<AgentId>) -> Self {
        let assignments = agents
            .into_iter()
            .map(|agent_id| AgentAssignment::new(agent_id, WorkflowRole::Contributor))
            .collect();

        Self {
            workflow_id,
            pattern: OrchestrationType::Swarm,
            assignments,
            orchestrator: None,
            max_agents: None,
            timeout_secs: Some(3600),
            allow_dynamic_agents: true,
            selection_policy: "dynamic_handoff".to_string(),
            auto_handoff: true,
            params: serde_json::json!({}),
        }
    }

    /// Create emergent orchestration config
    pub fn emergent(workflow_id: WorkflowId) -> Self {
        Self {
            workflow_id,
            pattern: OrchestrationType::Emergent,
            assignments: Vec::new(),
            orchestrator: None,
            max_agents: None,
            timeout_secs: Some(3600),
            allow_dynamic_agents: true,
            selection_policy: "self_organizing".to_string(),
            auto_handoff: true,
            params: serde_json::json!({}),
        }
    }

    /// Add an agent assignment
    pub fn with_assignment(mut self, assignment: AgentAssignment) -> Self {
        self.assignments.push(assignment);
        self
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_handoff_creation() {
        let from = AgentId::generate();
        let to = AgentId::generate();

        let handoff = Handoff::new(from, to, "Task needs expertise", serde_json::json!({}));

        assert_eq!(handoff.from_agent, from);
        assert_eq!(handoff.to_agent, to);
    }

    #[test]
    fn test_orchestration_configs() {
        let workflow_id = WorkflowId::generate();
        let orchestrator = AgentId::generate();

        let supervisor_config = OrchestrationConfig::supervisor(workflow_id, orchestrator);
        assert_eq!(supervisor_config.pattern, OrchestrationType::Supervisor);
        assert_eq!(supervisor_config.orchestrator, Some(orchestrator));

        let swarm_config = OrchestrationConfig::swarm(
            workflow_id,
            vec![AgentId::generate(), AgentId::generate()],
        );
        assert_eq!(swarm_config.pattern, OrchestrationType::Swarm);

        let emergent_config = OrchestrationConfig::emergent(workflow_id);
        assert_eq!(emergent_config.pattern, OrchestrationType::Emergent);
    }
}
