import sys
import os
import kaggle_environments

sys.path.insert(0, os.path.abspath('.'))

import candidates.candidate_cl_fert_gated as m1_module
from scratch.run_wheat_quota_sweep_50seeds import ParameterizedQuotaAgent

def audit_seed_deep(seed):
    print(f"==================================================")
    print(f"DEEP DIVE: SEED {seed}")
    print(f"==================================================")
    cfg = {"episodeSteps": 720, "seed": seed}

    def run_agent(agent_cls, *args):
        agent_inst = agent_cls(*args) if args else agent_cls()
        env = kaggle_environments.make("kaggriculture", configuration=cfg)
        log = []

        orig_call = agent_inst.__call__
        def wrapped_call(obs, config=None):
            step = int(obs.get("step", 0) or 0)
            p = int(obs.get("player", 0) or 0)
            farms = obs.get("farms") or [{}, {}]
            farm = farms[p] if p < len(farms) else {}
            tiles = farm.get("tiles") or []
            priv = obs.get("private") or {}
            
            sheep_tiles = {}
            cow_tiles = {}
            wheat_tiles = {}
            for y in range(len(tiles)):
                for x in range(len(tiles[y])):
                    t = tiles[y][x]
                    if isinstance(t, dict):
                        if t.get("animal") == "SHEEP":
                            sheep_tiles[(x, y)] = dict(t)
                        elif t.get("animal") == "COW":
                            cow_tiles[(x, y)] = dict(t)
                        elif t.get("crop") == "WHEAT":
                            wheat_tiles[(x, y)] = dict(t)

            action = orig_call(obs, config)
            log.append({
                "step": step,
                "day": step // 24,
                "hour": step % 24,
                "money": farm.get("money", 0),
                "shed": dict(priv.get("shed", {})),
                "seeds": dict(priv.get("seeds", {})),
                "invs": list(priv.get("inventories", [])),
                "farmer": farm.get("farmer"),
                "hands": list(farm.get("hands", [])),
                "sheep_tiles": sheep_tiles,
                "cow_tiles": cow_tiles,
                "wheat_tiles": wheat_tiles,
                "action": action
            })
            return action

        agent_inst.__call__ = wrapped_call
        steps = env.run([agent_inst, "starter"])
        return steps[-1][0]["reward"], log

    rew_m1, log_m1 = run_agent(m1_module.ClosedLoopEconomicV1)
    rew_q50, log_q50 = run_agent(ParameterizedQuotaAgent, 50)

    print(f"Seed {seed} | M1 Rew: {rew_m1:,.0f} | Q50 Rew: {rew_q50:,.0f} | Diff: {rew_q50 - rew_m1:+,.0f}")

    def analyze_buys_and_places(log, name):
        buys = []
        places = []
        for e in log:
            act = e["action"]
            if isinstance(act, dict):
                for o in act.get("market", []):
                    if isinstance(o, list) and len(o) >= 3 and o[0] == "BUY_ANIMAL":
                        buys.append((e["day"], e["hour"], o[1], o[2], e["money"]))
                w_acts = [act.get("farmer", ["PASS"])] + act.get("hands", [])
                for w_idx, w_act in enumerate(w_acts):
                    if isinstance(w_act, list) and len(w_act) >= 2 and w_act[0] == "PLACE":
                        places.append((e["day"], e["hour"], w_idx, w_act[1]))
        print(f"\n[{name}] Animal Buys ({len(buys)}):")
        for b in buys:
            print(f"  Day {b[0]:2d} Hr {b[1]:2d}: Bought {b[3]} {b[2]} (Money: {b[4]:.0f})")
        print(f"[{name}] Animal Placements ({len(places)}):")
        for p in places:
            print(f"  Day {p[0]:2d} Hr {p[1]:2d}: Worker {p[2]} PLACED {p[3]}")

    analyze_buys_and_places(log_m1, "M1")
    analyze_buys_and_places(log_q50, "Q50")

    # Trace sheep state divergence
    print("\n--- SHEEP COUNTS & ESCAPES ---")
    for d in range(30):
        e1 = [x for x in log_m1 if x["day"] == d and x["hour"] == 23][0]
        e2 = [x for x in log_q50 if x["day"] == d and x["hour"] == 23][0]
        s1 = len(e1["sheep_tiles"])
        s2 = len(e2["sheep_tiles"])
        u1_fed = sum(1 for t in e1["sheep_tiles"].values() if not t.get("fed_today"))
        u2_fed = sum(1 for t in e2["sheep_tiles"].values() if not t.get("fed_today"))
        u1_care = sum(1 for t in e1["sheep_tiles"].values() if not t.get("cared_today"))
        u2_care = sum(1 for t in e2["sheep_tiles"].values() if not t.get("cared_today"))
        if s1 != s2 or u1_fed != u2_fed or u1_care != u2_care:
            print(f"Day {d:2d}: M1 Sheep={s1} (unfed={u1_fed}, uncared={u1_care}) | Q50 Sheep={s2} (unfed={u2_fed}, uncared={u2_care})")

if __name__ == "__main__":
    audit_seed_deep(1060)
