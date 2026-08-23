"""Unit tests for Jules C2 Capability Enhancement Directive governance validation."""

from pathlib import Path


def test_jules_c2_capability_enhancement_directive_exists_and_conforms():
    """Verify that JULES_C2_CAPABILITY_ENHANCEMENT_DIRECTIVE.md exists and contains all required protocols and sections."""
    root_dir = Path(__file__).parent.parent
    directive_file = root_dir / "docs" / "governance" / "JULES_C2_CAPABILITY_ENHANCEMENT_DIRECTIVE.md"

    assert directive_file.exists(), "The Jules C2 Capability Enhancement Directive must exist under docs/governance/"

    content = directive_file.read_text(encoding="utf-8")

    # Title check
    assert "# JULES C2 CAPABILITY ENHANCEMENT DIRECTIVE" in content

    # Mission and core principles check
    assert "Enhance Jules’ ability to operate as a true C2 execution partner" in content
    assert "stronger parallel execution" in content
    assert "better repo awareness" in content
    assert "faster capability compounding" in content

    # Protocol and section checks
    required_sections = [
        "1. ALWAYS START WITH REPO TRUTH",
        "REPO FIRST PROTOCOL",
        "2. SUPER SEARCH ENHANCEMENT PROTOCOL",
        "3. BIG JUMP WAVE PARALLEL CAPABILITY MODE",
        "4. CONCURRENT EXECUTION IMPROVEMENT",
        "5. OPERATING LOOP",
        "6. C2 ROLE DEFINITION",
        "7. FAILURE MEMORY",
        "FINAL DIRECTIVE",
    ]

    for section in required_sections:
        assert section in content, f"Missing required section or protocol in directive: '{section}'"

    # Core rule checks
    assert "Repository truth > chat context > assumptions" in content
    assert "Do not collapse flights." in content


def test_governance_cross_references():
    """Verify that existing governance documents cross-reference the Jules C2 Capability Enhancement Directive."""
    root_dir = Path(__file__).parent.parent
    gov_dir = root_dir / "docs" / "governance"

    ref_doc = "docs/governance/JULES_C2_CAPABILITY_ENHANCEMENT_DIRECTIVE.md"

    c2_frame = gov_dir / "C2_FRAME.md"
    assert c2_frame.exists()
    assert ref_doc in c2_frame.read_text(encoding="utf-8")

    c2_operating_model = gov_dir / "C2_FLIGHT_CONTROL_OPERATING_MODEL.md"
    assert c2_operating_model.exists()
    assert ref_doc in c2_operating_model.read_text(encoding="utf-8")

    big_jump_frame = gov_dir / "BIG_JUMP_WAVE_C2_5X4_OPERATING_FRAME.md"
    assert big_jump_frame.exists()
    assert ref_doc in big_jump_frame.read_text(encoding="utf-8")
