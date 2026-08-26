"""Tests for hardened 5x4 Big Jump Wave evidence."""
from scripts.execute_big_jump_wave_20_cells import get_commit_sha, validate_20_cell_wave_payload

def test_validator_requires_exactly_20_cells_and_exact_sha():
    sha=get_commit_sha(); errors=validate_20_cell_wave_payload({"cells":[]},sha); assert any("Rule 1" in e for e in errors)

def test_validator_rejects_stale_sha():
    sha=get_commit_sha(); cells=[]
    for f in range(1,6):
        for g in range(1,5): cells.append({"flight_id":f"F{f}","lifecycle_gate":f"G{g}","exact_head_sha":"0"*40,"source_target":"sage/c2/adaptive_mission_selection.py","verification_result":"PASS","provenance_ref":f"r-{f}-{g}","cell_digest":f"d-{f}-{g}"})
    assert any("Rule 5" in e for e in validate_20_cell_wave_payload({"cells":cells},sha))

def test_validator_rejects_duplicate_cells():
    sha=get_commit_sha(); cells=[]
    for f in range(1,6):
        for g in range(1,5): cells.append({"flight_id":f"F{f}","lifecycle_gate":f"G{g}","exact_head_sha":sha,"source_target":"sage/c2/adaptive_mission_selection.py","verification_result":"PASS","provenance_ref":f"r-{f}-{g}","cell_digest":f"d-{f}-{g}"})
    cells[-1]=dict(cells[0]); cells[-1]["cell_digest"]="duplicate"; assert any("Rule 3" in e or "Rule 9" in e for e in validate_20_cell_wave_payload({"cells":cells},sha))
