#!/usr/bin/env python3
"""Execute live FrontierDependencyRouter workflow:

Candidate Intake -> Risk Profile & Dependency Evaluation -> C2 Authorization Package -> FrontierIntelligenceBridge wave execution.

Outputs observable evidence to evidence_capture/frontier_dependency_router_evidence.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from sage.c2.frontier_dependency_router import (  # noqa: E402
    FrontierDependencyRouter,
)
from sage.c2.frontier_intelligence_bridge import (  # noqa: E402
    AuthorizedCandidate,
    FrontierIntelligenceBridge,
)
from sage.experimental.sagi_discovery_flight_selector import (  # noqa: E402
    DiscoveryCandidate,
    FlightRole,
    SAGIDiscoveryFlightSelector,
)

EVIDENCE_PATH = repo_root / "evidence_capture" / "frontier_dependency_router_evidence.json"


def main() -> int:
    print("=" * 70)
    print("SAGE C2 FRONTIER DEPENDENCY ROUTER EXECUTION")
    print("=" * 70)

    router = FrontierDependencyRouter()

    candidates_meta = (
        {
            "cand": DiscoveryCandidate(
                candidate_id="cand_consequent_01",
                description="Consequent frontier: intelligent multi-vector execution",
                role=FlightRole.CONSEQUENT_FRONTIER,
                consequentiality=0.9,
                information_gain=0.8,
                falsification_value=0.7,
                safety=0.95,
                evidence_gap=0.6,
                provenance_ref="provenance_ref_consequent_01",
            ),
            "paths": ("sage/c2/multi_frontier_dispatch.py",),
            "edges": ("sage.c2", "sage.experimental"),
        },
        {
            "cand": DiscoveryCandidate(
                candidate_id="cand_info_gain_02",
                description="Information gain: context rehydration continuity",
                role=FlightRole.INFORMATION_GAIN,
                consequentiality=0.8,
                information_gain=0.95,
                falsification_value=0.6,
                safety=0.9,
                evidence_gap=0.5,
                provenance_ref="provenance_ref_info_gain_02",
            ),
            "paths": ("sage/experimental/act/continuity_control.py",),
            "edges": ("sage.experimental.act",),
        },
        {
            "cand": DiscoveryCandidate(
                candidate_id="cand_falsification_03",
                description="Falsification: adversarial gate boundary testing",
                role=FlightRole.FALSIFICATION,
                consequentiality=0.7,
                information_gain=0.7,
                falsification_value=0.9,
                safety=0.85,
                evidence_gap=0.4,
                provenance_ref="provenance_ref_falsification_03",
            ),
            "paths": ("tests/c2/test_frontier_intelligence_bridge.py",),
            "edges": ("tests.c2",),
        },
        {
            "cand": DiscoveryCandidate(
                candidate_id="cand_recovery_04",
                description="Recovery regression: fail-closed safety verification",
                role=FlightRole.RECOVERY_REGRESSION,
                consequentiality=0.85,
                information_gain=0.75,
                falsification_value=0.8,
                safety=0.9,
                evidence_gap=0.5,
                provenance_ref="provenance_ref_recovery_04",
            ),
            "paths": ("sage/experimental/five_flight_reconvergence.py",),
            "edges": ("sage.experimental",),
        },
        {
            "cand": DiscoveryCandidate(
                candidate_id="cand_transfer_05",
                description="Independent transfer: capability warehouse archiving",
                role=FlightRole.INDEPENDENT_TRANSFER,
                consequentiality=0.75,
                information_gain=0.8,
                falsification_value=0.65,
                safety=0.92,
                evidence_gap=0.45,
                provenance_ref="provenance_ref_transfer_05",
            ),
            "paths": ("evidence_capture/multi_frontier_dispatch_evidence.json",),
            "edges": ("evidence_capture",),
        },
    )

    discovery_candidates = tuple(m["cand"] for m in candidates_meta)
    packages = []
    authorized_map = {}

    for m in candidates_meta:
        cand = m["cand"]
        risk_profile = router.evaluate_risk(
            candidate_id=cand.candidate_id,
            target_paths=m["paths"],
            dependency_edges=m["edges"],
            base_consequentiality=cand.consequentiality,
        )
        # Apply C2 Operator Authorization Token
        auth_token = f"auth_token_c2_{cand.candidate_id}"
        pkg = router.prepare_authorization_package(
            risk_profile,
            authorized_by="c2_lifecycle_router_authorizer",
            authorization_token=auth_token,
        )
        packages.append(pkg)
        authorized_map[cand.candidate_id] = AuthorizedCandidate(
            candidate_id=cand.candidate_id,
            authorized=pkg.authorization_ready,
            authorized_by=pkg.authorized_by,
            authorization_token=pkg.authorization_token,
        )

    # Select proposal
    selector = SAGIDiscoveryFlightSelector()
    proposal = selector.select(discovery_candidates, frontier_digest="frontier_digest_router_v1")

    # Bridge dispatch
    bridge = FrontierIntelligenceBridge()
    bridge_receipt = bridge.adapt_and_dispatch(proposal, authorized_map)

    evidence_data = {
        "commit_sha": router.commit_sha,
        "packages": [p.to_dict() for p in packages],
        "bridge_receipt": bridge_receipt.to_dict(),
        "router_verdict": "PASS" if bridge_receipt.bridge_verdict == "PASS" else "HOLD",
    }

    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(EVIDENCE_PATH, "w", encoding="utf-8") as f:
        json.dump(evidence_data, f, indent=2)

    print(f"Commit SHA: {router.commit_sha}")
    print(f"Packages Evaluated: {len(packages)}")
    print(f"Bridge Verdict: {bridge_receipt.bridge_verdict}")
    print(f"Router Verdict: {evidence_data['router_verdict']}")
    print(f"Evidence Captured: {EVIDENCE_PATH}")

    if evidence_data["router_verdict"] != "PASS":
        print("\n[!] DEPENDENCY ROUTER EXECUTION FAILED OR HELD", file=sys.stderr)
        return 1

    print("\n[✓] FRONTIER DEPENDENCY ROUTER SUCCESSFUL — RISK PROFILES & WAVE DISPATCH VERIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
