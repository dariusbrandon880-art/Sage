"""SAGE-ACT-PROD Demonstrator Foundation test suite."""

import os
import json
import pytest

from sage.experimental.act.act_prod_demonstrator import (
    SAGEProdDemonstrator,
    render_html_visualizer,
)


def test_demonstrator_state_compilation():
    """Verify that the demonstrator successfully compiles simulated capabilities and state lineages."""
    demonstrator = SAGEProdDemonstrator(output_path="evidence_capture/act_prod_demonstrator_run.json")

    state = demonstrator.compile_demonstration_state(
        session_id="session_demo_101",
        user_id="usr_admin",
        approver="supervisor_charlie",
        signature="sig_demo_123",
    )

    assert state["session_id"] == "session_demo_101"
    assert state["user_id"] == "usr_admin"
    assert "demonstrator_checksum" in state
    assert len(state["inputs_mapped"]) == 4

    # Divergence Display Assertion
    assert state["divergence_visibility"]["divergence_detected"] is True
    assert state["divergence_visibility"]["conflict_type"] == "state_split_brain"

    # Checkpoint and Receipt display
    assert len(state["recovery_checkpoint_visibility"]["checkpoints"]) == 1
    assert state["receipt_verification_display"]["signature_valid"] is True

    # Human approval simulation
    assert state["human_review_checkpoint_simulation"]["status"] == "AUTHORIZED"
    assert state["human_review_checkpoint_simulation"]["approver"] == "supervisor_charlie"


def test_demonstrator_evidence_export():
    """Verify that the compiled state is successfully exported to a durable JSON artifact."""
    output_path = "evidence_capture/act_prod_demonstrator_run.json"
    if os.path.exists(output_path):
        os.remove(output_path)

    demonstrator = SAGEProdDemonstrator(output_path=output_path)
    demonstrator.compile_demonstration_state(
        session_id="session_demo_202",
        user_id="usr_admin",
        approver="supervisor_bob",
        signature="sig_abc",
    )

    path = demonstrator.export_evidence_artifact("session_demo_202")
    assert path == output_path
    assert os.path.exists(output_path)

    # Read the artifact to check its validity
    with open(output_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["session_id"] == "session_demo_202"
    assert data["user_id"] == "usr_admin"
    assert data["demonstrator_metadata"]["mode"] == "read_only_experimental_sandbox"


def test_demonstrator_html_visualizer():
    """Verify that the state payload is correctly rendered into the HTML visualizer."""
    demonstrator = SAGEProdDemonstrator()
    state = demonstrator.compile_demonstration_state(
        session_id="session_demo_303",
        user_id="usr_admin",
        approver="supervisor_alice",
        signature="sig_xyz",
    )

    html = render_html_visualizer(state)
    assert "session_demo_303" in html
    assert "SAGE-ACT-PROD Demonstrator" in html
    assert "supervisor_alice" in html
    assert state["demonstrator_checksum"] in html


def test_demonstrator_invalid_session_export():
    """Verify that exporting a non-existent session results in an error."""
    demonstrator = SAGEProdDemonstrator()
    with pytest.raises(ValueError, match="Session 'session_non_existent' not found"):
        demonstrator.export_evidence_artifact("session_non_existent")
