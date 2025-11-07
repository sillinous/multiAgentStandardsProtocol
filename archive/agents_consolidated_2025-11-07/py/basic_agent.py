"""
Basic Autonomous Agent Implementation
Based on APQC Agent Blueprints

This is the simplest possible agent implementation.
Use this as a starting point for your own agents.
"""

import json
from datetime import datetime
from typing import Dict, Any, List


class BasicAutonomousAgent:
    """
    Simple autonomous agent that follows APQC blueprint specification
    """

    def __init__(self, blueprint: Dict[str, Any]):
        """
        Initialize agent from APQC blueprint

        Args:
            blueprint: Agent configuration from enriched_agents.json
        """
        self.blueprint = blueprint
        self.agent_id = blueprint["agent_id"]
        self.version = blueprint["version"]
        self.metadata = blueprint["metadata"]
        self.capabilities = blueprint["capabilities"]

        # Runtime state
        self.state = {}
        self.task_history = []
        self.task_count = 0

        print(f"[INIT] Agent {self.agent_id}")
        print(f"       Process: {self.metadata['process_name']}")
        print(f"       Capabilities: {', '.join(self.capabilities[:3])}...")

    def process(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a task using agent capabilities

        Args:
            task: Task dictionary with:
                - id: Task identifier
                - description: What to do
                - data: Input data
                - context: Previous results (optional)

        Returns:
            Result dictionary with status, result, metadata
        """
        self.task_count += 1
        task_id = task.get("id", f"task_{self.task_count}")

        print(f"\n[TASK] {task_id}")
        print(f"       Description: {task.get('description', 'No description')}")

        # Record task start
        start_time = datetime.now()

        try:
            # This is where your agent logic goes
            # Examples:
            # - Call LLM API (OpenAI, Anthropic, etc.)
            # - Query database
            # - Process data
            # - Make decisions
            # - Generate content

            # Placeholder result
            result = self._execute_task(task)

            # Record success
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            output = {
                "task_id": task_id,
                "agent_id": self.agent_id,
                "status": "completed",
                "result": result,
                "metadata": {
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "duration_seconds": duration,
                    "capabilities_used": self.capabilities[:3],
                },
            }

            # Store in history
            self.task_history.append(output)

            print(f"       Status: COMPLETED ({duration:.2f}s)")
            return output

        except Exception as e:
            print(f"       Status: FAILED - {str(e)}")

            return {
                "task_id": task_id,
                "agent_id": self.agent_id,
                "status": "failed",
                "error": str(e),
                "metadata": {
                    "start_time": start_time.isoformat(),
                    "end_time": datetime.now().isoformat(),
                },
            }

    def _execute_task(self, task: Dict[str, Any]) -> Any:
        """
        Execute the actual task logic
        Override this method to implement your agent's behavior
        """
        # Example: Simple analysis based on agent capabilities
        if "analysis" in self.capabilities:
            return {
                "analysis": f"Analyzed {task.get('description')}",
                "insights": ["Insight 1", "Insight 2", "Insight 3"],
                "recommendations": ["Recommendation 1", "Recommendation 2"],
            }

        elif "decision_making" in self.capabilities:
            return {
                "decision": "approved",
                "confidence": 0.85,
                "reasoning": "Based on available data and strategic objectives",
            }

        else:
            return {"result": f"Processed using capabilities: {', '.join(self.capabilities)}"}

    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        return {
            "agent_id": self.agent_id,
            "process": self.metadata["process_name"],
            "category": self.metadata["category_name"],
            "tasks_processed": self.task_count,
            "capabilities": self.capabilities,
            "success_rate": self._calculate_success_rate(),
        }

    def _calculate_success_rate(self) -> float:
        """Calculate percentage of successful tasks"""
        if not self.task_history:
            return 0.0

        successful = sum(1 for t in self.task_history if t["status"] == "completed")
        return (successful / len(self.task_history)) * 100


# Example usage
if __name__ == "__main__":
    # Load agents
    with open("../enriched_agents.json", "r") as f:
        all_agents = json.load(f)

    # Create agent from first blueprint (Vision & Strategy)
    agent_config = all_agents[0]
    agent = BasicAutonomousAgent(agent_config)

    # Process some tasks
    tasks = [
        {
            "id": "task_001",
            "description": "Analyze current market position and competitive landscape",
            "data": {
                "market": "sustainable_mobility",
                "region": "europe",
                "competitors": ["company_a", "company_b", "company_c"],
            },
        },
        {
            "id": "task_002",
            "description": "Develop 5-year vision for autonomous mobility services",
            "data": {
                "current_state": "early_stage_startup",
                "target_state": "market_leader",
                "timeframe_years": 5,
            },
        },
        {
            "id": "task_003",
            "description": "Identify strategic partnership opportunities",
            "data": {
                "focus_areas": ["technology", "distribution", "investment"],
                "geography": "germany",
            },
        },
    ]

    # Execute tasks
    print("\n" + "=" * 60)
    print("EXECUTING TASKS")
    print("=" * 60)

    results = []
    for task in tasks:
        result = agent.process(task)
        results.append(result)

    # Show statistics
    print("\n" + "=" * 60)
    print("AGENT STATISTICS")
    print("=" * 60)

    stats = agent.get_stats()
    print(f"\nAgent: {stats['agent_id']}")
    print(f"Process: {stats['process']}")
    print(f"Category: {stats['category']}")
    print(f"Tasks Processed: {stats['tasks_processed']}")
    print(f"Success Rate: {stats['success_rate']:.1f}%")
    print(f"\nCapabilities:")
    for cap in stats["capabilities"]:
        print(f"  - {cap}")

    print("\n" + "=" * 60)
    print("DONE!")
    print("=" * 60)
