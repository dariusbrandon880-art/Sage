"""SAGE Reward & Evidence Protocol v1 (SAGE-RP-1.0) and Autonomous RewardAdjudicator.

This module formalizes the SAGE scoring constitution, machine-readable SEP/1
evidence packet ingestion, contribution-versus-outcome attribution ledgers,
and deterministic reward adjudication.

SAGE REWARD LAW:
1. Reward formulas are versioned (SAGE-RP-1.0).
2. Historical rewards are never recalculated under a newer formula.
3. Every reward references the protocol version used.
4. Every reward references immutable evidence.
5. Every reward has a deterministic settlement ID.
6. Duplicate evidence cannot mint duplicate reward.
7. C2 cannot directly mint Points or XP.
8. Models cannot directly mint Points or XP.
9. Human-readable reports cannot override structured evidence.
10. Formula changes require governed protocol promotion.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from sage.experimental.airspace.boss_progression import (
    BOSS_BADGE_CADENCE,
    BossClass,
    BossOutcome,
    BossProgressionAuthority,
)
from sage.experimental.airspace.manager import AirspaceManager
from sage.experimental.airspace.models import StationID, XPCategory
from sage.experimental.airspace.points_xp_economy import (
    BASE_POINTS,
    PointEventType,
    PointsXPEconomy,
)


SCORING_PROTOCOL_VERSION: str = "SAGE-RP-1.0"
SAGE_SEP_VERSION: str = "SAGE-SEP/1"
POINTS_PER_XP: int = 10

HEX_SHA40 = re.compile(r"^[0-9a-fA-F]{40}$")
SHA256_DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-fA-F]{64}$")


def resolve_station_id(val: Any) -> StationID:
    """Resolve agent nameplate or station string into canonical StationID."""
    if isinstance(val, StationID):
        return val
    s = str(val).upper().strip()
    alias_map = {
        "CHATGPT_C2": StationID.MISSION_CONTROL,
        "CHATGPT": StationID.MISSION_CONTROL,
        "C2": StationID.MISSION_CONTROL,
        "MISSION_CONTROL": StationID.MISSION_CONTROL,
        "JULES": StationID.ENGINEERING_FLIGHT,
        "ENGINEERING_FLIGHT": StationID.ENGINEERING_FLIGHT,
        "GEMINI": StationID.INTEL_STATION,
        "INTEL_STATION": StationID.INTEL_STATION,
        "HUMAN": StationID.MISSION_DIRECTOR,
        "MISSION_DIRECTOR": StationID.MISSION_DIRECTOR,
    }
    if s in alias_map:
        return alias_map[s]
    try:
        return StationID(s)
    except ValueError:
        return StationID.MISSION_CONTROL


def verify_git_commit_exists(commit_sha: str) -> bool:
    """Independently verify that a 40-character commit SHA exists in git object database."""
    if not HEX_SHA40.fullmatch(commit_sha):
        return False
    try:
        res = subprocess.run(
            ["git", "cat-file", "-e", f"{commit_sha}^{{commit}}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=2.0,
        )
        return res.returncode == 0
    except Exception:
        return False


@dataclass(frozen=True)
class ContributionUnit:
    """Demonstrable contribution toward an outcome."""

    actor: StationID
    role: str
    contribution_type: str
    share_weight: float
    claim_ref: str
    actor_nameplate: str = ""

    def __post_init__(self) -> None:
        if not self.actor_nameplate:
            object.__setattr__(self, "actor_nameplate", str(self.actor))

        if not math.isfinite(self.share_weight) or self.share_weight <= 0.0:
            raise ValueError(f"ContributionUnit share_weight must be a positive finite number, got {self.share_weight}.")

        resolved_from_actor = resolve_station_id(self.actor)
        resolved_from_nameplate = resolve_station_id(self.actor_nameplate)
        if resolved_from_actor != resolved_from_nameplate:
            raise ValueError(
                f"Attribution mismatch: actor '{self.actor}' ({resolved_from_actor.value}) "
                f"conflicts with nameplate '{self.actor_nameplate}' ({resolved_from_nameplate.value})."
            )

        object.__setattr__(self, "actor", resolved_from_actor)

        if not self.role.strip():
            raise ValueError("ContributionUnit requires a non-empty role.")
        if not self.contribution_type.strip():
            raise ValueError("ContributionUnit requires a non-empty contribution_type.")
        if not self.claim_ref.strip():
            raise ValueError("ContributionUnit claim_ref is required.")

    def model_payload(self) -> Dict[str, Any]:
        return {
            "actor": self.actor.value,
            "actor_nameplate": self.actor_nameplate,
            "role": self.role,
            "contribution_type": self.contribution_type,
            "share_weight": self.share_weight,
            "claim_ref": self.claim_ref,
        }


@dataclass(frozen=True)
class SAGEEvidencePacket:
    """Machine-readable evidence packet (SEP/1 protocol)."""

    protocol: str
    mission_id: str
    subject_repo: str
    target_sha: str
    observed_sha: str
    claim_type: str
    claim_statement: str
    primary_actor: StationID
    supporting_agents: Tuple[StationID, ...]
    contributions: Tuple[ContributionUnit, ...]
    evidence_refs: Tuple[str, ...]
    verification_status: str  # VERIFIED, FAILED, HOLD, REJECTED
    outcome_type: PointEventType
    boss_class: Optional[BossClass] = None
    integrity_digest: str = ""
    reward_requested: bool = True
    protocol_version: str = "1.0"
    primary_actor_nameplate: str = ""

    def __post_init__(self) -> None:
        if self.protocol not in (SAGE_SEP_VERSION, "SEP/1", "SAGE-SEP/1"):
            raise ValueError(f"Invalid evidence protocol: {self.protocol}")
        if not self.mission_id.strip():
            raise ValueError("SAGEEvidencePacket mission_id is required.")
        if not HEX_SHA40.fullmatch(self.target_sha):
            raise ValueError("SAGEEvidencePacket target_sha must be a 40-character commit SHA.")
        if not HEX_SHA40.fullmatch(self.observed_sha):
            raise ValueError("SAGEEvidencePacket observed_sha must be a 40-character commit SHA.")
        if self.target_sha != self.observed_sha:
            raise ValueError(f"SHA mismatch: target_sha ({self.target_sha}) != observed_sha ({self.observed_sha})")

        # Verify target SHA actually exists in git repository object database
        if not verify_git_commit_exists(self.target_sha):
            raise ValueError(f"Target commit SHA {self.target_sha} does not exist in repository history.")

        if not self.primary_actor_nameplate:
            object.__setattr__(self, "primary_actor_nameplate", str(self.primary_actor))
        resolved_primary = resolve_station_id(self.primary_actor)
        object.__setattr__(self, "primary_actor", resolved_primary)

        resolved_supporting = tuple(resolve_station_id(a) for a in self.supporting_agents)
        object.__setattr__(self, "supporting_agents", resolved_supporting)

        # Validate contribution unit collisions
        seen_stations = set()
        seen_nameplates = set()
        for c in self.contributions:
            st = c.actor.value
            np = c.actor_nameplate.upper().strip()
            if st in seen_stations or np in seen_nameplates:
                raise ValueError(f"Duplicate contribution unit collision for actor/nameplate: {c.actor_nameplate} ({st})")
            seen_stations.add(st)
            seen_nameplates.add(np)

        if not self.evidence_refs:
            raise ValueError("SAGEEvidencePacket evidence_refs must not be empty.")

        # Compute canonical sha256: digest if empty
        if not self.integrity_digest:
            digest_str = hashlib.sha256(
                f"{self.mission_id}:{self.target_sha}:{self.claim_statement}:{':'.join(self.evidence_refs)}".encode("utf-8")
            ).hexdigest()
            object.__setattr__(self, "integrity_digest", f"sha256:{digest_str}")

        # Validate integrity digest uses strict sha256:<64 hex> format
        if not SHA256_DIGEST_PATTERN.fullmatch(self.integrity_digest):
            raise ValueError(f"Integrity digest must strictly match sha256:<64 hex chars>, got '{self.integrity_digest}'.")

    @classmethod
    def parse_report_payload(cls, raw: Dict[str, Any]) -> SAGEEvidencePacket:
        """Parse structured report or dictionary into SAGEEvidencePacket."""
        protocol = raw.get("protocol", "SAGE-SEP/1")
        mission_id = raw.get("mission_id", "UNKNOWN_MISSION")
        subject = raw.get("subject", {})
        repo = subject.get("repository", raw.get("subject_repo", "dariusbrandon880-art/Sage"))
        target_sha = subject.get("commit", raw.get("target_sha", ""))
        observed_sha = raw.get("observed_sha", target_sha)

        claim = raw.get("claim", {})
        claim_type = claim.get("type", raw.get("claim_type", "verified_repair"))
        claim_statement = claim.get("statement", raw.get("claim_statement", "Verified mission execution"))

        execution = raw.get("execution", {})
        primary_actor_str = execution.get("actor", raw.get("primary_actor", "CHATGPT_C2"))
        primary_actor = resolve_station_id(primary_actor_str)

        supporting_raw = execution.get("supporting_agents", raw.get("supporting_agents", []))
        supporting_agents = tuple(resolve_station_id(a) for a in supporting_raw)

        raw_contributions = raw.get("contributions", [])
        parsed_contributions = []
        for c in raw_contributions:
            parsed_contributions.append(
                ContributionUnit(
                    actor=resolve_station_id(c["actor"]),
                    actor_nameplate=str(c["actor"]),
                    role=str(c["role"]),
                    contribution_type=str(c["contribution_type"]),
                    share_weight=float(c.get("share_weight", 1.0)),
                    claim_ref=str(c.get("claim_ref", mission_id)),
                )
            )

        verification = raw.get("verification", {})
        v_status = verification.get("status", raw.get("verification_status", "HOLD"))

        outcome = raw.get("outcome", {})
        outcome_type_str = outcome.get("type", raw.get("outcome_type", "REPAIR"))
        outcome_type = PointEventType(outcome_type_str)

        boss_class_val = outcome.get("boss_class", raw.get("boss_class"))
        boss_class = BossClass(boss_class_val) if boss_class_val else None

        evidence_list = raw.get("evidence", raw.get("evidence_refs", ["exact_head_ci"]))
        evidence_refs = tuple(str(e) for e in evidence_list)

        integrity = raw.get("integrity", {})
        integrity_digest = integrity.get("digest", raw.get("integrity_digest", ""))

        reward = raw.get("reward", {})
        reward_requested = reward.get("requested", raw.get("reward_requested", True))

        return cls(
            protocol=protocol,
            mission_id=mission_id,
            subject_repo=repo,
            target_sha=target_sha,
            observed_sha=observed_sha,
            claim_type=claim_type,
            claim_statement=claim_statement,
            primary_actor=primary_actor,
            primary_actor_nameplate=str(primary_actor_str),
            supporting_agents=supporting_agents,
            contributions=tuple(parsed_contributions),
            evidence_refs=evidence_refs,
            verification_status=v_status,
            outcome_type=outcome_type,
            boss_class=boss_class,
            integrity_digest=integrity_digest,
            reward_requested=reward_requested,
        )

    def model_payload(self) -> Dict[str, Any]:
        return {
            "protocol": self.protocol,
            "mission_id": self.mission_id,
            "subject_repo": self.subject_repo,
            "target_sha": self.target_sha,
            "observed_sha": self.observed_sha,
            "claim_type": self.claim_type,
            "claim_statement": self.claim_statement,
            "primary_actor": self.primary_actor.value,
            "primary_actor_nameplate": self.primary_actor_nameplate,
            "supporting_agents": [a.value for a in self.supporting_agents],
            "contributions": [c.model_payload() for c in self.contributions],
            "evidence_refs": list(self.evidence_refs),
            "verification_status": self.verification_status,
            "outcome_type": self.outcome_type.value,
            "boss_class": self.boss_class.value if self.boss_class else None,
            "integrity_digest": self.integrity_digest,
            "reward_requested": self.reward_requested,
        }


@dataclass(frozen=True)
class RewardRequest:
    """Formal request for reward adjudication submitted to SAGE RewardAdjudicator."""

    evidence_packet: SAGEEvidencePacket
    protocol_version: str = SCORING_PROTOCOL_VERSION
    difficulty: int = 1
    verification_quality: int = 1
    impact: int = 1
    reuse: int = 1
    causal_parent_refs: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.protocol_version != SCORING_PROTOCOL_VERSION:
            raise ValueError(
                f"Protocol version mismatch: request {self.protocol_version} != {SCORING_PROTOCOL_VERSION}"
            )
        for name, val in (
            ("difficulty", self.difficulty),
            ("verification_quality", self.verification_quality),
            ("impact", self.impact),
            ("reuse", self.reuse),
        ):
            if val < 1 or val > 5:
                raise ValueError(f"{name} must be between 1 and 5")


@dataclass(frozen=True)
class RewardDecision:
    """Canonical settlement result from SAGE RewardAdjudicator."""

    protocol_version: str
    settlement_id: str
    mission_id: str
    primary_actor: StationID
    outcome_type: PointEventType
    base_points: int
    multiplier: float
    outcome_point_pool: int
    attributed_points: Dict[str, int]
    attribution_status: str  # VERIFIED_ATTRIBUTION, ATTRIBUTION_INDETERMINATE
    xp_before: int
    xp_minted: int
    xp_after: int
    badge_awards: Tuple[str, ...]
    rank: str
    promotion_eligibility: bool
    conservation_check_passed: bool
    idempotency_check_passed: bool
    evidence_digest: str
    timestamp: float = field(default_factory=time.time)
    receipt_header_text: str = ""

    def model_payload(self) -> Dict[str, Any]:
        return {
            "protocol_version": self.protocol_version,
            "settlement_id": self.settlement_id,
            "mission_id": self.mission_id,
            "primary_actor": self.primary_actor.value,
            "outcome_type": self.outcome_type.value,
            "base_points": self.base_points,
            "multiplier": self.multiplier,
            "outcome_point_pool": self.outcome_point_pool,
            "attributed_points": self.attributed_points,
            "attribution_status": self.attribution_status,
            "xp_before": self.xp_before,
            "xp_minted": self.xp_minted,
            "xp_after": self.xp_after,
            "badge_awards": list(self.badge_awards),
            "rank": self.rank,
            "promotion_eligibility": self.promotion_eligibility,
            "conservation_check_passed": self.conservation_check_passed,
            "idempotency_check_passed": self.idempotency_check_passed,
            "evidence_digest": self.evidence_digest,
            "timestamp": self.timestamp,
        }


class RewardAdjudicator:
    """Autonomous, deterministic SAGE Reward Adjudicator."""

    @classmethod
    def calculate_settlement_id(
        cls,
        protocol_version: str,
        mission_id: str,
        target_sha: str,
        outcome_type: PointEventType,
        primary_actor: StationID,
        evidence_digest: str,
    ) -> str:
        payload = f"{protocol_version}:{mission_id}:{target_sha}:{outcome_type.value}:{primary_actor.value}:{evidence_digest}"
        return "settlement:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @classmethod
    def adjudicate(
        cls,
        request: RewardRequest,
        manager: AirspaceManager,
        *,
        actor: str = "SAGE_REWARD_ADJUDICATOR",
    ) -> RewardDecision:
        """Independently adjudicate a verified evidence packet against SAGE-RP-1.0."""
        pkt = request.evidence_packet

        # 1. Verification boundary check
        if pkt.verification_status != "VERIFIED":
            raise ValueError(
                f"Reward adjudication rejected: evidence verification status is '{pkt.verification_status}', required 'VERIFIED'."
            )
        if not pkt.reward_requested:
            raise ValueError("Reward adjudication rejected: reward_requested is False.")

        # 2. Derive deterministic settlement ID
        evidence_digest = pkt.integrity_digest
        settlement_id = cls.calculate_settlement_id(
            protocol_version=request.protocol_version,
            mission_id=pkt.mission_id,
            target_sha=pkt.target_sha,
            outcome_type=pkt.outcome_type,
            primary_actor=pkt.primary_actor,
            evidence_digest=evidence_digest,
        )

        # 3. Check Idempotency against historical events
        existing = cls._find_existing_settlement(manager, settlement_id)
        if existing is not None:
            return existing

        # 4. Calculate outcome point pool
        base_pts = BASE_POINTS[pkt.outcome_type]
        multiplier = (request.difficulty + request.verification_quality + request.impact + request.reuse) / 4.0
        outcome_pool = max(1, round(base_pts * multiplier))

        # 5. Evaluate contribution ledger vs outcome pool (Conservation Principle)
        attributed_points: Dict[str, int] = {}
        if pkt.contributions:
            total_weight = sum(c.share_weight for c in pkt.contributions)
            if total_weight > 0:
                raw_allocations = {
                    c.actor_nameplate or c.actor.value: int(round(outcome_pool * (c.share_weight / total_weight)))
                    for c in pkt.contributions
                }
                # Conservation check and remainder adjustment
                sum_alloc = sum(raw_allocations.values())
                remainder = outcome_pool - sum_alloc
                if raw_allocations:
                    first_key = list(raw_allocations.keys())[0]
                    raw_allocations[first_key] += remainder
                attributed_points = raw_allocations
                attribution_status = "VERIFIED_ATTRIBUTION"
            else:
                attributed_points = {pkt.primary_actor_nameplate or pkt.primary_actor.value: outcome_pool}
                attribution_status = "ATTRIBUTION_INDETERMINATE"
        else:
            attributed_points = {pkt.primary_actor_nameplate or pkt.primary_actor.value: outcome_pool}
            attribution_status = "ATTRIBUTION_INDETERMINATE"

        conservation_passed = sum(attributed_points.values()) == outcome_pool
        if not conservation_passed:
            raise ValueError(f"CONSERVATION_VIOLATION: Attributed points sum {sum(attributed_points.values())} != outcome pool {outcome_pool}")

        # 6. Reconstruct pre-settlement state for primary actor
        current_state = manager.reconstruct_airspace_state()
        xp_before = current_state.game_progression.get_total_xp_for_station(pkt.primary_actor)

        # 7. Persist verified point awards (exact allocated points per participant with multiplier 1.0)
        points_ref = f"{settlement_id}:{pkt.mission_id}"
        for nameplate_str, pts in attributed_points.items():
            station_enum = resolve_station_id(nameplate_str)
            PointsXPEconomy.award_verified_event(
                manager=manager,
                actor=actor,
                event_id=f"evt-{settlement_id}-{nameplate_str}",
                station_id=station_enum,
                event_type=pkt.outcome_type,
                verified_event_ref=f"{points_ref}:{nameplate_str}",
                evidence_refs=pkt.evidence_refs,
                reason=f"Adjudicated reward under {request.protocol_version} for mission {pkt.mission_id}",
                category=XPCategory.MISSION_XP,
                base_points=pts,  # Pass exact allocated share
                difficulty=1,     # Multiplier dimensions set to 1 so VerifiedPointAward.points == pts exactly
                verification_quality=1,
                impact=1,
                reuse=1,
            )

        # 8. Boss outcome recording & Cadence-correct Badge Semantics
        badge_awards: List[str] = []
        if pkt.outcome_type in (PointEventType.BOSS_KILL, PointEventType.BOSS_CAPTURE):
            boss_class = pkt.boss_class or BossClass.BIG
            is_kill = pkt.outcome_type == PointEventType.BOSS_KILL
            is_capture = pkt.outcome_type == PointEventType.BOSS_CAPTURE

            # Record outcome in ledger first
            boss_outcome = BossOutcome(
                event_id=f"boss-{settlement_id}",
                station_id=pkt.primary_actor,
                boss_class=boss_class,
                verified_event_ref=f"boss-ref-{settlement_id}",
                evidence_refs=pkt.evidence_refs,
                kill=is_kill,
                capture=is_capture,
            )
            BossProgressionAuthority.record_verified_outcome(
                manager,
                actor=actor,
                outcome=boss_outcome,
                reason=f"Verified Boss Outcome for mission {pkt.mission_id}",
            )

            # Check cadence threshold using canonical BossProgressionAuthority
            progression = BossProgressionAuthority.project_station(manager, pkt.primary_actor)
            cadence_required = BOSS_BADGE_CADENCE[boss_class]
            count = (progression.big_kills + progression.big_captures) if boss_class == BossClass.BIG else (progression.major_kills + progression.major_captures)
            if count > 0 and (count % cadence_required) == 0:
                badge_awards.append(f"BOSS_{boss_class.value}_BADGE")

        # 9. Reconstruct post-settlement state
        post_state = manager.reconstruct_airspace_state()
        xp_after = post_state.game_progression.get_total_xp_for_station(pkt.primary_actor)
        xp_minted = max(0, xp_after - xp_before)
        station_obj = post_state.stations.get(pkt.primary_actor)
        rank = f"CQL-{station_obj.current_cql}" if station_obj else "OPERATIONAL"

        # Promotion eligibility: Do NOT hardcode True. Query qualification registry or set False
        promotion_eligibility = False
        if station_obj:
            current_cql = station_obj.current_cql
            if current_cql < 7 and post_state.qualification_registry:
                # Promotion requires explicit qualification advancement gate
                promotion_eligibility = False

        # Record settlement event into AirspaceManager event log
        manager.record_event(
            event_type="REWARD_SETTLED",
            actor=actor,
            payload={
                "protocol_version": request.protocol_version,
                "settlement_id": settlement_id,
                "mission_id": pkt.mission_id,
                "primary_actor": pkt.primary_actor.value,
                "outcome_type": pkt.outcome_type.value,
                "base_points": base_pts,
                "multiplier": multiplier,
                "outcome_point_pool": outcome_pool,
                "attributed_points": attributed_points,
                "attribution_status": attribution_status,
                "xp_before": xp_before,
                "xp_minted": xp_minted,
                "xp_after": xp_after,
                "badge_awards": badge_awards,
                "rank": rank,
                "promotion_eligibility": promotion_eligibility,
                "conservation_check_passed": conservation_passed,
                "idempotency_check_passed": True,
                "evidence_digest": evidence_digest,
            },
            evidence_refs=list(pkt.evidence_refs),
        )

        receipt_text = cls.format_reward_receipt(
            mission_id=pkt.mission_id,
            outcome_type=pkt.outcome_type.value,
            protocol_version=request.protocol_version,
            verified_points=outcome_pool,
            xp_minted=xp_minted,
            badge=" | ".join(badge_awards) if badge_awards else "NONE",
            rank=rank,
            settlement_id=settlement_id,
        )

        return RewardDecision(
            protocol_version=request.protocol_version,
            settlement_id=settlement_id,
            mission_id=pkt.mission_id,
            primary_actor=pkt.primary_actor,
            outcome_type=pkt.outcome_type,
            base_points=base_pts,
            multiplier=multiplier,
            outcome_point_pool=outcome_pool,
            attributed_points=attributed_points,
            attribution_status=attribution_status,
            xp_before=xp_before,
            xp_minted=xp_minted,
            xp_after=xp_after,
            badge_awards=tuple(badge_awards),
            rank=rank,
            promotion_eligibility=promotion_eligibility,
            conservation_check_passed=conservation_passed,
            idempotency_check_passed=True,
            evidence_digest=evidence_digest,
            receipt_header_text=receipt_text,
        )

    @classmethod
    def build_sagi_learning_signal(cls, decision: RewardDecision) -> Dict[str, Any]:
        """Transform a RewardDecision into a structured learning signal for SAGI Brain."""
        signal_payload = f"sagi-learning:{decision.settlement_id}:{decision.mission_id}:{decision.outcome_point_pool}"
        learning_signal_id = "sagi-sig:" + hashlib.sha256(signal_payload.encode()).hexdigest()
        return {
            "learning_signal_id": learning_signal_id,
            "settlement_id": decision.settlement_id,
            "mission_id": decision.mission_id,
            "outcome_type": decision.outcome_type.value,
            "outcome_point_pool": decision.outcome_point_pool,
            "attribution_status": decision.attribution_status,
            "xp_minted": decision.xp_minted,
            "conservation_verified": decision.conservation_check_passed,
            "metacognitive_feedback": {
                "performance_tier": "ELITE" if decision.outcome_point_pool >= 100 else "STANDARD",
                "attribution_quality": decision.attribution_status,
                "multi_agent_collaboration": len(decision.attributed_points) > 1,
            },
        }

    @classmethod
    def _find_existing_settlement(
        cls, manager: AirspaceManager, settlement_id: str
    ) -> Optional[RewardDecision]:
        for raw in manager._load_raw_events():
            if raw.get("event_type") != "REWARD_SETTLED":
                continue
            p = raw.get("payload", {})
            if p.get("settlement_id") == settlement_id:
                return RewardDecision(
                    protocol_version=str(p.get("protocol_version", SCORING_PROTOCOL_VERSION)),
                    settlement_id=str(p["settlement_id"]),
                    mission_id=str(p.get("mission_id", "")),
                    primary_actor=resolve_station_id(p.get("primary_actor", "MISSION_CONTROL")),
                    outcome_type=PointEventType(str(p.get("outcome_type", "REPAIR"))),
                    base_points=int(p.get("base_points", 0)),
                    multiplier=float(p.get("multiplier", 1.0)),
                    outcome_point_pool=int(p.get("outcome_point_pool", 0)),
                    attributed_points=dict(p.get("attributed_points", {})),
                    attribution_status=str(p.get("attribution_status", "ATTRIBUTION_INDETERMINATE")),
                    xp_before=int(p.get("xp_before", 0)),
                    xp_minted=0,  # Replay yields 0 newly minted XP
                    xp_after=int(p.get("xp_after", 0)),
                    badge_awards=tuple(p.get("badge_awards", [])),
                    rank=str(p.get("rank", "RECRUIT")),
                    promotion_eligibility=bool(p.get("promotion_eligibility", False)),
                    conservation_check_passed=bool(p.get("conservation_check_passed", True)),
                    idempotency_check_passed=True,
                    evidence_digest=str(p.get("evidence_digest", "")),
                    receipt_header_text=cls.format_reward_receipt(
                        mission_id=str(p.get("mission_id", "")),
                        outcome_type=str(p.get("outcome_type", "")),
                        protocol_version=str(p.get("protocol_version", SCORING_PROTOCOL_VERSION)),
                        verified_points=int(p.get("outcome_point_pool", 0)),
                        xp_minted=0,
                        badge=" | ".join(p.get("badge_awards", [])) if p.get("badge_awards") else "NONE",
                        rank=str(p.get("rank", "RECRUIT")),
                        settlement_id=str(p["settlement_id"]),
                    ),
                )
        return None

    @staticmethod
    def format_reward_receipt(
        *,
        mission_id: str,
        outcome_type: str,
        protocol_version: str,
        verified_points: int,
        xp_minted: int,
        badge: str,
        rank: str,
        settlement_id: str,
    ) -> str:
        lines = [
            "╔════════════════════════════════════╗",
            "║ SAGE REWARD RECEIPT                ║",
            "╠════════════════════════════════════╣",
            f"║ Mission: {mission_id:<26} ║",
            f"║ Outcome: {outcome_type:<26} ║",
            f"║ Protocol: {protocol_version:<25} ║",
            "║                                    ║",
            f"║ Verified Points: {verified_points:<17} ║",
            f"║ XP Minted: {xp_minted:<23} ║",
            f"║ Badge: {badge:<27} ║",
            f"║ Rank: {rank:<28} ║",
            "║                                    ║",
            "║ Evidence: VERIFIED                 ║",
            f"║ Settlement: {settlement_id[:22]:<22} ║",
            "╚════════════════════════════════════╝",
        ]
        return "\n".join(lines)
