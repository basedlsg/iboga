from iboga_experiment.power import paired_binary_group_count
from iboga_experiment.protocol_audit import ProtocolRequirements, audit_manifest
from iboga_experiment.verifier_qualification import audit_qualification_cases, summarize_verifier_results
from iboga_experiment.config import MODELS


def _record(group: str, stage: int, domain: str, split: str, phase: str, condition: str) -> dict:
    return {
        "id": f"{group}-{stage}-{phase}-{condition}",
        "semantic_group_id": group,
        "stage": stage,
        "domain": domain,
        "split": split,
        "phase": phase,
        "condition": condition,
        "provenance": {
            "generator": "test",
            "generator_version": "1",
            "code_revision": "test",
            "rights_status": "cleared",
            "privacy_review": "passed",
        },
        "reviewer_ids": ["r1", "r2"],
        "adjudication_status": "adjudicated",
    }


def test_audit_counts_independent_groups_not_records():
    records = [_record("g1", 1, "research", "development", "immediate", "D")]
    records.append(_record("g1", 1, "research", "development", "delayed", "D"))
    report = audit_manifest(records, requirements=ProtocolRequirements(min_groups_per_stage=1, min_domains=1, require_confirmatory_split=False, require_all_conditions=False))
    assert report["independent_group_count"] == 1
    assert report["stage_group_counts"]["1"] == 1
    assert report["ok"] is False


def test_audit_rejects_cross_split_group_and_missing_protocol_phases():
    records = [_record("g1", 1, "research", "development", "immediate", "D"), _record("g1", 1, "research", "confirmatory", "immediate", "D")]
    report = audit_manifest(records, requirements=ProtocolRequirements(min_groups_per_stage=1, min_domains=1, require_all_conditions=False))
    assert any("crosses split" in error for error in report["errors"])
    assert any("missing required phases" in error for error in report["errors"])


def test_power_grid_keeps_small_effects_expensive():
    assert paired_binary_group_count(0.08, 0.25) > paired_binary_group_count(0.15, 0.25)
    assert paired_binary_group_count(0.08, 0.25) >= 300


def test_verifier_qualification_requires_human_adjudication():
    case = {
        "id": "q1",
        "category": "supported",
        "source_case_id": "seed-1",
        "adjudicated_verdict": "approve",
        "reviewer_ids": ["r1", "r2"],
        "adjudication_status": "adjudicated",
    }
    assert audit_qualification_cases([case], minimums={"supported": 1})["ok"] is True


def test_verifier_release_gate_uses_upper_false_approval_interval():
    results = [
        {
            "id": "q1",
            "category": "supported",
            "adjudicated_verdict": "approve",
            "observed_verdict": "approve",
        },
        {
            "id": "q2",
            "category": "unsupported_fluent",
            "adjudicated_verdict": "reject",
            "observed_verdict": "approve",
        },
    ]
    report = summarize_verifier_results(results)
    assert report["false_approval_95ci"]["estimate"] == 0.5
    assert report["qualification_ready_for_safety_gating"] is False


def test_bedrock_model_limits_match_documented_flash_limit():
    assert MODELS["deepseek-v3.2"].max_output_tokens == 8_000
    assert MODELS["kimi-k2.5"].max_output_tokens == 16_000
    assert MODELS["glm-4.7-flash"].max_output_tokens == 4_000
