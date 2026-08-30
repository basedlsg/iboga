from iboga_experiment.mechanism_v1 import CONDITIONS, MechanismV1Runner, cases_from_paired_benchmark


def test_v1_cases_use_one_surface_variant_per_independent_group():
    cases = cases_from_paired_benchmark()
    assert len(cases) == 8
    assert len({case.semantic_group_id for case in cases}) == 4


def test_fixture_v1_runs_all_seven_conditions_without_claiming_evidence():
    result = MechanismV1Runner(None, "fixture").run(cases_from_paired_benchmark(), repeats=1)
    assert tuple(result["conditions"]) == CONDITIONS
    assert result["reference_only"] is True
    assert result["independent_group_count"] == 4
    assert all(result["summary"][condition]["safe_correct_success_rate"] == 1.0 for condition in CONDITIONS)
    assert result["summary"]["R"]["memory_commit_rate"] == 1.0
    assert result["summary"]["G"]["memory_commit_rate"] == 1.0
    assert result["summary"]["C"]["memory_commit_rate"] == 1.0


def test_fixture_v1_preserves_axis_separation():
    result = MechanismV1Runner(None, "fixture").run(cases_from_paired_benchmark(), repeats=1, conditions=("D",))
    observed = result["records"][0]["observed"]
    required = {"action", "evidence_sufficiency", "authorization", "risk", "data_boundary", "reversibility", "human_gate_required"}
    assert required.issubset(observed)
