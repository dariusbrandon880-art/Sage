"""C2 execution primitives for the five active SAGE capability fronts.

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


FIVE_FRONT_NAMES = (
    "drive_continuity",
    "governed_execution",
    "sports_research",
    "native_persisted_evidence",
    "progression_receipts",
)


def run_frontier(frontier: str, operation: Callable[[], Any]) -> FrontierResult:
    """Execute one bounded frontier and return an observable result."""
    if frontier not in FIVE_FRONT_NAMES:
        raise ValueError(f"Unknown C2 frontier: {frontier}")
    try:
        return FrontierResult(frontier=frontier, status="OBSERVED", result=operation())
    except Exception as exc:
        return FrontierResult(frontier=frontier, status="HOLD", error=str(exc))


def drive_dry_run(sync_manager: Any, credentials_path: str = ".sage/credentials.json") -> FrontierResult:
    return run_frontier(
        "drive_continuity",
        lambda: sync_manager.sync_projection_to_drive(
            credentials_path=credentials_path,
            target_dir="SAGE",
        ),
    )


def governed_execution(controller: Any, mission: dict[str, Any], execution_result: dict[str, Any]) -> FrontierResult:
    def _run() -> dict[str, Any]:
        receipts = [controller.intake_mission(mission), controller.prioritize(), controller.validate_preflight(), controller.prepare_handoff(), controller.emit_handoff(), controller.receive_execution_result(execution_result), controller.validate_evidence({"execution_result": execution_result}), controller.classify_outcome()]
        return {"state": controller.current_state.value, "receipt_count": len(receipts)}
    return run_frontier("governed_execution", _run)


def load_persisted_evidence(loader: Any) -> FrontierResult:
    return run_frontier("native_persisted_evidence", loader.load_all)


def serialize_progression_receipt(serializer: Any, receipt: Any) -> FrontierResult:
    return run_frontier("progression_receipts", lambda: serializer.serialize(receipt))
