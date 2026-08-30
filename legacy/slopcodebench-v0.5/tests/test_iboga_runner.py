import json
import os
import subprocess
from pathlib import Path

def test_dry_run_arm_c(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("SLOPCODEBENCH_DIR", str(tmp_path))
    
    cmd = [
        "python", "scripts/iboga_runner.py",
        "--trajectory-id", "testtraj_c",
        "--model", "test-model",
        "--problem", "test-prob",
        "--arm", "C",
        "--dry-run"
    ]
    
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert "DRY RUN: would execute command:" in res.stderr
    
    session_dir = tmp_path / "iboga-data" / "sessions" / "testtraj_c"
    assert (session_dir / "hook.sh").exists()
    assert (session_dir / "session-ch2.json").exists()
    
    with open(session_dir / "session-ch2.json") as f:
        data = json.load(f)
        assert data == {"retrospective": "stub retrospective"}

def test_dry_run_arm_a(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("SLOPCODEBENCH_DIR", str(tmp_path))
    
    cmd = [
        "python", "scripts/iboga_runner.py",
        "--trajectory-id", "testtraj_a",
        "--model", "test-model",
        "--problem", "test-prob",
        "--arm", "A",
        "--dry-run"
    ]
    
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    
    session_dir = tmp_path / "iboga-data" / "sessions" / "testtraj_a"
    with open(session_dir / "session-ch2.json") as f:
        data = json.load(f)
        assert data == {"resentment_inventory": "stub", "past_tense_panorama": "stub"}

def test_dry_run_arm_0(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("SLOPCODEBENCH_DIR", str(tmp_path))
    
    cmd = [
        "python", "scripts/iboga_runner.py",
        "--trajectory-id", "testtraj_0",
        "--model", "test-model",
        "--problem", "test-prob",
        "--arm", "0",
        "--dry-run"
    ]
    
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    
    session_dir = tmp_path / "iboga-data" / "sessions" / "testtraj_0"
    with open(session_dir / "session-ch2.json") as f:
        data = json.load(f)
        assert data == {}

def test_cost_cap(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("SLOPCODEBENCH_DIR", str(tmp_path))
    
    iboga_data = tmp_path / "iboga-data"
    iboga_data.mkdir()
    with open(iboga_data / "cost-total.json", "w") as f:
        json.dump({"total_cost": 950.0}, f)
        
    cmd = [
        "python", "scripts/iboga_runner.py",
        "--trajectory-id", "testtraj_cap",
        "--model", "test-model",
        "--problem", "test-prob",
        "--arm", "C",
        "--dry-run"
    ]
    
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 1
    assert "Hard stop" in res.stderr

def test_mount_guard(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("SLOPCODEBENCH_DIR", str(tmp_path))
    
    config_dir = tmp_path / "configs" / "runs"
    config_dir.mkdir(parents=True)
    with open(config_dir / "lite_under20.yaml", "w") as f:
        f.write("some_config: value\ndocker:\n  extra_mounts:\n    - /host/path:/container/path\n    - /home/user/iboga-data:/workspace/iboga-data\n")
        
    cmd = [
        "python", "scripts/iboga_runner.py",
        "--trajectory-id", "testtraj_mount",
        "--model", "test-model",
        "--problem", "test-prob",
        "--arm", "C",
        "--dry-run"
    ]
    
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 1
    assert "Mount guard violation" in res.stderr

