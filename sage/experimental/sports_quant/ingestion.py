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
    market_type: str = ""
    line_value: float | None = None

    def __post_init__(self) -> None:
        if not self.event_id or not self.event_start_utc or not self.observed_at_utc:
            raise ValueError("MARKET_SNAPSHOT_INVALID: event identity and timestamps are required")
        if not self.market:
            raise ValueError("MARKET_SNAPSHOT_INVALID: market is required")
        if not self.prices:
            raise ValueError("MARKET_SNAPSHOT_INVALID: at least one market price is required")
        if any(price <= 0 for price in self.prices.values()):
            raise ValueError("MARKET_SNAPSHOT_INVALID: prices must be positive")

    @property
    def canonical_market_type(self) -> str:
        return (self.market_type or self.market).strip().lower()

    @property
    def canonical_line_value(self) -> str:
        return "" if self.line_value is None else format(self.line_value, ".12g")

    @property
    def market_identity(self) -> tuple[str, str, str, str]:
        return (self.event_id, self.canonical_market_type, self.canonical_line_value, self.observed_at_utc)


@dataclass(frozen=True)
class PlayerPropSnapshot:
    event_id: str
    sport: str
    league: str
    event_start_utc: str
    observed_at_utc: str
    player_name: str
    prop_category: str
    threshold: float | None
    prices: Mapping[str, float]
    source: str = "FanDuel market reference"
    source_url: str = ""
    sharp_reference_price: float | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.event_id or not self.event_start_utc or not self.observed_at_utc:
            raise ValueError("PLAYER_PROP_SNAPSHOT_INVALID: event identity and timestamps are required")
        if not self.player_name or not self.prop_category:
            raise ValueError("PLAYER_PROP_SNAPSHOT_INVALID: player_name and prop_category are required")
        if not self.prices:
            raise ValueError("PLAYER_PROP_SNAPSHOT_INVALID: at least one market price is required")
        if any(price <= 0 for price in self.prices.values()):
            raise ValueError("PLAYER_PROP_SNAPSHOT_INVALID: prices must be positive")

    @property
    def canonical_market_type(self) -> str:
        return "player_prop"

    @property
    def canonical_line_value(self) -> str:
        return "" if self.threshold is None else format(self.threshold, ".12g")

    @property
    def market_identity(self) -> tuple[str, str, str, str, str]:
        return (self.event_id, self.canonical_market_type, self.prop_category.strip().lower(), self.canonical_line_value, self.observed_at_utc)


class FanDuelSnapshotAdapter:
    """Parse a FanDuel-shaped read-only snapshot; never places or authenticates wagers."""

    SOURCE_NAME = "FanDuel market reference"

    @staticmethod
    def american_to_decimal(american_odds: int | float) -> float:
        if american_odds == 0:
            raise ValueError("INVALID_AMERICAN_ODDS: odds cannot be zero")
        if american_odds > 0:
            return round(1.0 + (american_odds / 100.0), 4)
        return round(1.0 + (100.0 / abs(american_odds)), 4)

    @classmethod
    def parse_player_prop(cls, payload: Mapping[str, Any]) -> PlayerPropSnapshot:
        event = payload.get("event") or {}
        prop = payload.get("prop") or payload
        market = payload.get("market") or {}
        raw_prices = prop.get("prices") or market.get("prices") or payload.get("prices") or {}
        american_prices = prop.get("american_prices") or payload.get("american_prices")
        if american_prices and not raw_prices:
            prices = {str(k): cls.american_to_decimal(v) for k, v in american_prices.items()}
        else:
            prices = {str(k): float(v) for k, v in raw_prices.items()}
        raw_thresh = prop.get("threshold") if "threshold" in prop else payload.get("threshold")
        threshold = float(raw_thresh) if raw_thresh is not None else None
        sharp_ref = prop.get("sharp_reference_price") if "sharp_reference_price" in prop else payload.get("sharp_reference_price")
        sharp_price = float(sharp_ref) if sharp_ref is not None else None
        return PlayerPropSnapshot(
            event_id=str(event.get("id") or payload.get("event_id") or ""),
            sport=str(event.get("sport") or payload.get("sport") or ""),
            league=str(event.get("league") or payload.get("league") or ""),
            event_start_utc=str(event.get("start_utc") or payload.get("event_start_utc") or ""),
            observed_at_utc=str(payload.get("observed_at_utc") or ""),
            player_name=str(prop.get("player_name") or payload.get("player_name") or ""),
            prop_category=str(prop.get("category") or payload.get("prop_category") or market.get("name") or ""),
            threshold=threshold,
            prices=prices,
            source=str(payload.get("source") or cls.SOURCE_NAME),
            source_url=str(payload.get("source_url") or ""),
            sharp_reference_price=sharp_price,
            metadata=dict(payload.get("metadata") or prop.get("metadata") or {}),
        )

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> MarketSnapshot:
        event = payload.get("event") or {}
        market = payload.get("market") or {}
        prices = market.get("prices") or payload.get("prices") or {}
        raw_line = market.get("line_value") if market.get("line_value") is not None else payload.get("line_value")
        line_value = float(raw_line) if raw_line is not None else None
        market_name = str(market.get("name") or payload.get("market_name") or "")
        market_type = str(market.get("type") or payload.get("market_type") or "")
        return MarketSnapshot(
            event_id=str(event.get("id") or payload.get("event_id") or ""),
            sport=str(event.get("sport") or payload.get("sport") or ""),
            league=str(event.get("league") or payload.get("league") or ""),
            event_start_utc=str(event.get("start_utc") or payload.get("event_start_utc") or ""),
            observed_at_utc=str(payload.get("observed_at_utc") or ""),
            market=market_name,
            prices={str(k): float(v) for k, v in prices.items()},
            source=str(payload.get("source") or cls.SOURCE_NAME),
            source_url=str(payload.get("source_url") or ""),
            metadata=dict(payload.get("metadata") or {}),
            market_type=market_type,
            line_value=line_value,
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
