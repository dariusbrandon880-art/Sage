from sage.c2.decision_autopsy import (
    CounterfactualRecord,
    DecisionAutopsyEngine,
    DecisionRecord,
    OutcomeRecord,
    classify_outcome_without_decision_hindsight,
)


HASH = "snapshot-001"


def decision() -> DecisionRecord:
    return DecisionRecord(
        decision_id="decision-001",
        mission_id="mission-001",
        decided_at_utc="2026-09-01T10:00:00Z",
        information_snapshot_hash=HASH,
        information_refs=("obs-001", "obs-002"),
        assumptions=("availability-stable",),
        chosen_action="A",
        alternatives=("B", "C"),
        chosen_expected_utility=0.70,
        alternative_expected_utilities=(("B", 0.60), ("C", 0.40)),
        decision_confidence=0.80,
    )


def counterfactuals():
    return (
        CounterfactualRecord("B", 0.60, HASH, "2026-09-01T10:00:00Z"),
        CounterfactualRecord("C", 0.40, HASH, "2026-09-01T10:00:00Z"),
    )


def test_good_decision_bad_outcome_is_variance():
    autopsy = DecisionAutopsyEngine().autopsy(
        decision(),
        OutcomeRecord("outcome-001", "decision-001", "2026-09-01T12:00:00Z", 0.20),
        counterfactuals(),
        lesson="Preserve the decision policy; investigate environmental variance.",
    )
    assert autopsy.decision_quality == "GOOD_DECISION"
    assert autopsy.outcome_quality == "BAD"
    assert autopsy.attribution == "VARIANCE"
    assert autopsy.regret == 0.0


def test_bad_decision_good_outcome_preserves_decision_error():
    d = decision()
    d = DecisionRecord(
        decision_id=d.decision_id,
        mission_id=d.mission_id,
        decided_at_utc=d.decided_at_utc,
        information_snapshot_hash=d.information_snapshot_hash,
        information_refs=d.information_refs,
        assumptions=d.assumptions,
        chosen_action=d.chosen_action,
        alternatives=d.alternatives,
        chosen_expected_utility=0.30,
        alternative_expected_utilities=d.alternative_expected_utilities,
        decision_confidence=d.decision_confidence,
    )
    autopsy = DecisionAutopsyEngine().autopsy(
        d,
        OutcomeRecord("outcome-002", d.decision_id, "2026-09-01T12:00:00Z", 0.80),
        counterfactuals(),
        lesson="Choose the higher expected-utility path when evidence is equivalent.",
    )
    assert autopsy.decision_quality == "BAD_DECISION"
    assert autopsy.outcome_quality == "GOOD"
    assert autopsy.attribution == "DECISION_ERROR"
    assert autopsy.regret == 0.30


def test_counterfactual_cannot_use_hindsight_information():
    cf = CounterfactualRecord("B", 0.60, "post-outcome-snapshot", "2026-09-01T10:00:00Z")
    try:
        DecisionAutopsyEngine().autopsy(
            decision(),
            OutcomeRecord("outcome-003", "decision-001", "2026-09-01T12:00:00Z", 0.20),
            (cf, CounterfactualRecord("C", 0.40, HASH, "2026-09-01T10:00:00Z")),
            lesson="Should never be accepted.",
        )
    except ValueError as exc:
        assert "decision-time" in str(exc)
    else:
        raise AssertionError("expected hindsight information to fail closed")


def test_missing_alternative_fails_closed():
    try:
        DecisionAutopsyEngine().autopsy(
            decision(),
            OutcomeRecord("outcome-004", "decision-001", "2026-09-01T12:00:00Z", 0.70),
            (counterfactuals()[0],),
            lesson="Incomplete counterfactual coverage.",
        )
    except ValueError as exc:
        assert "cover every" in str(exc)
    else:
        raise AssertionError("expected incomplete counterfactual coverage to fail closed")


def test_outcome_cannot_precede_decision():
    try:
        DecisionAutopsyEngine().autopsy(
            decision(),
            OutcomeRecord("outcome-005", "decision-001", "2026-09-01T09:59:59Z", 0.80),
            counterfactuals(),
            lesson="Chronology violation.",
        )
    except ValueError as exc:
        assert "precede decision" in str(exc)
    else:
        raise AssertionError("expected chronology violation to fail closed")


def test_pure_outcome_classifier_uses_locked_expectation():
    d = decision()
    assert classify_outcome_without_decision_hindsight(
        d, OutcomeRecord("outcome-006", d.decision_id, "2026-09-01T11:00:00Z", 0.90)
    ) == "GOOD"
    assert classify_outcome_without_decision_hindsight(
        d, OutcomeRecord("outcome-007", d.decision_id, "2026-09-01T11:00:00Z", 0.50)
    ) == "BAD"


def test_decision_record_state_is_immutable():
    d = decision()
    try:
        d.chosen_action = "B"
    except AttributeError:
        pass
    else:
        raise AssertionError("expected frozen decision state")
