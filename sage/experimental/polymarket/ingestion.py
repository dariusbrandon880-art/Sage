"""Polymarket Read-Only Ingestion Boundary & Adapters.

Implements read-only Gamma discovery & CLOB order-book observation adapters and normalization.
Never authenticates, wagers, or executes transactions (wagering_executed = False).
"""

import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from .lane_spec import (
    ExecutionGuardViolation,
    LifecycleStage,
    PolymarketEvidenceRecord,
    PolymarketMarketSnapshot,
    PolymarketObservation,
)


class PolymarketGammaAdapter:
    """Read-only adapter for Polymarket Gamma API (market/event discovery)."""

    GAMMA_ENDPOINT = "https://gamma-api.polymarket.com/events"

    @classmethod
    def parse_event_payload(cls, raw_event: Mapping[str, Any], retrieved_at_utc: str | None = None) -> tuple[PolymarketMarketSnapshot, ...]:
        now_utc = retrieved_at_utc or datetime.now(timezone.utc).isoformat()
        snapshots: list[PolymarketMarketSnapshot] = []

        markets = raw_event.get("markets") or [raw_event]
        for m in markets:
            if not isinstance(m, dict):
                continue
            condition_id = str(m.get("conditionId") or m.get("condition_id") or "")
            question_id = str(m.get("questionID") or m.get("question_id") or condition_id)
            question = str(m.get("question") or raw_event.get("title") or "")

            raw_outcomes = m.get("outcomes") or ["Yes", "No"]
            if isinstance(raw_outcomes, str):
                try:
                    raw_outcomes = json.loads(raw_outcomes)
                except Exception:
                    raw_outcomes = ["Yes", "No"]
            outcomes = tuple(str(o) for o in raw_outcomes)

            raw_prices = m.get("outcomePrices") or m.get("outcome_prices") or [0.5, 0.5]
            if isinstance(raw_prices, str):
                try:
                    raw_prices = json.loads(raw_prices)
                except Exception:
                    raw_prices = [0.5, 0.5]

            prices: dict[str, float] = {}
            for idx, out in enumerate(outcomes):
                p_val = float(raw_prices[idx]) if idx < len(raw_prices) else 0.5
                prices[out] = min(max(p_val, 0.0), 1.0)

            vol = float(m.get("volume24hr") or m.get("volume") or 0.0)
            liq = float(m.get("liquidity") or 0.0)
            active = bool(m.get("active", True))
            closed = bool(m.get("closed", False))

            if condition_id and question_id:
                snapshots.append(
                    PolymarketMarketSnapshot(
                        condition_id=condition_id,
                        question_id=question_id,
                        question=question,
                        outcomes=outcomes,
                        outcome_prices=prices,
                        observed_at_utc=now_utc,
                        volume_24h=vol,
                        liquidity=liq,
                        active=active,
                        closed=closed,
                        source="Polymarket Gamma API",
                        source_url=cls.GAMMA_ENDPOINT,
                        metadata={"raw_event_id": str(raw_event.get("id") or "")},
                    )
                )

        return tuple(snapshots)


class PolymarketCLOBAdapter:
    """Read-only adapter for Polymarket CLOB API (order book & mid-market price observer)."""

    CLOB_ENDPOINT = "https://clob.polymarket.com/book"

    @classmethod
    def parse_book_payload(
        cls,
        condition_id: str,
        question_id: str,
        question: str,
        raw_book: Mapping[str, Any],
        retrieved_at_utc: str | None = None,
    ) -> PolymarketMarketSnapshot:
        now_utc = retrieved_at_utc or datetime.now(timezone.utc).isoformat()
        bids = raw_book.get("bids") or []
        asks = raw_book.get("asks") or []

        best_bid = float(bids[0]["price"]) if bids and isinstance(bids[0], dict) else 0.5
        best_ask = float(asks[0]["price"]) if asks and isinstance(asks[0], dict) else 0.5
        mid_price = min(max((best_bid + best_ask) / 2.0, 0.0), 1.0)

        prices = {"Yes": round(mid_price, 6), "No": round(1.0 - mid_price, 6)}

        return PolymarketMarketSnapshot(
            condition_id=condition_id,
            question_id=question_id,
            question=question,
            outcomes=("Yes", "No"),
            outcome_prices=prices,
            observed_at_utc=now_utc,
            volume_24h=0.0,
            liquidity=0.0,
            active=True,
            closed=False,
            source="Polymarket CLOB API",
            source_url=cls.CLOB_ENDPOINT,
            metadata={"best_bid": best_bid, "best_ask": best_ask},
        )


class PolymarketIngestionEngine:
    """Read-only market intelligence ingestion engine."""

    ADAPTER_VERSION = "1.0.0"

    @staticmethod
    def compute_raw_hash(raw_data: str | bytes) -> str:
        data = raw_data.encode("utf-8") if isinstance(raw_data, str) else raw_data
        return hashlib.sha256(data).hexdigest()

    @classmethod
    def ingest_raw_feed(
        cls,
        raw_payload: str | bytes | Mapping[str, Any] | Sequence[Any],
        provider: str = "Polymarket Gamma/CLOB",
        provenance_class: str = "fixture",
        parent_hash: str = "GENESIS",
    ) -> tuple[tuple[PolymarketObservation, ...], PolymarketEvidenceRecord]:
        now_utc = datetime.now(timezone.utc).isoformat()

        if isinstance(raw_payload, (str, bytes)):
            raw_str = raw_payload.decode("utf-8") if isinstance(raw_payload, bytes) else raw_payload
            raw_hash = cls.compute_raw_hash(raw_str)
            try:
                parsed = json.loads(raw_str)
            except Exception as e:
                raise ValueError(f"POLYMARKET_RAW_FEED_PARSE_ERROR: invalid JSON: {e}")
        else:
            raw_str = json.dumps(raw_payload, sort_keys=True)
            raw_hash = cls.compute_raw_hash(raw_str)
            parsed = raw_payload

        events = parsed if isinstance(parsed, list) else [parsed]
        all_snapshots: list[PolymarketMarketSnapshot] = []

        for ev in events:
            if isinstance(ev, dict):
                snaps = PolymarketGammaAdapter.parse_event_payload(ev, retrieved_at_utc=now_utc)
                all_snapshots.extend(snaps)

        observations: list[PolymarketObservation] = []
        for idx, snap in enumerate(all_snapshots):
            obs_id = f"obs_{snap.condition_id}_{idx}"
            norm_hash = snap.canonical_hash
            observations.append(
                PolymarketObservation(
                    observation_id=obs_id,
                    snapshot=snap,
                    retrieved_at_utc=now_utc,
                    raw_payload_hash=raw_hash,
                    normalized_payload_hash=norm_hash,
                    provenance_class=provenance_class,
                    wagering_executed=False,
                )
            )

        obs_tuple = tuple(observations)
        evidence_id = f"evi_{now_utc.replace(':', '').replace('-', '')}"
        obs_summary_hash = hashlib.sha256(json.dumps([o.observation_id for o in obs_tuple]).encode("utf-8")).hexdigest()

        rec_hash = PolymarketEvidenceRecord.compute_record_hash(
            evidence_id=evidence_id,
            stage=LifecycleStage.DISCOVER,
            parent_hash=parent_hash,
            timestamp_utc=now_utc,
            obs_hash=obs_summary_hash,
        )

        evidence = PolymarketEvidenceRecord(
            evidence_id=evidence_id,
            stage=LifecycleStage.DISCOVER,
            observation=obs_tuple[0] if obs_tuple else None,
            forecast=None,
            parent_hash=parent_hash,
            current_hash=rec_hash,
            timestamp_utc=now_utc,
            provenance_metadata={"provider": provider, "observation_count": len(obs_tuple)},
            wagering_executed=False,
        )

        return obs_tuple, evidence
