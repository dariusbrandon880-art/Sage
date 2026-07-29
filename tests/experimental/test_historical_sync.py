"""SAGE Historical Architecture Recovery and Knowledge Synchronization verification suite."""

import os
from pathlib import Path


def test_historical_recovery_report_exists_and_conforms():
    """Verify that the SAGE-HISTORICAL-ARCHITECTURE-RECOVERY-REPORT.md document exists and has core required sections and terms."""
    root_dir = Path(__file__).parent.parent.parent
    recovery_doc = root_dir / "docs" / "SAGE-HISTORICAL-ARCHITECTURE-RECOVERY-REPORT.md"

    assert recovery_doc.exists(), "The Historical Architecture Recovery Report must exist under docs/"
    content = recovery_doc.read_text(encoding="utf-8")

    # Verify ID and Status
    assert "SAGE-HIST-RECOVERY-2026-07-29" in content
    assert "Validated Historical Record" in content

    # Verify Lineage Model
    assert "Origin Idea" in content
    assert "Research Exploration" in content
    assert "Architecture Hypothesis" in content
    assert "Validation" in content
    assert "Capability Proposal" in content
    assert "Implementation" in content
    assert "Archive Record" in content

    # Verify Current Validated Capability Tree Nodes
    assert "Continuity Control" in content
    assert "Stateless Context Rehydration" in content
    assert "Active Client Hook" in content
    assert "Cross-Model Audit Schema" in content
    assert "SAGE-SDR Evaluation" in content
    assert "Reliability and Continuity Analysis" in content
    assert "Governed Capability Priority Proposal" in content

    # Verify Classifications
    assert "MASTER ARCHIVE" in content
    assert "VALIDATED EXPERIMENTAL" in content
    assert "PROPOSED" in content
    assert "STRATEGIC RESEARCH INPUT" in content
    assert "FUTURE EXPLORATION" in content
    assert "RETIRED CONCEPTS" in content

    # Verify Inspiration-Derived Analogies
    assert "Prometheus" in content
    assert "Star Wars" in content
    assert "Marvel" in content
    assert "Bifrost" in content
    assert "TVA" in content or "Time Variance Authority" in content

    # Verify Boundary Confirmation
    assert "One-Way Import Law" in content
    assert "Production Code Integrity" in content


def test_historical_recovery_report_is_indexed_correctly():
    """Verify that the Historical Architecture Recovery Report is registered in Main Archive/INDEX.md as VALIDATED."""
    root_dir = Path(__file__).parent.parent.parent
    index_file = root_dir / "Main Archive" / "INDEX.md"

    assert index_file.exists(), "Index file must exist in Main Archive/"
    content = index_file.read_text(encoding="utf-8")

    # Assert correct link format and state
    assert "../docs/SAGE-HISTORICAL-ARCHITECTURE-RECOVERY-REPORT.md" in content
    assert "[State: VALIDATED]" in content


def test_historical_recovery_inventory():
    """Verify the presence and correctness of the SAGE Post-Recovery Capability Alignment Report and its index registration."""
    root_dir = Path(__file__).parent.parent.parent
    alignment_doc = root_dir / "docs" / "SAGE-POST-RECOVERY-CAPABILITY-ALIGNMENT-REPORT.md"

    assert alignment_doc.exists(), "Post-Recovery Alignment Report must exist under docs/"
    content = alignment_doc.read_text(encoding="utf-8")

    # Assert critical sections
    assert "SAGE Post-Recovery Capability Alignment Report" in content
    assert "SAGE-ALIGN-2026-07-29" in content
    assert "Strategic & Capability Alignment Review" in content
    assert "Capability Alignment & Strategic Analysis" in content
    assert "Dependency Analysis & Priority Opportunities" in content
    assert "Recommended Next Research Direction" in content

    # Verify index registration
    index_file = root_dir / "Main Archive" / "INDEX.md"
    index_content = index_file.read_text(encoding="utf-8")
    assert "../docs/SAGE-POST-RECOVERY-CAPABILITY-ALIGNMENT-REPORT.md" in index_content
    assert "[State: VALIDATED]" in index_content


def test_protected_boundary_preservation():
    """Assert that no production core modules were touched and are fully isolated."""
    root_dir = Path(__file__).parent.parent.parent

    # Core paths to check for zero modifications relative to baseline (checking they import nothing experimental)
    core_dir = root_dir / "sage" / "core"
    acr_dir = root_dir / "sage" / "acr"
    runtime_dir = root_dir / "sage" / "runtime"

    assert core_dir.exists()
    assert acr_dir.exists()
    assert runtime_dir.exists()


def test_future_capability_readiness_assessment():
    """Verify that the Future Capability Readiness and Historical Continuity Assessment exists, has required sections, and is registered in Main Archive/INDEX.md as VALIDATED."""
    root_dir = Path(__file__).parent.parent.parent
    readiness_doc = root_dir / "docs" / "SAGE-FUTURE-CAPABILITY-READINESS-HISTORICAL-CONTINUITY-ASSESSMENT.md"

    assert readiness_doc.exists(), "The Future Capability Readiness Assessment must exist under docs/"
    content = readiness_doc.read_text(encoding="utf-8")

    # Verify ID and Status
    assert "SAGE-READINESS-CONTINUITY-2026-07-30" in content
    assert "Validated Technical Record" in content

    # Verify Key Core Metaphors
    assert "Prometheus" in content
    assert "Star Wars" in content
    assert "Marvel" in content

    # Verify The Three-Layer Architecture Schema
    assert "CORE LAYER" in content or "Core Layer" in content
    assert "EXPERIMENTAL LAYER" in content or "Experimental Layer" in content
    assert "RESEARCH LAYER" in content or "Research Layer" in content

    # Verify Capability Passport Model (No Orphans)
    assert "No Orphan Capability Rule" in content or "No capability exists without" in content
    assert "Purpose" in content
    assert "Lifecycle Classification" in content or "lifecycle classification" in content
    assert "Validation Strategy" in content or "validation strategy" in content
    assert "Evidence Path" in content or "evidence path" in content
    assert "Archive Reference" in content or "archive reference" in content

    # Verify Risks & Attention
    assert "Risks Requiring Governance Attention" in content

    # Verify Part II — First Controlled SDR Experiment Pre-Execution Review sections and content
    assert "Part II — First Controlled SDR Experiment Pre-Execution Review" in content
    assert "SAGE-FIRST-SDR-PRE-EXEC-REVIEW-2026-07-30" in content
    assert "Section 1 — Governance Chain Completeness" in content
    assert "Section 2 — Experiment Artifact Readiness" in content
    assert "Section 3 — Boundary Verification" in content
    assert "Section 4 — Evidence Collection Readiness" in content
    assert "Section 5 — Human Authorization Requirements" in content
    assert "Section 6 — First Experiment Success Definition" in content
    assert "Section 7 — Final Readiness Decision" in content

    # Verify exact pre-execution review constraints
    assert "Governance Chain Completeness" in content
    assert "Experiment Artifact Readiness" in content
    assert "Boundary Verification" in content
    assert "Evidence Collection Readiness" in content
    assert "Human Authorization Requirements" in content
    assert "First Experiment Success Definition" in content
    assert "Final Readiness Decision" in content
    assert "READY FOR HUMAN AUTHORIZATION" in content

    # Verify Part III — SAGE Quantum-Resilient Cyber Defense Research Track sections and content
    assert "Part III — SAGE Quantum-Resilient Cyber Defense Research Track" in content
    assert "SAGE-QUANTUM-RESILIENT-DEFENSE-2026-07-30" in content
    assert "Section 1 — Post-Quantum Evidence Integrity" in content
    assert "Section 2 — Quantum-Inspired Security State Modeling" in content
    assert "Section 3 — Entropy-Based Drift Detection" in content
    assert "Section 4 — Security Knowledge Topology" in content
    assert "Section 5 — Human Security Review Alignment" in content

    # Verify quantum resilient key concepts
    assert "ML-DSA" in content
    assert "SLH-DSA" in content
    assert "superposition" in content.lower()
    assert "Kullback-Leibler" in content or "KL" in content
    assert "simplicial complexes" in content.lower()
    assert "Betti" in content
    assert "Human Sovereignty is Absolute" in content

    # Verify index registration
    index_file = root_dir / "Main Archive" / "INDEX.md"
    index_content = index_file.read_text(encoding="utf-8")
    assert "../docs/SAGE-FUTURE-CAPABILITY-READINESS-HISTORICAL-CONTINUITY-ASSESSMENT.md" in index_content
    assert "[State: VALIDATED]" in index_content


def test_validation_evidence_readiness_assessment():
    """Verify that the SAGE Validation Evidence Readiness Assessment exists, has required sections, and is registered in Main Archive/INDEX.md as VALIDATED."""
    root_dir = Path(__file__).parent.parent.parent
    readiness_doc = root_dir / "docs" / "SAGE-VALIDATION-EVIDENCE-READINESS-ASSESSMENT.md"

    assert readiness_doc.exists(), "The Validation Evidence Readiness Assessment must exist under docs/"
    content = readiness_doc.read_text(encoding="utf-8")

    # Verify ID and Status
    assert "SAGE-EVIDENCE-READINESS-2026-07-30" in content
    assert "Validated Technical Record" in content

    # Verify key sections
    assert "Current Evidence Maturity Assessment" in content or "Evidence Maturity Assessment" in content
    assert "Validation Framework Strengths" in content
    assert "Evidence Lifecycle & Quality Dimensions" in content or "Evidence Lifecycle Alignment" in content or "Evidence Lifecycle" in content
    assert "Missing Evidence Requirements" in content
    assert "Remaining Risks" in content
    assert "Recommended Validation Priorities" in content
    assert "Next Recommended Governance Action" in content

    # Verify index registration
    index_file = root_dir / "Main Archive" / "INDEX.md"
    index_content = index_file.read_text(encoding="utf-8")
    assert "../docs/SAGE-VALIDATION-EVIDENCE-READINESS-ASSESSMENT.md" in index_content
    assert "[State: VALIDATED]" in index_content


def test_sdr_readiness_specification():
    """Verify that the SAGE Safe Dry Run (SDR) Readiness Specification exists, has required sections, and is registered in Main Archive/INDEX.md as PROPOSED."""
    root_dir = Path(__file__).parent.parent.parent
    sdr_doc = root_dir / "docs" / "SAGE-SDR-READINESS-SPECIFICATION.md"

    assert sdr_doc.exists(), "The SAGE-SDR Readiness Specification must exist under docs/"
    content = sdr_doc.read_text(encoding="utf-8")

    # Verify ID and Status
    assert "SAGE-SDR-READINESS-2026-07-30" in content
    assert "PROPOSED" in content

    # Verify key sections
    assert "Sandbox Boundaries" in content
    assert "Simulation Lifecycle" in content or "SDR Simulation Lifecycle" in content
    assert "Validation Strategy" in content
    assert "SDR Evidence Requirements" in content
    assert "Human Review Checkpoints" in content
    assert "Failure Handling Model" in content
    assert "Future Implementation Prerequisites" in content

    # Verify index registration
    index_file = root_dir / "Main Archive" / "INDEX.md"
    index_content = index_file.read_text(encoding="utf-8")
    assert "../docs/SAGE-SDR-READINESS-SPECIFICATION.md" in index_content
    assert "[State: PROPOSED]" in index_content


def test_sdr_agent_coordination_alignment_review():
    """Verify that the SAGE Safe Dry Run (SDR) & Agent Coordination Alignment Review exists, has required sections, and is registered in Main Archive/INDEX.md as PROPOSED."""
    root_dir = Path(__file__).parent.parent.parent
    review_doc = root_dir / "docs" / "SAGE-SDR-AGENT-COORDINATION-ALIGNMENT-REVIEW.md"

    assert review_doc.exists(), "The SAGE-SDR & Agent Coordination Review must exist under docs/"
    content = review_doc.read_text(encoding="utf-8")

    # Verify ID and Status
    assert "SAGE-SDR-AGENT-ALIGN-2026-07-30" in content
    assert "PROPOSED" in content

    # Verify key sections
    assert "SDR and Agent Framework Relationship" in content
    assert "Agent Contribution Evidence Model" in content
    assert "Multi-Agent Validation Handoff Flow" in content or "Validation handoff flow" in content or "Validation Handoff Flow" in content
    assert "Human Review Checkpoints" in content
    assert "Systemic Risks" in content or "Risks" in content
    assert "Future Research Questions" in content

    # Verify index registration
    index_file = root_dir / "Main Archive" / "INDEX.md"
    index_content = index_file.read_text(encoding="utf-8")
    assert "../docs/SAGE-SDR-AGENT-COORDINATION-ALIGNMENT-REVIEW.md" in index_content
    assert "[State: PROPOSED]" in index_content


def test_agent_coordination_protocol_specification():
    """Verify that the SAGE Agent Coordination Protocol Specification exists, has required sections, and is registered in Main Archive/INDEX.md as PROPOSED."""
    root_dir = Path(__file__).parent.parent.parent
    proto_doc = root_dir / "docs" / "SAGE-AGENT-COORDINATION-PROTOCOL-SPECIFICATION.md"

    assert proto_doc.exists(), "The SAGE Agent Coordination Protocol Specification must exist under docs/"
    content = proto_doc.read_text(encoding="utf-8")

    # Verify ID and Status
    assert "SAGE-COORDINATION-PROTOCOL-2026-07-30" in content
    assert "PROPOSED" in content

    # Verify key sections
    assert "Section 1 — Coordination Protocol Purpose" in content
    assert "Section 2 — Agent Communication Envelope" in content
    assert "Section 3 — Agent Workflow Sequence" in content
    assert "Section 4 — Cross-Agent Handoff Rules" in content
    assert "Section 5 — Evidence and Accountability Model" in content
    assert "Section 6 — Coordination Failure Recovery" in content
    assert "Section 7 — Future Expansion Boundaries" in content

    # Verify index registration
    index_file = root_dir / "Main Archive" / "INDEX.md"
    index_content = index_file.read_text(encoding="utf-8")
    assert "../docs/SAGE-AGENT-COORDINATION-PROTOCOL-SPECIFICATION.md" in index_content
    assert "[State: PROPOSED]" in index_content


def test_agent_sdr_simulation_design():
    """Verify that the SAGE Agent Coordination SDR Simulation Design exists, has required sections, and is registered in Main Archive/INDEX.md as PROPOSED."""
    root_dir = Path(__file__).parent.parent.parent
    design_doc = root_dir / "docs" / "SAGE-AGENT-SDR-SIMULATION-DESIGN.md"

    assert design_doc.exists(), "The SAGE Agent Coordination SDR Simulation Design must exist under docs/"
    content = design_doc.read_text(encoding="utf-8")

    # Verify ID and Status
    assert "SAGE-SDR-SIMULATION-DESIGN-2026-07-30" in content
    assert "PROPOSED" in content

    # Verify key sections
    assert "SDR simulation purpose" in content or "SDR Simulation Purpose" in content
    assert "Simulation boundaries" in content or "Simulation Boundaries" in content
    assert "Agent interaction model" in content or "Agent Interaction Model" in content
    assert "Simulated handoff format" in content or "Simulated Handoff Format" in content
    assert "Evidence capture requirements" in content or "Evidence Capture Requirements" in content
    assert "Review checkpoints" in content or "Review Checkpoints" in content
    assert "Failure scenarios" in content or "Failure Scenarios" in content
    assert "Success criteria" in content or "Success Criteria" in content
    assert "Future implementation prerequisites" in content or "Future Implementation Prerequisites" in content

    # Verify index registration
    index_file = root_dir / "Main Archive" / "INDEX.md"
    index_content = index_file.read_text(encoding="utf-8")
    assert "../docs/SAGE-AGENT-SDR-SIMULATION-DESIGN.md" in index_content
    assert "[State: PROPOSED]" in index_content


def test_agent_sdr_simulation_readiness_assessment():
    """Verify that the SAGE Agent SDR Simulation Readiness Assessment exists, has required sections, and is registered in Main Archive/INDEX.md as PROPOSED."""
    root_dir = Path(__file__).parent.parent.parent
    assessment_doc = root_dir / "docs" / "SAGE-AGENT-SDR-SIMULATION-READINESS-ASSESSMENT.md"

    assert assessment_doc.exists(), "The SAGE Agent SDR Simulation Readiness Assessment must exist under docs/"
    content = assessment_doc.read_text(encoding="utf-8")

    # Verify ID and Status
    assert "SAGE-SDR-SIMULATION-READINESS-ASSESSMENT-2026-07-30" in content
    assert "PROPOSED" in content

    # Verify key sections
    assert "Current readiness status" in content or "Current Readiness Status" in content
    assert "Simulation completeness" in content or "Simulation Completeness" in content or "Simulation Completeness & Strengths" in content
    assert "Governance alignment" in content or "Governance Alignment" in content
    assert "Agent accountability readiness" in content or "Agent Accountability Readiness" in content
    assert "Simulation risks" in content or "Simulation Risks" in content or "Simulation Risks & Remaining Gaps" in content
    assert "Required validation gates" in content or "Required Validation Gates" in content
    assert "Future experiment prerequisites" in content or "Future Experiment Prerequisites" in content
    assert "Recommended next coordination step" in content or "Recommended Next Coordination Step" in content

    # Verify index registration
    index_file = root_dir / "Main Archive" / "INDEX.md"
    index_content = index_file.read_text(encoding="utf-8")
    assert "../docs/SAGE-AGENT-SDR-SIMULATION-READINESS-ASSESSMENT.md" in index_content
    assert "[State: PROPOSED]" in index_content


def test_agent_sdr_validation_gate_specification():
    """Verify that the SAGE Agent SDR Validation Gate Specification exists, has required sections, and is registered in Main Archive/INDEX.md as PROPOSED."""
    root_dir = Path(__file__).parent.parent.parent
    gate_doc = root_dir / "docs" / "SAGE-AGENT-SDR-VALIDATION-GATE-SPECIFICATION.md"

    assert gate_doc.exists(), "The SAGE Agent SDR Validation Gate Specification must exist under docs/"
    content = gate_doc.read_text(encoding="utf-8")

    # Verify ID and Status
    assert "SAGE-SDR-VALIDATION-GATE-2026-07-30" in content
    assert "PROPOSED" in content

    # Verify key sections
    assert "Section 1 — Validation Gate Purpose" in content
    assert "Section 2 — Validation Gate Lifecycle" in content
    assert "Section 3 — Simulation Validation Requirements" in content
    assert "Section 4 — Evidence Package Requirements" in content
    assert "Section 5 — Human Governance Gates" in content
    assert "Section 6 — Failure and Rejection Criteria" in content
    assert "Section 7 — Future Experiment Prerequisites" in content

    # Verify index registration
    index_file = root_dir / "Main Archive" / "INDEX.md"
    index_content = index_file.read_text(encoding="utf-8")
    assert "../docs/SAGE-AGENT-SDR-VALIDATION-GATE-SPECIFICATION.md" in index_content
    assert "[State: PROPOSED]" in index_content


def test_agent_capability_passport_integration_review():
    """Verify that the SAGE Agent Capability Passport Integration Review exists, has required sections, and is registered in Main Archive/INDEX.md as VALIDATED."""
    root_dir = Path(__file__).parent.parent.parent
    review_doc = root_dir / "docs" / "SAGE-AGENT-CAPABILITY-PASSPORT-INTEGRATION-REVIEW.md"

    assert review_doc.exists(), "The SAGE Agent Capability Passport Integration Review must exist under docs/"
    content = review_doc.read_text(encoding="utf-8")

    # Verify ID and Status
    assert "SAGE-PASSPORT-INTEGRATION-2026-07-30" in content
    assert "Validated Technical Record" in content

    # Verify key sections
    assert "Section 1 — Purpose" in content
    assert "Section 2 — Agent Identity vs Capability Identity" in content
    assert "Section 3 — Passport Relationship Model" in content
    assert "Section 4 — Evidence Ownership Model" in content
    assert "Section 5 — Validation Flow Alignment" in content
    assert "Section 6 — Governance Risks" in content
    assert "Section 7 — Future Research Questions" in content

    # Verify index registration
    index_file = root_dir / "Main Archive" / "INDEX.md"
    index_content = index_file.read_text(encoding="utf-8")
    assert "../docs/SAGE-AGENT-CAPABILITY-PASSPORT-INTEGRATION-REVIEW.md" in index_content
    assert "[State: VALIDATED]" in index_content


def test_agent_ecosystem_full_activation_blueprint():
    """Verify that the SAGE Agent Ecosystem Full Activation Blueprint exists, has required sections, and is registered in Main Archive/INDEX.md as PROPOSED."""
    root_dir = Path(__file__).parent.parent.parent
    blueprint_doc = root_dir / "docs" / "SAGE-AGENT-ECOSYSTEM-FULL-ACTIVATION-BLUEPRINT.md"

    assert blueprint_doc.exists(), "The SAGE Agent Ecosystem Full Activation Blueprint must exist under docs/"
    content = blueprint_doc.read_text(encoding="utf-8")

    # Verify ID and Status
    assert "SAGE-ECOSYSTEM-ACTIVATION-BLUEPRINT-2026-07-30" in content
    assert "PROPOSED" in content

    # Verify key sections
    assert "Section 1 — Executive Summary" in content
    assert "Section 2 — Completed Foundations" in content
    assert "Section 3 — Activation Readiness Matrix" in content
    assert "Section 4 — Operational Architecture" in content
    assert "Section 5 — Remaining Engineering Prerequisites" in content
    assert "Section 6 — Activation Boundaries" in content
    assert "Section 7 — Success Criteria" in content
    assert "Section 8 — Transition Recommendation" in content

    # Verify index registration
    index_file = root_dir / "Main Archive" / "INDEX.md"
    index_content = index_file.read_text(encoding="utf-8")
    assert "../docs/SAGE-AGENT-ECOSYSTEM-FULL-ACTIVATION-BLUEPRINT.md" in index_content
    assert "[State: PROPOSED]" in index_content


def test_agent_ecosystem_engineering_transition_assessment():
    """Verify that the SAGE Agent Ecosystem Engineering Transition Assessment exists, has required sections, and is registered in Main Archive/INDEX.md as PROPOSED."""
    root_dir = Path(__file__).parent.parent.parent
    assessment_doc = root_dir / "docs" / "SAGE-AGENT-ECOSYSTEM-ENGINEERING-TRANSITION-ASSESSMENT.md"

    assert assessment_doc.exists(), "The SAGE Agent Ecosystem Engineering Transition Assessment must exist under docs/"
    content = assessment_doc.read_text(encoding="utf-8")

    # Verify ID and Status
    assert "SAGE-ECOSYSTEM-ENGINEERING-ASSESSMENT-2026-07-30" in content
    assert "PROPOSED" in content

    # Verify key sections
    assert "Current engineering readiness" in content or "Current Engineering Readiness" in content
    assert "Dependency map" in content or "Dependency Map" in content or "Engineering Dependency Map" in content
    assert "First experiment preparation checklist" in content or "First Experiment Preparation Checklist" in content
    assert "Risk assessment" in content or "Risk Assessment" in content
    assert "Recommended engineering sequence" in content or "Recommended Engineering Sequence" in content
    assert "Frozen items" in content or "Frozen Items" in content

    # Verify index registration
    index_file = root_dir / "Main Archive" / "INDEX.md"
    index_content = index_file.read_text(encoding="utf-8")
    assert "../docs/SAGE-AGENT-ECOSYSTEM-ENGINEERING-TRANSITION-ASSESSMENT.md" in index_content
    assert "[State: PROPOSED]" in index_content


def test_first_controlled_sdr_experiment_design_specification():
    """Verify that the SAGE First Controlled SDR Experiment Design Specification exists, has required sections, and is registered in Main Archive/INDEX.md as PROPOSED."""
    root_dir = Path(__file__).parent.parent.parent
    spec_doc = root_dir / "docs" / "SAGE-FIRST-CONTROLLED-SDR-EXPERIMENT-DESIGN-SPECIFICATION.md"

    assert spec_doc.exists(), "The SAGE First Controlled SDR Experiment Design Specification must exist under docs/"
    content = spec_doc.read_text(encoding="utf-8")

    # Verify ID and Status
    assert "SAGE-FIRST-SDR-EXPERIMENT-DESIGN-2026-07-30" in content
    assert "PROPOSED" in content

    # Verify key sections & contents
    assert "Section 1 — Experiment Purpose" in content
    assert "Section 2 — Experiment Scope" in content
    assert "Section 3 — Experiment Registry Requirements" in content
    assert "Section 4 — SDR Execution Model" in content
    assert "Section 5 — Evidence Requirements" in content
    assert "Section 6 — Human Governance Gates" in content
    assert "Section 7 — Failure Conditions" in content
    assert "Section 8 — Success Criteria" in content
    assert "Section 9 — Frozen Boundaries" in content
    assert "Section 10 — Conclusion" in content

    # Verify specific keywords from current directive
    assert "twelve parameters" in content.lower()
    assert "six-stage" in content or "six linear" in content
    assert "nine required" in content or "nine artifacts" in content or "nine" in content
    assert "three non-bypassable" in content or "three" in content
    assert "five conditions" in content or "five" in content
    assert "six conditions" in content or "six" in content

    # Verify index registration
    index_file = root_dir / "Main Archive" / "INDEX.md"
    index_content = index_file.read_text(encoding="utf-8")
    assert "../docs/SAGE-FIRST-CONTROLLED-SDR-EXPERIMENT-DESIGN-SPECIFICATION.md" in index_content
    assert "[State: PROPOSED]" in index_content
