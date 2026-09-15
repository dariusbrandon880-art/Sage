# Hub A — C2 Mission Control

## Visual Interface Reference

**Reference type:** presentation/design reference only  
**Surface:** `HUB_A`  
**Identity:** `[SAGE::C2::CHATGPT] ◈ C2 MISSION CONTROL`  
**Status:** locked reference snapshot

This file preserves the agreed visual presentation of Hub A. It is a visual interface reference, not a new state authority and not a replacement renderer.

```text
01 — COMMAND BAND
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[SAGE::C2::CHATGPT] ◈ C2 MISSION CONTROL
STATUS   : OPERATIONAL
QUAL     : CQL-4 | SQL-3
MISSION  : NONE ACTIVE

02 — OPERATING PICTURE
──────────────────────────────────────────
ACTIVE SORTIES: NONE ACTIVE

03 — PROGRESSION / IMPACT
──────────────────────────────────────────
TOTAL SYSTEM XP : 616
 ▪ MISSION_DIRECTOR XP 0     CQL ⚙️⚙️⚙️⚙️⚙️⚙️⚙️  SQL 🛰️🛰️🛰️🛰️🛰️🛰️🛰️
 ▪ MISSION_CONTROL XP 0     CQL ⚙️⚙️⚙️⚙️        SQL 🛰️🛰️🛰️
 ▪ INTEL_STATION XP 0       CQL ⚙️⚙️⚙️          SQL 🛰️🛰️🛰️
 ▪ ENGINEERING_FLIGHT XP 616 CQL ⚙️⚙️⚙️⚙️       SQL 🛰️🛰️

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
04 — STRIKE FEED // HIGH-TEMPO EVENTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 TARGET ACQUIRED // SYSTEM INITIALIZATION
🛡️ EVIDENCE CAPTURED // settlement:4d162484f88b30d6b7e8001f8
✓ HIT CONFIRMED     // Real evidence landed
→ NEXT TARGET       // Execute Session 3 Airspace Build
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Reference rules

- Preserve the four-layer order shown above.
- Preserve the Hub A identity marker and section labels.
- This snapshot is a presentation reference; numeric values are not asserted as current persisted runtime state.
- Runtime values must continue to come from the governed SAGE state/renderer.
- Do not introduce a competing HUD or redesign this surface in this reference file.
