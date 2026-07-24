"""Checkpoint system for SAGE Continuity Intelligence."""

import json
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class ContinuityCheckpoint(BaseModel):
    """Model representing a structured continuity checkpoint of the system."""

    id: str = Field(default_factory=lambda: f"chk_{uuid.uuid4().hex[:8]}")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    current_sage_state: dict[str, Any] = Field(default_factory=dict)
    active_goals: list[str] = Field(default_factory=list)
    recent_decisions: list[str] = Field(default_factory=list)
    repository_state_reference: dict[str, Any] = Field(default_factory=dict)
    validation_status: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CheckpointManager:
    """Manages creation, loading, listing, and recovery of continuity checkpoints."""

    def __init__(self, storage_path: str = "sage_data/checkpoints"):
        """Initialize Checkpoint Manager.

        Args:
            storage_path: Directory path for persisting checkpoints.
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.checkpoints: dict[str, ContinuityCheckpoint] = {}
        self._load_all_checkpoints()

    def _get_git_reference(self) -> dict[str, Any]:
        """Safely fetch git repository state reference, falling back gracefully on failure."""
        try:
            branch = (
                subprocess.check_output(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"], stderr=subprocess.DEVNULL
                )
                .decode()
                .strip()
            )
            commit = (
                subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL)
                .decode()
                .strip()
            )
            status = (
                subprocess.check_output(["git", "status", "--porcelain"], stderr=subprocess.DEVNULL)
                .decode()
                .strip()
            )
            return {
                "branch": branch,
                "commit": commit,
                "is_dirty": bool(status),
                "status_output": status,
            }
        except Exception:
            return {
                "branch": "unknown",
                "commit": "unknown",
                "is_dirty": False,
                "status_output": "",
            }

    def create_checkpoint(
        self,
        current_sage_state: dict[str, Any],
        active_goals: list[str],
        recent_decisions: list[str],
        validation_status: dict[str, Any],
        checkpoint_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ContinuityCheckpoint:
        """Create and persist a new continuity checkpoint."""
        chk_id = checkpoint_id or f"chk_{uuid.uuid4().hex[:8]}"
        git_ref = self._get_git_reference()

        checkpoint = ContinuityCheckpoint(
            id=chk_id,
            current_sage_state=current_sage_state,
            active_goals=active_goals,
            recent_decisions=recent_decisions,
            repository_state_reference=git_ref,
            validation_status=validation_status,
            metadata=metadata or {},
        )

        self.checkpoints[chk_id] = checkpoint
        self.save_checkpoint(checkpoint)
        return checkpoint

    def retrieve_checkpoint(self, checkpoint_id: str) -> ContinuityCheckpoint | None:
        """Retrieve a checkpoint by ID."""
        if checkpoint_id in self.checkpoints:
            return self.checkpoints[checkpoint_id]

        filepath = self.storage_path / f"{checkpoint_id}.json"
        if filepath.exists():
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                    checkpoint = ContinuityCheckpoint(**data)
                    self.checkpoints[checkpoint_id] = checkpoint
                    return checkpoint
            except Exception:
                pass
        return None

    def save_checkpoint(self, checkpoint: ContinuityCheckpoint) -> None:
        """Save/persist a continuity checkpoint."""
        self.checkpoints[checkpoint.id] = checkpoint
        self.storage_path.mkdir(parents=True, exist_ok=True)
        filepath = self.storage_path / f"{checkpoint.id}.json"
        with open(filepath, "w") as f:
            json.dump(checkpoint.model_dump(), f, indent=2, default=str)

    def list_all(self) -> list[ContinuityCheckpoint]:
        """List all managed checkpoints."""
        return list(self.checkpoints.values())

    def _load_all_checkpoints(self) -> None:
        """Load all persisted checkpoints from disk."""
        if not self.storage_path.exists():
            return
        for filepath in self.storage_path.glob("*.json"):
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                    checkpoint = ContinuityCheckpoint(**data)
                    self.checkpoints[checkpoint.id] = checkpoint
            except Exception:
                pass
