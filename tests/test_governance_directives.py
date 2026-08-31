"""Unit tests for SAGE C2 governance validation."""

from pathlib import Path


def test_jules_c2_capability_enhancement_directive_exists_and_conforms():
    root_dir = Path(__file__).parent.parent
    directive_file = root_dir / "docs" / "governance" / "JULES_C2_CAPABILITY_ENHANCEMENT_DIRECTIVE.md"
    assert directive_file.exists()
    content = directive_file.read_text(encoding="utf-8")
    assert "# JULES C2 CAPABILITY ENHANCEMENT DIRECTIVE" in content
    assert "Enhance Jules’ ability to operate as a true C2 execution partner" in content
    assert "stronger parallel execution" in content
    assert "better repo awareness" in content
    assert "faster capability compounding" in content
    required_sections = [
        "1. ALWAYS START WITH REPO TRUTH", "REPO FIRST PROTOCOL",
        "2. SUPER SEARCH ENHANCEMENT PROTOCOL", "3. BIG JUMP WAVE PARALLEL CAPABILITY MODE",
        "4. CONCURRENT EXECUTION IMPROVEMENT", "5. OPERATING LOOP", "6. C2 ROLE DEFINITION",
        "7. FAILURE MEMORY", "FINAL DIRECTIVE",
    ]
    for section in required_sections:
        assert section in content
    assert "Repository truth > chat context > assumptions" in content
    assert "Do not collapse flights." in content
    assert "independent capability attack vector" in content
    assert "Big Strike Wave Definition" in content
    assert "Jules Capability Upgrade Targets" in content


def test_jules_five_flight_c2_capability_expansion_directive_exists_and_conforms():
    root_dir = Path(__file__).parent.parent
    expansion_file = root_dir / "docs" / "governance" / "JULES_FIVE_FLIGHT_C2_CAPABILITY_EXPANSION_DIRECTIVE.md"
    assert expansion_file.exists()
    content = expansion_file.read_text(encoding="utf-8")
    assert "# JULES — FIVE-FLIGHT C2 CAPABILITY EXPANSION DIRECTIVE" in content
    for section in [
        "REQUIRED SUPER SEARCH DOMAINS", "1. Multi-Agent Orchestration", "2. Flight Lifecycle Automation",
        "3. C2 Decision Intelligence", "4. Repository Intelligence", "5. Verification Flight Improvements",
        "FIVE-FLIGHT OPERATING MODEL TARGET", "HARD RULES", "SELF-AUDIT QUESTIONS", "SUCCESS CRITERIA",
    ]:
        assert section in content


def test_five_flight_locked_model_and_big_strike_conformance():
    root_dir = Path(__file__).parent.parent
    gov_dir = root_dir / "docs" / "governance"
    campaign_content = (gov_dir / "C2_FIVE_FLIGHT_CAMPAIGN_ARCHITECTURE.md").read_text(encoding="utf-8")
    assert "# C2 FIVE-FLIGHT MODEL (LOCKED)" in campaign_content
    assert "Big Strike Wave Definition" in campaign_content
    assert "independent capability attack vector" in campaign_content
    operating_content = (gov_dir / "BIG_JUMP_WAVE_C2_5X4_OPERATING_FRAME.md").read_text(encoding="utf-8")
    assert "## Core Model — Five Reusable Open Slots" in operating_content
    assert "OPEN" in operating_content
    assert "reusable execution slot" in operating_content
    assert "no permanent capability labels" in operating_content
    assert "Big Strike Wave Definition" in operating_content


def test_governance_cross_references():
    root_dir = Path(__file__).parent.parent
    gov_dir = root_dir / "docs" / "governance"
    ref_doc = "docs/governance/JULES_C2_CAPABILITY_ENHANCEMENT_DIRECTIVE.md"
    for name in ["C2_FRAME.md", "C2_FLIGHT_CONTROL_OPERATING_MODEL.md", "BIG_JUMP_WAVE_C2_5X4_OPERATING_FRAME.md"]:
        assert ref_doc in (gov_dir / name).read_text(encoding="utf-8")
    enhancement_doc = gov_dir / "JULES_C2_CAPABILITY_ENHANCEMENT_DIRECTIVE.md"
    assert "JULES_FIVE_FLIGHT_C2_CAPABILITY_EXPANSION_DIRECTIVE.md" in enhancement_doc.read_text(encoding="utf-8")


def test_c2_big_jump_wave_15_flight_concurrency_doctrine_is_canonical():
    root_dir = Path(__file__).parent.parent
    content = (root_dir / "docs" / "governance" / "SAGE_C2_BIG_JUMP_WAVE_15_FLIGHT_CONCURRENCY_DOCTRINE.md").read_text(encoding="utf-8")
    for anchor in [
        "BIG JUMP WAVE IS THE NORMAL SAGE EXECUTION WORKFLOW.",
        "5 independent paths x 4 lifecycle stages = 20 advancement cells.",
        "3 Jules sessions x 5 flights per wave = 15 distinct flight missions",
        "Each flight may use the complete governed execution aperture",
        "MULTI-NODE = OPTIONAL TOPOLOGY", "True concurrency", "Rolling/batched execution",
        "Super Search is a reconnaissance sensor", "GIT / REPO TRUTH = AUTHORITY", "Medium Flow",
    ]:
        assert anchor in content
    assert "Medium Flow is retired" in content
    assert "must not" in content


def test_c2_exact_order_contract_binds_big_jump_wave_doctrine():
    root_dir = Path(__file__).parent.parent
    content = (root_dir / "docs" / "governance" / "CHATGPT_C2_EXACT_ORDER_ANTI_DRIFT_CONTRACT.md").read_text(encoding="utf-8")
    for anchor in [
        "CHATGPT_C2_EXACT_ORDER_ANTI_DRIFT", "SAGE_C2_BIG_JUMP_WAVE_15_FLIGHT_CONCURRENCY_DOCTRINE.md",
        "Big Jump Wave is the normal SAGE execution workflow",
        "5x4 means five paths x four lifecycle milestone gates = 20 advancement cells",
        "Three concurrently executing Jules wave sessions can represent up to 15 distinct active flight missions",
        "Multi-node is optional topology", "Five flights is concurrent mission ownership across independent vehicles",
        "PREFLIGHT -> EXECUTE -> TEST -> EVIDENCE -> VERIFY -> RECONCILE -> REPORT",
        "SAGE is one governed organism with modular organs",
    ]:
        assert anchor in content


def test_continuous_exchange_immersion_doctrine_is_canonical_and_bound():
    root_dir = Path(__file__).parent.parent
    gov_dir = root_dir / "docs" / "governance"
    doctrine = gov_dir / "SAGE_CONTINUOUS_EXCHANGE_IMMERSION_DOCTRINE.md"
    contract = gov_dir / "CHATGPT_C2_EXACT_ORDER_ANTI_DRIFT_CONTRACT.md"
    assert doctrine.exists()
    doctrine_content = doctrine.read_text(encoding="utf-8")
    contract_content = contract.read_text(encoding="utf-8")
    for anchor in [
        "Every governed exchange enters the same canonical control plane",
        "Every exchange is a fresh governance boundary",
        "Session continuity is a **rehydration mechanism**",
        "Station identity is runtime-owned",
        "Immersion is a **projection**, not authority",
        "Super Search and SAGI research are **external intelligence sensors**",
        "Every new Jules session must begin with",
        "The doctrine itself is not proof of enforcement",
    ]:
        assert anchor in doctrine_content
    assert "CONTINUOUS_EXCHANGE_IMMERSION_DOCTRINE.md" in contract_content
    assert "Every governed exchange must remain bound" in contract_content
    assert "CONTINUITY RULE: each governed exchange is a new verification boundary" in contract_content
    assert "IMMERSION RULE: station identity, governance mode, and presentation must derive from the governed runtime projection" in contract_content
    assert "Contract ID: `CHATGPT_C2_EXACT_ORDER_ANTI_DRIFT`" in contract_content


def test_organism_jigsaw_architecture_directive_conforms():
    root_dir = Path(__file__).parent.parent
    content = (root_dir / "docs" / "governance" / "SAGE_ORGANISM_JIGSAW_ARCHITECTURE.md").read_text(encoding="utf-8")
    for anchor in [
        "SAGE_ORGANISM_JIGSAW_ARCHITECTURE", "Executive Summary: One Organism, Modular Organs",
        "The Jigsaw Taxonomy: Subsystem Relationships", "The 10 Connective Tissue Integration Gates",
        "CORE", "SERVICE", "PROJECTION", "EVIDENCE_LEARNING", "Gate 1: Mission Intake → C2 Core",
        "Gate 10: Capability Warehouse → Next Mission", "Law 13",
    ]:
        assert anchor in content
