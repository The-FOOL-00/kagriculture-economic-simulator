# SPDX-License-Identifier: MIT
"""Kagriculture V34 Exact Local Forward Search Engine.

Evaluates localized, A7-compatible tactical deviations against baseline A7 continuation
under identical seed, opponent, and seat conditions.
Measures multi-horizon cash deltas: +4, +8, +16, +32, +64, +128, and terminal (+720),
physical worker displacement / resynchronization, liquidity safety, and win/loss impact.
"""

from __future__ import annotations
import copy
from dataclasses import dataclass
import os
import sys
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from kaggle_environments import make
from scripts.v32_common import load_agent
from candidates.v32_rlx2.opponents import load_league_opponent
from candidates.v34_a7_tactical.tactical_types import (
    TacticalCandidate, TacticalOutcome, MultiHorizonDeltas,
    HorizonTrajectory, OpportunityLabel, PromotionStatus
)
from candidates.v34_a7_tactical.liquidity_guard import LiquidityGuard


def _get_shared_obs(env: Any, pos: int) -> Dict[str, Any]:
    obs = copy.deepcopy(env.steps[-1][pos]["observation"])
    for k in ("step", "market", "town", "day", "hour"):
        if k in env.steps[-1][0]["observation"] and k not in obs:
            obs[k] = env.steps[-1][0]["observation"][k]
    return obs


class ExactLocalSearchEngine:
    """Simulates exact paired multi-horizon rollouts comparing baseline A7 vs Tactical Deviation."""

    def __init__(self):
        self.liquidity_guard = LiquidityGuard()

    def run_paired_counterfactual(
        self,
        seed: int,
        opponent_id: str,
        seat: int,
        branch_step: int,
        candidate: TacticalCandidate,
    ) -> TacticalOutcome:
        """Executes two paired rollouts from step 0:

        Rollout 1: Pure A7 vs Opponent
        Rollout 2: A7 up to branch_step -> Candidate Action at branch_step -> A7 continuation vs Opponent
        """
        # 1. Run Baseline A7 Rollout
        env_a7 = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
        env_a7.reset()
        a7_agent = load_agent("E9_AST")
        opp_a7 = load_league_opponent(opponent_id)

        a7_snapshots: Dict[int, float] = {}
        a7_farmer_positions: Dict[int, Tuple[int, int]] = {}
        target_horizons = [
            branch_step + 4,
            branch_step + 8,
            branch_step + 16,
            branch_step + 32,
            branch_step + 64,
            branch_step + 128,
        ]

        while not env_a7.done:
            obs_p = _get_shared_obs(env_a7, seat)
            obs_opp = _get_shared_obs(env_a7, 1 - seat)
            step = int(obs_p.get("step", 0) or 0)

            p_farm = (obs_p.get("farms", []) or [{}])[seat] if len(obs_p.get("farms", [])) > seat else {}
            current_cash = float(p_farm.get("money", 0.0) or 0.0)
            f_pos = tuple(p_farm.get("farmer", [0, 0]))

            if step in target_horizons:
                a7_snapshots[step] = current_cash
                a7_farmer_positions[step] = f_pos

            act_p = a7_agent.act(obs_p)
            act_opp = opp_a7(obs_opp)

            if seat == 0:
                env_a7.step([act_p, act_opp])
            else:
                env_a7.step([act_opp, act_p])

        a7_final_cash = float(env_a7.steps[-1][seat]["reward"] or 0.0)
        a7_opp_cash = float(env_a7.steps[-1][1 - seat]["reward"] or 0.0)
        a7_won = a7_final_cash > a7_opp_cash

        # 2. Run Candidate Rollout
        env_cand = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
        env_cand.reset()
        cand_a7_agent = load_agent("E9_AST")
        opp_cand = load_league_opponent(opponent_id)

        cand_snapshots: Dict[int, float] = {}
        cand_min_cash = float("inf")
        physical_divergence_ticks = 0
        liquidity_safe = True

        while not env_cand.done:
            obs_p = _get_shared_obs(env_cand, seat)
            obs_opp = _get_shared_obs(env_cand, 1 - seat)
            step = int(obs_p.get("step", 0) or 0)

            p_farm = (obs_p.get("farms", []) or [{}])[seat] if len(obs_p.get("farms", [])) > seat else {}
            current_cash = float(p_farm.get("money", 0.0) or 0.0)
            cand_min_cash = min(cand_min_cash, current_cash)
            f_pos = tuple(p_farm.get("farmer", [0, 0]))

            if step in target_horizons:
                cand_snapshots[step] = current_cash
                # Check worker position divergence
                expected_f_pos = a7_farmer_positions.get(step, f_pos)
                if f_pos != expected_f_pos:
                    physical_divergence_ticks += 1

            act_opp = opp_cand(obs_opp)

            if step == branch_step:
                # Apply Candidate Action
                act_p = copy.deepcopy(candidate.candidate_action)
                # Verify liquidity guard
                mkt_orders = act_p.get("market", []) or []
                prices = {k: float(v) for k, v in (obs_p.get("market", {}).get("prices", {}) or {}).items()}
                l_status = self.liquidity_guard.evaluate_action_liquidity(
                    current_cash=current_cash,
                    step=step,
                    active_workers=len(p_farm.get("hands", []) or []) + 1,
                    market_orders=mkt_orders,
                    prices=prices,
                )
                if not l_status.is_safe:
                    liquidity_safe = False
                # Advance internal state of A7 agent so it tracks this step
                _ = cand_a7_agent.act(obs_p)
            else:
                # Normal A7 continuation
                act_p = cand_a7_agent.act(obs_p)

            if seat == 0:
                env_cand.step([act_p, act_opp])
            else:
                env_cand.step([act_opp, act_p])

        cand_final_cash = float(env_cand.steps[-1][seat]["reward"] or 0.0)
        cand_opp_cash = float(env_cand.steps[-1][1 - seat]["reward"] or 0.0)
        cand_won = cand_final_cash > cand_opp_cash

        # 3. Compute Multi-Horizon Deltas
        d4 = cand_snapshots.get(branch_step + 4, cand_final_cash) - a7_snapshots.get(branch_step + 4, a7_final_cash)
        d8 = cand_snapshots.get(branch_step + 8, cand_final_cash) - a7_snapshots.get(branch_step + 8, a7_final_cash)
        d16 = cand_snapshots.get(branch_step + 16, cand_final_cash) - a7_snapshots.get(branch_step + 16, a7_final_cash)
        d32 = cand_snapshots.get(branch_step + 32, cand_final_cash) - a7_snapshots.get(branch_step + 32, a7_final_cash)
        d64 = cand_snapshots.get(branch_step + 64, cand_final_cash) - a7_snapshots.get(branch_step + 64, a7_final_cash)
        d128 = cand_snapshots.get(branch_step + 128, cand_final_cash) - a7_snapshots.get(branch_step + 128, a7_final_cash)
        d_term = cand_final_cash - a7_final_cash

        # Classify Horizon Trajectory
        if d4 > 0 and d_term < -100.0:
            trajectory = HorizonTrajectory.REVERSING
        elif d_term > 0 and d_term > d4 * 1.5:
            trajectory = HorizonTrajectory.COMPOUNDING
        elif d_term > 0 and abs(d_term - d4) <= max(50.0, 0.25 * abs(d_term)):
            trajectory = HorizonTrajectory.STABLE
        elif d4 > d_term > 0:
            trajectory = HorizonTrajectory.DECAYING
        elif d4 <= 0 and d_term > 0:
            trajectory = HorizonTrajectory.DELAYED
        else:
            trajectory = HorizonTrajectory.STABLE

        # Classify Opportunity Label
        if d_term < -2500.0 or not liquidity_safe or cand_min_cash < 10.0:
            label = OpportunityLabel.CATASTROPHIC_RISK
        elif -50.0 <= d_term <= 50.0:
            label = OpportunityLabel.A7_DOMINANT
        elif d_term > 500.0 and trajectory in (HorizonTrajectory.STABLE, HorizonTrajectory.COMPOUNDING) and liquidity_safe:
            label = OpportunityLabel.LARGE_SAFE_GAIN
        elif 50.0 < d_term <= 500.0 and liquidity_safe:
            label = OpportunityLabel.SMALL_SAFE_GAIN
        elif d_term > 500.0 and trajectory == HorizonTrajectory.REVERSING:
            label = OpportunityLabel.CATASTROPHIC_RISK
        elif d_term > 500.0:
            label = OpportunityLabel.LARGE_UNCERTAIN_GAIN
        else:
            label = OpportunityLabel.SMALL_RISKY_GAIN

        return TacticalOutcome(
            candidate_id=candidate.action_id,
            step=branch_step,
            seed=seed,
            opponent_id=opponent_id,
            seat=seat,
            a7_terminal_cash=a7_final_cash,
            cand_terminal_cash=cand_final_cash,
            deltas=MultiHorizonDeltas(
                delta_4=d4,
                delta_8=d8,
                delta_16=d16,
                delta_32=d32,
                delta_64=d64,
                delta_128=d128,
                delta_terminal=d_term,
                trajectory=trajectory,
            ),
            a7_won=a7_won,
            cand_won=cand_won,
            min_cash=cand_min_cash,
            physical_divergence_steps=physical_divergence_ticks,
            resync_success=(physical_divergence_ticks == 0),
            liquidity_safe=liquidity_safe,
            opportunity_label=label,
        )
