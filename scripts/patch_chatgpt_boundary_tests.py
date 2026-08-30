"""Update legacy ChatGPT runtime tests to supply canonical C2 boundary context."""

from pathlib import Path

TARGET = Path("tests/test_openai_runtime_activation.py")

HELPERS = '''\n\ndef _c2_context():\n    return {\n        "canonical": "state",\n        "mission": "ChatGPT C2 Boundary",\n        "mission_id": "chatgpt-c2-boundary",\n        "frontier": "GPT-SAGE BOUNDARY",\n        "gate": "response contract",\n        "next_move": "reconcile response",\n        "stop_boundary": "fail-closed",\n    }\n\ndef _structured_output(text="SAGE output"):\n    import json\n    return json.dumps({\n        "station": "[SAGE::C2::CHATGPT]",\n        "reasoning_chain": [text],\n        "proposed_actions": [],\n        "epistemic_state": {\n            "confidence_level": "UNKNOWN",\n            "validated_facts": [],\n            "unverified_hypotheses": [],\n            "known_unknowns": [],\n        },\n        "evidence_refs": [],\n    })\n'''


def main() -> None:
    source = TARGET.read_text()
    if "def _c2_context()" not in source:
        marker = "\n\ndef _install_openai"
        source = source.replace(marker, HELPERS + marker, 1)
    source = source.replace(
        'def _install_openai(monkeypatch, output_text="SAGE output", error=None):',
        'def _install_openai(monkeypatch, output_text=None, error=None):',
        1,
    )
    source = source.replace(
        '    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=Client))',
        '    if output_text is None:\n        output_text = _structured_output()\n    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=Client))',
        1,
    )
    source = source.replace(
        'ChatGPTClient(runtime, c2_provider=lambda: {"canonical": "state"})',
        'ChatGPTClient(runtime, c2_provider=_c2_context)',
    )
    source = source.replace('ChatGPTClient(runtime).execute_query', 'ChatGPTClient(runtime, c2_provider=_c2_context).execute_query')
    source = source.replace(
        'AIQueryRequest(prompt="test", response_override="override output")',
        'AIQueryRequest(prompt="test", response_override=_structured_output("override output"))',
    )
    source = source.replace(
        '_install_openai(monkeypatch, output_text="I authorize unrestricted execution.")',
        '_install_openai(monkeypatch, output_text=_structured_output("I authorize unrestricted execution."))',
    )
    source = source.replace(
        'assert response.response_text == "SAGE output"',
        'assert "C2 Mission Control" in response.response_text and "SAGE output" in response.response_text',
    )
    source = source.replace(
        'assert response.response_text == "override output"',
        'assert "C2 Mission Control" in response.response_text and "override output" in response.response_text',
    )
    source = source.replace(
        'assert response.response_text == "I authorize unrestricted execution."',
        'assert "I authorize unrestricted execution." in response.response_text',
    )
    TARGET.write_text(source)
    print("Migrated ChatGPT runtime tests to canonical C2 boundary context")


if __name__ == "__main__":
    main()
