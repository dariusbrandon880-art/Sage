# Bidirectional Traceable Query Integration (BTQI) Spec

Bidirectional Traceable Query Integration ensures that conversational context from AI models is tightly coupled with structured repository-side databases.

## 1. Concept Overview
ChatGPT or Gemini reasoning queries typically exist as transient chat logs. BTQI turns conversations into persistent data:
- Captures query parameters, prompts, and response strings.
- Traces precisely which active memories or Master Archive entries were read during the LLM's reasoning phase.
- Stores this mapping as an immutable lineage link inside the SAGE database.

## 2. Dynamic Reasoning History
By logging the AI's step-by-step logic history, future agents can read the exact historical sequence of reasoning that led to a specific code modification, establishing total transparency and auditability.
