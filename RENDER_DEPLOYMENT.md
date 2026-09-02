# SAGE-Render Deployment & C2 Integration Guide

## Objective

Deploy SAGE to Render as a live, authenticated HTTP service that C2/ChatGPT can interrogate for state, render prompts, and capture evidence.

**Target Architecture:**
```
ChatGPT/C2 Client
    ↓
[x-api-key header]
    ↓
SAGE API Gateway (Render HTTPS)
    ↓
Canonical Runtime State
    ↓
Memory + Archive + Evidence
```

---

## Prerequisites

1. **GitHub Repository:** `dariusbrandon880-art/Sage` (already linked)
2. **Render Account:** Free tier supports 1 web service + auto-redeployment from GitHub
3. **OpenAI API Key:** Required for ChatGPT rendering
   - Sign up at https://platform.openai.com/api/keys
   - Generate a new secret key (do NOT commit to Git)

---

## Step 1: Configure Environment Secrets on Render

### Via Render Dashboard:

1. Go to **Render Dashboard** → **Services** → **Create Web Service**
2. Connect GitHub repository: `dariusbrandon880-art/Sage`
3. Select branch: `main`
4. Configure environment variables:

| Variable | Value | Source |
|----------|-------|--------|
| `ENV` | `production` | Static |
| `SAGE_REQUIRE_AUTH` | `true` | Static |
| `OPENAI_API_KEY` | `sk-...` | **Secret from OpenAI** |
| `SAGE_API_KEYS` | `your-generated-key-1` | Generated (save locally) |
| `PORT` | `8000` | Static |
| `MEMORY_BACKEND` | `disk` | Static |
| `ARCHIVE_BACKEND` | `disk` | Static |
| `CHATGPT_EVIDENCE_CAPTURE` | `true` | Static |

**Critical:** Do NOT commit `OPENAI_API_KEY` to Git. Set it only on Render via the dashboard.

---

## Step 2: Deploy to Render

1. **Auto-Deploy:** Render automatically redeployments on every `push` to `main`
2. **Manual Deploy:** Trigger via Render dashboard if needed
3. **Monitor:** Check **Render Logs** for deployment status

Expected log output:
```
Collecting sage-runtime==0.1.0
...
Application startup complete [uvicorn]
Uvicorn running on http://0.0.0.0:8000
```

---

## Step 3: Verify Deployment Health

Once deployed, SAGE exposes a health check endpoint:

```bash
curl https://sage-runtime-xyz123.onrender.com/health \
  -H "x-api-key: your-generated-key-1"
```

Expected response:
```json
{
  "status": "healthy",
  "deployment": {
    "environment": "production",
    "openai_configured": true,
    "auth_required": true,
    "timestamp": "2026-09-02T..."
  },
  ...
}
```

---

## Step 4: C2 Client Integration — Query SAGE

### Endpoint: `/chat/render` (Authenticated)

**Request:**
```bash
curl -X POST https://sage-runtime-xyz123.onrender.com/chat/render \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-generated-key-1" \
  -d '{
    "prompt": "What is SAGE mission status?",
    "session_id": "c2-session-001",
    "model": "gpt-4",
    "bind_to_decision": null
  }'
```

**Response:**
```json
{
  "content": "SAGE Autonomous Continuity Runtime is active...",
  "model": "gpt-4",
  "session_id": "c2-session-001",
  "evidence_id": "mem_xyz789",
  "timestamp": "2026-09-02T...",
  "governed": true,
  "usage": null
}
```

### Endpoint: `/chat/render/stream` (Streaming)

**Request:**
```bash
curl -X POST https://sage-runtime-xyz123.onrender.com/chat/render/stream \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-generated-key-1" \
  -d '{
    "prompt": "List SAGE capabilities",
    "stream": true
  }'
```

**Response:** NDJSON-formatted chunks
```
{"chunk": "SAGE ", "chunk_number": 1, "session_id": "..."}
{"chunk": "provides ", "chunk_number": 2, "session_id": "..."}
...
```

---

## Step 5: Verify Evidence Capture

Query the memory endpoint to confirm ChatGPT interactions are logged:

```bash
curl https://sage-runtime-xyz123.onrender.com/memory/search/tag/chatgpt \
  -H "x-api-key: your-generated-key-1"
```

Response shows all ChatGPT rendering evidence:
```json
{
  "tag": "chatgpt",
  "count": 3,
  "results": [
    {
      "id": "mem_xyz789",
      "object_type": "chatgpt_render",
      "content": {
        "prompt": "...",
        "response": "...",
        "authenticated": true
      },
      "confidence": "VALIDATED"
    },
    ...
  ]
}
```

---

## Step 6: Diagnostics & Monitoring

### Check Runtime Status:
```bash
curl https://sage-runtime-xyz123.onrender.com/status \
  -H "x-api-key: your-generated-key-1"
```

### Check Control Plane:
```bash
curl https://sage-runtime-xyz123.onrender.com/runtime/control-plane \
  -H "x-api-key: your-generated-key-1"
```

### Check Deployed Capabilities:
```bash
curl https://sage-runtime-xyz123.onrender.com/runtime/capabilities \
  -H "x-api-key: your-generated-key-1"
```

---

## Security Checklist

- ✅ HTTPS enforced (Render provides free SSL)
- ✅ API key required for all protected endpoints
- ✅ `OPENAI_API_KEY` never committed to Git
- ✅ Authentication enforced in middleware
- ✅ Evidence logged for all ChatGPT interactions
- ✅ Fail-closed default (unauthorized requests rejected)

---

## Troubleshooting

### Issue: `OPENAI_API_KEY not configured`
**Solution:** Verify environment variable set on Render dashboard, redeploy, check logs.

### Issue: `401 Unauthorized` on authenticated endpoint
**Solution:** Verify `x-api-key` header is correct and matches `SAGE_API_KEYS`.

### Issue: ChatGPT responses not appearing in evidence
**Solution:** Verify `CHATGPT_EVIDENCE_CAPTURE=true` in Render environment, check logs for rendering errors.

### Issue: Slow startup
**Solution:** Free tier Render has 15-minute build timeout. On first deploy, may take 5-10 minutes to start.

---

## Next Steps for C2

1. **Recon:** C2 queries `/health` to verify SAGE is alive
2. **Query State:** C2 queries `/status` to understand current objective/task
3. **Render Prompts:** C2 POSTs to `/chat/render` with governed prompts
4. **Capture Evidence:** C2 queries `/memory/search/tag/chatgpt` to inspect interaction records
5. **Decide:** C2 creates decisions via `/decision` endpoint with evidence bindings

---

**Status:** Ready for deployment. Execute the following:

```bash
# 1. Push to main (triggers auto-deploy)
git push origin main

# 2. On Render dashboard, set OPENAI_API_KEY via UI
# 3. Monitor logs for successful startup
# 4. Test health check once deployed
```
