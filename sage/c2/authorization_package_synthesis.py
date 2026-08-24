"""Authorization Package Synthesizer for SAGE C2 Adaptive Frontier Selection.

Synthesizes immutable C2 AuthorizationPackages mapping dependency graphs, protected namespace touches,
risk surfaces, and verification obligations prior to C2 authorization gate evaluation.

Governance Laws:
- Default Fail-Closed: AuthorizationPackage is_authorized defaults to False until explicit C2 token is attached.
- Protected Path Isolation: Candidates touching protected namespaces (sage/core/, sage/runtime/) default to UNAUTHORIZED_RISK_SURFACE.
- Cryptographic Package Hashes: Package integrity is locked via SHA-256 fingerprints.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import subprocess
from typing import Any, Dict, List, Optional, Tuple

PROTECTED_CORE_NAMESPACES = (
    "sage/core/",
    "sage/runtime/",
    "sage/acr/",
    "sage/agents/",
    "docs/governance/",
    ".github/workflows/",
)


@dataclass(frozen=True)
class SynthesizedRiskSurface:
    candidate_id: str
    risk_score: float
    protected_paths: Tuple[str, ...]
    verification_plan_present: bool
    evidence_requirements: Tuple[str, ...]
    risk_verdict: str  # SAFE, EVALUATION_REQUIRED, BLOCKED

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AuthorizationPackage:
    package_id: str
    candidate_id: str
    risk_surface: SynthesizedRiskSurface
    is_authorized: bool
    authorization_status: str
    authorization_token: Optional[str]
    package_hash: str
    commit_sha: str

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


def compute_package_hash(
    candidate_id: str,
    risk_score: float,
    is_authorized: bool,
    token: str,
    commit_sha: str,
) -> str:
    payload = f"{candidate_id}:{risk_score:.4f}:{is_authorized}:{token}:{commit_sha}".encode(
        "utf-8"
    )
    return hashlib.sha256(payload).hexdigest()


class AuthorizationPackageSynthesizer:
    """Synthesizes candidate risk surfaces and authorization packages for C2 decision gate evaluation."""

    def __init__(self, commit_sha: Optional[str] = None) -> None:
        self.commit_sha = commit_sha or _get_current_commit_sha()

    def evaluate_risk_surface(
        self,
        candidate_id: str,
        target_paths: Tuple[str, ...],
        evidence_requirements: Tuple[str, ...] = (),
        verification_plan_present: bool = True,
    ) -> SynthesizedRiskSurface:
        """Evaluate target file paths and verification plan to compute risk surface."""
        if not candidate_id:
            raise ValueError("candidate_id is required for risk surface synthesis")

        touches: List[str] = []
        for path in target_paths:
            for protected in PROTECTED_CORE_NAMESPACES:
                if path.startswith(protected) or protected in path:
                    touches.append(path)
                    break

        touch_tuple = tuple(sorted(set(touches)))
        evidence_tuple = tuple(sorted(set(evidence_requirements)))

        # Risk scoring logic:
        # Base risk: 0.1
        # Touch risk: +0.4 per protected path
        # Missing verification plan penalty: +0.3
        raw_risk = 0.1 + (len(touch_tuple) * 0.4) + (0.3 if not verification_plan_present else 0.0)
        risk_score = round(min(1.0, max(0.0, raw_risk)), 4)

        if len(touch_tuple) > 0:
            risk_verdict = "BLOCKED"
        elif not verification_plan_present or risk_score >= 0.4:
            risk_verdict = "EVALUATION_REQUIRED"
        else:
            risk_verdict = "SAFE"

        return SynthesizedRiskSurface(
            candidate_id=candidate_id,
            risk_score=risk_score,
            protected_paths=touch_tuple,
            verification_plan_present=verification_plan_present,
            evidence_requirements=evidence_tuple,
            risk_verdict=risk_verdict,
        )

    def synthesize_package(
        self,
        candidate_id: str,
        target_paths: Tuple[str, ...],
        evidence_requirements: Tuple[str, ...] = (),
        verification_plan_present: bool = True,
        authorization_token: Optional[str] = None,
    ) -> AuthorizationPackage:
        """Synthesize AuthorizationPackage with default fail-closed is_authorized=False."""
        risk_surface = self.evaluate_risk_surface(
            candidate_id=candidate_id,
            target_paths=target_paths,
            evidence_requirements=evidence_requirements,
            verification_plan_present=verification_plan_present,
        )

        # Fail-closed authorization gate evaluation
        if risk_surface.risk_verdict == "BLOCKED" and not authorization_token:
            is_authorized = False
            status = "BLOCKED_PROTECTED_PATH_TOUCH"
            token_used = "NONE"
        elif not verification_plan_present:
            is_authorized = False
            status = "BLOCKED_MISSING_VERIFICATION_PLAN"
            token_used = "NONE"
        elif authorization_token:
            is_authorized = True
            status = "AUTHORIZED_BY_C2"
            token_used = authorization_token
        else:
            # Unapproved default
            is_authorized = False
            status = "UNAPPROVED_DEFAULT"
            token_used = "NONE"

        package_hash = compute_package_hash(
            candidate_id=candidate_id,
            risk_score=risk_surface.risk_score,
            is_authorized=is_authorized,
            token=token_used,
            commit_sha=self.commit_sha,
        )

        package_id = f"auth_pkg_{hashlib.sha256(package_hash.encode()).hexdigest()[:12]}"

        return AuthorizationPackage(
            package_id=package_id,
            candidate_id=candidate_id,
            risk_surface=risk_surface,
            is_authorized=is_authorized,
            authorization_status=status,
            authorization_token=authorization_token,
            package_hash=package_hash,
            commit_sha=self.commit_sha,
        )
