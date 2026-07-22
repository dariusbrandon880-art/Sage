# SAGE Implementation Roadmap - v2.0 & Beyond

This roadmap outlines concrete engineering milestones to transition SAGE into a live, connected production-ready continuity service.

---

## Phase 2: Live Integration Connectors (Active Implementation)

### 1. ChatGPT Custom Action Integration
- **Objective**: Deploy OpenAPI specs to let ChatGPT connect directly to local/remote SAGE.
- **Tasks**:
  - Export standard `openapi.json` from SAGE FastAPI app.
  - Test ChatGPT Custom GPT Action query routing with local tunnel (e.g. ngrok).

### 2. Google Drive Real-Time Syncer
- **Objective**: Automatically synchronize promoted `ArchiveEntry` nodes to a shared Google Drive.
- **Tasks**:
  - Configure Google Cloud OAuth Credentials.
  - Implement Drive API file creation helper within `sage/integration.py`.

### 3. Real-Time GitHub Webhook Server
- **Objective**: Ingest live repo pushes, pull requests, and status checks.
- **Tasks**:
  - Deploy SAGE in an always-on hosting environment.
  - Add signature-based validation (`x-hub-signature`) on `/tools/github/event` endpoint.
