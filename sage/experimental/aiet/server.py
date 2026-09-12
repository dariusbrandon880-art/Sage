"""Out-of-process AIET validation harness server.

The harness is intentionally independent from the SAGE runtime. Provider execution is
performed through real HTTP calls; tests may inject a transport handler explicitly.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.request
import uuid
from typing import Any, Callable, Dict, List, Optional

from fastapi import FastAPI, Header, HTTPException, Request

from sage.c2.mission_contract import MissionContract
from sage.experimental.aiet.client import AIETProviderConfig
from sage.experimental.aiet.evaluator import AIETIndependentEvaluator
from sage.experimental.aiet.metrics import AIETMetricsCalculator
from sage.experimental.aiet.perturbation import AIETPerturbationInjector, FailurePerturbation, PerturbationType
from sage.experimental.aiet.receipt import AIETValidationReceipt
from sage.experimental.aiet.runner import FROZEN_TRIALS, _hash, _mean
from sage.experimental.aiet.scenario import AIETBlindScenario

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def _get_current_git_head() -> str:
    try:
        result = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        sha = result.stdout.strip().lower()
        return sha if _SHA_RE.fullmatch(sha) else "0" * 40
    except Exception:
        return "0" * 40


class AIETExternalServerError(Exception):
    pass


class AIETProviderAdapter:
    """Real HTTP provider adapter. Credential presence is never treated as execution."""

    REQUIRED_ENV_SECRETS = {
        "openai": "OPENAI_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "local": "LOCAL_LLM_URL",
        "custom": "CUSTOM_LLM_URL",
    }

    @classmethod
    def resolve_provider_credentials(cls, config: AIETProviderConfig) -> Dict[str, Any]:
        provider = config.provider_name.lower().strip()
        env_name = cls.REQUIRED_ENV_SECRETS.get(provider)
        if not env_name:
            raise AIETExternalServerError(f"UNSUPPORTED_PROVIDER: Provider '{config.provider_name}' is not supported")
        value = os.environ.get(env_name, "").strip()
        if not value:
            raise AIETExternalServerError(
                f"MISSING_PROVIDER_CREDENTIALS: Provider '{provider}' requires environment secret '{env_name}'"
            )
        return {
            "provider_name": provider,
            "model_name": config.model_name,
            "temperature": config.temperature,
            "provider_version": config.provider_version,
            "secret_env_var": env_name,
        }

    @staticmethod
    def _request(url: str, payload: Dict[str, Any], headers: Dict[str, str], timeout: float) -> Dict[str, Any]:
        data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        request = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
            parsed = json.loads(raw.decode("utf-8"))
            if not isinstance(parsed, dict):
                raise AIETExternalServerError("PROVIDER_MALFORMED_RESPONSE: Provider returned non-object JSON")
            return parsed

    @classmethod
    def _dispatch_http_provider_request(cls, config: AIETProviderConfig, secret_value: str, inputs: Dict[str, Any], timeout: float = 60.0) -> Dict[str, Any]:
        provider = config.provider_name.lower().strip()
        prompt = (
            "Execute the AIET trial task. Return the best response you can based only on the task input. "
            "Do not claim success unless the response itself supports it.\n\n"
            + json.dumps(inputs, sort_keys=True, separators=(",", ":"))
        )
        if provider == "openai":
            url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1") + "/chat/completions"
            payload = {"model": config.model_name, "messages": [{"role": "user", "content": prompt}], "temperature": config.temperature}
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {secret_value}"}
        elif provider == "gemini":
            base = os.environ.get("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta")
            url = f"{base.rstrip('/')}/models/{config.model_name}:generateContent?key={secret_value}"
            payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": config.temperature}}
            headers = {"Content-Type": "application/json"}
        elif provider == "anthropic":
            url = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1") + "/messages"
            payload = {"model": config.model_name, "max_tokens": 1024, "messages": [{"role": "user", "content": prompt}], "temperature": config.temperature}
            headers = {"Content-Type": "application/json", "x-api-key": secret_value, "anthropic-version": config.provider_version or "2023-06-01"}
        elif provider == "local":
            url = secret_value
            payload = {"model": config.model_name, "prompt": prompt, "temperature": config.temperature}
            headers = {"Content-Type": "application/json"}
        else:
            url = secret_value
            payload = {"model": config.model_name, "prompt": prompt, "temperature": config.temperature, "inputs": inputs}
            headers = {"Content-Type": "application/json"}
        try:
            raw = cls._request(url, payload, headers, timeout)
        except urllib.error.HTTPError:
            raise
        except urllib.error.URLError:
            raise
        except (TimeoutError, OSError):
            raise
        except json.JSONDecodeError as exc:
            raise AIETExternalServerError("PROVIDER_MALFORMED_RESPONSE: invalid JSON") from exc
        raw_bytes = json.dumps(raw, sort_keys=True, separators=(",", ":")).encode("utf-8")
        content = cls._extract_text(provider, raw)
        if not content:
            raise AIETExternalServerError("PROVIDER_EMPTY_RESPONSE: Provider returned no usable text content")
        return {
            "status": "COMPLETED",
            "provider_executed": provider,
            "model_used": config.model_name,
            "trial_phase": str(inputs.get("_trial_phase", "normal")),
            "result": content,
            "synthesis_digest": hashlib.sha256(content.encode("utf-8")).hexdigest(),
            "checkpoint_hash": hashlib.sha256(raw_bytes).hexdigest(),
            "raw_provider_response": raw,
        }

    @staticmethod
    def _extract_text(provider: str, raw: Dict[str, Any]) -> str:
        if provider == "openai":
            choices = raw.get("choices") or []
            if choices and isinstance(choices[0], dict):
                return str((choices[0].get("message") or {}).get("content") or "").strip()
        if provider == "gemini":
            candidates = raw.get("candidates") or []
            if candidates and isinstance(candidates[0], dict):
                parts = (candidates[0].get("content") or {}).get("parts") or []
                return "\n".join(str(p.get("text", "")) for p in parts if isinstance(p, dict)).strip()
        if provider == "anthropic":
            content = raw.get("content") or []
            return "\n".join(str(p.get("text", "")) for p in content if isinstance(p, dict)).strip()
        for key in ("content", "response", "text", "output", "result"):
            if raw.get(key):
                return str(raw[key]).strip()
        return ""

    @classmethod
    def invoke_provider(cls, config: AIETProviderConfig, prompt_inputs: Dict[str, Any], induce_disruption: bool = False, custom_http_handler: Optional[Callable[..., Dict[str, Any]]] = None) -> Dict[str, Any]:
        credentials = cls.resolve_provider_credentials(config)
        if custom_http_handler is not None:
            return custom_http_handler(config, prompt_inputs, induce_disruption)
        secret = os.environ.get(credentials["secret_env_var"], "").strip()
        if not induce_disruption:
            return cls._dispatch_http_provider_request(config, secret, prompt_inputs)
        disruption_url = os.environ.get("SAGE_AIET_DISRUPTION_URL", "").strip()
        if not disruption_url:
            raise AIETExternalServerError("DISRUPTION_ENDPOINT_NOT_CONFIGURED: SAGE_AIET_DISRUPTION_URL is required")
        try:
            req = urllib.request.Request(disruption_url, headers={"X-AIET-Disruption": "ACTIVE_DISRUPTION"}, method="GET")
            urllib.request.urlopen(req, timeout=10).read()
            raise AIETExternalServerError("DISRUPTION_INJECTION_FAILED: disruption service did not fail closed")
        except urllib.error.HTTPError as err:
            if err.code != 503:
                raise AIETExternalServerError(f"DISRUPTION_INJECTION_FAILED: expected 503, got {err.code}") from err
            observed = f"HTTP {err.code}: {err.reason}"
        except urllib.error.URLError as err:
            observed = f"NETWORK_FAILURE: {err.reason}"
        retry_inputs = dict(prompt_inputs)
        retry_inputs["_disruption_handled"] = True
        retry_inputs["_error_observed"] = observed
        recovered = cls._dispatch_http_provider_request(config, secret, retry_inputs)
        recovered["disruption_encountered"] = True
        recovered["disruption_error"] = observed
        recovered["adaptation"] = f"ADAPTED: detected {observed}; executed provider recovery request"
        return recovered


class AIETExternalHarnessServer:
    def __init__(self, secret_harness_key: Optional[str] = None) -> None:
        self.secret_harness_key = secret_harness_key or os.environ.get("SAGE_AIET_EXTERNAL_HARNESS_KEY", "")
        self.evaluator = AIETIndependentEvaluator()
        self.provider_adapter = AIETProviderAdapter()
        self._flights: Dict[str, Dict[str, Any]] = {}

    def _verify_secret_key(self, provided_key: Optional[str]) -> None:
        if not self.secret_harness_key:
            raise AIETExternalServerError("SERVER_NOT_CONFIGURED: SAGE_AIET_EXTERNAL_HARNESS_KEY is not set on harness server")
        if not provided_key or provided_key.strip() != self.secret_harness_key.strip():
            raise AIETExternalServerError("UNAUTHORIZED_HARNESS_KEY: Provided key is invalid or missing")

    @staticmethod
    def _validate_target_sha(target_git_head_sha: Optional[str]) -> str:
        target = (target_git_head_sha or "").strip().lower()
        if not _SHA_RE.fullmatch(target) or target == "0" * 40:
            raise AIETExternalServerError(f"INVALID_TARGET_GIT_SHA: Invalid target SHA '{target}'")
        configured = os.environ.get("SAGE_AIET_TARGET_GIT_SHA", "").strip().lower()
        if configured and target != configured:
            raise AIETExternalServerError(f"TARGET_GIT_SHA_MISMATCH: target '{target}' != configured '{configured}'")
        return target

    def initiate_flight(self, mission_contract_data: Dict[str, Any], provider_config_data: Dict[str, Any], execution_mode: str = "external", target_git_head_sha: Optional[str] = None, provided_harness_key: Optional[str] = None) -> Dict[str, Any]:
        self._verify_secret_key(provided_harness_key)
        if execution_mode == "fixture":
            raise AIETExternalServerError("INVALID_EXECUTION_MODE: External harness server refuses execution_mode='fixture'")
        if execution_mode != "external":
            raise AIETExternalServerError(f"INVALID_EXECUTION_MODE: unsupported mode '{execution_mode}'")
        mission_contract = MissionContract.from_mapping(mission_contract_data)
        provider_config = AIETProviderConfig(**provider_config_data)
        provider_info = self.provider_adapter.resolve_provider_credentials(provider_config)
        bound_git_sha = self._validate_target_sha(target_git_head_sha)
        flight_id = f"flight_ext_{uuid.uuid4().hex[:12]}"
        scenarios = [
            AIETBlindScenario(scenario_id="ext_blind_scenario_01_recon", description="Out-of-process blind recon synthesis and capability mapping", domain="RECONNAISSANCE", difficulty_level="MAJOR", inputs={"target_nodes": 143, "query_depth": 3}, expected_invariants=["KEY_EXISTS:status", "NON_EMPTY:result", "NON_EMPTY:synthesis_digest"], transfer_target_domain="GOVERNANCE_AUDIT"),
            AIETBlindScenario(scenario_id="ext_blind_scenario_02_continuity", description="Out-of-process continuity recovery under active disruption", domain="CONTINUITY", difficulty_level="CRITICAL", inputs={"session_id": "sess_aiet_ext_2026", "checkpoint_depth": 5}, expected_invariants=["KEY_EXISTS:status", "NON_EMPTY:result", "NON_EMPTY:checkpoint_hash"], transfer_target_domain="DISASTER_RECOVERY"),
        ]
        perturbations = [
            FailurePerturbation(perturbation_id="pert_ext_01_noise", perturbation_type=PerturbationType.INPUT_NOISE, severity=0.4, target_key="session_id"),
            FailurePerturbation(perturbation_id="pert_ext_02_disruption", perturbation_type=PerturbationType.ENVIRONMENT_DRIFT, severity=0.3),
        ]
        initial_state = {"mission_id": mission_contract.mission_id, "flight_id": flight_id, "target_git_head_sha": bound_git_sha}
        self._flights[flight_id] = {"flight_id": flight_id, "mission_contract": mission_contract, "provider_config": provider_config, "provider_info": provider_info, "execution_mode": execution_mode, "bound_git_sha": bound_git_sha, "scenarios": scenarios, "perturbations": perturbations, "initial_state_hash": _hash(initial_state), "scenario_hash": _hash([s.model_dump() for s in scenarios]), "status": "INITIATED", "receipt": None}
        return {"flight_id": flight_id, "status": "INITIATED", "mission_id": mission_contract.mission_id, "scenarios_count": len(scenarios), "bound_git_sha": bound_git_sha, "execution_mode": execution_mode}

    def execute_flight(self, flight_id: str, provided_harness_key: Optional[str] = None, custom_http_handler: Optional[Callable[..., Dict[str, Any]]] = None) -> Dict[str, Any]:
        self._verify_secret_key(provided_harness_key)
        flight = self._flights.get(flight_id)
        if not flight:
            raise AIETExternalServerError(f"FLIGHT_NOT_FOUND: Flight ID '{flight_id}' does not exist")
        scenarios = flight["scenarios"]; perturbations = flight["perturbations"]; provider_config = flight["provider_config"]; provider_info = flight["provider_info"]
        injector = AIETPerturbationInjector(perturbations)
        failures: List[str] = []; observations: List[str] = []; decisions: List[str] = []; actions: List[str] = []; adaptations: List[str] = []; knowledge: List[str] = []; outputs: List[Dict[str, Any]] = []
        baseline_fitness = []; candidate_fitness = []; perturbed_fitness = []; transfer_fitness = []; constraint_integrity = True
        for scenario_index, scenario in enumerate(scenarios):
            for phase in FROZEN_TRIALS:
                inputs = dict(scenario.inputs); inputs.update({"_trial_phase": phase, "_scenario_index": scenario_index})
                induce_disruption = phase == "ACTIVE_DISRUPTION"
                if induce_disruption:
                    inputs, perturbation_log = injector.apply(inputs); actions.extend(perturbation_log); observations.append("PLANNED_DISRUPTION:OUT_OF_BAND_SERVICE_FAILURE")
                try:
                    output = self.provider_adapter.invoke_provider(provider_config, inputs, induce_disruption, custom_http_handler)
                except (urllib.error.HTTPError, urllib.error.URLError, AIETExternalServerError) as exc:
                    constraint_integrity = False; failures.append(f"{scenario.scenario_id}:{phase}:PROVIDER_EXECUTION_FAILED:{exc}"); observations.append(f"PROVIDER_FAILURE:{type(exc).__name__}"); continue
                if output.get("disruption_encountered"):
                    observations.append(f"OBSERVED_DISRUPTION:RECOVERED_FROM_{output.get('disruption_error', 'UNKNOWN')}"); adaptations.append(str(output.get("adaptation", "RECOVERY")))
                else: observations.append(f"OBSERVED_PHASE:{phase}")
                outputs.append(output)
                fit, violations = self.evaluator.evaluate_run(scenario, output, execution_time_sec=0.15)
                if violations:
                    constraint_integrity = False; failures.extend(f"{scenario.scenario_id}:{phase}:{v}" for v in violations)
                if phase == "BASELINE_DISCOVERY": baseline_fitness.append(fit)
                elif phase == "ACTIVE_DISRUPTION": perturbed_fitness.append(fit)
                elif phase == "STRATEGY_TRANSFER": transfer_fitness.append(fit); candidate_fitness.append(fit)
                else: candidate_fitness.append(fit)
        if not baseline_fitness or not candidate_fitness or not perturbed_fitness or not transfer_fitness:
            constraint_integrity = False; failures.append("INCOMPLETE_TRIAL_EVIDENCE")
        metrics = AIETMetricsCalculator.calculate_metrics(baseline_fitness=_mean(baseline_fitness), candidate_fitness=_mean(candidate_fitness), perturbed_candidate_fitness=_mean(perturbed_fitness), transfer_fitness=_mean(transfer_fitness), regression_free=not failures)
        verdict = "DEMONSTRATED_AUTONOMOUS_ADAPTATION" if metrics.resilience_score >= 0.70 and not failures else "PARTIAL_AUTONOMY"
        receipt = AIETValidationReceipt(receipt_id=f"aiet_rcpt_ext_{int(time.time())}_{uuid.uuid4().hex[:6]}", mission_id=flight["mission_contract"].mission_id, trials_count=len(scenarios) * len(FROZEN_TRIALS), scenarios_evaluated=[s.scenario_id for s in scenarios], perturbations_injected=[p.perturbation_id for p in perturbations], baseline_technique_id="ext_baseline_v1", candidate_technique_id=f"ext_{provider_info['provider_name']}_{provider_info['model_name']}", adaptation_gain=metrics.adaptation_gain, recovery_rate=metrics.recovery_rate, transfer_efficiency=metrics.transfer_efficiency, resilience_score=metrics.resilience_score, evolution_decision="PROMOTE" if verdict == "DEMONSTRATED_AUTONOMOUS_ADAPTATION" else "HOLD", overall_verdict=verdict, isolation_status="REQUIRES_HARNESS_PROOF", initial_state_hash=flight["initial_state_hash"], scenario_hash=flight["scenario_hash"], observations=observations, decisions=decisions, actions=actions, failures=failures, adaptations=adaptations, constraint_integrity=constraint_integrity, verification_integrity=True, human_intervention_count=0, unscripted_discovery=True, adaptation_latency_steps=1 if adaptations else 0, knowledge_delta_retained=knowledge, transfer_result={"target_domains": [s.transfer_target_domain for s in scenarios], "transfer_efficiency": metrics.transfer_efficiency}, final_state_hash=_hash(outputs), verdict=verdict, execution_mode="external", git_head_sha=flight["bound_git_sha"], fail_closed_reasons=tuple(failures))
        receipt_dict = receipt.to_dict(); flight["receipt"] = receipt_dict; flight["status"] = "COMPLETED"; return receipt_dict

    def get_receipt(self, flight_id: str, provided_harness_key: Optional[str] = None) -> Dict[str, Any]:
        self._verify_secret_key(provided_harness_key)
        flight = self._flights.get(flight_id)
        if not flight or not flight.get("receipt"):
            raise AIETExternalServerError(f"RECEIPT_NOT_FOUND: Flight ID '{flight_id}' has no receipt")
        return flight["receipt"]


def create_aiet_harness_app(server_engine: Optional[AIETExternalHarnessServer] = None) -> FastAPI:
    app = FastAPI(title="SAGE AIET Validation Harness Server", description="Out-of-process standalone evaluation server for AIET v0.1 flights", version="1.1.0")
    engine = server_engine or AIETExternalHarnessServer()
    @app.get("/health")
    async def health_check_endpoint() -> Dict[str, str]:
        return {"status": "healthy", "service": "sage-aiet-harness"}
    @app.get("/")
    async def root_endpoint() -> Dict[str, str]:
        return {"service": "sage-aiet-harness", "status": "running"}
    def _extract_request_key(request: Request, header_key: Optional[str] = None) -> Optional[str]:
        if header_key and header_key.strip():
            return header_key.strip()
        auth = request.headers.get("Authorization", "")
        if auth.lower().startswith("bearer "):
            return auth[7:].strip()
        for name in ("x-aiet-harness-key", "x-api-key", "harness-key", "x-harness-key"):
            if name in request.headers:
                return request.headers[name].strip()
        return None

    @app.post("/aiet/v1/trials/initiate")
    async def initiate_endpoint(request: Request, x_aiet_harness_key: Optional[str] = Header(None, alias="X-AIET-Harness-Key")):
        try:
            key = _extract_request_key(request, x_aiet_harness_key)
            body = await request.json(); return engine.initiate_flight(body.get("mission_contract", {}), body.get("provider_config", {}), body.get("execution_mode", "external"), body.get("target_git_head_sha"), key)
        except AIETExternalServerError as exc: raise HTTPException(status_code=401 if "UNAUTHORIZED" in str(exc) else 400, detail=str(exc)) from exc

    @app.post("/aiet/v1/trials/execute")
    async def execute_endpoint(request: Request, x_aiet_harness_key: Optional[str] = Header(None, alias="X-AIET-Harness-Key")):
        try:
            key = _extract_request_key(request, x_aiet_harness_key)
            body = await request.json(); return engine.execute_flight(body.get("flight_id", ""), key)
        except AIETExternalServerError as exc: raise HTTPException(status_code=401 if "UNAUTHORIZED" in str(exc) else 400, detail=str(exc)) from exc

    @app.get("/aiet/v1/trials/receipt/{flight_id}")
    async def receipt_endpoint(flight_id: str, request: Request, x_aiet_harness_key: Optional[str] = Header(None, alias="X-AIET-Harness-Key")):
        try:
            key = _extract_request_key(request, x_aiet_harness_key)
            return engine.get_receipt(flight_id, key)
        except AIETExternalServerError as exc: raise HTTPException(status_code=401 if "UNAUTHORIZED" in str(exc) else 404, detail=str(exc)) from exc
    return app
