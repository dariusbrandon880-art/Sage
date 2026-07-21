"""Tests for SAGE Intelligence Layer."""

from sage.intelligence.core import LLMBridge, ContextAwareRouter, PatternMatcher, ReasoningLoop


def test_context_aware_router():
    """Test routing based on registered category keywords."""
    router = ContextAwareRouter()
    router.add_route("database", ["postgres", "sqlite", "migrations"])
    router.add_route("security", ["oauth", "auth", "api key", "cipher"])

    assert router.route_context("Need to setup sqlite migrations") == "database"
    assert router.route_context("How to refresh oauth token?") == "security"
    assert router.route_context("General questions about testing") == "default"


def test_pattern_matcher_extraction():
    """Test dynamic regex-based template extraction."""
    extracted = PatternMatcher.extract_variables(
        text="Task T-800 is blocked by Database Connection Timeout",
        template="Task {task_id} is blocked by {blocker}",
    )
    assert extracted == {"task_id": "T-800", "blocker": "Database Connection Timeout"}


def test_llm_bridge_complete():
    """Test LLM bridge heuristic completion mock modes."""
    bridge = LLMBridge(provider="mock")

    # 1. High-load diagnostic trigger
    resp1 = bridge.complete("Please diagnose this environment's high memory load.")
    assert "Trigger proactive checkpoint" in resp1

    # 2. General resolve
    resp2 = bridge.complete("Hello, please answer yes or no.")
    assert "Autonomously resolved" in resp2


def test_reasoning_loop_cycle():
    """Test ReasoningLoop evaluate_task to decision mapping."""
    bridge = LLMBridge(provider="mock")
    loop = ReasoningLoop(bridge)

    eval_result1 = loop.evaluate_task(
        objective="Maintain continuous up-time",
        current_task="diagnose performance spikes",
        context={"ram_usage": "98%"},
    )
    assert eval_result1["recommended_action"] == "checkpoint"
    assert eval_result1["confidence_score"] == 0.95

    eval_result2 = loop.evaluate_task(
        objective="Maintain continuous up-time",
        current_task="solve database pool locks",
        context={"pool_active": 100},
    )
    assert eval_result2["recommended_action"] == "remediate"
