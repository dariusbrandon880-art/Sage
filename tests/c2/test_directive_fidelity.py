"""Unit tests for Flight A: Directive Fidelity & Exact-Order Sentinel."""

from sage.c2.directive_fidelity import (
    DirectiveContract,
    DirectiveFingerprint,
    ExactOrderSentinel,
)


def test_directive_fingerprint_creation():
    raw_instruction = (
        "Check live repo.\n"
        "Inspect PR.\n"
        "Run verification.\n"
        "Do not merge."
    )
    contract = DirectiveFingerprint.create_contract(raw_instruction, directive_id="dir-test-01")

    assert contract.directive_id == "dir-test-01"
    assert len(contract.raw_instruction_hash) == 64
    assert len(contract.ordered_actions) == 3
    assert contract.ordered_actions[0].action == "Check live repo."
    assert contract.ordered_actions[1].action == "Inspect PR."
    assert contract.ordered_actions[2].action == "Run verification."
    assert len(contract.explicit_constraints) == 1
    assert contract.explicit_constraints[0] == "Do not merge."
    assert "merge" in contract.forbidden_additions


def test_exact_order_sentinel_valid_plan():
    raw_instruction = (
        "Check live repo.\n"
        "Inspect PR.\n"
        "Run verification.\n"
        "Do not merge."
    )
    contract = DirectiveFingerprint.create_contract(raw_instruction)

    proposed_plan = [
        "Check live repo",
        "Inspect PR",
        "Run verification",
    ]

    result = ExactOrderSentinel.validate_plan(contract, proposed_plan)
    assert result.is_valid is True
    assert len(result.violations) == 0


def test_exact_order_sentinel_rejects_forbidden_addition():
    raw_instruction = (
        "Check live repo.\n"
        "Inspect PR.\n"
        "Run verification.\n"
        "Do not merge."
    )
    contract = DirectiveFingerprint.create_contract(raw_instruction)

    proposed_plan = [
        "Check live repo",
        "Inspect PR",
        "Run verification",
        "Merge PR",
    ]

    result = ExactOrderSentinel.validate_plan(contract, proposed_plan)
    assert result.is_valid is False
    assert any("Forbidden action addition detected" in v for v in result.violations)
    assert any("merge" in v for v in result.violations)
