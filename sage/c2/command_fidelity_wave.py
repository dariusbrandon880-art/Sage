"""Flight E: Five-Flight Command Fidelity Wave Dispatcher for SAGE C2.

The dispatcher is a reconvergence boundary. Live-state claims require an
operation receipt supplied by the operation boundary; the dispatcher never
creates a receipt and never treats a boolean as proof of live execution.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
from typing import Any, Dict, List, Optional, Tuple

from sage.c2.claim_provenance import ClaimProvenanceCompiler
from sage.c2.directive_fidelity import DirectiveFingerprint, ExactOrderSentinel
from sage.c2.drift_sentinel import DriftReplayScenario, DriftSentinel
from sage.c2.reality_gate import OperationalClaim, RealityGate, SourceReceipt


def _get_current_commit_sha() -> str:
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
    status: str
    receipt_hash: str
    commit_sha: str
    metrics: Dict[str, Any]


@dataclass
class CommandFidelityWaveReceipt:
    commit_sha: str
    timestamp_utc: float
    flight_results: List[FidelityFlightResult]
    wave_verdict: str
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
    REQUIRED_FLIGHTS = ("Flight A", "Flight B", "Flight C", "Flight D", "Flight E")

    def __init__(self, commit_sha: Optional[str] = None) -> None:
        self.commit_sha = commit_sha or _get_current_commit_sha()

    @classmethod
    def validate_persisted_evidence(
        cls,
        evidence_path: str | Path,
        expected_commit_sha: Optional[str] = None,
    ) -> bool:
        target_sha = expected_commit_sha or _get_current_commit_sha()
        if not target_sha or target_sha == "UNKNOWN_COMMIT":
            return False
        path = Path(evidence_path)
        if not path.exists():
            raise FileNotFoundError(f"Persisted evidence file not found: {path}")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return False
        if data.get("commit_sha") != target_sha or data.get("wave_verdict") != "PASS":
            return False
        flights = data.get("flight_results")
        if not isinstance(flights, list) or len(flights) != 5:
            return False
        if tuple(f.get("flight_id") for f in flights) != cls.REQUIRED_FLIGHTS:
            return False
        for flight in flights:
            if flight.get("commit_sha") != target_sha or flight.get("status") != "PASS":
                return False
            if not isinstance(flight.get("receipt_hash"), str) or not flight["receipt_hash"]:
                return False
            metrics = flight.get("metrics")
            if not isinstance(metrics, dict):
                return False
            if metrics.get("stale_sha_detected") is True:
                return False
            if metrics.get("contradicted_claims_count", 0) != 0:
                return False
            if metrics.get("unresolved_claims_count", 0) != 0:
                return False
        summary = data.get("summary")
        return (
            isinstance(summary, dict)
            and summary.get("total_flights") == 5
            and summary.get("passed_flights") == 5
            and summary.get("wave_verdict") == "PASS"
            and summary.get("stale_sha_detected") is not True
        )

    def dispatch_wave(
        self,
        operation_receipt: Optional[SourceReceipt] = None,
    ) -> CommandFidelityWaveReceipt:
        """Run the wave; live flights require an externally produced operation receipt."""
        timestamp = time.time()
        results: List[FidelityFlightResult] = []

        raw_instr = "Check live repo.\nInspect PR.\nRun verification.\nDo not merge."
        contract = DirectiveFingerprint.create_contract(raw_instr)
        valid_res = ExactOrderSentinel.validate_plan(
            contract, ["Check live repo", "Inspect PR", "Run verification"]
        )
        invalid_res = ExactOrderSentinel.validate_plan(contract, ["Check live repo", "Merge PR"])
        status = "PASS" if valid_res.is_valid and not invalid_res.is_valid else "HOLD"
        results.append(
            FidelityFlightResult(
                "Flight A", "Directive Fidelity", "sage.c2.directive_fidelity", status,
                hashlib.sha256(f"FlightA:{contract.raw_instruction_hash}:{self.commit_sha}:{status}".encode()).hexdigest(),
                self.commit_sha,
                {"valid_plan_passed": valid_res.is_valid, "invalid_plan_blocked": not invalid_res.is_valid,
                 "forbidden_additions_count": len(contract.forbidden_additions)},
            )
        )

        # No receipt is manufactured here. The operation boundary must provide it.
        if operation_receipt is None:
            live_claims: List[OperationalClaim] = [
                OperationalClaim(
                    "c1", "GitHub main was verified live.", "github", f"commit:{self.commit_sha}"
                )
            ]
            gate_res = RealityGate.evaluate_claims(live_claims, [])
            flight_b_status = "HOLD"
            flight_b_metrics = {
                "permitted_claims_count": len(gate_res.permitted_claims),
                "blocked_claims_count": len(gate_res.blocked_claims),
                "operation_receipt_present": False,
            }
            claims = live_claims
            receipts: Tuple[SourceReceipt, ...] = ()
        else:
            claims = [
                OperationalClaim(
                    "c1",
                    f"GitHub main is at {operation_receipt.sha256_digest}.",
                    "github",
                    operation_receipt.resource_id,
                )
            ]
            gate_res = RealityGate.evaluate_claims(claims, [operation_receipt])
            flight_b_status = "PASS" if gate_res.is_permitted else "HOLD"
            flight_b_metrics = {
                "permitted_claims_count": len(gate_res.permitted_claims),
                "blocked_claims_count": len(gate_res.blocked_claims),
                "operation_receipt_present": True,
            }
            receipts = (operation_receipt,)
        results.append(
            FidelityFlightResult(
                "Flight B", "Reality Gate", "sage.c2.reality_gate", flight_b_status,
                hashlib.sha256(f"FlightB:{flight_b_status}:{self.commit_sha}".encode()).hexdigest(),
                self.commit_sha, flight_b_metrics,
            )
        )

        compile_res = ClaimProvenanceCompiler.compile_claims(claims, receipts)
        flight_c_status = "PASS" if compile_res.is_valid else "HOLD"
        results.append(
            FidelityFlightResult(
                "Flight C", "Claim Provenance Compiler", "sage.c2.claim_provenance", flight_c_status,
                hashlib.sha256(f"FlightC:{compile_res.is_valid}:{self.commit_sha}".encode()).hexdigest(),
                self.commit_sha,
                {"verified_claims_count": len(compile_res.verified_claims),
                 "unresolved_claims_count": len(compile_res.unresolved_claims),
                 "contradicted_claims_count": len(compile_res.contradicted_claims)},
            )
        )

        scenario = DriftReplayScenario(
            "sc-dispatch-01", raw_instr, contract,
            ("Check live repo", "Inspect PR", "Run verification"),
            (claims[0],), receipts, operation_receipt is not None,
        )
        drift_report = DriftSentinel.run_suite([scenario])
        flight_d_status = "PASS" if drift_report.metrics.overall_drift_rate == 0.0 else "HOLD"
        results.append(
            FidelityFlightResult(
                "Flight D", "Fresh-Session Drift Sentinel", "sage.c2.drift_sentinel", flight_d_status,
                hashlib.sha256(f"FlightD:{drift_report.metrics.overall_drift_rate}:{self.commit_sha}".encode()).hexdigest(),
                self.commit_sha, asdict(drift_report.metrics),
            )
        )

        stale_sha_found = any(f.commit_sha != self.commit_sha for f in results)
        all_passed = all(f.status == "PASS" for f in results) and not stale_sha_found and operation_receipt is not None
        wave_verdict = "PASS" if all_passed else "HOLD"
        results.append(
            FidelityFlightResult(
                "Flight E", "Wave Reconvergence", "sage.c2.command_fidelity_wave", wave_verdict,
                hashlib.sha256(f"FlightE:{wave_verdict}:{self.commit_sha}:{timestamp}".encode()).hexdigest(),
                self.commit_sha, {"wave_reconverged": all_passed, "stale_sha_detected": stale_sha_found,
                                  "operation_receipt_present": operation_receipt is not None},
            )
        )
        return CommandFidelityWaveReceipt(
            self.commit_sha, timestamp, results, wave_verdict,
            {"total_flights": 5, "passed_flights": sum(f.status == "PASS" for f in results),
             "wave_verdict": wave_verdict, "stale_sha_detected": stale_sha_found,
             "operation_receipt_present": operation_receipt is not None},
        )
