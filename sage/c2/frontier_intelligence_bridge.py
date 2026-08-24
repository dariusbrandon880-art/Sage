"""Frontier Intelligence Bridge connecting discovery proposals to C2 MultiFrontierDispatcher.

Provides a fail-closed authorization gate ensuring discovery candidates
cannot execute through MultiFrontierDispatcher without explicit C2 authorization.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping

from sage.c2.multi_frontier_dispatch import (
    MultiFrontierDispatcher,
    MultiFrontierDispatchReceipt,
)


@dataclass(frozen=True)
class FrontierBridgeDispatchReceipt:
    proposal_frontier_digest: str
    proposal_selection_digest: str
    authorized_candidate_ids: tuple[str, ...]
    unauthorized_candidate_ids: tuple[str, ...]
    is_authorized: bool
    dispatch_result: MultiFrontierDispatchReceipt | None
    bridge_digest: str

    def digest(self) -> str:
        payload = {
            "proposal_frontier_digest": self.proposal_frontier_digest,
            "proposal_selection_digest": self.proposal_selection_digest,
            "authorized_candidate_ids": sorted(self.authorized_candidate_ids),
            "unauthorized_candidate_ids": sorted(self.unauthorized_candidate_ids),
            "is_authorized": self.is_authorized,
            "dispatch_verdict": self.dispatch_result.wave_verdict if self.dispatch_result else "REJECTED_UNAUTHORIZED",
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class FrontierIntelligenceBridge:
    """Fail-closed bridge adapting discovery proposals to MultiFrontierDispatcher."""

    def __init__(self, dispatcher: MultiFrontierDispatcher | None = None):
        self.dispatcher = dispatcher or MultiFrontierDispatcher()

    def bridge_and_dispatch(
        self,
        proposal: Any,
        *,
        authorized_candidate_ids: tuple[str, ...],
        commit_sha: str | None = None,
    ) -> FrontierBridgeDispatchReceipt:
        """Evaluate candidate authorizations and dispatch via MultiFrontierDispatcher if approved."""
        if not proposal or not getattr(proposal, "candidates", None):
            raise ValueError("proposal requires valid discovery candidates")

        candidates = proposal.candidates
        candidate_ids = tuple(getattr(c, "candidate_id", "") for c in candidates)
        authorized_set = set(authorized_candidate_ids)

        authorized_ids = tuple(sorted(cid for cid in candidate_ids if cid in authorized_set))
        unauthorized_ids = tuple(sorted(cid for cid in candidate_ids if cid not in authorized_set))

        is_authorized = len(unauthorized_ids) == 0 and len(authorized_ids) == len(candidate_ids)

        if not is_authorized:
            receipt = FrontierBridgeDispatchReceipt(
                proposal_frontier_digest=getattr(proposal, "frontier_digest", ""),
                proposal_selection_digest=getattr(proposal, "selection_digest", ""),
                authorized_candidate_ids=authorized_ids,
                unauthorized_candidate_ids=unauthorized_ids,
                is_authorized=False,
                dispatch_result=None,
                bridge_digest="",
            )
            object.__setattr__(receipt, "bridge_digest", receipt.digest())
            return receipt

        # Dispatch via MultiFrontierDispatcher
        if commit_sha:
            self.dispatcher.commit_sha = commit_sha

        dispatch_result = self.dispatcher.dispatch_all()

        receipt = FrontierBridgeDispatchReceipt(
            proposal_frontier_digest=getattr(proposal, "frontier_digest", ""),
            proposal_selection_digest=getattr(proposal, "selection_digest", ""),
            authorized_candidate_ids=authorized_ids,
            unauthorized_candidate_ids=unauthorized_ids,
            is_authorized=True,
            dispatch_result=dispatch_result,
            bridge_digest="",
        )
        object.__setattr__(receipt, "bridge_digest", receipt.digest())
        return receipt
