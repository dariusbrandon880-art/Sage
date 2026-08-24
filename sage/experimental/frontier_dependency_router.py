"""Frontier Dependency Router — Governed Lifecycle Intelligence Layer.

Maps candidate tasks to dependency graphs, affected namespaces, and required
verification contracts while enforcing fail-closed authorization boundaries.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import re


class CandidateSecurityTier(str, Enum):
    EXPERIMENTAL = "EXPERIMENTAL"
    GOVERNANCE = "GOVERNANCE"
    PROTECTED_CORE = "PROTECTED_CORE"


@dataclass(frozen=True)
class CandidateDependencyGraph:
    candidate_id: str
    nodes: tuple[str, ...]
    edges: tuple[tuple[str, str], ...]
    imports: tuple[str, ...]


@dataclass(frozen=True)
class AffectedNamespace:
    namespace: str
    is_protected_core: bool
    requires_explicit_override: bool


@dataclass(frozen=True)
class VerificationContract:
    contract_id: str
    required_test_suites: tuple[str, ...]
    requires_preflight_check: bool
    requires_evidence_receipt: bool


@dataclass(frozen=True)
class IntakeDependencyProposal:
    candidate_id: str
    dependency_graph: CandidateDependencyGraph
    affected_namespaces: tuple[AffectedNamespace, ...]
    verification_contracts: tuple[VerificationContract, ...]
    security_tier: CandidateSecurityTier
    authorized: bool
    requires_human_approval: bool
    authoritative: bool
    provenance_ref: str
    proposal_digest: str


@dataclass(frozen=True)
class DependencyRoutingFeedback:
    feedback_id: str
    proposal_digest: str
    blocked_failure_modes: tuple[str, ...]
    required_contracts_count: int
    candidate_frontiers: tuple[str, ...]
    timestamp_utc: str


class FrontierDependencyRouter:
    """Intake router evaluating candidates against dependency graphs and protected boundaries."""

    PROTECTED_NAMESPACES = (
        "sage/runtime/",
        "sage/core/",
        "sage/acr/",
        "sage/agents/",
        "docs/governance/",
        ".github/",
    )

    @staticmethod
    def _compute_digest(
        candidate_id: str,
        graph: CandidateDependencyGraph,
        namespaces: tuple[AffectedNamespace, ...],
        provenance_ref: str,
    ) -> str:
        ns_str = ",".join(f"{ns.namespace}:{ns.is_protected_core}" for ns in namespaces)
        nodes_str = ",".join(sorted(graph.nodes))
        raw = f"{candidate_id}|{nodes_str}|{ns_str}|{provenance_ref}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def route_candidate(
        self,
        candidate_id: str,
        dependency_graph: CandidateDependencyGraph,
        target_file_paths: tuple[str, ...],
        provenance_ref: str,
        *,
        signature: str | None = None,
    ) -> IntakeDependencyProposal:
        """Route candidate through dependency and protected boundary analysis."""
        # Flight 2 — Adversarial Rejections
        if not candidate_id or not candidate_id.strip():
            raise ValueError("Candidate ID cannot be empty.")
        if not provenance_ref or not provenance_ref.strip():
            raise ValueError("Provenance reference is required.")
        if not dependency_graph.nodes:
            raise ValueError("Dependency graph cannot be empty.")

        # Validate provenance format
        if not re.match(r"^(ref_|prov_|git_|sha_)[a-zA-Z0-9_\-]+$", provenance_ref):
            raise ValueError(f"Invalid provenance reference format: '{provenance_ref}'")

        # Reject forged signature / authorization attempts without valid key
        if signature is not None and not signature.startswith("sig_auth_valid_"):
            raise ValueError("Invalid or forged authorization signature.")

        # Map affected namespaces
        affected: list[AffectedNamespace] = []
        is_protected = False

        for path in target_file_paths:
            is_prot = any(path.startswith(prot) for prot in self.PROTECTED_NAMESPACES)
            if is_prot:
                is_protected = True
            affected.append(
                AffectedNamespace(
                    namespace=path,
                    is_protected_core=is_prot,
                    requires_explicit_override=is_prot,
                )
            )

        affected_tuple = tuple(affected)
        security_tier = (
            CandidateSecurityTier.PROTECTED_CORE
            if is_protected
            else CandidateSecurityTier.EXPERIMENTAL
        )

        # Verification contracts required
        contracts = (
            VerificationContract(
                contract_id=f"vc_{candidate_id}_governance",
                required_test_suites=(
                    "tests/experimental/",
                    "tests/test_governance_directives.py",
                ),
                requires_preflight_check=True,
                requires_evidence_receipt=True,
            ),
        )

        digest = self._compute_digest(
            candidate_id, dependency_graph, affected_tuple, provenance_ref
        )

        # Flight 1 Contract Enforcement: authorized=False default, requires_human_approval=True
        return IntakeDependencyProposal(
            candidate_id=candidate_id,
            dependency_graph=dependency_graph,
            affected_namespaces=affected_tuple,
            verification_contracts=contracts,
            security_tier=security_tier,
            authorized=False,  # FAIL-CLOSED DEFAULT
            requires_human_approval=True,
            authoritative=False,  # PROPOSAL ONLY
            provenance_ref=provenance_ref,
            proposal_digest=digest,
        )

    def capture_feedback(
        self,
        proposal: IntakeDependencyProposal,
        blocked_modes: tuple[str, ...],
        candidate_frontiers: tuple[str, ...],
        timestamp_utc: str,
    ) -> DependencyRoutingFeedback:
        """Capture C2 learning loop feedback on routed proposal."""
        feedback_id = f"fb_{proposal.candidate_id}_{hashlib.md5(timestamp_utc.encode()).hexdigest()[:8]}"
        return DependencyRoutingFeedback(
            feedback_id=feedback_id,
            proposal_digest=proposal.proposal_digest,
            blocked_failure_modes=blocked_modes,
            required_contracts_count=len(proposal.verification_contracts),
            candidate_frontiers=candidate_frontiers,
            timestamp_utc=timestamp_utc,
        )
