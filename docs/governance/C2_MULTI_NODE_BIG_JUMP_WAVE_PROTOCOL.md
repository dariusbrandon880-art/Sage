# SAGE C2 Multi-Node Big Jump Wave Execution Protocol

**Document ID:** `C2_MULTI_NODE_BIG_JUMP_WAVE_PROTOCOL`
**Version:** `1.0`
**Authority:** SAGE C2 Persistent Operating Contract + Master Archive + `docs/governance/BIG_JUMP_WAVE_C2_5X4_OPERATING_FRAME.md` + `docs/governance/C2_FIVE_FLIGHT_CAMPAIGN_ARCHITECTURE.md`

## 1. Executive Purpose

This protocol establishes canonical rules for Multi-Node Big Jump Waves across concurrent C2/Jules execution nodes. C2 MUST NOT collapse independent flights into lifecycle stages or bypass verification.

## 2. Multi-Node Architecture

- Node A: Primary Repair Wave — 5 flights + 2 reserves.
- Node B: Independent Verification Wave — 5 flights + 2 reserves.
- Node C: Adversarial Research Wave — 5 flights + 2 reserves.
- C2 Multi-Node Reconvergence aggregates evidence, receipts, and exact HEAD provenance before promotion.

## 3. Mandatory Laws

1. **Node Autonomy:** each node operates as an independent bounded execution unit.
2. **Flight Preservation:** each flight is an independent capability frontier, never a pipeline stage.
3. **Zero Flow Alteration:** the SENSE → RECON → SUPER SEARCH → BOUND → DECIDE → AUTHORIZE → BUILD → OBSERVE → VERIFY → COMPOUND loop is immutable; attempted alteration fails closed.
4. **Namespace Collision Locks:** concurrent write targets must not overlap.
5. **Reserve Capacity:** each node may hold two reserve slots for newly discovered defects.
6. **Cryptographic Reconvergence:** outputs and evidence bind to the exact active git SHA and aggregate into a signed receipt.

## 4. Verification Standard

A wave is verified only when all active flights pass, collision checks pass, exact-head provenance is valid, and the platform suite passes against the active HEAD. No email, generated artifact, or historical claim outranks live repository truth.

The implementation is a governed execution model; external workflow dispatch remains subject to the authenticated GitHub control plane.
