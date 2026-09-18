"""Phase 1 Polymarket read-only ingestion tests."""

import hashlib
import json

import pytest

from sage.experimental.polymarket.ingestion import (
    PolymarketCLOBAdapter,
    PolymarketGammaAdapter,
    PolymarketIngestionEngine,
)
from sage.experimental.polymarket.lane_spec import (
    ExecutionGuardViolation,
    MarketObservation,
    PolymarketEvidenceRecord,
    PolymarketLaneState,
    SageForecast,
    PriceEchoContaminationError,
)


def test_gamma_adapter_normalizes_observation():
    event = {
        "id": "event-1",
        "title": "Fed decision",
        "markets": [{
            "conditionId": "cond-1",
            "question": "Will the Fed cut?",
            "outcomes": ["Yes", "No"],
            "outcomePrices": ["0.65", "0.35"],
            "spread": 0.02,
        }],
    }
    observations = PolymarketGammaAdapter.parse_event_payload(
        event, retrieved_at_utc="2026-01-01T00:00:00+00:00"
    )
    assert len(observations) == 1
    assert observations[0].market_id == "cond-1"
    assert observations[0].market_implied_probability == 0.65
    assert observations[0].raw_payload_hash == hashlib.sha256(
        json.dumps(event, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def test_clob_adapter_is_observation_only():
    observation = PolymarketCLOBAdapter.parse_book_payload(
        "cond-2", "event-2", "Will X happen?",
        {"bids": [{"price": "0.48", "size": "100"}],
         "asks": [{"price": "0.52", "size": "100"}]},
        retrieved_at_utc="2026-01-01T00:00:00+00:00",
    )
    assert observation.market_implied_probability == 0.5
    assert observation.spread == pytest.approx(0.04)
    assert observation.provenance_source == "polymarket_clob_v2"


def test_ingestion_engine_is_read_only_and_deterministic_hashing():
    payload = {"id": "event-3", "markets": [{
        "conditionId": "cond-3",
        "question": "Will X happen?",
        "outcomes": ["Yes", "No"],
        "outcomePrices": ["0.55", "0.45"],
    }]}
    observations = PolymarketIngestionEngine.ingest_raw_feed(payload)
    assert len(observations) == 1
    assert observations[0].market_id == "cond-3"
    assert PolymarketIngestionEngine.compute_raw_hash("abc") == hashlib.sha256(b"abc").hexdigest()


def test_canonical_lane_contract_rejects_execution():
    with pytest.raises(ExecutionGuardViolation):
        PolymarketEvidenceRecord(
            record_id="r1",
            execution_attempted=True,
        )


def test_canonical_lane_contract_rejects_price_echo():
    forecast = SageForecast(
        forecast_id="f1",
        market_id="m1",
        forecast_probability=0.60,
        model_version="v1",
        forecast_timestamp_utc="2026-01-01T00:00:00+00:00",
        rationale_digest="a" * 64,
        price_echo_check_passed=True,
    )
    observation = MarketObservation(
        market_id="m1",
        event_id="e1",
        question="Q?",
        timestamp_utc="2026-01-01T00:00:00+00:00",
        market_implied_probability=0.60,
        order_book_depth={},
        spread=0.02,
        raw_payload_hash="b" * 64,
    )
    record = PolymarketEvidenceRecord(record_id="r1", observation=observation)
    with pytest.raises(PriceEchoContaminationError):
        record.seal_forecast(forecast, market_obs_prob=0.60)


def test_lane_states_and_zero_execution_sentinel():
    assert [s.value for s in PolymarketLaneState] == [
        "DISCOVER", "SNAPSHOT", "HASH", "FORECAST",
        "SEAL", "RESOLVE", "CALIBRATE", "AUDIT",
    ]
    record = PolymarketEvidenceRecord(record_id="r2")
    with pytest.raises(ExecutionGuardViolation):
        record.attempt_execution()
