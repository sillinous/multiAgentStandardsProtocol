"""
Agent Learning System - Enables Agents to Learn and Improve Autonomously

This module provides a comprehensive learning framework for agents to:
- Learn from experience (success/failure patterns)
- Share knowledge with other agents
- Adapt strategies based on outcomes
- Build collective intelligence
- Self-improve through reinforcement

Features:
- Experience replay and pattern recognition
- Knowledge graph for shared learnings
- Reinforcement learning framework
- Collaborative filtering for best practices
- Meta-learning for strategy adaptation
- Performance-based optimization

Version: 1.0.0
Date: 2025-10-18
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import numpy as np
from collections import defaultdict, deque
import hashlib


class ExperienceType(Enum):
    """Types of agent experiences"""

    SUCCESS = "success"
    FAILURE = "failure"
    OPTIMIZATION = "optimization"
    COLLABORATION = "collaboration"
    DISCOVERY = "discovery"


class LearningStrategy(Enum):
    """Learning strategies"""

    REINFORCEMENT = "reinforcement"
    SUPERVISED = "supervised"
    UNSUPERVISED = "unsupervised"
    META_LEARNING = "meta_learning"
    TRANSFER_LEARNING = "transfer_learning"


@dataclass
class Experience:
    """Single experience record"""

    experience_id: str
    agent_id: str
    agent_type: str
    experience_type: str
    timestamp: str
    context: Dict[str, Any]
    action: Dict[str, Any]
    outcome: Dict[str, Any]
    reward: float
    confidence: float = 0.0
    validated: bool = False
    validation_count: int = 0
    metadata: Dict[str, Any] = None


@dataclass
class KnowledgeNode:
    """Node in knowledge graph"""

    node_id: str
    knowledge_type: str  # pattern, rule, strategy, best_practice
    content: Dict[str, Any]
    confidence: float
    source_agents: List[str]
    validation_score: float
    usage_count: int
    created_at: str
    updated_at: str
    tags: List[str]


@dataclass
class LearningGoal:
    """Agent learning objective"""

    goal_id: str
    agent_id: str
    goal_type: str  # performance, efficiency, accuracy, collaboration
    target_metric: str
    current_value: float
    target_value: float
    deadline: Optional[str]
    progress: float
    strategy: str
    status: str  # active, achieved, abandoned


class AgentLearningSystem:
    """
    Comprehensive learning system for autonomous agents

    Enables agents to:
    1. Record and analyze experiences
    2. Learn patterns from successes/failures
    3. Share knowledge with other agents
    4. Adapt strategies based on outcomes
    5. Set and track learning goals
    6. Build collective intelligence

    Usage:
        learning_system = AgentLearningSystem()

        # Record experience
        learning_system.record_experience(
            agent_id="agent_001",
            agent_type="traffic_prediction",
            experience_type=ExperienceType.SUCCESS,
            context={"time": "rush_hour", "location": "downtown"},
            action={"model": "neural_network", "features": [...]},
            outcome={"accuracy": 0.95},
            reward=0.95
        )

        # Get recommendations
        recommendations = learning_system.get_recommendations(
            agent_id="agent_001",
            current_context={"time": "rush_hour"}
        )

        # Share knowledge
        learning_system.share_knowledge(
            from_agent="agent_001",
            knowledge_type="pattern",
            content={"pattern": "rush_hour_prediction"},
            confidence=0.9
        )
    """

    def __init__(self, db_path: Optional[str] = None):
        """Initialize learning system"""
        if db_path is None:
            db_path = str(Path(__file__).parent.parent.parent / "agent_learning.db")

        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._initialize_database()

        # In-memory caches for performance
        self.experience_buffer = deque(maxlen=1000)
        self.knowledge_cache = {}
        self.pattern_cache = {}

    def _initialize_database(self):
        """Create database schema"""
        cursor = self.conn.cursor()

        # Experiences table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS experiences (
                experience_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                agent_type TEXT NOT NULL,
                experience_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                context_json TEXT NOT NULL,
                action_json TEXT NOT NULL,
                outcome_json TEXT NOT NULL,
                reward REAL NOT NULL,
                confidence REAL DEFAULT 0.0,
                validated BOOLEAN DEFAULT 0,
                validation_count INTEGER DEFAULT 0,
                metadata_json TEXT,
                created_at TEXT NOT NULL
            )
        """
        )

        # Knowledge graph table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS knowledge_graph (
                node_id TEXT PRIMARY KEY,
                knowledge_type TEXT NOT NULL,
                content_json TEXT NOT NULL,
                confidence REAL NOT NULL,
                source_agents_json TEXT NOT NULL,
                validation_score REAL DEFAULT 0.0,
                usage_count INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                tags_json TEXT
            )
        """
        )

        # Learning goals table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS learning_goals (
                goal_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                goal_type TEXT NOT NULL,
                target_metric TEXT NOT NULL,
                current_value REAL NOT NULL,
                target_value REAL NOT NULL,
                deadline TEXT,
                progress REAL DEFAULT 0.0,
                strategy TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """
        )

        # Patterns table (learned patterns)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS learned_patterns (
                pattern_id TEXT PRIMARY KEY,
                pattern_type TEXT NOT NULL,
                pattern_data_json TEXT NOT NULL,
                confidence REAL NOT NULL,
                support_count INTEGER DEFAULT 0,
                discovered_by TEXT NOT NULL,
                validated_by_json TEXT,
                created_at TEXT NOT NULL,
                last_validated TEXT
            )
        """
        )

        # Agent performance tracking
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS agent_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                timestamp TEXT NOT NULL,
                context_json TEXT
            )
        """
        )

        # Knowledge transfer log
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS knowledge_transfers (
                transfer_id TEXT PRIMARY KEY,
                from_agent_id TEXT NOT NULL,
                to_agent_id TEXT,
                knowledge_node_id TEXT NOT NULL,
                transfer_type TEXT NOT NULL,
                success BOOLEAN DEFAULT 0,
                feedback_json TEXT,
                transferred_at TEXT NOT NULL
            )
        """
        )

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_experiences_agent ON experiences(agent_id)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_experiences_type ON experiences(experience_type)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_experiences_timestamp ON experiences(timestamp)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_knowledge_type ON knowledge_graph(knowledge_type)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_patterns_type ON learned_patterns(pattern_type)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_performance_agent ON agent_performance(agent_id)"
        )

        self.conn.commit()

    def record_experience(
        self,
        agent_id: str,
        agent_type: str,
        experience_type: ExperienceType,
        context: Dict[str, Any],
        action: Dict[str, Any],
        outcome: Dict[str, Any],
        reward: float,
        confidence: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Record an agent experience for learning

        Args:
            agent_id: Unique agent identifier
            agent_type: Type of agent
            experience_type: Type of experience
            context: Contextual information when action was taken
            action: Action that was performed
            outcome: Result of the action
            reward: Reward signal (-1.0 to 1.0)
            confidence: Agent's confidence in the action
            metadata: Additional metadata

        Returns:
            experience_id
        """
        timestamp = datetime.now().isoformat()
        experience_id = self._generate_experience_id(agent_id, timestamp)

        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO experiences (
                experience_id, agent_id, agent_type, experience_type,
                timestamp, context_json, action_json, outcome_json,
                reward, confidence, metadata_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                experience_id,
                agent_id,
                agent_type,
                experience_type.value,
                timestamp,
                json.dumps(context),
                json.dumps(action),
                json.dumps(outcome),
                reward,
                confidence,
                json.dumps(metadata or {}),
                timestamp,
            ),
        )

        self.conn.commit()

        # Add to buffer for quick access
        self.experience_buffer.append(
            {
                "experience_id": experience_id,
                "agent_id": agent_id,
                "agent_type": agent_type,
                "timestamp": timestamp,
                "reward": reward,
            }
        )

        # Trigger pattern learning if enough experiences
        if len(self.experience_buffer) >= 50:
            self._discover_patterns_async(agent_id)

        return experience_id

    def get_recommendations(
        self, agent_id: str, current_context: Dict[str, Any], top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get action recommendations based on learned experiences

        Args:
            agent_id: Agent requesting recommendations
            current_context: Current situation context
            top_k: Number of top recommendations to return

        Returns:
            List of recommended actions with confidence scores
        """
        cursor = self.conn.cursor()

        # Get similar past experiences
        cursor.execute(
            """
            SELECT experience_id, context_json, action_json, outcome_json, reward, confidence
            FROM experiences
            WHERE agent_id = ? AND experience_type = ?
            ORDER BY timestamp DESC
            LIMIT 100
        """,
            (agent_id, ExperienceType.SUCCESS.value),
        )

        experiences = cursor.fetchall()

        # Score experiences by context similarity
        scored_actions = []
        for exp in experiences:
            exp_context = json.loads(exp["context_json"])
            similarity = self._calculate_context_similarity(current_context, exp_context)

            if similarity > 0.3:  # Threshold for relevance
                action = json.loads(exp["action_json"])
                scored_actions.append(
                    {
                        "action": action,
                        "confidence": similarity * exp["reward"] * (exp["confidence"] + 1) / 2,
                        "context_similarity": similarity,
                        "past_reward": exp["reward"],
                        "source_experience": exp["experience_id"],
                    }
                )

        # Sort by confidence and return top-k
        scored_actions.sort(key=lambda x: x["confidence"], reverse=True)
        return scored_actions[:top_k]

    def share_knowledge(
        self,
        from_agent: str,
        knowledge_type: str,
        content: Dict[str, Any],
        confidence: float,
        tags: Optional[List[str]] = None,
        target_agents: Optional[List[str]] = None,
    ) -> str:
        """
        Share knowledge across agents

        Args:
            from_agent: Agent sharing knowledge
            knowledge_type: Type of knowledge (pattern, rule, strategy, best_practice)
            content: Knowledge content
            confidence: Confidence in this knowledge
            tags: Tags for categorization
            target_agents: Specific agents to share with (None = all)

        Returns:
            node_id of created knowledge node
        """
        timestamp = datetime.now().isoformat()
        node_id = self._generate_knowledge_id(from_agent, knowledge_type, timestamp)

        cursor = self.conn.cursor()

        # Create knowledge node
        cursor.execute(
            """
            INSERT OR REPLACE INTO knowledge_graph (
                node_id, knowledge_type, content_json, confidence,
                source_agents_json, validation_score, usage_count,
                created_at, updated_at, tags_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                node_id,
                knowledge_type,
                json.dumps(content),
                confidence,
                json.dumps([from_agent]),
                0.0,
                0,
                timestamp,
                timestamp,
                json.dumps(tags or []),
            ),
        )

        # Log knowledge transfers
        if target_agents:
            for target in target_agents:
                transfer_id = (
                    f"transfer_{node_id}_{target}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                )
                cursor.execute(
                    """
                    INSERT INTO knowledge_transfers (
                        transfer_id, from_agent_id, to_agent_id,
                        knowledge_node_id, transfer_type, transferred_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (transfer_id, from_agent, target, node_id, "direct", timestamp),
                )
        else:
            # Broadcast to all agents
            transfer_id = f"transfer_{node_id}_broadcast_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            cursor.execute(
                """
                INSERT INTO knowledge_transfers (
                    transfer_id, from_agent_id, to_agent_id,
                    knowledge_node_id, transfer_type, transferred_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """,
                (transfer_id, from_agent, None, node_id, "broadcast", timestamp),
            )

        self.conn.commit()

        # Update cache
        self.knowledge_cache[node_id] = {
            "type": knowledge_type,
            "content": content,
            "confidence": confidence,
        }

        return node_id

    def get_shared_knowledge(
        self,
        agent_id: str,
        knowledge_type: Optional[str] = None,
        min_confidence: float = 0.5,
        tags: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve shared knowledge relevant to agent

        Args:
            agent_id: Agent requesting knowledge
            knowledge_type: Filter by knowledge type
            min_confidence: Minimum confidence threshold
            tags: Filter by tags

        Returns:
            List of knowledge nodes
        """
        cursor = self.conn.cursor()

        query = """
            SELECT k.*, t.transferred_at
            FROM knowledge_graph k
            LEFT JOIN knowledge_transfers t ON k.node_id = t.knowledge_node_id
            WHERE k.confidence >= ?
                AND (t.to_agent_id = ? OR t.to_agent_id IS NULL)
        """
        params = [min_confidence, agent_id]

        if knowledge_type:
            query += " AND k.knowledge_type = ?"
            params.append(knowledge_type)

        query += " ORDER BY k.confidence DESC, k.usage_count DESC LIMIT 50"

        cursor.execute(query, params)
        results = cursor.fetchall()

        knowledge_list = []
        for row in results:
            knowledge = {
                "node_id": row["node_id"],
                "knowledge_type": row["knowledge_type"],
                "content": json.loads(row["content_json"]),
                "confidence": row["confidence"],
                "source_agents": json.loads(row["source_agents_json"]),
                "validation_score": row["validation_score"],
                "usage_count": row["usage_count"],
                "tags": json.loads(row["tags_json"]) if row["tags_json"] else [],
            }

            # Filter by tags if specified
            if tags:
                if any(tag in knowledge["tags"] for tag in tags):
                    knowledge_list.append(knowledge)
            else:
                knowledge_list.append(knowledge)

        return knowledge_list

    def set_learning_goal(
        self,
        agent_id: str,
        goal_type: str,
        target_metric: str,
        current_value: float,
        target_value: float,
        strategy: str,
        deadline: Optional[str] = None,
    ) -> str:
        """
        Set a learning goal for an agent

        Args:
            agent_id: Agent setting the goal
            goal_type: Type of goal (performance, efficiency, accuracy, collaboration)
            target_metric: Metric to improve
            current_value: Current metric value
            target_value: Target metric value
            strategy: Learning strategy to use
            deadline: Optional deadline

        Returns:
            goal_id
        """
        timestamp = datetime.now().isoformat()
        goal_id = f"goal_{agent_id}_{target_metric}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO learning_goals (
                goal_id, agent_id, goal_type, target_metric,
                current_value, target_value, deadline, progress,
                strategy, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                goal_id,
                agent_id,
                goal_type,
                target_metric,
                current_value,
                target_value,
                deadline,
                0.0,
                strategy,
                "active",
                timestamp,
                timestamp,
            ),
        )

        self.conn.commit()
        return goal_id

    def update_goal_progress(self, goal_id: str, new_value: float) -> Dict[str, Any]:
        """
        Update progress on a learning goal

        Args:
            goal_id: Goal to update
            new_value: New metric value

        Returns:
            Updated goal status
        """
        cursor = self.conn.cursor()

        # Get current goal
        cursor.execute("SELECT * FROM learning_goals WHERE goal_id = ?", (goal_id,))
        goal = cursor.fetchone()

        if not goal:
            raise ValueError(f"Goal {goal_id} not found")

        # Calculate progress
        current = goal["current_value"]
        target = goal["target_value"]
        progress = (new_value - current) / (target - current) if target != current else 1.0
        progress = max(0.0, min(1.0, progress))

        # Update status
        status = "achieved" if progress >= 1.0 else "active"

        cursor.execute(
            """
            UPDATE learning_goals
            SET current_value = ?, progress = ?, status = ?, updated_at = ?
            WHERE goal_id = ?
        """,
            (new_value, progress, status, datetime.now().isoformat(), goal_id),
        )

        self.conn.commit()

        return {
            "goal_id": goal_id,
            "progress": progress,
            "status": status,
            "current_value": new_value,
            "target_value": target,
        }

    def discover_patterns(
        self,
        agent_id: Optional[str] = None,
        experience_type: Optional[ExperienceType] = None,
        min_support: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Discover patterns from experiences

        Args:
            agent_id: Limit to specific agent (None = all)
            experience_type: Filter by experience type
            min_support: Minimum number of supporting experiences

        Returns:
            List of discovered patterns
        """
        cursor = self.conn.cursor()

        # Get experiences
        query = "SELECT * FROM experiences WHERE 1=1"
        params = []

        if agent_id:
            query += " AND agent_id = ?"
            params.append(agent_id)

        if experience_type:
            query += " AND experience_type = ?"
            params.append(experience_type.value)

        query += " ORDER BY timestamp DESC LIMIT 500"

        cursor.execute(query, params)
        experiences = cursor.fetchall()

        # Group by context patterns
        pattern_groups = defaultdict(list)

        for exp in experiences:
            context = json.loads(exp["context_json"])
            pattern_key = self._extract_pattern_key(context)
            pattern_groups[pattern_key].append(
                {
                    "action": json.loads(exp["action_json"]),
                    "outcome": json.loads(exp["outcome_json"]),
                    "reward": exp["reward"],
                }
            )

        # Identify significant patterns
        patterns = []
        for pattern_key, group in pattern_groups.items():
            if len(group) >= min_support:
                avg_reward = np.mean([item["reward"] for item in group])

                if avg_reward > 0.5:  # Positive pattern
                    pattern = {
                        "pattern_key": pattern_key,
                        "support_count": len(group),
                        "average_reward": float(avg_reward),
                        "confidence": float(min(len(group) / 10, 1.0)),
                        "type": "success_pattern",
                        "discovered_at": datetime.now().isoformat(),
                    }
                    patterns.append(pattern)

                    # Save pattern
                    pattern_id = f"pattern_{hashlib.md5(pattern_key.encode()).hexdigest()[:8]}"
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO learned_patterns (
                            pattern_id, pattern_type, pattern_data_json,
                            confidence, support_count, discovered_by, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            pattern_id,
                            "success_pattern",
                            json.dumps(pattern),
                            pattern["confidence"],
                            len(group),
                            agent_id or "system",
                            datetime.now().isoformat(),
                        ),
                    )

        self.conn.commit()
        return patterns

    def get_agent_performance_trend(
        self, agent_id: str, metric_name: str, days: int = 7
    ) -> Dict[str, Any]:
        """
        Get performance trend for an agent

        Args:
            agent_id: Agent to analyze
            metric_name: Metric to track
            days: Number of days to analyze

        Returns:
            Performance trend data
        """
        cursor = self.conn.cursor()

        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        cursor.execute(
            """
            SELECT metric_value, timestamp
            FROM agent_performance
            WHERE agent_id = ? AND metric_name = ? AND timestamp >= ?
            ORDER BY timestamp ASC
        """,
            (agent_id, metric_name, cutoff_date),
        )

        data_points = cursor.fetchall()

        if not data_points:
            return {"trend": "no_data", "values": []}

        values = [row["metric_value"] for row in data_points]

        # Calculate trend
        if len(values) >= 2:
            first_half_avg = np.mean(values[: len(values) // 2])
            second_half_avg = np.mean(values[len(values) // 2 :])

            if second_half_avg > first_half_avg * 1.05:
                trend = "improving"
            elif second_half_avg < first_half_avg * 0.95:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"

        return {
            "trend": trend,
            "values": values,
            "average": float(np.mean(values)),
            "recent_average": float(np.mean(values[-min(10, len(values)) :])),
            "data_points": len(values),
        }

    def _calculate_context_similarity(
        self, context1: Dict[str, Any], context2: Dict[str, Any]
    ) -> float:
        """Calculate similarity between two contexts"""
        # Simple Jaccard similarity on keys and values
        set1 = set(f"{k}:{v}" for k, v in context1.items())
        set2 = set(f"{k}:{v}" for k, v in context2.items())

        if not set1 and not set2:
            return 1.0
        if not set1 or not set2:
            return 0.0

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0

    def _extract_pattern_key(self, context: Dict[str, Any]) -> str:
        """Extract pattern key from context"""
        # Create a normalized key from context
        sorted_items = sorted(context.items())
        return "|".join(f"{k}:{v}" for k, v in sorted_items)

    def _generate_experience_id(self, agent_id: str, timestamp: str) -> str:
        """Generate unique experience ID"""
        data = f"{agent_id}_{timestamp}".encode()
        return f"exp_{hashlib.md5(data).hexdigest()[:12]}"

    def _generate_knowledge_id(self, agent_id: str, knowledge_type: str, timestamp: str) -> str:
        """Generate unique knowledge node ID"""
        data = f"{agent_id}_{knowledge_type}_{timestamp}".encode()
        return f"knowledge_{hashlib.md5(data).hexdigest()[:12]}"

    def _discover_patterns_async(self, agent_id: str):
        """Asynchronously discover patterns (placeholder for async implementation)"""
        # In production, this would trigger background pattern discovery
        pass

    def get_statistics(self) -> Dict[str, Any]:
        """Get learning system statistics"""
        cursor = self.conn.cursor()

        stats = {}

        # Total experiences
        cursor.execute("SELECT COUNT(*) FROM experiences")
        stats["total_experiences"] = cursor.fetchone()[0]

        # Experiences by type
        cursor.execute(
            """
            SELECT experience_type, COUNT(*) as count
            FROM experiences
            GROUP BY experience_type
        """
        )
        stats["by_type"] = {row[0]: row[1] for row in cursor.fetchall()}

        # Knowledge nodes
        cursor.execute("SELECT COUNT(*) FROM knowledge_graph")
        stats["knowledge_nodes"] = cursor.fetchone()[0]

        # Learned patterns
        cursor.execute("SELECT COUNT(*) FROM learned_patterns")
        stats["learned_patterns"] = cursor.fetchone()[0]

        # Active learning goals
        cursor.execute("SELECT COUNT(*) FROM learning_goals WHERE status = 'active'")
        stats["active_learning_goals"] = cursor.fetchone()[0]

        # Knowledge transfers
        cursor.execute("SELECT COUNT(*) FROM knowledge_transfers")
        stats["knowledge_transfers"] = cursor.fetchone()[0]

        return stats

    def close(self):
        """Close database connection"""
        self.conn.close()


# Singleton instance
_learning_system_instance = None


def get_learning_system(db_path: Optional[str] = None) -> AgentLearningSystem:
    """Get or create learning system singleton"""
    global _learning_system_instance
    if _learning_system_instance is None:
        _learning_system_instance = AgentLearningSystem(db_path)
    return _learning_system_instance
