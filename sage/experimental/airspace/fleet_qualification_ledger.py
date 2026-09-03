"""Legacy fleet qualification snapshot/recovery compatibility layer.

Canonical career progression is owned by the Airspace event/progression substrate.
This legacy ledger remains available for snapshot/recovery compatibility, but it
must not mint XP, assign rank, or infer qualification from raw XP. Those operations
are deliberately fail-closed so stale direct-XP behavior cannot silently reappear.
"""

from __future__ import annotations

import json
import time
from typing import Dict

from pydantic import BaseModel, Field


class FleetRankState(BaseModel):
    """Historical fleet state retained for compatibility and snapshot recovery."""

    agent_id: str
    rank_title: str = "Cadet"
    total_xp: int = 0
    cql_qualified: bool = False
    sql_qualified: bool = False
    verification_badges: list[str] = Field(default_factory=list)
    last_updated: float = Field(default_factory=time.time)


class FleetQualificationLedger:
    """Legacy snapshot/recovery surface with direct progression mutation disabled."""

    def __init__(self) -> None:
        self._states: Dict[str, FleetRankState] = {}

    def get_or_create_state(self, agent_id: str) -> FleetRankState:
        """Retrieve or initialize a historical compatibility state."""
        if agent_id not in self._states:
            self._states[agent_id] = FleetRankState(agent_id=agent_id)
        return self._states[agent_id]

    def record_xp_event(self, agent_id: str, xp_gained: int, badge: str | None = None) -> FleetRankState:
        """Reject the obsolete direct-XP/rank mutation path.

        Career XP must enter through verified Points and the canonical Airspace
        event ledger. Rank and qualification are governed projections, not side
        effects of a raw XP increment.
        """
        raise RuntimeError(
            "Direct FleetQualificationLedger XP mutation is disabled; "
            "use the canonical verified-event Points -> XP progression path."
        )

    def export_snapshot(self) -> str:
        """Export historical compatibility state for recovery."""
        snapshot_data = {
            "timestamp": time.time(),
            "agents": {agent_id: state.model_dump() for agent_id, state in self._states.items()},
        }
        return json.dumps(snapshot_data, indent=2)

    def recover_from_snapshot(self, snapshot_json: str) -> int:
        """Restore historical states without recalculating rank or qualification."""
        data = json.loads(snapshot_json)
        agents_data = data.get("agents", {})
        restored_count = 0
        for agent_id, agent_dict in agents_data.items():
            self._states[agent_id] = FleetRankState(**agent_dict)
            restored_count += 1
        return restored_count
