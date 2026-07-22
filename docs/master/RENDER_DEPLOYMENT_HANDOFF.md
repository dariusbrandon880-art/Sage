# SAGE RUNTIME RENDER DEPLOYMENT HANDOFF SPECIFICATION

This document provides the definitive, production-ready **Render Deployment Handoff Specification** for the **SAGE Autonomous Continuity Runtime**.

As no direct Render API connection is active within the automated sandbox, follow these structured instructions to deploy SAGE directly on Render using the repository's native production-grade configuration.

---

## 1. Core Deployment Settings

| Parameter | Recommended Value / Setting | Description |
| :--- | :--- | :--- |
| **Service Type** | `Web Service` | To host the FastAPI REST API. |
| **Language / Environment**| `Docker` | Leverages SAGE's optimized multi-stage `Dockerfile`. |
| **Region** | `Oregon (US West)` (or your preferred region) | Deploy closest to your target users/services. |
| **Branch** | `main` | The stable production-ready branch. |
| **Plan** | `Free` (Standard free tier) | Zero cost tier. |
| **Health Check Path** | `/health` | Informs Render's load balancer of container status. |

---

## 2. Free Tier vs Paid Tier Tradeoffs

### 2.1 Free Tier (Default Configuration)
* **Cost:** $0.00/month.
* **Storage:** Ephemeral (in-memory backend).
* **State Loss:** SAGE states, memories, active sessions, and checkpoints will be **lost on container restarts, idle sleep cycles, and redeployments**.
* **Configuration:** `MEMORY_BACKEND=in-memory` and `ARCHIVE_BACKEND=in-memory`.
* **Use Case:** Suitable for development, testing, staging, and lightweight ephemeral pipelines.

### 2.2 Paid Tier (Durable Execution)
* **Cost:** Starting from $7.00/month (Starter Web Service) + $2.50/month (10GB Persistent Disk volume). Total: **$9.50/month**.
* **Storage:** Durable (persistent disk attached at `/app/sage_data`).
* **State Loss:** State is **permanently preserved** across redeployments, restarts, and server reboot cycles.
* **Configuration:** Change `MEMORY_BACKEND=disk`, `ARCHIVE_BACKEND=disk`, and attach a persistent disk volume named `sage-data` in your Render service or Blueprint settings.
* **Use Case:** Recommended for actual production use where state continuity is required.

---

## 3. Repository Configuration

* **Canonical Repository URL:** `https://github.com/dariusbrandon880-art/Sage`
* **Root Directory:** `./` (Repository root)
* **Dockerfile Path:** `Dockerfile`

---

## 4. Build and Start Commands

Because we use the native **Docker** environment:
* **Build Command:** Handled automatically by Render using the repo's `Dockerfile`.
* **Start Command:** Handled automatically by the `CMD` instruction inside the `Dockerfile`:
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
| **`MEMORY_BACKEND`** | `in-memory` | Enables in-memory state store (defaults to `in-memory` for free tier, change to `disk` for paid tier). |
| **`ARCHIVE_BACKEND`** | `in-memory` | Enables in-memory archive store (defaults to `in-memory` for free tier, change to `disk` for paid tier). |
| **`ENABLE_CONTINUITY`** | `true` | Activates autonomous workspace capturing. |
| **`GOOGLE_WORKSPACE_CREDENTIALS_PATH`** | `sage_data/credentials.json` | Stores OAuth secrets path. |
| **`GITHUB_WEBHOOK_SECRET`** | *[Insert secure secret]* | HMAC validation key for raw GitHub events. |
| **`GEMINI_API_KEY`** | *[Insert Gemini API Key]* | API key for Gemini / Jules reasoning loops. |

---

## 6. Blueprint Deployment (Declarative YAML)

SAGE provides a pre-configured, free-tier compatible `render.yaml` Blueprint specification at the repository root. You can deploy this service instantly via **Render Blueprints**:

1. Log in to your [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** and select **Blueprint**.
3. Connect your GitHub repository (`dariusbrandon880-art/Sage`).
4. Render will automatically parse `render.yaml` and prompt you to confirm the creation of the **`sage-runtime`** web service on the **Free** plan.
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

### Step 7.2: Workspace Authorization Flow (If using Google Workspace sync)
To complete the initial OAuth loop headlessly on Render:
1. Log into your Render dashboard, find your `sage-runtime` service, and open the **Shell** tab.
2. Ensure you have uploaded your GCP `credentials.json` file to `/app/sage_data/credentials.json` (you can place this file directly or trigger it via volume mounts). Note: on the Free plan, files written here are ephemeral and will be lost when the container restarts.
3. Run the initial interactive authorization command:
   ```bash
   python3 -c "from sage.api import workspace_sync_mgr; workspace_sync_mgr.sync_to_google_workspace('sage_data/credentials.json')"
   ```
4. Copy the generated Google login URL from the logs, paste it into your browser, accept scopes, and authorize the SAGE app.
5. SAGE will write `token.json` directly into `sage_data/`. On the Free plan, subsequent scheduled syncs will run completely headlessly within the current container lifecycle. For persistent token storage, upgrade to a Paid tier with a persistent disk volume.
