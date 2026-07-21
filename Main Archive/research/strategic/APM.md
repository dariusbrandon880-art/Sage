# Autonomous Process Monitor (APM) Spec

The Autonomous Process Monitor proactively measures development velocity, flags bottlenecks, and initiates self-healing cycles.

## 1. Concept Overview
The APM operates as a background supervisor inside the automation layer:
- **Velocity Metrics**: Tracks how long an objective or task remains in an active state.
- **Stall Detection**: Detects if no files are modified, no commits are logged, or no tests are run within a predefined timeout.
- **Proactive Checkpointing**: Automatically triggers a `checkpoint` of the current workspace state before initiating any major code generation task.

## 2. Recovery Workflow
If the APM detects that a process is blocked (e.g. repeated test failures), it logs a blocker entry, queries the memory layer for matching recovery solutions, and runs self-healing scripts.
