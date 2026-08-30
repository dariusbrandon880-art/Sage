"""Tests for live capability execution boundary hardening."""

import pytest
from sage.c2.live_operation_receipt import execute_live_capability


class ValidCapability:
    capability_id = "cap_sensor_01"

    def invoke(self, *, operation: str, task: str):
        return {
            "target_resource": "sensor_feed_alpha",
            "success": True,
            "result": {"status": "ACTIVE", "task": task},
        }


class EmptyCapabilityID:
    capability_id = ""

    def invoke(self, *, operation: str, task: str):
        return {"target_resource": "sensor_feed_alpha", "success": True}


class MissingTargetResource:
    capability_id = "cap_sensor_02"

    def invoke(self, *, operation: str, task: str):
        return {"success": True}


def test_positive_live_capability_execution():
    cap = ValidCapability()
    receipt = execute_live_capability(cap, operation="verify_sensor", task="check feed")
    assert receipt.capability == "cap_sensor_01"
    assert receipt.target_resource == "sensor_feed_alpha"
    assert receipt.verify() is True


def test_empty_capability_id_raises_value_error():
    cap = EmptyCapabilityID()
    with pytest.raises(ValueError, match="Live capability must have a non-empty capability_id"):
        execute_live_capability(cap, operation="verify_sensor", task="check feed")


def test_missing_target_resource_raises_value_error():
    cap = MissingTargetResource()
    with pytest.raises(ValueError, match="Live capability result is missing target_resource"):
        execute_live_capability(cap, operation="verify_sensor", task="check feed")
