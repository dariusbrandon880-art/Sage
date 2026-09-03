"""Read-only SAGE immersion projections.

This module deliberately consumes canonical AirspaceState and emits only
presentation data: symbols, stacks, tags, and live mission-state glyphs.
The manager-backed organism HUD additionally reconstructs Points and verified
Boss progression from the same append-only Airspace ledger; it never creates a
second source of truth or mutates progression.
"""

from __future__ import annotations

from sage.experimental.airspace.models import AirspaceState, SortieState, StationID
from sage.experimental.airspace.nameplate import STATION_ICONS, STATION_NAMEPLATES
from sage.experimental.airspace.organism_projection import OrganismProjection


CAPABILITY_GLYPHS = {"CQL": "⚙️", "SQL": "🛰️"}

SORTIE_GLYPHS = {
    SortieState.CREATED: "○", SortieState.BRIEFED: "▱", SortieState.CLEARED: "✓",
    SortieState.ACTIVE: "✈️", SortieState.EVIDENCE_CAPTURE: "🛡️", SortieState.DEBRIEF: "▣",
    SortieState.VERIFIED: "⭐", SortieState.CLOSED: "●", SortieState.BLOCKED: "⛔",
    SortieState.FAILED: "⚠️", SortieState.ABORTED: "↩",
}

SGP_RECOMMENDATION_GLYPHS = {"GRAVY": "🎰", "GENUINE_PLUS_EV": "📈", "BOOST_TRAP": "⚠️", "CONDITIONAL_ACCEPT": "🎯"}
PICK_ACTION_GLYPHS = {"POSITIVE_EV": "📈", "EDGE": "⚡", "KELLY": "💰", "LOCKED": "🔒", "WIN": "🏆", "LOSS": "❌", "PUSH": "⏸️", "UNRESOLVED": "🎲"}
CQL_LABELS = {0: "UNQUALIFIED", 1: "CONCEPTUAL", 2: "IMPLEMENTED", 3: "VERIFIED", 4: "OPERATIONAL", 5: "CONTINUOUS", 6: "ADAPTIVE", 7: "FRONTIER"}


def render_capability_stack(state: AirspaceState, station_id: StationID) -> str:
    station = state.stations[station_id]
    cql = max(0, min(7, station.current_cql)); sql = max(0, min(7, station.current_sql))
    return f"CQL {CAPABILITY_GLYPHS['CQL'] * cql or '—'}  SQL {CAPABILITY_GLYPHS['SQL'] * sql or '—'}"


def render_capability_tags(state: AirspaceState, station_id: StationID) -> tuple[str, ...]:
    station = state.stations[station_id]; tags = []
    if station.current_cql > 0: tags.append(f"CQL-{station.current_cql} {CQL_LABELS[station.current_cql]}")
    if station.current_sql > 0: tags.append(f"SQL-{station.current_sql}")
    return tuple(tags)


def render_sortie_glyph(sortie_state: SortieState) -> str:
    return SORTIE_GLYPHS[sortie_state]


def render_live_sortie_strip(state: AirspaceState, *, station_id: StationID | None = None) -> str:
    sorties = state.active_sorties
    if station_id is not None: sorties = [sortie for sortie in sorties if sortie.station == station_id]
    if not sorties: return "NO ACTIVE SORTIES"
    return "  ".join(f"{render_sortie_glyph(sortie.status)} {sortie.station.value} {sortie.status.value}" for sortie in sorties)


def render_immersion_nameplate(state: AirspaceState, station_id: StationID, *, compact: bool = True) -> str:
    station = state.stations[station_id]; xp = state.game_progression.get_total_xp_for_station(station_id)
    icon = STATION_ICONS.get(station_id, "▪"); tags = render_capability_tags(state, station_id)
    stack = render_capability_stack(state, station_id); live = render_live_sortie_strip(state, station_id=station_id)
    identity = f"{STATION_NAMEPLATES[station_id]} {icon} {station.agent_name}"
    if compact:
        return f"{identity} // CQL-{station.current_cql} // SQL-{station.current_sql} // XP {xp} // {stack} // {' | '.join(tags) if tags else 'UNQUALIFIED'} // {live}"
    return f"{identity}\n  ROLE      : {station.role_description}\n  XP        : {xp}\n  STACK     : {stack}\n  QUALIFIED : {' | '.join(tags) if tags else 'UNQUALIFIED'}\n  SORTIES   : {live}"


def render_sgp_boost_glyph(recommendation: str) -> str:
    return SGP_RECOMMENDATION_GLYPHS.get(recommendation.upper(), "🎯")


def render_sports_pick_action_strip(*, player_or_selection: str, market_or_category: str, projected_prob: float, fd_price: float, expected_value: float, edge_score: float, kelly_stake: float, recommendation: str = "GENUINE_PLUS_EV", lock_verified: bool = True, outcome_status: str = "UNRESOLVED") -> str:
    boost_glyph = render_sgp_boost_glyph(recommendation); ev_glyph = PICK_ACTION_GLYPHS["POSITIVE_EV"] if expected_value > 0 else "📉"; lock_glyph = PICK_ACTION_GLYPHS["LOCKED"] if lock_verified else "🔓"
    outcome_glyph = {"WIN": PICK_ACTION_GLYPHS["WIN"], "LOSS": PICK_ACTION_GLYPHS["LOSS"], "PUSH": PICK_ACTION_GLYPHS["PUSH"]}.get(outcome_status.upper(), PICK_ACTION_GLYPHS["UNRESOLVED"])
    return f"{boost_glyph} PICK [{player_or_selection} | {market_or_category}] @ {fd_price:.2f} | PROB {projected_prob:.1%} | EV {ev_glyph} {expected_value:+.2%} | EDGE {PICK_ACTION_GLYPHS['EDGE']} {edge_score:+.2%} | KELLY {PICK_ACTION_GLYPHS['KELLY']} {kelly_stake:.2%} | LOCK {lock_glyph} | STATUS {outcome_glyph} {outcome_status}"


def render_strike_feed(state: AirspaceState) -> str:
    lines = ["━" * 42, "04 — STRIKE FEED // HIGH-TEMPO EVENTS", "━" * 42]
    lines.append(f"🎯 TARGET ACQUIRED // {state.current_frontiers[-1] if state.current_frontiers else 'SYSTEM INITIALIZATION'}")
    if state.active_sorties:
        latest = state.active_sorties[-1]; lines.append(f"⚡ MARINE STRIKE    // {render_sortie_glyph(latest.status)} [{latest.sortie_id}] {latest.station.value}"); lines.append(f"   target: {latest.target[:36]}")
    if state.recent_evidence:
        lines.append(f"🛡️ EVIDENCE CAPTURED// {state.recent_evidence[-1][:36]}"); lines.append("✓ HIT CONFIRMED    // Real evidence landed")
    lines.append(f"→ NEXT TARGET      // {state.next_clearance[:36]}"); lines.append("━" * 42)
    return "\n".join(lines)


def render_four_layer_hud(state: AirspaceState) -> str:
    lines = ["01 — COMMAND BAND", "━" * 42]
    c2 = state.stations.get(StationID.MISSION_CONTROL); c2_cql = c2.current_cql if c2 else 0; c2_sql = c2.current_sql if c2 else 0
    lines += ["[SAGE::C2::CHATGPT] ◈ C2 MISSION CONTROL", f"STATUS   : {state.mode}", f"QUAL     : CQL-{c2_cql} | SQL-{c2_sql}"]
    if state.active_mission: lines += [f"MISSION  : {state.active_mission.mission_id} [{state.active_mission.priority}]", f"THEATER  : {state.active_mission.theater}"]
    else: lines.append("MISSION  : NONE ACTIVE")
    lines += ["\n02 — OPERATING PICTURE", "─" * 42]
    if state.active_sorties:
        lines.append("ACTIVE SORTIES:")
        for s in state.active_sorties[-3:]: lines.append(f" {render_sortie_glyph(s.status)} [{s.sortie_id}] {s.station.value:<12} {s.status.value}")
    else: lines.append("ACTIVE SORTIES: NONE ACTIVE")
    lines += ["\n03 — PROGRESSION / IMPACT", "─" * 42, f"TOTAL SYSTEM XP : {state.game_progression.get_total_airspace_xp()}"]
    for st_id, station in state.stations.items(): lines.append(f" ▪ {st_id.value:<12} XP {state.game_progression.get_total_xp_for_station(st_id):<5} {render_capability_stack(state, st_id)}")
    lines += ["\n" + render_strike_feed(state)]
    return "\n".join(lines)


def render_four_layer_hud_from_manager(manager, *, status: str = "READY") -> str:
    """Render the operational HUD with the full organism progression roster."""
    state = manager.reconstruct_airspace_state()
    hud = render_four_layer_hud(state)
    roster = OrganismProjection.render_roster(manager, state, status=status)
    return f"{hud}\n\n05 — ORGANISM PROGRESSION\n{'─' * 42}\n{roster}"
