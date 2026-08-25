"""Unit tests for Flight C: Claim-to-Receipt Compiler & Factual Claim Verification."""

import time

from sage.c2.claim_provenance import ClaimProvenanceCompiler
from sage.c2.reality_gate import OperationalClaim, SourceReceipt


def _receipt(resource_id: str, digest: str) -> SourceReceipt:
    return SourceReceipt(
        source_type="github",
        resource_id=resource_id,
        sha256_digest=digest,
        timestamp_utc=time.time(),
        metadata={"origin": "operation_boundary", "operation": "github_observation"},
    )


def test_claim_provenance_compiler_verified():
    resource = "commit:70d1e798d5deee425a138e12ec070c8b10af2793"
    claim = OperationalClaim(
        "c1",
        "GitHub main commit is 70d1e798d5deee425a138e12ec070c8b10af2793.",
        "github",
        resource,
    )

    res = ClaimProvenanceCompiler.compile_claims([claim], [_receipt(resource, resource.split(":", 1)[1])])
    assert res.is_valid is True
    assert len(res.verified_claims) == 1
    assert res.verified_claims[0].status == "PERMITTED"


def test_claim_provenance_compiler_unresolved():
    resource = "commit:70d1e798d5deee425a138e12ec070c8b10af2793"
    claim = OperationalClaim("c1", "GitHub main commit is 70d1e7.", "github", resource)

    res = ClaimProvenanceCompiler.compile_claims([claim], [])
    assert res.is_valid is False
    assert len(res.unresolved_claims) == 1
    assert res.unresolved_claims[0].status == "UNRESOLVED"


def test_claim_provenance_compiler_contradicted():
    expected = "commit:70d1e798d5deee425a138e12ec070c8b10af2793"
    actual = "commit:af43700000000000000000000000000000000000"
    claim = OperationalClaim("c1", "GitHub main commit is 70d1e7.", "github", expected)

    res = ClaimProvenanceCompiler.compile_claims([claim], [_receipt(actual, actual.split(":", 1)[1])])
    assert res.is_valid is False
    assert len(res.contradicted_claims) == 1
    assert res.contradicted_claims[0].status == "CONTRADICTED"
