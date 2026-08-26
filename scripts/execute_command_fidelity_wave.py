#!/usr/bin/env python3
"""Run the recovered five-flight command-fidelity wave against active HEAD."""
from pathlib import Path
import json, os, sys
repo_root=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(repo_root))
from sage.c2.command_fidelity_wave import CommandFidelityWaveDispatcher

def main():
    expected=os.environ.get("SAGE_EXPECTED_COMMIT_SHA")
    dispatcher=CommandFidelityWaveDispatcher(expected)
    receipt=dispatcher.dispatch_wave()
    if expected and receipt.commit_sha != expected:
        raise SystemExit(f"HEAD mismatch: {receipt.commit_sha} != {expected}")
    path=repo_root/"evidence_capture/command_fidelity_wave_evidence.json"
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(receipt.to_dict(),indent=2)+"\n",encoding="utf-8")
    print(f"{receipt.wave_verdict}: {receipt.commit_sha}")
    return 0 if receipt.wave_verdict=="PASS" else 1
if __name__=="__main__": raise SystemExit(main())
