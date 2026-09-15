import sys
import os
import json
import kaggle_environments

sys.path.insert(0, os.path.abspath('.'))

import candidates.candidate_cl_fert_gated as m1_module
from scratch.run_wheat_quota_sweep_50seeds import ParameterizedQuotaAgent

class DetailedInstrumentedAgent:
    def __init__(self, base_cls, *args):
        self.agent = base_cls(*args) if args else base_cls()
        self.history = []

    def __call__(self, obs, config=None):
        step = int(obs.get("step", 0) or 0)
        p = int(obs.get("player", 0) or 0)
        farms = obs.get("farms") or [{}, {}]
        farm = farms[p] if p < len(farms) else {}
        tiles = farm.get("tiles") or []
        priv = obs.get("private") or {}
        shed = dict(priv.get("shed") or {})
        seeds = dict(priv.get("seeds") or {})
        invs = list(priv.get("inventories") or [])

        # Record field state
        sheep = {}
        cows = {}
        wheat = {}
        for y in range(len(tiles)):
            for x in range(len(tiles[y])):
                t = tiles[y][x]
                if isinstance(t, dict):
                    k = t.get("kind")
                    anim = t.get("animal")
                    crop = t.get("crop")
                    if anim == "SHEEP":
                        sheep[(x, y)] = dict(t)
                    elif anim == "COW":
                        cows[(x, y)] = dict(t)
                    elif crop == "WHEAT":
                        wheat[(x, y)] = dict(t)

        act = self.agent(obs, config)

        w_acts = [act.get("farmer", ["PASS"])] + act.get("hands", [])
        w_pos = [tuple(farm.get("farmer", [4, 4]))] + [tuple(h) for h in farm.get("hands", [])]

        self.history.append({
            "step": step,
            "day": step // 24,
            "hour": step % 24,
            "money": farm.get("money", 0),
            "shed": shed,
            "seeds": seeds,
            "invs": invs,
            "sheep": sheep,
            "cows": cows,
            "wheat": wheat,
            "w_pos": w_pos,
            "w_acts": w_acts,
            "market": act.get("market", [])
        })
        return act

def audit_seed(seed):
    cfg = {"episodeSteps": 720, "seed": seed}

    # Run M1
    m1_inst = DetailedInstrumentedAgent(m1_module.ClosedLoopEconomicV1)
    env = kaggle_environments.make("kaggriculture", configuration=cfg)
    steps_m1 = env.run([m1_inst, "starter"])
    rew_m1 = steps_m1[-1][0]["reward"]

    # Run Q50
    q50_inst = DetailedInstrumentedAgent(ParameterizedQuotaAgent, 50)
    env = kaggle_environments.make("kaggriculture", configuration=cfg)
    steps_q50 = env.run([q50_inst, "starter"])
    rew_q50 = steps_q50[-1][0]["reward"]

    print(f"\n=======================================================")
    print(f"AUDIT FOR SEED {seed}")
    print(f"M1: ${rew_m1:,.0f} | Q50: ${rew_q50:,.0f} | Delta: ${rew_q50 - rew_m1:+,.0f}")
    print(f"=======================================================")

    # 1. Animal purchase & placement tracking
    def get_animal_events(history):
        events = []
        for h in history:
            d, hr = h["day"], h["hour"]
            for o in h["market"]:
                if isinstance(o, list) and len(o) >= 3 and o[0] == "BUY_ANIMAL":
                    events.append((d, hr, f"BUY {o[2]} {o[1]}", h["money"]))
            for w_idx, a in enumerate(h["w_acts"]):
                if isinstance(a, list) and len(a) >= 2 and a[0] == "PLACE":
                    events.append((d, hr, f"PLACE {a[1]} by worker {w_idx} at {h['w_pos'][w_idx]}", h["money"]))
        return events

    m1_events = get_animal_events(m1_inst.history)
    q50_events = get_animal_events(q50_inst.history)

    print("\n--- ANIMAL EVENTS ---")
    print("M1 Events:")
    for e in m1_events:
        print(f"  Day {e[0]:2d} Hr {e[1]:2d}: {e[2]} (Money: ${e[3]:,.0f})")
    print("Q50 Events:")
    for e in q50_events:
        print(f"  Day {e[0]:2d} Hr {e[1]:2d}: {e[2]} (Money: ${e[3]:,.0f})")

    # 2. Daily Wool Harvest & Production
    def get_wool_timeline(history):
        wool_harvested = 0
        daily_harvest = []
        for d in range(30):
            d_harvest = 0
            for hr in range(24):
                step = d * 24 + hr
                h = history[step]
                for w_idx, a in enumerate(h["w_acts"]):
                    if isinstance(a, list) and a[0] == "HARVEST":
                        pos = h["w_pos"][w_idx]
                        if pos in h["sheep"]:
                            # Sheep harvest!
                            yu = h["sheep"][pos].get("yield_units", 0)
                            d_harvest += yu
            wool_harvested += d_harvest
            daily_harvest.append((d, d_harvest, wool_harvested))
        return daily_harvest

    m1_wool = get_wool_timeline(m1_inst.history)
    q50_wool = get_wool_timeline(q50_inst.history)

    print("\n--- DAILY WOOL HARVEST COMPARISON ---")
    print(f"{'Day':<4} | {'M1 Day Wool':<12} {'M1 Cum Wool':<12} | {'Q50 Day Wool':<13} {'Q50 Cum Wool':<13} | {'Diff':<8}")
    for d in range(30):
        m_day, m_cum = m1_wool[d][1], m1_wool[d][2]
        q_day, q_cum = q50_wool[d][1], q50_wool[d][2]
        diff = q_cum - m_cum
        if m_day != q_day or diff != 0:
            print(f"{d:<4} | {m_day:<12} {m_cum:<12} | {q_day:<13} {q_cum:<13} | {diff:+d}")

    # 3. Step-by-step sheep lifecycle timeline during first divergence
    # Find day where sheep count or wool diverged
    div_day = None
    for d in range(30):
        m_sheep = len(m1_inst.history[d*24+23]["sheep"])
        q_sheep = len(q50_inst.history[d*24+23]["sheep"])
        m_cum = m1_wool[d][2]
        q_cum = q50_wool[d][2]
        if m_sheep != q_sheep or m_cum != q_cum:
            div_day = d
            break

    print(f"\n--- FIRST DIVERGENCE DAY: Day {div_day} ---")
    if div_day is not None:
        # Print hours of div_day
        for hr in range(24):
            step = div_day * 24 + hr
            hm = m1_inst.history[step]
            hq = q50_inst.history[step]
            
            # Check what workers were doing
            m_wheat_harv = [w for w, a in enumerate(hm["w_acts"]) if a[0] == "HARVEST" and hm["w_pos"][w] in hm["wheat"]]
            q_wheat_harv = [w for w, a in enumerate(hq["w_acts"]) if a[0] == "HARVEST" and hq["w_pos"][w] in hq["wheat"]]
            m_sheep_acts = [(w, a[0]) for w, a in enumerate(hm["w_acts"]) if a[0] in ("FEED", "CARE", "HARVEST") and hm["w_pos"][w] in hm["sheep"]]
            q_sheep_acts = [(w, a[0]) for w, a in enumerate(hq["w_acts"]) if a[0] in ("FEED", "CARE", "HARVEST") and hq["w_pos"][w] in hq["sheep"]]
            
            if q_wheat_harv or q_sheep_acts or m_sheep_acts or m_wheat_harv:
                print(f"Hour {hr:2d}:")
                print(f"  M1:  Sheep acts: {m_sheep_acts} | Wheat harvests: {len(m_wheat_harv)} | Money: ${hm['money']:.0f} | Shed Wheat: {hm['shed'].get('WHEAT', 0)}")
                print(f"  Q50: Sheep acts: {q_sheep_acts} | Wheat harvests: {len(q_wheat_harv)} | Money: ${hq['money']:.0f} | Shed Wheat: {hq['shed'].get('WHEAT', 0)}")

    return {
        "seed": seed,
        "rew_m1": rew_m1,
        "rew_q50": rew_q50,
        "m1_wool_total": m1_wool[-1][2],
        "q50_wool_total": q50_wool[-1][2],
        "m1_events": m1_events,
        "q50_events": q50_events
    }

if __name__ == "__main__":
    for s in [1060, 1086]:
        audit_seed(s)
