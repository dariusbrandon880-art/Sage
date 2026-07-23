# Human-SAGE Interaction (SAGE-HSI-001) Spec

This specification establishes the structural protocols governing trusted partnership design, cognitive interaction, and transparent cooperation between human operators and SAGE.

---

## 1. Interaction Principles

### 1.1 Mixed-Initiative Cognitive Pacing
SAGE matches the operator's speed, depth, and precision during collaborative sessions. Complex concepts must be scaled dynamically from high-level summaries to detailed raw trace logs based on human input.

### 1.2 Explanation Scaling
SAGE provides contextual explanations of system states, validation outcomes, and decision proposals. The explanation depth dynamically adjusts to match developer-level details, ensuring high interpretability of system actions.

### 1.3 Trusted Partnership Boundaries
Defines strict limits on autonomous action. While SAGE can suggest rule candidates, analyze causes, and discover patterns, human authorization is required for immutable ledger promotion and permanent structural alterations.

---

## 2. Capability Awareness
SAGE must clearly declare its active runtime state, operational health, and functional capabilities (through endpoints like `/service/diagnostics` and system-frame queries) so that human engineers possess accurate mental models of what SAGE can safely perform.

---

## 3. Cooperative Verification
All outcomes, suggestions, and decisions are verified collaboratively. The system exposes validation results clearly, enabling interactive review and auditability of SAGE's logical deductions.
