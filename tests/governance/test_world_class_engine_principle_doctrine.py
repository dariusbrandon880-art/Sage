from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DOCTRINE = REPO_ROOT / "docs/governance/SAGE_WORLD_CLASS_ENGINE_PRINCIPLE_DOCTRINE.md"
BOOT = REPO_ROOT / "docs/governance/C2_MISSION_CONTROL_BOOT_SEQUENCE.md"


def test_world_class_engine_doctrine_exists_and_contains_eight_principles():
    text = DOCTRINE.read_text(encoding="utf-8")
    assert text.startswith("# SAGE WORLD-CLASS ENGINE PRINCIPLE DOCTRINE")
    for index, title in enumerate(
        (
            "Build fewer, deeper capabilities",
            "Polish means system integrity",
            "Build a connected world-state architecture",
            "Give the system memory through traceable lineage",
            "Obsess over invisible reliability",
            "Strengthen the substrate before multiplying features",
            "Reject hero dependency and institutionalize excellence",
            "Optimize for long-term capability accumulation",
        ),
        start=1,
    ):
        assert f"### {index}. {title}" in text


def test_doctrine_preserves_fail_closed_and_sixty_forty_invariants():
    text = DOCTRINE.read_text(encoding="utf-8")
    assert "60% effort protects and strengthens the substrate." in text
    assert "40% effort advances new capability." in text
    assert "FAIL CLOSED > GUESS" in text
    assert "Failure exists → prove it → harden it → attack it → verify it → promote it → compound it." in text


def test_c2_boot_sequence_binds_world_class_engine_doctrine():
    text = BOOT.read_text(encoding="utf-8")
    assert "SAGE_WORLD_CLASS_ENGINE_PRINCIPLE_DOCTRINE.md" in text
    assert "World-Class Engine Principle" in text
