from pathlib import Path

from sage.experimental.sports_quant import DailySportsPortfolioEngine, ProvenanceClass, RealMarketFeedAdapter
from sage.experimental.sports_quant.portfolio_audit import build_diversity_report

FIXTURE_PATH = Path(__file__).resolve().parent.parent / "fixtures" / "sports_real_multi_sport_feed_response.json"


def test_target_50_preserves_all_fixture_sports_and_events():
    raw_payload = FIXTURE_PATH.read_text(encoding="utf-8")
    snapshots, provenance = RealMarketFeedAdapter.parse_raw_feed(
        raw_payload=raw_payload,
        provider="The Odds API Multi-Sport Fixture",
        endpoint=str(FIXTURE_PATH),
        provenance_class=ProvenanceClass.FIXTURE.value,
    )

    assert len(snapshots) == 60
    assert len(provenance.event_ids) == 20

    portfolio = DailySportsPortfolioEngine(target=50, parlay_share=0.30).build(
        snapshots, cycle_id="target-50-diversity-reconciliation"
    )

    assert portfolio.count == 50
    assert portfolio.single_count == 35
    assert portfolio.parlay_count == 15
    assert {sport for sport, count in portfolio.sport_counts.items() if count > 0} == {
        "MLB",
        "NBA",
        "NFL",
        "NHL",
    }

    sport_by_event = {snapshot.event_id: snapshot.sport for snapshot in snapshots}
    report = build_diversity_report(portfolio.records, sport_by_event, provenance=provenance)

    assert report.unique_sports == 4
    assert report.single_unique_sports == 4
    assert report.unique_events == 20
    assert report.single_unique_events == 20
    assert report.total_records == 50


def test_target_unmet_is_fail_closed_in_engine():
    raw_payload = FIXTURE_PATH.read_text(encoding="utf-8")
    snapshots, _ = RealMarketFeedAdapter.parse_raw_feed(
        raw_payload=raw_payload,
        provider="The Odds API Multi-Sport Fixture",
        endpoint=str(FIXTURE_PATH),
        provenance_class=ProvenanceClass.FIXTURE.value,
    )

    try:
        DailySportsPortfolioEngine(target=1000, parlay_share=0.30).build(
            snapshots, cycle_id="target-50-fail-closed"
        )
    except ValueError as exc:
        assert "DAILY_TARGET_UNMET" in str(exc)
    else:
        raise AssertionError("Expected DAILY_TARGET_UNMET fail-closed behavior")
