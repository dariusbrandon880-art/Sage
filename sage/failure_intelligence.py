"""Read-only failure fingerprinting and repair qualification records."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from hashlib import sha256

_WS = re.compile(r"\s+")
_HEX = re.compile(r"\b[0-9a-f]{7,64}\b", re.I)
_NUM = re.compile(r"\b\d+\b")

# Explicit, immutable failure surfaces that the progression preflight may block.
# These are governance hazards already represented by the repository's validation
# suites; they are intentionally descriptive and never select or rewrite missions.
KNOWN_FAILURE_PATTERNS = frozenset(
    {
        "known_failure_trigger",
        "protected namespace violation",
        "unauthorized state mutation",
        "evidence bypass",
        "roleplay execution",
    }
)


def normalize_failure(message: str) -> str:
    """Normalize incidental log noise while preserving the failure shape.

    Known governance failure surfaces receive the compatibility marker consumed by
    the read-only progression preflight boundary. Unknown failures remain ordinary
    normalized strings and are never promoted to known patterns implicitly.
    """
    if not isinstance(message, str) or not message.strip():
        raise ValueError("failure message required")
    compact = _WS.sub(" ", message.strip())
    normalized = _NUM.sub("#", _HEX.sub("<sha>", compact)).lower()
    if normalized in KNOWN_FAILURE_PATTERNS:
        return f"known_failure_trigger:{normalized}"
    return normalized


def failure_fingerprint(command: str, message: str) -> str:
    """Create a deterministic fingerprint for one normalized failure surface."""
    if not isinstance(command, str) or not command.strip():
        raise ValueError("command required")
    payload = {
        "command": command.strip(),
        "message": normalize_failure(message),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


@dataclass(frozen=True)
class FailureObservation:
    """One nonzero-exit observation with execution provenance."""

    fingerprint: str
    command: str
    message: str
    commit_sha: str
    surface: str
    exit_code: int

    def __post_init__(self) -> None:
        if len(self.fingerprint) != 64 or not all(
            char in "0123456789abcdef" for char in self.fingerprint
        ):
            raise ValueError("invalid fingerprint")
        if not self.command.strip() or not self.commit_sha.strip() or not self.surface.strip():
            raise ValueError("required provenance missing")
        if self.exit_code == 0:
            raise ValueError("failure observation cannot have zero exit code")


@dataclass(frozen=True)
class RepairQualification:
    """A repair is qualified only by evidence from a true descendant."""

    fingerprint: str
    repair_sha: str
    descendant_sha: str
    qualified: bool
    evidence_ref: str

    def __post_init__(self) -> None:
        if not self.fingerprint or not self.repair_sha or not self.descendant_sha or not self.evidence_ref:
            raise ValueError("qualification provenance missing")
        if self.qualified and self.repair_sha == self.descendant_sha:
            raise ValueError("qualification requires descendant evidence")


def collapse(
    observations: list[FailureObservation],
) -> dict[str, tuple[FailureObservation, ...]]:
    """Group repeated observations by their deterministic failure fingerprint."""
    grouped: dict[str, list[FailureObservation]] = {}
    for observation in observations:
        grouped.setdefault(observation.fingerprint, []).append(observation)
    return {key: tuple(value) for key, value in sorted(grouped.items())}
