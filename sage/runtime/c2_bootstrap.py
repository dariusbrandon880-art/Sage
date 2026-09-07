"""C2 bootstrap enforcement primitives.

This module makes SAGE entry behavior explicit: execution surfaces must
rehydrate governed state before entering model execution.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable

if TYPE_CHECKING:
    from sage.acr.bridge import ACRBridge
    from sage.acr.session.session_state import SessionStateManager


@dataclass(frozen=True)
class C2BootResult:
    """Result of the pre-execution C2 handshake."""

    rehydrated: bool
    execution_surface_checked: bool
    direct_execution_available: bool
    blocker: str | None = None


class C2Bootstrap:
    """Mandatory entry gate before SAGE execution begins.

    Corrects the false inference:
      surfaces != rehydrated
      surfaces != execution readiness
    """

    def __init__(
        self,
        available_surfaces: Iterable[str],
        acr_bridge: ACRBridge | None = None,
        session_manager: SessionStateManager | None = None,
        required_session_id: str | None = None,
    ):
        self.available_surfaces = tuple(available_surfaces)
        self.acr_bridge = acr_bridge
        self.session_manager = session_manager
        self.required_session_id = required_session_id

    def boot(self) -> C2BootResult:
        """Perform the non-negotiable C2 entry sequence.

        The caller supplies actual available execution surfaces and state bridges.
        Surface presence alone does not imply rehydration or execution readiness.
        """
        if not self.available_surfaces:
            return C2BootResult(
                rehydrated=False,
                execution_surface_checked=True,
                direct_execution_available=False,
                blocker="No execution surface available",
            )

        rehydrated = False
        blocker = None

        if self.session_manager is not None:
            if self.required_session_id:
                session = self.session_manager.retrieve_session(self.required_session_id)
                if session is not None:
                    rehydrated = True
                else:
                    blocker = f"Required session '{self.required_session_id}' not found in SessionStateManager"
            else:
                sessions = self.session_manager.list_all()
                if sessions:
                    rehydrated = True
                else:
                    blocker = "SessionStateManager contains no persisted sessions"
        elif self.acr_bridge is not None:
            state = self.acr_bridge.load_state()
            lineage = self.acr_bridge.get_lineage()
            if state or lineage:
                rehydrated = True
            else:
                blocker = "ACRBridge contains no persisted continuity state or lineage"
        else:
            blocker = "Governed state rehydration not verified (no ACRBridge or SessionStateManager supplied)"

        if not rehydrated:
            return C2BootResult(
                rehydrated=False,
                execution_surface_checked=True,
                direct_execution_available=False,
                blocker=blocker,
            )

        return C2BootResult(
            rehydrated=True,
            execution_surface_checked=True,
            direct_execution_available=True,
        )
