"""Executable test suite for Stage 2.2 PreRecordedPredictionValidator."""

import json
import subprocess
import sys
import pytest
from sage.experimental.act.phase_4_eval import (
    EvaluationClassification,
    LearningIntervention,
    PostExecutionObservation,
    PreExecutionBaseline,
    PreRecordedPredictionValidator,
    PreRecordedPredictionValidatorResult,
)


VALID_SHA_1 = "a" * 64
VALID_SHA_2 = "b" * 64
VALID_SHA_3 = "c" * 64


def make_valid_triplet(
    baseline_score: float = 0.80,
    observed_score: float = 0.90,
    t_base: float = 1000.0,
    t_inter: float = 2000.0,
    t_obs: float = 3000.0,
    fixture_id: str = "fix_101",
    fixture_hash: str = "hash_fix_101",
    baseline_sha: str = VALID_SHA_1,
    receipt_sha: str = VALID_SHA_2,
):
    b = PreExecutionBaseline(
        fixture_id=fixture_id,
        fixture_hash=fixture_hash,
        baseline_sha256=baseline_sha,
        baseline_score=baseline_score,
        timestamp=t_base,
    )
    i = LearningIntervention(
        fixture_id=fixture_id,
        intervention_id="int_01",
        learning_signal_hash=VALID_SHA_3,
        timestamp=t_inter,
    )
    o = PostExecutionObservation(
        fixture_id=fixture_id,
        fixture_hash=fixture_hash,
        receipt_sha256=receipt_sha,
        observed_score=observed_score,
        timestamp=t_obs,
    )
    return b, i, o


# --- VALID TESTS ---

def test_valid_positive_delta_improvement():
    """Positive delta (> epsilon) produces VALID_IMPROVEMENT."""
    b, i, o = make_valid_triplet(baseline_score=0.70, observed_score=0.85)
    res = PreRecordedPredictionValidator.evaluate(b, i, o, epsilon=1e-4)

    assert res.is_valid is True
    assert res.classification == EvaluationClassification.VALID_IMPROVEMENT
    assert pytest.approx(res.delta_score, abs=1e-6) == 0.15
    assert len(res.rejection_reasons) == 0


def test_valid_negative_delta_regression():
    """Negative delta (<-epsilon) produces VALID_REGRESSION."""
    b, i, o = make_valid_triplet(baseline_score=0.85, observed_score=0.70)
    res = PreRecordedPredictionValidator.evaluate(b, i, o, epsilon=1e-4)

    assert res.is_valid is True
    assert res.classification == EvaluationClassification.VALID_REGRESSION
    assert pytest.approx(res.delta_score, abs=1e-6) == -0.15
    assert len(res.rejection_reasons) == 0


def test_valid_zero_delta_neutral():
    """Zero delta produces VALID_NEUTRAL."""
    b, i, o = make_valid_triplet(baseline_score=0.80, observed_score=0.80)
    res = PreRecordedPredictionValidator.evaluate(b, i, o, epsilon=1e-4)

    assert res.is_valid is True
    assert res.classification == EvaluationClassification.VALID_NEUTRAL
    assert pytest.approx(res.delta_score, abs=1e-6) == 0.0
    assert len(res.rejection_reasons) == 0


def test_valid_epsilon_boundaries():
    """Boundary test around epsilon threshold."""
    eps = 1e-4

    # Exactly +epsilon -> NEUTRAL
    b1, i1, o1 = make_valid_triplet(baseline_score=0.50, observed_score=0.50 + eps)
    r1 = PreRecordedPredictionValidator.evaluate(b1, i1, o1, epsilon=eps)
    assert r1.classification == EvaluationClassification.VALID_NEUTRAL

    # > +epsilon -> IMPROVEMENT
    b2, i2, o2 = make_valid_triplet(baseline_score=0.50, observed_score=0.50 + eps + 1e-6)
    r2 = PreRecordedPredictionValidator.evaluate(b2, i2, o2, epsilon=eps)
    assert r2.classification == EvaluationClassification.VALID_IMPROVEMENT

    # Exactly -epsilon -> NEUTRAL
    b3, i3, o3 = make_valid_triplet(baseline_score=0.50, observed_score=0.50 - eps)
    r3 = PreRecordedPredictionValidator.evaluate(b3, i3, o3, epsilon=eps)
    assert r3.classification == EvaluationClassification.VALID_NEUTRAL

    # < -epsilon -> REGRESSION
    b4, i4, o4 = make_valid_triplet(baseline_score=0.50, observed_score=0.50 - eps - 1e-6)
    r4 = PreRecordedPredictionValidator.evaluate(b4, i4, o4, epsilon=eps)
    assert r4.classification == EvaluationClassification.VALID_REGRESSION


# --- INVALID TESTS ---

def test_invalid_fixture_id_mismatch():
    """Fixture ID mismatch across baseline/intervention/observation fails validation."""
    b, i, o = make_valid_triplet()
    i.fixture_id = "fix_999_mismatch"

    res = PreRecordedPredictionValidator.evaluate(b, i, o)

    assert res.is_valid is False
    assert res.classification == EvaluationClassification.INVALID_EVALUATION
    assert any("Fixture ID mismatch" in reason for reason in res.rejection_reasons)


def test_invalid_fixture_hash_mismatch():
    """Fixture hash mismatch between baseline and observation fails validation."""
    b, i, o = make_valid_triplet()
    o.fixture_hash = "hash_tampered_fix"

    res = PreRecordedPredictionValidator.evaluate(b, i, o)

    assert res.is_valid is False
    assert res.classification == EvaluationClassification.INVALID_EVALUATION
    assert any("Fixture hash mismatch" in reason for reason in res.rejection_reasons)


def test_invalid_temporal_baseline_equal_intervention():
    """Baseline timestamp == intervention timestamp fails validation."""
    b, i, o = make_valid_triplet(t_base=1000.0, t_inter=1000.0, t_obs=2000.0)

    res = PreRecordedPredictionValidator.evaluate(b, i, o)

    assert res.is_valid is False
    assert res.classification == EvaluationClassification.INVALID_EVALUATION
    assert any("baseline timestamp" in reason for reason in res.rejection_reasons)


def test_invalid_temporal_baseline_greater_than_intervention():
    """Baseline timestamp > intervention timestamp fails validation."""
    b, i, o = make_valid_triplet(t_base=2500.0, t_inter=2000.0, t_obs=3000.0)

    res = PreRecordedPredictionValidator.evaluate(b, i, o)

    assert res.is_valid is False
    assert res.classification == EvaluationClassification.INVALID_EVALUATION
    assert any("baseline timestamp" in reason for reason in res.rejection_reasons)


def test_invalid_temporal_intervention_equal_observation():
    """Intervention timestamp == observation timestamp fails validation."""
    b, i, o = make_valid_triplet(t_base=1000.0, t_inter=2000.0, t_obs=2000.0)

    res = PreRecordedPredictionValidator.evaluate(b, i, o)

    assert res.is_valid is False
    assert res.classification == EvaluationClassification.INVALID_EVALUATION
    assert any("intervention timestamp" in reason for reason in res.rejection_reasons)


def test_invalid_temporal_intervention_greater_than_observation():
    """Intervention timestamp > observation timestamp fails validation."""
    b, i, o = make_valid_triplet(t_base=1000.0, t_inter=3500.0, t_obs=3000.0)

    res = PreRecordedPredictionValidator.evaluate(b, i, o)

    assert res.is_valid is False
    assert res.classification == EvaluationClassification.INVALID_EVALUATION
    assert any("intervention timestamp" in reason for reason in res.rejection_reasons)


def test_invalid_empty_baseline_sha():
    """Empty baseline SHA-256 string fails validation."""
    b, i, o = make_valid_triplet(baseline_sha="")

    res = PreRecordedPredictionValidator.evaluate(b, i, o)

    assert res.is_valid is False
    assert res.classification == EvaluationClassification.INVALID_EVALUATION
    assert any("Invalid baseline_sha256" in reason for reason in res.rejection_reasons)


def test_invalid_malformed_baseline_sha():
    """Malformed (short/non-hex) baseline SHA-256 string fails validation."""
    b, i, o = make_valid_triplet(baseline_sha="not_a_sha256_hash")

    res = PreRecordedPredictionValidator.evaluate(b, i, o)

    assert res.is_valid is False
    assert res.classification == EvaluationClassification.INVALID_EVALUATION
    assert any("Invalid baseline_sha256" in reason for reason in res.rejection_reasons)


def test_invalid_empty_receipt_sha():
    """Empty receipt SHA-256 string fails validation."""
    b, i, o = make_valid_triplet(receipt_sha="")

    res = PreRecordedPredictionValidator.evaluate(b, i, o)

    assert res.is_valid is False
    assert res.classification == EvaluationClassification.INVALID_EVALUATION
    assert any("Invalid receipt_sha256" in reason for reason in res.rejection_reasons)


def test_invalid_malformed_receipt_sha():
    """Malformed receipt SHA-256 string fails validation."""
    b, i, o = make_valid_triplet(receipt_sha="abc123_invalid_len")

    res = PreRecordedPredictionValidator.evaluate(b, i, o)

    assert res.is_valid is False
    assert res.classification == EvaluationClassification.INVALID_EVALUATION
    assert any("Invalid receipt_sha256" in reason for reason in res.rejection_reasons)


# --- CROSS-PROCESS SERIALIZATION TEST ---

def test_cross_process_serialization_and_reconstruction():
    """Serialize triplet & result to JSON, deserialize in fresh Python subprocess, and assert identical classification and delta."""
    b, i, o = make_valid_triplet(baseline_score=0.65, observed_score=0.88)
    expected_res = PreRecordedPredictionValidator.evaluate(b, i, o)

    payload = {
        "baseline": b.to_dict(),
        "intervention": i.to_dict(),
        "observation": o.to_dict(),
        "expected_result": expected_res.to_dict(),
    }

    serialized_json = json.dumps(payload)

    python_code = f"""
import sys
import json
from sage.experimental.act.phase_4_eval import (
    PreExecutionBaseline,
    LearningIntervention,
    PostExecutionObservation,
    PreRecordedPredictionValidator,
    PreRecordedPredictionValidatorResult,
)

raw = json.loads('''{serialized_json}''')
b = PreExecutionBaseline.from_dict(raw['baseline'])
i = LearningIntervention.from_dict(raw['intervention'])
o = PostExecutionObservation.from_dict(raw['observation'])

res = PreRecordedPredictionValidator.evaluate(b, i, o)

expected = PreRecordedPredictionValidatorResult.from_dict(raw['expected_result'])

assert res.classification == expected.classification, f"Class mismatch: {{res.classification}} != {{expected.classification}}"
assert abs(res.delta_score - expected.delta_score) < 1e-6, f"Delta mismatch: {{res.delta_score}} != {{expected.delta_score}}"
assert res.is_valid == expected.is_valid
assert res.fixture_id == expected.fixture_id
print("CROSS_PROCESS_SUCCESS")
"""

    proc = subprocess.run(
        [sys.executable, "-c", python_code],
        capture_output=True,
        text=True,
        check=True,
    )

    assert "CROSS_PROCESS_SUCCESS" in proc.stdout
