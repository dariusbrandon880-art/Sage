# SAGE Live External Connectors & Activation Specification

This document details the exhaustive audit, technical specifications, and configuration instructions required to transition SAGE (Autonomous Continuity Runtime) from repository-operational state into fully activated live engineering status.

SAGE is designed to run in a secured live environment, bridging local state persistence with external AI, code repositories, and workspace productivity systems.

---

## 1. Live Integration Audit

| Connection Endpoint | Protocol / Flow | Auth Mechanism | Current Readiness | Target Live State |
| :--- | :--- | :--- | :--- | :--- |
| **SAGE System Frame** | GET HTTP HTTPS | Header `x-api-key` | **Fully Activated**. Exposed at `/system-frame`. | Live status, snapshotted context, and connector registry feed |
| **OpenAI Custom GPT Actions** | REST HTTP HTTPS | Header `x-api-key` (Bearer / Custom) | **Fully Activated**. Schema provided in Sec 2. | Connected to public HTTPS Gateway |
| **Gemini / Jules Connector** | REST Endpoint | Secure API Key + Local SDK / REST routing | **Fully Activated**. Native REST API integrated with error boundaries. | Direct automated multiline reasoning sync |
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

### 2.2 SAGE OpenAPI 3.0 Specification (JSON)
SAGE hosts a pre-configured OpenAPI 3.0 action schema at `docs/master/CUSTOM_GPT_OPENAPI_SCHEMA.json`. You can paste the JSON structure directly:

```json
{
  "openapi": "3.0.0",
  "info": {
    "title": "SAGE Autonomous Continuity Runtime API",
    "description": "API schema for SAGE Actions in ChatGPT Custom GPTs. Allows secure system context retrieval and ingestion of continuity states.",
    "version": "1.1.0"
  },
  "servers": [
    {
      "url": "https://sage-runtime.onrender.com",
      "description": "Production SAGE Server"
    }
  ],
  "paths": {
    "/system-frame": {
      "get": {
        "summary": "Retrieve complete SAGE Operational Context",
        "description": "Provides a read-only snapshot of current SAGE status, milestones, active tasks, blockers, and connector states.",
        "operationId": "getSystemFrame",
        "responses": {
          "200": {
            "description": "Successful retrieval of SAGE Context Frame",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "runtime_status": {"type": "string"},
                    "master_snapshot_markdown": {"type": "string"},
                    "session_state_markdown": {"type": "string"},
                    "current_milestone": {"type": "string"},
                    "active_task": {"type": "string"},
                    "blockers": {"type": "array", "items": {"type": "string"}},
                    "validated_architecture_summary": {"type": "object"},
                    "connectors": {"type": "array", "items": {"type": "object"}},
                    "runtime_health": {"type": "object"}
                  }
                }
              }
            }
          }
        }
      }
    },
    "/ingest": {
      "post": {
        "summary": "Ingest Session Payload into SAGE Continuity Bridge",
        "description": "Saves active engineering tasks, context, validated memories, and technical decisions under a unified single-transaction workflow.",
        "operationId": "ingestPayload",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/ExternalSessionPayload"
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Payload successfully ingested",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "session_id": {"type": "string"},
                    "checkpoint_id": {"type": "string"},
                    "snapshot_id": {"type": "string"}
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
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

## 5. Google AI / Gemini / Jules Activation

Gemini and Jules agents sync directly with SAGE using secure API keys and local integration layers. SAGE exposes dedicated connectors that format reasoning inputs, retrieve context from active state, and post turn transactions into the unified database.

### 5.1 Activation Steps
1. Provision a Gemini API Key from Google AI Studio.
2. Configure `GEMINI_API_KEY` inside `.env` or your Render environment variables.
3. Set `SAGE_API_KEYS` to include your secure agent token.
4. Execute queries against `/ai/query/gemini-jules` to sync agent steps directly to the SAGE single-transaction ingest loop.

### 5.2 Optional Vertex AI Integration
SAGE is fully prepared to support future Google Cloud Vertex AI integrations. Moving from Google AI Studio (Gemini SDK) to Enterprise Vertex AI can be achieved cleanly by updating your credentials to point to your Google Cloud Service Account keyfile and invoking the GCP Vertex AI client libraries:
- Required scopes: `https://www.googleapis.com/auth/cloud-platform`
- Package target: `google-cloud-aiplatform`

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
