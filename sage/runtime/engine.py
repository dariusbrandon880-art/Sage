"""SAGE Runtime Engine - core execution loop for autonomous continuity."""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

from sage.models import (
    RuntimeState,
    MemoryObject,
    DecisionEntry,
    ArchiveEntry,
    ConfidenceLevel,
    DecisionType,
    ExternalSessionPayload,
)
from sage.memory import Memory
from sage.archive import Archive
from sage.decision import DecisionTracker
from sage.acr.bridge import ACRBridge
from sage.acr.session import (
    SessionStateManager,
    ContextTracker,
    CheckpointManager,
    SessionState,
    ContinuityContext,
    ContinuityCheckpoint,
)


class ExecutionContext(BaseModel):
    """Context for a single execution cycle."""

    session_id: str
    turn_number: int
    metadata: Dict[str, Any] = {}


class SageRuntime:
    """Main runtime engine for SAGE autonomous continuity operations."""

    def __init__(
        self, workspace_path: Optional[str] = None, config: Optional[Dict[str, Any]] = None
    ):
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

        # Initialize continuity intelligence subsystems
        self.session_manager = SessionStateManager(str(self.workspace_path / "sessions"))
        self.context_tracker = ContextTracker(
            str(self.workspace_path / "context"), session_manager=self.session_manager
        )
        self.checkpoint_manager = CheckpointManager(str(self.workspace_path / "checkpoints"))

        # Initialize validation system
        from sage.validation import ValidationSystem

        self.validation = ValidationSystem(self.memory, self.archive)

        # Load existing state if available, otherwise init fresh
        self.current_state = RuntimeState()
        self._load_state()

        # Telemetry
        from sage.runtime.metrics import get_metrics_collector
        metrics = get_metrics_collector()
        metrics.increment("runtime.initialization")
        metrics.record_event("runtime_initialized", {"workspace": str(self.workspace_path)})

        # Controlled Initialization Sequence
        from sage.runtime.diagnostics import InitializationManager
        self.init_mgr = InitializationManager(self)
        self.init_summary = self.init_mgr.run_init_sequence()

    def start(self) -> None:
        """Start the SAGE runtime."""
        self.active = True
        from sage.runtime.metrics import get_metrics_collector
        metrics = get_metrics_collector()
        metrics.set_gauge("runtime.active", 1.0)
        metrics.record_event("runtime_started")

    def stop(self) -> None:
        """Stop the SAGE runtime."""
        self.active = False
        from sage.runtime.metrics import get_metrics_collector
        metrics = get_metrics_collector()
        metrics.set_gauge("runtime.active", 0.0)
        metrics.record_event("runtime_stopped")

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
        old_objective = self.current_state.current_objective or "None"
        self.current_state.current_objective = objective
        self._save_state()

        session_id = f"session_{uuid.uuid4().hex[:8]}"
        self.acr.add_session_link(session_id)

        # Create structured SessionState and transition context
        self.session_manager.create_session(
            session_id=session_id,
            active_objectives=[objective],
            metadata={"source": "set_objective"}
        )
        self.context_tracker.record_transition(
            from_state=f"objective:{old_objective}",
            to_state=f"objective:{objective}",
            reason="Objective updated via set_objective"
        )

        self.context = ExecutionContext(
            session_id=session_id,
            turn_number=self.acr.get_session_depth(),
            metadata={"objective": objective},
        )

        from sage.runtime.metrics import get_metrics_collector
        metrics = get_metrics_collector()
        metrics.increment("objectives.total")
        metrics.record_event("objective_set", {"objective": objective, "session_id": session_id})

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
                metadata={"task": task},
            )

        # Update SessionState
        session_state = self.session_manager.retrieve_session(session_id)
        if not session_state:
            session_state = self.session_manager.create_session(
                session_id=session_id,
                active_objectives=[self.current_state.current_objective] if self.current_state.current_objective else [],
            )
        session_state.add_pending_action(f"task:{task}")
        self.session_manager.save_session(session_state)

        from sage.runtime.metrics import get_metrics_collector
        metrics = get_metrics_collector()
        metrics.increment("tasks.total")
        metrics.record_event("task_set", {"task": task, "session_id": session_id})
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
            "session_depth": self.acr.get_session_depth(),
        }

    def checkpoint(self) -> str:
        """Create a checkpoint of the entire runtime state.

        Returns:
            ID of the created checkpoint.
        """
        checkpoint_id = f"checkpoint_{uuid.uuid4().hex[:8]}"
        checkpoint_file = self.workspace_path / f"{checkpoint_id}.json"

        try:
            with open(checkpoint_file, "w") as f:
                json.dump(self.export_all(), f, indent=2, default=str)
        except Exception:
            pass

        # Create structured ContinuityCheckpoint
        try:
            self.checkpoint_manager.create_checkpoint(
                current_sage_state=self.current_state.model_dump(),
                active_goals=[
                    self.current_state.current_objective or "",
                    self.current_state.active_task or "",
                ],
                recent_decisions=[d.id for d in self.decisions.list_all()[-5:]],
                validation_status=self.verify_integrity(),
                checkpoint_id=checkpoint_id,
            )
        except Exception:
            pass

        from sage.runtime.metrics import get_metrics_collector
        metrics = get_metrics_collector()
        metrics.increment("checkpoints.total")
        metrics.record_event("checkpoint_created", {"checkpoint_id": checkpoint_id})
        return checkpoint_id

    def export_all(self) -> Dict[str, Any]:
        """Export all runtime databases and current state as a single state map.

        Returns:
            Dictionary representation of all runtime state and databases.
        """
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "state": self.current_state.model_dump(),
            "memory": [obj.model_dump() for obj in self.memory.list_all()],
            "archive": [entry.model_dump() for entry in self.archive.list_all()],
            "decisions": [d.model_dump() for d in self.decisions.list_all()],
            "lineage": self.acr.get_lineage(),
            "sessions": [s.model_dump() for s in self.session_manager.list_all()],
            "context": self.context_tracker.get_current_context().model_dump() if self.context_tracker.get_current_context() else None,
            "continuity_checkpoints": [c.model_dump() for c in self.checkpoint_manager.list_all()],
        }

    def generate_handoff(self, target_path: Optional[str] = None) -> str:
        """Generate a continuity handoff artifact.

        Args:
            target_path: Optional path to save handoff JSON.

        Returns:
            The handoff JSON path.
        """
        handoff_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "state": self.current_state.model_dump(),
            "lineage": self.acr.get_lineage(),
            "metadata": {
                "memory_count": len(self.memory.list_all()),
                "archive_count": len(self.archive.list_all()),
                "decision_count": len(self.decisions.list_all()),
            },
            "sessions": [s.model_dump() for s in self.session_manager.list_all()],
            "context": self.context_tracker.get_current_context().model_dump() if self.context_tracker.get_current_context() else None,
            "continuity_checkpoints": [c.model_dump() for c in self.checkpoint_manager.list_all()],
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

            # Restore sessions
            for item in handoff_data.get("sessions", []):
                try:
                    sess = SessionState(**item)
                    self.session_manager.save_session(sess)
                except Exception:
                    pass

            # Restore context
            context_data = handoff_data.get("context")
            if context_data:
                try:
                    ctx = ContinuityContext(**context_data)
                    self.context_tracker.save_context(ctx)
                except Exception:
                    pass

            # Restore checkpoints
            for item in handoff_data.get("continuity_checkpoints", []):
                try:
                    chk = ContinuityCheckpoint(**item)
                    self.checkpoint_manager.save_checkpoint(chk)
                except Exception:
                    pass

            # Initialize context
            if self.current_state.current_objective:
                self.context = ExecutionContext(
                    session_id=self.acr.get_parent_session() or f"session_{uuid.uuid4().hex[:8]}",
                    turn_number=self.acr.get_session_depth() + 1,
                    metadata={"objective": self.current_state.current_objective},
                )
            return True
        except Exception:
            return False

    def _load_state(self) -> None:
        """Load state.json from workspace."""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r") as f:
                    data = json.load(f)
                    self.current_state = RuntimeState(**data)
            except Exception:
                pass

    def _save_state(self) -> None:
        """Save state.json to workspace."""
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.state_file, "w") as f:
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
                    with open(p, "r") as f:
                        checkpoints_data[p.stem] = json.load(f)
                except Exception:
                    pass

        # Gathers snapshot data
        snapshot_data = {
            "id": snapshot_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "state": self.current_state.model_dump(),
            "memory": [obj.model_dump() for obj in self.memory.list_all()],
            "archive": [entry.model_dump() for entry in self.archive.list_all()],
            "decisions": [d.model_dump() for d in self.decisions.list_all()],
            "checkpoints": checkpoints_data,
            "lineage": self.acr.get_lineage(),
            "continuity_state": self.acr.continuity_state,
            "sessions": [s.model_dump() for s in self.session_manager.list_all()],
            "context": self.context_tracker.get_current_context().model_dump() if self.context_tracker.get_current_context() else None,
            "continuity_checkpoints": [c.model_dump() for c in self.checkpoint_manager.list_all()],
        }

        # Save to .sage/sage_state.json
        state_path = Path(".sage/sage_state.json")
        state_path.parent.mkdir(parents=True, exist_ok=True)

        snapshots_registry = {"snapshots": {}}
        if state_path.exists():
            try:
                with open(state_path, "r") as f:
                    snapshots_registry = json.load(f)
                    if "snapshots" not in snapshots_registry:
                        snapshots_registry["snapshots"] = {}
            except Exception:
                pass

        snapshots_registry["snapshots"][snapshot_id] = snapshot_data

        with open(state_path, "w") as f:
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
            with open(state_path, "r") as f:
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
            with open(state_path, "r") as f:
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

        # Sessions
        if self.session_manager.storage_path.exists():
            for p in self.session_manager.storage_path.glob("*.json"):
                try:
                    p.unlink()
                except Exception:
                    pass
        self.session_manager.sessions.clear()

        # Context
        if self.context_tracker.storage_path.exists():
            for p in self.context_tracker.storage_path.glob("*.json"):
                try:
                    p.unlink()
                except Exception:
                    pass
        self.context_tracker.context = None

        # Checkpoints (Continuity)
        if self.checkpoint_manager.storage_path.exists():
            for p in self.checkpoint_manager.storage_path.glob("*.json"):
                try:
                    p.unlink()
                except Exception:
                    pass
        self.checkpoint_manager.checkpoints.clear()

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
                with open(self.archive_path / f"{entry.id}.json", "w") as f:
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
                with open(self.workspace_path / f"{checkpoint_id}.json", "w") as f:
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

        # Restore sessions
        for item in snapshot_data.get("sessions", []):
            try:
                sess = SessionState(**item)
                self.session_manager.save_session(sess)
            except Exception:
                pass

        # Restore context
        context_data = snapshot_data.get("context")
        if context_data:
            try:
                ctx = ContinuityContext(**context_data)
                self.context_tracker.save_context(ctx)
            except Exception:
                pass

        # Restore continuity checkpoints
        for item in snapshot_data.get("continuity_checkpoints", []):
            try:
                chk = ContinuityCheckpoint(**item)
                self.checkpoint_manager.save_checkpoint(chk)
            except Exception:
                pass

        # 8. Re-initialize context if needed
        if self.current_state.current_objective:
            self.context = ExecutionContext(
                session_id=self.acr.get_parent_session() or f"session_{uuid.uuid4().hex[:8]}",
                turn_number=self.acr.get_session_depth() + 1,
                metadata={"objective": self.current_state.current_objective},
            )

        return True

    def ingest_session_payload(self, payload: ExternalSessionPayload) -> Dict[str, Any]:
        """Execute the single, authoritative continuity ingestion path.

        Path: External Session -> Ingest Interface -> AutonomousContinuityRuntime
              -> Intake -> Classification -> Validation -> Archive Routing
              -> Persistence -> Decision Tracking -> Evidence Tracking
              -> Checkpoint -> Workspace Snapshot -> Restoration
        """
        # --- 1. Intake ---
        session_id = payload.session_id or f"session_{uuid.uuid4().hex[:8]}"
        self.acr.add_session_link(session_id)

        # Initialize structured session state
        session_state = self.session_manager.create_session(
            session_id=session_id,
            active_objectives=[payload.objective],
            metadata=payload.metadata,
        )
        if payload.task:
            session_state.add_pending_action(f"task:{payload.task}")
            self.context_tracker.add_unresolved_item(f"task:{payload.task}")

        # --- 2. Classification ---
        self.current_state.current_objective = payload.objective
        if payload.task:
            self.current_state.active_task = payload.task

        # Process and classify memories
        ingested_memories = []
        for m_data in payload.memories:
            obj_id = m_data.get("id") or str(uuid.uuid4())
            conf_str = m_data.get("confidence") or "hypothesis"
            obj_type = m_data.get("object_type") or "general"

            m_obj = MemoryObject(
                id=obj_id,
                object_type=obj_type,
                content=m_data.get("content") or {},
                tags=m_data.get("tags") or [],
                confidence=ConfidenceLevel(conf_str),
            )
            ingested_memories.append(m_obj)

        # Process and classify decisions
        ingested_decisions = []
        for d_data in payload.decisions:
            dec_id = d_data.get("id") or str(uuid.uuid4())
            dec_type_str = d_data.get("decision_type") or "technical"

            d_entry = DecisionEntry(
                id=dec_id,
                decision_type=DecisionType(dec_type_str),
                description=d_data.get("description") or "",
                rationale=d_data.get("rationale") or "",
                evidence=d_data.get("evidence") or [],
                outcome=d_data.get("outcome"),
            )
            ingested_decisions.append(d_entry)

        # --- 3. Validation ---
        validation_results = {}
        for m_obj in ingested_memories:
            # Store in Memory first (Persistence)
            self.memory.store(m_obj)
            is_valid, failed_rules = self.validation.validate_memory(m_obj.id)
            validation_results[m_obj.id] = {"is_valid": is_valid, "failed_rules": failed_rules}

            # Record action completion
            session_state.add_completed_action(f"ingest_memory:{m_obj.id}")
            self.context_tracker.add_recent_change(f"Ingested memory: {m_obj.id}")

        # --- 4. Archive Routing & 5. Persistence ---
        routed_archive_ids = []
        for m_obj in ingested_memories:
            v_res = validation_results[m_obj.id]
            if v_res["is_valid"]:
                should_archive = (
                    m_obj.confidence == ConfidenceLevel.ARCHIVED
                    or m_obj.content.get("archive") is True
                )
                if should_archive:
                    success, archive_id_or_err = self.validation.promote_to_archive(
                        m_obj.id,
                        title=m_obj.content.get("title") or f"Archived Ingestion {m_obj.id}",
                        tags=m_obj.tags,
                    )
                    if success:
                        routed_archive_ids.append(archive_id_or_err)
                        session_state.add_archive_reference(archive_id_or_err)
                        self.context_tracker.add_recent_change(f"Promoted {m_obj.id} to archive: {archive_id_or_err}")
                else:
                    self.validation.promote_to_validated(m_obj.id)

        # Persist runtime state changes
        self._save_state()

        # --- 6. Decision Tracking & 7. Evidence Tracking ---
        tracked_decision_ids = []
        for d_entry in ingested_decisions:
            dec_id = self.decisions.record_decision(
                decision_type=d_entry.decision_type,
                description=d_entry.description,
                rationale=d_entry.rationale,
                evidence=d_entry.evidence,
                decision_id=d_entry.id,
            )
            tracked_decision_ids.append(dec_id)
            session_state.add_decision(dec_id)
            self.context_tracker.add_recent_change(f"Recorded decision: {dec_id}")

            # Evidence tracking
            for ev_id in d_entry.evidence:
                m_obj_to_link = self.memory.retrieve(ev_id)
                if m_obj_to_link:
                    if "decisions" not in m_obj_to_link.content:
                        m_obj_to_link.content["decisions"] = []
                    if dec_id not in m_obj_to_link.content["decisions"]:
                        m_obj_to_link.content["decisions"].append(dec_id)
                    self.memory.store(m_obj_to_link)

                archive_id = f"archive_{ev_id}"
                arch_entry = self.archive.retrieve_entry(archive_id)
                if arch_entry:
                    if dec_id not in arch_entry.decision_history:
                        arch_entry.decision_history.append(dec_id)
                        self.archive.promote_to_archive(arch_entry)

        # Persist the updated SessionState
        self.session_manager.save_session(session_state)

        # --- 8. Checkpoint ---
        checkpoint_id = self.checkpoint()

        # --- 9. Workspace Snapshot ---
        snapshot_id = self.create_workspace_snapshot()

        # --- 10. Restoration ---
        self.context = ExecutionContext(
            session_id=session_id,
            turn_number=self.acr.get_session_depth(),
            metadata={
                "objective": payload.objective,
                "task": payload.task,
                "checkpoint_id": checkpoint_id,
                "snapshot_id": snapshot_id,
            },
        )

        from sage.runtime.metrics import get_metrics_collector
        metrics = get_metrics_collector()
        metrics.increment("ingestions.total")
        metrics.record_event("payload_ingested", {"session_id": session_id, "checkpoint_id": checkpoint_id, "snapshot_id": snapshot_id})

        return {
            "session_id": session_id,
            "checkpoint_id": checkpoint_id,
            "snapshot_id": snapshot_id,
            "ingested_memories": [m.id for m in ingested_memories],
            "routed_archive_entries": routed_archive_ids,
            "tracked_decisions": tracked_decision_ids,
            "validation_results": validation_results,
            "status": "success",
        }

    def reason_over_continuity(self) -> Dict[str, Any]:
        """Reason over stored continuity state, active context, memories, and decisions."""
        all_memories = self.memory.list_all()
        all_decisions = self.decisions.list_all()
        all_archive = self.archive.list_all()
        lineage = self.acr.get_lineage()

        has_objective = bool(self.current_state.current_objective)
        has_task = bool(self.current_state.active_task)
        blockers_count = len(self.current_state.blockers)

        aligned_memories = []
        task_keywords = set((self.current_state.active_task or "").lower().split())
        for m in all_memories:
            tags_lower = {t.lower() for t in m.tags}
            if tags_lower.intersection(task_keywords):
                aligned_memories.append(m.id)

        unsupported_decisions = []
        for d in all_decisions:
            valid_ev_count = 0
            for ev_id in d.evidence:
                if self.memory.retrieve(ev_id) or self.archive.retrieve_entry(f"archive_{ev_id}"):
                    valid_ev_count += 1
            if valid_ev_count == 0 and d.evidence:
                unsupported_decisions.append(d.id)

        suggestions = []
        if self.current_state.blockers:
            suggestions.append(
                f"Resolve the active blockers: {', '.join(self.current_state.blockers)}."
            )
        if not all_decisions:
            suggestions.append(
                "No technical/architectural decisions recorded yet. Document key system choices."
            )
        if has_objective and not has_task:
            suggestions.append(
                "Active objective is set but no task is selected. Define a task to progress."
            )

        return {
            "objective_alignment": "aligned" if (has_objective and has_task) else "needs_alignment",
            "active_blockers_count": blockers_count,
            "session_depth": len(lineage),
            "analyzed_memories_count": len(all_memories),
            "analyzed_decisions_count": len(all_decisions),
            "analyzed_archive_entries_count": len(all_archive),
            "aligned_memories": aligned_memories,
            "unsupported_decisions": unsupported_decisions,
            "suggestions": suggestions,
            "status": "active",
        }

    def verify_integrity(self) -> Dict[str, Any]:
        """Perform repository-side self-verification of data stores and state referential integrity."""
        issues = []

        # 1. Structural Checks
        for name, path in [
            ("Memory Store", self.memory_path),
            ("Master Archive", self.archive_path),
            ("Decisions Store", self.decisions_path),
        ]:
            if not path.exists():
                issues.append(f"{name} directory does not exist at '{path}'.")

        # 2. Syntax/Readability check for persisted JSON files
        loaded_files_count = 0
        corrupted_files = []
        if self.workspace_path.exists():
            for p in self.workspace_path.glob("**/*.json"):
                loaded_files_count += 1
                try:
                    with open(p, "r") as f:
                        json.load(f)
                except Exception as e:
                    corrupted_files.append(str(p))
                    issues.append(f"File {p} is corrupted: {str(e)}")

        # 3. Referential Integrity Check
        missing_evidence = []
        all_decisions = self.decisions.list_all()
        for d in all_decisions:
            for ev_id in d.evidence:
                m_obj = self.memory.retrieve(ev_id)
                arch_entry = self.archive.retrieve_entry(
                    f"archive_{ev_id}"
                ) or self.archive.retrieve_entry(ev_id)
                if not m_obj and not arch_entry:
                    missing_evidence.append({"decision_id": d.id, "evidence_id": ev_id})
                    issues.append(f"Decision '{d.id}' references non-existent evidence '{ev_id}'.")

        # 4. Lineage Continuity Check
        lineage = self.acr.get_lineage()
        lineage_valid = True
        if not lineage and self.current_state.current_objective:
            lineage_valid = False
            issues.append("Lineage is empty but an active objective is set.")

        return {
            "is_valid": len(issues) == 0,
            "loaded_files_count": loaded_files_count,
            "corrupted_files": corrupted_files,
            "referential_integrity": {
                "missing_evidence_links": missing_evidence,
                "decisions_analyzed": len(all_decisions),
            },
            "lineage_valid": lineage_valid,
            "issues": issues,
        }
