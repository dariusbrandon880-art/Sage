from sage.c2.frontier_scanner import overlapping_frontiers
from sage.c2.mission_contract import MissionContract, MissionContractError


def test_contract_parses_and_enforces_authority_boundary():
    contract = MissionContract.from_mapping(
        {
            "schema_version": "1.0",
            "mission_id": "FLIGHT-TEST-01",
            "intent": "Validate bounded execution",
            "authority_boundary": {
                "allowed_paths": ["sage/c2/**", "tests/governance/**"],
                "prohibited_paths": ["docs/master/**"],
            },
            "completion_criteria": {
                "required_tests": ["tests/governance/test_executable_mission_contracts.py"],
                "min_coverage_pct": 90,
                "provenance_required": True,
            },
            "stop_the_line_conditions": ["CROSS_BOUNDARY_FILE_TOUCH"],
        }
    )

    assert contract.check_paths(["sage/c2/mission_contract.py"]) == ()
    assert contract.check_paths(["docs/master/CONSTITUTION.md"]) == ("PROHIBITED_PATH:docs/master/CONSTITUTION.md",)
    assert contract.check_paths(["sage/runtime/model_gateway.py"]) == ("OUTSIDE_BOUNDARY:sage/runtime/model_gateway.py",)
    assert contract.requires_stop(["CROSS_BOUNDARY_FILE_TOUCH"]) == ("CROSS_BOUNDARY_FILE_TOUCH",)
    assert contract.completion_gates()["provenance_required"] is True


def test_contract_rejects_invalid_schema_values():
    try:
        MissionContract.from_mapping(
            {
                "schema_version": "2.0",
                "mission_id": "bad",
                "intent": "bad",
            }
        )
    except MissionContractError:
        pass
    else:
        raise AssertionError("unsupported contract schema must fail closed")


def test_frontier_overlap_detection_is_deterministic():
    assert overlapping_frontiers(
        {
            "F1": ["sage/c2/a.py", "sage/c2/b.py"],
            "F2": ["sage/c2/c.py"],
            "F3": ["sage/c2/b.py", "tests/test_b.py"],
        }
    ) == {("F1", "F3")}
