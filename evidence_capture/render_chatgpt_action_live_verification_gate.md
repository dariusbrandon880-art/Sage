# Live Render Verification Gate

PR #364 is not `CONNECTED_AND_GOVERNED` yet.

The committed Render receipt used a mock URL (`http://mock-render-url.onrender.com`), so it proves only mocked HTTP behavior. It does not prove a real Render deployment, deployed commit identity, authentication, or a live governed ChatGPT request.

Required before merge:
- actual Render HTTPS service URL
- deployed commit SHA matching the verified source
- live `/health`
- live `/openapi.json`
- live authenticated `/status`
- live authenticated `/ai/query/chatgpt`
- evidence receipt bound to that live request

Until all are present, status is `PENDING_LIVE_VERIFICATION`.
