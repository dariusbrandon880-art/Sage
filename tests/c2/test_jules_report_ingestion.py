from sage.c2.jules_report_ingestion import JulesReport, ingest_jules_report


SHA = "e8589d31629feb5ee6a5ea3f44f327f0b2c91885"
OTHER_SHA = "6a69a970d96582b7d0d53778cc1da3300eccdc84"


class FakeRuntime:
    def __init__(self):
        self.payloads = []

    def ingest_session_payload(self, payload):
        self.payloads.append(payload)


def make_report(**overrides):
    data = {
        "session_id": "session_jules_001",
        "report_id": "jules-report-001",
        "git_sha": SHA,
        "branch": "c2/jules-report-ingestion-contract",
        "status": "VERIFIED",
        "objective": "Close Jules report to C2 continuity seam",
        "summary": "Structured report accepted for continuity ingestion.",
        "evidence": ["pytest:tests/c2/test_jules_report_ingestion.py"],
        "state_deltas": {"frontier": "jules-report-ingestion"},
        "pr_number": 999,
        "pr_head_sha": SHA,
    }
    data.update(overrides)
    return JulesReport.model_validate(data)


def test_matching_head_ingests_observation_only():
    runtime = FakeRuntime()
    result = ingest_jules_report(runtime, make_report(), canonical_git_sha=SHA)

    assert result.accepted is True
    assert len(runtime.payloads) == 1
    payload = runtime.payloads[0]
    assert payload.task is None
    assert payload.metadata["canonical_git_sha"] == SHA
    assert payload.memories[0]["object_type"] == "jules_execution_report"


def test_report_head_mismatch_fails_closed_without_ingestion():
    runtime = FakeRuntime()
    result = ingest_jules_report(runtime, make_report(git_sha=OTHER_SHA, pr_head_sha=OTHER_SHA), canonical_git_sha=SHA)

    assert result.accepted is False
    assert "does not match canonical Git HEAD" in result.rejection_reason
    assert runtime.payloads == []


def test_pr_head_mismatch_fails_closed_without_ingestion():
    runtime = FakeRuntime()
    result = ingest_jules_report(runtime, make_report(pr_head_sha=OTHER_SHA), canonical_git_sha=SHA)

    assert result.accepted is False
    assert "PR head SHA" in result.rejection_reason
    assert runtime.payloads == []


def test_invalid_report_sha_is_rejected_before_runtime_write():
    runtime = FakeRuntime()
    try:
        ingest_jules_report(runtime, make_report(git_sha="not-a-sha", pr_head_sha=None), canonical_git_sha=SHA)
    except ValueError as exc:
        assert "40 lowercase hexadecimal" in str(exc)
    else:
        raise AssertionError("invalid report SHA must be rejected")
    assert runtime.payloads == []
