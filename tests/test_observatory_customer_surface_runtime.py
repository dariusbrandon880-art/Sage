from pathlib import Path


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
