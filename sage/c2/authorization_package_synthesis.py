"""Authorization Package Synthesis Layer for SAGE C2 Big Jump Wave.

Synthesizes comprehensive AuthorizationPackage records for discovery candidates,
mapping dependency graphs, affected namespaces, risk surfaces, verification requirements,
and evidence obligations prior to C2 authorization gate evaluation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class RiskSurface:
    score: float  # [0.0, 1.0] normalized
    affected_namespaces: tuple[str, ...]
    protected_boundary_crossing: bool
    potential_failure_modes: tuple[str, ...]


@dataclass(frozen=True)
class VerificationObligation:
    required_tests: tuple[str, ...]
    evidence_receipt_types: tuple[str, ...]
    reconvergence_required: bool


@dataclass(frozen=True)
class AuthorizationPackage:
    candidate_id: str
    description: str
    provenance_ref: str
    dependency_graph: dict[str, tuple[str, ...]]  # node -> prerequisites
    risk_surface: RiskSurface
    verification_obligation: VerificationObligation
    is_authorized: bool
    package_digest: str

    def digest(self) -> str:
        payload = {
            "candidate_id": self.candidate_id,
            "description": self.description,
            "provenance_ref": self.provenance_ref,
            "dependency_graph": {k: sorted(v) for k, v in sorted(self.dependency_graph.items())},
            "risk_score": self.risk_surface.score,
            "protected_boundary_crossing": self.risk_surface.protected_boundary_crossing,
            "required_tests": sorted(self.verification_obligation.required_tests),
            "is_authorized": self.is_authorized,
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class AuthorizationPackageSynthesizer:
    """Synthesizes C2 authorization packages and evaluates risk boundaries."""

    PROTECTED_NAMESPACES = (
        "sage/runtime/",
        "sage/core/",
        "sage/acr/",
        "sage/agents/",
    )

    def synthesize_package(
        self,
        candidate_data: Dict[str, Any],
        *,
        authorized_ids: Optional[Tuple[str, ...]] = None,
    ) -> AuthorizationPackage:
        """Synthesize a complete AuthorizationPackage for an inbound candidate."""
        candidate_id = str(candidate_data.get("candidate_id", ""))
        if not candidate_id:
            raise ValueError("candidate_id is required for synthesis")

        description = str(candidate_data.get("description", ""))
        provenance_ref = str(candidate_data.get("provenance_ref", ""))
        if not provenance_ref:
            raise ValueError("provenance_ref is required for synthesis")

        # Extract dependency graph or default to candidate_id -> prerequisites
        raw_deps = candidate_data.get("dependency_graph", {})
        if not raw_deps and "prerequisites" in candidate_data:
            prereqs = tuple(sorted(candidate_data["prerequisites"].keys()))
            dependency_graph = {candidate_id: prereqs}
        else:
            dependency_graph = {
                str(k): tuple(sorted(str(dep) for dep in v))
                for k, v in raw_deps.items()
            }

        # Analyze affected namespaces and risk surface
        affected = tuple(sorted(set(candidate_data.get("affected_namespaces", ["sage/c2/"]))))
        protected_crossing = any(
            any(affected_ns.startswith(prot) or prot in affected_ns for prot in self.PROTECTED_NAMESPACES)
            for affected_ns in affected
        )

        base_risk = float(candidate_data.get("risk_score", 0.2))
        if protected_crossing:
            base_risk = max(base_risk, 0.85)

        unfulfilled_prereqs = [
            req for req, satisfied in candidate_data.get("prerequisites", {}).items() if not satisfied
        ]
        if unfulfilled_prereqs:
            base_risk = 1.0  # High risk on unfulfilled prerequisite

        risk_surface = RiskSurface(
            score=min(1.0, max(0.0, base_risk)),
            affected_namespaces=affected,
            protected_boundary_crossing=protected_crossing,
            potential_failure_modes=tuple(sorted(candidate_data.get("failure_modes", ["unauthorized_escalation"]))),
        )

        verification_obligation = VerificationObligation(
            required_tests=tuple(sorted(candidate_data.get("required_tests", ["poetry run pytest"]))),
            evidence_receipt_types=tuple(sorted(candidate_data.get("receipt_types", ["AuthorizationReceipt"]))),
            reconvergence_required=True,
        )

        # Fail-closed authorization gate
        is_authorized = False
        if authorized_ids and candidate_id in authorized_ids and risk_surface.score < 0.8:
            is_authorized = True

        pkg = AuthorizationPackage(
            candidate_id=candidate_id,
            description=description,
            provenance_ref=provenance_ref,
            dependency_graph=dependency_graph,
            risk_surface=risk_surface,
            verification_obligation=verification_obligation,
            is_authorized=is_authorized,
            package_digest="",
        )
        object.__setattr__(pkg, "package_digest", pkg.digest())
        return pkg
