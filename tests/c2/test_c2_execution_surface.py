from sage.c2.c2_execution_surface import C2CommandType, C2ExecutionRequest, C2ExecutionSurfaceEngine

VALID_SHA = "7cdebce6e542ab5e8975194c6610f388e83942a9"

def test_success_and_receipt():
    rcpt = C2ExecutionSurfaceEngine().execute_request(C2ExecutionRequest(request_id="req-001", command_type=C2CommandType.READ, target_path="sage/c2/c2_execution_surface.py", starting_git_head=VALID_SHA))
    assert rcpt.status == "SUCCESS" and len(rcpt.receipt_hash) == 64

def test_protected_namespace_rejected():
    rcpt = C2ExecutionSurfaceEngine().execute_request(C2ExecutionRequest(request_id="req-002", command_type=C2CommandType.WRITE, target_path="sage/core/spek.py", starting_git_head=VALID_SHA))
    assert rcpt.status == "REJECTED_PROTECTED_NAMESPACE"

def test_invalid_sha_rejected():
    rcpt = C2ExecutionSurfaceEngine().execute_request(C2ExecutionRequest(request_id="req-003", command_type=C2CommandType.READ, target_path="sage/c2/c2_execution_surface.py", starting_git_head="shortsha123"))
    assert rcpt.status == "REJECTED_INVALID_SHA"
