"""
Enhanced Base Agent - Next Generation Autonomous Agent

Integrates all advanced capabilities:
- Agent learning system
- Tool discovery and dynamic capabilities
- Collaborative problem solving
- Advanced protocols (A2A, A2P, ACP, ANP, MCP)
- Autonomous decision-making
- Self-improvement loops

This is the new standard for all agents in the ecosystem.

Version: 2.0.0
Date: 2025-10-18
"""

from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import asyncio
import logging

# Import CANONICAL base
from .base_agent_v1 import BaseAgent
from .protocols import (
    ProtocolMixin, A2AMessage, A2PTransaction,
    ACPCoordination, ANPRegistration, MessageType
)

# Import new systems
from .agent_learning_system import (
    AgentLearningSystem, ExperienceType, LearningStrategy,
    get_learning_system
)
from .tool_discovery_system import (
    ToolDiscoverySystem, ToolSource, ToolCategory,
    get_discovery_system
)
from .collaborative_problem_solving import (
    CollaborativeProblemSolving, ProblemSeverity, ProblemCategory,
    SolutionStrategy, get_collaborative_problem_solving
)


class EnhancedBaseAgent(BaseAgent, ProtocolMixin):
    """
    Enhanced Base Agent with Advanced Autonomous Capabilities

    New Capabilities:
    1. **Learning & Adaptation**
       - Learn from every execution
       - Adapt strategies based on outcomes
       - Share knowledge with other agents
       - Set and track learning goals

    2. **Dynamic Tool Discovery**
       - Discover new tools autonomously
       - Evaluate and integrate tools
       - Expand capabilities at runtime
       - Get tool recommendations

    3. **Collaborative Problem Solving**
       - Detect problems autonomously
       - Collaborate with other agents to solve
       - Share solutions and best practices
       - Escalate when needed

    4. **Advanced Protocols**
       - Full A2A, A2P, ACP, ANP, MCP support
       - Seamless inter-agent communication
       - Financial transactions between agents
       - Coordination and swarm intelligence

    5. **Self-Improvement**
       - Autonomous performance monitoring
       - Self-optimization loops
       - Capability expansion
       - Knowledge acquisition

    Usage:
        class MyAgent(EnhancedBaseAgent):
            async def _configure_data_sources(self):
                # Configure your data sources
                pass

            async def _execute_logic(self, input_data, fetched_data):
                # Your agent logic with automatic learning
                result = self.do_something(input_data)

                # Learning happens automatically
                # Tool recommendations happen automatically
                # Problem detection happens automatically

                return result

        agent = MyAgent(
            agent_id="my_agent_001",
            agent_type="my_custom_type"
        )

        await agent.initialize()
        result = await agent.execute({"task": "analyze"})
    """

    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        config: Optional[Dict[str, Any]] = None,
        enable_learning: bool = True,
        enable_tool_discovery: bool = True,
        enable_problem_solving: bool = True
    ):
        # Initialize base agent
        BaseAgent.__init__(self, agent_id, agent_type, config)
        ProtocolMixin.__init__(self)

        # Feature flags
        self.enable_learning = enable_learning
        self.enable_tool_discovery = enable_tool_discovery
        self.enable_problem_solving = enable_problem_solving

        # Initialize systems
        self.learning_system: Optional[AgentLearningSystem] = None
        self.tool_discovery: Optional[ToolDiscoverySystem] = None
        self.problem_solver: Optional[CollaborativeProblemSolving] = None

        # Agent capabilities registry
        self.capabilities_list: List[str] = []
        self.dynamic_tools: Dict[str, Callable] = {}

        # Learning goals
        self.active_learning_goals: List[str] = []

        # Performance baseline
        self.performance_baseline: Dict[str, float] = {}

    async def initialize(self):
        """Enhanced initialization with all systems"""
        # Base initialization
        await super().initialize()

        # Initialize learning system
        if self.enable_learning:
            self.learning_system = get_learning_system()
            self.logger.info(f"Learning system initialized for {self.agent_id}")

        # Initialize tool discovery
        if self.enable_tool_discovery:
            self.tool_discovery = get_discovery_system()
            await self._discover_initial_tools()
            self.logger.info(f"Tool discovery system initialized for {self.agent_id}")

        # Initialize problem solving
        if self.enable_problem_solving:
            self.problem_solver = get_collaborative_problem_solving()
            self.logger.info(f"Problem solving system initialized for {self.agent_id}")

        # Register on agent network (ANP)
        await self._register_on_network()

        # Set initial learning goals
        await self._set_initial_learning_goals()

        self.logger.info(f"Enhanced agent {self.agent_id} fully initialized")

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced execution with automatic learning and problem detection"""
        start_time = datetime.now()
        execution_context = {
            'agent_id': self.agent_id,
            'agent_type': self.agent_type,
            'input_data_summary': self._summarize_input(input_data),
            'timestamp': start_time.isoformat()
        }

        try:
            # Get tool recommendations before execution
            if self.enable_tool_discovery and self.tool_discovery:
                recommendations = await self._get_tool_recommendations(input_data)
                if recommendations:
                    self.logger.info(f"Tool recommendations: {len(recommendations)}")

            # Pre-execution checks
            await self._pre_execution_checks(input_data)

            # Fetch required data
            data = await self._fetch_required_data(input_data)

            # Core agent logic
            result = await self._execute_logic(input_data, data)

            # Validate output
            validated_result = await self._validate_output(result)

            # Calculate reward signal
            reward = self._calculate_reward(input_data, validated_result)

            # Record experience for learning
            if self.enable_learning and self.learning_system:
                await self._record_learning_experience(
                    input_data,
                    validated_result,
                    reward,
                    execution_context
                )

            # Update metrics
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            self._update_metrics('success', execution_time)

            # Check for performance degradation (problem detection)
            if self.enable_problem_solving:
                await self._check_performance_degradation(execution_time)

            # Update learning goals
            if self.enable_learning:
                await self._update_learning_progress(execution_time, reward)

            return validated_result

        except Exception as e:
            self.logger.error(f"Agent execution failed: {e}", exc_info=True)

            # Record failure experience
            if self.enable_learning and self.learning_system:
                await self._record_failure_experience(
                    input_data,
                    str(e),
                    execution_context
                )

            # Detect and report problem
            if self.enable_problem_solving and self.problem_solver:
                await self._report_problem(
                    category=ProblemCategory.BUSINESS_LOGIC,
                    severity=ProblemSeverity.HIGH,
                    description=f"Execution failed: {str(e)}",
                    context=execution_context
                )

            self._update_metrics('error', 0)
            raise

    async def learn_from_peers(
        self,
        knowledge_type: Optional[str] = None,
        min_confidence: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Learn from knowledge shared by other agents

        Args:
            knowledge_type: Filter by type (pattern, rule, strategy, best_practice)
            min_confidence: Minimum confidence threshold

        Returns:
            List of learned knowledge nodes
        """
        if not self.enable_learning or not self.learning_system:
            return []

        # Get shared knowledge
        knowledge_nodes = self.learning_system.get_shared_knowledge(
            agent_id=self.agent_id,
            knowledge_type=knowledge_type,
            min_confidence=min_confidence
        )

        # Apply learned knowledge
        applied_knowledge = []
        for node in knowledge_nodes:
            if await self._apply_knowledge(node):
                applied_knowledge.append(node)

        self.logger.info(f"Learned {len(applied_knowledge)} knowledge nodes from peers")
        return applied_knowledge

    async def share_knowledge(
        self,
        knowledge_type: str,
        content: Dict[str, Any],
        confidence: float,
        tags: Optional[List[str]] = None
    ) -> str:
        """
        Share knowledge with other agents

        Args:
            knowledge_type: Type of knowledge
            content: Knowledge content
            confidence: Confidence in this knowledge
            tags: Tags for categorization

        Returns:
            knowledge_node_id
        """
        if not self.enable_learning or not self.learning_system:
            raise ValueError("Learning system not enabled")

        node_id = self.learning_system.share_knowledge(
            from_agent=self.agent_id,
            knowledge_type=knowledge_type,
            content=content,
            confidence=confidence,
            tags=tags
        )

        self.logger.info(f"Shared knowledge node {node_id}")
        return node_id

    async def discover_and_add_capability(
        self,
        capability_name: str,
        description: str,
        required_tools: List[str]
    ) -> str:
        """
        Dynamically discover and add new capability

        Args:
            capability_name: Name of capability
            description: Description
            required_tools: Tools needed

        Returns:
            capability_id
        """
        if not self.enable_tool_discovery or not self.tool_discovery:
            raise ValueError("Tool discovery not enabled")

        # Discover and evaluate required tools
        for tool_name in required_tools:
            if tool_name not in self.dynamic_tools:
                # Try to discover tool
                tools = self.tool_discovery.recommend_tools(
                    task_description=tool_name,
                    context={'agent_type': self.agent_type},
                    agent_id=self.agent_id,
                    top_k=1
                )

                if tools:
                    # Add tool to agent
                    self.dynamic_tools[tool_name] = tools[0]

        # Register capability
        capability_id = self.tool_discovery.add_agent_capability(
            agent_id=self.agent_id,
            capability_name=capability_name,
            description=description,
            required_tools=required_tools,
            proficiency_level=0.5
        )

        # Add to capabilities list
        self.capabilities_list.append(capability_name)

        self.logger.info(f"Added new capability: {capability_name} ({capability_id})")
        return capability_id

    async def collaborate_on_problem(
        self,
        problem_id: str,
        contribution_type: str,
        contribution_data: Dict[str, Any]
    ) -> str:
        """
        Contribute to collaborative problem solving

        Args:
            problem_id: Problem being solved
            contribution_type: Type of contribution
            contribution_data: Contribution details

        Returns:
            contribution_id
        """
        if not self.enable_problem_solving or not self.problem_solver:
            raise ValueError("Problem solving not enabled")

        # Find active session for this problem
        # Simplified - in production would query active sessions
        session_id = f"session_{problem_id}_active"

        contribution_id = self.problem_solver.contribute_solution(
            session_id=session_id,
            agent_id=self.agent_id,
            contribution_type=contribution_type,
            contribution_data=contribution_data
        )

        self.logger.info(f"Contributed to problem {problem_id}: {contribution_id}")
        return contribution_id

    async def set_learning_goal(
        self,
        goal_type: str,
        target_metric: str,
        current_value: float,
        target_value: float,
        strategy: str = LearningStrategy.REINFORCEMENT.value,
        deadline: Optional[str] = None
    ) -> str:
        """
        Set a learning goal for self-improvement

        Args:
            goal_type: Type of goal (performance, efficiency, accuracy)
            target_metric: Metric to improve
            current_value: Current value
            target_value: Target value
            strategy: Learning strategy
            deadline: Optional deadline

        Returns:
            goal_id
        """
        if not self.enable_learning or not self.learning_system:
            raise ValueError("Learning system not enabled")

        goal_id = self.learning_system.set_learning_goal(
            agent_id=self.agent_id,
            goal_type=goal_type,
            target_metric=target_metric,
            current_value=current_value,
            target_value=target_value,
            strategy=strategy,
            deadline=deadline
        )

        self.active_learning_goals.append(goal_id)
        self.logger.info(f"Set learning goal: {target_metric} {current_value} -> {target_value}")

        return goal_id

    async def get_performance_insights(self) -> Dict[str, Any]:
        """Get insights into agent performance and learning"""
        insights = {
            'agent_id': self.agent_id,
            'agent_type': self.agent_type,
            'metrics': self.metrics,
            'capabilities': len(self.capabilities_list),
            'learning_enabled': self.enable_learning,
            'tool_discovery_enabled': self.enable_tool_discovery,
            'problem_solving_enabled': self.enable_problem_solving
        }

        # Add learning insights
        if self.enable_learning and self.learning_system:
            insights['learning_goals'] = len(self.active_learning_goals)

            # Get performance trends
            for metric_name in ['execution_time_ms', 'success_rate']:
                trend = self.learning_system.get_agent_performance_trend(
                    agent_id=self.agent_id,
                    metric_name=metric_name,
                    days=7
                )
                insights[f'{metric_name}_trend'] = trend

        # Add tool insights
        if self.enable_tool_discovery and self.tool_discovery:
            capabilities = self.tool_discovery.get_agent_capabilities(self.agent_id)
            insights['dynamic_capabilities'] = len(capabilities)
            insights['total_tools'] = len(self.dynamic_tools)

        return insights

    # Private methods for internal systems

    async def _discover_initial_tools(self):
        """Discover initial set of tools"""
        if not self.tool_discovery:
            return

        # Discover from local filesystem
        tools = self.tool_discovery.discover_tools(
            source=ToolSource.LOCAL_FILESYSTEM,
            search_paths=["./tools", "./autonomous-ecosystem/tools"]
        )

        # Discover from shared agents
        shared_tools = self.tool_discovery.discover_tools(
            source=ToolSource.AGENT_SHARED
        )

        total_discovered = len(tools) + len(shared_tools)
        self.logger.info(f"Discovered {total_discovered} initial tools")

    async def _register_on_network(self):
        """Register agent on the agent network (ANP)"""
        try:
            registration = await self.register_on_network()
            self.logger.info(f"Registered on agent network: {registration.agent_id}")
        except Exception as e:
            self.logger.warning(f"Network registration failed: {e}")

    async def _set_initial_learning_goals(self):
        """Set initial learning goals for the agent"""
        if not self.enable_learning or not self.learning_system:
            return

        # Set default goal: improve average execution time
        try:
            goal_id = await self.set_learning_goal(
                goal_type="performance",
                target_metric="avg_execution_time_ms",
                current_value=self.metrics['avg_decision_time_ms'],
                target_value=max(self.metrics['avg_decision_time_ms'] * 0.8, 100),
                strategy=LearningStrategy.REINFORCEMENT.value
            )
            self.logger.info(f"Set initial learning goal: {goal_id}")
        except Exception as e:
            self.logger.warning(f"Failed to set initial learning goal: {e}")

    async def _get_tool_recommendations(
        self,
        input_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get tool recommendations for current task"""
        if not self.tool_discovery:
            return []

        task_description = self._infer_task_description(input_data)

        recommendations = self.tool_discovery.recommend_tools(
            task_description=task_description,
            context={'input_data': input_data},
            agent_id=self.agent_id,
            top_k=3
        )

        return recommendations

    async def _record_learning_experience(
        self,
        input_data: Dict[str, Any],
        result: Dict[str, Any],
        reward: float,
        context: Dict[str, Any]
    ):
        """Record experience for learning"""
        if not self.learning_system:
            return

        try:
            experience_id = self.learning_system.record_experience(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                experience_type=ExperienceType.SUCCESS if reward > 0 else ExperienceType.FAILURE,
                context=context,
                action={'input': self._summarize_input(input_data)},
                outcome={'result_summary': self._summarize_output(result)},
                reward=reward,
                confidence=0.8
            )

            self.logger.debug(f"Recorded experience: {experience_id}")
        except Exception as e:
            self.logger.warning(f"Failed to record experience: {e}")

    async def _record_failure_experience(
        self,
        input_data: Dict[str, Any],
        error: str,
        context: Dict[str, Any]
    ):
        """Record failure experience"""
        if not self.learning_system:
            return

        try:
            self.learning_system.record_experience(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                experience_type=ExperienceType.FAILURE,
                context=context,
                action={'input': self._summarize_input(input_data)},
                outcome={'error': error},
                reward=-0.5,
                confidence=0.9
            )
        except Exception as e:
            self.logger.warning(f"Failed to record failure: {e}")

    async def _check_performance_degradation(self, execution_time: float):
        """Check if performance has degraded significantly"""
        if not self.problem_solver:
            return

        # Establish baseline on first executions
        if 'execution_time_avg' not in self.performance_baseline:
            self.performance_baseline['execution_time_avg'] = execution_time
            self.performance_baseline['execution_count'] = 1
            return

        # Update running average
        count = self.performance_baseline['execution_count']
        avg = self.performance_baseline['execution_time_avg']
        new_avg = (avg * count + execution_time) / (count + 1)
        self.performance_baseline['execution_time_avg'] = new_avg
        self.performance_baseline['execution_count'] = count + 1

        # Check for degradation (>50% slower than average)
        if execution_time > new_avg * 1.5 and count > 10:
            await self._report_problem(
                category=ProblemCategory.PERFORMANCE,
                severity=ProblemSeverity.MEDIUM,
                description=f"Execution time degradation detected: {execution_time:.2f}ms vs {new_avg:.2f}ms average",
                context={
                    'current_execution_time': execution_time,
                    'average_execution_time': new_avg,
                    'degradation_factor': execution_time / new_avg
                }
            )

    async def _report_problem(
        self,
        category: ProblemCategory,
        severity: ProblemSeverity,
        description: str,
        context: Dict[str, Any]
    ):
        """Report a detected problem"""
        if not self.problem_solver:
            return

        try:
            problem_id = self.problem_solver.detect_problem(
                detector_agent=self.agent_id,
                category=category,
                severity=severity,
                description=description,
                context=context,
                symptoms=[],
                affected_agents=[self.agent_id]
            )

            self.logger.warning(f"Reported problem: {problem_id} - {description}")
        except Exception as e:
            self.logger.error(f"Failed to report problem: {e}")

    async def _update_learning_progress(self, execution_time: float, reward: float):
        """Update progress on learning goals"""
        if not self.learning_system:
            return

        for goal_id in self.active_learning_goals:
            try:
                # Update goal with new metric value
                result = self.learning_system.update_goal_progress(
                    goal_id=goal_id,
                    new_value=execution_time  # Simplified - would track specific metrics
                )

                if result['status'] == 'achieved':
                    self.logger.info(f"Learning goal achieved: {goal_id}")
                    self.active_learning_goals.remove(goal_id)

            except Exception as e:
                self.logger.debug(f"Failed to update learning goal {goal_id}: {e}")

    async def _apply_knowledge(self, knowledge_node: Dict[str, Any]) -> bool:
        """Apply learned knowledge from peers"""
        try:
            # Extract knowledge content
            content = knowledge_node['content']
            knowledge_type = knowledge_node['knowledge_type']

            # Apply based on type
            if knowledge_type == 'pattern':
                # Store pattern for future use
                self.state[f"learned_pattern_{knowledge_node['node_id']}"] = content
            elif knowledge_type == 'best_practice':
                # Update configuration
                self.config.update(content.get('config_updates', {}))
            elif knowledge_type == 'strategy':
                # Store strategy
                self.state[f"learned_strategy_{knowledge_node['node_id']}"] = content

            self.logger.info(f"Applied knowledge: {knowledge_node['node_id']}")
            return True

        except Exception as e:
            self.logger.warning(f"Failed to apply knowledge: {e}")
            return False

    def _calculate_reward(
        self,
        input_data: Dict[str, Any],
        result: Dict[str, Any]
    ) -> float:
        """Calculate reward signal for learning (override in subclass)"""
        # Default implementation - can be overridden
        if result.get('success', True):
            return 1.0
        return 0.0

    def _summarize_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize input data for logging"""
        return {
            'keys': list(input_data.keys()),
            'size': len(str(input_data))
        }

    def _summarize_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize output for logging"""
        return {
            'keys': list(output.keys()),
            'size': len(str(output))
        }

    def _infer_task_description(self, input_data: Dict[str, Any]) -> str:
        """Infer task description from input (override in subclass)"""
        task_type = input_data.get('type', input_data.get('task', 'general_task'))
        return f"Perform {task_type} operation"
