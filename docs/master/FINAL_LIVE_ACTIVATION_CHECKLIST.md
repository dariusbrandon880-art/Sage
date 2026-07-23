# SAGE FINAL LIVE ACTIVATION CHECKLIST

This document serves as the **definitive, step-by-step operational checklist** to guide SAGE's transition from its repository-operational status into a live, secure engineering runtime.

Since the repository implementation is fully complete, tested, and ready, the remaining transition relies entirely on **external credentials, provider access, hosting setup, and domain ownership**. Follow this checklist to complete the real live activation.

---

```
             ┌────────────────────────────────────────┐
             │       Public HTTPS URL / Gateway       │
             └───────────────────┬────────────────────┘
                                 │ (x-api-key / HMAC)
                                 ▼
             ┌────────────────────────────────────────┐
             │            SAGE API Gateway            │
             └───────────────────┬────────────────────┘
                                 ▼
             ┌────────────────────────────────────────┐
             │           Continuity Bridge            │
             └───────────────────┬────────────────────┘
                                 ▼
             ┌────────────────────────────────────────┐
             │           Validation System            │
             └───────────────────┬────────────────────┘
                                 ▼
             ┌────────────────────────────────────────┐
             │           Decision Tracking            │
             └───────────────────┬────────────────────┘
                                 ▼
             ┌────────────────────────────────────────┐
             │             Master Archive             │
             └───────────────────┬────────────────────┘
                                 ▼
             ┌────────────────────────────────────────┐
             │        Persistent State Storage        │
             └────────────────────────────────────────┘
```

---

## 1. Hosting & HTTPS Terminated Gateway Setup
To expose SAGE to external services (ChatGPT, GitHub, Google Workspace), it must be hosted at a public HTTPS URL.

### ▢ Step 1.1: Provision Host Infrastructure
* **Action:** Launch a secure VM (AWS EC2, DigitalOcean Droplet, GCP VM, or similar cloud VM).
* **Firewall / Security Group:** Open ports `80` (HTTP) and `443` (HTTPS) to the public internet. Ensure port `8000` is kept internal or closed.

### ▢ Step 1.2: Point Domain DNS
* **Action:** Create an `A` record on your domain registrar pointing to your VM’s public IP (e.g., `sage.yourdomain.com`).

### ▢ Step 1.3: Configure Production Environment (`.env`)
* **Action:** Rename `.env.example` to `.env` on your server and customize:
  ```bash
  ENV=production
  DEBUG=false
  PORT=8000
  HOST=0.0.0.0
  SAGE_API_KEYS=prod-secure-random-key-here
  SAGE_REQUIRE_AUTH=true
  MEMORY_BACKEND=disk
  ARCHIVE_BACKEND=disk
  ENABLE_CONTINUITY=true
  ```

### ▢ Step 1.4: Run the Containerized Runtime
* **Action:** Execute the Docker daemon to build and launch the SAGE server in the background:
  ```bash
  docker-compose up -d --build
  ```
* **Verify API Startup Command:** Confirm container logs with `docker logs -f sage-continuity-runtime`.
* **Public Endpoint Requirement Check:** Run `curl http://localhost:8000/health` to confirm the internal server returns `{"status":"healthy","runtime":"active"}`.

### ▢ Step 1.5: Configure Nginx SSL Reverse Proxy
* **Action:** Install Nginx and configure it with Certbot (Let's Encrypt) to terminate SSL/TLS.
* **Nginx Configuration Path:** `/etc/nginx/sites-available/sage`
  ```nginx
  server {
      listen 80;
      server_name sage.yourdomain.com;
      return 301 https://$host$request_uri;
  }

  server {
      listen 443 ssl http2;
      server_name sage.yourdomain.com;

      ssl_certificate /etc/letsencrypt/live/sage.yourdomain.com/fullchain.pem;
      ssl_certificate_key /etc/letsencrypt/live/sage.yourdomain.com/privkey.pem;

      location / {
          proxy_pass http://127.0.0.1:8000;
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
          proxy_set_header X-Forwarded-Proto $scheme;
      }
  }
  ```
* **Enable Configuration:** Run `ln -s /etc/nginx/sites-available/sage /etc/nginx/sites-enabled/` and restart Nginx: `sudo systemctl restart nginx`.

---

## 2. OpenAI Custom GPT Action Setup
Allows custom or team ChatGPT instances to query, index, and ingest context into SAGE's live runtime state.

### ▢ Step 2.1: Open Custom GPT Builder
* **Action:** Navigate to [ChatGPT Custom GPTs](https://chatgpt.com/gpts/editor).

### ▢ Step 2.2: Paste SAGE OpenAPI Schema
* **Action:** Copy the entire OpenAPI 3.0 specification from **`docs/master/EXTERNAL_SETUP.md` (Section 2.2)**.
* **Update Target URL:** Modify the `servers.url` parameter in the schema to point to your secure domain:
  ```yaml
  servers:
    - url: https://sage.yourdomain.com
  ```

### ▢ Step 2.3: Configure Header-Based Authentication
* **Action:** Under **Authentication** in the ChatGPT Custom Action builder:
  * Select **API Key**.
  * Choose **Custom** (or Bearer) as the Auth Type.
  * Enter **Header Name:** `x-api-key`.
  * **API Key Value:** Input the exact key string generated in your production `.env` file (`SAGE_API_KEYS`).

### ▢ Step 2.4: Perform Handshake Test
* **Action:** In the ChatGPT preview pane, type:
  > "Get current SAGE status."
* **Expected Flow:** ChatGPT will make an HTTP request to `https://sage.yourdomain.com/status` passing the `x-api-key` header, retrieve the active objectives, task descriptions, and return them seamlessly in the chat.

---

## 3. Gemini / Jules Agent Activation
Enables local high-fidelity deep-reasoning cycles to run and sync their turns directly to the SAGE single-transaction ingest loop.

### ▢ Step 3.1: Obtain Gemini API Key
* **Action:** Go to [Google AI Studio](https://aistudio.google.com/) and create a secure API Key.

### ▢ Step 3.2: Map Environmental Variables
* **Action:** Add the key to your production `.env` file:
  ```bash
  GEMINI_API_KEY=your_actual_ai_studio_api_key_here
  ```
* **Hot Reload / Restart:** Run `docker-compose restart sage-runtime` to register the new key.

### ▢ Step 3.3: Verify Integration Loop
* **Action:** Make a POST request to trigger a reasoning loop query:
  ```bash
  curl -X POST https://sage.yourdomain.com/ai/query/gemini-jules \
       -H "Content-Type: application/json" \
       -H "x-api-key: your-secure-api-key" \
       -d '{"prompt": "Assess architectural alignment of current memory objects"}'
  ```
* **Expected Flow:** SAGE will trigger the Gemini client, compile a list of context matching key phrases, execute the query, and route the conversation transcript back into the persistent Continuity Bridge as a validated memory object automatically.

---

## 4. Google Workspace Live OAuth & Sync Activation
Allows SAGE to sync architectural specifications, master snapshots, and sprint statuses to Google Docs and Google Sheets automatically.

### ▢ Step 4.1: Register GCP Project
* **Action:** Go to the [Google Cloud Console](https://console.cloud.google.com/).
* **Create Project:** Name it `SAGE-Continuity`.

### ▢ Step 4.2: Enable API Libraries
* **Action:** Search for and enable these APIs:
  * **Google Drive API**
  * **Google Docs API**
  * **Google Sheets API**

### ▢ Step 4.3: Configure OAuth Consent Screen
* **Action:** Navigate to **OAuth consent screen** in GCP:
  * Choose **External** (or **Internal** if within an enterprise Google Workspace).
  * Set App Name to `SAGE Runtime`.
  * Under **Scopes**, add manually:
    * `https://www.googleapis.com/auth/documents`
    * `https://www.googleapis.com/auth/spreadsheets`
    * `https://www.googleapis.com/auth/drive.file`
  * Add your Google account email under **Test Users**.

### ▢ Step 4.4: Create Desktop Client Credentials
* **Action:** Go to **Credentials** > **+ Create Credentials** > **OAuth client ID**.
  * Choose application type: **Desktop Application**.
  * Download the generated Client Secret JSON file.

### ▢ Step 4.5: Mount Credentials
* **Action:** Rename the downloaded JSON file to `credentials.json` and place it in the `.sage/` storage folder of your SAGE server deployment:
  * Target path: `.sage/credentials.json`

### ▢ Step 4.6: Initial Manual OAuth Login Web-flow
* **Action:** Run the manual synchronization command once from the terminal inside the running container (or host VM) to trigger the initial web authentication loop:
  ```bash
  docker exec -it sage-continuity-runtime python3 -c "from sage.api import workspace_sync_mgr; workspace_sync_mgr.sync_to_google_workspace('.sage/credentials.json')"
  ```
* **Expected Flow:** A browser redirection URL will print in the terminal. Copy and open this URL in your browser, log in with your Google account, grant permission, and paste the resulting authorization token back if requested (or let the desktop redirect port handle it).
* **Token Persistence:** SAGE will write `token.json` into `.sage/`. Subsequent syncs from endpoints like `POST /tools/workspace/sync` will run automated, headless, and without user prompts.

---

## 5. GitHub Live Webhook Connection
Injects repository events (commits, PRs, releases) into SAGE to keep context perfectly synced with code changes.

### ▢ Step 5.1: Create Webhook in GitHub Settings
* **Action:** Navigate to your GitHub repository: **Settings** > **Webhooks** > **Add webhook**.
* **Required Webhook URL:** `https://sage.yourdomain.com/tools/github/event`
* **Content Type:** `application/json`

### ▢ Step 5.2: Configure Webhook Secret
* **Action:** Generate a secure random string (e.g., `openssl rand -hex 24`).
* **In GitHub Webhook Settings:** Paste this secret in the **Secret** field.
* **In SAGE Production Server `.env`:** Configure the matching variable:
  ```bash
  GITHUB_WEBHOOK_SECRET=your_generated_secret_string_here
  ```
* **Restart SAGE Container:** `docker-compose restart sage-runtime`.

### ▢ Step 5.3: Select Webhook Event Triggers
* **Action:** Choose "Let me select individual events" in GitHub:
  * **Pushes**
  * **Pull requests**
  * **Releases**
* **Save Webhook:** Click **Add webhook** to activate.

### ▢ Step 5.4: Test Signature Validation
* **Action:** Commit a trivial change or trigger a test webhook payload from GitHub.
* **Expected Flow:** GitHub sends an HTTP POST to SAGE with `X-Hub-Signature-256`. SAGE validates the HMAC payload, parses repository and user tags, and indexes the event as a validated memory object automatically.

---

## 6. SAGE Operational Verification Check
Confirm SAGE is functional end-to-end.

* **Action:** Execute the Python readiness checker in production mode to confirm 100% green compliance:
  ```bash
  docker exec -it sage-continuity-runtime python3 scripts/production_check.py
  ```
* **Expected Result:**
  ```text
  [✓] Runtime Environment compatible
  [✓] FastAPI & Pydantic verified
  [✓] Global API key verification active
  [✓] HMAC payload signature validation active
  [✓] Persistent directory checks completed successfully
  SAGE STATUS: FULLY PROVISIONED AND READY FOR SECURE PRODUCTION DEPLOYMENT!
  ```
