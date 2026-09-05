"""Deterministic diversity receipt for Sports/RCE shadow portfolios."""

from dataclasses import asdict, dataclass
from typing import Iterable, Mapping

from .prediction import PredictionRecord


@dataclass(frozen=True)
class PortfolioDiversityReport:
    """Auditable portfolio diversity metrics.

    Parent parlays are reported separately from singles so parlay multiplication
    cannot masquerade as additional underlying market diversity.
    """

    total_records: int
    unique_events: int
    unique_sports: int
    unique_market_types: int
    unique_event_market_types: int
    unique_event_market_lines: int
    unique_prediction_ids: int
    single_count: int
    parlay_count: int
    single_unique_events: int
    single_unique_sports: int
    single_unique_market_types: int
    single_unique_event_market_types: int
    single_unique_event_market_lines: int
    single_unique_prediction_ids: int

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


def _identity(record: PredictionRecord) -> tuple[str, str, str, str]:
    return (
        record.event_id,
        record.canonical_market_type,
        record.selection.strip().lower(),
        record.canonical_line_value,
    )


def _metrics(records: tuple[PredictionRecord, ...], sport_by_event: Mapping[str, str]) -> dict[str, int]:
    event_market_types = {
        (r.event_id, r.canonical_market_type) for r in records
    }
    event_market_lines = {
        (r.event_id, r.canonical_market_type, r.canonical_line_value)
        for r in records
    }
    return {
        "events": len({r.event_id for r in records}),
        "sports": len({sport_by_event[r.event_id].upper() for r in records if r.event_id in sport_by_event}),
        "market_types": len({r.canonical_market_type for r in records}),
        "event_market_types": len(event_market_types),
        "event_market_lines": len(event_market_lines),
        "prediction_ids": len({r.prediction_id for r in records}),
    }


def build_diversity_report(
    records: Iterable[PredictionRecord],
    sport_by_event: Mapping[str, str],
) -> PortfolioDiversityReport:
    """Build the canonical eight-metric diversity receipt from portfolio records."""

    all_records = tuple(records)
    singles = tuple(r for r in all_records if not r.is_parlay)
    all_metrics = _metrics(all_records, sport_by_event)
    single_metrics = _metrics(singles, sport_by_event)
    return PortfolioDiversityReport(
        total_records=len(all_records),
        unique_events=all_metrics["events"],
        unique_sports=all_metrics["sports"],
        unique_market_types=all_metrics["market_types"],
        unique_event_market_types=all_metrics["event_market_types"],
        unique_event_market_lines=all_metrics["event_market_lines"],
        unique_prediction_ids=all_metrics["prediction_ids"],
        single_count=len(singles),
        parlay_count=len(all_records) - len(singles),
        single_unique_events=single_metrics["events"],
        single_unique_sports=single_metrics["sports"],
        single_unique_market_types=single_metrics["market_types"],
        single_unique_event_market_types=single_metrics["event_market_types"],
        single_unique_event_market_lines=single_metrics["event_market_lines"],
        single_unique_prediction_ids=single_metrics["prediction_ids"],
    )


def render_receipt(report: PortfolioDiversityReport) -> str:
    """Render a stable, machine-readable JSON receipt."""
    import json

    return json.dumps(report.to_dict(), sort_keys=True, separators=(",", ":"))
