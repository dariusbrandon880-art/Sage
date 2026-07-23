# SAGE 2 CONNECTOR ACTIVATION PACK

This document serves as the **SAGE 2 Connector Activation Pack**, providing the definitive, operational schemas, authentication criteria, endpoint references, and readiness checklists for all active and integrated connectors of the **SAGE Autonomous Continuity Runtime**.

---

## 1. OpenAI / ChatGPT Action Integration

### 1.1. Purpose Definition
Enables custom or team ChatGPT instances to query SAGE's live runtime state, extract historical engineering decisions, retrieve validated memories, and ingest session payloads directly into the runtime's single-transaction ingestion loop.

### 1.2. Required Environment Variables
* **`SAGE_REQUIRE_AUTH`**: Must be set to `true` to protect endpoints.
* **`SAGE_API_KEYS`**: Secret key(s) generated on the server to authorize the Custom GPT client's requests.

### 1.3. Authentication Method
* **Type**: Header-based API Key.
* **Header Name**: `x-api-key`
* **Authorization Scheme**: Strict matching against configured `SAGE_API_KEYS`.

### 1.4. Endpoint / Configuration Reference
* **Main Fetch Endpoint**: `GET /system-frame`
* **Ingestion Endpoint**: `POST /ingest`
* **OpenAPI 3.0 Specification**: Located at `docs/master/CUSTOM_GPT_OPENAPI_SCHEMA.json`.
* **Server Target URL**: `https://sage-runtime.onrender.com`

### 1.5. Activation Checklist
* [ ] Verify Render web service is hosting SAGE with `SAGE_REQUIRE_AUTH=true`.
* [ ] Configure unique, strong random secret in `SAGE_API_KEYS` on Render dashboard.
* [ ] Copy the JSON contents of `docs/master/CUSTOM_GPT_OPENAPI_SCHEMA.json`.
* [ ] Open ChatGPT Custom GPT Builder ➔ Actions.
* [ ] Paste the OpenAPI schema, replacing the `servers.url` parameter with your secure live URL (e.g., `https://sage-runtime.onrender.com`).
* [ ] Choose **API Key** under Custom Action Authentication, setting Type to **Custom**, Header Name to `x-api-key`, and value to match `SAGE_API_KEYS`.
* [ ] Perform handshake check by typing "Get current SAGE status" in the builder preview pane.

### 1.6. Current Status
* **Status**: **READY**
* **Verification**: Fully covered via `tests/test_api_auth.py` and the E2E cross-platform continuity proof.

---

## 2. Google AI / Gemini & Jules Integration

### 2.1. Purpose Definition
Enables deep local reasoning and multi-turn agent cycles using Gemini/Jules to sync code execution, execute self-verification sweeps, and automatically persist conversation transcripts/outcomes back to SAGE's memory layer.

### 2.2. Required Environment Variables
* **`GEMINI_API_KEY`**: Active Google AI Studio API key.

### 2.3. Authentication Method
* **Type**: Direct HTTPS REST header parameter authorization.
* **Header Parameter**: Passed directly to Google's `generativelanguage` endpoints.
* **Local Boundary**: Managed securely inside `GeminiJulesClient` configuration.

### 2.4. Endpoint / Configuration Reference
* **Query Endpoint**: `POST /ai/query/gemini-jules`
* **Context Retrieval**: `GET /ai/context?prompt={query}`
* **Underlying Model**: Google Gemini Pro (or Gemini Flash fallback).

### 2.5. Activation Checklist
* [ ] Obtain a valid API Key from Google AI Studio.
* [ ] Configure the `GEMINI_API_KEY` environment variable in the Render dashboard.
* [ ] Run `python scripts/production_check.py` to confirm the key is registered.
* [ ] Call `POST /ai/query/gemini-jules` with a trial prompt to verify connection.

### 2.6. Current Status
* **Status**: **READY**
* **Verification**: Verified via `tests/test_phase2_activation.py` and `tests/test_runtime_intelligence.py` capability discovery.

---

## 3. GitHub Webhook Integration

### 3.1. Purpose Definition
Ingests repository events (pushes, pull requests, releases, and CI/CD runs) in real time to automatically build SAGE session timelines, preserve code lineage, and record decisions tied directly to commit hashes.

### 3.2. Required Environment Variables
* **`GITHUB_WEBHOOK_SECRET`**: HMAC token string shared between GitHub and the SAGE server.

### 3.3. Authentication Method
* **Type**: Secure SHA-256 HMAC Signature Verification.
* **Header Name**: `X-Hub-Signature-256`
* **Security Guard**: Timing-attack safe comparison via `hmac.compare_digest`.

### 3.4. Endpoint / Configuration Reference
* **Webhook URL Path**: `POST /tools/github/event`
* **Supported Payload Modes**: Handles both raw GitHub Webhook JSON structures and standardized `GitHubEvent` schemas.

### 3.5. Activation Checklist
* [ ] Generate a secure SHA-256 secret (e.g., `openssl rand -hex 24`).
* [ ] Add this secret to the `GITHUB_WEBHOOK_SECRET` variable in the Render environment settings.
* [ ] Go to GitHub Repository Settings ➔ Webhooks ➔ Add webhook.
* [ ] Set Payload URL to `https://your-sage-service.onrender.com/tools/github/event`.
* [ ] Set Content Type to `application/json`.
* [ ] Paste the generated secret in the **Secret** field.
* [ ] Choose individual event triggers: "Pushes", "Pull requests", "Releases".
* [ ] Save the webhook and trigger a test payload from GitHub.

### 3.6. Current Status
* **Status**: **READY**
* **Verification**: Verified via signature-matching unit tests in `tests/test_phase2_activation.py`.

---

## 4. Google Workspace OAuth Integration

### 4.1. Purpose Definition
Enables headless, automated mirroring of repository state (master snapshots, roadmap specs, active sprints, and session timelines) into Google Docs and Google Sheets, facilitating cross-platform visibility and continuous synchronization.

### 4.2. Required Environment Variables
* **`GOOGLE_WORKSPACE_CREDENTIALS_PATH`**: Path to the client secrets file (defaults to `.sage/credentials.json`).

### 4.3. Authentication Method
* **Type**: Headless Google OAuth 2.0.
* **Scope Criteria**:
  * `https://www.googleapis.com/auth/documents`
  * `https://www.googleapis.com/auth/spreadsheets`
  * `https://www.googleapis.com/auth/drive.file`
* **Token Storage**: Serialized credential token stored locally in `.sage/token.json` for persistent headless refresh.

### 4.4. Endpoint / Configuration Reference
* **Manual Sync / Status Endpoint**: `POST /tools/workspace/sync`
* **Credentials Target File**: `.sage/credentials.json`

### 4.5. Activation Checklist
* [ ] Create a GCP Project and enable Drive, Docs, and Sheets APIs.
* [ ] Configure OAuth consent screen to "External" (or "Internal") and authorize test scopes.
* [ ] Generate and download a Desktop Application OAuth client secret JSON.
* [ ] Rename this file to `credentials.json` and upload it to the `.sage/` directory on your server.
* [ ] Run the initial manual sync from the server terminal:
  `python -c "from sage.api import workspace_sync_mgr; workspace_sync_mgr.sync_to_google_workspace('.sage/credentials.json')"`
* [ ] Copy the printed authorization URL, authenticate via browser, and paste the code back to generate `.sage/token.json`.
* [ ] Test the integration headlessly by making a POST request to `/tools/workspace/sync`.

### 4.6. Current Status
* **Status**: **READY (Dry-Run)**
* **Verification**: Tested extensively under `tests/test_continuity_bridge.py` and `tests/test_phase2_activation.py` using fallback mock diagnostics.
