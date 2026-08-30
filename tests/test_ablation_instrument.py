from iboga_experiment.ablation_run import _minimal_pair_flip_rate
from iboga_experiment.paired_benchmark import audit, build_samples


def test_minimal_pair_benchmark_is_auditable():
    report = audit(build_samples())
    assert report["ok"] is True
    assert report["pairs"] == 4
    assert report["n"] == 24


def test_minimal_pair_metric_requires_both_members():
    records = [
        {"condition": "direct", "pair_id": "p", "pair_member": "base", "variant": "base", "completed": True, "correct": True, "observed": {"action": "hold"}},
        {"condition": "direct", "pair_id": "p", "pair_member": "flip", "variant": "base", "completed": True, "correct": True, "observed": {"action": "approve"}},
    ]
    assert _minimal_pair_flip_rate(records, "direct") == {
        "eligible_pairs": 1,
        "exact_both_members_rate": 1.0,
        "decision_flip_rate": 1.0,
    }
