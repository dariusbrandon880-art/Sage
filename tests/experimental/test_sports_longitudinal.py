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
    ReconciliationRunReceipt
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
