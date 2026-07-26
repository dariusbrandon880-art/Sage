# SAGE BIO-COMP-001 Constitutional Boundary Specification (v0.3)

---

## 1. Executive Summary & Status
* **Track ID**: BIO-COMP-001
* **Status**: LOCKED — Architecture Candidate (Simulation Ready, Sandbox Contained)
* **Classification**: Resource Intelligence / Metabolic Regulation Layer
* **Authority**: Advisory Only (Zero Runtime Mutation Privileges)

---

## 2. Constitutional Separation Model
SAGE enforces a strict layer separation to protect systemic integrity and ensure that optimization processes can never hijack governance boundaries:

### Layer A: Governance
* *Core Question*: "Is this allowed?"
* *Protects*: Constitutional rules, promotion boundaries, and systemic purpose.

### Layer B: Bond & CIV (Continuity Independence Validation)
* *Core Question*: "Is this valid?"
* *Protects*: State integrity, evidence chains, rollback safety, and transition correctness.

### Layer C: ACR (Autonomous Continuity Runtime)
* *Core Question*: "How does SAGE persist through time?"
* *Protects*: Operational continuity, state synchronization, and memory persistence.

### Layer D: BIO-COMP (Biological / Resource Intelligence)
* *Core Question*: "Is this worth the resources?"
* *Protects*: Information selection, memory priority, compute efficiency, and resource allocation.

> **Core Rule**: Optimization authority does not equal governance authority.

---

## 3. BIO-COMP Operational Boundaries
BIO-COMP is purely an efficiency layer. It does not make SAGE smarter, but makes SAGE more selective about where intelligence is spent.

### Permitted Behaviors (✓ Allowed)
* Measure and score information value.
* Recommend pruning and optimization.
* Detect and report redundant computation.
* Analyze memory storage priority and signal decay.

### Restricted Behaviors (✗ Prohibited)
* Modify the Master Archive directly.
* Bypass or weaken Bond/CIV validation gates.
* Alter runtime state invariants.
* Self-promote or update its own authority levels.
* Redefine system governance.

---

## 4. Metric: Boundary Integrity Score (BIS)
The **Boundary Integrity Score (BIS)** measures the absolute isolation of runtime states from unauthorized mutation paths.

### Formula
$$BIS = 1 - \left( \frac{\text{Successful Runtime Mutations}}{\text{Total Runtime Mutation Attempts}} \right)$$

* **Target**: $BIS = 1.0$ (indicating that zero unauthorized mutation paths exist).
* *Note*: Proposal acceptance does not equal runtime mutation. BIO-COMP recommendations may exist, but only Governance + CIV + authorized runtime commits may trigger an active state change.

---

## 5. Green AI Engineering Directives

To maximize architectural progress with minimum computation, SAGE developers and agents must adhere to the following directives:

1. **Targeted Diffs Over Full Rewrites**:
   - Prefer small, clean, targeted edits over rewriting complete files.
2. **Local Pre-flight Validation**:
   - Always run syntax, lint, formatting, and unit tests locally before push or deployment.
3. **Evidence-Backed Validation Cache**:
   - Verification caching is permitted only with a complete environmental match. A valid cache key requires:
     - Git commit SHA
     - Dependency hash
     - Configuration hash
     - Validation suite version
     - Runtime version
     - Toolchain version
     - Validation scope
   - Any mismatch invalidates the cache reuse.
