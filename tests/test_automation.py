"""Tests for SAGE Automation Layer."""

import pytest
import tempfile
from pathlib import Path
from sage.runtime import SageRuntime
from sage.automation.core import AutomationScheduler, SelfHealingPolicy, ProactiveCheckpointer


@pytest.fixture
def temp_workspace():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_automation_scheduler():
    """Test background scheduler job registration and tick execution."""
    scheduler = AutomationScheduler()
    called = 0

    def job():
        nonlocal called
        called += 1
        return "job_done"

    scheduler.schedule_job("test_job", job, interval_seconds=1)
    assert len(scheduler.jobs) == 1
    assert scheduler.jobs["test_job"]["execution_count"] == 0

    executed = scheduler.execute_active_jobs()
    assert executed == 1
    assert called == 1
    assert scheduler.jobs["test_job"]["execution_count"] == 1
    assert len(scheduler.execution_history) == 1
    assert scheduler.execution_history[0]["result"] == "job_done"


def test_self_healing_remediate_blockers(temp_workspace):
    """Test self-healing policies identifying and healing minor blockers."""
    runtime = SageRuntime(str(temp_workspace))
    healing = SelfHealingPolicy(runtime)

    # 1. Initially healthy
    check_healthy = healing.run_health_check()
    assert check_healthy["healthy"] is True
    assert check_healthy["recommended_action"] == "none"

    # 2. Add temporary blocker
    runtime.add_blocker("Minor Database Connection Timeout")
    check_unhealthy = healing.run_health_check()
    assert check_unhealthy["healthy"] is False
    assert check_unhealthy["recommended_action"] == "remediate_blockers"

    # 3. Trigger healing
    healed = healing.heal()
    assert healed is True

    # Verify blocker was automatically resolved
    status = runtime.get_status()
    assert len(status["blockers"]) == 0


def test_proactive_checkpointer(temp_workspace):
    """Test proactive checkpointer auto-checkpoint execution."""
    runtime = SageRuntime(str(temp_workspace))
    checkpointer = ProactiveCheckpointer(runtime, max_tasks_before_checkpoint=3)

    # First two progression ticks do not trigger checkpoint
    assert checkpointer.increment_and_evaluate() is None
    assert checkpointer.increment_and_evaluate() is None

    # Third progression tick triggers a checkpoint ID
    chk_id = checkpointer.increment_and_evaluate()
    assert chk_id is not None
    assert chk_id.startswith("checkpoint_")

    # Counter resets
    assert checkpointer.task_counter == 0
