# SAGE Render Deployment & ChatGPT Action Activation Guide

This guide details the exact procedure for connecting your live Render deployment (`sage-runtime` or `Sage-1`) to an OpenAI ChatGPT Custom Action, achieving verified `CONNECTED_AND_GOVERNED` operational status.

---

## 1. Deployment Architecture & Status

Your Render dashboard shows two active web service deployments:
- **`sage-runtime`**: Python 3 Web Service, Oregon Region (`https://sage-runtime.onrender.com`).
- **`Sage-1`**: Python 3 Web Service, Virginia Region.

Both services run SAGE's unified ASGI process (`uvicorn sage.experimental.observatory.server:app`), serving both the **SAGE Observatory HUD** (customer/operator UI at `/`) and the full **SAGE Execution REST API** (`/status`, `/ingest`, `/ai/query/chatgpt`, `/openapi.json`, etc.).

---

## 2. Live Verification Protocol

Run the automated verification script against your deployed Render service URL to verify health, authentication, and endpoint availability:

```bash
PYTHONPATH=. poetry run python scripts/verify_render_chatgpt_action.py https://<your-service-name>.onrender.com <your-sage-api-key>
```

This generates an authoritative SHA-bound evidence receipt at:
`evidence_capture/render_chatgpt_action_verification.json`

---

## 3. Configuring the ChatGPT Custom Action

### Step 3.1: Navigate to Custom GPT Editor
1. Open [ChatGPT GPT Editor](https://chatgpt.com/gpts/editor).
2. Select your SAGE GPT or click **Create**.
3. Under **Configure**, scroll down and click **Create new action**.

### Step 3.2: Import OpenAPI Specification
In the **Schema** box, choose one of these two options:
- **Option A (URL Import)**: Paste `https://<your-service-name>.onrender.com/openapi.json` and click **Import**.
- **Option B (Copy/Paste Schema)**: Copy the contents of `docs/openapi.json` or `docs/openapi.yaml` directly into the text box.

### Step 3.3: Configure Authentication
1. Click **Authentication** (gear icon beside Authentication).
2. Select **API Key**.
3. Set **Auth Type** to **Custom** or **Bearer**.
4. Set **Header Name** to: `x-api-key`
5. Set **API Key** to: The secret key configured in your Render service's `SAGE_API_KEYS` environment variable.
6. Click **Save**.

---

## 4. Canonical OpenAPI 3.0 Endpoints Reference

The ChatGPT Action exposes the following primary governed pathways:

| Path | Method | Purpose | Auth Required |
| :--- | :--- | :--- | :--- |
| `/health` | `GET` | Health check & surface status | No |
| `/status` | `GET` | Active objective, task, memory & decision counts | Yes (`x-api-key`) |
| `/ai/query/chatgpt` | `POST` | Execute governed ChatGPT reasoning turn | Yes (`x-api-key`) |
| `/ingest` | `POST` | Authoritative single-turn session payload ingestion | Yes (`x-api-key`) |
| `/reason` | `GET` | Compute state continuity reasoning & alignment | Yes (`x-api-key`) |
| `/verify` | `GET` | Audit disk, memory, and lineage integrity | Yes (`x-api-key`) |
| `/objective` | `POST` | Configure active high-level system objective | Yes (`x-api-key`) |
| `/task` | `POST` | Configure active engineering task | Yes (`x-api-key`) |
| `/openapi.json` | `GET` | Retrieve live OpenAPI 3.0 JSON specification | No |

---

## 5. Environment Variables Checklist on Render

Ensure the following environment variables are set in your Render Web Service Dashboard (**Settings > Environment Variables**):

- `SAGE_REQUIRE_AUTH`: `true`
- `SAGE_API_KEYS`: `<your-secure-random-api-key>`
- `OPENAI_API_KEY`: `<your-openai-api-key>`
- `ENV`: `production`
- `ENABLE_CONTINUITY`: `true`
