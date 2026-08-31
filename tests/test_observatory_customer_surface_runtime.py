import os
from pathlib import Path
from fastapi.testclient import TestClient

from sage.experimental.observatory.server import app as obs_app


def test_customer_surface_server_exposes_live_acceptance_and_nameplates():
    source = Path('sage/experimental/observatory/server.py').read_text(encoding='utf-8')
    assert 'CUSTOMER ACCEPTANCE SURFACE' in source
    assert '/api/state' in source
    assert '/api/hud' in source
    assert 'LIVE AGENT NAMEPLATES' in source
    assert 'setInterval(load,5000)' in source
    assert 'GOVERNED CHATGPT COMMAND CONSOLE' in source
    assert 'sendChatGPTQuery' in source
    assert '/ai/query/chatgpt' in source


def test_production_deploy_targets_customer_surface():
    docker = Path('Dockerfile').read_text(encoding='utf-8')
    render = Path('render.yaml').read_text(encoding='utf-8')
    expected = 'uvicorn sage.experimental.observatory.server:app'
    assert expected in docker
    assert expected in render
    assert 'COPY scripts/ ./scripts/' in docker


def test_observatory_server_mounts_runtime_and_delegates_root_api():
    client = TestClient(obs_app)

    # 1. Observatory customer endpoints
    assert client.get('/').status_code == 200
    assert client.get('/health').status_code == 200
    assert client.get('/api/state').status_code == 200
    assert client.get('/api/hud').status_code == 200

    # 2. Mounted /runtime endpoints
    assert client.get('/runtime/status').status_code == 200

    # 3. Delegated root REST API endpoints
    assert client.get('/status').status_code == 200
    assert client.get('/openapi.json').status_code == 200


def test_observatory_server_auth_middleware_bypass_rules(monkeypatch):
    monkeypatch.setenv("SAGE_REQUIRE_AUTH", "true")
    client = TestClient(obs_app)

    # Bypassed paths should succeed without auth
    assert client.get('/').status_code == 200
    assert client.get('/health').status_code == 200
    assert client.get('/api/state').status_code == 200
    assert client.get('/openapi.json').status_code == 200

    # Protected paths (both root and mounted under /runtime/) must enforce x-api-key
    assert client.get('/status').status_code == 401
    assert client.get('/runtime/status').status_code == 401
    assert client.get('/status', headers={'x-api-key': 'sage-default-key-2026'}).status_code == 200
    assert client.get('/runtime/status', headers={'x-api-key': 'sage-default-key-2026'}).status_code == 200
