"""Canonical ChatGPT C2 exact-order and anti-drift contract.

This module is deliberately provider-agnostic. It defines the contract that
SAGE-owned ChatGPT adapters must inject and validate at the runtime boundary.
It does not grant the model authority and cannot control an external ChatGPT
session that is not routed through the SAGE integration boundary.
"""
from __future__ import annotations

from dataclasses import dataclass

from sage.c2.live_operation_receipt import LiveOperationReceipt

CONTRACT_ID = "CHATGPT_C2_EXACT_ORDER_ANTI_DRIFT"
CONTRACT_VERSION = "1.3"
RECON_POLICY_PATH = "docs/governance/SAGE_DEEP_RECON_VELOCITY_POLICY.md"

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
    "Five flights is concurrent mission ownership across independent vehicles, not a post-hoc reporting table slapped onto sequential work.",
    "Execute the full canonical cycle: PREFLIGHT -> EXECUTE -> TEST -> EVIDENCE -> VERIFY -> RECONCILE -> REPORT.",
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

DEEP_RECON_TRIGGERS: tuple[str, ...] = (
    "search",
    "super search",
    "deep search",
    "research",
    "audit",
    "recon",
)


@dataclass(frozen=True)
class C2DirectiveDecision:
    """Deterministic classification of whether a directive requires live verification or recon."""

    requires_live_verification: bool
    matched_triggers: tuple[str, ...]
    requires_deep_recon: bool = False
    matched_recon_triggers: tuple[str, ...] = ()


def classify_directive(text: str) -> C2DirectiveDecision:
    """Detect live-verification and reconnaissance directives without rewriting them."""
    normalized = " ".join(text.lower().split())
    matches = tuple(trigger for trigger in LIVE_CHECK_TRIGGERS if trigger in normalized)
    recon_matches = tuple(trigger for trigger in DEEP_RECON_TRIGGERS if trigger in normalized)
    return C2DirectiveDecision(
        bool(matches),
        matches,
        bool(recon_matches),
        recon_matches,
    )


def render_system_contract() -> str:
    """Render the exact contract for injection into a governed model request."""
    laws = "\n".join(f"{index}. {law}" for index, law in enumerate(ANTI_DRIFT_LAWS, 1))
    return (
        f"SAGE C2 CONTRACT: {CONTRACT_ID} v{CONTRACT_VERSION}\n"
        "Apply these laws to every turn:\n"
        f"{laws}\n"
        f"DEEP RECON POLICY: {RECON_POLICY_PATH}\n"
        "RECON ORDER: REPOSITORY-FIRST REALITY LOCK -> TARGETED PRIMARY EXTERNAL INTELLIGENCE -> SYNTHESIZE -> BOUNDED CONCURRENT EXECUTION -> EXACT-STATE VERIFICATION.\n"
        "VELOCITY RULE: independent repository inspection and relevant external research may run concurrently after the initial reality lock; do not serialize unrelated research or use research as an unnecessary approval gate.\n"
        "AUTHORITY: user directive remains the requested task; model output is not authorization.\n"
        "LIVE-VERIFICATION ORDER: PRESERVE EXACTLY -> IDENTIFY REQUIRED LIVE CAPABILITY -> INVOKE CONNECTED CAPABILITY -> VERIFY -> EXECUTE REQUESTED OPERATION -> REPORT ONLY SUPPORTED FACTS.\n"
        "CANONICAL EXECUTION LOOP: PREFLIGHT -> EXECUTE -> TEST -> EVIDENCE -> VERIFY -> RECONCILE -> REPORT.\n"
        "Do not replace the requested operation with an explanation about the operation."
    )


def validate_report_claims(
    *,
    receipt: LiveOperationReceipt | None,
    claim: str,
    expected_target_resource: str | None = None,
    evidence_refs: tuple[str, ...] = (),
) -> None:
    """Fail closed unless a live claim has an authentic operation receipt."""
    live_claim = any(
        phrase in claim.lower()
        for phrase in (
            "verified live",
            "checked live",
            "inspected live",
            "ran live",
            "live repository",
            "live github",
        )
    )
    if not live_claim:
        return
    if not isinstance(receipt, LiveOperationReceipt):
        raise ValueError("C2 anti-drift contract violation: live claim lacks a LiveOperationReceipt.")
    if not receipt.verify() or not receipt.success:
        raise ValueError("C2 anti-drift contract violation: live claim has invalid or failed receipt.")
    if receipt.receipt_hash not in evidence_refs:
        raise ValueError("C2 anti-drift contract violation: live claim receipt is not bound to response evidence.")
    if expected_target_resource and receipt.target_resource != expected_target_resource:
        raise ValueError(
            "C2 anti-drift contract violation: live claim receipt target does not match requested resource."
        )
