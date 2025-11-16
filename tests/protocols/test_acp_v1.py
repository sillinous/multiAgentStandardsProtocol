"""
Unit Tests for Agent Coordination Protocol (ACP) v1.0

Comprehensive test coverage including:
- Coordination creation (all 6 patterns: swarm, pipeline, hierarchical, consensus, auction, collaborative)
- Coordination lifecycle (start, pause, complete)
- Participant join/leave
- Task creation and assignment
- Task status updates
- Dependency management
- Shared state synchronization
- Progress tracking
- Available tasks query
"""

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime
from dataclasses import asdict

from superstandard.protocols.acp_implementation import (
    # Data models
    CoordinationType,
    CoordinationStatus,
    TaskStatus,
    Task,
    Participant,
    ACPCoordination,
    CoordinationMessage,

    # Core classes
    CoordinationManager,
    ACPClient,
)


@pytest_asyncio.fixture
async def manager():
    """Create a test coordination manager."""
    return CoordinationManager()


@pytest_asyncio.fixture
async def coordinator_client(manager):
    """Create a coordinator client."""
    return ACPClient(manager, "coordinator-agent")


@pytest_asyncio.fixture
async def worker_client1(manager):
    """Create a worker client."""
    return ACPClient(manager, "worker-1")


@pytest_asyncio.fixture
async def worker_client2(manager):
    """Create a worker client."""
    return ACPClient(manager, "worker-2")


@pytest_asyncio.fixture
async def sample_coordination(manager):
    """Create a sample coordination."""
    result = await manager.create_coordination(
        coordinator_id="test-coordinator",
        coordination_type=CoordinationType.SWARM.value,
        goal="Test coordination goal",
        coordination_plan={"strategy": "test"}
    )
    return result["coordination_id"]


# ============================================================================
# COORDINATION CREATION TESTS
# ============================================================================


@pytest.mark.unit
@pytest.mark.protocol
class TestCoordinationCreation:
    """Test coordination creation for all patterns."""

    @pytest.mark.asyncio
    async def test_create_swarm_coordination(self, manager):
        """Test creating swarm coordination."""
        result = await manager.create_coordination(
            coordinator_id="coord-1",
            coordination_type=CoordinationType.SWARM.value,
            goal="Process data in parallel"
        )

        assert result["success"] is True
        assert "coordination_id" in result
        assert result["coordination"]["coordination_type"] == CoordinationType.SWARM.value
        assert result["coordination"]["goal"] == "Process data in parallel"

    @pytest.mark.asyncio
    async def test_create_pipeline_coordination(self, manager):
        """Test creating pipeline coordination."""
        result = await manager.create_coordination(
            coordinator_id="coord-1",
            coordination_type=CoordinationType.PIPELINE.value,
            goal="Sequential data processing"
        )

        assert result["success"] is True
        assert result["coordination"]["coordination_type"] == CoordinationType.PIPELINE.value

    @pytest.mark.asyncio
    async def test_create_hierarchical_coordination(self, manager):
        """Test creating hierarchical coordination."""
        result = await manager.create_coordination(
            coordinator_id="coord-1",
            coordination_type=CoordinationType.HIERARCHICAL.value,
            goal="Delegated task execution"
        )

        assert result["success"] is True
        assert result["coordination"]["coordination_type"] == CoordinationType.HIERARCHICAL.value

    @pytest.mark.asyncio
    async def test_create_consensus_coordination(self, manager):
        """Test creating consensus coordination."""
        result = await manager.create_coordination(
            coordinator_id="coord-1",
            coordination_type=CoordinationType.CONSENSUS.value,
            goal="Reach agreement on decision"
        )

        assert result["success"] is True
        assert result["coordination"]["coordination_type"] == CoordinationType.CONSENSUS.value

    @pytest.mark.asyncio
    async def test_create_auction_coordination(self, manager):
        """Test creating auction coordination."""
        result = await manager.create_coordination(
            coordinator_id="coord-1",
            coordination_type=CoordinationType.AUCTION.value,
            goal="Bid for task execution"
        )

        assert result["success"] is True
        assert result["coordination"]["coordination_type"] == CoordinationType.AUCTION.value

    @pytest.mark.asyncio
    async def test_create_collaborative_coordination(self, manager):
        """Test creating collaborative coordination."""
        result = await manager.create_coordination(
            coordinator_id="coord-1",
            coordination_type=CoordinationType.COLLABORATIVE.value,
            goal="Work together on complex problem"
        )

        assert result["success"] is True
        assert result["coordination"]["coordination_type"] == CoordinationType.COLLABORATIVE.value

    @pytest.mark.asyncio
    async def test_create_coordination_with_plan(self, manager):
        """Test creating coordination with custom plan."""
        plan = {
            "strategy": "divide_and_conquer",
            "parallelism": 4,
            "timeout": 3600
        }

        result = await manager.create_coordination(
            coordinator_id="coord-1",
            coordination_type=CoordinationType.SWARM.value,
            goal="Test goal",
            coordination_plan=plan
        )

        assert result["success"] is True
        assert result["coordination"]["coordination_plan"]["strategy"] == "divide_and_conquer"

    @pytest.mark.asyncio
    async def test_create_coordination_with_metadata(self, manager):
        """Test creating coordination with metadata."""
        metadata = {
            "priority": "high",
            "deadline": "2025-12-31",
            "tags": ["urgent", "production"]
        }

        result = await manager.create_coordination(
            coordinator_id="coord-1",
            coordination_type=CoordinationType.SWARM.value,
            goal="Test goal",
            metadata=metadata
        )

        assert result["success"] is True
        assert result["coordination"]["metadata"]["priority"] == "high"

    @pytest.mark.asyncio
    async def test_coordinator_auto_joins(self, manager):
        """Test that coordinator automatically joins as participant."""
        result = await manager.create_coordination(
            coordinator_id="coord-1",
            coordination_type=CoordinationType.SWARM.value,
            goal="Test goal"
        )

        coord_id = result["coordination_id"]
        coordination = await manager.get_coordination(coord_id)

        assert "coord-1" in coordination["participants"]
        assert coordination["participants"]["coord-1"]["role"] == "coordinator"


# ============================================================================
# COORDINATION LIFECYCLE TESTS
# ============================================================================


@pytest.mark.unit
@pytest.mark.protocol
class TestCoordinationLifecycle:
    """Test coordination lifecycle management."""

    @pytest.mark.asyncio
    async def test_start_coordination(self, manager, sample_coordination):
        """Test starting a coordination."""
        result = await manager.start_coordination(sample_coordination)

        assert result["success"] is True
        coord = await manager.get_coordination(sample_coordination)
        assert coord["status"] == CoordinationStatus.ACTIVE.value

    @pytest.mark.asyncio
    async def test_start_nonexistent_coordination(self, manager):
        """Test starting coordination that doesn't exist."""
        result = await manager.start_coordination("nonexistent-id")
        assert result["success"] is False
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_pause_coordination(self, manager, sample_coordination):
        """Test pausing a coordination."""
        await manager.start_coordination(sample_coordination)
        result = await manager.pause_coordination(sample_coordination)

        assert result["success"] is True
        coord = await manager.get_coordination(sample_coordination)
        assert coord["status"] == CoordinationStatus.PAUSED.value

    @pytest.mark.asyncio
    async def test_complete_coordination(self, manager, sample_coordination):
        """Test completing a coordination."""
        await manager.start_coordination(sample_coordination)
        result = await manager.complete_coordination(sample_coordination)

        assert result["success"] is True
        assert "summary" in result
        coord = await manager.get_coordination(sample_coordination)
        assert coord["status"] == CoordinationStatus.COMPLETED.value
        assert coord["completed_at"] is not None

    @pytest.mark.asyncio
    async def test_complete_coordination_decrements_active_count(self, manager, sample_coordination):
        """Test that completing coordination updates active count."""
        initial_stats = await manager.get_statistics()
        initial_active = initial_stats["stats"]["active_coordinations"]

        await manager.complete_coordination(sample_coordination)

        final_stats = await manager.get_statistics()
        final_active = final_stats["stats"]["active_coordinations"]

        assert final_active == initial_active - 1

    @pytest.mark.asyncio
    async def test_coordination_summary(self, manager, sample_coordination):
        """Test coordination summary generation."""
        # Add some tasks
        await manager.create_task(
            sample_coordination,
            task_type="processing",
            description="Task 1"
        )

        result = await manager.complete_coordination(sample_coordination)
        summary = result["summary"]

        assert summary["coordination_id"] == sample_coordination
        assert summary["goal"] == "Test coordination goal"
        assert summary["total_tasks"] == 1
        assert "duration" in summary


# ============================================================================
# PARTICIPANT MANAGEMENT TESTS
# ============================================================================


@pytest.mark.unit
@pytest.mark.protocol
class TestParticipantManagement:
    """Test participant join/leave functionality."""

    @pytest.mark.asyncio
    async def test_join_coordination(self, manager, sample_coordination):
        """Test agent joining coordination."""
        result = await manager.join_coordination(
            coordination_id=sample_coordination,
            agent_id="worker-1",
            agent_type="analyzer",
            capabilities=["text-analysis", "processing"]
        )

        assert result["success"] is True
        assert result["participant"]["agent_id"] == "worker-1"
        assert "text-analysis" in result["participant"]["capabilities"]

    @pytest.mark.asyncio
    async def test_join_nonexistent_coordination(self, manager):
        """Test joining coordination that doesn't exist."""
        result = await manager.join_coordination(
            coordination_id="nonexistent",
            agent_id="worker-1",
            agent_type="worker",
            capabilities=["test"]
        )

        assert result["success"] is False
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_join_already_joined(self, manager, sample_coordination):
        """Test agent joining coordination twice."""
        await manager.join_coordination(
            sample_coordination, "worker-1", "worker", ["test"]
        )

        result = await manager.join_coordination(
            sample_coordination, "worker-1", "worker", ["test"]
        )

        assert result["success"] is False
        assert "already in coordination" in result["error"]

    @pytest.mark.asyncio
    async def test_join_with_custom_role(self, manager, sample_coordination):
        """Test joining with custom role."""
        result = await manager.join_coordination(
            sample_coordination,
            agent_id="observer-1",
            agent_type="observer",
            capabilities=[],
            role="observer"
        )

        assert result["success"] is True
        assert result["participant"]["role"] == "observer"

    @pytest.mark.asyncio
    async def test_leave_coordination(self, manager, sample_coordination):
        """Test agent leaving coordination."""
        await manager.join_coordination(
            sample_coordination, "worker-1", "worker", ["test"]
        )

        result = await manager.leave_coordination(sample_coordination, "worker-1")

        assert result["success"] is True
        coord = await manager.get_coordination(sample_coordination)
        assert "worker-1" not in coord["participants"]

    @pytest.mark.asyncio
    async def test_leave_reassigns_tasks(self, manager, sample_coordination):
        """Test that leaving agent's tasks are reassigned."""
        # Join and get assigned a task
        await manager.join_coordination(
            sample_coordination, "worker-1", "worker", ["test"]
        )

        task_result = await manager.create_task(
            sample_coordination, "processing", "Test task"
        )
        task_id = task_result["task_id"]

        await manager.assign_task(sample_coordination, task_id, "worker-1")

        # Leave coordination
        await manager.leave_coordination(sample_coordination, "worker-1")

        # Check task is unassigned
        coord = await manager.get_coordination(sample_coordination)
        task = coord["tasks"][task_id]
        assert task["assigned_to"] is None
        assert task["status"] == TaskStatus.PENDING.value

    @pytest.mark.asyncio
    async def test_multiple_participants(self, manager, sample_coordination):
        """Test multiple participants joining."""
        participants = [
            ("worker-1", "analyzer", ["analysis"]),
            ("worker-2", "processor", ["processing"]),
            ("worker-3", "validator", ["validation"]),
        ]

        for agent_id, agent_type, capabilities in participants:
            result = await manager.join_coordination(
                sample_coordination, agent_id, agent_type, capabilities
            )
            assert result["success"] is True

        coord = await manager.get_coordination(sample_coordination)
        # +1 for coordinator
        assert len(coord["participants"]) == len(participants) + 1


# ============================================================================
# TASK CREATION TESTS
# ============================================================================


@pytest.mark.unit
@pytest.mark.protocol
class TestTaskCreation:
    """Test task creation functionality."""

    @pytest.mark.asyncio
    async def test_create_task(self, manager, sample_coordination):
        """Test creating a task."""
        result = await manager.create_task(
            coordination_id=sample_coordination,
            task_type="data_processing",
            description="Process dataset chunk",
            priority=7
        )

        assert result["success"] is True
        assert "task_id" in result
        assert result["task"]["task_type"] == "data_processing"
        assert result["task"]["priority"] == 7

    @pytest.mark.asyncio
    async def test_create_task_nonexistent_coordination(self, manager):
        """Test creating task in nonexistent coordination."""
        result = await manager.create_task(
            coordination_id="nonexistent",
            task_type="test",
            description="Test task"
        )

        assert result["success"] is False
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_create_task_with_dependencies(self, manager, sample_coordination):
        """Test creating task with dependencies."""
        # Create first task
        result1 = await manager.create_task(
            sample_coordination, "preprocessing", "Preprocess data"
        )
        task1_id = result1["task_id"]

        # Create dependent task
        result2 = await manager.create_task(
            coordination_id=sample_coordination,
            task_type="analysis",
            description="Analyze preprocessed data",
            dependencies=[task1_id]
        )

        assert result2["success"] is True
        assert task1_id in result2["task"]["dependencies"]

    @pytest.mark.asyncio
    async def test_create_task_with_input_data(self, manager, sample_coordination):
        """Test creating task with input data."""
        input_data = {
            "dataset_path": "/data/input.csv",
            "parameters": {"threshold": 0.5}
        }

        result = await manager.create_task(
            coordination_id=sample_coordination,
            task_type="processing",
            description="Process data",
            input_data=input_data
        )

        assert result["success"] is True
        assert result["task"]["input_data"]["dataset_path"] == "/data/input.csv"

    @pytest.mark.asyncio
    async def test_create_multiple_tasks(self, manager, sample_coordination):
        """Test creating multiple tasks."""
        task_ids = []

        for i in range(5):
            result = await manager.create_task(
                sample_coordination,
                task_type="processing",
                description=f"Task {i}",
                priority=i
            )
            assert result["success"] is True
            task_ids.append(result["task_id"])

        coord = await manager.get_coordination(sample_coordination)
        assert len(coord["tasks"]) == 5


# ============================================================================
# TASK ASSIGNMENT TESTS
# ============================================================================


@pytest.mark.unit
@pytest.mark.protocol
class TestTaskAssignment:
    """Test task assignment functionality."""

    @pytest.mark.asyncio
    async def test_assign_task(self, manager, sample_coordination):
        """Test assigning task to agent."""
        # Join coordination
        await manager.join_coordination(
            sample_coordination, "worker-1", "worker", ["test"]
        )

        # Create task
        task_result = await manager.create_task(
            sample_coordination, "processing", "Test task"
        )
        task_id = task_result["task_id"]

        # Assign task
        result = await manager.assign_task(sample_coordination, task_id, "worker-1")

        assert result["success"] is True
        assert result["task_id"] == task_id
        assert result["agent_id"] == "worker-1"

        # Verify assignment
        coord = await manager.get_coordination(sample_coordination)
        task = coord["tasks"][task_id]
        assert task["assigned_to"] == "worker-1"
        assert task["status"] == TaskStatus.ASSIGNED.value

    @pytest.mark.asyncio
    async def test_assign_task_updates_participant(self, manager, sample_coordination):
        """Test that task assignment updates participant."""
        await manager.join_coordination(
            sample_coordination, "worker-1", "worker", ["test"]
        )

        task_result = await manager.create_task(
            sample_coordination, "processing", "Test task"
        )
        task_id = task_result["task_id"]

        await manager.assign_task(sample_coordination, task_id, "worker-1")

        coord = await manager.get_coordination(sample_coordination)
        participant = coord["participants"]["worker-1"]
        assert task_id in participant["assigned_tasks"]

    @pytest.mark.asyncio
    async def test_assign_task_nonexistent_coordination(self, manager):
        """Test assigning task in nonexistent coordination."""
        result = await manager.assign_task("nonexistent", "task-1", "worker-1")
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_assign_nonexistent_task(self, manager, sample_coordination):
        """Test assigning nonexistent task."""
        await manager.join_coordination(
            sample_coordination, "worker-1", "worker", ["test"]
        )

        result = await manager.assign_task(
            sample_coordination, "nonexistent-task", "worker-1"
        )
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_assign_to_nonparticipant(self, manager, sample_coordination):
        """Test assigning task to non-participant."""
        task_result = await manager.create_task(
            sample_coordination, "processing", "Test task"
        )
        task_id = task_result["task_id"]

        result = await manager.assign_task(
            sample_coordination, task_id, "nonexistent-worker"
        )
        assert result["success"] is False


# ============================================================================
# TASK STATUS TESTS
# ============================================================================


@pytest.mark.unit
@pytest.mark.protocol
class TestTaskStatus:
    """Test task status updates."""

    @pytest.mark.asyncio
    async def test_update_task_to_in_progress(self, manager, sample_coordination):
        """Test updating task to in_progress."""
        task_result = await manager.create_task(
            sample_coordination, "processing", "Test task"
        )
        task_id = task_result["task_id"]

        result = await manager.update_task_status(
            sample_coordination, task_id, TaskStatus.IN_PROGRESS.value
        )

        assert result["success"] is True
        coord = await manager.get_coordination(sample_coordination)
        task = coord["tasks"][task_id]
        assert task["status"] == TaskStatus.IN_PROGRESS.value
        assert task["started_at"] is not None

    @pytest.mark.asyncio
    async def test_update_task_to_completed(self, manager, sample_coordination):
        """Test completing a task."""
        await manager.join_coordination(
            sample_coordination, "worker-1", "worker", ["test"]
        )

        task_result = await manager.create_task(
            sample_coordination, "processing", "Test task"
        )
        task_id = task_result["task_id"]

        await manager.assign_task(sample_coordination, task_id, "worker-1")

        output_data = {"result": "success", "value": 42}
        result = await manager.update_task_status(
            sample_coordination,
            task_id,
            TaskStatus.COMPLETED.value,
            output_data=output_data
        )

        assert result["success"] is True
        coord = await manager.get_coordination(sample_coordination)
        task = coord["tasks"][task_id]
        assert task["status"] == TaskStatus.COMPLETED.value
        assert task["completed_at"] is not None
        assert task["output_data"]["result"] == "success"

    @pytest.mark.asyncio
    async def test_complete_task_updates_participant(self, manager, sample_coordination):
        """Test that completing task updates participant stats."""
        await manager.join_coordination(
            sample_coordination, "worker-1", "worker", ["test"]
        )

        task_result = await manager.create_task(
            sample_coordination, "processing", "Test task"
        )
        task_id = task_result["task_id"]

        await manager.assign_task(sample_coordination, task_id, "worker-1")
        await manager.update_task_status(
            sample_coordination, task_id, TaskStatus.COMPLETED.value
        )

        coord = await manager.get_coordination(sample_coordination)
        participant = coord["participants"]["worker-1"]
        assert task_id not in participant["assigned_tasks"]
        assert task_id in participant["completed_tasks"]

    @pytest.mark.asyncio
    async def test_update_task_increments_completed_stats(self, manager, sample_coordination):
        """Test that completing tasks increments stats."""
        initial_stats = await manager.get_statistics()
        initial_completed = initial_stats["stats"]["completed_tasks"]

        task_result = await manager.create_task(
            sample_coordination, "processing", "Test task"
        )
        task_id = task_result["task_id"]

        await manager.update_task_status(
            sample_coordination, task_id, TaskStatus.COMPLETED.value
        )

        final_stats = await manager.get_statistics()
        final_completed = final_stats["stats"]["completed_tasks"]

        assert final_completed == initial_completed + 1

    @pytest.mark.asyncio
    async def test_update_nonexistent_task(self, manager, sample_coordination):
        """Test updating nonexistent task."""
        result = await manager.update_task_status(
            sample_coordination, "nonexistent", TaskStatus.COMPLETED.value
        )
        assert result["success"] is False


# ============================================================================
# DEPENDENCY MANAGEMENT TESTS
# ============================================================================


@pytest.mark.unit
@pytest.mark.protocol
class TestDependencyManagement:
    """Test task dependency management."""

    @pytest.mark.asyncio
    async def test_get_available_tasks_no_dependencies(self, manager, sample_coordination):
        """Test getting available tasks without dependencies."""
        # Create tasks without dependencies
        for i in range(3):
            await manager.create_task(
                sample_coordination, "processing", f"Task {i}"
            )

        available = await manager.get_available_tasks(sample_coordination)
        assert len(available) == 3

    @pytest.mark.asyncio
    async def test_get_available_tasks_with_dependencies(self, manager, sample_coordination):
        """Test that tasks with unmet dependencies are not available."""
        # Create first task
        result1 = await manager.create_task(
            sample_coordination, "preprocessing", "Preprocess"
        )
        task1_id = result1["task_id"]

        # Create dependent task
        await manager.create_task(
            sample_coordination,
            "analysis",
            "Analyze",
            dependencies=[task1_id]
        )

        # Only first task should be available
        available = await manager.get_available_tasks(sample_coordination)
        assert len(available) == 1
        assert available[0]["task_id"] == task1_id

    @pytest.mark.asyncio
    async def test_available_tasks_after_dependency_completion(self, manager, sample_coordination):
        """Test that completing dependency makes dependent task available."""
        # Create dependency chain
        result1 = await manager.create_task(
            sample_coordination, "task1", "First"
        )
        task1_id = result1["task_id"]

        result2 = await manager.create_task(
            sample_coordination, "task2", "Second", dependencies=[task1_id]
        )
        task2_id = result2["task_id"]

        # Initially only task1 available
        available = await manager.get_available_tasks(sample_coordination)
        assert len(available) == 1

        # Complete task1
        await manager.update_task_status(
            sample_coordination, task1_id, TaskStatus.COMPLETED.value
        )

        # Now task2 should be available
        available = await manager.get_available_tasks(sample_coordination)
        assert len(available) == 1
        assert available[0]["task_id"] == task2_id

    @pytest.mark.asyncio
    async def test_available_tasks_sorted_by_priority(self, manager, sample_coordination):
        """Test that available tasks are sorted by priority."""
        priorities = [3, 8, 5, 1, 9]

        for priority in priorities:
            await manager.create_task(
                sample_coordination,
                "processing",
                f"Task priority {priority}",
                priority=priority
            )

        available = await manager.get_available_tasks(sample_coordination)
        task_priorities = [task["priority"] for task in available]

        # Should be sorted descending (highest priority first)
        assert task_priorities == sorted(priorities, reverse=True)

    @pytest.mark.asyncio
    async def test_complex_dependency_chain(self, manager, sample_coordination):
        """Test complex dependency chain."""
        # Create dependency graph:
        #   task1 -> task3
        #   task2 -> task3
        #   task3 -> task4

        result1 = await manager.create_task(sample_coordination, "t1", "Task 1")
        result2 = await manager.create_task(sample_coordination, "t2", "Task 2")
        task1_id = result1["task_id"]
        task2_id = result2["task_id"]

        result3 = await manager.create_task(
            sample_coordination, "t3", "Task 3", dependencies=[task1_id, task2_id]
        )
        task3_id = result3["task_id"]

        result4 = await manager.create_task(
            sample_coordination, "t4", "Task 4", dependencies=[task3_id]
        )

        # Initially only task1 and task2 available
        available = await manager.get_available_tasks(sample_coordination)
        assert len(available) == 2

        # Complete task1
        await manager.update_task_status(
            sample_coordination, task1_id, TaskStatus.COMPLETED.value
        )
        available = await manager.get_available_tasks(sample_coordination)
        assert len(available) == 1  # Still only task2

        # Complete task2
        await manager.update_task_status(
            sample_coordination, task2_id, TaskStatus.COMPLETED.value
        )
        available = await manager.get_available_tasks(sample_coordination)
        assert len(available) == 1  # Now task3

        # Complete task3
        await manager.update_task_status(
            sample_coordination, task3_id, TaskStatus.COMPLETED.value
        )
        available = await manager.get_available_tasks(sample_coordination)
        assert len(available) == 1  # Now task4


# ============================================================================
# SHARED STATE TESTS
# ============================================================================


@pytest.mark.unit
@pytest.mark.protocol
class TestSharedState:
    """Test shared state synchronization."""

    @pytest.mark.asyncio
    async def test_update_shared_state(self, manager, sample_coordination):
        """Test updating shared state."""
        updates = {
            "processed_items": 100,
            "current_phase": "analysis"
        }

        result = await manager.update_shared_state(
            sample_coordination, "worker-1", updates
        )

        assert result["success"] is True
        assert result["shared_state"]["processed_items"] == 100

    @pytest.mark.asyncio
    async def test_get_shared_state(self, manager, sample_coordination):
        """Test getting shared state."""
        updates = {"key1": "value1", "key2": 42}
        await manager.update_shared_state(sample_coordination, "worker-1", updates)

        state = await manager.get_shared_state(sample_coordination)
        assert state["key1"] == "value1"
        assert state["key2"] == 42

    @pytest.mark.asyncio
    async def test_shared_state_merges_updates(self, manager, sample_coordination):
        """Test that state updates are merged."""
        await manager.update_shared_state(
            sample_coordination, "worker-1", {"a": 1, "b": 2}
        )
        await manager.update_shared_state(
            sample_coordination, "worker-2", {"b": 3, "c": 4}
        )

        state = await manager.get_shared_state(sample_coordination)
        assert state["a"] == 1
        assert state["b"] == 3  # Updated
        assert state["c"] == 4

    @pytest.mark.asyncio
    async def test_update_state_nonexistent_coordination(self, manager):
        """Test updating state in nonexistent coordination."""
        result = await manager.update_shared_state(
            "nonexistent", "worker-1", {"key": "value"}
        )
        assert result["success"] is False


# ============================================================================
# PROGRESS TRACKING TESTS
# ============================================================================


@pytest.mark.unit
@pytest.mark.protocol
class TestProgressTracking:
    """Test progress tracking functionality."""

    @pytest.mark.asyncio
    async def test_progress_empty_coordination(self, manager, sample_coordination):
        """Test progress with no tasks."""
        progress = await manager.get_progress(sample_coordination)

        assert progress["total_tasks"] == 0
        assert progress["completed_tasks"] == 0
        assert progress["progress_percentage"] == 0.0

    @pytest.mark.asyncio
    async def test_progress_with_tasks(self, manager, sample_coordination):
        """Test progress calculation with tasks."""
        # Create 4 tasks
        task_ids = []
        for i in range(4):
            result = await manager.create_task(
                sample_coordination, "processing", f"Task {i}"
            )
            task_ids.append(result["task_id"])

        # Complete 2 tasks
        for i in range(2):
            await manager.update_task_status(
                sample_coordination, task_ids[i], TaskStatus.COMPLETED.value
            )

        progress = await manager.get_progress(sample_coordination)
        assert progress["total_tasks"] == 4
        assert progress["completed_tasks"] == 2
        assert progress["progress_percentage"] == 50.0

    @pytest.mark.asyncio
    async def test_progress_tracks_status_breakdown(self, manager, sample_coordination):
        """Test progress tracks tasks by status."""
        # Create tasks with different statuses
        task_ids = []
        for i in range(6):
            result = await manager.create_task(
                sample_coordination, "processing", f"Task {i}"
            )
            task_ids.append(result["task_id"])

        # Set different statuses
        await manager.update_task_status(
            sample_coordination, task_ids[0], TaskStatus.COMPLETED.value
        )
        await manager.update_task_status(
            sample_coordination, task_ids[1], TaskStatus.COMPLETED.value
        )
        await manager.update_task_status(
            sample_coordination, task_ids[2], TaskStatus.IN_PROGRESS.value
        )
        await manager.update_task_status(
            sample_coordination, task_ids[3], TaskStatus.IN_PROGRESS.value
        )
        # tasks 4 and 5 remain PENDING

        progress = await manager.get_progress(sample_coordination)
        assert progress["completed_tasks"] == 2
        assert progress["in_progress_tasks"] == 2
        assert progress["pending_tasks"] == 2

    @pytest.mark.asyncio
    async def test_progress_includes_participant_count(self, manager, sample_coordination):
        """Test progress includes participant count."""
        await manager.join_coordination(
            sample_coordination, "worker-1", "worker", ["test"]
        )
        await manager.join_coordination(
            sample_coordination, "worker-2", "worker", ["test"]
        )

        # Add a task so progress returns full information
        await manager.create_task(sample_coordination, "test", "Test task")

        progress = await manager.get_progress(sample_coordination)
        # +1 for coordinator
        assert progress["participants"] == 3


# ============================================================================
# EVENT SYSTEM TESTS
# ============================================================================


@pytest.mark.unit
@pytest.mark.protocol
class TestEventSystem:
    """Test event system functionality."""

    @pytest.mark.asyncio
    async def test_coordination_created_event(self, manager):
        """Test coordination created event."""
        events = []

        def handler(data):
            events.append(data.coordination_id)

        manager.on_event("coordination_created", handler)

        result = await manager.create_coordination(
            "coord-1", CoordinationType.SWARM.value, "Test"
        )

        assert len(events) == 1
        assert events[0] == result["coordination_id"]

    @pytest.mark.asyncio
    async def test_task_created_event(self, manager, sample_coordination):
        """Test task created event."""
        events = []

        def handler(data):
            events.append(data["task"].task_id)

        manager.on_event("task_created", handler)

        result = await manager.create_task(
            sample_coordination, "processing", "Test"
        )

        assert len(events) == 1
        assert events[0] == result["task_id"]

    @pytest.mark.asyncio
    async def test_participant_joined_event(self, manager, sample_coordination):
        """Test participant joined event."""
        events = []

        def handler(data):
            events.append(data["participant"].agent_id)

        manager.on_event("participant_joined", handler)

        await manager.join_coordination(
            sample_coordination, "worker-1", "worker", ["test"]
        )

        assert len(events) == 1
        assert events[0] == "worker-1"

    @pytest.mark.asyncio
    async def test_async_event_handler(self, manager, sample_coordination):
        """Test async event handlers."""
        events = []

        async def async_handler(data):
            await asyncio.sleep(0.01)
            events.append("async")

        manager.on_event("task_created", async_handler)

        await manager.create_task(sample_coordination, "processing", "Test")
        await asyncio.sleep(0.05)

        assert len(events) == 1


# ============================================================================
# ACP CLIENT TESTS
# ============================================================================


@pytest.mark.unit
@pytest.mark.protocol
class TestACPClient:
    """Test ACP client functionality."""

    @pytest.mark.asyncio
    async def test_client_create_coordination(self, coordinator_client):
        """Test client creating coordination."""
        coord_id = await coordinator_client.create_coordination(
            coordination_type=CoordinationType.SWARM.value,
            goal="Test goal"
        )

        assert coord_id is not None
        assert len(coord_id) > 0

    @pytest.mark.asyncio
    async def test_client_join(self, coordinator_client, worker_client1):
        """Test client joining coordination."""
        coord_id = await coordinator_client.create_coordination(
            CoordinationType.SWARM.value, "Test"
        )

        success = await worker_client1.join(
            coord_id, "analyzer", ["analysis"]
        )
        assert success is True

    @pytest.mark.asyncio
    async def test_client_leave(self, coordinator_client, worker_client1):
        """Test client leaving coordination."""
        coord_id = await coordinator_client.create_coordination(
            CoordinationType.SWARM.value, "Test"
        )

        await worker_client1.join(coord_id, "worker", ["test"])
        success = await worker_client1.leave(coord_id)
        assert success is True

    @pytest.mark.asyncio
    async def test_client_create_task(self, coordinator_client):
        """Test client creating task."""
        coord_id = await coordinator_client.create_coordination(
            CoordinationType.SWARM.value, "Test"
        )

        task_id = await coordinator_client.create_task(
            coord_id, "processing", "Test task", priority=7
        )
        assert task_id is not None

    @pytest.mark.asyncio
    async def test_client_claim_task(self, coordinator_client, worker_client1):
        """Test client claiming task."""
        coord_id = await coordinator_client.create_coordination(
            CoordinationType.SWARM.value, "Test"
        )

        await worker_client1.join(coord_id, "worker", ["test"])
        task_id = await coordinator_client.create_task(
            coord_id, "processing", "Test"
        )

        success = await worker_client1.claim_task(coord_id, task_id)
        assert success is True

    @pytest.mark.asyncio
    async def test_client_update_task(self, coordinator_client, worker_client1):
        """Test client updating task."""
        coord_id = await coordinator_client.create_coordination(
            CoordinationType.SWARM.value, "Test"
        )

        task_id = await coordinator_client.create_task(
            coord_id, "processing", "Test"
        )

        success = await coordinator_client.update_task(
            coord_id, task_id, TaskStatus.IN_PROGRESS.value
        )
        assert success is True

    @pytest.mark.asyncio
    async def test_client_update_state(self, coordinator_client):
        """Test client updating shared state."""
        coord_id = await coordinator_client.create_coordination(
            CoordinationType.SWARM.value, "Test"
        )

        success = await coordinator_client.update_state(
            coord_id, {"key": "value"}
        )
        assert success is True

    @pytest.mark.asyncio
    async def test_client_get_progress(self, coordinator_client):
        """Test client getting progress."""
        coord_id = await coordinator_client.create_coordination(
            CoordinationType.SWARM.value, "Test"
        )

        progress = await coordinator_client.get_progress(coord_id)
        assert "total_tasks" in progress


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


@pytest.mark.integration
@pytest.mark.protocol
class TestACPIntegration:
    """Integration tests for complete ACP workflows."""

    @pytest.mark.asyncio
    async def test_full_swarm_workflow(self, manager):
        """Test complete swarm coordination workflow."""
        # Create coordination
        result = await manager.create_coordination(
            "coordinator", CoordinationType.SWARM.value, "Process dataset"
        )
        coord_id = result["coordination_id"]

        # Start coordination
        await manager.start_coordination(coord_id)

        # Workers join
        await manager.join_coordination(coord_id, "worker-1", "processor", ["processing"])
        await manager.join_coordination(coord_id, "worker-2", "processor", ["processing"])

        # Create tasks
        task_ids = []
        for i in range(4):
            result = await manager.create_task(
                coord_id, "processing", f"Process chunk {i}"
            )
            task_ids.append(result["task_id"])

        # Workers claim and complete tasks
        await manager.assign_task(coord_id, task_ids[0], "worker-1")
        await manager.assign_task(coord_id, task_ids[1], "worker-2")

        await manager.update_task_status(
            coord_id, task_ids[0], TaskStatus.IN_PROGRESS.value
        )
        await manager.update_task_status(
            coord_id, task_ids[0], TaskStatus.COMPLETED.value,
            output_data={"result": "chunk0"}
        )

        # Check progress
        progress = await manager.get_progress(coord_id)
        assert progress["completed_tasks"] == 1
        assert progress["participants"] == 3  # coordinator + 2 workers

        # Complete coordination
        result = await manager.complete_coordination(coord_id)
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_pipeline_workflow(self, manager):
        """Test pipeline coordination with sequential tasks."""
        result = await manager.create_coordination(
            "coordinator", CoordinationType.PIPELINE.value, "Sequential processing"
        )
        coord_id = result["coordination_id"]

        # Create pipeline stages
        result1 = await manager.create_task(coord_id, "fetch", "Fetch data")
        task1_id = result1["task_id"]

        result2 = await manager.create_task(
            coord_id, "process", "Process data", dependencies=[task1_id]
        )
        task2_id = result2["task_id"]

        result3 = await manager.create_task(
            coord_id, "store", "Store results", dependencies=[task2_id]
        )
        task3_id = result3["task_id"]

        # Only first task available
        available = await manager.get_available_tasks(coord_id)
        assert len(available) == 1
        assert available[0]["task_id"] == task1_id

        # Complete stage 1
        await manager.update_task_status(
            coord_id, task1_id, TaskStatus.COMPLETED.value
        )

        # Now stage 2 available
        available = await manager.get_available_tasks(coord_id)
        assert len(available) == 1
        assert available[0]["task_id"] == task2_id

        # Complete stage 2
        await manager.update_task_status(
            coord_id, task2_id, TaskStatus.COMPLETED.value
        )

        # Now stage 3 available
        available = await manager.get_available_tasks(coord_id)
        assert len(available) == 1
        assert available[0]["task_id"] == task3_id

    @pytest.mark.asyncio
    async def test_hierarchical_delegation(self, manager):
        """Test hierarchical coordination with delegation."""
        result = await manager.create_coordination(
            "supervisor", CoordinationType.HIERARCHICAL.value, "Supervised execution"
        )
        coord_id = result["coordination_id"]

        # Supervisor creates high-level tasks
        result1 = await manager.create_task(
            coord_id, "analyze", "Analyze dataset", priority=10
        )
        result2 = await manager.create_task(
            coord_id, "report", "Generate report", priority=8
        )

        # Subordinates join
        await manager.join_coordination(
            coord_id, "analyst", "analyst", ["analysis"], role="subordinate"
        )
        await manager.join_coordination(
            coord_id, "reporter", "reporter", ["reporting"], role="subordinate"
        )

        # Supervisor assigns tasks
        await manager.assign_task(coord_id, result1["task_id"], "analyst")
        await manager.assign_task(coord_id, result2["task_id"], "reporter")

        coord = await manager.get_coordination(coord_id)
        assert coord["participants"]["analyst"]["role"] == "subordinate"

    @pytest.mark.asyncio
    async def test_state_synchronization(self, manager):
        """Test state synchronization across participants."""
        result = await manager.create_coordination(
            "coordinator", CoordinationType.COLLABORATIVE.value, "Collaborative work"
        )
        coord_id = result["coordination_id"]

        # Multiple agents update state
        await manager.update_shared_state(
            coord_id, "agent-1", {"processed": 100, "agent1_status": "working"}
        )
        await manager.update_shared_state(
            coord_id, "agent-2", {"processed": 200, "agent2_status": "working"}
        )

        state = await manager.get_shared_state(coord_id)
        assert state["processed"] == 200  # Last update
        assert state["agent1_status"] == "working"
        assert state["agent2_status"] == "working"

    @pytest.mark.asyncio
    async def test_concurrent_task_execution(self, manager):
        """Test concurrent task execution and updates."""
        result = await manager.create_coordination(
            "coordinator", CoordinationType.SWARM.value, "Concurrent processing"
        )
        coord_id = result["coordination_id"]

        # Create multiple tasks
        task_ids = []
        for i in range(10):
            result = await manager.create_task(
                coord_id, "processing", f"Task {i}"
            )
            task_ids.append(result["task_id"])

        # Simulate concurrent completion
        completion_tasks = [
            manager.update_task_status(
                coord_id, task_id, TaskStatus.COMPLETED.value
            )
            for task_id in task_ids[:5]
        ]
        await asyncio.gather(*completion_tasks)

        progress = await manager.get_progress(coord_id)
        assert progress["completed_tasks"] == 5
        assert progress["pending_tasks"] == 5
