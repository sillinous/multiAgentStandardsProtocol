"""
Context Preservation Agent v1.0 - Architecturally Compliant
============================================================

Meta-Agent for Session Continuity and Knowledge Management

This agent maintains comprehensive context to allow AI assistants and agents
to understand the full backstory and pick up work seamlessly across sessions.

**Architectural Compliance:**
- Follows 8 architectural principles
- Supports 5 protocols (A2A, A2P, ACP, ANP, MCP)
- Environment-based configuration (12-factor)
- Standardized lifecycle management
- Resource monitoring and metrics

**Version:** 1.0
**Category:** Meta-Agent (Context Management & Knowledge)
**Protocols:** A2A, A2P, ACP, ANP, MCP
"""

import asyncio
import json
import os
import time
import psutil
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from library.core.base_agent import BaseAgent
from library.core.protocols import ProtocolMixin


# =========================================================================
# Constants
# =========================================================================

AGENT_TYPE = "context_preservation"
VERSION = "1.0"

DEFAULT_MAX_CONVERSATION_HISTORY = 1000
DEFAULT_MAX_KNOWLEDGE_ENTRIES = 5000


# =========================================================================
# Domain Models
# =========================================================================

@dataclass
class ProjectIdentity:
    """Core project identity"""
    name: str = ""
    mission: str = ""
    vision: str = ""
    values: List[str] = field(default_factory=list)
    unique_approach: str = ""
    target_audience: List[str] = field(default_factory=list)
    updated_at: str = ""


@dataclass
class TechnicalArchitecture:
    """Technical architecture context"""
    core_components: Dict[str, Any] = field(default_factory=dict)
    tech_stack: Dict[str, Any] = field(default_factory=dict)
    agent_types: List[str] = field(default_factory=list)
    data_flow: str = ""
    deployment: Dict[str, Any] = field(default_factory=dict)
    repos: List[str] = field(default_factory=list)
    documentation_links: List[str] = field(default_factory=list)
    updated_at: str = ""


@dataclass
class BusinessContext:
    """Business context"""
    current_stage: str = ""
    revenue_model: str = ""
    go_to_market: str = ""
    key_metrics: Dict[str, Any] = field(default_factory=dict)
    active_opportunities: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    updated_at: str = ""


# =========================================================================
# Configuration
# =========================================================================

@dataclass
class ContextPreservationAgentConfig:
    """
    Configuration for Context Preservation Agent

    All values can be overridden via environment variables following
    12-factor app methodology.
    """
    # Storage limits
    max_conversation_history: int = DEFAULT_MAX_CONVERSATION_HISTORY
    max_knowledge_entries: int = DEFAULT_MAX_KNOWLEDGE_ENTRIES

    # Export settings
    export_directory: str = "./context_exports"

    # Resource limits
    memory_limit_mb: int = 1024  # Higher limit due to context storage
    cpu_limit_percent: float = 80.0

    @classmethod
    def from_environment(cls) -> "ContextPreservationAgentConfig":
        """Create configuration from environment variables"""
        return cls(
            max_conversation_history=int(os.getenv(
                "CONTEXT_MAX_CONVERSATIONS",
                str(DEFAULT_MAX_CONVERSATION_HISTORY)
            )),
            max_knowledge_entries=int(os.getenv(
                "CONTEXT_MAX_KNOWLEDGE",
                str(DEFAULT_MAX_KNOWLEDGE_ENTRIES)
            )),
            export_directory=os.getenv(
                "CONTEXT_EXPORT_DIR",
                "./context_exports"
            ),
            memory_limit_mb=int(os.getenv("CONTEXT_MEMORY_LIMIT_MB", "1024")),
            cpu_limit_percent=float(os.getenv("CONTEXT_CPU_LIMIT_PERCENT", "80.0"))
        )


# =========================================================================
# Context Preservation Agent
# =========================================================================

class ContextPreservationAgent(BaseAgent, ProtocolMixin):
    """
    Meta-agent for maintaining comprehensive context and session continuity

    **Capabilities:**
    - Project identity management
    - Technical architecture tracking
    - Business context preservation
    - Relationship management
    - Active thread tracking
    - Knowledge base maintenance
    - Conversation history
    - AI onboarding brief generation
    - Agent handoff brief generation

    **Architectural Standards:**
    - Inherits from BaseAgent + ProtocolMixin
    - Environment-based configuration
    - Resource monitoring
    - Full lifecycle management
    - Protocol support (A2A, A2P, ACP, ANP, MCP)
    """

    def __init__(
        self,
        agent_id: str,
        config: ContextPreservationAgentConfig,
        project_name: str = "Project"
    ):
        """Initialize Context Preservation Agent"""
        # Initialize both parent classes
        super(BaseAgent, self).__init__()
        self.agent_id = agent_id
        self.agent_type = AGENT_TYPE
        self.version = VERSION
        ProtocolMixin.__init__(self)

        # Store typed config
        self.typed_config = config
        self.project_name = project_name

        # Context database
        self.context_db = {
            'project_identity': {},
            'technical_architecture': {},
            'business_context': {},
            'relationships': {},
            'active_threads': {},
            'knowledge_base': {},
            'conversation_history': []
        }

        # State tracking
        self.state = {
            "initialized": False,
            "last_update": None,
            "total_updates": 0
        }

        # Metrics
        self.metrics = {
            "context_updates": 0,
            "briefs_generated": 0,
            "knowledge_entries": 0,
            "conversations_logged": 0,
            "exports_completed": 0
        }

        # Resource tracking
        self.process = psutil.Process()

    # =====================================================================
    # Abstract Method Implementations (Required by BaseAgent)
    # =====================================================================

    async def _configure_data_sources(self):
        """Configure data sources - context managed internally"""
        pass

    async def _initialize_specific(self):
        """Agent-specific initialization - handled in initialize()"""
        pass

    async def _fetch_required_data(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch required data - context agent uses internal storage"""
        return {}

    async def _execute_logic(
        self,
        input_data: Dict[str, Any],
        fetched_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Core execution logic - delegates to execute() method"""
        return await self.execute(input_data)

    # =====================================================================
    # Lifecycle Methods
    # =====================================================================

    async def initialize(self) -> Dict[str, Any]:
        """Initialize the agent"""
        try:
            start_time = time.time()

            # Create export directory if it doesn't exist
            os.makedirs(self.typed_config.export_directory, exist_ok=True)

            # Protocol support is provided by ProtocolMixin base class
            # No manual protocol enabling needed

            self.state["initialized"] = True
            self.state["last_update"] = datetime.now().isoformat()

            init_time_ms = (time.time() - start_time) * 1000

            return {
                "success": True,
                "agent_id": self.agent_id,
                "agent_type": self.agent_type,
                "version": self.version,
                "project_name": self.project_name,
                "initialization_time_ms": round(init_time_ms, 2)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Initialization failed: {str(e)}"
            }

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute context preservation operations

        Supported operations:
        - update_project_identity: Update core project identity
        - update_technical_architecture: Update technical architecture context
        - update_business_context: Update business context
        - update_relationships: Track key relationships
        - add_active_thread: Add an active work thread
        - add_knowledge: Add to knowledge base
        - log_conversation: Log important conversation
        - generate_ai_brief: Generate AI onboarding brief
        - generate_agent_brief: Generate agent handoff brief
        - export_context: Export full context database
        - get_context_summary: Get summary of current context
        """
        if not self.state["initialized"]:
            return {
                "success": False,
                "error": "Agent not initialized. Call initialize() first."
            }

        start_time = time.time()

        try:
            operation = input_data.get("operation") or input_data.get("type")

            if not operation:
                return {
                    "success": False,
                    "error": "No operation specified"
                }

            # Route to appropriate handler
            if operation == "update_project_identity":
                result = await self._update_project_identity(input_data)
            elif operation == "update_technical_architecture":
                result = await self._update_technical_architecture(input_data)
            elif operation == "update_business_context":
                result = await self._update_business_context(input_data)
            elif operation == "update_relationships":
                result = await self._update_relationships(input_data)
            elif operation == "add_active_thread":
                result = await self._add_active_thread(input_data)
            elif operation == "add_knowledge":
                result = await self._add_knowledge(input_data)
            elif operation == "log_conversation":
                result = await self._log_conversation(input_data)
            elif operation == "generate_ai_brief":
                result = await self._generate_ai_brief()
            elif operation == "generate_agent_brief":
                result = await self._generate_agent_brief(input_data)
            elif operation == "export_context":
                result = await self._export_context(input_data)
            elif operation == "get_context_summary":
                result = await self._get_context_summary()
            else:
                result = {
                    "success": False,
                    "error": f"Unknown operation: {operation}"
                }

            # Track execution time
            execution_time_ms = (time.time() - start_time) * 1000
            result["execution_time_ms"] = round(execution_time_ms, 2)

            # Update state
            if result.get("success"):
                self.state["total_updates"] += 1
                self.state["last_update"] = datetime.now().isoformat()

            return result

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            return {
                "success": False,
                "error": str(e),
                "execution_time_ms": round(execution_time_ms, 2)
            }

    async def shutdown(self) -> Dict[str, Any]:
        """Shutdown the agent and clean up resources"""
        try:
            # Optionally export context before shutdown
            self.state["initialized"] = False

            return {
                "status": "shutdown",
                "agent_id": self.agent_id,
                "final_metrics": {
                    "context_updates": self.metrics["context_updates"],
                    "briefs_generated": self.metrics["briefs_generated"],
                    "knowledge_entries": self.metrics["knowledge_entries"],
                    "conversations_logged": self.metrics["conversations_logged"],
                    "exports_completed": self.metrics["exports_completed"]
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "reason": f"Shutdown failed: {str(e)}"
            }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        try:
            # Get resource usage
            memory_mb = self.process.memory_info().rss / 1024 / 1024
            cpu_percent = self.process.cpu_percent(interval=0.1)

            # Check resource limits
            memory_ok = memory_mb < self.typed_config.memory_limit_mb
            cpu_ok = cpu_percent < self.typed_config.cpu_limit_percent

            # Check storage limits
            conversation_ok = len(self.context_db['conversation_history']) < self.typed_config.max_conversation_history
            knowledge_ok = len(self.context_db['knowledge_base']) < self.typed_config.max_knowledge_entries

            status = "ready" if (memory_ok and cpu_ok and conversation_ok and knowledge_ok) else "degraded"

            return {
                "status": status,
                "agent_id": self.agent_id,
                "initialized": self.state["initialized"],
                "resources": {
                    "memory_mb": round(memory_mb, 2),
                    "memory_limit_mb": self.typed_config.memory_limit_mb,
                    "memory_percent": round((memory_mb / self.typed_config.memory_limit_mb) * 100, 1),
                    "cpu_percent": round(cpu_percent, 1),
                    "cpu_limit_percent": self.typed_config.cpu_limit_percent
                },
                "storage": {
                    "conversations": len(self.context_db['conversation_history']),
                    "max_conversations": self.typed_config.max_conversation_history,
                    "knowledge_entries": len(self.context_db['knowledge_base']),
                    "max_knowledge_entries": self.typed_config.max_knowledge_entries,
                    "active_threads": len(self.context_db['active_threads'])
                },
                "state": self.state.copy(),
                "metrics": self.metrics.copy()
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    # =====================================================================
    # Context Update Methods
    # =====================================================================

    async def _update_project_identity(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update core project identity"""
        identity = data.get("identity", {})

        self.context_db['project_identity'] = {
            'name': identity.get('name', self.project_name),
            'mission': identity.get('mission', ''),
            'vision': identity.get('vision', ''),
            'values': identity.get('values', []),
            'unique_approach': identity.get('unique_approach', ''),
            'target_audience': identity.get('target_audience', []),
            'updated_at': datetime.now().isoformat()
        }

        self.metrics["context_updates"] += 1

        return {
            "success": True,
            "message": "Project identity updated"
        }

    async def _update_technical_architecture(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update technical architecture context"""
        architecture = data.get("architecture", {})

        self.context_db['technical_architecture'] = {
            'core_components': architecture.get('core_components', {}),
            'tech_stack': architecture.get('tech_stack', {}),
            'agent_types': architecture.get('agent_types', []),
            'data_flow': architecture.get('data_flow', ''),
            'deployment': architecture.get('deployment', {}),
            'repos': architecture.get('repos', []),
            'documentation_links': architecture.get('documentation_links', []),
            'updated_at': datetime.now().isoformat()
        }

        self.metrics["context_updates"] += 1

        return {
            "success": True,
            "message": "Technical architecture updated"
        }

    async def _update_business_context(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update business context"""
        business = data.get("business", {})

        self.context_db['business_context'] = {
            'current_stage': business.get('current_stage', ''),
            'revenue_model': business.get('revenue_model', ''),
            'go_to_market': business.get('go_to_market', ''),
            'key_metrics': business.get('key_metrics', {}),
            'active_opportunities': business.get('active_opportunities', []),
            'constraints': business.get('constraints', []),
            'updated_at': datetime.now().isoformat()
        }

        self.metrics["context_updates"] += 1

        return {
            "success": True,
            "message": "Business context updated"
        }

    async def _update_relationships(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Track key relationships"""
        relationships = data.get("relationships", [])

        self.context_db['relationships'] = {
            'partners': [],
            'advisors': [],
            'customers': [],
            'community': [],
            'updated_at': datetime.now().isoformat()
        }

        for rel in relationships:
            category = rel.get('type', 'community')
            if category not in self.context_db['relationships']:
                self.context_db['relationships'][category] = []

            self.context_db['relationships'][category].append({
                'name': rel.get('name', ''),
                'role': rel.get('role', ''),
                'context': rel.get('context', ''),
                'status': rel.get('status', 'active'),
                'value': rel.get('value', ''),
                'next_action': rel.get('next_action', '')
            })

        self.metrics["context_updates"] += 1

        return {
            "success": True,
            "message": f"{len(relationships)} relationships updated"
        }

    async def _add_active_thread(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Add an active work thread"""
        thread_id = data.get("thread_id")
        thread = data.get("thread", {})

        if not thread_id:
            return {"success": False, "error": "thread_id required"}

        self.context_db['active_threads'][thread_id] = {
            'title': thread.get('title', ''),
            'description': thread.get('description', ''),
            'status': thread.get('status', 'in_progress'),
            'priority': thread.get('priority', 'medium'),
            'context': thread.get('context', {}),
            'next_steps': thread.get('next_steps', []),
            'blockers': thread.get('blockers', []),
            'related_threads': thread.get('related_threads', []),
            'started_at': thread.get('started_at', datetime.now().isoformat()),
            'updated_at': datetime.now().isoformat()
        }

        self.metrics["context_updates"] += 1

        return {
            "success": True,
            "message": f"Thread '{thread_id}' added"
        }

    async def _add_knowledge(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Add to knowledge base"""
        knowledge_id = data.get("knowledge_id")
        knowledge = data.get("knowledge", {})

        if not knowledge_id:
            return {"success": False, "error": "knowledge_id required"}

        # Check storage limit
        if len(self.context_db['knowledge_base']) >= self.typed_config.max_knowledge_entries:
            return {
                "success": False,
                "error": f"Knowledge base limit reached ({self.typed_config.max_knowledge_entries})"
            }

        self.context_db['knowledge_base'][knowledge_id] = {
            'topic': knowledge.get('topic', ''),
            'summary': knowledge.get('summary', ''),
            'details': knowledge.get('details', {}),
            'related_topics': knowledge.get('related_topics', []),
            'source': knowledge.get('source', ''),
            'confidence': knowledge.get('confidence', 'high'),
            'added_at': datetime.now().isoformat()
        }

        self.metrics["knowledge_entries"] += 1

        return {
            "success": True,
            "message": f"Knowledge '{knowledge_id}' added"
        }

    async def _log_conversation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Log important conversation"""
        conversation = data.get("conversation", {})

        # Check storage limit
        if len(self.context_db['conversation_history']) >= self.typed_config.max_conversation_history:
            # Remove oldest entry
            self.context_db['conversation_history'].pop(0)

        self.context_db['conversation_history'].append({
            'timestamp': datetime.now().isoformat(),
            'participants': conversation.get('participants', []),
            'topic': conversation.get('topic', ''),
            'key_points': conversation.get('key_points', []),
            'decisions': conversation.get('decisions', []),
            'action_items': conversation.get('action_items', [])
        })

        self.metrics["conversations_logged"] += 1

        return {
            "success": True,
            "message": "Conversation logged"
        }

    # =====================================================================
    # Brief Generation Methods
    # =====================================================================

    async def _generate_ai_brief(self) -> Dict[str, Any]:
        """Generate AI onboarding brief"""
        brief = {
            'generated_at': datetime.now().isoformat(),
            'for_ai_assistant': True,

            'quick_context': {
                'project': self.context_db['project_identity'].get('name', self.project_name),
                'mission': self.context_db['project_identity'].get('mission', ''),
                'current_phase': self.context_db['business_context'].get('current_stage', '')
            },

            'what_we_are_building': {
                'product': self.context_db['project_identity'].get('unique_approach', ''),
                'architecture': self.context_db['technical_architecture'].get('core_components', {}),
                'tech_stack': self.context_db['technical_architecture'].get('tech_stack', {})
            },

            'business_situation': {
                'stage': self.context_db['business_context'].get('current_stage', ''),
                'revenue': self.context_db['business_context'].get('revenue_model', ''),
                'active_opportunities': self.context_db['business_context'].get('active_opportunities', []),
                'key_metrics': self.context_db['business_context'].get('key_metrics', {})
            },

            'what_is_happening_now': {
                'active_threads': [
                    {
                        'id': tid,
                        'title': t['title'],
                        'status': t['status'],
                        'priority': t['priority'],
                        'next_steps': t['next_steps']
                    }
                    for tid, t in self.context_db['active_threads'].items()
                ],
                'total_knowledge_entries': len(self.context_db['knowledge_base']),
                'recent_conversations': len(self.context_db['conversation_history'])
            }
        }

        self.metrics["briefs_generated"] += 1

        return {
            "success": True,
            "brief": brief
        }

    async def _generate_agent_brief(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate agent handoff brief"""
        agent_type = data.get("agent_type", "unknown")

        brief = {
            'agent_type': agent_type,
            'generated_at': datetime.now().isoformat(),

            'your_role': self._define_agent_role(agent_type),

            'current_context': {
                'project_state': self.context_db['business_context'].get('current_stage', ''),
                'active_work': [
                    t for t in self.context_db['active_threads'].values()
                ],
                'knowledge_entries': len(self.context_db['knowledge_base'])
            },

            'collaboration_context': {
                'other_active_threads': len(self.context_db['active_threads']),
                'total_agents': len(self.context_db['technical_architecture'].get('agent_types', []))
            }
        }

        self.metrics["briefs_generated"] += 1

        return {
            "success": True,
            "brief": brief
        }

    # =====================================================================
    # Export Methods
    # =====================================================================

    async def _export_context(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Export full context database"""
        filename = data.get("filename", f"context_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        filepath = os.path.join(self.typed_config.export_directory, filename)

        with open(filepath, 'w') as f:
            json.dump(self.context_db, f, indent=2, default=str)

        self.metrics["exports_completed"] += 1

        return {
            "success": True,
            "filepath": filepath,
            "message": "Context exported successfully"
        }

    async def _get_context_summary(self) -> Dict[str, Any]:
        """Get summary of current context"""
        return {
            "success": True,
            "summary": {
                "project_name": self.context_db['project_identity'].get('name', self.project_name),
                "active_threads": len(self.context_db['active_threads']),
                "knowledge_entries": len(self.context_db['knowledge_base']),
                "conversations_logged": len(self.context_db['conversation_history']),
                "relationships_tracked": sum(
                    len(v) for k, v in self.context_db.get('relationships', {}).items()
                    if isinstance(v, list)
                ),
                "last_update": self.state.get("last_update")
            }
        }

    # =====================================================================
    # Helper Methods
    # =====================================================================

    def _define_agent_role(self, agent_type: str) -> str:
        """Define specific agent role"""
        roles = {
            'development': 'Write and maintain code for the autonomous system',
            'testing': 'Test code quality and find issues',
            'design': 'Design system architecture and features',
            'qa': 'Review and validate implementations',
            'storytelling': 'Create marketing content and narratives',
            'documentation': 'Maintain comprehensive documentation',
            'orchestration': 'Coordinate multi-agent workflows',
            'monitoring': 'Track agent activity and performance'
        }
        return roles.get(agent_type.lower(), 'Support the overall mission')


# =========================================================================
# Factory Function
# =========================================================================

async def create_context_preservation_agent(
    agent_id: str = "context_preserve_001",
    config: Optional[ContextPreservationAgentConfig] = None,
    project_name: str = "Project"
) -> ContextPreservationAgent:
    """
    Factory function to create and initialize a Context Preservation Agent

    Args:
        agent_id: Unique identifier for the agent
        config: Configuration object (uses environment if not provided)
        project_name: Name of the project being tracked

    Returns:
        Initialized ContextPreservationAgent instance
    """
    if config is None:
        config = ContextPreservationAgentConfig.from_environment()

    agent = ContextPreservationAgent(
        agent_id=agent_id,
        config=config,
        project_name=project_name
    )

    await agent.initialize()

    return agent


# =========================================================================
# Main (for testing)
# =========================================================================

if __name__ == "__main__":
    async def demo():
        """Demonstrate Context Preservation Agent capabilities"""
        print("\n" + "=" * 80)
        print("CONTEXT PRESERVATION AGENT v1.0 - DEMO")
        print("=" * 80)

        # Create agent
        print("\n[1] Creating agent...")
        agent = await create_context_preservation_agent(
            agent_id="context_demo",
            project_name="Autonomous Ecosystem"
        )
        print(f"    Agent created: {agent.agent_id}")
        print(f"    Project: {agent.project_name}")

        # Update project identity
        print("\n[2] Updating project identity...")
        result = await agent.execute({
            "operation": "update_project_identity",
            "identity": {
                "name": "Autonomous Ecosystem",
                "mission": "Build self-improving agent ecosystems",
                "vision": "Every business runs on autonomous agents",
                "values": ["Transparency", "Speed", "Impact"],
                "unique_approach": "Agents that improve themselves"
            }
        })
        print(f"    Result: {result.get('message')}")

        # Add knowledge
        print("\n[3] Adding knowledge entry...")
        result = await agent.execute({
            "operation": "add_knowledge",
            "knowledge_id": "agent_retrofitting",
            "knowledge": {
                "topic": "Agent Architectural Standards",
                "summary": "8 principles and 5 protocols for compliant agents",
                "confidence": "high",
                "source": "Implementation experience"
            }
        })
        print(f"    Result: {result.get('message')}")

        # Add active thread
        print("\n[4] Adding active thread...")
        result = await agent.execute({
            "operation": "add_active_thread",
            "thread_id": "agent_retrofitting",
            "thread": {
                "title": "Retrofit 70+ agents to standards",
                "status": "in_progress",
                "priority": "high",
                "next_steps": ["Complete 10 agents", "Create integration tests"]
            }
        })
        print(f"    Result: {result.get('message')}")

        # Log conversation
        print("\n[5] Logging conversation...")
        result = await agent.execute({
            "operation": "log_conversation",
            "conversation": {
                "participants": ["User", "Claude"],
                "topic": "Agent retrofitting progress",
                "key_points": ["8 agents completed", "100% test pass rate"],
                "decisions": ["Continue retrofitting more agents"]
            }
        })
        print(f"    Result: {result.get('message')}")

        # Generate AI brief
        print("\n[6] Generating AI onboarding brief...")
        result = await agent.execute({"operation": "generate_ai_brief"})
        if result.get('success'):
            brief = result['brief']
            print(f"    Project: {brief['quick_context']['project']}")
            print(f"    Mission: {brief['quick_context']['mission']}")
            print(f"    Active threads: {len(brief['what_is_happening_now']['active_threads'])}")

        # Get context summary
        print("\n[7] Getting context summary...")
        result = await agent.execute({"operation": "get_context_summary"})
        if result.get('success'):
            summary = result['summary']
            print(f"    Project: {summary['project_name']}")
            print(f"    Active threads: {summary['active_threads']}")
            print(f"    Knowledge entries: {summary['knowledge_entries']}")
            print(f"    Conversations: {summary['conversations_logged']}")

        # Health check
        print("\n[8] Health check:")
        health = await agent.health_check()
        print(f"    Status: {health['status']}")
        print(f"    Memory: {health['resources']['memory_mb']:.2f} MB")
        print(f"    Storage: {json.dumps(health['storage'], indent=6)}")

        # Shutdown
        print("\n[9] Shutting down...")
        shutdown_result = await agent.shutdown()
        print(f"    Status: {shutdown_result['status']}")
        print(f"    Final metrics: {json.dumps(shutdown_result['final_metrics'], indent=6)}")

        print("\n" + "=" * 80)
        print("DEMO COMPLETE")
        print("=" * 80 + "\n")

    asyncio.run(demo())
