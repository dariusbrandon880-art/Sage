"""Bounded sport/competition adapters for the canonical sports contract.

Adapters normalize external event payloads. They do not implement independent
prediction engines and they never synthesize observations when a source is absent.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping

from sage.experimental.sports_contract import SportsEventIdentity


@dataclass(frozen=True)
class SportsAdapter:
    sport: str
    competition: str
    source_id: str

    def normalize_event(self, payload: Mapping[str, Any]) -> SportsEventIdentity:
        required = ("event_id", "scheduled_start_utc", "home", "away")
        missing = [key for key in required if not payload.get(key)]
        if missing:
            raise ValueError(f"ADAPTER_PAYLOAD_INCOMPLETE: {self.sport}/{self.competition}: {missing}")
        event = SportsEventIdentity(
            event_id=str(payload["event_id"]),
            sport=self.sport,
            competition=self.competition,
            scheduled_start_utc=str(payload["scheduled_start_utc"]),
            home_competitor=str(payload["home"]),
            away_competitor=str(payload["away"]),
        )
        event.validate()
        return event


_ADAPTERS: Dict[tuple[str, str], SportsAdapter] = {}


def register_adapter(adapter: SportsAdapter) -> None:
    key = (adapter.sport.lower(), adapter.competition.upper())
    if key in _ADAPTERS:
        raise ValueError(f"SPORT_ADAPTER_ALREADY_REGISTERED: {key}")
    _ADAPTERS[key] = adapter


def get_adapter(sport: str, competition: str) -> SportsAdapter:
    key = (sport.lower(), competition.upper())
    try:
        return _ADAPTERS[key]
    except KeyError as exc:
        raise KeyError(f"SPORT_ADAPTER_NOT_REGISTERED: {sport}/{competition}") from exc


def registered_adapters() -> tuple[SportsAdapter, ...]:
    return tuple(_ADAPTERS.values())


# Registry declarations only. External providers must be supplied at runtime;
# these declarations intentionally contain no fabricated event data.
for _sport, _competitions in {
    "baseball": ("MLB",),
    "basketball": ("NBA", "WNBA", "NCAAB"),
    "football": ("NFL", "NCAAF"),
    "hockey": ("NHL",),
    "tennis": ("ATP", "WTA"),
}.items():
    for _competition in _competitions:
        register_adapter(SportsAdapter(_sport, _competition, source_id="runtime-provider"))

# Soccer is intentionally competition-extensible: domestic leagues,
# international competitions, and tournaments register through the same API.

__all__ = ["SportsAdapter", "register_adapter", "get_adapter", "registered_adapters"]
