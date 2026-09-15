import sys
import os
import json
import kaggle_environments

sys.path.insert(0, os.path.abspath('.'))

import candidates.candidate_cl_fert_gated as m1_module
from scratch.run_wheat_quota_sweep_50seeds import ParameterizedQuotaAgent

def run_phase_diagnostics():
    seeds = [1060, 1086, 1076, 1047, 1004]
    
    diag = {
        "seeds": seeds,
        "phase2_reasons": {
            "unfed": 0,
            "uncared": 0,
            "fed_late": 0,
            "cared_late": 0,
            "worker_occupied_by_wheat": 0,
            "animal_trapped_in_shed": 0,
            "slot_occupied_by_cow": 0,
            "sheep_escaped": 0
        },
        "phase3_matrix": {
            "hours_0_to_4": {"sheep_crit": "VERY HIGH (morning feed+care)", "wheat_crit": "MED (ripe harvest/water)", "conflict_count": 0},
            "hours_5_to_11": {"sheep_crit": "MED (residual care/milk/wool)", "wheat_crit": "HIGH (field maintenance)", "conflict_count": 0},
            "hours_12_to_19": {"sheep_crit": "LOW (already fed/cared)", "wheat_crit": "HIGH (harvest/water/plant)", "conflict_count": 0},
            "hours_20_to_23": {"sheep_crit": "VERY HIGH (emergency feeding before midnight)", "wheat_crit": "LOW (should yield to avoid escape)", "conflict_count": 0}
        },
        "phase4_wrong_worker": {
            "wheat_harvests_during_sheep_unmet": 0,
            "wheat_harvests_stealing_nearby_worker": 0,
            "wheat_harvests_could_be_deferred": 0,
            "sheep_cycles_lost": 0
        },
        "phase5_opportunistic": {
            "worker_pass_turns": 0,
            "wheat_harvestable_during_idle": 0,
            "upper_bound_wheat_units": 0,
            "upper_bound_wheat_revenue": 0.0
        },
        "phase7_timing": {
            "total_wheat_harvests": 0,
            "harvested_at_yu_4": 0,
            "harvested_at_yu_5": 0,
            "harvested_at_yu_6": 0,
            "harvested_before_decay": 0,
            "decayed_units": 0
        },
        "phase9_labor": {
            "wool_price_mean": 0.0,
            "wheat_price_mean": 0.0,
            "milk_price_mean": 0.0,
            "straw_price_mean": 0.0,
            "sheep_care_action_value": 0.0,
            "wheat_harvest_action_value": 0.0,
            "opportunity_ratio": 0.0
        }
    }

    class TrackingAgent:
        def __init__(self, base_cls, *args):
            self.agent = base_cls(*args) if args else base_cls()
            self.logs = []

        def __call__(self, obs, config=None):
            step = int(obs.get("step", 0) or 0)
            p = int(obs.get("player", 0) or 0)
            farm = (obs.get("farms") or [{}, {}])[p]
            tiles = farm.get("tiles") or []
            priv = obs.get("private") or {}
            shed = dict(priv.get("shed") or {})
            market = (obs.get("market") or {})
            prices = dict(market.get("prices") or {})

            sheep_info = {}
            cow_info = {}
            wheat_info = {}
            for y in range(10):
                for x in range(10):
                    t = tiles[y][x]
                    if isinstance(t, dict):
                        anim = t.get("animal")
                        crop = t.get("crop")
                        if anim == "SHEEP":
                            sheep_info[(x, y)] = dict(t)
                        elif anim == "COW":
                            cow_info[(x, y)] = dict(t)
                        elif crop == "WHEAT":
                            wheat_info[(x, y)] = dict(t)

            act = self.agent(obs, config)
            w_acts = [act.get("farmer", ["PASS"])] + act.get("hands", [])
            w_pos = [tuple(farm.get("farmer", [4, 4]))] + [tuple(h) for h in farm.get("hands", [])]

            self.logs.append({
                "step": step,
                "day": step // 24,
                "hour": step % 24,
                "money": farm.get("money", 0),
                "shed": shed,
                "prices": prices,
                "sheep": sheep_info,
                "cows": cow_info,
                "wheat": wheat_info,
                "w_acts": w_acts,
                "w_pos": w_pos,
                "worker_targets": dict(getattr(self.agent, "_worker_targets", {}))
            })
            return act

    prices_collector = {"WOOL": [], "WHEAT": [], "MILK": [], "STRAWBERRY": []}

    for s in seeds:
        cfg = {"episodeSteps": 720, "seed": s}
        
        m1_agent = TrackingAgent(m1_module.ClosedLoopEconomicV1)
        env = kaggle_environments.make("kaggriculture", configuration=cfg)
        m1_steps = env.run([m1_agent, "starter"])
        m1_rew = m1_steps[-1][0]["reward"]

        q50_agent = TrackingAgent(ParameterizedQuotaAgent, 50)
        env = kaggle_environments.make("kaggriculture", configuration=cfg)
        q50_steps = env.run([q50_agent, "starter"])
        q50_rew = q50_steps[-1][0]["reward"]

        # Collect prices
        for e in q50_agent.logs:
            for it in prices_collector:
                if it in e["prices"]:
                    prices_collector[it].append(e["prices"][it])

        # Step by step analysis
        for eq in q50_agent.logs:
            day, hr = eq["day"], eq["hour"]
            
            # Check hungry or uncared sheep
            hungry_sheep = [pos for pos, sh in eq["sheep"].items() if not sh.get("fed_today")]
            uncared_sheep = [pos for pos, sh in eq["sheep"].items() if not sh.get("cared_today")]
            sheep_needing_care = len(hungry_sheep) + len(uncared_sheep)

            # Check conflicts by hour
            for w, a in enumerate(eq["w_acts"]):
                pos = eq["w_pos"][w]
                if isinstance(a, list) and a[0] == "HARVEST" and pos in eq["wheat"]:
                    diag["phase7_timing"]["total_wheat_harvests"] += 1
                    yu = eq["wheat"][pos].get("yield_units", 0)
                    if yu <= 4: diag["phase7_timing"]["harvested_at_yu_4"] += 1
                    elif yu == 5: diag["phase7_timing"]["harvested_at_yu_5"] += 1
                    else: diag["phase7_timing"]["harvested_at_yu_6"] += 1

                    if sheep_needing_care > 0:
                        diag["phase4_wrong_worker"]["wheat_harvests_during_sheep_unmet"] += 1
                        diag["phase4_wrong_worker"]["wheat_harvests_could_be_deferred"] += 1
                        targets = hungry_sheep + uncared_sheep
                        min_d_sheep = min(abs(pos[0]-sp[0]) + abs(pos[1]-sp[1]) for sp in targets)
                        if min_d_sheep <= 4:
                            diag["phase4_wrong_worker"]["wheat_harvests_stealing_nearby_worker"] += 1
                        
                        if 0 <= hr <= 4: diag["phase3_matrix"]["hours_0_to_4"]["conflict_count"] += 1
                        elif 5 <= hr <= 11: diag["phase3_matrix"]["hours_5_to_11"]["conflict_count"] += 1
                        elif 12 <= hr <= 19: diag["phase3_matrix"]["hours_12_to_19"]["conflict_count"] += 1
                        else: diag["phase3_matrix"]["hours_20_to_23"]["conflict_count"] += 1

                if isinstance(a, list) and a[0] == "PASS":
                    diag["phase5_opportunistic"]["worker_pass_turns"] += 1
                    for wp, wt in eq["wheat"].items():
                        if abs(pos[0]-wp[0]) + abs(pos[1]-wp[1]) <= 1 and wt.get("yield_units", 0) >= 4:
                            diag["phase5_opportunistic"]["wheat_harvestable_during_idle"] += 1
                            break

        # Check end of day sheep audit for escapes and unplaced sheep
        for d in range(29):
            em_list = [x for x in m1_agent.logs if x["day"] == d and x["hour"] == 23]
            eq_list = [x for x in q50_agent.logs if x["day"] == d and x["hour"] == 23]
            if not em_list or not eq_list: continue
            em, eq = em_list[0], eq_list[0]
            m_sh = len(em["sheep"])
            q_sh = len(eq["sheep"])
            if q_sh < m_sh:
                diag["phase2_reasons"]["sheep_escaped"] += (m_sh - q_sh)
            
            unfed_q = sum(1 for sh in eq["sheep"].values() if not sh.get("fed_today"))
            uncared_q = sum(1 for sh in eq["sheep"].values() if not sh.get("cared_today"))
            diag["phase2_reasons"]["unfed"] += unfed_q
            diag["phase2_reasons"]["uncared"] += uncared_q

            if eq["shed"].get("SHEEP", 0) > 0:
                diag["phase2_reasons"]["animal_trapped_in_shed"] += eq["shed"]["SHEEP"]

    # Compute labor values
    mean_wool = sum(prices_collector["WOOL"]) / max(1, len(prices_collector["WOOL"]))
    mean_wheat = sum(prices_collector["WHEAT"]) / max(1, len(prices_collector["WHEAT"]))
    mean_milk = sum(prices_collector["MILK"]) / max(1, len(prices_collector["MILK"]))
    mean_straw = sum(prices_collector["STRAWBERRY"]) / max(1, len(prices_collector["STRAWBERRY"]))

    diag["phase9_labor"]["wool_price_mean"] = round(mean_wool, 2)
    diag["phase9_labor"]["wheat_price_mean"] = round(mean_wheat, 2)
    diag["phase9_labor"]["milk_price_mean"] = round(mean_milk, 2)
    diag["phase9_labor"]["straw_price_mean"] = round(mean_straw, 2)

    diag["phase9_labor"]["sheep_care_action_value"] = round(mean_wool, 2)
    diag["phase9_labor"]["wheat_harvest_action_value"] = round(mean_wheat * 4.5, 2)
    diag["phase9_labor"]["opportunity_ratio"] = round(diag["phase9_labor"]["sheep_care_action_value"] / max(1, diag["phase9_labor"]["wheat_harvest_action_value"]), 2)

    # Opportunistic upper bound
    diag["phase5_opportunistic"]["upper_bound_wheat_units"] = diag["phase5_opportunistic"]["wheat_harvestable_during_idle"] * 4
    diag["phase5_opportunistic"]["upper_bound_wheat_revenue"] = round(diag["phase5_opportunistic"]["upper_bound_wheat_units"] * mean_wheat, 2)

    with open("scratch/full_phases_2_to_9_results.json", "w") as f:
        json.dump(diag, f, indent=2)

    print("=== FULL PHASES 2 TO 9 DIAGNOSTIC COMPLETE ===")
    print(json.dumps(diag, indent=2))

if __name__ == "__main__":
    run_phase_diagnostics()
