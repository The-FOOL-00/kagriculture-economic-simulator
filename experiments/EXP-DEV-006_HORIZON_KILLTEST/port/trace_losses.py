# SPDX-License-Identifier: MIT
"""Instrumented replay of the two DEV-005 loss seeds (247025, 247034).

For each seed plays:
  M1: dev005 (seat S) vs baseline  -- treatment world
  M0: baseline (seat S) vs baseline -- counterfactual world (S in {0,1})
Pre-288 the focal seat is backbone policy in both worlds, so money paths are
identical until the switch; the first post-288 divergence is the treatment
effect onset. Logs per-step money, herd sizes, and focal market orders.
Allowed seeds: 247025, 247034 ONLY.
"""
import os
import sys
import json
import importlib.util

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
PORT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PORT_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))

import kagsim_py as kagsim
from dev_005_confirmed_shop_scheduler import Dev005ConfirmedShopScheduler

BASELINE_PATH = os.path.join(BASE_DIR, "candidates", "compiled_v54_plus_residual.py")
ALLOWED = (247025, 247034)


def load_baseline(name):
    spec = importlib.util.spec_from_file_location(name, BASELINE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def herd_of(obs_farm, priv):
    sheep_tiles = sum(1 for row in obs_farm["tiles"] for t in row
                      if isinstance(t, dict) and t.get("animal") == "SHEEP")
    cow_tiles = sum(1 for row in obs_farm["tiles"] for t in row
                    if isinstance(t, dict) and t.get("animal") == "COW")
    return {"sheep_tiles": sheep_tiles, "cow_tiles": cow_tiles,
            "shed_sheep": priv["shed"].get("SHEEP", 0),
            "shed_cow": priv["shed"].get("COW", 0),
            "shed_wheat": priv["shed"].get("WHEAT", 0)}


def play(seed, focal_cls, focal_seat):
    assert seed in ALLOWED, seed
    g = kagsim.Game(seed)
    focal = focal_cls(seat=focal_seat, seed=seed) if focal_cls is not None else None
    base_mod = load_baseline(f"tr_{seed}_{focal_seat}_{focal_cls is not None}")
    other = load_baseline(f"tro_{seed}_{focal_seat}_{focal_cls is not None}")
    trace = []
    while not g.done:
        o = g.observe(focal_seat)
        step = o["step"]
        if focal_cls is None:
            a_focal = base_mod.agent(g.observe(focal_seat))
        else:
            a_focal = focal.act(o)
        oo = 1 - focal_seat
        a_other = other.agent(g.observe(oo))
        if focal_seat == 0:
            g.step(a_focal, a_other)
        else:
            g.step(a_other, a_focal)
        o2 = g.observe(focal_seat)
        o_opp = g.observe(oo)
        trace.append({"step": step,
                      "money": float(o2["farms"][focal_seat]["money"]),
                      "opp_money": float(o2["farms"][oo]["money"]),
                      "shops": list(o2["town"]["unlocked_shops"]),
                      "herd": herd_of(o2["farms"][focal_seat], o2["private"]),
                      "market": [list(x) for x in a_focal.get("market", [])],
                      "farmer": list(a_focal.get("farmer", []))})
    return trace, (focal.decision_events if focal_cls is not None else None)


def main():
    out = {}
    for seed in ALLOWED:
        out[seed] = {}
        for seat in (0, 1):
            tr_treat, deci = play(seed, Dev005ConfirmedShopScheduler, seat)
            tr_base, _ = play(seed, None, seat)
            assert len(tr_treat) == len(tr_base) == 719
            # pre-288 identity check + first divergence
            pre_ok = all(tr_treat[t]["money"] == tr_base[t]["money"] for t in range(288))
            first_div = None
            for t in range(288, 719):
                if tr_treat[t]["money"] != tr_base[t]["money"]:
                    first_div = t
                    break
            # post-288 order-class summary for focal agent
            buy_sell = {}
            for t in range(288, 719):
                for o in tr_treat[t]["market"]:
                    key = tuple(o[:2])
                    buy_sell[key] = buy_sell.get(key, 0) + (o[2] if len(o) > 2 else 1)
            # first ACTION divergence (market or farmer) at/after 288
            first_act = None
            for t in range(288, 719):
                if (tr_treat[t]["market"] != tr_base[t]["market"]
                        or tr_treat[t]["farmer"] != tr_base[t]["farmer"]):
                    first_act = t
                    break
            # shop-sequence divergence between worlds
            shop_div = None
            for t in range(719):
                if tr_treat[t]["shops"] != tr_base[t]["shops"]:
                    shop_div = t
                    break
            out[seed][seat] = {
                "pre288_money_identical": pre_ok,
                "first_money_divergence_step": first_div,
                "first_action_divergence_step": first_act,
                "shop_divergence_step": shop_div,
                "money_treat_end": tr_treat[-1]["money"],
                "money_base_end": tr_base[-1]["money"],
                "opp_money_treat_end": tr_treat[-1]["opp_money"],
                "opp_money_base_end": tr_base[-1]["opp_money"],
                "shops_treat_end": tr_treat[-1]["shops"],
                "shops_base_end": tr_base[-1]["shops"],
                "herd_treat_end": tr_treat[-1]["herd"],
                "herd_base_end": tr_base[-1]["herd"],
                "treat_post288_market_totals": {str(k): v for k, v in sorted(buy_sell.items())},
                "money_path_treat": [r["money"] for r in tr_treat],
                "money_path_base": [r["money"] for r in tr_base],
                "opp_path_treat": [r["opp_money"] for r in tr_treat],
                "opp_path_base": [r["opp_money"] for r in tr_base],
                "sheep_tiles_treat": [r["herd"]["sheep_tiles"] for r in tr_treat],
                "sheep_tiles_base": [r["herd"]["sheep_tiles"] for r in tr_base],
                "shops_path_treat": [r["shops"] for r in tr_treat],
                "shops_path_base": [r["shops"] for r in tr_base],
            }
            print(f"seed {seed} seat {seat}: pre288_identical={pre_ok} "
                  f"first_money_div={first_div} first_act_div={first_act} "
                  f"shop_div={shop_div} treat_end={tr_treat[-1]['money']} "
                  f"base_end={tr_base[-1]['money']} "
                  f"opp_treat={tr_treat[-1]['opp_money']} opp_base={tr_base[-1]['opp_money']}",
                  flush=True)
            print(f"  shops_treat={tr_treat[-1]['shops']}", flush=True)
            print(f"  shops_base ={tr_base[-1]['shops']}", flush=True)
    with open(os.path.join(PORT_DIR, "loss_seed_traces.json"), "w") as f:
        json.dump(out, f)
    print("wrote loss_seed_traces.json")


if __name__ == "__main__":
    main()
