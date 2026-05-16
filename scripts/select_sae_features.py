"""
select_sae_features.py

Purpose:
Select the top-20 SAE features that fire most selectively on self-referential text,
using the locked probe corpus.

GPU Memory Requirement:
Running this script with a real model requires a GPU with at least 24 GB of VRAM.
If using --device cuda and VRAM is less than 20GB, it will fall back to 4-bit bitsandbytes loading.

Usage:
  python scripts/select_sae_features.py \
    --probe-corpus sae-probe-corpus.json \
    --output sae-features.json \
    [--layer 50] [--top-k 20] [--device cuda|cpu] [--self-test]
"""

import argparse
import hashlib
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone

import torch
import torch.nn as nn
import numpy as np

# huggingface_hub and safetensors are imported lazily inside load_goodfire_sae()
# so that --self-test (CPU-only, synthetic SAE) runs with just torch + numpy.

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

EXPECTED_HASH = "4a0853a0b97fd9ba3e4c443be5afdd8619735fe7d5dc7d317ec0e7fc97ce0229"


def check_corpus_hash(corpus_path: str):
    with open(corpus_path, "rb") as f:
        content = f.read()
    file_hash = hashlib.sha256(content).hexdigest()
    if file_hash != EXPECTED_HASH:
        logging.warning(f"SHA-256 hash of {corpus_path} differs from expected.")
        logging.warning(f"Expected: {EXPECTED_HASH}")
        logging.warning(f"Actual:   {file_hash}")
    else:
        logging.info("Corpus hash verified successfully.")
    return file_hash


def load_goodfire_sae(layer: int, device: str):
    """
    Loads Goodfire's open SAE weights from HuggingFace via safetensors.
    
    Expected weight-key layout:
      - encoder weight: e.g. "W_enc" or something similar
      - encoder bias: e.g. "b_enc" 
      - decoder weight: e.g. "W_dec"
      
    This function pulls Goodfire/Llama-3.3-70B-Instruct-SAE-l50 by default (layer 50).
    Since layout might differ, human intervention might be needed to map the exact keys.
    """
    from huggingface_hub import hf_hub_download
    from safetensors.torch import load_file

    logging.info(f"Loading Goodfire safetensors SAE for layer {layer}")
    repo_id = f"Goodfire/Llama-3.3-70B-Instruct-SAE-l{layer}"
    
    try:
        # We try to download the safetensors file
        filename = "sae_weights.safetensors" # This might need adjustment based on actual repo contents
        file_path = hf_hub_download(repo_id=repo_id, filename=filename)
        weights = load_file(file_path)
    except Exception as e:
        logging.warning(f"Could not load Goodfire SAE from {repo_id}/{filename}: {e}")
        # Trying 'model.safetensors' as an alternative standard name
        try:
            filename = "model.safetensors"
            file_path = hf_hub_download(repo_id=repo_id, filename=filename)
            weights = load_file(file_path)
        except Exception as e2:
            raise RuntimeError(f"Failed to load Goodfire SAE weights: {e2}")

    # Inspect keys to find standard SAE mappings
    # Typical keys:
    # W_enc (d_model, d_sae)
    # b_enc (d_sae)
    # W_dec (d_sae, d_model)
    # b_dec (d_model) # sometimes
    
    w_enc = None
    b_enc = None
    
    # Simple mapping heuristic
    if "W_enc" in weights: w_enc = weights["W_enc"]
    elif "encoder.weight" in weights: w_enc = weights["encoder.weight"].T
    
    if "b_enc" in weights: b_enc = weights["b_enc"]
    elif "encoder.bias" in weights: b_enc = weights["encoder.bias"]
    
    if w_enc is None or b_enc is None:
        raise ValueError(f"Could not map Goodfire SAE keys. Found: {list(weights.keys())}")
        
    class GoodfireSAE(nn.Module):
        def __init__(self, w_enc, b_enc):
            super().__init__()
            # Store them as parameters/buffers
            self.w_enc = nn.Parameter(w_enc.to(device).to(torch.float32))
            self.b_enc = nn.Parameter(b_enc.to(device).to(torch.float32))
            self.device = device
            
        def encode(self, x):
            x = x.to(torch.float32)
            # Standard SAE encoder: ReLU(x @ W_enc + b_enc)
            return torch.relu(x @ self.w_enc + self.b_enc)

    return GoodfireSAE(w_enc, b_enc), repo_id


class SyntheticSAE(nn.Module):
    def __init__(self, d_model=64, d_sae=256, device="cpu"):
        super().__init__()
        torch.manual_seed(42)
        self.w_enc = nn.Parameter(torch.randn(d_model, d_sae, device=device))
        self.b_enc = nn.Parameter(torch.randn(d_sae, device=device))
        
    def encode(self, x):
        return torch.relu(x @ self.w_enc + self.b_enc)


def get_synthetic_activations(text: str, d_model: int = 64, seq_len: int = 10, device: str = "cpu"):
    """
    Generate deterministic synthetic activations based on the hash of the text.
    """
    h = int(hashlib.md5(text.encode('utf-8')).hexdigest(), 16)
    torch.manual_seed(h % (2**32))
    # Return (1, seq_len, d_model)
    return torch.randn(1, seq_len, d_model, device=device)


def aggregate_features(activations_list):
    """
    Given a list of tensors of shape (1, seq_len, d_sae), compute the mean across all tokens in the list.
    """
    if not activations_list:
        return None
    # Concat all along the sequence dimension: (1, total_seq_len, d_sae)
    all_acts = torch.cat(activations_list, dim=1)
    # Mean over tokens (dim=1)
    mean_acts = all_acts.mean(dim=(0, 1))
    return mean_acts


def compute_ratios(act_self, act_ctrl, epsilon=1e-6):
    """
    Computes (act_self + epsilon) / (act_ctrl + epsilon)
    """
    return (act_self + epsilon) / (act_ctrl + epsilon)


def rank_features(ratios, mean_self, mean_ctrl, top_k):
    """
    Ranks features by ratio descending, and returns top_k features.
    """
    ratios_np = ratios.detach().cpu().numpy()
    mean_self_np = mean_self.detach().cpu().numpy()
    mean_ctrl_np = mean_ctrl.detach().cpu().numpy()
    
    # Sort descending
    sorted_indices = np.argsort(ratios_np)[::-1]
    
    top_k_indices = sorted_indices[:top_k]
    
    features = []
    num_greater_than_2 = 0
    for rank, idx in enumerate(top_k_indices):
        ratio_val = float(ratios_np[idx])
        if ratio_val > 2.0:
            num_greater_than_2 += 1
            
        features.append({
            "feature_id": int(idx),
            "act_self": float(mean_self_np[idx]),
            "act_ctrl": float(mean_ctrl_np[idx]),
            "ratio": ratio_val,
            "rank": rank + 1
        })
        
    return features, num_greater_than_2


def main():
    parser = argparse.ArgumentParser(description="Select SAE features.")
    parser.add_argument("--probe-corpus", type=str, required=True, help="Path to sae-probe-corpus.json")
    parser.add_argument("--output", type=str, required=True, help="Path to output sae-features.json")
    parser.add_argument("--layer", type=int, default=50, help="Transformer layer to hook (Goodfire Llama-3.3-70B SAE is layer 50)")
    parser.add_argument("--top-k", type=int, default=20, help="Number of features to select")
    parser.add_argument("--device", type=str, default="cpu", help="Device to use (cuda|cpu)")
    parser.add_argument("--self-test", action="store_true", help="Run in self-test mode with synthetic SAE")
    
    args = parser.parse_args()
    
    # 1. Load and check corpus
    with open(args.probe_corpus, "r") as f:
        corpus = json.load(f)
    
    corpus_hash = check_corpus_hash(args.probe_corpus)
    
    self_prompts = corpus.get("self_referential", [])
    ctrl_prompts = corpus.get("control", [])
    
    if args.self_test:
        logging.info("Running in --self-test mode.")
        device = "cpu" # Enforce CPU for self test
        sae = SyntheticSAE(d_model=64, d_sae=256, device=device)
        sae_loader = "self_test_synthetic"
        sae_id = "synthetic-sae"
        
        # 4. Generate and encode activations
        self_acts = []
        ctrl_acts = []
        
        for prompt in self_prompts:
            acts = get_synthetic_activations(prompt, d_model=64, seq_len=10, device=device)
            f_acts = sae.encode(acts)
            # Store on CPU memory to avoid GPU VRAM leaks during mapping
            self_acts.append(f_acts.cpu())
            
        for prompt in ctrl_prompts:
            acts = get_synthetic_activations(prompt, d_model=64, seq_len=10, device=device)
            f_acts = sae.encode(acts)
            ctrl_acts.append(f_acts.cpu())
            
    else:
        # Real model execution path
        device = args.device
        if device.startswith("cuda") and not torch.cuda.is_available():
            logging.warning("CUDA is not available, falling back to CPU")
            device = "cpu"
            
        logging.info("Loading Llama-3.3-70B-Instruct...")
        # (Assuming transformers is available)
        import transformers
        
        model_id = "meta-llama/Llama-3.3-70B-Instruct"
        
        load_kwargs = {"device_map": device, "torch_dtype": torch.bfloat16}
        if device.startswith("cuda"):
            # Check VRAM - use the actual device id if specified like cuda:0
            device_id = 0 if device == "cuda" else int(device.split(":")[1])
            try:
                vram = torch.cuda.get_device_properties(device_id).total_memory
                if vram < 20 * 1024**3:
                    logging.info("VRAM < 20GB, using 4-bit fallback.")
                    load_kwargs["load_in_4bit"] = True
            except Exception as e:
                logging.warning(f"Could not get VRAM: {e}")
                
        try:
            tokenizer = transformers.AutoTokenizer.from_pretrained(model_id)
            model = transformers.AutoModelForCausalLM.from_pretrained(model_id, **load_kwargs)
            logging.info("Model loaded.")
        except Exception as e:
            logging.error(f"Failed to load model: {e}")
            sys.exit(1)
            
        # SAE Loading logic
        from sae_lens import SAE
        sae_loader = None
        sae_id = None
        sae = None
        
        # Try finding it in sae_lens registry
        try:
            sae = SAE.from_pretrained("Llama-3.3-70B-Instruct", f"layer_{args.layer}")
            sae_loader = "sae_lens"
        except Exception as e:
            logging.info(f"SAE not found in sae_lens or could not load via sae_lens ({e}). Falling back to Goodfire safetensors.")
            sae, sae_id = load_goodfire_sae(args.layer, device)
            sae_loader = "goodfire_safetensors"
            
        # 4. Generate and encode activations (Real model)
        self_acts = []
        ctrl_acts = []
        
        def get_model_activations(prompt):
            inputs = tokenizer(prompt, return_tensors="pt").to(device)
            with torch.no_grad():
                # Extract layer activations. Huggingface models output hidden states if output_hidden_states=True
                outputs = model(**inputs, output_hidden_states=True)
                # Hidden states is a tuple, layers are 0-indexed.
                # Usually embedding is 0, so layer 1 is 1. We want args.layer
                hidden_state = outputs.hidden_states[args.layer]
            return hidden_state

        for prompt in self_prompts:
            acts = get_model_activations(prompt)
            f_acts = sae.encode(acts)
            self_acts.append(f_acts.cpu())
            
        for prompt in ctrl_prompts:
            acts = get_model_activations(prompt)
            f_acts = sae.encode(acts)
            ctrl_acts.append(f_acts.cpu())

    # 5. Aggregate per feature
    mean_self = aggregate_features(self_acts)
    mean_ctrl = aggregate_features(ctrl_acts)
    
    ratios = compute_ratios(mean_self, mean_ctrl)
    
    # 6. Rank by ratio descending
    features, num_greater_than_2 = rank_features(ratios, mean_self, mean_ctrl, args.top_k)
        
    # Status logic
    status = "locked"
    if num_greater_than_2 < 5:
        status = "demoted"
        
    # 7. Write sae-features.json
    output_data = {
        "version": "0.5.0",
        "status": status,
        "sae_loader": sae_loader,
        "sae_id": sae_id,
        "sae_layer": args.layer,
        "probe_corpus_sha256": corpus_hash,
        "selected_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "features": features
    }
    
    with open(args.output, "w") as f:
        json.dump(output_data, f, indent=2)
        
    # 8. Print readable top-20 table
    print(f"\nStatus: {status} (Features with ratio > 2.0: {num_greater_than_2})")
    print(f"{'Rank':<5} | {'Feature ID':<10} | {'Act Self':<12} | {'Act Ctrl':<12} | {'Ratio':<10}")
    print("-" * 60)
    for f in features:
        print(f"{f['rank']:<5} | {f['feature_id']:<10} | {f['act_self']:<12.4f} | {f['act_ctrl']:<12.4f} | {f['ratio']:<10.4f}")

if __name__ == "__main__":
    main()
