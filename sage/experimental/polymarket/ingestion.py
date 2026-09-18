"""Polymarket Phase 1 read-only ingestion adapters.

Discovery and order-book observation only. No authentication, wallet access,
order placement, capital movement, or trading execution is permitted.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence
from urllib.request import Request, urlopen

from .lane_spec import MarketObservation


class PolymarketGammaAdapter:
    """Parse Gamma discovery payloads into canonical market observations."""

    GAMMA_ENDPOINT = "https://gamma-api.polymarket.com/events"

    @classmethod
    def parse_event_payload(
        cls,
        raw_event: Mapping[str, Any],
        retrieved_at_utc: str | None = None,
    ) -> tuple[MarketObservation, ...]:
        timestamp = retrieved_at_utc or datetime.now(timezone.utc).isoformat()
        markets = raw_event.get("markets") or [raw_event]
        observations: list[MarketObservation] = []
        raw_hash = hashlib.sha256(
            json.dumps(raw_event, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        for market in markets:
            if not isinstance(market, Mapping):
                continue
            market_id = str(
                market.get("conditionId")
                or market.get("condition_id")
                or market.get("id")
                or ""
            )
            event_id = str(raw_event.get("id") or raw_event.get("event_id") or market_id)
            question = str(market.get("question") or raw_event.get("title") or "")
            prices = market.get("outcomePrices") or market.get("outcome_prices") or []
            if isinstance(prices, str):
                try:
                    prices = json.loads(prices)
                except (TypeError, ValueError):
                    prices = []
            prices = list(prices)
            if not market_id or not question or not prices:
                continue

            implied = float(prices[0])
            outcomes = market.get("outcomes") or ["Yes", "No"]
            if isinstance(outcomes, str):
                try:
                    outcomes = json.loads(outcomes)
                except (TypeError, ValueError):
                    outcomes = ["Yes", "No"]

            observations.append(
                MarketObservation(
                    market_id=market_id,
                    event_id=event_id,
                    question=question,
                    timestamp_utc=timestamp,
                    market_implied_probability=max(0.0, min(1.0, implied)),
                    order_book_depth={"outcomes": list(outcomes)},
                    spread=max(
                        0.0,
                        float(market.get("spread") or 0.0),
                    ),
                    raw_payload_hash=raw_hash,
                    provenance_source="polymarket_gamma",
                )
            )
        return tuple(observations)


class PolymarketCLOBAdapter:
    """Parse CLOB order-book payloads without performing execution."""

    CLOB_ENDPOINT = "https://clob.polymarket.com/book"

    @classmethod
    def parse_book_payload(
        cls,
        market_id: str,
        event_id: str,
        question: str,
        raw_book: Mapping[str, Any],
        retrieved_at_utc: str | None = None,
    ) -> MarketObservation:
        timestamp = retrieved_at_utc or datetime.now(timezone.utc).isoformat()
        bids = raw_book.get("bids") or []
        asks = raw_book.get("asks") or []

        def price(level: Any, default: float) -> float:
            if isinstance(level, Mapping):
                return float(level.get("price", default))
            return float(default)

        best_bid = price(bids[0], 0.0) if bids else 0.0
        best_ask = price(asks[0], 1.0) if asks else 1.0
        best_bid = max(0.0, min(1.0, best_bid))
        best_ask = max(0.0, min(1.0, best_ask))
        implied = max(0.0, min(1.0, (best_bid + best_ask) / 2.0))
        spread = max(0.0, best_ask - best_bid)
        raw_hash = hashlib.sha256(
            json.dumps(raw_book, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        return MarketObservation(
            market_id=market_id,
            event_id=event_id,
            question=question,
            timestamp_utc=timestamp,
            market_implied_probability=implied,
            order_book_depth={"bids": list(bids), "asks": list(asks)},
            spread=spread,
            raw_payload_hash=raw_hash,
            provenance_source="polymarket_clob_v2",
        )


class PolymarketIngestionEngine:
    """Normalize raw read-only feeds into canonical Phase 1 observations."""

    ADAPTER_VERSION = "1.1.0"

    @staticmethod
    def compute_raw_hash(raw_data: str | bytes) -> str:
        data = raw_data.encode("utf-8") if isinstance(raw_data, str) else raw_data
        return hashlib.sha256(data).hexdigest()

    @classmethod
    def ingest_raw_feed(
        cls,
        raw_payload: str | bytes | Mapping[str, Any] | Sequence[Any],
        provider: str = "Polymarket Gamma/CLOB",
    ) -> tuple[MarketObservation, ...]:
        if isinstance(raw_payload, (str, bytes)):
            raw = raw_payload.decode("utf-8") if isinstance(raw_payload, bytes) else raw_payload
            parsed = json.loads(raw)
        else:
            parsed = raw_payload

        events = parsed if isinstance(parsed, Sequence) and not isinstance(parsed, (str, bytes, Mapping)) else [parsed]
        observations: list[MarketObservation] = []
        for event in events:
            if isinstance(event, Mapping):
                observations.extend(
                    PolymarketGammaAdapter.parse_event_payload(event)
                )
        return tuple(observations)

    @staticmethod
    def fetch_read_only(
        url: str,
        *,
        timeout: float = 10.0,
    ) -> bytes:
        """Fetch public market data only; never sends authentication or execution data."""
        request = Request(url, method="GET", headers={"Accept": "application/json"})
        with urlopen(request, timeout=timeout) as response:
            return response.read()
