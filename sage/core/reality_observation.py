"""Reality Observation v0.1 — immutable T1 observation boundary for SAGE.

This module models a late-arriving observation without asserting that the
observation is true, authoritative, or execution-enabling. It is intentionally
storage-free and signing-free so higher layers can bind the observation into
reconciliation or attestation flows without coupling this primitive to them.
"""

from dataclasses import dataclass, field
import hashlib
import json
from typing import ClassVar


class RealityObservationValidationError(ValueError):
    """Raised when a reality observation violates its structural contract."""


@dataclass(frozen=True)
class RealityObservation:
    """Immutable description of a T1 observed state or consequence.

    The object records *what observation was referenced, where/when it was
    observed, and how the observer is classified*. It does not decide whether
    the observation is correct and never grants authority.
    """

    observation_id: str
    context_id: str
    source_id: str
    source_version: str
    observed_at: str
    observation_ref: str
    observation_kind: str
    observer_class: str = "UNKNOWN"
    authority_granted: bool = field(default=False, init=False)

    VALID_OBSERVER_CLASSES: ClassVar[frozenset[str]] = frozenset(
        {"SELF", "INTERNAL", "EXTERNAL", "UNKNOWN"}
    )

    def __post_init__(self) -> None:
        fields = {
            "observation_id": self.observation_id,
            "context_id": self.context_id,
            "source_id": self.source_id,
            "source_version": self.source_version,
            "observed_at": self.observed_at,
            "observation_ref": self.observation_ref,
            "observation_kind": self.observation_kind,
        }
        for name, value in fields.items():
            if not isinstance(value, str) or not value.strip():
                raise RealityObservationValidationError(
                    f"{name} must be a non-empty string."
                )

        if self.observer_class not in self.VALID_OBSERVER_CLASSES:
            raise RealityObservationValidationError(
                f"Invalid observer_class: {self.observer_class}. "
                f"Must be one of {sorted(self.VALID_OBSERVER_CLASSES)}"
            )

    @property
    def observation_digest(self) -> str:
        """Return the deterministic SHA-256 identity of the T1 observation envelope."""
        payload = {
            "context_id": self.context_id,
            "observation_id": self.observation_id,
            "observation_kind": self.observation_kind,
            "observation_ref": self.observation_ref,
            "observed_at": self.observed_at,
            "observer_class": self.observer_class,
            "source_id": self.source_id,
            "source_version": self.source_version,
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, object]:
        """Return a stable public projection without hidden state."""
        return {
            "observation_id": self.observation_id,
            "context_id": self.context_id,
            "source_id": self.source_id,
            "source_version": self.source_version,
            "observed_at": self.observed_at,
            "observation_ref": self.observation_ref,
            "observation_kind": self.observation_kind,
            "observer_class": self.observer_class,
            "observation_digest": self.observation_digest,
            "authority_granted": self.authority_granted,
        }
