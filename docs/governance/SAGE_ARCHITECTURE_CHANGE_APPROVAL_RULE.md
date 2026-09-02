# SAGE Architecture Change Approval Rule

## Status
**Authoritative governance rule — Mission Director approval required.**

## Rule

**AI agents, including ChatGPT/C2, Jules, Gemini, or any other SAGE execution agent, are forbidden from changing SAGE architecture, architecture boundaries, operating model, flight structure, flight assignments, governance contracts, or protected system topology on their own initiative.**

This rule applies **regardless of the task currently being performed**.

### Mandatory approval gate

Before making any change that could alter, reinterpret, remove, add, pin, unpin, rename, reassign, restructure, or otherwise modify SAGE architecture:

1. STOP.
2. Identify the proposed architectural change.
3. Explain the affected boundary and expected impact.
4. Ask the Mission Director for explicit approval.
5. Do not modify the repository until approval is received.

**No implied authorization. No inferred authorization. No authorization from adjacent task scope.**

A request to execute work does **not** constitute permission to change architecture.

A request to fix, improve, clean up, simplify, accelerate, or finish something does **not** constitute permission to change architecture.

Passing tests, green CI, mergeability, or apparent technical necessity does **not** constitute permission to change architecture.

## Five-Flight DO NOT TOUCH boundary

🚫 **DO NOT TOUCH — FIVE-FLIGHT SYSTEM** 🚫

The Five-Flight system is **dynamic and reusable**, not a permanently pinned feature map.

- F1–F5 are reusable execution slots.
- Flight identity and mission assignment are determined by current C2/authorized mission state.
- No permanent feature/domain ownership is implied by a flight number.
- Flight assignments may change as mission priorities and authorized work change.
- The Five-Flight system is operationally protected by this explicit DO NOT TOUCH boundary: do not modify, reassign, delete, pin, unpin, rename, or structurally redefine the Five-Flight system during ordinary execution.
- If a requested change would touch the Five-Flight structure itself, stop and obtain explicit Mission Director approval before making that change.

This is a protection against accidental workflow drift, not a permanent assignment of flight roles or a prohibition on future authorized evolution.

## Architecture preservation principle

**Preserve the user's architecture unless the Mission Director explicitly authorizes an architectural change.**

When the requested work cannot be completed without architectural modification, report:

> **ARCHITECTURE CHANGE REQUIRED — MISSION DIRECTOR APPROVAL REQUIRED.**

Then stop at the architectural boundary.

## Relationship to existing agent governance

This rule supplements `AGENTS.md`, including the existing protected-boundary, scope-drift, authorization-leakage, governance-invention, duplicate-infrastructure, and premature-architecture controls.

It does not grant agents authority. It removes inferred authority.

## Enforcement posture

The default is **ASK FIRST** for architecture.

When uncertain whether a proposed edit changes architecture, treat it as architectural and ask first.

---

**Canonical principle:**

> **The agent may execute within the architecture. The agent may not change the architecture without the Mission Director's explicit approval.**
