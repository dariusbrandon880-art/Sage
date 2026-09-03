"""Test suite for SAGE Reward & Evidence Protocol v1 (SAGE-RP-1.0) and Autonomous Adjudicator."""

import pytest
from pathlib import Path

from sage.c2.reward_adjudication_bridge import request_c2_reward_adjudication
from sage.experimental.airspace.boss_progression import BossClass, BossProgressionAuthority
from sage.experimental.airspace.manager import AirspaceManager
from sage.experimental.airspace.models import StationID
from sage.experimental.airspace.points_xp_economy import BASE_POINTS, PointEventType, PointsXPEconomy
from sage.experimental.airspace.reward_protocol import (
    SCORING_PROTOCOL_VERSION,
    ContributionUnit,
    RewardAdjudicator,
    RewardRequest,
    SAGEEvidencePacket,
    resolve_station_id,
)


VALID_COMMIT_SHA = "75c583db46bb90cc2af925f807e1809bd7023f12"


def test_scoring_constitution_base_points_and_version():
    """Verify locked base points and version string for SAGE-RP-1.0."""
    assert SCORING_PROTOCOL_VERSION == "SAGE-RP-1.0"
    assert BASE_POINTS[PointEventType.RECON] == 5
    assert BASE_POINTS[PointEventType.ANALYSIS] == 10
    assert BASE_POINTS[PointEventType.BUILD] == 25
    assert BASE_POINTS[PointEventType.REPAIR] == 25
    assert BASE_POINTS[PointEventType.VERIFICATION] == 10
    assert BASE_POINTS[PointEventType.BREAKTHROUGH] == 50
    assert BASE_POINTS[PointEventType.CAPABILITY_CAPTURE] == 100
    assert BASE_POINTS[PointEventType.BOSS_KILL] == 100
    assert BASE_POINTS[PointEventType.BOSS_CAPTURE] == 100
    assert BASE_POINTS[PointEventType.COLLABORATION] == 10
    assert BASE_POINTS[PointEventType.REUSE] == 50
    assert BASE_POINTS[PointEventType.RECOVERY] == 25


def test_station_id_resolution_and_aliases():
    """Verify agent nameplates resolve to canonical StationIDs."""
    assert resolve_station_id("CHATGPT_C2") == StationID.MISSION_CONTROL
    assert resolve_station_id("JULES") == StationID.ENGINEERING_FLIGHT
    assert resolve_station_id("GEMINI") == StationID.INTEL_STATION
    assert resolve_station_id("HUMAN") == StationID.MISSION_DIRECTOR


def test_evidence_packet_sha_mismatch_fails_closed():
    """Verify SAGEEvidencePacket rejects mismatched target_sha and observed_sha."""
    with pytest.raises(ValueError, match="SHA mismatch"):
        SAGEEvidencePacket(
            protocol="SAGE-SEP/1",
            mission_id="M-001",
            subject_repo="Sage",
            target_sha=VALID_COMMIT_SHA,
            observed_sha="1111111111222222222233333333334444444444",
            claim_type="repair",
            claim_statement="Fixed bug",
            primary_actor=StationID.MISSION_CONTROL,
            supporting_agents=(),
            contributions=(),
            evidence_refs=("ref1",),
            verification_status="VERIFIED",
            outcome_type=PointEventType.REPAIR,
        )


def test_unverified_evidence_rejected_by_adjudicator(tmp_path: Path):
    """Verify RewardAdjudicator rejects unverified evidence packets."""
    pkt = SAGEEvidencePacket(
        protocol="SAGE-SEP/1",
        mission_id="M-002",
        subject_repo="Sage",
        target_sha=VALID_COMMIT_SHA,
        observed_sha=VALID_COMMIT_SHA,
        claim_type="repair",
        claim_statement="Fixed bug",
        primary_actor=StationID.MISSION_CONTROL,
        supporting_agents=(),
        contributions=(),
        evidence_refs=("ref1",),
        verification_status="HOLD",
        outcome_type=PointEventType.REPAIR,
    )
    request = RewardRequest(evidence_packet=pkt)
    manager = AirspaceManager(ledger_path=tmp_path / "ledger.json")
    with pytest.raises(ValueError, match="required 'VERIFIED'"):
        RewardAdjudicator.adjudicate(request, manager)


def test_adjudicator_multi_agent_contribution_and_conservation(tmp_path: Path):
    """Verify multi-agent contribution splitting and conservation principle."""
    contributions = (
        ContributionUnit(
            actor=StationID.MISSION_CONTROL,
            actor_nameplate="CHATGPT_C2",
            role="MISSION_CONTROL",
            contribution_type="DIRECTION",
            share_weight=0.5,
            claim_ref="C-1",
        ),
        ContributionUnit(
            actor=StationID.ENGINEERING_FLIGHT,
            actor_nameplate="JULES",
            role="BUILDER",
            contribution_type="EXECUTION",
            share_weight=0.3,
            claim_ref="C-2",
        ),
        ContributionUnit(
            actor=StationID.INTEL_STATION,
            actor_nameplate="GEMINI",
            role="RECON",
            contribution_type="PROBE",
            share_weight=0.2,
            claim_ref="C-3",
        ),
    )
    pkt = SAGEEvidencePacket(
        protocol="SAGE-SEP/1",
        mission_id="BOSS-0001",
        subject_repo="Sage",
        target_sha=VALID_COMMIT_SHA,
        observed_sha=VALID_COMMIT_SHA,
        claim_type="boss_repair",
        claim_statement="Boss defeated",
        primary_actor=StationID.MISSION_CONTROL,
        primary_actor_nameplate="CHATGPT_C2",
        supporting_agents=(StationID.ENGINEERING_FLIGHT, StationID.INTEL_STATION),
        contributions=contributions,
        evidence_refs=("ci_pass",),
        verification_status="VERIFIED",
        outcome_type=PointEventType.BOSS_KILL,
        boss_class=BossClass.BIG,
    )
    request = RewardRequest(evidence_packet=pkt, difficulty=2, verification_quality=2, impact=2, reuse=2)
    manager = AirspaceManager(ledger_path=tmp_path / "ledger.json")

    decision = RewardAdjudicator.adjudicate(request, manager)

    assert decision.outcome_point_pool == 200  # 100 base * 2x multiplier
    assert decision.attribution_status == "VERIFIED_ATTRIBUTION"
    assert sum(decision.attributed_points.values()) == decision.outcome_point_pool
    assert decision.attributed_points["CHATGPT_C2"] == 100
    assert decision.attributed_points["JULES"] == 60
    assert decision.attributed_points["GEMINI"] == 40
    assert decision.conservation_check_passed is True
    assert decision.xp_minted == 10  # 100 points -> 10 XP for MISSION_CONTROL
    assert "BOSS BREAKER" in decision.badge_awards


def test_adjudicator_idempotency_prevents_double_minting(tmp_path: Path):
    """Verify duplicate reward adjudication requests do not double-mint points or XP."""
    pkt = SAGEEvidencePacket(
        protocol="SAGE-SEP/1",
        mission_id="M-IDEM-01",
        subject_repo="Sage",
        target_sha=VALID_COMMIT_SHA,
        observed_sha=VALID_COMMIT_SHA,
        claim_type="repair",
        claim_statement="Idempotency test",
        primary_actor=StationID.MISSION_CONTROL,
        primary_actor_nameplate="CHATGPT_C2",
        supporting_agents=(),
        contributions=(),
        evidence_refs=("ci_pass",),
        verification_status="VERIFIED",
        outcome_type=PointEventType.REPAIR,
    )
    request = RewardRequest(evidence_packet=pkt)
    manager = AirspaceManager(ledger_path=tmp_path / "ledger.json")

    first = RewardAdjudicator.adjudicate(request, manager)
    assert first.xp_minted == 2  # 25 points -> 2 XP

    second = RewardAdjudicator.adjudicate(request, manager)
    assert second.settlement_id == first.settlement_id
    assert second.xp_minted == 0
    assert second.idempotency_check_passed is True


def test_indeterminate_attribution_fallback(tmp_path: Path):
    """Verify missing contribution ledger defaults to primary actor with ATTRIBUTION_INDETERMINATE."""
    pkt = SAGEEvidencePacket(
        protocol="SAGE-SEP/1",
        mission_id="M-INDET-01",
        subject_repo="Sage",
        target_sha=VALID_COMMIT_SHA,
        observed_sha=VALID_COMMIT_SHA,
        claim_type="recon",
        claim_statement="Recon sweep",
        primary_actor=StationID.MISSION_CONTROL,
        primary_actor_nameplate="CHATGPT_C2",
        supporting_agents=(),
        contributions=(),
        evidence_refs=("ci_pass",),
        verification_status="VERIFIED",
        outcome_type=PointEventType.RECON,
    )
    request = RewardRequest(evidence_packet=pkt)
    manager = AirspaceManager(ledger_path=tmp_path / "ledger.json")

    decision = RewardAdjudicator.adjudicate(request, manager)
    assert decision.attribution_status == "ATTRIBUTION_INDETERMINATE"
    assert decision.attributed_points == {"CHATGPT_C2": 5}


def test_c2_reward_adjudication_bridge(tmp_path: Path):
    """Verify C2 bridge dispatch converts report dict and adjudicates cleanly."""
    payload = {
        "protocol": "SAGE-SEP/1",
        "mission_id": "C2-BRIDGE-01",
        "subject": {"commit": VALID_COMMIT_SHA},
        "claim": {"statement": "Bridge dispatch"},
        "execution": {"actor": "CHATGPT_C2"},
        "evidence": ["ci"],
        "verification": {"status": "VERIFIED"},
        "outcome": {"type": "BUILD"},
    }
    manager = AirspaceManager(ledger_path=tmp_path / "ledger.json")
    res = request_c2_reward_adjudication(payload, manager=manager)
    assert res["protocol_version"] == "SAGE-RP-1.0"
    assert res["outcome_point_pool"] == 25
    assert res["primary_actor"] == "MISSION_CONTROL"


def test_sagi_learning_signal_generation(tmp_path: Path):
    """Verify build_sagi_learning_signal produces structured feedback for SAGI Brain."""
    pkt = SAGEEvidencePacket(
        protocol="SAGE-SEP/1",
        mission_id="SAGI-SIG-01",
        subject_repo="Sage",
        target_sha=VALID_COMMIT_SHA,
        observed_sha=VALID_COMMIT_SHA,
        claim_type="breakthrough",
        claim_statement="SAGI breakthrough",
        primary_actor=StationID.MISSION_CONTROL,
        primary_actor_nameplate="CHATGPT_C2",
        supporting_agents=(),
        contributions=(),
        evidence_refs=("ci_pass",),
        verification_status="VERIFIED",
        outcome_type=PointEventType.BREAKTHROUGH,
    )
    request = RewardRequest(evidence_packet=pkt)
    manager = AirspaceManager(ledger_path=tmp_path / "ledger.json")
    decision = RewardAdjudicator.adjudicate(request, manager)

    signal = RewardAdjudicator.build_sagi_learning_signal(decision)
    assert signal["mission_id"] == "SAGI-SIG-01"
    assert signal["outcome_point_pool"] == 50
    assert signal["conservation_verified"] is True
    assert "metacognitive_feedback" in signal
