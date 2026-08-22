import pytest

from sage.failure_intelligence import (
    FailureObservation,
    RepairQualification,
    collapse,
    failure_fingerprint,
    normalize_failure,
)


def test_normalization_removes_sha_and_numeric_noise():
    assert normalize_failure(" Error 42 at abcdef1234567 ") == "error # at <sha>"


def test_identical_normalized_failures_collapse():
    fingerprint = failure_fingerprint("ruff check", "EXE001 line 12")
    first = FailureObservation(
        fingerprint,
        "ruff check",
        "EXE001 line 12",
        "a" * 40,
        "F1",
        1,
    )
    second = FailureObservation(
        fingerprint,
        "ruff check",
        "EXE001 line 99",
        "b" * 40,
        "F4",
        1,
    )
    assert list(collapse([first, second]).values())[0] == (first, second)


def test_zero_exit_cannot_be_recorded_as_failure():
    fingerprint = failure_fingerprint("pytest", "boom")
    with pytest.raises(ValueError):
        FailureObservation(fingerprint, "pytest", "boom", "a" * 40, "F1", 0)


def test_repair_requires_descendant_evidence():
    fingerprint = failure_fingerprint("pytest", "boom")
    with pytest.raises(ValueError):
        RepairQualification(fingerprint, "a" * 40, "a" * 40, True, "run/1")


def test_invalid_inputs_fail_closed():
    with pytest.raises(ValueError):
        normalize_failure("   ")
    with pytest.raises(ValueError):
        failure_fingerprint("", "boom")
