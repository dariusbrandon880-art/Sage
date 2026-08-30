# SAGE Experiment Ledger → Evolution Bridge v1

## Purpose

Close the evidence loop without creating autonomous promotion authority.

```text
Experiment Ledger
      ↓
measured trials
      ↓
EvolutionBaseline + EvolutionCandidate
      ↓
EvolutionLoop
      ↓
PROMOTE_CANDIDATE / HOLD / REJECT
      ↓
external validation + promotion authority
```

## Evidence contract

Every trial is tied to a mission, technique, unique trial ID, evidence reference, and exact 40-character Git commit SHA. A candidate becomes replicated only after at least two ledger trials. Adversarial challenge, regression status, evidence completeness, and human review are carried into the candidate gates.

The bridge averages the recorded fitness vectors; it does not manufacture missing measurements. Negative or incomplete evidence remains represented by failed gates and therefore produces `HOLD` rather than a success claim.

## Governance boundary

`PROMOTE_CANDIDATE` means the measured candidate cleared the evaluation gates. It does **not** authorize production mutation, archive promotion, or permanent capability adoption. `EvolutionEvaluation.promotion_authorized` remains false by construction.

## Proof target

A future real experiment should be able to reproduce this causal chain:

1. Same mission class and declared baseline.
2. Competing technique recorded as repeated trials.
3. Fitness measurements attached to evidence and exact repository provenance.
4. Adversarial/counterexample trial recorded.
5. Regression result recorded.
6. Independent human review recorded.
7. EvolutionLoop evaluates the resulting evidence.
8. Only external governance can promote the candidate.

This bridge is infrastructure for that experiment; it is not itself evidence that a technique is superior.
