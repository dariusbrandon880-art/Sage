from pathlib import Path

import yaml


WORKFLOW = Path('.github/workflows/operator-acceptance-runtime.yml')


def test_operator_acceptance_workflow_cannot_manufacture_pass_verdicts():
    text = WORKFLOW.read_text(encoding='utf-8')
    assert '--operator-verdict PASS' not in text
    assert 'ci://operator-acceptance/' not in text
    assert 'no verified external operator evidence supplied' in text
    assert 'Synthetic or missing operator evidence refs are forbidden' in text


def test_operator_acceptance_workflow_keeps_exact_head_binding():
    text = WORKFLOW.read_text(encoding='utf-8')
    assert 'EXPECTED_SHA' in text
    assert 'git rev-parse HEAD' in text
