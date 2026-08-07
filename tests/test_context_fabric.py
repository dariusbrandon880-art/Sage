"""Tests for SAGE Context Fabric Integration.

Covers the full cycle: ingestion -> classification -> validated state objects ->
archive promotion -> context rehydration -> REST API verification.
"""

import tempfile
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from sage.acr.session.context_tracker import SAGEContextFabric
from sage.api import app
from sage.models import (
    ArchiveEntry,
    ConfidenceLevel,
    DecisionType,
    ExternalSessionPayload,
    KnowledgeState,
)
from sage.runtime import SAGERuntime


@pytest.fixture
def clean_workspace():
    """Provides a temporary, clean workspace directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_context_fabric_ingestion_classification_and_rehydration(clean_workspace):
    """Test the complete flow of ingestion, classification, archive promotion, and rehydration."""
    # 1. Initialize Runtime with clean workspace
    runtime = SAGERuntime(str(clean_workspace))
    runtime.start()

    # Define a session payload representing the external context
    session_id = f"sess_fabric_{uuid.uuid4().hex[:6]}"
    payload = ExternalSessionPayload(
        session_id=session_id,
        objective="Verify Context Fabric flow",
        task="Ingest and promote fabric state",
        memories=[
            {
                "id": "mem_fabric_001",
                "object_type": "fact",
                "content": {"subject": "SAGE Context Fabric", "status": "integrated"},
                "tags": ["fabric", "civ-test"],
                "confidence": "validated",
            }
        ],
        decisions=[
            {
                "id": "dec_fabric_001",
                "decision_type": "technical",
                "description": "Store state objects unified in SAGEContextFabric",
                "rationale": "Allows clean rehydration from archive boundary",
                "evidence": ["mem_fabric_001"],
            }
        ],
    )

    # 2. ACR Ingestion & Session State flow
    ingest_result = runtime.ingest_session_payload(payload)
    assert ingest_result["status"] == "success"
    assert ingest_result["session_id"] == session_id

    # 3. Retrieve Context Fabric (Verification of Step 1: Object Contracts)
    fabric = runtime.context_tracker.get_context_fabric(session_id)
    assert isinstance(fabric, SAGEContextFabric)
    assert fabric.session_id == session_id
    assert fabric.active_context is not None
    assert "Verify Context Fabric flow" in fabric.active_objectives
    assert "dec_fabric_001" in fabric.important_decisions

    # 4. Promote Context Fabric to Master Archive
    archive_id = f"arch_fabric_{uuid.uuid4().hex[:6]}"
    arch_entry = ArchiveEntry(
        id=archive_id,
        title="Archived Context Fabric Backup",
        tags=["fabric-backup"],
        knowledge_state=KnowledgeState.ARCHIVED,
        content={
            "current_objective": runtime.current_state.current_objective,
            "active_task": runtime.current_state.active_task,
            "session_state": runtime.session_manager.retrieve_session(session_id).model_dump(),
            "active_context": runtime.context_tracker.get_current_context().model_dump(),
        },
    )
    runtime.archive.promote_to_archive(arch_entry)

    # Retrieve from archive boundary to ensure it's persisted correctly
    retrieved_entry = runtime.archive.retrieve_entry(archive_id)
    assert retrieved_entry is not None
    assert retrieved_entry.title == "Archived Context Fabric Backup"
    assert retrieved_entry.content["current_objective"] == "Verify Context Fabric flow"

    # Stop current runtime
    runtime.stop()

    # 5. Initialize fresh/empty runtime to simulate rehydration
    fresh_workspace = clean_workspace / "fresh_node"
    fresh_workspace.mkdir()

    # Copy the archive directory to the fresh node workspace to simulate shared knowledge/state
    fresh_archive_dir = fresh_workspace / "archive"
    fresh_archive_dir.mkdir(parents=True, exist_ok=True)
    for p in (clean_workspace / "archive").glob("*.json"):
        with open(p, "r") as src, open(fresh_archive_dir / p.name, "w") as dest:
            dest.write(src.read())

    runtime_beta = SAGERuntime(str(fresh_workspace))
    runtime_beta.start()

    # Beta runtime is empty initially
    assert runtime_beta.current_state.current_objective is None
    assert runtime_beta.current_state.active_task is None

    # Trigger rehydration using the master archive retrieval boundary
    rehydrate_success = runtime_beta.rehydrate_fabric_from_archive(archive_id)
    assert rehydrate_success is True

    # Verify Beta has fully rehydrated and recovered state
    assert runtime_beta.current_state.current_objective == "Verify Context Fabric flow"
    assert runtime_beta.current_state.active_task == "Ingest and promote fabric state"

    rehydrated_sess = runtime_beta.session_manager.retrieve_session(session_id)
    assert rehydrated_sess is not None
    assert "Verify Context Fabric flow" in rehydrated_sess.active_objectives
    assert "dec_fabric_001" in rehydrated_sess.important_decisions

    # Stop Beta runtime
    runtime_beta.stop()


def test_api_system_frame_endpoints(clean_workspace):
    """Test the /system-frame and /system-frame/rehydrate API endpoints."""
    # Use TestClient and configure global api runtime
    from sage.api import runtime as api_runtime, validation as api_validation
    orig_workspace = getattr(api_runtime, "workspace_path", "sage_data")
    api_runtime.__init__(workspace_path=str(clean_workspace))
    api_runtime.start()
    api_validation.__init__(api_runtime.memory, api_runtime.archive)

    try:
        with TestClient(app) as client:
            # 1. Get initial empty system-frame
            response = client.get("/system-frame")
            assert response.status_code == 200
            data = response.json()
            assert "active_context" in data

            # Set active objectives/tasks to build active context
            client.post("/objective", json={"objective": "API objective"})
            client.post("/task", json={"task": "API task"})

            response = client.get("/system-frame")
            assert response.status_code == 200
            data = response.json()
            assert "API objective" in data["active_objectives"]

            # Promote context fabric mock to archive to test API rehydration
            archive_id = "arch_api_fabric_001"
            arch_entry = ArchiveEntry(
                id=archive_id,
                title="Archived API Context Fabric Backup",
                tags=["fabric-api"],
                knowledge_state=KnowledgeState.ARCHIVED,
                content={
                    "current_objective": "Rehydrated Objective via API",
                    "active_task": "Rehydrated Task via API",
                    "session_state": {
                        "session_id": "api_rehydrated_sess",
                        "active_objectives": ["Rehydrated Objective via API"],
                        "completed_actions": [],
                        "pending_actions": [],
                        "important_decisions": [],
                        "related_archive_references": [],
                        "metadata": {},
                    },
                    "active_context": {
                        "current_project_state": "rehydrated",
                        "active_milestone": "milestone_api",
                        "unresolved_items": [],
                        "recent_changes": ["Rehydrated from endpoint"],
                        "important_context_transitions": [],
                        "metadata": {},
                    },
                },
            )
            api_runtime.archive.promote_to_archive(arch_entry)

            # 2. POST to /system-frame/rehydrate
            response = client.post("/system-frame/rehydrate", json={"archive_id": archive_id})
            assert response.status_code == 200
            assert "Successfully rehydrated" in response.json()["message"]

            # Verify active runtime state updated
            assert api_runtime.current_state.current_objective == "Rehydrated Objective via API"
            assert api_runtime.current_state.active_task == "Rehydrated Task via API"

            # Verify system-frame endpoint reflects updated context fabric
            response = client.get("/system-frame", params={"session_id": "api_rehydrated_sess"})
            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == "api_rehydrated_sess"
            assert "Rehydrated Objective via API" in data["active_objectives"]
            assert data["active_context"]["current_project_state"] == "rehydrated"
            assert data["active_context"]["active_milestone"] == "milestone_api"
    finally:
        # Restore the original global workspace path
        api_runtime.__init__(workspace_path=orig_workspace)
