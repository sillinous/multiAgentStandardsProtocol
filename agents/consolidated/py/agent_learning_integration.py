# Agent Learning Integration Layer
# Integrates the learning framework into existing agent systems

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.agent_knowledge import (
    AgentLearner,
    AgentTeacher,
    get_knowledge_base,
    LearningMode,
    create_learning_loop
)

logger = logging.getLogger(__name__)


class LearningAgentWrapper:
    """
    Wrapper that adds learning capabilities to any agent

    Usage:
        agent = MarketResearchAgent(...)
        learning_agent = LearningAgentWrapper(agent, "market_research_agent_1")

        # Agent automatically learns from tasks
        result = await learning_agent.execute_task(task_data)
    """

    def __init__(
        self,
        agent: Any,
        agent_name: str,
        learning_mode: LearningMode = LearningMode.ACTIVE
    ):
        self.agent = agent
        self.agent_name = agent_name
        self.learner = AgentLearner(agent_name, learning_mode)
        self.teacher = AgentTeacher(agent_name)
        self.task_count = 0

        logger.info(f"🎓 Learning capabilities enabled for {agent_name}")

    async def execute_task_with_learning(
        self,
        task_data: Dict[str, Any],
        original_execute_func
    ) -> Dict[str, Any]:
        """
        Execute a task and automatically learn from the outcome

        Args:
            task_data: Task to execute
            original_execute_func: The agent's original execute function

        Returns:
            Task result with learning metadata
        """
        self.task_count += 1
        task_start = datetime.utcnow()

        # Recall relevant knowledge before execution
        relevant_knowledge = self.learner.recall_knowledge(
            task_context={
                'task_type': task_data.get('type', 'unknown'),
                'tags': task_data.get('tags', [])
            },
            min_confidence=0.6
        )

        if relevant_knowledge:
            logger.info(
                f"💡 {self.agent_name} recalled {len(relevant_knowledge)} "
                f"relevant knowledge entries"
            )
            # Inject knowledge into task context
            task_data['recalled_knowledge'] = [
                {
                    'id': k.knowledge_id,
                    'content': k.content,
                    'confidence': k.confidence,
                    'category': k.category
                }
                for k in relevant_knowledge
            ]

        try:
            # Execute the task
            result = await original_execute_func(task_data)

            # Learn from success
            if result.get('success', False):
                knowledge_id = self.learner.learn_from_success(
                    task_description=task_data.get('description', str(task_data)),
                    solution={
                        'approach': result.get('approach', 'unknown'),
                        'result': result.get('result', {}),
                        'method': result.get('method', 'unknown')
                    },
                    context={
                        'task_type': task_data.get('type', 'unknown'),
                        'duration_seconds': (datetime.utcnow() - task_start).total_seconds(),
                        'conditions': task_data.get('context', {}),
                        'success_factors': result.get('success_factors', [])
                    },
                    tags=task_data.get('tags', []) + ['success']
                )

                result['learned_knowledge_id'] = knowledge_id

                # Reinforce any recalled knowledge that was used
                if 'used_knowledge_ids' in result:
                    for kid in result['used_knowledge_ids']:
                        self.learner.knowledge_base.reinforce(
                            knowledge_id=kid,
                            success=True,
                            context={'task': task_data.get('type')}
                        )

            else:
                # Learn from failure
                knowledge_id = self.learner.learn_from_failure(
                    task_description=task_data.get('description', str(task_data)),
                    attempted_solution={
                        'approach': result.get('approach', 'unknown'),
                        'method': result.get('method', 'unknown')
                    },
                    failure_reason=result.get('error', 'Unknown error'),
                    context={
                        'task_type': task_data.get('type', 'unknown'),
                        'duration_seconds': (datetime.utcnow() - task_start).total_seconds(),
                        'conditions': task_data.get('context', {}),
                        'lessons': result.get('lessons_learned', [])
                    },
                    tags=task_data.get('tags', []) + ['failure']
                )

                result['learned_knowledge_id'] = knowledge_id

            # Add learning metadata to result
            result['learning_metadata'] = {
                'agent_name': self.agent_name,
                'task_count': self.task_count,
                'knowledge_recalled': len(relevant_knowledge),
                'learned': True
            }

            return result

        except Exception as e:
            # Learn from exceptions too
            logger.error(f"Task execution failed with exception: {e}")

            knowledge_id = self.learner.learn_from_failure(
                task_description=task_data.get('description', str(task_data)),
                attempted_solution={
                    'approach': task_data.get('approach', 'unknown')
                },
                failure_reason=str(e),
                context={
                    'task_type': task_data.get('type', 'unknown'),
                    'exception_type': type(e).__name__
                },
                tags=task_data.get('tags', []) + ['exception', 'failure']
            )

            raise

    def teach_another_agent(
        self,
        student_agent_name: str,
        topic: Optional[str] = None
    ) -> Dict[str, Any]:
        """Teach knowledge to another agent"""
        return self.teacher.teach(
            student_agent=student_agent_name,
            topic=topic,
            max_lessons=20
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get combined learning and teaching stats"""
        return {
            'agent_name': self.agent_name,
            'tasks_executed': self.task_count,
            'learning_stats': self.learner.get_learning_stats(),
            'teaching_stats': self.teacher.get_teaching_stats()
        }


def enable_agent_learning(
    agent: Any,
    agent_name: str,
    learning_mode: LearningMode = LearningMode.ACTIVE
) -> LearningAgentWrapper:
    """
    Enable learning capabilities for an existing agent

    Args:
        agent: Existing agent instance
        agent_name: Unique name for this agent
        learning_mode: Learning mode to use

    Returns:
        Learning-enabled agent wrapper
    """
    return LearningAgentWrapper(agent, agent_name, learning_mode)


# Monkey-patch helper for existing agent classes
def add_learning_to_agent_class(agent_class):
    """
    Decorator to add learning capabilities to an agent class

    Usage:
        @add_learning_to_agent_class
        class MyAgent:
            async def analyze(self, data):
                # ... existing code ...
                return result

    The agent will now automatically learn from each analysis.
    """
    original_init = agent_class.__init__

    def new_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)

        # Add learner and teacher
        agent_name = getattr(self, 'agent_name', None) or getattr(self, 'agent_id', 'unknown_agent')
        self._learner = AgentLearner(agent_name)
        self._teacher = AgentTeacher(agent_name)

        logger.info(f"🎓 Added learning capabilities to {agent_name}")

    # Replace __init__
    agent_class.__init__ = new_init

    # Add helper methods
    def recall_knowledge(self, task_context: Dict[str, Any]) -> List:
        """Recall relevant knowledge for a task"""
        return self._learner.recall_knowledge(task_context)

    def learn_from_result(self, task_data: Dict[str, Any], result: Dict[str, Any]):
        """Learn from a task result"""
        task_result = {
            'task': task_data.get('description', str(task_data)),
            'success': result.get('success', False),
            'solution': result.get('solution', {}),
            'context': task_data.get('context', {}),
            'tags': task_data.get('tags', [])
        }

        if result.get('error'):
            task_result['error'] = result['error']
            task_result['attempted_solution'] = result.get('attempted_solution', {})

        return create_learning_loop(
            agent_name=getattr(self, 'agent_name', 'unknown_agent'),
            task_result=task_result
        )

    agent_class.recall_knowledge = recall_knowledge
    agent_class.learn_from_result = learn_from_result

    return agent_class


# Global registry of learning-enabled agents
_learning_agents_registry: Dict[str, LearningAgentWrapper] = {}


def register_learning_agent(agent_name: str, wrapper: LearningAgentWrapper):
    """Register a learning-enabled agent"""
    _learning_agents_registry[agent_name] = wrapper
    logger.info(f"📝 Registered learning agent: {agent_name}")


def get_learning_agent(agent_name: str) -> Optional[LearningAgentWrapper]:
    """Get a registered learning agent"""
    return _learning_agents_registry.get(agent_name)


def get_all_learning_agents() -> Dict[str, LearningAgentWrapper]:
    """Get all registered learning agents"""
    return _learning_agents_registry.copy()


def get_learning_ecosystem_stats() -> Dict[str, Any]:
    """Get statistics for the entire learning ecosystem"""
    kb = get_knowledge_base()

    return {
        'total_learning_agents': len(_learning_agents_registry),
        'agents': {
            name: wrapper.get_stats()
            for name, wrapper in _learning_agents_registry.items()
        },
        'knowledge_base': kb.get_statistics(),
        'timestamp': datetime.utcnow().isoformat()
    }
