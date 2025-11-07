"""
Agent Template Generator - Rapid Agent Creation Tool

This tool generates fully scaffolded agents with:
- Base class inheritance
- Standard methods and structure
- Capability declarations
- Version tracking
- Documentation templates
- Test scaffolding
- Registration in capability registry

Usage:
    # Interactive mode
    python create_agent.py --interactive

    # Command line mode
    python create_agent.py \
        --name "RouteOptimizationAgent" \
        --category "logistics" \
        --capabilities "route_optimization,traffic_awareness" \
        --version "1.0.0"
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import argparse

# Templates directory structure
LIBRARY_ROOT = Path(__file__).parent.parent / "library"
AGENTS_DIR = LIBRARY_ROOT / "agents"
TESTS_DIR = Path(__file__).parent.parent / "tests" / "agents"
DOCS_DIR = Path(__file__).parent.parent / "docs" / "agents"


class AgentTemplateGenerator:
    """Generates agent code from templates"""

    CATEGORIES = {
        "internal": "Internal process automation agents",
        "logistics": "Logistics and transportation domain agents",
        "data": "Data processing and algorithm agents",
        "integration": "External API and service integration agents",
        "business": "Business logic and rules agents",
        "ml": "Machine learning and AI agents",
        "monitoring": "System monitoring and observability agents",
        "security": "Security and compliance agents",
    }

    def __init__(self):
        self.ensure_directories()

    def ensure_directories(self):
        """Create directory structure if it doesn't exist"""
        for category in self.CATEGORIES.keys():
            (AGENTS_DIR / category).mkdir(parents=True, exist_ok=True)

        TESTS_DIR.mkdir(parents=True, exist_ok=True)
        DOCS_DIR.mkdir(parents=True, exist_ok=True)

    def generate_agent_code(
        self,
        name: str,
        category: str,
        capabilities: List[str],
        description: str,
        version: str = "1.0.0",
    ) -> str:
        """Generate agent Python code"""

        class_name = name if name.endswith("Agent") else f"{name}Agent"
        agent_id = self.to_snake_case(name)

        capabilities_list = ",\n        ".join([f'"{cap}"' for cap in capabilities])

        template = f'''"""
{class_name} - {description}

Category: {self.CATEGORIES.get(category, "Custom")}
Version: {version}
Created: {datetime.now().strftime("%Y-%m-%d")}

Capabilities:
{chr(10).join([f"- {cap}" for cap in capabilities])}
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from superstandard.agents.base.base_agent import BaseAgent, AgentCapability


@dataclass
class {class_name}Config:
    """Configuration for {class_name}"""
    # Add configuration parameters here
    max_retries: int = 3
    timeout_seconds: int = 30
    # Add more config as needed


class {class_name}(BaseAgent):
    """
    {description}

    This agent provides the following capabilities:
{chr(10).join([f"    - {cap}" for cap in capabilities])}

    Usage:
        agent = {class_name}()
        result = await agent.execute_task({{
            "type": "example_task",
            "data": {{}}
        }})
    """

    def __init__(
        self,
        agent_id: str = "{agent_id}_001",
        config: Optional[{class_name}Config] = None,
        workspace_path: str = "./autonomous-ecosystem/workspace"
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type="{agent_id}",
            capabilities=[
                # Map to AgentCapability enum as appropriate
                AgentCapability.ANALYSIS,
                # AgentCapability.COORDINATION,
                # AgentCapability.MONITORING,
                # etc.
            ],
            workspace_path=workspace_path
        )

        self.config = config or {class_name}Config()

        # Agent-specific initialization
        self.capabilities_list = [
            {capabilities_list}
        ]

        # Metrics
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.total_execution_time_ms = 0

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task with this agent

        Args:
            task: Task dictionary with 'type' and task-specific data

        Returns:
            Result dictionary with success status and data
        """
        task_type = task.get("type")
        start_time = datetime.now()

        try:
            # Route to appropriate handler
            if task_type == "example_task":
                result = await self._handle_example_task(task)
            elif task_type == "another_task":
                result = await self._handle_another_task(task)
            else:
                return {{
                    "success": False,
                    "error": f"Unknown task type: {{task_type}}"
                }}

            # Update metrics
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            self.tasks_completed += 1
            self.total_execution_time_ms += execution_time

            result["execution_time_ms"] = execution_time
            return result

        except Exception as e:
            self.tasks_failed += 1
            return {{
                "success": False,
                "error": str(e),
                "task_type": task_type
            }}

    async def analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze data and provide insights

        Args:
            input_data: Data to analyze

        Returns:
            Analysis results
        """
        analysis_type = input_data.get("analysis_type", "overview")

        if analysis_type == "overview":
            return self._analyze_overview()
        elif analysis_type == "performance":
            return self._analyze_performance()
        elif analysis_type == "capabilities":
            return self._analyze_capabilities()
        else:
            return {{"error": f"Unknown analysis type: {{analysis_type}}"}}

    # =====================================================================
    # Task Handlers (Implement your business logic here)
    # =====================================================================

    async def _handle_example_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle example task"""
        # TODO: Implement task logic

        return {{
            "success": True,
            "message": "Example task completed",
            "data": {{}}
        }}

    async def _handle_another_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle another task type"""
        # TODO: Implement task logic

        return {{
            "success": True,
            "message": "Another task completed",
            "data": {{}}
        }}

    # =====================================================================
    # Analysis Methods
    # =====================================================================

    def _analyze_overview(self) -> Dict[str, Any]:
        """Provide overview analysis"""
        return {{
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "capabilities": self.capabilities_list,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "success_rate": self._calculate_success_rate(),
            "avg_execution_time_ms": self._calculate_avg_execution_time()
        }}

    def _analyze_performance(self) -> Dict[str, Any]:
        """Analyze agent performance"""
        return {{
            "total_tasks": self.tasks_completed + self.tasks_failed,
            "success_rate": self._calculate_success_rate(),
            "avg_execution_time_ms": self._calculate_avg_execution_time(),
            "total_execution_time_ms": self.total_execution_time_ms
        }}

    def _analyze_capabilities(self) -> Dict[str, Any]:
        """Analyze agent capabilities"""
        return {{
            "capabilities": self.capabilities_list,
            "capability_count": len(self.capabilities_list),
            "category": "{category}",
            "version": "{version}"
        }}

    # =====================================================================
    # Helper Methods
    # =====================================================================

    def _calculate_success_rate(self) -> float:
        """Calculate task success rate"""
        total = self.tasks_completed + self.tasks_failed
        return (self.tasks_completed / total * 100) if total > 0 else 0.0

    def _calculate_avg_execution_time(self) -> float:
        """Calculate average execution time"""
        return (
            self.total_execution_time_ms / self.tasks_completed
            if self.tasks_completed > 0
            else 0.0
        )


# Singleton instance
_{agent_id}_instance = None

def get_{agent_id}() -> {class_name}:
    """Get or create {class_name} instance"""
    global _{agent_id}_instance
    if _{agent_id}_instance is None:
        _{agent_id}_instance = {class_name}()
    return _{agent_id}_instance


if __name__ == "__main__":
    # Demo the agent
    import asyncio

    async def demo():
        agent = get_{agent_id}()

        # Execute example task
        result = await agent.execute_task({{
            "type": "example_task",
            "data": {{"example": "value"}}
        }})

        print("\\n[Task Result]")
        print(json.dumps(result, indent=2))

        # Get analysis
        analysis = await agent.analyze({{"analysis_type": "overview"}})

        print("\\n[Agent Analysis]")
        print(json.dumps(analysis, indent=2))

    asyncio.run(demo())
'''

        return template

    def generate_test_code(self, name: str, category: str, capabilities: List[str]) -> str:
        """Generate test code for the agent"""

        class_name = name if name.endswith("Agent") else f"{name}Agent"
        agent_id = self.to_snake_case(name)

        template = f'''"""
Tests for {class_name}

Run with: pytest tests/agents/test_{agent_id}.py
"""

import pytest
import asyncio
from agents.{category}.{agent_id} import {class_name}, get_{agent_id}


class Test{class_name}:
    """Test suite for {class_name}"""

    @pytest.fixture
    def agent(self):
        """Create agent instance for testing"""
        return {class_name}(agent_id="test_{agent_id}")

    @pytest.mark.asyncio
    async def test_execute_example_task(self, agent):
        """Test example task execution"""
        result = await agent.execute_task({{
            "type": "example_task",
            "data": {{"test": "value"}}
        }})

        assert result["success"] == True
        assert "data" in result
        assert "execution_time_ms" in result

    @pytest.mark.asyncio
    async def test_execute_invalid_task(self, agent):
        """Test handling of invalid task type"""
        result = await agent.execute_task({{
            "type": "invalid_task"
        }})

        assert result["success"] == False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_analyze_overview(self, agent):
        """Test overview analysis"""
        result = await agent.analyze({{"analysis_type": "overview"}})

        assert "agent_id" in result
        assert "capabilities" in result
        assert "success_rate" in result

    @pytest.mark.asyncio
    async def test_analyze_performance(self, agent):
        """Test performance analysis"""
        # Execute some tasks first
        await agent.execute_task({{"type": "example_task"}})

        result = await agent.analyze({{"analysis_type": "performance"}})

        assert "total_tasks" in result
        assert "success_rate" in result
        assert result["total_tasks"] >= 1

    @pytest.mark.asyncio
    async def test_singleton_instance(self):
        """Test singleton pattern"""
        agent1 = get_{agent_id}()
        agent2 = get_{agent_id}()

        assert agent1 is agent2

    @pytest.mark.asyncio
    async def test_capabilities(self, agent):
        """Test agent capabilities"""
        result = await agent.analyze({{"analysis_type": "capabilities"}})

        assert "capabilities" in result
        assert len(result["capabilities"]) > 0

        # Check specific capabilities
        expected_capabilities = {[f'"{cap}"' for cap in capabilities]}
        for cap in expected_capabilities:
            assert cap in result["capabilities"]

    @pytest.mark.asyncio
    async def test_error_handling(self, agent):
        """Test error handling"""
        # This should trigger an error gracefully
        result = await agent.execute_task({{
            "type": "example_task",
            "data": None  # Invalid data
        }})

        # Should handle error without crashing
        assert "success" in result

    @pytest.mark.asyncio
    async def test_metrics_tracking(self, agent):
        """Test that metrics are tracked correctly"""
        initial_completed = agent.tasks_completed

        # Execute successful task
        await agent.execute_task({{"type": "example_task"}})

        assert agent.tasks_completed == initial_completed + 1
        assert agent.total_execution_time_ms > 0
'''

        return template

    def generate_documentation(
        self, name: str, category: str, capabilities: List[str], description: str, version: str
    ) -> str:
        """Generate documentation for the agent"""

        class_name = name if name.endswith("Agent") else f"{name}Agent"
        agent_id = self.to_snake_case(name)

        template = f"""# {class_name}

**Version:** {version}
**Category:** {self.CATEGORIES.get(category, "Custom")}
**Created:** {datetime.now().strftime("%Y-%m-%d")}

---

## Overview

{description}

## Capabilities

This agent provides the following capabilities:

{chr(10).join([f"- **{cap}** - {cap.replace('_', ' ').title()}" for cap in capabilities])}

## Installation

```python
from agents.{category}.{agent_id} import {class_name}, get_{agent_id}
```

## Usage

### Basic Usage

```python
import asyncio
from agents.{category}.{agent_id} import get_{agent_id}

async def main():
    agent = get_{agent_id}()

    # Execute a task
    result = await agent.execute_task({{
        "type": "example_task",
        "data": {{
            # Task-specific data
        }}
    }})

    print(result)

asyncio.run(main())
```

### Advanced Usage

```python
from agents.{category}.{agent_id} import {class_name}, {class_name}Config

# Custom configuration
config = {class_name}Config(
    max_retries=5,
    timeout_seconds=60
)

# Create agent with config
agent = {class_name}(
    agent_id="custom_{agent_id}",
    config=config
)

# Execute task
result = await agent.execute_task({{
    "type": "another_task",
    "data": {{}}
}})
```

### Analysis

```python
# Get overview analysis
overview = await agent.analyze({{"analysis_type": "overview"}})
print(f"Success Rate: {{overview['success_rate']}}%")

# Get performance analysis
performance = await agent.analyze({{"analysis_type": "performance"}})
print(f"Avg Execution Time: {{performance['avg_execution_time_ms']}}ms")

# Get capabilities analysis
capabilities = await agent.analyze({{"analysis_type": "capabilities"}})
print(f"Capabilities: {{capabilities['capabilities']}}")
```

## Task Types

### example_task

**Description:** Example task handler

**Input:**
```python
{{
    "type": "example_task",
    "data": {{
        "example": "value"
    }}
}}
```

**Output:**
```python
{{
    "success": True,
    "message": "Example task completed",
    "data": {{}},
    "execution_time_ms": 123.45
}}
```

### another_task

**Description:** Another task handler

**Input:**
```python
{{
    "type": "another_task",
    "data": {{}}
}}
```

**Output:**
```python
{{
    "success": True,
    "message": "Another task completed",
    "data": {{}},
    "execution_time_ms": 98.76
}}
```

## Configuration

### {class_name}Config

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| max_retries | int | 3 | Maximum number of retry attempts |
| timeout_seconds | int | 30 | Task execution timeout |

## Performance Characteristics

- **Average Execution Time:** TBD (measure in production)
- **Success Rate:** TBD (track over time)
- **Throughput:** TBD (tasks per second)
- **Resource Usage:** TBD (CPU, memory)

## Error Handling

The agent handles errors gracefully and returns structured error responses:

```python
{{
    "success": False,
    "error": "Error description",
    "task_type": "example_task"
}}
```

## Dependencies

- Python 3.8+
- asyncio
- dataclasses
- (Add specific dependencies as needed)

## Version History

### {version} ({datetime.now().strftime("%Y-%m-%d")})
- Initial release
- Implemented core capabilities
- Added {len(capabilities)} capabilities

## Contributing

To enhance this agent:

1. Add new capabilities to the capabilities list
2. Implement corresponding task handlers
3. Add tests for new functionality
4. Update documentation
5. Increment version number appropriately

## Examples

### Example 1: Basic Task Execution

```python
agent = get_{agent_id}()
result = await agent.execute_task({{
    "type": "example_task",
    "data": {{"key": "value"}}
}})
```

### Example 2: Batch Processing

```python
agent = get_{agent_id}()
tasks = [
    {{"type": "example_task", "data": {{"id": 1}}}},
    {{"type": "example_task", "data": {{"id": 2}}}},
    {{"type": "example_task", "data": {{"id": 3}}}}
]

results = await asyncio.gather(*[
    agent.execute_task(task) for task in tasks
])
```

### Example 3: Error Handling

```python
try:
    result = await agent.execute_task({{
        "type": "invalid_task"
    }})

    if not result["success"]:
        print(f"Error: {{result['error']}}")
except Exception as e:
    print(f"Unexpected error: {{e}}")
```

## Related Agents

- (List related agents in the library)
- (Suggest swarms that include this agent)

## Support

For issues, questions, or contributions:
- File issues in the project repository
- Contact the maintainers
- Check the agent library documentation

---

**Last Updated:** {datetime.now().strftime("%Y-%m-%d")}
"""

        return template

    def to_snake_case(self, name: str) -> str:
        """Convert name to snake_case"""
        import re

        name = re.sub("Agent$", "", name)  # Remove Agent suffix if present
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    def create_agent(
        self,
        name: str,
        category: str,
        capabilities: List[str],
        description: str,
        version: str = "1.0.0",
    ):
        """Create a new agent with all supporting files"""

        agent_id = self.to_snake_case(name)
        class_name = name if name.endswith("Agent") else f"{name}Agent"

        # Generate code
        agent_code = self.generate_agent_code(name, category, capabilities, description, version)
        test_code = self.generate_test_code(name, category, capabilities)
        docs = self.generate_documentation(name, category, capabilities, description, version)

        # Write files
        agent_file = AGENTS_DIR / category / f"{agent_id}.py"
        test_file = TESTS_DIR / f"test_{agent_id}.py"
        docs_file = DOCS_DIR / f"{agent_id}.md"

        with open(agent_file, "w") as f:
            f.write(agent_code)

        with open(test_file, "w") as f:
            f.write(test_code)

        with open(docs_file, "w") as f:
            f.write(docs)

        # Create __init__.py if it doesn't exist
        init_file = AGENTS_DIR / category / "__init__.py"
        if not init_file.exists():
            with open(init_file, "w") as f:
                f.write(f'"""{self.CATEGORIES.get(category, "Custom")}"""\n')

        print(
            f"""
[SUCCESS] Agent Created Successfully!

Agent: {class_name}
Category: {category}
Version: {version}

Files Created:
- {agent_file}
- {test_file}
- {docs_file}

Next Steps:
1. Implement business logic in: {agent_file}
2. Add tests in: {test_file}
3. Run tests: pytest {test_file}
4. Register agent in capability registry
5. Update library documentation

To use your agent:
    from agents.{category}.{agent_id} import get_{agent_id}
    agent = get_{agent_id}()
    result = await agent.execute_task({{"type": "example_task"}})
"""
        )


def interactive_mode():
    """Run in interactive mode"""
    print(
        """
    ╔═══════════════════════════════════════════════════╗
    ║   Agent Template Generator - Interactive Mode     ║
    ╚═══════════════════════════════════════════════════╝
    """
    )

    generator = AgentTemplateGenerator()

    # Get agent name
    name = input("Agent Name (e.g., 'RouteOptimization' or 'RouteOptimizationAgent'): ").strip()
    if not name:
        print("❌ Agent name is required")
        return

    # Get category
    print("\nAvailable Categories:")
    for i, (key, desc) in enumerate(generator.CATEGORIES.items(), 1):
        print(f"  {i}. {key:15} - {desc}")

    category_idx = input("\nSelect category (1-8): ").strip()
    try:
        category = list(generator.CATEGORIES.keys())[int(category_idx) - 1]
    except (ValueError, IndexError):
        print("❌ Invalid category")
        return

    # Get capabilities
    capabilities_input = input(
        "\nCapabilities (comma-separated, e.g., 'route_optimization,traffic_awareness'): "
    ).strip()
    capabilities = [cap.strip() for cap in capabilities_input.split(",") if cap.strip()]

    if not capabilities:
        print("❌ At least one capability is required")
        return

    # Get description
    description = input("\nAgent Description: ").strip()
    if not description:
        description = f"Agent for {name}"

    # Get version
    version = input("\nVersion (default: 1.0.0): ").strip() or "1.0.0"

    # Create agent
    generator.create_agent(name, category, capabilities, description, version)


def main():
    parser = argparse.ArgumentParser(description="Generate agent templates")
    parser.add_argument("--interactive", "-i", action="store_true", help="Run in interactive mode")
    parser.add_argument("--name", "-n", help="Agent name")
    parser.add_argument("--category", "-c", help="Agent category")
    parser.add_argument("--capabilities", help="Comma-separated capabilities")
    parser.add_argument("--description", "-d", help="Agent description")
    parser.add_argument("--version", "-v", default="1.0.0", help="Agent version")

    args = parser.parse_args()

    if args.interactive:
        interactive_mode()
    elif args.name and args.category and args.capabilities:
        generator = AgentTemplateGenerator()
        capabilities = [cap.strip() for cap in args.capabilities.split(",")]
        description = args.description or f"Agent for {args.name}"

        generator.create_agent(args.name, args.category, capabilities, description, args.version)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
