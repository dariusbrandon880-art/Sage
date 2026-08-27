from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOCTRINE = ROOT / "docs/governance/SAGE_HIGH_TEMPO_MISSION_EXECUTION_DOCTRINE.md"
C2_MODEL = ROOT / "docs/governance/C2_FLIGHT_CONTROL_OPERATING_MODEL.md"
JULES_DIRECTIVE = ROOT / "docs/governance/JULES_C2_CAPABILITY_ENHANCEMENT_DIRECTIVE.md"


def test_high_tempo_doctrine_is_canonical_and_wired_into_execution_docs():
    assert DOCTRINE.is_file()
    doctrine = DOCTRINE.read_text(encoding="utf-8")
    c2_model = C2_MODEL.read_text(encoding="utf-8")
    jules = JULES_DIRECTIVE.read_text(encoding="utf-8")

    required = (
        "One objective, one wave, one close",
        "Repo first",
        "Radio discipline",
        "Stop-the-line / fail-closed rule",
        "Mission completion boundary",
        "Anti-drift invariants",
        "Super Search is part of the wave",
        "Two-way-door / one-way-door discipline",
    )
    for marker in required:
        assert marker in doctrine

    pointer = "docs/governance/SAGE_HIGH_TEMPO_MISSION_EXECUTION_DOCTRINE.md"
    assert pointer in c2_model
    assert pointer in jules


def test_high_tempo_doctrine_preserves_existing_sage_loops():
    doctrine = DOCTRINE.read_text(encoding="utf-8")
    assert "SENSE -> BOUND -> ACT -> MEASURE -> LEARN -> VERIFY -> IMPROVE" in doctrine
    assert "SENSE -> RECON -> SUPER SEARCH -> BOUND -> DECIDE -> AUTHORIZE -> BUILD -> OBSERVE -> VERIFY -> COMPOUND" in doctrine
    assert "The new loop is a cadence/control layer over the existing architecture, not a replacement architecture." in doctrine
