# SAGE SPEK v1.1: Policy Enforcement Kernel Specification

This document details the production-ready specification and implementation controls of the **SAGE Policy Enforcement Kernel (SPEK) v1.1 Hardened Core**.

---

## 1. System Architecture Map

SPEK coordinates five primary sub-systems to enforce deterministic rule boundaries, immutably audit changes, and isolate security scopes:

```
                  +-----------------------------------+
                  |      SAGE AI / Runtime Layer      |
                  +-----------------------------------+
                                    |
                    [ Submit Control Proposal ]
                                    |
                                    v
                  +-----------------------------------+
                  |    External Security Boundary     |  <-- Prevents unauthorized writes
                  +-----------------------------------+
                                    |
                                    v
                  +-----------------------------------+
                  |       HDG v2 Epistemic Graph      |  <-- Lineage and contradiction validation
                  +-----------------------------------+
                                    |
                                    v
                  +-----------------------------------+
                  |     Compliance & Lifecycle State   |  <-- Evaluates thresholds, routes result
                  +-----------------------------------+
                       /                             \
                      /                               \
                     v                                 v
        [ State == APPROVED ]                [ State == REJECTED ]
                    |                                 |
                    v                                 v
        +-----------------------+          +-----------------------+
        |  Promotion Queue Log  |          | Negative Results JSON |
        +-----------------------+          +-----------------------+
                    \                                 /
                     \                               /
                      v                             v
                  +-----------------------------------+
                  |     Immutable Chained Receipts    |  <-- EAS-001 Attestation audit vault
                  +-----------------------------------+
```

---

## 2. Core Functional Specifications

### 2.1 SPEK Lifecycle Engine

Proposals are evaluated deterministically against structured rules and transition through the following canonical states:

1. **PROPOSED**: Change input received with evidence references.
2. **EVALUATED**: Checked by the HDG v2 engine for parent ancestry.
3. **VALIDATED**: Authenticated via the CryptographicAttestationProvider.
4. **APPROVED** / **REJECTED**:
   - **APPROVED**: Reaches the minimum evidence threshold (0.8) with zero contradiction markers. Automatically logged inside `promotion_queue.log`.
   - **REJECTED**: Fails constraints. Captured inside `negative_results.json` along with comprehensive rejection evidence. Never executed.
5. **ARCHIVED**: Formally promoted and permanently logged.

### 2.2 HDG v2 Epistemic Causality Engine

Tracks dependency causality across hypotheses to prevent ancestral lineage deletion.
- **Ancestry Tracking**: Every hypothesis preserves references to parent nodes. Missing ancestors cause a fail-closed execution halt.
- **Contradiction Detection**: Rejects opposite claims or declared conflicts to maintain semantic consistency.

### 2.3 Cryptographic Attestation Layer

Pluggable, timing-safe signing framework using derived, non-hardcoded local deterministic HMAC-SHA256 signing keys, easily replaceable with external TPM/HSM providers.

### 2.4 Security Boundary Enforcement

Isolates critical governance and archive paths. Unauthorized write attempts to `sage/core` or `.sage` raise path permission failures to secure the core control plane.

---

## 3. Persistent Storage and Log Files

- **Receipt Vault**: `spek_vault.json` - Cryptographically linked EAS-001 validation receipt chain (immutable backlink pointers).
- **Negative Registry**: `negative_results.json` - Structured rejection registry.
- **Promotion Queue**: `promotion_queue.log` - Append-only line queue for approved promotion records.
