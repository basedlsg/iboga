import pytest
import torch
import sys
import os
import numpy as np

# Add the scripts directory to the path so we can import select_sae_features
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts.select_sae_features import aggregate_features, compute_ratios, rank_features

def test_aggregation_math():
    # Shape: (batch_size, seq_len, d_sae)
    # We pass a list of tensors representing acts for prompts.
    # We want mean across all tokens in all prompts.
    
    # Prompt 1: 1 token, 2 features
    act1 = torch.tensor([[[2.0, 4.0]]])
    # Prompt 2: 2 tokens, 2 features
    act2 = torch.tensor([[[6.0, 8.0], [10.0, 12.0]]])
    
    # Total tokens = 3
    # Sum for feature 0: 2 + 6 + 10 = 18. Mean = 6.0
    # Sum for feature 1: 4 + 8 + 12 = 24. Mean = 8.0
    mean_act = aggregate_features([act1, act2])
    assert torch.allclose(mean_act, torch.tensor([6.0, 8.0]))
    
def test_compute_ratios():
    act_self = torch.tensor([10.0, 1.0, 0.0])
    act_ctrl = torch.tensor([5.0, 1.0, 0.0])
    
    # ratio = (act_self + 1e-6) / (act_ctrl + 1e-6)
    ratios = compute_ratios(act_self, act_ctrl, epsilon=1e-6)
    
    assert torch.allclose(ratios[0], torch.tensor(10.000001 / 5.000001))
    assert torch.allclose(ratios[1], torch.tensor(1.000001 / 1.000001))
    assert torch.allclose(ratios[2], torch.tensor(1e-6 / 1e-6))

def test_rank_features():
    ratios = torch.tensor([1.5, 3.0, 0.5, 2.5])
    mean_self = torch.tensor([1.5, 6.0, 0.5, 5.0])
    mean_ctrl = torch.tensor([1.0, 2.0, 1.0, 2.0])
    
    features, num_greater_than_2 = rank_features(ratios, mean_self, mean_ctrl, top_k=2)
    
    assert num_greater_than_2 == 2
    
    # Check top 2 features
    assert len(features) == 2
    
    # First is idx 1 (ratio 3.0)
    assert features[0]["feature_id"] == 1
    assert features[0]["ratio"] == 3.0
    assert features[0]["rank"] == 1
    assert features[0]["act_self"] == 6.0
    
    # Second is idx 3 (ratio 2.5)
    assert features[1]["feature_id"] == 3
    assert features[1]["ratio"] == 2.5
    assert features[1]["rank"] == 2
    assert features[1]["act_self"] == 5.0

