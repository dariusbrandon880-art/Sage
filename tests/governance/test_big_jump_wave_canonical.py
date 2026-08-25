"""Machine-readable guardrails for the canonical SAGE Big Jump Wave workflow."""

from pathlib import Path


ROOT = Path(__file__).parents[2]
CAMPAIGN = ROOT / "docs" / "governance" / "C2_FIVE_FLIGHT_CAMPAIGN_ARCHITECTURE.md"


def test_big_jump_wave_is_canonical_execution_workflow():
    content = CAMPAIGN.read_text(encoding="utf-8")
    assert "**Big Jump Wave is the normal SAGE execution workflow.**" in content
    assert "There is no Medium Flow operating mode." in content
    assert "**Retired operating mode:** Medium Flow." in content
    assert "# Big Jump Wave Definition" in content
    assert "is the canonical SAGE execution unit" in content


def test_five_flight_model_remains_locked():
    content = CAMPAIGN.read_text(encoding="utf-8")
    assert "# C2 FIVE-FLIGHT MODEL (LOCKED)" in content
    assert content.count("FLIGHT 1") >= 1
    assert content.count("FLIGHT 2") >= 1
    assert content.count("FLIGHT 3") >= 1
    assert content.count("FLIGHT 4") >= 1
    assert content.count("FLIGHT 5") >= 1
    assert "C2 RECONVERGENCE" in content


def test_big_jump_wave_preserves_governance_boundaries():
    content = CAMPAIGN.read_text(encoding="utf-8")
    for required in (
        "RECON + SUPER SEARCH",
        "BOUND + AUTHORIZE",
        "INDEPENDENT VERIFY",
        "EVIDENCE / RECEIPTS",
        "The three SAGE lanes remain authoritative.",
    ):
        assert required in content
