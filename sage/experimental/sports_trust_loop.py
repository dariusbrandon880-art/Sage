"""Bounded longitudinal trust-loop contracts for the protected Sports/RCE lane.

This module adds validation and reporting around existing immutable prediction
and ledger primitives; it has no wagering, payment, scheduling, or authority role.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from hashlib import sha256
from math import log
from typing import Iterable, Mapping, Optional
import json

TERMINAL_NONSCORING = frozenset({"ABSTAIN", "DATA_UNAVAILABLE", "SOURCE_UNAVAILABLE", "VOID", "PUSH", "UNRESOLVED", "INVALID_POST_LOCK"})
SCORABLE = frozenset({"WIN", "LOSS"})


def _utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("TIMESTAMP_TIMEZONE_REQUIRED")
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True)
class EligibilityDecision:
    event_id: str
    decision: str
    eligibility_timestamp_utc: str
    market_close_timestamp_utc: str
    reason: str = ""

    def validate(self) -> None:
        if self.decision not in {"ELIGIBLE", "ABSTAIN", "DATA_UNAVAILABLE", "INVALID_POST_LOCK"}:
            raise ValueError("INVALID_ELIGIBILITY_DECISION")
        if _utc(self.eligibility_timestamp_utc) >= _utc(self.market_close_timestamp_utc) and self.decision == "ELIGIBLE":
            raise ValueError("ELIGIBILITY_AFTER_MARKET_CLOSE")


@dataclass(frozen=True)
class LockedInputProvenance:
    source_name: str
    source_timestamp_utc: str
    market_definition: str
    model_version: str
    input_fingerprint: str
    payload_fingerprint: str

    def fingerprint(self) -> str:
        return sha256(json.dumps(asdict(self), sort_keys=True).encode()).hexdigest()


def validate_locked_prediction(*, eligibility: EligibilityDecision, lock_timestamp_utc: str, provenance: LockedInputProvenance) -> str:
    eligibility.validate()
    if eligibility.decision != "ELIGIBLE":
        raise ValueError("PREDICTION_NOT_ELIGIBLE")
    if _utc(lock_timestamp_utc) >= _utc(eligibility.market_close_timestamp_utc):
        raise ValueError("LOCK_AT_OR_AFTER_MARKET_CLOSE")
    if not provenance.input_fingerprint or not provenance.payload_fingerprint:
        raise ValueError("MISSING_PRELOCK_PROVENANCE")
    _utc(provenance.source_timestamp_utc)
    return provenance.fingerprint()


def log_loss(probability: float, outcome: int) -> float:
    if not 0.0 < probability < 1.0 or outcome not in (0, 1):
        raise ValueError("INVALID_PROBABILITY_OR_OUTCOME")
    return -(outcome * log(probability) + (1 - outcome) * log(1 - probability))


def score_prediction(probability: float, status: str) -> Optional[dict[str, float]]:
    if status in TERMINAL_NONSCORING:
        return None
    if status not in SCORABLE:
        raise ValueError("UNKNOWN_OUTCOME_STATUS")
    outcome = 1 if status == "WIN" else 0
    return {"brier": (probability - outcome) ** 2, "log_loss": log_loss(probability, outcome)}


def summarize(records: Iterable[Mapping[str, object]]) -> dict[str, object]:
    rows = list(records)
    scored = [r for r in rows if r.get("outcome_status") in SCORABLE]
    abstentions = sum(1 for r in rows if r.get("outcome_status") == "ABSTAIN")
    unavailable = sum(1 for r in rows if r.get("outcome_status") in {"DATA_UNAVAILABLE", "SOURCE_UNAVAILABLE"})
    briers = [float(r["brier"]) for r in scored if r.get("brier") is not None]
    losses = [float(r["log_loss"]) for r in scored if r.get("log_loss") is not None]
    return {"sample_size": len(rows), "scored_count": len(scored), "coverage": len(scored) / len(rows) if rows else 0.0, "abstentions": abstentions, "unavailable": unavailable, "mean_brier": sum(briers) / len(briers) if briers else None, "mean_log_loss": sum(losses) / len(losses) if losses else None}
