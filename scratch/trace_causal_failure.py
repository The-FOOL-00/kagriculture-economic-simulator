import sys, os
sys.path.insert(0, '.')
import copy

from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v44_economic_portfolio.main as v44_mod

def run_trace(seed, transform_fn=None):
    sim = FastKagricultureSim(seed=seed)
    obs = sim.reset(seed=seed)
    history = []
    
    for step in range(719):
        a49 = v49_mod.agent(obs[0])
        a44 = v44_mod.agent(obs[1])
        
        if transform_fn and isinstance(a49, dict) and "market" in a49:
            new_m = transform_fn(step, a49["market"])
            if new_m is not None:
                a49 = copy.deepcopy(a49)
                a49["market"] = new_m
                
        obs, _, done, _ = sim.step([a49, a44])
        c49 = float(obs[0]["farms"][0]["money"])
        c44 = float(obs[1]["farms"][1]["money"])
        shed49 = dict(sim.state[0].observation.private["shed"])
        history.append({
            "step": step,
            "cash49": c49,
            "cash44": c44,
            "margin": c49 - c44,
            "shed49": shed49
        })
        if done: break
    return history

hist_base = run_trace(250621, None)

# Test Q6_step697_wool_first
def perm_697(step, m):
    if step != 697 or not m: return m
    sells = [x for x in m if x and x[0] == "SELL"]
    item_order = ["WOOL", "CARROT", "EGG", "MILK"]
    item_rank = {item: i for i, item in enumerate(item_order)}
    sorted_sells = sorted(sells, key=lambda x: item_rank.get(x[1], 99))
    res = copy.deepcopy(m)
    ptr = 0
    for i, x in enumerate(res):
        if x and x[0] == "SELL":
            res[i] = sorted_sells[ptr]
            ptr += 1
    return res

hist_697 = run_trace(250621, perm_697)

# Test Q6_step694_wool_first
def perm_694(step, m):
    if step != 694 or not m: return m
    sells = [x for x in m if x and x[0] == "SELL"]
    item_order = ["WOOL", "TOMATO", "WHEAT", "FERTILIZER", "EGG"]
    item_rank = {item: i for i, item in enumerate(item_order)}
    sorted_sells = sorted(sells, key=lambda x: item_rank.get(x[1], 99))
    res = copy.deepcopy(m)
    ptr = 0
    for i, x in enumerate(res):
        if x and x[0] == "SELL":
            res[i] = sorted_sells[ptr]
            ptr += 1
    return res

hist_694 = run_trace(250621, perm_694)

print("First divergence for Q6_step697_wool_first:")
for s in range(719):
    if hist_base[s]["margin"] != hist_697[s]["margin"]:
        print(f"  Step {s}: Base Marg={hist_base[s]['margin']} vs Trans Marg={hist_697[s]['margin']} (diff {hist_697[s]['margin'] - hist_base[s]['margin']})")
        print(f"  Base Cash49={hist_base[s]['cash49']}, Trans Cash49={hist_697[s]['cash49']}")
        print(f"  Base Shed49={hist_base[s]['shed49']}, Trans Shed49={hist_697[s]['shed49']}")
        break

print("\nFirst divergence for Q6_step694_wool_first:")
for s in range(719):
    if hist_base[s]["margin"] != hist_694[s]["margin"]:
        print(f"  Step {s}: Base Marg={hist_base[s]['margin']} vs Trans Marg={hist_694[s]['margin']} (diff {hist_694[s]['margin'] - hist_base[s]['margin']})")
        print(f"  Base Cash49={hist_base[s]['cash49']}, Trans Cash49={hist_694[s]['cash49']}")
        print(f"  Base Shed49={hist_base[s]['shed49']}, Trans Shed49={hist_694[s]['shed49']}")
        break
