"""External Remote Flight Client for SAGE AIET Validation Lab.

Communicates with an out-of-process external AIET harness deployment.
Enforces fail-closed rules: refuses fixture fallbacks, validates cryptographic receipt proof
hashes, and requires explicit environment credential injection.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict, Optional, Tuple

from pydantic import BaseModel, Field

from sage.c2.mission_contract import MissionContract
from sage.experimental.aiet.receipt import AIETValidationReceipt


class AIETProviderConfig(BaseModel):
    """Configuration abstraction for external model provider execution."""

    provider_name: str = Field(..., description="Provider identifier (e.g. openai, gemini, anthropic, local)")
    model_name: str = Field(..., description="Exact model name string (e.g. gpt-4o, gemini-1.5-pro)")
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    provider_version: Optional[str] = Field(default=None)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AIETExternalClientError(Exception):
    """Base exception for AIET external flight client errors."""

    pass


class AIETExternalClient:
    """Client for out-of-process external AIET validation harness endpoints."""

    def __init__(
        self,
        harness_url: Optional[str] = None,
        harness_key: Optional[str] = None,
        timeout_sec: float = 30.0,
    ) -> None:
        self.harness_url = (harness_url or os.environ.get("SAGE_AIET_EXTERNAL_HARNESS_URL", "")).rstrip("/")
        self.harness_key = harness_key or os.environ.get("SAGE_AIET_EXTERNAL_HARNESS_KEY", "")
        self.timeout_sec = max(1.0, float(timeout_sec))

    def is_configured(self) -> bool:
        """Return True if both external harness URL and harness key are provisioned."""
        return bool(self.harness_url and self.harness_key)

    def _require_configuration(self) -> Tuple[str, str]:
        """Fail closed if external harness URL or key are missing."""
        if not self.harness_url or not self.harness_key:
            raise AIETExternalClientError(
                "EXTERNAL_HARNESS_NOT_CONFIGURED: SAGE_AIET_EXTERNAL_HARNESS_URL and "
                "SAGE_AIET_EXTERNAL_HARNESS_KEY must be set in environment or constructor"
            )
        return self.harness_url, self.harness_key

    def initiate_flight(
        self,
        mission_contract: MissionContract,
        provider_config: AIETProviderConfig,
        execution_mode: str = "external",
        target_git_head_sha: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Initiate an external validation flight on the remote harness."""
        if execution_mode == "fixture":
            raise AIETExternalClientError(
                "INVALID_EXECUTION_MODE: AIETExternalClient refuses execution_mode='fixture'"
            )

        harness_url, harness_key = self._require_configuration()
        endpoint = f"{harness_url}/aiet/v1/trials/initiate"

        payload = {
            "mission_contract": {
                "schema_version": "1.0",
                "mission_id": mission_contract.mission_id,
                "intent": mission_contract.intent,
                "authority_boundary": {
                    "allowed_paths": list(mission_contract.allowed_paths),
                    "prohibited_paths": list(mission_contract.prohibited_paths),
                },
                "completion_criteria": {
                    "required_tests": list(mission_contract.required_tests),
                    "min_coverage_pct": mission_contract.min_coverage_pct,
                    "provenance_required": mission_contract.provenance_required,
                },
                "stop_the_line_conditions": list(mission_contract.stop_the_line_conditions),
                "metadata": dict(mission_contract.metadata),
            },
            "provider_config": provider_config.model_dump(),
            "execution_mode": execution_mode,
            "target_git_head_sha": target_git_head_sha,
        }

        req_data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "X-AIET-Harness-Key": harness_key,
            "User-Agent": "SAGE-AIET-ExternalClient/1.0",
        }

        req = urllib.request.Request(endpoint, data=req_data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if not isinstance(data, dict):
                    raise AIETExternalClientError("MALFORMED_RESPONSE: Harness did not return a JSON object")
                return data
        except urllib.error.HTTPError as err:
            body = err.read().decode("utf-8", errors="replace")
            raise AIETExternalClientError(f"HTTP_ERROR:{err.code}: {body}") from err
        except urllib.error.URLError as err:
            raise AIETExternalClientError(f"CONNECTION_ERROR: {err.reason}") from err
        except Exception as err:
            raise AIETExternalClientError(f"UNEXPECTED_CLIENT_ERROR: {err}") from err

    def execute_flight(self, flight_id: str) -> AIETValidationReceipt:
        """Execute the five frozen trial phases on the remote harness and return validated receipt."""
        harness_url, harness_key = self._require_configuration()
        endpoint = f"{harness_url}/aiet/v1/trials/execute"

        payload = {"flight_id": flight_id}
        req_data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "X-AIET-Harness-Key": harness_key,
            "User-Agent": "SAGE-AIET-ExternalClient/1.0",
        }

        req = urllib.request.Request(endpoint, data=req_data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:
                raw_data = json.loads(resp.read().decode("utf-8"))
                return self.validate_remote_receipt(raw_data)
        except urllib.error.HTTPError as err:
            body = err.read().decode("utf-8", errors="replace")
            raise AIETExternalClientError(f"HTTP_ERROR:{err.code}: {body}") from err
        except urllib.error.URLError as err:
            raise AIETExternalClientError(f"CONNECTION_ERROR: {err.reason}") from err
        except Exception as err:
            if isinstance(err, AIETExternalClientError):
                raise
            raise AIETExternalClientError(f"UNEXPECTED_CLIENT_ERROR: {err}") from err

    def fetch_receipt(self, flight_id: str) -> AIETValidationReceipt:
        """Fetch and validate a previously generated external validation receipt."""
        harness_url, harness_key = self._require_configuration()
        endpoint = f"{harness_url}/aiet/v1/trials/receipt/{flight_id}"

        headers = {
            "X-AIET-Harness-Key": harness_key,
            "User-Agent": "SAGE-AIET-ExternalClient/1.0",
        }

        req = urllib.request.Request(endpoint, headers=headers, method="GET")

        try:
            with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:
                raw_data = json.loads(resp.read().decode("utf-8"))
                return self.validate_remote_receipt(raw_data)
        except urllib.error.HTTPError as err:
            body = err.read().decode("utf-8", errors="replace")
            raise AIETExternalClientError(f"HTTP_ERROR:{err.code}: {body}") from err
        except urllib.error.URLError as err:
            raise AIETExternalClientError(f"CONNECTION_ERROR: {err.reason}") from err
        except Exception as err:
            if isinstance(err, AIETExternalClientError):
                raise
            raise AIETExternalClientError(f"UNEXPECTED_CLIENT_ERROR: {err}") from err

    @staticmethod
    def validate_remote_receipt(
        receipt_payload: Dict[str, Any],
        expected_target_sha: Optional[str] = None,
    ) -> AIETValidationReceipt:
        """Validate proof hashes, isolation status, and integrity rules of a remote receipt."""
        if not isinstance(receipt_payload, dict):
            raise AIETExternalClientError("MALFORMED_RECEIPT: Payload must be a dictionary")

        try:
            receipt = AIETValidationReceipt(**receipt_payload)
        except Exception as err:
            raise AIETExternalClientError(f"RECEIPT_SCHEMA_ERROR: {err}") from err

        if receipt.execution_mode == "fixture":
            raise AIETExternalClientError(
                "INVALID_EXTERNAL_RECEIPT: Remote receipt claims execution_mode='fixture'"
            )

        if receipt.human_intervention_count > 0 and receipt.overall_verdict != "INVALID_EXPERIMENT":
            raise AIETExternalClientError(
                "HUMAN_INTERVENTION_VIOLATION: Human interventions detected but verdict is not INVALID_EXPERIMENT"
            )

        computed_hash = receipt.compute_hash()
        if receipt.evidence_proof_hash and receipt.evidence_proof_hash != computed_hash:
            raise AIETExternalClientError(
                f"RECEIPT_HASH_MISMATCH: Computed proof hash ({computed_hash}) does not match "
                f"evidence_proof_hash ({receipt.evidence_proof_hash})"
            )

        if len(receipt.git_head_sha) != 40 or receipt.git_head_sha == "0" * 40:
            raise AIETExternalClientError(
                f"INVALID_GIT_HEAD_SHA: Receipt git_head_sha is invalid ({receipt.git_head_sha})"
            )

        if expected_target_sha and receipt.git_head_sha != expected_target_sha:
            raise AIETExternalClientError(
                f"TARGET_GIT_SHA_MISMATCH: Receipt git_head_sha ({receipt.git_head_sha}) "
                f"does not match expected target SHA ({expected_target_sha})"
            )

        return receipt
