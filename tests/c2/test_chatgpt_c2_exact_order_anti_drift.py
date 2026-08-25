import json
import hashlib
from types import SimpleNamespace

import pytest

from sage.c2.chatgpt_c2_contract import (
    ANTI_DRIFT_LAWS,
    CONTRACT_ID,
    CONTRACT_VERSION,
    LiveOperationReceipt,
    classify_directive,
    render_system_contract,
    validate_report_claims,
)
from sage.runtime.model_adapters import OpenAIResponsesAdapter, _system_instructions
from sage.runtime.model_gateway import SAGEProtocolGovernor, SAGERuntime, SAGEStateSnapshot


def state() -> SAGEStateSnapshot:
    return SAGEStateSnapshot(
        state_version="1",
        instance_id="sage-instance",
        mission_id="mission-1",
        session_id="session-1",
        authority_scope="authorized-frontier",
        active_frontier="c2",
        stop_boundary="independent-verification",
    )


def test_contract_contains_all_ten_laws_and_identity():
    rendered = render_system_contract()
    assert CONTRACT_ID in rendered
    assert CONTRACT_VERSION in rendered
    assert len(ANTI_DRIFT_LAWS) == 10
    for law in ANTI_DRIFT_LAWS:
        assert law in rendered


def test_live_check_directive_requires_live_verification():
    decision = classify_directive("Check live repo and inspect PR")
    assert decision.requires_live_verification is True
    assert "check live repo" in decision.matched_triggers
    assert "inspect pr" in decision.matched_triggers


def test_normal_directive_does_not_force_live_check():
    decision = classify_directive("Design five future research frontiers")
    assert decision.requires_live_verification is False


def test_missing_receipt_fails_closed():
    with pytest.raises(ValueError, match="lacks an authoritative LiveOperationReceipt"):
        validate_report_claims(claim="Verified live repository state", operation_receipt=None)


def test_failed_operation_receipt_fails_closed():
    ts = 1000.0
    op_type = "live_check"
    target = "repo"
    success = False
    h = hashlib.sha256(f"{op_type}:{target}:{success}:{ts}".encode()).hexdigest()
    failed_receipt = LiveOperationReceipt(
        operation_type=op_type, target=target, success=success, timestamp=ts, receipt_hash=h
    )

    with pytest.raises(ValueError, match="operation receipt indicates operation failure"):
        validate_report_claims(claim="Verified live repository state", operation_receipt=failed_receipt)


def test_tampered_hash_receipt_fails_closed():
    tampered_receipt = LiveOperationReceipt(
        operation_type="live_check",
        target="repo",
        success=True,
        timestamp=1000.0,
        receipt_hash="tampered_fake_hash_123"
    )

    with pytest.raises(ValueError, match="cryptographic hash mismatch or tampered"):
        validate_report_claims(claim="Verified live repository state", operation_receipt=tampered_receipt)


def test_mismatched_target_receipt_fails_closed():
    ts = 1000.0
    op_type = "live_check"
    target = "wrong_repo"
    success = True
    h = hashlib.sha256(f"{op_type}:{target}:{success}:{ts}".encode()).hexdigest()
    receipt = LiveOperationReceipt(
        operation_type=op_type, target=target, success=success, timestamp=ts, receipt_hash=h
    )

    with pytest.raises(ValueError, match="does not match expected 'canonical_repo'"):
        validate_report_claims(
            claim="Verified live repository state",
            operation_receipt=receipt,
            expected_target="canonical_repo"
        )


def test_mismatched_op_type_receipt_fails_closed():
    ts = 1000.0
    op_type = "dry_run"
    target = "repo"
    success = True
    h = hashlib.sha256(f"{op_type}:{target}:{success}:{ts}".encode()).hexdigest()
    receipt = LiveOperationReceipt(
        operation_type=op_type, target=target, success=success, timestamp=ts, receipt_hash=h
    )

    with pytest.raises(ValueError, match="does not match expected 'live_check'"):
        validate_report_claims(
            claim="Verified live repository state",
            operation_receipt=receipt,
            expected_operation_type="live_check"
        )


def test_valid_receipt_allows_live_claim():
    ts = 1000.0
    op_type = "live_check"
    target = "repo"
    success = True
    h = hashlib.sha256(f"{op_type}:{target}:{success}:{ts}".encode()).hexdigest()
    valid_receipt = LiveOperationReceipt(
        operation_type=op_type, target=target, success=success, timestamp=ts, receipt_hash=h
    )

    validate_report_claims(
        claim="Verified live repository state",
        operation_receipt=valid_receipt,
        expected_operation_type="live_check",
        expected_target="repo"
    )


def test_openai_system_instructions_embed_exact_order_contract():
    envelope = SAGERuntime(state()).envelope("c2")
    instructions = _system_instructions(envelope)
    assert CONTRACT_ID in instructions


def test_station_spoof_is_rejected():
    spoofed = json.dumps({
        "station": "[SAGE::FAKE::CHATGPT]",
        "reasoning_chain": ["recon complete"],
        "proposed_actions": [],
        "epistemic_state": {"confidence_level": "LOW"},
        "evidence_refs": [],
    })
    structured = SAGEProtocolGovernor.validate_and_parse(spoofed)
    assert any("station identity mismatch" in violation.lower() for violation in structured.violations)


def test_missing_station_is_rejected():
    missing = json.dumps({
        "reasoning_chain": ["recon complete"],
        "proposed_actions": [],
        "epistemic_state": {"confidence_level": "LOW"},
        "evidence_refs": [],
    })
    structured = SAGEProtocolGovernor.validate_and_parse(missing)
    assert any("missing required sage station identity" in violation.lower() for violation in structured.violations)


def test_openai_adapter_rejects_spoofed_station():
    spoofed = json.dumps({
        "station": "[SAGE::FAKE::CHATGPT]",
        "reasoning_chain": ["recon"],
        "proposed_actions": [],
        "epistemic_state": {"confidence_level": "LOW"},
        "evidence_refs": [],
    })

    class FakeResponses:
        def create(self, **kwargs):
            return SimpleNamespace(output_text=spoofed)

    class FakeClient:
        responses = FakeResponses()

    runtime = SAGERuntime(state())
    with pytest.raises(ValueError, match="SAGE Protocol Governance Violation"):
        runtime.invoke(OpenAIResponsesAdapter(FakeClient(), model_id="test"), "check live repo", model_role="c2")
