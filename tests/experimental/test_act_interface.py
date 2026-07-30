"""SAGE-ACT Milestone 1 Interface validation and Import isolation test suite."""

import pytest
import os
import ast
from pathlib import Path

from sage.experimental.act import SessionTaskTreeLinker, TaskDecisionBinder


def test_session_task_tree_linker_valid():
    """Verify standard valid linkage mapping."""
    linker = SessionTaskTreeLinker()
    result = linker.link_session_to_tasks(
        session_id="session_f6b3d4e5",
        task_ids=["task_001_deploy", "task_002_test"],
    )

    assert result["session_id"] == "session_f6b3d4e5"
    assert len(result["mapped_tasks"]) == 2
    assert "task_001_deploy" in result["mapped_tasks"]
    assert result["validation_status"] == "INTERFACE_VERIFIED"
    assert result["read_only_assertion"] is True
    assert "linked_at" in result


def test_session_task_tree_linker_invalid_session_id():
    """Verify that an invalid session_id format is rejected."""
    linker = SessionTaskTreeLinker()
    with pytest.raises(ValueError, match="Invalid session_id format"):
        linker.link_session_to_tasks(
            session_id="sess_f6b3d4e5",  # Invalid prefix (must be session_)
            task_ids=["task_001"],
        )


def test_session_task_tree_linker_invalid_task_id():
    """Verify that an invalid task_id format is rejected."""
    linker = SessionTaskTreeLinker()
    with pytest.raises(ValueError, match="Invalid task_id format"):
        linker.link_session_to_tasks(
            session_id="session_f6b3d4e5",
            task_ids=["task_001", "deploy_task_002"],  # Invalid prefix
        )


def test_task_decision_binder_valid():
    """Verify standard valid decision binding mapping."""
    binder = TaskDecisionBinder()
    result = binder.bind_task_to_decisions(
        task_id="task_2026_spek",
        decision_ids=["decision_001_approve", "proposal_002_auth"],
    )

    assert result["task_id"] == "task_2026_spek"
    assert len(result["bound_decisions"]) == 2
    assert "proposal_002_auth" in result["bound_decisions"]
    assert result["validation_status"] == "INTERFACE_VERIFIED"
    assert result["read_only_assertion"] is True
    assert "bound_at" in result


def test_task_decision_binder_invalid_task_id():
    """Verify that an invalid task_id format is rejected by the binder."""
    binder = TaskDecisionBinder()
    with pytest.raises(ValueError, match="Invalid task_id format"):
        binder.bind_task_to_decisions(
            task_id="t_2026",  # Invalid prefix
            decision_ids=["decision_001"],
        )


def test_task_decision_binder_invalid_decision_id():
    """Verify that an invalid decision_id format is rejected by the binder."""
    binder = TaskDecisionBinder()
    with pytest.raises(ValueError, match="Invalid decision/proposal ID format"):
        binder.bind_task_to_decisions(
            task_id="task_2026",
            decision_ids=["decision_001", "approved_dec_002"],  # Invalid prefix
        )


def test_one_way_import_isolation_enforcement():
    """Verify absolute enforcement of the One-Way Import Law.

    No module in the frozen production/core namespace ('sage/acr/', 'sage/core/', etc.)
    is allowed to import from 'sage.experimental' or 'sage.experimental.act'.
    """
    root_path = Path(__file__).parent.parent.parent / "sage"
    assert root_path.exists(), f"Could not find SAGE source path at: {root_path}"

    for file_path in root_path.glob("**/*.py"):
        # Exclude files inside sage/experimental
        if "experimental" in file_path.parts:
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            try:
                tree = ast.parse(f.read(), filename=str(file_path))
            except SyntaxError as e:
                pytest.fail(f"Syntax error while parsing {file_path}: {e}")

            for node in ast.walk(tree):
                # Check direct imports (e.g., 'import sage.experimental')
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert "sage.experimental" not in alias.name, (
                            f"One-Way Import Law Violation inside production: '{file_path}' "
                            f"attempts to directly import '{alias.name}'"
                        )
                # Check from imports (e.g., 'from sage.experimental.act import SessionTaskTreeLinker')
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        assert "sage.experimental" not in node.module, (
                            f"One-Way Import Law Violation inside production: '{file_path}' "
                            f"attempts to import from module '{node.module}'"
                        )


def test_smallest_sandbox_validation_event():
    """Verify the smallest possible sandbox validation event and governance lifecycle."""
    from sage.experimental.act import (
        CapabilityPassportValidator,
        CapabilityEvidenceReceiptGenerator,
        HumanReviewGate,
    )

    # 1. Define one agent identity, one restricted capability, controlled input, expected output
    passport = {
        "capability_id": "CAP-SCR-003",
        "name": "Stateless Context Rehydration",
        "purpose": "Verify chronological execution sequences from client-held checkpoints.",
        "lifecycle_state": "PROPOSED",
        "validation_strategy": "Linter Invariant Checking",
        "evidence_path": "docs/SAGE-ACT-MILESTONE-3-EVIDENCE.md",
        "dependencies": [],
        "human_signoff": "SUPERVISOR-SAGE-001",
    }

    # Validate Passport
    passport_validator = CapabilityPassportValidator()
    passport_result = passport_validator.validate_passport(passport)
    assert passport_result["capability_id"] == "CAP-SCR-003"
    assert passport_result["validation_status"] == "PASSPORT_VALIDATED"

    # 2. Simulate validation result input and generate secure evidence receipt
    receipt_input = {
        "receipt_id": "REC-SDR-ERR-001",
        "capability_id": "CAP-SCR-003",
        "validation_result": "PASSED",  # Or FAILED depending on check
        "evidence_reference": "sha256(Inputs) = a89f3c7e",
        "timestamp": "2026-07-30T12:00:00Z",
        "review_status": "PENDING_MANUAL_AUDIT",
        "archive_destination": "Main Archive/INDEX.md",
    }
    receipt_generator = CapabilityEvidenceReceiptGenerator()
    receipt = receipt_generator.generate_receipt(receipt_input)

    assert receipt["receipt_id"] == "REC-SDR-ERR-001"
    assert receipt["validator_id"] == "VAL-SDR-001"
    assert receipt["validation_result"] == "PASSED"

    # 3. human review gate PASS criteria
    review_gate = HumanReviewGate()
    review_result_pass = review_gate.process_review(receipt, "Complete, non-repudiable logs verified. Conformant to CMAPS.")

    assert review_result_pass["review_id"] == "REV-001"
    assert review_result_pass["review_decision"] == "APPROVED_BY_GOVERNANCE"
    assert review_result_pass["validation_status"] == "VALIDATED"

    # 4. human review gate FAIL criteria
    review_result_fail = review_gate.process_review(receipt, "FAIL: chronological trace mismatch detected in trace.")
    assert review_result_fail["review_decision"] == "REJECTED_BY_GOVERNANCE"
    assert review_result_fail["validation_status"] == "PROPOSED"


def test_agent_envelope_validation_success():
    """Verify that a valid experimental agent handoff envelope passes validation successfully."""
    from sage.experimental.agents import (
        AgentCommunicationEnvelope,
        ExperimentalAgentRegistry,
        EnvelopeValidator,
    )

    registry = ExperimentalAgentRegistry()
    validator = EnvelopeValidator(registry)

    # Valid handoff between chatgpt-coordinator and jules-engineer
    envelope = AgentCommunicationEnvelope(
        mission_id="MSN-2026-001",
        sender_identity="chatgpt-coordinator",
        receiver_identity="jules-engineer",
        task_objective="Draft session receipt spec inside sandbox",
        authorized_capability="CAP-ACT-001",
        constraints=["Sandbox directories only", "No production imports"],
        expected_artifact="docs/sandbox/SAGE-CRC-SPEC.md",
        evidence_reference="sha256(Inputs) = a89f3c7e",
        review_status="PENDING_MANUAL_AUDIT",
    )

    result = validator.validate_envelope(envelope)
    assert result["mission_id"] == "MSN-2026-001"
    assert result["validation_status"] == "ENVELOPE_VALIDATED"
    assert result["read_only_assertion"] is True
    assert "validated_at" in result


def test_agent_envelope_validation_invalid_identity():
    """Verify that an invalid sender or receiver identity is rejected."""
    from sage.experimental.agents import (
        AgentCommunicationEnvelope,
        ExperimentalAgentRegistry,
        EnvelopeValidator,
    )

    registry = ExperimentalAgentRegistry()
    validator = EnvelopeValidator(registry)

    # Invalid sender (rogue-agent is not registered)
    envelope_bad_sender = AgentCommunicationEnvelope(
        mission_id="MSN-2026-001",
        sender_identity="rogue-agent",
        receiver_identity="jules-engineer",
        task_objective="Draft spec",
        authorized_capability="CAP-ACT-001",
        constraints=[],
        expected_artifact="docs/sandbox/spec.md",
        evidence_reference="sha256(Inputs) = a89f3c7e",
        review_status="PENDING_MANUAL_AUDIT",
    )

    with pytest.raises(ValueError, match="Sender identity 'rogue-agent' is not registered"):
        validator.validate_envelope(envelope_bad_sender)

    # Invalid receiver (rogue-receiver is not registered)
    envelope_bad_receiver = AgentCommunicationEnvelope(
        mission_id="MSN-2026-001",
        sender_identity="chatgpt-coordinator",
        receiver_identity="rogue-receiver",
        task_objective="Draft spec",
        authorized_capability="CAP-ACT-001",
        constraints=[],
        expected_artifact="docs/sandbox/spec.md",
        evidence_reference="sha256(Inputs) = a89f3c7e",
        review_status="PENDING_MANUAL_AUDIT",
    )

    with pytest.raises(ValueError, match="Receiver identity 'rogue-receiver' is not registered"):
        validator.validate_envelope(envelope_bad_receiver)


def test_agent_envelope_validation_invalid_capability():
    """Verify that an unauthorized capability for the sender is rejected."""
    from sage.experimental.agents import (
        AgentCommunicationEnvelope,
        ExperimentalAgentRegistry,
        EnvelopeValidator,
    )

    registry = ExperimentalAgentRegistry()
    validator = EnvelopeValidator(registry)

    # chatgpt-coordinator is authorized only for CAP-ACT-001, attempting CAP-SCR-003
    envelope_bad_cap = AgentCommunicationEnvelope(
        mission_id="MSN-2026-001",
        sender_identity="chatgpt-coordinator",
        receiver_identity="jules-engineer",
        task_objective="Draft spec",
        authorized_capability="CAP-SCR-003",
        constraints=[],
        expected_artifact="docs/sandbox/spec.md",
        evidence_reference="sha256(Inputs) = a89f3c7e",
        review_status="PENDING_MANUAL_AUDIT",
    )

    with pytest.raises(ValueError, match="Capability 'CAP-SCR-003' is not authorized for sender 'chatgpt-coordinator'"):
        validator.validate_envelope(envelope_bad_cap)


def test_agent_envelope_validation_protected_path_rejection():
    """Verify that a request accessing protected directories is rejected."""
    from sage.experimental.agents import (
        AgentCommunicationEnvelope,
        ExperimentalAgentRegistry,
        EnvelopeValidator,
    )

    registry = ExperimentalAgentRegistry()
    validator = EnvelopeValidator(registry)

    # Attempting to write output artifact directly into protected sage/runtime/
    envelope_bad_path = AgentCommunicationEnvelope(
        mission_id="MSN-2026-001",
        sender_identity="chatgpt-coordinator",
        receiver_identity="jules-engineer",
        task_objective="Attempting injection",
        authorized_capability="CAP-ACT-001",
        constraints=[],
        expected_artifact="sage/runtime/malicious.py",
        evidence_reference="sha256(Inputs) = a89f3c7e",
        review_status="PENDING_MANUAL_AUDIT",
    )

    with pytest.raises(ValueError, match="Protected path access attempt detected: 'sage/runtime/malicious.py'"):
        validator.validate_envelope(envelope_bad_path)

    # Attempting to place protected sage/core/ in constraints
    envelope_bad_constraint = AgentCommunicationEnvelope(
        mission_id="MSN-2026-001",
        sender_identity="chatgpt-coordinator",
        receiver_identity="jules-engineer",
        task_objective="Attempting injection",
        authorized_capability="CAP-ACT-001",
        constraints=["Write to sage/core/engine.py allowed"],
        expected_artifact="docs/sandbox/safe.md",
        evidence_reference="sha256(Inputs) = a89f3c7e",
        review_status="PENDING_MANUAL_AUDIT",
    )

    with pytest.raises(ValueError, match="Protected path access attempt detected: 'Write to sage/core/engine.py allowed'"):
        validator.validate_envelope(envelope_bad_constraint)


def test_agent_envelope_validation_missing_evidence():
    """Verify that an envelope with a missing or empty evidence reference is rejected."""
    from sage.experimental.agents import (
        AgentCommunicationEnvelope,
        ExperimentalAgentRegistry,
        EnvelopeValidator,
    )

    registry = ExperimentalAgentRegistry()
    validator = EnvelopeValidator(registry)

    # Missing evidence reference (empty string)
    envelope_no_evidence = AgentCommunicationEnvelope(
        mission_id="MSN-2026-001",
        sender_identity="chatgpt-coordinator",
        receiver_identity="jules-engineer",
        task_objective="Draft spec",
        authorized_capability="CAP-ACT-001",
        constraints=[],
        expected_artifact="docs/sandbox/spec.md",
        evidence_reference="  ",  # empty/whitespace
        review_status="PENDING_MANUAL_AUDIT",
    )

    with pytest.raises(ValueError, match="Evidence reference is required and cannot be empty"):
        validator.validate_envelope(envelope_no_evidence)
