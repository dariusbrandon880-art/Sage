"""Unit tests for SAGE Governed Mission Intake Layer."""

import pytest
import time
from sage.mission_intake import SAGEMissionIntakeLayer, MissionProposal


def test_valid_proposal_acceptance():
    """Verify that a valid proposal is enqueued in the MISSION_PROPOSED state."""
    intake = SAGEMissionIntakeLayer()
    proposal = {
        "name": "Audit System Linage",
        "description": "Trace cryptographic audit trails across session records",
        "objective": "Verify the integrity of SHA-256 fingerprint chains in PML",
        "operator_id": "operator_jules_01",
        "prerequisites": {"value_appraisal_approved": True}
    }

    res = intake.submit_proposal(proposal)
    assert res["accepted"] is True
    assert res["status"] == "ACCEPTED"
    assert res["current_state"] == "MISSION_PROPOSED"
    assert res["queue_position"] == 0

    # Verify queue entry
    queue = intake.get_queue()
    assert len(queue) == 1
    enqueued = queue[0]
    assert enqueued.name == "Audit System Linage"
    assert enqueued.current_state == "MISSION_PROPOSED"


def test_malformed_proposal_rejection():
    """Verify that malformed proposals are rejected and audited."""
    intake = SAGEMissionIntakeLayer()
    proposal = {
        "name": "Audit System Linage",
        # Missing description, objective, operator_id
    }

    res = intake.submit_proposal(proposal)
    assert res["accepted"] is False
    assert res["status"] == "REJECTED"
    assert "Missing required fields" in res["reason"]

    # Verify rejection record
    rejections = intake.get_rejections()
    assert len(rejections) == 1
    assert rejections[0].proposal_data == proposal
    assert "Missing required fields" in rejections[0].rejection_reason


def test_missing_required_metadata():
    """Verify that proposals with empty or blank fields are rejected."""
    intake = SAGEMissionIntakeLayer()
    proposal = {
        "name": "   ",  # Blank name
        "description": "Valid description",
        "objective": "Valid objective",
        "operator_id": "operator_jules_01"
    }

    res = intake.submit_proposal(proposal)
    assert res["accepted"] is False
    assert "cannot be empty or blank" in res["reason"]


def test_deterministic_mission_ids():
    """Verify that identical proposal parameters yield identical, deterministic IDs."""
    intake = SAGEMissionIntakeLayer()
    timestamp = 1786020547.0

    id1 = intake.generate_deterministic_id("Test Mission", "operator_01", timestamp)
    id2 = intake.generate_deterministic_id("Test Mission", "operator_01", timestamp)
    assert id1 == id2
    assert id1.startswith("msn-intake-")


def test_deterministic_queue_ordering():
    """Verify that FIFO queue ordering is strictly maintained."""
    intake = SAGEMissionIntakeLayer()

    p1 = {"name": "M1", "description": "D", "objective": "O", "operator_id": "Op"}
    p2 = {"name": "M2", "description": "D", "objective": "O", "operator_id": "Op"}

    res1 = intake.submit_proposal(p1)
    res2 = intake.submit_proposal(p2)

    assert res1["queue_position"] == 0
    assert res2["queue_position"] == 1

    queue = intake.get_queue()
    assert queue[0].name == "M1"
    assert queue[1].name == "M2"


def test_provenance_preservation():
    """Verify that accepted states preserve operator provenance and original inputs."""
    intake = SAGEMissionIntakeLayer()
    proposal = {
        "name": "Audit System Linage",
        "description": "Trace cryptographic audit trails across session records",
        "objective": "Verify the integrity of SHA-256 fingerprint chains in PML",
        "operator_id": "operator_jules_01",
        "prerequisites": {"value_appraisal_approved": True}
    }

    res = intake.submit_proposal(proposal)
    enqueued = intake.get_queue()[0]

    provenance = enqueued.metadata["provenance"]
    assert provenance["operator_id"] == "operator_jules_01"
    assert provenance["original_proposal"] == proposal


def test_intake_cannot_authorize_execution():
    """Verify that the intake layer cannot authorize execution independently."""
    intake = SAGEMissionIntakeLayer()
    proposal = {
        "name": "Audit System",
        "description": "Trace audit trails",
        "objective": "Verify integrity",
        "operator_id": "operator_jules_01"
    }

    res = intake.submit_proposal(proposal)
    mission_id = res["mission_id"]

    # Attempting to directly hand off to EXECUTION_AUTHORIZED fails due to strict sequence check and prerequisites
    res_auth = intake.handoff_to_controller(mission_id, "EXECUTION_AUTHORIZED")
    assert res_auth["success"] is False
    assert "Cannot skip sequential stages" in res_auth["decision_reason"]


def test_integration_with_progression_controller():
    """Verify integration and controller handoff for a valid direct sequential step."""
    intake = SAGEMissionIntakeLayer()
    proposal = {
        "name": "Audit System",
        "description": "Trace audit trails",
        "objective": "Verify integrity",
        "operator_id": "operator_jules_01",
        "prerequisites": {"value_appraisal_approved": True}
    }

    res = intake.submit_proposal(proposal)
    mission_id = res["mission_id"]

    # Sequential handoff from MISSION_PROPOSED -> VALUE_EVALUATED
    res_transition = intake.handoff_to_controller(mission_id, "VALUE_EVALUATED")
    assert res_transition["success"] is True
    assert res_transition["transitioned"] is True
    assert res_transition["explainable_trace"]["next_allowed_state"] == "VALUE_EVALUATED"

    # Enqueued state is updated
    assert intake.get_queue()[0].current_state == "VALUE_EVALUATED"
