"""Unit and integration tests for the Authorized Tool Bridge Foundation."""

import pytest
from sage.runtime import SageRuntime
from sage.acr.tool_bridge import (
    validate_tool_payload,
    classify_trust_level,
    get_repository_state,
    get_build_status,
    get_test_results,
    submit_validation_event,
    TrustLevel,
    InvalidPayloadError,
    ToolPayload,
)


def test_validate_tool_payload_valid():
    """Verify schema validation accepts a complete, well-formed payload."""
    payload_dict = {
        "source": "github",
        "event_type": "build_status",
        "data": {"status": "success", "duration_sec": 42},
        "metadata": {"commit_sha": "abc123def", "author": "jules"},
        "signature": "sha256=abcdef",
    }
    payload = validate_tool_payload(payload_dict)
    assert isinstance(payload, ToolPayload)
    assert payload.source == "github"
    assert payload.event_type == "build_status"
    assert payload.data["status"] == "success"
    assert payload.metadata["author"] == "jules"
    assert payload.signature == "sha256=abcdef"


def test_validate_tool_payload_invalid():
    """Verify schema validation rejects malformed payloads and raises InvalidPayloadError."""
    # Missing required 'source' and 'event_type' fields
    payload_dict = {
        "data": {"status": "success"},
    }
    with pytest.raises(InvalidPayloadError) as exc_info:
        validate_tool_payload(payload_dict)
    assert "Schema validation failed" in str(exc_info.value)


def test_classify_trust_level_fully_trusted():
    """Verify that cryptographically signed payloads are classified as FULLY_TRUSTED."""
    payload = ToolPayload(
        source="mcp", event_type="test_run", data={"tests": "passed"}, signature="mcp-authenticated"
    )
    assert classify_trust_level(payload) == TrustLevel.FULLY_TRUSTED

    payload_sig = ToolPayload(
        source="github", event_type="push", signature="sha256=verified_hmac_hash"
    )
    assert classify_trust_level(payload_sig) == TrustLevel.FULLY_TRUSTED


def test_classify_trust_level_metadata_verified():
    """Verify that payloads with complete context tracking parameters are classified as METADATA_VERIFIED."""
    payload = ToolPayload(
        source="ci",
        event_type="build_status",
        metadata={"author": "developer_alpha", "commit_sha": "xyz987"},
    )
    assert classify_trust_level(payload) == TrustLevel.METADATA_VERIFIED


def test_classify_trust_level_untrusted():
    """Verify that payloads with missing verification data remain UNTRUSTED."""
    payload = ToolPayload(source="render", event_type="deploy")
    assert classify_trust_level(payload) == TrustLevel.UNTRUSTED


def test_get_repository_state():
    """Verify repository git status retrieval runs and falls back gracefully."""
    state = get_repository_state()
    assert "is_git" in state
    assert "status" in state
    assert "uncommitted_changes" in state
    assert "diff_summary" in state


def test_get_build_status():
    """Verify build status retrieval checks the environment and package layout."""
    status = get_build_status()
    assert "build_status" in status
    assert "pyproject_found" in status
    assert status["pyproject_found"] is True


def test_get_test_results():
    """Verify test results scanner lists Python test files in the test directory."""
    results = get_test_results()
    assert "status" in results
    assert "test_files_count" in results
    assert results["test_files_count"] > 0
    assert "test_tool_bridge.py" in results["test_files"]


def test_submit_validation_event_integration():
    """Verify that submitting an event routes through the bridge, classifies trust, preserves evidence, and ingests into ACR."""
    runtime = SageRuntime()
    runtime.start()

    payload_dict = {
        "source": "github",
        "event_type": "release_published",
        "data": {"tag": "v1.1.0-prod", "changelog": "Hardened deployment pipelines"},
        "metadata": {"author": "jules", "ref": "refs/tags/v1.1.0-prod"},
        "signature": "sha256=verified_release_signature",
    }

    result = submit_validation_event(payload_dict, runtime)
    assert result["status"] == "success"
    assert result["trust_level"] == "fully_trusted"
    assert result["payload_validated"] is True

    # Verify ingestion results
    ingest_res = result["ingest_result"]
    assert ingest_res["status"] == "success"
    assert "session_id" in ingest_res

    # Verify context and memory storage has stored the event and preserved evidence lineage
    memories = runtime.memory.list_all()
    # Find the ingested memory for this tool bridge event
    event_memory = None
    for m in memories:
        if "tool_bridge" in m.tags and "release_published" in m.tags:
            event_memory = m
            break

    assert event_memory is not None
    assert event_memory.object_type == "external_tool_release_published"
    assert event_memory.content["source"] == "github"
    assert event_memory.content["trust_level"] == "fully_trusted"
    assert event_memory.content["data"]["tag"] == "v1.1.0-prod"
