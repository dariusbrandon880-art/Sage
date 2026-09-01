from sage.c2.decision_autopsy import CounterfactualRecord, DecisionAutopsy, DecisionAutopsyEngine, DecisionRecord, OutcomeRecord
from sage.experimental.sagi.regret import RegretAttributionEngine


def _autopsy(attribution: str, regret: float = 2.0) -> DecisionAutopsy:
    decision = DecisionRecord(
        decision_id="d1",
        mission_id="m1",
        decided_at_utc="2026-09-01T00:00:00Z",
        information_snapshot_hash="snapshot1",
        information_refs=("obs1",),
        assumptions=("a1",),
        chosen_action="A",
        alternatives=("B", "C"),
        chosen_expected_utility=5.0,
        alternative_expected_utilities=(("B", 7.0), ("C", 4.0)),
        decision_confidence=0.8,
    )
    outcome = OutcomeRecord(
        outcome_id="o1",
        decision_id="d1",
        observed_at_utc="2026-09-01T01:00:00Z",
        actual_utility=3.0,
    )
    return DecisionAutopsyEngine().autopsy(
        decision,
        outcome,
        (
            CounterfactualRecord("B", 7.0, "snapshot1", "2026-09-01T00:00:00Z"),
            CounterfactualRecord("C", 4.0, "snapshot1", "2026-09-01T00:00:00Z"),
        ),
        attribution=attribution,
        lesson="bounded lesson",
    )


def test_decision_error_becomes_avoidable_regret():
    record = RegretAttributionEngine().derive(_autopsy("DECISION_ERROR"))
    assert record.regret_class == "DECISION_REGRET"
    assert record.avoidable is True
    assert record.learning_signal == "REVIEW_DECISION_HEURISTIC"


def test_variance_regret_does_not_mark_policy_avoidable():
    record = RegretAttributionEngine().derive(_autopsy("VARIANCE"))
    assert record.regret_class == "VARIANCE_REGRET"
    assert record.avoidable is False
    assert "VARIANCE_MEMORY" in record.learning_signal


def test_information_shock_updates_information_requirements():
    record = RegretAttributionEngine().derive(_autopsy("INFORMATION_SHOCK"))
    assert record.regret_class == "INFORMATION_SHOCK_REGRET"
    assert record.learning_signal == "UPDATE_INFORMATION_REQUIREMENTS"


def test_zero_regret_produces_no_regret_class():
    record = RegretAttributionEngine().derive(_autopsy("UNKNOWN", regret=0.0))
    assert record.regret_class == "NO_REGRET"
    assert record.avoidable is False
    assert record.learning_signal == "NO_LEARNING_DELTA"


def test_all_nonzero_attributions_map_to_bounded_regret_classes():
    engine = RegretAttributionEngine()
    for attribution, expected in {
        "DECISION_ERROR": "DECISION_REGRET",
        "VARIANCE": "VARIANCE_REGRET",
        "INFORMATION_SHOCK": "INFORMATION_SHOCK_REGRET",
        "ENVIRONMENT_SHIFT": "ENVIRONMENT_SHIFT_REGRET",
        "COORDINATION_FAILURE": "COORDINATION_REGRET",
        "CONSTRAINT_FAILURE": "CONSTRAINT_REGRET",
        "INSUFFICIENT_EVIDENCE": "INSUFFICIENT_EVIDENCE_REGRET",
        "UNKNOWN": "UNKNOWN_REGRET",
    }.items():
        assert engine.derive(_autopsy(attribution)).regret_class == expected
