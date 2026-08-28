#!/usr/bin/env python3
"""Single-command SAGE session bootstrap and evidence capture."""
from __future__ import annotations
import argparse
import json
from sage.c2.operator_acceptance_bootstrap import BootstrapFailure, OperatorAcceptanceBootstrap


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--mission-id", required=True)
    p.add_argument("--main-goal", action="append", required=True)
    p.add_argument("--side-goal", action="append", default=[])
    p.add_argument("--flight", action="append", default=[])
    p.add_argument("--operator-interface")
    p.add_argument("--operator-verdict", choices=["PASS", "FAIL"])
    p.add_argument("--evidence-ref")
    p.add_argument("--defect-id")
    p.add_argument("--output", default="evidence_capture/operator_acceptance_receipt.json")
    args = p.parse_args()
    try:
        bootstrap = OperatorAcceptanceBootstrap()
        state = bootstrap.rehydrate(args.mission_id, args.main_goal, args.side_goal, args.flight)
        bootstrap.require_execution_ready(state)
        if any([args.operator_interface, args.operator_verdict, args.evidence_ref]):
            if not all([args.operator_interface, args.operator_verdict, args.evidence_ref]):
                raise BootstrapFailure("operator interface, verdict, and evidence ref must be supplied together")
            bootstrap.capture_operator_observation(state, args.operator_interface, args.operator_verdict, args.evidence_ref, args.defect_id)
        path = bootstrap.evidence_receipt(state, args.output)
        print(json.dumps({"status": state.acceptance_status, "canonical_git_sha": state.canonical_git_sha, "receipt": str(path), "open_defects": state.open_defects}))
        return 0
    except BootstrapFailure as exc:
        print(json.dumps({"status":"FAIL_CLOSED", "reason":str(exc)}))
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
