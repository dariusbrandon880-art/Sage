from sage.c2.whole_organism_loop import WholeOrganismLoopEngine
from sage.c2.workflow_velocity import MultiSessionVelocityEngine
from sage.experimental.airspace.manager import AirspaceManager
from sage.experimental.airspace.models import StationID
from sage.experimental.airspace.nameplate import render_organism_nameplate
from sage.experimental.airspace.organism_projection import OrganismProjection
from sage.experimental.airspace.points_xp_economy import PointEventType, PointsXPEconomy


def _valid_flight_payloads():
    return [
        {
            "flight_id": f"F{i}",
            "target": f"Target Subsystem {i}",
            "classification": "ACTIVE",
            "target_files": [f"sage/target_{i}.py"],
            "target_namespaces": [f"sage.target_{i}"],
            "pr_or_change": f"PR #{300 + i}",
            "executor": lambda i=i: {"execution_result": "PASS", "tests_passed": 10 + i},
        }
        for i in range(1, 6)
    ]


def test_workflow_completion_awards_points_and_mints_xp(tmp_path):
    storage_dir = tmp_path / "evidence"
    storage_dir.mkdir(parents=True, exist_ok=True)
    manager = AirspaceManager(tmp_path / "ledger.json")
    engine = WholeOrganismLoopEngine(storage_dir=str(storage_dir))
    head_sha = engine.get_current_head_sha()

    receipt = engine.execute_whole_organism_loop(
        mission_id="progression_integration_001",
        session_id="session_progression_001",
        flight_payloads=_valid_flight_payloads(),
        exact_git_head=head_sha,
        manager=manager,
    )

    assert receipt.all_stages_completed is True
    assert "progression_reward" in receipt.learning_signal
    reward = receipt.learning_signal["progression_reward"]
    assert reward is not None
    assert reward["base_points"] == 50
    assert sum(reward["attributed_points"].values()) > 0
    assert reward["xp_minted"] > 0


def test_require_progression_adjudication_fails_closed_on_error(tmp_path, monkeypatch):
    import pytest
    engine = MultiSessionVelocityEngine()
    head_sha = "40cfd2dc54981638c680ba72a8c19324f99f8306"

    # Simulate adjudication failure
    def _failing_bridge(*args, **kwargs):
        raise ValueError("Simulated adjudication bridge failure")

    monkeypatch.setattr("sage.c2.reward_adjudication_bridge.request_c2_reward_adjudication", _failing_bridge)

    with pytest.raises(RuntimeError, match="PROGRESSION_ADJUDICATION_FAILED"):
        engine.execute_velocity_wave(
            wave_id="velocity_fail_closed_001",
            session_id="session_fail_001",
            flight_payloads=_valid_flight_payloads(),
            exact_git_head=head_sha,
            require_progression_adjudication=True,
        )


def test_velocity_wave_completion_awards_progression_reward(tmp_path):
    manager = AirspaceManager(tmp_path / "ledger.json")
    engine = MultiSessionVelocityEngine()
    head_sha = "40cfd2dc54981638c680ba72a8c19324f99f8306"

    receipt = engine.execute_velocity_wave(
        wave_id="velocity_wave_progression_001",
        session_id="session_velocity_001",
        flight_payloads=_valid_flight_payloads(),
        exact_git_head=head_sha,
        manager=manager,
    )

    assert receipt.rolls_royce_quality_passed is True
    assert receipt.organism_growth_receipt is not None
    assert "progression_reward" in receipt.organism_growth_receipt
    reward = receipt.organism_growth_receipt["progression_reward"]
    assert reward is not None
    assert reward["base_points"] == 25
    assert sum(reward["attributed_points"].values()) > 0
    assert reward["xp_minted"] > 0


def test_duplicate_workflow_completion_is_idempotent(tmp_path):
    storage_dir = tmp_path / "evidence"
    storage_dir.mkdir(parents=True, exist_ok=True)
    engine = WholeOrganismLoopEngine(storage_dir=str(storage_dir))
    head_sha = engine.get_current_head_sha()

    receipt_1 = engine.execute_whole_organism_loop(
        mission_id="idempotency_test_001",
        session_id="session_idem_001",
        flight_payloads=_valid_flight_payloads(),
        exact_git_head=head_sha,
    )

    receipt_2 = engine.execute_whole_organism_loop(
        mission_id="idempotency_test_001",
        session_id="session_idem_001",
        flight_payloads=_valid_flight_payloads(),
        exact_git_head=head_sha,
    )

    reward_1 = receipt_1.learning_signal.get("progression_reward")
    reward_2 = receipt_2.learning_signal.get("progression_reward")

    assert reward_1["settlement_id"] == reward_2["settlement_id"]
    assert reward_2["idempotency_check_passed"] is True


def test_immersion_surfaces_consume_workflow_progression_state(tmp_path):
    manager = AirspaceManager(tmp_path / "ledger.json")
    station_id = StationID.ENGINEERING_FLIGHT

    PointsXPEconomy.award_verified_event(
        manager,
        actor="Jules",
        event_id="e2e-event-1",
        station_id=station_id,
        event_type=PointEventType.BUILD,
        verified_event_ref="verified-ref-e2e-001",
        evidence_refs=("evidence-ref-e2e",),
        reason="e2e workflow verification",
        base_points=100,
        difficulty=3,
        verification_quality=5,
        impact=4,
        reuse=4,
    )

    state = manager.reconstruct_airspace_state()
    projection = OrganismProjection.project_station(manager, state, station_id)

    assert projection.points > 0
    assert projection.career_xp == projection.points // 10
    assert projection.rank_level >= 1
    assert projection.rank_title != ""

    tag = OrganismProjection.render_agent_tag(projection)
    assert f"RANK Lvl {projection.rank_level} {projection.rank_title}" in tag
    assert f"POINTS {projection.points}" in tag
    assert f"XP {projection.career_xp}" in tag

    nameplate = render_organism_nameplate(manager, station_id)
    assert f"RANK Lvl {projection.rank_level} {projection.rank_title}" in nameplate
