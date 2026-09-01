#!/usr/bin/env python3
"""Execute SAGE Adaptive Frontier Selection v0.1 workflow:

Candidate Intake -> Risk Surface Evaluation -> Authorization Package Synthesis -> C2 Gate -> Bridge Dispatch Wave.

Outputs evidence receipt to evidence_capture/adaptive_frontier_selection_evidence.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from sage.c2.authorization_package_synthesis import (  # noqa: E402
    AuthorizationPackageSynthesizer,
)
from sage.c2.build_jump_wave import FlightMissionSpec  # noqa: E402
from sage.c2.frontier_intelligence_bridge import (  # noqa: E402
    FrontierIntelligenceBridge,
)
from sage.experimental.sagi_discovery_flight_selector import (  # noqa: E402
    DiscoveryCandidate,
    FlightRole,
    SAGIDiscoveryFlightSelector,
)
from sage.mission_intake import SAGEMissionIntakeLayer  # noqa: E402

EVIDENCE_PATH = repo_root / "evidence_capture" / "adaptive_frontier_selection_evidence.json"


def main() -> int:
    print("=" * 70)
    print("SAGE ADAPTIVE FRONTIER SELECTION V0.1 EXECUTION")
    print("=" * 70)

    # 1. Mission Intake
    intake = SAGEMissionIntakeLayer()
    proposal_data = {
        "name": "Adaptive Frontier Selection",
        "description": "Synthesize candidate risk surfaces and authorization packages",
        "objective": "Govern intake to dispatch transition without autonomous promotion",
        "operator_id": "operator_c2_authorizer",
        "provenance_ref": "ref_adaptive_selection_2026",
        "prerequisites": {"value_appraisal_approved": True},
    }
    intake_res = intake.submit_proposal(proposal_data)

    # 2. Risk Surface & Authorization Package Synthesis
    synthesizer = AuthorizationPackageSynthesizer()

    candidates_def = (
        {
            "cand": DiscoveryCandidate(
                candidate_id="cand_consequent_adaptive_01",
                description="Consequent frontier: adaptive selection engine",
                role=FlightRole.CONSEQUENT_FRONTIER,
                consequentiality=0.9,
                information_gain=0.8,
                falsification_value=0.7,
                safety=0.95,
                evidence_gap=0.6,
                provenance_ref="provenance_adaptive_01",
            ),
            "paths": ("sage/c2/authorization_package_synthesis.py",),
        },
        {
            "cand": DiscoveryCandidate(
                candidate_id="cand_info_gain_adaptive_02",
                description="Information gain: intake lineage tracking",
                role=FlightRole.INFORMATION_GAIN,
                consequentiality=0.8,
                information_gain=0.95,
                falsification_value=0.6,
                safety=0.9,
                evidence_gap=0.5,
                provenance_ref="provenance_adaptive_02",
            ),
            "paths": ("sage/mission_intake.py",),
        },
        {
            "cand": DiscoveryCandidate(
                candidate_id="cand_falsification_adaptive_03",
                description="Falsification: risk surface error boundary testing",
                role=FlightRole.FALSIFICATION,
                consequentiality=0.7,
                information_gain=0.7,
                falsification_value=0.9,
                safety=0.85,
                evidence_gap=0.4,
                provenance_ref="provenance_adaptive_03",
            ),
            "paths": ("tests/test_authorization_package_synthesis.py",),
        },
        {
            "cand": DiscoveryCandidate(
                candidate_id="cand_recovery_adaptive_04",
                description="Recovery regression: fail-closed gate verification",
                role=FlightRole.RECOVERY_REGRESSION,
                consequentiality=0.85,
                information_gain=0.75,
                falsification_value=0.8,
                safety=0.9,
                evidence_gap=0.5,
                provenance_ref="provenance_adaptive_04",
            ),
            "paths": ("sage/experimental/five_flight_reconvergence.py",),
        },
        {
            "cand": DiscoveryCandidate(
                candidate_id="cand_transfer_adaptive_05",
                description="Independent transfer: evidence receipt archiving",
                role=FlightRole.INDEPENDENT_TRANSFER,
                consequentiality=0.75,
                information_gain=0.8,
                falsification_value=0.65,
                safety=0.92,
                evidence_gap=0.45,
                provenance_ref="provenance_adaptive_05",
            ),
            "paths": ("evidence_capture/adaptive_frontier_selection_evidence.json",),
        },
    )

    packages = []
    authorized_candidate_ids = []
    discovery_candidates = tuple(item["cand"] for item in candidates_def)

    for item in candidates_def:
        cand = item["cand"]
        pkg = synthesizer.synthesize_package(
            candidate_id=cand.candidate_id,
            target_paths=item["paths"],
            evidence_requirements=("git_commit", "test_report", "evidence_receipt"),
            verification_plan_present=True,
            authorization_token=f"auth_token_c2_adaptive_{cand.candidate_id}",
        )
        packages.append(pkg)
        if pkg.is_authorized:
            authorized_candidate_ids.append(cand.candidate_id)

    # 3. SAGI Selection
    selector = SAGIDiscoveryFlightSelector()
    proposal = selector.select(discovery_candidates, frontier_digest="frontier_digest_adaptive_v1")

    # 4. Bridge Wave Dispatch
    bridge = FrontierIntelligenceBridge()
    missions = [
        FlightMissionSpec(
            flight_id="F1",
            frontier_name="Adaptive Selection Engine",
            target_path="sage/c2/authorization_package_synthesis.py",
            collision_zone="sage/c2/authorization_package_synthesis",
            evidence_ref="evidence_capture/adaptive_frontier_selection_evidence.json",
            pr_or_change="PR-ADAPTIVE-F1",
            test_references=["tests/test_authorization_package_synthesis.py"],
        ),
        FlightMissionSpec(
            flight_id="F2",
            frontier_name="Intake Lineage Tracking",
            target_path="sage/mission_intake.py",
            collision_zone="sage/mission_intake",
            evidence_ref="evidence_capture/adaptive_frontier_selection_evidence.json",
            pr_or_change="PR-ADAPTIVE-F2",
            test_references=["tests/test_mission_intake.py"],
        ),
        FlightMissionSpec(
            flight_id="F3",
            frontier_name="Risk Surface Error Boundary Testing",
            target_path="sage/c2/frontier_intelligence_bridge.py",
            collision_zone="sage/c2/frontier_intelligence_bridge",
            evidence_ref="evidence_capture/adaptive_frontier_selection_evidence.json",
            pr_or_change="PR-ADAPTIVE-F3",
            test_references=["tests/test_frontier_intelligence_bridge.py"],
        ),
        FlightMissionSpec(
            flight_id="F4",
            frontier_name="Fail-Closed Gate Verification",
            target_path="sage/experimental/sagi_discovery_flight_selector.py",
            collision_zone="sage/experimental/sagi_discovery_flight_selector",
            evidence_ref="evidence_capture/adaptive_frontier_selection_evidence.json",
            pr_or_change="PR-ADAPTIVE-F4",
            test_references=["tests/experimental/test_sagi_discovery_flight_selector.py"],
        ),
        FlightMissionSpec(
            flight_id="F5",
            frontier_name="Evidence Receipt Archiving",
            target_path="sage/c2/multi_frontier_dispatch.py",
            collision_zone="sage/c2/multi_frontier_dispatch",
            evidence_ref="evidence_capture/adaptive_frontier_selection_evidence.json",
            pr_or_change="PR-ADAPTIVE-F5",
            test_references=["tests/c2/test_multi_frontier_dispatch.py"],
        ),
    ]
    bridge_receipt = bridge.bridge_and_dispatch(
        proposal,
        authorized_candidate_ids=tuple(authorized_candidate_ids),
        missions=missions,
        commit_sha=synthesizer.commit_sha,
    )

    evidence_data = {
        "commit_sha": synthesizer.commit_sha,
        "intake_submission": intake_res,
        "packages": [p.to_dict() for p in packages],
        "proposal_selection_digest": proposal.selection_digest,
        "bridge_digest": bridge_receipt.bridge_digest,
        "is_authorized": bridge_receipt.is_authorized,
        "dispatch_verdict": (
            bridge_receipt.dispatch_result.wave_verdict
            if bridge_receipt.dispatch_result
            else "BLOCKED"
        ),
        "selection_verdict": (
            "PASS"
            if bridge_receipt.is_authorized
            and bridge_receipt.dispatch_result
            and bridge_receipt.dispatch_result.wave_verdict == "PASS"
            else "HOLD"
        ),
    }

    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(EVIDENCE_PATH, "w", encoding="utf-8") as f:
        json.dump(evidence_data, f, indent=2)

    print(f"Commit SHA: {synthesizer.commit_sha}")
    print(f"Intake Mission ID: {intake_res.get('mission_id')}")
    print(f"Packages Synthesized: {len(packages)}")
    print(f"Selection Digest: {proposal.selection_digest}")
    print(f"Bridge Digest: {bridge_receipt.bridge_digest}")
    print(f"Dispatch Verdict: {evidence_data['dispatch_verdict']}")
    print(f"Selection Verdict: {evidence_data['selection_verdict']}")
    print(f"Evidence Captured: {EVIDENCE_PATH}")

    if evidence_data["selection_verdict"] != "PASS":
        print("\n[!] ADAPTIVE FRONTIER SELECTION FAILED OR HELD", file=sys.stderr)
        return 1

    print("\n[✓] ADAPTIVE FRONTIER SELECTION V0.1 SUCCESSFUL — INTAKE TO WAVE VERIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
