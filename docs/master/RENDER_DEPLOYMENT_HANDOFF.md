# SAGE RUNTIME RENDER DEPLOYMENT HANDOFF SPECIFICATION

This document provides the definitive, production-ready **Render Deployment Handoff Specification** for the **SAGE Autonomous Continuity Runtime**.

As no direct Render API connection is active within the automated sandbox, follow these structured instructions to deploy SAGE directly on Render using the repository's native production-grade configuration.

---

## 1. Core Deployment Settings

| Parameter | Recommended Value / Setting | Description |
| :--- | :--- | :--- |
| **Service Type** | `Web Service` | To host the FastAPI REST API. |
| **Language / Environment**| `Python` | Optimized python environment with PEP 621 pyproject.toml support. |
| **Region** | `Oregon (US West)` (or your preferred region) | Deploy closest to your target users/services. |
| **Branch** | `main` | The stable production-ready branch. |
| **Plan** | `Free` | Highly compatible with Render's Free tier. |
| **Health Check Path** | `/health` | Informs Render's load balancer of container status. |

---

## 2. Repository Configuration

* **Canonical Repository URL:** `https://github.com/dariusbrandon880-art/Sage`
* **Root Directory:** `./` (Repository root)

---

## 3. Storage Setup
To support Render's Free Tier completely without requiring paid, disk-mounted resources, the runtime uses stateless in-memory backends.

* **Disk Storage:** None (No paid disk mounts required).
* **InMemory Configuration:** Ensure `MEMORY_BACKEND` and `ARCHIVE_BACKEND` are set to `in-memory`.
* **Configuration Sync:** Ensure `GOOGLE_WORKSPACE_CREDENTIALS_PATH` is configured as `.sage/credentials.json`.

---

## 4. Build and Start Commands

Because we use the native **Python** environment with pyproject.toml:
* **Build Command:** Overrides the default requirements.txt command to install packages using SAGE's PEP 621 packaging:
  ```bash
  pip install --upgrade pip && pip install .
  ```
* **Start Command:** Runs SAGE's FastAPI app using uvicorn:
  ```bash
  uvicorn sage.api:app --host 0.0.0.0 --port 8000
  ```
* **Port Mapping:** Port `8000` is exposed. Render automatically routes public HTTPS traffic (port 443) to internal port `8000` if configured.

---

## 5. Required Environment Variables

Configure the following variables in the **Environment** tab of your Render service dashboard:

| Variable Name | Value | Description |
| :--- | :--- | :--- |
| **`ENV`** | `production` | Sets the runtime to production mode. |
| **`DEBUG`** | `false` | Disables debugging logs and endpoints. |
| **`PORT`** | `8000` | Port matching SAGE’s exposure. |
| **`HOST`** | `0.0.0.0` | Bind host address. |
| **`SAGE_REQUIRE_AUTH`** | `true` | Enforces `x-api-key` header verification. |
| **`SAGE_API_KEYS`** | *[Click "Generate Value" or insert secret]* | Secret API token(s) used for Custom GPT & API auth. |
| **`MEMORY_BACKEND`** | `in-memory` | Enables in-memory stateless persistence. |
| **`ARCHIVE_BACKEND`** | `in-memory` | Enables in-memory historical event logging. |
| **`ENABLE_CONTINUITY`** | `true` | Activates autonomous workspace capturing. |
| **`GOOGLE_WORKSPACE_CREDENTIALS_PATH`** | `.sage/credentials.json` | Stores OAuth secrets on the local repo directory. |
| **`GITHUB_WEBHOOK_SECRET`** | *[Insert secure secret]* | HMAC validation key for raw GitHub events. |
| **`GEMINI_API_KEY`** | *[Insert Gemini API Key]* | API key for Gemini / Jules reasoning loops. |

---

## 6. Blueprint Deployment (Declarative YAML)

SAGE provides a pre-configured `render.yaml` Blueprint specification at the repository root. You can deploy this service instantly via **Render Blueprints**:

1. Log in to your [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** and select **Blueprint**.
3. Connect your GitHub repository (`dariusbrandon880-art/Sage`).
4. Render will automatically parse `render.yaml` and prompt you to confirm the creation of the **`sage-runtime`** web service.
5. Click **Approve** to initiate build.

---

## 7. Manual Authorization & Live Verification Steps

Once the web service is deployed successfully, follow these final validation steps:

### Step 7.1: Verify Server Health
Query the public endpoint to verify that the container is active and responding:
```bash
curl -f https://your-sage-service.onrender.com/health
# Expected Output: {"status":"healthy","runtime":"active"}
```

### Step 7.2: Google Workspace Sync Dry-Run
Since in-memory mode is stateless, you can verify Workspace Sync integrity using dry-run diagnostics on startup:
```bash
python3 -c "from sage.api import workspace_sync_mgr; workspace_sync_mgr.sync_to_google_workspace('.sage/credentials.json')"
```
This is fully supported on Render's Free tier.
