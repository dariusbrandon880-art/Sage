"""Tests for the governed native multimodal perception bridge."""

import pytest

from sage.c2.perception_bridge import EvidenceStage, PerceptionBridge, PerceptionClaim, PerceptionEvent


@pytest.fixture
def event() -> PerceptionEvent:
    return PerceptionEvent(
        event_id="perception-test-001",
        timestamp=1_700_000_000.0,
        source="native_multimodal_interface",
        user_intent="identify the vehicle on screen",
        modality=["screen", "audio"],
        claims=[
            PerceptionClaim(text="A vehicle is visible.", stage=EvidenceStage.OBSERVED, confidence=0.99),
            PerceptionClaim(text="The vehicle may be a Lamborghini Miura.", stage=EvidenceStage.INFERRED, confidence=0.82),
            PerceptionClaim(text="Manufacturer history was searched.", stage=EvidenceStage.SEARCHED, source_ref="search:manufacturer"),
            PerceptionClaim(text="The model identity is supported by the cited source.", stage=EvidenceStage.VERIFIED, source_ref="source:manufacturer"),
        ],
    )


def test_ingest_accepts_explicit_native_multimodal_source(event: PerceptionEvent) -> None:
    accepted = PerceptionBridge().ingest(event)
    assert accepted.event_id == event.event_id


def test_ingest_rejects_unknown_sensor_source(event: PerceptionEvent) -> None:
    event.source = "imaginary_device_feed"
    with pytest.raises(ValueError, match="Unsupported perception source"):
        PerceptionBridge().ingest(event)


def test_ingest_requires_explicit_claims(event: PerceptionEvent) -> None:
    event.claims = []
    with pytest.raises(ValueError, match="at least one explicit claim"):
        PerceptionBridge().ingest(event)


def test_claim_stages_never_collapse(event: PerceptionEvent) -> None:
    assert len(PerceptionBridge.claims_at_stage(event, EvidenceStage.OBSERVED)) == 1
    assert len(PerceptionBridge.claims_at_stage(event, EvidenceStage.INFERRED)) == 1
    assert len(PerceptionBridge.claims_at_stage(event, EvidenceStage.SEARCHED)) == 1
    assert len(PerceptionBridge.claims_at_stage(event, EvidenceStage.VERIFIED)) == 1


def test_digest_is_deterministic(event: PerceptionEvent) -> None:
    assert PerceptionBridge.canonical_digest(event) == PerceptionBridge.canonical_digest(event)
    assert len(PerceptionBridge.canonical_digest(event)) == 64


def test_acceptance_summary_is_fail_closed(event: PerceptionEvent) -> None:
    summary = PerceptionBridge.acceptance_summary(event)
    assert summary["fail_closed"] is True
    assert summary["observed_count"] == 1
    assert summary["inferred_count"] == 1
    assert summary["searched_count"] == 1
    assert summary["verified_count"] == 1
