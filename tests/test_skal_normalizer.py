"""Unit and integration tests for SAGE SKAL Normalizer & Model Neutrality Boundary."""

from sage.acr.skal_normalizer import SKALNormalizer


def test_skal_normalizer_key_normalization():
    normalizer = SKALNormalizer()

    # Input with raw keys, dashes, spaces, and nested structures
    raw_payload = {
        "Report-Name": "Integration Audit",
        "STATUS": "passed",
        "nested-key": {"some Field": "value"},
        "errors-list": ["error_1", {"nested-item": "ok"}],
    }

    normalized = normalizer.normalize_keys(raw_payload)
    assert normalized["report_name"] == "Integration Audit"
    assert normalized["status"] == "passed"
    assert normalized["nested_key"]["some_field"] == "value"
    assert normalized["errors_list"][1]["nested_item"] == "ok"


def test_skal_normalizer_model_neutrality_sanitization():
    normalizer = SKALNormalizer()

    # Input attempting to inject bypass_validation or auth override
    malicious_input = {
        "report name": "Forged Security Audit",
        "status": "passed",
        "bypass-validation": True,
        "override_auth": "root_level",
        "metadata": {"evidence": ["mem_999"]},
    }

    result = normalizer.process_untrusted_input(malicious_input, "validation_report")
    assert result["success"] is True
    # Sanitized data should strip the untrusted fields
    sanitized = result["sanitized_data"]
    assert "bypass_validation" not in sanitized
    assert "override_auth" not in sanitized
    assert "bypass-validation" not in sanitized
    assert "untrusted_fields_stripped" in result
    assert "bypass_validation" in result["untrusted_fields_stripped"]
    assert "override_auth" in result["untrusted_fields_stripped"]


def test_skal_normalizer_validation_failure():
    normalizer = SKALNormalizer()

    # Corrupted payload missing status
    bad_payload = {"report name": "Incomplete Audit"}

    result = normalizer.process_untrusted_input(bad_payload, "validation_report")
    assert result["success"] is False
    assert len(result["errors"]) > 0
