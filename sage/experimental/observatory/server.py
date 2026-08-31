"""Customer-facing SAGE Observatory and live command HUD.

The Observatory is the operator/customer acceptance surface. It renders canonical
identity, mission state, and acceptance evidence from the repository-backed adapter.
The production service mounts the authenticated SAGE runtime under /runtime so the
customer surface and execution API are served by the same process.
"""

import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

from sage.api import app as api_app, lifecycle_mgr
from sage.experimental.observatory.adapter import SAGEObservatoryAdapter
from sage.live_agent_hud import get_live_agent_hud

app = FastAPI(
    title="SAGE Observatory & Execution Runtime API",
    description="Customer-facing SAGE live command HUD, acceptance surface, and REST API runtime gateway",
    version="1.2.0",
)
adapter = SAGEObservatoryAdapter()


@app.middleware("http")
async def api_key_auth_middleware(request: Request, call_next):
    require_auth = os.getenv("SAGE_REQUIRE_AUTH", "false").lower() == "true"
    bypass_paths = ["/", "/health", "/docs", "/redoc", "/openapi.json", "/api/state", "/api/hud"]

    if require_auth and request.url.path not in bypass_paths and not request.url.path.startswith("/runtime/"):
        x_api_key = request.headers.get("x-api-key")
        if not x_api_key or not lifecycle_mgr.authorize(x_api_key):
            return JSONResponse(
                status_code=401, content={"detail": "Unauthorized: Invalid or missing API key."}
            )

    return await call_next(request)


# Mount the authenticated SAGE API runtime under /runtime
app.mount("/runtime", api_app)


@app.get("/health")
async def health():
    return {"status": "healthy", "surface": "sage-observatory", "runtime": "active"}


@app.get("/api/state")
async def get_state():
    try:
        return JSONResponse(content=adapter.compute_view_model().model_dump())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to compute Observatory state: {exc!s}") from exc


@app.get("/api/hud")
async def get_hud(agent_id: str = "MISSION_CONTROL"):
    try:
        return JSONResponse(content=get_live_agent_hud(agent_id))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to compute live agent HUD: {exc!s}") from exc


@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    html = """<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>SAGE OBSERVATORY — CUSTOMER ACCEPTANCE SURFACE</title><style>
:root{--bg:#030a0d;--panel:#07151a;--line:#0c303a;--cyan:#00e5ff;--green:#00e676;--text:#b0bec5;--bright:#e0f7fa;--red:#ff1744}*{box-sizing:border-box}body{margin:0;padding:18px;background:var(--bg);color:var(--text);font:12px 'Courier New',monospace}header,.panel{background:var(--panel);border:1px solid var(--line);box-shadow:0 0 14px #00e5ff12}header{padding:16px;margin-bottom:18px;display:flex;justify-content:space-between;gap:16px}h1{margin:0;color:var(--cyan);font-size:24px;letter-spacing:2px}.sub{margin-top:5px;color:#507b8a}.hud-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.agent{border:1px solid var(--line);padding:12px;background:#030f13}.agent.active{border-color:var(--cyan)}.tag{font-size:14px;color:var(--bright);font-weight:bold;margin-bottom:8px}.agent-name{color:var(--cyan);font-size:11px}.meta{margin-top:7px;line-height:1.6}.state,.ok{color:var(--green);font-weight:bold}.self{border-color:var(--green)}pre{white-space:pre-wrap;overflow:auto;color:var(--bright);margin:0}.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}.panel{padding:15px;margin-bottom:18px}.title{color:var(--cyan);font-weight:bold;letter-spacing:1px;border-bottom:1px solid var(--line);padding-bottom:7px;margin-bottom:12px}.row{padding:7px 0;border-bottom:1px solid var(--line)}.muted{color:#507b8a}.bad{color:var(--red)}@media(max-width:900px){.hud-grid,.grid{grid-template-columns:1fr 1fr}}@media(max-width:600px){header{display:block}.hud-grid,.grid{grid-template-columns:1fr}}</style></head><body><header><div><h1>SAGE OBSERVATORY</h1><div class='sub'>CUSTOMER ACCEPTANCE SURFACE / LIVE COMMAND HUD</div></div><div>STATUS: <span class='ok'>LIVE OBSERVATION</span><br>IDENTITY: <span class='ok'>CANONICAL</span></div></header><section class='panel'><div class='title'>00 // LIVE AGENT NAMEPLATES — CUSTOMER VISIBLE</div><div id='hud' class='hud-grid'><div class='muted'>Loading canonical identity...</div></div></section><section class='panel'><div class='title'>00B // CUSTOMER ACCEPTANCE — ACTUAL STATE</div><pre id='acceptance'>Loading...</pre></section><div class='grid'><section class='panel'><div class='title'>01 // SELF HUD PROJECTION</div><pre id='self'>Loading...</pre></section><section class='panel'><div class='title'>02 // GOVERNED COORDINATION</div><pre id='coord'>Loading...</pre></section></div><section class='panel'><div class='title'>03 // REPOSITORY-BACKED FORENSIC STATE</div><pre id='forensic'>Loading...</pre></section><script>
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function load(){try{const [hr,sr]=await Promise.all([fetch('/api/hud?agent_id=MISSION_CONTROL'),fetch('/api/state')]);if(!hr.ok||!sr.ok)throw Error('API failure');const hud=await hr.json(),state=await sr.json();const roster=hud.team?.roster||[];document.getElementById('hud').innerHTML=roster.map(x=>`<article class='agent ${x.nameplate===hud.self?.nameplate?'active self':''}'><div class='tag'>${esc(x.nameplate)}</div><div class='agent-name'>${esc(x.agent_name)}</div><div class='meta'>ROLE: ${esc(x.role)}<br>CQL-${esc(x.cql)} / SQL-${esc(x.sql)} / XP-${esc(x.xp)}<br>STATE: <span class='state'>${esc(x.state)}</span></div></article>`).join('');document.getElementById('acceptance').textContent=JSON.stringify(state.customer_acceptance_surface,null,2);document.getElementById('self').textContent=JSON.stringify(hud.self,null,2);document.getElementById('coord').textContent=JSON.stringify({status:hud.team?.coordination_status,pending:hud.coordination?.pending_count,delivery:hud.coordination?.delivery_semantics},null,2);document.getElementById('forensic').textContent=JSON.stringify(state,null,2)}catch(e){document.getElementById('hud').innerHTML=`<span class='bad'>CUSTOMER SURFACE LOAD FAILURE: ${esc(e)}</span>`}}load();setInterval(load,5000);
</script></body></html>"""
    return HTMLResponse(content=html, status_code=200)


# Delegate root API paths from api_app so endpoints like /status and /ai/query/chatgpt resolve directly at root
existing_paths = {r.path for r in app.routes}
for route in api_app.routes:
    if route.path not in existing_paths and route.path not in ["/", "/health"]:
        app.routes.append(route)
