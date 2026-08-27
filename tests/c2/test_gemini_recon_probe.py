"""Tests for Gemini Recon Node capability probe."""

from unittest.mock import patch

from sage.c2.gemini_recon_probe import GeminiReconCapabilityReport, GeminiReconProbe


def _probe_with_controlled_capabilities(**overrides):
    """Return a probe with deterministic capability-boundary checks."""
    probe = GeminiReconProbe(repo_dir=".")
    defaults = {
        "_check_cli_execution": True,
        "_check_repo_access": (True, "https://github.com/dariusbrandon880-art/Sage.git"),
        "_check_gemini_cli_availability": (False, True),
        "_check_zero_mutation_capability": True,
    }
    defaults.update(overrides)
    return probe, defaults


def test_gemini_recon_probe_evaluation():
    probe, capabilities = _probe_with_controlled_capabilities()
    with (
        patch.object(probe, "_check_cli_execution", return_value=capabilities["_check_cli_execution"]),
        patch.object(probe, "_check_repo_access", return_value=capabilities["_check_repo_access"]),
        patch.object(
            probe,
            "_check_gemini_cli_availability",
            return_value=capabilities["_check_gemini_cli_availability"],
        ),
        patch.object(
            probe,
            "_check_zero_mutation_capability",
            return_value=capabilities["_check_zero_mutation_capability"],
        ),
    ):
        report = probe.evaluate_capability()

    assert isinstance(report, GeminiReconCapabilityReport)
    assert report.can_run_cli is True
    assert report.repo_access_valid is True
    assert report.repo_origin.endswith("/Sage.git")
    assert report.cli_package_available is True
    assert report.cli_installed is False
    assert report.zero_mutation_capable is True
    assert report.is_provisionable() is True


def test_gemini_recon_probe_auth_detection_with_env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test_key_123")
    probe, capabilities = _probe_with_controlled_capabilities()
    with (
        patch.object(probe, "_check_cli_execution", return_value=capabilities["_check_cli_execution"]),
        patch.object(probe, "_check_repo_access", return_value=capabilities["_check_repo_access"]),
        patch.object(
            probe,
            "_check_gemini_cli_availability",
            return_value=capabilities["_check_gemini_cli_availability"],
        ),
        patch.object(
            probe,
            "_check_zero_mutation_capability",
            return_value=capabilities["_check_zero_mutation_capability"],
        ),
    ):
        report = probe.evaluate_capability()

    assert report.auth_configured is True
    assert report.auth_method_detected == "GEMINI_API_KEY"
    assert report.interactive_auth_required is False
    assert report.is_fully_executable() is True


def test_gemini_recon_probe_auth_detection_without_env(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_GENAI_USE_VERTEXAI", raising=False)
    monkeypatch.delenv("GOOGLE_GENAI_USE_GCA", raising=False)

    probe, capabilities = _probe_with_controlled_capabilities()
    with (
        patch("os.path.exists", return_value=False),
        patch.object(probe, "_check_cli_execution", return_value=capabilities["_check_cli_execution"]),
        patch.object(probe, "_check_repo_access", return_value=capabilities["_check_repo_access"]),
        patch.object(
            probe,
            "_check_gemini_cli_availability",
            return_value=capabilities["_check_gemini_cli_availability"],
        ),
        patch.object(
            probe,
            "_check_zero_mutation_capability",
            return_value=capabilities["_check_zero_mutation_capability"],
        ),
    ):
        report = probe.evaluate_capability()

    assert report.auth_configured is False
    assert report.auth_method_detected is None
    assert report.interactive_auth_required is True
    assert report.is_fully_executable() is False
    assert report.is_provisionable() is True
