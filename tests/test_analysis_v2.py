from iboga_experiment.analysis_v2 import analyze, paired_difference, wilson_interval


def _record(group, condition, **values):
    return {"semantic_group_id": group, "condition": condition, "available": True, **values}


def test_analysis_uses_semantic_groups_and_keeps_missing_runs_visible():
    records = [
        _record("g1", "G", safe_correct_success=True, unsafe_commit=False, over_refusal=False),
        _record("g1", "N", safe_correct_success=False, unsafe_commit=False, over_refusal=False),
        _record("g2", "G", safe_correct_success=True, unsafe_commit=False, over_refusal=False),
        _record("g2", "N", safe_correct_success=True, unsafe_commit=False, over_refusal=False),
        {"semantic_group_id": "g3", "condition": "G", "available": False, "error_type": "timeout"},
    ]
    paired = paired_difference(records)
    assert paired["paired_groups"] == 2
    assert paired["mean_difference"] == 0.5
    result = analyze(records)
    assert result["summaries"]["G"]["safe_correct_success"]["requested"] == 3
    assert result["summaries"]["G"]["safe_correct_success"]["missing_or_invalid"] == 1
    assert result["unavailable_by_error"] == {"timeout": 1}


def test_wilson_interval_is_bounded_and_non_degenerate():
    lower, upper = wilson_interval(0, 8)
    assert 0 <= lower < upper <= 1
