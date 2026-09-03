"""Regression coverage for SAGE-RP-1.0 repair invariants."""
from pathlib import Path
import math
import pytest

from sage.experimental.airspace.boss_progression import BossClass, BossProgressionAuthority
from sage.experimental.airspace.manager import AirspaceManager
from sage.experimental.airspace.models import StationID
from sage.experimental.airspace.points_xp_economy import PointEventType
from sage.experimental.airspace.reward_protocol import ContributionUnit, RewardAdjudicator, RewardRequest, SAGEEvidencePacket

SHA = "75c583db46bb90cc2af925f807e1809bd7023f12"


def packet(tmp_path: Path, *, contributions=(), digest="", outcome=PointEventType.BOSS_KILL):
    return SAGEEvidencePacket(protocol="SAGE-SEP/1", mission_id="RP-REPAIR", subject_repo="dariusbrandon880-art/Sage",
        target_sha=SHA, observed_sha=SHA, claim_type="repair", claim_statement="repair invariant",
        primary_actor=StationID.MISSION_CONTROL, primary_actor_nameplate="CHATGPT_C2", supporting_agents=(),
        contributions=tuple(contributions), evidence_refs=("exact_head_ci",), verification_status="VERIFIED",
        outcome_type=outcome, boss_class=BossClass.BIG, integrity_digest=digest)


def test_contribution_pool_is_conserved_without_remultiplication(tmp_path: Path):
    contributions = (
        ContributionUnit(StationID.MISSION_CONTROL, "C2", "DIRECTION", .5, "c1", "CHATGPT_C2"),
        ContributionUnit(StationID.ENGINEERING_FLIGHT, "BUILD", "EXECUTION", .3, "c2", "JULES"),
        ContributionUnit(StationID.INTEL_STATION, "RECON", "PROBE", .2, "c3", "GEMINI"),
    )
    mgr = AirspaceManager(ledger_path=tmp_path / "ledger.json")
    decision = RewardAdjudicator.adjudicate(RewardRequest(packet(tmp_path, contributions=contributions), difficulty=2, verification_quality=2, impact=2, reuse=2), mgr)
    assert decision.outcome_point_pool == 200
    assert decision.attributed_points == {"CHATGPT_C2": 100, "JULES": 60, "GEMINI": 40}
    assert sum(decision.attributed_points.values()) == 200
    points = [e["payload"]["verified_points"] for e in mgr._load_raw_events() if e.get("event_type") == "POINTS_AWARDED"]
    assert sorted(points) == [40, 60, 100]
    assert sum(points) == 200


def test_promotion_is_not_claimed_by_reward_protocol(tmp_path: Path):
    mgr = AirspaceManager(ledger_path=tmp_path / "ledger.json")
    decision = RewardAdjudicator.adjudicate(RewardRequest(packet(tmp_path, outcome=PointEventType.REPAIR)), mgr)
    assert decision.promotion_eligibility is False
    settlement = [e for e in mgr._load_raw_events() if e.get("event_type") == "REWARD_SETTLED"][-1]
    assert settlement["payload"]["promotion_eligibility"] is False


def test_single_boss_outcome_does_not_mint_cadence_badge(tmp_path: Path):
    mgr = AirspaceManager(ledger_path=tmp_path / "ledger.json")
    decision = RewardAdjudicator.adjudicate(RewardRequest(packet(tmp_path),), mgr)
    assert decision.badge_awards == ()
    progression = BossProgressionAuthority.project_station(mgr, StationID.MISSION_CONTROL)
    assert progression.big_kills == 1
    assert progression.big_badges == 0


def test_non_sha256_digest_is_rejected(tmp_path: Path):
    mgr = AirspaceManager(ledger_path=tmp_path / "ledger.json")
    with pytest.raises(ValueError, match="integrity_digest"):
        RewardAdjudicator.adjudicate(RewardRequest(packet(tmp_path, digest="sha256:" + SHA)), mgr)


def test_duplicate_nameplate_is_rejected(tmp_path: Path):
    contributions = (
        ContributionUnit(StationID.MISSION_CONTROL, "C2", "DIRECTION", .5, "c1", "CHATGPT_C2"),
        ContributionUnit(StationID.MISSION_CONTROL, "C2", "DIRECTION", .5, "c2", "CHATGPT_C2"),
    )
    mgr = AirspaceManager(ledger_path=tmp_path / "ledger.json")
    with pytest.raises(ValueError, match="Duplicate"):
        RewardAdjudicator.adjudicate(RewardRequest(packet(tmp_path, contributions=contributions)), mgr)


def test_nonfinite_weight_is_rejected():
    with pytest.raises(ValueError, match="finite"):
        ContributionUnit(StationID.MISSION_CONTROL, "C2", "DIRECTION", math.nan, "c1", "CHATGPT_C2")


def test_actor_nameplate_mismatch_is_rejected():
    with pytest.raises(ValueError, match="mismatch"):
        ContributionUnit(StationID.MISSION_CONTROL, "C2", "DIRECTION", 1.0, "c1", "JULES")


def test_replay_is_idempotent(tmp_path: Path):
    mgr = AirspaceManager(ledger_path=tmp_path / "ledger.json")
    request = RewardRequest(packet(tmp_path, outcome=PointEventType.REPAIR))
    first = RewardAdjudicator.adjudicate(request, mgr)
    second = RewardAdjudicator.adjudicate(request, mgr)
    assert second.settlement_id == first.settlement_id
    assert second.xp_minted == 0
