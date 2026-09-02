# SAGE Career Progression Contract — Queue #02

**Status:** Agreed / locked concept
**Scope:** Rank + career progression architecture
**Queue:** #02 Rank System Finalization

## Core rule

**Rank is an aggregate career designation reflecting an agent's demonstrated evolution across real work, workflow evolution, capability evolution, verified progression, XP, accomplishments, and career history. Rank does not grant capabilities.**

Capabilities and workflow evolution are observed from actual SAGE work. Rank is the resulting designation after those signals are evaluated together.

## Progression signals

The career record may accumulate verified events from real SAGE activity, including builds, repairs, inventions, research, discoveries, verification breakthroughs, difficult integration or operational work, missions, sorties, exceptional problem resolution, and Boss outcomes.

No category is inherently worth a fixed amount. The substance, difficulty, verification, impact, reuse, and contribution of the real event must be evaluated by the later Points and XP contracts.

## Boss progression

Bosses are first-class career events. A Boss is an exceptional real SAGE accomplishment, not fictional combat state. Examples include a difficult build, major repair, invention, research breakthrough, severe failure resolved, security problem defeated, or other genuinely difficult capability.

Boss classes:

- Minor Boss
- Big Boss
- Major Boss

A verified Boss outcome produces durable career recognition: a **stripe**. The stripe records the accomplishment independently from Points and XP.

A Boss may contribute to Points, XP, rank assessment, career history, later HUD recognition, and shared mission progress. Those downstream values are not fixed by this contract; later numbered steps determine them.

## Attribution and shared progress

Every progression event must distinguish **individual contribution** from **shared SAGE outcome**.

ChatGPT, Jules, Gemini, and future agents retain attributable career history. A joint accomplishment can have multiple contributors while remaining one shared SAGE outcome.

Conceptual contribution record:

```text
EVENT
  primary_agent
  contributors[]
  shared_outcome
  evidence
  verification
  points
  xp
  recognition/stripe
```

The exact schema is intentionally deferred to the relevant numbered queue items.

## Promotion authority

The system may evaluate an agent's record and generate a **promotion proposal**. The system does not silently promote the agent.

The Director retains promotion authority.

```text
career evidence
      -> readiness evaluation
      -> promotion proposal (optional)
      -> Director decision
      -> persistent rank change
```

Automatic promotion is not part of this contract.

## Rank ladder boundary

The agreed 30-title ladder is shared across agents. Career specialization remains separate from rank. **C2 is not a rank**; C2 remains the command/control function.

The exact title list is already locked by the Queue #02 rank tests. This contract governs what the ladder means, not the title vocabulary itself.

## Research notes

### Marine Corps

The Marine Corps rank structure demonstrates increasing responsibility and distinguishes senior advisory roles from technical-specialist tracks. This supports using rank as a career designation reflecting accumulated responsibility rather than a simple XP unlock.

### Department of the Air Force

Air Force force-development material combines education, training, and experience across career development and connects progression to competencies, experience, performance, and increasing responsibility. This supports treating workflow and capability evolution as inputs to rank rather than capabilities as things rank grants.

### Game progression

Game systems are useful as mechanic references, not authorities. Mastery/proficiency systems support separating accumulated progression from demonstrated mastery. Achievement and recognition systems support durable accomplishment records. SAGE must preserve its evidence-governed model rather than copying a game economy.

## Explicit non-goals

This contract does not yet define Point values, XP conversion, automatic XP thresholds, promotion thresholds, exact Boss reward amounts, demotion mechanics, anti-farming implementation, HUD rendering, or Five-Flight structure.

## Governance note

This is intentionally a small locked piece of Queue #02. New mechanics must follow:

**discover -> discuss -> agree -> lock into repo -> verify -> proceed.**
