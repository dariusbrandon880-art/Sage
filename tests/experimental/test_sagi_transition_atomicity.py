"""Adversarial tests for SAGI evolution transition atomicity and recovery."""

from copy import deepcopy

import pytest

from sage.experimental.sagi.controller import SAGIEvolutionController


class RaisingVerifier:
    def verify_proposal(self, state, candidate):
        raise RuntimeError("injected transition interruption")


def test_evolution_cycle_rolls_back_state_and_controller_metrics_on_exception():
    controller = SAGIEvolutionController(verifier=RaisingVerifier())
    before_state = deepcopy(controller.state)
    before_failures = deepcopy(controller.generator.failure_memory)
    before_receipts = deepcopy(controller.receipt_history)

    with pytest.raises(RuntimeError, match="injected transition interruption"):
        controller.execute_evolution_cycle()

    assert controller.state == before_state
    assert controller.state.verify_integrity() is True
    assert controller.generator.failure_memory == before_failures
    assert controller.receipt_history == before_receipts
    assert controller.successful_cycles == 0
    assert controller.failed_cycles == 0


def test_post_transition_integrity_failure_rolls_back_every_mutation():
    controller = SAGIEvolutionController()
    before_state = deepcopy(controller.state)
    before_failures = deepcopy(controller.generator.failure_memory)
    before_receipts = deepcopy(controller.receipt_history)

    def fail_integrity(_parent_hash):
        raise RuntimeError("injected integrity failure")

    controller._assert_transition_integrity = fail_integrity

    with pytest.raises(RuntimeError, match="injected integrity failure"):
        controller.execute_evolution_cycle()

    assert controller.state == before_state
    assert controller.state.verify_integrity() is True
    assert controller.generator.failure_memory == before_failures
    assert controller.receipt_history == before_receipts
    assert controller.successful_cycles == 0
    assert controller.failed_cycles == 0


def test_successful_transition_still_emits_integrity_verified_receipt():
    controller = SAGIEvolutionController()

    receipt = controller.execute_evolution_cycle()

    assert receipt.parent_state_hash != receipt.next_state_hash
    assert receipt.verify_integrity() is True
    assert controller.state.verify_integrity() is True
    assert controller.receipt_history == [receipt]
