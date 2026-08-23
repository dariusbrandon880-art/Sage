#!/usr/bin/env python3
"""Execute the bounded Flight 003 horizon-residual observation."""
from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

# Ensure repository root is on sys.path reliably
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from sage.experimental.horizon_residual import HorizonEpisode, HorizonResidualAnalyzer


def main() -> int:
    episodes = [
        HorizonEpisode("flight003-short-001", "short", True),
        HorizonEpisode("flight003-short-002", "short", True),
        HorizonEpisode("flight003-long-001", "long", True, retained=True),
        HorizonEpisode("flight003-long-002", "long", False, recovered_after_failure=True),
    ]
    report = HorizonResidualAnalyzer().analyze(episodes)
    payload = {
        "flight": "003",
        "flight_name": "Horizon Residual",
        "observation_only": True,
        "authority_boundary": "descriptive evidence only; never a capability verdict",
        "report": asdict(report),
        "verdict": "OBSERVATION_RECORDED",
    }

    # Persist evidence receipt artifact to evidence_capture/
    evidence_path = repo_root / "evidence_capture" / "flight_003_horizon_residual_evidence.json"
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")

    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
