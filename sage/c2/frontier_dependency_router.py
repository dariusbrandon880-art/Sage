"""Frontier Dependency Router for SAGE C2 Lifecycle Intake.

Analyzes candidate dependencies, target file paths, and protected namespace interactions
to generate C2 AuthorizationPackages and FrontierRiskProfiles.

Governance Laws:
- Fail-Closed Risk Assessment: Candidates touching protected core namespaces require explicit operator authorization.
- Immutable Risk Profiles: Risk evaluations are deterministic SHA-256 fingerprinted records.
- Zero Obscurity: Every candidate dependency edge and target path is explicitly declared and audited.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import subprocess
from typing import Any, Dict, List, Optional, Tuple

PROTECTED_NAMESPACES = (
    "sage/core/",
    "sage/runtime/",
    "sage/acr/",
    "sage/agents/",
    "docs/governance/",
    ".github/workflows/",
)


@dataclass(frozen=True)
class FrontierRiskProfile:
    candidate_id: str
    risk_score: float
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    protected_path_touches: Tuple[str, ...]
    dependency_edges: Tuple[str, ...]
    requires_operator_override: bool
    fingerprint: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AuthorizationPackage:
    candidate_id: str
    risk_profile: FrontierRiskProfile
    authorization_ready: bool
    c2_authorization_status: str  # PENDING, AUTHORIZED, BLOCKED
    authorized_by: str
    authorization_token: str
    package_hash: str

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


def compute_risk_fingerprint(
    candidate_id: str, risk_score: float, touches: Tuple[str, ...], edges: Tuple[str, ...]
) -> str:
    payload = f"{candidate_id}:{risk_score:.4f}:{','.join(sorted(touches))}:{','.join(sorted(edges))}".encode(
        "utf-8"
    )
    return hashlib.sha256(payload).hexdigest()


def compute_package_hash(candidate_id: str, status: str, token: str, commit_sha: str) -> str:
    payload = f"{candidate_id}:{status}:{token}:{commit_sha}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class FrontierDependencyRouter:
    """Analyzes candidate dependencies, evaluates risk profiles, and builds C2 authorization packages."""

    def __init__(self, commit_sha: Optional[str] = None) -> None:
        self.commit_sha = commit_sha or _get_current_commit_sha()

    def evaluate_risk(
        self,
        candidate_id: str,
        target_paths: Tuple[str, ...],
        dependency_edges: Tuple[str, ...] = (),
        base_consequentiality: float = 0.5,
    ) -> FrontierRiskProfile:
        """Analyze target paths and dependencies to produce a deterministic FrontierRiskProfile."""
        if not candidate_id:
            raise ValueError("candidate_id is required for risk evaluation")

        touches: List[str] = []
        for path in target_paths:
            for protected in PROTECTED_NAMESPACES:
                if path.startswith(protected) or protected in path:
                    touches.append(path)
                    break

        touch_tuple = tuple(sorted(set(touches)))
        edge_tuple = tuple(sorted(set(dependency_edges)))

        # Risk Score Calculation:
        # Base risk from consequentiality (0.0 - 0.3)
        # Touch risk: +0.3 per protected path touched (max 0.6)
        # Edge count risk: +0.05 per dependency edge (max 0.1)
        touch_penalty = min(0.6, len(touch_tuple) * 0.3)
        edge_penalty = min(0.1, len(edge_tuple) * 0.05)
        raw_score = (base_consequentiality * 0.3) + touch_penalty + edge_penalty
        risk_score = round(min(1.0, max(0.0, raw_score)), 4)

        if risk_score >= 0.8:
            risk_level = "CRITICAL"
        elif risk_score >= 0.5:
            risk_level = "HIGH"
        elif risk_score >= 0.25:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        requires_override = risk_level in ("HIGH", "CRITICAL") or len(touch_tuple) > 0
        fingerprint = compute_risk_fingerprint(candidate_id, risk_score, touch_tuple, edge_tuple)

        return FrontierRiskProfile(
            candidate_id=candidate_id,
            risk_score=risk_score,
            risk_level=risk_level,
            protected_path_touches=touch_tuple,
            dependency_edges=edge_tuple,
            requires_operator_override=requires_override,
            fingerprint=fingerprint,
        )

    def prepare_authorization_package(
        self,
        risk_profile: FrontierRiskProfile,
        authorized_by: Optional[str] = None,
        authorization_token: Optional[str] = None,
    ) -> AuthorizationPackage:
        """Package risk profile with authorization decision."""
        if risk_profile.requires_operator_override and not authorization_token:
            ready = False
            status = "BLOCKED"
            token = "UNAUTHORIZED_HIGH_RISK"
            authorizer = "PENDING_OPERATOR_REVIEW"
        elif authorization_token:
            ready = True
            status = "AUTHORIZED"
            token = authorization_token
            authorizer = authorized_by or "c2_governance_authorizer"
        else:
            ready = True
            status = "AUTHORIZED"
            token = f"auto_token_low_risk_{risk_profile.candidate_id}"
            authorizer = "c2_automated_policy"

        pkg_hash = compute_package_hash(risk_profile.candidate_id, status, token, self.commit_sha)

        return AuthorizationPackage(
            candidate_id=risk_profile.candidate_id,
            risk_profile=risk_profile,
            authorization_ready=ready,
            c2_authorization_status=status,
            authorized_by=authorizer,
            authorization_token=token,
            package_hash=pkg_hash,
        )
