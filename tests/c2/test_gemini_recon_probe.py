"""Tests for Gemini Recon Node capability probe."""

import os
from unittest.mock import patch
from sage.c2.gemini_recon_probe import GeminiReconProbe, GeminiReconCapabilityReport


def test_gemini_recon_probe_evaluation():
    probe = GeminiReconProbe(repo_dir=".")
    report = probe.evaluate_capability()

    assert isinstance(report, GeminiReconCapabilityReport)
    assert report.can_run_cli is True
    assert report.repo_access_valid is True
    assert "Sage" in report.repo_origin or "sage" in report.repo_origin
    assert report.cli_package_available is True
    assert report.zero_mutation_capable is True
    assert report.is_provisionable() is True


def test_gemini_recon_probe_auth_detection_with_env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test_key_123")
    probe = GeminiReconProbe(repo_dir=".")
    report = probe.evaluate_capability()

    assert report.auth_configured is True
    assert report.auth_method_detected == "GEMINI_API_KEY"
    assert report.interactive_auth_required is False
    assert report.is_fully_executable() is True


def test_gemini_recon_probe_auth_detection_without_env(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_GENAI_USE_VERTEXAI", raising=False)
    monkeypatch.delenv("GOOGLE_GENAI_USE_GCA", raising=False)

    with patch("os.path.exists", return_value=False):
        probe = GeminiReconProbe(repo_dir=".")
        report = probe.evaluate_capability()

        assert report.auth_configured is False
        assert report.auth_method_detected is None
        assert report.interactive_auth_required is True
        assert report.is_fully_executable() is False
        assert report.is_provisionable() is True
