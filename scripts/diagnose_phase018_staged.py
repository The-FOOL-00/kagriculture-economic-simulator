#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Phase 018 §25: diagnostic staged-vs-lump counterfactual (preregistered sample).

Replays 2 B2-S1 match prefixes, captures states at blocked-promising wheat
tranches, and compares lump-sum vs staged (SELL q1 now + SELL q2 at t+k)
execution under the frozen Phase016 evaluator. Diagnostic only: answers whether
negative results come from lump-sum execution rather than the opportunity.

Sample (preregistered from B2-S1 ledger: local>0, escalated, uncommitted):
  249323/seat0/step290: WHEAT q13 (loc+496/fin+16), q5 (loc+194/fin+12)
  249322/seat1/step251: WHEAT q12 (loc+232/fin-52), q10 (loc+170/fin-30)
  249322/seat1/step291: WHEAT q8 (loc+310/fin-3), q5 (loc+193/fin-4)
Plus top-local safety-failed wheat patch per captured step when present.
Verdict rule (preregistered): staged materially better (sign flip to >+$15 or
>2x improvement) in >=3 states -> representation matters (Outcome D direction).

Writes results/PHASE018_STAGED_DIAGNOSTIC.json.
"""

from __future__ import annotations

import copy
import json
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
CPPSIM = os.path.join(REPO_ROOT, "external_repos", "kaggriculture-cppsim")
if CPPSIM not in sys.path:
    sys.path.insert(0, CPPSIM)

import kagsim
from aec.config import build_phase018_arm_b2_s1_config, build_phase018_arm_b2_control_config
from aec.counterfactual.horizon import select_adaptive_horizon
from aec.counterfactual.macro_detector import MacroRegimeTransitionDetector
from aec.counterfactual.simulator import CounterfactualSimulator
from aec.integration.executor import AECExecutor
from aec.market.tranche_synthesizer import AutonomousTrancheOrderSynthesizer
from aec.patches.patch import CoupledPatch

SAMPLE = [
    (249323, 0, 290, "WHEAT", 13),
    (249323, 0, 290, "WHEAT", 5),
    (249322, 1, 251, "WHEAT", 12),
    (249322, 1, 251, "WHEAT", 10),
    (249322, 1, 291, "WHEAT", 8),
    (249322, 1, 291, "WHEAT", 5),
]
SPLITS = (0.5, 0.34)
DELAYS = (6, 12)
OUT = os.path.join(REPO_ROOT, "results", "PHASE018_STAGED_DIAGNOSTIC.json")


def capture_states():
    """Replay prefixes; capture (econ_state, baseline_action, continuation)."""
    by_seed = {}
    for seed, seat, step, comm, qty in SAMPLE:
        by_seed.setdefault((seed, seat), []).append((step, comm, qty))
    caps = {}
    synth = AutonomousTrancheOrderSynthesizer()
    for (seed, seat), wants in sorted(by_seed.items()):
        max_step = max(w[0] for w in wants)
        game = kagsim.Game(seed)
        trt = AECExecutor(config=build_phase018_arm_b2_s1_config())
        ctrl = AECExecutor(config=build_phase018_arm_b2_control_config())
        targets = {w[0] for w in wants}
        while not game.done and game.step_count <= max_step:
            o0, o1 = game.observe(0), game.observe(1)
            step_now = int(o0.get("step", 0) or 0)
            if seat == 0:
                a0, a1 = trt.act(o0), ctrl.act(o1)
            else:
                a0, a1 = ctrl.act(o0), trt.act(o1)
            if step_now in targets:
                base = trt.backbone.get_cached_result()
                assert base is not None
                baseline_action = base.canonical_action_copy()
                econ_state = copy.deepcopy(trt._prev_econ_state)
                n_hands = max(0, len(econ_state.workers.workers) - 1)
                cont = trt.backbone.get_future_trajectory(
                    step=step_now, horizon=trt.config.extended_horizon,
                    player=econ_state.player, n_hands=n_hands)
                v3fn = trt.backbone._agent_fn
                for (wstep, comm, qty) in wants:
                    if wstep == step_now:
                        caps[(seed, seat, step_now, comm, qty)] = {
                            "econ_state": econ_state, "baseline_action": baseline_action,
                            "continuation": cont, "v3fn": v3fn, "config": trt.config,
                        }
            game.step(a0, a1)
    return caps, synth


def evaluate(patch, baseline_action, econ_state, horizon, continuation, v3fn,
             probe_res, sim, detector):
    macro = probe_res.requires_escalation
    out = sim.evaluate(
        candidate_patch=patch, baseline_action=baseline_action,
        econ_state=econ_state, horizon=horizon,
        continuation_trajectory=continuation[: max(0, horizon - 1)] if continuation else None,
        v3_agent_callable=v3fn, macro_escalated=macro,
        macro_escalation_reason=probe_res.reason if macro else "",
        macro_regime_type=probe_res.regime_type.value,
    )
    return out


def main():
    caps, synth = capture_states()
    assert len(caps) == len(SAMPLE), f"captured {len(caps)}/{len(SAMPLE)}"
    detector = MacroRegimeTransitionDetector()
    sim = CounterfactualSimulator()
    report = []
    for key in SAMPLE:
        seed, seat, step, comm, qty = key
        cap = caps[key]
        es, base_act = cap["econ_state"], cap["baseline_action"]
        cont, v3fn, cfg = cap["continuation"], cap["v3fn"], cap["config"]

        def mkpatch(q, tag):
            orders = synth.construct_sequential_market_orders(
                base_act.get("market", []), comm, q)
            return CoupledPatch(
                patch_id=f"DIAG_{tag}_{comm}_q{q}_S{step}",
                source_opportunity_id=f"DIAG_{seed}_{step}",
                mechanism_family="AUTONOMOUS_TRANCHE_ORDER_SYNTHESIZER",
                market_mutations=orders)

        lump = mkpatch(qty, "LUMP")
        probe_lump = detector.probe_candidate(lump, base_act, es)
        h_lump = select_adaptive_horizon(lump, es, cfg, cont, macro_probe_result=probe_lump)
        out_lump = evaluate(lump, base_act, es, h_lump, cont, v3fn, probe_lump, sim, detector)
        row = {"seed": seed, "seat": seat, "step": step, "commodity": comm, "qty": qty,
               "lump": {"margin": out_lump.delta_terminal_margin,
                        "money": out_lump.delta_our_money,
                        "horizon": h_lump, "escalated": probe_lump.requires_escalation,
                        "regime": probe_lump.regime_type.value},
               "staged": []}
        for frac in SPLITS:
            q1 = max(1, min(qty - 1, int(round(qty * frac))))
            q2 = qty - q1
            if q2 < 1:
                continue
            for k in DELAYS:
                leg1 = mkpatch(q1, f"STAGE1_{q1}")
                spliced = [copy.deepcopy(a) for a in (cont or [])]
                if len(spliced) >= k:
                    tape_mkt = spliced[k - 1].get("market", []) or []
                    leg2_mkt = synth.construct_sequential_market_orders(tape_mkt, comm, q2)
                    spliced[k - 1] = dict(spliced[k - 1], market=leg2_mkt)
                    leg1.spliced_continuation = spliced
                probe_s = detector.probe_candidate(leg1, base_act, es)
                h_s = select_adaptive_horizon(leg1, es, cfg, cont, macro_probe_result=probe_s)
                out_s = evaluate(leg1, base_act, es, h_s, cont, v3fn, probe_s, sim, detector)
                row["staged"].append(
                    {"q1": q1, "q2": q2, "k": k, "margin": out_s.delta_terminal_margin,
                     "money": out_s.delta_our_money, "horizon": h_s,
                     "escalated": probe_s.requires_escalation,
                     "regime": probe_s.regime_type.value})
        report.append(row)
        print(f"{seed}/{seat}@{step} {comm}q{qty}: lump={row['lump']['margin']:+.1f} "
              f"best_staged={max([s['margin'] for s in row['staged']], default=float('nan')):+.1f}")
    with open(OUT, "w") as f:
        json.dump(report, f, indent=2)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
