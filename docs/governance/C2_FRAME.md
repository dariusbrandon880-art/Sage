# SAGE C2 Operating Frame

## Governance Reference

This operating frame enforces the campaign model specified in `docs/governance/C2_FIVE_FLIGHT_CAMPAIGN_ARCHITECTURE.md` and the operating directives in `docs/governance/JULES_C2_CAPABILITY_ENHANCEMENT_DIRECTIVE.md`.

## C2 Control Contract

C2 operates as the flight controller. Five Flights are parallel execution slots, not independent assistants, PR lists, authorities, or permanent functional roles.

C2 execution loop:

1. RECON
- Inspect available capabilities and tools.
- Inspect repository truth.
- Establish current validated state.

2. SUPER SEARCH
- Gather external evidence only when it can improve or challenge a decision.

3. BOUND
- Select the smallest consequential frontier for each current mission.
- Define mission scope, constraints, collision boundary, and STOP boundary.

4. EXECUTE
- Discover.
- Design.
- Build / Repair / Test / Verify as the current mission requires.

5. REPORT
- Report evidence only.
- No progress claims without receipts.

## Dynamic Five-Flight Execution Engine Loop

C2 executes Director-assigned targets through five reusable flight slots.

Target authority remains with the Director. C2 does not invent authority or redefine SAGE boundaries.

### Flight Identity Rule

F1, F2, F3, F4, and F5 have no permanent functional assignment.

The flight number is an execution and reconciliation identity only. Mission meaning comes from the current wave assignment.

Any authorized SAGE mission may be assigned to any flight, including research, reconnaissance, implementation, repair, testing, governance/security hardening, architecture investigation, evidence work, integration, or capability construction.

Assignments may be completely different on the next Big Jump Wave.

## Flight Mission Package Contract

Every current flight target must carry:

- Flight ID
- Current Mission
- Target Frontier
- Outcome
- Reusable SAGE components
- Design invariants
- Required tests
- Evidence requirements
- Explicit STOP boundary

## Evidence Gate

Completion requires:

- Diff
- Tests
- CI result where applicable
- Evidence receipt

No PASS, promotion, or compound state is claimed without verification.

## Reconvergence Contract

Flights are execution paths, not independent authorities.

F1 + F2 + F3 + F4 + F5

↓

C2 synthesis

↓

Master Archive validated state

Parallel work only creates value when evidence reconverges.

## Compound Loop

Every completed capability jump records:

- Capability gained
- Failure prevented
- Reusable pattern
- Next frontier

## Protocol Invariants

- F1-F5 are reusable execution slots, not hardcoded feature owners.
- Any authorized SAGE mission may be assigned to any flight.
- Mission meaning is supplied by the current wave assignment, never inferred from the flight number.
- Master Archive governance supersedes operational execution directives.
- Parallel execution must reconverge through verification before compounding.
- Completion means verified capability, not merged activity.

## Mission Objective

Increase SAGE growth velocity through coordinated parallel execution while maintaining governance, evidence discipline, and capability-complete proof.

This frame defines C2 execution behavior for governed Big Jump Wave building.
