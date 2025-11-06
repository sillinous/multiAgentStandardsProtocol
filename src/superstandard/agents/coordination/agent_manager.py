#!/usr/bin/env python3
"""
🌙 Agent Management System - Autonomous Agent Ecosystem

Provides comprehensive agent management including:
- Agent discovery and metadata
- Shared memory/context management
- Learning system for agent evolution
- Real-time output monitoring
- Inter-agent communication
- Autonomous decision making

This enables agents to:
1. Function independently and autonomously
2. Share learnings through shared memory
3. Make decisions based on environment feedback
4. Evolve and improve their behavior over time
5. Learn from each other's experiences
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)

# Data directories
DATA_DIR = Path(__file__).parent.parent / "data"
AGENT_MEMORY_DIR = DATA_DIR / "agent_memory"
AGENT_LEARNINGS_DIR = DATA_DIR / "agent_learnings"
AGENT_OUTPUTS_DIR = DATA_DIR / "agent_outputs"

# Create directories
for dir_path in [AGENT_MEMORY_DIR, AGENT_LEARNINGS_DIR, AGENT_OUTPUTS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)


class AgentStatus(Enum):
    """Agent execution status"""

    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    ERROR = "error"


@dataclass
class AgentRequirement:
    """Input/Output requirement for agent"""

    name: str
    type: str  # 'input', 'output', 'dependency'
    description: str
    format: str  # 'json', 'csv', 'text', etc.
    required: bool = True
    default: Optional[Any] = None


@dataclass
class AgentLearning:
    """Learning record from agent execution"""

    agent_name: str
    learning_id: str
    timestamp: datetime
    category: str  # 'market_insight', 'strategy', 'failure', 'success'
    content: Dict[str, Any]
    confidence: float  # 0-1
    applicable_to: List[str] = field(default_factory=list)  # Other agents this applies to

    def __post_init__(self):
        """Handle timestamp conversion from string to datetime"""
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = asdict(self)
        data["timestamp"] = (
            self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp
        )
        return data


@dataclass
class AgentMemory:
    """Shared memory entry for agent ecosystem"""

    memory_id: str
    agent_name: str
    timestamp: datetime
    category: str  # 'observation', 'insight', 'decision', 'warning'
    content: Dict[str, Any]
    ttl_seconds: Optional[int] = None  # Time to live
    accessible_by: List[str] = field(default_factory=list)  # Agents that can access this

    def __post_init__(self):
        """Handle timestamp conversion from string to datetime"""
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = asdict(self)
        data["timestamp"] = (
            self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp
        )
        return data


@dataclass
class AgentOutput:
    """Agent execution output"""

    agent_name: str
    execution_id: str
    timestamp: datetime
    status: AgentStatus
    output_data: Dict[str, Any]
    errors: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0

    def __post_init__(self):
        """Handle timestamp and status conversion from JSON"""
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp)
        if isinstance(self.status, str):
            self.status = AgentStatus(self.status)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = asdict(self)
        data["timestamp"] = (
            self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp
        )
        data["status"] = self.status.value if isinstance(self.status, AgentStatus) else self.status
        return data


class AgentMemoryManager:
    """Manages shared memory across agent ecosystem"""

    def __init__(self):
        self.memory_file = AGENT_MEMORY_DIR / "shared_memory.json"
        self.memory: List[AgentMemory] = self._load_memory()

    def _load_memory(self) -> List[AgentMemory]:
        """Load memory from disk"""
        if not self.memory_file.exists():
            return []

        try:
            with open(self.memory_file, "r") as f:
                data = json.load(f)
                return [AgentMemory(**m) for m in data]
        except Exception as e:
            logger.error(f"Error loading memory: {e}")
            return []

    def _save_memory(self):
        """Save memory to disk"""
        try:
            with open(self.memory_file, "w") as f:
                json.dump([m.to_dict() for m in self.memory], f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving memory: {e}")

    def store_memory(
        self,
        agent_name: str,
        category: str,
        content: Dict,
        accessible_by: Optional[List[str]] = None,
    ) -> AgentMemory:
        """Store memory entry"""
        memory = AgentMemory(
            memory_id=self._generate_id(),
            agent_name=agent_name,
            timestamp=datetime.utcnow(),
            category=category,
            content=content,
            accessible_by=accessible_by or [],
        )
        self.memory.append(memory)
        self._save_memory()
        logger.info(f"Stored memory: {agent_name}:{category}")
        return memory

    def get_memory(
        self, agent_name: str, category: Optional[str] = None, limit: int = 100
    ) -> List[AgentMemory]:
        """Get accessible memory for agent"""
        filtered = [
            m
            for m in self.memory
            if (agent_name in m.accessible_by or m.agent_name == agent_name or not m.accessible_by)
            and (category is None or m.category == category)
        ]
        return sorted(filtered, key=lambda x: x.timestamp, reverse=True)[:limit]

    def get_observations(self) -> List[AgentMemory]:
        """Get all observations from all agents"""
        return [m for m in self.memory if m.category == "observation"]

    def get_insights(self) -> List[AgentMemory]:
        """Get all insights from all agents"""
        return [m for m in self.memory if m.category == "insight"]

    def get_warnings(self) -> List[AgentMemory]:
        """Get all warnings from all agents"""
        return [m for m in self.memory if m.category == "warning"]

    @staticmethod
    def _generate_id() -> str:
        """Generate unique ID"""
        return hashlib.md5(f"{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16]


class AgentLearningManager:
    """Manages agent learnings and evolution"""

    def __init__(self):
        self.learnings_dir = AGENT_LEARNINGS_DIR

    def record_learning(
        self,
        agent_name: str,
        category: str,
        content: Dict,
        confidence: float,
        applicable_to: Optional[List[str]] = None,
    ) -> AgentLearning:
        """Record a learning from agent execution"""
        learning = AgentLearning(
            agent_name=agent_name,
            learning_id=self._generate_id(),
            timestamp=datetime.utcnow(),
            category=category,
            content=content,
            confidence=confidence,
            applicable_to=applicable_to or [],
        )

        # Save learning
        learning_file = self.learnings_dir / f"{agent_name}_{learning.learning_id}.json"
        try:
            with open(learning_file, "w") as f:
                json.dump(learning.to_dict(), f, indent=2)
            logger.info(f"Recorded learning for {agent_name}: {category}")
        except Exception as e:
            logger.error(f"Error saving learning: {e}")

        return learning

    def get_learnings(self, agent_name: str, category: Optional[str] = None) -> List[AgentLearning]:
        """Get learnings for an agent"""
        learnings = []
        pattern = f"{agent_name}_*.json" if agent_name else "*.json"

        for file in self.learnings_dir.glob(pattern):
            try:
                with open(file, "r") as f:
                    data = json.load(f)
                    if category is None or data.get("category") == category:
                        learnings.append(AgentLearning(**data))
            except Exception as e:
                logger.error(f"Error loading learning: {e}")

        return sorted(learnings, key=lambda x: x.confidence, reverse=True)

    def get_high_confidence_learnings(self, min_confidence: float = 0.8) -> List[AgentLearning]:
        """Get high-confidence learnings across all agents"""
        learnings = []
        for file in self.learnings_dir.glob("*.json"):
            try:
                with open(file, "r") as f:
                    data = json.load(f)
                    if data.get("confidence", 0) >= min_confidence:
                        learnings.append(AgentLearning(**data))
            except Exception as e:
                logger.error(f"Error loading learning: {e}")

        return sorted(learnings, key=lambda x: x.confidence, reverse=True)

    def suggest_improvements(self, agent_name: str) -> Dict[str, Any]:
        """Suggest code improvements based on learnings"""
        learnings = self.get_learnings(agent_name)
        failures = [l for l in learnings if l.category == "failure"]
        successes = [l for l in learnings if l.category == "success"]

        suggestions = {
            "agent_name": agent_name,
            "total_learnings": len(learnings),
            "failure_patterns": [],
            "success_patterns": [],
            "recommended_changes": [],
        }

        # Analyze failures
        if failures:
            suggestions["failure_patterns"] = [
                {
                    "pattern": f.content.get("pattern"),
                    "occurrences": len(
                        [
                            x
                            for x in failures
                            if x.content.get("pattern") == f.content.get("pattern")
                        ]
                    ),
                    "confidence": f.confidence,
                }
                for f in failures[:5]
            ]

        # Analyze successes
        if successes:
            suggestions["success_patterns"] = [
                {
                    "pattern": s.content.get("pattern"),
                    "occurrences": len(
                        [
                            x
                            for x in successes
                            if x.content.get("pattern") == s.content.get("pattern")
                        ]
                    ),
                    "confidence": s.confidence,
                }
                for s in successes[:5]
            ]

        # Generate recommendations
        if failures:
            suggestions["recommended_changes"] = [
                f"Address failure pattern: {f.content.get('pattern')}" for f in failures[:3]
            ]

        return suggestions

    @staticmethod
    def _generate_id() -> str:
        """Generate unique ID"""
        return hashlib.md5(f"{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16]


class AgentOutputManager:
    """Manages agent execution outputs"""

    def __init__(self):
        self.outputs_dir = AGENT_OUTPUTS_DIR

    def store_output(
        self,
        agent_name: str,
        execution_id: str,
        status: AgentStatus,
        output_data: Dict,
        errors: Optional[List[str]] = None,
        duration_seconds: float = 0.0,
    ) -> AgentOutput:
        """Store agent execution output"""
        output = AgentOutput(
            agent_name=agent_name,
            execution_id=execution_id,
            timestamp=datetime.utcnow(),
            status=status,
            output_data=output_data,
            errors=errors or [],
            duration_seconds=duration_seconds,
        )

        # Save output
        output_file = self.outputs_dir / f"{agent_name}_{execution_id}.json"
        try:
            with open(output_file, "w") as f:
                json.dump(output.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Error saving output: {e}")

        return output

    def get_latest_outputs(
        self, agent_name: Optional[str] = None, limit: int = 20
    ) -> List[AgentOutput]:
        """Get latest outputs"""
        outputs = []
        pattern = f"{agent_name}_*.json" if agent_name else "*.json"

        for file in sorted(self.outputs_dir.glob(pattern), reverse=True)[:limit]:
            try:
                with open(file, "r") as f:
                    data = json.load(f)
                    outputs.append(AgentOutput(**data))
            except Exception as e:
                logger.error(f"Error loading output: {e}")

        return outputs

    def get_agent_stats(self, agent_name: str) -> Dict[str, Any]:
        """Get execution statistics for an agent"""
        outputs = self.get_latest_outputs(agent_name, limit=100)

        total = len(outputs)
        successful = len([o for o in outputs if o.status == AgentStatus.SUCCESS])
        failed = len([o for o in outputs if o.status == AgentStatus.FAILED])
        avg_duration = sum(o.duration_seconds for o in outputs) / total if total > 0 else 0

        return {
            "agent_name": agent_name,
            "total_executions": total,
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / total * 100) if total > 0 else 0,
            "avg_duration_seconds": avg_duration,
            "latest_execution": outputs[0].to_dict() if outputs else None,
        }


# Global managers
memory_manager = AgentMemoryManager()
learning_manager = AgentLearningManager()
output_manager = AgentOutputManager()
