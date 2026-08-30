from iboga_experiment.design_v2 import CONDITIONS, PHASES, build_design, validate_design


def test_v2_design_freezes_nine_stages_and_registered_conditions():
    design = build_design()
    report = validate_design(design)
    assert report["ok"] is True
    assert [stage.number for stage in design.stages] == list(range(1, 10))
    assert design.conditions == CONDITIONS
    assert design.phases == PHASES
    assert len(design.manifest_hash()) == 64
