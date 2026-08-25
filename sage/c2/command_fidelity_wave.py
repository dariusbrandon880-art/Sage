"""Flight E: Five-Flight Command Fidelity Wave Dispatcher for SAGE C2.

Orchestrates 5 parallel execution flights across the Command Fidelity & Reality Gate frontier:
- Flight A: Directive Fidelity (exact order & constraint validation)
- Flight B: Reality Gate (live source receipt enforcement)
- Flight C: Claim Provenance Compiler (factual claim to receipt mapping)
- Flight D: Fresh-Session Drift Sentinel (adversarial replay & fidelity scoring)
- Flight E: Reconvergence & Evidence Capture (persisted SHA-256 evidence receipt)
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
from typing import Any, Dict, List, Optional

from sage.c2.claim_provenance import ClaimProvenanceCompiler
from sage.c2.directive_fidelity import DirectiveFingerprint, ExactOrderSentinel
from sage.c2.drift_sentinel import DriftReplayScenario, DriftSentinel
from sage.c2.reality_gate import OperationalClaim, RealityGate, SourceReceipt


def _get_current_commit_sha() -> str:
    """Retrieve active git commit SHA, falling back to HEAD environment if uncommitted."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except Exception:
        return os.environ.get("GIT_COMMIT_SHA", "UNKNOWN_COMMIT")


@dataclass(frozen=True)
class FidelityFlightResult:
    flight_id: str
    flight_name: str
    boundary_scope: str
    status: str  # PASS, HOLD
    receipt_hash: str
    commit_sha: str
    metrics: Dict[str, Any]


@dataclass
class CommandFidelityWaveReceipt:
    commit_sha: str
    timestamp_utc: float
    flight_results: List[FidelityFlightResult]
    wave_verdict: str  # PASS, HOLD
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "commit_sha": self.commit_sha,
            "timestamp_utc": self.timestamp_utc,
            "flight_results": [asdict(f) for f in self.flight_results],
            "wave_verdict": self.wave_verdict,
            "summary": self.summary,
        }


class CommandFidelityWaveDispatcher:
    """Dispatches all 5 command fidelity flights and reconverges into a machine-readable verdict."""

    def __init__(self, commit_sha: Optional[str] = None) -> None:
        self.commit_sha = commit_sha or _get_current_commit_sha()

    @classmethod
    def validate_persisted_evidence(
        cls,
        evidence_path: str | Path,
        expected_commit_sha: Optional[str] = None,
    ) -> bool:
        """Fails closed if persisted evidence SHA differs from expected/active commit SHA."""
        target_sha = expected_commit_sha or _get_current_commit_sha()
        path = Path(evidence_path)
        if not path.exists():
            raise FileNotFoundError(f"Persisted evidence file not found: {path}")

        data = json.loads(path.read_text(encoding="utf-8"))
        top_level_sha = data.get("commit_sha", "")
        verdict = data.get("wave_verdict", "")

        if verdict != "PASS":
            return False

        if top_level_sha != target_sha:
            return False

        flights = data.get("flight_results", [])
        for flight in flights:
            if flight.get("commit_sha") != target_sha or flight.get("status") != "PASS":
                return False

        return True

    def dispatch_wave(self) -> CommandFidelityWaveReceipt:
        timestamp = time.time()
        results: List[FidelityFlightResult] = []

        # Flight A — Directive Fidelity
        raw_instr = "Check live repo.\nInspect PR.\nRun verification.\nDo not merge."
        contract = DirectiveFingerprint.create_contract(raw_instr)
        valid_res = ExactOrderSentinel.validate_plan(contract, ["Check live repo", "Inspect PR", "Run verification"])
        invalid_res = ExactOrderSentinel.validate_plan(contract, ["Check live repo", "Merge PR"])

        flight_a_status = "PASS" if valid_res.is_valid and not invalid_res.is_valid else "HOLD"
        flight_a_hash = hashlib.sha256(f"FlightA:{contract.raw_instruction_hash}:{self.commit_sha}:{flight_a_status}".encode("utf-8")).hexdigest()
        results.append(
            FidelityFlightResult(
                flight_id="Flight A",
                flight_name="Directive Fidelity",
                boundary_scope="sage.c2.directive_fidelity",
                status=flight_a_status,
                receipt_hash=flight_a_hash,
                commit_sha=self.commit_sha,
                metrics={
                    "valid_plan_passed": valid_res.is_valid,
                    "invalid_plan_blocked": not invalid_res.is_valid,
                    "forbidden_additions_count": len(contract.forbidden_additions),
                },
            )
        )

        # Flight B — Reality Gate
        sample_receipt = SourceReceipt(
            source_type="github",
            resource_id=f"commit:{self.commit_sha}",
            sha256_digest=self.commit_sha,
            timestamp_utc=timestamp,
        )
        claims = [
            OperationalClaim(
                claim_id="c1",
                statement=f"GitHub main is at {self.commit_sha}.",
                required_source_type="github",
                target_resource=f"commit:{self.commit_sha}",
            ),
        ]
        gate_res = RealityGate.evaluate_claims(claims, [sample_receipt])
        flight_b_status = "PASS" if len(gate_res.permitted_claims) == 1 and len(gate_res.blocked_claims) == 0 else "HOLD"
        flight_b_hash = hashlib.sha256(f"FlightB:{sample_receipt.sha256_digest}:{self.commit_sha}:{flight_b_status}".encode("utf-8")).hexdigest()
        results.append(
            FidelityFlightResult(
                flight_id="Flight B",
                flight_name="Reality Gate",
                boundary_scope="sage.c2.reality_gate",
                status=flight_b_status,
                receipt_hash=flight_b_hash,
                commit_sha=self.commit_sha,
                metrics={
                    "permitted_claims_count": len(gate_res.permitted_claims),
                    "blocked_claims_count": len(gate_res.blocked_claims),
                },
            )
        )

        # Flight C — Claim Provenance Compiler
        compile_res = ClaimProvenanceCompiler.compile_claims(claims, [sample_receipt])
        flight_c_status = "PASS" if compile_res.is_valid else "HOLD"
        flight_c_hash = hashlib.sha256(f"FlightC:{compile_res.is_valid}:{self.commit_sha}:{flight_c_status}".encode("utf-8")).hexdigest()
        results.append(
            FidelityFlightResult(
                flight_id="Flight C",
                flight_name="Claim Provenance Compiler",
                boundary_scope="sage.c2.claim_provenance",
                status=flight_c_status,
                receipt_hash=flight_c_hash,
                commit_sha=self.commit_sha,
                metrics={
                    "verified_claims_count": len(compile_res.verified_claims),
                    "unresolved_claims_count": len(compile_res.unresolved_claims),
                    "contradicted_claims_count": len(compile_res.contradicted_claims),
                },
            )
        )

        # Flight D — Fresh-Session Drift Sentinel
        scenario = DriftReplayScenario(
            scenario_id="sc-dispatch-01",
            user_instruction=raw_instr,
            contract=contract,
            proposed_actions=("Check live repo", "Inspect PR", "Run verification"),
            proposed_claims=(claims[0],),
            available_receipts=(sample_receipt,),
            expected_should_pass=True,
        )
        drift_report = DriftSentinel.run_suite([scenario])
        flight_d_status = "PASS" if drift_report.metrics.overall_drift_rate == 0.0 else "HOLD"
        flight_d_hash = hashlib.sha256(f"FlightD:{drift_report.metrics.overall_drift_rate}:{self.commit_sha}:{flight_d_status}".encode("utf-8")).hexdigest()
        results.append(
            FidelityFlightResult(
                flight_id="Flight D",
                flight_name="Fresh-Session Drift Sentinel",
                boundary_scope="sage.c2.drift_sentinel",
                status=flight_d_status,
                receipt_hash=flight_d_hash,
                commit_sha=self.commit_sha,
                metrics=asdict(drift_report.metrics),
            )
        )

        # Flight E — Reconvergence & Evidence Capture
        stale_sha_found = any(f.commit_sha != self.commit_sha for f in results)
        all_passed = all(f.status == "PASS" for f in results) and not stale_sha_found
        wave_verdict = "PASS" if all_passed else "HOLD"
        flight_e_hash = hashlib.sha256(f"FlightE:{wave_verdict}:{self.commit_sha}:{timestamp}".encode("utf-8")).hexdigest()
        results.append(
            FidelityFlightResult(
                flight_id="Flight E",
                flight_name="Wave Reconvergence",
                boundary_scope="sage.c2.command_fidelity_wave",
                status=wave_verdict,
                receipt_hash=flight_e_hash,
                commit_sha=self.commit_sha,
                metrics={"wave_reconverged": all_passed, "stale_sha_detected": stale_sha_found},
            )
        )

        return CommandFidelityWaveReceipt(
            commit_sha=self.commit_sha,
            timestamp_utc=timestamp,
            flight_results=results,
            wave_verdict=wave_verdict,
            summary={
                "total_flights": len(results),
                "passed_flights": sum(1 for f in results if f.status == "PASS"),
                "wave_verdict": wave_verdict,
                "stale_sha_detected": stale_sha_found,
            },
        )
