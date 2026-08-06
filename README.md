# SAGE: Autonomous Continuity Runtime (ACR)

SAGE is a high-fidelity, governed multi-agent execution framework designed to maintain strict state alignment and operational continuity across stateless LLM/engineering sessions. By establishing a persistent, non-repudiable audit ledger, cryptographic hash chain integrity, and prefrontal cortex simulated safety gateways, SAGE ensures linear development progress with zero workflow drift.

---

## 🚀 Key Capabilities

* **State Persistence & Rehydration:** Chronological replay of mission states directly from repository ledger records, bypassing conversational history limitations.
* **Prefrontal Cortex (PFC) Simulator:** Executive control safety gate evaluating proposed actions against mission alignment, completed-work protection, operator constraints, and evidence requirements before execution.
* **Non-Repudiable Evidence Ledger:** Integrated Cross-Model Audit Payload Schema (CMAPS) and SAGE-CCL ledger layers, tracking nonces, signatures, and cryptographic fingerprints of workspace artifacts.
* **Workspace Drift & Contamination Scanning:** Live background scanning of protected namespaces (`sage/runtime/`, `sage/core/`, `sage/acr/`, `sage/agents/`) to prevent external workspace corruption and unauthorized modifications.
* **NASA-Inspired OIL Metrics:** Real-time diagnostics engine computing dynamic metrics (lifecycle completion rate, recovery success rate, evidence quality, context preservation) rendering directly to the Operator Control Tower.

---

## 🗺️ Validated Milestones

1. **SAGE-ACT Milestone 1 & 2 Core:** Session-to-Task lineage tree linkers, advanced authorization safety gates, and validation protocols.
2. **Milestone 3 Continuity Control Loop:** Sandboxed isolation rules, telemetry taps, chronological monotonicity checks, and SAGE Operational Intelligence (OIL) metrics collector.
3. **Phase 0 Cognitive State Kernel:** Cognitive State Schemas and Prefrontal Cortex (PFC) Simulator safety gates.
4. **Phase 1 Cognitive Continuity & OpenAI Runtime:** State Loader, Continuity Retrieval Interface, PFC Governed Executor, and secure OpenAI runtime auth/activator loops.

---

## 🛠️ Getting Started & Testing

SAGE is built on Python and managed via Poetry.

### Dependencies
Install all required libraries and development dependencies:
```bash
poetry install
```

### Running Tests
Our test suite includes targeted unit tests, integration tests, adversarial validation checks, and isolation enforcement validations.
```bash
poetry run pytest
```
*Current status:* **100% Passing (246 Green Platform Tests)**.

---

## 🤝 Contribution Path

We welcome contributions from the community! To maintain strict repository security and quality, please follow the guidelines in [CONTRIBUTING.md](CONTRIBUTING.md):
1. Create a feature branch off `main`.
2. Do not modify production namespaces (`sage/runtime/`, `sage/core/`, `sage/acr/`, `sage/agents/`). Implement new features in `sage/experimental/`.
3. Ensure all tests pass cleanly before creating a Pull Request.

---

## 📄 License & Legal Strategy
SAGE is open-source software licensed under the [MIT License](LICENSE). For full details on project ownership, copyright, trademarks, and intellectual property, please refer to [docs/legal/IP_STRATEGY.md](docs/legal/IP_STRATEGY.md).
