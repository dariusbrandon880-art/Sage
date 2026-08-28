#!/usr/bin/env python3
"""Single-command SAGE session bootstrap and multi-surface evidence capture."""
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
    p.add_argument("--required-interface", action="append", default=[])
    p.add_argument("--operator-interface", action="append", default=[])
    p.add_argument("--operator-verdict", action="append", choices=["PASS", "FAIL"], default=[])
    p.add_argument("--evidence-ref", action="append", default=[])
    p.add_argument("--defect-id", action="append", default=[])
    p.add_argument("--output", default="evidence_capture/operator_acceptance_receipt.json")
    args = p.parse_args()
    try:
        bootstrap = OperatorAcceptanceBootstrap()
        state = bootstrap.rehydrate(
            args.mission_id,
            args.main_goal,
            args.side_goal,
            args.flight,
            args.required_interface,
        )
        bootstrap.require_execution_ready(state)
        counts = (len(args.operator_interface), len(args.operator_verdict), len(args.evidence_ref))
        if any(counts):
            if len(set(counts)) != 1:
                raise BootstrapFailure("operator interface, verdict, and evidence refs must have equal counts")
            if len(args.defect_id) not in (0, len(args.operator_interface)):
                raise BootstrapFailure("defect ids must be omitted or supplied once per operator observation")
            defects = args.defect_id or [None] * len(args.operator_interface)
            for interface, verdict, evidence, defect in zip(
                args.operator_interface, args.operator_verdict, args.evidence_ref, defects
            ):
                bootstrap.capture_operator_observation(state, interface, verdict, evidence, defect)
        path = bootstrap.evidence_receipt(state, args.output)
        print(json.dumps({"status": state.acceptance_status, "canonical_git_sha": state.canonical_git_sha, "receipt": str(path), "open_defects": state.open_defects}))
        return 0
    except BootstrapFailure as exc:
        print(json.dumps({"status":"FAIL_CLOSED", "reason":str(exc)}))
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
