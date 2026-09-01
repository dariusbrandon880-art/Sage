import pytest

from sage.experimental.sports_quant import PropEdgeResult
from sage.experimental.sports_quant.decision_bridge import (
    autopsy_sports_decision,
    build_sports_decision,
    derive_sports_learning_signal,
)


BEFORE = "2026-09-01T00:00:00Z"
AFTER = "2026-09-01T02:00:00Z"


def edge(selection: str, projected: float, confidence: float = 0.9) -> PropEdgeResult:
    return PropEdgeResult(
        player_name="Player One",
        prop_category="points",
        selection=selection,
        fanduel_decimal_price=2.0,
        fanduel_implied_prob=0.5,
        projected_prob=projected,
        edge_score=projected - 0.5,
        expected_value=(projected * 2.0) - 1.0,
        confidence_score=confidence,
        is_positive_ev=projected > 0.5,
        kelly_stake_recommendation=0.0,
        rationale="paper research",
    )


def test_bridge_creates_immutable_paper_decision():
    decision = build_sports_decision(
        edge("over", 0.65),
        [edge("under", 0.35)],
        decision_id="sports-d1",
        mission_id="sports-m1",
        decided_at_utc=BEFORE,
    )
    assert decision.chosen_selection == "over"
    assert decision.alternatives == (("under", 0.35),)
    assert decision.wagering_executed is False
    assert len(decision.information_snapshot_hash) == 64


def test_bridge_rejects_duplicate_chosen_alternative():
    with pytest.raises(ValueError, match="ALTERNATIVE_DUPLICATE"):
        build_sports_decision(
            edge("over", 0.65),
            [edge("over", 0.60)],
            decision_id="sports-d2",
            mission_id="sports-m2",
            decided_at_utc=BEFORE,
        )


def test_bridge_autopsies_paper_outcome_and_derives_regret():
    chosen = edge("over", 0.65)
    decision = build_sports_decision(
        chosen,
        [edge("under", 0.35)],
        decision_id="sports-d3",
        mission_id="sports-m3",
        decided_at_utc=BEFORE,
    )
    autopsy = autopsy_sports_decision(
        decision,
        chosen,
        outcome_id="sports-o3",
        observed_at_utc=AFTER,
        actual_utility=0.0,
    )
    signal = derive_sports_learning_signal(autopsy)
    assert autopsy.decision_id == decision.decision_id
    assert autopsy.outcome_id == "sports-o3"
    assert signal.decision_id == decision.decision_id
    assert signal.regret_class == "NO_REGRET"
    assert signal.avoidable is False


def test_bridge_preserves_no_wagering_boundary():
    chosen = edge("over", 0.65)
    decision = build_sports_decision(
        chosen,
        [edge("under", 0.35)],
        decision_id="sports-d4",
        mission_id="sports-m4",
        decided_at_utc=BEFORE,
    )
    assert decision.wagering_executed is False
    with pytest.raises(ValueError, match="SHADOW_BOUNDARY_VIOLATION"):
        from sage.experimental.sports_quant.decision_bridge import SportsDecision

        SportsDecision(
            decision_id="sports-d5",
            mission_id="sports-m5",
            event_id="event",
            decided_at_utc=BEFORE,
            information_snapshot_hash="hash",
            chosen_selection="over",
            chosen_projected_probability=0.65,
            alternatives=(("under", 0.35),),
            wagering_executed=True,
        )
