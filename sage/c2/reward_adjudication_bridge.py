"""C2 Bridge for SAGE Reward Adjudication (SAGE-RP-1.0).

This module exposes C2-level request dispatch for reward adjudication while
adhering strictly to the SAGE One-Way Import Law via dynamic module resolution.
C2 may request adjudication for verified evidence packets; C2 cannot directly
mint Points or XP.
"""

from __future__ import annotations

import importlib
from typing import Any, Dict, Optional


def request_c2_reward_adjudication(
    report_payload: Dict[str, Any],
    manager: Optional[Any] = None,
    *,
    difficulty: int = 1,
    verification_quality: int = 1,
    impact: int = 1,
    reuse: int = 1,
) -> Dict[str, Any]:
    """Dynamically resolve SAGE RewardAdjudicator and process a report payload."""
    rp_mod = importlib.import_module("sage.experimental.airspace.reward_protocol")
    airspace_mod = importlib.import_module("sage.experimental.airspace.manager")

    if manager is None:
        manager = airspace_mod.AirspaceManager()

    pkt = rp_mod.SAGEEvidencePacket.parse_report_payload(report_payload)
    request = rp_mod.RewardRequest(
        evidence_packet=pkt,
        difficulty=difficulty,
        verification_quality=verification_quality,
        impact=impact,
        reuse=reuse,
    )

    decision = rp_mod.RewardAdjudicator.adjudicate(request, manager)
    return decision.model_payload()
