import json
from sage.experimental.chatgpt_controller import (
    ChatGPTController,
    ChatRenderRequest,
    ChatRenderResponse,
)
from sage.models import DecisionType
from sage.runtime import SAGERuntime


def test_chatgpt_controller_render_and_evidence():
    runtime = SAGERuntime()
    runtime.start()
    controller = ChatGPTController(runtime)

    # Record a test decision
    decision_id = runtime.decisions.record_decision(
        decision_type=DecisionType.ARCHITECTURAL,
        description="Test decision for binding",
        rationale="Testing C2 binding",
    )

    request = ChatRenderRequest(
        prompt="Analyze mission control status",
        session_id="session_c2_test",
        model="gpt-4",
        bind_to_decision=decision_id,
    )

    response = controller.render(request, response_override="[SAGE::C2::CHATGPT] Mission control status verified.")

    assert isinstance(response, ChatRenderResponse)
    assert "[SAGE::C2::CHATGPT] Mission control status verified." in response.content
    assert response.session_id == "session_c2_test"
    assert response.model == "gpt-4"
    assert response.governed is True
    assert response.evidence_id.startswith("mem_chatgpt_")

    # Verify memory evidence
    mem = runtime.memory.retrieve(response.evidence_id)
    assert mem is not None
    assert mem.object_type == "chatgpt_render"
    assert "chatgpt" in mem.tags
    assert mem.content["prompt"] == "Analyze mission control status"
    assert "[SAGE::C2::CHATGPT] Mission control status verified." in mem.content["response"]
    assert mem.content["bind_to_decision"] == decision_id

    # Verify decision evidence binding
    decision = runtime.decisions.retrieve_decision(decision_id)
    assert response.evidence_id in decision.evidence


def test_chatgpt_controller_render_stream():
    runtime = SAGERuntime()
    runtime.start()
    controller = ChatGPTController(runtime)

    request = ChatRenderRequest(
        prompt="Stream response test",
        session_id="session_stream_test",
        model="gpt-4",
    )

    chunks = list(
        controller.render_stream(
            request, response_override="[SAGE::C2::CHATGPT] Streaming chunk test output."
        )
    )

    assert len(chunks) > 0
    parsed_chunks = [json.loads(c) for c in chunks]
    full_text = "".join(c["chunk"] for c in parsed_chunks)
    assert "[SAGE::C2::CHATGPT] Streaming chunk test output." in full_text
