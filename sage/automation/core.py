"""Automation Layer for SAGE - unattended background scheduling, self-healing, and auto-checkpointing."""

from typing import List, Dict, Any, Callable, Optional


class AutomationScheduler:
    """Task scheduler for running background automation scripts and recurring tasks."""

    def __init__(self):
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.execution_history: List[Dict[str, Any]] = []

    def schedule_job(
        self, name: str, job_callable: Callable[[], Any], interval_seconds: int = 60
    ) -> None:
        """Register a job to run periodically."""
        self.jobs[name] = {
            "callable": job_callable,
            "interval": interval_seconds,
            "active": True,
            "execution_count": 0,
        }

    def execute_active_jobs(self) -> int:
        """Manually trigger a tick cycle to execute all active jobs."""
        executed = 0
        for name, info in self.jobs.items():
            if info["active"]:
                try:
                    result = info["callable"]()
                    info["execution_count"] += 1
                    self.execution_history.append(
                        {"job": name, "status": "success", "result": result}
                    )
                except Exception as e:
                    self.execution_history.append(
                        {"job": name, "status": "failed", "error": str(e)}
                    )
                executed += 1
        return executed


class SelfHealingPolicy:
    """Policy engine to evaluate health of SAGE Runtime and apply automated recovery/rollback."""

    def __init__(self, runtime_instance: Any):
        """Initialize with SAGE Runtime instance."""
        self.runtime = runtime_instance

    def run_health_check(self) -> Dict[str, Any]:
        """Assess runtime state and look for blockers or resource limits."""
        status = self.runtime.get_status()
        has_blockers = len(status.get("blockers", [])) > 0

        # Self-healing recommendation
        action = "none"
        if has_blockers:
            action = "remediate_blockers"
        elif status.get("session_depth", 0) > 10:
            action = "consolidate_sessions"

        return {
            "healthy": not has_blockers,
            "recommended_action": action,
            "blocker_count": len(status.get("blockers", [])),
        }

    def heal(self) -> bool:
        """Attempt to self-heal based on health recommendations."""
        check = self.run_health_check()
        action = check["recommended_action"]

        if action == "remediate_blockers":
            # Heuristically auto-resolve non-fatal blockers
            blockers = list(self.runtime.current_state.blockers)
            for blocker in blockers:
                if (
                    "temporary" in blocker.lower()
                    or "minor" in blocker.lower()
                    or "timeout" in blocker.lower()
                ):
                    self.runtime.resolve_blocker(blocker)
            return True

        elif action == "consolidate_sessions":
            # Trigger automatic checkpointing and clean history
            self.runtime.checkpoint()
            self.runtime.acr.clear_state()
            return True

        return False


class ProactiveCheckpointer:
    """Auto-checkpointing engine that watches task progression."""

    def __init__(self, runtime_instance: Any, max_tasks_before_checkpoint: int = 5):
        self.runtime = runtime_instance
        self.max_tasks_before_checkpoint = max_tasks_before_checkpoint
        self.task_counter = 0

    def increment_and_evaluate(self) -> Optional[str]:
        """Call whenever a task changes or is processed; triggers checkpoint if limit met."""
        self.task_counter += 1
        if self.task_counter >= self.max_tasks_before_checkpoint:
            checkpoint_id = self.runtime.checkpoint()
            self.task_counter = 0
            return checkpoint_id
        return None
