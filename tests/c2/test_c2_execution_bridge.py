"""Tests for governed C2 execution bridge exact-head behavior."""
import pytest
from sage.c2.c2_execution_bridge import C2ExecutionBridge, C2ExecutionRequest, C2ExecutionReceipt
SHA="0123456789abcdef0123456789abcdef01234567"
def test_receipt_hash_integrity():
    r=C2ExecutionReceipt(receipt_id="r",request_id="q",command="READ",target_path="sage/c2/x.py",starting_head_sha=SHA,resulting_head_sha=SHA,status="SUCCESS"); r.receipt_hash=r.compute_hash(); assert len(r.receipt_hash)==64 and r.receipt_hash==r.compute_hash()
def test_invalid_command_rejected():
    r=C2ExecutionBridge(SHA).execute(C2ExecutionRequest(request_id="q",command="EXPLODE",target_path="x",expected_head_sha=SHA)); assert r.status=="REJECTED"
def test_short_or_stale_sha_rejected():
    b=C2ExecutionBridge(SHA); r=b.execute(C2ExecutionRequest(request_id="q",command="READ",target_path="x",expected_head_sha="stale")); assert r.status=="REJECTED"
def test_protected_write_requires_auth():
    b=C2ExecutionBridge(SHA); r=b.execute(C2ExecutionRequest(request_id="q",command="WRITE",target_path="sage/core/x.py",expected_head_sha=SHA)); assert r.status=="REJECTED"
def test_protected_write_with_auth_succeeds():
    b=C2ExecutionBridge(SHA); r=b.execute(C2ExecutionRequest(request_id="q",command="WRITE",target_path="sage/core/x.py",expected_head_sha=SHA,auth_token="SAGE_SYSTEM_AUTH_TOKEN")); assert r.status=="SUCCESS"
def test_commit_generates_full_sha():
    b=C2ExecutionBridge(SHA); r=b.execute(C2ExecutionRequest(request_id="q",command="COMMIT",target_path="sage/experimental/x.py",expected_head_sha=SHA)); assert r.status=="SUCCESS" and len(r.resulting_head_sha)==40 and b.current_head_sha==r.resulting_head_sha
