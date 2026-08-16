"""Core Domain Models for SAGE Airspace / C2 + Capability Progression Subsystem.

Defines Stations, Missions, Sorties (with strict state machine), Intel Telemetry,
CQL/SQL Capability Qualification Registries, XP Progression, and Airspace State.
"""

from datetime import datetime, timezone
from enum import Enum, IntEnum
import hashlib
import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------
# Stations
# ---------------------------------------------------------

class StationID(str, Enum):
    """SAGE Airspace Station Identifiers."""
    MISSION_DIRECTOR = "MISSION_DIRECTOR"
    MISSION_CONTROL = "MISSION_CONTROL"
    INTEL_STATION = "INTEL_STATION"
    ENGINEERING_FLIGHT = "ENGINEERING_FLIGHT"


class Station(BaseModel):
    """Station representation mapping SAGE operational responsibilities."""
    station_id: StationID
    agent_name: str  # Human, GPT, Gemini, Jules
    role_description: str
    current_cql: int = 0  # CQL-0 to CQL-7
    current_sql: int = 0  # SQL-0 to SQL-7 (primarily Intel)
    active_status: bool = True


# ---------------------------------------------------------
# Sortie States & Transitions
# ---------------------------------------------------------

class SortieState(str, Enum):
    """Sortie Lifecycle States."""
    CREATED = "CREATED"
    BRIEFED = "BRIEFED"
    CLEARED = "CLEARED"
    ACTIVE = "ACTIVE"
    EVIDENCE_CAPTURE = "EVIDENCE_CAPTURE"
    DEBRIEF = "DEBRIEF"
    VERIFIED = "VERIFIED"
    CLOSED = "CLOSED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"


VALID_SORTIE_PREDECESSORS: Dict[SortieState, List[Optional[SortieState]]] = {
    SortieState.CREATED: [None],
    SortieState.BRIEFED: [SortieState.CREATED],
    SortieState.CLEARED: [SortieState.BRIEFED],
    SortieState.ACTIVE: [SortieState.CLEARED],
    SortieState.EVIDENCE_CAPTURE: [SortieState.ACTIVE],
    SortieState.DEBRIEF: [SortieState.EVIDENCE_CAPTURE],
    SortieState.VERIFIED: [SortieState.DEBRIEF],
    SortieState.CLOSED: [SortieState.VERIFIED],
    # Terminal/Interrupted states can transition from any non-terminal active state
    SortieState.BLOCKED: [SortieState.CREATED, SortieState.BRIEFED, SortieState.CLEARED, SortieState.ACTIVE, SortieState.EVIDENCE_CAPTURE, SortieState.DEBRIEF],
    SortieState.FAILED: [SortieState.CREATED, SortieState.BRIEFED, SortieState.CLEARED, SortieState.ACTIVE, SortieState.EVIDENCE_CAPTURE, SortieState.DEBRIEF],
    SortieState.ABORTED: [SortieState.CREATED, SortieState.BRIEFED, SortieState.CLEARED, SortieState.ACTIVE, SortieState.EVIDENCE_CAPTURE, SortieState.DEBRIEF],
}


class Mission(BaseModel):
    """Mission Domain Object representing a higher-level goal or campaign."""
    mission_id: str
    mission_name: str
    theater: str  # e.g. "Sports/RCE", "Airspace/C2", "Core Infrastructure"
    priority: str = "P0"
    objective: str
    authorized_scope: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    assigned_stations: List[StationID] = Field(default_factory=list)
    status: str = "ACTIVE"  # CREATED, ACTIVE, PAUSED, COMPLETED, ABORTED
    success_conditions: List[str] = Field(default_factory=list)
    failure_conditions: List[str] = Field(default_factory=list)
    evidence_requirements: List[str] = Field(default_factory=list)
    current_frontier: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Sortie(BaseModel):
    """Sortie Domain Object representing a bounded execution or research unit."""
    sortie_id: str
    mission_id: str
    station: StationID
    objective: str
    target: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    constraints: List[str] = Field(default_factory=list)
    status: SortieState = SortieState.CREATED
    artifacts: List[str] = Field(default_factory=list)
    tests: List[str] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)
    result: Dict[str, Any] = Field(default_factory=dict)
    next_frontier: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def transition_to(self, target_state: SortieState, reason: str = "") -> "Sortie":
        """Executes a state transition for the sortie enforcing strict predecessor rules."""
        allowed_predecessors = VALID_SORTIE_PREDECESSORS.get(target_state, [])
        if self.status not in allowed_predecessors:
            raise ValueError(
                f"Invalid Sortie Transition: Cannot transition from '{self.status.value}' to '{target_state.value}'. "
                f"Allowed predecessors: {[p.value for p in allowed_predecessors if p]}"
            )
        self.status = target_state
        self.updated_at = datetime.now(timezone.utc).isoformat()
        if reason:
            self.result["last_transition_reason"] = reason
        return self


# ---------------------------------------------------------
# Intel Telemetry
# ---------------------------------------------------------

class IntelAssessment(str, Enum):
    """Intel Assessment Enum."""
    CONFIRMED = "CONFIRMED"
    CONTRADICTED = "CONTRADICTED"
    UNKNOWN = "UNKNOWN"
    NEW_OPPORTUNITY = "NEW_OPPORTUNITY"


class IntelTelemetry(BaseModel):
    """Structured Intel Telemetry Object adhering to Gemini's recon specification."""
    telemetry_id: str
    target: str
    vector: str
    assessment: IntelAssessment
    findings: List[str] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)
    adversarial_review: str
    proposed_action: str
    source: Dict[str, str] = Field(default_factory=dict)  # Must include 'type' and ('url' or 'doc' or 'repo')
    contradiction_details: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @model_validator(mode="after")
    def validate_source_and_contradictions(self) -> "IntelTelemetry":
        """Enforces explicit source reference requirements and contradiction preservation."""
        if not self.source or not isinstance(self.source, dict):
            if self.assessment != IntelAssessment.UNKNOWN:
                raise ValueError("Intel Telemetry Failure: Source dictionary required unless assessment is UNKNOWN.")
        else:
            has_valid_source = ("url" in self.source or "doc" in self.source or "repo" in self.source or "api" in self.source)
            if not has_valid_source and self.assessment != IntelAssessment.UNKNOWN:
                raise ValueError("Intel Telemetry Failure: Source must contain url, doc, repo, or api reference.")

        if self.assessment == IntelAssessment.CONTRADICTED and not self.contradiction_details:
            raise ValueError("Intel Telemetry Failure: CONTRADICTED assessment requires contradiction_details.")

        return self


# ---------------------------------------------------------
# Capability Qualification System (CQL & SQL)
# ---------------------------------------------------------

class CQL(IntEnum):
    """Capability Qualification Levels (CQL-0 to CQL-7)."""
    CQL_0_UNQUALIFIED = 0
    CQL_1_CONCEPTUAL = 1
    CQL_2_IMPLEMENTED = 2
    CQL_3_VERIFIED = 3
    CQL_4_OPERATIONAL = 4
    CQL_5_CONTINUOUS = 5
    CQL_6_ADAPTIVE = 6
    CQL_7_FRONTIER = 7


class SQL(IntEnum):
    """Search/Intel Qualification Levels (SQL-0 to SQL-7)."""
    SQL_0_UNQUALIFIED = 0
    SQL_1_CONCEPTUAL = 1
    SQL_2_SEARCH_EXECUTION = 2
    SQL_3_VERIFIED_RECON = 3
    SQL_4_OPERATIONAL_INTELLIGENCE = 4
    SQL_5_CONTINUOUS_INTELLIGENCE = 5
    SQL_6_ADAPTIVE_INTELLIGENCE = 6
    SQL_7_FRONTIER_INTELLIGENCE = 7


class QualificationEvent(BaseModel):
    """Record of a capability qualification advancement."""
    event_id: str
    station_id: StationID
    agent_name: str
    qualification_type: str  # "CQL" or "SQL"
    previous_level: int
    new_level: int
    promotion_reason: str
    evidence_refs: List[str] = Field(default_factory=list)
    test_refs: List[str] = Field(default_factory=list)
    validator: str = "Mission Control"
    downstream_effect: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class QualificationChallengeEvent(BaseModel):
    """Record of a qualification challenge or revocation due to falsifying evidence."""
    challenge_id: str
    station_id: StationID
    qualification_type: str  # "CQL" or "SQL"
    challenged_level: int
    new_level: int
    reason: str
    falsifying_evidence_refs: List[str] = Field(default_factory=list)
    outcome: str = "REVOKED"  # REVOKED or MAINTAINED
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class QualificationRegistry(BaseModel):
    """Registry maintaining capability levels and history for SAGE stations."""
    cql_levels: Dict[StationID, int] = Field(default_factory=lambda: {
        StationID.MISSION_DIRECTOR: 7,
        StationID.MISSION_CONTROL: 4,
        StationID.INTEL_STATION: 3,
        StationID.ENGINEERING_FLIGHT: 4,
    })
    sql_levels: Dict[StationID, int] = Field(default_factory=lambda: {
        StationID.MISSION_DIRECTOR: 7,
        StationID.MISSION_CONTROL: 3,
        StationID.INTEL_STATION: 3,
        StationID.ENGINEERING_FLIGHT: 2,
    })
    promotion_history: List[QualificationEvent] = Field(default_factory=list)
    challenge_history: List[QualificationChallengeEvent] = Field(default_factory=list)

    def promote_station(
        self,
        station_id: StationID,
        agent_name: str,
        qualification_type: str,
        target_level: int,
        reason: str,
        evidence_refs: List[str],
        test_refs: List[str],
        validator: str = "Mission Control",
        downstream_effect: Optional[str] = None,
    ) -> QualificationEvent:
        """Promotes a station's CQL or SQL level if evidence requirements are strictly met."""
        if qualification_type not in ("CQL", "SQL"):
            raise ValueError(f"Invalid qualification_type '{qualification_type}'. Must be 'CQL' or 'SQL'.")

        current_levels = self.cql_levels if qualification_type == "CQL" else self.sql_levels
        current_lvl = current_levels.get(station_id, 0)

        if target_level <= current_lvl:
            raise ValueError(f"Cannot promote to level {target_level} from current level {current_lvl}.")

        # Level skipping prevention
        if target_level > current_lvl + 1:
            raise ValueError(
                f"Level Skipping Rejected: Cannot jump from {qualification_type}-{current_lvl} "
                f"directly to {qualification_type}-{target_level}."
            )

        # Evidence requirements validation
        if target_level >= 2 and not evidence_refs:
            raise ValueError(f"Promotion to {qualification_type}-{target_level} requires evidence_refs.")
        if target_level >= 3 and not test_refs and qualification_type == "CQL":
            raise ValueError(f"Promotion to CQL-{target_level} requires test_refs.")

        event = QualificationEvent(
            event_id=f"qual_evt_{hashlib.sha256(f'{station_id}:{qualification_type}:{target_level}:{datetime.now(timezone.utc).isoformat()}'.encode('utf-8')).hexdigest()[:12]}",
            station_id=station_id,
            agent_name=agent_name,
            qualification_type=qualification_type,
            previous_level=current_lvl,
            new_level=target_level,
            promotion_reason=reason,
            evidence_refs=evidence_refs,
            test_refs=test_refs,
            validator=validator,
            downstream_effect=downstream_effect,
        )

        current_levels[station_id] = target_level
        self.promotion_history.append(event)
        return event

    def challenge_qualification(
        self,
        station_id: StationID,
        qualification_type: str,
        reason: str,
        falsifying_evidence_refs: List[str],
        demotion_target: int,
    ) -> QualificationChallengeEvent:
        """Logs a qualification challenge and demotes the station without erasing promotion history."""
        if not falsifying_evidence_refs:
            raise ValueError("Qualification Challenge Failure: Falsifying evidence references required.")

        current_levels = self.cql_levels if qualification_type == "CQL" else self.sql_levels
        current_lvl = current_levels.get(station_id, 0)

        challenge = QualificationChallengeEvent(
            challenge_id=f"chal_{hashlib.sha256(f'{station_id}:{reason}'.encode('utf-8')).hexdigest()[:12]}",
            station_id=station_id,
            qualification_type=qualification_type,
            challenged_level=current_lvl,
            new_level=demotion_target,
            reason=reason,
            falsifying_evidence_refs=falsifying_evidence_refs,
            outcome="REVOKED" if demotion_target < current_lvl else "MAINTAINED",
        )

        if demotion_target < current_lvl:
            current_levels[station_id] = demotion_target

        self.challenge_history.append(challenge)
        return challenge


# ---------------------------------------------------------
# Game Progression & XP Layer
# ---------------------------------------------------------

class XPCategory(str, Enum):
    """XP Progression Categories."""
    MISSION_XP = "MISSION_XP"
    EVIDENCE_XP = "EVIDENCE_XP"
    CONTINUITY_XP = "CONTINUITY_XP"
    RECON_XP = "RECON_XP"
    ENGINEERING_FLIGHT_XP = "ENGINEERING_FLIGHT_XP"
    FRONTIER_XP = "FRONTIER_XP"


class XPEvent(BaseModel):
    """An XP event awarded for real, verified progress."""
    event_id: str
    station_id: StationID
    category: XPCategory
    amount: int
    reason: str
    verified_event_ref: str  # Must point to a commit, test, receipt, or evidence artifact
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @field_validator("verified_event_ref")
    @classmethod
    def validate_verified_ref(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError("XP Event Rejected: verified_event_ref cannot be empty.")
        return v


class GameProgression(BaseModel):
    """Game Progression tracking accumulated XP and level thresholds derived from verified state."""
    xp_events: List[XPEvent] = Field(default_factory=list)

    def award_xp(
        self,
        station_id: StationID,
        category: XPCategory,
        amount: int,
        reason: str,
        verified_event_ref: str,
    ) -> XPEvent:
        """Awards XP backed strictly by a verified event reference."""
        if amount <= 0:
            raise ValueError("XP Award Rejected: XP amount must be positive.")

        event = XPEvent(
            event_id=f"xp_{hashlib.sha256(f'{station_id}:{category}:{verified_event_ref}'.encode('utf-8')).hexdigest()[:12]}",
            station_id=station_id,
            category=category,
            amount=amount,
            reason=reason,
            verified_event_ref=verified_event_ref,
        )
        self.xp_events.append(event)
        return event

    def get_total_xp_for_station(self, station_id: StationID) -> int:
        return sum(e.amount for e in self.xp_events if e.station_id == station_id)

    def get_total_airspace_xp(self) -> int:
        return sum(e.amount for e in self.xp_events)


# ---------------------------------------------------------
# Overall Airspace State
# ---------------------------------------------------------

class AirspaceState(BaseModel):
    """Master Airspace Observable Operating State."""
    airspace_id: str = "SAGE-AIRSPACE-001"
    session_id: str = "session_airspace_v1"
    mode: str = "OPERATIONAL"  # OPERATIONAL, RESEARCH, AUDIT
    active_mission: Optional[Mission] = None
    active_sorties: List[Sortie] = Field(default_factory=list)
    stations: Dict[StationID, Station] = Field(default_factory=lambda: {
        StationID.MISSION_DIRECTOR: Station(
            station_id=StationID.MISSION_DIRECTOR,
            agent_name="Human Director",
            role_description="Strategic Command & Final Clearance Authority",
            current_cql=7,
            current_sql=7,
        ),
        StationID.MISSION_CONTROL: Station(
            station_id=StationID.MISSION_CONTROL,
            agent_name="GPT",
            role_description="C2 Synthesis & Operational Coordination",
            current_cql=4,
            current_sql=3,
        ),
        StationID.INTEL_STATION: Station(
            station_id=StationID.INTEL_STATION,
            agent_name="Gemini",
            role_description="Recon, Search Telemetry & Adversarial Review",
            current_cql=3,
            current_sql=3,
        ),
        StationID.ENGINEERING_FLIGHT: Station(
            station_id=StationID.ENGINEERING_FLIGHT,
            agent_name="Jules",
            role_description="Engineering Execution & Test Verification",
            current_cql=4,
            current_sql=2,
        ),
    })
    current_frontiers: List[str] = Field(default_factory=list)
    qualification_registry: QualificationRegistry = Field(default_factory=QualificationRegistry)
    game_progression: GameProgression = Field(default_factory=GameProgression)
    recent_evidence: List[str] = Field(default_factory=list)
    next_clearance: str = "Execute Session 3 Airspace Build"
    last_updated: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
