"""Read-only market ingestion boundary for the sports quantitative lane."""

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence


class ProvenanceClass(str, Enum):
    SYNTHETIC = "synthetic"
    FIXTURE = "fixture"
    EXTERNAL_LIVE = "external_live"
    HISTORICAL_EXTERNAL = "historical_external"


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


@dataclass(frozen=True)
class MarketProvenance:
    provider: str
    endpoint: str
    retrieved_at_utc: str
    source_observed_at_utc: str
    event_ids: tuple[str, ...]
    snapshot_count: int
    raw_payload_hash: str
    normalized_payload_hash: str
    provenance_class: str
    adapter_version: str = "1.0.0"

    def __post_init__(self) -> None:
        if not self.provider:
            raise ValueError("MARKET_PROVENANCE_INVALID: provider is required")
        if self.snapshot_count < 0:
            raise ValueError("MARKET_PROVENANCE_INVALID: snapshot_count cannot be negative")

        prov_str = str(self.provenance_class).strip().lower()
        if prov_str == ProvenanceClass.EXTERNAL_LIVE.value or prov_str == "external_live":
            if not self.endpoint or self.endpoint.startswith("synthetic://"):
                raise ValueError("PROVENANCE_INTEGRITY_VIOLATION: external_live requires a valid external source_endpoint/url")
            if not self.raw_payload_hash:
                raise ValueError("PROVENANCE_INTEGRITY_VIOLATION: external_live requires non-empty raw_payload_hash")
            if not self.retrieved_at_utc or not self.source_observed_at_utc:
                raise ValueError("PROVENANCE_INTEGRITY_VIOLATION: external_live requires valid retrieval and observation timestamps")
            if self.provider.strip().lower() in ("synthetic", "synthetic_generator"):
                raise ValueError("PROVENANCE_INTEGRITY_VIOLATION: external_live cannot claim synthetic provider")

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_provider": self.provider,
            "source_endpoint": self.endpoint,
            "retrieved_at": self.retrieved_at_utc,
            "source_observed_at": self.source_observed_at_utc,
            "event_ids": list(self.event_ids),
            "snapshot_count": self.snapshot_count,
            "raw_payload_hash": self.raw_payload_hash,
            "normalized_payload_hash": self.normalized_payload_hash,
            "provenance_class": str(self.provenance_class),
            "adapter_version": self.adapter_version,
        }


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


class RealMarketFeedAdapter:
    """Read-only external market feed client and adapter.

    Normalizes multi-event odds API responses (Odds API / FanDuel feeds) into canonical
    MarketSnapshot instances and captures cryptographic raw-and-normalized payload provenance.
    Never authenticates or executes wagers (wagering_executed = False).
    """

    ADAPTER_VERSION = "1.0.0"

    @staticmethod
    def compute_raw_hash(raw_bytes_or_str: bytes | str) -> str:
        data = raw_bytes_or_str.encode("utf-8") if isinstance(raw_bytes_or_str, str) else raw_bytes_or_str
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def compute_normalized_hash(snapshots: Sequence[MarketSnapshot]) -> str:
        items = []
        for s in snapshots:
            items.append({
                "event_id": s.event_id,
                "sport": s.sport,
                "league": s.league,
                "event_start_utc": s.event_start_utc,
                "observed_at_utc": s.observed_at_utc,
                "market": s.market,
                "market_type": s.canonical_market_type,
                "line_value": s.canonical_line_value,
                "prices": {k: round(v, 6) for k, v in sorted(s.prices.items())},
            })
        sorted_repr = json.dumps(sorted(items, key=lambda x: (x["event_id"], x["market_type"], x["line_value"])), sort_keys=True)
        return hashlib.sha256(sorted_repr.encode("utf-8")).hexdigest()

    @classmethod
    def parse_raw_feed(
        cls,
        raw_payload: str | bytes | Mapping[str, Any] | Sequence[Any],
        provider: str = "The Odds API",
        endpoint: str = "https://api.the-odds-api.com/v4/sports/upcoming/odds",
        provenance_class: str = ProvenanceClass.FIXTURE.value,
        adapter_version: str = ADAPTER_VERSION,
        retrieved_at_utc: str | None = None,
    ) -> tuple[tuple[MarketSnapshot, ...], MarketProvenance]:
        """Parse raw external market payload into normalized snapshots and provenance capture."""
        now_utc = datetime.now(timezone.utc).isoformat()
        retrieved_at = retrieved_at_utc or now_utc

        if isinstance(raw_payload, (str, bytes)):
            raw_str = raw_payload.decode("utf-8") if isinstance(raw_payload, bytes) else raw_payload
            raw_hash = cls.compute_raw_hash(raw_str)
            try:
                parsed = json.loads(raw_str)
            except Exception as e:
                raise ValueError(f"RAW_FEED_PARSE_ERROR: invalid JSON payload: {e}")
        else:
            raw_str = json.dumps(raw_payload, sort_keys=True)
            raw_hash = cls.compute_raw_hash(raw_str)
            parsed = raw_payload

        snapshots: list[MarketSnapshot] = []
        observed_timestamps: list[str] = []

        # Handle top-level list of events (Odds API format) or wrapped object
        events_list = parsed if isinstance(parsed, list) else parsed.get("events") or parsed.get("data") or [parsed]

        for item in events_list:
            if not isinstance(item, dict):
                continue
            # Check if this is an Odds API style event object
            if "sport_key" in item or "bookmakers" in item:
                event_id = str(item.get("id") or item.get("event_id") or "")
                sport = str(item.get("sport_title") or item.get("sport_key") or "").upper()
                league = str(item.get("sport_key") or sport).upper()
                start_utc = str(item.get("commence_time") or item.get("start_utc") or now_utc)

                bookmakers = item.get("bookmakers") or []
                for bm in bookmakers:
                    bm_name = str(bm.get("title") or bm.get("key") or provider)
                    bm_observed = str(bm.get("last_update") or retrieved_at)
                    observed_timestamps.append(bm_observed)

                    for market in bm.get("markets") or []:
                        m_type = str(market.get("key") or market.get("name") or "h2h").lower()
                        # Map Odds API market key to canonical
                        market_name = "moneyline" if m_type in ("h2h", "moneyline") else m_type
                        outcomes = market.get("outcomes") or []
                        prices: dict[str, float] = {}
                        line_val: float | None = None

                        for out in outcomes:
                            name = str(out.get("name") or "selection").lower()
                            price = float(out.get("price") or 0.0)
                            if price > 0:
                                prices[name] = price
                            if "point" in out and out["point"] is not None:
                                line_val = float(out["point"])

                        if prices:
                            snapshots.append(
                                MarketSnapshot(
                                    event_id=event_id,
                                    sport=sport,
                                    league=league,
                                    event_start_utc=start_utc,
                                    observed_at_utc=bm_observed,
                                    market=market_name,
                                    prices=prices,
                                    source=f"{provider} ({bm_name})",
                                    source_url=endpoint,
                                    market_type=market_name,
                                    line_value=line_val,
                                    metadata={"raw_provider": provider, "bookmaker": bm_name},
                                )
                            )
            elif "event" in item or "prices" in item or "market" in item:
                # Direct FanDuel mapping or MarketSnapshot dictionary
                snap = FanDuelSnapshotAdapter.from_mapping(item)
                snapshots.append(snap)
                observed_timestamps.append(snap.observed_at_utc)

        snapshot_tuple = tuple(snapshots)
        event_ids = tuple(sorted({s.event_id for s in snapshot_tuple}))
        source_observed_at = observed_timestamps[0] if observed_timestamps else retrieved_at
        norm_hash = cls.compute_normalized_hash(snapshot_tuple)

        provenance = MarketProvenance(
            provider=provider,
            endpoint=endpoint,
            retrieved_at_utc=retrieved_at,
            source_observed_at_utc=source_observed_at,
            event_ids=event_ids,
            snapshot_count=len(snapshot_tuple),
            raw_payload_hash=raw_hash,
            normalized_payload_hash=norm_hash,
            provenance_class=provenance_class,
            adapter_version=adapter_version,
        )

        return snapshot_tuple, provenance

    @classmethod
    def fetch_live_feed(
        cls,
        endpoint: str,
        api_key: str | None = None,
        timeout: float = 10.0,
        provider: str = "The Odds API",
        adapter_version: str = ADAPTER_VERSION,
    ) -> tuple[tuple[MarketSnapshot, ...], MarketProvenance]:
        """Perform a read-only HTTP GET request to fetch live market feed odds.

        Zero wagering surface: purely read-only market intelligence capture.
        """
        url = endpoint
        if api_key and "apiKey=" not in url and "api_key=" not in url:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}apiKey={api_key}"

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "SAGE-C2-Market-Intelligence/1.0 (Read-Only)",
                "Accept": "application/json",
            },
        )
        retrieved_at = datetime.now(timezone.utc).isoformat()
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw_bytes = resp.read()
        except Exception as e:
            raise RuntimeError(f"LIVE_FEED_FETCH_FAILED: unable to reach live feed endpoint '{endpoint}': {e}")

        return cls.parse_raw_feed(
            raw_payload=raw_bytes,
            provider=provider,
            endpoint=endpoint,
            provenance_class=ProvenanceClass.EXTERNAL_LIVE.value,
            adapter_version=adapter_version,
            retrieved_at_utc=retrieved_at,
        )
