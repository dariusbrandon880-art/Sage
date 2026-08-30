from sage.c2.conversation_provenance import (
    Station,
    classify_director_input,
    classify_relayed_station_message,
    distinguish_input_from_relay,
)


def test_director_input_is_distinct_from_station_report():
    item = classify_director_input("Check Jules' report")
    assert item.sender is Station.DIRECTOR
    assert item.recipient is Station.C2_CHATGPT
    assert item.message_kind == "director_input"
    assert item.source == "operator_input"


def test_relay_preserves_jules_identity():
    item = classify_relayed_station_message(sender=Station.ENGINEER_JULES, content="Tests passed")
    assert item.sender is Station.ENGINEER_JULES
    assert item.recipient is Station.C2_CHATGPT
    assert item.message_kind == "station_relay"
    assert item.source == "human_relay"


def test_relay_preserves_gemini_identity():
    item = classify_relayed_station_message(sender=Station.INTEL_GEMINI, content="Challenge result")
    assert item.sender is Station.INTEL_GEMINI


def test_context_boundary_separates_director_from_relays():
    context = distinguish_input_from_relay(
        director_content="Reconcile this",
        relayed_messages={Station.ENGINEER_JULES: "Implemented it", Station.INTEL_GEMINI: "Challenge it"},
    )
    assert context["director_input"]["sender"] == Station.DIRECTOR.value
    assert [x["sender"] for x in context["relayed_station_messages"]] == [
        Station.ENGINEER_JULES.value,
        Station.INTEL_GEMINI.value,
    ]
    assert context["relay_authority"] == "non_canonical_input_until_reconciled"


def test_director_cannot_be_mislabelled_as_relay():
    try:
        classify_relayed_station_message(sender=Station.DIRECTOR, content="directive")
    except ValueError:
        pass
    else:
        raise AssertionError("Director input was accepted as a station relay")


def test_envelope_is_immutable():
    item = classify_director_input("do work")
    try:
        item.content = "changed"
    except Exception:
        pass
    else:
        raise AssertionError("conversation envelope was mutable")
