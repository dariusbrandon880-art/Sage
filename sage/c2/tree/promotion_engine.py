"""Fail-closed promotion gate with evidence-bound atomic Git integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import logging
import re
import time
from typing import Any, Dict, List, Protocol

logger = logging.getLogger(__name__)
HEX_SHA_REGEX = re.compile(r"^[0-9a-fA-F]{40}$")
BRANCH_NAME_REGEX = re.compile(r"^[A-Za-z0-9._/-]+$")


class PromotionStatus(Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    PROMOTED = "PROMOTED"
    FAILED = "FAILED"


class TargetDriftError(Exception):
    """Raised when the target ref changed during an atomic CAS attempt."""


class GitProvider(Protocol):
    """Provider contract for atomic, ancestry-safe canonical integration."""

    def integrate_cas(
        self, source_sha: str, expected_target_sha: str, target_branch: str
    ) -> str: ...

    def verify_clean_status(self) -> bool: ...


@dataclass(frozen=True)
class EvidenceReceipt:
    receipt_id: str
    flight_id: str
    stage: str
    commit_sha: str
    passed: bool
    timestamp: float
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PromotionCandidate:
    branch_name: str
    source_sha: str
    target_sha: str
    required_gates: List[str]
    evidence_receipts: List[EvidenceReceipt] = field(default_factory=list)
    status: PromotionStatus = PromotionStatus.PENDING


class PromotionEngine:
    """Fail-closed promotion gate for the canonical SAGE trunk."""

    def __init__(
        self,
        git_provider: GitProvider,
        canonical_branch: str = "main",
        max_receipt_age: float = 86400.0,
        clock_skew_tolerance: float = 300.0,
    ):
        self.git_provider = git_provider
        self.canonical_branch = canonical_branch
        self.max_receipt_age = max_receipt_age
        self.clock_skew_tolerance = clock_skew_tolerance

    @staticmethod
    def _validate_sha(sha: str, name: str) -> str:
        if not isinstance(sha, str) or not HEX_SHA_REGEX.fullmatch(sha):
            raise ValueError(
                f"Invalid 40-character hex commit SHA for {name}: {sha!r}"
            )
        return sha.lower()

    def _validate_branch(self, branch_name: str) -> None:
        if (
            not isinstance(branch_name, str)
            or not branch_name
            or branch_name.startswith("/")
            or branch_name.endswith("/")
            or branch_name.startswith("-")
            or ".." in branch_name
            or "@{" in branch_name
            or not BRANCH_NAME_REGEX.fullmatch(branch_name)
        ):
            raise ValueError(f"Invalid branch name format: {branch_name!r}")
        if branch_name == self.canonical_branch:
            raise ValueError(
                f"Candidate branch cannot be canonical branch {self.canonical_branch!r}"
            )

    def verify_candidate(
        self, candidate: PromotionCandidate
    ) -> Dict[str, EvidenceReceipt]:
        """Return the unique required-gate -> receipt mapping or reject closed."""
        try:
            source_sha = self._validate_sha(candidate.source_sha, "source_sha")
            self._validate_sha(candidate.target_sha, "target_sha")
            self._validate_branch(candidate.branch_name)
        except ValueError as exc:
            candidate.status = PromotionStatus.REJECTED
            logger.error("Promotion rejected during input validation: %s", exc)
            return {}

        candidate.source_sha = source_sha

        if source_sha == candidate.target_sha.lower():
            candidate.status = PromotionStatus.REJECTED
            logger.error("Promotion rejected: source_sha equals target_sha (no-op or self-promotion).")
            return {}

        if not candidate.required_gates or len(set(candidate.required_gates)) != len(
            candidate.required_gates
        ):
            candidate.status = PromotionStatus.REJECTED
            logger.error(
                "Promotion rejected: required_gates must be non-empty and unique."
            )
            return {}

        gate_receipt_map: Dict[str, EvidenceReceipt] = {}
        seen_stages: set[str] = set()

        for receipt in candidate.evidence_receipts:
            if (
                not receipt.receipt_id
                or not receipt.flight_id
                or not receipt.stage
                or not isinstance(receipt.timestamp, (int, float))
            ):
                candidate.status = PromotionStatus.REJECTED
                logger.error("Promotion rejected: malformed evidence receipt.")
                return {}

            now = time.time()
            if (
                receipt.timestamp < (now - self.max_receipt_age)
                or receipt.timestamp > (now + self.clock_skew_tolerance)
            ):
                candidate.status = PromotionStatus.REJECTED
                logger.error("Promotion rejected: receipt %s timestamp expired or future-skewed.", receipt.receipt_id)
                return {}

            try:
                receipt_sha = self._validate_sha(
                    receipt.commit_sha, f"receipt {receipt.receipt_id} commit_sha"
                )
            except ValueError as exc:
                candidate.status = PromotionStatus.REJECTED
                logger.error("Promotion rejected: %s", exc)
                return {}

            if receipt.stage in seen_stages:
                candidate.status = PromotionStatus.REJECTED
                logger.error(
                    "Promotion rejected: duplicate evidence stage %r.", receipt.stage
                )
                return {}
            seen_stages.add(receipt.stage)

            if receipt_sha != candidate.source_sha:
                logger.warning(
                    "Ignoring unbound receipt %s: %s != %s",
                    receipt.receipt_id,
                    receipt.commit_sha,
                    candidate.source_sha,
                )
                continue
            if receipt.passed:
                gate_receipt_map[receipt.stage] = receipt

        for gate in candidate.required_gates:
            if gate not in gate_receipt_map:
                candidate.status = PromotionStatus.REJECTED
                logger.warning("Required promotion gate unsatisfied: %s", gate)
                return {}

        candidate.status = PromotionStatus.VERIFIED
        return {gate: gate_receipt_map[gate] for gate in candidate.required_gates}

    def execute_promotion(self, candidate: PromotionCandidate) -> Dict[str, Any]:
        """Verify evidence, perform atomic CAS integration, verify, then record lineage."""
        gate_map = self.verify_candidate(candidate)
        if candidate.status != PromotionStatus.VERIFIED:
            raise PermissionError(
                f"Zero-bypass gate violation: candidate {candidate.branch_name!r} "
                "failed evidence verification."
            )

        try:
            new_head_sha = self.git_provider.integrate_cas(
                source_sha=candidate.source_sha,
                expected_target_sha=candidate.target_sha,
                target_branch=self.canonical_branch,
            )
        except TargetDriftError:
            candidate.status = PromotionStatus.REJECTED
            raise
        except Exception as exc:
            candidate.status = PromotionStatus.FAILED
            raise RuntimeError(f"Git integration execution failed: {exc}") from exc

        if not self.git_provider.verify_clean_status():
            candidate.status = PromotionStatus.FAILED
            raise RuntimeError(
                "Post-integration verification failed: workspace is dirty."
            )

        candidate.status = PromotionStatus.PROMOTED
        return {
            "branch_name": candidate.branch_name,
            "promoted_at": time.time(),
            "canonical_branch": self.canonical_branch,
            "source_sha": candidate.source_sha,
            "previous_main_sha": candidate.target_sha.lower(),
            "new_main_sha": self._validate_sha(new_head_sha, "new_main_sha"),
            "verified_gates": {
                gate: {
                    "receipt_id": receipt.receipt_id,
                    "flight_id": receipt.flight_id,
                    "commit_sha": receipt.commit_sha.lower(),
                    "timestamp": receipt.timestamp,
                }
                for gate, receipt in gate_map.items()
            },
        }
