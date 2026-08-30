"""Read-only market ingestion boundary for the sports quantitative lane."""

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class MarketSnapshot:
    event_id: str
    sport: str
    league: str
    event_start_utc: str
    observed_at_utc: str
    market: str
    prices: Mapping[str, float]
    source: str
    source_url: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.event_id or not self.event_start_utc or not self.observed_at_utc:
            raise ValueError("MARKET_SNAPSHOT_INVALID: event identity and timestamps are required")
        if not self.prices:
            raise ValueError("MARKET_SNAPSHOT_INVALID: at least one market price is required")
        if any(price <= 0 for price in self.prices.values()):
            raise ValueError("MARKET_SNAPSHOT_INVALID: prices must be positive")


class FanDuelSnapshotAdapter:
    """Parse a FanDuel-shaped read-only snapshot; never places or authenticates wagers."""

    SOURCE_NAME = "FanDuel market reference"

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> MarketSnapshot:
        event = payload.get("event") or {}
        market = payload.get("market") or {}
        prices = market.get("prices") or payload.get("prices") or {}
        return MarketSnapshot(
            event_id=str(event.get("id") or payload.get("event_id") or ""),
            sport=str(event.get("sport") or payload.get("sport") or ""),
            league=str(event.get("league") or payload.get("league") or ""),
            event_start_utc=str(event.get("start_utc") or payload.get("event_start_utc") or ""),
            observed_at_utc=str(payload.get("observed_at_utc") or ""),
            market=str(market.get("name") or payload.get("market_name") or ""),
            prices={str(k): float(v) for k, v in prices.items()},
            source=str(payload.get("source") or cls.SOURCE_NAME),
            source_url=str(payload.get("source_url") or ""),
            metadata=dict(payload.get("metadata") or {}),
        )

    @staticmethod
    def implied_probability(decimal_price: float) -> float:
        if decimal_price <= 0:
            raise ValueError("INVALID_PRICE: decimal price must be positive")
        return 1.0 / decimal_price

    @classmethod
    def normalized_probabilities(cls, snapshot: MarketSnapshot) -> dict[str, float]:
        implied = {key: cls.implied_probability(value) for key, value in snapshot.prices.items()}
        total = sum(implied.values())
        if total <= 0:
            raise ValueError("MARKET_NORMALIZATION_FAILED")
        return {key: value / total for key, value in implied.items()}
