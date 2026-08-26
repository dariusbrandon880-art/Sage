"""Five-flight Command Fidelity + Reality Gate dispatcher."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
import hashlib, json, subprocess, time
from pathlib import Path
from typing import Any, Dict, List, Optional
from sage.c2.claim_provenance import ClaimProvenanceCompiler
from sage.c2.directive_fidelity import DirectiveFingerprint, ExactOrderSentinel
from sage.c2.drift_sentinel import DriftReplayScenario, DriftSentinel
from sage.c2.reality_gate import OperationalClaim, RealityGate, SourceReceipt

def _get_current_commit_sha() -> str:
    result=subprocess.run(["git","rev-parse","HEAD"],capture_output=True,text=True,check=True)
    sha=result.stdout.strip()
    if len(sha)!=40: raise RuntimeError(f"invalid active HEAD SHA: {sha!r}")
    return sha

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
    summary: Dict[str, Any]=field(default_factory=dict)
    def to_dict(self): return {"commit_sha":self.commit_sha,"timestamp_utc":self.timestamp_utc,"flight_results":[asdict(f) for f in self.flight_results],"wave_verdict":self.wave_verdict,"summary":self.summary}

class CommandFidelityWaveDispatcher:
    def __init__(self, commit_sha: Optional[str]=None): self.commit_sha=commit_sha or _get_current_commit_sha()
    @classmethod
    def validate_persisted_evidence(cls,evidence_path: str|Path,expected_commit_sha: Optional[str]=None)->bool:
        data=json.loads(Path(evidence_path).read_text(encoding="utf-8")); target=expected_commit_sha or _get_current_commit_sha()
        return data.get("wave_verdict")=="PASS" and data.get("commit_sha")==target and all(f.get("commit_sha")==target and f.get("status")=="PASS" for f in data.get("flight_results",[]))
    def dispatch_wave(self)->CommandFidelityWaveReceipt:
        timestamp=time.time(); results=[]
        raw="Check live repo.\nInspect PR.\nRun verification.\nDo not merge."
        contract=DirectiveFingerprint.create_contract(raw)
        valid=ExactOrderSentinel.validate_plan(contract,["Check live repo","Inspect PR","Run verification"])
        invalid=ExactOrderSentinel.validate_plan(contract,["Check live repo","Merge PR"])
        status="PASS" if valid.is_valid and not invalid.is_valid else "HOLD"
        digest=hashlib.sha256(f"A:{contract.raw_instruction_hash}:{self.commit_sha}:{status}".encode()).hexdigest()
        results.append(FidelityFlightResult("Flight A","Directive Fidelity","sage.c2.directive_fidelity",status,digest,self.commit_sha,{"valid_plan_passed":valid.is_valid,"invalid_plan_blocked":not invalid.is_valid}))
        receipt=SourceReceipt("github",f"commit:{self.commit_sha}",self.commit_sha,timestamp)
        claim=OperationalClaim("c1",f"GitHub main is at {self.commit_sha}","github",f"commit:{self.commit_sha}")
        gate=RealityGate.evaluate_claims([claim],[receipt])
        status="PASS" if gate.is_permitted else "HOLD"; digest=hashlib.sha256(f"B:{self.commit_sha}:{status}".encode()).hexdigest()
        results.append(FidelityFlightResult("Flight B","Reality Gate","sage.c2.reality_gate",status,digest,self.commit_sha,{"permitted_claims_count":len(gate.permitted_claims)}))
        compiled=ClaimProvenanceCompiler.compile_claims([claim],[receipt]); status="PASS" if compiled.is_valid else "HOLD"; digest=hashlib.sha256(f"C:{self.commit_sha}:{status}".encode()).hexdigest()
        results.append(FidelityFlightResult("Flight C","Claim Provenance Compiler","sage.c2.claim_provenance",status,digest,self.commit_sha,{"verified_claims_count":len(compiled.verified_claims)}))
        scenario=DriftReplayScenario("dispatch",raw,contract,("Check live repo","Inspect PR","Run verification"),(claim,),(receipt,),True)
        drift=DriftSentinel.run_suite([scenario]); status="PASS" if drift.metrics.overall_drift_rate==0 else "HOLD"; digest=hashlib.sha256(f"D:{self.commit_sha}:{status}".encode()).hexdigest()
        results.append(FidelityFlightResult("Flight D","Fresh-Session Drift Sentinel","sage.c2.drift_sentinel",status,digest,self.commit_sha,asdict(drift.metrics)))
        wave="PASS" if all(r.status=="PASS" for r in results) else "HOLD"; digest=hashlib.sha256(f"E:{self.commit_sha}:{wave}:{timestamp}".encode()).hexdigest()
        results.append(FidelityFlightResult("Flight E","Wave Reconvergence","sage.c2.command_fidelity_wave",wave,digest,self.commit_sha,{"wave_reconverged":wave=="PASS"}))
        return CommandFidelityWaveReceipt(self.commit_sha,timestamp,results,wave,{"total_flights":5,"passed_flights":sum(r.status=="PASS" for r in results)})
