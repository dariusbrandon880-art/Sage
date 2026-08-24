"""Frontier Intelligence Bridge for SAGE C2 Big Jump Wave execution.

Adapts a SAGI FlightSelectionProposal into C2 MultiFrontierDispatcher flight missions
while enforcing fail-closed authorization, selection digest verification,
and candidate safety gates.

Governance Laws:
- Fail-Closed Authorization: Every candidate must have explicit authorization (authorized == True).
- No Autonomous Promotion: Proposals are selection candidates until authorized by C2.
- Selection Digest Verification: Recomputes and validates proposal selection_digest before wave build.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import importlib
import subprocess
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class AuthorizedCandidate:
    candidate_id: str
    authorized: bool
    authorized_by: str
    authorization_token: str


@dataclass(frozen=True)
class FrontierBridgeReceipt:
    selection_digest: str
    frontier_digest: str
    authorized_candidate_ids: Tuple[str, ...]
    unauthorized_candidate_ids: Tuple[str, ...]
    bridge_verdict: str
    commit_sha: str
    dispatch_receipt: Optional[Dict[str, Any]] = None
    provenance_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _get_current_commit_sha() -> str:
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except Exception:
        return "UNKNOWN_COMMIT"


def compute_bridge_provenance_hash(
    selection_digest: str, frontier_digest: str, authorized_ids: Tuple[str, ...], commit_sha: str
) -> str:
    payload = f"{selection_digest}:{frontier_digest}:{','.join(sorted(authorized_ids))}:{commit_sha}".encode(
        "utf-8"
    )
    return hashlib.sha256(payload).hexdigest()


class FrontierIntelligenceBridge:
    """Governed bridge mapping SAGI proposals to C2 MultiFrontierDispatcher execution waves."""

    def __init__(self, commit_sha: Optional[str] = None) -> None:
        self.commit_sha = commit_sha or _get_current_commit_sha()

    def adapt_and_dispatch(
        self,
        proposal: Any,  # FlightSelectionProposal
        authorized_candidates: Dict[str, AuthorizedCandidate],
    ) -> FrontierBridgeReceipt:
        """Validate proposal, enforce candidate authorization gate, adapt to dispatcher, and execute wave."""
        if not hasattr(proposal, "selection_digest") or not proposal.selection_digest:
            raise ValueError("Invalid proposal: missing selection_digest")
        if not hasattr(proposal, "frontier_digest") or not proposal.frontier_digest:
            raise ValueError("Invalid proposal: missing frontier_digest")
        if not hasattr(proposal, "candidates") or not proposal.candidates:
            raise ValueError("Invalid proposal: candidates list is empty")

        if len(proposal.candidates) != 5:
            raise ValueError(
                f"Proposal must contain exactly 5 candidates, found {len(proposal.candidates)}"
            )

        # Re-verify selection digest
        mod_selector = importlib.import_module("sage.experimental.sagi_discovery_flight_selector")
        SAGIDiscoveryFlightSelector = mod_selector.SAGIDiscoveryFlightSelector

        recomputed_digest = SAGIDiscoveryFlightSelector._digest(
            proposal.candidates, proposal.frontier_digest
        )
        if recomputed_digest != proposal.selection_digest:
            raise ValueError(
                f"Selection digest mismatch! Recomputed '{recomputed_digest}' != expected '{proposal.selection_digest}'"
            )

        authorized_ids: List[str] = []
        unauthorized_ids: List[str] = []

        for candidate in proposal.candidates:
            cid = candidate.candidate_id
            if candidate.safety <= 0.0:
                raise ValueError(f"Candidate '{cid}' has unsafe score safety={candidate.safety}")
            if not candidate.provenance_ref:
                raise ValueError(f"Candidate '{cid}' missing required provenance_ref")

            auth_record = authorized_candidates.get(cid)
            if auth_record and auth_record.authorized:
                authorized_ids.append(cid)
            else:
                unauthorized_ids.append(cid)

        # Fail closed if any selected candidate is unauthorized
        if unauthorized_ids:
            raise PermissionError(
                f"Frontier Intelligence Gate Violation: Candidate(s) {unauthorized_ids} lack explicit C2 authorization"
            )

        # Dispatch wave via MultiFrontierDispatcher
        mod_dispatcher = importlib.import_module("sage.c2.multi_frontier_dispatch")
        MultiFrontierDispatcher = mod_dispatcher.MultiFrontierDispatcher

        dispatcher = MultiFrontierDispatcher(commit_sha=self.commit_sha)
        dispatch_receipt = dispatcher.dispatch_all()

        provenance_hash = compute_bridge_provenance_hash(
            proposal.selection_digest,
            proposal.frontier_digest,
            tuple(sorted(authorized_ids)),
            self.commit_sha,
        )

        overall_verdict = (
            "PASS" if (not unauthorized_ids and dispatch_receipt.wave_verdict == "PASS") else "HOLD"
        )

        return FrontierBridgeReceipt(
            selection_digest=proposal.selection_digest,
            frontier_digest=proposal.frontier_digest,
            authorized_candidate_ids=tuple(sorted(authorized_ids)),
            unauthorized_candidate_ids=tuple(sorted(unauthorized_ids)),
            bridge_verdict=overall_verdict,
            commit_sha=self.commit_sha,
            dispatch_receipt=dispatch_receipt.to_dict(),
            provenance_hash=provenance_hash,
        )
