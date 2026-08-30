# C2 Marine Mode Reconciliation — PR #331

PR #331 was closed as superseded after exact live-main inspection.

## Truth

- PR #331 was based on `main` at `9962cbe20c227d3e8432bf475fa15a939f5039a3`.
- Its head was `908bdc433b0ff918cfbb00f6b519e6f250af404c`.
- The branch had diverged from current `main` and was 30 commits behind.
- Current `main` already contains the newer `sage/c2/experiment_ledger.py` and `scripts/execute_experiment_ledger_wave.py` surfaces.
- The current mainline ExperimentLedger is the append-only evolution-trial model and intentionally remains non-authoritative for promotion.

## Disposition

`PR #331 = SUPERSEDED / CLOSED`

No obsolete ledger implementation was promoted. No force-push or destructive rewrite was used.

## C2 Rule

Prefer the newest canonical mainline substrate over merging an older divergent implementation that would replace it. Continue from current `main` with the next bounded Big Jump Wave / immersion acceptance target.
