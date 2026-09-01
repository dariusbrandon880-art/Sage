# SAGE WORLD-CLASS ENGINE PRINCIPLE DOCTRINE

**Status:** Governance doctrine
**Scope:** SAGE architecture, engineering, capability development, verification, and long-term system evolution
**Operating frame:** 60% HARDEN / 40% ADVANCE

## Purpose

SAGE should be developed as a long-lived intelligence engine, not as a stream of feature releases. The World-Class Engine Principle adapts the strongest useful lesson from Rockstar/Take-Two's operating philosophy: concentrate talent and engineering effort on a limited number of high-value capabilities, protect quality, and compound the value of the underlying system over time.

Take-Two publicly describes Rockstar's strategy as developing a limited number of titles known for quality and longevity, while its broader operating pillars emphasize creativity, innovation, and efficiency. SAGE adopts the engineering lesson, not the entertainment business model. External industry observations remain research input rather than canonical SAGE truth.

## The Eight Principles

### 1. Build fewer, deeper capabilities

Optimize for verified capability gained per promotion, not PR count or activity volume.

A capability is not complete because code exists. It is complete when the declared acceptance boundary has implementation, adversarial verification, evidence, and reusable value.

The 60/40 frame means:

- 60% effort protects and strengthens the substrate.
- 40% effort advances new capability.
- Advancement never bypasses an unresolved integrity boundary that materially affects the mission.

### 2. Polish means system integrity

SAGE's equivalent of polish is reliability under attack.

Before promotion, deliberately test the capability against realistic failure modes including stale authority, replay, corruption, interruption, SHA mismatch, provenance loss, false success, and invalid recovery.

If the system cannot prove its boundary, it defaults to `HOLD` rather than manufacturing confidence.

### 3. Build a connected world-state architecture

SAGE is one governed organism, not a collection of impressive modules.

The canonical capability path is:

**SAGI → C2 → Mission → Flight → Execution → Evidence → Verification → Master State**

Each boundary must preserve identity, authorization, state continuity, provenance, and acceptance semantics. A subsystem must not silently invent a parallel authority or state model.

### 4. Give the system memory through traceable lineage

Every meaningful action should be reconstructable.

At the applicable acceptance boundary, lineage should answer:

**Who authorized → What state existed → Which mission → Which exact SHA → Which flight → What executed → What evidence resulted → What verification occurred → What became canonical**

Receipts, hashes, state digests, and evidence are mechanisms for reconstructing truth—not substitutes for verification.

### 5. Obsess over invisible reliability

The highest-value failures are often the ones an operator should never have to notice.

SAGE hardening should prioritize invisible reliability against:

- stale authority replay;
- corrupted or partially mutated state;
- interrupted transitions;
- cross-flight contamination;
- incorrect mission binding;
- evidence/state mismatch;
- provenance loss;
- noncanonical promotion;
- false-green verification;
- invalid recovery.

The desired user experience is simple: **SAGE did the right thing.**

### 6. Strengthen the substrate before multiplying features

Prefer mechanisms that make future capabilities safer over isolated features that solve one narrow case.

Examples include:

- transition atomicity;
- mission and execution binding;
- state integrity verification;
- receipt integrity;
- promotion-boundary controls;
- canonical SHA enforcement;
- fail-closed authorization.

A substrate improvement compounds. Future capabilities inherit the stronger boundary instead of recreating it independently.

### 7. Reject hero dependency and institutionalize excellence

SAGE must not depend on one developer, one agent, one session, or undocumented tribal knowledge.

Engineering quality must be encoded in:

- governance contracts;
- tests;
- evidence schemas;
- boot/re-hydration procedures;
- repository-native checks;
- review boundaries;
- explicit ownership;
- durable documentation.

The system should remain understandable and operable when the original implementer is absent.

### 8. Optimize for long-term capability accumulation

SAGE should compound capability rather than repeatedly reset its context.

Every promotion should leave behind reusable infrastructure, validated knowledge, negative knowledge, evidence, and clearer boundaries for the next mission.

The objective is not today's impressive demo. The objective is a system that becomes harder to corrupt, easier to verify, and more capable with every validated generation.

## Operating Doctrine

When choosing the next mission, prefer:

1. the largest verified capability gain;
2. the highest-value blocker removal;
3. the strongest evidence path;
4. the greatest future reuse;
5. the smallest change that closes a demonstrated failure seam.

Do not create work merely because an issue, branch, or historical plan exists. First prove that the problem remains present on canonical `main`.

**Failure exists → prove it → harden it → attack it → verify it → promote it → compound it.**

## Governance Invariants

- **REPO TRUTH > AGENT REPORT**
- **CANONICAL STATE > STALE BRANCH**
- **EVIDENCE > ASSERTION**
- **VERIFICATION > CONFIDENCE**
- **FAIL CLOSED > GUESS**
- **HARDEN FIRST > FEATURE THEATER**
- External research informs challenge and discovery; it does not become canonical without validation.
- No promotion without exact-head reconciliation at the declared acceptance boundary.
- No duplicate hardening when the demonstrated seam is already closed.
- No capability expansion merely to maintain activity.

## SAGE Evolution Loop

The doctrine operates through the governed loop:

**SENSE → BOUND → ACT → MEASURE → LEARN → VERIFY → IMPROVE**

The loop is complete only when the improvement becomes reusable substrate or a validated capability at its declared boundary.

## Relationship to C2 Boot

The C2 Mission Control Boot Sequence is the operational bootstrap companion to this doctrine. C2 execution surfaces should rehydrate this doctrine alongside the canonical mission contract, live repository state, evidence, acceptance state, and flight board before executing a mission.

## External Source Boundary

The World-Class Engine Principle was inspired by public descriptions of Rockstar/Take-Two's quality, longevity, creativity, innovation, and efficiency philosophy. SAGE does **not** treat Rockstar, Take-Two, or external commentary as architectural authority. External material is Super Search/research input only and must remain separated from canonical validated state until independently verified.

## Final Principle

**Build like a world-class studio. Govern like critical infrastructure. Verify like an adversary. Compound like an engine.**
