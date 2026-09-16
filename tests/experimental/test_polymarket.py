"""Tests for Polymarket External Intelligence Lane & Phase 1 Ingestion."""

import pytest
from datetime import datetime, timezone

from sage.experimental.polymarket.lane_spec import (
    ExecutionGuardViolation,
    LifecycleStage,
    PriceEchoViolation,
    PolymarketEvidenceRecord,
    PolymarketForecastRecord,
    PolymarketLaneContract,
    PolymarketMarketSnapshot,
    PolymarketObservation,
)
from sage.experimental.polymarket.ingestion import (
    PolymarketCLOBAdapter,
    PolymarketGammaAdapter,
    PolymarketIngestionEngine,
)


def test_polymarket_snapshot_validations():
    now_utc = datetime.now(timezone.utc).isoformat()
    snap = PolymarketMarketSnapshot(
        condition_id="0x123",
        question_id="0x456",
        question="Will inflation drop below 2% in 2026?",
        outcomes=("Yes", "No"),
        outcome_prices={"Yes": 0.45, "No": 0.55},
        observed_at_utc=now_utc,
    )
    assert snap.condition_id == "0x123"
    assert len(snap.canonical_hash) == 64

    # Invalid prices
    with pytest.raises(ValueError, match="prices must be valid probabilities"):
        PolymarketMarketSnapshot(
            condition_id="0x123",
            question_id="0x456",
            question="Q?",
            outcomes=("Yes", "No"),
            outcome_prices={"Yes": 1.5, "No": -0.5},
            observed_at_utc=now_utc,
        )


def test_zero_execution_guard_enforcement():
    now_utc = datetime.now(timezone.utc).isoformat()
    snap = PolymarketMarketSnapshot(
        condition_id="0x123",
        question_id="0x456",
        question="Q?",
        outcomes=("Yes", "No"),
        outcome_prices={"Yes": 0.5, "No": 0.5},
        observed_at_utc=now_utc,
    )

    # Wagering executed True must fail closed
    with pytest.raises(ExecutionGuardViolation, match="wagering_executed must be False"):
        PolymarketObservation(
            observation_id="obs_1",
            snapshot=snap,
            retrieved_at_utc=now_utc,
            raw_payload_hash="abc",
            normalized_payload_hash="def",
            wagering_executed=True,
        )

    with pytest.raises(ExecutionGuardViolation, match="Illegal execution parameter"):
        PolymarketLaneContract.verify_zero_execution({"buy": "0x123", "amount": 100})


def test_price_echo_isolation_check():
    now_utc = datetime.now(timezone.utc).isoformat()
    # Price echo: prediction matches market prices exactly
    fc_echo = PolymarketForecastRecord(
        forecast_id="fc_1",
        condition_id="0x123",
        predicted_probabilities={"Yes": 0.60, "No": 0.40},
        forecast_generated_at_utc=now_utc,
        model_version="v1",
        rationale="echo test",
        market_price_at_forecast={"Yes": 0.60, "No": 0.40},
    )
    assert fc_echo.validate_price_echo_isolation() is False

    # Independent forecast differs from market price
    fc_independent = PolymarketForecastRecord(
        forecast_id="fc_2",
        condition_id="0x123",
        predicted_probabilities={"Yes": 0.75, "No": 0.25},
        forecast_generated_at_utc=now_utc,
        model_version="v1",
        rationale="independent analysis",
        market_price_at_forecast={"Yes": 0.60, "No": 0.40},
    )
    assert fc_independent.validate_price_echo_isolation() is True


def test_gamma_adapter_parsing():
    raw_event = {
        "id": "1001",
        "title": "Fed Rate Decision",
        "markets": [
            {
                "conditionId": "0xcond1",
                "questionID": "0xq1",
                "question": "Will Fed cut rates in Q3?",
                "outcomes": ["Yes", "No"],
                "outcomePrices": ["0.65", "0.35"],
                "volume24hr": "50000.0",
                "liquidity": "100000.0",
            }
        ],
    }
    snaps = PolymarketGammaAdapter.parse_event_payload(raw_event)
    assert len(snaps) == 1
    assert snaps[0].condition_id == "0xcond1"
    assert snaps[0].outcome_prices["Yes"] == 0.65
    assert snaps[0].volume_24h == 50000.0


def test_clob_adapter_parsing():
    raw_book = {
        "bids": [{"price": "0.48", "size": "100"}],
        "asks": [{"price": "0.52", "size": "100"}],
    }
    snap = PolymarketCLOBAdapter.parse_book_payload("0xcond2", "0xq2", "Will X happen?", raw_book)
    assert snap.outcome_prices["Yes"] == 0.5
    assert snap.outcome_prices["No"] == 0.5


def test_ingestion_engine_and_evidence_record():
    raw_event = {
        "id": "2002",
        "title": "Election Market",
        "markets": [
            {
                "conditionId": "0xelect1",
                "questionID": "0xqelect1",
                "question": "Who wins?",
                "outcomes": ["Candidate A", "Candidate B"],
                "outcomePrices": ["0.55", "0.45"],
            }
        ],
    }
    obs_tuple, evidence = PolymarketIngestionEngine.ingest_raw_feed(raw_event, parent_hash="GENESIS")
    assert len(obs_tuple) == 1
    assert obs_tuple[0].snapshot.condition_id == "0xelect1"
    assert evidence.stage == LifecycleStage.DISCOVER
    assert evidence.parent_hash == "GENESIS"
    assert len(evidence.current_hash) == 64
    assert evidence.wagering_executed is False


def test_lifecycle_transition_rule():
    PolymarketLaneContract.validate_lifecycle_transition(LifecycleStage.DISCOVER, LifecycleStage.SNAPSHOT)
    with pytest.raises(ValueError, match="Cannot transition from LifecycleStage.DISCOVER to LifecycleStage.FORECAST"):
        PolymarketLaneContract.validate_lifecycle_transition(LifecycleStage.DISCOVER, LifecycleStage.FORECAST)
