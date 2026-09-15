import sys
import os
import json
import kaggle_environments

sys.path.insert(0, os.path.abspath('.'))

import candidates.candidate_cl_fert_gated as m1_module
from scratch.run_wheat_quota_sweep_50seeds import ParameterizedQuotaAgent

def trace_seed(seed):
    cfg = {"episodeSteps": 720, "seed": seed}

    def trace_agent(agent, name):
        env = kaggle_environments.make("kaggriculture", configuration=cfg)
        steps = env.run([agent, "starter"])
        
        daily_events = []
        for d in range(30):
            # snapshot at hour 23
            st_idx = d * 24 + 23
            if st_idx >= len(steps): st_idx = len(steps) - 1
            st = steps[st_idx]
            obs = st[0]["observation"]
            farm = obs["farms"][0]
            priv = obs["private"]
            tiles = farm["tiles"]
            shed = priv["shed"]
            
            cows_pos = {}
            sheep_pos = {}
            for y in range(len(tiles)):
                for x in range(len(tiles[y])):
                    t = tiles[y][x]
                    if isinstance(t, dict) and "animal" in t:
                        if t["animal"] == "COW":
                            cows_pos[(x, y)] = {"yield": t.get("yield_units"), "fed": t.get("fed_today"), "cared": t.get("cared_today")}
                        elif t["animal"] == "SHEEP":
                            sheep_pos[(x, y)] = {"yield": t.get("yield_units"), "fed": t.get("fed_today"), "cared": t.get("cared_today")}

            daily_events.append({
                "day": d,
                "cows_on_field": len(cows_pos),
                "sheep_on_field": len(sheep_pos),
                "cows_pos": list(cows_pos.keys()),
                "sheep_pos": list(sheep_pos.keys()),
                "shed_cow": shed.get("COW", 0),
                "shed_sheep": shed.get("SHEEP", 0),
                "money": farm.get("money", 0)
            })

        sold = {"WHEAT": 0, "WOOL": 0, "STRAWBERRY": 0, "MILK": 0}
        for st in steps:
            for o in (st[0].get("action") or {}).get("market", []):
                if isinstance(o, list) and len(o) >= 3 and o[0] == "SELL":
                    if o[1] in sold: sold[o[1]] += o[2]

        return {
            "name": name,
            "reward": steps[-1][0]["reward"],
            "sold": sold,
            "daily": daily_events
        }

    m1_trace = trace_agent(m1_module.ClosedLoopEconomicV1(), "M1")
    q50_trace = trace_agent(ParameterizedQuotaAgent(50), "Q50")

    return m1_trace, q50_trace

def main():
    seeds_to_check = [1004, 1000, 1050]
    for s in seeds_to_check:
        print(f"\n=======================================================")
        print(f"TRACING SEED {s}")
        print(f"=======================================================")
        m1_t, q50_t = trace_seed(s)
        print(f"M1:  Reward=${m1_t['reward']:,.0f} | Wool={m1_t['sold']['WOOL']} | Wheat={m1_t['sold']['WHEAT']}")
        print(f"Q50: Reward=${q50_t['reward']:,.0f} | Wool={q50_t['sold']['WOOL']} | Wheat={q50_t['sold']['WHEAT']}")
        
        print("\nDay-by-Day Livestock Comparison (Days 5 to 15):")
        print(f"{'Day':<4} | {'M1: Field(C/S) Shed(C/S)':<26} {'M1 Sheep Tiles':<20} | {'Q50: Field(C/S) Shed(C/S)':<26} {'Q50 Sheep Tiles':<20}")
        for d in range(5, 16):
            m = m1_t["daily"][d]
            q = q50_t["daily"][d]
            m_str = f"C:{m['cows_on_field']} S:{m['sheep_on_field']} | Shed C:{m['shed_cow']} S:{m['shed_sheep']}"
            q_str = f"C:{q['cows_on_field']} S:{q['sheep_on_field']} | Shed C:{q['shed_cow']} S:{q['shed_sheep']}"
            print(f"{d:<4} | {m_str:<26} {str(m['sheep_pos']):<20} | {q_str:<26} {str(q['sheep_pos']):<20}")

if __name__ == "__main__":
    main()
