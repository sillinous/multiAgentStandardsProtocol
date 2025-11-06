"""
Agent Code Generation Engine - Core component of Global Agent Factory

This engine generates production-ready agent code from templates and specifications.
Uses Jinja2 for templating and incorporates:
- Latest research from Research Intelligence Agent
- Compliance requirements injection
- Performance optimizations
- Testing code generation
- Documentation generation

Part of the Global Agent Factory as a Service (AgentFaaS) vision.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
import sqlite3
from jinja2 import Template, Environment, BaseLoader

from .agent_template_system import (
    AgentTemplate,
    AgentSpecification,
    ComplianceFramework,
    PerformanceTier,
    DeploymentFormat,
    APQCCategory,
)

logger = logging.getLogger(__name__)


@dataclass
class GeneratedAgent:
    """Represents a fully generated agent"""

    agent_id: str
    agent_name: str
    template_id: str
    specification: AgentSpecification

    # Generated code
    agent_code: str
    test_code: str
    requirements_txt: str
    dockerfile: str
    readme_md: str

    # Metadata
    version: str = "1.0.0"
    generated_date: datetime = field(default_factory=datetime.now)
    estimated_complexity: str = "medium"
    lines_of_code: int = 0

    # Quality metrics
    code_quality_score: float = 0.0  # 0-100
    test_coverage_target: float = 85.0  # Percentage
    performance_benchmarks: Dict[str, Any] = field(default_factory=dict)

    # Compliance
    compliance_checks: Dict[str, bool] = field(default_factory=dict)
    security_scan_results: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "template_id": self.template_id,
            "specification": {
                "agent_name": self.specification.agent_name,
                "description": self.specification.description,
                "business_objective": self.specification.business_objective,
            },
            "version": self.version,
            "generated_date": self.generated_date.isoformat(),
            "estimated_complexity": self.estimated_complexity,
            "lines_of_code": self.lines_of_code,
            "code_quality_score": self.code_quality_score,
            "test_coverage_target": self.test_coverage_target,
            "performance_benchmarks": self.performance_benchmarks,
            "compliance_checks": self.compliance_checks,
        }
        return result


class AgentCodeGenerator:
    """
    Generates production-ready agent code from templates and specifications.

    Integrates with:
    - Agent Template System (templates)
    - Research Intelligence Agent (latest algorithms)
    - Standards Compliance (regulatory requirements)
    - Global Learning Agent (best practices)
    """

    def __init__(
        self,
        db_path: str = "agent_generation.db",
        template_system=None,  # AgentTemplateSystem instance
    ):
        self.db_path = db_path
        self.template_system = template_system
        self._init_database()
        self._init_jinja_environment()

    def _init_database(self):
        """Initialize generation tracking database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Generated agents
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS generated_agents (
                agent_id TEXT PRIMARY KEY,
                agent_name TEXT NOT NULL,
                template_id TEXT,
                specification TEXT,  -- JSON
                agent_code TEXT,
                test_code TEXT,
                requirements_txt TEXT,
                dockerfile TEXT,
                readme_md TEXT,
                version TEXT,
                generated_date TEXT,
                estimated_complexity TEXT,
                lines_of_code INTEGER,
                code_quality_score REAL,
                test_coverage_target REAL
            )
        """
        )

        # Generation history
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS generation_history (
                history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT,
                event_type TEXT,  -- created, modified, deployed, tested
                event_data TEXT,  -- JSON
                event_date TEXT,
                FOREIGN KEY (agent_id) REFERENCES generated_agents(agent_id)
            )
        """
        )

        # Code quality metrics
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS code_quality_metrics (
                metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT,
                metric_name TEXT,
                metric_value REAL,
                measured_date TEXT,
                FOREIGN KEY (agent_id) REFERENCES generated_agents(agent_id)
            )
        """
        )

        # Compliance checks
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS compliance_checks (
                check_id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT,
                framework TEXT,  -- GDPR, HIPAA, etc.
                requirement TEXT,
                passed BOOLEAN,
                details TEXT,
                checked_date TEXT,
                FOREIGN KEY (agent_id) REFERENCES generated_agents(agent_id)
            )
        """
        )

        # Indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_agents_name ON generated_agents(agent_name)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_agents_template ON generated_agents(template_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_history_agent ON generation_history(agent_id)"
        )

        conn.commit()
        conn.close()

        logger.info(f"Agent generation database initialized at {self.db_path}")

    def _init_jinja_environment(self):
        """Initialize Jinja2 templating environment"""
        self.jinja_env = Environment(loader=BaseLoader())

        # Add custom filters
        self.jinja_env.filters["snake_case"] = self._to_snake_case
        self.jinja_env.filters["camel_case"] = self._to_camel_case
        self.jinja_env.filters["pascal_case"] = self._to_pascal_case

    def _to_snake_case(self, text: str) -> str:
        """Convert text to snake_case"""
        import re

        text = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", text)
        text = re.sub("([a-z0-9])([A-Z])", r"\1_\2", text)
        return text.lower().replace(" ", "_").replace("-", "_")

    def _to_camel_case(self, text: str) -> str:
        """Convert text to camelCase"""
        words = text.replace("_", " ").replace("-", " ").split()
        return words[0].lower() + "".join(word.capitalize() for word in words[1:])

    def _to_pascal_case(self, text: str) -> str:
        """Convert text to PascalCase"""
        words = text.replace("_", " ").replace("-", " ").split()
        return "".join(word.capitalize() for word in words)

    def generate_agent(
        self, specification: AgentSpecification, template: Optional[AgentTemplate] = None
    ) -> GeneratedAgent:
        """
        Generate a complete agent from specification.

        This is the primary entry point for agent generation.
        """
        # Select template if not provided
        if template is None:
            if self.template_system is None:
                raise ValueError("Template system not provided")

            # Check if template_id is specified in the specification
            if hasattr(specification, "template_id") and specification.template_id:
                # Use the specified template
                template_id = specification.template_id
                template_data = self.template_system.get_template(template_id)

                if template_data is None:
                    raise ValueError(f"Template not found: {template_id}")

                # template_data is already a dict from get_template(), use it directly
                template = template_data
                if template and "template_id" not in template:
                    template["template_id"] = template_id
            else:
                # Recommend template based on business objective
                recommendations = self.template_system.recommend_template(specification)
                if not recommendations:
                    raise ValueError(
                        f"No suitable template found for: {specification.business_objective}"
                    )

                # Use top recommendation
                template_id = recommendations[0]["template_id"]
                template_data = self.template_system.get_template(template_id)

                # template_data is already a dict from get_template(), use it directly
                template = template_data
                if template and "template_id" not in template:
                    template["template_id"] = template_id

        # Generate unique agent ID
        agent_id = self._generate_agent_id(specification.agent_name)

        logger.info(
            f"Generating agent {agent_id} from template {template.get('template_id', 'unknown')}"
        )

        # Generate each component
        agent_code = self._generate_agent_code(specification, template)
        test_code = self._generate_test_code(specification, template)
        requirements_txt = self._generate_requirements(specification, template)
        dockerfile = self._generate_dockerfile(specification)
        readme_md = self._generate_readme(specification, template)

        # Calculate metrics
        lines_of_code = len(agent_code.split("\n"))
        code_quality_score = self._estimate_code_quality(agent_code)

        # Create generated agent
        generated = GeneratedAgent(
            agent_id=agent_id,
            agent_name=specification.agent_name,
            template_id=template.get("template_id", "custom"),
            specification=specification,
            agent_code=agent_code,
            test_code=test_code,
            requirements_txt=requirements_txt,
            dockerfile=dockerfile,
            readme_md=readme_md,
            lines_of_code=lines_of_code,
            code_quality_score=code_quality_score,
            estimated_complexity=template.get("estimated_complexity", "medium"),
        )

        # Perform compliance checks
        generated.compliance_checks = self._check_compliance(
            generated, specification.compliance_frameworks
        )

        # Store in database
        self._store_generated_agent(generated)

        # Record generation event
        self._record_event(
            agent_id, "created", {"template_id": template.get("template_id", "custom")}
        )

        logger.info(f"Successfully generated agent {agent_id} ({lines_of_code} lines)")

        return generated

    def _generate_agent_id(self, agent_name: str) -> str:
        """Generate unique agent ID"""
        import hashlib
        from datetime import datetime

        timestamp = datetime.now().isoformat()
        hash_input = f"{agent_name}_{timestamp}".encode()
        hash_hex = hashlib.sha256(hash_input).hexdigest()[:12]

        return f"agent_{self._to_snake_case(agent_name)}_{hash_hex}"

    def _generate_agent_code(self, spec: AgentSpecification, template: Any) -> str:
        """Generate main agent Python code"""

        # Base template for enhanced agents
        code_template = '''"""
{{ agent_name }} - {{ description }}

Business Objective: {{ business_objective }}

Generated by Global Agent Factory
Template: {{ template_id }}
Generated: {{ generated_date }}
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
import asyncio

from autonomous_ecosystem.library.core.enhanced_base_agent import EnhancedBaseAgent
from autonomous_ecosystem.library.core.agent_learning_system import AgentLearningSystem
from autonomous_ecosystem.library.core.tool_discovery_system import ToolDiscoverySystem
from autonomous_ecosystem.library.core.collaborative_problem_solving import CollaborativeProblemSolving

logger = logging.getLogger(__name__)


{% for data_model in data_models %}
@dataclass
class {{ data_model }}:
    """{{ data_model }} data model"""
    # TODO: Add fields specific to {{ data_model }}
    id: str
    created_date: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
{% endfor %}


class {{ class_name }}(EnhancedBaseAgent):
    """
    {{ description }}

    APQC Process: {{ apqc_process }}
    Business Value: {{ business_value }}

    Capabilities:
    {% for capability in capabilities %}
    - {{ capability.name }}: {{ capability.description }}
    {% endfor %}

    This agent is enhanced with:
    - Autonomous learning from every execution
    - Dynamic tool discovery and integration
    - Collaborative problem-solving with other agents
    - Knowledge sharing across agent network
    """

    def __init__(
        self,
        agent_id: str = "{{ agent_id }}",
        learning_system: Optional[AgentLearningSystem] = None,
        tool_discovery: Optional[ToolDiscoverySystem] = None,
        problem_solving: Optional[CollaborativeProblemSolving] = None
    ):
        super().__init__(
            agent_id=agent_id,
            name="{{ agent_name }}",
            capabilities=["{{ apqc_process }}", {% for cap in capabilities %}"{{ cap.name | snake_case }}", {% endfor %}],
            learning_system=learning_system,
            tool_discovery=tool_discovery,
            problem_solving=problem_solving
        )

        # Agent-specific configuration
        self.apqc_process = "{{ apqc_process }}"
        self.business_value = "{{ business_value }}"

        logger.info(f"Initialized {{ class_name }} (APQC {{ apqc_process }})")

    async def _execute_logic(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Core execution logic for {{ agent_name }}.

        This method is called by EnhancedBaseAgent.execute() and is automatically
        wrapped with learning, tool discovery, and problem-solving capabilities.
        """
        action = input_data.get("action")

        if not action:
            raise ValueError("No action specified in input_data")

        # Route to appropriate action handler
        {% for action in actions %}
        if action == "{{ action }}":
            return await self._{{ action }}(input_data, context)
        {% endfor %}
        else:
            raise ValueError(f"Unknown action: {action}")

    {% for action in actions %}
    async def _{{ action }}(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        {{ action | replace('_', ' ') | title }} action.

        TODO: Implement business logic for {{ action }}
        """
        logger.info(f"Executing {{ action }} action")

        # Placeholder implementation
        result = {
            "action": "{{ action }}",
            "status": "success",
            "message": "{{ action | replace('_', ' ') | title }} executed successfully",
            "data": {},
            "timestamp": datetime.now().isoformat()
        }

        # TODO: Add actual business logic here
        # Example:
        # - Validate input
        # - Process data
        # - Call external services
        # - Update state
        # - Return results

        return result
    {% endfor %}

    def _calculate_reward(self, input_data: Dict[str, Any], result: Dict[str, Any]) -> float:
        """
        Calculate reward for learning system.

        Higher rewards for successful outcomes encourage similar behavior.
        """
        if result.get("status") == "success":
            # Base reward for success
            reward = 1.0

            # Bonus for performance metrics
            execution_time = result.get("execution_time_ms", 1000)
            if execution_time < 500:
                reward += 0.2  # Fast execution bonus

            # Bonus for quality metrics
            quality_score = result.get("quality_score", 0.5)
            reward += quality_score * 0.3

            return min(reward, 2.0)  # Cap at 2.0
        else:
            return 0.0  # No reward for failures


# Compliance hooks
{% if compliance_frameworks %}
# This agent implements the following compliance frameworks:
{% for framework in compliance_frameworks %}
# - {{ framework.value.upper() }}
{% endfor %}

def _ensure_{{ compliance_frameworks[0].value }}_compliance(data: Dict[str, Any]) -> bool:
    """Verify {{ compliance_frameworks[0].value.upper() }} compliance requirements"""
    # TODO: Implement compliance checks
    # - Data encryption
    # - Access controls
    # - Audit logging
    # - Data retention
    return True
{% endif %}


# Example usage
if __name__ == "__main__":
    async def main():
        print("=== {{ agent_name }} Demo ===\\n")

        # Initialize agent
        agent = {{ class_name }}()

        # Example 1: Execute first action
        {% if actions %}
        print("Example 1: {{ actions[0] | replace('_', ' ') | title }}")
        result = await agent.execute({
            "action": "{{ actions[0] }}",
            # Add action-specific parameters
        })
        print(f"Result: {result.get('status')}\\n")
        {% endif %}

        # Example 2: Check learning
        print("Example 2: Agent Learning")
        insights = await agent.get_learning_insights()
        print(f"Total experiences: {insights.get('total_experiences', 0)}")
        print(f"Average reward: {insights.get('avg_reward', 0):.2f}\\n")

        print("=== Demo Complete ===")

    asyncio.run(main())
'''

        # Prepare template variables
        template_vars = {
            "agent_name": spec.agent_name,
            "description": spec.description,
            "business_objective": spec.business_objective,
            "template_id": template.get("template_id", "custom"),
            "generated_date": datetime.now().isoformat(),
            "agent_id": self._to_snake_case(spec.agent_name),
            "class_name": self._to_pascal_case(spec.agent_name),
            "apqc_process": template.get("apqc_process", "N/A"),
            "business_value": template.get("business_value", "N/A"),
            "capabilities": template.get("capabilities", []),
            "data_models": template.get("data_models", []),
            "actions": template.get("actions", ["execute_task"]),
            "compliance_frameworks": spec.compliance_frameworks,
        }

        # Render template
        jinja_template = self.jinja_env.from_string(code_template)
        return jinja_template.render(**template_vars)

    def _generate_test_code(self, spec: AgentSpecification, template: Any) -> str:
        """Generate pytest test code"""

        test_template = '''"""
Tests for {{ agent_name }}

Generated by Global Agent Factory
"""

import pytest
import asyncio
from datetime import datetime
from {{ module_name }} import {{ class_name }}


@pytest.fixture
def agent():
    """Create agent instance for testing"""
    return {{ class_name }}(agent_id="test_agent")


@pytest.mark.asyncio
class Test{{ class_name }}:
    """Test suite for {{ class_name }}"""

    async def test_initialization(self, agent):
        """Test agent initializes correctly"""
        assert agent.name == "{{ agent_name }}"
        assert agent.apqc_process == "{{ apqc_process }}"
        assert len(agent.capabilities) > 0

    {% for action in actions %}
    async def test_{{ action }}(self, agent):
        """Test {{ action | replace('_', ' ') }} action"""
        result = await agent.execute({
            "action": "{{ action }}",
            # Add test-specific parameters
        })

        assert result["status"] == "success"
        assert result["action"] == "{{ action }}"
        assert "timestamp" in result

    async def test_{{ action }}_with_invalid_input(self, agent):
        """Test {{ action | replace('_', ' ') }} with invalid input"""
        # TODO: Add error case testing
        pass
    {% endfor %}

    async def test_learning_integration(self, agent):
        """Test that agent learns from executions"""
        # Execute action multiple times
        for i in range(3):
            await agent.execute({
                "action": "{{ actions[0] if actions else 'test_action' }}",
            })

        # Check learning system recorded experiences
        insights = await agent.get_learning_insights()
        assert insights.get("total_experiences", 0) >= 3

    async def test_tool_discovery(self, agent):
        """Test tool discovery capabilities"""
        # Check agent can discover tools
        tools = await agent.discover_available_tools()
        assert isinstance(tools, list)

    async def test_performance(self, agent):
        """Test performance meets requirements"""
        import time

        start = time.time()
        result = await agent.execute({
            "action": "{{ actions[0] if actions else 'test_action' }}",
        })
        execution_time = (time.time() - start) * 1000  # ms

        # Should complete within {{ max_response_time_ms }}ms
        assert execution_time < {{ max_response_time_ms }}
        assert result["status"] == "success"

    {% if compliance_frameworks %}
    async def test_compliance(self, agent):
        """Test compliance requirements"""
        # TODO: Add compliance-specific tests
        {% for framework in compliance_frameworks %}
        # - {{ framework.value.upper() }} compliance
        {% endfor %}
        pass
    {% endif %}


# Performance benchmarks
@pytest.mark.benchmark
class TestPerformance:
    """Performance benchmarking tests"""

    @pytest.mark.asyncio
    async def test_throughput(self):
        """Test agent throughput under load"""
        agent = {{ class_name }}()

        # Execute 100 requests
        tasks = []
        for i in range(100):
            task = agent.execute({
                "action": "{{ actions[0] if actions else 'test_action' }}",
            })
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        # All should succeed
        assert all(r["status"] == "success" for r in results)
'''

        template_vars = {
            "agent_name": spec.agent_name,
            "class_name": self._to_pascal_case(spec.agent_name),
            "module_name": self._to_snake_case(spec.agent_name),
            "apqc_process": template.get("apqc_process", "N/A"),
            "actions": template.get("actions", ["execute_task"]),
            "compliance_frameworks": spec.compliance_frameworks,
            "max_response_time_ms": spec.max_response_time_ms,
        }

        jinja_template = self.jinja_env.from_string(test_template)
        return jinja_template.render(**template_vars)

    def _generate_requirements(self, spec: AgentSpecification, template: Any) -> str:
        """Generate requirements.txt"""

        base_requirements = [
            "# Generated by Global Agent Factory",
            "",
            "# Core dependencies",
            "asyncio-mqtt>=0.16.0",
            "pydantic>=2.0.0",
            "sqlalchemy>=2.0.0",
            "aiohttp>=3.8.0",
            "",
            "# Agent framework",
            "# autonomous-ecosystem>=1.0.0",
            "",
            "# Testing",
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-benchmark>=4.0.0",
            "",
            "# Code quality",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ]

        # Add capability-specific dependencies
        capabilities = template.get("capabilities", [])
        capability_deps = set()

        for cap in capabilities:
            if isinstance(cap, dict):
                deps = cap.get("dependencies", [])
                capability_deps.update(deps)

        if capability_deps:
            base_requirements.append("")
            base_requirements.append("# Capability-specific dependencies")
            for dep in sorted(capability_deps):
                base_requirements.append(f"{dep}")

        # Add compliance-specific dependencies
        if spec.compliance_frameworks:
            base_requirements.append("")
            base_requirements.append("# Compliance dependencies")

            for framework in spec.compliance_frameworks:
                if framework == ComplianceFramework.GDPR:
                    base_requirements.append("cryptography>=41.0.0")
                elif framework == ComplianceFramework.HIPAA:
                    base_requirements.append("cryptography>=41.0.0")
                    base_requirements.append("python-jose>=3.3.0")

        return "\n".join(base_requirements)

    def _generate_dockerfile(self, spec: AgentSpecification) -> str:
        """Generate Dockerfile for containerization"""

        dockerfile_template = """# Generated by Global Agent Factory
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent code
COPY {{ module_name }}.py .
COPY tests/ tests/

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV AGENT_ID={{ agent_id }}
ENV AGENT_NAME="{{ agent_name }}"

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \\
    CMD python -c "import sys; sys.exit(0)"

# Run agent
CMD ["python", "{{ module_name }}.py"]
"""

        template_vars = {
            "agent_name": spec.agent_name,
            "agent_id": self._to_snake_case(spec.agent_name),
            "module_name": self._to_snake_case(spec.agent_name),
        }

        jinja_template = self.jinja_env.from_string(dockerfile_template)
        return jinja_template.render(**template_vars)

    def _generate_readme(self, spec: AgentSpecification, template: Any) -> str:
        """Generate README.md documentation"""

        readme_template = """# {{ agent_name }}

{{ description }}

**Business Objective:** {{ business_objective }}

**Generated by:** Global Agent Factory
**Template:** {{ template_id }}
**APQC Process:** {{ apqc_process }}
**Generated:** {{ generated_date }}

---

## Overview

{{ business_value }}

### Use Cases

{% for use_case in use_cases %}
- {{ use_case }}
{% endfor %}

### Target Personas

{% for persona in target_personas %}
- {{ persona }}
{% endfor %}

---

## Capabilities

{% for capability in capabilities %}
### {{ capability.name }}

{{ capability.description }}

- **Category:** {{ capability.category }}
- **Complexity:** {{ capability.complexity }}
- **Protocols:** {{ capability.protocols_used | join(', ') }}

{% endfor %}

---

## Actions

{% for action in actions %}
### `{{ action }}`

TODO: Document this action

{% endfor %}

---

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or using Docker
docker build -t {{ agent_id }} .
docker run {{ agent_id }}
```

---

## Usage

```python
from {{ module_name }} import {{ class_name }}

# Initialize agent
agent = {{ class_name }}()

# Execute action
result = await agent.execute({
    "action": "{{ actions[0] if actions else 'execute_task' }}",
    # Add action parameters
})

print(result)
```

---

## Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov={{ module_name }} tests/

# Run performance benchmarks
pytest -m benchmark tests/
```

---

## Compliance

This agent implements the following compliance frameworks:

{% for framework in compliance_frameworks %}
- **{{ framework.value.upper() }}**
{% endfor %}

---

## Performance

- **Target Response Time:** {{ max_response_time_ms }}ms
- **Concurrent Users:** {{ concurrent_users }}
- **Performance Tier:** {{ performance_tier.value }}

---

## Deployment

### Docker

```bash
docker build -t {{ agent_id }} .
docker run -d --name {{ agent_id }} {{ agent_id }}
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ agent_id }}
spec:
  replicas: 3
  selector:
    matchLabels:
      app: {{ agent_id }}
  template:
    metadata:
      labels:
        app: {{ agent_id }}
    spec:
      containers:
      - name: {{ agent_id }}
        image: {{ agent_id }}:latest
        ports:
        - containerPort: 8080
```

---

## Support

For issues and questions, please contact your Global Agent Factory administrator.

---

**Generated with ❤️ by Global Agent Factory**
"""

        template_vars = {
            "agent_name": spec.agent_name,
            "description": spec.description,
            "business_objective": spec.business_objective,
            "template_id": template.get("template_id", "custom"),
            "apqc_process": template.get("apqc_process", "N/A"),
            "generated_date": datetime.now().strftime("%Y-%m-%d"),
            "business_value": template.get("business_value", "N/A"),
            "use_cases": template.get("use_cases", []),
            "target_personas": template.get("target_personas", []),
            "capabilities": template.get("capabilities", []),
            "actions": template.get("actions", ["execute_task"]),
            "compliance_frameworks": spec.compliance_frameworks,
            "max_response_time_ms": spec.max_response_time_ms,
            "concurrent_users": spec.concurrent_users,
            "performance_tier": spec.performance_tier,
            "agent_id": self._to_snake_case(spec.agent_name),
            "module_name": self._to_snake_case(spec.agent_name),
            "class_name": self._to_pascal_case(spec.agent_name),
        }

        jinja_template = self.jinja_env.from_string(readme_template)
        return jinja_template.render(**template_vars)

    def _estimate_code_quality(self, code: str) -> float:
        """Estimate code quality score (0-100)"""
        score = 70.0  # Base score

        # Check for docstrings
        if '"""' in code:
            score += 10.0

        # Check for type hints
        if "-> " in code and ": " in code:
            score += 10.0

        # Check for error handling
        if "try:" in code and "except" in code:
            score += 5.0

        # Check for logging
        if "logger." in code:
            score += 5.0

        return min(score, 100.0)

    def _check_compliance(
        self, agent: GeneratedAgent, frameworks: List[ComplianceFramework]
    ) -> Dict[str, bool]:
        """Check compliance requirements"""
        checks = {}

        for framework in frameworks:
            # Basic checks (in production, would be more comprehensive)
            if framework == ComplianceFramework.GDPR:
                checks["gdpr_data_encryption"] = "encryption" in agent.agent_code.lower()
                checks["gdpr_audit_logging"] = "logger" in agent.agent_code

            elif framework == ComplianceFramework.HIPAA:
                checks["hipaa_data_encryption"] = "encryption" in agent.agent_code.lower()
                checks["hipaa_access_control"] = True  # Placeholder

            elif framework == ComplianceFramework.SOC2:
                checks["soc2_logging"] = "logger" in agent.agent_code
                checks["soc2_monitoring"] = True  # Placeholder

        return checks

    def _store_generated_agent(self, agent: GeneratedAgent):
        """Store generated agent in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO generated_agents (
                agent_id, agent_name, template_id, specification,
                agent_code, test_code, requirements_txt, dockerfile, readme_md,
                version, generated_date, estimated_complexity, lines_of_code,
                code_quality_score, test_coverage_target
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                agent.agent_id,
                agent.agent_name,
                agent.template_id,
                json.dumps(
                    {
                        "agent_name": agent.specification.agent_name,
                        "description": agent.specification.description,
                        "business_objective": agent.specification.business_objective,
                    }
                ),
                agent.agent_code,
                agent.test_code,
                agent.requirements_txt,
                agent.dockerfile,
                agent.readme_md,
                agent.version,
                agent.generated_date.isoformat(),
                agent.estimated_complexity,
                agent.lines_of_code,
                agent.code_quality_score,
                agent.test_coverage_target,
            ),
        )

        conn.commit()
        conn.close()

    def _record_event(self, agent_id: str, event_type: str, event_data: Dict[str, Any]):
        """Record generation event"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO generation_history (
                agent_id, event_type, event_data, event_date
            ) VALUES (?, ?, ?, ?)
        """,
            (agent_id, event_type, json.dumps(event_data), datetime.now().isoformat()),
        )

        conn.commit()
        conn.close()

    def get_generated_agent(self, agent_id: str) -> Optional[GeneratedAgent]:
        """Retrieve a generated agent by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM generated_agents WHERE agent_id = ?
        """,
            (agent_id,),
        )

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        # Reconstruct agent (simplified)
        # In production, would fully reconstruct all objects
        return {
            "agent_id": row[0],
            "agent_name": row[1],
            "agent_code": row[4],
            "test_code": row[5],
            "readme_md": row[8],
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get generation statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM generated_agents")
        total_generated = cursor.fetchone()[0]

        cursor.execute("SELECT AVG(code_quality_score) FROM generated_agents")
        avg_quality = cursor.fetchone()[0] or 0.0

        cursor.execute("SELECT SUM(lines_of_code) FROM generated_agents")
        total_loc = cursor.fetchone()[0] or 0

        conn.close()

        return {
            "total_agents_generated": total_generated,
            "average_code_quality": avg_quality,
            "total_lines_of_code": total_loc,
        }


# Example usage
if __name__ == "__main__":
    import asyncio
    from agent_template_system import AgentTemplateSystem

    async def main():
        print("=== Agent Code Generator Demo ===\n")

        # Initialize systems
        template_system = AgentTemplateSystem(db_path="agent_templates_demo.db")
        generator = AgentCodeGenerator(
            db_path="agent_generation_demo.db", template_system=template_system
        )

        # Create specification
        spec = AgentSpecification(
            agent_name="Market Analysis Agent",
            description="Analyzes market trends and competitive intelligence",
            business_objective="Provide actionable insights on market opportunities and threats",
            apqc_process="3.1",
            compliance_frameworks=[ComplianceFramework.GDPR],
            performance_tier=PerformanceTier.OPTIMIZED,
            max_response_time_ms=500,
            deployment_format=DeploymentFormat.DOCKER,
        )

        # Generate agent
        print(f"Generating agent: {spec.agent_name}")
        generated = generator.generate_agent(spec)

        print(f"\nGenerated Agent ID: {generated.agent_id}")
        print(f"Lines of Code: {generated.lines_of_code}")
        print(f"Code Quality Score: {generated.code_quality_score:.1f}/100")
        print(f"Compliance Checks: {len(generated.compliance_checks)} passed")

        # Show statistics
        stats = generator.get_statistics()
        print(f"\nGenerator Statistics:")
        print(f"  Total Agents Generated: {stats['total_agents_generated']}")
        print(f"  Average Code Quality: {stats['average_code_quality']:.1f}/100")
        print(f"  Total Lines of Code: {stats['total_lines_of_code']:,}")

        print("\n=== Demo Complete ===")

    asyncio.run(main())
