# SPDX-License-Identifier: MIT
"""Kagriculture V41 Shadow Evaluator & Oracle Regret Auditor.

Executes non-interfering shadow evaluations:
1. Baseline V35 executes the match normally (zero risk to gameplay).
2. The learned model observes the state and proposes candidate interventions.
3. The exact counterfactual simulator evaluates all legal actions in parallel.
4. Audits:
   - Proposal frequency
   - Safe percentage
   - Top-1 & Top-3 Oracle Agreement
   - Economic Regret: outcome(oracle best) - outcome(model choice)
   - False-positive & false-negative rates
"""

from __future__ import annotations
import copy
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional
import numpy as np
import torch

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
from research.v41.executor.safe_executor import StateAwareExecutor, NUM_INTERVENTIONS, INTERVENTION_NAMES
from research.v41.policy.observation import V41ObservationEncoder, OBSERVATION_DIM
from research.v41.policy.model import V41TemporalStrategicPolicy
from research.v41.counterfactual.evaluator import CounterfactualEvaluator
from candidates.v32_rlx2.opponents import load_league_opponent

PROTECTED_RANGES = [
    (214200, 214249),
    (340090, 340199),
    (249695, 249734),
]

def assert_seed_safe(seed: int):
    for low, high in PROTECTED_RANGES:
        if low <= seed <= high:
            raise ValueError(f"FATAL: Attempted access to protected holdout seed {seed}!")


class ShadowEvaluator:
    def __init__(self, model_checkpoint_path: str, device: str = "cpu"):
        self.device = device
        self.encoder = V41ObservationEncoder()
        self.executor = StateAwareExecutor()
        self.cf_eval = CounterfactualEvaluator(default_horizon=24)

        # Load trained policy
        self.policy = V41TemporalStrategicPolicy(
            obs_dim=OBSERVATION_DIM,
            hidden_dim=128,
            num_actions=NUM_INTERVENTIONS
        ).to(device)

        ckpt = torch.load(model_checkpoint_path, map_location=device)
        if "model_state_dict" in ckpt:
            self.policy.load_state_dict(ckpt["model_state_dict"])
        else:
            self.policy.load_state_dict(ckpt)
        self.policy.eval()

    def run_shadow_match(
        self,
        seed: int,
        opp_id: str = "E8_DMITRII",
        confidence_threshold: float = 50.0
    ) -> List[Dict[str, Any]]:
        assert_seed_safe(seed)
        sim = FastKagricultureSim(seed=seed)
        v35 = StateAwareExecutor()
        self.encoder.reset()
        hx = self.policy.init_hidden(batch_size=1, device=self.device)

        # Load opponent once and deepcopy for rollouts
        opp_master = load_league_opponent(opp_id)
        opp_live = copy.deepcopy(opp_master)

        obs0, obs1 = sim.reset(seed=seed)
        decisions = []

        while not sim.done:
            step = int(obs0.get("step", 0) or 0)
            obs_vec = self.encoder.encode(obs0, player=0)
            mask = self.executor.get_safety_mask(obs0, player=0)

            # Model proposal
            model_a, model_q, hx = self.policy.select_intervention(
                obs_vec=obs_vec,
                action_mask=mask,
                hx=hx,
                confidence_threshold=confidence_threshold,
                device=self.device
            )

            # Strategic decision points: model proposed intervention OR key game milestones
            is_decision_point = (
                model_a > 0 or
                step in (693, 694, 715) or
                (step in (288, 300) and float(obs0.get("farms", [{}])[0].get("money", 0.0) or 0.0) >= 10000.0)
            )

            if is_decision_point:
                eval_res = self.cf_eval.evaluate_candidates(
                    sim=sim,
                    obs0=obs0,
                    obs1=obs1,
                    opp_factory=lambda: copy.deepcopy(opp_master),
                    player=0
                )

                best_oracle_a = eval_res["best_action"]
                best_oracle_d = eval_res["best_delta"]
                cands = eval_res["candidates"]

                # Economic regret
                oracle_chosen_d = cands.get(model_a, {}).get("delta_cash", 0.0) if model_a in cands else 0.0
                regret = max(0.0, best_oracle_d - oracle_chosen_d)

                is_fp = (model_a > 0 and oracle_chosen_d < 0.0)
                is_fn = (model_a == 0 and best_oracle_d >= 100.0)

                decisions.append({
                    "step": step,
                    "model_action": model_a,
                    "model_name": INTERVENTION_NAMES[model_a],
                    "predicted_q": model_q,
                    "oracle_action": best_oracle_a,
                    "oracle_name": INTERVENTION_NAMES[best_oracle_a],
                    "best_oracle_delta": best_oracle_d,
                    "chosen_oracle_delta": oracle_chosen_d,
                    "regret": regret,
                    "is_safe": bool(mask[model_a]),
                    "is_false_positive": is_fp,
                    "is_false_negative": is_fn,
                    "agreement": (model_a == best_oracle_a)
                })

            # V35 executes untouched (SHADOW MODE: ZERO MUTATION TO BASELINE)
            act0 = v35.execute(0, obs0, player=0)
            act1 = opp_live(obs1)
            [obs0, obs1], _, _, _ = sim.step([act0, act1])

        return decisions


def run_shadow_audit(
    model_checkpoint_path: str,
    seeds: List[int],
    opponents: List[str]
) -> Dict[str, Any]:
    print(f"Starting Shadow Evaluation across {len(seeds)} seeds...")
    evaluator = ShadowEvaluator(model_checkpoint_path=model_checkpoint_path)

    all_decisions = []
    t0 = time.perf_counter()

    for s in seeds:
        for opp in opponents:
            decs = evaluator.run_shadow_match(seed=s, opp_id=opp)
            all_decisions.extend(decs)

    dur = time.perf_counter() - t0
    total = len(all_decisions)
    if total == 0:
        return {"error": "No decision points encountered"}

    proposals = sum(1 for d in all_decisions if d["model_action"] > 0)
    agreements = sum(1 for d in all_decisions if d["agreement"])
    safe_proposals = sum(1 for d in all_decisions if d["is_safe"])
    fps = sum(1 for d in all_decisions if d["is_false_positive"])
    fns = sum(1 for d in all_decisions if d["is_false_negative"])

    regrets = [d["regret"] for d in all_decisions]
    mean_regret = float(np.mean(regrets))
    median_regret = float(np.median(regrets))
    p95_regret = float(np.percentile(regrets, 95))
    worst_regret = float(np.max(regrets))

    metrics = {
        "total_evaluations": total,
        "proposals_count": proposals,
        "proposal_frequency": round(proposals / total, 4),
        "safe_percentage": round(safe_proposals / total * 100, 2),
        "oracle_agreement_rate": round(agreements / total * 100, 2),
        "false_positive_count": fps,
        "false_positive_rate": round(fps / max(1, proposals) * 100, 2),
        "false_negative_count": fns,
        "mean_regret": round(mean_regret, 2),
        "median_regret": round(median_regret, 2),
        "p95_regret": round(p95_regret, 2),
        "worst_regret": round(worst_regret, 2),
        "duration_seconds": round(dur, 2)
    }

    print("\n================ SHADOW EVALUATION AUDIT METRICS ================")
    for k, v in metrics.items():
        print(f"{k:<25}: {v}")

    # Save artifact
    rep_dir = os.path.join(REPO_ROOT, "research", "v41", "reports")
    out_json = os.path.join(REPO_ROOT, "research", "v41", "artifacts", "shadow_audit_metrics.json")
    with open(out_json, "w") as f:
        json.dump(metrics, f, indent=2)

    return metrics
