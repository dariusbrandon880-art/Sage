"""C2 bootstrap enforcement primitives.

This module makes SAGE entry behavior explicit: execution surfaces must
rehydrate governed state before entering model execution.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable


@dataclass(frozen=True)
class C2BootResult:
    """Result of the pre-execution C2 handshake."""

    rehydrated: bool
    execution_surface_checked: bool
    direct_execution_available: bool
    blocker: str | None = None
    restoration_evidence: dict[str, Any] = field(default_factory=dict)
    readiness_evidence: dict[str, Any] = field(default_factory=dict)


class C2Bootstrap:
    """Mandatory entry gate before SAGE execution begins."""

    def __init__(self, available_surfaces: Iterable[str]):
        self.available_surfaces = tuple(available_surfaces)

    def boot(
        self,
        state_restored: bool = False,
        runtime_validated: bool = False,
        session_lineage_valid: bool = False,
        restoration_evidence: dict[str, Any] | None = None,
        readiness_evidence: dict[str, Any] | None = None,
    ) -> C2BootResult:
        """Perform the non-negotiable C2 entry sequence.

        Execution readiness follows a strict fail-closed chain:
        surface discovered → state restored → runtime validated → execution permitted.
        """
        rest_ev = dict(restoration_evidence or {})
        read_ev = dict(readiness_evidence or {})

        if not self.available_surfaces:
            return C2BootResult(
                rehydrated=False,
                execution_surface_checked=True,
                direct_execution_available=False,
                blocker="No execution surface available",
                restoration_evidence=rest_ev,
                readiness_evidence=read_ev,
            )

        if not state_restored:
            return C2BootResult(
                rehydrated=False,
                execution_surface_checked=True,
                direct_execution_available=False,
                blocker="State restoration evidence missing or invalid",
                restoration_evidence=rest_ev,
                readiness_evidence=read_ev,
            )

        if not runtime_validated:
            return C2BootResult(
                rehydrated=True,
                execution_surface_checked=True,
                direct_execution_available=False,
                blocker="Runtime state integrity check failed",
                restoration_evidence=rest_ev,
                readiness_evidence=read_ev,
            )

        if not session_lineage_valid:
            return C2BootResult(
                rehydrated=True,
                execution_surface_checked=True,
                direct_execution_available=False,
                blocker="Session lineage continuity broken or missing",
                restoration_evidence=rest_ev,
                readiness_evidence=read_ev,
            )

        return C2BootResult(
            rehydrated=True,
            execution_surface_checked=True,
            direct_execution_available=True,
            blocker=None,
            restoration_evidence=rest_ev,
            readiness_evidence=read_ev,
        )
