import pytest

from sage.core.verified_progression_projection import VerifiedProgressionProjection


def _build(**overrides):
    values = {
        "projection_id": "vp-001",
        "mission_id": "mission-001",
        "mission_state": "COMPLETED",
        "evidence_references": ["evidence:b", "evidence:a"],
        "verification_verdict": "VERIFIED",
        "capability_id": "CAP-001",
        "capability_supported": True,
        "current_qualification_state": "UNQUALIFIED",
        "locked_next_capabilities": ["CAP-003", "CAP-002"],
    }
    values.update(overrides)
    return VerifiedProgressionProjection.build(**values)


def test_projection_is_deterministic_and_normalizes_reference_order():
    first = _build(evidence_references=["evidence:b", "evidence:a"])
    second = _build(evidence_references=["evidence:a", "evidence:b"])

    assert first.projection_digest == second.projection_digest
    assert first.evidence_references == ("evidence:a", "evidence:b")
    assert first.locked_next_capabilities == ("CAP-002", "CAP-003")


def test_verified_support_requires_reviewer_and_never_grants_authority():
    projection = _build()

    assert projection.capability_supported is True
    assert projection.reviewer_authorization_required is True
    assert projection.current_qualification_state == "UNQUALIFIED"
    assert projection.read_only is True
    assert projection.authority_granted is False


def test_unverified_verdict_cannot_become_positive_capability_support():
    for verdict in ("HOLD", "FALSIFIED", "PENDING", "INDETERMINATE"):
        projection = _build(verification_verdict=verdict)
        assert projection.capability_supported is False
        assert projection.reviewer_authorization_required is False


def test_input_collections_are_not_retained_as_mutable_state():
    evidence = ["evidence:a"]
    locked = ["CAP-002"]
    projection = _build(evidence_references=evidence, locked_next_capabilities=locked)

    evidence.append("evidence:mutated")
    locked.append("CAP-003")

    assert projection.evidence_references == ("evidence:a",)
    assert projection.locked_next_capabilities == ("CAP-002",)


def test_invalid_verdict_fails_closed():
    with pytest.raises(ValueError, match="invalid verification_verdict"):
        _build(verification_verdict="SUCCESS")


def test_invalid_qualification_state_fails_closed():
    with pytest.raises(ValueError, match="invalid current_qualification_state"):
        _build(current_qualification_state="PROMOTED")


def test_duplicate_references_fail_closed():
    with pytest.raises(ValueError, match="must be unique"):
        _build(evidence_references=["evidence:a", "evidence:a"])


def test_missing_required_identifiers_fail_closed():
    with pytest.raises(ValueError, match="mission_id"):
        _build(mission_id="")
    with pytest.raises(ValueError, match="capability_id"):
        _build(capability_id="   ")


def test_projection_is_immutable_and_authority_firewall_is_hard():
    projection = _build()

    with pytest.raises(Exception):
        projection.capability_supported = False

    with pytest.raises(ValueError, match="authority_granted"):
        VerifiedProgressionProjection(
            projection_id="vp-002",
            mission_id="mission-002",
            mission_state="COMPLETE",
            verification_verdict="VERIFIED",
            evidence_references=("evidence:a",),
            capability_id="CAP-002",
            capability_supported=True,
            current_qualification_state="UNQUALIFIED",
            reviewer_authorization_required=True,
            locked_next_capabilities=(),
            projection_digest="digest",
            authority_granted=True,
        )


def test_projection_digest_changes_when_consequential_input_changes():
    baseline = _build()
    changed = _build(mission_state="FAILED")
    changed_evidence = _build(evidence_references=["evidence:c"])
    changed_capability = _build(capability_id="CAP-999")

    assert baseline.projection_digest != changed.projection_digest
    assert baseline.projection_digest != changed_evidence.projection_digest
    assert baseline.projection_digest != changed_capability.projection_digest


def test_public_projection_is_complete_and_read_only():
    projection = _build()
    data = projection.to_dict()

    assert data["projection_version"] == "verified-progression-v0.1"
    assert data["projection_digest"] == projection.projection_digest
    assert data["reviewer_authorization_required"] is True
    assert data["authority_granted"] is False
    assert data["read_only"] is True
    assert "xp" not in data
    assert "promote" not in data
    assert "apply" not in data
