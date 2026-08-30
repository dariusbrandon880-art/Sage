from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BOOT = ROOT / "docs" / "SAGE-CHAT-BOOT.md"
HARDENING = ROOT / "docs" / "governance" / "SAGE_C2_PERSISTENCE_AND_IMMERSION_HARDENING_PROTOCOL.md"
DESIGN = ROOT / "docs" / "architecture" / "SAGE-IMMERSION-LANGUAGE-DESIGN-LAB.md"


def test_boot_manifest_requires_immersion_across_the_full_workflow():
    text = BOOT.read_text(encoding="utf-8")
    assert "IMMERSION IS PART OF THE FULL SAGE WORKFLOW, NOT AN OPTIONAL PRESENTATION MODE." in text
    assert "[SAGE::C2::CHATGPT] **C2 Mission Control**" in text
    assert "docs/architecture/SAGE-IMMERSION-LANGUAGE-DESIGN-LAB.md" in text
    assert "REHYDRATE -> REALITY LOCK -> MISSION LOCK -> IDENTITY LOCK -> ACTIVE-FRONTIER LOCK -> EXECUTE" in text


def test_hardening_contract_covers_known_immersion_drift_modes():
    text = HARDENING.read_text(encoding="utf-8")
    required = (
        "long-context truncation",
        "omitted nameplate in an intermediate response",
        "reopened old chat with changed `main`",
        "new chat with repository available",
        "repository unavailable",
        "IMMERSION CONTINUOUS",
    )
    for marker in required:
        assert marker in text


def test_design_lab_preserves_interface_and_truth_boundaries():
    text = DESIGN.read_text(encoding="utf-8")
    assert "Real SAGE event → canonical state change → immersion projection" in text
    assert "Never immersion → assumed achievement → canonical state" in text
    assert "ChatGPT is the interface" in text
    assert "Military / aerospace / NASA-style operational language" in text
