"""SAGE Observatory Standalone Read-Only Forensic Server.

Exposes a standalone, read-only dashboard visualizing verified repository evidence
and forensic views of SAGE.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pathlib import Path

from sage.experimental.observatory.adapter import SAGEObservatoryAdapter

app = FastAPI(
    title="SAGE Observatory",
    description="SAGE Read-Only Forensic State Interface",
    version="1.0.0"
)

# Read-only adapter
adapter = SAGEObservatoryAdapter()


@app.get("/api/state")
async def get_state():
    """Retrieve normalized forensic view model of the repository."""
    try:
        model = adapter.compute_view_model()
        return JSONResponse(content=model.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compute forensic view model: {e!s}")


@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    """Renders the futurist sci-fi cybernetic command dashboard interface."""
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SAGE OBSERVATORY - FORENSIC INTERFACE</title>
    <style>
        :root {
            --bg-color: #030a0d;
            --panel-bg: #07151a;
            --border-color: #0c303a;
            --accent-cyan: #00e5ff;
            --accent-green: #00e676;
            --accent-yellow: #ffd200;
            --accent-red: #ff1744;
            --accent-purple: #d500f9;
            --text-color: #b0bec5;
            --text-bright: #e0f7fa;
        }

        body {
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: "Courier New", Courier, monospace;
            margin: 0;
            padding: 20px;
            box-sizing: border-box;
            overflow-x: hidden;
        }

        header {
            border: 2px solid var(--border-color);
            background-color: var(--panel-bg);
            padding: 15px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 0 15px rgba(0, 229, 255, 0.1);
        }

        h1 {
            color: var(--accent-cyan);
            margin: 0;
            font-size: 24px;
            text-transform: uppercase;
            letter-spacing: 2px;
            text-shadow: 0 0 8px rgba(0, 229, 255, 0.4);
        }

        .subtitle {
            font-size: 11px;
            color: var(--text-color);
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .grid-container {
            display: grid;
            grid-template-columns: 1fr 1.5fr;
            grid-gap: 20px;
            margin-bottom: 20px;
        }

        @media (max-width: 1024px) {
            .grid-container {
                grid-template-columns: 1fr;
            }
        }

        .panel {
            background-color: var(--panel-bg);
            border: 1px solid var(--border-color);
            padding: 15px;
            box-sizing: border-box;
            position: relative;
        }

        .panel::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            width: 8px;
            height: 8px;
            border-top: 2px solid var(--accent-cyan);
            border-left: 2px solid var(--accent-cyan);
        }

        .panel-title {
            color: var(--accent-cyan);
            font-size: 14px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-top: 0;
            margin-bottom: 15px;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 5px;
            display: flex;
            justify-content: space-between;
        }

        /* Spine Styles */
        .spine-node {
            display: flex;
            align-items: center;
            margin-bottom: 12px;
            font-size: 12px;
            position: relative;
        }

        .spine-node:not(:last-child)::after {
            content: "";
            position: absolute;
            left: 10px;
            top: 15px;
            bottom: -15px;
            width: 2px;
            background-color: var(--border-color);
        }

        .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 15px;
            border: 2px solid #000;
            flex-shrink: 0;
        }

        .status-dot.GREEN { background-color: var(--accent-green); box-shadow: 0 0 8px var(--accent-green); }
        .status-dot.YELLOW { background-color: var(--accent-yellow); box-shadow: 0 0 8px var(--accent-yellow); }
        .status-dot.RED { background-color: var(--accent-red); box-shadow: 0 0 8px var(--accent-red); }
        .status-dot.PURPLE { background-color: var(--accent-purple); box-shadow: 0 0 8px var(--accent-purple); }
        .status-dot.GREY { background-color: #2b2b2b; }
        .status-dot.BLUE { background-color: #00bcff; box-shadow: 0 0 8px #00bcff; }

        .spine-content {
            flex-grow: 1;
        }

        .spine-name {
            color: var(--text-bright);
            font-weight: bold;
        }

        .spine-src {
            font-size: 9px;
            color: #507b8a;
            display: block;
        }

        /* Differential styles */
        .diff-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            grid-gap: 15px;
            font-size: 12px;
        }

        .diff-box {
            border: 1px solid var(--border-color);
            background-color: rgba(12, 48, 58, 0.2);
            padding: 10px;
        }

        .diff-box-title {
            color: var(--accent-cyan);
            font-size: 10px;
            text-transform: uppercase;
            margin-bottom: 5px;
        }

        .diff-result {
            font-family: monospace;
            color: var(--text-bright);
        }

        .emergent-banner {
            grid-column: span 2;
            text-align: center;
            padding: 8px;
            border: 1px dashed var(--accent-yellow);
            color: var(--accent-yellow);
            font-size: 11px;
            text-transform: uppercase;
        }

        /* Homeostatic balance */
        .balance-item {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            font-size: 12px;
        }

        .balance-label {
            color: var(--text-color);
        }

        .balance-val {
            color: var(--accent-green);
            font-weight: bold;
        }

        /* Galaxy / Network Topology */
        .galaxy-canvas {
            border: 1px solid var(--border-color);
            height: 220px;
            display: flex;
            justify-content: space-around;
            align-items: center;
            background-color: rgba(3, 10, 13, 0.5);
            position: relative;
        }

        .galaxy-node {
            border: 1px solid var(--accent-cyan);
            background-color: var(--panel-bg);
            padding: 8px 12px;
            font-size: 10px;
            color: var(--text-bright);
            text-transform: uppercase;
            box-shadow: 0 0 10px rgba(0, 229, 255, 0.2);
        }

        .galaxy-node.falsified {
            border-color: var(--accent-red);
            color: var(--accent-red);
        }

        .galaxy-connection {
            position: absolute;
            height: 2px;
            background-color: var(--border-color);
            z-index: -1;
        }

        /* Lineage and fail boxes */
        .forensic-lineage {
            font-size: 11px;
            border-collapse: collapse;
            width: 100%;
        }

        .forensic-lineage th, .forensic-lineage td {
            border: 1px solid var(--border-color);
            padding: 8px;
            text-align: left;
        }

        .forensic-lineage th {
            background-color: rgba(12, 48, 58, 0.4);
            color: var(--accent-cyan);
        }

        /* Section borders and utilities */
        .neon-border {
            border-color: var(--accent-cyan);
            box-shadow: 0 0 10px rgba(0, 229, 255, 0.2);
        }

        footer {
            text-align: center;
            font-size: 10px;
            margin-top: 30px;
            border-top: 1px solid var(--border-color);
            padding-top: 15px;
            color: #507b8a;
            text-transform: uppercase;
        }
    </style>
</head>
<body>

    <header>
        <div>
            <h1>SAGE OBSERVATORY</h1>
            <div class="subtitle">Repository-Backed Forensic Proof Center</div>
        </div>
        <div style="text-align: right; font-size: 11px;">
            <div>STATUS: <span style="color: var(--accent-green); font-weight: bold;">ACTIVE OBSERVATION</span></div>
            <div>RUNTIME BOUNDARY: <span style="color: var(--accent-cyan);">READ-ONLY SECURE STERILITY</span></div>
        </div>
    </header>

    <div class="grid-container">

        <!-- Window A: Causal Spine -->
        <div class="panel">
            <div class="panel-title">
                <span>01 // CAUSAL EXECUTION SPINE</span>
                <span style="font-size: 9px; color: #507b8a;">PERSISTENCE ANCHOR</span>
            </div>
            <div id="causal-spine-container">
                <!-- Loaded dynamically -->
            </div>
        </div>

        <!-- Right Side: Galaxy + Homeostatic -->
        <div style="display: flex; flex-direction: column; gap: 20px;">

            <!-- Window D: Galaxy & Topology -->
            <div class="panel">
                <div class="panel-title">
                    <span>02 // CAPABILITY GALAXY TOPOLOGY</span>
                    <span style="font-size: 9px; color: #507b8a;">MAP VIEW</span>
                </div>
                <div class="galaxy-canvas" id="galaxy-container">
                    <!-- Configured statically and dynamically -->
                    <div class="galaxy-node">Mission</div>
                    <div style="width: 30px; height: 2px; background-color: var(--accent-green);"></div>
                    <div class="galaxy-node">Preflight Locks</div>
                    <div style="width: 30px; height: 2px; background-color: var(--accent-green);"></div>
                    <div class="galaxy-node">PFC Kernel</div>
                    <div style="width: 30px; height: 2px; background-dash: 2px; background-color: var(--border-color);"></div>
                    <div class="galaxy-node falsified">MEC Handoff</div>
                </div>
            </div>

            <!-- Window C: Homeostatic Balance -->
            <div class="panel">
                <div class="panel-title">
                    <span>03 // HOMEOSTATIC REPOSITORY BALANCE</span>
                    <span style="font-size: 9px; color: #507b8a;">EQUILIBRIUM LEVEL</span>
                </div>
                <div id="balance-container">
                    <!-- Loaded dynamically -->
                </div>
            </div>

        </div>

    </div>

    <div class="grid-container" style="grid-template-columns: 1.5fr 1fr;">

        <!-- Lineage and Differential Windows -->
        <div class="panel">
            <div class="panel-title">
                <span>04 // CONTINUITY & FORENSIC LINEAGE</span>
                <span style="font-size: 9px; color: #507b8a;">EVIDENCE CHAIN</span>
            </div>
            <table class="forensic-lineage">
                <thead>
                    <tr>
                        <th>STAGE / STEP</th>
                        <th>REPRESENTATION / EVIDENCE SOURCE</th>
                        <th>PROVEN STATUS</th>
                    </tr>
                </thead>
                <tbody id="lineage-container">
                    <!-- Loaded dynamically -->
                </tbody>
            </table>
        </div>

        <div class="panel">
            <div class="panel-title">
                <span>05 // COUNTERFACTUAL FALSIFICATION LENS</span>
                <span style="font-size: 9px; color: #507b8a;">DIFFERENTIAL STANDARD</span>
            </div>
            <div class="diff-grid" id="diff-container">
                <!-- Loaded dynamically -->
            </div>
        </div>

    </div>

    <!-- Window E: Failure & Governance Boundaries -->
    <div class="panel" style="margin-bottom: 20px;">
        <div class="panel-title">
            <span>06 // FAILURE & GOVERNANCE BOUNDARIES</span>
            <span style="font-size: 9px; color: var(--accent-red);">BLOCKED ATTACKS</span>
        </div>
        <div id="failures-container" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); grid-gap: 15px;">
            <!-- Loaded dynamically -->
        </div>
    </div>

    <footer>
        SAGE OBSERVATORY LAYER v1.0.0 // BORINGLY EMPIRICAL // THE REPOSITORY REMAINS THE SOURCE OF TRUTH
    </footer>

    <script>
        async function fetchState() {
            try {
                const res = await fetch('/api/state');
                const data = await res.json();
                renderUI(data);
            } catch (err) {
                console.error("Failed to load SAGE Observatory State:", err);
            }
        }

        function renderUI(data) {
            // 1. Render Spine
            const spineContainer = document.getElementById('causal-spine-container');
            spineContainer.innerHTML = data.causal_spine.map(node => `
                <div class="spine-node">
                    <div class="status-dot ${node.status}"></div>
                    <div class="spine-content">
                        <span class="spine-name">${node.name}</span> - ${node.details}
                        <span class="spine-src">evidence: ${node.evidence_source || 'N/A'}</span>
                    </div>
                </div>
            `).join('');

            // 2. Render Balance
            const balanceContainer = document.getElementById('balance-container');
            const bal = data.homeostatic_balance;
            balanceContainer.innerHTML = `
                <div class="balance-item"><span class="balance-label">GOVERNANCE INVARIANTS (Namespace Drift)</span><span class="balance-val">${bal.namespace_drift}</span></div>
                <div class="balance-item"><span class="balance-label">EVIDENCE CONTINUITY (Lineage)</span><span class="balance-val" style="color: var(--accent-cyan);">${bal.lineage_completeness * 100}%</span></div>
                <div class="balance-item"><span class="balance-label">REGRESSION HEALTH</span><span class="balance-val">${bal.regression_health}</span></div>
                <div class="balance-item"><span class="balance-label">ARCHITECTURE LEANNESS</span><span class="balance-val">${bal.architecture_leanness}</span></div>
                <div class="balance-item"><span class="balance-label">EXECUTION HEALTH</span><span class="balance-val">${bal.execution_health}</span></div>
                <div class="balance-item"><span class="balance-label">AUTHORIZATION INTEGRITY</span><span class="balance-val">${bal.authorization_integrity}</span></div>
            `;

            // 3. Render Lineage
            const lineageContainer = document.getElementById('lineage-container');
            const lineageSteps = data.forensic_lineages.msn_differential_test;
            lineageContainer.innerHTML = lineageSteps.map(step => `
                <tr>
                    <td style="color: var(--text-bright); font-weight: bold;">${step.step}</td>
                    <td>${step.evidence}</td>
                    <td style="color: ${step.status === 'VERIFIED' ? 'var(--accent-green)' : '#507b8a'};">${step.status}</td>
                </tr>
            `).join('');

            // 4. Render Differential Proof
            const diffContainer = document.getElementById('diff-container');
            const diff = data.differential_lens;
            diffContainer.innerHTML = `
                <div class="diff-box">
                    <div class="diff-box-title">Primitive A (Alone)</div>
                    <div class="diff-result">${diff.primitive_a} -> <span style="color: var(--accent-yellow); font-weight: bold;">${diff.outcome_a}</span></div>
                </div>
                <div class="diff-box">
                    <div class="diff-box-title">Consumer B (Alone)</div>
                    <div class="diff-result">${diff.primitive_b} -> <span style="color: var(--accent-green); font-weight: bold;">${diff.outcome_b}</span></div>
                </div>
                <div class="diff-box" style="grid-column: span 2;">
                    <div class="diff-box-title">A + B Composition (Emergent Differential)</div>
                    <div class="diff-result">${diff.difference}</div>
                </div>
                <div class="emergent-banner">
                    Governance: ${diff.governance_status}
                </div>
            `;

            // 5. Render Failures
            const failuresContainer = document.getElementById('failures-container');
            failuresContainer.innerHTML = data.failure_boundaries.map(bound => `
                <div class="diff-box" style="border-color: var(--accent-red);">
                    <div class="diff-box-title" style="color: var(--accent-red); font-weight: bold;">${bound.type}</div>
                    <div style="color: var(--text-bright); margin-bottom: 5px;">${bound.description}</div>
                    <span class="spine-src">source boundary: ${bound.evidence_ref}</span>
                </div>
            `).join('');
        }

        // Initial fetch
        fetchState();
    </script>
</body>
</html>
"""
    return HTMLResponse(content=html_content, status_code=200)
