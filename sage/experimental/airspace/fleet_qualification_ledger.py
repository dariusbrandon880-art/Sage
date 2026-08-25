"""Fleet Qualification Ledger & State Recovery Engine.

Maps verified evidence receipts, test proofs, and XP events to military fleet rank states,
providing state persistence, snapshot exporting, and recovery capabilities.
"""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FleetRankState(BaseModel):
    """Military rank state of an airspace fleet agent."""
    agent_id: str
    rank_title: str = "Cadet"
    total_xp: int = 0
    cql_qualified: bool = False
    sql_qualified: bool = False
    verification_badges: List[str] = Field(default_factory=list)
    last_updated: float = Field(default_factory=time.time)


class FleetQualificationLedger:
    """Ledger tracking fleet agent qualification states and supporting snapshot export/recovery."""

    def __init__(self):
        self._states: Dict[str, FleetRankState] = {}

    def get_or_create_state(self, agent_id: str) -> FleetRankState:
        """Retrieves or initializes rank state for an agent."""
        if agent_id not in self._states:
            self._states[agent_id] = FleetRankState(agent_id=agent_id)
        return self._states[agent_id]

    def record_xp_event(self, agent_id: str, xp_gained: int, badge: Optional[str] = None) -> FleetRankState:
        """Records an XP gain event and updates rank state."""
        state = self.get_or_create_state(agent_id)
        state.total_xp += xp_gained

        if badge and badge not in state.verification_badges:
            state.verification_badges.append(badge)

        # Update rank title based on total XP thresholds
        if state.total_xp >= 1000:
            state.rank_title = "Fleet Commander"
            state.cql_qualified = True
            state.sql_qualified = True
        elif state.total_xp >= 500:
            state.rank_title = "Squadron Leader"
            state.cql_qualified = True
        elif state.total_xp >= 100:
            state.rank_title = "Flight Captain"

        state.last_updated = time.time()
        return state

    def export_snapshot(self) -> str:
        """Exports the complete ledger state as a JSON snapshot string."""
        snapshot_data = {
            "timestamp": time.time(),
            "agents": {agent_id: state.model_dump() for agent_id, state in self._states.items()},
        }
        return json.dumps(snapshot_data, indent=2)

    def recover_from_snapshot(self, snapshot_json: str) -> int:
        """Restores ledger states from a JSON snapshot string."""
        data = json.loads(snapshot_json)
        agents_data = data.get("agents", {})
        restored_count = 0
        for agent_id, agent_dict in agents_data.items():
            self._states[agent_id] = FleetRankState(**agent_dict)
            restored_count += 1
        return restored_count
