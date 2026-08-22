#!/usr/bin/env python3
"""Execute the bounded Flight 003 horizon-residual observation."""
from __future__ import annotations

import json
from dataclasses import asdict

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
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
