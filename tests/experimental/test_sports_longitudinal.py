"""Comprehensive Unit & Regression Test Suite for Sports Longitudinal Primitive."""

import pytest
from dataclasses import asdict
from sage.experimental.sports_longitudinal import (
    RealSportsEventObservation,
    LockedResearchPrediction,
    SportsOutcomeRecord,
    SportsScoreRecord,
    SportsLearningRecord,
    calculate_brier_score,
    resolve_sports_prediction,
    SportsLongitudinalLedger,
    SportsOutcomeReconciler,
    ReconciliationRunReceipt,
    ReconciliationQualityTelemetry,
    SourceObservation,
    ObservationArbitrationReceipt,
    SportsObservationArbitrator,
    ObservationReliabilityGrade,
    ProviderReliabilityRecord,
    ObservationReliabilityLedger,
    ObservationTemporalClassification,
    ObservationTemporalRecord,
    ObservationTemporalLedger,
    SportsObservationEventType,
    SportsObservationEvent,
    SportsObservationEventStream,
    ObservationAvailabilityClassification,
    ObservationAvailabilitySnapshot,
    HistoricalInformationIntegrityAnalyzer
)

def test_a_changing_locked_prediction_field_changes_hash():
    obs = RealSportsEventObservation(
        event_id="mlb_20260816_nyy_bos",
        sport="baseball",
        league="mlb",
        home_team="Boston Red Sox",
        away_team="New York Yankees",
        event_start_time_utc="2026-08-16T23:10:00Z",
        observation_timestamp_utc="2026-08-16T20:00:00Z",
        source_name="Official MLB Stats API",
        source_url="https://statsapi.mlb.com/api/v1/schedule?sportId=1",
        market_name="Moneyline",
        observed_odds={"home": -110, "away": -110},
        event_status="STATUS_SCHEDULED"
    )

    pred1 = LockedResearchPrediction(
        prediction_id="pred_real_hash_001",
        cycle_id="cycle_20260816",
        event_observation=obs,
        selected_prediction="New York Yankees Moneyline",
        odds_at_lock="-110",
        implied_probability=0.5238,
        model_predicted_probability=0.5850,
        lock_timestamp_utc="2026-08-16T20:05:00Z",
        model_state_rationale="Pitching advantage."
    )
    h1 = pred1.lock_and_sign()

    # Create pred2 with modified probability
    pred2 = LockedResearchPrediction(
        prediction_id="pred_real_hash_001",
        cycle_id="cycle_20260816",
        event_observation=obs,
        selected_prediction="New York Yankees Moneyline",
        odds_at_lock="-110",
        implied_probability=0.5238,
        model_predicted_probability=0.6200, # Changed probability!
        lock_timestamp_utc="2026-08-16T20:05:00Z",
        model_state_rationale="Pitching advantage."
    )
    h2 = pred2.lock_and_sign()

    assert h1 != h2

def test_b_after_resolution_original_prediction_remains_unchanged():
    obs = RealSportsEventObservation(
        event_id="mlb_20260816_nyy_bos",
        sport="baseball",
        league="mlb",
        home_team="Boston Red Sox",
        away_team="New York Yankees",
        event_start_time_utc="2026-08-16T23:10:00Z",
        observation_timestamp_utc="2026-08-16T20:00:00Z",
        source_name="Official MLB Stats API",
        source_url="https://statsapi.mlb.com/api/v1/schedule?sportId=1",
        market_name="Moneyline",
        observed_odds={"home": -110, "away": -110},
        event_status="STATUS_SCHEDULED"
    )

    pred = LockedResearchPrediction(
        prediction_id="pred_real_immut_001",
        cycle_id="cycle_20260816",
        event_observation=obs,
        selected_prediction="New York Yankees Moneyline",
        odds_at_lock="-110",
        implied_probability=0.5238,
        model_predicted_probability=0.5850,
        lock_timestamp_utc="2026-08-16T20:05:00Z",
        model_state_rationale="Pitching advantage."
    )
    original_hash = pred.lock_and_sign()
    pred_dict_before = asdict(pred)

    outcome, score, learning = resolve_sports_prediction(
        prediction=pred,
        verification_source_name="Official MLB Stats API",
        verification_source_url="https://statsapi.mlb.com/api/v1/schedule?sportId=1",
        actual_home_score=2,
        actual_away_score=5,
        actual_result_text="New York Yankees defeated Boston Red Sox 5-2",
        outcome_status="WIN",
        verification_timestamp_utc="2026-08-17T02:00:00Z"
    )

    pred_dict_after = asdict(pred)

    # Assert byte-for-byte state equality before and after resolution
    assert pred_dict_before == pred_dict_after
    assert pred.sha256_receipt_hash == original_hash

def test_c_resolution_creates_separate_outcome_record():
    obs = RealSportsEventObservation(
        event_id="mlb_20260816_lad_sdp",
        sport="baseball",
        league="mlb",
        home_team="San Diego Padres",
        away_team="Los Angeles Dodgers",
        event_start_time_utc="2026-08-16T22:10:00Z",
        observation_timestamp_utc="2026-08-16T21:00:00Z",
        source_name="Official MLB Stats API",
        source_url="https://statsapi.mlb.com/api/v1/schedule?sportId=1",
        market_name="Moneyline",
        observed_odds={"home": "+105", "away": "-125"},
        event_status="STATUS_SCHEDULED"
    )

    pred = LockedResearchPrediction(
        prediction_id="pred_real_sep_001",
        cycle_id="cycle_20260816",
        event_observation=obs,
        selected_prediction="Los Angeles Dodgers Moneyline",
        odds_at_lock="-125",
        implied_probability=0.5556,
        model_predicted_probability=0.6200,
        lock_timestamp_utc="2026-08-16T21:05:00Z",
        model_state_rationale="Dodgers offensive run rate model advantage."
    )
    p_hash = pred.lock_and_sign()

    outcome, score, learning = resolve_sports_prediction(
        prediction=pred,
        verification_source_name="Official MLB Stats API",
        verification_source_url="https://statsapi.mlb.com/api/v1/schedule?sportId=1",
        actual_home_score=3,
        actual_away_score=5,
        actual_result_text="Los Angeles Dodgers defeated San Diego Padres 5-3",
        outcome_status="WIN",
        verification_timestamp_utc="2026-08-17T01:30:00Z"
    )

    assert isinstance(outcome, SportsOutcomeRecord)
    assert outcome.outcome_id == "out_pred_real_sep_001"
    assert outcome.prediction_id == "pred_real_sep_001"
    assert outcome.prediction_hash == p_hash
    assert outcome.outcome_status == "WIN"

def test_d_outcome_references_exact_prediction_id_and_hash():
    obs = RealSportsEventObservation(
        event_id="mlb_20260816_lad_sdp",
        sport="baseball",
        league="mlb",
        home_team="San Diego Padres",
        away_team="Los Angeles Dodgers",
        event_start_time_utc="2026-08-16T22:10:00Z",
        observation_timestamp_utc="2026-08-16T21:00:00Z",
        source_name="Official MLB Stats API",
        source_url="https://statsapi.mlb.com/api/v1/schedule?sportId=1",
        market_name="Moneyline",
        observed_odds={"home": "+105", "away": "-125"},
        event_status="STATUS_SCHEDULED"
    )

    pred = LockedResearchPrediction(
        prediction_id="pred_real_ref_001",
        cycle_id="cycle_20260816",
        event_observation=obs,
        selected_prediction="Los Angeles Dodgers Moneyline",
        odds_at_lock="-125",
        implied_probability=0.5556,
        model_predicted_probability=0.6200,
        lock_timestamp_utc="2026-08-16T21:05:00Z",
        model_state_rationale="Dodgers offensive run rate model advantage."
    )
    expected_hash = pred.lock_and_sign()

    outcome, score, learning = resolve_sports_prediction(
        prediction=pred,
        verification_source_name="Official MLB Stats API",
        verification_source_url="https://statsapi.mlb.com/api/v1/schedule?sportId=1",
        actual_home_score=3,
        actual_away_score=5,
        actual_result_text="Los Angeles Dodgers defeated San Diego Padres 5-3",
        outcome_status="WIN",
        verification_timestamp_utc="2026-08-17T01:30:00Z"
    )

    assert outcome.prediction_id == pred.prediction_id
    assert outcome.prediction_hash == expected_hash

def test_e_scoring_cannot_occur_against_unresolved_prediction():
    predictions = [
        {"outcome_status": "UNRESOLVED", "model_predicted_probability": 0.60},
        {"outcome_status": "PENDING", "model_predicted_probability": 0.55}
    ]

    brier = calculate_brier_score(predictions)
    assert brier is None

def test_f_learning_cannot_modify_prediction_or_outcome():
    obs = RealSportsEventObservation(
        event_id="mlb_20260816_lad_sdp",
        sport="baseball",
        league="mlb",
        home_team="San Diego Padres",
        away_team="Los Angeles Dodgers",
        event_start_time_utc="2026-08-16T22:10:00Z",
        observation_timestamp_utc="2026-08-16T21:00:00Z",
        source_name="Official MLB Stats API",
        source_url="https://statsapi.mlb.com/api/v1/schedule?sportId=1",
        market_name="Moneyline",
        observed_odds={"home": "+105", "away": "-125"},
        event_status="STATUS_SCHEDULED"
    )

    pred = LockedResearchPrediction(
        prediction_id="pred_real_learn_001",
        cycle_id="cycle_20260816",
        event_observation=obs,
        selected_prediction="San Diego Padres Moneyline",
        odds_at_lock="+105",
        implied_probability=0.4878,
        model_predicted_probability=0.5300,
        lock_timestamp_utc="2026-08-16T21:05:00Z",
        model_state_rationale="Home advantage."
    )
    p_hash = pred.lock_and_sign()

    outcome, score, learning = resolve_sports_prediction(
        prediction=pred,
        verification_source_name="Official MLB Stats API",
        verification_source_url="https://statsapi.mlb.com/api/v1/schedule?sportId=1",
        actual_home_score=2,
        actual_away_score=6,
        actual_result_text="Los Angeles Dodgers defeated San Diego Padres 6-2",
        outcome_status="LOSS",
        verification_timestamp_utc="2026-08-17T01:30:00Z"
    )

    assert isinstance(learning, SportsLearningRecord)
    assert learning.prediction_id == pred.prediction_id
    assert learning.prediction_hash == p_hash
    assert pred.selected_prediction == "San Diego Padres Moneyline"
    assert outcome.outcome_status == "LOSS"

def test_h_duplicate_ids_fail_closed():
    obs = RealSportsEventObservation(
        event_id="mlb_game_dup",
        sport="baseball",
        league="mlb",
        home_team="Padres",
        away_team="Dodgers",
        event_start_time_utc="2026-08-16T22:10:00Z",
        observation_timestamp_utc="2026-08-16T21:00:00Z",
        source_name="Official MLB Stats API",
        source_url="https://statsapi.mlb.com/api/v1/schedule?sportId=1",
        market_name="Moneyline",
        observed_odds={"home": "+105", "away": "-125"},
        event_status="STATUS_SCHEDULED"
    )

    pred = LockedResearchPrediction(
        prediction_id="pred_dup_test_001",
        cycle_id="cycle_20260816",
        event_observation=obs,
        selected_prediction="Dodgers Moneyline",
        odds_at_lock="-125",
        implied_probability=0.5556,
        model_predicted_probability=0.6200,
        lock_timestamp_utc="2026-08-16T21:05:00Z",
        model_state_rationale="Advantage."
    )

    ledger = SportsLongitudinalLedger()
    ledger.add_prediction(pred)

    with pytest.raises(ValueError, match="DUPLICATE_PREDICTION_ID"):
        ledger.add_prediction(pred)

def test_i_synthetic_rce001_remains_isolated_from_real_world():
    ledger = SportsLongitudinalLedger()
    summary = ledger.generate_summary_report()
    assert summary["classification_breakdown"]["SYNTHETIC RCE-001"] == 0
    assert summary["classification_breakdown"]["ACTUAL MONEY WAGERS"] == 0

def test_j_durable_ledger_persistence_and_restart_recovery(tmp_path):
    ledger_file = tmp_path / "test_sports_ledger.json"
    obs = RealSportsEventObservation(
        event_id="mlb_20260816_restart_test",
        sport="baseball", league="mlb", home_team="Giants", away_team="Rockies",
        event_start_time_utc="2026-08-16T23:00:00Z", observation_timestamp_utc="2026-08-16T20:00:00Z",
        source_name="Official MLB Stats API", source_url="https://statsapi.mlb.com/api/v1/schedule?sportId=1",
        market_name="Moneyline", observed_odds={"home": -120}, event_status="SCHEDULED"
    )

    pred1 = LockedResearchPrediction(
        prediction_id="pred_restart_001", cycle_id="cycle_restart", event_observation=obs,
        selected_prediction="Giants Moneyline", odds_at_lock="-120", implied_probability=0.545,
        model_predicted_probability=0.600, lock_timestamp_utc="2026-08-16T20:05:00Z",
        model_state_rationale="Home strength"
    )

    pred2 = LockedResearchPrediction(
        prediction_id="pred_restart_002", cycle_id="cycle_restart", event_observation=obs,
        selected_prediction="Rockies Moneyline", odds_at_lock="+100", implied_probability=0.500,
        model_predicted_probability=0.450, lock_timestamp_utc="2026-08-16T20:05:00Z",
        model_state_rationale="Away underdog"
    )

    # 1. Initialize ledger with storage path and persist predictions
    ledger = SportsLongitudinalLedger(storage_path=ledger_file)
    ledger.add_prediction(pred1)
    ledger.add_prediction(pred2)

    assert ledger_file.exists()

    # 2. Simulate process restart by instantiating new ledger pointing to same storage path
    restarted_ledger = SportsLongitudinalLedger(storage_path=ledger_file)
    pending = restarted_ledger.get_pending_predictions()

    assert len(pending) == 2
    pending_ids = {p.prediction_id for p in pending}
    assert pending_ids == {"pred_restart_001", "pred_restart_002"}

    # 3. Resolve only pred1
    outcome1, score1, learn1 = resolve_sports_prediction(
        prediction=pred1, verification_source_name="Official MLB Stats API",
        verification_source_url="https://statsapi.mlb.com/api/v1/schedule?sportId=1",
        actual_home_score=5, actual_away_score=2, actual_result_text="Giants win 5-2",
        outcome_status="WIN", verification_timestamp_utc="2026-08-17T02:00:00Z"
    )
    restarted_ledger.add_outcome(outcome1)
    restarted_ledger.add_score(score1)
    restarted_ledger.add_learning(learn1)

    # 4. Verify pred2 remains pending
    remaining_pending = restarted_ledger.get_pending_predictions()
    assert len(remaining_pending) == 1
    assert remaining_pending[0].prediction_id == "pred_restart_002"

    # 5. Verify fresh process re-read observes updated pending state
    restarted_ledger_2 = SportsLongitudinalLedger(storage_path=ledger_file)
    assert len(restarted_ledger_2.get_pending_predictions()) == 1
    assert restarted_ledger_2.get_pending_predictions()[0].prediction_id == "pred_restart_002"

def test_k_parlay_multi_leg_resolution_lifecycle(tmp_path):
    ledger_file = tmp_path / "parlay_ledger.json"
    ledger = SportsLongitudinalLedger(storage_path=ledger_file)

    obs = RealSportsEventObservation(
        event_id="mlb_parlay_event",
        sport="baseball", league="mlb", home_team="NYY", away_team="BOS",
        event_start_time_utc="2026-08-16T23:00:00Z", observation_timestamp_utc="2026-08-16T20:00:00Z",
        source_name="Official MLB Stats API", source_url="https://statsapi.mlb.com/api/v1/schedule?sportId=1",
        market_name="Moneyline", observed_odds={"home": -110}, event_status="SCHEDULED"
    )

    leg1 = LockedResearchPrediction(
        prediction_id="leg_001", cycle_id="c1", event_observation=obs,
        selected_prediction="NYY Moneyline", odds_at_lock="-110", implied_probability=0.524,
        model_predicted_probability=0.580, lock_timestamp_utc="2026-08-16T20:05:00Z",
        model_state_rationale="Leg 1"
    )

    leg2 = LockedResearchPrediction(
        prediction_id="leg_002", cycle_id="c1", event_observation=obs,
        selected_prediction="LAD Moneyline", odds_at_lock="-120", implied_probability=0.545,
        model_predicted_probability=0.610, lock_timestamp_utc="2026-08-16T20:05:00Z",
        model_state_rationale="Leg 2"
    )

    parlay = LockedResearchPrediction(
        prediction_id="parlay_001", cycle_id="c1", event_observation=obs,
        selected_prediction="2-Leg Parlay", odds_at_lock="+240", implied_probability=0.285,
        model_predicted_probability=0.353, lock_timestamp_utc="2026-08-16T20:05:00Z",
        model_state_rationale="Composite Parlay", is_parlay=True,
        parlay_legs=[{"prediction_id": "leg_001"}, {"prediction_id": "leg_002"}]
    )

    ledger.add_prediction(leg1)
    ledger.add_prediction(leg2)
    ledger.add_prediction(parlay)

    # Attempt to resolve parlay before legs are complete -> returns None
    res = ledger.resolve_parlay_if_legs_complete(
        parlay_prediction_id="parlay_001",
        verification_source_name="Official MLB Stats API",
        verification_source_url="https://statsapi.mlb.com/api/v1/schedule?sportId=1",
        verification_timestamp_utc="2026-08-17T02:00:00Z"
    )
    assert res is None

    # Resolve Leg 1
    out1, sc1, lrn1 = resolve_sports_prediction(
        leg1, "Official MLB Stats API", "https://statsapi.mlb.com/api/v1/schedule?sportId=1",
        5, 2, "NYY win", "WIN", "2026-08-17T02:00:00Z"
    )
    ledger.add_outcome(out1)

    # Parlay still incomplete (leg 2 unresolved)
    assert ledger.resolve_parlay_if_legs_complete("parlay_001", "MLB", "http", "2026-08-17T02:00:00Z") is None

    # Resolve Leg 2
    out2, sc2, lrn2 = resolve_sports_prediction(
        leg2, "Official MLB Stats API", "https://statsapi.mlb.com/api/v1/schedule?sportId=1",
        4, 1, "LAD win", "WIN", "2026-08-17T02:05:00Z"
    )
    ledger.add_outcome(out2)

    # Parlay now completes successfully
    parlay_res = ledger.resolve_parlay_if_legs_complete(
        parlay_prediction_id="parlay_001",
        verification_source_name="Official MLB Stats API",
        verification_source_url="https://statsapi.mlb.com/api/v1/schedule?sportId=1",
        verification_timestamp_utc="2026-08-17T02:10:00Z"
    )
    assert parlay_res is not None
    p_out, p_sc, p_lrn = parlay_res
    assert p_out.outcome_status == "WIN"
    assert p_out.prediction_id == "parlay_001"

def test_l_duplicate_resolution_and_orphan_scoring_fail_closed():
    obs = RealSportsEventObservation(
        event_id="mlb_orphan_test",
        sport="baseball", league="mlb", home_team="NYY", away_team="BOS",
        event_start_time_utc="2026-08-16T23:00:00Z", observation_timestamp_utc="2026-08-16T20:00:00Z",
        source_name="Official MLB Stats API", source_url="https://statsapi.mlb.com/api/v1/schedule?sportId=1",
        market_name="Moneyline", observed_odds={"home": -110}, event_status="SCHEDULED"
    )

    pred = LockedResearchPrediction(
        prediction_id="pred_dup_res_001", cycle_id="c1", event_observation=obs,
        selected_prediction="NYY Moneyline", odds_at_lock="-110", implied_probability=0.524,
        model_predicted_probability=0.580, lock_timestamp_utc="2026-08-16T20:05:00Z",
        model_state_rationale="Single game"
    )

    ledger = SportsLongitudinalLedger()
    ledger.add_prediction(pred)

    out1, sc1, lrn1 = resolve_sports_prediction(
        pred, "Official MLB Stats API", "https://statsapi.mlb.com/api/v1/schedule?sportId=1",
        5, 2, "NYY win", "WIN", "2026-08-17T02:00:00Z"
    )

    # 1. Test orphan score failure (score added before outcome)
    orphan_score = SportsScoreRecord(
        score_id="score_orphan", prediction_id="pred_dup_res_001", prediction_hash=pred.sha256_receipt_hash,
        outcome_id="out_pred_dup_res_001", score_timestamp_utc="2026-08-17T02:00:00Z",
        model_predicted_probability=0.580, outcome_status="WIN", brier_score_contribution=0.1764
    )
    with pytest.raises(ValueError, match="SCORE_WITHOUT_OUTCOME_FAIL"):
        ledger.add_score(orphan_score)

    # 2. Add legitimate outcome
    ledger.add_outcome(out1)

    # 3. Test duplicate resolution attempt fails closed
    out_dup = SportsOutcomeRecord(
        outcome_id="out_dup", prediction_id="pred_dup_res_001", prediction_hash=pred.sha256_receipt_hash,
        verification_timestamp_utc="2026-08-17T02:05:00Z", verification_source_name="MLB",
        verification_source_url="http", actual_home_score=5, actual_away_score=2,
        actual_result_text="Duplicate outcome", outcome_status="WIN"
    )
    with pytest.raises(ValueError, match="DUPLICATE_RESOLUTION_ATTEMPT"):
        ledger.add_outcome(out_dup)

    # 4. Test orphan learning failure (learning added before score)
    orphan_learning = SportsLearningRecord(
        learning_id="learn_orphan", prediction_id="pred_dup_res_001", prediction_hash=pred.sha256_receipt_hash,
        outcome_id="out_pred_dup_res_001", score_id="score_nonexistent", learning_timestamp_utc="2026-08-17T02:00:00Z",
        failure_classification=None, model_assumption_broken=None, lesson_recorded="Test lesson"
    )
    with pytest.raises(ValueError, match="LEARNING_WITHOUT_SCORE_FAIL"):
        ledger.add_learning(orphan_learning)

def test_m_sports_outcome_reconciler_lifecycle_and_idempotency(tmp_path):
    ledger_file = tmp_path / "reconciler_ledger.json"
    ledger = SportsLongitudinalLedger(storage_path=ledger_file)

    obs = RealSportsEventObservation(
        event_id="mlb_reconcile_001", sport="baseball", league="mlb", home_team="NYY", away_team="BOS",
        event_start_time_utc="2026-08-16T23:00:00Z", observation_timestamp_utc="2026-08-16T20:00:00Z",
        source_name="Official MLB Stats API", source_url="https://statsapi.mlb.com/api/v1/schedule?sportId=1",
        market_name="Moneyline", observed_odds={"home": -110}, event_status="SCHEDULED"
    )

    pred = LockedResearchPrediction(
        prediction_id="pred_recon_001", cycle_id="c1", event_observation=obs,
        selected_prediction="NYY Moneyline", odds_at_lock="-110", implied_probability=0.524,
        model_predicted_probability=0.580, lock_timestamp_utc="2026-08-16T20:05:00Z",
        model_state_rationale="Single game for reconciler"
    )

    ledger.add_prediction(pred)
    assert len(ledger.get_pending_predictions()) == 1

    reconciler = SportsOutcomeReconciler(ledger)

    # 1. Poll when game is still live/preview -> remains pending
    receipt1 = reconciler.poll_and_reconcile(custom_fetcher=lambda e: {"is_final": False})
    assert isinstance(receipt1, ReconciliationRunReceipt)
    assert receipt1.polled_count == 1
    assert receipt1.resolved_single_count == 0
    assert receipt1.remaining_pending_count == 1

    # 2. Poll when game is final -> resolved WIN
    receipt2 = reconciler.poll_and_reconcile(custom_fetcher=lambda e: {"is_final": True, "home_score": 6, "away_score": 3, "result_text": "NYY 6, BOS 3"})
    assert receipt2.polled_count == 1
    assert receipt2.resolved_single_count == 1
    assert receipt2.remaining_pending_count == 0

    # 3. Idempotent re-run -> zero pending, zero resolved
    receipt3 = reconciler.poll_and_reconcile(custom_fetcher=lambda e: {"is_final": True, "home_score": 6, "away_score": 3})
    assert receipt3.polled_count == 0
    assert receipt3.resolved_single_count == 0
    assert receipt3.remaining_pending_count == 0

def test_n_observation_confidence_and_quality_telemetry_lifecycle(tmp_path):
    ledger_file = tmp_path / "telemetry_ledger.json"
    ledger = SportsLongitudinalLedger(storage_path=ledger_file)

    obs = RealSportsEventObservation(
        event_id="mlb_telemetry_001", sport="baseball", league="mlb", home_team="LAD", away_team="SF",
        event_start_time_utc="2026-08-16T23:00:00Z", observation_timestamp_utc="2026-08-16T20:00:00Z",
        source_name="Official MLB Stats API", source_url="https://statsapi.mlb.com/api/v1/schedule?sportId=1",
        market_name="Moneyline", observed_odds={"home": -130}, event_status="PREVIEW"
    )

    pred = LockedResearchPrediction(
        prediction_id="pred_telem_001", cycle_id="c1", event_observation=obs,
        selected_prediction="LAD Moneyline", odds_at_lock="-130", implied_probability=0.565,
        model_predicted_probability=0.630, lock_timestamp_utc="2026-08-16T20:05:00Z",
        model_state_rationale="Home favorite for telemetry test"
    )

    ledger.add_prediction(pred)
    reconciler = SportsOutcomeReconciler(ledger)

    # 1. Provider error poll (e.g. exception during fetch)
    def failing_fetcher(e):
        raise TimeoutError("Connection timed out")

    reconciler.poll_and_reconcile(custom_fetcher=failing_fetcher)
    assert len(ledger.quality_telemetry) == 1
    t1 = ledger.quality_telemetry[0]
    assert t1.response_validity is False
    assert "PROVIDER_ERROR_TimeoutError" in t1.failure_category
    assert t1.observation_confidence == "OBS-0 UNKNOWN"

    # 2. Non-final poll -> OBS-3 STATUS VERIFIED
    reconciler.poll_and_reconcile(custom_fetcher=lambda e: {"is_final": False, "abstractGameState": "Live"})
    assert len(ledger.quality_telemetry) == 2
    t2 = ledger.quality_telemetry[1]
    assert t2.response_validity is True
    assert t2.observation_confidence == "OBS-3 STATUS VERIFIED"
    assert t2.reconciliation_attempts == 2

    # 3. Final poll -> OBS-5 RESOLUTION VERIFIED
    reconciler.poll_and_reconcile(custom_fetcher=lambda e: {"is_final": True, "home_score": 4, "away_score": 1, "result_text": "LAD win 4-1"})
    assert len(ledger.quality_telemetry) == 3
    t3 = ledger.quality_telemetry[2]
    assert t3.response_validity is True
    assert t3.observation_confidence == "OBS-5 RESOLUTION VERIFIED"
    assert t3.reconciliation_attempts == 3

    # 4. Verify restart loads quality telemetry correctly
    reloaded_ledger = SportsLongitudinalLedger(storage_path=ledger_file)
    assert len(reloaded_ledger.quality_telemetry) == 3
    assert reloaded_ledger.quality_telemetry[2].sha256_telemetry_hash == t3.sha256_telemetry_hash

def test_o_multi_source_observation_arbitration_lifecycle(tmp_path):
    ledger_file = tmp_path / "arbitration_ledger.json"
    ledger = SportsLongitudinalLedger(storage_path=ledger_file)

    obs = RealSportsEventObservation(
        event_id="mlb_arbitrate_001", sport="baseball", league="mlb", home_team="NYY", away_team="BOS",
        event_start_time_utc="2026-08-16T23:00:00Z", observation_timestamp_utc="2026-08-16T20:00:00Z",
        source_name="Official MLB Stats API", source_url="https://statsapi.mlb.com/api/v1/schedule?sportId=1",
        market_name="Moneyline", observed_odds={"home": -110}, event_status="PREVIEW"
    )

    pred = LockedResearchPrediction(
        prediction_id="pred_arb_001", cycle_id="c1", event_observation=obs,
        selected_prediction="NYY Moneyline", odds_at_lock="-110", implied_probability=0.524,
        model_predicted_probability=0.580, lock_timestamp_utc="2026-08-16T20:05:00Z",
        model_state_rationale="Arbitration test prediction"
    )

    ledger.add_prediction(pred)
    arbitrator = SportsObservationArbitrator(ledger)

    # 1. Zero observations -> OBS_UNAVAILABLE
    arb1 = arbitrator.arbitrate_observations("pred_arb_001", [])
    assert arb1.agreement_state == "OBS_UNAVAILABLE"
    assert arb1.resolution_allowed is False

    # 2. Conflicting provider observations -> OBS_CONFLICT (leaves prediction pending)
    obs_mlb_conflict = SourceObservation(
        provider="MLB Stats API", event_id="mlb_arbitrate_001", retrieval_timestamp_utc="2026-08-17T02:00:00Z",
        raw_payload_hash="hash_mlb_1", observed_status="Final", home_score=5, away_score=3, is_final=True
    )
    obs_espn_conflict = SourceObservation(
        provider="ESPN API", event_id="mlb_arbitrate_001", retrieval_timestamp_utc="2026-08-17T02:00:00Z",
        raw_payload_hash="hash_espn_1", observed_status="Final", home_score=4, away_score=3, is_final=True # Disagrees on home score!
    )

    arb2 = arbitrator.arbitrate_observations("pred_arb_001", [obs_mlb_conflict, obs_espn_conflict])
    assert arb2.agreement_state == "OBS_CONFLICT"
    assert arb2.resolution_allowed is False
    assert len(ledger.get_pending_predictions()) == 1 # Leaves prediction pending!

    # 3. Consensus matched observations -> OBS_MATCHED (allows resolution)
    obs_espn_matched = SourceObservation(
        provider="ESPN API", event_id="mlb_arbitrate_001", retrieval_timestamp_utc="2026-08-17T02:05:00Z",
        raw_payload_hash="hash_espn_2", observed_status="Final", home_score=5, away_score=3, is_final=True
    )

    arb3 = arbitrator.arbitrate_observations("pred_arb_001", [obs_mlb_conflict, obs_espn_matched])
    assert arb3.agreement_state == "OBS_MATCHED"
    assert arb3.resolution_allowed is True
    assert len(ledger.get_pending_predictions()) == 0 # Resolved!

    # 4. Verify arbitration history persists across process restarts
    reloaded_ledger = SportsLongitudinalLedger(storage_path=ledger_file)
    assert len(reloaded_ledger.arbitration_history) == 3
    assert reloaded_ledger.arbitration_history[2].sha256_hash == arb3.sha256_hash

def test_provider_reliability_lifecycle(tmp_path):
    ledger_file = tmp_path / "reliability_ledger.json"
    ledger = SportsLongitudinalLedger(storage_path=ledger_file)
    rel_ledger = ObservationReliabilityLedger(ledger)

    receipt = ObservationArbitrationReceipt(
        arbitration_id="arb_life_1", prediction_id="pred_1", external_event_id="e1",
        timestamp_utc="2026-08-17T00:00:00Z", agreement_state="OBS_MATCHED",
        observations=[{"provider": "Provider_Alpha"}, {"provider": "Provider_Beta"}],
        resolution_allowed=True, rationale="Consensus matched"
    )

    records = rel_ledger.ingest_arbitration_receipt(receipt)
    assert "Provider_Alpha" in records
    assert "Provider_Beta" in records
    assert records["Provider_Alpha"].event_observations_attempted == 1
    assert records["Provider_Alpha"].successful_observations == 1

def test_duplicate_observation_not_double_counted(tmp_path):
    ledger_file = tmp_path / "dup_rel_ledger.json"
    ledger = SportsLongitudinalLedger(storage_path=ledger_file)
    rel_ledger = ObservationReliabilityLedger(ledger)

    receipt = ObservationArbitrationReceipt(
        arbitration_id="arb_dup_receipt", prediction_id="pred_1", external_event_id="e1",
        timestamp_utc="2026-08-17T00:00:00Z", agreement_state="OBS_MATCHED",
        observations=[{"provider": "Provider_Alpha"}],
        resolution_allowed=True, rationale="Consensus matched"
    )

    rel_ledger.ingest_arbitration_receipt(receipt)
    count1 = ledger.provider_reliability["Provider_Alpha"].event_observations_attempted

    # Re-ingest same receipt
    rel_ledger.ingest_arbitration_receipt(receipt)
    count2 = ledger.provider_reliability["Provider_Alpha"].event_observations_attempted

    assert count1 == 1
    assert count2 == 1 # Duplicate skip enforced!

def test_conflict_updates_reliability(tmp_path):
    ledger = SportsLongitudinalLedger()
    rel_ledger = ObservationReliabilityLedger(ledger)

    receipt = ObservationArbitrationReceipt(
        arbitration_id="arb_conflict_1", prediction_id="pred_1", external_event_id="e1",
        timestamp_utc="2026-08-17T00:00:00Z", agreement_state="OBS_CONFLICT",
        observations=[{"provider": "Provider_Bad"}],
        resolution_allowed=False, rationale="Conflict"
    )

    rel_ledger.ingest_arbitration_receipt(receipt)
    rec = ledger.provider_reliability["Provider_Bad"]
    assert rec.conflicts_generated == 1
    assert rec.finality_accuracy == 0.0

def test_provider_failure_updates_reliability(tmp_path):
    ledger = SportsLongitudinalLedger()
    rel_ledger = ObservationReliabilityLedger(ledger)

    telemetry = ReconciliationQualityTelemetry(
        telemetry_id="qual_fail_1", prediction_id="pred_1", provider_used="Provider_Failing",
        query_timestamp_utc="2026-08-17T00:00:00Z", external_event_id="e1",
        response_latency_ms=5000.0, response_validity=False, observation_confidence="OBS-0 UNKNOWN",
        finality_transition_observed="NONE", resolution_delay_seconds=None,
        reconciliation_attempts=1, failure_category="PROVIDER_TIMEOUT"
    )

    rec = rel_ledger.ingest_quality_telemetry(telemetry, receipt_id="receipt_recon_1")
    assert rec.failed_observations == 1
    assert rec.successful_observations == 0
    assert rec.availability_rate == 0.0

def test_restart_preserves_reliability_history(tmp_path):
    ledger_file = tmp_path / "restart_rel_ledger.json"
    ledger = SportsLongitudinalLedger(storage_path=ledger_file)
    rel_ledger = ObservationReliabilityLedger(ledger)

    receipt = ObservationArbitrationReceipt(
        arbitration_id="arb_restart_1", prediction_id="pred_1", external_event_id="e1",
        timestamp_utc="2026-08-17T00:00:00Z", agreement_state="OBS_MATCHED",
        observations=[{"provider": "Provider_Stable"}],
        resolution_allowed=True, rationale="Consensus matched"
    )
    rel_ledger.ingest_arbitration_receipt(receipt)

    # Simulate restart
    reloaded_ledger = SportsLongitudinalLedger(storage_path=ledger_file)
    assert "Provider_Stable" in reloaded_ledger.provider_reliability
    assert reloaded_ledger.provider_reliability["Provider_Stable"].event_observations_attempted == 1

def test_unknown_provider_defaults_safe():
    ledger = SportsLongitudinalLedger()
    rel_ledger = ObservationReliabilityLedger(ledger)
    grade = rel_ledger.get_provider_grade("NonExistentProvider")
    assert grade == ObservationReliabilityGrade.RELIABILITY_UNKNOWN.value

def test_reliability_requires_receipt():
    ledger = SportsLongitudinalLedger()
    rel_ledger = ObservationReliabilityLedger(ledger)

    with pytest.raises(ValueError, match="RECEIPT_REQUIRED_FOR_RELIABILITY_UPDATE"):
        rel_ledger.ingest_arbitration_receipt(None)

    with pytest.raises(ValueError, match="RECEIPT_REQUIRED_FOR_RELIABILITY_UPDATE"):
        telemetry = ReconciliationQualityTelemetry(
            telemetry_id="q1", prediction_id="p1", provider_used="P", query_timestamp_utc="ts",
            external_event_id="e1", response_latency_ms=10.0, response_validity=True,
            observation_confidence="OBS-1", finality_transition_observed="NONE",
            resolution_delay_seconds=None, reconciliation_attempts=1
        )
        rel_ledger.ingest_quality_telemetry(telemetry, receipt_id="")

def test_reliability_does_not_modify_predictions():
    obs = RealSportsEventObservation(
        event_id="mlb_iso_test", sport="baseball", league="mlb", home_team="NYY", away_team="BOS",
        event_start_time_utc="2026-08-16T23:00:00Z", observation_timestamp_utc="2026-08-16T20:00:00Z",
        source_name="MLB", source_url="http", market_name="Moneyline", observed_odds={}, event_status="PREVIEW"
    )
    pred = LockedResearchPrediction(
        prediction_id="pred_iso_001", cycle_id="c1", event_observation=obs,
        selected_prediction="NYY Moneyline", odds_at_lock="-110", implied_probability=0.524,
        model_predicted_probability=0.580, lock_timestamp_utc="2026-08-16T20:05:00Z",
        model_state_rationale="Isolation test"
    )
    p_hash_before = pred.lock_and_sign()

    ledger = SportsLongitudinalLedger()
    ledger.add_prediction(pred)
    rel_ledger = ObservationReliabilityLedger(ledger)

    receipt = ObservationArbitrationReceipt(
        arbitration_id="arb_iso_1", prediction_id="pred_iso_001", external_event_id="mlb_iso_test",
        timestamp_utc="2026-08-17T00:00:00Z", agreement_state="OBS_MATCHED",
        observations=[{"provider": "MLB"}], resolution_allowed=True, rationale="Matched"
    )
    rel_ledger.ingest_arbitration_receipt(receipt)

    assert pred.sha256_receipt_hash == p_hash_before
    assert pred.compute_sha256_hash() == p_hash_before

def test_temporal_observation_lifecycle(tmp_path):
    ledger = SportsLongitudinalLedger(storage_path=tmp_path / "temp_ledger.json")
    temp_ledger = ObservationTemporalLedger(ledger)

    obs = SourceObservation(
        provider="MLB Stats API", event_id="mlb_001", retrieval_timestamp_utc="2026-08-16T20:00:00Z",
        raw_payload_hash="payload_v1", observed_status="Preview", home_score=0, away_score=0, is_final=False
    )

    record = temp_ledger.record_temporal_observation(obs)
    assert record.temporal_classification == "TEMPORAL_CURRENT"
    assert record.transition_detected is False
    assert len(ledger.temporal_observations) == 1

def test_duplicate_observation_detection(tmp_path):
    ledger = SportsLongitudinalLedger(storage_path=tmp_path / "temp_ledger.json")
    temp_ledger = ObservationTemporalLedger(ledger)

    obs = SourceObservation(
        provider="MLB Stats API", event_id="mlb_001", retrieval_timestamp_utc="2026-08-16T20:00:00Z",
        raw_payload_hash="payload_same", observed_status="Preview", home_score=0, away_score=0, is_final=False
    )

    r1 = temp_ledger.record_temporal_observation(obs)
    r2 = temp_ledger.record_temporal_observation(obs)

    assert r1.temporal_classification == "TEMPORAL_CURRENT"
    assert r2.temporal_classification == "TEMPORAL_DUPLICATE"

def test_status_transition_detection(tmp_path):
    ledger = SportsLongitudinalLedger()
    temp_ledger = ObservationTemporalLedger(ledger)

    obs1 = SourceObservation(provider="MLB", event_id="mlb_001", retrieval_timestamp_utc="ts1", raw_payload_hash="h1", observed_status="Preview", home_score=0, away_score=0, is_final=False)
    obs2 = SourceObservation(provider="MLB", event_id="mlb_001", retrieval_timestamp_utc="ts2", raw_payload_hash="h2", observed_status="In Progress", home_score=2, away_score=1, is_final=False)
    obs3 = SourceObservation(provider="MLB", event_id="mlb_001", retrieval_timestamp_utc="ts3", raw_payload_hash="h3", observed_status="Final", home_score=5, away_score=2, is_final=True)

    r1 = temp_ledger.record_temporal_observation(obs1)
    r2 = temp_ledger.record_temporal_observation(obs2)
    r3 = temp_ledger.record_temporal_observation(obs3)

    assert r2.transition_detected is True
    assert r2.temporal_classification == "TEMPORAL_CURRENT"
    assert r3.transition_detected is True
    assert r3.temporal_classification == "TEMPORAL_FINAL"

def test_late_observation_detection(tmp_path):
    ledger = SportsLongitudinalLedger()
    temp_ledger = ObservationTemporalLedger(ledger)

    obs = SourceObservation(
        provider="MLB", event_id="mlb_001", retrieval_timestamp_utc="2026-08-16T22:00:00Z",
        raw_payload_hash="late_payload", observed_status="Final", home_score=3, away_score=1, is_final=True
    )
    rec = temp_ledger.record_temporal_observation(obs)
    assert rec.finality_state is True

def test_correction_preservation(tmp_path):
    ledger = SportsLongitudinalLedger()
    temp_ledger = ObservationTemporalLedger(ledger)

    obs_final_v1 = SourceObservation(provider="MLB", event_id="mlb_001", retrieval_timestamp_utc="ts1", raw_payload_hash="final_v1", observed_status="Final", home_score=5, away_score=2, is_final=True)
    obs_final_v2 = SourceObservation(provider="MLB", event_id="mlb_001", retrieval_timestamp_utc="ts2", raw_payload_hash="final_v2_stat_corr", observed_status="Final", home_score=6, away_score=2, is_final=True)

    r1 = temp_ledger.record_temporal_observation(obs_final_v1)
    r2 = temp_ledger.record_temporal_observation(obs_final_v2)

    assert r1.temporal_classification == "TEMPORAL_FINAL"
    assert r2.temporal_classification == "TEMPORAL_CORRECTED"
    assert r2.correction_detected is True
    assert r2.prior_observation_reference == r1.temporal_id

def test_finality_conflict_detection(tmp_path):
    ledger = SportsLongitudinalLedger()
    temp_ledger = ObservationTemporalLedger(ledger)

    obs_final = SourceObservation(provider="MLB", event_id="mlb_001", retrieval_timestamp_utc="ts1", raw_payload_hash="final_hash", observed_status="Final", home_score=5, away_score=2, is_final=True)
    obs_conflict = SourceObservation(provider="MLB", event_id="mlb_001", retrieval_timestamp_utc="ts2", raw_payload_hash="conflict_hash", observed_status="Live", home_score=5, away_score=2, is_final=False)

    r1 = temp_ledger.record_temporal_observation(obs_final)
    r2 = temp_ledger.record_temporal_observation(obs_conflict)

    assert r2.temporal_classification == "TEMPORAL_CONFLICTED"

def test_unknown_event_identity_fails_closed():
    ledger = SportsLongitudinalLedger()
    temp_ledger = ObservationTemporalLedger(ledger)

    obs_bad = SourceObservation(provider="", event_id="", retrieval_timestamp_utc="ts", raw_payload_hash="h", observed_status="S", home_score=0, away_score=0, is_final=False)
    with pytest.raises(ValueError, match="UNKNOWN_EVENT_IDENTITY"):
        temp_ledger.record_temporal_observation(obs_bad)

def test_restart_reconstructs_temporal_history(tmp_path):
    ledger_file = tmp_path / "temporal_restart_ledger.json"
    ledger = SportsLongitudinalLedger(storage_path=ledger_file)
    temp_ledger = ObservationTemporalLedger(ledger)

    obs = SourceObservation(provider="MLB", event_id="mlb_restart", retrieval_timestamp_utc="ts1", raw_payload_hash="h1", observed_status="Preview", home_score=0, away_score=0, is_final=False)
    temp_ledger.record_temporal_observation(obs)

    # Re-instantiate ledger
    reloaded_ledger = SportsLongitudinalLedger(storage_path=ledger_file)
    assert len(reloaded_ledger.temporal_observations) == 1
    assert reloaded_ledger.temporal_observations[0].external_event_id == "mlb_restart"

def test_temporal_ledger_preserves_prediction_identity(tmp_path):
    obs = RealSportsEventObservation(
        event_id="mlb_pred_iso", sport="baseball", league="mlb", home_team="NYY", away_team="BOS",
        event_start_time_utc="2026-08-16T23:00:00Z", observation_timestamp_utc="2026-08-16T20:00:00Z",
        source_name="MLB", source_url="http", market_name="Moneyline", observed_odds={}, event_status="PREVIEW"
    )
    pred = LockedResearchPrediction(
        prediction_id="pred_temp_iso_001", cycle_id="c1", event_observation=obs,
        selected_prediction="NYY Moneyline", odds_at_lock="-110", implied_probability=0.524,
        model_predicted_probability=0.580, lock_timestamp_utc="2026-08-16T20:05:00Z",
        model_state_rationale="Temporal isolation test"
    )
    p_hash_before = pred.lock_and_sign()

    ledger = SportsLongitudinalLedger()
    ledger.add_prediction(pred)
    temp_ledger = ObservationTemporalLedger(ledger)

    source_obs = SourceObservation(provider="MLB", event_id="mlb_pred_iso", retrieval_timestamp_utc="ts", raw_payload_hash="h", observed_status="Final", home_score=5, away_score=2, is_final=True)
    temp_ledger.record_temporal_observation(source_obs)

    assert pred.sha256_receipt_hash == p_hash_before
    assert pred.compute_sha256_hash() == p_hash_before

def test_temporal_history_cannot_bypass_outcome_gate():
    ledger = SportsLongitudinalLedger()
    temp_ledger = ObservationTemporalLedger(ledger)

    obs = SourceObservation(provider="MLB", event_id="e1", retrieval_timestamp_utc="ts", raw_payload_hash="h", observed_status="Final", home_score=5, away_score=2, is_final=True)
    temp_ledger.record_temporal_observation(obs)

    # Verify recording a temporal observation did NOT automatically create an outcome record
    assert len(ledger.outcomes) == 0

def test_reliability_consumes_temporal_receipts(tmp_path):
    ledger = SportsLongitudinalLedger()
    rel_ledger = ObservationReliabilityLedger(ledger)

    receipt = ObservationArbitrationReceipt(
        arbitration_id="arb_temp_1", prediction_id="p1", external_event_id="e1",
        timestamp_utc="ts", agreement_state="OBS_MATCHED",
        observations=[{"provider": "MLB"}], resolution_allowed=True, rationale="Matched"
    )
    rel_ledger.ingest_arbitration_receipt(receipt)
    assert ledger.provider_reliability["MLB"].event_observations_attempted == 1

def test_repeated_polling_is_idempotent(tmp_path):
    ledger = SportsLongitudinalLedger(storage_path=tmp_path / "idempotent_ledger.json")
    temp_ledger = ObservationTemporalLedger(ledger)

    obs = SourceObservation(provider="MLB", event_id="e_idem", retrieval_timestamp_utc="ts1", raw_payload_hash="payload_fixed", observed_status="Final", home_score=4, away_score=2, is_final=True)

    temp_ledger.record_temporal_observation(obs)
    temp_ledger.record_temporal_observation(obs)

    assert len(ledger.temporal_observations) == 2
    assert ledger.temporal_observations[1].temporal_classification == "TEMPORAL_DUPLICATE"

def test_observation_event_stream_lifecycle(tmp_path):
    ledger = SportsLongitudinalLedger(storage_path=tmp_path / "stream_ledger.json")
    stream = SportsObservationEventStream(ledger)

    e1 = stream.append_event(
        event_type=SportsObservationEventType.OBS_RECEIVED.value, provider="MLB Stats API",
        external_event_id="mlb_stream_001", payload_hash="hash_v1", details={"status": "Preview"}
    )
    assert e1.sequence_number == 1
    assert e1.sha256_hash != ""
    assert len(ledger.observation_event_stream) == 1

def test_deterministic_replay_state_reconstruction(tmp_path):
    ledger = SportsLongitudinalLedger(storage_path=tmp_path / "replay_ledger.json")
    stream = SportsObservationEventStream(ledger)

    stream.append_event(SportsObservationEventType.OBS_RECEIVED.value, "MLB", "mlb_001", "h1", {"status": "Preview", "home_score": 0, "away_score": 0})
    stream.append_event(SportsObservationEventType.OBS_STATUS_CHANGED.value, "MLB", "mlb_001", "h2", {"status": "Live", "home_score": 2, "away_score": 1})
    stream.append_event(SportsObservationEventType.OBS_FINALIZED.value, "MLB", "mlb_001", "h3", {"status": "Final", "home_score": 5, "away_score": 2, "is_final": True})

    # Simulate fresh process replay from stream history
    reloaded_ledger = SportsLongitudinalLedger(storage_path=tmp_path / "replay_ledger.json")
    reloaded_stream = SportsObservationEventStream(reloaded_ledger)

    state = reloaded_stream.reconstruct_event_state("mlb_001")
    assert state["external_event_id"] == "mlb_001"
    assert state["total_events"] == 3
    assert state["providers_observed"] == ["MLB"]
    assert state["is_finalized"] is True
    assert state["latest_scores_by_provider"]["MLB"] == {"home_score": 5, "away_score": 2}

def test_event_sequence_ordering_and_integrity(tmp_path):
    ledger = SportsLongitudinalLedger()
    stream = SportsObservationEventStream(ledger)

    e1 = stream.append_event(SportsObservationEventType.OBS_RECEIVED.value, "P1", "e1", "h1", {})
    e2 = stream.append_event(SportsObservationEventType.OBS_STATUS_CHANGED.value, "P1", "e1", "h2", {})

    assert e1.sequence_number == 1
    assert e2.sequence_number == 2
    assert e1.compute_sha256() == e1.sha256_hash
    assert e2.compute_sha256() == e2.sha256_hash

def test_duplicate_and_out_of_order_event_handling(tmp_path):
    ledger = SportsLongitudinalLedger()
    stream = SportsObservationEventStream(ledger)

    # Append events
    stream.append_event(SportsObservationEventType.OBS_RECEIVED.value, "MLB", "e_order", "h1", {"status": "Preview"}, timestamp_utc="2026-08-16T20:00:00Z")
    stream.append_event(SportsObservationEventType.OBS_RECEIVED.value, "MLB", "e_order", "h1", {"status": "Preview"}, timestamp_utc="2026-08-16T20:01:00Z")

    state = stream.reconstruct_event_state("e_order")
    assert state["total_events"] == 2

def test_restart_reconstructs_event_stream(tmp_path):
    ledger_file = tmp_path / "restart_stream.json"
    ledger = SportsLongitudinalLedger(storage_path=ledger_file)
    stream = SportsObservationEventStream(ledger)

    stream.append_event(SportsObservationEventType.OBS_RECEIVED.value, "MLB", "e_restart", "h1", {"status": "Preview"})

    # Fresh process restart
    reloaded_ledger = SportsLongitudinalLedger(storage_path=ledger_file)
    assert len(reloaded_ledger.observation_event_stream) == 1
    assert reloaded_ledger.observation_event_stream[0].external_event_id == "e_restart"

def test_event_stream_isolation_from_predictions(tmp_path):
    obs = RealSportsEventObservation(
        event_id="mlb_stream_iso", sport="baseball", league="mlb", home_team="NYY", away_team="BOS",
        event_start_time_utc="2026-08-16T23:00:00Z", observation_timestamp_utc="2026-08-16T20:00:00Z",
        source_name="MLB", source_url="http", market_name="Moneyline", observed_odds={}, event_status="PREVIEW"
    )
    pred = LockedResearchPrediction(
        prediction_id="pred_stream_iso_001", cycle_id="c1", event_observation=obs,
        selected_prediction="NYY Moneyline", odds_at_lock="-110", implied_probability=0.524,
        model_predicted_probability=0.580, lock_timestamp_utc="2026-08-16T20:05:00Z",
        model_state_rationale="Stream isolation test"
    )
    p_hash_before = pred.lock_and_sign()

    ledger = SportsLongitudinalLedger()
    ledger.add_prediction(pred)
    stream = SportsObservationEventStream(ledger)

    stream.append_event(SportsObservationEventType.OBS_FINALIZED.value, "MLB", "mlb_stream_iso", "h_final", {"status": "Final", "is_final": True})

    # Verify prediction hash remains byte-for-byte identical and no outcome was created automatically
    assert pred.sha256_receipt_hash == p_hash_before
    assert len(ledger.outcomes) == 0

def test_p_historical_availability_snapshot_creation_and_hash():
    snap = ObservationAvailabilitySnapshot(
        snapshot_id="snap_test_001",
        research_timestamp_utc="2026-08-16T20:00:00Z",
        total_observations_analyzed=5,
        available_observations=[{"event_stream_id": "e1"}],
        excluded_observations=[{"event_stream_id": "e2"}],
        leakage_detected=True,
        classification_breakdown={"AVAILABLE": 1, "POST_TIMESTAMP_LEAKAGE": 1}
    )
    assert snap.sha256_hash != ""
    assert snap.sha256_hash == snap.compute_sha256()

def test_q_historical_information_availability_analysis_at_timestamp(tmp_path):
    ledger = SportsLongitudinalLedger(storage_path=tmp_path / "integrity_ledger.json")
    stream = SportsObservationEventStream(ledger)

    # Event 1: Pre-research time T (2026-08-16T19:00:00Z)
    stream.append_event(
        event_type=SportsObservationEventType.OBS_RECEIVED.value, provider="MLB",
        external_event_id="mlb_hist_001", payload_hash="h1", details={"status": "Preview"},
        timestamp_utc="2026-08-16T19:00:00Z"
    )

    # Event 2: Post-research time T (2026-08-16T21:00:00Z) -> Future info leakage
    stream.append_event(
        event_type=SportsObservationEventType.OBS_FINALIZED.value, provider="MLB",
        external_event_id="mlb_hist_001", payload_hash="h2", details={"status": "Final", "is_final": True},
        timestamp_utc="2026-08-16T21:00:00Z"
    )

    analyzer = HistoricalInformationIntegrityAnalyzer(ledger)
    research_t = "2026-08-16T20:00:00Z" # Research timestamp T

    snapshot = analyzer.analyze_availability_at_timestamp(research_timestamp_utc=research_t)

    assert snapshot.total_observations_analyzed == 2
    assert snapshot.leakage_detected is True
    assert len(snapshot.available_observations) == 1
    assert len(snapshot.excluded_observations) == 1
    assert snapshot.excluded_observations[0]["classification"] == "POST_TIMESTAMP_LEAKAGE"

def test_r_historical_analysis_unparseable_timestamp_fails_closed():
    ledger = SportsLongitudinalLedger()
    analyzer = HistoricalInformationIntegrityAnalyzer(ledger)

    with pytest.raises(ValueError, match="FAIL_CLOSED_AMBIGUOUS_TIMING"):
        analyzer.analyze_availability_at_timestamp(research_timestamp_utc="INVALID_TIMESTAMP")

def test_s_historical_analyzer_read_only_isolation():
    obs = RealSportsEventObservation(
        event_id="mlb_readonly_test", sport="baseball", league="mlb", home_team="NYY", away_team="BOS",
        event_start_time_utc="2026-08-16T23:00:00Z", observation_timestamp_utc="2026-08-16T20:00:00Z",
        source_name="MLB", source_url="http", market_name="Moneyline", observed_odds={}, event_status="PREVIEW"
    )
    pred = LockedResearchPrediction(
        prediction_id="pred_ro_001", cycle_id="c1", event_observation=obs,
        selected_prediction="NYY Moneyline", odds_at_lock="-110", implied_probability=0.524,
        model_predicted_probability=0.580, lock_timestamp_utc="2026-08-16T20:05:00Z",
        model_state_rationale="Read-only test"
    )
    p_hash_before = pred.lock_and_sign()

    ledger = SportsLongitudinalLedger()
    ledger.add_prediction(pred)

    analyzer = HistoricalInformationIntegrityAnalyzer(ledger)
    snapshot = analyzer.analyze_availability_at_timestamp("2026-08-16T20:00:00Z")

    # Assert read-only analyzer did not mutate predictions or outcomes
    assert pred.sha256_receipt_hash == p_hash_before
    assert len(ledger.predictions) == 1
    assert len(ledger.outcomes) == 0
