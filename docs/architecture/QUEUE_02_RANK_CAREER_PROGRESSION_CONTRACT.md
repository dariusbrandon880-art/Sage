# Queue #02 — Rank & Career Progression Contract

**Status:** AGREED / LOCKED CONCEPTUAL CONTRACT  
**Scope:** Rank-system progression semantics only  
**Five-Flight architecture:** unchanged  
**C2:** control/orchestration function, never a rank

## 1. Core rule

A SAGE rank is an **aggregate career designation reflecting demonstrated agent evolution**. Rank does not grant, unlock, or prescribe capabilities.

The causal direction is:

`REAL WORK → WORKFLOW EVOLUTION → CAPABILITY EVOLUTION → VERIFIED PROGRESSION → CAREER RECORD → RANK ASSESSMENT`

XP, Points, accomplishments, Boss outcomes, badges, and other verified progression signals may contribute to the assessment, but no single signal is itself the definition of rank.

## 2. What contributes to an agent's evolution

The career record may accumulate verified evidence from real SAGE work, including:

- builds and implementations
- repairs and recovery work
- inventions and novel solutions
- discoveries and research breakthroughs
- verification breakthroughs
- difficult failures resolved
- intelligence/recon contributions
- workflow improvements
- missions and sorties
- exceptional operational work
- other genuinely demonstrated capabilities discovered and governed by SAGE

The system must not invent accomplishments merely to advance an agent.

## 3. Bosses are exceptional career events

A **Boss** is a governed difficulty classification for an exceptional real SAGE accomplishment. It is not required to represent literal combat.

Only two Boss classes are recognized by this contract:

- **Big Boss** — represented visually by **⭐**
- **Major Boss** — represented visually by **⭐⭐**

Examples can include a difficult build, major repair, invention, architecture breakthrough, severe production failure resolved, major research breakthrough, difficult recon/intelligence problem, security problem, integration problem, or another genuinely exceptional challenge.

Not every hard task qualifies as a Boss, and a task must not become a Boss merely because it consumed time or effort. As SAGE accumulates real verified work and evidence, the system should detect patterns that appear Boss-worthy and **propose** Boss classification. The Director retains final authority to confirm/recognize the Boss event.

A verified Boss battle/kill/capture creates the career's Boss accomplishment record and contributes Points and XP according to the verified substance of the event. Boss class does not imply a fixed automatic XP payout.

## 4. Stripes, Points, XP, and badges

These are distinct progression signals.

- **Stripe:** the visual tally of an agent's cumulative verified Boss battles/kills/captures. One Boss battle = one Stripe; two Boss battles = two Stripes; and so on.
- **Boss stars:** identify the class of the Boss associated with the current/recorded Boss event: ⭐ = Big Boss; ⭐⭐ = Major Boss.
- **Points:** quantified verified work value assigned to an event.
- **XP:** durable career progression accumulated from governed progression events.
- **Badges:** separate durable recognition for governed accomplishments/attributes; badges are not interchangeable with Boss Stripes, Points, or XP.
- **Rank:** aggregate designation reflecting the agent's overall evolution.

### Locked Boss visual

The HUD/career presentation uses the following visual relationship:

```text
⭐  |  ⚔️⚔️⚔️⚔️   = Big Boss | 4 cumulative Boss battles
⭐⭐ |  ⚔️⚔️       = Major Boss | 2 cumulative Boss battles
```

The **stars identify Boss class**. The **Stripe tally records how many Boss battles the agent has accumulated**. The tally sits directly beside the Boss-star marker in the visual presentation.

The exact visual glyphs and presentation can later be rendered by the HUD implementation, but this semantic relationship is locked by Queue #02. No HUD implementation is being coupled into this contract.

## 5. Attribution and shared progress

Every progression event must preserve individual attribution while allowing shared mission credit.

A multi-agent event can record, as applicable:

- primary contributor
- contributing agents
- contribution type(s)
- evidence lineage
- verified outcome
- shared SAGE capability gained

Example:

```text
MISSION / BOSS EVENT
Primary:       Jules
Recon:         Gemini
Verification:  ChatGPT
Shared result: SAGE capability gained
```

Individual career records receive attributable progression. The shared SAGE record receives the collective mission outcome. Collaboration must not erase individual contribution or cause one agent to inherit another agent's accomplishment.

## 6. Promotion authority

The system may evaluate the career record and produce a **promotion proposal**.

A proposal can summarize:

- current rank
- Points
- XP
- Boss Stripe tally
- verified accomplishments
- badges
- workflow evolution
- capability evolution
- evidence lineage
- apparent readiness for the next rank

A proposal is **not** a promotion.

The **Director retains promotion authority** under the governed career system.

No automatic promotion rule is established by this contract.

## 7. Rank vocabulary boundary

The agreed 30-rank SAGE ladder remains the shared vocabulary for all agents. Career specialization may differ by agent; rank does not encode or grant a permanent job/domain assignment.

C2 is outside the ladder because C2 is a control function rather than a career rank.

The Marine/Air Force blend is SAGE immersion terminology inspired by real progression concepts; it does not confer real-world military authority or status.

## 8. Research notes — real systems consulted

### Marine Corps

Marine progression is useful as a reference for increasing responsibility, leadership, and distinct professional/technical development paths. SAGE borrows the progression principle, not a literal military personnel system.

### U.S. Air Force

Air Force development materials emphasize education, training, experience, competencies, and increasing responsibility. This supports treating agent evolution as broader than a numerical XP bar.

### Warframe

Warframe's Mastery Rank aggregates progression across equipment and missions and uses separate rank tests before advancement. A useful lesson for SAGE is that accumulated progression and demonstrated advancement can be distinct. Warframe also prevents repeatedly farming the same first-time Mastery sources, which is relevant to later anti-farming design.

### Deep Rock Galactic

Deep Rock Galactic separates class progression, player rank, and promotion/prestige. Its promotion system demonstrates the value of making promotion a distinct career milestone rather than merely another XP increment. Its rank model also supports the concept of aggregate activity contributing to career standing.

### Broader progression research

Cross-genre research supports separating progression currencies from durable accomplishments, specialization, commendations/badges, titles, milestones, and difficult encounter recognition. SAGE uses these as design evidence only and does not copy another game's combat or progression economy.

### Research boundary

These systems are references and design evidence only. SAGE does not copy their currencies, unlock trees, combat assumptions, or authority models. The SAGE progression model remains governed by real work, evidence, attribution, and Director-controlled promotion.

## 9. Explicit non-goals for this lock

This contract does **not** yet define:

- exact Point values
- Point → XP conversion
- automatic XP awards
- rank thresholds
- promotion eligibility formulas
- demotion/invalidation propagation
- exact Boss reward amounts
- HUD implementation
- anti-farming implementation
- Five-Flight structure

Those remain separate numbered work items and are not to be silently coupled into Queue #02.
