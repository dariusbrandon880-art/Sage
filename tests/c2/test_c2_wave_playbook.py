"""Tests for recovered C2 Wave Playbook Engine."""
from sage.c2.c2_wave_playbook import C2WavePlaybookEngine, PlaybookExecutionReceipt

def test_receipt_hash_integrity():
    r=PlaybookExecutionReceipt(playbook_id="p",wave_id="w",flight_frontiers=["F1","F2","F3","F4","F5"],success_rate=1.0,first_pass_verification=True,execution_time_seconds=1); r.receipt_hash=r.compute_hash(); assert len(r.receipt_hash)==64 and r.receipt_hash==r.compute_hash()
def test_default_pattern():
    p=C2WavePlaybookEngine().suggest_optimization_pattern(); assert p.pattern_name=="DEFAULT_FIVE_FLIGHT_WAVE" and p.optimal_flight_count==5 and len(p.recommended_frontiers)==5
def test_history_drives_pattern():
    e=C2WavePlaybookEngine(); e.record_wave_execution("p","w1",["F1","F2"],1,True,1); e.record_wave_execution("p","w2",["F1","F5"],.8,False,2); p=e.suggest_optimization_pattern(); assert p.pattern_name=="OPTIMIZED_PARALLEL_WAVE" and p.historical_first_pass_rate==.5 and "F1" in p.recommended_frontiers
