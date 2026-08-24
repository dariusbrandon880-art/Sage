"""Agent Identity HUD Projection Subsystem.

Projects a formatted, ASCII/text-based Command Center Identity Badge for display
in ChatGPT / agent chat interfaces, exposing agent call sign, station role,
CQL/SQL qualification levels, active mission, readiness status, and verified evidence count.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib


@dataclass(frozen=True)
class AgentHUDIdentity:
    call_sign: str             # e.g., "Jules", "GPT", "Gemini", "Human Director"
    station_id: str            # "ENGINEERING_FLIGHT", "MISSION_CONTROL", etc.
    station_role: str          # "Engineering Execution & Verification Lead"
    cql_level: int             # Capability Qualification Level (0-7)
    sql_level: int             # Search Qualification Level (0-7)
    active_mission_id: str     # e.g., "Big Strike: Frontier Intelligence & Immersion"
    fleet_readiness_status: str # "READY", "DEGRADED", "UNQUALIFIED"
    verified_evidence_count: int


class AgentHUDProjectionEngine:
    """Renders formatted Command Center Identity Badges for agent chat interfaces."""

    @staticmethod
    def render_identity_badge(identity: AgentHUDIdentity) -> str:
        """Render a formatted, high-visibility Command Center Identity Badge."""
        cql_str = f"CQL-{identity.cql_level}"
        sql_str = f"SQL-{identity.sql_level}"
        badge_header = f"═══ [ SAGE COMMAND CENTER :: {identity.call_sign.upper()} ] ═══"

        line = "═" * len(badge_header)

        badge = (
            f"{line}\n"
            f"{badge_header}\n"
            f"  • Call Sign        : {identity.call_sign}\n"
            f"  • Station ID       : {identity.station_id}\n"
            f"  • Role             : {identity.station_role}\n"
            f"  • Qualification    : {cql_str} / {sql_str}\n"
            f"  • Active Mission   : {identity.active_mission_id}\n"
            f"  • Fleet Readiness  : {identity.fleet_readiness_status}\n"
            f"  • Evidence Count   : {identity.verified_evidence_count} verified receipts\n"
            f"{line}"
        )
        return badge

    @staticmethod
    def generate_chat_greeting(identity: AgentHUDIdentity) -> str:
        """Generate a rehydrated chat turn header prefix for continuous immersion."""
        badge = AgentHUDProjectionEngine.render_identity_badge(identity)
        return f"{badge}\n\n[{identity.call_sign} :: Station {identity.station_id} active and standing by for C2 flight orders.]"
