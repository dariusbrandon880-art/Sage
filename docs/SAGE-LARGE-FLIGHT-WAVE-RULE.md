# SAGE Large Flight Wave Rule

The default large empirical flight aperture is **five complete campaigns in one
wave**. Each campaign contains the four established longitudinal cells:
Recovery, Reuse, Retention/Regression, and Compound.

**5 campaigns x 4 cells = 20 independently observed flight cells.**

## Production law

- Enumerate all 20 cells before launch.
- Run independent cells concurrently when isolation permits.
- `fail-fast` is disabled: one cell failure must not cancel independent cells.
- Preserve cell-level evidence and provenance.
- Missing/unobserved cells force `HOLD` for the campaign or wave.
- Shared infrastructure failures collapse into one repair frontier.
- After repair, re-run every affected cell.
- The wave is not complete until all 20 cells have evidence-backed terminal
  states: `PASS`, `HOLD`, `NEGATIVE_RESULT`, or `BLOCKED_WITH_EVIDENCE`.
- Capability qualification remains downstream of the existing evaluator and
  independent C2 verification.

## Why this is a capability

The capability is not merely executing more jobs. It is maintaining epistemic
completeness while production aperture expands: execution, observation,
provenance, failure isolation, repair, and verification all scale together.

If the execution surface cannot launch the full wave, that is an execution
surface defect to repair—not a reason to silently reduce the authorized wave.

## Boundary

The wave runner cannot mutate canonical capability state, grant authority,
or convert observations into qualification. Those boundaries remain governed
and serialized.
