"""SAGE Command Center engine - providing deep, structured, multi-view operational visibility."""

from typing import Dict, Any
import os
from pathlib import Path
from datetime import datetime, timezone
from sage.runtime.health import check_health


class CommandCenter:
    """SAGE Command Center v1 engine."""

    def __init__(self, runtime: Any):
        """Initialize SAGE Command Center with the active SAGE runtime instance."""
        self.runtime = runtime

    def get_visibility_payload(self) -> Dict[str, Any]:
        """Compile and return SAGE Command Center operational visibility status across all 4 key views."""
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "current_system_view": self._get_current_system_view(),
            "archive_view": self._get_archive_view(),
            "runtime_view": self._get_runtime_view(),
            "continuity_view": self._get_continuity_view(),
        }

    def _get_current_system_view(self) -> Dict[str, Any]:
        """View 1: Current System View."""
        # 1. Runtime Status
        runtime_status = "active" if getattr(self.runtime, "active", False) else "inactive"

        # 2. Current Milestone
        current_milestone = (
            "Milestone 2.3 - Full Integration Activation & Portability Bridge Candidate"
        )
        # Try to parse from ROADMAP.md if present
        roadmap_path = Path("docs/master/ROADMAP.md")
        if roadmap_path.exists():
            try:
                with open(roadmap_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip().startswith("## Milestone") or line.strip().startswith(
                            "### Milestone"
                        ):
                            current_milestone = line.strip().lstrip("#").strip()
                            break
            except Exception:
                pass

        # 3. Active Task
        active_task = "None"
        if hasattr(self.runtime, "current_state") and self.runtime.current_state is not None:
            active_task = getattr(self.runtime.current_state, "active_task", "None") or "None"

        # 4. Blockers
        blockers = []
        if hasattr(self.runtime, "current_state") and self.runtime.current_state is not None:
            blockers = getattr(self.runtime.current_state, "blockers", []) or []

        # 5. Last Checkpoint
        last_checkpoint = "None"
        try:
            workspace = getattr(self.runtime, "workspace_path", Path("sage_data"))
            checkpoints_dir = workspace / "checkpoints"
            chk_files = []
            if checkpoints_dir.exists():
                chk_files = list(checkpoints_dir.glob("checkpoint_*.json"))
            if not chk_files and workspace.exists():
                chk_files = list(workspace.glob("checkpoint_*.json"))
            if chk_files:
                newest = max(chk_files, key=lambda p: p.stat().st_mtime)
                last_checkpoint = newest.name
        except Exception:
            pass

        # 6. Validation State
        validation_state = {"is_valid": True, "issues": []}
        if hasattr(self.runtime, "verify_integrity"):
            try:
                validation_state = self.runtime.verify_integrity()
            except Exception as e:
                validation_state = {
                    "is_valid": False,
                    "issues": [f"Integrity check crashed: {str(e)}"],
                }

        return {
            "runtime_status": runtime_status,
            "current_milestone": current_milestone,
            "active_task": active_task,
            "blockers": blockers,
            "last_checkpoint": last_checkpoint,
            "validation_state": validation_state,
        }

    def _get_archive_view(self) -> Dict[str, Any]:
        """View 2: Archive View."""
        # 1. Master Archive Status
        master_archive_status = (
            "available"
            if hasattr(self.runtime, "archive") and self.runtime.archive is not None
            else "unavailable"
        )

        # 2. Latest Reports
        latest_reports = []
        # Query latest memories in store that are validation_report or raw reports
        if hasattr(self.runtime, "memory") and self.runtime.memory is not None:
            try:
                # Get last 5 memories of type validation_report
                reports = self.runtime.memory.search_by_type("validation_report")
                latest_reports = [r.model_dump() for r in reports[-5:]]
            except Exception:
                pass

        # 3. Recent Decisions
        recent_decisions = []
        if hasattr(self.runtime, "decisions") and self.runtime.decisions is not None:
            try:
                recent_decisions = [d.model_dump() for d in self.runtime.decisions.list_all()[-5:]]
            except Exception:
                pass

        # 4. Recent Operational Records
        recent_operational_records = []
        if hasattr(self.runtime, "archive") and self.runtime.archive is not None:
            try:
                recent_operational_records = [
                    entry.model_dump() for entry in self.runtime.archive.list_all()[-5:]
                ]
            except Exception:
                pass

        return {
            "master_archive_status": master_archive_status,
            "latest_reports": latest_reports,
            "recent_decisions": recent_decisions,
            "recent_operational_records": recent_operational_records,
        }

    def _get_runtime_view(self) -> Dict[str, Any]:
        """View 3: Runtime View."""
        # 1. Health Status
        health_status = check_health(self.runtime)

        # 2. API Status
        api_status = {
            "status": "online",
            "version": "1.1.0",
            "framework": "FastAPI",
            "port": int(os.getenv("PORT", "8000")),
            "host": os.getenv("HOST", "0.0.0.0"),
            "require_auth": os.getenv("SAGE_REQUIRE_AUTH", "false").lower() == "true",
        }

        # 3. Active Connectors
        openai_key = os.getenv("OPENAI_API_KEY") or os.getenv("SAGE_API_KEYS")
        gemini_key = os.getenv("GEMINI_API_KEY")
        gw_creds_path = os.getenv("GOOGLE_WORKSPACE_CREDENTIALS_PATH", ".sage/credentials.json")
        gw_configured = Path(gw_creds_path).exists()
        gh_secret = os.getenv("GITHUB_WEBHOOK_SECRET")
        render_production = os.getenv("ENV") == "production"

        active_connectors = {
            "OpenAI / ChatGPT": "CONNECTED" if openai_key else "NOT CONFIGURED",
            "Google AI / Gemini": "CONNECTED" if gemini_key else "NOT CONFIGURED",
            "Jules": "CONNECTED" if gemini_key else "NOT CONFIGURED",
            "Google Workspace": "CONNECTED" if gw_configured else "NOT CONFIGURED",
            "GitHub": "CONNECTED" if gh_secret else "NOT CONFIGURED",
            "Render": "CONNECTED" if render_production else "NOT CONFIGURED",
        }

        # 4. Environment Readiness
        environment_readiness = {
            "SAGE_REQUIRE_AUTH": os.getenv("SAGE_REQUIRE_AUTH", "false").lower() == "true",
            "SAGE_API_KEYS": "configured" if os.getenv("SAGE_API_KEYS") else "missing",
            "GITHUB_WEBHOOK_SECRET": "configured" if gh_secret else "missing",
            "GEMINI_API_KEY": "configured" if gemini_key else "missing",
            "GOOGLE_WORKSPACE_CREDENTIALS_PATH": "configured" if gw_configured else "missing",
        }

        return {
            "health_status": health_status,
            "api_status": api_status,
            "active_connectors": active_connectors,
            "environment_readiness": environment_readiness,
        }

    def _get_continuity_view(self) -> Dict[str, Any]:
        """View 4: Continuity View."""
        # 1. Latest Session State
        latest_session_state = {}
        if hasattr(self.runtime, "current_state") and self.runtime.current_state is not None:
            try:
                latest_session_state = self.runtime.current_state.model_dump()
            except Exception:
                latest_session_state = {
                    "current_objective": getattr(
                        self.runtime.current_state, "current_objective", None
                    ),
                    "active_task": getattr(self.runtime.current_state, "active_task", None),
                    "blockers": getattr(self.runtime.current_state, "blockers", []),
                    "dependencies": getattr(self.runtime.current_state, "dependencies", []),
                }

        # 2. Checkpoint History
        checkpoint_history = []
        try:
            workspace = getattr(self.runtime, "workspace_path", Path("sage_data"))
            checkpoints_dir = workspace / "checkpoints"
            chk_files = []
            if checkpoints_dir.exists():
                chk_files = list(checkpoints_dir.glob("checkpoint_*.json"))
            if not chk_files and workspace.exists():
                chk_files = list(workspace.glob("checkpoint_*.json"))

            for f in chk_files:
                checkpoint_history.append(
                    {
                        "id": f.stem,
                        "filename": f.name,
                        "created_at": datetime.fromtimestamp(
                            f.stat().st_mtime, timezone.utc
                        ).isoformat(),
                        "size_bytes": f.stat().st_size,
                    }
                )
            # Sort newest first
            checkpoint_history.sort(key=lambda x: x["created_at"], reverse=True)
        except Exception:
            pass

        # 3. Restoration Readiness
        restoration_readiness = {
            "checkpoints_dir_exists": False,
            "can_restore": False,
            "active_sessions_count": 0,
        }
        try:
            workspace = getattr(self.runtime, "workspace_path", Path("sage_data"))
            restoration_readiness["checkpoints_dir_exists"] = (
                workspace / "checkpoints"
            ).exists() or workspace.exists()
            restoration_readiness["can_restore"] = len(checkpoint_history) > 0

            sessions_dir = workspace / "sessions"
            if sessions_dir.exists():
                restoration_readiness["active_sessions_count"] = len(
                    list(sessions_dir.glob("session_*.json"))
                )
        except Exception:
            pass

        return {
            "latest_session_state": latest_session_state,
            "checkpoint_history": checkpoint_history,
            "restoration_readiness": restoration_readiness,
        }
