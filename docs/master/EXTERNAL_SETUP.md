# SAGE EXTERNAL INTERFACES & OAUTH SETUP GUIDE

This document defines the configuration layout, permissions, and custom integration setup instructions required to establish secure, automated continuity connections from ChatGPT, Gemini, GitHub, and Google Workspace to SAGE Runtime.

---

## 1. ChatGPT Custom Action Integration

To enable a custom engineering GPT to automatically interact with SAGE, you must register SAGE's REST API as an **Action**. SAGE secures all ingestion endpoints with strict `x-api-key` headers matching the environmental configuration of `SAGE_API_KEYS`.

### 1.1 OpenAPI 3.0 Action Schema
Copy and paste this OpenAPI spec into the ChatGPT Custom Action creator:

```json
{
  "openapi": "3.0.0",
  "info": {
    "title": "SAGE Continuity Bridge API",
    "description": "Exposes core SAGE memory and session continuity endpoints to preserve context autonomously.",
    "version": "1.0.0"
  },
  "servers": [
    {
      "url": "https://your-sage-domain.com",
      "description": "Hosted SAGE Runtime instance"
    }
  ],
  "paths": {
    "/ingest": {
      "post": {
        "summary": "Ingest Session Payload",
        "description": "Standardizes external ChatGPT session interactions directly into SAGERuntime's authoritative bridge pathway.",
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
            "description": "Successful ingestion and state checkpoint serialization"
          }
        }
      }
    },
    "/continuity/auto-capture": {
      "post": {
        "summary": "Auto-capture Local Git Session",
        "description": "Triggers an automated check of local modified files, active branches, and ADRs, committing them to the memory graph.",
        "operationId": "autoCaptureGitSession",
        "responses": {
          "200": {
            "description": "Git workspace successfully captured and serialized."
          }
        }
      }
    }
  },
  "components": {
    "schemas": {
      "ExternalSessionPayload": {
        "type": "object",
        "required": ["objective"],
        "properties": {
          "session_id": {
            "type": "string"
          },
          "objective": {
            "type": "string"
          },
          "task": {
            "type": "string"
          },
          "memories": {
            "type": "array",
            "items": {
              "type": "object"
            }
          },
          "decisions": {
            "type": "array",
            "items": {
              "type": "object"
            }
          }
        }
      }
    },
    "securitySchemes": {
      "ApiKeyAuth": {
        "type": "apiKey",
        "in": "header",
        "name": "x-api-key"
      }
    }
  },
  "security": [
    {
      "ApiKeyAuth": []
    }
  ]
}
```

### 1.2 Authentication Setup
1. In the ChatGPT Action configuration, choose **API Key** as the authentication type.
2. Select **Custom** or **Header** matching `x-api-key` as the parameter name.
3. Paste the valid key registered in SAGE's `settings.py` / `SAGE_API_KEYS` list.

---

## 2. Google Workspace Synchronization Setup

SAGE uses `GoogleWorkspaceSyncManager` to automatically mirror repository documentation files to Google Docs and status metrics to Google Sheets. If active cloud connections are disabled (due to credential absence), SAGE falls back gracefully to a dry-run diagnostic mode.

### 2.1 Required Scopes
The Google Cloud console project must authorize SAGE with the following scopes:
- `https://www.googleapis.com/auth/documents` (Create, edit, and read Google Docs)
- `https://www.googleapis.com/auth/spreadsheets` (Create, edit, and read Google Sheets)
- `https://www.googleapis.com/auth/drive.file` (Locate or create files within user-allocated space)

### 2.2 Local Activation
To immediately activate live synchronization:
1. Install required google packages:
   ```bash
   pip install google-api-python-client google-auth-oauthlib google-auth-httplib2
   ```
2. Download your OAuth 2.0 Client credentials file from your Google Cloud Console.
3. Save the JSON file in SAGE's directory, for example as `.sage/credentials.json`.
4. Trigger the synchronization via FastAPI:
   ```bash
   curl -X POST "http://localhost:8000/tools/workspace/sync?credentials_path=.sage/credentials.json"
   ```

---

## 3. GitHub Webhook Listener Setup

GitHub repository-side events are standard-mapped and received directly via `/tools/github/event`.

### 3.1 Webhook Registration
To stream live VCS events (commit push, pull request, releases):
1. In your GitHub repository, navigate to **Settings** -> **Webhooks** -> **Add Webhook**.
2. Set the payload URL to your hosted SAGE public API:
   `https://your-sage-domain.com/tools/github/event`
3. Select content type: `application/json`.
4. Choose the individual events option and tick: **Pushes**, **Pull requests**, and **Releases**.
5. Save. The SAGE Continuity Bridge will automatically capture event timelines and link commits to SAGE Decisions and Active Tasks.

---

## 4. Production Deployment & Port Setup

SAGE can be easily launched and maintained as a production server or within isolated container spaces.

### 4.1 Launching via Docker Compose
To run SAGE on port `8000` with automated persistent volumes, execute:
```bash
docker-compose up --build -d
```

### 4.2 Automated Pre-Flight Diagnostics
Before going live, execute the SAGE Activation and Production Readiness check:
```bash
python scripts/activate_runtime.py --dry-run
```
This script checks the port occupancy, environmental parameter configurations, verifies database storage directories, and runs local referential integrity diagnostics (`verify_integrity()`) to confirm 100% pre-flight correctness.

---

## 5. System Frame Endpoint Spec

The `/system-frame` GET endpoint provides an authorized way to serialize state documents (`docs/master/MASTER_SNAPSHOT.md` and `docs/master/SESSION_STATE.md`) in one structured, secure JSON payload.

- **Endpoint**: `GET /system-frame`
- **Headers Required**:
  - `x-api-key`: SAGE API authorization key.
- **JSON Response Structure**:
  ```json
  {
    "status": "success",
    "timestamp": "2026-07-22T22:00:00.000000",
    "master_snapshot": {
      "file_path": "docs/master/MASTER_SNAPSHOT.md",
      "content": "...",
      "character_count": 1234
    },
    "session_state": {
      "file_path": "docs/master/SESSION_STATE.md",
      "content": "...",
      "character_count": 567
    }
  }
  ```
