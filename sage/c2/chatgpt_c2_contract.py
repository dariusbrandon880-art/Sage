"""Canonical ChatGPT C2 exact-order, anti-drift, and marathon-execution contract."""
from __future__ import annotations

from dataclasses import dataclass
from sage.c2.live_operation_receipt import LiveOperationReceipt

CONTRACT_ID = "CHATGPT_C2_EXACT_ORDER_ANTI_DRIFT"
CONTRACT_VERSION = "1.4"
RECON_POLICY_PATH = "docs/governance/SAGE_DEEP_RECON_VELOCITY_POLICY.md"
LOCKED_EXECUTION_UPDATE_PATH = "docs/governance/CHATGPT_C2_LOCKED_EXECUTION_UPDATE_2026-08-29.md"
TECHNIQUE_LEARNING_PATH = "sage/core/technique_learning.py"

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
    "SAGE is one governed organism with modular organs. All subsystems map into the Jigsaw taxonomy (CORE, SERVICE, PROJECTION, EVIDENCE_LEARNING). No subsystem may maintain duplicate C2, state, or workflow authority.",
)

# Keep the live boundary explicit. A bare word such as "verify" in an ordinary
# task is not sufficient to force a live capability; live intent must be explicit.
LIVE_CHECK_TRIGGERS: tuple[str, ...] = ("check live repo", "check github", "check live connection", "verify live", "verify connection", "inspect pr", "inspect pull request", "check current branch", "run it", "run yourself")
DEEP_RECON_TRIGGERS: tuple[str, ...] = ("search", "super search", "deep search", "research", "audit", "recon", "full repo", "whole repo", "full sweep")
MARATHON_TRIGGERS: tuple[str, ...] = ("go", "fly", "advance", "run it", "keep going", "finish", "handle all", "full marathon", "compound")
REHYDRATION_TRIGGERS: tuple[str, ...] = (
    "lock onto repo", "lock onto the repo", "lock onto sage", "lock onto the sage repo",
    "whole repo truth", "whole repo", "repo truth", "rehydrate", "re-hydrate", "c2 rehydration",
)
REHYDRATION_SEQUENCE: tuple[str, ...] = (
    "REHYDRATE", "REALITY LOCK", "MISSION LOCK", "IDENTITY LOCK", "ACTIVE-FRONTIER LOCK",
)

@dataclass(frozen=True)
class C2DirectiveDecision:
    requires_live_verification: bool
    matched_triggers: tuple[str, ...]
    requires_deep_recon: bool = False
    matched_recon_triggers: tuple[str, ...] = ()
    requires_marathon_execution: bool = False
    matched_marathon_triggers: tuple[str, ...] = ()
    requires_rehydration: bool = False
    matched_rehydration_triggers: tuple[str, ...] = ()


def classify_directive(text: str) -> C2DirectiveDecision:
    normalized = " ".join(text.lower().split())
    matches = tuple(t for t in LIVE_CHECK_TRIGGERS if t in normalized)
    recon_matches = tuple(t for t in DEEP_RECON_TRIGGERS if t in normalized)
    marathon_matches = tuple(t for t in MARATHON_TRIGGERS if t in normalized)
    rehydration_matches = tuple(t for t in REHYDRATION_TRIGGERS if t in normalized)
    return C2DirectiveDecision(
        bool(matches), matches, bool(recon_matches), recon_matches,
        bool(marathon_matches), marathon_matches, bool(rehydration_matches), rehydration_matches,
    )


def render_system_contract() -> str:
    laws = "\n".join(f"{i}. {law}" for i, law in enumerate(ANTI_DRIFT_LAWS, 1))
    sequence = " -> ".join(REHYDRATION_SEQUENCE)
    return (
        f"SAGE C2 CONTRACT: {CONTRACT_ID} v{CONTRACT_VERSION}\n"
        "Apply these laws to every turn:\n" f"{laws}\n"
        f"DEEP RECON POLICY: {RECON_POLICY_PATH}\n"
        f"LOCKED EXECUTION UPDATE: {LOCKED_EXECUTION_UPDATE_PATH}\n"
        f"TECHNIQUE LEARNING BOUNDARY: {TECHNIQUE_LEARNING_PATH}\n"
        f"REHYDRATION TRIGGERS: {', '.join(REHYDRATION_TRIGGERS)}\n"
        f"MANDATORY REHYDRATION SEQUENCE: {sequence}\n"
        "A repo/SAGE truth-lock directive MUST execute the mandatory rehydration sequence before ordinary task execution; merely looking up a file does not satisfy rehydration.\n"
        "RECON ORDER: REPOSITORY-FIRST REALITY LOCK -> TARGETED PRIMARY EXTERNAL INTELLIGENCE -> SYNTHESIZE -> BOUNDED CONCURRENT EXECUTION -> EXACT-STATE VERIFICATION.\n"
        "VELOCITY RULE: independent repository inspection and relevant external research may run concurrently after the initial reality lock; do not serialize unrelated research or use research as an unnecessary approval gate.\n"
        "MARATHON RULE: when the user authorizes continuation, execute the largest coherent consequential frontier available within scope; do not return a planning-loop response while causally connected executable work remains.\n"
        "MARINE RULE: for deep consequential boundaries, inspect the full causally connected system surface, not merely the visible defect.\n"
        "COMPOUND RULE: advance independent executable branches in the same governed campaign and feed validated reusable results into the next causally relevant stage.\n"
        "PRESERVATION RULE: locate and reuse validated SAGE substrate before creating new authority, state, workflow, prediction, persistence, or evidence primitives.\n"
        "DELEGATION RULE: Jules and other stations are execution multipliers; delegation never transfers C2 mission framing, independent verification, evidence judgment, reconciliation, or closure ownership.\n"
        "TECHNIQUE-LEARNING RULE: experience may produce a TechniqueCandidate, but behavior is not changed by the candidate. A technique becomes reviewable only after replicated, independently evidenced comparison against an explicit baseline metric; counterexamples force HOLD.\n"
        "TECHNIQUE-PROMOTION RULE: TechniqueValidation is a non-authoritative review posture. It cannot mutate the model, grant authority, promote capability, persist state, or bypass existing evidence/promotion gates.\n"
        "ACCEPTANCE LADDER: IMPLEMENTATION -> TEST -> RUNTIME OBSERVATION -> EMPIRICAL VALIDATION -> PROMOTION.\n"
        "FINAL RECONCILIATION: working state -> branch HEAD -> PR HEAD -> target main -> CI/workflows -> evidence receipts -> mission/issue state.\n"
        "AUTHORITY: user directive remains the requested task; model output is not authorization.\n"
        "LIVE-VERIFICATION ORDER: PRESERVE EXACTLY -> IDENTIFY REQUIRED LIVE CAPABILITY -> INVOKE CONNECTED CAPABILITY -> VERIFY -> EXECUTE REQUESTED OPERATION -> REPORT ONLY SUPPORTED FACTS.\n"
        "CANONICAL EXECUTION LOOP: PREFLIGHT -> EXECUTE -> TEST -> EVIDENCE -> VERIFY -> RECONCILE -> REPORT.\n"
        "Do not replace the requested operation with an explanation about the operation."
    )


def validate_report_claims(*, receipt: LiveOperationReceipt | None, claim: str, expected_target_resource: str | None = None, evidence_refs: tuple[str, ...] = ()) -> None:
    live_claim = any(p in claim.lower() for p in ("verified live", "checked live", "inspected live", "ran live", "live repository", "live github"))
    if not live_claim:
        return
    if not isinstance(receipt, LiveOperationReceipt):
        raise ValueError("C2 anti-drift contract violation: live claim lacks a LiveOperationReceipt.")
    if not receipt.verify() or not receipt.success:
        raise ValueError("C2 anti-drift contract violation: live claim has invalid or failed receipt.")
    if receipt.receipt_hash not in evidence_refs:
        raise ValueError("C2 anti-drift contract violation: live claim receipt is not bound to response evidence.")
    if expected_target_resource and receipt.target_resource != expected_target_resource:
        raise ValueError("C2 anti-drift contract violation: live claim receipt target does not match requested resource.")


def validate_directive_compliance(directive_text: str) -> C2DirectiveDecision:
    """Classify C2 directive text and verify contract law alignment."""
    if not directive_text or not directive_text.strip():
        raise ValueError("C2 directive text cannot be empty.")
    return classify_directive(directive_text)
