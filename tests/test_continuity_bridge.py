"""Tests for SAGE Autonomous Continuity Runtime (ACR) Continuity Bridge (ingest, reason, verify)."""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch

from sage.models import (
    MemoryObject,
    ConfidenceLevel,
    DecisionType,
    ExternalSessionPayload,
)
from sage.runtime import SageRuntime
from sage.cli import main as cli_main
from sage.integration import (
    ChatGPTClient,
    GeminiJulesClient,
    GoogleWorkspaceSyncManager,
    AIQueryRequest,
    GitHubEvent,
    GoogleWorkspaceArtifact,
    ToolIntegrationManager,
)


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


def test_cli_continuity_bridge_commands(temp_workspace):
    """Test SAGE CLI subcommands ingest, reason, and verify."""
    # Create an ingestion payload file
    payload_file = temp_workspace / "payload.json"
    payload_data = {
        "session_id": "cli_session_123",
        "objective": "Test SAGE CLI objective",
        "task": "Test SAGE CLI task",
        "memories": [],
        "decisions": [],
    }
    with open(payload_file, "w") as f:
        json.dump(payload_data, f)

    # Use patch to mock SageRuntime to point to our temp_workspace
    with patch("sage.cli.SageRuntime", return_value=SageRuntime(str(temp_workspace))):
        # 1. Test Ingest Command
        with patch("sys.argv", ["sage-cli", "ingest", "--file", str(payload_file)]):
            with patch("builtins.print") as mock_print:
                cli_main()
                # Ensure something was printed and printed text contains session_id or success
                printed_args = [call_args[0] for call_args, _ in mock_print.call_args_list]
                full_print = "".join(printed_args)
                assert "cli_session_123" in full_print or "success" in full_print.lower()

        # 2. Test Reason Command
        with patch("sys.argv", ["sage-cli", "reason"]):
            with patch("builtins.print") as mock_print:
                cli_main()
                printed_args = [call_args[0] for call_args, _ in mock_print.call_args_list]
                full_print = "".join(printed_args)
                assert "objective_alignment" in full_print

        # 3. Test Verify Command
        with patch("sys.argv", ["sage-cli", "verify"]):
            with patch("builtins.print") as mock_print:
                try:
                    cli_main()
                except SystemExit as e:
                    assert e.code == 0
                printed_args = [call_args[0] for call_args, _ in mock_print.call_args_list]
                full_print = "".join(printed_args)
                assert "is_valid" in full_print


def test_ai_clients_and_tools_bridge_routing(temp_workspace):
    """Test that ChatGPT, Gemini, and Tool managers route directly through ingest_session_payload."""
    runtime = SageRuntime(str(temp_workspace))
    runtime.set_objective("Unified Bridge Integration")

    chatgpt = ChatGPTClient(runtime)
    gemini = GeminiJulesClient(runtime)
    tool_mgr = ToolIntegrationManager(runtime)

    # 1. ChatGPT
    chatgpt_req = AIQueryRequest(prompt="Explain the Continuity Bridge architecture")
    chatgpt_res = chatgpt.execute_query(chatgpt_req)
    assert chatgpt_res.session_id is not None
    # Verify interaction is ingested as memory
    memories = runtime.memory.list_all()
    chatgpt_mems = [m for m in memories if "chatgpt" in m.tags]
    assert len(chatgpt_mems) == 1
    assert chatgpt_mems[0].content["prompt"] == "Explain the Continuity Bridge architecture"

    # 2. Gemini
    gemini_req = AIQueryRequest(
        prompt="What are SAGE requirements?", session_id=chatgpt_res.session_id
    )
    gemini_res = gemini.execute_query(gemini_req)
    assert gemini_res.session_id == chatgpt_res.session_id
    # Verify interaction is ingested as memory
    memories = runtime.memory.list_all()
    gemini_mems = [m for m in memories if "gemini_jules" in m.tags]
    assert len(gemini_mems) == 1

    # 3. Tool manager GitHub index
    gh_event = GitHubEvent(
        event_type="commit",
        repository="test-repo",
        author="Jules",
        payload={"message": "Initial design"},
    )
    tool_mgr.index_github_event(gh_event)
    memories = runtime.memory.list_all()
    gh_mems = [m for m in memories if "github" in m.tags]
    assert len(gh_mems) == 1

    # 4. Tool manager Workspace index
    artifact = GoogleWorkspaceArtifact(
        doc_id="arch_spec_1",
        title="Architecture Specification Doc",
        doc_type="doc",
        last_modified_by="Jules",
        url="https://drive.google.com/doc1",
    )
    tool_mgr.index_workspace_artifact(artifact)
    memories = runtime.memory.list_all()
    ws_mems = [m for m in memories if "google_workspace" in m.tags]
    assert len(ws_mems) == 1


def test_google_workspace_sync_dry_run_diagnostics(temp_workspace):
    """Test Google Workspace Sync Manager dry-run diagnostics mode."""
    runtime = SageRuntime(str(temp_workspace))
    runtime.set_objective("Testing Workspace Sync")
    runtime.set_task("Verify Sync Mapper")

    sync_mgr = GoogleWorkspaceSyncManager(runtime)
    # Trigger sync (should fallback to dry-run since credentials and packages are not there/mocked)
    result = sync_mgr.sync_to_google_workspace()

    assert result["mode"] == "dry-run"
    assert result["status"] == "prepared"
    assert "required_scopes" in result
    assert "https://www.googleapis.com/auth/documents" in result["required_scopes"]
    assert "google_docs" in result["sync_mappings"]
    assert "google_sheets" in result["sync_mappings"]

    # Verify document attributes
    google_docs = result["sync_mappings"]["google_docs"]
    assert len(google_docs) > 0
    snapshot_mapping = next(
        d for d in google_docs if d["source_file"] == "docs/master/MASTER_SNAPSHOT.md"
    )
    assert snapshot_mapping["title"] == "SAGE Master Snapshot"

    # Verify sheet status values mapped correctly
    google_sheets = result["sync_mappings"]["google_sheets"]
    assert google_sheets["Engineering Tracker"]["current_objective"] == "Testing Workspace Sync"
    assert google_sheets["Engineering Tracker"]["active_task"] == "Verify Sync Mapper"
