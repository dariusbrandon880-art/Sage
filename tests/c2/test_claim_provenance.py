"""Unit tests for Flight C: Claim-to-Receipt Compiler & Factual Claim Verification."""

import time
from sage.c2.claim_provenance import ClaimProvenanceCompiler
from sage.c2.reality_gate import OperationalClaim, SourceReceipt


def test_claim_provenance_compiler_verified():
    claims = [
        OperationalClaim(
            claim_id="c1",
            statement="GitHub main commit is 70d1e798d5deee425a138e12ec070c8b10af2793.",
            required_source_type="github",
            target_resource="commit:70d1e798d5deee425a138e12ec070c8b10af2793",
        )
    ]
    receipts = [
        SourceReceipt(
            source_type="github",
            resource_id="commit:70d1e798d5deee425a138e12ec070c8b10af2793",
            sha256_digest="70d1e798d5deee425a138e12ec070c8b10af2793",
            timestamp_utc=time.time(),
        )
    ]

    res = ClaimProvenanceCompiler.compile_claims(claims, receipts)
    assert res.is_valid is True
    assert len(res.verified_claims) == 1
    assert res.verified_claims[0].status == "PERMITTED"


def test_claim_provenance_compiler_unresolved():
    claims = [
        OperationalClaim(
            claim_id="c1",
            statement="GitHub main commit is 70d1e798d5deee425a138e12ec070c8b10af2793.",
            required_source_type="github",
            target_resource="commit:70d1e798d5deee425a138e12ec070c8b10af2793",
        )
    ]
    receipts = []

    res = ClaimProvenanceCompiler.compile_claims(claims, receipts)
    assert res.is_valid is False
    assert len(res.unresolved_claims) == 1
    assert res.unresolved_claims[0].status == "UNRESOLVED"


def test_claim_provenance_compiler_contradicted():
    claims = [
        OperationalClaim(
            claim_id="c1",
            statement="GitHub main commit is 70d1e798d5deee425a138e12ec070c8b10af2793.",
            required_source_type="github",
            target_resource="commit:70d1e798d5deee425a138e12ec070c8b10af2793",
        )
    ]
    receipts = [
        SourceReceipt(
            source_type="github",
            resource_id="commit:af43700000000000000000000000000000000000",
            sha256_digest="af43700000000000000000000000000000000000",
            timestamp_utc=time.time(),
        )
    ]

    res = ClaimProvenanceCompiler.compile_claims(claims, receipts)
    assert res.is_valid is False
    assert len(res.contradicted_claims) == 1
    assert res.contradicted_claims[0].status == "CONTRADICTED"
