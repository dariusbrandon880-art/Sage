"""Governed tests for the point-in-time sports shadow research lane.

The canonical testbed is prediction-only: no synthetic market observations, public
consensus, CLV fabrication, parlay generation, or wagering execution is permitted.
"""

from datetime import datetime, timezone, timedelta

import pytest

from sage.experimental.sports_longitudinal import (
    LockedResearchPrediction,
    ObservationProvenance,
    ReplayableObservationStream,
    RealSportsEventObservation,
    TemporalConsistencyValidator,
)


def make_observation(start: datetime, observed: datetime) -> RealSportsEventObservation:
    return RealSportsEventObservation(
        event_id="game-1",
        sport="baseball",
        league="MLB",
        home_team="Home",
        away_team="Away",
        event_start_time_utc=start.isoformat(),
        observation_timestamp_utc=observed.isoformat(),
        source_name="Official schedule source",
        source_url="https://statsapi.mlb.com/api/v1/schedule",
        market_name="NONE",
        observed_odds={},
        event_status="Scheduled",
    )


def test_point_in_time_lock_is_strictly_before_event_start():
    observed = datetime(2026, 8, 30, 18, tzinfo=timezone.utc)
    start = observed + timedelta(hours=1)
    obs = make_observation(start, observed)

    pred = LockedResearchPrediction(
        prediction_id="pred-1",
        cycle_id="cycle-1",
        event_observation=obs,
        selected_prediction="Home",
        odds_at_lock="UNAVAILABLE",
        implied_probability=0.5,
        model_predicted_probability=0.6,
        lock_timestamp_utc=observed.isoformat(),
        model_state_rationale="Pre-event baseline only",
        is_parlay=False,
        parlay_legs=[],
    )
    assert pred.lock_and_sign()


def test_temporal_guard_rejects_started_event():
    start = datetime(2026, 8, 30, 18, tzinfo=timezone.utc)
    observed = start + timedelta(minutes=1)
    with pytest.raises(ValueError, match="TEMPORAL_CONSISTENCY_VIOLATION"):
        TemporalConsistencyValidator.validate_pre_game_observation(
            observed.isoformat(), start.isoformat()
        )


def test_replay_stream_requires_real_pre_event_provenance():
    observed = datetime(2026, 8, 30, 18, tzinfo=timezone.utc)
    start = observed + timedelta(hours=1)
    payload = {"game_pk": "1", "home_team": "Home", "away_team": "Away"}
    provenance = ObservationProvenance(
        source_id="schedule-1",
        source_name="Official schedule source",
        source_url="https://statsapi.mlb.com/api/v1/schedule",
        source_timestamp_utc=observed.isoformat(),
        raw_payload_hash="raw-hash",
        ingest_timestamp_utc=observed.isoformat(),
    )
    stream = ReplayableObservationStream()
    event = stream.append_event(
        event_id="game-1",
        observation_id="obs-1",
        observation_timestamp_utc=observed.isoformat(),
        event_start_time_utc=start.isoformat(),
        provenance=provenance,
        payload=payload,
    )
    assert event.event_hash
    assert event.provenance.provenance_hash


def test_prediction_rejects_backdated_or_post_event_lock():
    start = datetime(2026, 8, 30, 18, tzinfo=timezone.utc)
    post_event = start + timedelta(minutes=1)
    obs = make_observation(start, start - timedelta(minutes=15))
    with pytest.raises(ValueError, match="TEMPORAL_LOCK_VIOLATION"):
        LockedResearchPrediction(
            prediction_id="pred-post-event",
            cycle_id="cycle-1",
            event_observation=obs,
            selected_prediction="Home",
            odds_at_lock="UNAVAILABLE",
            implied_probability=0.5,
            model_predicted_probability=0.6,
            lock_timestamp_utc=post_event.isoformat(),
            model_state_rationale="Invalid post-event attempt",
        )


def test_market_consensus_and_parlay_surfaces_are_not_part_of_canonical_prediction():
    observed = datetime(2026, 8, 30, 18, tzinfo=timezone.utc)
    start = observed + timedelta(hours=1)
    obs = make_observation(start, observed)
    pred = LockedResearchPrediction(
        prediction_id="pred-clean",
        cycle_id="cycle-clean",
        event_observation=obs,
        selected_prediction="Home",
        odds_at_lock="UNAVAILABLE",
        implied_probability=0.5,
        model_predicted_probability=0.6,
        lock_timestamp_utc=observed.isoformat(),
        model_state_rationale="No market or consensus inputs",
        is_parlay=False,
        parlay_legs=[],
    )
    assert pred.event_observation.observed_odds == {}
    assert pred.is_parlay is False
    assert pred.parlay_legs == []
    assert pred.odds_at_lock == "UNAVAILABLE"
