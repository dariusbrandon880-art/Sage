"""SAGE Runtime Engine - core execution loop for autonomous continuity."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

from sage.models import RuntimeState, MemoryObject, DecisionEntry, ArchiveEntry
from sage.memory import Memory
from sage.archive import Archive
from sage.decision import DecisionTracker
from sage.acr.bridge import ACRBridge


class ExecutionContext(BaseModel):
    """Context for a single execution cycle."""
    session_id: str
    turn_number: int
    metadata: Dict[str, Any] = {}


class SageRuntime:
    """Main runtime engine for SAGE autonomous continuity operations."""

    def __init__(self, workspace_path: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        """Initialize SAGE runtime.
        
        Args:
            workspace_path: Optional path to workspace directory.
            config: Optional runtime configuration dictionary.
        """
        # Support passing config as the first positional argument
        if isinstance(workspace_path, dict):
            config = workspace_path
            workspace_path = None

        self.config = config or {}
        self.workspace_path = Path(workspace_path or "sage_data")
        self.active = False
        self.context: Optional[ExecutionContext] = None

        # Setup subsystem storage paths
        self.memory_path = self.workspace_path / "memory"
        self.archive_path = self.workspace_path / "archive"
        self.decisions_path = self.workspace_path / "decisions"
        self.state_file = self.workspace_path / "state.json"

        # Initialize subsystems
        self.memory = Memory(str(self.memory_path))
        self.archive = Archive(str(self.archive_path))
        self.decisions = DecisionTracker(str(self.decisions_path))
        self.acr = ACRBridge(persistence_path=str(self.workspace_path / "continuity"))

        # Load existing state if available, otherwise init fresh
        self.current_state = RuntimeState()
        self._load_state()

    def start(self) -> None:
        """Start the SAGE runtime."""
        self.active = True

    def stop(self) -> None:
        """Stop the SAGE runtime."""
        self.active = False

    def is_running(self) -> bool:
        """Check if runtime is active."""
        return self.active

    def set_objective(self, objective: str) -> str:
        """Set the current objective and generate a session ID.

        Args:
            objective: The objective string.

        Returns:
            The generated session ID.
        """
        self.current_state.current_objective = objective
        self._save_state()

        session_id = f"session_{uuid.uuid4().hex[:8]}"
        self.acr.add_session_link(session_id)

        self.context = ExecutionContext(
            session_id=session_id,
            turn_number=self.acr.get_session_depth(),
            metadata={"objective": objective}
        )
        return session_id

    def set_task(self, task: str) -> str:
        """Set the current task and generate/update session context.

        Args:
            task: The task description string.

        Returns:
            The session ID.
        """
        self.current_state.active_task = task
        self._save_state()

        if self.context:
            self.context.turn_number += 1
            self.context.metadata["last_task"] = task
            session_id = self.context.session_id
        else:
            session_id = f"session_{uuid.uuid4().hex[:8]}"
            self.acr.add_session_link(session_id)
            self.context = ExecutionContext(
                session_id=session_id,
                turn_number=self.acr.get_session_depth(),
                metadata={"task": task}
            )
        return session_id

    def add_blocker(self, blocker: str) -> None:
        """Add a blocker to the active blockers list.

        Args:
            blocker: Description of the blocker.
        """
        if blocker not in self.current_state.blockers:
            self.current_state.blockers.append(blocker)
            self._save_state()

    def resolve_blocker(self, blocker: str) -> None:
        """Remove a blocker from the active blockers list.

        Args:
            blocker: Description of the blocker.
        """
        if blocker in self.current_state.blockers:
            self.current_state.blockers.remove(blocker)
            self._save_state()

    def get_status(self) -> Dict[str, Any]:
        """Retrieve runtime status information.

        Returns:
            Dictionary containing status properties.
        """
        return {
            "active": self.is_running(),
            "current_objective": self.current_state.current_objective,
            "active_task": self.current_state.active_task,
            "blockers": self.current_state.blockers,
            "dependencies": self.current_state.dependencies,
            "memory_count": len(self.memory.list_all()),
            "archive_count": len(self.archive.list_all()),
            "decision_count": len(self.decisions.list_all()),
            "session_depth": self.acr.get_session_depth()
        }

    def checkpoint(self) -> str:
        """Create a checkpoint of the entire runtime state.

        Returns:
            ID of the created checkpoint.
        """
        checkpoint_id = f"checkpoint_{uuid.uuid4().hex[:8]}"
        checkpoint_file = self.workspace_path / f"{checkpoint_id}.json"

        try:
            with open(checkpoint_file, 'w') as f:
                json.dump(self.export_all(), f, indent=2, default=str)
        except Exception:
            pass

        return checkpoint_id

    def export_all(self) -> Dict[str, Any]:
        """Export all runtime databases and current state as a single state map.

        Returns:
            Dictionary representation of all runtime state and databases.
        """
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "state": self.current_state.model_dump(),
            "memory": [obj.model_dump() for obj in self.memory.list_all()],
            "archive": [entry.model_dump() for entry in self.archive.list_all()],
            "decisions": [d.model_dump() for d in self.decisions.list_all()],
            "lineage": self.acr.get_lineage()
        }

    def generate_handoff(self, target_path: Optional[str] = None) -> str:
        """Generate a continuity handoff artifact.

        Args:
            target_path: Optional path to save handoff JSON.

        Returns:
            The handoff JSON path.
        """
        handoff_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "state": self.current_state.model_dump(),
            "lineage": self.acr.get_lineage(),
            "metadata": {
                "memory_count": len(self.memory.list_all()),
                "archive_count": len(self.archive.list_all()),
                "decision_count": len(self.decisions.list_all())
            }
        }

        path = Path(target_path or self.workspace_path / "handoff.json")
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            json.dump(handoff_data, f, indent=2, default=str)

        return str(path)

    def restore_session(self, handoff_path: str) -> bool:
        """Restore runtime state from a handoff artifact.

        Args:
            handoff_path: Path to the handoff JSON file.

        Returns:
            True if restoration was successful, False otherwise.
        """
        path = Path(handoff_path)
        if not path.exists():
            return False

        try:
            with open(path, "r") as f:
                handoff_data = json.load(f)

            # Restore state
            state_data = handoff_data.get("state", {})
            self.current_state = RuntimeState(**state_data)
            self._save_state()

            # Restore lineage in ACRBridge
            self.acr.clear_state()
            for session_id in handoff_data.get("lineage", []):
                self.acr.add_session_link(session_id)

            # Initialize context
            if self.current_state.current_objective:
                self.context = ExecutionContext(
                    session_id=self.acr.get_parent_session() or f"session_{uuid.uuid4().hex[:8]}",
                    turn_number=self.acr.get_session_depth() + 1,
                    metadata={"objective": self.current_state.current_objective}
                )
            return True
        except Exception:
            return False

    def _load_state(self) -> None:
        """Load state.json from workspace."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    self.current_state = RuntimeState(**data)
            except Exception:
                pass

    def _save_state(self) -> None:
        """Save state.json to workspace."""
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.current_state.model_dump(), f, indent=2)
        except Exception:
            pass

    def create_workspace_snapshot(self, snapshot_id: Optional[str] = None) -> str:
        """Serialize active state, memory state, decisions, checkpoints, and continuity metadata
        into the persistent repository directory '.sage/sage_state.json'.

        Args:
            snapshot_id: Optional identifier. If not provided, a unique ID is generated.

        Returns:
            The snapshot ID.
        """
        if not snapshot_id:
            snapshot_id = f"snapshot_{uuid.uuid4().hex[:8]}"

        # Gather checkpoints
        checkpoints_data = {}
        if self.workspace_path.exists():
            for p in self.workspace_path.glob("checkpoint_*.json"):
                try:
                    with open(p, 'r') as f:
                        checkpoints_data[p.stem] = json.load(f)
                except Exception:
                    pass

        # Gathers snapshot data
        snapshot_data = {
            "id": snapshot_id,
            "timestamp": datetime.utcnow().isoformat(),
            "state": self.current_state.model_dump(),
            "memory": [obj.model_dump() for obj in self.memory.list_all()],
            "archive": [entry.model_dump() for entry in self.archive.list_all()],
            "decisions": [d.model_dump() for d in self.decisions.list_all()],
            "checkpoints": checkpoints_data,
            "lineage": self.acr.get_lineage(),
            "continuity_state": self.acr.continuity_state,
        }

        # Save to .sage/sage_state.json
        state_path = Path(".sage/sage_state.json")
        state_path.parent.mkdir(parents=True, exist_ok=True)

        snapshots_registry = {"snapshots": {}}
        if state_path.exists():
            try:
                with open(state_path, 'r') as f:
                    snapshots_registry = json.load(f)
                    if "snapshots" not in snapshots_registry:
                        snapshots_registry["snapshots"] = {}
            except Exception:
                pass

        snapshots_registry["snapshots"][snapshot_id] = snapshot_data

        with open(state_path, 'w') as f:
            json.dump(snapshots_registry, f, indent=2, default=str)

        return snapshot_id

    def list_workspace_snapshots(self) -> List[Dict[str, Any]]:
        """List all snapshots stored in the workspace registry.

        Returns:
            List of snapshot metadata/details.
        """
        state_path = Path(".sage/sage_state.json")
        if not state_path.exists():
            return []

        try:
            with open(state_path, 'r') as f:
                snapshots_registry = json.load(f)
                snapshots = snapshots_registry.get("snapshots", {})
                return list(snapshots.values())
        except Exception:
            return []

    def restore_workspace_snapshot(self, snapshot_id: str) -> bool:
        """Restore active state, memory, decisions, and continuity metadata from a snapshot.

        Args:
            snapshot_id: The ID of the snapshot to restore.

        Returns:
            True if restoration was successful, False otherwise.
        """
        state_path = Path(".sage/sage_state.json")
        if not state_path.exists():
            return False

        try:
            with open(state_path, 'r') as f:
                snapshots_registry = json.load(f)
                snapshots = snapshots_registry.get("snapshots", {})
                if snapshot_id not in snapshots:
                    return False
                snapshot_data = snapshots[snapshot_id]
        except Exception:
            return False

        # 1. Clear existing workspace databases on disk to ensure clean hydration
        # Memory
        if self.memory_path.exists():
            for p in self.memory_path.glob("*.json"):
                try:
                    p.unlink()
                except Exception:
                    pass
        self.memory.objects.clear()

        # Archive
        if self.archive_path.exists():
            for p in self.archive_path.glob("*.json"):
                try:
                    p.unlink()
                except Exception:
                    pass
        self.archive.entries.clear()

        # Decisions
        if self.decisions_path.exists():
            for p in self.decisions_path.glob("*.json"):
                try:
                    p.unlink()
                except Exception:
                    pass
        self.decisions.decisions.clear()

        # Checkpoints
        if self.workspace_path.exists():
            for p in self.workspace_path.glob("checkpoint_*.json"):
                try:
                    p.unlink()
                except Exception:
                    pass

        # State file
        if self.state_file.exists():
            try:
                self.state_file.unlink()
            except Exception:
                pass

        # Ensure directory paths exist
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        self.memory_path.mkdir(parents=True, exist_ok=True)
        self.archive_path.mkdir(parents=True, exist_ok=True)
        self.decisions_path.mkdir(parents=True, exist_ok=True)

        # 2. Restore active state
        self.current_state = RuntimeState(**snapshot_data["state"])
        self._save_state()

        # 3. Restore memory objects
        for item in snapshot_data.get("memory", []):
            try:
                obj = MemoryObject(**item)
                self.memory.store(obj)
            except Exception:
                pass

        # 4. Restore archive entries
        for item in snapshot_data.get("archive", []):
            try:
                entry = ArchiveEntry(**item)
                self.archive.entries[entry.id] = entry
                with open(self.archive_path / f"{entry.id}.json", 'w') as f:
                    json.dump(entry.model_dump(), f, indent=2, default=str)
            except Exception:
                pass

        # 5. Restore decisions
        for item in snapshot_data.get("decisions", []):
            try:
                entry = DecisionEntry(**item)
                self.decisions.decisions[entry.id] = entry
                self.decisions._save_decision(entry)
            except Exception:
                pass

        # 6. Restore checkpoints
        for checkpoint_id, checkpoint_content in snapshot_data.get("checkpoints", {}).items():
            try:
                with open(self.workspace_path / f"{checkpoint_id}.json", 'w') as f:
                    json.dump(checkpoint_content, f, indent=2, default=str)
            except Exception:
                pass

        # 7. Restore continuity bridge
        try:
            self.acr.clear_state()
            self.acr.save_state(snapshot_data.get("continuity_state", {}))
            for session_id in snapshot_data.get("lineage", []):
                self.acr.add_session_link(session_id)
        except Exception:
            pass

        # 8. Re-initialize context if needed
        if self.current_state.current_objective:
            self.context = ExecutionContext(
                session_id=self.acr.get_parent_session() or f"session_{uuid.uuid4().hex[:8]}",
                turn_number=self.acr.get_session_depth() + 1,
                metadata={"objective": self.current_state.current_objective}
            )

        return True
