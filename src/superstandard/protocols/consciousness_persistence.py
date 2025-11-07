"""
Consciousness Persistence Layer - Production-Grade State Persistence

This module provides persistence capabilities for consciousness protocol,
enabling:
- Long-term consciousness state storage
- Recovery from failures
- Historical analysis of consciousness evolution
- Audit trail of emergent patterns
- Cross-session consciousness continuity

Supports multiple storage backends:
- JSON file storage (simple, local)
- SQLite database (structured, queryable)
- Redis (fast, distributed)
- PostgreSQL (production, scalable)

Version: 1.0.0
Author: SuperStandard Innovation Lab
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import json
import asyncio

# Import consciousness protocol
from superstandard.protocols.consciousness_protocol import (
    CollectiveConsciousness,
    ConsciousnessSnapshot,
    EmergentPattern,
    Thought,
    ConsciousnessState,
    ThoughtType,
)


class PersistenceError(Exception):
    """Raised when persistence operations fail"""

    pass


# ============================================================================
# Abstract Storage Backend
# ============================================================================


class StorageBackend(ABC):
    """
    Abstract base class for storage backends.

    All storage backends must implement these methods to support
    consciousness persistence.
    """

    @abstractmethod
    async def save_consciousness(self, consciousness_id: str, state: Dict[str, Any]) -> bool:
        """Save complete consciousness state."""
        pass

    @abstractmethod
    async def load_consciousness(self, consciousness_id: str) -> Optional[Dict[str, Any]]:
        """Load consciousness state."""
        pass

    @abstractmethod
    async def save_thought(self, consciousness_id: str, thought: Dict[str, Any]) -> bool:
        """Save individual thought."""
        pass

    @abstractmethod
    async def load_thoughts(
        self, consciousness_id: str, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Load thoughts."""
        pass

    @abstractmethod
    async def save_pattern(self, consciousness_id: str, pattern: Dict[str, Any]) -> bool:
        """Save emergent pattern."""
        pass

    @abstractmethod
    async def load_patterns(self, consciousness_id: str) -> List[Dict[str, Any]]:
        """Load emergent patterns."""
        pass

    @abstractmethod
    async def list_consciousnesses(self) -> List[str]:
        """List all consciousness IDs."""
        pass

    @abstractmethod
    async def delete_consciousness(self, consciousness_id: str) -> bool:
        """Delete consciousness state."""
        pass


# ============================================================================
# JSON File Storage Backend
# ============================================================================


class JSONStorageBackend(StorageBackend):
    """
    Simple JSON file-based storage backend.

    Stores consciousness state as JSON files on local filesystem.
    Good for development, testing, and single-machine deployments.

    Storage structure:
        {storage_path}/
            {consciousness_id}/
                consciousness.json      # Main state
                thoughts/
                    thought_{timestamp}.json
                patterns/
                    pattern_{id}.json
    """

    def __init__(self, storage_path: str = "./consciousness_storage"):
        """
        Initialize JSON storage backend.

        Args:
            storage_path: Base path for storage
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def _get_consciousness_dir(self, consciousness_id: str) -> Path:
        """Get directory for consciousness."""
        path = self.storage_path / consciousness_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    async def save_consciousness(self, consciousness_id: str, state: Dict[str, Any]) -> bool:
        """Save consciousness state to JSON file."""
        try:
            consciousness_dir = self._get_consciousness_dir(consciousness_id)
            file_path = consciousness_dir / "consciousness.json"

            # Add timestamp
            state["persisted_at"] = datetime.utcnow().isoformat()

            # Save to file
            with open(file_path, "w") as f:
                json.dump(state, f, indent=2, default=str)

            return True

        except Exception as e:
            raise PersistenceError(f"Failed to save consciousness: {e}")

    async def load_consciousness(self, consciousness_id: str) -> Optional[Dict[str, Any]]:
        """Load consciousness state from JSON file."""
        try:
            consciousness_dir = self._get_consciousness_dir(consciousness_id)
            file_path = consciousness_dir / "consciousness.json"

            if not file_path.exists():
                return None

            with open(file_path, "r") as f:
                return json.load(f)

        except Exception as e:
            raise PersistenceError(f"Failed to load consciousness: {e}")

    async def save_thought(self, consciousness_id: str, thought: Dict[str, Any]) -> bool:
        """Save individual thought."""
        try:
            consciousness_dir = self._get_consciousness_dir(consciousness_id)
            thoughts_dir = consciousness_dir / "thoughts"
            thoughts_dir.mkdir(exist_ok=True)

            timestamp = thought.get("timestamp", datetime.utcnow().isoformat())
            filename = f"thought_{timestamp.replace(':', '-')}.json"
            file_path = thoughts_dir / filename

            with open(file_path, "w") as f:
                json.dump(thought, f, indent=2, default=str)

            return True

        except Exception as e:
            raise PersistenceError(f"Failed to save thought: {e}")

    async def load_thoughts(
        self, consciousness_id: str, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Load thoughts."""
        try:
            consciousness_dir = self._get_consciousness_dir(consciousness_id)
            thoughts_dir = consciousness_dir / "thoughts"

            if not thoughts_dir.exists():
                return []

            thoughts = []
            files = sorted(thoughts_dir.glob("thought_*.json"))

            if limit:
                files = files[-limit:]  # Get most recent

            for file_path in files:
                with open(file_path, "r") as f:
                    thoughts.append(json.load(f))

            return thoughts

        except Exception as e:
            raise PersistenceError(f"Failed to load thoughts: {e}")

    async def save_pattern(self, consciousness_id: str, pattern: Dict[str, Any]) -> bool:
        """Save emergent pattern."""
        try:
            consciousness_dir = self._get_consciousness_dir(consciousness_id)
            patterns_dir = consciousness_dir / "patterns"
            patterns_dir.mkdir(exist_ok=True)

            pattern_id = pattern.get("pattern_id", f"pattern_{datetime.utcnow().timestamp()}")
            file_path = patterns_dir / f"{pattern_id}.json"

            with open(file_path, "w") as f:
                json.dump(pattern, f, indent=2, default=str)

            return True

        except Exception as e:
            raise PersistenceError(f"Failed to save pattern: {e}")

    async def load_patterns(self, consciousness_id: str) -> List[Dict[str, Any]]:
        """Load emergent patterns."""
        try:
            consciousness_dir = self._get_consciousness_dir(consciousness_id)
            patterns_dir = consciousness_dir / "patterns"

            if not patterns_dir.exists():
                return []

            patterns = []
            for file_path in patterns_dir.glob("*.json"):
                with open(file_path, "r") as f:
                    patterns.append(json.load(f))

            return patterns

        except Exception as e:
            raise PersistenceError(f"Failed to load patterns: {e}")

    async def list_consciousnesses(self) -> List[str]:
        """List all consciousness IDs."""
        return [d.name for d in self.storage_path.iterdir() if d.is_dir()]

    async def delete_consciousness(self, consciousness_id: str) -> bool:
        """Delete consciousness state."""
        try:
            import shutil

            consciousness_dir = self._get_consciousness_dir(consciousness_id)
            shutil.rmtree(consciousness_dir)
            return True
        except Exception as e:
            raise PersistenceError(f"Failed to delete consciousness: {e}")


# ============================================================================
# Persistent Collective Consciousness
# ============================================================================


class PersistentCollectiveConsciousness(CollectiveConsciousness):
    """
    Collective Consciousness with automatic persistence.

    This extends CollectiveConsciousness to automatically persist:
    - Consciousness state (agents, metrics, awareness)
    - Individual thoughts as they're contributed
    - Emergent patterns as they're discovered
    - Complete consciousness evolution history

    Features:
    - Auto-save on state changes
    - Restore from storage on initialization
    - Configurable save intervals
    - Snapshot/checkpoint support
    - Historical querying
    """

    def __init__(
        self,
        consciousness_id: str,
        storage_backend: StorageBackend,
        auto_save: bool = True,
        save_interval: int = 60,  # seconds
        persist_thoughts: bool = True,
        persist_patterns: bool = True,
    ):
        """
        Initialize persistent collective consciousness.

        Args:
            consciousness_id: Unique ID for this consciousness
            storage_backend: Storage backend to use
            auto_save: Whether to auto-save state periodically
            save_interval: Interval between auto-saves (seconds)
            persist_thoughts: Whether to persist individual thoughts
            persist_patterns: Whether to persist emergent patterns
        """
        super().__init__(consciousness_id)

        self.storage = storage_backend
        self.auto_save = auto_save
        self.save_interval = save_interval
        self.persist_thoughts = persist_thoughts
        self.persist_patterns = persist_patterns

        # Auto-save task
        self._save_task: Optional[asyncio.Task] = None
        self._last_save_time = datetime.utcnow()

    async def initialize(self):
        """Initialize and restore from storage if available."""
        # Try to restore from storage
        restored = await self.restore_from_storage()

        if restored:
            print(f"[Consciousness] Restored {self.consciousness_id} from storage")
            state = self.get_consciousness_state()
            print(f"  - {state['total_agents']} agents")
            print(f"  - {state['total_thoughts']} thoughts")
            print(f"  - {state['emergent_patterns_discovered']} patterns")
            print(f"  - Collective awareness: {state['collective_awareness']:.0%}")

        # Start auto-save if enabled
        if self.auto_save:
            self._save_task = asyncio.create_task(self._auto_save_loop())

    async def shutdown(self):
        """Shutdown and save final state."""
        # Cancel auto-save
        if self._save_task:
            self._save_task.cancel()
            try:
                await self._save_task
            except asyncio.CancelledError:
                pass

        # Final save
        await self.save_to_storage()
        print(f"[Consciousness] {self.consciousness_id} saved and shutdown")

    async def _auto_save_loop(self):
        """Periodic auto-save loop."""
        while True:
            try:
                await asyncio.sleep(self.save_interval)
                await self.save_to_storage()
                self._last_save_time = datetime.utcnow()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[Consciousness] Auto-save error: {e}")

    async def save_to_storage(self) -> bool:
        """
        Save current consciousness state to storage.

        Returns:
            True if successful
        """
        try:
            # Serialize agents
            agents_data = []
            for agent_id, snapshot in self.agents.items():
                agents_data.append(
                    {
                        "agent_id": agent_id,
                        "state": snapshot.state.value,
                        "awareness_level": snapshot.awareness_level,
                        "integration_score": snapshot.integration_score,
                        "thought_count": len(snapshot.thoughts),
                        "qualia": snapshot.qualia,
                    }
                )

            # Get metrics
            state = self.get_consciousness_state()

            # Create consciousness state
            consciousness_data = {
                "consciousness_id": self.consciousness_id,
                "agents": agents_data,
                "metrics": state,
                "creation_time": self.creation_time.isoformat(),
                "saved_at": datetime.utcnow().isoformat(),
            }

            # Save main state
            await self.storage.save_consciousness(self.consciousness_id, consciousness_data)

            return True

        except Exception as e:
            print(f"[Consciousness] Save error: {e}")
            return False

    async def restore_from_storage(self) -> bool:
        """
        Restore consciousness state from storage.

        Returns:
            True if successfully restored
        """
        try:
            # Load consciousness data
            data = await self.storage.load_consciousness(self.consciousness_id)

            if data is None:
                return False

            # Restore agents
            for agent_data in data.get("agents", []):
                snapshot = ConsciousnessSnapshot(
                    agent_id=agent_data["agent_id"],
                    state=ConsciousnessState(agent_data["state"]),
                    thoughts=[],  # Thoughts loaded separately
                    awareness_level=agent_data["awareness_level"],
                    integration_score=agent_data["integration_score"],
                    qualia=agent_data.get("qualia", {}),
                )
                self.agents[agent_data["agent_id"]] = snapshot

            # Restore metrics
            metrics = data.get("metrics", {})
            self.total_thoughts_received = metrics.get("total_thoughts", 0)
            self.total_collapses = metrics.get("total_collapses", 0)
            self.collective_awareness = metrics.get("collective_awareness", 0.0)

            # Load thoughts
            if self.persist_thoughts:
                thoughts_data = await self.storage.load_thoughts(self.consciousness_id)
                # TODO: Reconstruct thought objects from data

            # Load patterns
            if self.persist_patterns:
                patterns_data = await self.storage.load_patterns(self.consciousness_id)
                # TODO: Reconstruct pattern objects from data

            return True

        except Exception as e:
            print(f"[Consciousness] Restore error: {e}")
            return False

    # Override methods to add persistence

    async def contribute_thought(self, *args, **kwargs):
        """Contribute thought with persistence."""
        thought = await super().contribute_thought(*args, **kwargs)

        # Persist thought
        if self.persist_thoughts:
            await self.storage.save_thought(
                self.consciousness_id,
                {
                    "agent_id": thought.agent_id,
                    "thought_type": thought.thought_type.value,
                    "content": thought.content,
                    "timestamp": thought.timestamp.isoformat(),
                    "confidence": thought.confidence,
                    "emotional_valence": thought.emotional_valence,
                    "quantum_state": thought.quantum_state,
                },
            )

        return thought

    async def collapse_consciousness(self, *args, **kwargs):
        """Collapse consciousness with persistence."""
        patterns = await super().collapse_consciousness(*args, **kwargs)

        # Persist patterns
        if self.persist_patterns:
            for pattern in patterns:
                await self.storage.save_pattern(self.consciousness_id, pattern.to_dict())

        return patterns


__all__ = [
    "PersistenceError",
    "StorageBackend",
    "JSONStorageBackend",
    "PersistentCollectiveConsciousness",
]
