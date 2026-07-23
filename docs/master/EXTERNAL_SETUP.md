# SAGE Live External Connectors & Activation Specification

This document details the exhaustive audit, technical specifications, and configuration instructions required to transition SAGE (Autonomous Continuity Runtime) from repository-operational state into fully activated live engineering status.

SAGE is designed to run in a secured live environment, bridging local state persistence with external AI, code repositories, and workspace productivity systems.

---

## 1. Live Integration Audit

| Connection Endpoint | Protocol / Flow | Auth Mechanism | Current Readiness | Target Live State |
| :--- | :--- | :--- | :--- | :--- |
| **OpenAI Custom GPT Actions** | REST HTTP HTTPS | Header `x-api-key` (Bearer / Custom) | **Ready**. Schema provided in Sec 2. | Connected to public HTTPS Gateway |
| **Gemini / Jules Connector** | REST Endpoint | Secure API Key + Local SDK routing | **Ready**. Handled via local query / ingest. | Direct automated multiline reasoning sync |
| **GitHub Webhook Listener** | HTTP POST Webhook | `X-Hub-Signature-256` (HMAC-SHA256) | **Ready**. Signature validation built-in. | Automatic ingestion of PRs & commits |
| **Google Workspace Sync** | OAuth 2.0 Web flow | `credentials.json` Client Secret / Access Token | **Ready**. Features auto-dryrun fallback. | Live mirroring of State Docs to Docs/Sheets |
| **HTTPS API Gateway** | ASGI HTTPS Port 8000 | Reverse-proxy (Nginx / Caddy) + SSL certs | **Ready**. Docker/Uvicorn config ready. | Hosted on public domain with Let's Encrypt |

---

## 2. OpenAI Custom GPT Action Setup & OpenAPI 3.0 Schema

An OpenAI Custom GPT Action allows standard or custom ChatGPT instances to interact directly with SAGE's persistent state. When configured, ChatGPT becomes a co-developer that can read active tasks, suggest architecture modifications, record decisions, and promote memories to the master archive.

### 2.1 Configuration Steps
1. Navigate to [ChatGPT custom GPT builder](https://chatgpt.com/gpts/editor).
2. Create or select your custom SAGE Assistant GPT.
3. Scroll down and click **Configure**, then click **Create new action**.
4. In the **Schema** input, paste the OpenAPI 3.0 YAML/JSON specification provided below.
5. In the **Authentication** section:
   - Select **API Key**.
   - Set Auth type to **Custom** or **Bearer**.
   - Set Header Name to `x-api-key`.
   - Paste one of the valid keys configured in your `SAGE_API_KEYS` environment variable.
6. Under **Privacy Policy**, specify your secure URL or placeholder.

### 2.2 SAGE OpenAPI 3.0 Specification (YAML)
Paste this exact YAML schema into the ChatGPT Action configuration:

```yaml
openapi: 3.0.0
info:
  title: SAGE Autonomous Continuity API
  description: API gateway for SAGE ACR (Autonomous Continuity Runtime) enabling persistent state, validated knowledge lineage, decision tracking, and memory ingestion.
  version: 1.0.0
servers:
  - url: https://your-sage-domain.com
    description: Production Live Gateway
paths:
  /status:
    get:
      summary: Get active runtime status
      description: Returns SAGE's status, active task, current objective, blockers, and database metrics.
      operationId: getStatus
      responses:
        '200':
          description: Successful status retrieval
          content:
            application/json:
              schema:
                type: object
                properties:
                  active:
                    type: boolean
                  current_objective:
                    type: string
                  active_task:
                    type: string
                  blockers:
                    type: array
                    items:
                      type: string
                  dependencies:
                    type: array
                    items:
                      type: string
                  memory_count:
                    type: integer
                  archive_count:
                    type: integer
                  decision_count:
                    type: integer
                  session_depth:
                    type: integer

  /ingest:
    post:
      summary: Ingest external session payload
      description: Single authoritative pathway to load sessions, validate memories, track decisions, route archived entries, and checkpoint state.
      operationId: ingestPayload
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ExternalSessionPayload'
      responses:
        '200':
          description: Ingestion and checkpoint successful
          content:
            application/json:
              schema:
                type: object
                properties:
                  session_id:
                    type: string
                  checkpoint_id:
                    type: string
                  snapshot_id:
                    type: string
                  status:
                    type: string

  /reason:
    get:
      summary: Reason over continuity state
      description: Examines stored state, active context, memory and decisions to provide aligned suggestions and flag unsupported architectural choices.
      operationId: reasonOverContinuity
      responses:
        '200':
          description: Continuity suggestions successfully computed
          content:
            application/json:
              schema:
                type: object

  /verify:
    get:
      summary: Run self-verification checks
      description: Audits data integrity, disk storage, file systems, and lineage referential consistency.
      operationId: verifyIntegrity
      responses:
        '200':
          description: Integrity report successfully computed
          content:
            application/json:
              schema:
                type: object

  /objective:
    post:
      summary: Set active objective
      description: Configures the system-wide active objective and registers a new session branch.
      operationId: setObjective
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - objective
              properties:
                objective:
                  type: string
      responses:
        '200':
          description: Objective successfully set

  /task:
    post:
      summary: Set active task
      description: Sets the current active engineering task under the active objective.
      operationId: setTask
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - task
              properties:
                task:
                  type: string
      responses:
        '200':
          description: Task successfully set

components:
  schemas:
    ExternalSessionPayload:
      type: object
      required:
        - objective
      properties:
        session_id:
          type: string
          description: Optional persistent session tracking ID.
        objective:
          type: string
          description: The high-level guiding objective.
        task:
          type: string
          description: The active task description.
        memories:
          type: array
          items:
            $ref: '#/components/schemas/MemoryInput'
        decisions:
          type: array
          items:
            $ref: '#/components/schemas/DecisionInput'
    MemoryInput:
      type: object
      required:
        - id
        - object_type
        - content
      properties:
        id:
          type: string
        object_type:
          type: string
          enum: [fact, rule, report, architectural_spec, general]
        content:
          type: object
        tags:
          type: array
          items:
            type: string
        confidence:
          type: string
          enum: [hypothesis, validated, archived]
    DecisionInput:
      type: object
      required:
        - id
        - decision_type
        - description
        - rationale
      properties:
        id:
          type: string
        decision_type:
          type: string
          enum: [architectural, technical, organizational, process]
        description:
          type: string
        rationale:
          type: string
        evidence:
          type: array
          items:
            type: string
          description: List of memory IDs supporting this decision.
```

---

## 3. Google Workspace OAuth & Sync Activation

SAGE mirrors canonical engineering markdown documents (e.g. Master Snapshot, roadmaps, sprint status) directly into Google Docs and Google Sheets.

### 3.1 OAuth Scope Registry
Google API operations require authorization with these exact scopes:
1. `https://www.googleapis.com/auth/documents` (Full read/write permissions for Google Docs)
2. `https://www.googleapis.com/auth/spreadsheets` (Full read/write permissions for Google Sheets)
3. `https://www.googleapis.com/auth/drive.file` (Required to create, locate, and structure Google Drive files)

### 3.2 Google Cloud Project Setup Guide
Follow these steps to obtain the exact required credentials file:
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project called `SAGE-Continuity`.
3. In the left-hand menu, navigate to **APIs & Services** > **Library**. Search for and enable:
   - **Google Drive API**
   - **Google Docs API**
   - **Google Sheets API**
4. Navigate to **APIs & Services** > **OAuth consent screen**:
   - Choose **External** (or **Internal** if within an organization workspace).
   - Fill in system info (AppName: `SAGE Runtime`).
   - Under **Scopes**, manually add the three scopes listed above.
   - Under **Test Users**, add your personal Google account email.
5. Navigate to **APIs & Services** > **Credentials**:
   - Click **+ Create Credentials** and select **OAuth client ID**.
   - Select **Desktop Application** as the application type.
   - Name it `SAGE Desktop Client`.
   - Click **Create**, then download the client secrets JSON.
6. Rename this file to `credentials.json` and place it under SAGE's persistent state directory:
   - Target location: `.sage/credentials.json`
7. Ensure that `google-api-python-client` and `google-auth-oauthlib` are installed in your runtime container.

When the REST endpoint `POST /tools/workspace/sync` is called, SAGE will detect `.sage/credentials.json` and initialize the standard OAuth Web authorization loop, persisting the resulting `token.json` under `.sage/` for subsequent automated headless synchronization.

---

## 4. GitHub Webhooks Integration

Live webhooks enable SAGE to track repository activity (such as pull requests, commits, and releases) directly into active memory.

### 4.1 Listener Configuration Steps
1. Navigate to your GitHub repository on github.com.
2. Go to **Settings** > **Webhooks** > **Add webhook**.
3. Set **Payload URL** to: `https://your-sage-domain.com/tools/github/event`
4. Set **Content type** to: `application/json`
5. Under **Secret**, enter a secure random passphrase (this will be your `GITHUB_WEBHOOK_SECRET`).
6. Under "Which events would you like to trigger this webhook?", choose:
   - Let me select individual events: **Pushes**, **Pull requests**, and **Releases**.
7. Click **Add webhook**.

### 4.2 Signature Security & Signature Validation
To prevent spoofing, SAGE validates all incoming GitHub events using the HMAC-SHA256 protocol. The signature passed in the `X-Hub-Signature-256` header must match SAGE's locally calculated signature using the `GITHUB_WEBHOOK_SECRET`.

---

## 5. Gemini / Jules Connector Activation

Gemini and Jules agents sync directly with SAGE using secure API keys and local integration layers. SAGE exposes dedicated connectors that format reasoning inputs, retrieve context from active state, and post turn transactions into the unified database.

### 5.1 Activation Steps
1. Provision a Gemini API Key from Google AI Studio.
2. Configure `GEMINI_API_KEY` inside `.env`.
3. Set `SAGE_API_KEYS` to include your secure agent token.
4. Execute queries against `/ai/query/gemini-jules` to sync agent steps directly to the SAGE single-transaction ingest loop.

---

## 6. Secure HTTPS Deployment Guide

SAGE must be hosted behind a reverse proxy using HTTPS/SSL to secure API key headers and payload transmissions.

### 6.1 Unified Docker Hosting
Deploy SAGE instantly using our verified `docker-compose.yml` and `Dockerfile` templates.

### 6.2 Reverse Proxy Configuration (Nginx)
Configure Nginx with automated Let's Encrypt certificates to terminate SSL and route requests to SAGE's local port `8000`:

```nginx
server {
    listen 80;
    server_name your-sage-domain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-sage-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-sage-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-sage-domain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
