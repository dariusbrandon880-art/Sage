"""SAGE Observatory read-only forensic and live-agent HUD interface."""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

from sage.experimental.observatory.adapter import SAGEObservatoryAdapter
from sage.live_agent_hud import get_live_agent_hud

app = FastAPI(title="SAGE Observatory", description="SAGE read-only forensic state and live agent identity interface", version="1.1.1")
adapter = SAGEObservatoryAdapter()

@app.get("/api/state")
async def get_state():
    try:
        return JSONResponse(content=adapter.compute_view_model().model_dump())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to compute forensic view model: {exc!s}") from exc

@app.get("/api/hud")
async def get_hud(agent_id: str = "MISSION_CONTROL"):
    try:
        return JSONResponse(content=get_live_agent_hud(agent_id))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to compute live agent HUD: {exc!s}") from exc

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    html = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>SAGE OBSERVATORY — LIVE COMMAND HUD</title><style>
:root{--bg:#030a0d;--panel:#07151a;--line:#0c303a;--cyan:#00e5ff;--green:#00e676;--text:#b0bec5;--bright:#e0f7fa}*{box-sizing:border-box}body{margin:0;padding:18px;background:var(--bg);color:var(--text);font:12px "Courier New",monospace}header,.panel{background:var(--panel);border:1px solid var(--line);box-shadow:0 0 14px #00e5ff12}header{padding:16px;margin-bottom:18px;display:flex;justify-content:space-between;gap:16px}h1{margin:0;color:var(--cyan);font-size:24px;letter-spacing:2px}.sub{margin-top:5px;color:#507b8a}.hud-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.agent{border:1px solid var(--line);padding:12px;background:#030f13}.agent.active{border-color:var(--cyan);box-shadow:0 0 12px #00e5ff22}.tag{font-size:14px;color:var(--bright);font-weight:bold;margin-bottom:8px}.agent-name{color:var(--cyan);font-size:11px}.meta{margin-top:7px;line-height:1.6}.state{color:var(--green);font-weight:bold}.self{border-color:var(--green)}pre{white-space:pre-wrap;overflow:auto;color:var(--bright);margin:0}.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}.panel{padding:15px;margin-bottom:18px}.title{color:var(--cyan);font-weight:bold;letter-spacing:1px;border-bottom:1px solid var(--line);padding-bottom:7px;margin-bottom:12px}.row{padding:7px 0;border-bottom:1px solid var(--line)}.muted{color:#507b8a}.ok{color:var(--green)}.bad{color:#ff1744}@media(max-width:900px){.hud-grid,.grid{grid-template-columns:1fr 1fr}}@media(max-width:600px){header{display:block}.hud-grid,.grid{grid-template-columns:1fr}}
</style></head><body><header><div><h1>SAGE OBSERVATORY</h1><div class="sub">REPOSITORY-BACKED LIVE COMMAND / FORENSIC INTERFACE</div></div><div>STATUS: <span class="ok">ACTIVE OBSERVATION</span><br>IDENTITY: <span class="ok">LIVE + CANONICAL</span></div></header><section class="panel"><div class="title">00 // LIVE AGENT NAMEPLATES — CANONICAL HUD</div><div id="hud" class="hud-grid"><div class="muted">Loading canonical identity...</div></div></section><section class="panel"><div class="title">00B // CUSTOMER ACCEPTANCE SURFACE BINDING</div><pre id="acceptance">Loading customer surface binding...</pre></section><div class="grid"><section class="panel"><div class="title">01 // SELF HUD PROJECTION</div><pre id="self">Loading...</pre></section><section class="panel"><div class="title">02 // GOVERNED COORDINATION</div><pre id="coord">Loading...</pre></section></div><div class="grid"><section class="panel"><div class="title">03 // CAUSAL EXECUTION SPINE</div><div id="spine">Loading...</div></section><section class="panel"><div class="title">04 // REPOSITORY BALANCE</div><div id="balance">Loading...</div></section></div><section class="panel"><div class="title">05 // FORENSIC STATE</div><pre id="forensic">Loading...</pre></section><script>
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function load(){const [hr,sr]=await Promise.all([fetch('/api/hud?agent_id=MISSION_CONTROL'),fetch('/api/state')]);if(!hr.ok||!sr.ok)throw Error('API failure');const hud=await hr.json(),state=await sr.json();const roster=hud.team?.roster||[];document.getElementById('hud').innerHTML=roster.map(x=>`<article class="agent ${x.nameplate===hud.self?.nameplate?'active self':''}"><div class="tag">${esc(x.nameplate)}</div><div class="agent-name">${esc(x.agent_name)}</div><div class="meta">ROLE: ${esc(x.role)}<br>CQL-${esc(x.cql)} / SQL-${esc(x.sql)} / XP-${esc(x.xp)}<br>STATE: <span class="state">${esc(x.state)}</span></div></article>`).join('');document.getElementById('acceptance').textContent=JSON.stringify(state.customer_acceptance_surface,null,2);document.getElementById('self').textContent=JSON.stringify(hud.self,null,2);document.getElementById('coord').textContent=JSON.stringify({status:hud.team?.coordination_status,pending:hud.coordination?.pending_count,delivery:hud.coordination?.delivery_semantics},null,2);document.getElementById('spine').innerHTML=(state.causal_spine||[]).map(x=>`<div class="row"><b>${esc(x.name)}</b> — ${esc(x.details)} <span class="muted">[${esc(x.status)}]</span></div>`).join('');const b=state.homeostatic_balance||{};document.getElementById('balance').innerHTML=Object.entries(b).map(([k,v])=>`<div class="row">${esc(k)} <b class="ok">${esc(v)}</b></div>`).join('');document.getElementById('forensic').textContent=JSON.stringify(state,null,2)}load().catch(e=>{document.getElementById('hud').innerHTML=`<span class="bad">HUD LOAD FAILURE: ${esc(e)}</span>`});
</script></body></html>'''
    return HTMLResponse(content=html, status_code=200)
