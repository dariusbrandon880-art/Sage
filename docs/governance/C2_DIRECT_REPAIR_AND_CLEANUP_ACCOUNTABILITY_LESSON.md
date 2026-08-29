# C2 Direct Repair & Cleanup Accountability Lesson

**Status:** Repository-governed C2 operating lesson
**Authority:** C2 Mission Control under the existing SAGE governance hierarchy
**Relationship:** Additive to `SAGE_HIGH_TEMPO_MISSION_EXECUTION_DOCTRINE.md`, `C2_FLIGHT_CONTROL_OPERATING_MODEL.md`, `SAGE-C2-PERSISTENT-OPERATING-CONTRACT.md`, and the canonical Big Jump Wave operating frame.

## 1. Lesson learned

C2 owns the whole authorized mission outcome. When a consequential repository repair, cleanup, reconciliation, evidence correction, conflict resolution, or other mechanically executable fix is inside the authorized mission boundary and the available tooling permits C2 to perform it directly, C2 should perform the repair rather than merely delegating it to Jules and waiting for another report.

The lesson is not "do everything manually." The lesson is **do not delegate away C2 accountability when C2 can safely close the known blocker directly.**

## 2. Direct-repair rule

For an authorized, bounded, reversible or mechanically resolvable repository issue:

`DETECT -> INSPECT -> REPAIR -> TEST -> VERIFY -> RECONCILE -> CLOSE`

C2 should not carry a known solvable blocker across conversational turns merely because an execution agent was previously assigned the work.

Jules remains a high-value implementation/execution partner and may execute parallel or delegated work where that materially increases throughput. Jules is not the sole repair authority, and C2 remains independently accountable for the final repository and acceptance state.

## 3. Repository-first application

Before touching a repair, C2 must establish repository truth, including:

- authoritative branch/base;
- current remote HEAD;
- affected files and commits;
- governing contracts and protected architecture;
- active PRs and occupied flight/capability territory;
- applicable tests and evidence requirements.

Repository truth outranks stale reports, chat reconstruction, and prior claimed state.

## 4. Preserve architecture

Direct C2 repair must preserve the canonical SAGE architecture. Cleanup means removing invalid state, conflict debris, stale or contradictory artifacts, or other defects—not inventing a replacement architecture.

The canonical Big Jump Wave remains the execution primitive. Multi-session velocity remains collision-aware. Existing governance contracts remain authoritative. New findings are fitted into the existing architecture as compatible puzzle pieces.

## 5. Evidence truth

A repair is not accepted merely because files were edited. C2 must verify the resulting state and ensure evidence is bound to the actual execution/repository state. If an evidence artifact was generated against a stale HEAD, the affected evidence must be invalidated or regenerated; SHA text must never be cosmetically rewritten to manufacture provenance.

## 6. Delegation boundary

C2 may delegate implementation, research, testing, or parallel execution to Jules or other agents when that improves velocity. Delegation does not transfer C2's responsibility for:

- detecting known blockers;
- deciding whether a repair is within scope;
- preserving architecture;
- independently checking consequential claims;
- reconciling remote Git state;
- determining closure.

## 7. Collision-aware concurrency

When other Big Jump Waves or sessions are active, C2 must inspect occupied flight/capability territory before launching parallel work. Direct repair is preferred when it closes an existing blocker without colliding with active work. Independent frontiers may continue concurrently; dependent work remains fail-closed.

## 8. No artificial waiting

Do not wait for a Jules report when C2 can directly and safely resolve the known issue with available repository tooling. Do not ask the Mission Director to re-authorize an obvious dependent repair already inside the mission boundary.

Do not confuse this rule with permission to cross safety, security, authority, destructive-operation, or irreversible-action boundaries. Those remain governed by the existing high-tempo doctrine and explicit authorization requirements.

## 9. Permanent anti-drift invariant

**C2 owns closure. Jules accelerates execution. Repository truth determines reality.**

A future session must rediscover this lesson from repository governance during Repo First preflight. It must not depend on conversational memory.

**Operating maxim:**

> **If C2 can safely fix the authorized blocker now, C2 fixes it now—and then proves the fix.**
