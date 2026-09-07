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
MULTI_FIXTURE_PATH = Path(__file__).resolve().parent.parent / "fixtures" / "sports_real_multi_sport_feed_response.json"


def test_real_market_feed_adapter_parses_recorded_fixture():
    assert FIXTURE_PATH.exists()
    raw_payload = FIXTURE_PATH.read_text(encoding="utf-8")

    snapshots, provenance = RealMarketFeedAdapter.parse_raw_feed(
        raw_payload=raw_payload,
        provider="The Odds API Fixture",
        endpoint=str(FIXTURE_PATH),
        provenance_class=ProvenanceClass.FIXTURE.value,
    )

    assert len(snapshots) == 11
    assert len(provenance.event_ids) == 4
    assert set(provenance.event_ids) == {
        "e2026_mlb_nyy_bos",
        "e2026_nba_bos_lal",
        "e2026_nfl_kc_sf",
        "e2026_nhl_edm_fla",
    }
    assert provenance.provenance_class == "fixture"
    assert provenance.snapshot_count == 11
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
    monkeypatch.setattr(probe.sys, "argv", ["probe_live_sports_feed.py", "--live", "--api-key", "test-key", "--target", "10"])

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
    assert prov_summary["snapshot_count"] == 11
    assert prov_summary["raw_payload_hash"] == provenance.raw_payload_hash
    assert prov_summary["normalized_payload_hash"] == provenance.normalized_payload_hash
    assert prov_summary["adapter_version"] == "1.0.0"


def test_probe_live_sports_feed_multi_sport_target_50(monkeypatch, tmp_path):
    import scripts.probe_live_sports_feed as probe

    monkeypatch.setattr(probe, "repo_root", tmp_path)
    (tmp_path / "tests" / "fixtures").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tests" / "fixtures" / "sports_real_multi_sport_feed_response.json").write_text(
        MULTI_FIXTURE_PATH.read_text(encoding="utf-8")
    )
    monkeypatch.setattr(probe.sys, "argv", ["probe_live_sports_feed.py", "--target", "50"])

    assert probe.main() == 0

    receipt_file = tmp_path / "evidence_capture" / "sports_live_probe_receipt.json"
    assert receipt_file.exists()
    receipt = json.loads(receipt_file.read_text(encoding="utf-8"))

    assert receipt["total_records"] == 50
    assert receipt["single_count"] == 35
    assert receipt["parlay_count"] == 15
    assert receipt["unique_sports"] == 4
    assert receipt["single_unique_sports"] == 4
    assert receipt["unique_events"] == 20
    assert receipt["single_unique_events"] == 20
    assert receipt["unique_prediction_ids"] == 50
    assert receipt["provenance_summary"]["provenance_class"] == "fixture"
    assert receipt["provenance_summary"]["snapshot_count"] == 60


def test_e2e_multi_sport_target_50_portfolio():
    raw_payload = MULTI_FIXTURE_PATH.read_text(encoding="utf-8")

    snapshots, provenance = RealMarketFeedAdapter.parse_raw_feed(
        raw_payload=raw_payload,
        provider="The Odds API Multi-Sport Fixture",
        endpoint=str(MULTI_FIXTURE_PATH),
        provenance_class=ProvenanceClass.FIXTURE.value,
    )

    assert len(snapshots) == 60
    assert len(provenance.event_ids) == 20

    portfolio_engine = DailySportsPortfolioEngine(target=50, parlay_share=0.30)
    portfolio = portfolio_engine.build(snapshots, cycle_id="e2e-multi-sport-50-test")

    assert portfolio.count == 50
    assert portfolio.single_count == 35
    assert portfolio.parlay_count == 15

    sport_by_event = {s.event_id: s.sport for s in snapshots}
    report = build_diversity_report(portfolio.records, sport_by_event, provenance=provenance)

    assert report.total_records == 50
    assert report.single_count == 35
    assert report.parlay_count == 15
    assert report.unique_sports == 4
    assert report.single_unique_sports == 4
    assert report.unique_events == 20
    assert report.single_unique_events == 20
    assert report.provenance_summary["snapshot_count"] == 60
