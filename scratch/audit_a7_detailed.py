import os
import sys
sys.path.insert(0, os.path.abspath("."))
import json
import numpy as np
import torch
from kaggle_environments import make
from aec.backbone.v27_ablation_adapters import V27AblationAdapter
from v32.p3.models import P3Policy
from v32.p2.features import Normalizer
from v32.p3 import codec as C

def compare_oracle_on_policy_states():
    seed = 249675
    print(f"=== TESTING A7 ORACLE ON POLICY STATES (Seed {seed}) ===")
    
    # 1. Load P4 Arm 1 model
    ckpt_path = "results/v32_p4_arm1_balanced.npz"
    norm = Normalizer.from_json(json.load(open("results/v32_p2_norm.json")))
    d = np.load(ckpt_path, allow_pickle=True)
    model = P3Policy(157, 12)
    model.load_state_dict({k: torch.tensor(v) for k, v in d.items() if k != "meta"})
    model.eval()
    
    # 2. Run policy in environment and query A7 at each policy state
    env = make("kaggriculture", configuration={"seed": seed})
    obs = env.reset()[0].observation
    
    # Create two A7 adapters:
    # adapter_native: runs on its own state
    # adapter_oracle: invoked step-by-step on policy states
    adapter_oracle = V27AblationAdapter("V27-ABL-A7")
    
    # Also run a reference A7 environment to see what A7 actually does on its own
    env_a7 = make("kaggriculture", configuration={"seed": seed})
    obs_a7 = env_a7.reset()[0].observation
    adapter_native = V27AblationAdapter("V27-ABL-A7")
    
    opp = V27AblationAdapter("V27-ABL-V3S")
    opp_a7 = V27AblationAdapter("V27-ABL-V3S")
    
    # We will simulate 24 steps
    print(f"{'Step':<5} | {'Policy Action':<35} | {'A7 Native Action':<35} | {'A7 On Policy State':<35} | Match?")
    print("-" * 125)
    
    # Keep temporal buffer for policy
    hist_feats = []
    
    from v32.p2.features import build_temporal_features
    # We need temporal features for policy. Let's see how policy constructs features.
    
if __name__ == "__main__":
    compare_oracle_on_policy_states()
