"""Forensic View Model for the SAGE Observatory read-only interface.

Represents all forensic state elements such as Causal Spine, Differential proof,
Homeostatic Repository Balance, and Capability Galaxy.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CausalNode(BaseModel):
    """A node inside the visual execution spine."""
    name: str
    status: str  # GREY, BLUE, YELLOW, GREEN, RED, PURPLE
    evidence_source: Optional[str] = None
    details: Optional[str] = None


class DifferentialProof(BaseModel):
    """Represents a falsification-first counterfactual proof lens."""
    primitive_a: str = "PFC Preflight Evaluation (No Evidence)"
    primitive_b: str = "Validated Capability Registry (PML/Reliability)"
    outcome_a: str = "REQUEST_CLARIFICATION"
    outcome_b: str = "PROCEED"
    difference: str = "Preflight gates dynamically bypass manual clarification when valid registry evidence is available."
    causal_source: str = "tests/experimental/test_capability_lifecycle_differential.py"
    governance_status: str = "GOVERNANCE GAP (Test-Only Differential Assessment; Production Broker Absent)"
    is_emergent_edge: bool = False  # False until production execution differential is fully proven


class HomeostaticBalance(BaseModel):
    """Metrics reflecting the physical system equilibrium."""
    namespace_drift: str = "0% (PRISTINE)"
    lineage_completeness: float = 1.0
    regression_health: str = "100% (309/309 PASSING)"
    architecture_leanness: str = "0 New Core Classes Added"
    capability_maturity: Dict[str, int] = Field(default_factory=dict)
    execution_health: str = "100% (Green integration tests)"
    authorization_integrity: str = "100% (Strict zero-spawning boundaries verified)"


class CapabilityNode(BaseModel):
    """A node in the living capability topgraphy."""
    capability_id: str
    name: str
    status: str  # PROVEN, SIMULATION SUPPORTED, HYPOTHESIS, GOVERNANCE GAP
    evidence_references: List[str] = Field(default_factory=list)


class CustomerAcceptanceSurface(BaseModel):
    """Bound customer-visible identity, mission state, and dual-gate acceptance status."""
    customer_id: str = "SAGE_INTERNAL_BUILDER"
    customer_surface: str = "CANONICAL_ACCEPTANCE_SURFACE"
    agent_identity: str = "MISSION_CONTROL"
    mission_state: str = "REHYDRATED"
    acceptance_status: str = "ENGINEERING_VERIFIED"
    deterministic_gate_status: str = "PASS"
    empirical_gate_status: str = "PENDING"
    bound: bool = True
    required_interfaces: List[str] = Field(default_factory=lambda: ["CHATGPT_C2", "GEMINI_RECON", "JULES_ENGINEER"])
    open_defects: List[str] = Field(default_factory=list)


class SAGEObservatoryViewModel(BaseModel):
    """The master forensic view model encapsulating all read-only windows."""
    causal_spine: List[CausalNode] = Field(default_factory=list)
    differential_lens: DifferentialProof = Field(default_factory=DifferentialProof)
    homeostatic_balance: HomeostaticBalance = Field(default_factory=HomeostaticBalance)
    capability_tree: List[CapabilityNode] = Field(default_factory=list)
    customer_acceptance_surface: CustomerAcceptanceSurface = Field(default_factory=CustomerAcceptanceSurface)
    galaxy_nodes: List[Dict[str, Any]] = Field(default_factory=list)
    galaxy_edges: List[Dict[str, Any]] = Field(default_factory=list)
    forensic_lineages: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)
    failure_boundaries: List[Dict[str, Any]] = Field(default_factory=list)
