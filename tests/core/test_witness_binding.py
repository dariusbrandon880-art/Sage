"""Adversarial tests for WitnessBinding v0.1."""

from sage.core.attestation import CryptographicAttestationProvider
from sage.core.witness_binding import (
    WitnessBinding,
    WitnessBindingValidationError,
    WitnessClaimKind,
)


def _claim(**overrides):
    values = {
        "evidence_ref": "sha256:evidence-001",
        "context_id": "ctx-001",
        "source_id": "sports-feed",
        "source_version": "2026-08-21T15:00Z-v1",
        "observed_at": "2026-08-21T15:00:01Z",
        "witness_id": "witness-alpha",
    }
    values.update(overrides)
    return WitnessBinding.create_witness_claim(
        **values,
        attestation_provider=CryptographicAttestationProvider("MOCK"),
    )


def test_deterministic_claim_digest_and_replay():
    a = _claim()
    b = _claim()
    assert a.claim_digest == b.claim_digest
    assert a.to_dict() == b.to_dict()


def test_signature_verifies_and_tampering_fails_closed():
    provider = CryptographicAttestationProvider("MOCK")
    claim = _claim()
    assert claim.verify_signature(provider)

    tampered = WitnessBinding(
        evidence_ref=claim.evidence_ref,
        context_id=claim.context_id,
        source_id=claim.source_id,
        source_version="attacker-version",
        observed_at=claim.observed_at,
        witness_id=claim.witness_id,
        provider_mode=claim.provider_mode,
        signature=claim.signature,
        claim_kind=claim.claim_kind,
    )
    assert not tampered.verify_signature(provider)


def test_metadata_is_bound_to_claim_digest():
    original = _claim()
    changed = _claim(observed_at="2026-08-21T15:00:02Z")
    assert original.claim_digest != changed.claim_digest


def test_context_and_source_substitution_changes_identity():
    original = _claim()
    assert original.claim_digest != _claim(context_id="ctx-002").claim_digest
    assert original.claim_digest != _claim(source_id="other-feed").claim_digest
    assert original.claim_digest != _claim(source_version="v2").claim_digest


def test_claim_kind_is_semantic_and_explicit():
    observation = _claim(claim_kind=WitnessClaimKind.OBSERVATION)
    controller = _claim(claim_kind=WitnessClaimKind.CONTROLLER_REPORT)
    effect = _claim(claim_kind=WitnessClaimKind.EFFECT_REPORT)
    assert len({observation.claim_digest, controller.claim_digest, effect.claim_digest}) == 3
    assert observation.to_dict()["claim_kind"] == "OBSERVATION"


def test_witness_never_grants_authority():
    claim = _claim()
    assert claim.authority_granted is False
    assert claim.to_dict()["authority_granted"] is False


def test_invalid_empty_provenance_fails_closed():
    try:
        _claim(source_version="")
    except WitnessBindingValidationError:
        return
    raise AssertionError("empty source_version must fail closed")


def test_wrong_provider_signature_does_not_verify():
    claim = _claim()
    assert not claim.verify_signature(CryptographicAttestationProvider("TPM"))


def test_provider_mode_is_recorded_without_becoming_authority():
    claim = _claim()
    assert claim.provider_mode == "MOCK"
    assert claim.authority_granted is False
