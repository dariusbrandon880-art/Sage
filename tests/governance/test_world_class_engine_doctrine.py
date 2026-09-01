"""Unit test suite verifying the structure, integrity, and canonical references of the

SAGE World-Class Engine Principle Architectural Doctrine.
"""

from pathlib import Path

import pytest


def test_world_class_engine_doctrine_file_exists():
    """Verify that the doctrine file exists at the expected path."""
    repo_root = Path(__file__).resolve().parents[2]
    doctrine_path = repo_root / "docs" / "governance" / "SAGE_WORLD_CLASS_ENGINE_PRINCIPLE_DOCTRINE.md"
    assert doctrine_path.exists(), f"Doctrine file missing at {doctrine_path}"


def test_world_class_engine_doctrine_contains_eight_pillars():
    """Verify that all eight core pillars of the World-Class Engine Principle are explicitly codified."""
    repo_root = Path(__file__).resolve().parents[2]
    doctrine_path = repo_root / "docs" / "governance" / "SAGE_WORLD_CLASS_ENGINE_PRINCIPLE_DOCTRINE.md"
    content = doctrine_path.read_text(encoding="utf-8")

    expected_pillars = [
        "Pillar 1: Build Fewer, Deeper Capabilities",
        'Pillar 2: "Polish" Means System Integrity',
        "Pillar 3: Connected World-State Architecture",
        "Pillar 4: Immutable Lineage and System Memory",
        "Pillar 5: Invisible Reliability against Invisible Edge Cases",
        "Pillar 6: Build an Engine, Not Just Features",
        "Pillar 7: Reject Burnout & Hero-Dependency",
        "Pillar 8: Institutionalized Excellence & Long-Term Capability Accumulation",
    ]

    for pillar in expected_pillars:
        assert pillar in content, f"Missing expected pillar in doctrine: {pillar}"


def test_world_class_engine_doctrine_contains_core_invariants():
    """Verify non-negotiable invariants are present in the doctrine file."""
    repo_root = Path(__file__).resolve().parents[2]
    doctrine_path = repo_root / "docs" / "governance" / "SAGE_WORLD_CLASS_ENGINE_PRINCIPLE_DOCTRINE.md"
    content = doctrine_path.read_text(encoding="utf-8")

    assert "NO PROMOTION WITHOUT VERIFICATION" in content
    assert "REASONING IS NOT AUTHORITY" in content
    assert "EXACT-HEAD RECONCILIATION" in content
    assert "HUMAN-GOVERNED PROMOTION" in content


def test_world_class_engine_doctrine_boot_manifest_reference():
    """Verify that the doctrine is bound into the SAGE Chat Boot Manifest."""
    repo_root = Path(__file__).resolve().parents[2]
    boot_manifest_path = repo_root / "docs" / "SAGE-CHAT-BOOT.md"
    content = boot_manifest_path.read_text(encoding="utf-8")

    assert "docs/governance/SAGE_WORLD_CLASS_ENGINE_PRINCIPLE_DOCTRINE.md" in content
