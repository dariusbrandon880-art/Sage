from pathlib import Path
from unittest.mock import patch

from sage.c2.chatgpt_immersion import project_chatgpt_immersion_response
from sage.c2.immersion_projection import (
    C2ProgressionProjection,
    project_c2_progression,
    project_mission_hud,
)
from sage.c2.immersion_state import ExecutionPhase, FlightStatus, ImmersionState, TrustStatus
from sage.c2.response_envelope import hud_update_key
from sage.experimental.airspace.boss_progression import BossClass, BossOutcome, BossProgressionAuthority
from sage.experimental.airspace.manager import AirspaceManager
from sage.experimental.airspace.models import StationID, XPCategory
from sage.experimental.airspace.organism_projection import OrganismProjection
from sage.experimental.airspace.points_xp_economy import PointEventType, PointsXPEconomy


def _state() -> ImmersionState:
    return ImmersionState(
        station_identity="[SAGE::C2::CHATGPT]",
        mission="Governed Operating Picture",
        phase=ExecutionPhase.VERIFY,
        flight_id="F1",
        flight_status=FlightStatus.ACTIVE,
        trust_status=TrustStatus.VERIFIED,
        frontier="Immersion Seam",
        gate="HUD_VERIFICATION",
        next_move="verify real progression in HUD",
        evidence_refs=("ref-101",),
        provenance_head="0123456789012345678901234567890123456789",
    )


def test_hud_renders_real_progression_from_canonical_ledger(tmp_path: Path) -> None:
    ledger_file = tmp_path / "ledger.json"
    mgr = AirspaceManager(ledger_file)

    mgr.award_xp(
        actor="C2",
        station_id=StationID.MISSION_CONTROL,
        category=XPCategory.MISSION_XP,
        amount=42,
        reason="Test Cognition",
        verified_event_ref="ref-101",
    )
    PointsXPEconomy.award_verified_event(
        mgr,
        event_id="evt_p_1",
        actor="C2",
        station_id=StationID.MISSION_CONTROL,
        event_type=PointEventType.BUILD,
        reason="Build awarded",
        verified_event_ref="ref-101",
        evidence_refs=["ref-101"],
    )

    state = _state()
    response = project_chatgpt_immersion_response(state, manager=mgr)
    rendered = response.render()

    assert "RANK     : Recruit — L1" in rendered
    assert "POINTS   :" in rendered
    assert "XP       : 42" in rendered
    assert "42 / 100 XP" in rendered

    assert "MISSION  : Governed Operating Picture" in rendered
    assert "FLIGHT   : F1 (ACTIVE)" in rendered
    assert "TRUST    : VERIFIED" in rendered
    assert "EVIDENCE : 1 verified ref(s) [ref-101]" in rendered


def test_boss_kills_captures_and_badges_come_from_canonical_projection(tmp_path: Path) -> None:
    ledger_file = tmp_path / "ledger.json"
    mgr = AirspaceManager(ledger_file)

    outcome = BossOutcome(
        event_id="evt_boss_01",
        station_id=StationID.MISSION_CONTROL,
        boss_class=BossClass.MAJOR,
        verified_event_ref="ref_boss_1",
        evidence_refs=("ref_boss_1",),
        kill=True,
    )
    BossProgressionAuthority.record_verified_outcome(
        mgr, actor="Director", outcome=outcome, reason="Major Boss Defeated"
    )

    state = _state()
    response = project_chatgpt_immersion_response(state, manager=mgr)
    rendered = response.render()

    assert "KILLS    : ⚔️ 1" in rendered
    assert "CAPTURES : ┃ 0" in rendered
    assert "BOSS     : ⭐×0  ⭐⭐×0" in rendered


def test_missing_progression_state_fails_closed_to_unknown_hold() -> None:
    state = _state()
    with patch("sage.c2.chatgpt_immersion._load_airspace_manager", side_effect=RuntimeError("no ledger")):
        response = project_chatgpt_immersion_response(state, organism_tag=None, manager=None)
        rendered = response.render()

    assert "RANK UNKNOWN" in rendered
    assert "POINTS UNKNOWN" in rendered
    assert "XP UNKNOWN" in rendered

    assert "RANK     : UNKNOWN" in rendered
    assert "POINTS   : UNKNOWN" in rendered
    assert "XP       : UNKNOWN" in rendered
    assert "PROGRESS : HOLD / UNVERIFIED" in rendered


def test_hud_update_key_changes_when_progression_changes(tmp_path: Path) -> None:
    ledger_file = tmp_path / "ledger.json"
    mgr = AirspaceManager(ledger_file)

    state = _state()
    resp1 = project_chatgpt_immersion_response(state, manager=mgr)
    key1 = resp1.hud_update_key

    PointsXPEconomy.award_verified_event(
        mgr,
        event_id="evt_p_delta",
        actor="C2",
        station_id=StationID.MISSION_CONTROL,
        event_type=PointEventType.BUILD,
        reason="Points Delta",
        verified_event_ref="ref-delta-1",
        evidence_refs=["ref-delta-1"],
    )

    resp2 = project_chatgpt_immersion_response(state, manager=mgr)
    key2 = resp2.hud_update_key

    assert key1 != key2


def test_unchanged_hud_state_remains_suppressible(tmp_path: Path) -> None:
    ledger_file = tmp_path / "ledger.json"
    mgr = AirspaceManager(ledger_file)

    state = _state()
    resp1 = project_chatgpt_immersion_response(state, manager=mgr)
    key1 = resp1.hud_update_key

    resp2 = project_chatgpt_immersion_response(
        state, manager=mgr, previous_hud_update_key=key1, force_hud=False
    )
    assert resp2.should_render_hud is False
    rendered2 = resp2.render()
    assert "01 — COMMAND BAND" not in rendered2

    resp3 = project_chatgpt_immersion_response(
        state, manager=mgr, previous_hud_update_key=key1, force_hud=True
    )
    assert resp3.should_render_hud is True
    assert "01 — COMMAND BAND" in resp3.render()


def test_renderer_and_projection_are_read_only(tmp_path: Path) -> None:
    ledger_file = tmp_path / "ledger.json"
    mgr = AirspaceManager(ledger_file)

    events_before = len(mgr._load_raw_events())
    state = _state()
    resp = project_chatgpt_immersion_response(state, manager=mgr)
    _ = resp.render()

    events_after = len(mgr._load_raw_events())
    assert events_before == events_after
    assert resp.immersion_envelope.read_only is True
