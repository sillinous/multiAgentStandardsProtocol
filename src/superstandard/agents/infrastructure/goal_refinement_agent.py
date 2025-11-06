"""
Phase 8: Goal Refinement & Autonomous Planning
Goal Refinement Agent - Main Orchestrator

Coordinates entire goal refinement pipeline:
Analyze → Clarify → Refine → Analyze Constraints → Generate Strategies → Select Path → Execute → Learn
"""

import asyncio
import logging
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import uuid

from src.agents.base_agent import BaseAgent
from src.models.model_factory import ModelFactory
from .goal_analyzer import GoalAnalyzer, GoalAnalysis, ClarificationEngine
from .goal_clarifier import GoalRefiner, RefinedGoal
from .constraint_analyzer import ConstraintAnalyzer, ConstraintSet, ResourcePlanner
from .strategy_generator import StrategyGenerator, PathSelector, StrategyPath
from .meta_goal_manager import MetaGoalManager, RecursiveDecomposer
from .adaptive_executor import AdaptiveExecutor, ExecutionMonitor

logger = logging.getLogger(__name__)


@dataclass
class RefinementResult:
    """Result of complete goal refinement pipeline"""

    refinement_id: str
    original_goal: str
    refined_goal: RefinedGoal
    analysis: GoalAnalysis
    clarifications_used: Dict[str, str]
    constraints: ConstraintSet
    generated_strategies: List[StrategyPath]
    selected_strategy: StrategyPath
    fallback_strategy: StrategyPath
    execution_plan: Dict[str, Any]
    estimated_success_probability: float
    readiness_score: float  # 0-1, how ready for execution
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "refinement_id": self.refinement_id,
            "original_goal": self.original_goal,
            "refined_goal": self.refined_goal.to_dict(),
            "estimated_success_probability": self.estimated_success_probability,
            "readiness_score": self.readiness_score,
            "selected_strategy": self.selected_strategy.name,
            "fallback_strategy": self.fallback_strategy.name if self.fallback_strategy else None,
            "created_at": self.created_at.isoformat(),
        }


class GoalRefinementAgent(BaseAgent):
    """Main orchestrator for goal refinement and execution"""

    def __init__(self):
        """Initialize the goal refinement agent"""
        super().__init__(agent_type="goal_refinement")

        # Initialize components
        self.analyzer = GoalAnalyzer(model_type="claude")
        self.clarifier = ClarificationEngine(model_type="claude")
        self.refiner = GoalRefiner(model_type="claude")
        self.constraint_analyzer = ConstraintAnalyzer(model_type="claude")
        self.resource_planner = ResourcePlanner()
        self.strategy_generator = StrategyGenerator(model_type="claude")
        self.path_selector = PathSelector(model_type="claude")
        self.meta_goal_manager = MetaGoalManager(model_type="claude")
        self.recursive_decomposer = RecursiveDecomposer(max_depth=10, model_type="claude")
        self.adaptive_executor = AdaptiveExecutor(adaptation_time_budget_ms=100.0)

        # Track refinements and executions
        self.refinement_history: Dict[str, RefinementResult] = {}
        self.execution_history: Dict[str, Dict] = {}

        logger.info("GoalRefinementAgent initialized with all components")

    def run(self):
        """Main agent loop"""
        logger.info("GoalRefinementAgent starting main loop")
        # This would be called by orchestrator - for now just log initialization
        logger.info("Agent ready to process goals")

    async def process_goal(self, goal: str, context: Optional[Dict] = None) -> RefinementResult:
        """
        Process a goal through complete refinement pipeline

        Args:
            goal: Goal statement to refine
            context: Optional context with agent capabilities, market data, etc.

        Returns:
            RefinementResult with refined goal and execution plan
        """
        refinement_id = str(uuid.uuid4())[:8]
        context = context or {}

        logger.info(f"Processing goal {refinement_id}: {goal}")

        try:
            # Step 1: Analyze goal
            logger.info(f"[{refinement_id}] Step 1: Analyzing goal...")
            analysis = self.analyzer.analyze_goal(goal, context)

            # Step 2: Generate clarification questions if needed
            clarifications = {}
            if analysis.requires_clarification:
                logger.info(f"[{refinement_id}] Step 2: Generating clarification questions...")
                questions = self.clarifier.generate_questions(analysis, max_questions=5)
                questions = self.clarifier.prioritize_questions(questions)

                # In production, this would get user input or query shared memory
                # For now, we'll auto-answer from context
                for question in questions:
                    answer = self.clarifier.auto_answer_from_memory(question, context)
                    if answer:
                        clarifications[question.question_text] = answer
                        logger.info(
                            f"[{refinement_id}] Auto-answered: {question.question_text[:50]}..."
                        )

            # Step 3: Refine goal
            logger.info(f"[{refinement_id}] Step 3: Refining goal...")
            refined_goal = self.refiner.refine_goal(analysis, clarifications, context)

            # Step 4: Analyze constraints
            logger.info(f"[{refinement_id}] Step 4: Analyzing constraints...")
            constraints = self.constraint_analyzer.analyze_constraints(refined_goal, context)

            # Step 5: Generate strategies
            logger.info(f"[{refinement_id}] Step 5: Generating execution strategies...")
            strategies = self.strategy_generator.generate_strategies(
                refined_goal, num_strategies=4, context=context
            )
            strategies = self.strategy_generator.rank_strategies(strategies, context)

            # Step 6: Select best strategy
            logger.info(f"[{refinement_id}] Step 6: Selecting best strategy...")
            selected_strategy = self.path_selector.select_best_path(strategies, context)
            fallback_strategy = self.path_selector.generate_fallback_path(selected_strategy)

            # Step 7: Create execution plan
            logger.info(f"[{refinement_id}] Step 7: Creating execution plan...")
            execution_plan = self._create_execution_plan(
                refined_goal, selected_strategy, constraints, context
            )

            # Step 8: Calculate readiness
            readiness = self._calculate_readiness(refined_goal, selected_strategy, constraints)

            # Create result
            result = RefinementResult(
                refinement_id=refinement_id,
                original_goal=goal,
                refined_goal=refined_goal,
                analysis=analysis,
                clarifications_used=clarifications,
                constraints=constraints,
                generated_strategies=strategies,
                selected_strategy=selected_strategy,
                fallback_strategy=fallback_strategy,
                execution_plan=execution_plan,
                estimated_success_probability=selected_strategy.success_probability,
                readiness_score=readiness,
            )

            # Store in history
            self.refinement_history[refinement_id] = result

            logger.info(
                f"[{refinement_id}] Refinement complete: "
                f"success_probability={result.estimated_success_probability:.0%}, "
                f"readiness={result.readiness_score:.0%}"
            )

            return result

        except Exception as e:
            logger.error(f"[{refinement_id}] Error processing goal: {str(e)}", exc_info=True)
            raise

    async def refine_and_execute(self, goal: str, context: Optional[Dict] = None) -> Dict:
        """
        Full pipeline: refine goal and execute it

        Args:
            goal: Goal to refine and execute
            context: Optional context

        Returns:
            Execution result
        """
        # Refine goal
        result = await self.process_goal(goal, context)

        if result.readiness_score < 0.5:
            logger.warning(
                f"Goal readiness low ({result.readiness_score:.0%}), requiring user confirmation"
            )
            return {"status": "pending_approval", "refinement_result": result.to_dict()}

        # Execute (would normally hand off to Strategy Agent)
        logger.info(f"Executing goal {result.refinement_id}: {result.selected_strategy.name}")

        execution_result = {
            "refinement_id": result.refinement_id,
            "goal_id": result.refined_goal.goal_id,
            "strategy": result.selected_strategy.name,
            "status": "execution_started",
            "estimated_duration": result.refined_goal.estimated_duration.total_seconds() / 60,
            "success_probability": result.estimated_success_probability,
        }

        self.execution_history[result.refinement_id] = execution_result
        return execution_result

    async def handle_vague_goal(
        self, goal: str, user_context: Optional[Dict] = None
    ) -> RefinedGoal:
        """
        Special handling for vague goals with interactive clarification

        Args:
            goal: Vague goal statement
            user_context: Optional user context

        Returns:
            Refined goal after clarification
        """
        logger.info(f"Handling vague goal: {goal}")

        analysis = self.analyzer.analyze_goal(goal, user_context or {})

        if analysis.classification.value != "vague":
            logger.info("Goal not vague, processing normally")
            result = await self.process_goal(goal, user_context)
            return result.refined_goal

        # Generate clarification questions
        questions = self.clarifier.generate_questions(analysis, max_questions=5)
        questions = self.clarifier.prioritize_questions(questions)

        logger.info(f"Generated {len(questions)} clarification questions")

        # Collect clarifications (in production, would be interactive)
        clarifications = {}
        for question in questions:
            # Try auto-answer first
            answer = self.clarifier.auto_answer_from_memory(question, user_context or {})
            if answer:
                clarifications[question.question_text] = answer

        # Refine with clarifications
        refined = self.refiner.refine_goal(analysis, clarifications, user_context or {})
        logger.info("Vague goal refined successfully")
        return refined

    async def generate_alternatives(
        self, goal: RefinedGoal, num_alternatives: int = 3
    ) -> List[StrategyPath]:
        """
        Generate alternative strategies for a refined goal

        Args:
            goal: Refined goal
            num_alternatives: Number of alternatives to generate

        Returns:
            List of alternative strategies
        """
        logger.info(f"Generating {num_alternatives} alternative strategies for goal {goal.goal_id}")

        strategies = self.strategy_generator.generate_strategies(
            goal, num_strategies=num_alternatives
        )
        strategies = self.strategy_generator.rank_strategies(strategies)

        return strategies

    async def execute_with_monitoring(
        self, refinement_result: RefinementResult, context: Optional[Dict] = None
    ) -> Dict:
        """
        Execute goal with continuous monitoring and adaptation

        Args:
            refinement_result: Result from process_goal
            context: Execution context

        Returns:
            Execution result with monitoring data
        """
        context = context or {}
        plan_id = f"exec_{refinement_result.refinement_id}"

        logger.info(f"Starting monitored execution: {plan_id}")

        # Start monitoring
        monitor = self.adaptive_executor.monitor_execution(
            plan_id, refinement_result.refined_goal, refinement_result.selected_strategy
        )

        # In production, would execute strategy steps and monitor continuously
        # For now, simulate execution
        execution_log = []

        for i, step in enumerate(refinement_result.selected_strategy.steps):
            # Simulate step execution
            monitor.progress_percent = (
                (i + 1) / len(refinement_result.selected_strategy.steps) * 100
            )
            monitor.completed_steps.append(step)

            # Detect environmental changes (in production, would be real-time)
            changes = self.adaptive_executor.detect_environmental_changes(plan_id, context)

            if changes:
                logger.warning(f"Detected {len(changes)} changes during execution")

                # Assess impact
                impact = self.adaptive_executor.assess_impact(
                    changes, refinement_result.refined_goal, monitor.current_strategy
                )

                # Adapt if needed
                if not impact.current_plan_viable:
                    logger.info("Current plan not viable, adapting...")
                    adapted, adaptations = self.adaptive_executor.adapt_plan(
                        plan_id, refinement_result.refined_goal, monitor.current_strategy, impact
                    )
                    execution_log.append(f"Adapted strategy: {adaptations}")

            execution_log.append(f"Step {i+1}: {step}")

        return {
            "plan_id": plan_id,
            "status": "completed",
            "progress": monitor.progress_percent,
            "completed_steps": len(monitor.completed_steps),
            "adaptations": len(monitor.adaptations_made),
            "final_success_probability": monitor.current_success_probability,
            "execution_log": execution_log,
        }

    async def learn_from_execution(
        self, refinement_id: str, execution_result: Dict, outcome: str = "success"
    ):
        """
        Learn from execution for future refinements

        Args:
            refinement_id: ID of refined goal
            execution_result: Result of execution
            outcome: "success", "partial_success", or "failure"
        """
        if refinement_id not in self.refinement_history:
            logger.warning(f"No refinement history for {refinement_id}")
            return

        refinement = self.refinement_history[refinement_id]

        logger.info(
            f"Learning from execution {refinement_id}: outcome={outcome}, "
            f"goal={refinement.original_goal[:50]}..."
        )

        # Record learning insights
        insight = {
            "refinement_id": refinement_id,
            "original_goal": refinement.original_goal,
            "refined_goal": refinement.refined_goal.refined_description,
            "strategy_used": refinement.selected_strategy.name,
            "outcome": outcome,
            "actual_duration": execution_result.get("duration_ms", 0),
            "estimated_duration": refinement.refined_goal.estimated_duration.total_seconds() * 1000,
            "adaptations_needed": execution_result.get("adaptations", 0),
            "learned_at": datetime.now().isoformat(),
        }

        # Store learning (in production, would update Phase 5 learning system)
        logger.info(f"Recorded learning: {outcome} for {refinement.selected_strategy.name}")

    def _create_execution_plan(
        self, goal: RefinedGoal, strategy: StrategyPath, constraints: ConstraintSet, context: Dict
    ) -> Dict:
        """Create detailed execution plan"""
        return {
            "goal_id": goal.goal_id,
            "strategy": strategy.name,
            "steps": strategy.steps,
            "estimated_duration_minutes": strategy.estimated_duration.total_seconds() / 60,
            "success_probability": strategy.success_probability,
            "risk_level": strategy.risk_level,
            "required_agents": strategy.resource_requirements.get("agents", []),
            "constraints": {
                "temporal": len(constraints.temporal_constraints),
                "resource": len(constraints.resource_constraints),
                "risk": len(constraints.risk_constraints),
            },
            "execution_window": self._suggest_execution_window(goal, strategy, context),
            "fallback_available": True,
            "ready_for_execution": True,
        }

    def _calculate_readiness(
        self, goal: RefinedGoal, strategy: StrategyPath, constraints: ConstraintSet
    ) -> float:
        """Calculate readiness score (0-1)"""
        readiness = 0.5  # Base score

        # Boost for high success probability
        readiness += goal.success_probability * 0.3

        # Boost for low risk
        risk_boost = {"LOW": 0.15, "MEDIUM": 0.05, "HIGH": -0.1, "CRITICAL": -0.3}
        readiness += risk_boost.get(strategy.risk_level, 0)

        # Penalty for hard constraint violations
        if constraints.conflicting_constraints:
            readiness -= len(constraints.conflicting_constraints) * 0.05

        return max(min(readiness, 1.0), 0.0)

    def _suggest_execution_window(
        self, goal: RefinedGoal, strategy: StrategyPath, context: Dict
    ) -> Dict:
        """Suggest optimal execution window"""
        start_time, confidence = self.resource_planner.estimate_optimal_start_time(goal, context)

        return {
            "suggested_start": start_time.isoformat(),
            "start_confidence": confidence,
            "estimated_duration_minutes": strategy.estimated_duration.total_seconds() / 60,
            "execution_window_available": True,
        }
