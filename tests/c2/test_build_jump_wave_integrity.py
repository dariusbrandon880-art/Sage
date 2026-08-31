"""Integrity tests for Big Jump Wave evidence isolation."""

from pathlib import Path

from sage.c2.build_jump_wave import BuildJumpWaveEngine, FlightMissionSpec
from sage.c2.flight_collision_lock import FlightLockRequest


def test_big_jump_wave_evidence_is_sha_namespaced(tmp_path, monkeypatch):
    engine = BuildJumpWaveEngine(storage_dir=str(tmp_path))
    monkeypatch.setattr(engine, "get_current_head_sha", lambda: "a" * 40)

    missions = [
        FlightMissionSpec(
            flight_id=f"F{i}",
            mission_name=f"wave-mission-{i}",
            target_path=f"sage/test_target_{i}.py",
            collision_zone=f"sage.test_{i}",
            evidence_ref=f"wave/F{i}.json",
            pr_or_change=f"test-{i}",
            test_references=[],
        )
        for i in range(1, 6)
    ]

    package = engine.execute_wave(wave_id="wave-isolation", missions=missions)
    assert package.reconvergence_verdict == "PASS"
    for i in range(1, 6):
        receipt = Path(tmp_path) / "waves" / "wave-isolation" / ("a" * 40) / f"F{i}_receipt.json"
        assert receipt.exists()
        assert "legacy" not in str(receipt)

    retry = engine.lock_manager.acquire_lock(
        FlightLockRequest(
            session_id="retry-session",
            flight_id="F1-retry",
            target_files=["sage/test_target_1.py"],
            target_namespaces=["sage.test_1"],
        )
    )
    assert retry.acquired is True
