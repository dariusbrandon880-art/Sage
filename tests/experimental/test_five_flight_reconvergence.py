from sage.experimental.five_flight_reconvergence import FlightEvidence, reconverge_five_flight_wave


def evidence(mission, commit="abc", verified=True, verdict="PASS"):
    return FlightEvidence(mission, commit, True, verified, verdict)


def test_complete_five_flight_wave_passes():
    missions = ("A", "B", "C", "D", "E")
    result = reconverge_five_flight_wave([evidence(m, "abc") for m in missions], missions, "abc")
    assert result.wave_verdict == "PASS"
    assert not result.missing


def test_missing_or_duplicate_flight_holds():
    missions = ("A", "B", "C", "D", "E")
    result = reconverge_five_flight_wave([evidence(m, "abc") for m in ("A", "B", "C", "D", "D")], missions, "abc")
    assert result.wave_verdict == "HOLD"
    assert result.missing == ("E",)
    assert result.duplicates == ("D",)


def test_stale_or_unverified_evidence_holds():
    missions = ("A", "B", "C", "D", "E")
    flights = [evidence(m, "abc") for m in missions]
    flights[-1] = evidence("E", "old")
    result = reconverge_five_flight_wave(flights, missions, "abc")
    assert result.wave_verdict == "HOLD"
    assert result.stale_commits == ("old",)
