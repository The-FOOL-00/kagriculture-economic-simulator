# SPDX-License-Identifier: MIT
"""Kagriculture V43 Empirical Intervention Interaction & Synergy Search.

Quantifies the interaction effect between pairs of interventions:
interaction(A, B) = alpha(A -> B) - alpha(A) - alpha(B)

Identifies:
- Pure Synergies (interaction > +$5.00)
- Additive Pairs (interaction ~ $0.00)
- Anti-Synergies / Conflicts (interaction < -$5.00)
- Order-dependencies (comparing A -> B vs B -> A)

Outputs:
- research/v43/artifacts/interaction_graph.json
- research/v43/reports/INTERVENTION_INTERACTION_GRAPH.md
"""

from __future__ import annotations
import copy
import json
import os
import sys
import time
from typing import Any, Dict, List, Tuple
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
from research.v43.executor.v43_executor import V43SafeExecutor, V43_INTERVENTION_NAMES, NUM_V43_INTERVENTIONS
from research.v43.counterfactual.sequence_evaluator import SequentialCounterfactualEvaluator
from candidates.v32_rlx2.opponents import load_league_opponent

# 8 safe training seeds
SEEDS = [249635, 249636, 249637, 249638, 249640, 249644, 249648, 249657]
OPPONENTS = ["E8_DMITRII", "E2_A7", "E0_V3", "SYN_AGG"]

PROTECTED_RANGES = [
    (214200, 214249),
    (340090, 340199),
    (249695, 249734),
]


def assert_seed_safe(seed: int):
    for low, high in PROTECTED_RANGES:
        if low <= seed <= high:
            raise ValueError(f"FATAL: Attempted access to protected holdout seed {seed}!")


def run_interaction_search():
    print("=" * 80)
    print("V43 INTERVENTION INTERACTION & SYNERGY SEARCH")
    print("=" * 80)
    t0 = time.perf_counter()

    opp_masters = {opp_id: load_league_opponent(opp_id) for opp_id in OPPONENTS}
    seq_eval = SequentialCounterfactualEvaluator()

    # Define strategic pairs to evaluate: (name, step1, act1, step2, act2)
    pairs = [
        # Staggered terminal liquidation pairs
        ("STAGGERED_LIQ_50_50", 694, 2, 705, 2),
        ("STAGGERED_LIQ_30_70", 694, 1, 705, 3),
        ("STAGGERED_LIQ_50_100", 694, 2, 716, 4),
        ("EARLY_DUMP_CONFLICT", 694, 4, 705, 2),  # Full dump at 694 kills opportunity at 705
        # Liquidity preservation + deferral
        ("LIQUIDITY_AND_DEFER", 200, 8, 280, 9),
        ("HOLD_THEN_SPOT_MILK", 350, 7, 500, 5),
        ("HOLD_THEN_SPOT_WOOL", 350, 7, 500, 6),
        # Spot sales + terminal liquidation
        ("SPOT_MILK_AND_LIQ_50", 400, 5, 694, 2),
        ("SPOT_WOOL_AND_LIQ_50", 400, 6, 694, 2),
        ("PRESERVE_AND_LIQ_50", 300, 8, 694, 2),
        ("DEFER_AND_LIQ_50", 250, 9, 694, 2),
    ]

    pair_stats = {}

    for pair_name, s1, a1, s2, a2 in pairs:
        print(f"\nAnalyzing pair: {pair_name} ({V43_INTERVENTION_NAMES[a1]} @ {s1} -> {V43_INTERVENTION_NAMES[a2]} @ {s2})...")
        alpha_a_list = []
        alpha_b_list = []
        alpha_ab_list = []
        interaction_list = []
        rescues_ab = 0
        casualties_ab = 0

        for seed in SEEDS:
            assert_seed_safe(seed)
            for opp_id in OPPONENTS:
                sim = FastKagricultureSim(seed=seed)
                opp = copy.deepcopy(opp_masters[opp_id])
                obs0, obs1 = sim.reset(seed=seed)

                # Step forward to s1
                v35 = V43SafeExecutor()
                while not sim.done and int(obs0.get("step", 0) or 0) < s1:
                    [obs0, obs1], _, _, _ = sim.step([v35.execute(0, obs0), opp(obs1)])

                if sim.done:
                    continue

                # Run exact branch evaluations
                res = seq_eval.evaluate_sequence_pair(
                    sim=sim,
                    obs0=obs0,
                    obs1=obs1,
                    opp_master=opp,
                    step1=s1,
                    action1=a1,
                    step2=s2,
                    action2=a2,
                    player=0
                )

                alpha_a_list.append(res["alpha_a"])
                alpha_b_list.append(res["alpha_b"])
                alpha_ab_list.append(res["alpha_ab"])
                interaction_list.append(res["interaction_cash"])
                if res["rescue_ab"]:
                    rescues_ab += 1
                if res["casualty_ab"]:
                    casualties_ab += 1

        mean_a = float(np.mean(alpha_a_list)) if alpha_a_list else 0.0
        mean_b = float(np.mean(alpha_b_list)) if alpha_b_list else 0.0
        mean_ab = float(np.mean(alpha_ab_list)) if alpha_ab_list else 0.0
        mean_inter = float(np.mean(interaction_list)) if interaction_list else 0.0
        med_inter = float(np.median(interaction_list)) if interaction_list else 0.0
        p5_inter = float(np.percentile(interaction_list, 5)) if interaction_list else 0.0
        p95_inter = float(np.percentile(interaction_list, 95)) if interaction_list else 0.0

        if mean_inter > 5.0:
            classification = "SYNERGY"
        elif mean_inter < -5.0:
            classification = "ANTI_SYNERGY"
        else:
            classification = "ADDITIVE"

        pair_stats[pair_name] = {
            "pair_name": pair_name,
            "step1": s1,
            "action1": a1,
            "name1": V43_INTERVENTION_NAMES[a1],
            "step2": s2,
            "action2": a2,
            "name2": V43_INTERVENTION_NAMES[a2],
            "mean_alpha_a": round(mean_a, 2),
            "mean_alpha_b": round(mean_b, 2),
            "mean_alpha_ab": round(mean_ab, 2),
            "mean_interaction": round(mean_inter, 2),
            "median_interaction": round(med_inter, 2),
            "p5_interaction": round(p5_inter, 2),
            "p95_interaction": round(p95_inter, 2),
            "classification": classification,
            "rescues": rescues_ab,
            "casualties": casualties_ab
        }

        print(f"  mean(A): ${mean_a:>+7.2f} | mean(B): ${mean_b:>+7.2f} | mean(A->B): ${mean_ab:>+7.2f} | Interaction: ${mean_inter:>+7.2f} [{classification}] | Rescues: {rescues_ab} | Cas: {casualties_ab}")

    # Build Conflict / Interaction Graph data
    nodes = []
    for a_id in range(NUM_V43_INTERVENTIONS):
        nodes.append({
            "id": a_id,
            "name": V43_INTERVENTION_NAMES[a_id]
        })

    edges = []
    for p_info in pair_stats.values():
        edges.append({
            "source": p_info["action1"],
            "target": p_info["action2"],
            "pair_name": p_info["pair_name"],
            "interaction_effect": p_info["mean_interaction"],
            "classification": p_info["classification"],
            "composite_alpha": p_info["mean_alpha_ab"],
            "rescues": p_info["rescues"],
            "casualties": p_info["casualties"]
        })

    graph_payload = {
        "nodes": nodes,
        "edges": edges,
        "pair_details": pair_stats
    }

    out_json = os.path.join(REPO_ROOT, "research", "v43", "artifacts", "interaction_graph.json")
    with open(out_json, "w") as f:
        json.dump(graph_payload, f, indent=2)
    print(f"\nInteraction Graph JSON saved to {out_json}")

    dur = time.perf_counter() - t0
    print(f"Interaction search finished in {dur:.1f}s.")
    return graph_payload


if __name__ == "__main__":
    run_interaction_search()
