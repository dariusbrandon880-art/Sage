# SAGE Executable Mission Contract Specification v1

**Status:** Implemented minimum executable control surface
**Parent doctrine:** `docs/governance/SAGE_HIGH_TEMPO_MISSION_EXECUTION_DOCTRINE.md`
**Purpose:** Turn deterministic mission boundaries into machine-checkable data without creating a competing authority model.

## Architectural decision

The High-Tempo Doctrine remains the governing intent layer. The executable Mission Contract is a **constraint representation**, not a replacement commander, authorization system, or mission planner.

Existing SAGE authority remains authoritative. The contract can narrow an authorized mission; it cannot expand authority.

This follows the repository's anti-regression rules against duplicate infrastructure, governance invention, premature architecture, and scope drift. Existing agent contracts remain the enforcement authority for agent permissions.

## Contract shape

```json
{
  "schema_version": "1.0",
  "mission_id": "FLIGHT-YYYY-MM-DD-NN",
  "intent": "Durable desired outcome",
  "authority_boundary": {
    "allowed_paths": ["sage/c2/**"],
    "prohibited_paths": ["sage/core/**"]
  },
  "completion_criteria": {
    "required_tests": [],
    "min_coverage_pct": null,
    "provenance_required": true
  },
  "stop_the_line_conditions": ["CROSS_BOUNDARY_FILE_TOUCH"],
  "metadata": {}
}
```

## Runtime behavior

`MissionContract` provides:

- strict schema/version validation;
- immutable mission identity and intent;
- path-boundary checking;
- prohibited-path checking;
- required-test and coverage gate representation;
- declared stop-the-line condition matching.

The implementation is stdlib-only to minimize dependency and deployment risk.

## Frontier behavior

`frontier_scanner.py` provides a conservative static map of local `sage.*` Python import edges among changed files and deterministic overlap detection for declared flight frontiers.

It is advisory until CI integration proves its precision. It does **not** claim to replace Git mergeability, complete dependency analysis, or runtime verification.

## Why this is the correct first slice

Gemini's audit identified four weaknesses: passive text-only enforcement, manual frontier mapping, context rehydration overhead, and missing dynamic tempo control. The first implementation targets the two most deterministic gaps—machine-readable boundaries and basic frontier overlap detection—without prematurely creating a full orchestration engine.

The repository already contains an AgentExecutionContract and a change-impact analyzer. The new capability therefore remains narrowly scoped to C2 mission representation and frontier analysis instead of duplicating agent authorization or impact-analysis infrastructure.

## Evidence boundary

A valid contract is **not** proof that a mission executed successfully.

The SAGE evidence hierarchy remains:

```text
CONTRACT VALID
    ↓
EXECUTION ATTEMPT
    ↓
TEST / OBSERVATION
    ↓
EVIDENCE
    ↓
INDEPENDENT VERIFICATION
    ↓
GIT RECONCILIATION
    ↓
MISSION CLOSE
```

This preserves the doctrine's explicit separation between authorization/configuration and execution proof.

## Super Search synthesis

External research supports the architectural direction but does not authorize it. Marine Corps MCDP 6 emphasizes durable intent so subordinate actions can adapt as circumstances change; this maps directly to SAGE's separation of intent from implementation steps.

Trunk-based development research reinforces short-lived, rapidly verified branches and speculative merge/build checks as throughput protections.

## Research backlog

The following remain research/invention candidates rather than production claims:

1. dynamic tempo controller;
2. semantic frontier engine beyond direct local imports;
3. automated quarantine orchestration;
4. structured radio/telemetry transport;
5. independent verifier-agent architecture;
6. automatic provenance synthesis.

Each must earn promotion through experiments and evidence rather than architectural enthusiasm.

## Promotion rule

A future Mission Contract v2 should not be introduced merely because it is more sophisticated. Promote only when a measured failure or verified capability gap demonstrates that v1 cannot safely or efficiently express the required mission boundary.
