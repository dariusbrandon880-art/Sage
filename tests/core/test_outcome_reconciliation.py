import pytest

from sage.core.outcome_reconciliation import (
    OutcomeReconciliation,
    OutcomeReconciliationStatus,
    OutcomeReconciliationValidationError,
)


def make_reconciliation(**overrides):
    values = {
        "decision_id": "decision-001",
        "context_id": "ctx-001",
        "t0_claim_ref": "claim-sha-001",
        "t1_observation_ref": "observation-sha-001",
        "reality_gap_assessment_ref": "assessment-sha-001",
        "outcome_ref": "outcome-sha-001",
        "status": OutcomeReconciliationStatus.RECONCILED,
        "rationale": "The declared claim was reconciled against the supplied T1 records.",
    }
    values.update(overrides)
    return OutcomeReconciliation.reconcile(**values)


def test_replay_is_deterministic():
    first = make_reconciliation()
    second = make_reconciliation()
    assert first.reconciliation_digest == second.reconciliation_digest
    assert first.to_dict() == second.to_dict()


@pytest.mark.parametrize(
    "field",
    [
        "decision_id",
        "context_id",
        "t0_claim_ref",
        "t1_observation_ref",
        "reality_gap_assessment_ref",
        "outcome_ref",
        "rationale",
    ],
)
def test_missing_required_fields_fail_closed(field):
    with pytest.raises(OutcomeReconciliationValidationError):
        make_reconciliation(**{field: ""})


@pytest.mark.parametrize(
    "field",
    [
        "decision_id",
        "context_id",
        "t0_claim_ref",
        "t1_observation_ref",
        "reality_gap_assessment_ref",
        "outcome_ref",
        "rationale",
        "status",
    ],
)
def test_lineage_or_status_substitution_changes_digest(field):
    if field == "status":
        changed = OutcomeReconciliationStatus.UNRESOLVED
    elif field == "rationale":
        changed = "Different reconciliation rationale."
    else:
        changed = f"changed-{field}"

    first = make_reconciliation()
    second = make_reconciliation(**{field: changed})
    assert first.reconciliation_digest != second.reconciliation_digest


def test_all_semantic_statuses_are_supported():
    for status in OutcomeReconciliationStatus:
        assert make_reconciliation(status=status).status is status


def test_invalid_status_fails_closed():
    with pytest.raises(OutcomeReconciliationValidationError):
        make_reconciliation(status="SUCCESS")


def test_authority_is_permanently_false_and_immutable():
    reconciliation = make_reconciliation()
    assert reconciliation.authority_granted is False
    with pytest.raises((AttributeError, TypeError)):
        reconciliation.authority_granted = True
    assert reconciliation.to_dict()["authority_granted"] is False


def test_public_projection_is_complete_and_deterministic():
    reconciliation = make_reconciliation()
    projection = reconciliation.to_dict()
    assert projection["reconciliation_digest"] == reconciliation.reconciliation_digest
    assert set(projection) == {
        "decision_id",
        "context_id",
        "t0_claim_ref",
        "t1_observation_ref",
        "reality_gap_assessment_ref",
        "outcome_ref",
        "status",
        "rationale",
        "reconciliation_digest",
        "authority_granted",
    }
