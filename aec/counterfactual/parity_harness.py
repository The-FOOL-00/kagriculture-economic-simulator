# SPDX-License-Identifier: MIT
"""Reusable Trace-Equivalence Parity Harness (§13).

Runs the authoritative real game engine (kagsim) and the isolated AEC counterfactual
engine side-by-side from identical pre-states, comparing all state variables and emitting
actionable diffs upon any divergence.
"""

from __future__ import annotations

import copy
import dataclasses
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import kagsim
from aec.counterfactual.simulator import CounterfactualSimulator, ShadowRolloutState, execute_market_lockstep
from aec.ir.economic_state import build_economic_state
from aec.config import PRODUCTS


@dataclass
class StateVariableDiff:
    """Detailed diff for a single divergent state variable."""
    variable_name: str
    real_engine_value: Any
    counterfactual_value: Any
    difference: Any
    critical: bool = True

    def __str__(self) -> str:
        crit_str = "[CRITICAL]" if self.critical else "[INFO]"
        return (
            f"  {crit_str} {self.variable_name}: "
            f"Real={self.real_engine_value}, CF={self.counterfactual_value}, Diff={self.difference}"
        )


@dataclass
class ParityComparisonResult:
    """Comprehensive result of a trace-equivalence comparison."""
    passed: bool
    step: int
    seed: int
    diffs: List[StateVariableDiff] = field(default_factory=list)
    real_post_state: Dict[str, Any] = field(default_factory=dict)
    cf_post_state: Dict[str, Any] = field(default_factory=dict)

    def summary(self) -> str:
        status = "PASSED (PERFECT PARITY)" if self.passed else f"FAILED ({len(self.diffs)} DIVERGENCES)"
        lines = [f"=== TRACE PARITY AUDIT [Seed {self.seed}, Step {self.step}]: {status} ==="]
        if not self.passed:
            lines.append("Divergences:")
            for d in self.diffs:
                lines.append(str(d))
        return "\n".join(lines)


class TraceEquivalenceHarness:
    """Authoritative semantic parity harness for verifying counterfactual fidelity."""

    def __init__(self, v3_callable: Optional[Any] = None) -> None:
        self.v3_callable = v3_callable
        if self.v3_callable is None:
            import tarfile
            with tarfile.open("submission_Vj_kc_v3.tar.gz", "r:gz") as tar:
                code = tar.extractfile("main.py").read().decode("utf-8")
            ns: Dict[str, Any] = {}
            exec(compile(code, "harness_v3_main.py", "exec"), ns)
            self.v3_callable = ns["agent"]

    def advance_game_to_step(self, seed: int, target_step: int) -> Tuple[kagsim.Game, Dict[str, Any], Dict[str, Any]]:
        """Advance a fresh kagsim game using baseline policy up to target_step."""
        game = kagsim.Game(seed)
        v3_0 = copy.deepcopy(self.v3_callable) if hasattr(self.v3_callable, "__copy__") else self.v3_callable
        v3_1 = copy.deepcopy(self.v3_callable) if hasattr(self.v3_callable, "__copy__") else self.v3_callable

        while game.step_count < target_step:
            o0 = game.observe(0)
            o1 = game.observe(1)
            game.step(v3_0(o0), v3_1(o1))

        obs0 = game.observe(0)
        obs1 = game.observe(1)
        return game, obs0, obs1

    def run_turn_parity_comparison(
        self,
        seed: int,
        step: int,
        player_action: Dict[str, Any],
        opponent_action: Dict[str, Any]
    ) -> ParityComparisonResult:
        """Run single turn step side-by-side between real engine and counterfactual simulator."""
        # 1. Advance real game
        game, pre_obs0, pre_obs1 = self.advance_game_to_step(seed, step)
        pre_money = float(pre_obs0["farms"][0]["money"])
        pre_shed = copy.deepcopy(pre_obs0["private"]["shed"])
        pre_m_inv = copy.deepcopy(pre_obs0["market"]["inventory"])
        pre_m_prices = copy.deepcopy(pre_obs0["market"]["prices"])

        # Execute in real engine
        game.step(player_action, opponent_action)
        post_obs0 = game.observe(0)

        real_money = float(post_obs0["farms"][0]["money"])
        real_shed = copy.deepcopy(post_obs0["private"]["shed"])
        real_m_inv = copy.deepcopy(post_obs0["market"]["inventory"])
        real_m_prices = copy.deepcopy(post_obs0["market"]["prices"])
        real_farmer = list(post_obs0["farms"][0]["farmer"])

        # 2. Execute in Counterfactual Simulator
        econ_state = build_economic_state(pre_obs0, None)
        rollout = ShadowRolloutState(econ_state)
        
        # Execute market lockstep directly against the supplied opponent action
        opp_market = opponent_action.get("market", []) or []
        execute_market_lockstep(rollout, player_action.get("market", []), opp_market)

        cf_money = float(rollout.money)
        cf_shed = copy.deepcopy(rollout.shed)
        cf_m_inv = copy.deepcopy(rollout.market_inv)
        cf_m_prices = copy.deepcopy(rollout.market_prices)

        # 3. Compare State Variables
        diffs: List[StateVariableDiff] = []

        # Money
        money_diff = cf_money - real_money
        if abs(money_diff) > 1e-4:
            diffs.append(StateVariableDiff("cash", real_money, cf_money, money_diff, critical=True))

        # Shed inventory
        for p in PRODUCTS:
            r_val = real_shed.get(p, 0)
            c_val = cf_shed.get(p, 0)
            if r_val != c_val:
                diffs.append(StateVariableDiff(f"shed_{p}", r_val, c_val, c_val - r_val, critical=True))

        # Market inventory
        for p in PRODUCTS:
            r_val = real_m_inv.get(p, 0)
            c_val = cf_m_inv.get(p, 0)
            if r_val != c_val:
                diffs.append(StateVariableDiff(f"market_inv_{p}", r_val, c_val, c_val - r_val, critical=False))

        # Market prices
        for p in PRODUCTS:
            r_val = real_m_prices.get(p, 0)
            c_val = cf_m_prices.get(p, 0)
            if r_val != c_val:
                diffs.append(StateVariableDiff(f"market_price_{p}", r_val, c_val, c_val - r_val, critical=True))

        passed = len(diffs) == 0
        return ParityComparisonResult(
            passed=passed,
            step=step,
            seed=seed,
            diffs=diffs,
            real_post_state={"money": real_money, "shed": real_shed, "market_inv": real_m_inv, "market_prices": real_m_prices},
            cf_post_state={"money": cf_money, "shed": cf_shed, "market_inv": cf_m_inv, "market_prices": cf_m_prices}
        )
