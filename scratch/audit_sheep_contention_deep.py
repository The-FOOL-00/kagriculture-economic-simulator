import sys
import os
import copy
import json
import kaggle_environments

# Add current directory to path
sys.path.insert(0, os.path.abspath('.'))

import candidates.candidate_cl_fert_gated as m1_module
from scratch.run_wheat_quota_sweep_50seeds import ParameterizedQuotaAgent

def run_forensic_comparison(seed):
    print(f"=== FORENSIC ANALYSIS FOR SEED {seed} ===")
    cfg = {"episodeSteps": 720, "seed": seed}

    # Run M1 with deep tracking
    # We will instrument the agent to log every step for sheep
    class InstrumentedM1(m1_module.ClosedLoopEconomicV1):
        def __init__(self):
            super().__init__()
            self.history = []

        def __call__(self, obs, config=None):
            step = int(obs.get("step", 0) or 0)
            p = int(obs.get("player", 0) or 0)
            farms = obs.get("farms") or [{}, {}]
            farm = farms[p] if p < len(farms) else {}
            tiles = farm.get("tiles") or []
            
            # Record sheep state at start of step
            sheep_states = {}
            for y in range(len(tiles)):
                for x in range(len(tiles[y])):
                    t = tiles[y][x]
                    if isinstance(t, dict) and t.get("animal") == "SHEEP":
                        sheep_states[(x, y)] = {
                            "fed_today": t.get("fed_today"),
                            "cared_today": t.get("cared_today"),
                            "yield_units": t.get("yield_units"),
                            "consecutive_unfed": t.get("consecutive_unfed"),
                            "pending_care_bonus": t.get("pending_care_bonus", 0)
                        }
            
            action = super().__call__(obs, config)
            
            self.history.append({
                "step": step,
                "day": step // 24,
                "hour": step % 24,
                "sheep_states": sheep_states,
                "action": action,
                "workers": [tuple(farm.get("farmer", [0, 0]))] + [tuple(h) for h in farm.get("hands", [])],
                "inventories": [dict(farm.get("farmer_inventory", {}))] + [dict(h) for h in farm.get("hands_inventories", [])],
                "money": farm.get("money", 0),
                "shed": dict(farm.get("shed", {}))
            })
            return action

    class InstrumentedQ50(ParameterizedQuotaAgent):
        def __init__(self):
            super().__init__(50)
            self.history = []

        def __call__(self, obs, config=None):
            step = int(obs.get("step", 0) or 0)
            p = int(obs.get("player", 0) or 0)
            farms = obs.get("farms") or [{}, {}]
            farm = farms[p] if p < len(farms) else {}
            tiles = farm.get("tiles") or []
            
            sheep_states = {}
            for y in range(len(tiles)):
                for x in range(len(tiles[y])):
                    t = tiles[y][x]
                    if isinstance(t, dict) and t.get("animal") == "SHEEP":
                        sheep_states[(x, y)] = {
                            "fed_today": t.get("fed_today"),
                            "cared_today": t.get("cared_today"),
                            "yield_units": t.get("yield_units"),
                            "consecutive_unfed": t.get("consecutive_unfed"),
                            "pending_care_bonus": t.get("pending_care_bonus", 0)
                        }
            
            action = super().__call__(obs, config)
            
            self.history.append({
                "step": step,
                "day": step // 24,
                "hour": step % 24,
                "sheep_states": sheep_states,
                "action": action,
                "workers": [tuple(farm.get("farmer", [0, 0]))] + [tuple(h) for h in farm.get("hands", [])],
                "inventories": [dict(farm.get("farmer_inventory", {}))] + [dict(h) for h in farm.get("hands_inventories", [])],
                "money": farm.get("money", 0),
                "shed": dict(farm.get("shed", {}))
            })
            return action

    # Run M1
    agent_m1 = InstrumentedM1()
    env = kaggle_environments.make("kaggriculture", configuration=cfg)
    steps_m1 = env.run([agent_m1, "starter"])
    rew_m1 = steps_m1[-1][0]["reward"]
    
    # Run Q50
    agent_q50 = InstrumentedQ50()
    env = kaggle_environments.make("kaggriculture", configuration=cfg)
    steps_q50 = env.run([agent_q50, "starter"])
    rew_q50 = steps_q50[-1][0]["reward"]

    print(f"Seed {seed}: M1 Reward = {rew_m1:,.0f} | Q50 Reward = {rew_q50:,.0f} | Delta = {rew_q50 - rew_m1:+,.0f}")

    # Analyze sheep lifecycle by day
    # Count how many days sheep were unfed or uncared
    def audit_lifecycle(history, label):
        # We check hour 23 of each day (step % 24 == 23)
        daily_sheep_audit = []
        for h in history:
            if h["hour"] == 23:
                day = h["day"]
                states = h["sheep_states"]
                n_sheep = len(states)
                unfed = sum(1 for pos, s in states.items() if not s["fed_today"])
                uncared = sum(1 for pos, s in states.items() if not s["cared_today"])
                bonus_sum = sum(s["pending_care_bonus"] for pos, s in states.items())
                daily_sheep_audit.append({
                    "day": day,
                    "n_sheep": n_sheep,
                    "unfed": unfed,
                    "uncared": uncared,
                    "bonus_sum": bonus_sum,
                    "states": states
                })
        return daily_sheep_audit

    audit_m1 = audit_lifecycle(agent_m1.history, "M1")
    audit_q50 = audit_lifecycle(agent_q50.history, "Q50")

    print(f"\n--- DAILY SHEEP AUDIT COMPARISON (SEED {seed}) ---")
    print(f"{'Day':<4} | {'M1 Sheep':<8} {'M1 Unfed':<8} {'M1 Uncared':<10} {'M1 CareBonus':<12} | {'Q50 Sheep':<9} {'Q50 Unfed':<9} {'Q50 Uncared':<11} {'Q50 CareBonus':<13} | {'Diff':<10}")
    
    divergences = []
    for d in range(len(audit_m1)):
        m = audit_m1[d]
        q = audit_q50[d]
        diff_str = ""
        if m["n_sheep"] != q["n_sheep"]:
            diff_str += f"SHEEP_COUNT({m['n_sheep']} vs {q['n_sheep']}) "
        if m["unfed"] != q["unfed"]:
            diff_str += f"UNFED({m['unfed']} vs {q['unfed']}) "
        if m["uncared"] != q["uncared"]:
            diff_str += f"UNCARED({m['uncared']} vs {q['uncared']}) "
        if m["bonus_sum"] != q["bonus_sum"]:
            diff_str += f"BONUS({m['bonus_sum']} vs {q['bonus_sum']}) "
        
        if diff_str:
            divergences.append(d)

        print(f"{d:<4} | {m['n_sheep']:<8} {m['unfed']:<8} {m['uncared']:<10} {m['bonus_sum']:<12} | {q['n_sheep']:<9} {q['unfed']:<9} {q['uncared']:<11} {q['bonus_sum']:<13} | {diff_str}")

    return {
        "seed": seed,
        "rew_m1": rew_m1,
        "rew_q50": rew_q50,
        "divergences": divergences,
        "history_m1": agent_m1.history,
        "history_q50": agent_q50.history
    }

if __name__ == "__main__":
    for s in [1060, 1086, 1076]:
        res = run_forensic_comparison(s)
