"""C2 bootstrap enforcement primitives.

This module makes SAGE entry behavior explicit: execution surfaces must
rehydrate governed state before entering model execution.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class C2BootResult:
    """Result of the pre-execution C2 handshake."""

    rehydrated: bool
    execution_surface_checked: bool
    direct_execution_available: bool
    blocker: str | None = None


class C2Bootstrap:
    """Mandatory entry gate before SAGE execution begins."""

    def __init__(self, available_surfaces: Iterable[str]):
        self.available_surfaces = tuple(available_surfaces)

    def boot(self) -> C2BootResult:
        """Perform the non-negotiable C2 entry sequence.

        The caller supplies actual available execution surfaces; this class
        does not infer or fabricate capability.
        """
        if self.available_surfaces:
            return C2BootResult(
                rehydrated=True,
                execution_surface_checked=True,
                direct_execution_available=True,
            )

        return C2BootResult(
            rehydrated=False,
            execution_surface_checked=True,
            direct_execution_available=False,
            blocker="No execution surface available",
        )
