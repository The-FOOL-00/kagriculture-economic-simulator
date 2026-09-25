# SPDX-License-Identifier: MIT
"""Kagriculture V40 League Evaluator and Paired Benchmark Harness.

Executes exact paired comparisons across candidate policies and baselines:
- Measures Paired Win Rate, Mean & Median Cash Margins
- Tracks Rescues (Candidate wins where Baseline lost)
- Tracks Casualties (Candidate loses where Baseline won)
- Guarantees strict seat symmetry and fresh-seed separation
"""

from __future__ import annotations
import copy
import json
import os
import sys
import time
from typing import Any, Callable, Dict, List, Optional, Tuple
import numpy as np
import torch

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
if os.path.join(REPO_ROOT, "scripts") not in sys.path:
    sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from candidates.v35_a7_opening.main import V35OpeningController
from candidates.v39_live_targeted.main import V39TargetedController
from candidates.v30_a7_standalone.main import agent as a7_agent_fn
from candidates.v32_rlx2.opponents import load_league_opponent
from research.v40.env.fast_sim import FastKagricultureSim
from research.v40.policy.observation import V40ObservationEncoder, OBSERVATION_DIM
from research.v40.policy.actions import StrategicMacroExecutor, get_macro_action_mask, NUM_MACRO_ACTIONS
from research.v40.policy.expert import V40ExpertPolicy
from research.v40.policy.model import V40RecurrentActorCritic

REPORTS_DIR = os.path.join(REPO_ROOT, "research", "v40", "reports")
CHECKPOINTS_DIR = os.path.join(REPO_ROOT, "research", "v40", "checkpoints")

# Strict check against protected holdouts
PROTECTED_RANGES = [
    (214200, 214249),
    (340090, 340199),
    (249695, 249734),
]

def assert_seed_safe(seed: int):
    for low, high in PROTECTED_RANGES:
        if low <= seed <= high:
            raise ValueError(f"FATAL: Attempted access to protected holdout seed {seed} ({low}..{high})!")


def run_single_match(
    agent_0: Callable[[Dict[str, Any], Optional[Dict[str, Any]]], Dict[str, Any]],
    agent_1: Callable[[Dict[str, Any], Optional[Dict[str, Any]]], Dict[str, Any]],
    seed: int
) -> Tuple[float, float, float]:
    """Runs a single match using FastKagricultureSim. Returns (r0, r1, duration)."""
    assert_seed_safe(seed)
    t0 = time.perf_counter()
    sim = FastKagricultureSim(seed=seed)
    obs0, obs1 = sim.reset(seed=seed)

    while not sim.done:
        act0 = agent_0(obs0)
        act1 = agent_1(obs1)
        [obs0, obs1], rewards, done, info = sim.step([act0, act1])

    dur = time.perf_counter() - t0
    r0 = float(sim.state[0].reward or 0.0)
    r1 = float(sim.state[1].reward or 0.0)
    return r0, r1, dur


def run_paired_matchup(
    candidate_fn_factory: Callable[[], Any],
    baseline_fn_factory: Callable[[], Any],
    opponent_id: str,
    seed: int
) -> Dict[str, Any]:
    """Runs 4 legs (seat 0 and seat 1 for candidate and baseline against opponent)."""
    assert_seed_safe(seed)

    # Leg 1: Candidate (Seat 0) vs Opponent (Seat 1)
    cand_0 = candidate_fn_factory()
    opp_1 = load_league_opponent(opponent_id)
    c_r0, o_r1, _ = run_single_match(cand_0, opp_1, seed)
    cand_win_seat0 = 1.0 if c_r0 > o_r1 else (0.5 if c_r0 == o_r1 else 0.0)

    # Leg 2: Baseline (Seat 0) vs Opponent (Seat 1)
    base_0 = baseline_fn_factory()
    opp_1_b = load_league_opponent(opponent_id)
    b_r0, ob_r1, _ = run_single_match(base_0, opp_1_b, seed)
    base_win_seat0 = 1.0 if b_r0 > ob_r1 else (0.5 if b_r0 == ob_r1 else 0.0)

    # Leg 3: Opponent (Seat 0) vs Candidate (Seat 1)
    opp_0 = load_league_opponent(opponent_id)
    cand_1 = candidate_fn_factory()
    o_r0, c_r1, _ = run_single_match(opp_0, cand_1, seed)
    cand_win_seat1 = 1.0 if c_r1 > o_r0 else (0.5 if c_r1 == o_r0 else 0.0)

    # Leg 4: Opponent (Seat 0) vs Baseline (Seat 1)
    opp_0_b = load_league_opponent(opponent_id)
    base_1 = baseline_fn_factory()
    ob_r0, b_r1, _ = run_single_match(opp_0_b, base_1, seed)
    base_win_seat1 = 1.0 if b_r1 > ob_r0 else (0.5 if b_r1 == ob_r0 else 0.0)

    # Aggregates across the 2 seats
    mean_cand_cash = (c_r0 + c_r1) / 2.0
    mean_base_cash = (b_r0 + b_r1) / 2.0
    cash_delta = mean_cand_cash - mean_base_cash

    cand_wins = (1 if cand_win_seat0 == 1.0 else 0) + (1 if cand_win_seat1 == 1.0 else 0)
    base_wins = (1 if base_win_seat0 == 1.0 else 0) + (1 if base_win_seat1 == 1.0 else 0)

    # Casualties: Baseline won, but Candidate did NOT win
    casualties = 0
    if base_win_seat0 == 1.0 and cand_win_seat0 < 1.0:
        casualties += 1
    if base_win_seat1 == 1.0 and cand_win_seat1 < 1.0:
        casualties += 1

    # Rescues: Baseline did not win, but Candidate WON
    rescues = 0
    if base_win_seat0 < 1.0 and cand_win_seat0 == 1.0:
        rescues += 1
    if base_win_seat1 < 1.0 and cand_win_seat1 == 1.0:
        rescues += 1

    return {
        "seed": seed,
        "opponent": opponent_id,
        "cand_cash_seat0": c_r0,
        "cand_cash_seat1": c_r1,
        "base_cash_seat0": b_r0,
        "base_cash_seat1": b_r1,
        "mean_cand_cash": mean_cand_cash,
        "mean_base_cash": mean_base_cash,
        "cash_delta": cash_delta,
        "cand_wins": cand_wins,
        "base_wins": base_wins,
        "rescues": rescues,
        "casualties": casualties,
    }


def evaluate_league_tournament(
    candidate_fn_factory: Callable[[], Any],
    candidate_name: str = "V40_CANDIDATE",
    baseline_type: str = "V35",
    seeds: Optional[List[int]] = None,
    opponents: Optional[List[str]] = None,
    output_report_name: Optional[str] = None
) -> Dict[str, Any]:
    """Runs a paired tournament across seats, seeds, and opponents."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    seeds = seeds or list(range(249675, 249695))  # Default 20 safe dev seeds
    opponents = opponents or ["E2_A7", "E8_DMITRII", "E0_V3", "SYN_AGG"]

    if baseline_type == "V35":
        baseline_fn_factory = lambda: V35OpeningController(wash_buy=25, wash_sell=25).act
    elif baseline_type == "V39":
        baseline_fn_factory = lambda: V39TargetedController().act
    else:
        baseline_fn_factory = lambda: V35OpeningController(wash_buy=25, wash_sell=25).act

    print("=" * 75)
    print(f"STARTING PAIRED TOURNAMENT: {candidate_name} vs {baseline_type}")
    print(f"Opponents: {opponents} | Seeds: {len(seeds)} safe seeds | Total Matches: {len(seeds) * len(opponents) * 2}")
    print("=" * 75)

    all_matches = []
    tot_rescues = 0
    tot_casualties = 0

    t0 = time.time()
    for s_idx, seed in enumerate(seeds):
        t_seed = time.perf_counter()
        s_rescues = 0
        s_casualties = 0
        for opp in opponents:
            res = run_paired_matchup(candidate_fn_factory, baseline_fn_factory, opp, seed)
            all_matches.append(res)
            tot_rescues += res["rescues"]
            tot_casualties += res["casualties"]
            s_rescues += res["rescues"]
            s_casualties += res["casualties"]
        print(f"  [Seed {s_idx+1:2d}/{len(seeds)}] Seed {seed} done in {time.perf_counter()-t_seed:.1f}s | Rescues: {s_rescues} | Casualties: {s_casualties}", flush=True)

    total_time = time.time() - t0
    total_legs = len(all_matches) * 2

    # Compute overall statistics
    total_cand_wins = sum(m["cand_wins"] for m in all_matches)
    total_base_wins = sum(m["base_wins"] for m in all_matches)
    cand_win_rate = (total_cand_wins / total_legs) * 100.0
    base_win_rate = (total_base_wins / total_legs) * 100.0

    cash_deltas = [m["cash_delta"] for m in all_matches]
    mean_cash_delta = float(np.mean(cash_deltas))
    median_cash_delta = float(np.median(cash_deltas))

    # Opponent-specific breakdown
    opp_stats = {}
    for opp in opponents:
        m_opp = [m for m in all_matches if m["opponent"] == opp]
        c_w = sum(m["cand_wins"] for m in m_opp)
        b_w = sum(m["base_wins"] for m in m_opp)
        legs = len(m_opp) * 2
        d_cash = [m["cash_delta"] for m in m_opp]
        opp_stats[opp] = {
            "legs": legs,
            "cand_wr": (c_w / legs) * 100.0,
            "base_wr": (b_w / legs) * 100.0,
            "mean_delta": float(np.mean(d_cash)),
            "rescues": sum(m["rescues"] for m in m_opp),
            "casualties": sum(m["casualties"] for m in m_opp),
        }

    print("\n" + "=" * 75)
    print(f"TOURNAMENT RESULTS SUMMARY: {candidate_name} vs {baseline_type}")
    print(f"Total Matches: {total_legs} | Duration: {total_time:.1f}s ({total_legs/total_time:.1f} matches/s)")
    print(f"Candidate Win Rate: {cand_win_rate:.1f}% ({total_cand_wins}/{total_legs})")
    print(f"Baseline Win Rate:  {base_win_rate:.1f}% ({total_base_wins}/{total_legs})")
    print(f"Win Rate Delta:     {cand_win_rate - base_win_rate:+.1f}%")
    print(f"Mean Paired Cash Delta:   ${mean_cash_delta:+,.1f}")
    print(f"Median Paired Cash Delta: ${median_cash_delta:+,.1f}")
    print(f"Rescues: {tot_rescues} | Casualties: {tot_casualties}")
    print("=" * 75)

    # Generate Markdown Report
    rep_name = output_report_name or f"{candidate_name}_vs_{baseline_type}_TOURNAMENT_REPORT.md"
    report_path = os.path.join(REPORTS_DIR, rep_name)

    report_md = f"""# V40 Tournament Evaluation Report: {candidate_name} vs {baseline_type}

**Document ID:** `{rep_name}`  
**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}  
**Total Paired Matches:** {total_legs} matches across {len(seeds)} seeds and {len(opponents)} opponents  
**Candidate Win Rate:** **{cand_win_rate:.1f}%** ({total_cand_wins}/{total_legs})  
**Baseline Win Rate:** **{base_win_rate:.1f}%** ({total_base_wins}/{total_legs})  
**Paired Win Rate Delta:** **{cand_win_rate - base_win_rate:+.1f}%**  
**Mean Cash Delta vs Baseline:** **${mean_cash_delta:+,.1f}**  
**Median Cash Delta:** **${median_cash_delta:+,.1f}**  
**Rescues:** **{tot_rescues}** | **Casualties:** **{tot_casualties}**  

---

## 1. Opponent-Specific Breakdown

| Opponent ID | Matches | {candidate_name} WR | {baseline_type} WR | WR Delta | Mean Cash Delta | Rescues | Casualties |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
"""
    for opp, s in opp_stats.items():
        delta_wr = s["cand_wr"] - s["base_wr"]
        report_md += (
            f"| `{opp}` | {s['legs']} | **{s['cand_wr']:.1f}%** | {s['base_wr']:.1f}% | "
            f"**{delta_wr:+.1f}%** | ${s['mean_delta']:+,.1f} | {s['rescues']} | {s['casualties']} |\n"
        )

    report_md += f"""
---

## 2. Casualty and Safety Audit

- **Zero-Casualty Standard:** Casualties = **{tot_casualties}**.
- **Rescue Count:** Rescues = **{tot_rescues}**.
"""
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_md)

    print(f"Saved tournament report to {report_path}")
    return {
        "candidate_wr": cand_win_rate,
        "baseline_wr": base_win_rate,
        "mean_cash_delta": mean_cash_delta,
        "rescues": tot_rescues,
        "casualties": tot_casualties,
        "report_path": report_path
    }


class V40NeuralCandidateAgent:
    """Production evaluation wrapper for V40 Recurrent Strategic Policy."""

    def __init__(self, checkpoint_path: str, macro_interval: int = 4, device: str = "cpu", deterministic: bool = True):
        self.macro_interval = macro_interval
        self.device = torch.device(device)
        self.deterministic = deterministic
        self.encoder = V40ObservationEncoder()
        self.expert = V40ExpertPolicy()
        self.executor = StrategicMacroExecutor()

        self.model = V40RecurrentActorCritic(
            obs_dim=OBSERVATION_DIM,
            num_actions=NUM_MACRO_ACTIONS,
            hidden_dim=128,
            rnn_type="GRU"
        ).to(self.device)

        state_dict = torch.load(checkpoint_path, map_location=self.device, weights_only=True)
        if "model_state_dict" in state_dict:
            state_dict = state_dict["model_state_dict"]
        self.model.load_state_dict(state_dict)
        self.model.eval()

        self.rnn_state = self.model.initial_state(batch_size=1, device=self.device)
        self.prev_macro_action = 0
        self.action_counts = {}

    def reset(self):
        self.encoder.reset()
        self.expert.reset()
        self.rnn_state = self.model.initial_state(batch_size=1, device=self.device)
        self.prev_macro_action = 0

    def act(self, obs: Dict[str, Any], cfg: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        step = int(obs.get("step", 0) or 0)
        player = int(obs.get("player", 0) or 0)

        if step <= 0:
            self.reset()

        # Macro decision tick
        if step % self.macro_interval == 0 and step < 710:
            obs_vec = self.encoder.encode(obs, player=player, prev_macro_action=self.prev_macro_action)
            mask = get_macro_action_mask(obs, player=player)

            obs_t = torch.tensor(obs_vec, dtype=torch.float32, device=self.device).unsqueeze(0)
            mask_t = torch.tensor(mask, dtype=torch.bool, device=self.device).unsqueeze(0)

            with torch.no_grad():
                act_t, lp_t, ent_t, val_t, next_rnn, aux_t = self.model.forward_step(
                    obs_t, mask_t, self.rnn_state, deterministic=self.deterministic
                )

            self.prev_macro_action = act_t.item()
            self.rnn_state = next_rnn
            self.action_counts[self.prev_macro_action] = self.action_counts.get(self.prev_macro_action, 0) + 1

        base_act = self.expert.act(obs, player=player)
        return self.executor.execute(self.prev_macro_action, base_act, obs, player=player)


def make_v40_candidate_factory(checkpoint_path: str) -> Callable[[], Any]:
    return lambda: V40NeuralCandidateAgent(checkpoint_path).act


if __name__ == "__main__":
    # Prioritize iter 10 checkpoint which achieved peak training performance (75% WR, +$97k margin)
    target_ckpt = os.path.join(CHECKPOINTS_DIR, "v40_ppo_iter_10.pt")
    if not os.path.exists(target_ckpt):
        target_ckpt = os.path.join(CHECKPOINTS_DIR, "v40_ppo_champion.pt")

    print(f"Evaluating V40 Checkpoint: {target_ckpt}")
    cand_factory = make_v40_candidate_factory(target_ckpt)

    # Clean held-out DEV seeds (249685..249689) - completely untouched during training
    fresh_seeds = list(range(249685, 249690))
    league_opponents = ["E2_A7", "E8_DMITRII", "E0_V3", "SYN_AGG"]

    print("\n--- Running Tournament: V40 vs V35 Baseline ---")
    res_v35 = evaluate_league_tournament(
        candidate_fn_factory=cand_factory,
        candidate_name="V40_PPO_ITER10",
        baseline_type="V35",
        seeds=fresh_seeds,
        opponents=league_opponents,
        output_report_name="V40_vs_V35_TOURNAMENT_REPORT.md"
    )

    print("\n--- Running Tournament: V40 vs V39 Baseline ---")
    res_v39 = evaluate_league_tournament(
        candidate_fn_factory=cand_factory,
        candidate_name="V40_PPO_ITER10",
        baseline_type="V39",
        seeds=fresh_seeds,
        opponents=league_opponents,
        output_report_name="V40_vs_V39_TOURNAMENT_REPORT.md"
    )
