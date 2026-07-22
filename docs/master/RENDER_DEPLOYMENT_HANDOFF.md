# SAGE RUNTIME RENDER DEPLOYMENT HANDOFF SPECIFICATION

This document provides the definitive, production-ready **Render Deployment Handoff Specification** for the **SAGE Autonomous Continuity Runtime**.

SAGE is configured for deployment directly on Render using its native, Poetry-compatible production setup.

---

## 1. Core Deployment Settings

| Parameter | Recommended Value / Setting | Description |
| :--- | :--- | :--- |
| **Service Type** | `Web Service` | To host the FastAPI REST API. |
| **Language / Environment**| `Python` | Native Python runtime with Poetry dependency management. |
| **Region** | `Oregon (US West)` (or your preferred region) | Deploy closest to your target users/services. |
| **Branch** | `main` | The stable production-ready branch. |
| **Plan** | `Free` (or higher) | Fully compatible with Render's free tier. |
| **Health Check Path** | `/health` | Informs Render's load balancer of container status. |

---

## 2. Repository Configuration

* **Canonical Repository URL:** `https://github.com/dariusbrandon880-art/Sage`
* **Root Directory:** `./` (Repository root)

---

## 3. Persistent Disk Setup (Optional)
SAGE defaults to stateful execution using file-based backends (`MEMORY_BACKEND=disk`, `ARCHIVE_BACKEND=disk`) if persistent storage is available. On the Render Free tier, it utilizes stateless in-memory backends (`MEMORY_BACKEND=in-memory`, `ARCHIVE_BACKEND=in-memory`). If upgrading to a paid tier with persistent disks:

* **Disk Name:** `sage-data`
* **Mount Path:** `/app/sage_data`
* **Size:** `10 GB`
* **Configuration Sync:** Ensure `GOOGLE_WORKSPACE_CREDENTIALS_PATH` is configured as `sage_data/credentials.json`.

---

## 4. Build and Start Commands

Because SAGE uses native **Poetry** package management:
* **Build Command:**
  ```bash
  pip install poetry && poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi --only main
  ```
* **Start Command:**
  ```bash
  python -m uvicorn sage.api:app --host 0.0.0.0 --port 8000
  ```
* **Port Mapping:** Port `8000` is exposed. Render automatically routes public HTTPS traffic (port 443) to internal port `8000`.

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
| **`MEMORY_BACKEND`** | `in-memory` (use `disk` on paid tier) | State persistence backend choice. |
| **`ARCHIVE_BACKEND`** | `in-memory` (use `disk` on paid tier) | Archive logger choice. |
| **`ENABLE_CONTINUITY`** | `true` | Activates autonomous workspace capturing. |
| **`GOOGLE_WORKSPACE_CREDENTIALS_PATH`** | `sage_data/credentials.json` | Stores OAuth secrets on the persistent volume. |
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
