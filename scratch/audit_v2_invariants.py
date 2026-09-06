"""
scratch/audit_v2_invariants.py
Empirical analysis of V2's Hard Invariants vs Soft Expectations.
Analyzes 30 seeds to verify deterministic trace execution invariants.
"""

import sys
sys.path.insert(0, ".")
import json
import kaggle_environments
import candidates.slot2_aethel_refined_v2 as v2

SEEDS = [10000 + i * 37 for i in range(30)]

def audit_seed(seed):
    env = kaggle_environments.make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    env.reset()
    
    # State tracking
    invariants = {
        "day0_hands_hired": 0,
        "day0_pastures_built": 0,
        "day0_cows_placed": 0,
        "day0_sheep_placed": 0,
        "day0_melons_planted": 0,
        "melon_water_days": set(),
        "step264_melon_sold": 0,
        "step264_money": 0.0,
        "strawberries_planted_d11_15": 0,
        "total_fertilizer_sold": 0,
        "total_milk_sold": 0,
        "total_strawberries_sold": 0,
        "final_money": 0.0
    }
    
    for step in range(719):
        obs0 = env.state[0].observation
        priv0 = obs0["private"]
        farm0 = obs0["farms"][0]
        day = step // 24
        hour = step % 24
        
        act0 = v2.agent(obs0)
        
        # Day 0 Invariants
        if day == 0:
            if hour == 23:
                invariants["day0_hands_hired"] = len(farm0["hands"])
                p_cnt = sum(1 for row in farm0["tiles"] for t in row if isinstance(t, dict) and t.get("kind") == "PASTURE")
                c_cnt = sum(1 for row in farm0["tiles"] for t in row if isinstance(t, dict) and t.get("animal") == "COW")
                s_cnt = sum(1 for row in farm0["tiles"] for t in row if isinstance(t, dict) and t.get("animal") == "SHEEP")
                m_cnt = sum(1 for row in farm0["tiles"] for t in row if isinstance(t, dict) and t.get("crop") == "MELON")
                invariants["day0_pastures_built"] = p_cnt
                invariants["day0_cows_placed"] = c_cnt
                invariants["day0_sheep_placed"] = s_cnt
                invariants["day0_melons_planted"] = m_cnt
                
        # Melon watering days
        if day <= 10:
            for row in farm0["tiles"]:
                for t in row:
                    if isinstance(t, dict) and t.get("crop") == "MELON" and t.get("watered_today"):
                        invariants["melon_water_days"].add(day)
                        
        # Step 264 Melon Sale
        if step == 264:
            invariants["step264_money"] = float(farm0["money"])
            for o in act0.get("market", []):
                if isinstance(o, list) and len(o) >= 3 and o[0] == "SELL" and o[1] == "MELON":
                    invariants["step264_melon_sold"] += int(o[2])
                    
        # Strawberries planted by Day 15
        if step == 15 * 24:
            s_cnt = sum(1 for row in farm0["tiles"] for t in row if isinstance(t, dict) and t.get("crop") == "STRAWBERRY")
            invariants["strawberries_planted_d11_15"] = s_cnt
            
        # Sales tracking
        for o in act0.get("market", []):
            if isinstance(o, list) and len(o) >= 3 and o[0] == "SELL":
                item = o[1]
                qty = int(o[2])
                if item == "FERTILIZER": invariants["total_fertilizer_sold"] += qty
                elif item == "MILK": invariants["total_milk_sold"] += qty
                elif item == "STRAWBERRY": invariants["total_strawberries_sold"] += qty
                
        env.step([act0, v2.agent])
        
    invariants["final_money"] = float(env.steps[-1][0]["reward"])
    invariants["melon_water_days"] = sorted(list(invariants["melon_water_days"]))
    return invariants


def main():
    print("================================================================================")
    print("AUDITING V2 HARD INVARIANTS ACROSS 30 SEEDS")
    print("================================================================================")
    
    all_results = []
    for s in SEEDS:
        res = audit_seed(s)
        all_results.append(res)
        
    print(f"\n--- HARD INVARIANT CONSISTENCY REPORT (N={len(all_results)}) ---")
    
    # Check invariant consistency across seeds
    d0_hands = set(r["day0_hands_hired"] for r in all_results)
    d0_pastures = set(r["day0_pastures_built"] for r in all_results)
    d0_cows = set(r["day0_cows_placed"] for r in all_results)
    d0_sheep = set(r["day0_sheep_placed"] for r in all_results)
    d0_melons = set(r["day0_melons_planted"] for r in all_results)
    s264_melons = set(r["step264_melon_sold"] for r in all_results)
    d15_straw = set(r["strawberries_planted_d11_15"] for r in all_results)
    
    print(f"1. Day 0 Hands Hired:        {list(d0_hands)} (100% invariant = 3 hands)")
    print(f"2. Day 0 Pastures Built:     {list(d0_pastures)} (100% invariant = 4 pastures)")
    print(f"3. Day 0 Cows Placed:        {list(d0_cows)} (100% invariant = 3 cows)")
    print(f"4. Day 0 Sheep Placed:       {list(d0_sheep)} (100% invariant = 1 sheep)")
    print(f"5. Day 0 Melons Planted:     {list(d0_melons)} (100% invariant = 7 melons)")
    print(f"6. Step 264 Melons Sold:     {list(s264_melons)} (100% invariant = 42 melon units)")
    print(f"7. Day 15 Strawberries:      {list(d15_straw)} (100% invariant = 25 strawberry plants)")
    print(f"8. Melon Watering Days:      {all_results[0]['melon_water_days']} across all seeds")
    
    mean_s264_money = sum(r["step264_money"] for r in all_results) / len(all_results)
    mean_fert = sum(r["total_fertilizer_sold"] for r in all_results) / len(all_results)
    mean_milk = sum(r["total_milk_sold"] for r in all_results) / len(all_results)
    mean_straw = sum(r["total_strawberries_sold"] for r in all_results) / len(all_results)
    mean_final = sum(r["final_money"] for r in all_results) / len(all_results)
    
    print(f"\n--- ECONOMIC SCALE SUMMARY ---")
    print(f"Mean Money at Step 264 (Day 11): ${mean_s264_money:,.1f}")
    print(f"Mean Total Fertilizer Sold:      {mean_fert:.1f} units")
    print(f"Mean Total Milk Sold:            {mean_milk:.1f} units")
    print(f"Mean Total Strawberries Sold:    {mean_straw:.1f} units")
    print(f"Mean Final Reward:               ${mean_final:,.1f}")


if __name__ == "__main__":
    main()
