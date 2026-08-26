"""Regression coverage for capabilities recovered from closed PR #248."""
from sage.c2.command_fidelity_wave import CommandFidelityWaveDispatcher
from sage.c2.directive_fidelity import DirectiveFingerprint, ExactOrderSentinel
from sage.c2.reality_gate import OperationalClaim, RealityGate, SourceReceipt
from sage.c2.claim_provenance import ClaimProvenanceCompiler
from sage.c2.drift_sentinel import DriftReplayScenario, DriftSentinel

HEAD="947408e6e77f9a15fdc2702e32e81b0cd935c733"

def test_directive_exact_order_and_forbidden_addition():
    contract=DirectiveFingerprint.create_contract("Check live repo.\nInspect PR.\nRun verification.\nDo not merge.")
    assert ExactOrderSentinel.validate_plan(contract,["Check live repo","Inspect PR","Run verification"]).is_valid
    assert not ExactOrderSentinel.validate_plan(contract,["Check live repo","Merge PR"]).is_valid

def test_reality_gate_requires_target_receipt():
    claim=OperationalClaim("c1",f"GitHub main is at {HEAD}","github",f"commit:{HEAD}")
    assert not RealityGate.evaluate_claims([claim],[]).is_permitted
    receipt=SourceReceipt("github",f"commit:{HEAD}",HEAD,0.0)
    assert RealityGate.evaluate_claims([claim],[receipt]).is_permitted

def test_claim_provenance_compiles_verified_claim():
    claim=OperationalClaim("c1",f"GitHub main is at {HEAD}","github",f"commit:{HEAD}")
    receipt=SourceReceipt("github",f"commit:{HEAD}",HEAD,0.0)
    result=ClaimProvenanceCompiler.compile_claims([claim],[receipt])
    assert result.is_valid
    assert len(result.verified_claims)==1

def test_drift_sentinel_passes_fresh_valid_session():
    raw="Check live repo.\nInspect PR.\nRun verification.\nDo not merge."
    contract=DirectiveFingerprint.create_contract(raw)
    claim=OperationalClaim("c1",f"GitHub main is at {HEAD}","github",f"commit:{HEAD}")
    receipt=SourceReceipt("github",f"commit:{HEAD}",HEAD,0.0)
    scenario=DriftReplayScenario("s1",raw,contract,("Check live repo","Inspect PR","Run verification"),(claim,),(receipt,),True)
    report=DriftSentinel.run_suite([scenario])
    assert report.passed_scenarios==1
    assert report.metrics.overall_drift_rate==0.0

def test_five_flight_dispatcher_reconverges():
    receipt=CommandFidelityWaveDispatcher(HEAD).dispatch_wave()
    assert receipt.wave_verdict=="PASS"
    assert len(receipt.flight_results)==5
    assert all(f.status=="PASS" and f.commit_sha==HEAD for f in receipt.flight_results)
