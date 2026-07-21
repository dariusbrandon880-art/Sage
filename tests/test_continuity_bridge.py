"""Tests for SAGE Autonomous Continuity Runtime (ACR) Continuity Bridge (ingest, reason, verify)."""

import pytest
import tempfile
import json
from pathlib import Path
from sage.models import (
    MemoryObject,
    ConfidenceLevel,
    DecisionType,
    ArchiveEntry,
    KnowledgeState,
    ExternalSessionPayload,
)
from sage.runtime import SageRuntime


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_continuity_bridge_ingest_pipeline(temp_workspace):
    """Test the single, authoritative ingest_session_payload pathway end-to-end."""
    runtime = SageRuntime(str(temp_workspace))

    # Construct the ingestion payload
    payload_data = {
        "session_id": "session_external_123",
        "objective": "Build the single unified SAGE platform",
        "task": "Implement the core ingestion interface",
        "memories": [
            {
                "id": "mem_rule_001",
                "object_type": "rule",
                "content": {
                    "title": "Ingestion Rule",
                    "description": "All payloads must follow the single authoritative path",
                    "archive": True,  # Request routing to master archive
                },
                "tags": ["architecture", "core"],
                "confidence": "validated",
            },
            {
                "id": "mem_fact_002",
                "object_type": "fact",
                "content": {"description": "Verification uses standard pytest-based test suites"},
                "tags": ["testing"],
                "confidence": "hypothesis",
            },
        ],
        "decisions": [
            {
                "id": "dec_arch_001",
                "decision_type": "architectural",
                "description": "Establish standard bridge pathway",
                "rationale": "Enforces complete rehydration and validation rules with zero bypasses",
                "evidence": ["mem_rule_001"],
            }
        ],
        "metadata": {"source": "ci_pipeline"},
    }

    payload = ExternalSessionPayload(**payload_data)

    # Trigger single authoritative path
    result = runtime.ingest_session_payload(payload)

    assert result["status"] == "success"
    assert result["session_id"] == "session_external_123"
    assert "checkpoint_id" in result
    assert "snapshot_id" in result

    # 1. Intake: Assert session ID is registered in lineage
    assert "session_external_123" in runtime.acr.get_lineage()

    # 2. Classification & Restoration: Assert active context is loaded/rehydrated
    assert runtime.current_state.current_objective == "Build the single unified SAGE platform"
    assert runtime.current_state.active_task == "Implement the core ingestion interface"
    assert runtime.context is not None
    assert runtime.context.session_id == "session_external_123"

    # 3. Validation: Check that both memories were stored
    mem1 = runtime.memory.retrieve("mem_rule_001")
    mem2 = runtime.memory.retrieve("mem_fact_002")
    assert mem1 is not None
    assert mem2 is not None

    # 4. Archive Routing: mem_rule_001 should be routed to Master Archive (due to archive=True or archived confidence)
    # Validate result lists it in routed entries
    assert "archive_mem_rule_001" in result["routed_archive_entries"]
    arch_entry = runtime.archive.retrieve_entry("archive_mem_rule_001")
    assert arch_entry is not None
    assert arch_entry.title == "Ingestion Rule"
    assert "architecture" in arch_entry.tags

    # Memory state for mem_rule_001 should be ARCHIVED
    assert mem1.confidence == ConfidenceLevel.ARCHIVED

    # mem_fact_002 is not marked for archiving, so it should be promoted to VALIDATED (since it's structurally valid)
    assert mem2.confidence == ConfidenceLevel.VALIDATED

    # 5. Decision & Evidence Tracking: check decision is recorded and links established
    dec = runtime.decisions.retrieve_decision("dec_arch_001")
    assert dec is not None
    assert dec.decision_type == DecisionType.ARCHITECTURAL
    assert dec.evidence == ["mem_rule_001"]

    # Verify memory links back to the decision
    updated_mem1 = runtime.memory.retrieve("mem_rule_001")
    assert "decisions" in updated_mem1.content
    assert "dec_arch_001" in updated_mem1.content["decisions"]

    # Verify archive entry links back to the decision
    updated_arch = runtime.archive.retrieve_entry("archive_mem_rule_001")
    assert "dec_arch_001" in updated_arch.decision_history

    # 6. Checkpoint & Snapshot: verify files are written
    checkpoint_file = temp_workspace / f"{result['checkpoint_id']}.json"
    assert checkpoint_file.exists()


def test_continuity_reasoning(temp_workspace):
    """Test reasoning over continuity databases."""
    runtime = SageRuntime(str(temp_workspace))

    # Initial state reasoning (no databases populated yet)
    reasoning_empty = runtime.reason_over_continuity()
    assert reasoning_empty["objective_alignment"] == "needs_alignment"
    assert any(
        "No technical/architectural decisions recorded" in sug
        for sug in reasoning_empty["suggestions"]
    )

    # Setup some state
    runtime.set_objective("Launch Mars Shuttle")
    runtime.set_task("Verify fuel booster")
    runtime.add_blocker("Fuel leak in engine B")

    # Store a memory and a decision referencing it
    obj = MemoryObject(
        id="mem_leak_001",
        object_type="report",
        content={"leak_rate": "high"},
        tags=["fuel", "engine"],
        confidence=ConfidenceLevel.HYPOTHESIS,
    )
    runtime.memory.store(obj)

    runtime.decisions.record_decision(
        decision_type=DecisionType.TECHNICAL,
        description="Replace engine B gasket",
        rationale="Seal fuel leakage",
        evidence=["mem_leak_001"],
        decision_id="dec_replace_gasket",
    )

    # Perform continuity reasoning with populated data
    reasoning_full = runtime.reason_over_continuity()
    assert reasoning_full["objective_alignment"] == "aligned"
    assert reasoning_full["active_blockers_count"] == 1
    assert reasoning_full["analyzed_memories_count"] == 1
    assert reasoning_full["analyzed_decisions_count"] == 1
    assert "mem_leak_001" in reasoning_full["aligned_memories"]
    assert len(reasoning_full["unsupported_decisions"]) == 0
    assert any("Resolve the active blockers" in sug for sug in reasoning_full["suggestions"])


def test_self_verification_integrity(temp_workspace):
    """Test self-verification and integrity checking."""
    runtime = SageRuntime(str(temp_workspace))

    # Initial state: verify empty workspace is syntactically valid (but folders exist because runtime initializes them)
    report = runtime.verify_integrity()
    assert report["is_valid"] is True
    assert report["lineage_valid"] is True

    # Record a decision with non-existent evidence to trigger referential integrity violation
    runtime.decisions.record_decision(
        decision_type=DecisionType.PROCESS,
        description="A decision",
        rationale="Just because",
        evidence=["ghost_evidence_id"],
        decision_id="dec_with_ghost",
    )

    # Verify integrity should now report a referential issue
    report_broken = runtime.verify_integrity()
    assert report_broken["is_valid"] is False
    assert len(report_broken["referential_integrity"]["missing_evidence_links"]) == 1
    assert (
        report_broken["referential_integrity"]["missing_evidence_links"][0]["evidence_id"]
        == "ghost_evidence_id"
    )
