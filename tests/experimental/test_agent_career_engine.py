import pytest

from sage.experimental.airspace.fleet_qualification_ledger import (
    CareerRank,
    FleetQualificationLedger,
)


def test_verified_points_convert_conservatively_to_career_xp():
    ledger = FleetQualificationLedger()
    event = ledger.record_verified_points(
        "JULES",
        850,
        verified_event_ref="receipt:sortie-001",
        evidence_refs=["evidence:sortie-001"],
    )

    assert event.points == 850
    assert ledger.convert_points_to_xp("JULES") == 85
    assert ledger.get_or_create_state("JULES").total_xp == 85


def test_duplicate_verified_event_cannot_farm_points():
    ledger = FleetQualificationLedger()
    kwargs = dict(
        agent_id="JULES",
        base_points=100,
        verified_event_ref="receipt:sortie-001",
        evidence_refs=["evidence:sortie-001"],
    )
    ledger.record_verified_points(**kwargs)

    with pytest.raises(ValueError, match="Duplicate verified_event_ref"):
        ledger.record_verified_points(**kwargs)


def test_promotion_requires_qualification_and_evidence_not_xp_alone():
    ledger = FleetQualificationLedger()
    ledger.record_verified_points(
        "JULES",
        1000,
        verified_event_ref="receipt:sortie-002",
        evidence_refs=["evidence:sortie-002"],
    )
    ledger.convert_points_to_xp("JULES")

    state = ledger.evaluate_promotion("JULES", cql_level=1, sql_level=0)
    assert state.rank_title == CareerRank.CADET.value
    assert state.promotion_eligible is False

    state = ledger.evaluate_promotion(
        "JULES",
        cql_level=2,
        sql_level=0,
        evidence_refs=["evidence:qualification-cql2"],
    )
    assert state.rank_title == CareerRank.FLIGHT_CAPTAIN.value


def test_higher_rank_requires_breadth_not_only_more_xp():
    ledger = FleetQualificationLedger()
    ledger.record_verified_points(
        "GEMINI",
        5000,
        verified_event_ref="receipt:sortie-003",
        evidence_refs=["evidence:sortie-003"],
    )
    ledger.convert_points_to_xp("GEMINI")

    state = ledger.evaluate_promotion(
        "GEMINI",
        cql_level=3,
        sql_level=1,
        evidence_refs=["evidence:cql3"],
    )
    assert state.rank_title == CareerRank.SQUADRON_LEADER.value

    state = ledger.evaluate_promotion(
        "GEMINI",
        cql_level=4,
        sql_level=2,
        evidence_refs=["evidence:cql4", "evidence:sql2"],
    )
    assert state.rank_title == CareerRank.FLEET_COMMANDER.value


def test_snapshot_recovery_preserves_career_history():
    ledger = FleetQualificationLedger()
    ledger.record_verified_points(
        "CHATGPT",
        1000,
        verified_event_ref="receipt:sortie-004",
        evidence_refs=["evidence:sortie-004"],
        badge="independent-verification",
    )
    ledger.convert_points_to_xp("CHATGPT")
    ledger.evaluate_promotion(
        "CHATGPT",
        cql_level=2,
        sql_level=0,
        evidence_refs=["evidence:cql2"],
    )

    restored = FleetQualificationLedger()
    assert restored.recover_from_snapshot(ledger.export_snapshot()) == 1
    state = restored.get_or_create_state("CHATGPT")
    assert state.total_xp == 100
    assert state.rank_title == CareerRank.FLIGHT_CAPTAIN.value
    assert state.verification_badges == ["independent-verification"]
    assert len(restored.get_promotion_history()) == 1
