# Contributing to SAGE

We are thrilled that you are interested in contributing to the SAGE Autonomous Continuity Runtime!

## How to Contribute

1. **Issues:** Search the issue tracker for existing requests before filing a new bug or feature proposal.
2. **Forking:** Fork the repository and create a feature branch off of the `main` branch.
3. **PML & Scope Discipline:** All contributions must adhere to strict scope discipline. Do not modify production namespaces (`sage/runtime/`, `sage/core/`, `sage/acr/`, `sage/agents/`) unless explicitly authorized. Use `sage/experimental/` for new experimental features.
4. **Testing:** Run the full platform test suite (`poetry run pytest`) to ensure 100% of tests pass and no regressions are introduced.
5. **Code Style:** Follow PEP 8 and project-specific formatting guidelines (Black line-length 100).

## Code of Conduct

By participating, you agree to abide by our Contributor Covenant [Code of Conduct](CODE_OF_CONDUCT.md).
