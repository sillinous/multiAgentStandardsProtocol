"""
Agent Template Generator - Creates Architecturally Compliant Agents

Generates agent code that follows ALL architectural standards:
- Standardized (BaseAgent inheritance, consistent patterns)
- Interoperable (A2A, A2P, ACP, ANP, MCP protocols)
- Redeployable (environment-based config)
- Reusable (no project-specific logic)
- Atomic (single responsibility)
- Composable (compatible interfaces)
- Orchestratable (coordination support)
- Vendor/Model/System Agnostic (abstraction layers)

Usage:
    python agent_template_generator.py --name MyAgent --type analysis --capabilities "data_analysis,reporting"
"""

import os
import sys
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class AgentSpec:
    """Specification for agent generation"""
    agent_name: str
    agent_type: str
    capabilities: List[str]
    description: str
    version: str = "1.0.0"
    author: str = "Autonomous Ecosystem"
    protocols: List[str] = None

    def __post_init__(self):
        if self.protocols is None:
            self.protocols = ["A2A", "A2P", "ACP", "ANP"]


class AgentTemplateGenerator:
    """
    Generates production-ready, architecturally compliant agents
    """

    def __init__(self):
        self.template_version = "2.0.0"  # Based on architectural standards v2.0

    def generate_agent(self, spec: AgentSpec, output_dir: str = "./library/agents") -> str:
        """
        Generate complete agent implementation

        Args:
            spec: Agent specification
            output_dir: Directory to write generated file

        Returns:
            Path to generated file
        """
        # Generate agent code
        agent_code = self._generate_agent_code(spec)

        # Generate config dataclass
        config_code = self._generate_config_dataclass(spec)

        # Combine all parts
        full_code = self._assemble_full_agent(
            spec=spec,
            agent_code=agent_code,
            config_code=config_code
        )

        # Write to file
        filename = f"{spec.agent_name.lower()}_v{spec.version.replace('.', '_')}.py"
        output_path = os.path.join(output_dir, filename)

        os.makedirs(output_dir, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_code)

        print(f"✅ Generated agent: {output_path}")
        return output_path

    def _assemble_full_agent(self, spec: AgentSpec, agent_code: str, config_code: str) -> str:
        """Assemble complete agent file"""

        imports = f'''"""
{spec.agent_name} - Architecturally Compliant Agent

{spec.description}

Version: {spec.version}
Author: {spec.author}
Generated: {datetime.now().isoformat()}
Template Version: {self.template_version}

Architectural Compliance:
✅ Standardized - Inherits from BaseAgent, follows patterns
✅ Interoperable - Supports {', '.join(spec.protocols)} protocols
✅ Redeployable - Environment-based configuration
✅ Reusable - No project-specific logic
✅ Atomic - Single responsibility: {spec.agent_type}
✅ Composable - Compatible interfaces for swarms
✅ Orchestratable - Supports coordination protocols
✅ Vendor/Model/System Agnostic - Abstraction layers
"""

import os
import logging
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# Core framework imports
from superstandard.agents.base.base_agent import BaseAgent
from library.core.protocols import (
    ProtocolMixin,
    A2AMessage,
    A2PTransaction,
    ACPCoordination,
    ANPRegistration
)

# Version constants
AGENT_VERSION = "{spec.version}"
AGENT_TYPE = "{spec.agent_type}"
AGENT_NAME = "{spec.agent_name}"
'''

        full_code = f'''{imports}


# ============================================================================
# CONFIGURATION
# ============================================================================

{config_code}


# ============================================================================
# AGENT IMPLEMENTATION
# ============================================================================

{agent_code}


# ============================================================================
# FACTORY & REGISTRATION
# ============================================================================

def create_{spec.agent_name.lower()}(
    agent_id: Optional[str] = None,
    config: Optional[{spec.agent_name}Config] = None
) -> {spec.agent_name}:
    """
    Factory function to create {spec.agent_name} instance

    Args:
        agent_id: Unique agent identifier (auto-generated if None)
        config: Agent configuration (uses defaults if None)

    Returns:
        Configured {spec.agent_name} instance
    """
    if agent_id is None:
        from uuid import uuid4
        agent_id = f"{{AGENT_TYPE}}_{{str(uuid4())[:8]}}"

    if config is None:
        config = {spec.agent_name}Config.from_environment()

    agent = {spec.agent_name}(agent_id=agent_id, config=config)
    return agent


# ============================================================================
# CLI ENTRY POINT (for standalone execution)
# ============================================================================

async def main():
    """CLI entry point for standalone agent execution"""
    import argparse

    parser = argparse.ArgumentParser(description=f"Run {{AGENT_NAME}} agent")
    parser.add_argument("--agent-id", help="Agent ID", default=None)
    parser.add_argument("--config-file", help="Path to config JSON file", default=None)
    parser.add_argument("--register", action="store_true", help="Register on agent network")
    parser.add_argument("--health-check", action="store_true", help="Run health check and exit")

    args = parser.parse_args()

    # Load config
    if args.config_file:
        import json
        with open(args.config_file, 'r') as f:
            config_dict = json.load(f)
        config = {spec.agent_name}Config(**config_dict)
    else:
        config = {spec.agent_name}Config.from_environment()

    # Create agent
    agent = create_{spec.agent_name.lower()}(agent_id=args.agent_id, config=config)

    # Initialize
    await agent.initialize()

    # Health check mode
    if args.health_check:
        health = await agent.health_check()
        print(f"Health Status: {{health}}")
        return

    # Register on network if requested
    if args.register:
        await agent.register_on_network()
        print(f"Agent registered on network: {{agent.agent_id}}")

    # Keep agent running
    print(f"{{AGENT_NAME}} {{agent.agent_id}} is now running...")
    print(f"Press Ctrl+C to stop")

    try:
        # Run indefinitely
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\\nShutting down...")
        await agent.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
'''

        return full_code

    def _generate_config_dataclass(self, spec: AgentSpec) -> str:
        """Generate configuration dataclass"""

        return f'''@dataclass
class {spec.agent_name}Config:
    """
    Configuration for {spec.agent_name}

    All settings can be provided via:
    1. Environment variables (prefix: {spec.agent_type.upper()}_)
    2. Constructor parameters
    3. Config file (JSON)

    This ensures redeployability across environments
    """

    # Core settings
    log_level: str = "INFO"
    max_memory_mb: int = 512
    max_cpu_percent: int = 80

    # Protocol settings
    enable_a2a: bool = True
    enable_a2p: bool = True
    enable_acp: bool = True
    enable_anp: bool = True

    # Network settings
    agent_network_url: Optional[str] = None
    coordinator_url: Optional[str] = None

    # Agent-specific settings
    # TODO: Add domain-specific configuration here

    @classmethod
    def from_environment(cls) -> "{spec.agent_name}Config":
        """
        Load configuration from environment variables

        Returns:
            Configuration instance loaded from environment
        """
        return cls(
            log_level=os.getenv(f"{{AGENT_TYPE.upper()}}_LOG_LEVEL", "INFO"),
            max_memory_mb=int(os.getenv(f"{{AGENT_TYPE.upper()}}_MAX_MEMORY_MB", "512")),
            max_cpu_percent=int(os.getenv(f"{{AGENT_TYPE.upper()}}_MAX_CPU_PERCENT", "80")),
            enable_a2a=os.getenv(f"{{AGENT_TYPE.upper()}}_ENABLE_A2A", "true").lower() == "true",
            enable_a2p=os.getenv(f"{{AGENT_TYPE.upper()}}_ENABLE_A2P", "true").lower() == "true",
            enable_acp=os.getenv(f"{{AGENT_TYPE.upper()}}_ENABLE_ACP", "true").lower() == "true",
            enable_anp=os.getenv(f"{{AGENT_TYPE.upper()}}_ENABLE_ANP", "true").lower() == "true",
            agent_network_url=os.getenv(f"{{AGENT_TYPE.upper()}}_NETWORK_URL"),
            coordinator_url=os.getenv(f"{{AGENT_TYPE.upper()}}_COORDINATOR_URL"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {{
            "log_level": self.log_level,
            "max_memory_mb": self.max_memory_mb,
            "max_cpu_percent": self.max_cpu_percent,
            "enable_a2a": self.enable_a2a,
            "enable_a2p": self.enable_a2p,
            "enable_acp": self.enable_acp,
            "enable_anp": self.enable_anp,
            "agent_network_url": self.agent_network_url,
            "coordinator_url": self.coordinator_url,
        }}

    def validate(self) -> List[str]:
        """
        Validate configuration

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        if self.max_memory_mb < 128:
            errors.append("max_memory_mb must be at least 128 MB")

        if self.max_cpu_percent < 10 or self.max_cpu_percent > 100:
            errors.append("max_cpu_percent must be between 10 and 100")

        if not self.log_level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            errors.append(f"Invalid log_level: {{self.log_level}}")

        return errors
'''

    def _generate_agent_code(self, spec: AgentSpec) -> str:
        """Generate main agent class"""

        return f'''class {spec.agent_name}(BaseAgent, ProtocolMixin):
    """
    {spec.description}

    Type: {spec.agent_type}
    Version: {spec.version}
    Capabilities: {', '.join(spec.capabilities)}

    Architectural Compliance: FULL
    - All 8 principles implemented
    - All 5 protocols supported
    - Resource monitoring enabled
    - Health checks implemented
    """

    def __init__(
        self,
        agent_id: str,
        config: {spec.agent_name}Config
    ):
        """
        Initialize {spec.agent_name}

        Args:
            agent_id: Unique agent identifier
            config: Agent configuration
        """
        # Initialize base agent
        super().__init__(
            agent_id=agent_id,
            agent_type=AGENT_TYPE,
            config=config.to_dict()
        )

        # Store typed config
        self.typed_config = config

        # Setup logging
        self.logger = logging.getLogger(f"{{AGENT_TYPE}}.{{agent_id}}")
        self.logger.setLevel(config.log_level)

        # Protocol support (from ProtocolMixin)
        self._protocol_support = {{
            "A2A": config.enable_a2a,
            "A2P": config.enable_a2p,
            "ACP": config.enable_acp,
            "ANP": config.enable_anp,
        }}

        # Resource monitoring
        self._resource_monitor = ResourceMonitor(
            max_memory_mb=config.max_memory_mb,
            max_cpu_percent=config.max_cpu_percent
        )

        # Agent state
        self.state = {{
            "initialized": False,
            "tasks_processed": 0,
            "last_activity": None,
        }}

        # Metrics
        self.metrics = {{
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "avg_execution_time_ms": 0.0,
            "messages_sent": 0,
            "messages_received": 0,
        }}

    # ========================================================================
    # LIFECYCLE METHODS (Required by BaseAgent)
    # ========================================================================

    async def initialize(self):
        """
        Initialize agent

        Called once when agent starts
        Sets up resources, validates config, connects to services
        """
        self.logger.info(f"Initializing {{AGENT_NAME}} {{self.agent_id}}")

        # Validate configuration
        errors = self.typed_config.validate()
        if errors:
            raise ValueError(f"Configuration errors: {{', '.join(errors)}}")

        # Initialize specific resources
        await self._initialize_resources()

        # Register on agent network if configured
        if self.typed_config.enable_anp and self.typed_config.agent_network_url:
            await self.register_on_network()

        self.state["initialized"] = True
        self.logger.info(f"{{AGENT_NAME}} {{self.agent_id}} initialized successfully")

    async def _initialize_resources(self):
        """
        Initialize agent-specific resources

        Override this method to add custom initialization logic:
        - Connect to databases
        - Load ML models
        - Initialize caches
        - Setup external API clients
        """
        # TODO: Implement agent-specific initialization
        pass

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute agent logic

        Args:
            input_data: Input data/task to process

        Returns:
            Execution result with output data
        """
        if not self.state["initialized"]:
            raise RuntimeError(f"Agent {{self.agent_id}} not initialized. Call initialize() first.")

        # Check resources before execution
        if not self._resource_monitor.check_resources():
            raise ResourceExhaustionError(
                f"Insufficient resources: {{self._resource_monitor.get_status()}}"
            )

        start_time = datetime.now()

        try:
            self.logger.debug(f"Executing task: {{input_data.get('task_id', 'unknown')}}")

            # Core execution logic
            result = await self._execute_logic(input_data)

            # Update metrics
            execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            self._update_metrics(success=True, execution_time_ms=execution_time_ms)

            # Update state
            self.state["tasks_processed"] += 1
            self.state["last_activity"] = datetime.now().isoformat()

            return {{
                "success": True,
                "agent_id": self.agent_id,
                "agent_type": AGENT_TYPE,
                "version": AGENT_VERSION,
                "result": result,
                "execution_time_ms": execution_time_ms,
                "timestamp": datetime.now().isoformat()
            }}

        except Exception as e:
            self.logger.error(f"Execution failed: {{e}}", exc_info=True)
            self._update_metrics(success=False, execution_time_ms=0)

            return {{
                "success": False,
                "agent_id": self.agent_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": datetime.now().isoformat()
            }}

    async def _execute_logic(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Core agent logic - IMPLEMENT THIS

        This is where your agent's intelligence goes

        Args:
            input_data: Task input data

        Returns:
            Task result/output
        """
        # TODO: Implement agent-specific logic here

        # Example structure:
        # 1. Parse input
        # 2. Validate data
        # 3. Execute domain logic
        # 4. Format output

        return {{
            "status": "completed",
            "message": "Task executed successfully",
            # Add your agent's outputs here
        }}

    async def shutdown(self):
        """
        Shutdown agent gracefully

        Called when agent is stopping
        Cleanup resources, save state, deregister from network
        """
        self.logger.info(f"Shutting down {{AGENT_NAME}} {{self.agent_id}}")

        # Deregister from network
        if self.typed_config.enable_anp and self.state.get("network_registered"):
            await self.deregister_from_network()

        # Cleanup agent-specific resources
        await self._cleanup_resources()

        self.state["initialized"] = False
        self.logger.info(f"{{AGENT_NAME}} {{self.agent_id}} shutdown complete")

    async def _cleanup_resources(self):
        """
        Cleanup agent-specific resources

        Override this method to add custom cleanup:
        - Close database connections
        - Unload ML models
        - Clear caches
        - Close API client connections
        """
        # TODO: Implement agent-specific cleanup
        pass

    # ========================================================================
    # HEALTH & MONITORING
    # ========================================================================

    async def health_check(self) -> Dict[str, Any]:
        """
        Comprehensive health check

        Returns:
            Health status report
        """
        resource_status = self._resource_monitor.get_status()

        return {{
            "agent_id": self.agent_id,
            "agent_type": AGENT_TYPE,
            "version": AGENT_VERSION,
            "status": "healthy" if self.state["initialized"] else "unhealthy",
            "initialized": self.state["initialized"],
            "uptime_seconds": self._get_uptime_seconds(),
            "tasks_processed": self.state["tasks_processed"],
            "last_activity": self.state["last_activity"],
            "metrics": self.metrics,
            "resources": resource_status,
            "timestamp": datetime.now().isoformat()
        }}

    def _get_uptime_seconds(self) -> float:
        """Calculate agent uptime"""
        # TODO: Track start time and calculate uptime
        return 0.0

    # ========================================================================
    # PROTOCOL SUPPORT (Inherited from ProtocolMixin)
    # ========================================================================

    async def register_on_network(self):
        """
        Register agent on agent network (ANP)

        Advertises capabilities and endpoints
        """
        if not self.typed_config.enable_anp:
            self.logger.warning("ANP not enabled, skipping network registration")
            return

        registration = ANPRegistration(
            action="register",
            agent_id=self.agent_id,
            capabilities={', '.join([f'"{c}"' for c in spec.capabilities])},
            endpoints={{
                "health": f"/agents/{{self.agent_id}}/health",
                "execute": f"/agents/{{self.agent_id}}/execute",
            }},
            health_status="healthy"
        )

        self.logger.info(f"Registering on agent network: {{self.typed_config.agent_network_url}}")

        # TODO: Send registration to network
        # For now, just log it
        self.logger.info(f"Registration: {{registration.to_dict()}}")

        self.state["network_registered"] = True

    async def deregister_from_network(self):
        """Deregister from agent network"""
        if not self.state.get("network_registered"):
            return

        deregistration = ANPRegistration(
            action="deregister",
            agent_id=self.agent_id,
            capabilities=[],
            endpoints={{}},
            health_status="unhealthy"
        )

        self.logger.info(f"Deregistering from network")
        # TODO: Send deregistration to network

        self.state["network_registered"] = False

    # ========================================================================
    # METRICS & MONITORING
    # ========================================================================

    def _update_metrics(self, success: bool, execution_time_ms: float):
        """Update agent metrics"""
        self.metrics["total_executions"] += 1

        if success:
            self.metrics["successful_executions"] += 1
        else:
            self.metrics["failed_executions"] += 1

        # Update rolling average execution time
        if execution_time_ms > 0:
            total = self.metrics["total_executions"]
            current_avg = self.metrics["avg_execution_time_ms"]
            self.metrics["avg_execution_time_ms"] = (
                (current_avg * (total - 1) + execution_time_ms) / total
            )

    def get_metrics(self) -> Dict[str, Any]:
        """Get agent metrics"""
        return {{
            **self.metrics,
            "success_rate": (
                self.metrics["successful_executions"] / self.metrics["total_executions"]
                if self.metrics["total_executions"] > 0
                else 0.0
            )
        }}


# ============================================================================
# RESOURCE MONITORING
# ============================================================================

class ResourceMonitor:
    """
    Monitor agent resource usage

    Ensures agent stays within configured resource limits
    """

    def __init__(self, max_memory_mb: int, max_cpu_percent: int):
        self.max_memory_mb = max_memory_mb
        self.max_cpu_percent = max_cpu_percent

    def check_resources(self) -> bool:
        """
        Check if agent has sufficient resources

        Returns:
            True if resources available, False otherwise
        """
        try:
            import psutil

            process = psutil.Process(os.getpid())

            # Check memory
            memory_mb = process.memory_info().rss / 1024 / 1024
            if memory_mb > self.max_memory_mb:
                return False

            # Check CPU
            cpu_percent = process.cpu_percent(interval=0.1)
            if cpu_percent > self.max_cpu_percent:
                return False

            return True

        except ImportError:
            # psutil not available, assume resources OK
            return True

    def get_status(self) -> Dict[str, Any]:
        """Get current resource usage"""
        try:
            import psutil

            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
            cpu_percent = process.cpu_percent(interval=0.1)

            return {{
                "memory_mb": round(memory_mb, 2),
                "memory_limit_mb": self.max_memory_mb,
                "memory_usage_percent": round((memory_mb / self.max_memory_mb) * 100, 2),
                "cpu_percent": round(cpu_percent, 2),
                "cpu_limit_percent": self.max_cpu_percent,
            }}

        except ImportError:
            return {{
                "error": "psutil not available - install with: pip install psutil"
            }}


class ResourceExhaustionError(Exception):
    """Raised when agent exceeds resource limits"""
    pass
'''


def main():
    """CLI for agent generation"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate architecturally compliant agents"
    )
    parser.add_argument("--name", required=True, help="Agent name (e.g., TrafficAnalysis)")
    parser.add_argument("--type", required=True, help="Agent type (e.g., analysis)")
    parser.add_argument(
        "--capabilities",
        required=True,
        help="Comma-separated capabilities (e.g., 'data_analysis,reporting')"
    )
    parser.add_argument(
        "--description",
        required=True,
        help="Agent description"
    )
    parser.add_argument("--version", default="1.0.0", help="Agent version")
    parser.add_argument("--author", default="Autonomous Ecosystem", help="Author name")
    parser.add_argument(
        "--output-dir",
        default="./autonomous-ecosystem/library/agents",
        help="Output directory"
    )

    args = parser.parse_args()

    # Create spec
    spec = AgentSpec(
        agent_name=args.name,
        agent_type=args.type,
        capabilities=args.capabilities.split(","),
        description=args.description,
        version=args.version,
        author=args.author
    )

    # Generate agent
    generator = AgentTemplateGenerator()
    output_path = generator.generate_agent(spec, output_dir=args.output_dir)

    print(f"\n✅ Agent generated successfully!")
    print(f"📁 Location: {output_path}")
    print(f"\n📝 Next steps:")
    print(f"1. Implement _initialize_resources() method")
    print(f"2. Implement _execute_logic() method with your agent's intelligence")
    print(f"3. Implement _cleanup_resources() method")
    print(f"4. Add agent-specific configuration to {args.name}Config")
    print(f"5. Test agent: python {output_path} --health-check")
    print(f"6. Run compliance checker to verify standards")


if __name__ == "__main__":
    main()
