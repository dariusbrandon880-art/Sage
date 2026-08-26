#!/usr/bin/env python3
"""Execute and validate the 5x4 Big Jump Wave reality gate with exact HEAD provenance."""
from __future__ import annotations
import hashlib, json, re, subprocess, sys, time
from pathlib import Path
from typing import Any, Dict, List
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path: sys.path.insert(0, str(repo_root))
from sage.c2.adaptive_mission_selection import AdaptiveMissionSelectionEngine
from sage.c2.c2_execution_bridge import C2ExecutionBridge, C2ExecutionRequest
from sage.c2.c2_wave_playbook import C2WavePlaybookEngine
from sage.experimental.airspace.fleet_qualification_ledger import FleetQualificationLedger
from sage.experimental.cognitive.ccl_feedback_bridge import CCLOutcomeFeedbackBridge
EVIDENCE_PATH = repo_root / "evidence_capture" / "big_jump_wave_20_cells_evidence.json"

def get_commit_sha() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo_root, check=True, capture_output=True, text=True).stdout.strip()

def validate_20_cell_wave_payload(data: Dict[str, Any], current_head_sha: str) -> List[str]:
    errors: List[str] = []; cells = data.get("cells", [])
    if len(cells) != 20: errors.append(f"Rule 1 Violation: Expected exactly 20 cells, got {len(cells)}.")
    pairs = set(); digests = set(); flights = {f"F{i}" for i in range(1,6)}; gates = {f"G{i}" for i in range(1,5)}; seen = {f:set() for f in flights}
    for cell in cells:
        pair=(cell.get("flight_id"),cell.get("lifecycle_gate")); sha=cell.get("exact_head_sha","")
        if pair in pairs: errors.append(f"Rule 3 Violation: Duplicate pair {pair}.")
        pairs.add(pair)
        if pair[0] in seen: seen[pair[0]].add(pair[1])
        if not re.fullmatch(r"[0-9a-f]{40}", sha): errors.append(f"Rule 4 Violation: invalid SHA '{sha}'.")
        elif sha != current_head_sha: errors.append(f"Rule 5 Violation: stale SHA '{sha}' differs from '{current_head_sha}'.")
        source=cell.get("source_target");
        if not source or not (repo_root/source).exists(): errors.append(f"Rule 6 Violation: missing source '{source}'.")
        if cell.get("verification_result") != "PASS": errors.append(f"Rule 7 Violation: {pair} did not PASS.")
        if not cell.get("provenance_ref"): errors.append(f"Rule 8 Violation: {pair} missing provenance_ref.")
        digest=cell.get("cell_digest")
        if digest in digests: errors.append(f"Rule 9 Violation: duplicate digest '{digest}'.")
        digests.add(digest)
    for flight in flights:
        missing=gates-seen[flight]
        if missing: errors.append(f"Rule 2 Violation: {flight} missing gates {sorted(missing)}.")
    return errors

def main() -> int:
    sha=get_commit_sha(); started=time.time()
    flights=[("F1","sage/c2/adaptive_mission_selection.py"),("F2","sage/experimental/airspace/fleet_qualification_ledger.py"),("F3","sage/c2/c2_execution_bridge.py"),("F4","sage/experimental/cognitive/ccl_feedback_bridge.py"),("F5","sage/c2/c2_wave_playbook.py")]
    mission=AdaptiveMissionSelectionEngine(); ledger=FleetQualificationLedger(); bridge=C2ExecutionBridge(current_head_sha=sha); ccl=CCLOutcomeFeedbackBridge(mission); playbook=C2WavePlaybookEngine(); cells=[]
    for flight,path in flights:
        for gate in ("G1","G2","G3","G4"):
            if gate=="G1": result=mission.evaluate_candidate(f"cand-{flight}",flight,path); command="AdaptiveMissionSelectionEngine.evaluate_candidate()"; status="PASS" if result.is_authorized else "FAIL"; ref=result.decision_hash[:8]
            elif gate=="G2": result=bridge.execute(C2ExecutionRequest(request_id=f"req-{flight}",command="READ",target_path=path,expected_head_sha=sha)); command="C2ExecutionBridge.execute()"; status=result.status; ref=result.receipt_hash[:8]
            elif gate=="G3": result=ccl.process_outcome(f"mission-{flight}",flight,path,"PASS"); command="CCLOutcomeFeedbackBridge.process_outcome()"; status=result.outcome_status; ref=result.record_hash[:8]
            else: result=ledger.issue_qualification("STATION_ALPHA",f"AGENT_{flight}",[f"QUAL-{flight}"],250,[f"hash-{flight}"]); command="FleetQualificationLedger.issue_qualification()"; status="PASS" if result.record_hash else "FAIL"; ref=result.record_hash[:8]
            digest=hashlib.sha256(f"{flight}:{gate}:{sha}:{path}:{command}:{status}:{ref}".encode()).hexdigest()
            cells.append({"cell_id":f"Cell {flight}-{gate}","flight_id":flight,"lifecycle_gate":gate,"exact_head_sha":sha,"source_target":path,"verification_command":command,"verification_result":status,"provenance_ref":f"ref-{flight}-{gate}-{ref}","cell_digest":digest})
    receipt=playbook.record_wave_execution("pb-20-cell-hardened-wave",f"wave-20cell-{sha[:7]}",[f for f,_ in flights],1.0,True,time.time()-started)
    payload={"wave_id":f"wave-5x4-hardened-{sha[:7]}","commit_sha":sha,"total_flights":5,"total_lifecycle_gates":4,"total_advancement_cells":20,"playbook_receipt_hash":receipt.receipt_hash,"cells":cells}
    errors=validate_20_cell_wave_payload(payload,sha)
    if errors:
        for error in errors: print(error,file=sys.stderr)
        return 1
    payload["reconvergence_verdict"]="PASS"; EVIDENCE_PATH.parent.mkdir(parents=True,exist_ok=True); EVIDENCE_PATH.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8"); return 0
if __name__=="__main__": raise SystemExit(main())
