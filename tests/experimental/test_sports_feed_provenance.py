import json
import pytest
from pathlib import Path

from sage.experimental.sports_quant import (
    DailySportsPortfolioEngine,
    MarketProvenance,
    MarketSnapshot,
    PredictionBatchEngine,
    ProvenanceClass,
    RealMarketFeedAdapter,
)
from sage.experimental.sports_quant.portfolio_audit import build_diversity_report, render_receipt

FIXTURE_PATH = Path(__file__).resolve().parent.parent / "fixtures" / "sports_real_feed_response.json"


def test_real_market_feed_adapter_parses_recorded_fixture():
    assert FIXTURE_PATH.exists()
    raw_payload = FIXTURE_PATH.read_text(encoding="utf-8")

    snapshots, provenance = RealMarketFeedAdapter.parse_raw_feed(
        raw_payload=raw_payload,
        provider="The Odds API Fixture",
        endpoint=str(FIXTURE_PATH),
        provenance_class=ProvenanceClass.FIXTURE.value,
    )

    assert len(snapshots) == 30
    assert len(provenance.event_ids) == 10
    assert "e2026_mlb_nyy_bos" in provenance.event_ids
    assert "e2026_nba_bos_lal" in provenance.event_ids
    assert provenance.provenance_class == "fixture"
    assert provenance.snapshot_count == 30
    assert len(provenance.raw_payload_hash) == 64
    assert len(provenance.normalized_payload_hash) == 64


def test_provenance_integrity_enforcements_for_external_live():
    # Valid external live provenance
    valid_live = MarketProvenance(
        provider="The Odds API",
        endpoint="https://api.the-odds-api.com/v4/sports/upcoming/odds",
        retrieved_at_utc="2026-09-10T12:00:00Z",
        source_observed_at_utc="2026-09-10T12:00:00Z",
        event_ids=("e1", "e2"),
        snapshot_count=2,
        raw_payload_hash="a" * 64,
        normalized_payload_hash="b" * 64,
        provenance_class=ProvenanceClass.EXTERNAL_LIVE.value,
    )
    assert valid_live.provenance_class == "external_live"

    # Fails closed if synthetic endpoint claimed as live
    with pytest.raises(ValueError, match="PROVENANCE_INTEGRITY_VIOLATION"):
        MarketProvenance(
            provider="The Odds API",
            endpoint="synthetic://market_universe",
            retrieved_at_utc="2026-09-10T12:00:00Z",
            source_observed_at_utc="2026-09-10T12:00:00Z",
            event_ids=("e1",),
            snapshot_count=1,
            raw_payload_hash="a" * 64,
            normalized_payload_hash="b" * 64,
            provenance_class=ProvenanceClass.EXTERNAL_LIVE.value,
        )

    # Fails closed if raw payload hash missing for live
    with pytest.raises(ValueError, match="PROVENANCE_INTEGRITY_VIOLATION"):
        MarketProvenance(
            provider="The Odds API",
            endpoint="https://api.the-odds-api.com/v4/sports/upcoming/odds",
            retrieved_at_utc="2026-09-10T12:00:00Z",
            source_observed_at_utc="2026-09-10T12:00:00Z",
            event_ids=("e1",),
            snapshot_count=1,
            raw_payload_hash="",
            normalized_payload_hash="b" * 64,
            provenance_class=ProvenanceClass.EXTERNAL_LIVE.value,
        )

    # Fails closed if synthetic generator claims external_live
    with pytest.raises(ValueError, match="PROVENANCE_INTEGRITY_VIOLATION"):
        MarketProvenance(
            provider="synthetic_generator",
            endpoint="https://api.the-odds-api.com/v4/sports/upcoming/odds",
            retrieved_at_utc="2026-09-10T12:00:00Z",
            source_observed_at_utc="2026-09-10T12:00:00Z",
            event_ids=("e1",),
            snapshot_count=1,
            raw_payload_hash="a" * 64,
            normalized_payload_hash="b" * 64,
            provenance_class=ProvenanceClass.EXTERNAL_LIVE.value,
        )


def test_live_vs_synthetic_provenance_distinction():
    syn = MarketProvenance(
        provider="synthetic_generator",
        endpoint="synthetic://universe",
        retrieved_at_utc="2026-09-05T12:00:00Z",
        source_observed_at_utc="2026-09-05T12:00:00Z",
        event_ids=("mlb-001",),
        snapshot_count=1,
        raw_payload_hash="1111",
        normalized_payload_hash="2222",
        provenance_class=ProvenanceClass.SYNTHETIC.value,
    )
    assert syn.provenance_class == "synthetic"
    assert syn.to_dict()["provenance_class"] == "synthetic"

    hist = MarketProvenance(
        provider="Odds API Archive",
        endpoint="https://api.the-odds-api.com/v4/historical",
        retrieved_at_utc="2026-09-05T12:00:00Z",
        source_observed_at_utc="2026-09-01T12:00:00Z",
        event_ids=("mlb-001",),
        snapshot_count=1,
        raw_payload_hash="3333",
        normalized_payload_hash="4444",
        provenance_class=ProvenanceClass.HISTORICAL_EXTERNAL.value,
    )
    assert hist.provenance_class == "historical_external"


def test_live_probe_success_emits_external_live_receipt(monkeypatch, tmp_path):
    import scripts.probe_live_sports_feed as probe

    raw_payload = FIXTURE_PATH.read_text(encoding="utf-8")
    snapshots, live_provenance = RealMarketFeedAdapter.parse_raw_feed(
        raw_payload=raw_payload,
        provider="The Odds API",
        endpoint="https://api.the-odds-api.com/v4/sports/upcoming/odds",
        provenance_class=ProvenanceClass.EXTERNAL_LIVE.value,
    )

    monkeypatch.setattr(
        probe.RealMarketFeedAdapter,
        "fetch_live_feed",
        staticmethod(lambda **_: (snapshots, live_provenance)),
    )
    monkeypatch.setattr(probe, "repo_root", tmp_path)
    monkeypatch.setattr(probe.sys, "argv", ["probe_live_sports_feed.py", "--live", "--api-key", "test-key"])

    assert probe.main() == 0

    receipt = json.loads((tmp_path / "evidence_capture" / "sports_live_probe_receipt.json").read_text())
    assert receipt["provenance_summary"]["provenance_class"] == ProvenanceClass.EXTERNAL_LIVE.value


def test_live_probe_failure_is_nonzero_and_does_not_emit_receipt(monkeypatch, tmp_path):
    import scripts.probe_live_sports_feed as probe

    def fail_fetch(**_):
        raise RuntimeError("simulated live fetch failure")

    monkeypatch.setattr(probe.RealMarketFeedAdapter, "fetch_live_feed", staticmethod(fail_fetch))
    monkeypatch.setattr(probe, "repo_root", tmp_path)
    monkeypatch.setattr(probe.sys, "argv", ["probe_live_sports_feed.py", "--live", "--api-key", "test-key"])

    assert probe.main() == 1
    assert not (tmp_path / "evidence_capture" / "sports_live_probe_receipt.json").exists()


def test_e2e_raw_feed_to_provenance_receipt():
    raw_payload = FIXTURE_PATH.read_text(encoding="utf-8")

    # 1. Adapter parses raw payload -> MarketSnapshot list + MarketProvenance
    snapshots, provenance = RealMarketFeedAdapter.parse_raw_feed(
        raw_payload=raw_payload,
        provider="FanDuel Odds Feed",
        endpoint="https://sportsbook.fanduel.com/api/sports",
        provenance_class=ProvenanceClass.FIXTURE.value,
    )

    # 2. Prediction Engine generates paper predictions
    batch_engine = PredictionBatchEngine(model_version="shadow-v1")
    predictions = batch_engine.generate(snapshots, cycle_id="e2e-provenance-test")
    assert len(predictions) > 0

    # 3. Portfolio Engine constructs portfolio
    portfolio_engine = DailySportsPortfolioEngine(target=10, parlay_share=0.30)
    portfolio = portfolio_engine.build(snapshots, cycle_id="e2e-provenance-test")
    assert portfolio.count == 10

    # 4. Portfolio Diversity Audit builds report with provenance
    sport_by_event = {s.event_id: s.sport for s in snapshots}
    report = build_diversity_report(portfolio.records, sport_by_event, provenance=provenance)

    # 5. Render JSON receipt
    receipt_str = render_receipt(report)
    receipt_dict = json.loads(receipt_str)

    # 6. Verify receipt contains all provenance summary fields and matching hashes
    prov_summary = receipt_dict["provenance_summary"]
    assert prov_summary["source_provider"] == "FanDuel Odds Feed"
    assert prov_summary["source_endpoint"] == "https://sportsbook.fanduel.com/api/sports"
    assert prov_summary["provenance_class"] == "fixture"
    assert prov_summary["snapshot_count"] == 30
    assert prov_summary["raw_payload_hash"] == provenance.raw_payload_hash
    assert prov_summary["normalized_payload_hash"] == provenance.normalized_payload_hash
    assert prov_summary["adapter_version"] == "1.0.0"


def test_50_record_operational_portfolio_wiring_and_longitudinal_retrieval(tmp_path):
    from sage.experimental.sports_longitudinal import SportsLongitudinalLedger, ingest_portfolio_into_ledger

    raw_payload = FIXTURE_PATH.read_text(encoding="utf-8")
    snapshots, provenance = RealMarketFeedAdapter.parse_raw_feed(
        raw_payload=raw_payload,
        provider="The Odds API Fixture",
        endpoint=str(FIXTURE_PATH),
        provenance_class=ProvenanceClass.FIXTURE.value,
    )

    cycle_id = "test-50-batch-cycle-2026"
    engine = DailySportsPortfolioEngine(target=50, parlay_share=0.30)
    portfolio = engine.build(snapshots, cycle_id=cycle_id)

    assert portfolio.count == 50
    assert portfolio.single_count == 35
    assert portfolio.parlay_count == 15

    # Diversity audit verification: must preserve all 10 unique source events and 4 unique sports
    sport_by_event = {s.event_id: s.sport for s in snapshots}
    report = build_diversity_report(portfolio.records, sport_by_event, provenance=provenance)
    assert report.total_records == 50
    assert report.single_count == 35
    assert report.parlay_count == 15
    assert report.unique_events == 10
    assert report.unique_sports == 4
    assert report.single_unique_events == 10
    assert report.single_unique_sports == 4

    ledger_file = tmp_path / "sports_longitudinal_ledger.json"
    ledger = SportsLongitudinalLedger(storage_path=ledger_file)

    locked_preds = ingest_portfolio_into_ledger(
        portfolio_records=portfolio.records,
        snapshots=snapshots,
        ledger=ledger,
        cycle_id=cycle_id,
        provenance=provenance,
    )

    assert len(locked_preds) == 50
    assert len(ledger.predictions) == 50

    # Verify reloading ledger retrieves exact batch by cycle_id
    reloaded_ledger = SportsLongitudinalLedger(storage_path=ledger_file)
    batch_preds = [p for p in reloaded_ledger.get_pending_predictions() if p.cycle_id == cycle_id]
    assert len(batch_preds) == 50

    singles = [p for p in batch_preds if not p.is_parlay]
    parlays = [p for p in batch_preds if p.is_parlay]
    assert len(singles) == 35
    assert len(parlays) == 15

    # Verify hash integrity on all locked predictions
    for p in batch_preds:
        assert p.compute_sha256_hash() == p.sha256_receipt_hash


def test_portfolio_engine_fails_closed_when_snapshots_insufficient():
    # Only 1 event snapshot -> cannot produce 50 target
    small_snapshots = [
        MarketSnapshot(
            event_id="e_small",
            sport="MLB",
            league="MLB",
            event_start_utc="2026-09-10T19:00:00Z",
            observed_at_utc="2026-09-10T12:00:00Z",
            market="moneyline",
            prices={"home": 1.9, "away": 1.9},
            source="test",
        )
    ]
    engine = DailySportsPortfolioEngine(target=50, parlay_share=0.30)
    with pytest.raises(ValueError, match="DAILY_TARGET_UNMET"):
        engine.build(small_snapshots, cycle_id="fail-closed-cycle")
