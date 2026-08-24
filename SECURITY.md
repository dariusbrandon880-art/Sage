# SAGE Security Policy

## Reporting Security Vulnerabilities

The SAGE (Autonomous Continuity Runtime) project treats security, attestation integrity, and fail-closed isolation as fundamental invariants.

If you discover a potential security vulnerability or secret exposure in this repository, please report it responsibly:

- **Primary Contact**: Security Team / Repository Maintainer (`dariusbrandon880-art`)
- **Reporting Method**: Please create a private security advisory on GitHub or email the maintainer directly.
- **Do NOT** open a public issue for sensitive security vulnerabilities.

## Security Controls & Invariants

SAGE enforces strict governance boundaries and security invariants across the codebase:

1. **Protected Core Namespaces**: `sage/runtime/`, `sage/core/`, `sage/acr/`, and `sage/agents/` are protected core namespaces. Unsigned or unauthorized modifications trigger fail-closed `Protected namespace violation` blocks.
2. **One-Way Import Law**: Production core code must never statically import experimental modules (`sage.experimental`).
3. **Immutable Evidence Receipts**: Historical evidence records stored under `evidence_capture/` are cryptographically hashed and immutable.
4. **Secret Scanning**: Credentials, API keys, and environment tokens are strictly prohibited from being committed to version control.
5. **Fail-Closed Execution**: Any violation of attestation checks, PFC executive gates, or missing authorization results in an immediate `FAIL-CLOSED` state.

## Supported Versions

| Version | Supported |
| ------- | --------- |
| Main (`main` branch) | :white_check_mark: Supported |
