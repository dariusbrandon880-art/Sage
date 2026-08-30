# SAGE Native Multimodal Perception Bridge

## Purpose

Define the governed boundary between a native multimodal interface (screen,
camera, and voice context) and SAGE's intelligence/governance layers.

SAGE does **not** claim direct device access. The interface is the upstream
perception gateway. SAGE receives only context explicitly presented by that
gateway and records what was observed separately from what was inferred,
searched, and verified.

## Epistemic contract

```text
OBSERVED != INFERRED != SEARCHED != VERIFIED
```

A perception event cannot silently promote an inference into an observation or
a search result into a verified fact. Each claim carries its own stage,
confidence, and optional provenance/source reference.

## Pipeline

```text
Native Multimodal Interface
        |
        v
   PerceptionEvent
        |
        +--> SENSE   -> explicit observed claims
        |
        +--> SEARCH  -> external/repository grounding references
        |
        +--> VERIFY  -> source-backed verified claims
        |
        +--> LEARN   -> session context reference
        |
        v
Governed synthesis
```

## Acceptance boundary

A future live interface adapter is accepted only when:

1. The upstream interface actually supplies the modality/context claimed.
2. SAGE records the source and user intent.
3. Observed, inferred, searched, and verified claims remain distinct.
4. Ambiguous perception remains uncertain rather than being fabricated.
5. The canonical event digest is reproducible for evidence binding.
6. No device access is claimed when no device context was supplied.

## First experiment

Use a real screen-sharing session while watching a film or examining a
technical artifact. Ask SAGE to identify what is visible and research its
real-world history. The experiment must distinguish:

- what the interface actually presented;
- what SAGE inferred from that presentation;
- what Super Search retrieved;
- what sources actually verified.

This is an interface capability experiment, not role-play.

## Architectural rule

This bridge is a capability layer. It does not replace C2, Mission Intake,
the Five-Flight architecture, or the existing Big Jump Wave. It supplies a
governed perception event that those existing layers can consume.
