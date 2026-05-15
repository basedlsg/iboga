import pytest
import sys
import os
from pathlib import Path

# Add the scripts dir to path to import the module
sys.path.append(str(Path(__file__).parent.parent / "scripts"))

from reproduce_slopcodebench_baselines import compute_ols_slope, estimate_cost, main
import reproduce_slopcodebench_baselines
from unittest.mock import patch, MagicMock

def test_compute_ols_slope():
    # Test with known data points
    # Points: (0, 1), (1, 3), (2, 5), (3, 7) => slope is exactly 2.0
    y_values = [1.0, 3.0, 5.0, 7.0]
    slope = compute_ols_slope(y_values)
    assert abs(slope - 2.0) < 1e-6
    
    # Points: (0, 0), (1, 1), (2, 0) => slope is 0.0
    y_values = [0.0, 1.0, 0.0]
    slope = compute_ols_slope(y_values)
    assert abs(slope - 0.0) < 1e-6

def test_cost_estimate_gate():
    # Mock the COST_TABLE
    models = ["expensive_model"]
    problems = ["p1", "p2"]
    
    with patch.dict("reproduce_slopcodebench_baselines.COST_TABLE", {"expensive_model": 30.0}):
        cost = estimate_cost(models, problems)
        assert cost == 60.0  # 30.0 * 2 problems
        
        # Now test the main function's behavior
        test_args = [
            "scripts/reproduce_slopcodebench_baselines.py",
            "--models", "expensive_model",
            "--problems", "p1,p2",
            "--upstream-leaderboard", "/tmp/dummy.json"
        ]
        with patch.object(sys, "argv", test_args):
            with pytest.raises(SystemExit) as e:
                main()
            assert e.value.code == 1
            
        test_args_confirm = [
            "scripts/reproduce_slopcodebench_baselines.py",
            "--models", "expensive_model",
            "--problems", "p1,p2",
            "--upstream-leaderboard", "/tmp/dummy_confirm.json",
            "--dry-run"
        ]
        # In this dummy confirm, we don't have the upstream comparisons set up fully,
        # so let's mock write_reports to return True (overall pass)
        with patch.object(sys, "argv", test_args_confirm), \
             patch("reproduce_slopcodebench_baselines.write_reports", return_value=True):
            with pytest.raises(SystemExit) as e:
                main()
            assert e.value.code == 0
