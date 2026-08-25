"""Unit tests for SAGE C2 governance validation."""

from pathlib import Path


def test_jules_c2_capability_enhancement_directive_exists_and_conforms():
    """Verify that JULES_C2_CAPABILITY_ENHANCEMENT_DIRECTIVE.md exists and contains all required protocols and sections."""
    root_dir = Path(__file__).parent.parent
    directive_file = root_dir / "docs" / "governance" / "JULES_C2_CAPABILITY_ENHANCEMENT_DIRECTIVE.md"

    assert directive_file.exists(), "The Jules C2 Capability Enhancement Directive must exist under docs/governance/"
    content = directive_file.read_text(encoding="utf-8")
    assert "# JULES C2 CAPABILITY ENHANCEMENT DIRECTIVE" in content
    assert "Enhance Jules’ ability to operate as a true C2 execution partner" in content
    assert "stronger parallel execution" in content
    assert "better repo awareness" in content
    assert "faster capability compounding" in content

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

    assert "Repository truth > chat context > assumptions" in content
    assert "Do not collapse flights." in content
    assert "independent capability attack vector" in content
    assert "Big Strike Wave Definition" in content
    assert "Jules Capability Upgrade Targets" in content


def test_jules_five_flight_c2_capability_expansion_directive_exists_and_conforms():
    """Verify that JULES_FIVE_FLIGHT_C2_CAPABILITY_EXPANSION_DIRECTIVE.md exists and contains required sections."""
    root_dir = Path(__file__).parent.parent
    expansion_file = root_dir / "docs" / "governance" / "JULES_FIVE_FLIGHT_C2_CAPABILITY_EXPANSION_DIRECTIVE.md"
    assert expansion_file.exists(), "The Five-Flight C2 Capability Expansion Directive must exist under docs/governance/"
    content = expansion_file.read_text(encoding="utf-8")
    assert "# JULES — FIVE-FLIGHT C2 CAPABILITY EXPANSION DIRECTIVE" in content
    required_sections = [
        "REQUIRED SUPER SEARCH DOMAINS",
        "1. Multi-Agent Orchestration",
        "2. Flight Lifecycle Automation",
        "3. C2 Decision Intelligence",
        "4. Repository Intelligence",
        "5. Verification Flight Improvements",
        "FIVE-FLIGHT OPERATING MODEL TARGET",
        "HARD RULES",
        "SELF-AUDIT QUESTIONS",
        "SUCCESS CRITERIA",
    ]
    for section in required_sections:
        assert section in content, f"Missing section in expansion directive: '{section}'"


def test_five_flight_locked_model_and_big_jump_conformance():
    """Verify that campaign architecture and 5x4 operating frame contain the locked Five-Flight and Big Jump Wave definitions."""
    root_dir = Path(__file__).parent.parent
    gov_dir = root_dir / "docs" / "governance"
    campaign_doc = gov_dir / "C2_FIVE_FLIGHT_CAMPAIGN_ARCHITECTURE.md"
    assert campaign_doc.exists()
    campaign_content = campaign_doc.read_text(encoding="utf-8")
    assert "# C2 FIVE-FLIGHT MODEL (LOCKED)" in campaign_content
    assert "# Big Jump Wave Definition" in campaign_content
    assert "A **Big Jump Wave** is the canonical SAGE execution unit:" in campaign_content
    assert "independent capability attack vector" in campaign_content

    operating_frame_doc = gov_dir / "BIG_JUMP_WAVE_C2_5X4_OPERATING_FRAME.md"
    assert operating_frame_doc.exists()
    operating_content = operating_frame_doc.read_text(encoding="utf-8")
    assert "## Core Model (Independent Vehicles)" in operating_content
    assert "Big Jump Wave" in operating_content


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
    enhancement_doc = gov_dir / "JULES_C2_CAPABILITY_ENHANCEMENT_DIRECTIVE.md"
    assert enhancement_doc.exists()
    assert "JULES_FIVE_FLIGHT_C2_CAPABILITY_EXPANSION_DIRECTIVE.md" in enhancement_doc.read_text(encoding="utf-8")


def test_c2_big_jump_wave_15_flight_concurrency_doctrine_is_canonical():
    """Machine-readable guard against drift in the Big Jump Wave, 5x4, and 15-flight model."""
    root_dir = Path(__file__).parent.parent
    gov_dir = root_dir / "docs" / "governance"
    doctrine = gov_dir / "SAGE_C2_BIG_JUMP_WAVE_15_FLIGHT_CONCURRENCY_DOCTRINE.md"
    assert doctrine.exists(), "The canonical C2 Big Jump Wave concurrency doctrine must exist."
    content = doctrine.read_text(encoding="utf-8")

    required_anchors = [
        "BIG JUMP WAVE IS THE NORMAL SAGE EXECUTION WORKFLOW.",
        "5 independent paths x 4 lifecycle stages = 20 advancement cells.",
        "3 Jules sessions x 5 flights per wave = 15 distinct flight missions",
        "Each flight may use the complete governed execution aperture",
        "Multi-Node Is Optional Topology",
        "True concurrency",
        "Rolling/batched execution",
        "Super Search is an intelligence/reconnaissance sensor",
        "Git / repo truth = authority",
        "Medium Flow",
    ]
    for anchor in required_anchors:
        assert anchor in content, f"Missing canonical C2 doctrine anchor: '{anchor}'"

    # Prevent the retired operating mode from silently becoming canonical again.
    assert "Medium Flow is retired" in content
    assert "must not" in content


def test_c2_exact_order_contract_binds_big_jump_wave_doctrine():
    """Verify that the C2 anti-drift contract points to the canonical Big Jump Wave doctrine."""
    root_dir = Path(__file__).parent.parent
    contract = root_dir / "docs" / "governance" / "CHATGPT_C2_EXACT_ORDER_ANTI_DRIFT_CONTRACT.md"
    assert contract.exists()
    content = contract.read_text(encoding="utf-8")
    assert "CHATGPT_C2_EXACT_ORDER_ANTI_DRIFT" in content
    assert "SAGE_C2_BIG_JUMP_WAVE_15_FLIGHT_CONCURRENCY_DOCTRINE.md" in content
    assert "Big Jump Wave is the normal SAGE execution workflow" in content
    assert "5x4 means five paths x four lifecycle milestone gates = 20 advancement cells" in content
    assert "**Three concurrently executing Jules wave sessions can represent up to 15 distinct active flight missions (3 x 5), but only when the underlying execution is actually active.**" in content
    assert "**Multi-node is optional topology and does not require exactly three nodes.**" in content
