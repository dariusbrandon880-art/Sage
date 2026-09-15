# SAGE HUD Canonical Contract

**Contract ID:** `SAGE-HUD-CANONICAL`
**Schema Version:** `1.0`
**Status:** GOVERNED / CANONICAL / READ-ONLY PRESENTATION CONTRACT
**Scope:** C2 rehydration and canonical SAGE Hub presentation

## 1. Authority

This document is the machine-verifiable presentation contract for the two canonical SAGE HUD surfaces.

It does **not** create, mutate, authorize, award, reconcile, or promote state. Canonical AirspaceState, the append-only event ledger, and governed repository/runtime evidence remain authoritative.

The existing `docs/governance/SAGE_C2_HUB_PRESENTATION_BOUNDARY.md` remains the contextual visibility doctrine. This document fixes the concrete surface identifiers, order, field semantics, and fail-closed requirements that doctrine refers to.

## 2. Rehydration Contract

A C2 rehydration flow MUST execute this semantic sequence:

```text
NEW CHAT
  -> SAGE REHYDRATION ENTRYPOINT
  -> LOAD THIS CANONICAL HUD CONTRACT
  -> LOAD CURRENT PERSISTED / RECONSTRUCTED ORGANISM STATE
  -> VALIDATE STATE AGAINST THIS CONTRACT
  -> SELECT HUB A, HUB B, OR COMPOSITE FROM GOVERNED CONTEXT
  -> RENDER THE SELECTED CANONICAL SURFACE
```

A C2 client MUST NOT use conversational memory, a pasted report, or a remembered screenshot as a substitute for current governed state.

If required authoritative state cannot be resolved, the flow MUST fail closed:

```text
REHYDRATION FAILURE
```

It MUST NOT fabricate values, substitute a generic dashboard, redesign the HUD, or silently downgrade to ordinary report prose.

## 3. Hub A — C2 Mission Control HUD

**Surface ID:** `HUB_A`
**Purpose:** operational command and mission-control visibility.

Exact section order:

1. `01 — COMMAND BAND`
2. `02 — OPERATING PICTURE`
3. `03 — PROGRESSION / IMPACT`
4. `04 — STRIKE FEED // HIGH-TEMPO EVENTS`

Canonical identity marker:

`[SAGE::C2::CHATGPT] ◈ C2 MISSION CONTROL`

### Hub A field semantics

| Field | Source / meaning |
|---|---|
| `STATUS` | canonical operating mode/state |
| `QUAL` | Mission Control station CQL/SQL qualification levels |
| `MISSION` | active canonical mission identifier/priority, or `NONE ACTIVE` |
| `THEATER` | active mission theater when an active mission exists |
| `ACTIVE SORTIES` | current canonical active sorties |
| `TOTAL SYSTEM XP` | canonical aggregate Airspace XP |
| station XP rows | canonical per-station XP plus CQL/SQL capability stack |
| strike feed | current frontier, sortie/evidence activity, and next clearance derived from canonical state |

No Hub A field may be filled with an invented value merely to complete the visual surface.

## 4. Hub B — SAGE Organism / Agent Projection

**Surface ID:** `HUB_B`
**Purpose:** organism-wide agent identity, qualification, career/progression, XP, and evidence-derived status.

Exact roster header:

`SAGE ORGANISM // AGENT PROJECTION`

When composed with Hub A, the wrapper section is:

`05 — ORGANISM PROGRESSION`

### Hub B field semantics

Each agent projection is derived from canonical station state plus the append-only event ledger:

| Field | Source / meaning |
|---|---|
| `agent_name` | canonical station identity |
| `RANK` | rank derived from career XP |
| `CQL` / `SQL` | canonical station qualification levels |
| `POINTS` | verified points projection |
| `XP` | career XP projection |
| `BOSS` | governed boss/badge projection |
| `⚔️` | total governed boss kills |
| `┃` | total governed captures |
| `status` | projection status; must not imply unverified state |

The projection is read-only and cannot award XP, change rank, grant badges, mutate missions, or create another state authority.

## 5. Composite Contract

**Surface ID:** `COMPOSITE`

Composite is Hub A followed by Hub B. It is a contextual composition, not a third HUD.

Semantic order:

```text
HUB_A
  -> 05 — ORGANISM PROGRESSION
  -> HUB_B
```

A composite MUST preserve both hub identities. It MUST NOT collapse them into a generic dashboard or report.

## 6. Contextual Selection

The governed runtime selects the surface required by the current interaction:

- ordinary operational C2 -> `HUB_A`
- organism / XP / rank / career -> `HUB_B`
- full organism/C2 rehydration or explicit full-state request -> `COMPOSITE`
- explicit Hub request for both -> `COMPOSITE`

Continuity alone MUST NOT force Hub B onto an ordinary Hub A turn.

## 7. No-Drift Rules

The following are normative prohibitions:

- **NO REDESIGN** — do not invent a replacement HUD.
- **NO SUBSTITUTION** — do not replace a canonical Hub with a generic dashboard/report.
- **NO FABRICATION** — do not invent unavailable state.
- **NO COLLAPSE** — Hub A and Hub B remain distinct semantic surfaces.
- **NO THIRD HUD** — shared XP/agent infrastructure does not create another presentation surface.
- **NO TRANSPORT AUTHORITY** — pasted Markdown, fences, Jules reports, screenshots, or chat memory are transport/input, not state authority.
- **NO REPORT FALLBACK** — when a canonical surface is required and available, ordinary prose does not replace it.

## 8. Machine-Testable Identifiers

The following identifiers are contract constants and MUST remain exact unless the schema version is deliberately changed through governed review:

```text
SAGE-HUD-CANONICAL
HUB_A
HUB_B
COMPOSITE
01 — COMMAND BAND
02 — OPERATING PICTURE
03 — PROGRESSION / IMPACT
04 — STRIKE FEED // HIGH-TEMPO EVENTS
05 — ORGANISM PROGRESSION
SAGE ORGANISM // AGENT PROJECTION
[SAGE::C2::CHATGPT] ◈ C2 MISSION CONTROL
```

## 9. Contract Change Rule

Any change to the identifiers, order, field semantics, contextual selection rules, or fail-closed behavior is a **governed HUD contract change**. It MUST update this specification and its regression tests together.

A renderer implementation may change internally, but its externally visible canonical contract may not drift silently.

## 10. Regression Acceptance

A fresh-chat continuity test passes only when:

1. the canonical contract is loaded;
2. current persisted/reconstructed organism state is loaded;
3. the requested/contextually selected Hub is identified correctly;
4. the exact canonical section identifiers and order are preserved;
5. actual state populates the fields;
6. unavailable state fails closed rather than being fabricated;
7. a fresh chat can rehydrate and continue from the same organism state without reteaching the HUD contract.
