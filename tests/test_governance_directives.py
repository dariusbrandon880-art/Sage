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


def test_jules_five_flight_c2_capability_expansion_directive_exists_and_conforms():
    """Verify that JULES_FIVE_FLIGHT_C2_CAPABILITY_EXPANSION_DIRECTIVE.md exists and contains required sections."""
    root_dir = Path(__file__).parent.parent
    expansion_file = root_dir / "docs" / "governance" / "JULES_FIVE_FLIGHT_C2_CAPABILITY_EXPANSION_DIRECTIVE.md"

    assert expansion_file.exists(), "The Five-Flight C2 Capability Expansion Directive must exist under docs/governance/"

    content = expansion_file.read_text(encoding="utf-8")

    # Title check
    assert "# JULES — FIVE-FLIGHT C2 CAPABILITY EXPANSION DIRECTIVE" in content

    # Section checks
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


def test_c2_big_build_learning_loop_experiment_report_exists_and_conforms():
    """Verify that C2_BIG_BUILD_LEARNING_LOOP_EXPERIMENT_REPORT.md exists and contains required sections."""
    root_dir = Path(__file__).parent.parent
    report_file = root_dir / "docs" / "governance" / "C2_BIG_BUILD_LEARNING_LOOP_EXPERIMENT_REPORT.md"

    assert report_file.exists(), "The C2 Big Build Learning Loop Experiment Report must exist under docs/governance/"

    content = report_file.read_text(encoding="utf-8")

    assert "# C2 BIG BUILD LEARNING LOOP EXPERIMENT REPORT" in content
    assert "NASA Systems Engineering Principles" in content
    assert "Henry Ford Production Principles" in content
    assert "Lamborghini Performance Engineering" in content
    assert "FLIGHT A — RESEARCH INTELLIGENCE" in content
    assert "FLIGHT B — C2 OPERATING CAPABILITY" in content
    assert "FLIGHT C — BIG JUMP WAVE ENGINE" in content
    assert "FLIGHT D — FALSIFICATION & FAILURE MEMORY" in content
    assert "FLIGHT E — CAPABILITY WAREHOUSE" in content
    assert "PROVEN ASSETS" in content
    assert "ACTIVE HYPOTHESES" in content


def test_big_strike_immersion_vocabulary_directive_exists_and_conforms():
    """Verify that BIG_STRIKE_IMMERSION_VOCABULARY_DIRECTIVE.md exists and contains required sections."""
    root_dir = Path(__file__).parent.parent
    strike_file = root_dir / "docs" / "governance" / "BIG_STRIKE_IMMERSION_VOCABULARY_DIRECTIVE.md"

    assert strike_file.exists(), "The Big Strike Immersion Vocabulary Directive must exist under docs/governance/"

    content = strike_file.read_text(encoding="utf-8")

    assert "# SAGE BIG STRIKE CAMPAIGN & IMMERSION VOCABULARY DIRECTIVE" in content
    assert "Precision Strike" in content
    assert "Recon Strike" in content
    assert "Defense Strike" in content
    assert "Countermeasure Sweep" in content
    assert "Supply Drop" in content
    assert "Command Push" in content
    assert "After Action Report" in content
    assert "SAGE FLEET COMMAND HUD" in content


def test_game_immersion_cross_media_research_report_exists_and_conforms():
    """Verify that GAME_IMMERSION_CROSS_MEDIA_RESEARCH_REPORT.md exists and contains required sections."""
    root_dir = Path(__file__).parent.parent
    report_file = root_dir / "docs" / "governance" / "GAME_IMMERSION_CROSS_MEDIA_RESEARCH_REPORT.md"

    assert report_file.exists(), "The Game Immersion Cross-Media Research Report must exist under docs/governance/"

    content = report_file.read_text(encoding="utf-8")

    assert "# GAME IMMERSION & CROSS-MEDIA SIMULATION RESEARCH REPORT" in content
    assert "EVE Online & Elite Dangerous" in content
    assert "XCOM & Darkest Dungeon" in content
    assert "DCS World & Arma 3" in content
    assert "StarCraft II & League of Legends Broadcast HUDs" in content
    assert "Star Trek (LCARS) & Ender's Game (Command School)" in content
    assert "Iron Man (JARVIS/FRIDAY) & The Matrix (Operator Station)" in content
    assert "FLIGHT 1 — TACTICAL SIMULATORS & PERSISTENT WORLD GAMES" in content
    assert "FLIGHT 2 — ESPORTS & LIVE-STREAM HUD ARCHITECTURES" in content
    assert "FLIGHT 3 — SCI-FI CINEMA & COMMAND INTERFACES" in content
    assert "FLIGHT 4 — ADVERSARIAL FALSIFICATION & ANTI-GAMIFICATION GAURDS" in content
    assert "FLIGHT 5 — CAPABILITY WAREHOUSE & SAGE INTEGRATION" in content


def test_sage_big_build_jump_wave_readiness_receipt_exists_and_conforms():
    """Verify that SAGE_BIG_BUILD_JUMP_WAVE_READINESS_RECEIPT.md exists and contains required sections."""
    root_dir = Path(__file__).parent.parent
    receipt_file = root_dir / "docs" / "governance" / "SAGE_BIG_BUILD_JUMP_WAVE_READINESS_RECEIPT.md"

    assert receipt_file.exists(), "The SAGE Big Build Jump Wave Readiness Receipt must exist under docs/governance/"

    content = receipt_file.read_text(encoding="utf-8")

    assert "# SAGE BIG BUILD JUMP WAVE READINESS RECEIPT" in content
    assert "PHASE 1 & 2 — REPOSITORY TRUTH & EXISTING WORK RECONCILIATION" in content
    assert "PHASE 3 — GOOGLE / EXTERNAL INTEGRATION GAP HUNT" in content
    assert "PHASE 4 — ASSEMBLY LINE COMPLETION AUDIT" in content
    assert "PHASE 5 — SPORTS SCIENCE CAPABILITY TRANSITION" in content
    assert "PHASE 6 — TWO NEW HIGH-VALUE SAGE CAPABILITY THEMES" in content
    assert "Multi-Agent Epistemic Consensus & Dispute Resolution Engine" in content
    assert "Autonomous Context Drift & Memory Rehydration Sentinel" in content
    assert "PHASE 7 — FIVE-FLIGHT BIG JUMP WAVE LAUNCH PLAN" in content


def test_fleet_qualification_immersion_recon_report_exists_and_conforms():
    """Verify that FLEET_QUALIFICATION_IMMERSION_RECON_REPORT.md exists and contains required sections."""
    root_dir = Path(__file__).parent.parent
    recon_file = root_dir / "docs" / "governance" / "FLEET_QUALIFICATION_IMMERSION_RECON_REPORT.md"

    assert recon_file.exists(), "The Fleet Qualification Immersion Recon Report must exist under docs/governance/"

    content = recon_file.read_text(encoding="utf-8")

    assert "# FLEET QUALIFICATION & IMMERSION ARCHITECTURE RECONNAISSANCE REPORT" in content
    assert "Air Force Qualification Models" in content
    assert "Flight Simulator & Tactical Progression Systems" in content
    assert "RPG Skill Tree & Qualification Curves" in content
    assert "FLIGHT A — EXTERNAL RESEARCH & PATTERN RECON" in content
    assert "FLIGHT B — SAGE ASSET MAPPING" in content
    assert "FLIGHT C — CANDIDATE FLEET QUALIFICATION MODEL" in content
    assert "FLIGHT D — ADVERSARIAL FALSIFICATION & RISK ANALYSIS" in content
    assert "FLIGHT E — CAPABILITY WAREHOUSE DECISION" in content


def test_public_security_posture_files_exist_and_conform():
    """Verify that SECURITY.md, .github/CODEOWNERS, and .github/workflows/security.yml exist and conform."""
    root_dir = Path(__file__).parent.parent

    security_md = root_dir / "SECURITY.md"
    assert security_md.exists(), "SECURITY.md must exist in the root directory"
    sec_content = security_md.read_text(encoding="utf-8")
    assert "# SAGE Security Policy" in sec_content
    assert "Protected Core Namespaces" in sec_content
    assert "One-Way Import Law" in sec_content

    codeowners = root_dir / ".github" / "CODEOWNERS"
    assert codeowners.exists(), ".github/CODEOWNERS must exist"
    co_content = codeowners.read_text(encoding="utf-8")
    assert "@dariusbrandon880-art" in co_content
    assert "/docs/governance/" in co_content

    sec_workflow = root_dir / ".github" / "workflows" / "security.yml"
    assert sec_workflow.exists(), ".github/workflows/security.yml must exist"
    wf_content = sec_workflow.read_text(encoding="utf-8")
    assert "Secret & Dependency Vulnerability Audit" in wf_content
