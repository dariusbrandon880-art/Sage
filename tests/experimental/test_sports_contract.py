from datetime import datetime, timezone, timedelta

import pytest

from sage.experimental.sports_adapters import get_adapter, registered_adapters
from sage.experimental.sports_contract import (
    CanonicalForecastContract,
    FeatureProvenance,
    OutcomeResolution,
    SportsEventIdentity,
    supported_competitions,
)


def _event(sport="baseball", competition="MLB"):
    start = datetime(2026, 8, 30, 18, tzinfo=timezone.utc)
    return SportsEventIdentity(
        event_id=f"{sport}-{competition}-1",
        sport=sport,
        competition=competition,
        scheduled_start_utc=start.isoformat(),
        home_competitor="Home",
        away_competitor="Away",
    )


def test_registry_covers_declared_multi_sport_frontier():
    pairs = set(supported_competitions())
    assert {"baseball", "basketball", "football", "hockey", "tennis"} <= {s for s, _ in pairs}
    assert {"MLB", "NBA", "WNBA", "NCAAB", "NFL", "NCAAF", "NHL", "ATP", "WTA"} <= {c for _, c in pairs}
    assert len(registered_adapters()) >= 9


def test_adapter_normalizes_without_embedding_prediction_logic():
    adapter = get_adapter("basketball", "NBA")
    event = adapter.normalize_event({
        "event_id": "nba-1",
        "scheduled_start_utc": "2026-08-30T18:00:00+00:00",
        "home": "Home",
        "away": "Away",
    })
    assert event.sport == "basketball"
    assert event.competition == "NBA"
    assert event.event_id == "nba-1"


def test_canonical_forecast_enforces_point_in_time_provenance():
    cutoff = datetime(2026, 8, 30, 17, tzinfo=timezone.utc)
    start = cutoff + timedelta(hours=1)
    forecast = CanonicalForecastContract(
        event=SportsEventIdentity(
            event_id="nfl-1", sport="football", competition="NFL",
            scheduled_start_utc=start.isoformat(), home_competitor="A", away_competitor="B"
        ),
        observation_cutoff_utc=cutoff.isoformat(),
        forecast_lock_utc=(cutoff + timedelta(minutes=1)).isoformat(),
        selected_outcome="A",
        predicted_probability=0.61,
        feature_provenance=(FeatureProvenance(
            feature_name="recent_form", source_id="feed-1", source_hash="abc",
            available_at_utc=(cutoff - timedelta(minutes=2)).isoformat()
        ),),
        source_hashes=("abc",),
        model_version="shadow-v1",
    )
    receipt = forecast.receipt_hash()
    assert len(receipt) == 64


def test_canonical_forecast_rejects_post_cutoff_feature():
    cutoff = datetime(2026, 8, 30, 17, tzinfo=timezone.utc)
    start = cutoff + timedelta(hours=1)
    forecast = CanonicalForecastContract(
        event=_event("hockey", "NHL"),
        observation_cutoff_utc=cutoff.isoformat(),
        forecast_lock_utc=(cutoff + timedelta(minutes=1)).isoformat(),
        selected_outcome="Home",
        predicted_probability=0.5,
        feature_provenance=(FeatureProvenance(
            feature_name="late_update", source_id="feed-1", source_hash="abc",
            available_at_utc=(cutoff + timedelta(seconds=1)).isoformat()
        ),),
        source_hashes=("abc",),
    )
    with pytest.raises(ValueError, match="FEATURE_LEAKAGE"):
        forecast.validate()


def test_outcome_resolution_requires_provenance():
    outcome = OutcomeResolution(
        event_id="tennis-ATP-1",
        resolved_at_utc="2026-08-30T22:00:00+00:00",
        outcome="Home",
        source_id="official-results",
        source_hash="results-hash",
    )
    outcome.validate()
