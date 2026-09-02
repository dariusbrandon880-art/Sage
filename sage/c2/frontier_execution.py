"""C2 execution primitives for the active SAGE progression fronts.

This module orchestrates existing SAGE components; it does not create a second
authority layer and does not promote observations into canonical knowledge.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FrontierResult:
    frontier: str
    status: str
    result: Any = None
    error: str | None = None


PROGRESSION_FRONT_NAMES = (
    "native_persisted_evidence",
    "progression_receipts",
)


def run_frontier(frontier: str, operation: Callable[[], Any]) -> FrontierResult:
    """Execute one bounded progression frontier and return an observable result."""
    if frontier not in PROGRESSION_FRONT_NAMES:
        raise ValueError(f"Unknown C2 progression frontier: {frontier}")
    try:
        return FrontierResult(frontier=frontier, status="OBSERVED", result=operation())
    except Exception as exc:
        return FrontierResult(frontier=frontier, status="HOLD", error=str(exc))


def load_persisted_evidence(loader: Any) -> FrontierResult:
    return run_frontier("native_persisted_evidence", loader.load_all)


def serialize_progression_receipt(serializer: Any, receipt: Any) -> FrontierResult:
    return run_frontier("progression_receipts", lambda: serializer.serialize(receipt))
