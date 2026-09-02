import pytest

from sage.experimental.airspace.points_economy import PointAward, PointEventType, PointsLedger


def award(ref: str, points: int = 100) -> PointAward:
    return PointAward(
        event_id=f"evt-{ref}",
        agent_id="GPT",
        event_type=PointEventType.VERIFICATION,
        base_points=points,
        difficulty=5,
        verification_quality=5,
        impact=5,
        reuse=5,
        verified_event_ref=ref,
        evidence_refs=(f"evidence:{ref}",),
    )


def test_verified_points_are_deterministic():
    assert award("verified-001", 100).verified_points == 100


def test_points_convert_to_xp_at_ten_to_one():
    ledger = PointsLedger([award("verified-001", 100)])
    assert ledger.verified_points_for_agent("GPT") == 100
    assert ledger.career_xp_for_agent("GPT") == 10
    assert ledger.unconverted_points_for_agent("GPT") == 0


def test_remainder_is_retained_until_ten_points():
    ledger = PointsLedger([award("verified-001", 15)])
    assert ledger.verified_points_for_agent("GPT") == 15
    assert ledger.career_xp_for_agent("GPT") == 1
    assert ledger.unconverted_points_for_agent("GPT") == 5


def test_verified_event_replay_is_idempotent():
    first = award("verified-001", 100)
    ledger = PointsLedger([first])
    ledger.record(first)
    assert len(ledger.awards()) == 1


def test_verified_event_cannot_be_reused_for_a_different_award():
    ledger = PointsLedger([award("verified-001", 100)])
    with pytest.raises(ValueError, match="already belongs"):
        ledger.record(award("verified-001", 200))


def test_point_award_requires_evidence():
    with pytest.raises(ValueError, match="evidence_refs"):
        PointAward(
            event_id="evt-1",
            agent_id="GPT",
            event_type=PointEventType.BUILD,
            base_points=10,
            difficulty=1,
            verification_quality=1,
            impact=1,
            reuse=1,
            verified_event_ref="commit:test",
            evidence_refs=(),
        )


def test_point_award_requires_verified_event_ref():
    with pytest.raises(ValueError, match="verified_event_ref"):
        PointAward(
            event_id="evt-1",
            agent_id="GPT",
            event_type=PointEventType.BUILD,
            base_points=10,
            difficulty=1,
            verification_quality=1,
            impact=1,
            reuse=1,
            verified_event_ref=" ",
            evidence_refs=("evidence:test",),
        )


def test_quality_dimensions_are_bounded():
    with pytest.raises(ValueError, match="difficulty"):
        award("verified-001").__class__(
            event_id="evt-1",
            agent_id="GPT",
            event_type=PointEventType.BUILD,
            base_points=10,
            difficulty=6,
            verification_quality=1,
            impact=1,
            reuse=1,
            verified_event_ref="commit:test",
            evidence_refs=("evidence:test",),
        )
