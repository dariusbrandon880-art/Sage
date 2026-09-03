"""SAGE Reward & Evidence Protocol v1 (SAGE-RP-1.0).

Canonical reward settlement boundary. The adjudicator computes one outcome pool,
attributes that pool without re-multiplication, and delegates progression/boss
state to the existing canonical authorities.
"""
from __future__ import annotations

import hashlib
import math
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from sage.experimental.airspace.boss_progression import (
    BossClass,
    BossOutcome,
    BossProgressionAuthority,
)
from sage.experimental.airspace.manager import AirspaceManager
from sage.experimental.airspace.models import StationID, XPCategory
from sage.experimental.airspace.points_xp_economy import BASE_POINTS, PointEventType, PointsXPEconomy

SCORING_PROTOCOL_VERSION = "SAGE-RP-1.0"
SAGE_SEP_VERSION = "SAGE-SEP/1"
POINTS_PER_XP = 10
HEX_SHA40 = re.compile(r"^[0-9a-fA-F]{40}$")
HEX_SHA64 = re.compile(r"^[0-9a-fA-F]{64}$")

_ALIAS_MAP = {
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


def resolve_station_id(val: Any) -> StationID:
    if isinstance(val, StationID):
        return val
    s = str(val).upper().strip()
    if s in _ALIAS_MAP:
        return _ALIAS_MAP[s]
    try:
        return StationID(s)
    except ValueError as exc:
        raise ValueError(f"Unknown station/nameplate: {val!r}") from exc


@dataclass(frozen=True)
class ContributionUnit:
    actor: StationID
    role: str
    contribution_type: str
    share_weight: float
    claim_ref: str
    actor_nameplate: str = ""

    def __post_init__(self) -> None:
        resolved = resolve_station_id(self.actor)
        object.__setattr__(self, "actor", resolved)
        if not self.actor_nameplate:
            object.__setattr__(self, "actor_nameplate", resolved.value)
        nameplate_station = resolve_station_id(self.actor_nameplate)
        if nameplate_station != resolved:
            raise ValueError(
                f"Contribution actor/nameplate mismatch: {resolved.value} != {self.actor_nameplate}"
            )
        if not self.role.strip():
            raise ValueError("ContributionUnit requires a non-empty role.")
        if not self.contribution_type.strip():
            raise ValueError("ContributionUnit requires a non-empty contribution_type.")
        if not math.isfinite(self.share_weight) or self.share_weight <= 0.0:
            raise ValueError("ContributionUnit share_weight must be finite and positive.")
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
    verification_status: str
    outcome_type: PointEventType
    boss_class: Optional[BossClass] = None
    integrity_digest: str = ""
    reward_requested: bool = True
    protocol_version: str = "1.0"
    primary_actor_nameplate: str = ""

    def __post_init__(self) -> None:
        if self.protocol not in (SAGE_SEP_VERSION, "SEP/1", "SAGE-SEP/1"):
            raise ValueError(f"Invalid evidence protocol: {self.protocol}")
        if not self.mission_id.strip() or not self.subject_repo.strip():
            raise ValueError("Evidence mission_id and subject_repo are required.")
        if not HEX_SHA40.fullmatch(self.target_sha) or not HEX_SHA40.fullmatch(self.observed_sha):
            raise ValueError("Evidence target_sha and observed_sha must be 40-character commit SHAs.")
        if self.target_sha != self.observed_sha:
            raise ValueError("SHA mismatch: target_sha != observed_sha")
        primary = resolve_station_id(self.primary_actor)
        object.__setattr__(self, "primary_actor", primary)
        if not self.primary_actor_nameplate:
            object.__setattr__(self, "primary_actor_nameplate", primary.value)
        if resolve_station_id(self.primary_actor_nameplate) != primary:
            raise ValueError("Primary actor/nameplate mapping is inconsistent.")
        object.__setattr__(self, "supporting_agents", tuple(resolve_station_id(a) for a in self.supporting_agents))
        if not self.evidence_refs:
            raise ValueError("SAGEEvidencePacket evidence_refs must not be empty.")
        if self.integrity_digest:
            if not HEX_SHA64.fullmatch(self.integrity_digest):
                raise ValueError("integrity_digest must be a 64-character SHA-256 hex digest.")
        else:
            digest = hashlib.sha256(
                f"{self.protocol}:{self.subject_repo}:{self.mission_id}:{self.target_sha}:{self.claim_statement}".encode()
            ).hexdigest()
            object.__setattr__(self, "integrity_digest", digest)

    @classmethod
    def parse_report_payload(cls, raw: Dict[str, Any]) -> "SAGEEvidencePacket":
        subject = raw.get("subject", {})
        claim = raw.get("claim", {})
        execution = raw.get("execution", {})
        verification = raw.get("verification", {})
        outcome = raw.get("outcome", {})
        integrity = raw.get("integrity", {})
        reward = raw.get("reward", {})
        mission_id = raw.get("mission_id", "UNKNOWN_MISSION")
        primary_nameplate = str(execution.get("actor", raw.get("primary_actor", "CHATGPT_C2")))
        contributions = tuple(
            ContributionUnit(
                actor=resolve_station_id(c["actor"]),
                actor_nameplate=str(c["actor"]),
                role=str(c["role"]),
                contribution_type=str(c["contribution_type"]),
                share_weight=float(c.get("share_weight", 1.0)),
                claim_ref=str(c.get("claim_ref", mission_id)),
            )
            for c in raw.get("contributions", [])
        )
        return cls(
            protocol=raw.get("protocol", SAGE_SEP_VERSION),
            mission_id=mission_id,
            subject_repo=subject.get("repository", raw.get("subject_repo", "dariusbrandon880-art/Sage")),
            target_sha=subject.get("commit", raw.get("target_sha", "")),
            observed_sha=raw.get("observed_sha", subject.get("commit", raw.get("target_sha", ""))),
            claim_type=claim.get("type", raw.get("claim_type", "verified_repair")),
            claim_statement=claim.get("statement", raw.get("claim_statement", "Verified mission execution")),
            primary_actor=resolve_station_id(primary_nameplate),
            primary_actor_nameplate=primary_nameplate,
            supporting_agents=tuple(resolve_station_id(a) for a in execution.get("supporting_agents", raw.get("supporting_agents", []))),
            contributions=contributions,
            evidence_refs=tuple(str(e) for e in raw.get("evidence", raw.get("evidence_refs", ["exact_head_ci"]))),
            verification_status=verification.get("status", raw.get("verification_status", "HOLD")),
            outcome_type=PointEventType(outcome.get("type", raw.get("outcome_type", "REPAIR"))),
            boss_class=BossClass(outcome["boss_class"]) if outcome.get("boss_class", raw.get("boss_class")) else None,
            integrity_digest=integrity.get("digest", raw.get("integrity_digest", "")),
            reward_requested=reward.get("requested", raw.get("reward_requested", True)),
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
    evidence_packet: SAGEEvidencePacket
    protocol_version: str = SCORING_PROTOCOL_VERSION
    difficulty: int = 1
    verification_quality: int = 1
    impact: int = 1
    reuse: int = 1
    causal_parent_refs: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.protocol_version != SCORING_PROTOCOL_VERSION:
            raise ValueError("Unsupported reward protocol version.")
        for name, value in (("difficulty", self.difficulty), ("verification_quality", self.verification_quality), ("impact", self.impact), ("reuse", self.reuse)):
            if not isinstance(value, int) or value < 1 or value > 5:
                raise ValueError(f"{name} must be between 1 and 5")


@dataclass(frozen=True)
class RewardDecision:
    protocol_version: str
    settlement_id: str
    mission_id: str
    primary_actor: StationID
    outcome_type: PointEventType
    base_points: int
    multiplier: float
    outcome_point_pool: int
    attributed_points: Dict[str, int]
    attribution_status: str
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
        return {"protocol_version": self.protocol_version, "settlement_id": self.settlement_id, "mission_id": self.mission_id, "primary_actor": self.primary_actor.value, "outcome_type": self.outcome_type.value, "base_points": self.base_points, "multiplier": self.multiplier, "outcome_point_pool": self.outcome_point_pool, "attributed_points": self.attributed_points, "attribution_status": self.attribution_status, "xp_before": self.xp_before, "xp_minted": self.xp_minted, "xp_after": self.xp_after, "badge_awards": list(self.badge_awards), "rank": self.rank, "promotion_eligibility": self.promotion_eligibility, "conservation_check_passed": self.conservation_check_passed, "idempotency_check_passed": self.idempotency_check_passed, "evidence_digest": self.evidence_digest, "timestamp": self.timestamp}


class RewardAdjudicator:
    @classmethod
    def calculate_settlement_id(cls, protocol_version: str, mission_id: str, target_sha: str, outcome_type: PointEventType, primary_actor: StationID, evidence_digest: str) -> str:
        payload = f"{protocol_version}:{mission_id}:{target_sha}:{outcome_type.value}:{primary_actor.value}:{evidence_digest}"
        return "settlement:" + hashlib.sha256(payload.encode()).hexdigest()

    @classmethod
    def adjudicate(cls, request: RewardRequest, manager: AirspaceManager, *, actor: str = "SAGE_REWARD_ADJUDICATOR") -> RewardDecision:
        pkt = request.evidence_packet
        if pkt.verification_status != "VERIFIED":
            raise ValueError(f"Reward adjudication rejected: evidence verification status is '{pkt.verification_status}', required 'VERIFIED'.")
        if not pkt.reward_requested:
            raise ValueError("Reward adjudication rejected: reward_requested is False.")
        settlement_id = cls.calculate_settlement_id(request.protocol_version, pkt.mission_id, pkt.target_sha, pkt.outcome_type, pkt.primary_actor, pkt.integrity_digest)
        existing = cls._find_existing_settlement(manager, settlement_id)
        if existing is not None:
            return existing

        # The repository-bound evidence packet must carry a real digest, and the
        # target/observed commit identifiers must be syntactically valid and equal.
        if not HEX_SHA40.fullmatch(pkt.target_sha) or pkt.target_sha != pkt.observed_sha:
            raise ValueError("Evidence commit binding failed closed.")
        if not HEX_SHA64.fullmatch(pkt.integrity_digest):
            raise ValueError("Evidence integrity digest failed closed.")

        seen_nameplates = set()
        for contribution in pkt.contributions:
            key = contribution.actor_nameplate.upper().strip()
            if key in seen_nameplates:
                raise ValueError(f"Duplicate contribution actor/nameplate: {contribution.actor_nameplate}")
            seen_nameplates.add(key)
            if resolve_station_id(key) != contribution.actor:
                raise ValueError("Contribution actor/nameplate mapping is inconsistent.")
            if not math.isfinite(contribution.share_weight) or contribution.share_weight <= 0:
                raise ValueError("Contribution share_weight must be finite and positive.")

        base_pts = BASE_POINTS[pkt.outcome_type]
        multiplier = (request.difficulty + request.verification_quality + request.impact + request.reuse) / 4.0
        outcome_pool = max(1, round(base_pts * multiplier))

        if pkt.contributions:
            total_weight = sum(c.share_weight for c in pkt.contributions)
            raw = [round(outcome_pool * c.share_weight / total_weight) for c in pkt.contributions]
            remainder = outcome_pool - sum(raw)
            raw[0] += remainder
            attributed_points = {c.actor_nameplate: pts for c, pts in zip(pkt.contributions, raw)}
            attribution_status = "VERIFIED_ATTRIBUTION"
        else:
            attributed_points = {pkt.primary_actor_nameplate: outcome_pool}
            attribution_status = "ATTRIBUTION_INDETERMINATE"
        if sum(attributed_points.values()) != outcome_pool:
            raise ValueError("Reward conservation invariant violated before settlement.")

        current_state = manager.reconstruct_airspace_state()
        xp_before = current_state.game_progression.get_total_xp_for_station(pkt.primary_actor)
        points_ref = f"{settlement_id}:{pkt.mission_id}"
        for nameplate, points in attributed_points.items():
            station = resolve_station_id(nameplate)
            result = PointsXPEconomy.award_verified_event(
                manager=manager, actor=actor, event_id=f"evt-{settlement_id}-{nameplate}", station_id=station,
                event_type=pkt.outcome_type, verified_event_ref=f"{points_ref}:{nameplate}", evidence_refs=pkt.evidence_refs,
                reason=f"Adjudicated reward under {request.protocol_version} for mission {pkt.mission_id}", category=XPCategory.MISSION_XP,
                base_points=points, difficulty=1, verification_quality=1, impact=1, reuse=1,
            )
            if result.award.points != points:
                raise ValueError("PointsXPEconomy re-multiplied an attributed allocation; settlement aborted.")

        badge_awards: List[str] = []
        if pkt.outcome_type in (PointEventType.BOSS_KILL, PointEventType.BOSS_CAPTURE):
            before_boss = BossProgressionAuthority.project_station(manager, pkt.primary_actor)
            boss_class = pkt.boss_class or BossClass.BIG
            boss_outcome = BossOutcome(
                event_id=f"boss-{settlement_id}", station_id=pkt.primary_actor, boss_class=boss_class,
                verified_event_ref=f"boss-ref-{settlement_id}", evidence_refs=pkt.evidence_refs,
                kill=pkt.outcome_type == PointEventType.BOSS_KILL, capture=pkt.outcome_type == PointEventType.BOSS_CAPTURE,
            )
            BossProgressionAuthority.record_verified_outcome(manager, actor=actor, outcome=boss_outcome, reason=f"Verified Boss Outcome for mission {pkt.mission_id}")
            after_boss = BossProgressionAuthority.project_station(manager, pkt.primary_actor)
            if after_boss.big_badges > before_boss.big_badges:
                badge_awards.append("BIG_BADGE")
            if after_boss.major_badges > before_boss.major_badges:
                badge_awards.append("MAJOR_BADGE")

        post_state = manager.reconstruct_airspace_state()
        xp_after = post_state.game_progression.get_total_xp_for_station(pkt.primary_actor)
        xp_minted = max(0, xp_after - xp_before)
        station_obj = post_state.stations.get(pkt.primary_actor)
        rank = f"CQL-{station_obj.current_cql}" if station_obj else "OPERATIONAL"
        manager.record_event(
            event_type="REWARD_SETTLED", actor=actor,
            payload={"protocol_version": request.protocol_version, "settlement_id": settlement_id, "mission_id": pkt.mission_id,
                     "primary_actor": pkt.primary_actor.value, "outcome_type": pkt.outcome_type.value, "base_points": base_pts,
                     "multiplier": multiplier, "outcome_point_pool": outcome_pool, "attributed_points": attributed_points,
                     "attribution_status": attribution_status, "xp_before": xp_before, "xp_minted": xp_minted, "xp_after": xp_after,
                     "badge_awards": badge_awards, "rank": rank, "promotion_eligibility": False,
                     "conservation_check_passed": True, "idempotency_check_passed": True, "evidence_digest": pkt.integrity_digest},
            evidence_refs=list(pkt.evidence_refs),
        )
        receipt = cls.format_reward_receipt(mission_id=pkt.mission_id, outcome_type=pkt.outcome_type.value, protocol_version=request.protocol_version,
                                            verified_points=outcome_pool, xp_minted=xp_minted, badge=" | ".join(badge_awards) if badge_awards else "NONE",
                                            rank=rank, settlement_id=settlement_id)
        return RewardDecision(request.protocol_version, settlement_id, pkt.mission_id, pkt.primary_actor, pkt.outcome_type, base_pts, multiplier,
                              outcome_pool, attributed_points, attribution_status, xp_before, xp_minted, xp_after, tuple(badge_awards), rank,
                              False, True, True, pkt.integrity_digest, receipt_header_text=receipt)

    @classmethod
    def build_sagi_learning_signal(cls, decision: RewardDecision) -> Dict[str, Any]:
        signal = f"sagi-learning:{decision.settlement_id}:{decision.mission_id}:{decision.outcome_point_pool}"
        return {"learning_signal_id": "sagi-sig:" + hashlib.sha256(signal.encode()).hexdigest(), "settlement_id": decision.settlement_id,
                "mission_id": decision.mission_id, "outcome_type": decision.outcome_type.value, "outcome_point_pool": decision.outcome_point_pool,
                "attribution_status": decision.attribution_status, "xp_minted": decision.xp_minted, "conservation_verified": decision.conservation_check_passed,
                "metacognitive_feedback": {"performance_tier": "ELITE" if decision.outcome_point_pool >= 100 else "STANDARD",
                                           "attribution_quality": decision.attribution_status, "multi_agent_collaboration": len(decision.attributed_points) > 1}}

    @classmethod
    def _find_existing_settlement(cls, manager: AirspaceManager, settlement_id: str) -> Optional[RewardDecision]:
        for raw in manager._load_raw_events():
            if raw.get("event_type") != "REWARD_SETTLED":
                continue
            p = raw.get("payload", {})
            if p.get("settlement_id") != settlement_id:
                continue
            return RewardDecision(protocol_version=str(p.get("protocol_version", SCORING_PROTOCOL_VERSION)), settlement_id=str(p["settlement_id"]),
                                  mission_id=str(p.get("mission_id", "")), primary_actor=resolve_station_id(p.get("primary_actor", "MISSION_CONTROL")),
                                  outcome_type=PointEventType(str(p.get("outcome_type", "REPAIR"))), base_points=int(p.get("base_points", 0)),
                                  multiplier=float(p.get("multiplier", 1.0)), outcome_point_pool=int(p.get("outcome_point_pool", 0)),
                                  attributed_points=dict(p.get("attributed_points", {})), attribution_status=str(p.get("attribution_status", "ATTRIBUTION_INDETERMINATE")),
                                  xp_before=int(p.get("xp_before", 0)), xp_minted=0, xp_after=int(p.get("xp_after", 0)),
                                  badge_awards=tuple(p.get("badge_awards", [])), rank=str(p.get("rank", "RECRUIT")),
                                  promotion_eligibility=bool(p.get("promotion_eligibility", False)), idempotency_check_passed=True,
                                  conservation_check_passed=bool(p.get("conservation_check_passed", False)), evidence_digest=str(p.get("evidence_digest", "")))
        return None

    @staticmethod
    def format_reward_receipt(*, mission_id: str, outcome_type: str, protocol_version: str, verified_points: int, xp_minted: int, badge: str, rank: str, settlement_id: str) -> str:
        return "\n".join(["╔════════════════════════════════════╗", "║ SAGE REWARD RECEIPT                ║", "╠════════════════════════════════════╣",
                         f"║ Mission: {mission_id:<26} ║", f"║ Outcome: {outcome_type:<26} ║", f"║ Protocol: {protocol_version:<25} ║",
                         "║                                    ║", f"║ Verified Points: {verified_points:<17} ║", f"║ XP Minted: {xp_minted:<23} ║",
                         f"║ Badge: {badge:<27} ║", f"║ Rank: {rank:<28} ║", "║                                    ║", "║ Evidence: VERIFIED                 ║",
                         f"║ Settlement: {settlement_id[:22]:<22} ║", "╚════════════════════════════════════╝"])


__all__ = ["SCORING_PROTOCOL_VERSION", "SAGE_SEP_VERSION", "POINTS_PER_XP", "ContributionUnit", "SAGEEvidencePacket", "RewardRequest", "RewardDecision", "RewardAdjudicator", "resolve_station_id"]