"""
Context Preservation Agent
Maintains comprehensive context for AI assistants and agents to understand the full backstory
and jump into work without missing a beat
"""

import json
from datetime import datetime
from typing import Dict, List, Optional


class ContextPreservationAgent:
    """
    Builds and maintains rich context documents that allow:
    - New AI assistants to understand the full project instantly
    - Agents to pick up work seamlessly
    - No loss of context across sessions
    """

    def __init__(self, project_name: str = "Graytonomous"):
        self.name = "ContextPreservationAgent"
        self.project_name = project_name
        self.context_db = {
            "project_identity": {},
            "technical_architecture": {},
            "business_context": {},
            "relationships": {},
            "active_threads": {},
            "knowledge_base": {},
            "conversation_history": [],
        }

    def update_project_identity(self, identity: Dict):
        """Update core project identity"""
        self.context_db["project_identity"] = {
            "name": identity.get("name", self.project_name),
            "mission": identity.get("mission", ""),
            "vision": identity.get("vision", ""),
            "values": identity.get("values", []),
            "unique_approach": identity.get("unique_approach", ""),
            "target_audience": identity.get("target_audience", []),
            "updated_at": datetime.now().isoformat(),
        }

    def update_technical_architecture(self, architecture: Dict):
        """Update technical architecture context"""
        self.context_db["technical_architecture"] = {
            "core_components": architecture.get("core_components", {}),
            "tech_stack": architecture.get("tech_stack", {}),
            "agent_types": architecture.get("agent_types", []),
            "data_flow": architecture.get("data_flow", ""),
            "deployment": architecture.get("deployment", {}),
            "repos": architecture.get("repos", []),
            "documentation_links": architecture.get("documentation_links", []),
            "updated_at": datetime.now().isoformat(),
        }

    def update_business_context(self, business: Dict):
        """Update business context"""
        self.context_db["business_context"] = {
            "current_stage": business.get("current_stage", ""),
            "revenue_model": business.get("revenue_model", ""),
            "go_to_market": business.get("go_to_market", ""),
            "key_metrics": business.get("key_metrics", {}),
            "active_opportunities": business.get("active_opportunities", []),
            "constraints": business.get("constraints", []),
            "updated_at": datetime.now().isoformat(),
        }

    def update_relationships(self, relationships: List[Dict]):
        """Track key relationships and partnerships"""
        self.context_db["relationships"] = {
            "partners": [],
            "advisors": [],
            "customers": [],
            "community": [],
            "updated_at": datetime.now().isoformat(),
        }

        for rel in relationships:
            category = rel.get("type", "community")
            self.context_db["relationships"][category].append(
                {
                    "name": rel.get("name", ""),
                    "role": rel.get("role", ""),
                    "context": rel.get("context", ""),
                    "status": rel.get("status", "active"),
                    "value": rel.get("value", ""),
                    "next_action": rel.get("next_action", ""),
                }
            )

    def add_active_thread(self, thread_id: str, thread: Dict):
        """Add an active work thread"""
        self.context_db["active_threads"][thread_id] = {
            "title": thread.get("title", ""),
            "description": thread.get("description", ""),
            "status": thread.get("status", "in_progress"),
            "priority": thread.get("priority", "medium"),
            "context": thread.get("context", {}),
            "next_steps": thread.get("next_steps", []),
            "blockers": thread.get("blockers", []),
            "related_threads": thread.get("related_threads", []),
            "started_at": thread.get("started_at", datetime.now().isoformat()),
            "updated_at": datetime.now().isoformat(),
        }

    def add_knowledge(self, knowledge_id: str, knowledge: Dict):
        """Add to knowledge base"""
        self.context_db["knowledge_base"][knowledge_id] = {
            "topic": knowledge.get("topic", ""),
            "summary": knowledge.get("summary", ""),
            "details": knowledge.get("details", {}),
            "related_topics": knowledge.get("related_topics", []),
            "source": knowledge.get("source", ""),
            "confidence": knowledge.get("confidence", "high"),
            "added_at": datetime.now().isoformat(),
        }

    def log_conversation(self, conversation: Dict):
        """Log important conversation for context"""
        self.context_db["conversation_history"].append(
            {
                "timestamp": datetime.now().isoformat(),
                "participants": conversation.get("participants", []),
                "topic": conversation.get("topic", ""),
                "key_points": conversation.get("key_points", []),
                "decisions": conversation.get("decisions", []),
                "action_items": conversation.get("action_items", []),
            }
        )

    def generate_ai_onboarding_brief(self) -> Dict:
        """
        Generate comprehensive brief for new AI assistant to get up to speed instantly
        """
        return {
            "generated_at": datetime.now().isoformat(),
            "for_ai_assistant": True,
            "quick_context": {
                "project": self.context_db["project_identity"].get("name", self.project_name),
                "mission": self.context_db["project_identity"].get("mission", ""),
                "current_phase": self.context_db["business_context"].get("current_stage", ""),
                "founder_situation": "Unemployed founder, building in public, seeking revenue and partnerships",
            },
            "what_we_are_building": {
                "product": self.context_db["project_identity"].get("unique_approach", ""),
                "architecture": self.context_db["technical_architecture"].get(
                    "core_components", {}
                ),
                "current_capabilities": self._extract_current_capabilities(),
                "tech_stack": self.context_db["technical_architecture"].get("tech_stack", {}),
            },
            "business_situation": {
                "stage": self.context_db["business_context"].get("current_stage", ""),
                "revenue": self.context_db["business_context"].get("revenue_model", ""),
                "active_opportunities": self.context_db["business_context"].get(
                    "active_opportunities", []
                ),
                "key_metrics": self.context_db["business_context"].get("key_metrics", {}),
            },
            "key_relationships": self._summarize_relationships(),
            "what_is_happening_now": {
                "active_threads": [
                    {
                        "id": tid,
                        "title": t["title"],
                        "status": t["status"],
                        "priority": t["priority"],
                        "next_steps": t["next_steps"],
                    }
                    for tid, t in self.context_db["active_threads"].items()
                ],
                "immediate_priorities": self._extract_immediate_priorities(),
                "blockers": self._extract_all_blockers(),
            },
            "how_to_help": {
                "you_can_assist_with": self._generate_assistance_areas(),
                "communication_style": "Direct, concise, action-oriented. Founder values speed over perfection.",
                "decision_making": "Founder makes final calls, but values AI reasoning and recommendations",
                "building_approach": "Build in public, ship fast, iterate, document everything",
            },
            "recent_context": {
                "last_10_conversations": self.context_db["conversation_history"][-10:],
                "recent_knowledge_added": self._get_recent_knowledge(5),
            },
            "knowledge_base_summary": self._summarize_knowledge_base(),
        }

    def generate_agent_handoff_brief(self, for_agent_type: str) -> Dict:
        """
        Generate specific handoff brief for an agent type
        """
        return {
            "agent_type": for_agent_type,
            "generated_at": datetime.now().isoformat(),
            "your_role": self._define_agent_role(for_agent_type),
            "current_context": {
                "project_state": self.context_db["business_context"].get("current_stage", ""),
                "active_work": [
                    t
                    for t in self.context_db["active_threads"].values()
                    if for_agent_type.lower() in t.get("context", {}).get("relevant_agents", [])
                ],
                "relevant_knowledge": self._get_relevant_knowledge(for_agent_type),
            },
            "immediate_tasks": self._get_agent_tasks(for_agent_type),
            "collaboration_context": {
                "other_active_agents": list(self.context_db["active_threads"].keys()),
                "coordination_points": self._get_coordination_needs(for_agent_type),
            },
            "success_criteria": self._define_success_criteria(for_agent_type),
        }

    def _extract_current_capabilities(self) -> List[str]:
        """Extract what the system can currently do"""
        capabilities = []
        tech = self.context_db["technical_architecture"]

        if "agent_types" in tech:
            capabilities.extend([f"Agent: {agent}" for agent in tech["agent_types"]])

        return capabilities

    def _summarize_relationships(self) -> Dict:
        """Summarize key relationships"""
        rels = self.context_db["relationships"]
        return {
            "key_partners": [p["name"] for p in rels.get("partners", [])],
            "potential_customers": [c["name"] for c in rels.get("customers", [])],
            "advisors": [a["name"] for a in rels.get("advisors", [])],
            "community_size": len(rels.get("community", [])),
        }

    def _extract_immediate_priorities(self) -> List[str]:
        """Extract immediate priority actions"""
        priorities = []
        for thread in self.context_db["active_threads"].values():
            if thread.get("priority") == "high" and thread.get("status") == "in_progress":
                priorities.extend(thread.get("next_steps", []))
        return priorities[:5]  # Top 5

    def _extract_all_blockers(self) -> List[Dict]:
        """Extract all current blockers"""
        blockers = []
        for thread_id, thread in self.context_db["active_threads"].items():
            for blocker in thread.get("blockers", []):
                blockers.append({"thread": thread["title"], "blocker": blocker})
        return blockers

    def _generate_assistance_areas(self) -> List[str]:
        """Generate list of how AI can help"""
        return [
            "Writing content (blog posts, tweets, documentation)",
            "Technical architecture and code generation",
            "Business strategy and decision analysis",
            "Partner/customer communication drafting",
            "Research and competitive analysis",
            "Problem-solving and debugging",
            "Planning and task breakdown",
        ]

    def _get_recent_knowledge(self, n: int) -> List[Dict]:
        """Get N most recent knowledge entries"""
        kb = self.context_db["knowledge_base"]
        sorted_knowledge = sorted(kb.items(), key=lambda x: x[1].get("added_at", ""), reverse=True)
        return [
            {"id": kid, "topic": k["topic"], "summary": k["summary"]}
            for kid, k in sorted_knowledge[:n]
        ]

    def _summarize_knowledge_base(self) -> Dict:
        """Summarize knowledge base contents"""
        kb = self.context_db["knowledge_base"]
        return {
            "total_entries": len(kb),
            "topics": list(set([k["topic"] for k in kb.values()])),
            "high_confidence_count": sum(1 for k in kb.values() if k.get("confidence") == "high"),
        }

    def _define_agent_role(self, agent_type: str) -> str:
        """Define specific agent role"""
        roles = {
            "development": "Write and maintain code for the autonomous system",
            "testing": "Test code quality and find issues",
            "design": "Design system architecture and features",
            "qa": "Review and validate implementations",
            "storytelling": "Create marketing content and narratives",
            "documentation": "Maintain comprehensive documentation",
        }
        return roles.get(agent_type.lower(), "Support the overall mission")

    def _get_relevant_knowledge(self, agent_type: str) -> List[Dict]:
        """Get knowledge relevant to specific agent"""
        # Simplified: return recent knowledge
        # Could be more sophisticated with tagging/filtering
        return self._get_recent_knowledge(3)

    def _get_agent_tasks(self, agent_type: str) -> List[str]:
        """Get immediate tasks for agent type"""
        # Extract from active threads
        tasks = []
        for thread in self.context_db["active_threads"].values():
            if agent_type.lower() in thread.get("context", {}).get("relevant_agents", []):
                tasks.extend(thread.get("next_steps", []))
        return tasks[:3]  # Top 3 tasks

    def _get_coordination_needs(self, agent_type: str) -> List[str]:
        """Get coordination requirements"""
        return [
            "Share results with orchestrator",
            "Wait for dependencies from other agents",
            "Update shared state when complete",
        ]

    def _define_success_criteria(self, agent_type: str) -> List[str]:
        """Define success criteria for agent"""
        criteria = {
            "development": ["Code works", "Tests pass", "Follows architecture"],
            "testing": ["All tests run", "Issues documented", "Regression prevented"],
            "storytelling": ["Content published", "Engagement measured", "Brand aligned"],
        }
        return criteria.get(agent_type.lower(), ["Task completed", "Quality maintained"])

    def export_context(self, filepath: str):
        """Export full context database"""
        with open(filepath, "w") as f:
            json.dump(self.context_db, f, indent=2, default=str)

    def export_ai_brief(self, filepath: str):
        """Export AI onboarding brief"""
        brief = self.generate_ai_onboarding_brief()
        with open(filepath, "w") as f:
            json.dump(brief, f, indent=2, default=str)


# Example usage
if __name__ == "__main__":
    agent = ContextPreservationAgent("Graytonomous")

    # Set up comprehensive context
    agent.update_project_identity(
        {
            "name": "Graytonomous",
            "mission": "Build autonomous agent ecosystems that improve themselves",
            "vision": "Every business runs on self-improving AI agents",
            "values": ["Transparency", "Speed", "Real-world impact"],
            "unique_approach": "Autonomous improvement loop: agents test, design, build, and deploy themselves",
            "target_audience": ["Developers", "Startups", "Enterprises", "AI enthusiasts"],
        }
    )

    agent.update_technical_architecture(
        {
            "core_components": {
                "improvement_loop": "Testing → Design → Development → QA → Consensus",
                "agent_factory": "Generates specialized agents from APQC framework",
                "orchestrator": "Coordinates multi-agent workflows",
                "dashboard": "Real-time monitoring and control",
            },
            "tech_stack": {
                "backend": "Python, FastAPI",
                "frontend": "Next.js, React",
                "agents": "Claude API, custom orchestration",
                "data": "PostgreSQL, Redis",
            },
            "agent_types": [
                "Testing Agent",
                "Design Agent",
                "Development Agent",
                "QA Agent",
                "Consensus Agent",
                "Route Discovery Agent",
                "Traffic Prediction Agent",
                "Storytelling Agent",
            ],
        }
    )

    agent.update_business_context(
        {
            "current_stage": "Validation & Partnership Development",
            "revenue_model": "SaaS + Custom deployments + Consulting",
            "go_to_market": "Build in public + Partnerships + Content marketing",
            "key_metrics": {
                "agents_built": 62,
                "validation_complete": True,
                "active_opportunities": 1,
            },
            "active_opportunities": [
                "Gerd partnership - German mobility startup",
                "October investor meeting exposure",
            ],
            "constraints": ["Unemployed founder", "Limited runway", "No team"],
        }
    )

    agent.update_relationships(
        [
            {
                "type": "partners",
                "name": "Gerd Fröhlich",
                "role": "CEO, FUTURES MOBILITY SERVICES",
                "context": "Real-time multi-car hopping challenge",
                "status": "opportunity",
                "value": "European market entry + investor network",
                "next_action": "Send confident response with validation results",
            }
        ]
    )

    agent.add_active_thread(
        "gerd_validation",
        {
            "title": "Validate Multi-Car Routing for Gerd",
            "description": "Prove agents can solve real-time multi-car hopping",
            "status": "complete",
            "priority": "high",
            "context": {
                "challenge": "3-hop routing with traffic and timing constraints",
                "relevant_agents": ["route_discovery", "traffic_prediction", "consensus"],
            },
            "next_steps": ["Document results", "Draft response to Gerd"],
            "blockers": [],
        },
    )

    agent.add_knowledge(
        "multi_car_routing_validation",
        {
            "topic": "Multi-car routing capability",
            "summary": "Autonomous agents successfully solved 3-hop multi-car routing challenge",
            "details": {
                "routes_found": 68,
                "optimal_solution": "3-hop, 72.7 min, $22.92",
                "confidence": "75%",
            },
            "confidence": "high",
            "source": "POC validation run",
        },
    )

    # Generate and print AI onboarding brief
    print("=" * 80)
    print("AI ASSISTANT ONBOARDING BRIEF")
    print("=" * 80)
    brief = agent.generate_ai_onboarding_brief()
    print(json.dumps(brief, indent=2))

    # Export
    agent.export_context("context_database.json")
    agent.export_ai_brief("ai_onboarding_brief.json")
    print("\n\n[Exported context to context_database.json]")
    print("[Exported AI brief to ai_onboarding_brief.json]")
