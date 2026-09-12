"""SAGE AIET (Autonomous Intelligence Evaluation & Testing) Validation Lab package.

Exposes the 7 canonical seams for evaluating AI operational autonomy, adaptability,
transfer, and resilience without creating a second C2 authority layer.
"""

from sage.experimental.aiet.adapter import AIETControlAdapter
from sage.experimental.aiet.client import AIETExternalClient, AIETExternalClientError, AIETProviderConfig
from sage.experimental.aiet.server import (
    AIETExternalHarnessServer,
    AIETExternalServerError,
    AIETProviderAdapter,
    create_aiet_harness_app,
)
from sage.experimental.aiet.evaluator import AIETIndependentEvaluator
from sage.experimental.aiet.metrics import AIETMetricsCalculator, AIETPerformanceMetrics
from sage.experimental.aiet.perturbation import AIETPerturbationInjector, FailurePerturbation
from sage.experimental.aiet.receipt import AIETValidationReceipt
from sage.experimental.aiet.runner import AIETMissionRunner
from sage.experimental.aiet.scenario import AIETBlindScenario

__all__ = [
    "AIETBlindScenario",
    "AIETControlAdapter",
    "AIETExternalClient",
    "AIETExternalClientError",
    "AIETExternalHarnessServer",
    "AIETExternalServerError",
    "AIETIndependentEvaluator",
    "AIETProviderAdapter",
    "AIETMetricsCalculator",
    "AIETMissionRunner",
    "AIETPerformanceMetrics",
    "AIETPerturbationInjector",
    "AIETProviderConfig",
    "AIETValidationReceipt",
    "create_aiet_harness_app",
    "FailurePerturbation",
]
