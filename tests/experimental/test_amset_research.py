import os

def test_amset_research_spec_existence_and_structure():
    """
    Validates that the SAGE-AMSET Research Specification exists under the docs/
    directory and conforms to all required structural and conceptual layout rules.
    """
    spec_path = "docs/SAGE-AMSET-RESEARCH-SPECIFICATION.md"
    assert os.path.exists(spec_path), f"Expected research specification at {spec_path} but it was not found."

    with open(spec_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Core required headers and sections (case-insensitive checking for robustness)
    required_sections = [
        "# SAGE-AMSET Research Specification",
        "## 1. AMSET Research Objective",
        "## 2. Evaluation Taxonomy",
        "## 3. Evidence Model",
        "## 4. Validation Framework Concept",
        "## 5. Governance Alignment",
        "## 6. Repository Safety Review",
        "## 7. Reliability Verification"
    ]

    for section in required_sections:
        assert section.lower() in content.lower(), f"Expected section '{section}' was not found in SAGE-AMSET Research Specification."

    # Specific conceptual assertions within taxonomy (case-insensitive checking)
    required_taxonomies = [
        "Adversarial instruction conflicts",
        "Context consistency failures",
        "Identity or role confusion",
        "Boundary compliance failures",
        "Output reliability degradation",
        "Reasoning drift indicators"
    ]
    for taxonomy in required_taxonomies:
        assert taxonomy.lower() in content.lower(), f"Expected taxonomy concept '{taxonomy}' was not found in the specification."

    # Verify that telemetry is declared as evidence-only
    assert "telemetry is strictly limited to passive" in content.lower(), \
        "Specification must declare that telemetry is restricted to passive evidence collection."
    assert "telemetry does not:" in content.lower(), \
        "Specification must define what telemetry does not do."

    # Verify governance lifecycle and human final authority
    assert "research → validation → evidence → human review → demonstration → master archive" in content.lower() or \
           "1. research" in content.lower(), \
           "Specification must define the full governance loop."
    assert "human authority remains final" in content.lower() or "sovereign human review" in content.lower(), \
        "Specification must confirm absolute final human authority."

    # Verify protected boundaries are listed and verified
    protected_namespaces = ["sage/runtime/", "sage/core/", "sage/acr/", "sage/agents/"]
    for ns in protected_namespaces:
        assert ns in content, f"Protected namespace '{ns}' should be documented in the safety review section."
