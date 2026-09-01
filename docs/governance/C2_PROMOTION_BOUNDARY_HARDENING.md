# SAGE C2 Promotion Boundary Hardening

## Purpose

Keep repository-native promotion rules explicit and auditable even when the
hosting platform has no active branch ruleset.

## Canonical promotion invariant

`REPO TRUTH -> EXACT HEAD -> REQUIRED VERIFICATION -> REVIEW -> PROMOTION`

An agent report, branch name, or open pull request is not evidence of
promotion. Canonical state is established only from the live repository ref
and independently verified evidence.

## Required control-plane boundaries

1. `main` is the canonical promotion target.
2. Changes to `.github/`, `docs/governance/`, `sage/c2/`, `sage/core/`,
   `scripts/`, and `tests/c2/` require CODEOWNERS review when branch rulesets
   are enabled.
3. Platform verification must pass before promotion.
4. Exact-head evidence must bind to the commit being promoted.
5. Failed, missing, stale, or contradictory evidence is a HOLD, never a PASS.
6. Stale or redundant branches are not capability authority.
7. External GitHub branch protection remains a platform control; this document
   does not pretend that a repository file can enable GitHub rulesets.

## Current platform gap

If live GitHub reports no ruleset protecting `main`, the gap is reported as
an external control-plane HOLD. Repository-native checks may document and test
the invariant, but they cannot truthfully claim to enforce GitHub merge
settings that are not configured.

## Marine-mode execution rule

C2 must inspect live repository truth first, identify the actual seam, make the
smallest governed change, exercise failure paths, and promote only after exact-
head verification. Build activity without a verified control-plane gap is not
progress.
