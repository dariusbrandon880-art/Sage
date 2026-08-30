from pathlib import Path


def test_sports_signal_contract_locks_temporal_and_shadow_boundaries() -> None:
    path = Path("docs/governance/SAGE_SPORTS_SIGNAL_INTELLIGENCE_CONTRACT.md")
    text = path.read_text(encoding="utf-8")

    required = (
        "DISCOVER → NORMALIZE → TIMESTAMP → BOUND → LOCK → PREDICT → RESOLVE → ATTRIBUTE → OOS VALIDATE → COMPOUND",
        "Every signal carries an authoritative `observed_at_utc` timestamp",
        "Information observed after lock is retained only as a diagnostic variant",
        "Super Search is an external intelligence sensor",
        "No economic-performance claim may be inferred from simulated bankrolls",
    )
    for marker in required:
        assert marker in text
