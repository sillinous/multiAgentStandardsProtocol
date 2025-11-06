"""
Agent Factory - Meta-Agent for Autonomous Agent Generation

This agent generates other agents based on APQC specifications.
The ultimate force multiplier for agent ecosystem expansion.
"""

import os
import sys
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# CRITICAL: Import from protocol-compliant BaseAgent (THE SINGLE SOURCE OF TRUTH)
from core.base_agent_v1 import BaseAgent, AgentCapability, MessageType
from services.code_generator import ClaudeCodeGenerator
from services.file_operations import SafeFileOperations


class AgentFactory(BaseAgent):
    """
    Meta-Agent that generates other agents automatically

    Capabilities:
    - Read APQC agent specifications from registry
    - Generate complete agent code using Claude API
    - Create library versions with proper versioning
    - Support batch generation (build multiple agents in parallel)
    - Integrate generated agents with orchestrator

    This agent is the key to exponential growth of your agent ecosystem.
    """

    def __init__(
        self,
        agent_id: str = "agent_factory_001",
        workspace_path: str = "./autonomous-ecosystem/workspace",
        library_path: str = "./autonomous-ecosystem/library",
        apqc_registry_path: str = "./autonomous-ecosystem/library/apqc_agents/registry.json",
        claude_api_key: Optional[str] = None,
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type="agent_factory",
            capabilities=[AgentCapability.DEVELOPMENT],
            workspace_path=workspace_path,
        )

        self.library_path = library_path
        self.apqc_registry_path = apqc_registry_path
        self.code_generator = ClaudeCodeGenerator(claude_api_key)
        self.file_ops = SafeFileOperations(".", os.path.join(workspace_path, "backups"))

        self.agents_generated = []
        self.generation_queue = []

        print(f"[{self.agent_id}] 🏭 Agent Factory initialized")
        print(f"  Library Path: {library_path}")
        print(f"  APQC Registry: {apqc_registry_path}")
        print(
            f"  Code Generation: {'Claude API ✅' if not self.code_generator.mock_mode else 'Mock Mode ⚠️'}"
        )

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent generation task"""
        task_type = task.get("type")

        if task_type == "generate_agent":
            agent_spec = task.get("agent_spec")
            return await self.generate_agent(agent_spec)

        elif task_type == "generate_batch":
            agent_ids = task.get("agent_ids", [])
            return await self.generate_batch(agent_ids)

        elif task_type == "generate_priority_agents":
            count = task.get("count", 10)
            return await self.generate_priority_agents(count)

        elif task_type == "generate_by_category":
            category_id = task.get("category_id")
            return await self.generate_category_agents(category_id)

        else:
            return {"error": f"Unknown task type: {task_type}"}

    async def analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze agent specifications and estimate generation effort"""
        agent_spec = input_data.get("agent_spec")

        return {
            "agent_id": agent_spec.get("agent_id"),
            "category": agent_spec.get("metadata", {}).get("category_name"),
            "complexity": self._estimate_complexity(agent_spec),
            "estimated_time_seconds": self._estimate_generation_time(agent_spec),
            "dependencies": agent_spec.get("integration", {}).get("required_services", []),
        }

    async def generate_agent(self, agent_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a single agent from APQC specification

        Args:
            agent_spec: APQC agent specification

        Returns:
            Generation result with file paths and status
        """
        agent_id = agent_spec.get("agent_id")
        print(f"\n[{self.agent_id}] 🔨 Generating agent: {agent_id}")

        metadata = agent_spec.get("metadata", {})
        print(f"  Category: {metadata.get('category_name')}")
        print(f"  Process: {metadata.get('process_name')}")
        print(f"  Type: {metadata.get('agent_type')}")

        result = {
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat(),
            "status": "in_progress",
            "files_created": [],
            "errors": [],
        }

        try:
            # Step 1: Generate agent code using Claude
            print(f"[{self.agent_id}]   📝 Generating agent code...")
            agent_code = await self._generate_agent_code(agent_spec)

            # Step 2: Create agent file in library
            print(f"[{self.agent_id}]   💾 Writing agent file...")
            agent_file_path = await self._create_agent_file(agent_spec, agent_code)
            result["files_created"].append(agent_file_path)

            # Step 3: Generate tests
            print(f"[{self.agent_id}]   🧪 Generating tests...")
            test_code = await self._generate_agent_tests(agent_spec, agent_code)
            test_file_path = await self._create_test_file(agent_spec, test_code)
            result["files_created"].append(test_file_path)

            # Step 4: Update library metadata
            print(f"[{self.agent_id}]   📋 Updating library registry...")
            await self._update_library_registry(agent_spec)

            result["status"] = "completed"
            print(f"[{self.agent_id}]   ✅ Agent generated successfully!")

        except Exception as e:
            result["status"] = "failed"
            result["errors"].append(str(e))
            print(f"[{self.agent_id}]   ❌ Generation failed: {e}")

        # Save generation report
        self.save_artifact(
            "agent_generations",
            result,
            f"{agent_id}_generation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        )

        # Send to orchestrator
        self.send_message(MessageType.IMPLEMENTATION_REPORT, "orchestrator", result)

        self.agents_generated.append(result)

        return result

    async def generate_batch(self, agent_ids: List[str]) -> Dict[str, Any]:
        """
        Generate multiple agents in parallel

        Args:
            agent_ids: List of APQC agent IDs to generate

        Returns:
            Batch generation results
        """
        print(f"\n[{self.agent_id}] 🏗️  BATCH GENERATION: {len(agent_ids)} agents")
        print(f"  Agent IDs: {', '.join(agent_ids[:5])}{'...' if len(agent_ids) > 5 else ''}")

        batch_result = {
            "timestamp": datetime.now().isoformat(),
            "total_agents": len(agent_ids),
            "started": 0,
            "completed": 0,
            "failed": 0,
            "results": [],
        }

        # Load APQC registry
        registry = await self._load_apqc_registry()

        # Create generation tasks
        tasks = []
        for agent_id in agent_ids:
            agent_spec = self._find_agent_spec(registry, agent_id)
            if agent_spec:
                tasks.append(self.generate_agent(agent_spec))
                batch_result["started"] += 1
            else:
                print(f"[{self.agent_id}]   ⚠️  Agent not found: {agent_id}")
                batch_result["results"].append(
                    {
                        "agent_id": agent_id,
                        "status": "not_found",
                        "error": "Agent specification not found in registry",
                    }
                )

        # Execute all generations in parallel
        print(f"[{self.agent_id}]   🚀 Launching {len(tasks)} parallel generations...")
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for result in results:
            if isinstance(result, Exception):
                batch_result["failed"] += 1
                batch_result["results"].append({"status": "error", "error": str(result)})
            else:
                if result.get("status") == "completed":
                    batch_result["completed"] += 1
                else:
                    batch_result["failed"] += 1
                batch_result["results"].append(result)

        print(f"\n[{self.agent_id}] ✅ BATCH COMPLETE:")
        print(f"  ✅ Completed: {batch_result['completed']}")
        print(f"  ❌ Failed: {batch_result['failed']}")
        print(
            f"  📊 Success Rate: {(batch_result['completed']/batch_result['total_agents']*100):.1f}%"
        )

        return batch_result

    async def generate_priority_agents(self, count: int = 10) -> Dict[str, Any]:
        """
        Generate the top priority agents for the platform

        Args:
            count: Number of priority agents to generate

        Returns:
            Generation results
        """
        print(f"\n[{self.agent_id}] 🎯 Generating {count} PRIORITY AGENTS")

        priority_agents = [
            # Tier 1: Market Intelligence (Category 3.0)
            "competitive_intelligence_agent",
            "customer_insights_agent",
            "trend_forecasting_agent",
            "product_opportunity_agent",
            # Tier 2: Analytics & Optimization (Category 8.0)
            "roi_calculator_agent",
            "cost_optimization_agent",
            "content_strategy_agent",
            # Tier 3: Enterprise (Category 12.0)
            "process_optimization_agent",
            "knowledge_management_agent",
            "data_quality_agent",
        ]

        # Take only requested count
        agents_to_generate = priority_agents[:count]

        # For now, map to APQC IDs (we'll need to map these properly)
        # Generate from registry instead
        registry = await self._load_apqc_registry()

        # Get first N agents from categories 3.0, 8.0, and 12.0
        target_categories = ["3.0", "8.0", "12.0"]
        agent_specs = []

        for agent in registry.get("agents", []):
            category_id = agent.get("metadata", {}).get("category_id")
            if category_id in target_categories and len(agent_specs) < count:
                agent_specs.append(agent.get("agent_id"))

        return await self.generate_batch(agent_specs)

    async def generate_category_agents(self, category_id: str) -> Dict[str, Any]:
        """
        Generate all agents in a specific APQC category

        Args:
            category_id: APQC category ID (e.g., "3.0", "8.0")

        Returns:
            Generation results
        """
        print(f"\n[{self.agent_id}] 📂 Generating all agents in category: {category_id}")

        registry = await self._load_apqc_registry()

        # Find all agents in category
        agent_ids = []
        for agent in registry.get("agents", []):
            if agent.get("metadata", {}).get("category_id") == category_id:
                agent_ids.append(agent.get("agent_id"))

        print(f"  Found {len(agent_ids)} agents in category {category_id}")

        return await self.generate_batch(agent_ids)

    # Private helper methods

    async def _generate_agent_code(self, agent_spec: Dict[str, Any]) -> str:
        """Generate agent code using Claude API"""

        metadata = agent_spec.get("metadata", {})
        capabilities = agent_spec.get("capabilities", [])

        prompt = f"""Generate a complete Python agent class based on this APQC specification:

Agent ID: {agent_spec.get('agent_id')}
Category: {metadata.get('category_name')}
Process: {metadata.get('process_name')}
Type: {metadata.get('agent_type')}
Domain: {metadata.get('domain')}

Capabilities: {', '.join(capabilities)}

Skills:
{json.dumps(agent_spec.get('skills', {}), indent=2)}

Behavior:
- Autonomous Level: {agent_spec.get('behavior', {}).get('autonomous_level')}
- Collaboration Mode: {agent_spec.get('behavior', {}).get('collaboration_mode')}
- Learning Enabled: {agent_spec.get('behavior', {}).get('learning_enabled')}

Integration Requirements:
- Compatible Agents: {', '.join(agent_spec.get('integration', {}).get('compatible_agents', []))}
- Required Services: {', '.join(agent_spec.get('integration', {}).get('required_services', []))}

Quality Requirements:
- Testing Required: {agent_spec.get('quality', {}).get('testing_required')}
- QA Threshold: {agent_spec.get('quality', {}).get('qa_threshold')}

Generate a complete agent class that:
1. Inherits from BaseAgent
2. Implements execute_task() and analyze() methods
3. Includes all specified capabilities
4. Has proper error handling and logging
5. Follows the existing agent patterns in the codebase
6. Includes comprehensive docstrings

The agent should be production-ready and follow Python best practices.
"""

        context = {
            "project": "autonomous-ecosystem",
            "base_class": "BaseAgent",
            "agent_type": metadata.get("agent_type"),
            "framework": "APQC 7.0.1",
        }

        code = await self.code_generator.generate_code(prompt, context)

        return code

    async def _generate_agent_tests(self, agent_spec: Dict[str, Any], agent_code: str) -> str:
        """Generate comprehensive tests for the agent"""

        prompt = f"""Generate comprehensive pytest tests for this agent:

Agent ID: {agent_spec.get('agent_id')}

Agent Code:
```python
{agent_code[:2000]}  # First 2000 chars
```

Generate tests that cover:
1. Agent initialization
2. Task execution
3. Analysis methods
4. Message passing
5. Error handling
6. Edge cases

Use pytest and async test patterns.
"""

        context = {"framework": "pytest", "type": "agent_tests"}

        return await self.code_generator.generate_code(prompt, context)

    async def _create_agent_file(self, agent_spec: Dict[str, Any], code: str) -> str:
        """Create agent file in library"""

        metadata = agent_spec.get("metadata", {})
        category_id = metadata.get("category_id", "unknown").replace(".", "_")
        agent_type = metadata.get("agent_type", "generic")

        # Determine library path
        category_path = os.path.join(self.library_path, category_id)
        os.makedirs(category_path, exist_ok=True)

        # Create filename
        agent_filename = f"{agent_type}_agent_v1.py"
        file_path = os.path.join(category_path, agent_filename)

        # Add header with PROTOCOL-COMPLIANT imports
        header = f'''"""
{metadata.get('category_name')} - {metadata.get('process_name')}

Agent ID: {agent_spec.get('agent_id')}
Version: {agent_spec.get('version')}
Framework: {agent_spec.get('framework')}
Generated: {datetime.now().isoformat()}

Auto-generated by Agent Factory (Protocol-Compliant)

This agent is FULLY COMPLIANT with all required protocols:
- A2A (Agent-to-Agent): Direct agent communication
- A2P (Agent-to-Pay): Financial transactions between agents
- ACP (Agent Coordination Protocol): Multi-agent coordination
- ANP (Agent Network Protocol): Agent discovery and registration
- MCP (Model Context Protocol): AI model integration
"""

import sys
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# CRITICAL: Import from protocol-compliant BaseAgent (THE SINGLE SOURCE OF TRUTH)
from core.base_agent_v1 import BaseAgent, AgentCapability, MessageType

'''

        full_code = header + code

        # Write file
        self.file_ops.create_file(file_path, full_code)

        print(f"    Created: {file_path}")

        return file_path

    async def _create_test_file(self, agent_spec: Dict[str, Any], test_code: str) -> str:
        """Create test file for agent"""

        agent_id = agent_spec.get("agent_id")
        test_path = os.path.join(self.workspace_path, "tests", "generated_agents")
        os.makedirs(test_path, exist_ok=True)

        test_filename = f"test_{agent_id}.py"
        file_path = os.path.join(test_path, test_filename)

        # Write file
        self.file_ops.create_file(file_path, test_code)

        print(f"    Created: {file_path}")

        return file_path

    async def _update_library_registry(self, agent_spec: Dict[str, Any]) -> None:
        """Update library registry with new agent"""

        registry_path = os.path.join(self.library_path, "generated_agents_registry.json")

        # Load existing registry
        if os.path.exists(registry_path):
            with open(registry_path, "r") as f:
                registry = json.load(f)
        else:
            registry = {"generated_at": datetime.now().isoformat(), "total_agents": 0, "agents": []}

        # Add new agent
        registry["agents"].append(
            {
                "agent_id": agent_spec.get("agent_id"),
                "category": agent_spec.get("metadata", {}).get("category_id"),
                "generated_at": datetime.now().isoformat(),
                "version": agent_spec.get("version"),
            }
        )

        registry["total_agents"] = len(registry["agents"])
        registry["last_updated"] = datetime.now().isoformat()

        # Save registry
        with open(registry_path, "w") as f:
            json.dump(registry, f, indent=2)

    async def _load_apqc_registry(self) -> Dict[str, Any]:
        """Load APQC registry"""

        if not os.path.exists(self.apqc_registry_path):
            raise FileNotFoundError(f"APQC registry not found: {self.apqc_registry_path}")

        with open(self.apqc_registry_path, "r") as f:
            return json.load(f)

    def _find_agent_spec(self, registry: Dict[str, Any], agent_id: str) -> Optional[Dict[str, Any]]:
        """Find agent specification in registry"""

        for agent in registry.get("agents", []):
            if agent.get("agent_id") == agent_id:
                return agent

        return None

    def _estimate_complexity(self, agent_spec: Dict[str, Any]) -> str:
        """Estimate agent complexity"""

        capabilities_count = len(agent_spec.get("capabilities", []))
        required_services = len(agent_spec.get("integration", {}).get("required_services", []))

        if capabilities_count > 8 or required_services > 3:
            return "high"
        elif capabilities_count > 5 or required_services > 1:
            return "medium"
        else:
            return "low"

    def _estimate_generation_time(self, agent_spec: Dict[str, Any]) -> int:
        """Estimate generation time in seconds"""

        complexity = self._estimate_complexity(agent_spec)

        time_map = {"low": 30, "medium": 60, "high": 120}

        return time_map.get(complexity, 60)


# Standalone execution
async def main():
    """Run Agent Factory standalone"""

    print("=" * 60)
    print("🏭 AGENT FACTORY - Autonomous Agent Generation System")
    print("=" * 60)

    factory = AgentFactory()

    # Generate priority agents
    result = await factory.generate_priority_agents(count=10)

    print("\n" + "=" * 60)
    print("📊 GENERATION SUMMARY")
    print("=" * 60)
    print(f"Total: {result['total_agents']}")
    print(f"✅ Completed: {result['completed']}")
    print(f"❌ Failed: {result['failed']}")
    print(f"Success Rate: {(result['completed']/result['total_agents']*100):.1f}%")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
