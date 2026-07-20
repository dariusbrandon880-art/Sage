"""SAGE Runtime Engine - core execution loop for autonomous continuity."""

import os
import json
import uuid
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from sage.models import RuntimeState
from sage.memory import MemoryStore
from sage.archive import Archive
from sage.decision import DecisionTracker


class ExecutionContext(BaseModel):
    """Context for a single execution cycle."""
    session_id: str
    turn_number: int
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SageRuntime:
    """Main runtime engine for SAGE autonomous continuity operations."""

    def __init__(self, workspace_path: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        """Initialize SAGE runtime.
        
        Args:
            workspace_path: Optional base directory for workspace storage.
            config: Optional runtime configuration dictionary.
        """
        self.config = config or {}
        self.active = False
        self.context: Optional[ExecutionContext] = None

        # Resolve workspace path and storage subdirectories
        # Support workspace_path passed in position 0 as config dict if initialized incorrectly
        if isinstance(workspace_path, dict):
            self.config.update(workspace_path)
            workspace_path = None

        self.workspace_path = Path(workspace_path or self.config.get("workspace_path", "sage_data"))
        self.workspace_path.mkdir(parents=True, exist_ok=True)

        # Initialize sub-systems with workspace paths
        self.memory = MemoryStore(persistent_path=str(self.workspace_path / "memory"))
        self.archive = Archive(storage_path=str(self.workspace_path / "archive"))
        self.decisions = DecisionTracker(storage_path=str(self.workspace_path / "decisions"))

        self.current_state = RuntimeState()
        self.load_state()

    def start(self) -> None:
        """Start the SAGE runtime."""
        self.active = True

    def stop(self) -> None:
        """Stop the SAGE runtime."""
        self.active = False

    def is_running(self) -> bool:
        """Check if runtime is active."""
        return self.active

    def get_status(self) -> Dict[str, Any]:
        """Get the current operational status of the runtime.

        Returns:
            A status summary dictionary.
        """
        return {
            "status": "online" if self.active else "offline",
            "is_running": self.active,
            "current_objective": self.current_state.current_objective,
            "active_task": self.current_state.active_task,
            "blockers": self.current_state.blockers,
            "dependencies": self.current_state.dependencies,
            "memory_sessions_count": len(self.memory.list_sessions()),
            "archive_entries_count": len(self.archive.list_all()),
            "decisions_count": len(self.decisions.list_all()),
        }

    def export_all(self) -> Dict[str, Any]:
        """Export the entire runtime operational state, memory, archive, and decisions.

        Returns:
            A dictionary of all exported states.
        """
        memory_state = {}
        if hasattr(self.memory, "export_state"):
            memory_state = self.memory.export_state()
        else:
            # Fallback if MemoryStore has no export_state
            memory_state = {
                "sessions": self.memory.list_sessions()
            }

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "state": self.current_state.model_dump(),
            "memory": memory_state,
            "archive": self.archive.export_state(),
            "decisions": self.decisions.export_state(),
        }

    def set_objective(self, objective: str) -> str:
        """Set the current high-level SAGE objective.

        Args:
            objective: Objective description.

        Returns:
            The current active session ID.
        """
        self.current_state.current_objective = objective
        self.save_state()

        # Ensure a context session exists
        if not self.context:
            session_id = f"session_{uuid.uuid4().hex[:8]}"
            self.context = ExecutionContext(session_id=session_id, turn_number=1)
            self.memory.create_session(session_id, {"created_at": datetime.utcnow().isoformat()})

        return self.context.session_id

    def set_task(self, task: str) -> str:
        """Set the active task under execution.

        Args:
            task: Task description.

        Returns:
            The current active session ID.
        """
        self.current_state.active_task = task
        self.save_state()

        if not self.context:
            session_id = f"session_{uuid.uuid4().hex[:8]}"
            self.context = ExecutionContext(session_id=session_id, turn_number=1)
            self.memory.create_session(session_id, {"created_at": datetime.utcnow().isoformat()})

        return self.context.session_id

    def add_blocker(self, blocker: str) -> None:
        """Add an operational or technical blocker.

        Args:
            blocker: Blocker description.
        """
        if blocker not in self.current_state.blockers:
            self.current_state.blockers.append(blocker)
            self.save_state()

    def resolve_blocker(self, blocker: str) -> None:
        """Resolve and remove an operational or technical blocker.

        Args:
            blocker: Blocker description to resolve.
        """
        if blocker in self.current_state.blockers:
            self.current_state.blockers.remove(blocker)
            self.save_state()

    def checkpoint(self) -> str:
        """Create a persistent checkpoint of the current runtime state.

        Returns:
            The generated checkpoint ID.
        """
        checkpoint_id = f"ckpt_{uuid.uuid4().hex[:12]}"
        checkpoints_dir = self.workspace_path / "checkpoints"
        checkpoints_dir.mkdir(parents=True, exist_ok=True)

        checkpoint_data = {
            "checkpoint_id": checkpoint_id,
            "timestamp": datetime.utcnow().isoformat(),
            "state": self.current_state.model_dump(),
        }

        filepath = checkpoints_dir / f"{checkpoint_id}.json"
        with open(filepath, "w") as f:
            json.dump(checkpoint_data, f, indent=2, default=str)

        return checkpoint_id

    def save_state(self) -> None:
        """Persist current runtime state to disk."""
        filepath = self.workspace_path / "state.json"
        with open(filepath, "w") as f:
            json.dump(self.current_state.model_dump(), f, indent=2, default=str)

    def load_state(self) -> None:
        """Load runtime state from disk if it exists."""
        filepath = self.workspace_path / "state.json"
        if filepath.exists():
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                    self.current_state = RuntimeState(**data)
            except Exception as e:
                print(f"Error loading runtime state: {e}")
