# SAGE Flight GPS v1.2 — Observer Contract

## Purpose

Flight GPS is the C2 airspace observer and recommender for multi-session execution. v1.2 is deliberately **read-only**: it may inspect Git/PR telemetry and recommend safe frontiers, but it does not merge, rebase, force-push, or otherwise mutate repository state.

## Three orthogonal control dimensions

1. **AirspaceStatus** — CLEAR, SHARED, DEPENDENT, OCCUPIED, STALE.
2. **FlightLifecycle** — PROPOSED, RESERVED, ACTIVE, TESTING, RECONVERGING, INTEGRATED, plus BLOCKED/FAILED/ABANDONED escapes.
3. **ObservabilityState** — NOMINAL, DEGRADED, OFFLINE.

Lifecycle never substitutes for airspace safety. Telemetry failure never implies empty airspace.

## Fail-closed dispatch

- NOMINAL: normal observation and five-slot recommendation.
- DEGRADED: local/partial observation is permitted, with ambiguous targets excluded rather than assumed safe.
- OFFLINE: no new wave recommendations are authorized.

## Stale ownership

An expired heartbeat is classified as STALE. Reclamation requires an owner probe. A responsive owner retains its lifecycle and receives a refreshed heartbeat; an unresponsive owner is marked ABANDONED while its manifest remains available for lineage preservation.

## Collision policy

Direct file, symbol, and evidence-artifact collisions block a candidate. Module overlap is SHARED and requires partitioning. Active owners produce OCCUPIED airspace; PR-owned overlapping work is DEPENDENT. Base drift is an observation signal and must not be conflated with lifecycle.

## Next enforcement boundary

After v1.2 observer tests and live telemetry verification are green, a separate enforcement change may connect Flight GPS recommendations to the five-flight wave dispatcher. That change must preserve the observer's read-only boundary and retain explicit evidence for every routing decision.
