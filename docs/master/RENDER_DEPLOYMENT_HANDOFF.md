# SAGE RUNTIME RENDER DEPLOYMENT HANDOFF SPECIFICATION

This document provides the definitive, production-ready **Render Deployment Handoff Specification** for the **SAGE Autonomous Continuity Runtime**, fully revised for **Render Free Tier compatibility**.

As SAGE is extremely lightweight (utilizing under 100MB RAM and starting in seconds), it runs flawlessly on Render's Free Web Service tier. Review the operational tiers, configuration choices, and instructions below to deploy SAGE.

---

## 1. Plan Tier Trade-offs & Analysis

| Feature | Free Tier (Stateless/In-Memory) | Paid Tier (Stateful/Persistent Disk) |
| :--- | :--- | :--- |
| **Render Plan** | `Free` ($0/mo) | `Starter` ($7/mo) + Disk ($0.25/GB/mo) |
| **Persistence** | **Ephemeral** (State resets on restart/redeploy) | **Persistent** (State retained on disk volume) |
| **Disk Support** | Not supported on Render Free Tier | Supported (attachable `sage-data` disk) |
| **Instance Spin-down**| Spins down after 15 mins of inactivity (delay on wake) | Always active, zero cold-start delay |
| **Config Backend**| `MEMORY_BACKEND=in-memory` | `MEMORY_BACKEND=disk` |

### Why SAGE Free Tier is Stateless:
Render Free Web Services do **not** support attaching Persistent Disks. While SAGE can still write files to ephemeral scratch directories in Free Tier, Render discards all filesystem modifications on restarts, redeployments, or daily recycling. To avoid un-synchronized state behavior, SAGE should be run with **`in-memory`** backends on the Free Tier, or upgraded to the **`Starter`** tier with a **`sage-data`** persistent disk for permanent, production-grade knowledge lineage preservation.

---

## 2. Core Deployment Settings

| Parameter | Free Tier Value | Stateful/Paid Tier Value |
| :--- | :--- | :--- |
| **Service Type** | `Web Service` | `Web Service` |
| **Language** | `Docker` | `Docker` |
| **Plan** | `Free` | `Starter` |
| **Branch** | `main` | `main` |
| **Dockerfile Path** | `Dockerfile` | `Dockerfile` |
| **Health Check Path**| `/health` | `/health` |

---

## 3. Persistent Disk Setup (Stateful/Paid Tier Only)
*This section is completely bypassed if you deploy SAGE on the Free Tier.*

* **Disk Name:** `sage-data`
* **Mount Path:** `/app/sage_data`
* **Size:** `10 GB`
* **Configuration Sync:** Ensure `GOOGLE_WORKSPACE_CREDENTIALS_PATH` is configured as `sage_data/credentials.json` so OAuth tokens are persisted on this volume instead of the ephemeral container layer.

---

## 4. Environment Variables

Configure the following variables in the **Environment** tab of your Render service dashboard:

| Variable Name | Free Tier Value | Stateful Tier Value | Description |
| :--- | :--- | :--- | :--- |
| **`ENV`** | `production` | `production` | Sets the runtime to production mode. |
| **`DEBUG`** | `false` | `false` | Disables debugging logs and endpoints. |
| **`PORT`** | `8000` | `8000` | Port matching SAGE’s exposure. |
| **`HOST`** | `0.0.0.0` | `0.0.0.0` | Bind host address. |
| **`SAGE_REQUIRE_AUTH`** | `true` | `true` | Enforces `x-api-key` header verification. |
| **`SAGE_API_KEYS`** | *[Auto-Generated]* | *[Auto-Generated]* | Secret API token(s) used for Custom GPT & API auth. |
| **`MEMORY_BACKEND`** | `in-memory` | `disk` | Storage backend for memories/sessions. |
| **`ARCHIVE_BACKEND`** | `in-memory` | `disk` | Storage backend for permanent knowledge archives. |
| **`ENABLE_CONTINUITY`** | `true` | `true` | Activates autonomous workspace capturing. |
| **`GOOGLE_WORKSPACE_CREDENTIALS_PATH`** | `.sage/credentials.json`| `sage_data/credentials.json` | Path to Google OAuth secrets. |
| **`GITHUB_WEBHOOK_SECRET`** | *[Insert Secret]* | *[Insert Secret]* | HMAC validation key for raw GitHub events. |
| **`GEMINI_API_KEY`** | *[Insert Secret]* | *[Insert Secret]* | API key for Gemini / Jules reasoning loops. |

---

## 5. Blueprint Deployment (Declarative YAML)

SAGE includes a pre-configured, free-tier compatible `render.yaml` Blueprint specification at the repository root. To deploy:

1. Log in to your [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** and select **Blueprint**.
3. Connect your GitHub repository (`dariusbrandon880-art/Sage`).
4. Render will parse `render.yaml`, configure SAGE on the **Free Web Service** tier, and prompt for confirmation.
5. Click **Approve** to build and launch immediately.
