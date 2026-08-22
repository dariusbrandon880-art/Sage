"""Effect observation v0.1 for post-transition causal verification.

This primitive records an independently observed effect of a governed
transition. It never performs the probe, mutates target state, retries work,
or infers success from an execution record. UNKNOWN is first-class when the
external boundary cannot be observed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from typing import ClassVar


class EffectObservationValidationError(ValueError):
    """Raised when an effect observation violates its structural contract."""


class TransitionOutcome(str, Enum):
    """Explicit outcomes for independently observed transition effects."""

    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class EffectObservation:
    """Immutable, deterministic projection of one observed transition effect."""

    execution_id: str
    target_boundary_id: str
    expected_state_hash: str
    observed_state_hash: str | None
    outcome: TransitionOutcome
    observed_at: str
    telemetry_source: str
    authority_granted: bool = field(default=False, init=False)

    VALID_OUTCOMES: ClassVar[frozenset[TransitionOutcome]] = frozenset(
        TransitionOutcome
    )

    def __post_init__(self) -> None:
        for name in (
            "execution_id",
            "target_boundary_id",
            "expected_state_hash",
            "observed_at",
            "telemetry_source",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise EffectObservationValidationError(
                    f"{name} must be a non-empty string."
                )

        if not isinstance(self.outcome, TransitionOutcome):
            raise EffectObservationValidationError(
                "outcome must be a TransitionOutcome."
            )

        if self.observed_state_hash is not None and not isinstance(
            self.observed_state_hash, str
        ):
            raise EffectObservationValidationError(
                "observed_state_hash must be a string or None."
            )
        if self.outcome is TransitionOutcome.UNKNOWN:
            if self.observed_state_hash is not None:
                raise EffectObservationValidationError(
                    "UNKNOWN observations cannot claim an observed state hash."
                )
        elif not self.observed_state_hash or not self.observed_state_hash.strip():
            raise EffectObservationValidationError(
                "non-UNKNOWN observations require an observed state hash."
            )
        if self.outcome is TransitionOutcome.CONFIRMED and (
            self.observed_state_hash != self.expected_state_hash
        ):
            raise EffectObservationValidationError(
                "CONFIRMED requires the observed state hash to match the expected hash."
            )

        try:
            parsed = datetime.fromisoformat(self.observed_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise EffectObservationValidationError(
                "observed_at must be an ISO-8601 timestamp."
            ) from exc
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise EffectObservationValidationError(
                "observed_at must include an explicit timezone."
            )
        if parsed.astimezone(timezone.utc) != parsed:
            raise EffectObservationValidationError(
                "observed_at must be expressed in UTC."
            )

    @property
    def observation_id(self) -> str:
        """Return the deterministic SHA-256 identity of the observation."""
        payload = {
            "execution_id": self.execution_id,
            "expected_state_hash": self.expected_state_hash,
            "observed_at": self.observed_at,
            "observed_state_hash": self.observed_state_hash,
            "outcome": self.outcome.value,
            "target_boundary_id": self.target_boundary_id,
            "telemetry_source": self.telemetry_source,
        }
        canonical = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, str | bool | None]:
        """Return the complete stable public projection."""
        return {
            "observation_id": self.observation_id,
            "execution_id": self.execution_id,
            "target_boundary_id": self.target_boundary_id,
            "expected_state_hash": self.expected_state_hash,
            "observed_state_hash": self.observed_state_hash,
            "outcome": self.outcome.value,
            "observed_at": self.observed_at,
            "telemetry_source": self.telemetry_source,
            "authority_granted": self.authority_granted,
        }

    @classmethod
    def observe(
        cls,
        *,
        execution_id: str,
        target_boundary_id: str,
        expected_state_hash: str,
        observed_state_hash: str | None,
        outcome: TransitionOutcome,
        observed_at: str,
        telemetry_source: str,
    ) -> "EffectObservation":
        """Construct one validated observation without performing side effects."""
        return cls(
            execution_id=execution_id,
            target_boundary_id=target_boundary_id,
            expected_state_hash=expected_state_hash,
            observed_state_hash=observed_state_hash,
            outcome=outcome,
            observed_at=observed_at,
            telemetry_source=telemetry_source,
        )
