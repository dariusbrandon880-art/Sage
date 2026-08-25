import json
from types import SimpleNamespace

import pytest

from sage.c2.chatgpt_c2_contract import (
    ANTI_DRIFT_LAWS,
    CONTRACT_ID,
    CONTRACT_VERSION,
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


def test_false_live_claim_fails_closed():
    with pytest.raises(ValueError, match="live verification claim"):
        validate_report_claims(live_operation_performed=False, claim="Verified live repository state")


def test_live_claim_is_allowed_after_live_operation():
    validate_report_claims(live_operation_performed=True, claim="Verified live repository state")


def test_openai_system_instructions_embed_exact_order_contract():
    envelope = SAGERuntime(state()).envelope("c2")
    instructions = _system_instructions(envelope)
    assert CONTRACT_ID in instructions
    assert "PRESERVE EXACTLY" in instructions
    assert "INVOKE CONNECTED CAPABILITY" in instructions
    assert "REPORT ONLY SUPPORTED FACTS" in instructions


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
