"""Fail-closed verification of a complete five-mission wave."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class FlightEvidence:
    mission_id: str
    commit_sha: str
    evidence_complete: bool
    independently_verified: bool
    verdict: str


@dataclass(frozen=True)
class FiveFlightResult:
    expected: tuple[str, ...]
    observed: tuple[str, ...]
    missing: tuple[str, ...]
    duplicates: tuple[str, ...]
    stale_commits: tuple[str, ...]
    wave_verdict: str


def reconverge_five_flight_wave(
    flights: Iterable[FlightEvidence],
    expected_missions: Iterable[str],
    expected_commit: str,
) -> FiveFlightResult:
    """Require exactly one complete, independently verified receipt per mission."""
    expected = tuple(dict.fromkeys(expected_missions))
    evidence = tuple(flights)
    counts: dict[str, int] = {}
    for flight in evidence:
        counts[flight.mission_id] = counts.get(flight.mission_id, 0) + 1

    observed = tuple(sorted(m for m in counts if m in expected))
    missing = tuple(sorted(set(expected) - set(observed)))
    duplicates = tuple(sorted(m for m, count in counts.items() if count > 1 and m in expected))
    stale = tuple(sorted({f.commit_sha for f in evidence if f.commit_sha != expected_commit}))
    valid = all(
        f.mission_id in expected
        and f.commit_sha == expected_commit
        and f.evidence_complete
        and f.independently_verified
        and f.verdict == "PASS"
        and counts[f.mission_id] == 1
        for f in evidence
    )
    verdict = "PASS" if len(expected) == 5 and valid and not missing and not duplicates and not stale else "HOLD"
    return FiveFlightResult(expected, observed, missing, duplicates, stale, verdict)
