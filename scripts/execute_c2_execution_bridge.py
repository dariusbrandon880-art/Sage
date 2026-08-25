"""Runner script executing harmless end-to-end smoke test of C2 Execution Bridge and persisting SHA-256 evidence receipt."""
import sys
from pathlib import Path

# Bootstrap sys.path to include repo root
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

import json
from sage.c2.c2_execution_bridge import C2ExecutionBridge, C2ExecutionRequest

def main():
    bridge = C2ExecutionBridge(root_dir=repo_root)

    # 1. Harmless write smoke test
    sample_path = "sage/experimental/c2_smoke_test_file.py"
    write_req = C2ExecutionRequest(
        action_type="WRITE",
        target_path=sample_path,
        content="# SAGE C2 Execution Bridge Smoke Test File\n",
        actor_id="[SAGE::C2::GPT_OPERATIONAL]",
    )
    write_receipt = bridge.execute_c2_request(write_req)

    # 2. Harmless test execution smoke test
    test_req = C2ExecutionRequest(
        action_type="TEST",
        command="poetry run pytest tests/c2/test_c2_execution_bridge.py",
        actor_id="[SAGE::C2::GPT_OPERATIONAL]",
    )
    test_receipt = bridge.execute_c2_request(test_req)

    # 3. Clean up sample smoke test file
    sample_file = repo_root / sample_path
    if sample_file.exists():
        sample_file.unlink()

    evidence_data = {
        "capability": "c2_execution_bridge",
        "smoke_test_write_status": write_receipt.result_status,
        "smoke_test_write_sha": write_receipt.resulting_sha,
        "smoke_test_test_status": test_receipt.result_status,
        "smoke_test_receipt_digest": test_receipt.digest(),
        "actor_id": "[SAGE::C2::GPT_OPERATIONAL]",
        "verification_status": "PASS" if write_receipt.result_status == "PASS" and test_receipt.result_status == "PASS" else "FAIL",
    }

    evidence_path = Path("evidence_capture/c2_execution_bridge_evidence.json")
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(json.dumps(evidence_data, indent=2), encoding="utf-8")
    print(f"[✓] C2 Execution Bridge Smoke Test Evidence generated at {evidence_path}")

if __name__ == "__main__":
    main()
