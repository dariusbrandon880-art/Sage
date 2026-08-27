from sage.c2.c2_execution_surface import C2CommandType, C2ExecutionRequest, C2ExecutionSurfaceEngine


def runtime_sha() -> str:
    sha = C2ExecutionSurfaceEngine.resolve_runtime_head()
    assert len(sha) == 40 and all(c in "0123456789abcdefABCDEF" for c in sha)
    return sha


def test_success_and_receipt():
    sha = runtime_sha()
    rcpt = C2ExecutionSurfaceEngine().execute_request(C2ExecutionRequest(request_id="req-001", command_type=C2CommandType.READ, target_path="sage/c2/c2_execution_surface.py", starting_git_head=sha))
    assert rcpt.status == "EXECUTED" and len(rcpt.receipt_hash) == 64
    assert rcpt.starting_git_head == sha and rcpt.resulting_git_head == sha


def test_stale_head_rejected():
    sha = runtime_sha(); stale_sha = "0" * 40 if sha.lower() != "0" * 40 else "1" * 40
    rcpt = C2ExecutionSurfaceEngine().execute_request(C2ExecutionRequest(request_id="req-002", command_type=C2CommandType.READ, target_path="sage/c2/c2_execution_surface.py", starting_git_head=stale_sha))
    assert rcpt.status == "REJECTED_STALE_HEAD"


def test_protected_namespace_rejected():
    rcpt = C2ExecutionSurfaceEngine().execute_request(C2ExecutionRequest(request_id="req-003", command_type=C2CommandType.WRITE, target_path="sage/core/spek.py", starting_git_head=runtime_sha()))
    assert rcpt.status == "REJECTED_PROTECTED_NAMESPACE"


def test_invalid_sha_rejected():
    rcpt = C2ExecutionSurfaceEngine().execute_request(C2ExecutionRequest(request_id="req-004", command_type=C2CommandType.READ, target_path="sage/c2/c2_execution_surface.py", starting_git_head="shortsha123"))
    assert rcpt.status == "REJECTED_INVALID_SHA"
