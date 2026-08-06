# SAGE Intellectual Property & Licensing Strategy

This document outlines the intellectual property (IP), licensing, and provenance strategies for SAGE (SAGE Autonomous Continuity Runtime).

## 1. Repository & Copyright Ownership

* **Ownership:** The repository and all contained materials are owned and maintained by the **SAGE Development Team**.
* **Copyright:** All code, specifications, and documentation are under the copyright of the **SAGE Development Team** (Copyright (c) 2026 SAGE Development Team).
* **Individual Contributions:** Contributors retain the copyright of their specific contributions, but grant a broad, non-exclusive, perpetual, royalty-free license to the SAGE Development Team to distribute and sub-license those contributions under the project's default license.

## 2. Licensing Model

* **Core & Experimental:** SAGE uses the standard **MIT License** for all code, modules, and tests.
* **Documentation:** All documentation is licensed under the **MIT License** to ensure maximum ease of use and dissemination.

## 3. Protected Branding & Trademarks

* **Project Identity:** The SAGE brand, including the name "SAGE Autonomous Continuity Runtime", is a reserved project identity.
* **Usage Restrictions:** Unauthorized commercial use of the SAGE name to imply endorsement or official partnership is prohibited. See [TRADEMARK.md](TRADEMARK.md) for detailed branding policy.

## 4. Public vs. Private Components

* **Public Repository:** The SAGE core, session managers, control plane, experimental cognitive kernel, and tests are public.
* **Private Components:** Any enterprise connectors, custom orchestrators, or proprietary adapters built by third parties can remain proprietary and private. The core SAGE MIT licensing permits linking without forcing proprietary components to open-source (no copyleft/viral licensing behavior).

## 5. Provenance & Evidence Strategy

SAGE leverages its own continuous operational mechanisms to establish strict, machine-readable provenance and audit traces:
* **Architecture Decision Records (ADR):** Major architectural choices are captured as immutable records, guaranteeing traceability.
* **Evidence Lineage:** Nonces, cryptographic hashes of workspaces, and git commit references are synchronized on-disk and recorded within `SessionState` ledgers.
* **Release History & Milestone Tracing:** Every major milestone and release explicitly references its supporting evidence report files inside `evidence_capture/`, providing high-fidelity verification of historical compliance.
