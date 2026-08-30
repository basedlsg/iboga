from pathlib import Path

from iboga_experiment.checkpoints import JsonlCheckpoint, record_key


def test_checkpoint_round_trips_and_rejects_manifest_mismatch(tmp_path: Path):
    path = tmp_path / "run.jsonl"
    checkpoint = JsonlCheckpoint(path, manifest_hash="abc")
    checkpoint.append({"repeat": 1, "condition": "G", "sample_id": "s1", "available": True})
    loaded = checkpoint.load()
    assert record_key(loaded[0]) == (1, "G", "s1")
    try:
        JsonlCheckpoint(path, manifest_hash="different").load()
    except ValueError as exc:
        assert "manifest hash" in str(exc)
    else:
        raise AssertionError("manifest mismatch must fail closed")
