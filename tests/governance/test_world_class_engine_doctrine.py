"""Verification tests for the SAGE World-Class Engine Principle doctrine."""

from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def test_world_class_engine_doctrine_exists_and_has_eight_principles() -> None:
    path = _repo_root() / "docs/governance/SAGE_WORLD_CLASS_ENGINE_PRINCIPLE_DOCTRINE.md"
    assert path.is_file()
    content = path.read_text(encoding="utf-8")
    expected = [
        "### 1. Build fewer, deeper capabilities",
        "### 2. Polish means system integrity",
        "### 3. Build a connected world-state architecture",
        "### 4. Give the system memory through traceable lineage",
        "### 5. Obsess over invisible reliability",
        "### 6. Strengthen the substrate before multiplying features",
        "### 7. Reject hero dependency and institutionalize excellence",
        "### 8. Optimize for long-term capability accumulation",
    ]
    for heading in expected:
        assert heading in content


def test_world_class_engine_doctrine_contains_non_negotiable_controls() -> None:
    path = _repo_root() / "docs/governance/SAGE_WORLD_CLASS_ENGINE_PRINCIPLE_DOCTRINE.md"
    content = path.read_text(encoding="utf-8")
    for invariant in (
        "SENSE -> BOUND -> ACT -> MEASURE -> LEARN -> VERIFY -> IMPROVE",
        "NO PROMOTION WITHOUT VERIFICATION",
        "REASONING IS NOT AUTHORITY",
        "EXACT-HEAD RECONCILIATION",
        "HUMAN-GOVERNED PROMOTION",
    ):
        assert invariant in content


def test_chat_boot_binds_world_class_engine_doctrine() -> None:
    path = _repo_root() / "docs/SAGE-CHAT-BOOT.md"
    content = path.read_text(encoding="utf-8")
    assert "SAGE_WORLD_CLASS_ENGINE_PRINCIPLE_DOCTRINE.md" in content


def test_big_jump_wave_frame_binds_world_class_engine_doctrine() -> None:
    path = _repo_root() / "docs/governance/BIG_JUMP_WAVE_C2_5X4_OPERATING_FRAME.md"
    content = path.read_text(encoding="utf-8")
    assert "SAGE_WORLD_CLASS_ENGINE_PRINCIPLE_DOCTRINE.md" in content
