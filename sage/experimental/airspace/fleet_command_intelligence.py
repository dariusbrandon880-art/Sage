"""Fleet Command Intelligence Layer — Persistent Fleet Progression & Tier System.

Tracks GPT (Mission Control) and Jules (Engineering Lead) qualification levels,
accumulated fleet XP, Big Strike milestones, and tier promotion receipts derived
strictly from evidence receipts.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
from typing import Optional


class FleetTier(str, Enum):
    """Fleet Capability Tiers."""
    CADET_FLEET = "CADET_FLEET"          # Level 1: Basic recon/build/verify
    OPERATIONAL_FLEET = "OPERATIONAL_FLEET"  # Level 2: 5-flight + routing
    FRONTIER_FLEET = "FRONTIER_FLEET"      # Level 3: Harder multi-domain
    STRATEGIC_FLEET = "STRATEGIC_FLEET"    # Level 4+: Large coordinated waves


TIER_XP_THRESHOLDS = {
    FleetTier.CADET_FLEET: 0,
    FleetTier.OPERATIONAL_FLEET: 100,
    FleetTier.FRONTIER_FLEET: 300,
    FleetTier.STRATEGIC_FLEET: 600,
}


@dataclass(frozen=True)
class FleetXPEvent:
    event_id: str
    station_id: str
    amount: int
    reason: str
    verified_event_ref: str
    timestamp_utc: str


@dataclass(frozen=True)
class FleetPromotionReceipt:
    receipt_id: str
    previous_tier: FleetTier
    new_tier: FleetTier
    total_xp: int
    verified_event_refs: tuple[str, ...]
    validator: str
    timestamp_utc: str
    receipt_digest: str


@dataclass(frozen=True)
class BigStrikeReceipt:
    strike_id: str
    strike_name: str
    wave_id: str
    contributing_flights_count: int
    unlocked_capability: str
    evidence_manifest_ref: str
    timestamp_utc: str
    strike_digest: str


class FleetCommandIntelligence:
    """Manages fleet state, XP accumulation, station ranks, and promotion receipts."""

    def __init__(
        self,
        initial_tier: FleetTier = FleetTier.CADET_FLEET,
        initial_xp: int = 0,
    ) -> None:
        self._current_tier = initial_tier
        self._total_xp = max(0, initial_xp)
        self._xp_events: list[FleetXPEvent] = []
        self._promotion_history: list[FleetPromotionReceipt] = []
        self._big_strike_history: list[BigStrikeReceipt] = []

    @property
    def current_tier(self) -> FleetTier:
        return self._current_tier

    @property
    def total_xp(self) -> int:
        return self._total_xp

    @property
    def xp_events(self) -> tuple[FleetXPEvent, ...]:
        return tuple(self._xp_events)

    @property
    def promotion_history(self) -> tuple[FleetPromotionReceipt, ...]:
        return tuple(self._promotion_history)

    @property
    def big_strike_history(self) -> tuple[BigStrikeReceipt, ...]:
        return tuple(self._big_strike_history)

    def award_xp(
        self,
        station_id: str,
        amount: int,
        reason: str,
        verified_event_ref: str,
        timestamp_utc: str,
    ) -> FleetXPEvent:
        """Award XP backed strictly by a non-empty verified event reference."""
        if amount <= 0:
            raise ValueError("XP amount must be positive.")
        if not verified_event_ref or not verified_event_ref.strip():
            raise ValueError("XP Award Rejected: verified_event_ref cannot be empty.")

        event_id = f"fxp_{hashlib.sha256(f'{station_id}:{verified_event_ref}:{amount}'.encode()).hexdigest()[:10]}"
        event = FleetXPEvent(
            event_id=event_id,
            station_id=station_id,
            amount=amount,
            reason=reason,
            verified_event_ref=verified_event_ref,
            timestamp_utc=timestamp_utc,
        )
        self._xp_events.append(event)
        self._total_xp += amount
        return event

    def evaluate_promotion(
        self,
        target_tier: FleetTier,
        verified_event_refs: tuple[str, ...],
        validator: str,
        timestamp_utc: str,
    ) -> FleetPromotionReceipt:
        """Evaluate and promote fleet tier if XP threshold and evidence criteria are met."""
        if not verified_event_refs:
            raise ValueError("Promotion Rejected: verified_event_refs cannot be empty.")

        required_xp = TIER_XP_THRESHOLDS[target_tier]
        if self._total_xp < required_xp:
            raise ValueError(
                f"Promotion Rejected: Total XP {self._total_xp} is below required threshold {required_xp} for {target_tier.value}."
            )

        # Level skipping prevention
        tier_sequence = list(FleetTier)
        current_idx = tier_sequence.index(self._current_tier)
        target_idx = tier_sequence.index(target_tier)

        if target_idx <= current_idx:
            raise ValueError(f"Cannot promote to level {target_tier.value} from {self._current_tier.value}.")
        if target_idx > current_idx + 1:
            raise ValueError(
                f"Level Skipping Rejected: Cannot jump from {self._current_tier.value} directly to {target_tier.value}."
            )

        receipt_id = f"fpr_{hashlib.sha256(f'{self._current_tier.value}:{target_tier.value}:{self._total_xp}'.encode()).hexdigest()[:10]}"
        digest_raw = f"{receipt_id}|{self._current_tier.value}|{target_tier.value}|{self._total_xp}|{','.join(verified_event_refs)}"
        digest = hashlib.sha256(digest_raw.encode()).hexdigest()

        receipt = FleetPromotionReceipt(
            receipt_id=receipt_id,
            previous_tier=self._current_tier,
            new_tier=target_tier,
            total_xp=self._total_xp,
            verified_event_refs=verified_event_refs,
            validator=validator,
            timestamp_utc=timestamp_utc,
            receipt_digest=digest,
        )

        self._current_tier = target_tier
        self._promotion_history.append(receipt)
        return receipt

    def record_big_strike(
        self,
        strike_name: str,
        wave_id: str,
        contributing_flights_count: int,
        unlocked_capability: str,
        evidence_manifest_ref: str,
        timestamp_utc: str,
    ) -> BigStrikeReceipt:
        """Record a Big Strike campaign milestone backed by an evidence manifest."""
        if contributing_flights_count < 5:
            raise ValueError("Big Strike Rejected: Requires at least 5 contributing flights.")
        if not evidence_manifest_ref or not evidence_manifest_ref.strip():
            raise ValueError("Big Strike Rejected: evidence_manifest_ref is required.")

        strike_id = f"strike_{hashlib.sha256(f'{strike_name}:{wave_id}'.encode()).hexdigest()[:10]}"
        digest_raw = f"{strike_id}|{strike_name}|{wave_id}|{contributing_flights_count}|{evidence_manifest_ref}"
        digest = hashlib.sha256(digest_raw.encode()).hexdigest()

        receipt = BigStrikeReceipt(
            strike_id=strike_id,
            strike_name=strike_name,
            wave_id=wave_id,
            contributing_flights_count=contributing_flights_count,
            unlocked_capability=unlocked_capability,
            evidence_manifest_ref=evidence_manifest_ref,
            timestamp_utc=timestamp_utc,
            strike_digest=digest,
        )

        self._big_strike_history.append(receipt)
        return receipt
