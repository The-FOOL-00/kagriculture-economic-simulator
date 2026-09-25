import json
import os
import sys
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)

from v32.p2.dataset import load_legs
from v32.p2.features import Normalizer
from v32.p3.dataset import build_samples

def compute_distances():
    norm = Normalizer.from_json(json.load(open(os.path.join(REPO_ROOT, "results", "v32_p2_norm.json"))))
    
    # Load 5,000 reference training samples to form the training manifold reference
    print("Loading reference training samples...")
    train_feats = []
    legs = list(load_legs(os.path.join(REPO_ROOT, "results", "v32_p2_bc_legs.jsonl")))
    for leg in legs[:25]:
        for s in build_samples(leg, leg["rows0"], leg["left"]):
            train_feats.append(s["feat"])
            if len(train_feats) >= 5000:
                break
        if len(train_feats) >= 5000:
            break
            
    F_train = norm.transform(train_feats)
    print(f"Loaded {len(F_train)} reference training feature vectors (shape {F_train.shape})")

    # Load diagnostic rollout vectors from results/v32_p5_rollout_diagnostic.json
    with open(os.path.join(REPO_ROOT, "results", "v32_p5_rollout_diagnostic.json")) as f:
        episodes = json.load(f)

    # For seed 249675:
    ep = episodes[0]
    
    intervals = [
        (0, 0, "Step 0"),
        (1, 10, "Steps 1-10"),
        (11, 24, "Steps 11-24"),
        (25, 72, "Steps 25-72"),
        (73, 288, "Steps 73-288"),
        (289, 719, "Steps 289-719")
    ]
    
    print("\nDistance from Policy Rollout States to Training Manifold (min Euclidean distance to F_train):")
    for start, end, label in intervals:
        dists = []
        for m in ep["step_metrics"]:
            t = m["step"]
            if start <= t <= end:
                dists.append(m["f_dist"])
        print(f"  {label:<15}: Mean ||s_t^P - s_t^T|| = {np.mean(dists):.2f} (max={np.max(dists):.2f})")

if __name__ == "__main__":
    compute_distances()
