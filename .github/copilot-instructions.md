# Sage 2 AI Engineering Instructions

## Mission
Sage 2 is an AI-assisted development project designed to eliminate manual copy/paste bottlenecks and establish an automated, test-driven development loop.

## Primary Goals
1. **Activate intelligent automation** — use AI agents to inspect, build, modify, and test the codebase
2. **Maintain the repository as source of truth** — all changes flow through version control
3. **Enable AI-driven iteration** — run tests, identify failures, fix issues automatically
4. **Eliminate manual overhead** — minimize hand-building; maximize AI reasoning and implementation

## How to Work with this Repo
- **Inspect first** — understand the current structure before proposing changes
- **Build systematically** — create features with tests, not just skeleton code
- **Validate continuously** — run the test suite after each meaningful change
- **Keep it documented** — maintain README, architecture notes, and inline comments
- **Commit incrementally** — each logical change gets a descriptive commit

## AI Agent Responsibilities
When working on Sage 2:
1. Read existing code and architecture
2. Propose changes with rationale
3. Implement changes atomically
4. Run and verify tests
5. Fix failing tests immediately
6. Commit with clear messages

## No Manual Placeholders
Do not create empty files or stub structures waiting for manual completion. Build complete, tested, working code.

## Canonical C2 HUD Presentation — LOCKED
The C2 HUD is a governed presentation contract, not an area for agent interpretation or redesign.

- **Hub A:** C2 Mission Control HUD / Four-Layer Operating Board.
- **Hub B:** SAGE Organism / Agent Projection. This is the progression/organism surface; do not create or resurrect a separate "XP HUD".
- The canonical visible HUD layers are exactly: `01 — COMMAND BAND`, `02 — OPERATING PICTURE`, `03 — PROGRESSION / IMPACT`, `04 — STRIKE FEED // HIGH-TEMPO EVENTS`, then `05 — ORGANISM PROGRESSION`.
- Preserve the canonical structured renderer in `sage/experimental/airspace/renderer.py`, `sage/experimental/airspace/immersion.py`, and the C2 presentation boundary. Do not substitute another ASCII dashboard, boxed dashboard, report table, generic agent HUD, or legacy HUD.
- Jules reports, pasted Markdown, archived text, and chat transport are claims/transport only. They are never the canonical HUD surface.
- When immersion or a Hub is requested, reconstruct the canonical Hub from governed runtime state. Do not fall back to remembered or invented HUDs when live state is unavailable; fail closed or explicitly report the missing verification capability.
- Fresh sessions must rehydrate from repository/runtime truth rather than resurrecting historical HUD designs from conversation memory.
- Do not add another HUD renderer or presentation authority. If an existing alternate HUD is discovered, audit its consumers and remove it rather than maintaining competing presentation paths.
- Any change to the locked HUD layout requires explicit operator authorization before implementation.

## Success Criteria
- ✅ AI agents can clone, inspect, and understand the repo
- ✅ Automated tests run and pass
- ✅ Features are built and verified by CI/CD
- ✅ The codebase evolves through AI-assisted reasoning, not copy/paste
- ✅ C2 HUD presentation remains bound to the canonical dual-hub contract across sessions and agents

---

**Status:** Baseline repository established. Ready for AI-assisted development.
