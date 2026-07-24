"""SAGE SKAL Normalizer & Model Neutrality Boundary (Gate 2 Prep).

Enforces the Model Neutrality Principle: external models provide untrusted telemetry data;
SAGE validates, normalizes, and governs before routing evidence.
"""

from typing import Dict, Any
from pydantic import ValidationError


class SKALNormalizer:
    """Performs strict normalization, key conversion, and validation of untrusted model inputs."""

    def __init__(self, validation_engine=None):
        self.validation = validation_engine

    def normalize_keys(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert raw dictionary keys with spaces or dashes to standard lowercase snake_case.

        Args:
            raw_data: Raw input dictionary.

        Returns:
            Dictionary with normalized snake_case keys.
        """
        normalized = {}
        for k, v in raw_data.items():
            norm_key = k.replace(" ", "_").replace("-", "_").lower()
            if isinstance(v, dict):
                normalized[norm_key] = self.normalize_keys(v)
            elif isinstance(v, list):
                normalized[norm_key] = [
                    self.normalize_keys(item) if isinstance(item, dict) else item for item in v
                ]
            else:
                normalized[norm_key] = v
        return normalized

    def process_untrusted_input(
        self, raw_input: Dict[str, Any], schema_type: str
    ) -> Dict[str, Any]:
        """Applies Model Neutrality Principle, sanitizes raw AI outputs, and validates against schemas.

        Args:
            raw_input: Raw untrusted JSON payload from external LLM/client.
            schema_type: Target schema type (e.g. "validation_report", "deployment_event", "architecture_decision").

        Returns:
            Dict containing validation status, sanitized data, and evidence tracking results.
        """
        # Step 1. Normalize all keys to standard snake_case
        normalized_data = self.normalize_keys(raw_input)

        # Step 2. Strip any untrusted or injected system flags/bypasses (Epistemic Firewall)
        sanitized = {}
        untrusted_fields_stripped = []
        for k, v in normalized_data.items():
            # Strip injected validation overrides
            if k in ["is_valid", "bypass_validation", "validation_bypass", "override_auth"]:
                untrusted_fields_stripped.append(k)
                continue
            sanitized[k] = v

        # Step 3. Enforce strict schema constraints and validation
        errors = []
        from sage.acr.skal import (
            SKALValidationReport,
            SKALDeploymentEvent,
            SKALArchitectureDecision,
        )

        try:
            if schema_type == "validation_report":
                SKALValidationReport(**sanitized)
            elif schema_type == "deployment_event":
                SKALDeploymentEvent(**sanitized)
            elif schema_type == "architecture_decision":
                SKALArchitectureDecision(**sanitized)
            else:
                errors.append(f"Unknown target schema type: '{schema_type}'")
        except ValidationError as e:
            errors.append(str(e))

        is_valid = len(errors) == 0

        # Step 4. Extract evidence and lineage references
        metadata = sanitized.get("metadata") or {}
        evidence = metadata.get("evidence") or []

        return {
            "success": is_valid,
            "schema_type": schema_type,
            "sanitized_data": sanitized if is_valid else None,
            "errors": errors,
            "evidence_references": list(evidence),
            "untrusted_fields_stripped": untrusted_fields_stripped,
        }
