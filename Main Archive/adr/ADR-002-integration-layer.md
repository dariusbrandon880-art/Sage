# ADR-002: SAGE Integration & Service Layers

- **Status**: APPROVED / ACTIVE
- **Date**: 2026-07-20
- **Deciders**: SAGE Development Team

---

## 1. Context
To make SAGE a practical development assistant, we need to bridge SAGE-ACR with external developer environments, including ChatGPT, Gemini, GitHub webhooks, and Google Workspace documentation.

---

## 2. Decision
We implement a decoupled Integration Layer (`sage/integration.py`) and Service Layer (`sage/service.py`):
1. **`LifecycleManager`**: Provides graceful server startup, shutdown, and health diagnostics.
2. **REST API Gateway**: Powered by FastAPI, exposing standardized endpoints for continuity tracking, memory querying, validation, and tool synchronization.
3. **`ChatGPTClient` / `GeminiJulesClient`**: Connectors that execute AI reasoning queries, dynamically retrieve contextual memories/archives matching the prompt, and track reasoning histories.
4. **`ToolIntegrationManager`**: Safely indexes incoming VCS metadata (`GitHubEvent`) and workspace documents (`GoogleWorkspaceArtifact`) into SAGE's short-term memory without duplicating existing external databases.

---

## 3. Consequences
- **Positive**: Standardized APIs allow any modern IDE, chat interface, or CI system to sync with SAGE. Zero duplication of external source databases.
- **Negative**: Adds secure token header management requirements (`SAGE_API_KEYS`) on lifecycle endpoints to prevent unauthorized remote shutdown.
