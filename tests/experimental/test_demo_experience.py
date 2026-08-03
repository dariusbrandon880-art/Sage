"""SAGE Demonstration Experience test suite."""

import os
import json
import pytest

from sage.experimental.act.demo_experience import SAGEDemoExperienceManager


def test_demo_experience_success():
    """Verify that launching the SAGE Demo Experience successfully compiles all existing capabilities."""
    manager = SAGEDemoExperienceManager(output_path="evidence_capture/demo_experience_evidence.json")

    experience = manager.launch_experience(
        session_id="session_exp_99",
        user_id="usr_tester",
        approver="supervisor_charlie",
        signature="sig_exp_abc",
    )

    assert experience["session_id"] == "session_exp_99"
    assert experience["status"] == "EXPERIENCE_SUCCESS"
    assert "experience_checksum" in experience
    assert "SAGE DEMONSTRATION RUN COMPLETE" in experience["demonstration_summary"]

    payload = experience["workflow_payload"]
    assert payload["session_id"] == "session_exp_99"
    assert payload["human_checkpoint"]["approver"] == "supervisor_charlie"

    # Export evidence and verify file structure
    path = manager.export_experience_evidence()
    assert path == "evidence_capture/demo_experience_evidence.json"
    assert os.path.exists(path)

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["session_id"] == "session_exp_99"
    assert data["usability_improvements"]["summary_presentation_enabled"] is True


def test_demo_experience_unexecuted_export():
    """Verify error on attempting to export a demo experience that has not yet run."""
    manager = SAGEDemoExperienceManager()
    with pytest.raises(ValueError, match="No experience has been executed yet"):
        manager.export_experience_evidence()
