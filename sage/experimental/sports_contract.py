"""Sport-agnostic SAGE sports forecasting contract.

This module defines the shared boundary for real-world sports shadow forecasting.
Sport/league behavior belongs in bounded adapters; prediction, temporal locking,
provenance, outcome resolution, and evidence semantics remain canonical.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Mapping, Optional
import hashlib
import json


SPORT_LEAGUE_REGISTRY: Mapping[str, tuple[str, ...]] = {
    "baseball": ("MLB",),
    "basketball": ("NBA", "WNBA", "NCAAB"),
    "football": ("NFL", "NCAAF"),
    "hockey": ("NHL",),
    "soccer": (),
    "tennis": ("ATP", "WTA"),
}


def utc_datetime(value: str) -> datetime:
    """Parse an ISO timestamp and normalize it to UTC."""
    value = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def canonical_hash(payload: Mapping[str, Any]) -> str:
    """Return a deterministic SHA-256 digest for a JSON-compatible payload."""
    encoded = json.dumps(dict(payload), sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class SportsEventIdentity:
    event_id: str
    sport: str
    competition: str
    scheduled_start_utc: str
    home_competitor: str
    away_competitor: str

    def validate(self) -> None:
        if not self.event_id or not self.sport or not self.competition:
            raise ValueError("SPORT_EVENT_IDENTITY_INCOMPLETE")
        if self.competition not in SPORT_LEAGUE_REGISTRY.get(self.sport.lower(), ()) and self.competition != "":
            # Empty registry entries intentionally permit adapter-defined competitions.
            if self.sport.lower() != "soccer":
                raise ValueError(f"UNREGISTERED_SPORT_COMPETITION: {self.sport}/{self.competition}")
        utc_datetime(self.scheduled_start_utc)


@dataclass(frozen=True)
class FeatureProvenance:
    feature_name: str
    source_id: str
    source_hash: str
    available_at_utc: str
    observed_at_utc: Optional[str] = None

    def validate_point_in_time(self, cutoff_utc: str) -> None:
        cutoff = utc_datetime(cutoff_utc)
        available = utc_datetime(self.available_at_utc)
        if available > cutoff:
            raise ValueError(
                f"FEATURE_LEAKAGE: {self.feature_name} available at {self.available_at_utc} after cutoff {cutoff_utc}"
            )


@dataclass(frozen=True)
class CanonicalForecastContract:
    """Immutable point-in-time forecast envelope shared by every sport adapter."""

    event: SportsEventIdentity
    observation_cutoff_utc: str
    forecast_lock_utc: str
    selected_outcome: str
    predicted_probability: float
    feature_provenance: tuple[FeatureProvenance, ...] = field(default_factory=tuple)
    source_hashes: tuple[str, ...] = field(default_factory=tuple)
    model_version: str = ""
    rationale: str = ""

    def validate(self) -> None:
        self.event.validate()
        cutoff = utc_datetime(self.observation_cutoff_utc)
        lock = utc_datetime(self.forecast_lock_utc)
        start = utc_datetime(self.event.scheduled_start_utc)
        if cutoff > lock:
            raise ValueError("OBSERVATION_CUTOFF_AFTER_FORECAST_LOCK")
        if lock >= start:
            raise ValueError("TEMPORAL_LOCK_VIOLATION")
        if not 0.0 <= self.predicted_probability <= 1.0:
            raise ValueError("INVALID_FORECAST_PROBABILITY")
        for provenance in self.feature_provenance:
            provenance.validate_point_in_time(self.observation_cutoff_utc)
        if not self.source_hashes and not self.feature_provenance:
            raise ValueError("MISSING_SOURCE_PROVENANCE")

    def receipt_hash(self) -> str:
        self.validate()
        return canonical_hash(asdict(self))


@dataclass(frozen=True)
class OutcomeResolution:
    event_id: str
    resolved_at_utc: str
    outcome: str
    source_id: str
    source_hash: str
    final_home_score: Optional[int] = None
    final_away_score: Optional[int] = None

    def validate(self) -> None:
        utc_datetime(self.resolved_at_utc)
        if not self.event_id or not self.source_id or not self.source_hash:
            raise ValueError("OUTCOME_RESOLUTION_PROVENANCE_INCOMPLETE")


@dataclass(frozen=True)
class ForecastReceipt:
    forecast: CanonicalForecastContract
    receipt_hash: str

    @classmethod
    def seal(cls, forecast: CanonicalForecastContract) -> "ForecastReceipt":
        return cls(forecast=forecast, receipt_hash=forecast.receipt_hash())


def supported_competitions() -> Iterable[tuple[str, str]]:
    """Enumerate explicitly registered sport/competition pairs."""
    for sport, competitions in SPORT_LEAGUE_REGISTRY.items():
        if competitions:
            yield from ((sport, competition) for competition in competitions)


__all__ = [
    "SPORT_LEAGUE_REGISTRY",
    "SportsEventIdentity",
    "FeatureProvenance",
    "CanonicalForecastContract",
    "OutcomeResolution",
    "ForecastReceipt",
    "supported_competitions",
    "utc_datetime",
    "canonical_hash",
]
