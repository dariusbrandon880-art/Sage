from sage import cli


def test_c2_response_renders_canonical_nameplate(monkeypatch, capsys):
    monkeypatch.setattr(
        "sage.agent_presence.render_chat_identity",
        lambda station_id="MISSION_CONTROL": "[SAGE::C2::CHATGPT] • CQL-9 • XP 42 • EXECUTING",
    )

    cli._print_c2_response("response body", runtime=None)

    rendered = capsys.readouterr().out
    assert rendered.splitlines()[0] == "[SAGE::C2::CHATGPT] • CQL-9 • XP 42 • EXECUTING"
    assert rendered.splitlines()[1] == "response body"
