import pytest

from sage.core.attestation import CryptographicAttestationProvider
from sage.core.witness_binding import (
    WitnessBinding,
    WitnessBindingValidationError,
    WitnessClaimKind,
)


def _claim(**overrides):
    values = {
        "evidence_ref": "evidence-001",
        "context_id": "ctx-001",
        "source_id": "source-001",
        "source_version": "v1",
        "observed_at": "2026-08-21T23:00:00Z",
        "witness_id": "witness-001",
    }
    values.update(overrides)
    return WitnessBinding.create_witness_claim(
        **values,
        attestation_provider=CryptographicAttestationProvider("MOCK"),
    )


def test_verification_report_separates_integrity_from_truth():
    provider = CryptographicAttestationProvider("MOCK")
    claim = _claim()

    report = claim.verification_report(provider)

    assert report["signature_valid"] is True
    assert report["provenance_bound"] is True
    assert report["independence_status"] == "UNKNOWN"
    assert report["real_world_effect_proven"] is False
    assert report["authority_granted"] is False
    assert report["verification_scope"] == "SIGNED_CLAIM_INTEGRITY_ONLY"


def test_metadata_substitution_invalidates_signature():
    provider = CryptographicAttestationProvider("MOCK")
    claim = _claim()
    substituted = WitnessBinding(
        evidence_ref=claim.evidence_ref,
        context_id=claim.context_id,
        source_id=claim.source_id,
        source_version="v2",
        observed_at=claim.observed_at,
        witness_id=claim.witness_id,
        provider_mode=claim.provider_mode,
        signature=claim.signature,
        claim_kind=claim.claim_kind,
    )

    assert substituted.verify_signature(provider) is False
    assert substituted.claim_digest != claim.claim_digest


def test_claim_kind_is_part_of_digest_and_signature():
    observation = _claim(claim_kind=WitnessClaimKind.OBSERVATION)
    controller = _claim(claim_kind=WitnessClaimKind.CONTROLLER_REPORT)

    assert observation.claim_digest != controller.claim_digest
    assert observation.signature != controller.signature


def test_authority_can_never_be_granted_by_witness_binding():
    claim = _claim()
    assert claim.authority_granted is False
    assert claim.to_dict()["authority_granted"] is False


def test_invalid_witness_identity_fails_closed():
    with pytest.raises(WitnessBindingValidationError):
        WitnessBinding(
            evidence_ref="evidence-001",
            context_id="ctx-001",
            source_id="source-001",
            source_version="v1",
            observed_at="2026-08-21T23:00:00Z",
            witness_id="",
            provider_mode="MOCK",
            signature="sig",
        )
