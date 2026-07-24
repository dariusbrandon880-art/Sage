"""Unit and integration tests for SAGE 2 concrete Track C.11 Continuity modules and endpoints."""

from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient
from sage.api import app
from sage.runtime import SageRuntime
from sage.acr.session import ContinuityContext, ContextTransition
from sage.models import MemoryObject


@pytest.fixture
def temp_runtime(tmp_path):
    return SageRuntime(workspace_path=str(tmp_path))


def test_state_calibration_sync(temp_runtime):
    # Setup context with an empty transition timestamp
    tx = ContextTransition(
        from_state="milestone:None",
        to_state="milestone:v1.1.0",
        reason="Test calibration",
        timestamp=None,  # Needs calibration!
    )
    context = ContinuityContext(
        current_project_state="active",
        active_milestone="v1.1.0",
        important_context_transitions=[tx],
    )

    res = temp_runtime.calibration_sync.calibrate_context(context)
    assert res["status"] == "synchronized"
    assert res["corrected_count"] == 1
    assert context.important_context_transitions[0].timestamp is not None


def test_state_validator_rules():
    from sage.acr.state_validator import StateValidator

    # 1. Lineage Graph Cycle Check
    assert StateValidator.validate_lineage_trees(["sess_1", "sess_2", "sess_3"]) is True
    assert StateValidator.validate_lineage_trees(["sess_1", "sess_2", "sess_1"]) is False  # Cycle!

    # 2. Rehydration Payload Audit
    valid_payload = {
        "state": {"current_objective": "Build platform core"},
        "lineage": ["sess_1"],
        "sessions": [],
    }
    assert len(StateValidator.validate_rehydration_payload(valid_payload)) == 0

    corrupted_payload = {"state": {}}  # Missing objective and keys!
    errors = StateValidator.validate_rehydration_payload(corrupted_payload)
    assert len(errors) > 0


def test_memory_importance_pipeline(temp_runtime):
    # Add a memory object
    m_obj = MemoryObject(
        object_type="technical",
        content={"title": "Design Specs"},
        tags=["core", "spec"],
        created_at=datetime.now(timezone.utc) - timedelta(days=14),  # Old! Should decay
    )
    temp_runtime.memory.store(m_obj)

    score = temp_runtime.importance_pipeline.evaluate_object_importance(m_obj)
    # Due to age decay (half-life of 7 days), 14 days is exactly 2 half-lives (decay factor of 0.25)
    # The score should decay significantly below its base
    assert score < 0.3

    audit = temp_runtime.importance_pipeline.run_importance_audit(prunable_threshold=0.5)
    assert audit["total_analyzed"] == 1
    assert m_obj.id in audit["prune_candidates"]


def test_apoptosis_manager_cleanup(temp_runtime):
    temp_runtime.start()
    assert temp_runtime.is_running() is True

    res = temp_runtime.apoptosis_manager.execute_graceful_apoptosis()
    assert res["success"] is True
    assert res["status"] == "terminated"
    assert temp_runtime.is_running() is False


def test_c11_api_endpoints():
    client = TestClient(app)

    # Test Importance Audit Endpoint
    audit_res = client.get("/runtime/importance/audit?threshold=0.9")
    assert audit_res.status_code == 200
    assert "total_analyzed" in audit_res.json()

    # Test Apoptosis Endpoint
    apoptosis_res = client.post("/runtime/apoptosis")
    assert apoptosis_res.status_code == 200
    assert apoptosis_res.json()["success"] is True
