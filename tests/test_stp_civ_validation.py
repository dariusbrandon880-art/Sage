"""Tests for SAGE 2 State Transition Protocol (STP) and CIV-001 (Continuity Independence Validation)."""

import pytest
import tempfile
import json
from pathlib import Path

from sage.models import (
    MemoryObject,
    ConfidenceLevel,
    DecisionType,
    ExternalSessionPayload,
)
from sage.runtime import SageRuntime


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_stp_transition_engine_integrity(temp_workspace):
    """Verify State Transition Protocol (STP) integrity: state mutations (S0 -> Delta -> Evidence -> Validation -> S1)."""
    runtime = SageRuntime(str(temp_workspace))

    # 1. State S0 (Initial State)
    assert runtime.current_state.current_objective is None
    assert runtime.current_state.active_task is None
    assert len(runtime.current_state.blockers) == 0

    # 2. Define Delta (External Ingestion Payload)
    payload_data = {
        "session_id": "stp_verification_session_01",
        "objective": "Verify SAGE 2 Core STP Mutators",
        "task": "Perform transactional transition validation",
        "memories": [
            {
                "id": "mem_stp_evidence_01",
                "object_type": "evidence",
                "content": {
                    "assertion": "STP guarantees transactional state integrity across SAGE subsystems"
                },
                "tags": ["stp", "validation"],
                "confidence": "hypothesis",
            }
        ],
        "decisions": [
            {
                "id": "dec_stp_rule_01",
                "decision_type": "architectural",
                "description": "Lock STP execution paths to single ingestion gateway",
                "rationale": "Prevents out-of-order state mutations and guarantees audit lineage",
                "evidence": ["mem_stp_evidence_01"],
            }
        ],
    }
    payload = ExternalSessionPayload(**payload_data)

    # 3. Apply Delta & Execute Validation (State Mutation Sequence)
    result = runtime.ingest_session_payload(payload)

    # 4. State S1 (Final State) Verification
    assert result["status"] == "success"
    assert result["session_id"] == "stp_verification_session_01"

    # Assert Objectives & Tasks (Classification & Restoration)
    assert runtime.current_state.current_objective == "Verify SAGE 2 Core STP Mutators"
    assert runtime.current_state.active_task == "Perform transactional transition validation"

    # Assert Evidence Intake
    mem = runtime.memory.retrieve("mem_stp_evidence_01")
    assert mem is not None
    assert mem.confidence == ConfidenceLevel.VALIDATED  # Autopromoted since it's valid

    # Assert Decision Recording
    dec = runtime.decisions.retrieve_decision("dec_stp_rule_01")
    assert dec is not None
    assert dec.decision_type == DecisionType.ARCHITECTURAL
    assert dec.evidence == ["mem_stp_evidence_01"]

    # Assert Context Transitions are logged
    transitions = runtime.context_tracker.get_current_context().important_context_transitions
    assert len(transitions) > 0
    # Last transition should reflect our objective change
    assert any("Verify SAGE 2 Core STP Mutators" in t.to_state for t in transitions)


def test_civ_001_independence_rehydration(temp_workspace):
    """Verify CIV-001 rehydration: prove zero-copy recovery and archive lineage restoration from snapshot alone."""
    # 1. Setup rich operational state in primary workspace
    runtime = SageRuntime(str(temp_workspace))
    runtime.set_objective("SAGE 2 Production Hardening")
    runtime.set_task("Implement CIV-001 Validation Protocol")
    runtime.add_blocker("A temporary staging blocker")

    # Store a memory and promote it
    m_obj = MemoryObject(
        id="mem_civ_validation_01",
        object_type="rule",
        content={"rule_desc": "All snapshot components must be rehydratable"},
        tags=["civ-001", "rehydration"],
        confidence=ConfidenceLevel.HYPOTHESIS,
    )
    runtime.memory.store(m_obj)
    runtime.validation.promote_to_validated("mem_civ_validation_01")

    # Record an architectural decision
    runtime.decisions.record_decision(
        decision_type=DecisionType.ARCHITECTURAL,
        description="Enforce CIV-001 clean-environment standards",
        rationale="Guarantees operational independence from chat hosts",
        evidence=["mem_civ_validation_01"],
        decision_id="dec_civ_01",
    )

    # Create checkpoints and workspace snapshot
    checkpoint_id = runtime.checkpoint()
    assert checkpoint_id is not None
    snapshot_id = runtime.create_workspace_snapshot()

    # 2. Simulate a completely empty fresh workspace environment
    empty_workspace = temp_workspace / "empty_isolated_env"
    isolated_runtime = SageRuntime(str(empty_workspace))

    assert isolated_runtime.current_state.current_objective is None
    assert isolated_runtime.current_state.active_task is None
    assert len(isolated_runtime.memory.list_all()) == 0

    # Copy the master snapshot file to the empty workspace environment
    # In real deployment, .sage/sage_state.json is committed or transferred
    state_file_src = Path(".sage/sage_state.json")
    state_file_dest = empty_workspace / "sage_state.json"
    state_file_dest.parent.mkdir(parents=True, exist_ok=True)

    with open(state_file_src, "r") as f_src:
        snapshots_data = json.load(f_src)

    with open(state_file_dest, "w") as f_dest:
        json.dump(snapshots_data, f_dest)

    # 3. Restore snapshot on the isolated runtime
    # First we monkeypatch or explicitly restore since restore_workspace_snapshot loads from .sage/sage_state.json
    # We will temporarily point state_path to our empty workspace
    original_state_path = Path(".sage/sage_state.json")
    try:
        # Swap the file temporarily so the restore method reads from it
        if original_state_path.exists():
            original_state_path.rename(temp_workspace / "sage_state_temp.json")

        with open(original_state_path, "w") as f_tmp:
            json.dump(snapshots_data, f_tmp)

        success = isolated_runtime.restore_workspace_snapshot(snapshot_id)
        assert success is True
    finally:
        # Revert swap
        if original_state_path.exists():
            original_state_path.unlink()
        temp_backup = temp_workspace / "sage_state_temp.json"
        if temp_backup.exists():
            temp_backup.rename(original_state_path)

    # 4. Verify 100% Context Rehydration & Lineage Restoration
    assert isolated_runtime.current_state.current_objective == "SAGE 2 Production Hardening"
    assert isolated_runtime.current_state.active_task == "Implement CIV-001 Validation Protocol"
    assert "A temporary staging blocker" in isolated_runtime.current_state.blockers

    # Check memories
    restored_mem = isolated_runtime.memory.retrieve("mem_civ_validation_01")
    assert restored_mem is not None
    assert restored_mem.confidence == ConfidenceLevel.VALIDATED
    assert "civ-001" in restored_mem.tags

    # Check decisions
    restored_dec = isolated_runtime.decisions.retrieve_decision("dec_civ_01")
    assert restored_dec is not None
    assert restored_dec.description == "Enforce CIV-001 clean-environment standards"
    assert restored_dec.evidence == ["mem_civ_validation_01"]

    # Verify self-integrity check passes on the rehydrated runtime
    report = isolated_runtime.verify_integrity()
    assert report["is_valid"] is True
    assert report["lineage_valid"] is True
