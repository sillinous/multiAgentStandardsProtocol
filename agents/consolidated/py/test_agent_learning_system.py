"""
Unit Tests for Agent Learning System

Tests all major functionality:
- Experience recording and retrieval
- Knowledge sharing and retrieval
- Recommendation engine
- Learning goals tracking
- Pattern discovery
- Performance trends

Version: 1.0.0
Date: 2025-10-18
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from library.core.agent_learning_system import (
    AgentLearningSystem,
    ExperienceType,
    LearningStrategy,
    Experience,
    KnowledgeNode,
    LearningGoal,
)


@pytest.fixture
def temp_db():
    """Create temporary database for testing"""
    fd, path = tempfile.mkstemp(suffix=".db")
    yield path
    os.close(fd)
    os.unlink(path)


@pytest.fixture
def learning_system(temp_db):
    """Create learning system instance for testing"""
    system = AgentLearningSystem(db_path=temp_db)
    yield system
    system.close()


class TestExperienceRecording:
    """Test experience recording functionality"""

    def test_record_success_experience(self, learning_system):
        """Test recording a successful experience"""
        experience_id = learning_system.record_experience(
            agent_id="test_agent_001",
            agent_type="test_type",
            experience_type=ExperienceType.SUCCESS,
            context={"scenario": "test", "time": "morning"},
            action={"method": "optimize", "param": 0.5},
            outcome={"result": "success", "metric": 0.95},
            reward=0.9,
            confidence=0.85,
        )

        assert experience_id is not None
        assert experience_id.startswith("exp_")

        # Verify it's in the database
        cursor = learning_system.conn.cursor()
        cursor.execute("SELECT * FROM experiences WHERE experience_id = ?", (experience_id,))
        row = cursor.fetchone()

        assert row is not None
        assert row["agent_id"] == "test_agent_001"
        assert row["experience_type"] == ExperienceType.SUCCESS.value
        assert row["reward"] == 0.9

    def test_record_failure_experience(self, learning_system):
        """Test recording a failure experience"""
        experience_id = learning_system.record_experience(
            agent_id="test_agent_002",
            agent_type="test_type",
            experience_type=ExperienceType.FAILURE,
            context={"scenario": "edge_case"},
            action={"method": "default"},
            outcome={"error": "timeout"},
            reward=-0.5,
            confidence=0.9,
        )

        assert experience_id is not None

        cursor = learning_system.conn.cursor()
        cursor.execute("SELECT * FROM experiences WHERE experience_id = ?", (experience_id,))
        row = cursor.fetchone()

        assert row["experience_type"] == ExperienceType.FAILURE.value
        assert row["reward"] == -0.5

    def test_record_multiple_experiences(self, learning_system):
        """Test recording multiple experiences"""
        agent_id = "test_agent_003"
        experience_ids = []

        for i in range(10):
            exp_id = learning_system.record_experience(
                agent_id=agent_id,
                agent_type="test_type",
                experience_type=ExperienceType.SUCCESS if i % 2 == 0 else ExperienceType.FAILURE,
                context={"iteration": i},
                action={"step": i},
                outcome={"score": i * 0.1},
                reward=i * 0.1,
                confidence=0.8,
            )
            experience_ids.append(exp_id)

        # Verify count
        cursor = learning_system.conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM experiences WHERE agent_id = ?", (agent_id,))
        count = cursor.fetchone()["count"]

        assert count == 10
        assert len(set(experience_ids)) == 10  # All unique


class TestKnowledgeSharing:
    """Test knowledge sharing functionality"""

    def test_share_knowledge(self, learning_system):
        """Test sharing knowledge with network"""
        node_id = learning_system.share_knowledge(
            from_agent="agent_001",
            knowledge_type="pattern",
            content={"pattern_name": "rush_hour_optimization", "details": "use_cache"},
            confidence=0.9,
            tags=["performance", "caching"],
        )

        assert node_id is not None
        assert node_id.startswith("knowledge_")

        # Verify in database
        cursor = learning_system.conn.cursor()
        cursor.execute("SELECT * FROM knowledge_graph WHERE node_id = ?", (node_id,))
        row = cursor.fetchone()

        assert row is not None
        assert row["knowledge_type"] == "pattern"
        assert row["confidence"] == 0.9

    def test_get_shared_knowledge(self, learning_system):
        """Test retrieving shared knowledge"""
        # Share some knowledge
        learning_system.share_knowledge(
            from_agent="agent_001",
            knowledge_type="best_practice",
            content={"practice": "validate_input"},
            confidence=0.95,
            tags=["validation"],
        )

        learning_system.share_knowledge(
            from_agent="agent_002",
            knowledge_type="best_practice",
            content={"practice": "error_handling"},
            confidence=0.85,
            tags=["error_handling"],
        )

        # Retrieve knowledge
        knowledge = learning_system.get_shared_knowledge(
            agent_id="agent_003", knowledge_type="best_practice", min_confidence=0.8
        )

        assert len(knowledge) == 2
        assert all(k["knowledge_type"] == "best_practice" for k in knowledge)
        assert all(k["confidence"] >= 0.8 for k in knowledge)

    def test_knowledge_filtering_by_confidence(self, learning_system):
        """Test filtering knowledge by confidence threshold"""
        learning_system.share_knowledge(
            from_agent="agent_001",
            knowledge_type="rule",
            content={"rule": "low_confidence"},
            confidence=0.5,
        )

        learning_system.share_knowledge(
            from_agent="agent_001",
            knowledge_type="rule",
            content={"rule": "high_confidence"},
            confidence=0.95,
        )

        # Get only high confidence
        knowledge = learning_system.get_shared_knowledge(agent_id="agent_002", min_confidence=0.9)

        assert len(knowledge) == 1
        assert knowledge[0]["content"]["rule"] == "high_confidence"


class TestRecommendationEngine:
    """Test recommendation engine"""

    def test_get_recommendations_no_history(self, learning_system):
        """Test getting recommendations with no history"""
        recommendations = learning_system.get_recommendations(
            agent_id="new_agent", current_context={"time": "morning"}, top_k=5
        )

        assert recommendations == []

    def test_get_recommendations_with_history(self, learning_system):
        """Test getting recommendations based on past experiences"""
        agent_id = "agent_rec_001"

        # Record some successful experiences
        for i in range(5):
            learning_system.record_experience(
                agent_id=agent_id,
                agent_type="test",
                experience_type=ExperienceType.SUCCESS,
                context={"time": "morning", "load": "high"},
                action={"strategy": "cache", "param": i},
                outcome={"success": True},
                reward=0.9,
                confidence=0.85,
            )

        # Get recommendations
        recommendations = learning_system.get_recommendations(
            agent_id=agent_id, current_context={"time": "morning", "load": "high"}, top_k=3
        )

        assert len(recommendations) > 0
        assert len(recommendations) <= 3
        assert all("confidence" in r for r in recommendations)
        assert all("action" in r for r in recommendations)

    def test_recommendations_sorted_by_confidence(self, learning_system):
        """Test that recommendations are sorted by confidence"""
        agent_id = "agent_rec_002"

        # Record experiences with different rewards
        for i, reward in enumerate([0.5, 0.9, 0.7]):
            learning_system.record_experience(
                agent_id=agent_id,
                agent_type="test",
                experience_type=ExperienceType.SUCCESS,
                context={"scenario": "test"},
                action={"option": i},
                outcome={"score": reward},
                reward=reward,
                confidence=0.8,
            )

        recommendations = learning_system.get_recommendations(
            agent_id=agent_id, current_context={"scenario": "test"}, top_k=3
        )

        # Should be sorted by confidence (descending)
        for i in range(len(recommendations) - 1):
            assert recommendations[i]["confidence"] >= recommendations[i + 1]["confidence"]


class TestLearningGoals:
    """Test learning goals functionality"""

    def test_set_learning_goal(self, learning_system):
        """Test setting a learning goal"""
        goal_id = learning_system.set_learning_goal(
            agent_id="agent_goal_001",
            goal_type="performance",
            target_metric="response_time",
            current_value=500.0,
            target_value=300.0,
            strategy=LearningStrategy.REINFORCEMENT.value,
        )

        assert goal_id is not None
        assert goal_id.startswith("goal_")

        # Verify in database
        cursor = learning_system.conn.cursor()
        cursor.execute("SELECT * FROM learning_goals WHERE goal_id = ?", (goal_id,))
        row = cursor.fetchone()

        assert row is not None
        assert row["target_metric"] == "response_time"
        assert row["current_value"] == 500.0
        assert row["target_value"] == 300.0
        assert row["status"] == "active"

    def test_update_goal_progress(self, learning_system):
        """Test updating learning goal progress"""
        goal_id = learning_system.set_learning_goal(
            agent_id="agent_goal_002",
            goal_type="accuracy",
            target_metric="prediction_accuracy",
            current_value=0.7,
            target_value=0.9,
            strategy=LearningStrategy.SUPERVISED.value,
        )

        # Update progress
        result = learning_system.update_goal_progress(goal_id=goal_id, new_value=0.8)

        assert result["progress"] == pytest.approx(0.5, rel=0.01)  # 50% progress
        assert result["status"] == "active"

        # Update to achieve goal
        result = learning_system.update_goal_progress(goal_id=goal_id, new_value=0.9)

        assert result["progress"] == pytest.approx(1.0, rel=0.01)
        assert result["status"] == "achieved"

    def test_goal_progress_calculation(self, learning_system):
        """Test goal progress calculation logic"""
        goal_id = learning_system.set_learning_goal(
            agent_id="agent_goal_003",
            goal_type="efficiency",
            target_metric="cost",
            current_value=100.0,
            target_value=50.0,
            strategy=LearningStrategy.REINFORCEMENT.value,
        )

        # 75% progress (100 -> 50, now at 62.5)
        result = learning_system.update_goal_progress(goal_id, 62.5)
        assert result["progress"] == pytest.approx(0.75, rel=0.01)


class TestPatternDiscovery:
    """Test pattern discovery functionality"""

    def test_discover_patterns_insufficient_data(self, learning_system):
        """Test pattern discovery with insufficient data"""
        patterns = learning_system.discover_patterns(agent_id="agent_pattern_001", min_support=3)

        assert patterns == []

    def test_discover_patterns_with_sufficient_data(self, learning_system):
        """Test discovering patterns from experiences"""
        agent_id = "agent_pattern_002"

        # Create repeating pattern
        for i in range(10):
            learning_system.record_experience(
                agent_id=agent_id,
                agent_type="test",
                experience_type=ExperienceType.SUCCESS,
                context={"time": "morning", "type": "A"},
                action={"strategy": "cache"},
                outcome={"success": True},
                reward=0.9,
                confidence=0.8,
            )

        patterns = learning_system.discover_patterns(agent_id=agent_id, min_support=3)

        assert len(patterns) > 0
        assert all(p["support_count"] >= 3 for p in patterns)
        assert all(p["average_reward"] > 0.5 for p in patterns)

    def test_pattern_confidence_scoring(self, learning_system):
        """Test pattern confidence scoring"""
        agent_id = "agent_pattern_003"

        # Create strong pattern (10 occurrences)
        for i in range(10):
            learning_system.record_experience(
                agent_id=agent_id,
                agent_type="test",
                experience_type=ExperienceType.SUCCESS,
                context={"scenario": "strong_pattern"},
                action={"method": "A"},
                outcome={"success": True},
                reward=0.95,
                confidence=0.9,
            )

        patterns = learning_system.discover_patterns(agent_id=agent_id, min_support=5)

        assert len(patterns) > 0
        # Higher support should lead to higher confidence (capped at 1.0)
        assert patterns[0]["confidence"] > 0.5


class TestPerformanceTrends:
    """Test performance trend analysis"""

    def test_get_performance_trend_no_data(self, learning_system):
        """Test getting performance trend with no data"""
        trend = learning_system.get_agent_performance_trend(
            agent_id="agent_perf_001", metric_name="execution_time", days=7
        )

        assert trend["trend"] == "no_data"
        assert trend["values"] == []

    def test_get_performance_trend_improving(self, learning_system):
        """Test detecting improving performance trend"""
        agent_id = "agent_perf_002"
        cursor = learning_system.conn.cursor()

        # Insert declining execution times (improving)
        base_time = datetime.now()
        for i in range(20):
            timestamp = (base_time - timedelta(days=19 - i)).isoformat()
            # Values: 500, 490, 480, ... 310 (improving)
            value = 500 - (i * 10)

            cursor.execute(
                """
                INSERT INTO agent_performance (agent_id, metric_name, metric_value, timestamp)
                VALUES (?, ?, ?, ?)
            """,
                (agent_id, "execution_time", value, timestamp),
            )

        learning_system.conn.commit()

        trend = learning_system.get_agent_performance_trend(
            agent_id=agent_id, metric_name="execution_time", days=20
        )

        assert trend["trend"] == "improving"
        assert len(trend["values"]) == 20
        assert trend["recent_average"] < trend["average"]  # Recent should be better

    def test_get_performance_trend_declining(self, learning_system):
        """Test detecting declining performance trend"""
        agent_id = "agent_perf_003"
        cursor = learning_system.conn.cursor()

        base_time = datetime.now()
        for i in range(20):
            timestamp = (base_time - timedelta(days=19 - i)).isoformat()
            # Values increasing (declining performance)
            value = 300 + (i * 10)

            cursor.execute(
                """
                INSERT INTO agent_performance (agent_id, metric_name, metric_value, timestamp)
                VALUES (?, ?, ?, ?)
            """,
                (agent_id, "execution_time", value, timestamp),
            )

        learning_system.conn.commit()

        trend = learning_system.get_agent_performance_trend(
            agent_id=agent_id, metric_name="execution_time", days=20
        )

        assert trend["trend"] == "declining"


class TestStatistics:
    """Test statistics gathering"""

    def test_get_statistics_empty(self, learning_system):
        """Test getting statistics from empty system"""
        stats = learning_system.get_statistics()

        assert stats["total_experiences"] == 0
        assert stats["knowledge_nodes"] == 0
        assert stats["learned_patterns"] == 0
        assert stats["active_learning_goals"] == 0
        assert stats["knowledge_transfers"] == 0

    def test_get_statistics_with_data(self, learning_system):
        """Test getting statistics with data"""
        # Add some experiences
        for i in range(10):
            learning_system.record_experience(
                agent_id=f"agent_{i}",
                agent_type="test",
                experience_type=ExperienceType.SUCCESS if i % 2 == 0 else ExperienceType.FAILURE,
                context={"i": i},
                action={"a": i},
                outcome={"o": i},
                reward=0.5,
            )

        # Share some knowledge
        for i in range(5):
            learning_system.share_knowledge(
                from_agent=f"agent_{i}", knowledge_type="pattern", content={"p": i}, confidence=0.8
            )

        # Set some goals
        for i in range(3):
            learning_system.set_learning_goal(
                agent_id=f"agent_{i}",
                goal_type="performance",
                target_metric="metric",
                current_value=0.5,
                target_value=0.9,
                strategy="reinforcement",
            )

        stats = learning_system.get_statistics()

        assert stats["total_experiences"] == 10
        assert stats["by_type"]["success"] == 5
        assert stats["by_type"]["failure"] == 5
        assert stats["knowledge_nodes"] == 5
        assert stats["active_learning_goals"] == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
