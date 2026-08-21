"""Adversarial tests for evidence binding integrity and admissibility."""

import hashlib
import json

import pytest

from sage.evidence_binding import (
    BINDING_VERSION,
    FALSIFIED,
    PENDING,
    VERIFIED,
    EvidenceBinding,
    EvidenceBindingVerifier,
)


def digest(value):
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def binding(ref="receipt:001", content=None, status=VERIFIED):
    payload = content or {"value": 42, "source": "fixture"}
    return EvidenceBinding(
        evidence_ref=ref,
        source_id="source-A",
        source_version="2026.08",
        observed_at="2026-08-21T23:00:00Z",
        content=payload,
        content_hash=digest(payload),
        verification_status=status,
    )


def test_verified_binding_is_admissible():
    item = binding()
    assert item.binding_version == BINDING_VERSION
    assert item.verify_integrity() is True
    assert item.is_admissible() is True


def test_tampered_content_fails_integrity():
    item = binding()
    tampered = EvidenceBinding(
        evidence_ref=item.evidence_ref,
        source_id=item.source_id,
        source_version=item.source_version,
        observed_at=item.observed_at,
        content={"value": 43, "source": "fixture"},
        content_hash=item.content_hash,
    )
    assert tampered.verify_integrity() is False
    assert tampered.is_admissible() is False


def test_pending_binding_is_not_admissible():
    item = binding(status=PENDING)
    assert item.verify_integrity() is True
    assert item.is_admissible() is False


def test_falsified_binding_is_not_admissible():
    item = binding(status=FALSIFIED)
    assert item.is_admissible() is False


def test_verifier_returns_verified_for_bound_valid_evidence():
    result = EvidenceBindingVerifier().verify_required(
        ["receipt:001"], {"receipt:001": binding()}
    )
    assert result == {"receipt:001": VERIFIED}


def test_missing_binding_is_pending():
    result = EvidenceBindingVerifier().verify_required(["receipt:001"], {})
    assert result == {"receipt:001": PENDING}


def test_wrong_ref_binding_is_falsified():
    result = EvidenceBindingVerifier().verify_required(
        ["receipt:001"], {"receipt:001": binding(ref="receipt:999")}
    )
    assert result == {"receipt:001": FALSIFIED}


def test_tampered_binding_is_falsified():
    item = binding()
    tampered = EvidenceBinding(
        evidence_ref=item.evidence_ref,
        source_id=item.source_id,
        source_version=item.source_version,
        observed_at=item.observed_at,
        content={"value": "tampered"},
        content_hash=item.content_hash,
    )
    result = EvidenceBindingVerifier().verify_required(["receipt:001"], {"receipt:001": tampered})
    assert result == {"receipt:001": FALSIFIED}


def test_duplicate_required_refs_fail_closed():
    with pytest.raises(ValueError, match="duplicate required evidence_ref"):
        EvidenceBindingVerifier().verify_required(["receipt:001", "receipt:001"], {})


def test_missing_source_metadata_fails_closed():
    with pytest.raises(ValueError, match="source_id"):
        EvidenceBinding(
            evidence_ref="receipt:001",
            source_id="",
            source_version="2026.08",
            observed_at="2026-08-21T23:00:00Z",
            content={"x": 1},
            content_hash=digest({"x": 1}),
        )
