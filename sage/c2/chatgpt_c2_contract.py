"""Canonical ChatGPT C2 exact-order and anti-drift contract.

This module is deliberately provider-agnostic. It defines the contract that
SAGE-owned ChatGPT adapters must inject and validate at the runtime boundary.
It does not grant the model authority and cannot control an external ChatGPT
session that is not routed through the SAGE integration boundary.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Iterable

CONTRACT_ID = "CHATGPT_C2_EXACT_ORDER_ANTI_DRIFT"
CONTRACT_VERSION = "1.0"

ANTI_DRIFT_LAWS: tuple[str, ...] = (
    "Preserve the user's directive exactly: do not change its meaning or requested order.",
    "Do not add requirements, capabilities, assumptions, constraints, lanes, tools, or conclusions not requested by the user.",
    "Do not assume an available connection is unavailable; attempt the applicable connected capability before reporting it unavailable.",
    "For live-check commands, invoke the applicable live capability before relying on pasted reports or chat history.",
    "Treat pasted reports as claims or intelligence; treat live tool results as verification.",
    "Do not substitute a different task, sequence, or scope for the user's requested operation.",
    "Never claim a live check, execution, test, merge, connection, or repository inspection occurred unless it actually occurred.",
    "When live evidence contradicts a report, preserve and report the contradiction instead of normalizing it away.",
    "Keep model reasoning, repository truth, authorization, and canonical state as separate authorities.",
    "Fail closed when required verification cannot be performed; never fabricate missing evidence.",
)

LIVE_CHECK_TRIGGERS: tuple[str, ...] = (
    "check live repo",
    "check github",
    "check live connection",
    "verify connection",
    "inspect pr",
    "inspect pull request",
    "check current branch",
    "run it",
    "run yourself",
    "verify",
)

@dataclass(frozen=True)
class C2DirectiveDecision:
    """Deterministic classification of whether a directive requires live verification."""

    requires_live_verification: bool
    matched_triggers: tuple[str, ...]


def classify_directive(text: str) -> C2DirectiveDecision:
    """Detect explicit live-verification directives without rewriting the directive."""
    normalized = " ".join(text.lower().split())
    matches = tuple(trigger for trigger in LIVE_CHECK_TRIGGERS if trigger in normalized)
    return C2DirectiveDecision(bool(matches), matches)


def render_system_contract() -> str:
    """Render the exact contract for injection into a governed model request."""
    laws = "\n".join(f"{index}. {law}" for index, law in enumerate(ANTI_DRIFT_LAWS, 1))
    return (
        f"SAGE C2 CONTRACT: {CONTRACT_ID} v{CONTRACT_VERSION}\n"
        "Apply these laws to every turn:\n"
        f"{laws}\n"
        "AUTHORITY: user directive remains the requested task; model output is not authorization.\n"
        "LIVE-VERIFICATION ORDER: preserve directive -> identify required live capability -> invoke it -> verify -> execute requested operation -> report supported facts.\n"
        "Do not replace the requested operation with an explanation about the operation."
    )


@dataclass(frozen=True)
class LiveOperationReceipt:
    """Receipt proving a live operation was actually executed against repository/API truth."""
    operation_type: str
    target: str
    success: bool
    timestamp: float
    receipt_hash: str

    def verify_hash(self) -> bool:
        """Verify that receipt_hash cryptographically matches the receipt payload parameters."""
        expected = hashlib.sha256(
            f"{self.operation_type}:{self.target}:{self.success}:{self.timestamp}".encode()
        ).hexdigest()
        return self.receipt_hash == expected


def validate_report_claims(
    *,
    claim: str,
    operation_receipt: LiveOperationReceipt | None = None,
    expected_operation_type: str | None = None,
    expected_target: str | None = None
) -> None:
    """Fail closed if a report claims live verification without an authoritative, hash-verified receipt.

    COMPLETELY ELIMINATES BOOLEAN TRUST (live_operation_performed: bool parameter removed).
    """
    claims_live = any(
        phrase in claim.lower()
        for phrase in ("verified live", "checked live", "inspected live", "ran live", "merged")
    )

    if claims_live:
        if operation_receipt is None:
            raise ValueError(
                "C2 anti-drift contract violation: live verification claim lacks an authoritative LiveOperationReceipt."
            )
        if not operation_receipt.success:
            raise ValueError(
                "C2 anti-drift contract violation: operation receipt indicates operation failure."
            )
        if not operation_receipt.verify_hash():
            raise ValueError(
                "C2 anti-drift contract violation: operation receipt cryptographic hash mismatch or tampered."
            )
        if expected_operation_type and operation_receipt.operation_type != expected_operation_type:
            raise ValueError(
                f"C2 anti-drift contract violation: receipt operation_type '{operation_receipt.operation_type}' "
                f"does not match expected '{expected_operation_type}'."
            )
        if expected_target and operation_receipt.target != expected_target:
            raise ValueError(
                f"C2 anti-drift contract violation: receipt target '{operation_receipt.target}' "
                f"does not match expected '{expected_target}'."
            )
