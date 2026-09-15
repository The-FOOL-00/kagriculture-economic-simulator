import os
import sys
import copy
import importlib.util
import kagsim

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BASELINE_PATH = os.path.join(BASE_DIR, "candidates", "compiled_v54_plus_residual.py")

spec = importlib.util.spec_from_file_location("compiled_baseline", BASELINE_PATH)
mod_base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod_base)

STRAWBERRY_SHOPS = {"SMOOTHIE_SHOP", "ICE_CREAM_SHOP", "BRUNCH_SPOT", "FARMERS_MARKET"}
PIZZA_SHOPS = {"PIZZA_SHOP"}
PET_SHOPS = {"PET_CAFE"}
BAKERY_SHOPS = {"BAKERY"}

def evaluate_opportunity(obs, step, seat):
    farms = obs.get("farms", [])
    farm = farms[seat] if seat < len(farms) else {}
    money = float(farm.get("money", 0.0))
    town = obs.get("town", {}) or {}
    unlocked_shops = list(town.get("unlocked_shops", []) or [])
    market = obs.get("market", {}) or {}
    prices = market.get("prices", {}) or {}
    
    t_remain = 720 - step
    k_spec = 4
    tau = 1500.0
    lambd = 0.25
    L_min = 2500.0
    switching_friction = 200.0
    
    # Risk penalty
    risk_penalty = lambd * max(0.0, L_min - money) + switching_friction
    
    # Check if Strawberry has shop support
    has_straw_shop = any(s in STRAWBERRY_SHOPS for s in unlocked_shops)
    straw_spot = float(prices.get("STRAWBERRY", 120))
    p_eff_straw = straw_spot if has_straw_shop else (0.65 * straw_spot)
    
    # Baseline expected revenue for 4 tiles (Strawberry)
    # Day 11 planting -> step 264. If step <= 264, remaining steps from 264 is 720 - 264 = 456.
    # Strawberry takes 6 days (144 steps) to mature, then yields 4 every 2 days (48 steps).
    mature_step = max(step + 144, 264 + 144)
    if 720 > mature_step:
        n_straw_harvests = (720 - mature_step) // 48 + 1
    else:
        n_straw_harvests = 0
    e_r_base = k_spec * n_straw_harvests * 4 * p_eff_straw
    straw_seed_cost = k_spec * 100.0
    
    best_crop = None
    best_delta = -999999.0
    best_spec_rev = 0.0
    best_seed_cost = 0.0
    
    candidates = []
    if any(s in PIZZA_SHOPS for s in unlocked_shops):
        candidates.append("TOMATO")
    if any(s in PET_SHOPS for s in unlocked_shops):
        candidates.append("CARROT")
    if any(s in BAKERY_SHOPS for s in unlocked_shops):
        candidates.append("WHEAT")
        
    for crop in candidates:
        if crop == "TOMATO":
            tom_spot = float(prices.get("TOMATO", 60))
            p_eff_crop = min(60.0, tom_spot)
            # Tomato takes 5 days (120 steps) to mature, yields 4 every 1 day (24 steps)
            mature_step = max(step + 120, 264 + 120)
            if 720 > mature_step:
                n_harvests = (720 - mature_step) // 24 + 1
            else:
                n_harvests = 0
            e_r_spec = k_spec * n_harvests * 4 * p_eff_crop
            seed_cost = k_spec * 50.0
        elif crop == "CARROT":
            car_spot = float(prices.get("CARROT", 35))
            p_eff_crop = min(35.0, car_spot)
            # Carrot takes 3 days (72 steps), single harvest of 4, can replant
            mature_step = max(step + 72, 264 + 72)
            n_cycles = (720 - mature_step) // 72 + 1
            e_r_spec = k_spec * n_cycles * 4 * p_eff_crop
            seed_cost = k_spec * n_cycles * 20.0
        elif crop == "WHEAT":
            wht_spot = float(prices.get("WHEAT", 25))
            p_eff_crop = min(25.0, wht_spot)
            # Wheat takes 2 days (48 steps), single harvest of 4, can replant
            mature_step = max(step + 48, 264 + 48)
            n_cycles = (720 - mature_step) // 48 + 1
            e_r_spec = k_spec * n_cycles * 4 * p_eff_crop
            seed_cost = k_spec * n_cycles * 10.0
            
        delta = (e_r_spec - seed_cost) - (e_r_base - straw_seed_cost) - risk_penalty
        if delta > best_delta:
            best_delta = delta
            best_crop = crop
            best_spec_rev = e_r_spec
            best_seed_cost = seed_cost
            
    decision = "SPECIALIZE" if (best_delta >= tau and money >= L_min) else "BASELINE"
    return {
        "step": step,
        "money": money,
        "shops": unlocked_shops,
        "candidates": candidates,
        "best_crop": best_crop,
        "best_delta": best_delta,
        "e_r_spec": best_spec_rev,
        "e_r_base": e_r_base,
        "risk_penalty": risk_penalty,
        "decision": decision
    }

# Test across 50 discovery seeds: 245000-245049
activations = 0
active_seeds = []
events = []

for seed in range(245000, 245050):
    g = kagsim.Game(seed)
    seed_activated = False
    
    # Run game with baseline agents
    spec0 = importlib.util.spec_from_file_location(f"b0_{seed}", BASELINE_PATH)
    m0 = importlib.util.module_from_spec(spec0)
    spec0.loader.exec_module(m0)
    
    spec1 = importlib.util.spec_from_file_location(f"b1_{seed}", BASELINE_PATH)
    m1 = importlib.util.module_from_spec(spec1)
    spec1.loader.exec_module(m1)
    
    while not g.done:
        s = g.step_count
        o0 = g.observe(0)
        o1 = g.observe(1)
        
        if s in [72, 144, 216, 288]:
            res = evaluate_opportunity(o0, s, 0)
            events.append((seed, res))
            if res["decision"] == "SPECIALIZE" and not seed_activated:
                seed_activated = True
                activations += 1
                active_seeds.append((seed, s, res["best_crop"], res["best_delta"]))
                
        a0 = m0.agent(o0)
        a1 = m1.agent(o1)
        g.step(a0, a1)

print(f"\nTotal Activations across 50 seeds: {activations} / 50 seeds")
print("Sample activations:")
for act in active_seeds[:10]:
    print(f"  Seed {act[0]} at Step {act[1]}: Crop={act[2]}, Delta={act[3]:.1f}")
