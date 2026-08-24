"""Unit tests for Fleet Command Intelligence Layer and progression mechanics."""

import pytest
from sage.experimental.airspace.fleet_command_intelligence import (
    FleetCommandIntelligence,
    FleetTier,
)


def test_fleet_command_intelligence_initial_state():
    """Verify initial fleet state and default tier."""
    fci = FleetCommandIntelligence()
    assert fci.current_tier == FleetTier.CADET_FLEET
    assert fci.total_xp == 0
    assert len(fci.xp_events) == 0
    assert len(fci.promotion_history) == 0
    assert len(fci.big_strike_history) == 0


def test_award_xp_with_verified_ref():
    """Verify awarding XP backed strictly by a non-empty verified reference."""
    fci = FleetCommandIntelligence()
    event = fci.award_xp(
        station_id="ENGINEERING_FLIGHT",
        amount=150,
        reason="Implemented Frontier Dependency Router with 100% tests",
        verified_event_ref="commit_sha_ed70dc8",
        timestamp_utc="2026-08-23T23:55:00Z",
    )

    assert event.amount == 150
    assert event.station_id == "ENGINEERING_FLIGHT"
    assert fci.total_xp == 150
    assert len(fci.xp_events) == 1


def test_award_xp_rejection_empty_ref():
    """Verify rejection of XP awards with empty verified event reference."""
    fci = FleetCommandIntelligence()
    with pytest.raises(ValueError, match="verified_event_ref cannot be empty"):
        fci.award_xp(
            station_id="MISSION_CONTROL",
            amount=50,
            reason="Unverified chat message",
            verified_event_ref="",
            timestamp_utc="2026-08-23T23:55:00Z",
        )


def test_evaluate_promotion_success():
    """Verify successful tier promotion when XP threshold and evidence refs are met."""
    fci = FleetCommandIntelligence()
    fci.award_xp(
        station_id="ENGINEERING_FLIGHT",
        amount=120,
        reason="Completed C2 Security Hardening Package",
        verified_event_ref="receipt_sec_001",
        timestamp_utc="2026-08-23T23:55:00Z",
    )

    receipt = fci.evaluate_promotion(
        target_tier=FleetTier.OPERATIONAL_FLEET,
        verified_event_refs=("receipt_sec_001", "commit_ed70dc8"),
        validator="Mission Control",
        timestamp_utc="2026-08-23T23:56:00Z",
    )

    assert receipt.previous_tier == FleetTier.CADET_FLEET
    assert receipt.new_tier == FleetTier.OPERATIONAL_FLEET
    assert fci.current_tier == FleetTier.OPERATIONAL_FLEET
    assert receipt.receipt_digest is not None


def test_evaluate_promotion_rejection_insufficient_xp():
    """Verify promotion rejection when total XP is below tier threshold."""
    fci = FleetCommandIntelligence()
    fci.award_xp(
        station_id="ENGINEERING_FLIGHT",
        amount=50,
        reason="Minor recon run",
        verified_event_ref="receipt_recon_001",
        timestamp_utc="2026-08-23T23:55:00Z",
    )

    with pytest.raises(ValueError, match="below required threshold"):
        fci.evaluate_promotion(
            target_tier=FleetTier.OPERATIONAL_FLEET,
            verified_event_refs=("receipt_recon_001",),
            validator="Mission Control",
            timestamp_utc="2026-08-23T23:56:00Z",
        )


def test_evaluate_promotion_level_skipping_rejection():
    """Verify rejection of direct level skipping from Level 1 to Level 3."""
    fci = FleetCommandIntelligence()
    fci.award_xp(
        station_id="ENGINEERING_FLIGHT",
        amount=500,
        reason="Massive verification wave",
        verified_event_ref="receipt_wave_001",
        timestamp_utc="2026-08-23T23:55:00Z",
    )

    with pytest.raises(ValueError, match="Level Skipping Rejected"):
        fci.evaluate_promotion(
            target_tier=FleetTier.FRONTIER_FLEET,
            verified_event_refs=("receipt_wave_001",),
            validator="Mission Control",
            timestamp_utc="2026-08-23T23:56:00Z",
        )


def test_record_big_strike_success():
    """Verify recording Big Strike campaign milestone backed by evidence manifest."""
    fci = FleetCommandIntelligence()
    receipt = fci.record_big_strike(
        strike_name="Big Strike: Frontier Intelligence Expansion",
        wave_id="wave_c2_five_front_001",
        contributing_flights_count=5,
        unlocked_capability="Automated Frontier Dependency Routing",
        evidence_manifest_ref="manifest_bs_001",
        timestamp_utc="2026-08-23T23:58:00Z",
    )

    assert receipt.strike_name == "Big Strike: Frontier Intelligence Expansion"
    assert receipt.contributing_flights_count == 5
    assert len(fci.big_strike_history) == 1


def test_record_big_strike_rejection_flights_count():
    """Verify rejection of Big Strike milestones with fewer than 5 flights."""
    fci = FleetCommandIntelligence()
    with pytest.raises(ValueError, match="Requires at least 5 contributing flights"):
        fci.record_big_strike(
            strike_name="Incomplete Strike",
            wave_id="wave_inc_001",
            contributing_flights_count=3,
            unlocked_capability="None",
            evidence_manifest_ref="manifest_inc",
            timestamp_utc="2026-08-23T23:58:00Z",
        )
