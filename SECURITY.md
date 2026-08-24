# SAGE Security Policy & Repository Governance

## Supported Versions

SAGE (Autonomous Continuity Runtime) maintains active security support on the canonical `main` branch.

| Version | Supported          |
| ------- | ------------------ |
| main    | :white_check_mark: |
| < main  | :x:                |

---

## Reporting a Vulnerability

Security is paramount in autonomous cognitive runtimes. If you discover a vulnerability, credential exposure, or authorization bypass:

1. **Do NOT open a public GitHub issue** for undisclosed security vulnerabilities.
2. Report security findings directly to the repository maintainers via private security advisory or designated contact channel.
3. Include clear steps to reproduce, impact assessment, and any proposed remediation.

Maintainers will acknowledge receipt within 24 hours and provide status updates on remediation.

---

## Protected Core Namespaces

SAGE enforces strict modular boundaries to prevent unauthorized core runtime mutations:

- `sage/core/`: Immutable core engines, SPEK validation, and attestation primitives.
- `sage/runtime/`: Kernel decision bridge, C2 context rehydration, and model gateway.
- `sage/c2/`: Command and Control flight execution and wave reconvergence.
- `docs/governance/`: Architectural contracts and operating frames.
- `.github/workflows/`: CI/CD automation and Five-Flight verification pipelines.

Workspace modifications inside these paths trigger fail-closed `Protected namespace violation` checks unless explicitly authorized by C2 governance.

---

## Security & Verification Invariants

1. **Zero Secret Exposure**: Plain API keys, credentials, private keys (`*.pem`, `*.key`), or session tokens must never be committed to git history.
2. **One-Way Import Law**: Core namespaces (`sage/core`, `sage/runtime`, `sage/c2`, `sage/acr`, `sage/agents`) must never statically import from speculative experimental modules (`sage/experimental`).
3. **Fail-Closed Execution**: Any missing prerequisite, signature mismatch, or unauthorized execution proposal fails closed without mutating canonical state.
4. **Cryptographic Provenance**: All execution receipts and capability promotions require SHA-256 fingerprint validation and immutable evidence receipts under `evidence_capture/`.
