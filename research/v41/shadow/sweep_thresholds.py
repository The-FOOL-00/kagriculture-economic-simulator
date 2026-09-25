import json
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v41.shadow.shadow_evaluator import ShadowEvaluator
from research.v41.executor.safe_executor import INTERVENTION_NAMES
import numpy as np

if __name__ == "__main__":
    ckpt = os.path.join(REPO_ROOT, "research", "v41", "checkpoints", "v41_offline_model.pt")
    seeds = [249675, 249676]
    opps = ["E8_DMITRII", "E2_A7"]

    evaluator = ShadowEvaluator(model_checkpoint_path=ckpt)

    print(f"{'Tau ($)':<8} | {'Proposals':<10} | {'FP Count':<9} | {'Mean Regret ($)':<16} | {'Agreement (%)':<14}")
    print("-" * 65)

    sweep_results = {}
    for tau in [5.0, 15.0, 30.0, 50.0, 100.0]:
        all_decs = []
        for s in seeds:
            for opp in opps:
                decs = evaluator.run_shadow_match(seed=s, opp_id=opp, confidence_threshold=tau)
                all_decs.extend(decs)

        total = len(all_decs)
        props = sum(1 for d in all_decs if d["model_action"] > 0)
        fps = sum(1 for d in all_decs if d["is_false_positive"])
        agreements = sum(1 for d in all_decs if d["agreement"])
        mean_regret = float(np.mean([d["regret"] for d in all_decs])) if all_decs else 0.0
        acc = agreements / max(1, total) * 100

        print(f"{tau:<8.1f} | {props:<10} | {fps:<9} | ${mean_regret:<15.2f} | {acc:<13.1f}%")
        sweep_results[tau] = {
            "tau": tau,
            "proposals": props,
            "false_positives": fps,
            "mean_regret": mean_regret,
            "agreement_rate": acc
        }

    out_path = os.path.join(REPO_ROOT, "research", "v41", "artifacts", "shadow_threshold_sweep.json")
    with open(out_path, "w") as f:
        json.dump(sweep_results, f, indent=2)
