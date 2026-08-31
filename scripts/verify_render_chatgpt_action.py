#!/usr/bin/env python3
"""Fail-closed live Render/ChatGPT Action verification tool."""

import json
import os
import sys
import time
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _configured_api_key(explicit_key: str | None) -> str | None:
    if explicit_key:
        return explicit_key.strip() or None
    configured = os.getenv("SAGE_API_KEYS", "").split(",")[0].strip()
    return configured or None


def verify_render_chatgpt_action(
    base_url: str | None = None,
    api_key: str | None = None,
    target_root: Path | None = None,
):
    root = Path(target_root) if target_root else PROJECT_ROOT
    base_url = (base_url or os.getenv("SAGE_RENDER_URL") or os.getenv("RENDER_EXTERNAL_URL") or "").rstrip("/")
    api_key = _configured_api_key(api_key)

    if not base_url:
        raise ValueError("SAGE_RENDER_URL or an explicit base_url is required for live verification")
    if not api_key:
        raise ValueError("An explicit API key is required; refusing to invent credentials")
    if not base_url.startswith("https://") and not base_url.startswith("http://localhost"):
        raise ValueError("Live verification requires an HTTPS target")

    import httpx

    results = {}
    verification_passed = True

    def get(path: str, headers=None):
        return httpx.get(f"{base_url}{path}", headers=headers, timeout=10.0)

    def post(path: str, payload, headers=None):
        return httpx.post(f"{base_url}{path}", json=payload, headers=headers, timeout=30.0)

    # Public readiness/schema surfaces.
    try:
        r = get("/health")
        results["health"] = {"status_code": r.status_code, "passed": r.status_code == 200}
        verification_passed &= r.status_code == 200
    except Exception as exc:
        results["health"] = {"status_code": 0, "error": str(exc), "passed": False}
        verification_passed = False

    try:
        r = get("/openapi.json")
        valid = False
        if r.status_code == 200:
            try:
                schema = r.json()
                valid = isinstance(schema, dict) and isinstance(schema.get("paths"), dict)
            except ValueError:
                valid = False
        results["openapi"] = {"status_code": r.status_code, "passed": valid}
        verification_passed &= valid
    except Exception as exc:
        results["openapi"] = {"status_code": 0, "error": str(exc), "passed": False}
        verification_passed = False

    headers = {"x-api-key": api_key}

    try:
        r = get("/status", headers=headers)
        results["status"] = {
            "status_code": r.status_code,
            "passed": r.status_code == 200,
        }
        verification_passed &= r.status_code == 200
    except Exception as exc:
        results["status"] = {"status_code": 0, "error": str(exc), "passed": False}
        verification_passed = False

    # A governed activation receipt requires an actual successful request, not merely reachability.
    try:
        payload = {
            "prompt": "Verify SAGE ChatGPT Action Runtime Handshake",
            "agent_id": "[SAGE::C2::CHATGPT]",
        }
        r = post("/ai/query/chatgpt", payload, headers=headers)
        response = None
        try:
            response = r.json()
        except ValueError:
            response = None
        governed = (
            r.status_code == 200
            and isinstance(response, dict)
            and bool(response.get("evidence") or response.get("receipt") or response.get("live_operation_receipt"))
        )
        results["ai_query_chatgpt"] = {
            "status_code": r.status_code,
            "passed": governed,
            "response_keys": sorted(response.keys()) if isinstance(response, dict) else [],
        }
        verification_passed &= governed
    except Exception as exc:
        results["ai_query_chatgpt"] = {"status_code": 0, "error": str(exc), "passed": False}
        verification_passed = False

    evidence = {
        "receipt_id": f"RECEIPT-RENDER-ACTION-{uuid.uuid4().hex[:8].upper()}",
        "timestamp": time.time(),
        "target_url": base_url,
        "verification_passed": verification_passed,
        "endpoint_results": results,
        "credentials_configured": True,
        "action_configuration_status": "CONNECTED_AND_GOVERNED" if verification_passed else "UNBRIDGED_HOST_SESSION",
        "fail_closed": not verification_passed,
    }

    evidence_file = root / "evidence_capture" / "render_chatgpt_action_verification.json"
    evidence_file.parent.mkdir(parents=True, exist_ok=True)
    evidence_file.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    return evidence


if __name__ == "__main__":
    url_arg = sys.argv[1] if len(sys.argv) > 1 else None
    key_arg = sys.argv[2] if len(sys.argv) > 2 else None
    print(json.dumps(verify_render_chatgpt_action(url_arg, key_arg), indent=2))
